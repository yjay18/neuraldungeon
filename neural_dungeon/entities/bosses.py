"""Boss implementations — 5 unique bosses, one per 2 floors."""
from __future__ import annotations

import math
import random
from neural_dungeon.config import (
    CLASSIFIER_HP, AUTOENCODER_HP, GAN_HP, TRANSFORMER_HP,
    LOSS_FUNCTION_HP, BOSS_FLOORS,
    ROOM_WIDTH, ROOM_HEIGHT,
    ATTENTION_TURN_RATE, TOKEN_DAMAGE,
)
from neural_dungeon.entities.enemies import Enemy
from neural_dungeon.entities.projectiles import Projectile
from neural_dungeon.utils import direction_to, distance, clamp, normalize


class BossEnemy(Enemy):
    """Base class for bosses."""

    def __init__(self, x, y, hp, speed, char, color, name, evolution_level=0):
        super().__init__(x, y, hp=hp, speed=speed, char=char, color=color,
                         hitbox_radius=1.0, evolution_level=evolution_level)
        self.is_boss = True
        self.boss_name = name
        self.phase = 1
        self.tick_counter = 0

    def _check_phase(self):
        ratio = self.hp / self.max_hp
        if ratio <= 0.25:
            self.phase = 3
        elif ratio <= 0.5:
            self.phase = 2
        else:
            self.phase = 1

    def _aimed_shot(self, px, py, speed=0.5, damage=12, color="red"):
        dx, dy = direction_to(self.x, self.y, px, py)
        return Projectile(
            x=self.x, y=self.y, dx=dx, dy=dy,
            speed=speed, damage=damage, owner="enemy",
            char="•", color=color,
        )


class TheClassifier(BossEnemy):
    """Floor 1 boss — fires decision boundary lines of bullets."""

    def __init__(self, x, y, evolution_level=0):
        super().__init__(x, y, hp=CLASSIFIER_HP, speed=0.06,
                         char="◈", color="bright_red",
                         name="The Classifier",
                         evolution_level=evolution_level)
        self.boundary_timer = 60
        self.shoot_timer = 45
        self.boundary_horizontal = True
        self.drift_angle = random.uniform(0, 2 * math.pi)

    def update(self, player_x, player_y, enemies=None,
               player_vx=0.0, player_vy=0.0, player_speed=0.0):
        if not self.alive:
            return []
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            return []

        self._check_phase()
        self.tick_counter += 1
        bullets = []

        # Drift around center
        cx, cy = ROOM_WIDTH / 2, ROOM_HEIGHT / 2
        self.drift_angle += 0.02
        target_x = cx + math.cos(self.drift_angle) * 8
        target_y = cy + math.sin(self.drift_angle) * 4
        dx, dy = direction_to(self.x, self.y, target_x, target_y)
        self.x += dx * self.speed
        self.y += dy * self.speed
        self._clamp_to_room()

        # Decision boundary — line of bullets
        boundary_cd = 35 if self.phase >= 2 else 60
        self.boundary_timer -= 1
        if self.boundary_timer <= 0:
            self.boundary_timer = boundary_cd
            bullets.extend(self._fire_boundary())
            if self.phase >= 2:
                # Fire both directions in phase 2
                self.boundary_horizontal = not self.boundary_horizontal
                bullets.extend(self._fire_boundary())
            self.boundary_horizontal = not self.boundary_horizontal

        # Aimed shot
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = 45
            bullets.append(self._aimed_shot(player_x, player_y))

        return bullets

    def _fire_boundary(self):
        """Fire a line of 10 bullets across the room."""
        bullets = []
        for i in range(10):
            if self.boundary_horizontal:
                bx = (i + 0.5) * (ROOM_WIDTH / 10)
                by = self.y
                bdx, bdy = 0.0, 1.0 if self.y < ROOM_HEIGHT / 2 else -1.0
            else:
                bx = self.x
                by = (i + 0.5) * (ROOM_HEIGHT / 10)
                bdx, bdy = 1.0 if self.x < ROOM_WIDTH / 2 else -1.0, 0.0
            bullets.append(Projectile(
                x=bx, y=by, dx=bdx, dy=bdy,
                speed=0.4, damage=8, owner="enemy",
                char="─" if self.boundary_horizontal else "│",
                color="bright_red",
            ))
        return bullets


