"""The Lanes — Zone 1 map data (80x75 tiles), built region by region."""
from neural_dungeon.colony.config import (
    MAP_COLS, MAP_ROWS,
    TILE_GROUND, TILE_GRASS, TILE_WALL, TILE_ROOF,
    TILE_TREE_TRUNK, TILE_FENCE, TILE_WATER, TILE_PATH,
    TILE_DOOR, TILE_TALL_GRASS, TILE_SIGN, TILE_FLOWER,
    TILE_PAVED, OVERLAY_NONE, OVERLAY_CANOPY,
)


def _fill(layer, r0, r1, c0, c1, val):
    """Fill a rectangle [r0..r1) x [c0..c1) with val."""
    for r in range(max(0, r0), min(MAP_ROWS, r1)):
        for c in range(max(0, c0), min(MAP_COLS, c1)):
            layer[r][c] = val


def _place_building(base, overlay, r0, c0, w, h, door_offset=None):
    """Place a single building: roof on top rows, wall on south row, door.

    h must be >= 2 (at least 1 roof row + 1 south-face wall row).
    door_offset: column offset from c0 for the door (on south face).
    """
    # Roof rows (all but last row)
    _fill(base, r0, r0 + h - 1, c0, c0 + w, TILE_ROOF)
    # South face wall (last row)
    _fill(base, r0 + h - 1, r0 + h, c0, c0 + w, TILE_WALL)
    # Door
    if door_offset is not None:
        dc = c0 + door_offset
        if 0 <= dc < MAP_COLS and r0 + h - 1 < MAP_ROWS:
            base[r0 + h - 1][dc] = TILE_DOOR


def _place_trees_scattered(base, overlay, r0, r1, c0, c1, density=30):
    """Place trees on grass tiles using deterministic hash. density=% chance."""
    for r in range(max(0, r0), min(MAP_ROWS, r1)):
        for c in range(max(0, c0), min(MAP_COLS, c1)):
            if base[r][c] not in (TILE_GRASS, TILE_FLOWER, TILE_TALL_GRASS):
                continue
            h = (r * 53 + c * 97) % 100
            if h < density:
                base[r][c] = TILE_TREE_TRUNK
                # Canopy on trunk + surrounding tiles
                for dr in range(-1, 2):
                    for dc in range(-1, 2):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < MAP_ROWS and 0 <= nc < MAP_COLS:
                            overlay[nr][nc] = OVERLAY_CANOPY


def _place_pond(base, r0, c0, w, h):
    """Place a rectangular water pond with 1-tile grass shore."""
    # Shore (grass ring)
    _fill(base, r0 - 1, r0 + h + 1, c0 - 1, c0 + w + 1, TILE_GRASS)
    # Water
    _fill(base, r0, r0 + h, c0, c0 + w, TILE_WATER)


def _place_path_cross(base, r_center, c_center, arm_len):
    """Place a cross-shaped cobblestone path."""
    for i in range(-arm_len, arm_len + 1):
        r = r_center + i
        c = c_center
        if 0 <= r < MAP_ROWS and 0 <= c < MAP_COLS:
            if base[r][c] in (TILE_GRASS, TILE_FLOWER):
                base[r][c] = TILE_PATH
        r2 = r_center
        c2 = c_center + i
        if 0 <= r2 < MAP_ROWS and 0 <= c2 < MAP_COLS:
            if base[r2][c2] in (TILE_GRASS, TILE_FLOWER):
                base[r2][c2] = TILE_PATH


def _place_path_rect(base, r0, r1, c0, c1):
    """Place path in a rectangle, only replacing grass-family tiles."""
    for r in range(max(0, r0), min(MAP_ROWS, r1)):
        for c in range(max(0, c0), min(MAP_COLS, c1)):
            if base[r][c] in (TILE_GRASS, TILE_FLOWER, TILE_TALL_GRASS):
                base[r][c] = TILE_PATH


