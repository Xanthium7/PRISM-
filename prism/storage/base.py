"""Storage protocol defining common operations for memory layers (L1, L2, future L3, L4)."""
from __future__ import annotations

from typing import Protocol

from ..models import PageBlock


class StorageProtocol(Protocol):
    name: str

    def put(self, page: PageBlock) -> None:
        """Store a page."""
        ...

    def take(self, seq: int) -> PageBlock:
        """Remove and return a page."""
        ...

    def get(self, seq: int) -> PageBlock:
        """Retrieve a page by seq without removing it."""
        ...

    def has(self, seq: int) -> bool:
        """Check if seq is present in this layer."""
        ...

    def pages(self) -> list[PageBlock]:
        """Return all pages sorted by seq."""
        ...
