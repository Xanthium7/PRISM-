"""Core data models: messages, pages, and topics.

This file sits at the base of the dependency tree and imports nothing
from storage, deciders, or the manager to guarantee no circular dependencies.
"""
from __future__ import annotations

from dataclasses import dataclass, field


def estimate_tokens(text: str) -> int:
    """Rough estimate: about 4 characters per token. Swap in a real tokenizer later."""
    return max(1, len(text) // 4)


@dataclass
class Message:
    role: str        # "user" | "assistant" | "tool" (and "system" for gap markers only)
    content: str

    @property
    def tokens(self) -> int:
        return estimate_tokens(self.content)


@dataclass
class PageBlock:
    seq: int                                   # permanent position in history; also its ID
    topic_id: int                              # which topic this page belongs to
    data: list[Message] = field(default_factory=list)
    type: str = "chat"                         # later: "summary", "file_stub"
    is_open: bool = True                       # still receiving messages

    @property
    def tokens(self) -> int:                   # this could be optimised using self.token of sorts
        return sum(m.tokens for m in self.data)


@dataclass
class TopicCard:
    """The index entry for a topic. This is all the router ever sees."""
    label: str
    description: str = ""
    key_facts: list[str] = field(default_factory=list)   # concrete, one fact each
    entities: list[str] = field(default_factory=list)    # names, files, places
    covered_through: int = -1                            # last page seq this card reflects

    def as_text(self) -> str:
        parts = [self.label, self.description, *self.key_facts, *self.entities]
        return " | ".join(p for p in parts if p)


@dataclass
class Topic:
    id: int
    card: TopicCard
    page_seqs: list[int] = field(default_factory=list)   # not necessarily consecutive
    is_open: bool = True
