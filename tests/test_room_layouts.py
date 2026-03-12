"""Tests for the room layout system."""
import pytest
from collections import deque

from neural_dungeon.config import ROOM_WIDTH, ROOM_HEIGHT, COVER_HP
from neural_dungeon.world.room_layouts import (
    Tile, empty_grid, place_obstacle, data_pillar, server_rack,
    layout_open_arena, layout_four_pillars, layout_corridors,
    layout_center_fortress, layout_firewall_gauntlet, layout_cross_maze,
    layout_pillar_grid, layout_ring_arena, layout_zigzag_walls,
    layout_neon_pits, get_layout_for_room, get_valid_spawn_positions,
    get_player_spawn, get_blocked_set, grid_to_collision_rects,
    is_walkable, DOOR_TOP, DOOR_BOTTOM, DOOR_LEFT, DOOR_RIGHT,
    DOOR_CLEARANCE,
)
from neural_dungeon.world.room import Room


def test_empty_grid_all_floor():
    grid = empty_grid()
    assert len(grid) == ROOM_HEIGHT
    assert len(grid[0]) == ROOM_WIDTH
    for y in range(ROOM_HEIGHT):
        for x in range(ROOM_WIDTH):
            assert grid[y][x] == Tile.FLOOR


def test_place_obstacle_in_bounds():
    grid = empty_grid()
    pillar = data_pillar()
    result = place_obstacle(grid, pillar, 10, 10)
    assert result is True
    assert grid[10][10] == Tile.WALL


def test_place_obstacle_door_clearance():
    grid = empty_grid()
    pillar = data_pillar()
    # Try placing right next to a door — should fail
    for door in [DOOR_TOP, DOOR_BOTTOM, DOOR_LEFT, DOOR_RIGHT]:
        fresh = empty_grid()
        result = place_obstacle(fresh, pillar, door[0], door[1])
        assert result is False, f"Should fail near door {door}"


def test_place_obstacle_no_overlap():
    grid = empty_grid()
    pillar = data_pillar()
    place_obstacle(grid, pillar, 10, 10)
    result = place_obstacle(grid, pillar, 10, 10)
    assert result is False


ALL_LAYOUTS = [
    layout_open_arena,
    layout_four_pillars,
    layout_corridors,
    layout_center_fortress,
    layout_firewall_gauntlet,
    layout_cross_maze,
    layout_pillar_grid,
    layout_ring_arena,
    layout_zigzag_walls,
    layout_neon_pits,
]


@pytest.mark.parametrize("layout_fn", ALL_LAYOUTS)
def test_all_layouts_generate(layout_fn):
    grid = layout_fn()
    assert len(grid) == ROOM_HEIGHT
    assert len(grid[0]) == ROOM_WIDTH
    for y in range(ROOM_HEIGHT):
        for x in range(ROOM_WIDTH):
            assert grid[y][x] in (
                Tile.FLOOR, Tile.WALL, Tile.COVER,
                Tile.PIT, Tile.SLOW, Tile.VENT,
            )


@pytest.mark.parametrize("layout_fn", ALL_LAYOUTS)
def test_all_layouts_walkable_path(layout_fn):
    """BFS from player spawn should reach at least 60% of floor tiles."""
    grid = layout_fn()
    px, py = get_player_spawn(grid)
    start = (int(px), int(py))

    # Count all walkable tiles
    total_walkable = 0
    for y in range(ROOM_HEIGHT):
        for x in range(ROOM_WIDTH):
            if is_walkable(grid[y][x]):
                total_walkable += 1

    # BFS from start
    visited = set()
    queue = deque([start])
    visited.add(start)
    while queue:
        cx, cy = queue.popleft()
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy
            if (nx, ny) in visited:
                continue
            if not (0 <= nx < ROOM_WIDTH and 0 <= ny < ROOM_HEIGHT):
                continue
            if is_walkable(grid[ny][nx]):
                visited.add((nx, ny))
                queue.append((nx, ny))

    reachable = len(visited)
    ratio = reachable / max(1, total_walkable)
    assert ratio >= 0.6, (
        f"{layout_fn.__name__}: only {ratio:.1%} reachable "
        f"({reachable}/{total_walkable})"
    )


