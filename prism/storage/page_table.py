"""The page table: maps each page sequence number (seq) to the memory layer it resides in.

Inspired by OS page tables tracking memory frames.
Only ContextManager.move() and initial page creation write to this table.
"""
from __future__ import annotations


class PageTable:
    def __init__(self):
        self._where: dict[int, str] = {}     # seq -> "L1" | "L2" (later "L3", "L4")

    def set(self, seq: int, layer: str) -> None:
        """Map page seq to a storage layer name."""
        self._where[seq] = layer

    def where(self, seq: int) -> str:
        """Return the layer name where page seq currently resides."""
        return self._where[seq]

    def pages_in(self, layer: str) -> list[int]:
        """Return a sorted list of all page sequence numbers in a given layer."""
        return sorted(s for s, l in self._where.items() if l == layer)


# Backward-compatibility alias
LocationBook = PageTable
