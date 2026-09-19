"""Jev-based deciders for fast System One decisions (TypeSafe AI)."""
from __future__ import annotations

from ..models import Message, Topic
from .interfaces import SegmentDecision


class JevClient:
    """PLACEHOLDER. Replace `ask` with a real call to the Jev API (see docs.typesafe.ai).

    ASSUMED shapes, based on the docs' description of Choice and Noul questions:
      request : state (text) + a list of questions
      Choice  -> {"choice": <option id>, "probabilities": {<option id>: p}, "confidence": c}
      Noul    -> {"noul": p}      (0 to 1, "is this statement true?")
    Returns a dict keyed by question id.
    """

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def ask(self, state: str, questions: list[dict]) -> dict:
        raise NotImplementedError("Connect JevClient.ask to the Jev API (early access).")


def _conversation_text(recent: list[Message], new_msg: Message) -> str:
    lines = [f"{m.role}: {m.content}" for m in recent]
    lines.append(f"NEWEST user message: {new_msg.content}")
    return "\n".join(lines)


class JevSegmenter:
    """One Choice question: continue / new / return to one of the old topics."""

    def __init__(self, client: JevClient, min_confidence: float = 0.6, return_threshold: float = 0.8):
        self.client = client
        self.min_confidence = min_confidence      # below this: assume "continue" (safest)
        self.return_threshold = return_threshold  # strict: a wrong merge is worse than a split

    def decide(
        self,
        open_topic: Topic | None,
        closed_topics: list[Topic],
        recent: list[Message],
        new_msg: Message,
    ) -> SegmentDecision:
        if open_topic is None:
            return SegmentDecision("new")

        options = {
            "continue": f"Continues the current topic: {open_topic.card.label}",
            "new": "Starts a completely new topic",
        }
        # Jev's Choice limit is 255 options. Beyond that, shortlist closed topics first.
        for t in closed_topics:
            options[f"return:{t.id}"] = f"Returns to an earlier topic: {t.card.as_text()}"

        result = self.client.ask(
            state=_conversation_text(recent, new_msg),
            questions=[{
                "type": "choice",
                "id": "segment",
                "question": "Which best describes the newest user message?",
                "options": options,
            }],
        )["segment"]

        choice, confidence = result["choice"], result["confidence"]
        if confidence < self.min_confidence:
            return SegmentDecision("continue", confidence=confidence)
        if choice.startswith("return:"):
            p = result["probabilities"].get(choice, 0.0)
            if p < self.return_threshold:
                return SegmentDecision("new", confidence=p)
            return SegmentDecision("return", int(choice.split(":")[1]), p)
        return SegmentDecision(choice, confidence=confidence)


class JevRouter:
    """One Noul question per topic: 'is this topic needed to answer the newest message?'"""

    def __init__(self, client: JevClient):
        self.client = client

    def score(
        self,
        topics: list[Topic],
        recent: list[Message],
        new_msg: Message,
    ) -> dict[int, float]:
        if not topics:
            return {}
        questions = [{
            "type": "noul",
            "id": f"topic_{t.id}",
            "statement": (
                "The newest user message needs information from this earlier "
                f"topic: {t.card.as_text()}"
            ),
        } for t in topics]
        result = self.client.ask(state=_conversation_text(recent, new_msg), questions=questions)
        return {t.id: result[f"topic_{t.id}"]["noul"] for t in topics}
