"""Player entity — state, stats, inventory, dodge roll."""
from neural_dungeon.config import (
    PLAYER_MAX_HP, PLAYER_SPEED, PLAYER_HITBOX_RADIUS,
    PLAYER_IFRAMES, DODGE_SPEED, DODGE_DURATION, DODGE_COOLDOWN,
    PLAYER_SHOOT_COOLDOWN, PLAYER_BULLET_SPEED, PLAYER_BULLET_DAMAGE,
    PLAYER_BULLET_RANGE, ROOM_WIDTH, ROOM_HEIGHT,
    DIR_NONE, WEAPON_GRADIENT_BEAM, WEAPONS,
    SLOW_MULTIPLIER,
)
from neural_dungeon.utils import clamp, normalize, resolve_tile_collision


class Player:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.hp = PLAYER_MAX_HP
        self.max_hp = PLAYER_MAX_HP
        self.speed = PLAYER_SPEED
        self.hitbox_radius = PLAYER_HITBOX_RADIUS
        self.alive = True

        self.move_dx = 0.0
        self.move_dy = 0.0

        self.aim_dx = 0.0
        self.aim_dy = -1.0  # default aim up

        self.dodging = False
        self.dodge_timer = 0
        self.dodge_cooldown = 0
        self.dodge_dx = 0.0
        self.dodge_dy = 0.0
        self.iframes = 0

        self.shoot_cooldown = 0
        self.shooting = False
        self.weapon = WEAPON_GRADIENT_BEAM

        self.data_fragments = 0
        self.passive_items: list[str] = []
        self.active_item: str | None = None
        self.active_item_cooldown = 0

        # Stat bonuses from weight room
        self.damage_bonus = 0.0
        self.speed_bonus = 0.0

        self.flashlight_on = True

        self.enemies_killed = 0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.rooms_cleared = 0
        self.floors_cleared = 0

    def has_passive(self, item_id: str) -> bool:
        return item_id in self.passive_items

    def add_passive(self, item_id: str) -> None:
        if item_id not in self.passive_items:
            self.passive_items.append(item_id)
            if item_id == "ram_upgrade":
                self.max_hp += 25
                self.hp = min(self.hp + 25, self.max_hp)

    def get_effective_damage(self, base_damage: int) -> int:
        mult = 1.0 + self.damage_bonus
        if self.has_passive("overclocked_core"):
            mult += 0.15
        return max(1, int(base_damage * mult))

    def get_effective_range(self, base_range: float) -> float:
        if self.has_passive("kernel_expansion"):
            return base_range * 1.25
        return base_range

    def can_use_active(self) -> bool:
        return (self.active_item is not None
                and self.active_item_cooldown <= 0
                and self.alive)

    def use_active(self) -> str | None:
        """Use active item. Returns item id or None."""
        if not self.can_use_active():
            return None
        from neural_dungeon.entities.items import ACTIVE_ITEMS
        item_id = self.active_item
        info = ACTIVE_ITEMS.get(item_id)
        if info:
            self.active_item_cooldown = info["cooldown"]
        return item_id

    @property
    def invulnerable(self) -> bool:
        return self.iframes > 0

    @property
    def weapon_info(self) -> dict:
        return WEAPONS[self.weapon]

    def start_dodge(self) -> bool:
        """Initiate dodge roll. Returns True if successful."""
        if self.dodging or self.dodge_cooldown > 0:
            return False
        dx, dy = self.move_dx, self.move_dy
        if dx == 0.0 and dy == 0.0:
            dx, dy = self.aim_dx, self.aim_dy
        if dx == 0.0 and dy == 0.0:
            return False
        self.dodge_dx, self.dodge_dy = normalize(dx, dy)
        self.dodging = True
        self.dodge_timer = DODGE_DURATION
        iframes = PLAYER_IFRAMES
        if self.has_passive("skip_connection"):
            iframes += 3
        self.iframes = iframes
        return True

    def take_damage(self, amount: int) -> int:
        """Returns actual damage taken (0 if invulnerable)."""
        if self.invulnerable or not self.alive:
            return 0
        actual = min(amount, self.hp)
        self.hp -= actual
        self.damage_taken += actual
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return actual

    def take_contact_damage(self, amount: int) -> int:
        """Contact damage with bias_shift passive reduction."""
        if self.has_passive("bias_shift"):
            amount = max(1, amount - 3)
        return self.take_damage(amount)

    def heal(self, amount: int) -> int:
        """Returns actual healing done."""
        actual = min(amount, self.max_hp - self.hp)
        self.hp += actual
        return actual

    def update(self, room_grid=None) -> None:
        if not self.alive:
            return

        # Check if standing on SLOW tile
        speed_mult = 1.0
        if room_grid is not None:
            from neural_dungeon.world.room_layouts import Tile
            gx, gy = int(self.x), int(self.y)
            if 0 <= gx < ROOM_WIDTH and 0 <= gy < ROOM_HEIGHT:
                if room_grid[gy][gx] == Tile.SLOW:
                    speed_mult = SLOW_MULTIPLIER

        effective_speed = self.speed * (1.0 + self.speed_bonus)
        if self.has_passive("batch_norm"):
            effective_speed *= 1.15

        old_x, old_y = self.x, self.y

        if self.dodging:
            dodge_spd = DODGE_SPEED
            if self.has_passive("gradient_boost"):
                dodge_spd *= 1.25
            self.x += self.dodge_dx * dodge_spd * speed_mult
            self.y += self.dodge_dy * dodge_spd * speed_mult
            self.dodge_timer -= 1
            if self.dodge_timer <= 0:
                self.dodging = False
                self.dodge_cooldown = DODGE_COOLDOWN
        else:
            if self.move_dx != 0.0 or self.move_dy != 0.0:
                ndx, ndy = normalize(self.move_dx, self.move_dy)
                self.x += ndx * effective_speed * speed_mult
                self.y += ndy * effective_speed * speed_mult

        margin = self.hitbox_radius + 0.5
        self.x = clamp(self.x, margin, ROOM_WIDTH - margin)
        self.y = clamp(self.y, margin, ROOM_HEIGHT - margin)

        # Tile collision (walls, cover — player can pass vents)
        if room_grid is not None:
            self.x, self.y = resolve_tile_collision(
                old_x, old_y, self.x, self.y,
                self.hitbox_radius, room_grid, block_vent=False,
            )

        if self.iframes > 0:
            self.iframes -= 1
        if self.dodge_cooldown > 0:
            self.dodge_cooldown -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.active_item_cooldown > 0:
            self.active_item_cooldown -= 1

    def can_shoot(self) -> bool:
        return self.shoot_cooldown <= 0 and self.shooting and not self.dodging

    def on_shoot(self) -> None:
        cd = self.weapon_info["fire_rate"]
        if self.has_passive("heat_sink"):
            cd = max(1, int(cd * 0.8))
        self.shoot_cooldown = cd

    def set_move(self, dx: float, dy: float) -> None:
        self.move_dx = dx
        self.move_dy = dy

    def set_aim(self, dx: float, dy: float) -> None:
        if dx != 0.0 or dy != 0.0:
            self.aim_dx, self.aim_dy = normalize(dx, dy)

    def reset_for_room(self, x: float, y: float) -> None:
        """Reset transient state when entering a new room."""
        self.x = x
        self.y = y
        self.dodging = False
        self.dodge_timer = 0
        self.dodge_cooldown = 0
        self.iframes = 0
        self.shoot_cooldown = 0
        self.move_dx = 0.0
        self.move_dy = 0.0
