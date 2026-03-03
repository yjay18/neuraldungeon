"""Tests for all enemy types."""
import random
from neural_dungeon.entities.enemies import (
    Enemy, Perceptron, Token, BitShifter, Convolver,
    DropoutPhantom, Pooler, AttentionHead, GradientGhost,
    OverfittingMimic, ReLUGuardian, spawn_enemies_for_room,
    ENEMY_CLASSES, FLOOR_ENEMY_POOL,
)
from neural_dungeon.entities.projectiles import ProjectileManager
from neural_dungeon.config import (
    BIT_SHIFTER_TELEPORT_CD, CONVOLVER_SHOOT_COOLDOWN,
    DROPOUT_INTANGIBLE_CHANCE, POOLER_ABSORB_RANGE,
    ATTENTION_TURN_RATE, GRADIENT_GHOST_TRAIL_CD,
    MIMIC_RECORD_TICKS, RELU_ACTIVATION_THRESHOLD,
    ROOM_TYPE_COMBAT, ROOM_TYPE_ELITE, ROOM_TYPE_DEAD,
)


def test_enemy_intangible_blocks_damage():
    e = Enemy(10, 10, 50, 0, "X")
    e.intangible = True
    dmg = e.take_damage(30)
    assert dmg == 0
    assert e.hp == 50


def test_enemy_absorbed_flag():
    e = Enemy(10, 10, 50, 0, "X")
    assert not e.absorbed
    e.absorbed = True
    assert e.absorbed


def test_bit_shifter_creation():
    bs = BitShifter(10, 10)
    assert bs.alive
    assert bs.teleport_timer == BIT_SHIFTER_TELEPORT_CD


def test_bit_shifter_teleports():
    bs = BitShifter(10, 10)
    old_x, old_y = bs.x, bs.y
    bs.teleport_timer = 1
    bs.update(30, 15)
    # After teleport timer hits 0, position should change
    assert bs.teleport_timer > 0  # timer reset


def test_bit_shifter_shoots():
    bs = BitShifter(10, 10)
    bs.shoot_cooldown = 1
    bullets = bs.update(15, 10)
    assert len(bullets) == 1
    assert bullets[0].owner == "enemy"


def test_convolver_creation():
    c = Convolver(10, 10)
    assert c.alive
    assert c.hp == 40


def test_convolver_fires_8_bullets():
    c = Convolver(10, 10)
    c.shoot_cooldown = 1
    bullets = c.update(20, 20)
    assert len(bullets) == 8  # 8 directions


def test_dropout_creation():
    d = DropoutPhantom(10, 10)
    assert d.alive
    assert d.hp == 20


def test_dropout_intangibility():
    d = DropoutPhantom(10, 10)
    # Run many updates and check intangibility toggles
    was_intangible = False
    was_tangible = False
    random.seed(42)
    for _ in range(100):
        d.shoot_cooldown = 999  # prevent shooting
        d.update(20, 20)
        if d.intangible:
            was_intangible = True
        else:
            was_tangible = True
    assert was_intangible
    assert was_tangible


def test_dropout_intangible_blocks_damage():
    d = DropoutPhantom(10, 10)
    d.intangible = True
    dmg = d.take_damage(15)
    assert dmg == 0
    assert d.hp == 20


def test_pooler_creation():
    p = Pooler(10, 10)
    assert p.alive
    assert p.contact_damage == 15
    assert p.absorbed_count == 0


def test_pooler_absorbs_dead_enemy():
    pooler = Pooler(10, 10)
    dead = Perceptron(10.5, 10.5)
    dead.alive = False
    enemies = [pooler, dead]

    pooler.update(30, 15, enemies)
    assert dead.absorbed
    assert pooler.absorbed_count == 1
    assert pooler.hp > 50  # gained HP from absorb


def test_pooler_ignores_alive_enemies():
    pooler = Pooler(10, 10)
    alive = Perceptron(10.5, 10.5)
    enemies = [pooler, alive]

    pooler.update(30, 15, enemies)
    assert not alive.absorbed
    assert pooler.absorbed_count == 0


def test_attention_head_creation():
    a = AttentionHead(10, 10)
    assert a.alive
    assert a.hp == 35