def _scatter_flowers(base, r0, r1, c0, c1, density=20):
    """Scatter flower tiles on grass."""
    for r in range(max(0, r0), min(MAP_ROWS, r1)):
        for c in range(max(0, c0), min(MAP_COLS, c1)):
            if base[r][c] == TILE_GRASS:
                h = (r * 31 + c * 67) % 100
                if h < density:
                    base[r][c] = TILE_FLOWER


def _scatter_tall_grass(base, r0, r1, c0, c1, density=15):
    """Scatter tall grass on grass tiles."""
    for r in range(max(0, r0), min(MAP_ROWS, r1)):
        for c in range(max(0, c0), min(MAP_COLS, c1)):
            if base[r][c] == TILE_GRASS:
                h = (r * 41 + c * 83) % 100
                if h < density:
                    base[r][c] = TILE_TALL_GRASS


def _place_sign(base, r, c):
    if 0 <= r < MAP_ROWS and 0 <= c < MAP_COLS:
        base[r][c] = TILE_SIGN


def build_lanes_map():
    """Build and return (base_layer, overlay_layer, locations)."""
    base = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    overlay = [[OVERLAY_NONE] * MAP_COLS for _ in range(MAP_ROWS)]

    # ================================================================
    # ROWS 0-5: Dense forest
    # ================================================================
    _fill(base, 0, 6, 0, MAP_COLS, TILE_TREE_TRUNK)
    _fill(overlay, 0, 6, 0, MAP_COLS, OVERLAY_CANOPY)
    # Extend canopy 1 row south of forest
    _fill(overlay, 6, 7, 0, MAP_COLS, OVERLAY_CANOPY)

    # ================================================================
    # ROWS 6-7: Fence (colony north wall) with blocked gap at 30-32
    # ================================================================
    _fill(base, 6, 8, 0, MAP_COLS, TILE_FENCE)
    # Gap in fence (blocked path to forest)
    _fill(base, 6, 8, 30, 33, TILE_GROUND)

    # ================================================================
    # ROWS 8-10: North road (PAVED full width)
    # ================================================================
    _fill(base, 8, 11, 0, MAP_COLS, TILE_PAVED)

    # YOUR HOUSE compound at cols 15-22, rows 8-14
    # Grass courtyard
    _fill(base, 8, 15, 15, 23, TILE_GRASS)
    _scatter_flowers(base, 8, 15, 15, 23, density=25)
    # Actual house (5x4) at cols 16-20, rows 9-12
    _place_building(base, overlay, 9, 16, 5, 4, door_offset=2)

    # OLD RUINS at cols 33-38, rows 8-12
    # Crumbled walls — just some wall tiles with gaps
    _fill(base, 8, 12, 33, 39, TILE_GRASS)
    _fill(base, 8, 10, 33, 36, TILE_WALL)
    _fill(base, 8, 10, 37, 39, TILE_WALL)
    # Gap in the middle
    base[9][36] = TILE_GROUND
    _place_sign(base, 12, 35)

    # ================================================================
    # ROWS 11-27: UPPER HALF
    # ================================================================

    # --- Large Park: cols 4-26, rows 11-27 ---
    _fill(base, 11, 28, 4, 27, TILE_GRASS)
    _scatter_flowers(base, 11, 28, 4, 27, density=15)
    # Cross-shaped path through park
    _place_path_cross(base, 19, 15, 7)
    # Pond at cols 8-13, rows 14-17
    _place_pond(base, 14, 8, 6, 4)
    # Second small pond
    _place_pond(base, 22, 18, 4, 3)
    # Flower patches
    _scatter_flowers(base, 16, 21, 20, 26, density=40)
    # Trees in park
    _place_trees_scattered(base, overlay, 11, 28, 4, 27, density=12)
    # Park sign
    _place_sign(base, 11, 4)

    # --- Vertical main road: cols 30-32 (full map height) ---
    _fill(base, 8, MAP_ROWS - 1, 30, 33, TILE_PAVED)

    # --- Single building: cols 34-42, rows 11-22 ---
    # Split into small buildings with alleys
    _place_building(base, overlay, 11, 34, 4, 4, door_offset=2)
    _place_building(base, overlay, 11, 39, 4, 4, door_offset=2)
    # 1-tile gap at row 15
    _place_building(base, overlay, 16, 34, 5, 4, door_offset=2)
    _place_building(base, overlay, 16, 40, 3, 4, door_offset=1)

    # --- 4 buildings joined: cols 45-62, rows 11-18 ---
    # Split into 4 separate ~4-wide buildings with alleys (h and v)
    _place_building(base, overlay, 11, 45, 4, 3, door_offset=2)
    _place_building(base, overlay, 11, 50, 4, 3, door_offset=2)
    _place_building(base, overlay, 11, 55, 4, 3, door_offset=2)
    _place_building(base, overlay, 11, 60, 3, 3, door_offset=1)
    # 1-tile gap at row 14
    _place_building(base, overlay, 15, 45, 4, 3, door_offset=2)
    _place_building(base, overlay, 15, 50, 4, 3, door_offset=2)
    _place_building(base, overlay, 15, 55, 4, 3, door_offset=2)
    _place_building(base, overlay, 15, 60, 3, 3, door_offset=1)

    # --- 2 buildings joined: cols 65-76, rows 11-18 ---
    _place_building(base, overlay, 11, 65, 5, 3, door_offset=2)
    _place_building(base, overlay, 11, 71, 5, 3, door_offset=2)
    # 1-tile gap at row 14
    _place_building(base, overlay, 15, 65, 5, 3, door_offset=2)
    _place_building(base, overlay, 15, 71, 5, 3, door_offset=2)

    # Ground between upper buildings
    # (alleys already GROUND from initialization)

    # ================================================================
    # ROWS 28-30: Main east-west road (PAVED, full width)
    # ================================================================
    _fill(base, 28, 31, 0, MAP_COLS, TILE_PAVED)
    # Bridge exit at cols 77-79
    _place_sign(base, 29, 77)

    # ================================================================
    # ROWS 31-32: Secondary road
    # ================================================================
    _fill(base, 31, 33, 0, MAP_COLS, TILE_PAVED)

    # ================================================================
    # ROWS 33-40: Two buildings side by side
    # ================================================================
    # Building group 1: cols 4-16 — split into 3 buildings
    _place_building(base, overlay, 33, 4, 4, 3, door_offset=2)
    _place_building(base, overlay, 33, 9, 4, 3, door_offset=2)
    _place_building(base, overlay, 33, 14, 3, 3, door_offset=1)
    # 1-tile gap at row 36
    _place_building(base, overlay, 37, 4, 4, 3, door_offset=2)
    _place_building(base, overlay, 37, 9, 4, 3, door_offset=2)
    _place_building(base, overlay, 37, 14, 3, 3, door_offset=1)

    # Building group 2: cols 18-30 — split into 3 buildings
    _place_building(base, overlay, 33, 18, 4, 3, door_offset=2)
    _place_building(base, overlay, 33, 23, 4, 3, door_offset=2)
    _place_building(base, overlay, 33, 28, 2, 3, door_offset=1)
    # 1-tile gap at row 36
    _place_building(base, overlay, 37, 18, 4, 3, door_offset=2)
    _place_building(base, overlay, 37, 23, 4, 3, door_offset=2)
    _place_building(base, overlay, 37, 28, 2, 3, door_offset=1)

    # ================================================================
    # ROWS 41-42: Road
    # ================================================================
    _fill(base, 41, 43, 0, MAP_COLS, TILE_PAVED)

    # ================================================================
    # ROWS 43-52: Starting house, adjacent building, large lower park
    # ================================================================

    # STARTING HOUSE compound: cols 4-18, rows 43-52
    # Courtyard + garden
    _fill(base, 43, 52, 4, 18, TILE_GRASS)
    _fill(base, 43, 52, 4, 8, TILE_GROUND)  # courtyard
    _scatter_flowers(base, 43, 52, 8, 18, density=20)
    # Actual house: 5x4 at cols 5-9, rows 45-48
    _place_building(base, overlay, 45, 5, 5, 4, door_offset=2)
    _place_sign(base, 49, 6)

    # Building next to house: cols 21-30, rows 43-50
    _place_building(base, overlay, 43, 21, 4, 3, door_offset=2)
    _place_building(base, overlay, 43, 26, 4, 3, door_offset=2)
    # 1-tile gap at row 46
    _place_building(base, overlay, 47, 21, 4, 3, door_offset=2)
    _place_building(base, overlay, 47, 26, 4, 3, door_offset=2)

    # LARGE LOWER PARK: cols 36-74, rows 33-52
    _fill(base, 33, 53, 36, 75, TILE_GRASS)
    _scatter_flowers(base, 33, 53, 36, 75, density=12)
    _scatter_tall_grass(base, 33, 53, 36, 75, density=10)
    # Paths through park
    _place_path_cross(base, 42, 55, 8)
    _place_path_rect(base, 38, 39, 40, 70)
    _place_path_rect(base, 48, 49, 40, 70)
    # Pond
    _place_pond(base, 39, 58, 7, 5)
    # Pond 2
    _place_pond(base, 45, 42, 5, 3)
    # Trees
    _place_trees_scattered(base, overlay, 33, 53, 36, 75, density=10)
    # Park sign
    _place_sign(base, 33, 36)

    # ================================================================
    # ROWS 53-54: Road, full width
    # ================================================================
    _fill(base, 53, 55, 0, MAP_COLS, TILE_PAVED)

    # ================================================================
    # ROWS 55-64: Buildings, bank, small start park
    # ================================================================

    # 4 buildings joined: cols 4-22 — split into 4, with vertical gaps
    _place_building(base, overlay, 55, 4, 4, 3, door_offset=2)
    _place_building(base, overlay, 55, 9, 4, 3, door_offset=2)
    _place_building(base, overlay, 55, 14, 4, 3, door_offset=2)
    _place_building(base, overlay, 55, 19, 4, 3, door_offset=2)
    # 1-tile gap at row 58 (ground from init)
    _place_building(base, overlay, 59, 4, 4, 3, door_offset=2)
    _place_building(base, overlay, 59, 9, 4, 3, door_offset=2)
    _place_building(base, overlay, 59, 14, 4, 3, door_offset=2)
    _place_building(base, overlay, 59, 19, 4, 3, door_offset=2)
    # 1-tile gap at row 62
    _place_building(base, overlay, 63, 4, 4, 2, door_offset=2)
    _place_building(base, overlay, 63, 9, 4, 2, door_offset=2)

    # BANK: cols 24-32 — split into two connected buildings
    _place_building(base, overlay, 55, 24, 4, 5, door_offset=2)
    _place_building(base, overlay, 55, 29, 4, 5, door_offset=2)
    _place_sign(base, 60, 24)

    # SMALL START PARK: cols 35-48, rows 55-64
    _fill(base, 55, 65, 35, 49, TILE_GRASS)
    _scatter_flowers(base, 55, 65, 35, 49, density=18)
    _scatter_tall_grass(base, 55, 65, 35, 49, density=20)
    _place_trees_scattered(base, overlay, 55, 65, 35, 49, density=15)
    # Small path
    _place_path_rect(base, 59, 60, 37, 47)
    _place_sign(base, 55, 41)

    # Right side — more buildings
    _place_building(base, overlay, 55, 52, 5, 4, door_offset=2)
    _place_building(base, overlay, 55, 58, 5, 4, door_offset=2)
    _place_building(base, overlay, 55, 64, 5, 4, door_offset=2)
    _place_building(base, overlay, 55, 70, 5, 4, door_offset=2)

    # ================================================================
    # ROWS 65-66: Road
    # ================================================================
    _fill(base, 65, 67, 0, MAP_COLS, TILE_PAVED)

    # ================================================================
    # ROWS 67-74: Bottom buildings + wild outskirts
    # ================================================================

    # 2 buildings joined: cols 4-18 — split into 2, vertical gap
    _place_building(base, overlay, 67, 4, 5, 3, door_offset=2)
    _place_building(base, overlay, 67, 10, 5, 3, door_offset=2)
    # 1-tile gap at row 70
    _place_building(base, overlay, 71, 4, 5, 3, door_offset=2)
    _place_building(base, overlay, 71, 10, 5, 3, door_offset=2)

    # More buildings cols 20-45
    _place_building(base, overlay, 67, 20, 5, 4, door_offset=2)
    _place_building(base, overlay, 67, 26, 5, 4, door_offset=2)
    _place_building(base, overlay, 67, 34, 5, 4, door_offset=2)
    _place_building(base, overlay, 67, 40, 5, 4, door_offset=2)

    # Lower-right quadrant: cols 50-78, rows 55-74 — wild outskirts
    _fill(base, 59, 74, 50, 79, TILE_GRASS)
    _scatter_tall_grass(base, 59, 74, 50, 79, density=25)
    _place_trees_scattered(base, overlay, 59, 74, 50, 79, density=18)
    # Restore buildings we just placed in this area
    _place_building(base, overlay, 67, 52, 5, 4, door_offset=2)
    _place_building(base, overlay, 67, 58, 5, 4, door_offset=2)

    # ================================================================
    # ROW 74: South fence
    # ================================================================
    _fill(base, 74, 75, 0, MAP_COLS, TILE_FENCE)

    # ================================================================
    # Edges: fence on east/west borders
    # ================================================================
    for r in range(6, 74):
        if base[r][0] not in (TILE_PAVED, TILE_FENCE):
            base[r][0] = TILE_FENCE
        if base[r][1] not in (TILE_PAVED, TILE_FENCE):
            base[r][1] = TILE_FENCE
        if base[r][MAP_COLS - 1] not in (TILE_PAVED, TILE_FENCE):
            base[r][MAP_COLS - 1] = TILE_FENCE
        if base[r][MAP_COLS - 2] not in (TILE_PAVED, TILE_FENCE):
            base[r][MAP_COLS - 2] = TILE_FENCE

    # ================================================================
    # LOCATIONS — special interaction points
    # ================================================================
    locations = {
        "your_house": {
            "pos": (7, 49), "type": "save",
            "text": "Home sweet home.",
        },
        "bank": {
            "pos": (27, 60), "type": "shop",
            "text": "Colony Bank. Supplies and treats.",
        },
        "small_park": {
            "pos": (41, 55), "type": "spawn",
            "text": "Small Park. Adventure starts here.",
        },
        "colony_park": {
            "pos": (15, 19), "type": "spawn",
            "text": "Colony Park. A peaceful place.",
        },
        "colony_gardens": {
            "pos": (55, 42), "type": "spawn",
            "text": "Colony Gardens. Lush and green.",
        },
        "bridge_exit": {
            "pos": (78, 29), "type": "exit",
            "text": "The Crossing \u2014 Coming Soon!",
        },
        "forest_entrance": {
            "pos": (31, 7), "type": "blocked",
            "text": "The Deep Woods \u2014 Too dangerous.",
        },
        "old_ruins": {
            "pos": (35, 12), "type": "info",
            "text": "Old colony ruins. What happened here?",
        },
        "starter_house": {
            "pos": (7, 49), "type": "save",
            "text": "Your home. The journey begins.",
        },
    }

    # Build sign->location lookup from SIGN tiles
    sign_locations = {}
    for name, loc in locations.items():
        cx, cy = loc["pos"]
        # Find nearest sign tile
        for dr in range(-2, 3):
            for dc in range(-2, 3):
                r, c = cy + dr, cx + dc
                if (0 <= r < MAP_ROWS and 0 <= c < MAP_COLS
                        and base[r][c] == TILE_SIGN):
                    sign_locations[(c, r)] = loc

    return base, overlay, locations, sign_locations


# Pre-built map data (computed once on import)
LANES_BASE, LANES_OVERLAY, LOCATIONS, SIGN_LOCATIONS = build_lanes_map()
