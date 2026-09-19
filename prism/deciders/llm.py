"""Card writer powered by an LLM (Claude Haiku or similar small model)."""
from __future__ import annotations

import json

from ..models import PageBlock, TopicCard

CARD_PROMPT = """You maintain an index card for one conversation topic.
You get the previous card (may be empty) and the new pages since it was written.
Return ONLY JSON: {"label": str, "description": str, "key_facts": [str], "entities": [str]}

Rules:
1. label: 8 words or fewer.
2. description: 2-3 sentences, what was discussed and how it ended.
3. key_facts: concrete values only (names, numbers, filenames, choices, decisions), one per item.
4. If a new fact contradicts an old one, replace the old one. Do not keep both.
5. Never drop a still-valid fact to save space. Never invent anything.
6. Keep the whole card under about 150 tokens.
"""


class LLMCardWriter:
    """PLACEHOLDER. Implement `_call_llm` with a small fast model (e.g. Claude Haiku)."""

    def write(self, old_card: TopicCard | None, pages: list[PageBlock]) -> TopicCard:
        if not pages:
            return old_card if old_card is not None else TopicCard(label="Empty topic")
        old = json.dumps(old_card.__dict__) if old_card else "(none)"
        new = "\n".join(f"{m.role}: {m.content}" for p in pages for m in p.data)
        raw = self._call_llm(f"{CARD_PROMPT}\nPREVIOUS CARD:\n{old}\n\nNEW PAGES:\n{new}")
        data = json.loads(raw)
        return TopicCard(
            label=data["label"],
            description=data["description"],
            key_facts=data["key_facts"],
            entities=data["entities"],
            covered_through=max(p.seq for p in pages),
        )

    def _call_llm(self, prompt: str) -> str:
        raise NotImplementedError("Connect this to a small LLM. It runs when a topic closes.")