class TheAutoencoder(BossEnemy):
    """Floor 3 boss — compressing arena with cover tiles."""

    def __init__(self, x, y, evolution_level=0):
        super().__init__(x, y, hp=AUTOENCODER_HP, speed=0.04,
                         char="◎", color="bright_magenta",
                         name="The Autoencoder",
                         evolution_level=evolution_level)
        self.burst_timer = 90
        self.cover_timer = 120
        self.spawned_covers = []  # (gx, gy) list for cleanup

    def update(self, player_x, player_y, enemies=None,
               player_vx=0.0, player_vy=0.0, player_speed=0.0):
        if not self.alive:
            return []
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            return []

        self._check_phase()
        self.tick_counter += 1
        bullets = []

        # Drift toward center
        cx, cy = ROOM_WIDTH / 2, ROOM_HEIGHT / 2
        if distance(self.x, self.y, cx, cy) > 3:
            dx, dy = direction_to(self.x, self.y, cx, cy)
            self.x += dx * self.speed
            self.y += dy * self.speed

        # Compressed burst
        burst_count = 8 if self.phase >= 2 else 4
        self.burst_timer -= 1
        if self.burst_timer <= 0:
            self.burst_timer = 70 if self.phase >= 2 else 90
            for i in range(burst_count):
                angle = (2 * math.pi / burst_count) * i
                bullets.append(Projectile(
                    x=self.x, y=self.y,
                    dx=math.cos(angle), dy=math.sin(angle),
                    speed=0.35, damage=10, owner="enemy",
                    char="∘", color="bright_magenta",
                ))

        # Aimed shot
        if self.tick_counter % 60 == 0:
            bullets.append(self._aimed_shot(player_x, player_y,
                                            color="magenta"))

        return bullets


class GANGenerator(BossEnemy):
    """GAN Generator half — spawns fake enemies."""

    def __init__(self, x, y, evolution_level=0):
        super().__init__(x, y, hp=GAN_HP, speed=0.05,
                         char="G", color="bright_green",
                         name="The GAN (Generator)",
                         evolution_level=evolution_level)
        self.spawn_timer = 90
        self.partner_alive = True
        self.spawn_queue = []  # fake enemies to add to room

    def update(self, player_x, player_y, enemies=None,
               player_vx=0.0, player_vy=0.0, player_speed=0.0):
        if not self.alive:
            return []
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            return []

        self.tick_counter += 1
        bullets = []

        # Wander away from player
        dist = distance(self.x, self.y, player_x, player_y)
        if dist < 12:
            dx, dy = direction_to(player_x, player_y, self.x, self.y)
            self.x += dx * self.speed
            self.y += dy * self.speed
        self._clamp_to_room()

        # Spawn fake tokens
        cd = 60 if not self.partner_alive else 90
        self.spawn_timer -= 1
        if self.spawn_timer <= 0:
            self.spawn_timer = cd
            self.spawn_queue = self._make_fakes()

        return bullets

    def _make_fakes(self):
        """Create 2 fake Token enemies."""
        fakes = []
        for _ in range(2):
            fake = Enemy(
                x=self.x + random.uniform(-2, 2),
                y=self.y + random.uniform(-2, 2),
                hp=1, speed=0.25, char="?", color="bright_green",
            )
            fake.contact_damage = 5
            fakes.append(fake)
        return fakes


