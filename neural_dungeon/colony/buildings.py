"""Per-building feature assignment + drawing on top of base tiles."""
import pygame
from neural_dungeon.colony.config import (
    TILE_WALL, TILE_ROOF, TILE_DOOR, WALKABLE_TILES,
    SCALED_TILE, MAP_COLS, MAP_ROWS,
    ROOF_COLORS, WALL_COLORS, STARTER_HOUSE_ROOF,
)


def get_building_colors(bx, by):
    """Deterministic roof + wall color for building at top-left (bx, by)."""
    h = (bx * 7 + by * 13) % 100
    roof = ROOF_COLORS[h % len(ROOF_COLORS)]
    wall = WALL_COLORS[(h // 6) % len(WALL_COLORS)]
    return roof, wall


def _find_buildings(base_layer):
    """Detect buildings as connected components of WALL/ROOF/DOOR tiles.

    Returns list of (top_left_col, top_left_row, width, height) tuples.
    """
    visited = set()
    buildings = []
    structure_tiles = {TILE_WALL, TILE_ROOF, TILE_DOOR}

    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            if (c, r) in visited:
                continue
            if base_layer[r][c] not in structure_tiles:
                continue
            # BFS flood fill
            queue = [(c, r)]
            visited.add((c, r))
            min_c, max_c = c, c
            min_r, max_r = r, r
            while queue:
                qc, qr = queue.pop(0)
                min_c = min(min_c, qc)
                max_c = max(max_c, qc)
                min_r = min(min_r, qr)
                max_r = max(max_r, qr)
                for dc, dr in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                    nc, nr = qc + dc, qr + dr
                    if (nc, nr) in visited:
                        continue
                    if 0 <= nc < MAP_COLS and 0 <= nr < MAP_ROWS:
                        if base_layer[nr][nc] in structure_tiles:
                            visited.add((nc, nr))
                            queue.append((nc, nr))
            buildings.append(
                (min_c, min_r, max_c - min_c + 1, max_r - min_r + 1))
    return buildings


def _is_south_facing(base_layer, row, col):
    """True if this WALL/ROOF tile has a walkable tile directly south."""
    if row + 1 >= MAP_ROWS:
        return False
    return base_layer[row + 1][col] in WALKABLE_TILES


def build_roof_color_map(base_layer):
    """Create a per-tile roof color lookup from detected buildings.

    Returns dict mapping (col, row) -> roof_color for all structure tiles.
    """
    buildings = _find_buildings(base_layer)
    color_map = {}
    structure_tiles = {TILE_WALL, TILE_ROOF, TILE_DOOR}

    # Check if starter house (near cols 5-9, rows 45-48)
    for bx, by, bw, bh in buildings:
        roof, _ = get_building_colors(bx, by)
        # Starter house detection (building near 5,45)
        if 4 <= bx <= 10 and 44 <= by <= 49 and bw <= 6 and bh <= 5:
            roof = STARTER_HOUSE_ROOF
        for r in range(by, by + bh):
            for c in range(bx, bx + bw):
                if (0 <= r < MAP_ROWS and 0 <= c < MAP_COLS
                        and base_layer[r][c] in structure_tiles):
                    color_map[(c, r)] = roof
    return color_map


def build_south_face_map(base_layer):
    """Map of (col, row) -> True for south-facing wall tiles."""
    south_map = {}
    for r in range(MAP_ROWS):
        for c in range(MAP_COLS):
            if base_layer[r][c] in (TILE_WALL, TILE_DOOR):
                if _is_south_facing(base_layer, r, c):
                    south_map[(c, r)] = True
    return south_map


def draw_building_shadows(screen, base_layer, cam_x, cam_y,
                          view_w, view_h):
    """Draw gradient shadow strips south and east of buildings."""
    st = SCALED_TILE
    start_col = max(0, int(cam_x // st) - 1)
    end_col = min(MAP_COLS, int((cam_x + view_w) // st) + 2)
    start_row = max(0, int(cam_y // st) - 1)
    end_row = min(MAP_ROWS, int((cam_y + view_h) // st) + 2)

    structure_tiles = {TILE_WALL, TILE_ROOF, TILE_DOOR}
    shadow_surf = pygame.Surface((st, 10), pygame.SRCALPHA)
    for i in range(10):
        alpha = int(56 * (1 - i / 10))
        pygame.draw.line(shadow_surf, (0, 0, 0, alpha),
                         (0, i), (st, i))

    shadow_east = pygame.Surface((8, st), pygame.SRCALPHA)
    for i in range(8):
        alpha = int(38 * (1 - i / 8))
        pygame.draw.line(shadow_east, (0, 0, 0, alpha),
                         (i, 0), (i, st))

    for r in range(start_row, end_row):
        for c in range(start_col, end_col):
            if base_layer[r][c] not in structure_tiles:
                continue
            px = c * st - cam_x
            py = r * st - cam_y
            # South shadow
            if (r + 1 < MAP_ROWS
                    and base_layer[r + 1][c] in WALKABLE_TILES):
                screen.blit(shadow_surf, (px, py + st))
            # East shadow
            if (c + 1 < MAP_COLS
                    and base_layer[r][c + 1] in WALKABLE_TILES):
                screen.blit(shadow_east, (px + st, py))


def draw_building_features(screen, base_layer, roof_color_map,
                           south_face_map, cam_x, cam_y,
                           view_w, view_h):
    """Draw per-building features on south-facing walls and roofs."""
    st = SCALED_TILE
    start_col = max(0, int(cam_x // st) - 1)
    end_col = min(MAP_COLS, int((cam_x + view_w) // st) + 2)
    start_row = max(0, int(cam_y // st) - 1)
    end_row = min(MAP_ROWS, int((cam_y + view_h) // st) + 2)

    for r in range(start_row, end_row):
        for c in range(start_col, end_col):
            if (c, r) not in south_face_map:
                continue
            px = int(c * st - cam_x)
            py = int(r * st - cam_y)
            h = (c * 31 + r * 17) % 100

            # Feature selection
            if h < 15:
                _draw_awning(screen, px, py)
            elif h < 25:
                _draw_flower_box(screen, px, py)
            elif h < 35:
                _draw_ac_unit(screen, px, py)
            elif h < 45:
                _draw_wall_lamp(screen, px, py)

            # Roof features (on ROOF tiles that are NOT south-facing)
            if r > 0 and base_layer[r - 1][c] == TILE_ROOF:
                rr = r - 1
                rpx = int(c * st - cam_x)
                rpy = int(rr * st - cam_y)
                rh = (c * 43 + rr * 19) % 100
                if rh < 12:
                    _draw_water_tank(screen, rpx, rpy)
                elif rh < 20:
                    _draw_antenna(screen, rpx, rpy)
                elif rh < 28:
                    _draw_clothesline(screen, rpx, rpy)


def _draw_awning(screen, px, py):
    """Striped awning above window."""
    for i in range(0, 20, 4):
        color = (180, 50, 40) if (i // 4) % 2 == 0 else (240, 230, 210)
        pygame.draw.rect(screen, color, (px + 4 + i, py - 2, 4, 6))


def _draw_flower_box(screen, px, py):
    """Flower box under window area."""
    pygame.draw.rect(screen, (120, 80, 40), (px + 8, py + 20, 16, 4))
    for i in range(3):
        color = [(215, 58, 48), (228, 205, 52), (162, 75, 178)][i]
        pygame.draw.circle(screen, color, (px + 12 + i * 5, py + 18), 2)


def _draw_ac_unit(screen, px, py):
    """AC unit (grey box with vent lines)."""
    pygame.draw.rect(screen, (160, 160, 160), (px + 2, py + 14, 10, 8))
    pygame.draw.rect(screen, (130, 130, 130), (px + 2, py + 14, 10, 8), 1)
    for i in range(3):
        pygame.draw.line(screen, (130, 130, 130),
                         (px + 4, py + 16 + i * 2),
                         (px + 10, py + 16 + i * 2))


def _draw_wall_lamp(screen, px, py):
    """Wall lamp next to where door would be."""
    pygame.draw.rect(screen, (80, 80, 80), (px + 26, py + 4, 3, 8))
    pygame.draw.circle(screen, (255, 240, 180), (px + 27, py + 4), 3)


def _draw_water_tank(screen, px, py):
    """Water tank on roof (common in Indian colonies)."""
    pygame.draw.rect(screen, (150, 150, 150), (px + 10, py + 4, 12, 16))
    pygame.draw.rect(screen, (130, 130, 130), (px + 10, py + 4, 12, 16), 1)
    pygame.draw.rect(screen, (160, 160, 160), (px + 8, py + 2, 16, 4))


def _draw_antenna(screen, px, py):
    """TV antenna on roof."""
    pygame.draw.line(screen, (100, 100, 100),
                     (px + 16, py + 20), (px + 16, py + 4), 1)
    pygame.draw.line(screen, (100, 100, 100),
                     (px + 10, py + 8), (px + 22, py + 8), 1)
    pygame.draw.line(screen, (100, 100, 100),
                     (px + 12, py + 12), (px + 20, py + 12), 1)


def _draw_clothesline(screen, px, py):
    """Clothesline with tiny laundry."""
    pygame.draw.line(screen, (80, 80, 80),
                     (px + 2, py + 6), (px + 30, py + 6), 1)
    colors = [(200, 200, 220), (220, 180, 180), (180, 220, 180)]
    for i, color in enumerate(colors):
        lx = px + 6 + i * 8
        pygame.draw.rect(screen, color, (lx, py + 7, 4, 5))
