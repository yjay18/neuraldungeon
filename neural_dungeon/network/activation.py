"""Forward pass and activation computation for floor generation."""
import torch
from neural_dungeon.network.dungeon_net import DungeonNet


def compute_floor_activations(net: DungeonNet) -> list[list[float]]:
    """Run forward pass and return activations per floor as plain lists.

    Returns a list of 5 lists. Each inner list has one float per
    output neuron of that layer (i.e. one per room on that floor).
    """
    raw = net.get_activations()
    result = []
    for act_tensor in raw:
        # act_tensor shape: (1, out_features) — squeeze batch dim
        values = act_tensor.squeeze(0).tolist()
        result.append(values)
    return result
