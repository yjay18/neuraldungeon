"""Load PixelLab building sprites + explicit placement list."""
import os
import pygame
from neural_dungeon.colony.config import SCALED_TILE, MAP_COLS, MAP_ROWS

_SPRITE_DIR = "assets/buildings"
_TILESET_DIR = "assets/tilesets"

# Residential buildings — cycled by position hash
RESIDENTIAL_KEYS = [
    "crackhouse", "patchwork", "mossgrown",
    "hazardblock", "neonden", "cyansquat",
]

# All 15 available sprite keys
ALL_KEYS = [
    "chaistall", "communityhall", "crackhouse", "cyansquat",
    "databank", "glitchshrine", "hazardblock", "homebase",
    "mossgrown", "neonden", "neonshop", "overgrownruins",
    "patchwork", "quarantine", "transmissiontower",
]

# Explicit building placements: (col, row, sprite_key)
# col/row = top-left tile where the 64x64 sprite draws (covers 2x2 tiles)
# Positioned at south-center of each building footprint.
BUILDING_PLACEMENTS = [
    # --- North area: old ruins + your house compound ---
    (34, 8, "overgrownruins"),       # old ruins L
    (37, 8, "overgrownruins"),       # old ruins R
    (17, 9, "homebase"),             # north house compound

    # --- Upper row east of park (rows 11-18) ---
    (35, 13, "crackhouse"),          # bldg east of park L
    (40, 13, "patchwork"),           # bldg east of park R
    (46, 11, "hazardblock"),         # 4-bldg block row1
    (51, 11, "neonden"),
    (56, 11, "cyansquat"),
    (60, 11, "neonshop"),
    (66, 11, "patchwork"),           # 2-bldg block row1
    (72, 11, "mossgrown"),
    (46, 15, "crackhouse"),          # 4-bldg block row2
    (51, 15, "hazardblock"),
    (56, 15, "neonden"),
    (60, 15, "cyansquat"),
    (66, 15, "neonshop"),            # 2-bldg block row2
    (72, 15, "patchwork"),
    (35, 18, "mossgrown"),           # lower bldg east of park
    (40, 18, "hazardblock"),

    # --- Middle rows 33-40: two building groups ---
    (5, 34, "crackhouse"),           # group1 row1
    (10, 34, "patchwork"),
    (14, 34, "mossgrown"),
    (19, 34, "neonden"),             # group2 row1
    (24, 34, "cyansquat"),
    (28, 34, "hazardblock"),
    (5, 38, "neonshop"),             # group1 row2
    (10, 38, "crackhouse"),
    (14, 38, "patchwork"),
    (19, 38, "mossgrown"),           # group2 row2
    (24, 38, "hazardblock"),
    (28, 38, "neonden"),

    # --- Rows 43-52: starter house area ---
    (22, 44, "cyansquat"),           # bldg next to house row1 L
    (27, 44, "neonshop"),            # bldg next to house row1 R
    (6, 47, "homebase"),             # *** STARTER HOUSE ***
    (22, 48, "patchwork"),           # bldg next to house row2 L
    (27, 48, "crackhouse"),          # bldg next to house row2 R

    # --- Rows 55-64: buildings + bank ---
    (5, 56, "hazardblock"),          # 4-bldg block row1
    (10, 56, "neonden"),
    (15, 56, "cyansquat"),
    (20, 56, "mossgrown"),
    (25, 58, "databank"),            # *** BANK L ***
    (30, 58, "databank"),            # bank R
    (53, 57, "quarantine"),          # right-side buildings
    (59, 57, "transmissiontower"),
    (65, 57, "glitchshrine"),
    (71, 57, "chaistall"),
    (5, 60, "patchwork"),            # 4-bldg block row2
    (10, 60, "crackhouse"),
    (15, 60, "hazardblock"),
    (20, 60, "neonshop"),
    (5, 63, "neonden"),              # small bottom pair
    (10, 63, "mossgrown"),

    # --- Rows 65-74: bottom buildings ---
    (5, 68, "cyansquat"),            # 2-bldg block row1
    (11, 68, "crackhouse"),
    (21, 69, "communityhall"),       # bigger buildings
    (27, 69, "mossgrown"),
    (35, 69, "hazardblock"),
    (41, 69, "neonden"),
    (53, 69, "quarantine"),          # wild outskirts buildings
    (59, 69, "patchwork"),
    (5, 72, "neonshop"),             # 2-bldg block row2
    (11, 72, "chaistall"),
]


def _project_root():
    return os.path.dirname(os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))))


def load_building_sprites():
    """Load all building PNGs as a name->Surface dict.

    Returns dict of {name: Surface} at native 64x64, or empty dict.
    """
    sprite_dir = os.path.join(_project_root(), _SPRITE_DIR)
    if not os.path.isdir(sprite_dir):
        return {}

    sprites = {}
    for filename in sorted(os.listdir(sprite_dir)):
        if not filename.endswith(".png"):
            continue
        key = filename[:-4]
        path = os.path.join(sprite_dir, filename)
        try:
            surf = pygame.image.load(path)
            if pygame.display.get_surface() is not None:
                surf = surf.convert_alpha()
            sprites[key] = surf
        except pygame.error:
            continue
    return sprites


def load_wang_tilesets():
    """Load Wang tilesets from assets/tilesets/.

    Returns dict of {name: [16 Surfaces]} where each Surface is 32x32.
    """
    tileset_dir = os.path.join(_project_root(), _TILESET_DIR)
    if not os.path.isdir(tileset_dir):
        return {}

    tilesets = {}
    for filename in sorted(os.listdir(tileset_dir)):
        if not filename.endswith(".png"):
            continue
        key = filename[:-4]
        path = os.path.join(tileset_dir, filename)
        try:
            sheet = pygame.image.load(path)
            if pygame.display.get_surface() is not None:
                sheet = sheet.convert_alpha()
            tw = sheet.get_width() // 4
            th = sheet.get_height() // 4
            tiles = []
            for row in range(4):
                for col in range(4):
                    rect = pygame.Rect(col * tw, row * th, tw, th)
                    tile = sheet.subsurface(rect).copy()
                    if tile.get_size() != (SCALED_TILE, SCALED_TILE):
                        tile = pygame.transform.scale(
                            tile, (SCALED_TILE, SCALED_TILE))
                    tiles.append(tile)
            tilesets[key] = tiles
        except pygame.error:
            continue
    return tilesets


def get_building_placements(sprites):
    """Return list of (world_px, world_py, surface) for rendering.

    Filters BUILDING_PLACEMENTS to only entries with loaded sprites.
    """
    if not sprites:
        return []

    st = SCALED_TILE
    renders = []
    for col, row, key in BUILDING_PLACEMENTS:
        surf = sprites.get(key)
        if surf is None:
            continue
        renders.append((col * st, row * st, surf))
    return renders
