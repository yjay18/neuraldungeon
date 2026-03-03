"""Tests for map/floor system."""
from neural_dungeon.world.floor import Floor
from neural_dungeon.world.room import Room
from neural_dungeon.config import ROOM_TYPE_START, ROOM_TYPE_COMBAT


def test_floor_generation():
    f = Floor(0, 5)
    assert len(f.rooms) == 5
    assert f.rooms[0].room_type == ROOM_TYPE_START
    assert f.current_room_index == 0


def test_floor_advance():
    f = Floor(0, 3)
    assert f.current_room_index == 0
    room = f.advance_room()
    assert room is not None
    assert f.current_room_index == 1


def test_floor_last_room():
    f = Floor(0, 2)
    f.advance_room()
    assert f.is_last_room
    assert f.advance_room() is None


def test_room_clear_state():
    r = Room(ROOM_TYPE_START, 0, 0)
    assert r.cleared  # start room is always cleared


def test_room_enter_spawns_enemies():
    r = Room(ROOM_TYPE_COMBAT, 1, 0)
    assert not r.entered
    r.enter()
    assert r.entered
    assert len(r.enemies) > 0