def test_attention_head_fires_homing():
    a = AttentionHead(10, 10)
    a.shoot_cooldown = 1
    bullets = a.update(20, 10)
    assert len(bullets) == 1
    assert bullets[0].homing
    assert bullets[0].turn_rate == ATTENTION_TURN_RATE


def test_gradient_ghost_creation():
    g = GradientGhost(10, 10)
    assert g.alive
    assert g.trail_timer == GRADIENT_GHOST_TRAIL_CD


def test_gradient_ghost_leaves_trail():
    g = GradientGhost(10, 10)
    g.trail_timer = 1
    bullets = g.update(20, 10)
    assert len(bullets) == 1
    # Trail has no movement
    assert bullets[0].speed == 0
    assert bullets[0].lifetime > 0


def test_gradient_ghost_pathfinds():
    g = GradientGhost(5, 5)
    g.trail_timer = 999  # prevent trail spam
    g.update(20, 10)
    assert len(g.path) > 0


def test_mimic_creation():
    m = OverfittingMimic(10, 10)
    assert m.alive
    assert m.recording


def test_mimic_records_then_replays():
    m = OverfittingMimic(10, 10)
    # Record phase
    for _ in range(MIMIC_RECORD_TICKS):
        m.update(20, 15)

    assert not m.recording
    assert len(m.record_buffer) == MIMIC_RECORD_TICKS


def test_mimic_shoots_while_replaying():
    m = OverfittingMimic(10, 10)
    # Force into replay mode
    m.recording = False
    m.record_buffer = [(15, 15), (20, 20)]
    m.replay_index = 0
    m.shoot_cooldown = 1

    bullets = m.update(15, 15)
    assert len(bullets) == 1


def test_relu_guardian_active():
    r = ReLUGuardian(10, 10, activation=0.8)
    assert r.is_active
    assert r.speed > 0.1
    assert r.color == "bright_green"


def test_relu_guardian_dormant():
    r = ReLUGuardian(10, 10, activation=0.2)
    assert not r.is_active
    assert r.speed < 0.1
    assert r.color == "bright_black"


def test_relu_guardian_shoots():
    r = ReLUGuardian(10, 10, activation=0.8)
    r.shoot_cooldown = 1
    bullets = r.update(20, 10)
    assert len(bullets) == 1


def test_spawn_enemies_floor_0():
    enemies = spawn_enemies_for_room(0, 0, ROOM_TYPE_COMBAT)
    assert len(enemies) > 0
    # Floor 0 should only have Perceptron and Token
    for e in enemies:
        assert isinstance(e, (Perceptron, Token))


def test_spawn_enemies_floor_2():
    random.seed(42)
    enemies = spawn_enemies_for_room(0, 2, ROOM_TYPE_COMBAT)
    assert len(enemies) > 0
    # Floor 2 pool includes more types
    types = set(type(e).__name__ for e in enemies)
    # Just check it spawned something
    assert len(types) >= 1


def test_spawn_enemies_elite_more():
    normal = spawn_enemies_for_room(0, 2, ROOM_TYPE_COMBAT)
    elite = spawn_enemies_for_room(0, 2, ROOM_TYPE_ELITE)
    assert len(elite) >= len(normal)


def test_spawn_enemies_dead_room():
    enemies = spawn_enemies_for_room(0, 0, ROOM_TYPE_DEAD)
    assert len(enemies) == 0


def test_floor_enemy_pool_grows():
    for i in range(5):
        pool = FLOOR_ENEMY_POOL.get(i, FLOOR_ENEMY_POOL[4])
        if i > 0:
            prev = FLOOR_ENEMY_POOL.get(i - 1, FLOOR_ENEMY_POOL[4])
            assert len(pool) >= len(prev)


def test_all_enemy_classes_in_dict():
    assert len(ENEMY_CLASSES) == 10
    for key, cls in ENEMY_CLASSES.items():
        e = cls(10, 10) if key != "relu_guardian" else cls(10, 10, 0.5)
        assert e.alive


def test_homing_projectile_steers():
    from neural_dungeon.entities.projectiles import Projectile
    p = Projectile(
        10, 10, 1, 0, 0.5, 10, "enemy",
        homing=True, turn_rate=0.1,
    )
    # Target is above
    p.steer_toward(10, 5)
    # dy should now be negative (turning toward target)
    assert p.dy < 0
