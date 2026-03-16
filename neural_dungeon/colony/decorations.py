"""Pre-baked decoration placement + drawing."""
import pygame
from neural_dungeon.colony.config import (
    TILE_WALL, TILE_ROOF, TILE_DOOR, WALKABLE_TILES,
    SCALED_TILE, MAP_COLS, MAP_ROWS,
    DECO_NONE, DECO_POTTED_PLANT, DECO_TRASH_CAN, DECO_BENCH,
    DECO_STREET_LAMP, DECO_MAILBOX, DECO_BOLLARD, DECO_BICYCLE,
    DECO_FIRE_HYDRANT, DECO_SCOOTER, DECO_CRATES, DECO_MANHOLE,
)

STRUCTURE_TILES = {TILE_WALL, TILE_ROOF, TILE_DOOR}

# Decorations that render at ground level (under player)
GROUND_DECOS = {DECO_MANHOLE, DECO_BOLLARD}
# Decorations that render tall (above ground, but below player if behind)
TALL_DECOS = {DECO_STREET_LAMP}


def _any_adjacent_building(col, row, base_layer):
    """Check if any of the 8 neighbors is a building tile."""
    for dr in range(-1, 2):
        for dc in range(-1, 2):
            if dr == 0 and dc == 0:
                continue
            nr, nc = row + dr, col + dc
            if 0 <= nr < MAP_ROWS and 0 <= nc < MAP_COLS:
                if base_layer[nr][nc] in STRUCTURE_TILES:
                    return True
    return False


def compute_decorations(base_layer):
    """Compute decoration_layer[row][col] once at map load."""
    deco = [[DECO_NONE] * MAP_COLS for _ in range(MAP_ROWS)]

    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            if base_layer[r][c] not in WALKABLE_TILES:
                continue
            if not _any_adjacent_building(c, r, base_layer):
                # Road-only decorations (very sparse)
                if (c * 53 + r * 97) % 300 == 0:
                    deco[r][c] = DECO_STREET_LAMP
                continue
            h = (c * 31 + r * 17) % 100
            if h < 7:
                deco[r][c] = DECO_POTTED_PLANT
            elif h < 12:
                deco[r][c] = DECO_TRASH_CAN
            elif h < 15:
                deco[r][c] = DECO_BENCH
            elif h < 20:
                deco[r][c] = DECO_STREET_LAMP
            elif h < 23:
                deco[r][c] = DECO_MAILBOX
            elif h < 26:
                deco[r][c] = DECO_BOLLARD
            elif h < 28:
                deco[r][c] = DECO_BICYCLE
            elif h < 29:
                deco[r][c] = DECO_FIRE_HYDRANT
            elif h < 30:
                deco[r][c] = DECO_SCOOTER
            elif h < 31:
                deco[r][c] = DECO_CRATES
            elif h < 32:
                deco[r][c] = DECO_MANHOLE
            # else DECO_NONE (~68% empty)

    return deco


