"""Enemy types — base class + all implementations."""
import random
import math
from neural_dungeon.config import (
    PERCEPTRON_HP, PERCEPTRON_SPEED, PERCEPTRON_SHOOT_COOLDOWN,
    PERCEPTRON_BULLET_SPEED, PERCEPTRON_BULLET_DAMAGE, PERCEPTRON_CHAR,
    TOKEN_HP, TOKEN_SPEED, TOKEN_DAMAGE, TOKEN_CHAR,
    BIT_SHIFTER_HP, BIT_SHIFTER_SPEED, BIT_SHIFTER_TELEPORT_CD,
    BIT_SHIFTER_SHOOT_COOLDOWN, BIT_SHIFTER_BULLET_SPEED,
    BIT_SHIFTER_BULLET_DAMAGE, BIT_SHIFTER_CHAR,
    CONVOLVER_HP, CONVOLVER_SPEED, CONVOLVER_SHOOT_COOLDOWN,
    CONVOLVER_BULLET_SPEED, CONVOLVER_BULLET_DAMAGE, CONVOLVER_CHAR,
    DROPOUT_HP, DROPOUT_SPEED, DROPOUT_SHOOT_COOLDOWN,
    DROPOUT_BULLET_SPEED, DROPOUT_BULLET_DAMAGE, DROPOUT_CHAR,
    DROPOUT_INTANGIBLE_CHANCE,
    POOLER_HP, POOLER_SPEED, POOLER_ABSORB_RANGE,
    POOLER_DAMAGE, POOLER_CHAR,
    ATTENTION_HP, ATTENTION_SPEED, ATTENTION_SHOOT_COOLDOWN,
    ATTENTION_BULLET_SPEED, ATTENTION_BULLET_DAMAGE,
    ATTENTION_TURN_RATE, ATTENTION_CHAR,
    GRADIENT_GHOST_HP, GRADIENT_GHOST_SPEED,
    GRADIENT_GHOST_TRAIL_CD, GRADIENT_GHOST_TRAIL_DAMAGE,
    GRADIENT_GHOST_CHAR,
    MIMIC_HP, MIMIC_RECORD_TICKS, MIMIC_SHOOT_COOLDOWN,
    MIMIC_BULLET_SPEED, MIMIC_BULLET_DAMAGE, MIMIC_CHAR,
    RELU_HP, RELU_SPEED_ACTIVE, RELU_SPEED_DORMANT,
    RELU_SHOOT_CD_ACTIVE, RELU_SHOOT_CD_DORMANT,
    RELU_BULLET_SPEED, RELU_BULLET_DAMAGE,
    RELU_ACTIVATION_THRESHOLD, RELU_CHAR,
    ROOM_WIDTH, ROOM_HEIGHT, COLOR_ENEMY_DEFAULT,
)
from neural_dungeon.utils import direction_to, distance, clamp, astar
from neural_dungeon.entities.projectiles import Projectile


class Enemy:
    def __init__(
        self,
        x: float,
        y: float,
        hp: int,
        speed: float,
        char: str,
        color: str = COLOR_ENEMY_DEFAULT,
        hitbox_radius: float = 0.5,
    ):
        self.x = x
        self.y = y
        self.hp = hp
        self.max_hp = hp
        self.speed = speed
        self.char = char
        self.color = color
        self.hitbox_radius = hitbox_radius
        self.alive = True
        self.contact_damage = 0
        self.intangible = False
        self.absorbed = False

    def take_damage(self, amount: int) -> int:
        if not self.alive or self.intangible:
            return 0
        actual = min(amount, self.hp)
        self.hp -= actual
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
        return actual

    def update(self, player_x: float, player_y: float,
               enemies: list | None = None) -> list[Projectile]:
        """Returns list of new projectiles to spawn."""
        return []

    def _clamp_to_room(self) -> None:
        margin = self.hitbox_radius + 0.5
        self.x = clamp(self.x, margin, ROOM_WIDTH - margin)
        self.y = clamp(self.y, margin, ROOM_HEIGHT - margin)


