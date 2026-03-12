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

# Neon color per room type
ROOM_NEON = {
    ROOM_TYPE_COMBAT: rgb("cyan"),
    ROOM_TYPE_ELITE: rgb("bright_magenta"),
    ROOM_TYPE_DEAD: rgb("bright_black"),
    ROOM_TYPE_SHOP: rgb("bright_yellow"),
    ROOM_TYPE_WEIGHT: rgb("bright_blue"),
    ROOM_TYPE_BOSS: rgb("bright_red"),
    ROOM_TYPE_START: rgb("bright_green"),
    ROOM_TYPE_CHECKPOINT: rgb("bright_cyan"),
}

ROOM_LABELS = {
    ROOM_TYPE_COMBAT: "X",
    ROOM_TYPE_ELITE: "!",
    ROOM_TYPE_DEAD: "-",
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

# Legend entries: (label, color, description)
LEGEND = [
    ("X", rgb("cyan"), "Combat"),
    ("!", rgb("bright_magenta"), "Elite"),
    ("-", rgb("bright_black"), "Safe"),
    ("$", rgb("bright_yellow"), "Shop"),
    ("W", rgb("bright_blue"), "Weight"),
]


def render_map_screen(screen, floor_map, floor_num, tick=0):
    font = pygame.font.SysFont("consolas", 18)
    font_big = pygame.font.SysFont("consolas", 30, bold=True)
    font_sm = pygame.font.SysFont("consolas", 13)
    font_lbl = pygame.font.SysFont("consolas", 16, bold=True)

    screen.fill(BG_COLOR)

    # Title
    title = font_big.render(
        f"LAYER {floor_num + 1} — NEURAL MAP",
        True, rgb("bright_cyan"),
    )
    screen.blit(title, ((SCREEN_WIDTH - title.get_width()) // 2, 25))

    # Map bounds
    map_top = 90
    map_bottom = 500
    map_left = 120
    map_right = SCREEN_WIDTH - 120
    row_count = floor_map.num_rows
    node_radius = 24
    cursor_row = floor_map.cursor_row

    # Build node positions (row 0 at bottom)
    node_pos = {}
    for row in range(row_count):
        nodes = floor_map.get_row_nodes(row)
        if not nodes:
            continue
        y = int(
            map_bottom
            - (row / max(1, row_count - 1)) * (map_bottom - map_top)
        )
        # Always space for 4 columns evenly
        for i, node in enumerate(nodes):
            x = int(
                map_left
                + (i + 0.5) / floor_map.nodes_per_row
                * (map_right - map_left)
            )
            node_pos[node.id] = (x, y)

    # -- Draw connection lines first --
    for node in floor_map.nodes.values():
        if node.id not in node_pos:
            continue
        x1, y1 = node_pos[node.id]
        for conn_id in node.connections:
            if conn_id not in node_pos:
                continue
            x2, y2 = node_pos[conn_id]

            # Bright lines for connections from current row
            if node.row == cursor_row:
                line_color = (0, 100, 120)
                width = 2
            elif node.visited:
                line_color = (0, 50, 40)
                width = 2
            else:
                line_color = (20, 20, 30)
                width = 1
            pygame.draw.line(screen, line_color, (x1, y1), (x2, y2), width)

    # -- Draw nodes --
    for node in floor_map.nodes.values():
        if node.id not in node_pos:
            continue
        x, y = node_pos[node.id]
        neon = ROOM_NEON.get(node.room_type, rgb("white"))

        is_cursor = (
            node.row == cursor_row and node.col == floor_map.cursor_col
        )
        is_active_row = node.row == cursor_row
        is_visited = node.visited

        if is_cursor:
            # Selected node: bright magenta pulsing glow
            pulse = 0.6 + 0.4 * abs(math.sin(tick * 0.08))
            sel_color = rgb("bright_green")
            glow_r = node_radius + 8 + int(pulse * 5)

            # Outer glow ring
            glow_col = (
                int(sel_color[0] * pulse * 0.5),
                int(sel_color[1] * pulse * 0.5),
                int(sel_color[2] * pulse * 0.5),
            )
            pygame.draw.circle(screen, glow_col, (x, y), glow_r, 3)
            # Filled bg
            pygame.draw.circle(screen, (0, 30, 20), (x, y), node_radius)
            # Bright border
            pygame.draw.circle(screen, sel_color, (x, y), node_radius, 3)
            lbl_color = rgb("bright_white")

        elif is_active_row:
            # Traversable: neon glow based on room type
            pygame.draw.circle(
                screen, glow(neon, 0.25), (x, y), node_radius + 4,
            )
            pygame.draw.circle(screen, glow(neon, 0.15), (x, y), node_radius)
            pygame.draw.circle(screen, neon, (x, y), node_radius, 2)
            lbl_color = neon

        elif is_visited:
            # Already visited: dim green outline
            pygame.draw.circle(screen, (10, 25, 15), (x, y), node_radius)
            pygame.draw.circle(
                screen, glow(rgb("green"), 0.4), (x, y), node_radius, 2,
            )
            lbl_color = glow(rgb("green"), 0.5)

        else:
            # Not reachable yet / future: very dim
            pygame.draw.circle(screen, (12, 12, 18), (x, y), node_radius)
            pygame.draw.circle(screen, (30, 30, 40), (x, y), node_radius, 1)
            lbl_color = (50, 50, 60)

        # Room type letter
        label = ROOM_LABELS.get(node.room_type, "?")
        lbl = font_lbl.render(label, True, lbl_color)
        screen.blit(
            lbl, (x - lbl.get_width() // 2, y - lbl.get_height() // 2),
        )

    # -- Row indicators on the left --
    for row in range(row_count):
        nodes = floor_map.get_row_nodes(row)
        if not nodes:
            continue
        any_id = nodes[0].id
        if any_id not in node_pos:
            continue
        _, ry = node_pos[any_id]
        if row == cursor_row:
            marker_color = rgb("bright_cyan")
            marker = "▶"
        elif row < cursor_row:
            marker_color = glow(rgb("green"), 0.4)
            marker = "✓"
        else:
            marker_color = (30, 30, 40)
            marker = "·"
        m = font.render(marker, True, marker_color)
        screen.blit(m, (map_left - 50, ry - m.get_height() // 2))

    # -- Info panel for selected node --
    cursor_node = floor_map.get_cursor_node()
    if cursor_node:
        name = ROOM_NAMES.get(cursor_node.room_type, "Unknown")
        neon = ROOM_NEON.get(cursor_node.room_type, rgb("white"))

        # Box
        info_y = 530
        box_w = 400
        box_x = (SCREEN_WIDTH - box_w) // 2
        pygame.draw.rect(
            screen, (10, 10, 20), (box_x, info_y, box_w, 50),
        )
        pygame.draw.rect(
            screen, glow(neon, 0.5), (box_x, info_y, box_w, 50), 1,
        )

        name_surf = font.render(name, True, neon)
        screen.blit(name_surf, (box_x + 15, info_y + 5))

        act_str = f"activation: {cursor_node.activation:.2f}"
        act_surf = font_sm.render(act_str, True, rgb("bright_black"))
        screen.blit(act_surf, (box_x + 15, info_y + 28))

    # -- Legend --
    leg_x = 30
    leg_y = 600
    for label, color, desc in LEGEND:
        # Small circle
        pygame.draw.circle(screen, glow(color, 0.3), (leg_x + 8, leg_y + 8), 8)
        pygame.draw.circle(screen, color, (leg_x + 8, leg_y + 8), 8, 1)
        l = font_sm.render(label, True, color)
        screen.blit(l, (leg_x + 4, leg_y + 1))
        d = font_sm.render(desc, True, rgb("bright_black"))
        screen.blit(d, (leg_x + 22, leg_y + 2))
        leg_x += 22 + d.get_width() + 20

    # -- Controls --
    ctrl = font_sm.render(
        "\u2190 \u2192 Navigate    Enter Confirm    Q Back",
        True, rgb("bright_yellow"),
    )
    screen.blit(ctrl, ((SCREEN_WIDTH - ctrl.get_width()) // 2, 660))

    hint = font_sm.render(
        "Pick your path through the neural network",
        True, (40, 40, 50),
    )
    screen.blit(hint, ((SCREEN_WIDTH - hint.get_width()) // 2, 685))
