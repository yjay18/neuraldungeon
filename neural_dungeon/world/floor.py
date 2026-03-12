"""Floor generation — builds rooms from neural network or fallback random."""
import random
import torch
from neural_dungeon.config import (
    ROOMS_PER_FLOOR, ROOM_TYPE_COMBAT, ROOM_TYPE_ELITE,
    ROOM_TYPE_DEAD, ROOM_TYPE_BOSS, ROOM_TYPE_START,
    BOSS_FLOORS,
)
from neural_dungeon.world.room import Room
from neural_dungeon.world.map_graph import FloorMap


class Floor:
    def __init__(self, floor_index: int, total_rooms: int = ROOMS_PER_FLOOR):
        self.floor_index = floor_index
        self.rooms: list[Room] = []
        self.current_room_index = 0
        self.floor_map: FloorMap | None = None
        self._generate_rooms_random(total_rooms)

    @classmethod
    def from_network(
        cls,
        floor_index: int,
        activations: list[float],
        weight_matrix: torch.Tensor,
    ) -> "Floor":
        """Build a floor from neural network activations and weights."""
        floor = cls.__new__(cls)
        floor.floor_index = floor_index
        floor.rooms = []
        floor.current_room_index = 0

        floor.floor_map = FloorMap(
            floor_index=floor_index,
            activations=activations,
            weight_matrix=weight_matrix,
        )

        return floor

    def build_rooms_from_path(self):
        """After the player picks a path on the map, create the room list."""
        if not self.floor_map:
            return

        self.rooms = []
        for node in self.floor_map.path_rooms:
            room = Room(
                room_type=node.room_type,
                room_index=len(self.rooms),
                floor_index=self.floor_index,
                activation=node.activation,
            )
            self.rooms.append(room)

        if not self.rooms:
            self.rooms.append(Room(
                room_type=ROOM_TYPE_COMBAT,
                room_index=0,
                floor_index=self.floor_index,
                activation=0.5,
            ))

        # Append boss room on boss floors
        if self.floor_index in BOSS_FLOORS:
            self.rooms.append(Room(
                room_type=ROOM_TYPE_BOSS,
                room_index=len(self.rooms),
                floor_index=self.floor_index,
                activation=1.0,
            ))

        self.current_room_index = 0

    def _generate_rooms_random(self, total: int) -> None:
        """Fallback: random linear rooms without network."""
        for i in range(total):
            if i == 0:
                rtype = ROOM_TYPE_START
            elif i == total - 1:
                rtype = ROOM_TYPE_COMBAT
            elif random.random() < 0.15:
                rtype = ROOM_TYPE_DEAD
            elif random.random() < 0.15 and self.floor_index > 0:
                rtype = ROOM_TYPE_ELITE
            else:
                rtype = ROOM_TYPE_COMBAT

            activation = random.uniform(0.2, 0.9)
            if rtype == ROOM_TYPE_DEAD:
                activation = 0.02
            elif rtype == ROOM_TYPE_ELITE:
                activation = random.uniform(0.7, 1.0)

            room = Room(
                room_type=rtype,
                room_index=i,
                floor_index=self.floor_index,
                activation=activation,
            )
            self.rooms.append(room)

    @property
    def current_room(self) -> Room:
        return self.rooms[self.current_room_index]

    @property
    def is_last_room(self) -> bool:
        return self.current_room_index >= len(self.rooms) - 1

    def advance_room(self) -> Room | None:
        """Move to next room. Returns new room or None if floor done."""
        if self.is_last_room:
            return None
        self.current_room_index += 1
        return self.current_room

    @property
    def progress(self) -> str:
        return f"Room {self.current_room_index + 1}/{len(self.rooms)}"

    @property
    def has_map(self) -> bool:
        return self.floor_map is not None