class Perceptron(Enemy):
    """Fires single aimed bullet. Circle-strafes at medium range."""

    def __init__(self, x: float, y: float, hp: int | None = None):
        super().__init__(
            x=x, y=y,
            hp=hp or PERCEPTRON_HP,
            speed=PERCEPTRON_SPEED,
            char=PERCEPTRON_CHAR,
            color="red",
        )
        self.shoot_cooldown = random.randint(0, PERCEPTRON_SHOOT_COOLDOWN)
        self.wander_angle = random.uniform(0, 2 * math.pi)
        self.wander_timer = random.randint(30, 90)

    def update(self, player_x: float, player_y: float,
               enemies: list | None = None) -> list[Projectile]:
        if not self.alive:
            return []

        bullets: list[Projectile] = []
        dist = distance(self.x, self.y, player_x, player_y)

        if dist > 15:
            dx, dy = direction_to(self.x, self.y, player_x, player_y)
            self.x += dx * self.speed
            self.y += dy * self.speed
        elif dist < 5:
            dx, dy = direction_to(self.x, self.y, player_x, player_y)
            self.x -= dx * self.speed
            self.y -= dy * self.speed
        else:
            self.wander_timer -= 1
            if self.wander_timer <= 0:
                self.wander_angle = random.uniform(0, 2 * math.pi)
                self.wander_timer = random.randint(30, 90)
            self.x += math.cos(self.wander_angle) * self.speed * 0.5
            self.y += math.sin(self.wander_angle) * self.speed * 0.5

        self._clamp_to_room()

        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and dist < 30:
            dx, dy = direction_to(self.x, self.y, player_x, player_y)
            bullet = Projectile(
                x=self.x, y=self.y,
                dx=dx, dy=dy,
                speed=PERCEPTRON_BULLET_SPEED,
                damage=PERCEPTRON_BULLET_DAMAGE,
                owner="enemy",
                char="•",
                color="red",
                max_range=35.0,
            )
            bullets.append(bullet)
            self.shoot_cooldown = PERCEPTRON_SHOOT_COOLDOWN + random.randint(-5, 10)

        return bullets


class Token(Enemy):
    """Walks toward player, explodes on contact. Spawns in groups."""

    def __init__(self, x: float, y: float, hp: int | None = None):
        super().__init__(
            x=x, y=y,
            hp=hp or TOKEN_HP,
            speed=TOKEN_SPEED,
            char=TOKEN_CHAR,
            color="yellow",
            hitbox_radius=0.4,
        )
        self.contact_damage = TOKEN_DAMAGE

    def update(self, player_x: float, player_y: float,
               enemies: list | None = None) -> list[Projectile]:
        if not self.alive:
            return []
        dx, dy = direction_to(self.x, self.y, player_x, player_y)
        self.x += dx * self.speed
        self.y += dy * self.speed
        self._clamp_to_room()
        return []


class BitShifter(Enemy):
    """Teleports to random position every few seconds, fires aimed shot."""

    def __init__(self, x: float, y: float, hp: int | None = None):
        super().__init__(
            x=x, y=y,
            hp=hp or BIT_SHIFTER_HP,
            speed=BIT_SHIFTER_SPEED,
            char=BIT_SHIFTER_CHAR,
            color="bright_magenta",
        )
        self.teleport_timer = BIT_SHIFTER_TELEPORT_CD
        self.shoot_cooldown = BIT_SHIFTER_SHOOT_COOLDOWN

    def update(self, player_x: float, player_y: float,
               enemies: list | None = None) -> list[Projectile]:
        if not self.alive:
            return []

        bullets: list[Projectile] = []

        self.teleport_timer -= 1
        if self.teleport_timer <= 0:
            margin = 3.0
            self.x = random.uniform(margin, ROOM_WIDTH - margin)
            self.y = random.uniform(margin, ROOM_HEIGHT - margin)
            self.teleport_timer = BIT_SHIFTER_TELEPORT_CD + random.randint(-10, 10)
            self.shoot_cooldown = BIT_SHIFTER_SHOOT_COOLDOWN

        # Slow drift toward player between teleports
        dx, dy = direction_to(self.x, self.y, player_x, player_y)
        self.x += dx * self.speed
        self.y += dy * self.speed
        self._clamp_to_room()

        self.shoot_cooldown -= 1
        dist = distance(self.x, self.y, player_x, player_y)
        if self.shoot_cooldown <= 0 and dist < 35:
            dx, dy = direction_to(self.x, self.y, player_x, player_y)
            bullet = Projectile(
                x=self.x, y=self.y,
                dx=dx, dy=dy,
                speed=BIT_SHIFTER_BULLET_SPEED,
                damage=BIT_SHIFTER_BULLET_DAMAGE,
                owner="enemy",
                char="⬡",
                color="bright_magenta",
                max_range=40.0,
            )
            bullets.append(bullet)
            self.shoot_cooldown = BIT_SHIFTER_SHOOT_COOLDOWN + random.randint(0, 15)

        return bullets


