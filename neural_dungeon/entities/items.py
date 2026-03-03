"""Items — passive, active, weapons. Stub for Phase 1."""
from __future__ import annotations


class Item:
    """Base item class."""

    def __init__(self, name: str, description: str, item_type: str):
        self.name = name
        self.description = description
        self.item_type = item_type  # "passive", "active", "weapon"
