"""Slay the Spire branching map built from neural network weights."""
import random
import torch
from neural_dungeon.config import (
    ROOM_TYPE_START, ROOM_TYPE_BOSS, ROOM_TYPE_SHOP,
    ROOM_TYPE_CHECKPOINT,
)
from neural_dungeon.network.weight_mapper import (
    activation_to_room_type,
    get_corridor_connections,
)


class MapNode:
    """A single node on the branching map."""
    def __init__(self, row: int, col: int, room_type: str, activation: float):
        self.row = row
        self.col = col
        self.room_type = room_type
        self.activation = activation
        self.connections: list[tuple[int, int]] = []  # (row, col) of connected nodes
        self.visited = False

    @property
    def id(self) -> tuple[int, int]:
        return (self.row, self.col)


class FloorMap:
    """Branching map for one floor, generated from network weights."""

    def __init__(
        self,
        floor_index: int,
        activations: list[float],
        weight_matrix: torch.Tensor,
        nodes_per_row: int = 4,
        num_rows: int = 4,
    ):
        self.floor_index = floor_index
        self.num_rows = num_rows
        self.nodes_per_row = nodes_per_row
        self.nodes: dict[tuple[int, int], MapNode] = {}
        self.selected_path: list[tuple[int, int]] = []
        self.cursor_row = 0
        self.cursor_col = 0

        self._build_map(activations, weight_matrix)

    def _build_map(self, activations: list[float], weight_matrix: torch.Tensor):
        """Build the branching map from activations and weight connections."""
        total_neurons = len(activations)

        # Pick a subset of neurons for each row of the map
        neurons_per_row = max(1, total_neurons // self.num_rows)

        for row in range(self.num_rows):
            start = row * neurons_per_row
            end = min(start + neurons_per_row, total_neurons)
            row_neurons = activations[start:end]

            # Pick nodes_per_row evenly spaced neurons from this chunk
            cols_count = min(self.nodes_per_row, len(row_neurons))
            step = max(1, len(row_neurons) // cols_count)

            for col in range(cols_count):
                idx = min(col * step, len(row_neurons) - 1)
                act = row_neurons[idx]
                global_idx = start + idx

                rtype = activation_to_room_type(
                    act, col, cols_count, self.floor_index,
                )
                node = MapNode(row, col, rtype, act)
                self.nodes[(row, col)] = node

        # Guarantee one shop per floor
        self._ensure_shop()

        # Build edges between adjacent rows using weight matrix
        self._build_edges(weight_matrix)

        # Make sure all nodes are reachable from row 0
        self._ensure_connectivity()

        # Set cursor to first node in bottom row (row 0)
        self.cursor_row = 0
        self.cursor_col = 0

    def _ensure_shop(self):
        """Make sure at least one node is a shop."""
        has_shop = any(
            n.room_type == ROOM_TYPE_SHOP for n in self.nodes.values()
        )
        if not has_shop:
            # Pick a middle-row node and make it a shop
            mid_row = self.num_rows // 2
            candidates = [
                n for n in self.nodes.values() if n.row == mid_row
            ]
            if candidates:
                random.choice(candidates).room_type = ROOM_TYPE_SHOP

    def _build_edges(self, weight_matrix: torch.Tensor):
        """Connect nodes in adjacent rows based on weight matrix."""
        for row in range(self.num_rows - 1):
            current_nodes = [
                n for n in self.nodes.values() if n.row == row
            ]
            next_nodes = [
                n for n in self.nodes.values() if n.row == row + 1
            ]
            if not current_nodes or not next_nodes:
                continue

            # Each current node connects to 1-3 nodes in the next row
            for node in current_nodes:
                # Pick connection count based on weight magnitudes
                num_conns = random.randint(1, min(3, len(next_nodes)))
                targets = random.sample(next_nodes, num_conns)
                for t in targets:
                    node.connections.append(t.id)

    def _ensure_connectivity(self):
        """Make sure every node in rows 1+ is reachable from row 0."""
        for row in range(1, self.num_rows):
            row_nodes = [n for n in self.nodes.values() if n.row == row]
            prev_nodes = [n for n in self.nodes.values() if n.row == row - 1]
            for node in row_nodes:
                # Check if any previous node connects here
                reachable = any(
                    node.id in p.connections for p in prev_nodes
                )
                if not reachable and prev_nodes:
                    # Add a connection from a random previous node
                    random.choice(prev_nodes).connections.append(node.id)

    def get_row_nodes(self, row: int) -> list[MapNode]:
        """Get all nodes in a given row, sorted by column."""
        nodes = [n for n in self.nodes.values() if n.row == row]
        nodes.sort(key=lambda n: n.col)
        return nodes

    def get_cursor_node(self) -> MapNode | None:
        return self.nodes.get((self.cursor_row, self.cursor_col))

    def get_reachable_next(self) -> list[MapNode]:
        """Get nodes the cursor can move to from current position."""
        node = self.get_cursor_node()
        if not node:
            return []
        return [
            self.nodes[conn_id]
            for conn_id in node.connections
            if conn_id in self.nodes
        ]

    def move_cursor(self, direction: str) -> bool:
        """Move cursor. Returns True if moved.

        'up' = advance to next row (pick from connections)
        'left'/'right' = switch between connected nodes in next row
        """
        if direction == "up":
            reachable = self.get_reachable_next()
            if not reachable:
                return False
            # Move to first reachable node in next row
            target = reachable[0]
            self.cursor_row = target.row
            self.cursor_col = target.col
            return True

        elif direction in ("left", "right"):
            reachable = self.get_reachable_next()
            if not reachable:
                # Stay in current row, shift column
                row_nodes = self.get_row_nodes(self.cursor_row)
                cols = [n.col for n in row_nodes]
                if self.cursor_col in cols:
                    idx = cols.index(self.cursor_col)
                    if direction == "left" and idx > 0:
                        self.cursor_col = cols[idx - 1]
                        return True
                    elif direction == "right" and idx < len(cols) - 1:
                        self.cursor_col = cols[idx + 1]
                        return True
                return False

            # Cycle through reachable nodes
            current_idx = 0
            for i, n in enumerate(reachable):
                if n.row == self.cursor_row and n.col == self.cursor_col:
                    current_idx = i
                    break

            if direction == "left":
                current_idx = (current_idx - 1) % len(reachable)
            else:
                current_idx = (current_idx + 1) % len(reachable)

            # Preview the target (don't commit yet)
            return True

        return False

    def confirm_selection(self) -> MapNode | None:
        """Confirm current cursor position and add to path."""
        node = self.get_cursor_node()
        if node:
            node.visited = True
            self.selected_path.append(node.id)
        return node

    @property
    def is_complete(self) -> bool:
        """Has the player reached the last row?"""
        return self.cursor_row >= self.num_rows - 1

    @property
    def path_rooms(self) -> list[MapNode]:
        """Get the rooms along the selected path."""
        return [self.nodes[nid] for nid in self.selected_path if nid in self.nodes]
