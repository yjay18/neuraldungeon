"""Colony overworld constants — tile IDs, colors, movement, camera."""

# -- Tile IDs -----------------------------------------------------------------
TILE_GROUND = 0
TILE_GRASS = 1
TILE_WALL = 2
TILE_ROOF = 3
TILE_TREE_TRUNK = 4
TILE_FENCE = 5
TILE_WATER = 6
TILE_PATH = 7
TILE_DOOR = 8
TILE_TALL_GRASS = 9
TILE_SIGN = 10
TILE_FLOWER = 11
TILE_PAVED = 12

WALKABLE_TILES = {
    TILE_GROUND, TILE_GRASS, TILE_PATH, TILE_DOOR,
    TILE_TALL_GRASS, TILE_FLOWER, TILE_PAVED,
}

# Overlay tile IDs
OVERLAY_NONE = 0
OVERLAY_CANOPY = 5

# -- Map dimensions -----------------------------------------------------------
MAP_COLS = 80
MAP_ROWS = 75
TILE_SIZE = 16
DISPLAY_SCALE = 2
SCALED_TILE = TILE_SIZE * DISPLAY_SCALE  # 32

MAP_PIXEL_W = MAP_COLS * SCALED_TILE  # 2560
MAP_PIXEL_H = MAP_ROWS * SCALED_TILE  # 2400

# -- Camera / viewport -------------------------------------------------------
VIEW_W = 960
VIEW_H = 720
CAMERA_LERP = 0.15

# -- Player movement ----------------------------------------------------------
PLAYER_MOVE_FRAMES = 6  # frames to lerp between tiles at 60fps
PLAYER_TILES_PER_SEC = 6

# -- Directions ---------------------------------------------------------------
DIR_DOWN = 0
DIR_UP = 1
DIR_LEFT = 2
DIR_RIGHT = 3

# -- Decoration IDs -----------------------------------------------------------
DECO_NONE = 0
DECO_POTTED_PLANT = 1
DECO_TRASH_CAN = 2
DECO_BENCH = 3
DECO_STREET_LAMP = 4
DECO_MAILBOX = 5
DECO_BOLLARD = 6
DECO_BICYCLE = 7
DECO_FIRE_HYDRANT = 8
DECO_SCOOTER = 9
DECO_CRATES = 10
DECO_MANHOLE = 11

# -- Tile base colors ---------------------------------------------------------
COLOR_GROUND = (194, 176, 130)
COLOR_GROUND_SPECKLE = (178, 160, 114)
COLOR_GROUND_CRACK = (165, 148, 104)
COLOR_GROUND_HIGHLIGHT = (208, 192, 148)
COLOR_GROUND_CURB = (158, 142, 98)

COLOR_PAVED = (172, 168, 156)
COLOR_PAVED_EDGE = (148, 144, 132)
COLOR_PAVED_LINE = (215, 200, 65)

COLOR_PATH_BASE = (192, 184, 172)
COLOR_PATH_GAP = (168, 160, 148)
COLOR_PATH_MOSS = (105, 135, 78)

COLOR_GRASS_VARIANTS = [
    ((92, 165, 60), (72, 142, 45), (110, 180, 75)),    # base
    ((88, 160, 56), (68, 138, 42), None),               # slightly darker
    ((96, 170, 64), (76, 148, 50), (112, 182, 78)),    # slightly lighter
    ((90, 162, 58), (70, 140, 44), None),               # warm shift
]

COLOR_TALL_GRASS_BASE = (62, 132, 42)
COLOR_TALL_GRASS_BLADE = (42, 105, 28)
COLOR_TALL_GRASS_TIP = (85, 155, 55)

COLOR_WATER = (52, 115, 182)
COLOR_WATER_HIGHLIGHT = (72, 142, 208)
COLOR_WATER_SPARKLE = (235, 242, 255)

COLOR_WALL_FRONT = (220, 205, 182)
COLOR_WALL_SIDING = (200, 185, 162)
COLOR_WALL_FOUNDATION = (175, 160, 135)
COLOR_WALL_WINDOW_GLASS = (50, 60, 80)
COLOR_WALL_WINDOW_FRAME = (195, 182, 158)
COLOR_WALL_WINDOW_HIGHLIGHT = (200, 218, 240)

COLOR_DOOR_WOOD = (115, 75, 38)
COLOR_DOOR_FRAME = (72, 45, 18)
COLOR_DOOR_KNOB = (225, 200, 55)
COLOR_DOOR_PORCH = (172, 135, 85)

COLOR_TREE_TRUNK = (95, 62, 28)
COLOR_TREE_OUTLINE = (72, 45, 18)
COLOR_CANOPY_SHADOW = (25, 82, 25)
COLOR_CANOPY_MAIN = (42, 128, 42)
COLOR_CANOPY_HIGHLIGHT = (68, 162, 55)
COLOR_CANOPY_BRIGHT = (82, 175, 68)

COLOR_HEDGE_BASE = (88, 162, 58)
COLOR_HEDGE_DARK = (32, 82, 28)
COLOR_HEDGE_HIGHLIGHT = (48, 105, 42)

COLOR_SIGN_POST = (90, 60, 30)
COLOR_SIGN_BOARD = (192, 168, 128)
COLOR_SIGN_BORDER = (100, 75, 40)

FLOWER_COLORS = [
    (215, 58, 48),   # red
    (228, 205, 52),  # yellow
    (162, 75, 178),  # purple
    (238, 235, 228), # white
]

# -- Building colors ----------------------------------------------------------
ROOF_COLORS = [
    (185, 72, 48),    # red clay
    (88, 102, 138),   # blue-grey slate
    (148, 108, 58),   # brown tile
    (62, 128, 82),    # green metal
    (165, 82, 52),    # dark terracotta
    (115, 92, 128),   # purple-grey
]

WALL_COLORS = [
    (220, 208, 185),  # cream
    (210, 205, 215),  # lavender grey
    (205, 215, 200),  # sage
    (218, 210, 195),  # warm beige
    (202, 208, 218),  # light blue
    (225, 215, 200),  # peach
]

# Starter house has unique roof color
STARTER_HOUSE_ROOF = (178, 75, 42)

# -- Sky / atmosphere ---------------------------------------------------------
COLOR_SKY = (135, 195, 235)
COLOR_WARM_TINT = (255, 248, 235)
