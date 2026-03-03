"""Branching map display between floors (pygame version)."""
import math
import pygame
from neural_dungeon.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT,
    ROOM_TYPE_COMBAT, ROOM_TYPE_ELITE, ROOM_TYPE_DEAD,
    ROOM_TYPE_SHOP, ROOM_TYPE_WEIGHT, ROOM_TYPE_BOSS,
    ROOM_TYPE_START, ROOM_TYPE_CHECKPOINT,
)
from neural_dungeon.render.colors import (
    activation_to_color, rgb, glow, BG_COLOR,
)

ROOM_LABELS = {
    ROOM_TYPE_COMBAT: "X",
    ROOM_TYPE_ELITE: "!",
    ROOM_TYPE_DEAD: " ",
    ROOM_TYPE_SHOP: "$",
    ROOM_TYPE_WEIGHT: "W",
    ROOM_TYPE_BOSS: "B",
    ROOM_TYPE_START: ">",
    ROOM_TYPE_CHECKPOINT: "C",
}

ROOM_NAMES = {
    ROOM_TYPE_COMBAT: "Neuron Room",
    ROOM_TYPE_ELITE: "High-Activation Room",
    ROOM_TYPE_DEAD: "Dead Neuron (safe)",
    ROOM_TYPE_SHOP: "Memory Bank (shop)",
    ROOM_TYPE_WEIGHT: "Weight Room",
    ROOM_TYPE_BOSS: "Boss Node",
    ROOM_TYPE_START: "Entry Point",
    ROOM_TYPE_CHECKPOINT: "Checkpoint",
}


def render_map_screen(screen, floor_map, floor_num, tick=0):
    """Draw the branching map on the pygame screen."""
    font = pygame.font.SysFont("consolas", 16)
    font_big = pygame.font.SysFont("consolas", 28, bold=True)
    font_sm = pygame.font.SysFont("consolas", 14)

    screen.fill(BG_COLOR)

    # Title
    title = font_big.render(
        f"LAYER {floor_num + 1} - NEURAL MAP",
        True, rgb("bright_cyan"),
    )
    screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 30))

    # Map layout
    map_top = 100
    map_bottom = 520
    map_left = 150
    map_right = SCREEN_WIDTH - 150
    row_count = floor_map.num_rows

    # Compute node positions (row 0 at bottom, top row at top)
    node_positions = {}
    for row in range(row_count):
        nodes = floor_map.get_row_nodes(row)
        if not nodes:
            continue
        # Y: bottom row (0) at map_bottom, top row at map_top
        y = int(map_bottom - (row / max(1, row_count - 1)) * (map_bottom - map_top))
        col_count = len(nodes)
        for i, node in enumerate(nodes):
            x = int(
                map_left + (i + 0.5) / col_count * (map_right - map_left)
            )
            node_positions[node.id] = (x, y)

    # Draw connection lines first (behind nodes)
    for node in floor_map.nodes.values():
        if node.id not in node_positions:
            continue
        x1, y1 = node_positions[node.id]
        for conn_id in node.connections:
            if conn_id in node_positions:
                x2, y2 = node_positions[conn_id]
                pygame.draw.line(
                    screen, (30, 50, 60), (x1, y1), (x2, y2), 1,
                )

    # Draw nodes
    node_radius = 22
    for node in floor_map.nodes.values():
        if node.id not in node_positions:
            continue
        x, y = node_positions[node.id]
        color = activation_to_color(node.activation)

        is_cursor = (
            node.row == floor_map.cursor_row
            and node.col == floor_map.cursor_col
        )
        is_visited = node.visited

        if is_cursor:
            # Pulsing highlight
            pulse = abs(math.sin(tick * 0.08))
            glow_r = node_radius + 6 + int(pulse * 4)
            pygame.draw.circle(
                screen, rgb("bright_cyan"), (x, y), glow_r, 2,
            )
            pygame.draw.circle(screen, (0, 20, 40), (x, y), node_radius)
            pygame.draw.circle(screen, rgb("bright_white"), (x, y), node_radius, 2)
        elif is_visited:
            pygame.draw.circle(screen, glow(color, 0.2), (x, y), node_radius)
            pygame.draw.circle(screen, rgb("bright_green"), (x, y), node_radius, 2)
        else:
            pygame.draw.circle(screen, glow(color, 0.3), (x, y), node_radius)
            pygame.draw.circle(screen, color, (x, y), node_radius, 2)

        # Room type label
        label = ROOM_LABELS.get(node.room_type, "?")
        lbl_color = rgb("bright_white") if is_cursor else color
        lbl = font.render(label, True, lbl_color)
        screen.blit(lbl, (x - lbl.get_width() // 2, y - lbl.get_height() // 2))

    # Info about selected node
    cursor_node = floor_map.get_cursor_node()
    if cursor_node:
        name = ROOM_NAMES.get(cursor_node.room_type, "Unknown")
        info = font.render(
            f"Selected: {name}  (activation: {cursor_node.activation:.2f})",
            True, rgb("white"),
        )
        screen.blit(info, ((SCREEN_WIDTH - info.get_width()) // 2, 560))

    # Controls
    ctrl = font_sm.render(
        "Arrow Keys - Navigate    Enter - Confirm    Q - Back",
        True, rgb("bright_yellow"),
    )
    screen.blit(ctrl, ((SCREEN_WIDTH - ctrl.get_width()) // 2, 610))

    hint = font_sm.render(
        "Pick your path through the neural network",
        True, rgb("bright_black"),
    )
    screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, 640))
