"""Tests for Chapter 2: Colony Creatures — overworld, map, movement."""
from neural_dungeon.colony.config import (
    TILE_GROUND, TILE_GRASS, TILE_WALL, TILE_ROOF,
    TILE_TREE_TRUNK, TILE_FENCE, TILE_WATER, TILE_PATH,
    TILE_DOOR, TILE_TALL_GRASS, TILE_SIGN, TILE_FLOWER,
    TILE_PAVED, WALKABLE_TILES,
    MAP_COLS, MAP_ROWS, SCALED_TILE,
    DIR_DOWN, DIR_UP, DIR_LEFT, DIR_RIGHT,
    DECO_NONE,
)
from neural_dungeon.colony.maps.the_lanes import (
    LANES_BASE, LANES_OVERLAY, LOCATIONS, SIGN_LOCATIONS,
    build_lanes_map,
)
from neural_dungeon.colony.camera import Camera
from neural_dungeon.colony.player_colony import ColonyPlayer
from neural_dungeon.colony.decorations import compute_decorations
from neural_dungeon.config import (
    STATE_TITLE, STATE_LEVEL_SELECT, STATE_COLONY_OVERWORLD,
    TOTAL_FLOORS,
)


# --- Map dimensions ---

def test_map_base_dimensions():
    assert len(LANES_BASE) == MAP_ROWS
    for row in LANES_BASE:
        assert len(row) == MAP_COLS


def test_map_overlay_dimensions():
    assert len(LANES_OVERLAY) == MAP_ROWS
    for row in LANES_OVERLAY:
        assert len(row) == MAP_COLS


def test_map_dimensions_are_80x75():
    assert MAP_COLS == 80
    assert MAP_ROWS == 75


# --- Tile collision (walkable vs non-walkable) ---

def test_walkable_tiles():
    walkable = {TILE_GROUND, TILE_GRASS, TILE_PATH, TILE_DOOR,
                TILE_TALL_GRASS, TILE_FLOWER, TILE_PAVED}
    assert walkable == WALKABLE_TILES


def test_non_walkable_tiles():
    non_walkable = {TILE_WALL, TILE_ROOF, TILE_TREE_TRUNK,
                    TILE_FENCE, TILE_WATER, TILE_SIGN}
    for tile in non_walkable:
        assert tile not in WALKABLE_TILES


def test_player_cannot_walk_on_wall():
    p = ColonyPlayer(10, 10)
    # Create a small test layer with wall to the right
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    layer[10][11] = TILE_WALL
    result = p.try_move(DIR_RIGHT, layer)
    assert result is False
    assert p.tile_x == 10


def test_player_cannot_walk_on_water():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    layer[10][11] = TILE_WATER
    result = p.try_move(DIR_RIGHT, layer)
    assert result is False


def test_player_cannot_walk_on_fence():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    layer[10][11] = TILE_FENCE
    result = p.try_move(DIR_RIGHT, layer)
    assert result is False


def test_player_cannot_walk_on_sign():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    layer[10][11] = TILE_SIGN
    result = p.try_move(DIR_RIGHT, layer)
    assert result is False


def test_player_can_walk_on_grass():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    layer[10][11] = TILE_GRASS
    result = p.try_move(DIR_RIGHT, layer)
    assert result is True


def test_player_can_walk_on_path():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    layer[10][11] = TILE_PATH
    result = p.try_move(DIR_RIGHT, layer)
    assert result is True


def test_player_can_walk_on_door():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    layer[10][11] = TILE_DOOR
    result = p.try_move(DIR_RIGHT, layer)
    assert result is True


def test_player_can_walk_on_tall_grass():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    layer[10][11] = TILE_TALL_GRASS
    result = p.try_move(DIR_RIGHT, layer)
    assert result is True


def test_player_can_walk_on_flower():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    layer[10][11] = TILE_FLOWER
    result = p.try_move(DIR_RIGHT, layer)
    assert result is True


def test_player_can_walk_on_paved():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    layer[10][11] = TILE_PAVED
    result = p.try_move(DIR_RIGHT, layer)
    assert result is True


# --- Player grid movement (4 directions, no diagonal) ---

def test_player_move_right():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    p.try_move(DIR_RIGHT, layer)
    assert p.target_tile_x == 11
    assert p.target_tile_y == 10


def test_player_move_left():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    p.try_move(DIR_LEFT, layer)
    assert p.target_tile_x == 9
    assert p.target_tile_y == 10


def test_player_move_up():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    p.try_move(DIR_UP, layer)
    assert p.target_tile_x == 10
    assert p.target_tile_y == 9


def test_player_move_down():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    p.try_move(DIR_DOWN, layer)
    assert p.target_tile_x == 10
    assert p.target_tile_y == 11


