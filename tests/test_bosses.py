"""Tests for boss implementations."""
import pytest

from neural_dungeon.config import (
    CLASSIFIER_HP, AUTOENCODER_HP, GAN_HP,
    TRANSFORMER_HP, LOSS_FUNCTION_HP,
    ROOM_WIDTH, ROOM_HEIGHT,
)
from neural_dungeon.entities.bosses import (
    TheClassifier, TheAutoencoder,
    GANGenerator, GANDiscriminator,
    TransformerHead, TheTransformer, TheLossFunction,
    spawn_boss,
)


def test_classifier_init():
    boss = TheClassifier(30, 10)
    assert boss.hp == CLASSIFIER_HP
    assert boss.is_boss
    assert boss.boss_name == "The Classifier"


def test_classifier_fires_boundary():
    boss = TheClassifier(30, 10)
    boss.boundary_timer = 1
    bullets = boss.update(30, 20)
    assert len(bullets) >= 10  # boundary line


def test_classifier_phase2():
    boss = TheClassifier(30, 10)
    boss.hp = int(CLASSIFIER_HP * 0.4)  # below 50%
    boss.boundary_timer = 1
    bullets = boss.update(30, 20)
    assert len(bullets) >= 20  # fires both directions


def test_autoencoder_init():
    boss = TheAutoencoder(30, 10)
    assert boss.hp == AUTOENCODER_HP
    assert boss.boss_name == "The Autoencoder"


def test_autoencoder_burst():
    boss = TheAutoencoder(30, 10)
    boss.burst_timer = 1
    bullets = boss.update(30, 20)
    assert len(bullets) >= 4  # phase 1 = 4 bullets


def test_autoencoder_phase2_burst():
    boss = TheAutoencoder(30, 10)
    boss.hp = int(AUTOENCODER_HP * 0.4)
    boss.burst_timer = 1
    bullets = boss.update(30, 20)
    assert len(bullets) >= 8  # phase 2 = 8 bullets


def test_gan_generator_spawns_fakes():
    gen = GANGenerator(30, 10)
    gen.spawn_timer = 1
    gen.update(40, 10)
    assert len(gen.spawn_queue) == 2
    for fake in gen.spawn_queue:
        assert fake.contact_damage == 5
        assert fake.hp == 1


def test_gan_discriminator_shoots():
    disc = GANDiscriminator(30, 10)
    disc.shoot_timer = 1
    bullets = disc.update(40, 10)
    assert len(bullets) == 1
    assert bullets[0].owner == "enemy"


def test_gan_enrage():
    disc = GANDiscriminator(30, 10)
    disc.partner_alive = False
    disc.shoot_timer = 1
    disc.update(40, 10)
    assert disc.shoot_timer == 30  # faster CD when partner dead


def test_transformer_init():
    core = TheTransformer(30, 10)
    assert core.hp == TRANSFORMER_HP
    assert core.intangible  # starts intangible


def test_transformer_becomes_tangible():
    core = TheTransformer(30, 10)
    heads = []
    for i in range(4):
        head = TransformerHead(30, 10, i, core)
        heads.append(head)
    core.heads = heads

    # Kill all heads
    for h in heads:
        h.alive = False

    core.update(40, 10)
    assert not core.intangible


def test_transformer_head_orbits():
    core = TheTransformer(30, 12)
    head = TransformerHead(30, 12, 0, core)
    old_angle = head.orbit_angle
    head.update(40, 10)
    assert head.orbit_angle > old_angle


def test_loss_function_init():
    boss = TheLossFunction(30, 10)
    assert boss.hp == LOSS_FUNCTION_HP
    assert boss.boss_name == "The Loss Function"


def test_loss_function_spiral():
    boss = TheLossFunction(30, 10)
    boss.spiral_timer = 1
    boss.shoot_timer = 99  # don't fire aimed shot
    bullets = boss.update(40, 10)
    assert len(bullets) >= 8  # spiral = 8 bullets


def test_loss_function_phase3_teleport():
    boss = TheLossFunction(30, 10)
    boss.hp = int(LOSS_FUNCTION_HP * 0.2)  # phase 3
    boss.teleport_timer = 1
    boss.spiral_timer = 99
    boss.shoot_timer = 99
    old_x = boss.x
    boss.update(40, 10)
    # Teleport should have moved
    assert boss.x != old_x or boss.y != 10


def test_loss_function_tracks_positions():
    boss = TheLossFunction(30, 10)
    for _ in range(15):
        boss.spiral_timer = 999
        boss.shoot_timer = 999
        boss.update(40, 10)
    assert len(boss.player_positions) == 15


# === spawn_boss tests ===

def test_spawn_boss_floor_1():
    enemies = spawn_boss(1)
    assert len(enemies) == 1
    assert isinstance(enemies[0], TheClassifier)


def test_spawn_boss_floor_3():
    enemies = spawn_boss(3)
    assert len(enemies) == 1
    assert isinstance(enemies[0], TheAutoencoder)


def test_spawn_boss_floor_5():
    enemies = spawn_boss(5)
    assert len(enemies) == 2
    types = {type(e).__name__ for e in enemies}
    assert "GANGenerator" in types
    assert "GANDiscriminator" in types


def test_spawn_boss_floor_7():
    enemies = spawn_boss(7)
    assert len(enemies) == 5  # core + 4 heads
    assert isinstance(enemies[0], TheTransformer)
    for e in enemies[1:]:
        assert isinstance(e, TransformerHead)


def test_spawn_boss_floor_9():
    enemies = spawn_boss(9)
    assert len(enemies) == 1
    assert isinstance(enemies[0], TheLossFunction)


def test_spawn_boss_no_boss_floor():
    enemies = spawn_boss(2)
    assert len(enemies) == 0


def test_all_bosses_frozen():
    for floor_idx in [1, 3, 5, 7, 9]:
        enemies = spawn_boss(floor_idx)
        for e in enemies:
            e.frozen_timer = 5
            bullets = e.update(30, 10)
            assert bullets == []
            assert e.frozen_timer == 4
