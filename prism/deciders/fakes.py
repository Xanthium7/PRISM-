"""Offline stand-ins for Jev and the card-writing LLM.

Uses simple keyword overlap and frequency counting so the system runs without any API.
Crude on purpose: they exist to exercise the manager and test invariants.
"""
from __future__ import annotations

import re
from collections import Counter

from ..models import Message, PageBlock, Topic, TopicCard
from .interfaces import SegmentDecision

STOPWORDS = set("""
the and for are but not you your with that this from have has had was were will would can could
should what which who how why when where about into just also then than them they their there
its it's i'm dont don't let lets please help need want like some any all more most very much
""".split())


def words(text: str) -> set[str]:
    out = set()
    for w in re.findall(r"[a-z]+", text.lower()):
        if len(w) > 2 and w not in STOPWORDS:
            if (w.endswith("ches") or w.endswith("shes") or w.endswith("sses") or w.endswith("xes")) and len(w) > 4:
                out.add(w[:-2])
            elif w.endswith("s") and not w.endswith("ss") and len(w) > 3:
                out.add(w[:-1])
            else:
                out.add(w)
    return out


def overlap(msg_words: set[str], topic_words: set[str]) -> float:
    return len(msg_words & topic_words) / len(msg_words) if msg_words else 0.0


class KeywordSegmenter:
    def __init__(self, continue_threshold: float = 0.2, return_threshold: float = 0.34):
        self.continue_threshold = continue_threshold
        self.return_threshold = return_threshold

    def decide(
        self,
        open_topic: Topic | None,
        closed_topics: list[Topic],
        recent: list[Message],
        new_msg: Message,
    ) -> SegmentDecision:
        if open_topic is None:
            return SegmentDecision("new")
        msg_words = words(new_msg.content)

        closed_words = set().union(*(words(t.card.as_text()) for t in closed_topics)) if closed_topics else set()
        open_card_words = words(open_topic.card.as_text())
        recent_words = words(" ".join(m.content for m in recent))
        recent_open_words = recent_words - (closed_words - open_card_words)
        open_words = open_card_words | recent_open_words
        open_score = overlap(msg_words, open_words)

        best_id, best_score = None, 0.0
        for t in closed_topics:
            s = overlap(msg_words, words(t.card.as_text()))
            if s > best_score:
                best_id, best_score = t.id, s

        if best_id is not None and best_score >= self.return_threshold and best_score > open_score:
            return SegmentDecision("return", best_id, best_score)
        if open_score >= self.continue_threshold or len(msg_words) <= 2:   # short replies continue
            return SegmentDecision("continue", confidence=open_score)
        return SegmentDecision("new")


class KeywordRouter:
    def score(
        self,
        topics: list[Topic],
        recent: list[Message],
        new_msg: Message,
    ) -> dict[int, float]:
        msg_words = words(new_msg.content)
        return {t.id: min(1.0, 2 * overlap(msg_words, words(t.card.as_text()))) for t in topics}


class FakeCardWriter:
    def write(self, old_card: TopicCard | None, pages: list[PageBlock]) -> TopicCard:
        if not pages:
            return old_card if old_card is not None else TopicCard(label="Empty topic")
        all_text = " ".join(m.content for p in pages for m in p.data)
        user_texts = [m.content for p in pages for m in p.data if m.role == "user"]
        top = [w for w, _ in Counter(words(all_text)).most_common(6)]
        entities = list(dict.fromkeys((old_card.entities if old_card else []) + top))[:10]
        facts = list(dict.fromkeys((old_card.key_facts if old_card else []) + [t[:80] for t in user_texts]))
        return TopicCard(
            label=" / ".join(entities[:3]) if entities else "General",
            description=f"Discussion about {', '.join(entities[:4])}." if entities else "Discussion.",
            key_facts=facts,
            entities=entities,
            covered_through=max(p.seq for p in pages),
        )
