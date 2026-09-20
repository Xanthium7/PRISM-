"""The topic table: tracks every topic, its card, and which page seqs belong to it."""
from __future__ import annotations

from ..models import Topic, TopicCard


class TopicTable:
    def __init__(self):
        self._topics: dict[int, Topic] = {}
        self._next_id = 1
        self._open_id: int | None = None

    @property
    def open_topic(self) -> Topic | None:
        return self._topics[self._open_id] if self._open_id is not None else None

    @property
    def open_topic_id(self) -> int | None:
        """ID of the current open topic, or None."""
        return self._open_id

    def new_topic(self, placeholder: str) -> Topic:
        if self._open_id is not None:
            raise RuntimeError("close the open topic before starting a new one")
        topic = Topic(id=self._next_id, card=TopicCard(label=placeholder))
        self._topics[topic.id] = topic
        self._open_id = topic.id
        self._next_id += 1
        return topic

    def close(self, topic_id: int) -> None:
        self._topics[topic_id].is_open = False
        if self._open_id == topic_id:
            self._open_id = None

    def reopen(self, topic_id: int) -> Topic:
        if self._open_id is not None:
            raise RuntimeError("close the open topic before reopening another")
        topic = self._topics[topic_id]
        topic.is_open = True
        self._open_id = topic_id
        return topic

    def add_page(self, topic_id: int, seq: int) -> None:
        self._topics[topic_id].page_seqs.append(seq)

    def get(self, topic_id: int) -> Topic:
        return self._topics[topic_id]

    def all(self) -> list[Topic]:
        return list(self._topics.values())

    def closed_topics(self) -> list[Topic]:
        return [t for t in self._topics.values() if not t.is_open]