class GANDiscriminator(BossEnemy):
    """GAN Discriminator half — shoots at player."""

    def __init__(self, x, y, evolution_level=0):
        super().__init__(x, y, hp=GAN_HP, speed=0.08,
                         char="D", color="bright_red",
                         name="The GAN (Discriminator)",
                         evolution_level=evolution_level)
        self.shoot_timer = 45
        self.partner_alive = True

    def update(self, player_x, player_y, enemies=None,
               player_vx=0.0, player_vy=0.0, player_speed=0.0):
        if not self.alive:
            return []
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            return []

        self.tick_counter += 1
        bullets = []

        # Chase player at medium range
        dist = distance(self.x, self.y, player_x, player_y)
        dx, dy = direction_to(self.x, self.y, player_x, player_y)
        if dist > 15:
            self.x += dx * self.speed
            self.y += dy * self.speed
        elif dist < 8:
            self.x -= dx * self.speed * 0.5
            self.y -= dy * self.speed * 0.5
        self._clamp_to_room()

        # Aimed shots
        cd = 30 if not self.partner_alive else 45
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = cd
            bullets.append(self._aimed_shot(player_x, player_y,
                                            speed=0.6, damage=10))

        return bullets


class TransformerHead(Enemy):
    """Orbiting attention head for the Transformer boss."""

    def __init__(self, x, y, orbit_index, core, evolution_level=0):
        super().__init__(x, y, hp=30, speed=0.0, char="◎",
                         color="bright_cyan",
                         evolution_level=evolution_level)
        self.orbit_index = orbit_index
        self.core = core
        self.orbit_angle = (2 * math.pi / 4) * orbit_index
        self.orbit_radius = 5.0
        self.shoot_timer = random.randint(30, 60)

    def update(self, player_x, player_y, enemies=None,
               player_vx=0.0, player_vy=0.0, player_speed=0.0):
        if not self.alive:
            return []
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            return []

        bullets = []

        # Orbit around core
        self.orbit_angle += 0.04
        self.x = self.core.x + math.cos(self.orbit_angle) * self.orbit_radius
        self.y = self.core.y + math.sin(self.orbit_angle) * self.orbit_radius
        self.x = clamp(self.x, 1, ROOM_WIDTH - 1)
        self.y = clamp(self.y, 1, ROOM_HEIGHT - 1)

        # Homing shots
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = 60
            dx, dy = direction_to(self.x, self.y, player_x, player_y)
            bullets.append(Projectile(
                x=self.x, y=self.y, dx=dx, dy=dy,
                speed=0.35, damage=10, owner="enemy",
                char="◦", color="bright_cyan",
                homing=True, turn_rate=0.04,
            ))

        return bullets


class TheTransformer(BossEnemy):
    """Floor 7 boss — core with 4 orbiting heads."""

    def __init__(self, x, y, evolution_level=0):
        super().__init__(x, y, hp=TRANSFORMER_HP, speed=0.03,
                         char="★", color="bright_yellow",
                         name="The Transformer",
                         evolution_level=evolution_level)
        self.heads = []  # populated by spawn_boss
        self.shoot_timer = 45
        self.intangible = True  # invulnerable while heads live

    def update(self, player_x, player_y, enemies=None,
               player_vx=0.0, player_vy=0.0, player_speed=0.0):
        if not self.alive:
            return []
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            return []

        self._check_phase()
        self.tick_counter += 1
        bullets = []

        # Check if heads are alive
        heads_alive = sum(1 for h in self.heads if h.alive)
        self.intangible = heads_alive > 0

        # Drift toward center
        cx, cy = ROOM_WIDTH / 2, ROOM_HEIGHT / 2
        if distance(self.x, self.y, cx, cy) > 5:
            dx, dy = direction_to(self.x, self.y, cx, cy)
            self.x += dx * self.speed
            self.y += dy * self.speed

        # Only shoot when exposed
        if not self.intangible:
            cd = 30 if self.phase >= 2 else 45
            self.shoot_timer -= 1
            if self.shoot_timer <= 0:
                self.shoot_timer = cd
                bullets.append(self._aimed_shot(player_x, player_y,
                                                speed=0.55, damage=15,
                                                color="bright_yellow"))

        return bullets


