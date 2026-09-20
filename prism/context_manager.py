"""The context manager: coordinates L1, L2, the topic table, the location book, and deciders.

Your app calls exactly two methods on the hot path:
    messages = manager.prepare_context(user_text)   # app passes `messages` to the LLM
    manager.record_reply(reply_text)                # save what the model said
"""
from __future__ import annotations

from collections import deque

from .deciders import CardWriter, Router, Segmenter
from .models import Message, PageBlock
from .storage import L1, L1FullError, L2, PageTable, StorageProtocol, TopicTable

# temporary topic label = first 60 characters of first message
PLACEHOLDER_CHARS = 60


class ContextManager:
    def __init__(
        self,
        l1: L1,
        l2: L2,
        topics: TopicTable,
        page_table: PageTable,
        segmenter: Segmenter,
        router: Router,
        card_writer: CardWriter,
        needed_threshold: float = 0.5,     # router probability needed to bring a topic in
        protect_recent_pages: int = 2,     # newest N pages in L1 are never demoted
        max_page_tokens: int = 400,        # long topics are split into pages at this size
        recent_window: int = 4,            # how many recent messages the deciders see
        reply_reserve: int = 0,            # tokens reserved in L1 for assistant reply
    ):
        self.l1, self.l2 = l1, l2
        self.topics = topics
        self.page_table = page_table
        self.segmenter = segmenter
        self.router = router
        self.card_writer = card_writer
        self.needed_threshold = needed_threshold
        self.protect_recent_pages = protect_recent_pages
        self.max_page_tokens = max_page_tokens
        self.reply_reserve = reply_reserve
        self._tail: deque[Message] = deque(maxlen=recent_window)
        self._next_seq = 0
        self._open_seq: int | None = None
        self._last_scores: dict[int, float] = {}
        self._last_wanted: list[int] = []
        self._moved_this_turn: set[int] = set()
        self.events: list[str] = []

    @property
    def open_seq(self) -> int | None:
        """Sequence number of the current open page, or None."""
        return self._open_seq

    @property
    def open_topic_id(self) -> int | None:
        """ID of the current open topic, or None."""
        return self.topics.open_topic_id

    @property
    def last_scores(self) -> dict[int, float]:
        """Router scores from the most recent prepare_context call (topic_id -> probability).
        Returns a copy so callers cannot accidentally mutate internal state."""
        return dict(self._last_scores)

    # ================================================================ public API

    def prepare_context(self, user_text: str) -> list[Message]:
        """Prepare context for the LLM call. Runs segmentation, routing, and layer transfers."""
        self._moved_this_turn = set()
        msg = Message("user", user_text)
        if msg.tokens > self.l1.max_tokens:
            raise L1FullError(
                f"User message ({msg.tokens} tokens) exceeds L1 max capacity ({self.l1.max_tokens})")

        open_topic = self.topics.open_topic
        decision = self.segmenter.decide(
            open_topic, self.topics.closed_topics(), list(self._tail), msg
        )

        if decision.action == "return" and decision.topic_id is not None:
            self.topics.get(decision.topic_id)

        is_split = (
            open_topic is not None
            and decision.action == "continue"
            and self._open_seq is not None
            and self.l1.get(self._open_seq).tokens >= self.max_page_tokens
        )
        will_open_new_page = open_topic is None or decision.action != "continue" or is_split

        if will_open_new_page:
            protected_count = max(0, self.protect_recent_pages - 1)
            protected_seqs = set(
                self.l1.seqs()[-protected_count:]) if protected_count > 0 else set()
            removable_tokens = sum(
                p.tokens for p in self.l1.pages() if p.seq not in protected_seqs)
        else:
            protected_seqs = {
                self._open_seq} if self._open_seq is not None else set()
            if self.protect_recent_pages > 0:
                protected_seqs.update(
                    self.l1.seqs()[-self.protect_recent_pages:])
            removable_tokens = sum(
                p.tokens for p in self.l1.pages() if p.seq not in protected_seqs)

        if self.l1.free_tokens + removable_tokens < msg.tokens:
            raise L1FullError(
                f"User message ({msg.tokens} tokens) cannot fit in L1")

        # 1. same topic, old topic, or new?
        self._apply_segmentation(decision, msg, is_split)
        # 2. which topics are needed?
        scores = self._route(msg)
        self._last_scores = dict(scores)
        wanted = [
            tid for tid, p in sorted(scores.items(), key=lambda kv: -kv[1])
            if p >= self.needed_threshold
        ]
        self._last_wanted = list(wanted)
        # 3. save the message
        self._add_to_open_page(msg, is_reply=False)
        # 4. L2 -> L1 for needed topics
        wanted = self._bring_in_needed(scores)
        self._last_wanted = list(wanted)
        # 5. over high_water? demote down to low_water
        self._relieve_pressure(scores, wanted)
        if self.reply_reserve > 0:
            protected = self._protected(wanted)
            self._make_room(self.reply_reserve, scores, protected)
        self._tail.append(msg)
        # 6. pages sorted by number with gap markers
        return self.l1.render()

    def record_reply(self, content: str, role: str = "assistant") -> None:
        """Save the model's reply (or a tool result) into the open page."""
        msg = Message(role, content)
        self._add_to_open_page(msg, is_reply=True)
        self._tail.append(msg)

    def move(self, seq: int, src: StorageProtocol, dst: StorageProtocol) -> None:
        """The ONLY way a page changes layer. Keeps the page table correct."""
        page = src.take(seq)
        try:
            dst.put(page)
        except L1FullError:
            src.put(page)
            raise
        self.page_table.set(seq, dst.name)
        self._moved_this_turn.add(seq)
        self._log(f"move page {seq}: {src.name} -> {dst.name}")

    def snapshot(self) -> str:
        """Human-readable overview of L1 and L2 allocations."""
        l1 = ", ".join(f"p{p.seq}[t{p.topic_id}{'*' if p.is_open else ''}, {p.tokens}tok]"
                       for p in self.l1.pages()) or "-"
        l2 = ", ".join(
            f"p{p.seq}[t{p.topic_id}, {p.tokens}tok]" for p in self.l2.pages()) or "-"
        return (f"L1 {self.l1.used_tokens}/{self.l1.max_tokens} tokens "
                f"({self.l1.utilization():.0%}): {l1}\n"
                f"L2: {l2}")

    def drain_events(self) -> list[str]:
        events, self.events = self.events, []
        return events

    # ================================================================ step 1: segment

    def _apply_segmentation(self, decision: any, msg: Message, is_split: bool) -> None:
        open_topic = self.topics.open_topic
        if open_topic is not None and decision.action == "continue":
            if is_split:
                page = self.l1.get(self._open_seq)
                page.is_open = False
                self._open_page(open_topic.id)
            return

        self._close_current_topic()
        if decision.action == "return" and decision.topic_id is not None:
            topic = self.topics.reopen(decision.topic_id)
            self._log(f"return to topic {topic.id} ({topic.card.label})")
        else:
            topic = self.topics.new_topic(
                placeholder=msg.content[:PLACEHOLDER_CHARS])
            self._log(f"new topic {topic.id}")
        self._open_page(topic.id)

    def _segment(self, msg: Message) -> None:
        open_topic = self.topics.open_topic
        decision = self.segmenter.decide(
            open_topic, self.topics.closed_topics(), list(self._tail), msg
        )
        is_split = (
            open_topic is not None
            and decision.action == "continue"
            and self._open_seq is not None
            and self.l1.get(self._open_seq).tokens >= self.max_page_tokens
        )
        self._apply_segmentation(decision, msg, is_split)

    def _open_page(self, topic_id: int) -> None:
        page = PageBlock(seq=self._next_seq, topic_id=topic_id)
        self._next_seq += 1
        self.l1.put(page)
        self.topics.add_page(topic_id, page.seq)
        self.page_table.set(page.seq, "L1")
        self._open_seq = page.seq

    def _close_current_topic(self) -> None:
        topic = self.topics.open_topic
        if topic is None:
            return
        if self._open_seq is not None:
            self.l1.get(self._open_seq).is_open = False
            self._open_seq = None
        self.topics.close(topic.id)
        new_pages = [self._page(
            s) for s in topic.page_seqs if s > topic.card.covered_through]
        # Synchronous card write in v1
        topic.card = self.card_writer.write(topic.card, new_pages)
        if topic.page_seqs:
            topic.card.covered_through = max(topic.page_seqs)
        self._log(f"closed topic {topic.id}, card: {topic.card.label}")

    # ================================================================ step 2: add

    def _add_to_open_page(self, msg: Message, is_reply: bool = False) -> None:
        try:
            self.l1.append_message(self._open_seq, msg)
        except L1FullError:
            if is_reply:
                protected = self._protected(self._last_wanted)
                scores = self._last_scores
                if not self._make_room(msg.tokens, scores, protected):
                    while self.l1.free_tokens < msg.tokens:
                        candidates = [
                            p for p in self.l1.pages() if p.seq != self._open_seq]
                        if not candidates:
                            raise
                        fresh = [
                            p for p in candidates if p.seq not in self._moved_this_turn]
                        pool = fresh if fresh else candidates
                        victim = min(pool, key=lambda p: (
                            scores.get(p.topic_id, 0.0), p.seq)).seq
                        self._log(
                            f"forced demotion of page {victim}: no room for reply")
                        self.move(victim, self.l1, self.l2)
            else:
                protected = self._protected(self._last_wanted)
                scores = self._last_scores
                if not self._make_room(msg.tokens, scores, protected):
                    raise
            self.l1.append_message(self._open_seq, msg)

    # ================================================================ step 3: route

    def _route(self, msg: Message) -> dict[int, float]:
        open_topic = self.topics.open_topic
        closed = self.topics.closed_topics()
        scores = self.router.score(closed, list(
            self._tail), msg) if closed else {}
        if open_topic is not None:
            # the current topic is always needed
            scores[open_topic.id] = 1.0
        return scores

    # ================================================================ step 4: bring in

    def _bring_in_needed(self, scores: dict[int, float]) -> list[int]:
        wanted = [
            tid for tid, p in sorted(scores.items(), key=lambda kv: -kv[1])
            if p >= self.needed_threshold
        ]
        protected = self._protected(wanted)
        for tid in wanted:
            for seq in sorted(self.topics.get(tid).page_seqs, reverse=True):   # newest first
                if self.page_table.where(seq) == "L1":
                    continue
                if seq in self._moved_this_turn:
                    continue
                page = self.l2.get(seq)
                if not self._make_room(page.tokens, scores, protected):
                    self._log(f"no room for page {seq} of topic {tid}")
                    break
                self.move(seq, self.l2, self.l1)
        return wanted

    # ================================================================ step 5: pressure

    def _relieve_pressure(self, scores: dict[int, float], wanted: list[int]) -> None:
        if not self.l1.over_high_water():
            return
        protected = self._protected(wanted)
        while self.l1.above_low_water():
            victim = self._pick_victim(scores, protected)
            if victim is None:
                break                              # everything left is protected
            self.move(victim, self.l1, self.l2)

    # ================================================================ helpers

    def _protected(self, wanted: list[int]) -> set[int]:
        protected: set[int] = set()
        if self._open_seq is not None:
            protected.add(self._open_seq)
        if self.protect_recent_pages > 0:
            newest = self.l1.seqs()[-self.protect_recent_pages:]
            protected.update(newest)
        for tid in wanted:
            protected.update(self.topics.get(tid).page_seqs)
        return protected

    def _pick_victim(self, scores: dict[int, float], protected: set[int]) -> int | None:
        candidates = [p for p in self.l1.pages(
        ) if p.seq not in protected and p.seq not in self._moved_this_turn]
        if not candidates:
            return None
        # least-needed topic first; oldest page first among equals
        return min(candidates, key=lambda p: (scores.get(p.topic_id, 0.0), p.seq)).seq

    def _make_room(self, needed: int, scores: dict[int, float], protected: set[int]) -> bool:
        while self.l1.free_tokens < needed:
            victim = self._pick_victim(scores, protected)
            if victim is None:
                return False
            self.move(victim, self.l1, self.l2)
        return True

    def _page(self, seq: int) -> PageBlock:
        return self.l1.get(seq) if self.page_table.where(seq) == "L1" else self.l2.get(seq)

    def _log(self, text: str) -> None:
        self.events.append(text)
