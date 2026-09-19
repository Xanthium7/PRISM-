"""L2: held pages that are kept word for word but not in the prompt."""
from __future__ import annotations

from ..models import PageBlock


class L2:
    """In-memory dictionary wrapper. Same interface methods as L1 for interchangeability."""
    name = "L2"

    def __init__(self):
        self._pages: dict[int, PageBlock] = {}

    def put(self, page: PageBlock) -> None:
        self._pages[page.seq] = page

    def take(self, seq: int) -> PageBlock:
        return self._pages.pop(seq)

    def get(self, seq: int) -> PageBlock:
        return self._pages[seq]

    def has(self, seq: int) -> bool:
        return seq in self._pages

    def pages(self) -> list[PageBlock]:
        return [self._pages[s] for s in sorted(self._pages)]

    def __len__(self) -> int:
        return len(self._pages)