class Convolver(Enemy):
    """Fires 3x3 grid of bullets periodically. Moves slowly."""

    def __init__(self, x: float, y: float, hp: int | None = None):
        super().__init__(
            x=x, y=y,
            hp=hp or CONVOLVER_HP,
            speed=CONVOLVER_SPEED,
            char=CONVOLVER_CHAR,
            color="bright_blue",
        )
        self.shoot_cooldown = CONVOLVER_SHOOT_COOLDOWN
        self.wander_angle = random.uniform(0, 2 * math.pi)

    def update(self, player_x: float, player_y: float,
               enemies: list | None = None) -> list[Projectile]:
        if not self.alive:
            return []

        bullets: list[Projectile] = []

        # Slow wander
        self.x += math.cos(self.wander_angle) * self.speed
        self.y += math.sin(self.wander_angle) * self.speed
        if random.random() < 0.02:
            self.wander_angle = random.uniform(0, 2 * math.pi)
        self._clamp_to_room()

        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0:
            # Fire 8 bullets in all directions
            directions = [
                (-1, -1), (0, -1), (1, -1),
                (-1, 0),           (1, 0),
                (-1, 1),  (0, 1),  (1, 1),
            ]
            for ddx, ddy in directions:
                mag = math.sqrt(ddx * ddx + ddy * ddy)
                if mag < 0.01:
                    continue
                ndx, ndy = ddx / mag, ddy / mag
                bullet = Projectile(
                    x=self.x, y=self.y,
                    dx=ndx, dy=ndy,
                    speed=CONVOLVER_BULLET_SPEED,
                    damage=CONVOLVER_BULLET_DAMAGE,
                    owner="enemy",
                    char="∘",
                    color="bright_blue",
                    max_range=25.0,
                )
                bullets.append(bullet)
            self.shoot_cooldown = CONVOLVER_SHOOT_COOLDOWN + random.randint(-10, 10)

        return bullets


class DropoutPhantom(Enemy):
    """30% chance to be intangible each tick. Flickers visually."""

    def __init__(self, x: float, y: float, hp: int | None = None):
        super().__init__(
            x=x, y=y,
            hp=hp or DROPOUT_HP,
            speed=DROPOUT_SPEED,
            char=DROPOUT_CHAR,
            color="bright_white",
        )
        self.shoot_cooldown = random.randint(0, DROPOUT_SHOOT_COOLDOWN)

    def update(self, player_x: float, player_y: float,
               enemies: list | None = None) -> list[Projectile]:
        if not self.alive:
            return []

        # Roll intangibility each tick
        self.intangible = random.random() < DROPOUT_INTANGIBLE_CHANCE
        self.color = "bright_black" if self.intangible else "bright_white"

        bullets: list[Projectile] = []
        dist = distance(self.x, self.y, player_x, player_y)

        dx, dy = direction_to(self.x, self.y, player_x, player_y)
        if dist > 12:
            self.x += dx * self.speed
            self.y += dy * self.speed
        elif dist < 6:
            self.x -= dx * self.speed
            self.y -= dy * self.speed
        self._clamp_to_room()

        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and dist < 30:
            dx, dy = direction_to(self.x, self.y, player_x, player_y)
            bullet = Projectile(
                x=self.x, y=self.y,
                dx=dx, dy=dy,
                speed=DROPOUT_BULLET_SPEED,
                damage=DROPOUT_BULLET_DAMAGE,
                owner="enemy",
                char="◇",
                color="white",
                max_range=30.0,
            )
            bullets.append(bullet)
            self.shoot_cooldown = DROPOUT_SHOOT_COOLDOWN + random.randint(-5, 10)

        return bullets


