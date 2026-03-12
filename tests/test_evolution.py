"""Tests for per-floor AI evolution system."""
import pytest
from collections import deque

from neural_dungeon.config import (
    ROOM_WIDTH, ROOM_HEIGHT, EVOLUTION_STAT_SCALE,
    EVOLUTION_LEAD_ACCURACY, PERCEPTRON_HP, TOKEN_HP,
)
from neural_dungeon.entities.enemies import (
    Enemy, Perceptron, Token, BitShifter, Convolver,
    DropoutPhantom, Pooler, AttentionHead, GradientGhost,
    OverfittingMimic, ReLUGuardian, spawn_enemies_for_room,
    _get_lead_accuracy, _get_spacing_dist,
)
from neural_dungeon.utils import lead_shot_direction, direction_to
from neural_dungeon.world.room_layouts import (
    Tile, layout_data_maze, layout_server_farm,
    layout_firewall_matrix, layout_neural_web,
    layout_cascade_gauntlet, get_player_spawn, is_walkable,
    get_layout_for_room,
)


# === Evolution Level Tests ===

def test_enemy_base_has_evolution_level():
    e = Enemy(10, 10, hp=20, speed=0.1, char="X", evolution_level=5)
    assert e.evolution_level == 5


def test_enemy_default_evolution_level():
    e = Enemy(10, 10, hp=20, speed=0.1, char="X")
    assert e.evolution_level == 0


@pytest.mark.parametrize("cls,kwargs", [
    (Perceptron, {}),
    (Token, {}),
    (BitShifter, {}),
    (Convolver, {}),
    (DropoutPhantom, {}),
    (Pooler, {}),
    (AttentionHead, {}),
    (GradientGhost, {}),
    (OverfittingMimic, {}),
    (ReLUGuardian, {"activation": 0.5}),
])
def test_all_enemies_accept_evolution_level(cls, kwargs):
    enemy = cls(10, 10, evolution_level=7, **kwargs)
    assert enemy.evolution_level == 7


@pytest.mark.parametrize("cls,kwargs", [
    (Perceptron, {}),
    (Token, {}),
    (BitShifter, {}),
    (Convolver, {}),
    (DropoutPhantom, {}),
    (Pooler, {}),
    (AttentionHead, {}),
    (GradientGhost, {}),
    (OverfittingMimic, {}),
    (ReLUGuardian, {"activation": 0.5}),
])
def test_all_enemies_update_accepts_player_velocity(cls, kwargs):
    enemy = cls(10, 10, **kwargs)
    bullets = enemy.update(
        15.0, 10.0, enemies=[],
        player_vx=1.0, player_vy=0.0, player_speed=0.4,
    )
    assert isinstance(bullets, list)


# === Lead Shot Tests ===

def test_lead_shot_no_accuracy():
    dx, dy = lead_shot_direction(
        0, 0, 10, 0,
        1.0, 0.0, 0.4, 0.5, accuracy=0.0,
    )
    # With 0 accuracy, should aim at current position
    base_dx, base_dy = direction_to(0, 0, 10, 0)
    assert abs(dx - base_dx) < 0.01
    assert abs(dy - base_dy) < 0.01


def test_lead_shot_full_accuracy():
    dx, dy = lead_shot_direction(
        0, 0, 10, 0,
        0.0, 1.0, 0.4, 0.5, accuracy=1.0,
    )
    # With full accuracy and target moving up, should aim ahead
    assert dy > 0.01  # should have some y component


def test_lead_accuracy_scales_with_floor():
    assert _get_lead_accuracy(0) == 0.0
    assert _get_lead_accuracy(2) == 0.0
    assert _get_lead_accuracy(3) > 0.0
    assert _get_lead_accuracy(9) > _get_lead_accuracy(3)


# === Spawn Scaling Tests ===

def test_spawn_enemies_floor_0():
    enemies = spawn_enemies_for_room(0, 0, "combat")
    assert len(enemies) > 0
    for e in enemies:
        assert e.evolution_level == 0


def test_spawn_enemies_floor_5():
    enemies = spawn_enemies_for_room(0, 5, "combat")
    assert len(enemies) > 0
    for e in enemies:
        assert e.evolution_level == 5


def test_spawn_enemies_floor_9():
    enemies = spawn_enemies_for_room(0, 9, "combat")
    assert len(enemies) > 0
    for e in enemies:
        assert e.evolution_level == 9
    # Count should be capped reasonably
    assert len(enemies) <= 15


def test_stat_scaling_applied():
    # Floor 9 enemies should have more HP than floor 0 enemies of same type
    e0 = Perceptron(10, 10, evolution_level=0)
    # Spawn at floor 9 should have scaled HP
    enemies_9 = spawn_enemies_for_room(0, 9, "combat")
    # At least one perceptron should have more HP than base
    scale = EVOLUTION_STAT_SCALE[9]
    expected_hp = int(PERCEPTRON_HP * scale)
    # The spawned enemies should have scaled HP
    for e in enemies_9:
        if isinstance(e, Perceptron):
            assert e.hp == expected_hp
            break


