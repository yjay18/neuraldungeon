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