def test_player_no_move_while_moving():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    p.try_move(DIR_RIGHT, layer)
    # Cannot move again while still in motion
    result = p.try_move(DIR_DOWN, layer)
    assert result is False


def test_player_move_completes():
    p = ColonyPlayer(10, 10)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    p.try_move(DIR_RIGHT, layer)
    # Simulate frames
    for _ in range(10):
        p.update()
    assert p.tile_x == 11
    assert p.moving is False


def test_player_out_of_bounds():
    p = ColonyPlayer(0, 0)
    layer = [[TILE_GROUND] * MAP_COLS for _ in range(MAP_ROWS)]
    result = p.try_move(DIR_LEFT, layer)
    assert result is False
    result = p.try_move(DIR_UP, layer)
    assert result is False


# --- Camera clamping ---

def test_camera_clamp_top_left():
    cam = Camera()
    cam.update(0, 0)
    assert cam.x >= 0
    assert cam.y >= 0


def test_camera_clamp_bottom_right():
    from neural_dungeon.colony.config import MAP_PIXEL_W, MAP_PIXEL_H, VIEW_W, VIEW_H
    cam = Camera()
    cam.update(MAP_PIXEL_W + 1000, MAP_PIXEL_H + 1000)
    # After enough updates the camera should clamp
    for _ in range(200):
        cam.update(MAP_PIXEL_W + 1000, MAP_PIXEL_H + 1000)
    assert cam.x <= MAP_PIXEL_W - VIEW_W
    assert cam.y <= MAP_PIXEL_H - VIEW_H


def test_camera_snap():
    cam = Camera()
    cam.snap_to(500, 500)
    from neural_dungeon.colony.config import VIEW_W, VIEW_H
    # Camera should be centered on target
    assert cam.x >= 0
    assert cam.y >= 0


# --- Location lookup ---

def test_locations_dict_has_entries():
    assert len(LOCATIONS) > 0


def test_bridge_exit_location():
    assert "bridge_exit" in LOCATIONS
    loc = LOCATIONS["bridge_exit"]
    assert loc["type"] == "exit"
    assert "Coming Soon" in loc["text"]


def test_forest_entrance_location():
    assert "forest_entrance" in LOCATIONS
    loc = LOCATIONS["forest_entrance"]
    assert loc["type"] == "blocked"


def test_colony_park_location():
    assert "colony_park" in LOCATIONS


# --- Decoration placement ---

def test_decorations_only_on_walkable():
    decos = compute_decorations(LANES_BASE)
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            if LANES_BASE[r][c] not in WALKABLE_TILES:
                assert decos[r][c] == DECO_NONE, \
                    f"Deco on non-walkable at ({c},{r})"


def test_decorations_layer_dimensions():
    decos = compute_decorations(LANES_BASE)
    assert len(decos) == MAP_ROWS
    for row in decos:
        assert len(row) == MAP_COLS


# --- Level select state transitions ---

def test_states_defined():
    assert STATE_LEVEL_SELECT == "level_select"
    assert STATE_COLONY_OVERWORLD == "colony_overworld"


def test_total_floors():
    assert TOTAL_FLOORS == 10


# --- Map build consistency ---

def test_map_rebuild_is_consistent():
    base1, overlay1, _, _ = build_lanes_map()
    base2, overlay2, _, _ = build_lanes_map()
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            assert base1[r][c] == base2[r][c], \
                f"Base mismatch at ({c},{r})"
            assert overlay1[r][c] == overlay2[r][c], \
                f"Overlay mismatch at ({c},{r})"


def test_map_has_buildings():
    """Map should contain wall and roof tiles."""
    has_wall = any(LANES_BASE[r][c] == TILE_WALL
                   for r in range(MAP_ROWS)
                   for c in range(MAP_COLS))
    has_roof = any(LANES_BASE[r][c] == TILE_ROOF
                   for r in range(MAP_ROWS)
                   for c in range(MAP_COLS))
    assert has_wall
    assert has_roof


def test_map_has_trees():
    has_trunk = any(LANES_BASE[r][c] == TILE_TREE_TRUNK
                    for r in range(MAP_ROWS)
                    for c in range(MAP_COLS))
    assert has_trunk


def test_map_has_water():
    has_water = any(LANES_BASE[r][c] == TILE_WATER
                    for r in range(MAP_ROWS)
                    for c in range(MAP_COLS))
    assert has_water


def test_map_has_paved_roads():
    has_paved = any(LANES_BASE[r][c] == TILE_PAVED
                    for r in range(MAP_ROWS)
                    for c in range(MAP_COLS))
    assert has_paved


def test_player_start_is_walkable():
    """Player starts at (7, 49) — must be walkable."""
    assert LANES_BASE[49][7] in WALKABLE_TILES
