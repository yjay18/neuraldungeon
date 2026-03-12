"""Helpers, geometry, pathfinding."""
import math
import heapq
from neural_dungeon.config import ROOM_WIDTH, ROOM_HEIGHT


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)


def normalize(dx: float, dy: float) -> tuple[float, float]:
    mag = math.sqrt(dx * dx + dy * dy)
    if mag < 1e-9:
        return (0.0, 0.0)
    return (dx / mag, dy / mag)


def direction_to(x1: float, y1: float, x2: float, y2: float) -> tuple[float, float]:
    return normalize(x2 - x1, y2 - y1)


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def in_bounds(x: float, y: float, margin: float = 0.5) -> bool:
    return margin <= x <= ROOM_WIDTH - margin and margin <= y <= ROOM_HEIGHT - margin


def circles_collide(
    x1: float, y1: float, r1: float,
    x2: float, y2: float, r2: float,
) -> bool:
    return distance(x1, y1, x2, y2) < r1 + r2


def resolve_tile_collision(old_x, old_y, new_x, new_y, radius, grid,
                           block_vent=False):
    """Slide-based tile collision. Returns resolved (x, y).

    Checks 4 cardinal hitbox points against blocking tiles.
    block_vent=True for enemies (they can't pass vents).
    """
    from neural_dungeon.world.room_layouts import Tile

    def _blocked(gx, gy):
        if gx < 0 or gx >= ROOM_WIDTH or gy < 0 or gy >= ROOM_HEIGHT:
            return False
        tile = grid[gy][gx]
        if tile in (Tile.WALL, Tile.COVER):
            return True
        if block_vent and tile == Tile.VENT:
            return True
        return False

    def _any_blocked(px, py):
        """Check 4 cardinal points of hitbox circle."""
        points = [
            (int(px + radius), int(py)),
            (int(px - radius), int(py)),
            (int(px), int(py + radius)),
            (int(px), int(py - radius)),
        ]
        for gx, gy in points:
            if _blocked(gx, gy):
                return True
        return False

    # Try full move
    if not _any_blocked(new_x, new_y):
        return new_x, new_y

    # Try x-only
    if not _any_blocked(new_x, old_y):
        return new_x, old_y

    # Try y-only
    if not _any_blocked(old_x, new_y):
        return old_x, new_y

    # Fully blocked
    return old_x, old_y


def lead_shot_direction(
    shooter_x: float, shooter_y: float,
    target_x: float, target_y: float,
    target_vx: float, target_vy: float,
    target_speed: float,
    bullet_speed: float,
    accuracy: float = 1.0,
) -> tuple[float, float]:
    """Aim ahead of a moving target. Returns (dx, dy) normalized.

    accuracy 0.0 = aim at current pos, 1.0 = perfect prediction.
    """
    base_dx, base_dy = direction_to(shooter_x, shooter_y, target_x, target_y)
    if accuracy < 0.01 or bullet_speed < 0.01:
        return base_dx, base_dy

    dist = distance(shooter_x, shooter_y, target_x, target_y)
    if dist < 0.1:
        return base_dx, base_dy

    # Predict where target will be when bullet arrives
    travel_ticks = min(dist / bullet_speed, 30)
    pred_x = target_x + target_vx * target_speed * travel_ticks
    pred_y = target_y + target_vy * target_speed * travel_ticks

    lead_dx, lead_dy = direction_to(shooter_x, shooter_y, pred_x, pred_y)

    # Lerp between dumb aim and lead aim
    final_dx = base_dx * (1 - accuracy) + lead_dx * accuracy
    final_dy = base_dy * (1 - accuracy) + lead_dy * accuracy
    return normalize(final_dx, final_dy)


def astar(
    start: tuple[int, int],
    goal: tuple[int, int],
    blocked: set[tuple[int, int]],
    width: int = ROOM_WIDTH,
    height: int = ROOM_HEIGHT,
) -> list[tuple[int, int]]:
    """A* pathfinding on a grid. Returns path as list of (x, y) or empty if no path."""
    if start == goal:
        return [start]

    open_set: list[tuple[float, tuple[int, int]]] = [(0.0, start)]
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    g_score: dict[tuple[int, int], float] = {start: 0.0}

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.append(start)
            path.reverse()
            return path

        cx, cy = current
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1),
                       (-1, -1), (1, -1), (-1, 1), (1, 1)]:
            nx, ny = cx + dx, cy + dy
            if not (0 <= nx < width and 0 <= ny < height):
                continue
            if (nx, ny) in blocked:
                continue
            cost = 1.414 if (dx != 0 and dy != 0) else 1.0
            new_g = g_score[current] + cost
            if new_g < g_score.get((nx, ny), float("inf")):
                g_score[(nx, ny)] = new_g
                f = new_g + distance(nx, ny, goal[0], goal[1])
                heapq.heappush(open_set, (f, (nx, ny)))
                came_from[(nx, ny)] = current

    return []