def draw_decoration(screen, deco_id, px, py):
    """Draw a single decoration at pixel position (px, py) = tile top-left."""
    st = SCALED_TILE
    cx = px + st // 2
    cy = py + st // 2

    if deco_id == DECO_POTTED_PLANT:
        # Terracotta pot
        pygame.draw.rect(screen, (178, 100, 50), (cx - 5, cy + 4, 10, 8))
        pygame.draw.rect(screen, (160, 85, 40), (cx - 6, cy + 3, 12, 3))
        # Green bush
        pygame.draw.circle(screen, (60, 130, 45), (cx, cy - 1), 6)
        pygame.draw.circle(screen, (75, 150, 55), (cx - 2, cy - 3), 4)

    elif deco_id == DECO_TRASH_CAN:
        pygame.draw.rect(screen, (140, 140, 140), (cx - 5, cy - 2, 10, 12))
        pygame.draw.rect(screen, (120, 120, 120), (cx - 5, cy - 2, 10, 12),
                         1)
        pygame.draw.rect(screen, (160, 160, 160), (cx - 6, cy - 4, 12, 3))

    elif deco_id == DECO_BENCH:
        # Seat
        pygame.draw.rect(screen, (130, 90, 50), (cx - 10, cy, 20, 4))
        # Legs
        pygame.draw.rect(screen, (100, 70, 35), (cx - 9, cy + 4, 3, 6))
        pygame.draw.rect(screen, (100, 70, 35), (cx + 6, cy + 4, 3, 6))
        # Back
        pygame.draw.rect(screen, (120, 85, 45), (cx - 10, cy - 4, 20, 3))

    elif deco_id == DECO_STREET_LAMP:
        # Post
        pygame.draw.rect(screen, (120, 120, 120), (cx - 1, cy - 10, 3, 22))
        # Lamp head
        pygame.draw.rect(screen, (180, 170, 140), (cx - 4, cy - 12, 9, 4))
        # Glow
        glow_surf = pygame.Surface((48, 48), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 240, 180, 15), (24, 24), 24)
        screen.blit(glow_surf, (cx - 24, cy - 36))

    elif deco_id == DECO_MAILBOX:
        pygame.draw.rect(screen, (80, 80, 80), (cx - 1, cy, 3, 10))
        pygame.draw.rect(screen, (200, 60, 50), (cx - 5, cy - 4, 10, 7))
        pygame.draw.rect(screen, (170, 50, 40), (cx - 5, cy - 4, 10, 7), 1)

    elif deco_id == DECO_BOLLARD:
        pygame.draw.rect(screen, (180, 175, 165), (cx - 3, cy - 2, 6, 10))
        pygame.draw.rect(screen, (160, 155, 145), (cx - 3, cy - 2, 6, 10),
                         1)

    elif deco_id == DECO_BICYCLE:
        # Frame
        pygame.draw.line(screen, (50, 80, 150), (cx - 6, cy), (cx, cy - 5),
                         2)
        pygame.draw.line(screen, (50, 80, 150), (cx, cy - 5), (cx + 6, cy),
                         2)
        # Wheels
        pygame.draw.circle(screen, (60, 60, 60), (cx - 6, cy + 2), 4, 1)
        pygame.draw.circle(screen, (60, 60, 60), (cx + 6, cy + 2), 4, 1)

    elif deco_id == DECO_FIRE_HYDRANT:
        pygame.draw.rect(screen, (200, 45, 35), (cx - 4, cy - 2, 8, 12))
        pygame.draw.rect(screen, (220, 55, 45), (cx - 6, cy, 12, 3))
        pygame.draw.circle(screen, (180, 40, 30), (cx, cy - 3), 4)

    elif deco_id == DECO_SCOOTER:
        # Body
        pygame.draw.rect(screen, (60, 80, 120), (cx - 6, cy - 4, 12, 6))
        # Wheels
        pygame.draw.circle(screen, (50, 50, 50), (cx - 5, cy + 4), 3)
        pygame.draw.circle(screen, (50, 50, 50), (cx + 5, cy + 4), 3)
        # Handle
        pygame.draw.line(screen, (80, 80, 80), (cx + 4, cy - 4),
                         (cx + 6, cy - 8), 2)

    elif deco_id == DECO_CRATES:
        pygame.draw.rect(screen, (150, 120, 70), (cx - 6, cy - 2, 8, 8))
        pygame.draw.rect(screen, (130, 100, 55), (cx - 6, cy - 2, 8, 8), 1)
        pygame.draw.rect(screen, (160, 130, 80), (cx - 2, cy - 6, 7, 7))
        pygame.draw.rect(screen, (140, 110, 60), (cx - 2, cy - 6, 7, 7), 1)

    elif deco_id == DECO_MANHOLE:
        pygame.draw.ellipse(screen, (80, 80, 80), (cx - 7, cy - 3, 14, 10))
        pygame.draw.ellipse(screen, (60, 60, 60), (cx - 7, cy - 3, 14, 10),
                            1)
        # Cross pattern
        pygame.draw.line(screen, (60, 60, 60), (cx - 4, cy + 1),
                         (cx + 4, cy + 1), 1)
        pygame.draw.line(screen, (60, 60, 60), (cx, cy - 2),
                         (cx, cy + 4), 1)
