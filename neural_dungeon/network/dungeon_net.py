"""The dungeon IS a neural network. 5-layer MLP whose weights define the world."""
import torch
import torch.nn as nn
from neural_dungeon.config import NETWORK_LAYERS, WEIGHT_CLAMP


class DungeonNet(nn.Module):
    def __init__(self):
        super().__init__()
        self.layers = nn.ModuleList([
            nn.Linear(in_f, out_f) for in_f, out_f in NETWORK_LAYERS
        ])
        self._init_weights()

    def _init_weights(self):
        for layer in self.layers:
            nn.init.xavier_uniform_(layer.weight)
            nn.init.zeros_(layer.bias)

    def forward(self, x: torch.Tensor) -> list[torch.Tensor]:
        """Run forward pass, return activations for each layer."""
        activations = []
        for layer in self.layers:
            x = layer(x)
            x = torch.sigmoid(x)
            activations.append(x)
        return activations

    def get_activations(self) -> list[torch.Tensor]:
        """Run random input through, return per-layer activation vectors."""
        with torch.no_grad():
            x = torch.randn(1, NETWORK_LAYERS[0][0])
            return self.forward(x)

    def clamp_weights(self):
        lo, hi = WEIGHT_CLAMP
        with torch.no_grad():
            for layer in self.layers:
                layer.weight.clamp_(lo, hi)
                layer.bias.clamp_(lo, hi)

    def get_weight_matrix(self, floor_index: int) -> torch.Tensor:
        return self.layers[floor_index].weight.data

    def get_bias(self, floor_index: int) -> torch.Tensor:
        return self.layers[floor_index].bias.data
