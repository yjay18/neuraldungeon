"""Tests for door proximity, shop, and weight room."""
import pytest

from neural_dungeon.config import (
    DOOR_GAME_X, DOOR_GAME_Y, DOOR_INTERACT_RANGE,
    ROOM_WIDTH, ROOM_HEIGHT, ROOM_TYPE_SHOP, ROOM_TYPE_WEIGHT,
    ROOM_TYPE_COMBAT, WEAPON_GRADIENT_BEAM,
)
from neural_dungeon.entities.player import Player
from neural_dungeon.utils import distance
from neural_dungeon.world.room import Room, WEIGHT_OPTIONS


# === Door proximity ===

def test_door_position():
    assert DOOR_GAME_X == ROOM_WIDTH // 2
    assert DOOR_GAME_Y == 0


def test_door_range():
    assert DOOR_INTERACT_RANGE > 0


def test_player_near_door():
    p = Player(DOOR_GAME_X, 2)
    dist = distance(p.x, p.y, DOOR_GAME_X, DOOR_GAME_Y)
    assert dist <= DOOR_INTERACT_RANGE


def test_player_far_from_door():
    p = Player(ROOM_WIDTH / 2, ROOM_HEIGHT - 3)
    dist = distance(p.x, p.y, DOOR_GAME_X, DOOR_GAME_Y)
    assert dist > DOOR_INTERACT_RANGE


# === Shop room ===

def test_shop_room_is_cleared():
    room = Room(ROOM_TYPE_SHOP, 0, 0)
    assert room.cleared


def test_shop_generates_items():
    room = Room(ROOM_TYPE_SHOP, 0, 0)
    p = Player(10, 10)
    room.enter(player=p)
    assert len(room.shop_items) > 0


def test_shop_buy_success():
    room = Room(ROOM_TYPE_SHOP, 0, 0)
    p = Player(10, 10)
    p.data_fragments = 100
    room.enter(player=p)

    if room.shop_items:
        item = room.shop_items[0]
        old_frags = p.data_fragments
        msg = room.shop_buy(0, p)
        assert msg is not None
        assert p.data_fragments < old_frags


def test_shop_buy_not_enough_fragments():
    room = Room(ROOM_TYPE_SHOP, 0, 0)
    p = Player(10, 10)
    p.data_fragments = 0
    room.enter(player=p)

    if room.shop_items:
        msg = room.shop_buy(0, p)
        assert msg == "Not enough fragments!"


def test_shop_buy_invalid_index():
    room = Room(ROOM_TYPE_SHOP, 0, 0)
    p = Player(10, 10)
    room.enter(player=p)
    msg = room.shop_buy(99, p)
    assert msg is None


def test_shop_buy_removes_item():
    room = Room(ROOM_TYPE_SHOP, 0, 0)
    p = Player(10, 10)
    p.data_fragments = 200
    room.enter(player=p)

    if room.shop_items:
        count_before = len(room.shop_items)
        room.shop_buy(0, p)
        assert len(room.shop_items) == count_before - 1


# === Weight room ===

def test_weight_room_is_cleared():
    room = Room(ROOM_TYPE_WEIGHT, 0, 0)
    assert room.cleared


def test_weight_room_options():
    room = Room(ROOM_TYPE_WEIGHT, 0, 0)
    assert len(room.weight_options) == 3


def test_weight_pick_hp():
    room = Room(ROOM_TYPE_WEIGHT, 0, 0)
    p = Player(10, 10)
    old_max = p.max_hp
    msg = room.weight_pick(0, p)  # +15 HP
    assert msg is not None
    assert p.max_hp == old_max + 15
    assert room.weight_used


def test_weight_pick_speed():
    room = Room(ROOM_TYPE_WEIGHT, 0, 0)
    p = Player(10, 10)
    msg = room.weight_pick(1, p)  # +8% speed
    assert msg is not None
    assert p.speed_bonus == pytest.approx(0.08)


def test_weight_pick_damage():
    room = Room(ROOM_TYPE_WEIGHT, 0, 0)
    p = Player(10, 10)
    msg = room.weight_pick(2, p)  # +10% damage
    assert msg is not None
    assert p.damage_bonus == pytest.approx(0.10)


def test_weight_pick_only_once():
    room = Room(ROOM_TYPE_WEIGHT, 0, 0)
    p = Player(10, 10)
    room.weight_pick(0, p)
    msg = room.weight_pick(1, p)
    assert msg is None


def test_weight_pick_invalid_index():
    room = Room(ROOM_TYPE_WEIGHT, 0, 0)
    p = Player(10, 10)
    msg = room.weight_pick(99, p)
    assert msg is None


# === Boss room ===

def test_boss_room_spawns_boss():
    from neural_dungeon.config import ROOM_TYPE_BOSS
    room = Room(ROOM_TYPE_BOSS, 0, 1)  # floor 1 = Classifier
    room.enter()
    assert len(room.enemies) > 0
    assert room.enemies[0].is_boss
