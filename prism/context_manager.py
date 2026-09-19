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

PLACEHOLDER_CHARS = 60      # temporary topic label = first 60 characters of first message


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
        self._tail: deque[Message] = deque(maxlen=recent_window)
        self._next_seq = 0
        self._open_seq: int | None = None
        self.events: list[str] = []

    # ================================================================ public API

    def prepare_context(self, user_text: str) -> list[Message]:
        """Prepare context for the LLM call. Runs segmentation, routing, and layer transfers."""
        msg = Message("user", user_text)
        self._segment(msg)                         # 1. same topic, old topic, or new?
        self._add_to_open_page(msg)                # 2. save the message
        scores = self._route(msg)                  # 3. which topics are needed?
        wanted = self._bring_in_needed(scores)     # 4. L2 -> L1 for needed topics
        self._relieve_pressure(scores, wanted)     # 5. over high_water? demote down to low_water
        self._tail.append(msg)
        return self.l1.render()                    # 6. pages sorted by number with gap markers

    def record_reply(self, content: str, role: str = "assistant") -> None:
        """Save the model's reply (or a tool result) into the open page."""
        msg = Message(role, content)
        self._add_to_open_page(msg)
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
        self._log(f"move page {seq}: {src.name} -> {dst.name}")

    def snapshot(self) -> str:
        """Human-readable overview of L1 and L2 allocations."""
        l1 = ", ".join(f"p{p.seq}[t{p.topic_id}{'*' if p.is_open else ''}, {p.tokens}tok]"
                       for p in self.l1.pages()) or "-"
        l2 = ", ".join(f"p{p.seq}[t{p.topic_id}, {p.tokens}tok]" for p in self.l2.pages()) or "-"
        return (f"L1 {self.l1.used_tokens}/{self.l1.max_tokens} tokens "
                f"({self.l1.utilization():.0%}): {l1}\n"
                f"L2: {l2}")

    def drain_events(self) -> list[str]:
        events, self.events = self.events, []
        return events

    # ================================================================ step 1: segment

    def _segment(self, msg: Message) -> None:
        open_topic = self.topics.open_topic
        decision = self.segmenter.decide(
            open_topic, self.topics.closed_topics(), list(self._tail), msg
        )

        if open_topic is not None and decision.action == "continue":
            page = self.l1.get(self._open_seq)
            if page.tokens >= self.max_page_tokens:      # split only between turns
                page.is_open = False
                self._open_page(open_topic.id)
            return

        self._close_current_topic()
        if decision.action == "return" and decision.topic_id is not None:
            topic = self.topics.reopen(decision.topic_id)
            self._log(f"return to topic {topic.id} ({topic.card.label})")
        else:
            topic = self.topics.new_topic(placeholder=msg.content[:PLACEHOLDER_CHARS])
            self._log(f"new topic {topic.id}")
        self._open_page(topic.id)

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
        new_pages = [self._page(s) for s in topic.page_seqs if s > topic.card.covered_through]
        # Synchronous card write in v1
        topic.card = self.card_writer.write(topic.card, new_pages)
        if topic.page_seqs:
            topic.card.covered_through = max(topic.page_seqs)
        self._log(f"closed topic {topic.id}, card: {topic.card.label}")

    # ================================================================ step 2: add

    def _add_to_open_page(self, msg: Message) -> None:
        try:
            self.l1.append_message(self._open_seq, msg)
        except L1FullError:
            if not self._make_room(msg.tokens, {}, {self._open_seq}):
                raise
            self.l1.append_message(self._open_seq, msg)

    # ================================================================ step 3: route

    def _route(self, msg: Message) -> dict[int, float]:
        open_topic = self.topics.open_topic
        closed = self.topics.closed_topics()
        scores = self.router.score(closed, list(self._tail), msg) if closed else {}
        if open_topic is not None:
            scores[open_topic.id] = 1.0               # the current topic is always needed
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
        newest = self.l1.seqs()[-self.protect_recent_pages:]
        protected.update(newest)
        for tid in wanted:
            protected.update(self.topics.get(tid).page_seqs)
        return protected

    def _pick_victim(self, scores: dict[int, float], protected: set[int]) -> int | None:
        candidates = [p for p in self.l1.pages() if p.seq not in protected]
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
