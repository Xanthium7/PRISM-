"""L1: active pages sent to the model as prompt context."""
from __future__ import annotations

from ..models import Message, PageBlock


class L1FullError(Exception):
    """Raised when something would not fit in L1. The manager must make room first."""


class L1:
    name = "L1"

    def __init__(self, max_tokens: int, high_water: float = 0.85, low_water: float = 0.70):
        if not 0 < low_water < high_water <= 1:
            raise ValueError("need 0 < low_water < high_water <= 1")
        self.max_tokens = max_tokens
        self.high_water = high_water
        self.low_water = low_water
        self._pages: dict[int, PageBlock] = {}     # seq -> page

    # ---- write ----
    def put(self, page: PageBlock) -> None:
        if page.seq in self._pages:
            raise ValueError(f"page {page.seq} is already in L1")
        if page.tokens > self.free_tokens:
            raise L1FullError(f"page {page.seq} needs {page.tokens} tokens, {self.free_tokens} free")
        self._pages[page.seq] = page

    def take(self, seq: int) -> PageBlock:
        page = self._pages[seq]
        if page.is_open:
            raise ValueError(f"page {seq} is open and cannot leave L1")
        del self._pages[seq]
        return page

    def append_message(self, seq: int, message: Message) -> None:
        if message.tokens > self.free_tokens:
            raise L1FullError(f"message needs {message.tokens} tokens, {self.free_tokens} free")
        self._pages[seq].data.append(message)

    # ---- read ----
    def get(self, seq: int) -> PageBlock:
        return self._pages[seq]

    def has(self, seq: int) -> bool:
        return seq in self._pages

    def seqs(self) -> list[int]:
        return sorted(self._pages)

    def pages(self) -> list[PageBlock]:
        return [self._pages[s] for s in self.seqs()] # returns the pages sorted by seq number

    def render(self, mark_gaps: bool = True) -> list[Message]:
        """Flatten pages sorted by seq. Insert a marker at gaps in seq."""
        out: list[Message] = []
        expected = 0
        for page in self.pages():
            if mark_gaps and page.seq != expected and out:
                out.append(Message("system", "[earlier messages omitted]"))
            elif mark_gaps and page.seq != 0 and not out:
                # First page in L1 is not seq 0
                out.append(Message("system", "[earlier messages omitted]"))
            out.extend(page.data)
            expected = page.seq + 1
        return out

    # ---- token accounting ----
    @property
    def used_tokens(self) -> int:
        return sum(p.tokens for p in self._pages.values())

    @property
    def free_tokens(self) -> int:
        return self.max_tokens - self.used_tokens

    def utilization(self) -> float:
        return self.used_tokens / self.max_tokens if self.max_tokens else 0.0

    def over_high_water(self) -> bool:
        return self.utilization() > self.high_water

    def above_low_water(self) -> bool:
        return self.utilization() > self.low_water
