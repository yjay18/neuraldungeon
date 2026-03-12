"""Projectile types — bullets, beams, patterns."""
import math
from neural_dungeon.config import ROOM_WIDTH, ROOM_HEIGHT
from neural_dungeon.utils import distance, in_bounds, normalize


class Projectile:
    def __init__(
        self,
        x: float,
        y: float,
        dx: float,
        dy: float,
        speed: float,
        damage: int,
        owner: str,  # "player" or "enemy"
        char: str = "·",
        color: str = "white",
        max_range: float = 50.0,
        piercing: bool = False,
        homing: bool = False,
        turn_rate: float = 0.0,
        lifetime: int = 0,  # 0 = no limit, >0 = ticks until despawn
    ):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.speed = speed
        self.damage = damage
        self.owner = owner
        self.char = char
        self.color = color
        self.max_range = max_range
        self.piercing = piercing
        self.homing = homing
        self.turn_rate = turn_rate
        self.lifetime = lifetime
        self.alive = True
        self.origin_x = x
        self.origin_y = y
        self.hitbox_radius = 0.3
        self.cover_hit = None  # (gx, gy) if bullet hit a cover tile

    @property
    def traveled(self) -> float:
        return distance(self.origin_x, self.origin_y, self.x, self.y)

    def update(self, room_grid=None) -> None:
        if not self.alive:
            return
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

        if self.lifetime > 0:
            self.lifetime -= 1
            if self.lifetime <= 0:
                self.alive = False
                return

        if not in_bounds(self.x, self.y, margin=-0.5) or self.traveled > self.max_range:
            self.alive = False
            return

        # Check tile collision
        if room_grid is not None:
            from neural_dungeon.world.room_layouts import Tile
            gx, gy = int(self.x), int(self.y)
            if 0 <= gx < ROOM_WIDTH and 0 <= gy < ROOM_HEIGHT:
                tile = room_grid[gy][gx]
                if tile == Tile.WALL:
                    self.alive = False
                elif tile == Tile.COVER:
                    if not self.piercing:
                        self.alive = False
                    self.cover_hit = (gx, gy)

    def steer_toward(self, tx: float, ty: float) -> None:
        """Adjust direction toward target by turn_rate radians."""
        if not self.homing or self.turn_rate <= 0:
            return
        # Current angle
        cur_angle = math.atan2(self.dy, self.dx)
        # Desired angle
        target_angle = math.atan2(ty - self.y, tx - self.x)
        # Angle difference, clamped to turn_rate
        diff = target_angle - cur_angle
        # Normalize to [-pi, pi]
        diff = (diff + math.pi) % (2 * math.pi) - math.pi
        if abs(diff) > self.turn_rate:
            diff = self.turn_rate if diff > 0 else -self.turn_rate
        new_angle = cur_angle + diff
        self.dx = math.cos(new_angle)
        self.dy = math.sin(new_angle)

    def kill(self) -> None:
        self.alive = False


class ProjectileManager:
    def __init__(self):
        self.projectiles: list[Projectile] = []

    def spawn(self, proj: Projectile) -> None:
        self.projectiles.append(proj)

    def update(self, player_x: float = 0.0, player_y: float = 0.0,
               room_grid=None) -> list[tuple[int, int, int]]:
        """Update all projectiles. Returns list of (gx, gy, damage) for cover hits."""
        cover_hits = []
        for p in self.projectiles:
            if p.homing and p.owner == "enemy":
                p.steer_toward(player_x, player_y)
            p.update(room_grid)
            if p.cover_hit is not None:
                cover_hits.append((*p.cover_hit, p.damage))
                p.cover_hit = None
        self.projectiles = [p for p in self.projectiles if p.alive]
        return cover_hits

    def get_player_bullets(self) -> list[Projectile]:
        return [p for p in self.projectiles if p.owner == "player"]

    def get_enemy_bullets(self) -> list[Projectile]:
        return [p for p in self.projectiles if p.owner == "enemy"]

    def clear(self) -> None:
        self.projectiles.clear()

    @property
    def count(self) -> int:
        return len(self.projectiles)
