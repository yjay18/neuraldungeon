"""Player entity — state, stats, inventory, dodge roll."""
from neural_dungeon.config import (
    PLAYER_MAX_HP, PLAYER_SPEED, PLAYER_HITBOX_RADIUS,
    PLAYER_IFRAMES, DODGE_SPEED, DODGE_DURATION, DODGE_COOLDOWN,
    PLAYER_SHOOT_COOLDOWN, PLAYER_BULLET_SPEED, PLAYER_BULLET_DAMAGE,
    PLAYER_BULLET_RANGE, ROOM_WIDTH, ROOM_HEIGHT,
    DIR_NONE, WEAPON_GRADIENT_BEAM, WEAPONS,
)
from neural_dungeon.utils import clamp, normalize


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

        self.enemies_killed = 0
        self.damage_dealt = 0
        self.damage_taken = 0
        self.rooms_cleared = 0
        self.floors_cleared = 0

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
        self.iframes = PLAYER_IFRAMES
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

    def heal(self, amount: int) -> int:
        """Returns actual healing done."""
        actual = min(amount, self.max_hp - self.hp)
        self.hp += actual
        return actual

    def update(self) -> None:
        if not self.alive:
            return

        if self.dodging:
            self.x += self.dodge_dx * DODGE_SPEED
            self.y += self.dodge_dy * DODGE_SPEED
            self.dodge_timer -= 1
            if self.dodge_timer <= 0:
                self.dodging = False
                self.dodge_cooldown = DODGE_COOLDOWN
        else:
            if self.move_dx != 0.0 or self.move_dy != 0.0:
                ndx, ndy = normalize(self.move_dx, self.move_dy)
                self.x += ndx * self.speed
                self.y += ndy * self.speed

        margin = self.hitbox_radius + 0.5
        self.x = clamp(self.x, margin, ROOM_WIDTH - margin)
        self.y = clamp(self.y, margin, ROOM_HEIGHT - margin)

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
        self.shoot_cooldown = self.weapon_info["fire_rate"]

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