class Pooler(Enemy):
    """Absorbs dead enemies to gain HP. Contact damage."""

    def __init__(self, x: float, y: float, hp: int | None = None):
        super().__init__(
            x=x, y=y,
            hp=hp or POOLER_HP,
            speed=POOLER_SPEED,
            char=POOLER_CHAR,
            color="bright_yellow",
            hitbox_radius=0.6,
        )
        self.contact_damage = POOLER_DAMAGE
        self.absorbed_count = 0

    def update(self, player_x: float, player_y: float,
               enemies: list | None = None) -> list[Projectile]:
        if not self.alive:
            return []

        # Look for dead enemies to absorb
        if enemies:
            nearest_dead = None
            nearest_dist = float("inf")
            for e in enemies:
                if e is self or e.alive or e.absorbed:
                    continue
                d = distance(self.x, self.y, e.x, e.y)
                if d < nearest_dist:
                    nearest_dist = d
                    nearest_dead = e

            if nearest_dead and nearest_dist < POOLER_ABSORB_RANGE:
                nearest_dead.absorbed = True
                self.absorbed_count += 1
                self.hp = min(self.hp + 15, self.max_hp + 50)
                self.max_hp = max(self.max_hp, self.hp)
                self.hitbox_radius = min(0.6 + self.absorbed_count * 0.1, 1.2)
                self.contact_damage += 3
            elif nearest_dead:
                # Move toward dead enemy
                dx, dy = direction_to(
                    self.x, self.y, nearest_dead.x, nearest_dead.y)
                self.x += dx * self.speed * 1.5
                self.y += dy * self.speed * 1.5
                self._clamp_to_room()
                return []

        # Otherwise move toward player
        dx, dy = direction_to(self.x, self.y, player_x, player_y)
        self.x += dx * self.speed
        self.y += dy * self.speed
        self._clamp_to_room()
        return []


class AttentionHead(Enemy):
    """Fires slow homing projectiles that track the player."""

    def __init__(self, x: float, y: float, hp: int | None = None):
        super().__init__(
            x=x, y=y,
            hp=hp or ATTENTION_HP,
            speed=ATTENTION_SPEED,
            char=ATTENTION_CHAR,
            color="bright_cyan",
        )
        self.shoot_cooldown = random.randint(0, ATTENTION_SHOOT_COOLDOWN)

    def update(self, player_x: float, player_y: float,
               enemies: list | None = None) -> list[Projectile]:
        if not self.alive:
            return []

        bullets: list[Projectile] = []
        dist = distance(self.x, self.y, player_x, player_y)

        # Stay at medium range
        dx, dy = direction_to(self.x, self.y, player_x, player_y)
        if dist > 20:
            self.x += dx * self.speed
            self.y += dy * self.speed
        elif dist < 10:
            self.x -= dx * self.speed
            self.y -= dy * self.speed
        self._clamp_to_room()

        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and dist < 35:
            dx, dy = direction_to(self.x, self.y, player_x, player_y)
            bullet = Projectile(
                x=self.x, y=self.y,
                dx=dx, dy=dy,
                speed=ATTENTION_BULLET_SPEED,
                damage=ATTENTION_BULLET_DAMAGE,
                owner="enemy",
                char="◎",
                color="bright_cyan",
                max_range=50.0,
                homing=True,
                turn_rate=ATTENTION_TURN_RATE,
            )
            bullets.append(bullet)
            self.shoot_cooldown = ATTENTION_SHOOT_COOLDOWN + random.randint(-5, 15)

        return bullets