class TheLossFunction(BossEnemy):
    """Floor 9 boss — adapts to player behavior."""

    def __init__(self, x, y, evolution_level=0):
        super().__init__(x, y, hp=LOSS_FUNCTION_HP, speed=0.07,
                         char="∑", color="bright_white",
                         name="The Loss Function",
                         evolution_level=evolution_level)
        self.spiral_timer = 90
        self.shoot_timer = 50
        self.teleport_timer = 120
        self.player_positions = []  # track last 30 positions

    def update(self, player_x, player_y, enemies=None,
               player_vx=0.0, player_vy=0.0, player_speed=0.0):
        if not self.alive:
            return []
        if self.frozen_timer > 0:
            self.frozen_timer -= 1
            return []

        self._check_phase()
        self.tick_counter += 1
        bullets = []

        # Track player movement
        self.player_positions.append((player_x, player_y))
        if len(self.player_positions) > 30:
            self.player_positions.pop(0)

        # Calculate player avg movement
        player_moving = False
        if len(self.player_positions) >= 10:
            x0, y0 = self.player_positions[-10]
            total_dist = distance(x0, y0, player_x, player_y)
            player_moving = total_dist > 3.0

        # Chase at medium range
        dist = distance(self.x, self.y, player_x, player_y)
        dx, dy = direction_to(self.x, self.y, player_x, player_y)
        if dist > 18:
            self.x += dx * self.speed
            self.y += dy * self.speed
        elif dist < 8:
            self.x -= dx * self.speed * 0.5
            self.y -= dy * self.speed * 0.5
        self._clamp_to_room()

        # Adaptive shooting
        self.shoot_timer -= 1
        if self.shoot_timer <= 0:
            self.shoot_timer = 40 if self.phase >= 2 else 50
            if player_moving:
                # Lead shots for moving targets
                from neural_dungeon.utils import lead_shot_direction
                ldx, ldy = lead_shot_direction(
                    self.x, self.y, player_x, player_y,
                    player_vx, player_vy, player_speed,
                    0.5, accuracy=0.8,
                )
                bullets.append(Projectile(
                    x=self.x, y=self.y, dx=ldx, dy=ldy,
                    speed=0.55, damage=12, owner="enemy",
                    char="•", color="bright_white",
                ))
            else:
                # Homing for stationary targets
                bullets.append(Projectile(
                    x=self.x, y=self.y, dx=dx, dy=dy,
                    speed=0.4, damage=10, owner="enemy",
                    char="◦", color="bright_white",
                    homing=True, turn_rate=0.05,
                ))

        # Spiral pattern
        spiral_cd = 60 if self.phase >= 2 else 90
        self.spiral_timer -= 1
        if self.spiral_timer <= 0:
            self.spiral_timer = spiral_cd
            for i in range(8):
                angle = (2 * math.pi / 8) * i + self.tick_counter * 0.1
                bullets.append(Projectile(
                    x=self.x, y=self.y,
                    dx=math.cos(angle), dy=math.sin(angle),
                    speed=0.35, damage=8, owner="enemy",
                    char="∘", color="bright_white",
                ))

        # Phase 3: teleport
        if self.phase >= 3:
            self.teleport_timer -= 1
            if self.teleport_timer <= 0:
                self.teleport_timer = 120
                self.x = random.uniform(5, ROOM_WIDTH - 5)
                self.y = random.uniform(3, ROOM_HEIGHT - 3)

        return bullets


def spawn_boss(floor_index):
    """Spawn boss enemies for the given floor. Returns list of enemies."""
    boss_key = BOSS_FLOORS.get(floor_index)
    if not boss_key:
        return []

    cx, cy = ROOM_WIDTH / 2, ROOM_HEIGHT / 2
    evo = floor_index

    if boss_key == "classifier":
        return [TheClassifier(cx, cy - 5, evolution_level=evo)]

    elif boss_key == "autoencoder":
        return [TheAutoencoder(cx, cy, evolution_level=evo)]

    elif boss_key == "gan":
        gen = GANGenerator(cx - 8, cy, evolution_level=evo)
        disc = GANDiscriminator(cx + 8, cy, evolution_level=evo)
        gen.partner_alive = True
        disc.partner_alive = True
        return [gen, disc]

    elif boss_key == "transformer":
        core = TheTransformer(cx, cy, evolution_level=evo)
        heads = []
        for i in range(4):
            head = TransformerHead(cx, cy, i, core, evolution_level=evo)
            heads.append(head)
        core.heads = heads
        return [core] + heads

    elif boss_key == "loss_function":
        return [TheLossFunction(cx, cy, evolution_level=evo)]

    return []
