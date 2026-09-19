"""Interfaces and decision types for deciders."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Protocol

from ..models import Message, PageBlock, Topic, TopicCard


@dataclass
class SegmentDecision:
    action: Literal["continue", "return", "new"]
    topic_id: int | None = None       # only set for "return"
    confidence: float = 1.0


class Segmenter(Protocol):
    def decide(
        self,
        open_topic: Topic | None,
        closed_topics: list[Topic],
        recent: list[Message],
        new_msg: Message,
    ) -> SegmentDecision:
        ...


class Router(Protocol):
    def score(
        self,
        topics: list[Topic],
        recent: list[Message],
        new_msg: Message,
    ) -> dict[int, float]:
        """Returns topic_id -> probability needed."""
        ...


class CardWriter(Protocol):
    def write(self, old_card: TopicCard | None, pages: list[PageBlock]) -> TopicCard:
        ...
