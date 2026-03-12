"""Tests for weapon configurations."""
import pytest
import math

from neural_dungeon.config import WEAPONS, WEAPON_GRADIENT_BEAM


def test_all_weapons_have_required_fields():
    required = [
        "name", "damage", "fire_rate", "bullet_speed",
        "bullet_char", "bullet_color", "spread", "projectiles",
        "range", "piercing", "homing", "turn_rate",
    ]
    for key, winfo in WEAPONS.items():
        for field in required:
            assert field in winfo, f"Weapon {key} missing {field}"


def test_weapon_count():
    assert len(WEAPONS) == 8


def test_gradient_beam_is_default():
    assert WEAPON_GRADIENT_BEAM in WEAPONS
    w = WEAPONS[WEAPON_GRADIENT_BEAM]
    assert w["piercing"] is False
    assert w["homing"] is False
    assert w["projectiles"] == 1


def test_scatter_shot_spread():
    w = WEAPONS["scatter_shot"]
    assert w["projectiles"] == 3
    assert w["spread"] > 0


def test_pulse_cannon_high_damage():
    w = WEAPONS["pulse_cannon"]
    assert w["damage"] == 20
    assert w["fire_rate"] >= 10  # slow fire rate


def test_piercing_ray():
    w = WEAPONS["piercing_ray"]
    assert w["piercing"] is True


def test_homing_burst():
    w = WEAPONS["homing_burst"]
    assert w["homing"] is True
    assert w["turn_rate"] > 0


def test_sniper_long_range():
    w = WEAPONS["sniper"]
    assert w["range"] == 60
    assert w["damage"] == 15


def test_shotgun_blast():
    w = WEAPONS["shotgun_blast"]
    assert w["projectiles"] == 5
    assert w["spread"] == 30.0
    assert w["range"] == 15  # short range


def test_rapid_fire_fast():
    w = WEAPONS["rapid_fire"]
    assert w["fire_rate"] == 2
    assert w["bullet_speed"] == 1.2
