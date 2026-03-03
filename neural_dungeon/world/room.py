"""Room types, contents, activation properties."""
from neural_dungeon.config import (
    ROOM_WIDTH, ROOM_HEIGHT,
    ROOM_TYPE_COMBAT, ROOM_TYPE_ELITE, ROOM_TYPE_DEAD,
    ROOM_TYPE_SHOP, ROOM_TYPE_BOSS, ROOM_TYPE_START,
)
from neural_dungeon.entities.enemies import Enemy, spawn_enemies_for_room


class Room:
    def __init__(
        self,
        room_type: str,
        room_index: int,
        floor_index: int,
        activation: float = 0.5,
    ):
        self.room_type = room_type
        self.room_index = room_index
        self.floor_index = floor_index
        self.activation = activation
        self.width = ROOM_WIDTH
        self.height = ROOM_HEIGHT
        self.cleared = room_type in (ROOM_TYPE_DEAD, ROOM_TYPE_SHOP, ROOM_TYPE_START)
        self.enemies: list[Enemy] = []
        self.entered = False

    def enter(self) -> None:
        if self.entered:
            return
        self.entered = True
        if not self.cleared:
            self.enemies = spawn_enemies_for_room(
                self.room_index, self.floor_index, self.room_type,
                activation=self.activation,
            )

    def update_clear_state(self) -> bool:
        """Returns True if the room just became cleared."""
        if self.cleared:
            return False
        if all(not e.alive for e in self.enemies):
            self.cleared = True
            return True
        return False

    @property
    def living_enemies(self) -> list[Enemy]:
        return [e for e in self.enemies if e.alive]

    @property
    def type_icon(self) -> str:
        icons = {
            ROOM_TYPE_COMBAT: "⚔",
            ROOM_TYPE_ELITE: "💀",
            ROOM_TYPE_DEAD: "◌",
            ROOM_TYPE_SHOP: "🏪",
            ROOM_TYPE_BOSS: "☠",
            ROOM_TYPE_START: "▶",
        }
        return icons.get(self.room_type, "?")

    @property
    def display_name(self) -> str:
        names = {
            ROOM_TYPE_COMBAT: "Neuron Room",
            ROOM_TYPE_ELITE: "High-Activation Room",
            ROOM_TYPE_DEAD: "Dead Neuron",
            ROOM_TYPE_SHOP: "Memory Bank",
            ROOM_TYPE_BOSS: "Boss Node",
            ROOM_TYPE_START: "Entry Point",
        }
        return names.get(self.room_type, "Unknown")