def test_spawn_enemies_no_spawn_for_dead():
    enemies = spawn_enemies_for_room(0, 5, "dead")
    assert len(enemies) == 0


def test_spawn_enemies_no_spawn_for_shop():
    enemies = spawn_enemies_for_room(0, 5, "shop")
    assert len(enemies) == 0


# === Per-Enemy Behavior Tests ===

def test_token_zigzag_at_floor_6():
    t = Token(10, 10, evolution_level=6)
    old_x = t.x
    t.update(15, 10)
    # Token should still move toward player
    assert t.x > old_x


def test_bitshifter_flanking_teleport_floor_6():
    bs = BitShifter(10, 10, evolution_level=6)
    bs.teleport_timer = 0  # force teleport next update
    bs.update(30, 12)
    # After teleport, should be near player (within flanking range)
    from neural_dungeon.utils import distance
    dist = distance(bs.x, bs.y, 30, 12)
    assert dist < 15.0


def test_gradient_ghost_repath_faster_floor_7():
    gg = GradientGhost(10, 10, evolution_level=7)
    gg.update(20, 10)
    assert gg.repath_timer <= 20


def test_gradient_ghost_repath_normal_floor_0():
    gg = GradientGhost(10, 10, evolution_level=0)
    gg.update(20, 10)
    assert gg.repath_timer <= 30


def test_mimic_records_faster_floor_8():
    m = OverfittingMimic(10, 10, evolution_level=8)
    assert m.record_duration == 60  # faster recording


def test_mimic_records_normal_floor_0():
    m = OverfittingMimic(10, 10, evolution_level=0)
    assert m.record_duration == 90  # normal recording


def test_spacing_dist_zero_before_floor_5():
    assert _get_spacing_dist(0) == 0.0
    assert _get_spacing_dist(4) == 0.0


def test_spacing_dist_positive_at_floor_5():
    assert _get_spacing_dist(5) > 0.0


# === Complex Layout Tests ===

COMPLEX_LAYOUTS = [
    layout_data_maze,
    layout_server_farm,
    layout_firewall_matrix,
    layout_neural_web,
    layout_cascade_gauntlet,
]


@pytest.mark.parametrize("layout_fn", COMPLEX_LAYOUTS)
def test_complex_layout_dimensions(layout_fn):
    grid = layout_fn()
    assert len(grid) == ROOM_HEIGHT
    assert len(grid[0]) == ROOM_WIDTH


@pytest.mark.parametrize("layout_fn", COMPLEX_LAYOUTS)
def test_complex_layout_valid_tiles(layout_fn):
    grid = layout_fn()
    for y in range(ROOM_HEIGHT):
        for x in range(ROOM_WIDTH):
            assert grid[y][x] in (
                Tile.FLOOR, Tile.WALL, Tile.COVER,
                Tile.PIT, Tile.SLOW, Tile.VENT,
            )


@pytest.mark.parametrize("layout_fn", COMPLEX_LAYOUTS)
def test_complex_layout_player_spawn(layout_fn):
    grid = layout_fn()
    px, py = get_player_spawn(grid)
    gx, gy = int(px), int(py)
    assert grid[gy][gx] == Tile.FLOOR, (
        f"{layout_fn.__name__}: player spawn at ({gx},{gy}) "
        f"is tile {grid[gy][gx]}"
    )


@pytest.mark.parametrize("layout_fn", COMPLEX_LAYOUTS)
def test_complex_layout_walkable_path(layout_fn):
    """BFS from player spawn should reach at least 50% of floor tiles."""
    grid = layout_fn()
    px, py = get_player_spawn(grid)
    start = (int(px), int(py))

    total_walkable = 0
    for y in range(ROOM_HEIGHT):
        for x in range(ROOM_WIDTH):
            if is_walkable(grid[y][x]):
                total_walkable += 1

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
    assert ratio >= 0.5, (
        f"{layout_fn.__name__}: only {ratio:.1%} reachable "
        f"({reachable}/{total_walkable})"
    )


def test_get_layout_for_room_floor_7():
    """Floor 7 combat room should generate a valid layout."""
    grid = get_layout_for_room(7, "combat", seed=42)
    assert len(grid) == ROOM_HEIGHT
    assert len(grid[0]) == ROOM_WIDTH


def test_get_layout_for_room_floor_9_elite():
    """Floor 9 elite room should generate a valid layout."""
    grid = get_layout_for_room(9, "elite", seed=42)
    assert len(grid) == ROOM_HEIGHT
    assert len(grid[0]) == ROOM_WIDTH
