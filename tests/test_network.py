"""Tests for neural network and map generation."""
import torch
from neural_dungeon.network.dungeon_net import DungeonNet
from neural_dungeon.network.activation import compute_floor_activations
from neural_dungeon.network.weight_mapper import (
    activation_to_room_type,
    get_corridor_connections,
)
from neural_dungeon.world.map_graph import FloorMap
from neural_dungeon.world.floor import Floor
from neural_dungeon.config import (
    NETWORK_LAYERS, ROOM_TYPE_DEAD, ROOM_TYPE_ELITE,
    ROOM_TYPE_COMBAT,
)


def test_dungeon_net_creation():
    net = DungeonNet()
    assert len(net.layers) == 5
    assert net.layers[0].in_features == 32
    assert net.layers[0].out_features == 48


def test_forward_pass():
    net = DungeonNet()
    activations = net.get_activations()
    assert len(activations) == 5
    # Sigmoid output should be between 0 and 1
    for act in activations:
        assert act.min() >= 0.0
        assert act.max() <= 1.0


def test_compute_floor_activations():
    net = DungeonNet()
    result = compute_floor_activations(net)
    assert len(result) == 5
    assert len(result[0]) == 48  # first layer: 32 -> 48
    assert len(result[1]) == 64  # second layer: 48 -> 64


def test_activation_to_room_type():
    assert activation_to_room_type(0.01, 1, 4, 0) == ROOM_TYPE_DEAD
    assert activation_to_room_type(0.8, 1, 4, 0) == ROOM_TYPE_ELITE
    assert activation_to_room_type(0.5, 1, 4, 0) == ROOM_TYPE_COMBAT


def test_corridor_connections():
    w = torch.randn(4, 8)
    conns = get_corridor_connections(w, top_k=3)
    assert len(conns) == 4
    for c in conns:
        assert len(c) == 3


def test_weight_clamp():
    net = DungeonNet()
    # Set some weights way out of range
    with torch.no_grad():
        net.layers[0].weight.fill_(10.0)
    net.clamp_weights()
    assert net.layers[0].weight.max() <= 2.0


def test_floor_map_creation():
    net = DungeonNet()
    activations = compute_floor_activations(net)
    weight_matrix = net.get_weight_matrix(0)
    fmap = FloorMap(0, activations[0], weight_matrix)
    assert len(fmap.nodes) > 0
    assert fmap.cursor_row == 0


def test_floor_from_network():
    net = DungeonNet()
    activations = compute_floor_activations(net)
    weight_matrix = net.get_weight_matrix(0)
    floor = Floor.from_network(0, activations[0], weight_matrix)
    assert floor.has_map
    assert floor.floor_map is not None


def test_floor_map_path_selection():
    net = DungeonNet()
    activations = compute_floor_activations(net)
    weight_matrix = net.get_weight_matrix(0)
    fmap = FloorMap(0, activations[0], weight_matrix)

    # Walk through the map
    while not fmap.is_complete:
        fmap.confirm_selection()
        if not fmap.is_complete:
            fmap.move_cursor("up")
    fmap.confirm_selection()

    assert len(fmap.selected_path) > 0
