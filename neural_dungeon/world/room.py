"""Room types, contents, activation properties."""
from neural_dungeon.config import (
    ROOM_WIDTH, ROOM_HEIGHT, COVER_HP,
    ROOM_TYPE_COMBAT, ROOM_TYPE_ELITE, ROOM_TYPE_DEAD,
    ROOM_TYPE_SHOP, ROOM_TYPE_WEIGHT, ROOM_TYPE_BOSS, ROOM_TYPE_START,
)
from neural_dungeon.entities.enemies import Enemy, spawn_enemies_for_room
from neural_dungeon.entities.items import generate_shop_items, roll_item_drop
from neural_dungeon.world.room_layouts import (
    get_layout_for_room, get_valid_spawn_positions,
    get_player_spawn, get_blocked_set, Tile,
)


# Weight room buff options
WEIGHT_OPTIONS = [
    {"id": "hp", "name": "+15 Max HP", "desc": "Increase max HP by 15 and heal 15"},
    {"id": "speed", "name": "+8% Speed", "desc": "Increase move speed by 8%"},
    {"id": "damage", "name": "+10% Damage", "desc": "Increase damage by 10%"},
]


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
        self.cleared = room_type in (
            ROOM_TYPE_DEAD, ROOM_TYPE_SHOP, ROOM_TYPE_WEIGHT, ROOM_TYPE_START,
        )
        self.enemies: list[Enemy] = []
        self.entered = False
        self.layout_grid = None
        self.blocked_set: set = set()
        self.cover_hp: dict[tuple[int, int], int] = {}

        # Shop state
        self.shop_items: list[dict] = []

        # Weight room state
        self.weight_options: list[dict] = list(WEIGHT_OPTIONS)
        self.weight_used = False

    def enter(self, player=None) -> None:
        if self.entered:
            return
        self.entered = True

        # Generate layout
        seed = hash((self.floor_index, self.room_index)) % (2**31)
        self.layout_grid = get_layout_for_room(
            self.floor_index, self.room_type, seed=seed,
        )
        self.blocked_set = get_blocked_set(self.layout_grid)
        self._init_cover_hp()

        if self.room_type == ROOM_TYPE_BOSS:
            from neural_dungeon.entities.bosses import spawn_boss
            self.enemies = spawn_boss(self.floor_index)
            # Place boss enemies at valid spawn positions
            player_start = get_player_spawn(self.layout_grid)
            positions = get_valid_spawn_positions(
                self.layout_grid, len(self.enemies), avoid_center=True,
                player_pos=player_start,
            )
            for i, enemy in enumerate(self.enemies):
                if i < len(positions):
                    enemy.x, enemy.y = positions[i]

        elif self.room_type == ROOM_TYPE_SHOP and player is not None:
            self.shop_items = generate_shop_items(
                player.weapon, player.passive_items, player.active_item,
            )

        elif not self.cleared:
            self.enemies = spawn_enemies_for_room(
                self.room_index, self.floor_index, self.room_type,
                activation=self.activation,
            )
            player_start = get_player_spawn(self.layout_grid)
            positions = get_valid_spawn_positions(
                self.layout_grid, len(self.enemies), avoid_center=True,
                player_pos=player_start,
            )
            for i, enemy in enumerate(self.enemies):
                if i < len(positions):
                    enemy.x, enemy.y = positions[i]

    def shop_buy(self, index, player) -> str | None:
        """Buy item at index. Returns message or None if can't buy."""
        if index < 0 or index >= len(self.shop_items):
            return None
        item = self.shop_items[index]
        if player.data_fragments < item["cost"]:
            return "Not enough fragments!"

        player.data_fragments -= item["cost"]

        if item["type"] == "weapon":
            player.weapon = item["id"]
            msg = f"Equipped {item['name']}!"
        elif item["type"] == "passive":
            player.add_passive(item["id"])
            msg = f"Got {item['name']}!"
        elif item["type"] == "active":
            player.active_item = item["id"]
            player.active_item_cooldown = 0
            msg = f"Got {item['name']}!"
        else:
            return None

        self.shop_items.pop(index)
        return msg

    def weight_pick(self, index, player) -> str | None:
        """Pick weight room buff. Returns message or None."""
        if self.weight_used:
            return None
        if index < 0 or index >= len(self.weight_options):
            return None

        opt = self.weight_options[index]
        self.weight_used = True

        if opt["id"] == "hp":
            player.max_hp += 15
            player.hp = min(player.hp + 15, player.max_hp)
            return "+15 Max HP!"
        elif opt["id"] == "speed":
            player.speed_bonus += 0.08
            return "+8% Speed!"
        elif opt["id"] == "damage":
            player.damage_bonus += 0.10
            return "+10% Damage!"
        return None

    def _init_cover_hp(self):
        self.cover_hp = {}
        if self.layout_grid is None:
            return
        for y in range(ROOM_HEIGHT):
            for x in range(ROOM_WIDTH):
                if self.layout_grid[y][x] == Tile.COVER:
                    self.cover_hp[(x, y)] = COVER_HP

    def damage_cover(self, gx: int, gy: int, damage: int) -> None:
        key = (gx, gy)
        if key not in self.cover_hp:
            return
        self.cover_hp[key] -= damage
        if self.cover_hp[key] <= 0:
            self.layout_grid[gy][gx] = Tile.FLOOR
            del self.cover_hp[key]
            self.blocked_set = get_blocked_set(self.layout_grid)

    def get_player_start(self) -> tuple[float, float]:
        if self.layout_grid is not None:
            return get_player_spawn(self.layout_grid)
        return (ROOM_WIDTH / 2, ROOM_HEIGHT - 3.0)

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
            ROOM_TYPE_WEIGHT: "⚖",
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
            ROOM_TYPE_WEIGHT: "Weight Room",
            ROOM_TYPE_BOSS: "Boss Node",
            ROOM_TYPE_START: "Entry Point",
        }
        return names.get(self.room_type, "Unknown")