class GradientGhost(Enemy):
    """Uses A* pathfinding. Leaves damaging trail behind."""

    def __init__(self, x: float, y: float, hp: int | None = None):
        super().__init__(
            x=x, y=y,
            hp=hp or GRADIENT_GHOST_HP,
            speed=GRADIENT_GHOST_SPEED,
            char=GRADIENT_GHOST_CHAR,
            color="magenta",
        )
        self.path: list[tuple[int, int]] = []
        self.path_index = 0
        self.repath_timer = 0
        self.trail_timer = GRADIENT_GHOST_TRAIL_CD

    def update(self, player_x: float, player_y: float,
               enemies: list | None = None) -> list[Projectile]:
        if not self.alive:
            return []

        bullets: list[Projectile] = []

        # Recalculate path periodically
        self.repath_timer -= 1
        if self.repath_timer <= 0 or not self.path:
            start = (int(round(self.x)), int(round(self.y)))
            goal = (int(round(player_x)), int(round(player_y)))
            start = (
                max(0, min(start[0], ROOM_WIDTH - 1)),
                max(0, min(start[1], ROOM_HEIGHT - 1)),
            )
            goal = (
                max(0, min(goal[0], ROOM_WIDTH - 1)),
                max(0, min(goal[1], ROOM_HEIGHT - 1)),
            )
            self.path = astar(start, goal, set())
            self.path_index = 0
            self.repath_timer = 30

        # Follow path
        if self.path and self.path_index < len(self.path):
            tx, ty = self.path[self.path_index]
            dx, dy = direction_to(self.x, self.y, tx, ty)
            self.x += dx * self.speed
            self.y += dy * self.speed
            if distance(self.x, self.y, tx, ty) < 0.5:
                self.path_index += 1
        else:
            dx, dy = direction_to(self.x, self.y, player_x, player_y)
            self.x += dx * self.speed
            self.y += dy * self.speed

        self._clamp_to_room()

        # Drop damaging trail
        self.trail_timer -= 1
        if self.trail_timer <= 0:
            trail = Projectile(
                x=self.x, y=self.y,
                dx=0, dy=0,
                speed=0,
                damage=GRADIENT_GHOST_TRAIL_DAMAGE,
                owner="enemy",
                char="·",
                color="magenta",
                max_range=999,
                lifetime=90,  # fades after 3 seconds
            )
            bullets.append(trail)
            self.trail_timer = GRADIENT_GHOST_TRAIL_CD

        return bullets


class OverfittingMimic(Enemy):
    """Records player movement, then replays it. Shoots while replaying."""

    def __init__(self, x: float, y: float, hp: int | None = None):
        super().__init__(
            x=x, y=y,
            hp=hp or MIMIC_HP,
            speed=0.0,
            char=MIMIC_CHAR,
            color="green",
        )
        self.recording = True
        self.record_buffer: list[tuple[float, float]] = []
        self.record_timer = MIMIC_RECORD_TICKS
        self.replay_index = 0
        self.shoot_cooldown = MIMIC_SHOOT_COOLDOWN

    def update(self, player_x: float, player_y: float,
               enemies: list | None = None) -> list[Projectile]:
        if not self.alive:
            return []

        bullets: list[Projectile] = []

        if self.recording:
            self.record_buffer.append((player_x, player_y))
            self.record_timer -= 1
            self.color = "green"

            if self.record_timer <= 0:
                self.recording = False
                self.replay_index = 0
        else:
            self.color = "bright_red"
            if self.replay_index < len(self.record_buffer):
                tx, ty = self.record_buffer[self.replay_index]
                dx, dy = direction_to(self.x, self.y, tx, ty)
                move_speed = 0.3
                self.x += dx * move_speed
                self.y += dy * move_speed
                if distance(self.x, self.y, tx, ty) < 1.0:
                    self.replay_index += 1
            else:
                # Done replaying, record again
                self.recording = True
                self.record_buffer.clear()
                self.record_timer = MIMIC_RECORD_TICKS
                self.replay_index = 0

            # Shoot while replaying
            self.shoot_cooldown -= 1
            dist = distance(self.x, self.y, player_x, player_y)
            if self.shoot_cooldown <= 0 and dist < 30:
                dx, dy = direction_to(self.x, self.y, player_x, player_y)
                bullet = Projectile(
                    x=self.x, y=self.y,
                    dx=dx, dy=dy,
                    speed=MIMIC_BULLET_SPEED,
                    damage=MIMIC_BULLET_DAMAGE,
                    owner="enemy",
                    char="◆",
                    color="bright_red",
                    max_range=30.0,
                )
                bullets.append(bullet)
                self.shoot_cooldown = MIMIC_SHOOT_COOLDOWN

        self._clamp_to_room()
        return bullets


