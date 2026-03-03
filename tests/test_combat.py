"""Tests for combat system."""
from neural_dungeon.entities.player import Player
from neural_dungeon.entities.enemies import Perceptron, Token
from neural_dungeon.entities.projectiles import Projectile, ProjectileManager
from neural_dungeon.combat.combat import (
    check_player_vs_enemy_bullets,
    check_player_bullets_vs_enemies,
    check_player_vs_enemy_contact,
)


def test_player_takes_damage():
    p = Player(10.0, 10.0)
    assert p.hp == 100
    p.take_damage(25)
    assert p.hp == 75
    assert p.alive


def test_player_dies():
    p = Player(10.0, 10.0)
    p.take_damage(100)
    assert p.hp == 0
    assert not p.alive


def test_player_invulnerable_during_iframes():
    p = Player(10.0, 10.0)
    p.iframes = 5
    dmg = p.take_damage(50)
    assert dmg == 0
    assert p.hp == 100


def test_enemy_takes_damage():
    e = Perceptron(20.0, 20.0)
    e.take_damage(10)
    assert e.hp == 15
    assert e.alive


def test_enemy_dies():
    e = Perceptron(20.0, 20.0)
    e.take_damage(25)
    assert e.hp == 0
    assert not e.alive


def test_bullet_collision_player():
    p = Player(10.0, 10.0)
    mgr = ProjectileManager()
    # Spawn enemy bullet at player position
    b = Projectile(10.0, 10.0, 0, 0, 0, 20, "enemy")
    mgr.spawn(b)
    dmg = check_player_vs_enemy_bullets(p, mgr)
    assert dmg == 20
    assert p.hp == 80
    assert not b.alive


def test_bullet_collision_enemy():
    e = Perceptron(20.0, 20.0)
    mgr = ProjectileManager()
    b = Projectile(20.0, 20.0, 0, 0, 0, 25, "player")
    mgr.spawn(b)
    killed = check_player_bullets_vs_enemies([e], mgr)
    assert len(killed) == 1
    assert not e.alive


def test_contact_damage():
    p = Player(10.0, 10.0)
    t = Token(10.0, 10.0)
    dmg = check_player_vs_enemy_contact(p, [t])
    assert dmg == 20
    assert p.hp == 80


def test_dodge_roll():
    p = Player(10.0, 10.0)
    p.set_move(1.0, 0.0)
    success = p.start_dodge()
    assert success
    assert p.dodging
    assert p.invulnerable


def test_projectile_despawns_out_of_bounds():
    b = Projectile(-5.0, -5.0, 0, 0, 1.0, 10, "player")
    b.update()
    assert not b.alive
