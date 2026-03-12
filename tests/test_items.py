"""Tests for items, shop, and drop system."""
import pytest

from neural_dungeon.config import (
    WEAPON_GRADIENT_BEAM, WEAPON_SCATTER_SHOT, WEAPONS,
    WEAPON_COST, PASSIVE_COST, ACTIVE_COST,
)
from neural_dungeon.entities.items import (
    PASSIVE_ITEMS, ACTIVE_ITEMS, SHOP_WEAPONS,
    generate_shop_items, roll_item_drop,
)
from neural_dungeon.entities.player import Player


# === Item definitions ===

def test_passive_items_count():
    assert len(PASSIVE_ITEMS) == 10


def test_active_items_count():
    assert len(ACTIVE_ITEMS) == 6


def test_all_passives_have_required_fields():
    for key, item in PASSIVE_ITEMS.items():
        assert "name" in item
        assert "desc" in item
        assert "cost" in item
        assert item["cost"] == PASSIVE_COST


def test_all_actives_have_required_fields():
    for key, item in ACTIVE_ITEMS.items():
        assert "name" in item
        assert "desc" in item
        assert "cost" in item
        assert "cooldown" in item
        assert item["cost"] == ACTIVE_COST
        assert item["cooldown"] > 0


def test_shop_weapons_list():
    assert len(SHOP_WEAPONS) == 7
    assert WEAPON_GRADIENT_BEAM not in SHOP_WEAPONS


# === Shop generation ===

def test_generate_shop_items_returns_items():
    items = generate_shop_items(WEAPON_GRADIENT_BEAM, [], None)
    assert len(items) == 3
    types = {i["type"] for i in items}
    assert "weapon" in types
    assert "passive" in types
    assert "active" in types


def test_generate_shop_no_duplicate_weapon():
    items = generate_shop_items(WEAPON_SCATTER_SHOT, [], None)
    weapons = [i for i in items if i["type"] == "weapon"]
    for w in weapons:
        assert w["id"] != WEAPON_SCATTER_SHOT


def test_generate_shop_no_duplicate_passive():
    all_passives = list(PASSIVE_ITEMS.keys())
    items = generate_shop_items(WEAPON_GRADIENT_BEAM, all_passives, None)
    passives = [i for i in items if i["type"] == "passive"]
    assert len(passives) == 0


# === Item drops ===

def test_drop_combat_returns_passive_or_none():
    for _ in range(100):
        drop = roll_item_drop("combat", WEAPON_GRADIENT_BEAM, [], None)
        if drop is not None:
            assert drop["type"] == "passive"


def test_drop_boss_guaranteed():
    drops = [roll_item_drop("boss", WEAPON_GRADIENT_BEAM, [], None) for _ in range(50)]
    non_none = [d for d in drops if d is not None]
    assert len(non_none) > 30  # should be most of them


def test_drop_no_duplicate_passive():
    all_passives = list(PASSIVE_ITEMS.keys())
    drop = roll_item_drop("combat", WEAPON_GRADIENT_BEAM, all_passives, None)
    assert drop is None  # no passives left to drop


# === Player item mechanics ===

def test_player_has_passive():
    p = Player(10, 10)
    assert not p.has_passive("overclocked_core")
    p.add_passive("overclocked_core")
    assert p.has_passive("overclocked_core")


def test_player_add_passive_no_duplicates():
    p = Player(10, 10)
    p.add_passive("overclocked_core")
    p.add_passive("overclocked_core")
    assert p.passive_items.count("overclocked_core") == 1


def test_player_ram_upgrade():
    p = Player(10, 10)
    old_max = p.max_hp
    p.add_passive("ram_upgrade")
    assert p.max_hp == old_max + 25
    assert p.hp >= old_max  # healed


def test_player_overclocked_core_damage():
    p = Player(10, 10)
    base = p.get_effective_damage(10)
    p.add_passive("overclocked_core")
    boosted = p.get_effective_damage(10)
    assert boosted > base


def test_player_kernel_expansion_range():
    p = Player(10, 10)
    base = p.get_effective_range(40)
    p.add_passive("kernel_expansion")
    boosted = p.get_effective_range(40)
    assert boosted == 50.0  # 40 * 1.25


def test_player_heat_sink():
    p = Player(10, 10)
    p.add_passive("heat_sink")
    p.shooting = True
    p.on_shoot()
    # Fire rate should be reduced by 20%
    expected = max(1, int(p.weapon_info["fire_rate"] * 0.8))
    assert p.shoot_cooldown == expected


def test_player_skip_connection():
    p = Player(10, 10)
    p.add_passive("skip_connection")
    p.move_dx = 1.0
    p.start_dodge()
    from neural_dungeon.config import PLAYER_IFRAMES
    assert p.iframes == PLAYER_IFRAMES + 3


def test_player_bias_shift():
    p = Player(10, 10)
    p.add_passive("bias_shift")
    dmg = p.take_contact_damage(10)
    assert dmg == 7  # 10 - 3


def test_player_bias_shift_minimum():
    p = Player(10, 10)
    p.add_passive("bias_shift")
    dmg = p.take_contact_damage(2)
    assert dmg == 1  # min 1


def test_player_damage_bonus():
    p = Player(10, 10)
    p.damage_bonus = 0.5
    dmg = p.get_effective_damage(10)
    assert dmg == 15  # 10 * 1.5


def test_player_speed_bonus():
    p = Player(10, 10)
    p.speed_bonus = 0.1
    p.move_dx = 1.0
    old_x = p.x
    p.update()
    moved = p.x - old_x
    # With 10% speed bonus should move faster than base
    p2 = Player(10, 10)
    p2.move_dx = 1.0
    old_x2 = p2.x
    p2.update()
    moved2 = p2.x - old_x2
    assert moved > moved2


def test_player_active_item():
    p = Player(10, 10)
    p.active_item = "memory_dump"
    assert p.can_use_active()
    item_id = p.use_active()
    assert item_id == "memory_dump"
    assert p.active_item_cooldown > 0
    assert not p.can_use_active()


def test_player_active_item_none():
    p = Player(10, 10)
    assert not p.can_use_active()
    assert p.use_active() is None