class ReLUGuardian(Enemy):
    """Behavior depends on room activation. Active if >= threshold."""

    def __init__(self, x: float, y: float, activation: float = 0.5,
                 hp: int | None = None):
        is_active = activation >= RELU_ACTIVATION_THRESHOLD
        super().__init__(
            x=x, y=y,
            hp=hp or RELU_HP,
            speed=RELU_SPEED_ACTIVE if is_active else RELU_SPEED_DORMANT,
            char=RELU_CHAR,
            color="bright_green" if is_active else "bright_black",
        )
        self.activation = activation
        self.is_active = is_active
        shoot_cd = RELU_SHOOT_CD_ACTIVE if is_active else RELU_SHOOT_CD_DORMANT
        self.shoot_cooldown = random.randint(0, shoot_cd)

    def update(self, player_x: float, player_y: float,
               enemies: list | None = None) -> list[Projectile]:
        if not self.alive:
            return []

        bullets: list[Projectile] = []
        dist = distance(self.x, self.y, player_x, player_y)

        if self.is_active:
            dx, dy = direction_to(self.x, self.y, player_x, player_y)
            self.x += dx * self.speed
            self.y += dy * self.speed
        else:
            if random.random() < 0.05:
                dx, dy = direction_to(self.x, self.y, player_x, player_y)
                self.x += dx * self.speed
                self.y += dy * self.speed

        self._clamp_to_room()

        shoot_cd = RELU_SHOOT_CD_ACTIVE if self.is_active else RELU_SHOOT_CD_DORMANT
        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and dist < 30:
            dx, dy = direction_to(self.x, self.y, player_x, player_y)
            bullet = Projectile(
                x=self.x, y=self.y,
                dx=dx, dy=dy,
                speed=RELU_BULLET_SPEED,
                damage=RELU_BULLET_DAMAGE,
                owner="enemy",
                char="▷",
                color="bright_green" if self.is_active else "bright_black",
                max_range=30.0,
            )
            bullets.append(bullet)
            self.shoot_cooldown = shoot_cd + random.randint(-5, 10)

        return bullets


# Which enemy types can appear on each floor (cumulative)
FLOOR_ENEMY_POOL = {
    0: ["perceptron", "token"],
    1: ["perceptron", "token", "bit_shifter", "dropout"],
    2: ["perceptron", "token", "bit_shifter", "dropout",
        "convolver", "gradient_ghost"],
    3: ["perceptron", "token", "bit_shifter", "dropout",
        "convolver", "gradient_ghost", "attention", "pooler", "mimic"],
    4: ["perceptron", "token", "bit_shifter", "dropout",
        "convolver", "gradient_ghost", "attention", "pooler",
        "mimic", "relu_guardian"],
}

ENEMY_CLASSES = {
    "perceptron": Perceptron,
    "token": Token,
    "bit_shifter": BitShifter,
    "convolver": Convolver,
    "dropout": DropoutPhantom,
    "pooler": Pooler,
    "attention": AttentionHead,
    "gradient_ghost": GradientGhost,
    "mimic": OverfittingMimic,
    "relu_guardian": ReLUGuardian,
}


def spawn_enemies_for_room(
    room_index: int,
    floor_index: int,
    room_type: str,
    activation: float = 0.5,
) -> list[Enemy]:
    from neural_dungeon.config import (
        ENEMIES_PER_ROOM_BASE, ENEMIES_PER_ROOM_SCALE,
        ROOM_TYPE_COMBAT, ROOM_TYPE_ELITE, ROOM_TYPE_BOSS,
        ROOM_TYPE_DEAD, ROOM_TYPE_SHOP, ROOM_TYPE_START,
    )

    if room_type in (ROOM_TYPE_DEAD, ROOM_TYPE_SHOP, ROOM_TYPE_START):
        return []

    count = int(ENEMIES_PER_ROOM_BASE + floor_index * ENEMIES_PER_ROOM_SCALE)
    if room_type == ROOM_TYPE_ELITE:
        count = int(count * 1.5)
    elif room_type == ROOM_TYPE_BOSS:
        count = max(1, count // 2)

    pool = FLOOR_ENEMY_POOL.get(floor_index, FLOOR_ENEMY_POOL[4])

    enemies: list[Enemy] = []
    margin = 3.0
    for _ in range(count):
        ex = random.uniform(margin, ROOM_WIDTH - margin)
        ey = random.uniform(margin, ROOM_HEIGHT - margin)
        # Avoid spawning on player start position (center bottom)
        while distance(ex, ey, ROOM_WIDTH / 2, ROOM_HEIGHT - 3) < 5.0:
            ex = random.uniform(margin, ROOM_WIDTH - margin)
            ey = random.uniform(margin, ROOM_HEIGHT - margin)

        enemy_key = random.choice(pool)

        if enemy_key == "relu_guardian":
            enemies.append(ReLUGuardian(ex, ey, activation=activation))
        else:
            cls = ENEMY_CLASSES[enemy_key]
            enemies.append(cls(ex, ey))

    return enemies
