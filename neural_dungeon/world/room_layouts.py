"""
Room Layout System — tile-based obstacles for rooms.
Each layout is a 60x25 grid of tile IDs.

Tile types:
  0 = FLOOR (walkable)
  1 = WALL (blocks movement + bullets)
  2 = COVER (blocks bullets, destructible)
  3 = PIT (damage zone, enemies avoid)
  4 = SLOW (movement penalty zone)
  5 = VENT (only player can pass)
"""
import math
import random
from enum import IntEnum

from neural_dungeon.config import ROOM_WIDTH, ROOM_HEIGHT

ROOM_W = ROOM_WIDTH
ROOM_H = ROOM_HEIGHT

MARGIN_X = 3
MARGIN_Y = 2

DOOR_TOP = (ROOM_W // 2, 0)
DOOR_BOTTOM = (ROOM_W // 2, ROOM_H - 1)
DOOR_LEFT = (0, ROOM_H // 2)
DOOR_RIGHT = (ROOM_W - 1, ROOM_H // 2)
DOOR_CLEARANCE = 3


class Tile(IntEnum):
    FLOOR = 0
    WALL = 1
    COVER = 2
    PIT = 3
    SLOW = 4
    VENT = 5


class Obstacle:
    def __init__(self, name, tiles):
        self.name = name
        self.tiles = tiles  # list of (dx, dy, tile_type)

    def width(self):
        return max(dx for dx, dy, t in self.tiles) + 1

    def height(self):
        return max(dy for dx, dy, t in self.tiles) + 1


# === CYBER THEME PREFABS ===

def server_rack(orientation="h"):
    if orientation == "h":
        return Obstacle("server_rack", [
            (dx, dy, Tile.COVER) for dx in range(3) for dy in range(2)
        ])
    return Obstacle("server_rack", [
        (dx, dy, Tile.COVER) for dx in range(2) for dy in range(3)
    ])


def data_pillar():
    return Obstacle("data_pillar", [(0, 0, Tile.WALL)])


def circuit_wall(length, direction="h"):
    if direction == "h":
        return Obstacle("circuit_wall",
                         [(i, 0, Tile.WALL) for i in range(length)])
    return Obstacle("circuit_wall",
                     [(0, i, Tile.WALL) for i in range(length)])


def firewall_row(length, gap_pos, gap_size=3):
    tiles = []
    for i in range(length):
        if gap_pos <= i < gap_pos + gap_size:
            continue
        tiles.append((i, 0, Tile.PIT))
    return Obstacle("firewall", tiles)


def firewall_col(length, gap_pos, gap_size=3):
    tiles = []
    for i in range(length):
        if gap_pos <= i < gap_pos + gap_size:
            continue
        tiles.append((0, i, Tile.PIT))
    return Obstacle("firewall", tiles)


def terminal_station():
    return Obstacle("terminal", [
        (dx, dy, Tile.COVER) for dx in range(2) for dy in range(2)
    ])


def neon_pad(w, h):
    return Obstacle("neon_pad", [
        (dx, dy, Tile.SLOW) for dx in range(w) for dy in range(h)
    ])


def vent_shaft(direction="h"):
    if direction == "h":
        return Obstacle("vent", [(0, 0, Tile.VENT), (1, 0, Tile.VENT)])
    return Obstacle("vent", [(0, 0, Tile.VENT), (0, 1, Tile.VENT)])


# === GRID HELPERS ===

def empty_grid():
    return [[Tile.FLOOR] * ROOM_W for _ in range(ROOM_H)]


def place_obstacle(grid, obstacle, ox, oy):
    for dx, dy, tile in obstacle.tiles:
        gx, gy = ox + dx, oy + dy
        if gx < 0 or gx >= ROOM_W or gy < 0 or gy >= ROOM_H:
            return False
        if grid[gy][gx] != Tile.FLOOR:
            return False
        for door in [DOOR_TOP, DOOR_BOTTOM, DOOR_LEFT, DOOR_RIGHT]:
            if (abs(gx - door[0]) <= DOOR_CLEARANCE
                    and abs(gy - door[1]) <= DOOR_CLEARANCE):
                return False
    for dx, dy, tile in obstacle.tiles:
        grid[oy + dy][ox + dx] = tile
    return True


def is_walkable(tile):
    return tile in (Tile.FLOOR, Tile.SLOW, Tile.VENT)


def is_blocking(tile):
    return tile in (Tile.WALL, Tile.COVER)


# === LAYOUT TEMPLATES ===

def layout_open_arena(difficulty=0.5):
    grid = empty_grid()
    rack_count = 4 + int(difficulty * 3)
    for _ in range(rack_count):
        for _attempt in range(20):
            x = random.randint(MARGIN_X, ROOM_W - MARGIN_X - 3)
            y = random.randint(MARGIN_Y, ROOM_H - MARGIN_Y - 2)
            orient = random.choice(["h", "v"])
            if place_obstacle(grid, server_rack(orient), x, y):
                break
    pillar_count = 4 + int(difficulty * 4)
    for _ in range(pillar_count):
        for _attempt in range(20):
            x = random.randint(MARGIN_X, ROOM_W - MARGIN_X - 1)
            y = random.randint(MARGIN_Y, ROOM_H - MARGIN_Y - 1)
            if place_obstacle(grid, data_pillar(), x, y):
                break
    return grid


def layout_four_pillars():
    grid = empty_grid()
    cx, cy = ROOM_W // 2, ROOM_H // 2
    positions = [
        (cx - 12, cy - 5), (cx + 10, cy - 5),
        (cx - 12, cy + 3), (cx + 10, cy + 3),
    ]
    for px, py in positions:
        for dx in range(2):
            for dy in range(2):
                place_obstacle(grid, data_pillar(), px + dx, py + dy)
        place_obstacle(grid, server_rack("h"), px + 3, py)
    place_obstacle(grid, terminal_station(), cx - 1, cy - 1)
    return grid


def layout_corridors():
    grid = empty_grid()
    wall_ys = [6, 12, 18]
    for wy in wall_ys:
        place_obstacle(grid, circuit_wall(20, "h"), MARGIN_X, wy)
        place_obstacle(grid, circuit_wall(20, "h"), MARGIN_X + 25, wy)
    place_obstacle(grid, circuit_wall(4, "v"), 15, 7)
    place_obstacle(grid, circuit_wall(4, "v"), 44, 7)
    place_obstacle(grid, circuit_wall(4, "v"), 15, 14)
    place_obstacle(grid, circuit_wall(4, "v"), 44, 14)
    for y_lane in [3, 9, 15, 21]:
        place_obstacle(grid, server_rack("h"), 10, y_lane)
        place_obstacle(grid, server_rack("h"), 35, y_lane)
    return grid


def layout_center_fortress():
    grid = empty_grid()
    cx, cy = ROOM_W // 2, ROOM_H // 2
    place_obstacle(grid, circuit_wall(12, "h"), cx - 6, cy - 4)
    place_obstacle(grid, circuit_wall(12, "h"), cx - 6, cy + 4)
    place_obstacle(grid, circuit_wall(3, "v"), cx - 7, cy - 4)
    place_obstacle(grid, circuit_wall(3, "v"), cx - 7, cy + 2)
    place_obstacle(grid, circuit_wall(3, "v"), cx + 6, cy - 4)
    place_obstacle(grid, circuit_wall(3, "v"), cx + 6, cy + 2)
    place_obstacle(grid, terminal_station(), cx - 1, cy - 1)
    for pos in [(cx - 18, cy - 3), (cx + 16, cy - 3),
                (cx - 18, cy + 2), (cx + 16, cy + 2)]:
        place_obstacle(grid, server_rack("v"), pos[0], pos[1])
    return grid


def layout_firewall_gauntlet():
    grid = empty_grid()
    fw_xs = [15, 30, 45]
    for fx in fw_xs:
        gap = random.randint(5, ROOM_H - 8)
        for y in range(MARGIN_Y, ROOM_H - MARGIN_Y):
            if gap <= y < gap + 4:
                continue
            if 0 <= y < ROOM_H and 0 <= fx < ROOM_W:
                grid[y][fx] = Tile.PIT
                if fx + 1 < ROOM_W:
                    grid[y][fx + 1] = Tile.PIT
    place_obstacle(grid, server_rack("v"), 8, 5)
    place_obstacle(grid, server_rack("v"), 8, 16)
    place_obstacle(grid, server_rack("v"), 22, 8)
    place_obstacle(grid, server_rack("v"), 22, 14)
    place_obstacle(grid, server_rack("v"), 37, 5)
    place_obstacle(grid, server_rack("v"), 37, 16)
    place_obstacle(grid, server_rack("v"), 52, 8)
    place_obstacle(grid, server_rack("v"), 52, 14)
    return grid


def layout_cross_maze():
    grid = empty_grid()
    cx, cy = ROOM_W // 2, ROOM_H // 2
    for x in range(MARGIN_X + 5, cx - 3):
        grid[cy][x] = Tile.WALL
    for x in range(cx + 3, ROOM_W - MARGIN_X - 5):
        grid[cy][x] = Tile.WALL
    for y in range(MARGIN_Y + 2, cy - 2):
        grid[y][cx] = Tile.WALL
    for y in range(cy + 2, ROOM_H - MARGIN_Y - 2):
        grid[y][cx] = Tile.WALL
    quadrant_centers = [
        (cx - 14, cy - 6), (cx + 14, cy - 6),
        (cx - 14, cy + 6), (cx + 14, cy + 6),
    ]
    for qx, qy in quadrant_centers:
        place_obstacle(grid, terminal_station(), qx, qy)
        place_obstacle(grid, data_pillar(), qx - 3, qy + 1)
        place_obstacle(grid, data_pillar(), qx + 3, qy - 1)
    return grid


def layout_pillar_grid():
    grid = empty_grid()
    start_x = 8
    start_y = 4
    spacing_x = 8
    spacing_y = 6
    for col in range(7):
        for row in range(3):
            px = start_x + col * spacing_x
            py = start_y + row * spacing_y
            if (MARGIN_X <= px < ROOM_W - MARGIN_X
                    and MARGIN_Y <= py < ROOM_H - MARGIN_Y):
                place_obstacle(grid, data_pillar(), px, py)
                if (col + row) % 3 == 0:
                    place_obstacle(grid, data_pillar(), px + 1, py)
    return grid


def layout_ring_arena():
    grid = empty_grid()
    cx, cy = ROOM_W // 2, ROOM_H // 2
    rx, ry = 12, 6
    for angle_step in range(72):
        a = angle_step * (2 * math.pi / 72)
        x = int(cx + rx * math.cos(a))
        y = int(cy + ry * math.sin(a))
        if (MARGIN_X < x < ROOM_W - MARGIN_X
                and MARGIN_Y < y < ROOM_H - MARGIN_Y):
            grid[y][x] = Tile.WALL
    # Carve 4 openings
    for dx in range(-2, 3):
        if 0 <= cy - ry < ROOM_H and 0 <= cx + dx < ROOM_W:
            grid[cy - ry][cx + dx] = Tile.FLOOR
        if 0 <= cy + ry < ROOM_H and 0 <= cx + dx < ROOM_W:
            grid[cy + ry][cx + dx] = Tile.FLOOR
    for dy in range(-1, 2):
        if 0 <= cy + dy < ROOM_H and 0 <= cx - rx < ROOM_W:
            grid[cy + dy][cx - rx] = Tile.FLOOR
        if 0 <= cy + dy < ROOM_H and 0 <= cx + rx < ROOM_W:
            grid[cy + dy][cx + rx] = Tile.FLOOR
    place_obstacle(grid, terminal_station(), cx - 1, cy - 1)
    for pos in [(cx - 20, cy), (cx + 19, cy),
                (cx, cy - 10), (cx, cy + 9)]:
        if (MARGIN_X <= pos[0] < ROOM_W - MARGIN_X
                and MARGIN_Y <= pos[1] < ROOM_H - MARGIN_Y):
            place_obstacle(grid, server_rack("h"), pos[0], pos[1])
    return grid


def layout_zigzag_walls():
    grid = empty_grid()
    stubs = [
        ("left", 5, 18), ("right", 9, 18),
        ("left", 13, 18), ("right", 17, 18),
        ("left", 21, 18),
    ]
    for side, y, length in stubs:
        if y >= ROOM_H - MARGIN_Y:
            continue
        if side == "left":
            place_obstacle(grid, circuit_wall(length, "h"), MARGIN_X, y)
        else:
            place_obstacle(grid, circuit_wall(length, "h"),
                           ROOM_W - MARGIN_X - length, y)
    place_obstacle(grid, server_rack("v"), ROOM_W - 10, 3)
    place_obstacle(grid, server_rack("v"), 8, 7)
    place_obstacle(grid, server_rack("v"), ROOM_W - 10, 11)
    place_obstacle(grid, server_rack("v"), 8, 15)
    place_obstacle(grid, server_rack("v"), ROOM_W - 10, 19)
    return grid


def layout_neon_pits():
    grid = empty_grid()
    neon_positions = [
        (6, 3, 8, 4), (46, 3, 8, 4),
        (6, 18, 8, 4), (46, 18, 8, 4),
        (26, 10, 8, 5),
    ]
    for nx, ny, nw, nh in neon_positions:
        for dx in range(nw):
            for dy in range(nh):
                gx, gy = nx + dx, ny + dy
                if 0 <= gx < ROOM_W and 0 <= gy < ROOM_H:
                    grid[gy][gx] = Tile.SLOW
    for x in range(18, 22):
        for y in range(5, 20):
            if grid[y][x] == Tile.FLOOR:
                grid[y][x] = Tile.PIT
    for x in range(38, 42):
        for y in range(5, 20):
            if grid[y][x] == Tile.FLOOR:
                grid[y][x] = Tile.PIT
    place_obstacle(grid, data_pillar(), 15, 12)
    place_obstacle(grid, data_pillar(), 44, 12)
    place_obstacle(grid, data_pillar(), 30, 6)
    place_obstacle(grid, data_pillar(), 30, 18)
    return grid


# === COMPLEX LAYOUTS (floors 5-9) ===

def layout_data_maze():
    """Dense maze of 2-tile-wide corridors with VENT shortcuts."""
    grid = empty_grid()
    # Fill interior with walls, then carve corridors
    for y in range(MARGIN_Y, ROOM_H - MARGIN_Y):
        for x in range(MARGIN_X, ROOM_W - MARGIN_X):
            grid[y][x] = Tile.WALL

    # Carve horizontal corridors
    corridor_ys = [4, 8, 12, 16, 20]
    for cy in corridor_ys:
        for x in range(MARGIN_X, ROOM_W - MARGIN_X):
            if 0 <= cy < ROOM_H:
                grid[cy][x] = Tile.FLOOR
            if 0 <= cy + 1 < ROOM_H:
                grid[cy + 1][x] = Tile.FLOOR

    # Carve vertical connectors between corridors
    connector_xs = [8, 18, 28, 38, 48]
    for cx in connector_xs:
        for y in range(MARGIN_Y, ROOM_H - MARGIN_Y):
            if 0 <= cx < ROOM_W:
                grid[y][cx] = Tile.FLOOR
            if 0 <= cx + 1 < ROOM_W:
                grid[y][cx + 1] = Tile.FLOOR

    # Add VENT shortcuts through some walls (player-only passages)
    vent_positions = [(13, 6), (23, 10), (33, 14), (43, 18)]
    for vx, vy in vent_positions:
        if 0 <= vx < ROOM_W and 0 <= vy < ROOM_H:
            grid[vy][vx] = Tile.VENT
        if 0 <= vx + 1 < ROOM_W and 0 <= vy < ROOM_H:
            grid[vy][vx + 1] = Tile.VENT

    # COVER at some intersections
    for cx in connector_xs[::2]:
        for cy in corridor_ys[::2]:
            if (0 <= cx - 1 < ROOM_W and 0 <= cy < ROOM_H
                    and grid[cy][cx - 1] == Tile.FLOOR):
                grid[cy][cx - 1] = Tile.COVER

    # Clear door areas
    _clear_doors(grid)
    return grid


def layout_server_farm():
    """Parallel server rack lanes with PIT borders between them."""
    grid = empty_grid()
    # 5 horizontal lanes separated by PIT rows
    lane_ys = [3, 8, 13, 18]
    lane_height = 3

    for lane_y in lane_ys:
        # PIT border above each lane
        pit_y = lane_y - 1
        if MARGIN_Y <= pit_y < ROOM_H - MARGIN_Y:
            for x in range(MARGIN_X, ROOM_W - MARGIN_X):
                grid[pit_y][x] = Tile.PIT

        # Gaps in PIT to cross lanes (2 gaps per border)
        gap_xs = [15, 44]
        if MARGIN_Y <= pit_y < ROOM_H - MARGIN_Y:
            for gx in gap_xs:
                for dx in range(3):
                    if 0 <= gx + dx < ROOM_W:
                        grid[pit_y][gx + dx] = Tile.FLOOR

    # SLOW zones at lane gap entrances
    for gx in [15, 44]:
        for lane_y in lane_ys:
            for dx in range(3):
                if (0 <= gx + dx < ROOM_W
                        and 0 <= lane_y < ROOM_H
                        and grid[lane_y][gx + dx] == Tile.FLOOR):
                    grid[lane_y][gx + dx] = Tile.SLOW

    # Server racks inside lanes
    for lane_y in lane_ys:
        for rack_x in [6, 22, 34, 50]:
            for dy in range(min(2, lane_height)):
                if 0 <= lane_y + dy < ROOM_H:
                    place_obstacle(grid, server_rack("h"), rack_x, lane_y + dy)

    _clear_doors(grid)
    return grid


def layout_firewall_matrix():
    """Grid of PIT squares with corridors between them."""
    grid = empty_grid()
    # 3x3 PIT squares arranged in a grid pattern
    pit_positions = [
        (7, 3), (22, 3), (37, 3), (52, 3),
        (7, 10), (22, 10), (37, 10), (52, 10),
        (7, 17), (22, 17), (37, 17), (52, 17),
    ]
    pit_size = 3

    for px, py in pit_positions:
        for dx in range(pit_size):
            for dy in range(pit_size):
                gx, gy = px + dx, py + dy
                if 0 <= gx < ROOM_W and 0 <= gy < ROOM_H:
                    grid[gy][gx] = Tile.PIT

    # COVER pillars at corridor intersections
    cover_positions = [
        (14, 7), (29, 7), (44, 7),
        (14, 14), (29, 14), (44, 14),
    ]
    for cx, cy in cover_positions:
        if 0 <= cx < ROOM_W and 0 <= cy < ROOM_H:
            grid[cy][cx] = Tile.COVER
        if 0 <= cx + 1 < ROOM_W and 0 <= cy < ROOM_H:
            grid[cy][cx + 1] = Tile.COVER

    _clear_doors(grid)
    return grid


def layout_neural_web():
    """Spokes radiating from center with VENT connections and PIT ring."""
    grid = empty_grid()
    cx, cy = ROOM_W // 2, ROOM_H // 2

    # 6 WALL spokes from center
    spoke_angles = [0, math.pi / 3, 2 * math.pi / 3,
                    math.pi, 4 * math.pi / 3, 5 * math.pi / 3]
    for angle in spoke_angles:
        for r in range(3, 15):
            sx = int(cx + r * math.cos(angle) * 1.5)
            sy = int(cy + r * math.sin(angle))
            if (MARGIN_X < sx < ROOM_W - MARGIN_X
                    and MARGIN_Y < sy < ROOM_H - MARGIN_Y):
                grid[sy][sx] = Tile.WALL

    # PIT ring around outer edge
    for angle_step in range(60):
        a = angle_step * (2 * math.pi / 60)
        rx = int(cx + 22 * math.cos(a))
        ry = int(cy + 9 * math.sin(a))
        if 1 <= rx < ROOM_W - 1 and 1 <= ry < ROOM_H - 1:
            grid[ry][rx] = Tile.PIT

    # SLOW zone at center hub
    for dx in range(-2, 3):
        for dy in range(-1, 2):
            gx, gy = cx + dx, cy + dy
            if 0 <= gx < ROOM_W and 0 <= gy < ROOM_H:
                grid[gy][gx] = Tile.SLOW

    # VENT connections between spokes
    vent_angles = [math.pi / 6, math.pi / 2, 5 * math.pi / 6,
                   7 * math.pi / 6, 3 * math.pi / 2, 11 * math.pi / 6]
    for angle in vent_angles:
        vx = int(cx + 8 * math.cos(angle) * 1.5)
        vy = int(cy + 8 * math.sin(angle))
        if (MARGIN_X < vx < ROOM_W - MARGIN_X
                and MARGIN_Y < vy < ROOM_H - MARGIN_Y
                and grid[vy][vx] == Tile.WALL):
            grid[vy][vx] = Tile.VENT

    _clear_doors(grid)
    return grid


def layout_cascade_gauntlet():
    """Diagonal barriers with offset gaps forcing S-curve movement."""
    grid = empty_grid()

    # 3 diagonal barriers from top-left to bottom-right
    barrier_starts = [(10, 2), (25, 2), (40, 2)]
    gap_offsets = [6, 14, 8]  # where the gap is in each barrier

    for idx, (bx, by) in enumerate(barrier_starts):
        gap_y = gap_offsets[idx]
        for step in range(ROOM_H - 4):
            wx = bx + step // 2
            wy = by + step
            if wy >= ROOM_H - MARGIN_Y:
                break
            if abs(step - gap_y) < 2:
                # Gap — add SLOW here
                if 0 <= wx < ROOM_W and 0 <= wy < ROOM_H:
                    grid[wy][wx] = Tile.SLOW
                continue
            if 0 <= wx < ROOM_W and 0 <= wy < ROOM_H:
                grid[wy][wx] = Tile.WALL
            if 0 <= wx + 1 < ROOM_W and 0 <= wy < ROOM_H:
                grid[wy][wx + 1] = Tile.WALL

    # PIT zones behind barriers (narrow strips)
    for bx, _ in barrier_starts:
        pit_x = bx - 2
        for y in range(4, ROOM_H - 4):
            if 0 <= pit_x < ROOM_W and grid[y][pit_x] == Tile.FLOOR:
                grid[y][pit_x] = Tile.PIT

    # COVER stepping stones through dangerous areas
    cover_spots = [(8, 6), (20, 10), (35, 8), (50, 14),
                   (15, 16), (32, 18), (45, 6)]
    for sx, sy in cover_spots:
        if 0 <= sx < ROOM_W and 0 <= sy < ROOM_H:
            grid[sy][sx] = Tile.COVER

    _clear_doors(grid)
    return grid


def _clear_doors(grid):
    """Ensure door areas are always walkable."""
    doors = [DOOR_TOP, DOOR_BOTTOM, DOOR_LEFT, DOOR_RIGHT]
    for dx_door, dy_door in doors:
        for dx in range(-DOOR_CLEARANCE, DOOR_CLEARANCE + 1):
            for dy in range(-DOOR_CLEARANCE, DOOR_CLEARANCE + 1):
                gx, gy = dx_door + dx, dy_door + dy
                if 0 <= gx < ROOM_W and 0 <= gy < ROOM_H:
                    if grid[gy][gx] != Tile.FLOOR:
                        grid[gy][gx] = Tile.FLOOR


# === LAYOUT REGISTRY ===

CYBER_LAYOUTS = {
    "open_arena": (layout_open_arena, 0, 9, ["neuron", "high_activation"]),
    "four_pillars": (layout_four_pillars, 0, 9, ["neuron"]),
    "corridors": (layout_corridors, 0, 9, ["neuron", "high_activation"]),
    "center_fortress": (layout_center_fortress, 1, 9, ["high_activation"]),
    "firewall_gauntlet": (layout_firewall_gauntlet, 1, 9,
                          ["high_activation"]),
    "cross_maze": (layout_cross_maze, 0, 9, ["neuron"]),
    "pillar_grid": (layout_pillar_grid, 0, 9, ["neuron"]),
    "ring_arena": (layout_ring_arena, 1, 9, ["high_activation", "boss"]),
    "zigzag_walls": (layout_zigzag_walls, 0, 9, ["neuron"]),
    "neon_pits": (layout_neon_pits, 1, 9, ["high_activation"]),
    # Complex layouts (floors 5-9)
    "data_maze": (layout_data_maze, 5, 9, ["neuron", "high_activation"]),
    "server_farm": (layout_server_farm, 5, 9, ["neuron"]),
    "firewall_matrix": (layout_firewall_matrix, 6, 9, ["high_activation"]),
    "neural_web": (layout_neural_web, 7, 9, ["high_activation", "boss"]),
    "cascade_gauntlet": (layout_cascade_gauntlet, 8, 9,
                         ["high_activation"]),
}

# Map game room types to layout room types
_GAME_TYPE_MAP = {
    "combat": "neuron",
    "elite": "high_activation",
    "dead": "dead_neuron",
    "shop": "memory_bank",
    "weight": "weight_room",
    "boss": "boss",
    "checkpoint": "neuron",
    "start": "dead_neuron",
}


def get_layout_for_room(floor_index, room_type, seed=None):
    """Select and generate a layout for the given floor and room type."""
    if seed is not None:
        random.seed(seed)

    # Map game room type to layout room type
    layout_type = _GAME_TYPE_MAP.get(room_type, room_type)

    if layout_type == "dead_neuron":
        return empty_grid()
    if layout_type == "memory_bank":
        return _shop_layout()
    if layout_type == "weight_room":
        return _weight_room_layout()

    candidates = []
    for name, (gen_fn, min_f, max_f, types) in CYBER_LAYOUTS.items():
        if min_f <= floor_index <= max_f and layout_type in types:
            candidates.append(gen_fn)

    if not candidates:
        candidates = [layout_open_arena]

    chosen = random.choice(candidates)

    if layout_type == "high_activation":
        if chosen == layout_open_arena:
            return chosen(difficulty=0.8)
        return chosen()
    else:
        if chosen == layout_open_arena:
            return chosen(difficulty=0.3 + floor_index * 0.15)
        return chosen()


def _shop_layout():
    grid = empty_grid()
    cx, cy = ROOM_W // 2, ROOM_H // 2
    place_obstacle(grid, server_rack("h"), cx - 10, cy - 3)
    place_obstacle(grid, server_rack("h"), cx + 7, cy - 3)
    place_obstacle(grid, server_rack("h"), cx - 10, cy + 2)
    place_obstacle(grid, server_rack("h"), cx + 7, cy + 2)
    place_obstacle(grid, terminal_station(), cx - 1, cy - 1)
    return grid


def _weight_room_layout():
    grid = empty_grid()
    cx, cy = ROOM_W // 2, ROOM_H // 2
    place_obstacle(grid, terminal_station(), cx - 1, cy - 1)
    for i in range(8):
        a = i * (2 * math.pi / 8)
        px = int(cx + 8 * math.cos(a))
        py = int(cy + 4 * math.sin(a))
        if (MARGIN_X < px < ROOM_W - MARGIN_X
                and MARGIN_Y < py < ROOM_H - MARGIN_Y):
            place_obstacle(grid, data_pillar(), px, py)
    return grid


# === SPAWN HELPERS ===

def get_valid_spawn_positions(grid, count, avoid_center=False,
                              min_dist_from_doors=5,
                              player_pos=None, min_dist_from_player=8):
    candidates = []
    cx, cy = ROOM_W / 2, ROOM_H / 2
    for y in range(ROOM_H):
        for x in range(ROOM_W):
            if grid[y][x] != Tile.FLOOR:
                continue
            too_close = False
            for door in [DOOR_TOP, DOOR_BOTTOM, DOOR_LEFT, DOOR_RIGHT]:
                if abs(x - door[0]) + abs(y - door[1]) < min_dist_from_doors:
                    too_close = True
                    break
            if too_close:
                continue
            if avoid_center and abs(x - cx) < 8 and abs(y - cy) < 4:
                continue
            # Keep enemies away from player start
            if player_pos is not None:
                px, py = player_pos
                dist = math.sqrt((x + 0.5 - px) ** 2 + (y + 0.5 - py) ** 2)
                if dist < min_dist_from_player:
                    continue
            candidates.append((float(x) + 0.5, float(y) + 0.5))
    random.shuffle(candidates)
    return candidates[:count]


def get_player_spawn(grid):
    cx = ROOM_W / 2
    for y in range(ROOM_H - 3, ROOM_H // 2, -1):
        for dx in range(-2, 3):
            x = int(cx) + dx
            if 0 <= x < ROOM_W and 0 <= y < ROOM_H:
                if grid[y][x] == Tile.FLOOR:
                    return (float(x) + 0.5, float(y) + 0.5)
    return (cx, ROOM_H - 3.0)


# === PATHFINDING / COLLISION INTEGRATION ===

def get_blocked_set(grid):
    blocked = set()
    for y in range(ROOM_H):
        for x in range(ROOM_W):
            if is_blocking(grid[y][x]) or grid[y][x] == Tile.PIT:
                blocked.add((x, y))
    return blocked


def grid_to_collision_rects(grid):
    rects = []
    visited = set()
    for y in range(ROOM_H):
        for x in range(ROOM_W):
            if (x, y) in visited:
                continue
            tile = grid[y][x]
            if not is_blocking(tile):
                continue
            max_w = 1
            while (x + max_w < ROOM_W
                   and grid[y][x + max_w] == tile
                   and (x + max_w, y) not in visited):
                max_w += 1
            max_h = 1
            expanding = True
            while expanding and y + max_h < ROOM_H:
                for dx in range(max_w):
                    if (grid[y + max_h][x + dx] != tile
                            or (x + dx, y + max_h) in visited):
                        expanding = False
                        break
                if expanding:
                    max_h += 1
            for dy in range(max_h):
                for dx in range(max_w):
                    visited.add((x + dx, y + dy))
            rects.append((float(x), float(y), float(max_w), float(max_h)))
    return rects