def test_spawn_positions_on_floor():
    grid = layout_open_arena()
    positions = get_valid_spawn_positions(grid, 10)
    assert len(positions) <= 10
    for x, y in positions:
        gx, gy = int(x), int(y)
        assert grid[gy][gx] == Tile.FLOOR


def test_player_spawn_on_floor():
    for layout_fn in ALL_LAYOUTS:
        grid = layout_fn()
        px, py = get_player_spawn(grid)
        gx, gy = int(px), int(py)
        assert grid[gy][gx] == Tile.FLOOR, (
            f"{layout_fn.__name__}: player spawn at ({gx},{gy}) "
            f"is tile {grid[gy][gx]}"
        )


def test_blocked_set_correct():
    grid = layout_firewall_gauntlet()
    blocked = get_blocked_set(grid)
    for y in range(ROOM_HEIGHT):
        for x in range(ROOM_WIDTH):
            tile = grid[y][x]
            if tile in (Tile.WALL, Tile.COVER, Tile.PIT):
                assert (x, y) in blocked, (
                    f"({x},{y}) tile={tile} should be in blocked set"
                )
            elif tile in (Tile.FLOOR, Tile.SLOW, Tile.VENT):
                assert (x, y) not in blocked


def test_collision_rects_cover_all_walls():
    grid = layout_four_pillars()
    rects = grid_to_collision_rects(grid)
    # Build set of all WALL/COVER positions
    wall_positions = set()
    for y in range(ROOM_HEIGHT):
        for x in range(ROOM_WIDTH):
            if grid[y][x] in (Tile.WALL, Tile.COVER):
                wall_positions.add((x, y))

    # Every wall/cover position should be inside some rect
    covered = set()
    for rx, ry, rw, rh in rects:
        for dy in range(int(rh)):
            for dx in range(int(rw)):
                covered.add((int(rx) + dx, int(ry) + dy))

    for pos in wall_positions:
        assert pos in covered, f"{pos} not covered by collision rects"


def test_get_layout_for_room_dead():
    grid = get_layout_for_room(0, "dead")
    for y in range(ROOM_HEIGHT):
        for x in range(ROOM_WIDTH):
            assert grid[y][x] == Tile.FLOOR


def test_get_layout_for_room_shop():
    grid = get_layout_for_room(0, "shop")
    has_cover = False
    for y in range(ROOM_HEIGHT):
        for x in range(ROOM_WIDTH):
            if grid[y][x] == Tile.COVER:
                has_cover = True
                break
    assert has_cover, "Shop layout should have COVER tiles"


def test_cover_destruction():
    room = Room(
        room_type="combat",
        room_index=0,
        floor_index=0,
        activation=0.5,
    )
    room.enter()
    assert room.layout_grid is not None

    # Find a cover tile
    cover_pos = None
    for y in range(ROOM_HEIGHT):
        for x in range(ROOM_WIDTH):
            if room.layout_grid[y][x] == Tile.COVER:
                cover_pos = (x, y)
                break
        if cover_pos:
            break

    if cover_pos is None:
        pytest.skip("No cover tiles in this layout")

    gx, gy = cover_pos
    assert (gx, gy) in room.cover_hp
    initial_hp = room.cover_hp[(gx, gy)]

    # Damage it partially
    room.damage_cover(gx, gy, 10)
    assert room.cover_hp[(gx, gy)] == initial_hp - 10
    assert room.layout_grid[gy][gx] == Tile.COVER

    # Destroy it
    room.damage_cover(gx, gy, initial_hp)
    assert (gx, gy) not in room.cover_hp
    assert room.layout_grid[gy][gx] == Tile.FLOOR
