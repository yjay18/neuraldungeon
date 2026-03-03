"""Map weight matrices to room and corridor properties."""
import torch
from neural_dungeon.config import (
    ACTIVATION_DEAD, ACTIVATION_LOW, ACTIVATION_HIGH,
    ROOM_TYPE_COMBAT, ROOM_TYPE_ELITE, ROOM_TYPE_DEAD,
    ROOM_TYPE_SHOP, ROOM_TYPE_WEIGHT, ROOM_TYPE_BOSS,
    ROOM_TYPE_START,
)


def activation_to_room_type(
    activation: float,
    node_index: int,
    total_nodes: int,
    floor_index: int,
) -> str:
    """Decide room type from activation value and position on the map."""
    # Edge positions get special rooms
    if node_index == 0 and floor_index > 0:
        return ROOM_TYPE_SHOP
    if node_index == total_nodes - 1 and total_nodes > 2:
        return ROOM_TYPE_WEIGHT

    if activation < ACTIVATION_DEAD:
        return ROOM_TYPE_DEAD
    elif activation > ACTIVATION_HIGH:
        return ROOM_TYPE_ELITE
    else:
        return ROOM_TYPE_COMBAT


def get_corridor_connections(
    weight_matrix: torch.Tensor,
    top_k: int = 3,
) -> list[list[int]]:
    """For each output neuron (row), find the top-K strongest input connections.

    Returns list of lists: connections[output_neuron] = [input_neuron_indices].
    Negative weights become trap corridors (tracked separately).
    """
    out_features, in_features = weight_matrix.shape
    connections = []

    for i in range(out_features):
        row = weight_matrix[i]
        # Get top-K by absolute value
        abs_row = row.abs()
        k = min(top_k, in_features)
        _, indices = torch.topk(abs_row, k)
        connections.append(indices.tolist())

    return connections


def get_corridor_weights(
    weight_matrix: torch.Tensor,
    connections: list[list[int]],
) -> list[list[float]]:
    """Get the actual weight values for each connection.

    Negative = trap corridor, positive = safe corridor.
    """
    result = []
    for i, conns in enumerate(connections):
        weights = [weight_matrix[i][j].item() for j in conns]
        result.append(weights)
    return result
