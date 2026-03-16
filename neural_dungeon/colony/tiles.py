"""Tile surface generation — procedural pixel art at 16x16, displayed at 2x."""
import random
import pygame
from neural_dungeon.colony.config import (
    TILE_SIZE, TILE_GROUND, TILE_GRASS, TILE_WALL, TILE_ROOF,
    TILE_TREE_TRUNK, TILE_FENCE, TILE_WATER, TILE_PATH,
    TILE_DOOR, TILE_TALL_GRASS, TILE_SIGN, TILE_FLOWER,
    TILE_PAVED, OVERLAY_CANOPY,
    COLOR_GROUND, COLOR_GROUND_SPECKLE, COLOR_GROUND_CRACK,
    COLOR_GROUND_HIGHLIGHT,
    COLOR_PAVED, COLOR_PAVED_EDGE, COLOR_PAVED_LINE,
    COLOR_PATH_BASE, COLOR_PATH_GAP, COLOR_PATH_MOSS,
    COLOR_GRASS_VARIANTS, COLOR_TALL_GRASS_BASE,
    COLOR_TALL_GRASS_BLADE, COLOR_TALL_GRASS_TIP,
    COLOR_WATER, COLOR_WATER_HIGHLIGHT,
    COLOR_WALL_FRONT, COLOR_WALL_SIDING, COLOR_WALL_FOUNDATION,
    COLOR_WALL_WINDOW_GLASS, COLOR_WALL_WINDOW_FRAME,
    COLOR_WALL_WINDOW_HIGHLIGHT,
    COLOR_DOOR_WOOD, COLOR_DOOR_FRAME, COLOR_DOOR_KNOB, COLOR_DOOR_PORCH,
    COLOR_TREE_TRUNK, COLOR_TREE_OUTLINE,
    COLOR_CANOPY_SHADOW, COLOR_CANOPY_MAIN,
    COLOR_CANOPY_HIGHLIGHT, COLOR_CANOPY_BRIGHT,
    COLOR_HEDGE_BASE, COLOR_HEDGE_DARK, COLOR_HEDGE_HIGHLIGHT,
    COLOR_SIGN_POST, COLOR_SIGN_BOARD, COLOR_SIGN_BORDER,
    FLOWER_COLORS, ROOF_COLORS, WALL_COLORS, STARTER_HOUSE_ROOF,
)

TS = TILE_SIZE  # 16


def _vary(color, amount=4):
    """Randomly vary each RGB channel by ±amount."""
    return tuple(max(0, min(255, c + random.randint(-amount, amount)))
                 for c in color)


def _dim(color, factor):
    return tuple(max(0, int(c * factor)) for c in color)


def _gen_ground_variants(count=6):
    """Generate dirt lane tile variants."""
    variants = []
    for vi in range(count):
        s = pygame.Surface((TS, TS))
        s.fill(COLOR_GROUND)
        random.seed(vi * 1000 + 42)
        # Speckle
        for _ in range(random.randint(5, 7)):
            x, y = random.randint(0, 15), random.randint(0, 15)
            s.set_at((x, y), COLOR_GROUND_SPECKLE)
        # Crack (40%)
        if random.random() < 0.4:
            cx = random.randint(3, 12)
            cy = random.randint(3, 12)
            length = random.randint(4, 6)
            for i in range(length):
                px = cx + i
                if 0 <= px < TS:
                    s.set_at((px, cy), COLOR_GROUND_CRACK)
        # Highlight pebbles
        for _ in range(random.randint(2, 3)):
            x, y = random.randint(0, 15), random.randint(0, 15)
            s.set_at((x, y), COLOR_GROUND_HIGHLIGHT)
        variants.append(s)
    return variants


def _gen_paved_variants(count=4):
    """Paved road variants — plain."""
    variants = []
    for vi in range(count):
        s = pygame.Surface((TS, TS))
        s.fill(COLOR_PAVED)
        random.seed(vi * 2000 + 99)
        for _ in range(random.randint(3, 4)):
            x, y = random.randint(0, 15), random.randint(0, 15)
            s.set_at((x, y), _vary(COLOR_PAVED, 6))
        # Edge curb
        for x in range(TS):
            s.set_at((x, 0), COLOR_PAVED_EDGE)
            s.set_at((x, 15), COLOR_PAVED_EDGE)
        variants.append(s)
    return variants


def _gen_paved_center_variants(count=4):
    """Paved road with dashed yellow center line."""
    variants = []
    for vi in range(count):
        s = pygame.Surface((TS, TS))
        s.fill(COLOR_PAVED)
        random.seed(vi * 2100 + 88)
        for _ in range(random.randint(3, 4)):
            x, y = random.randint(0, 15), random.randint(0, 15)
            s.set_at((x, y), _vary(COLOR_PAVED, 6))
        # Dashed yellow center line — horizontal: 4px dash, 3px gap
        # Use variant index to offset the dash pattern
        offset = (vi * 4) % 7
        for x in range(TS):
            pos_in_pattern = (x + offset) % 7
            if pos_in_pattern < 4:
                s.set_at((x, 7), COLOR_PAVED_LINE)
                s.set_at((x, 8), COLOR_PAVED_LINE)
        variants.append(s)
    return variants


def _gen_path_variants(count=4):
    """Cobblestone path variants — visible stone grid with mortar."""
    variants = []
    for vi in range(count):
        s = pygame.Surface((TS, TS))
        # Fill with mortar/gap color first
        s.fill(COLOR_PATH_GAP)
        random.seed(vi * 3000 + 77)
        # Stone grid 5x5 with 1px mortar gaps, offset every other row
        for sy in range(0, TS, 5):
            offset = 2 if (sy // 5) % 2 else 0
            for sx in range(offset, TS, 6):
                stone_color = _vary(COLOR_PATH_BASE, 6)
                for dy in range(min(4, TS - sy)):
                    for dx in range(min(5, TS - sx)):
                        s.set_at((sx + dx, sy + dy), stone_color)
        # Moss spots (15%)
        for _ in range(random.randint(0, 1)):
            mx, my = random.randint(2, 13), random.randint(2, 13)
            s.set_at((mx, my), COLOR_PATH_MOSS)
            s.set_at((mx + 1, my), COLOR_PATH_MOSS)
        variants.append(s)
    return variants


def _gen_grass_variants():
    """4 grass variants from color specs — subtle differences, blade marks."""
    variants = []
    for vi, (base, blade, highlight) in enumerate(COLOR_GRASS_VARIANTS):
        s = pygame.Surface((TS, TS))
        s.fill(base)
        random.seed(vi * 4000 + 55)
        # Blade marks on every variant (short 2-3px dark strokes)
        for _ in range(random.randint(6, 8)):
            bx = random.randint(1, 14)
            by = random.randint(4, 14)
            blade_len = random.randint(2, 3)
            for dy in range(blade_len):
                if by - dy >= 0:
                    s.set_at((bx, by - dy), blade)
        if highlight:
            for _ in range(random.randint(1, 2)):
                hx, hy = random.randint(2, 13), random.randint(2, 8)
                s.set_at((hx, hy), highlight)
        variants.append(s)
    return variants


def _gen_flower_variants(grass_variants, count=6):
    """Flower grass tiles — grass base + flower dots."""
    variants = []
    for vi in range(count):
        s = grass_variants[0].copy()
        random.seed(vi * 5000 + 33)
        num_flowers = random.randint(3, 4)
        chosen = random.sample(FLOWER_COLORS,
                               min(num_flowers, len(FLOWER_COLORS)))
        for fc in chosen:
            fx, fy = random.randint(2, 12), random.randint(2, 12)
            s.set_at((fx, fy), fc)
            s.set_at((fx + 1, fy), fc)
            s.set_at((fx, fy + 1), fc)
            s.set_at((fx + 1, fy + 1), fc)
        variants.append(s)
    return variants


def _gen_tall_grass_variants(count=4):
    """Wild/tall grass variants."""
    variants = []
    for vi in range(count):
        s = pygame.Surface((TS, TS))
        s.fill(COLOR_TALL_GRASS_BASE)
        random.seed(vi * 6000 + 11)
        for _ in range(random.randint(8, 10)):
            bx = random.randint(1, 14)
            by = random.randint(8, 14)
            blade_len = random.randint(5, 7)
            for dy in range(blade_len):
                if by - dy >= 0:
                    s.set_at((bx, by - dy), COLOR_TALL_GRASS_BLADE)
            # Bright tip
            if random.random() < 0.5:
                tip_y = by - blade_len + 1
                if tip_y >= 0:
                    s.set_at((bx, tip_y), COLOR_TALL_GRASS_TIP)
        variants.append(s)
    return variants


def _gen_wall_south():
    """South-facing wall tile (front face visible)."""
    s = pygame.Surface((TS, TS))
    # Shadow from roof overhang
    for x in range(TS):
        for y in range(3):
            s.set_at((x, y), (40, 35, 30))
    # Main wall face
    for x in range(TS):
        for y in range(3, 13):
            s.set_at((x, y), COLOR_WALL_FRONT)
    # Siding lines
    for y in (5, 8, 11):
        for x in range(TS):
            s.set_at((x, y), COLOR_WALL_SIDING)
    # Window (4x4 centered)
    for x in range(6, 10):
        for y in range(4, 8):
            s.set_at((x, y), COLOR_WALL_WINDOW_GLASS)
    # Window frame
    for x in range(5, 11):
        s.set_at((x, 3), COLOR_WALL_WINDOW_FRAME)
        s.set_at((x, 8), COLOR_WALL_WINDOW_FRAME)
    for y in range(3, 9):
        s.set_at((5, y), COLOR_WALL_WINDOW_FRAME)
        s.set_at((10, y), COLOR_WALL_WINDOW_FRAME)
    # Window highlight
    s.set_at((6, 4), COLOR_WALL_WINDOW_HIGHLIGHT)
    # Foundation
    for x in range(TS):
        for y in range(13, TS):
            s.set_at((x, y), COLOR_WALL_FOUNDATION)
    return s


def _gen_roof_tile(color):
    """Flat roof from above with ridge lines."""
    s = pygame.Surface((TS, TS))
    s.fill(color)
    ridge = _dim(color, 0.85)
    for x in range(TS):
        s.set_at((x, 5), ridge)
        s.set_at((x, 10), ridge)
    # Gradient: left lighter, right darker
    for y in range(TS):
        lc = tuple(min(255, c + 10) for c in color)
        s.set_at((0, y), lc)
        s.set_at((1, y), lc)
        rc = _dim(color, 0.92)
        s.set_at((14, y), rc)
        s.set_at((15, y), rc)
    return s


def _gen_door_tile():
    """Door tile — south-face wall with door."""
    s = _gen_wall_south()
    # Door (6x10)
    for x in range(5, 11):
        for y in range(4, 14):
            s.set_at((x, y), COLOR_DOOR_WOOD)
    # Frame
    for y in range(3, 15):
        s.set_at((4, y), COLOR_DOOR_FRAME)
        s.set_at((11, y), COLOR_DOOR_FRAME)
    for x in range(4, 12):
        s.set_at((x, 3), COLOR_DOOR_FRAME)
    # Knob
    s.set_at((9, 9), COLOR_DOOR_KNOB)
    s.set_at((9, 10), COLOR_DOOR_KNOB)
    # Porch strip
    for x in range(4, 12):
        s.set_at((x, 14), COLOR_DOOR_PORCH)
        s.set_at((x, 15), COLOR_DOOR_PORCH)
    return s


def _gen_tree_trunk(grass_base):
    """Tree trunk on grass base."""
    s = grass_base.copy()
    # Shadow ellipse
    for x in range(5, 11):
        for y in range(12, 15):
            if (x - 8) ** 2 + (y - 13) ** 2 * 2 < 12:
                c = s.get_at((x, y))
                s.set_at((x, y), _dim(c[:3], 0.7))
    # Trunk (4x6 centered)
    for x in range(6, 10):
        for y in range(6, 12):
            s.set_at((x, y), COLOR_TREE_TRUNK)
    # Outline
    for y in range(6, 12):
        s.set_at((5, y), COLOR_TREE_OUTLINE)
        s.set_at((10, y), COLOR_TREE_OUTLINE)
    for x in range(5, 11):
        s.set_at((x, 5), COLOR_TREE_OUTLINE)
    # Root flare
    s.set_at((5, 11), COLOR_TREE_TRUNK)
    s.set_at((10, 11), COLOR_TREE_TRUNK)
    return s


def _gen_canopy_variants(count=4):
    """Tree canopy overlay tiles."""
    variants = []
    for vi in range(count):
        s = pygame.Surface((TS, TS), pygame.SRCALPHA)
        random.seed(vi * 7000 + 22)
        cx, cy = 8, 8
        # Shadow circle
        sx, sy = cx + 2, cy + 3
        for x in range(TS):
            for y in range(TS):
                if (x - sx) ** 2 + (y - sy) ** 2 < 36:
                    s.set_at((x, y), COLOR_CANOPY_SHADOW + (200,))
        # Main circle
        for x in range(TS):
            for y in range(TS):
                if (x - cx) ** 2 + (y - cy) ** 2 < 56:
                    s.set_at((x, y), COLOR_CANOPY_MAIN + (220,))
        # Highlight
        hx, hy = cx - 2, cy - 2
        for x in range(TS):
            for y in range(TS):
                if (x - hx) ** 2 + (y - hy) ** 2 < 25:
                    s.set_at((x, y), COLOR_CANOPY_HIGHLIGHT + (200,))
        # Bright spot
        bx, by = cx - 3, cy - 4
        for x in range(TS):
            for y in range(TS):
                if (x - bx) ** 2 + (y - by) ** 2 < 9:
                    s.set_at((x, y), COLOR_CANOPY_BRIGHT + (180,))
        variants.append(s)
    return variants


def _gen_fence():
    """Hedge fence tile — rounded green mass."""
    s = pygame.Surface((TS, TS))
    s.fill(COLOR_HEDGE_BASE)
    # Rounded dark hedge mass
    for x in range(1, 15):
        for y in range(3, 11):
            # Round the corners
            if (x <= 2 or x >= 13) and (y <= 3 or y >= 10):
                continue
            s.set_at((x, y), COLOR_HEDGE_DARK)
    # Top highlight strip — slightly inset
    for x in range(2, 14):
        s.set_at((x, 3), COLOR_HEDGE_HIGHLIGHT)
        s.set_at((x, 4), COLOR_HEDGE_HIGHLIGHT)
    # Leaf detail — lighter spots
    s.set_at((5, 6), (40, 95, 35))
    s.set_at((10, 7), (40, 95, 35))
    # Shadow below hedge
    for x in range(2, 14):
        s.set_at((x, 11), _dim(COLOR_HEDGE_BASE, 0.7))
        s.set_at((x, 12), _dim(COLOR_HEDGE_BASE, 0.8))
    return s


def _gen_water_frames(count=4):
    """Water tile animation frames."""
    frames = []
    for fi in range(count):
        s = pygame.Surface((TS, TS))
        s.fill(COLOR_WATER)
        # Horizontal highlight streaks (shift per frame)
        for i in range(3):
            y = 4 + i * 4
            x_start = (fi * 2 + i * 5) % TS
            for dx in range(4):
                x = (x_start + dx) % TS
                s.set_at((x, y), COLOR_WATER_HIGHLIGHT)
        # Sparkle pixels
        random.seed(fi * 8000)
        for _ in range(2):
            sx = random.randint(1, 14)
            sy = random.randint(1, 14)
            s.set_at((sx, sy), (235, 242, 255))
        frames.append(s)
    return frames


def _gen_sign(ground_variant):
    """Sign post on ground."""
    s = ground_variant.copy()
    # Post
    for y in range(7, 15):
        s.set_at((7, y), COLOR_SIGN_POST)
        s.set_at((8, y), COLOR_SIGN_POST)
        s.set_at((9, y), COLOR_SIGN_POST)
    # Board
    for x in range(3, 13):
        for y in range(2, 8):
            s.set_at((x, y), COLOR_SIGN_BOARD)
    # Border
    for x in range(3, 13):
        s.set_at((x, 2), COLOR_SIGN_BORDER)
        s.set_at((x, 7), COLOR_SIGN_BORDER)
    for y in range(2, 8):
        s.set_at((3, y), COLOR_SIGN_BORDER)
        s.set_at((12, y), COLOR_SIGN_BORDER)
    return s


class TileCache:
    """Generates and caches all tile surfaces at startup."""

    def __init__(self):
        self.ground = _gen_ground_variants(6)
        self.paved = _gen_paved_variants(4)
        self.paved_center = _gen_paved_center_variants(4)
        self.path = _gen_path_variants(4)
        self.grass = _gen_grass_variants()
        self.flower = _gen_flower_variants(self.grass, 6)
        self.tall_grass = _gen_tall_grass_variants(4)
        self.wall_south = _gen_wall_south()
        self.door = _gen_door_tile()
        self.tree_trunk = _gen_tree_trunk(self.grass[0])
        self.canopy = _gen_canopy_variants(4)
        self.fence = _gen_fence()
        self.water_frames = _gen_water_frames(4)
        self.sign = _gen_sign(self.ground[0])

        # Roof tiles per color
        self.roof_tiles = {}
        for color in ROOF_COLORS:
            self.roof_tiles[color] = _gen_roof_tile(color)
        self.roof_tiles[STARTER_HOUSE_ROOF] = _gen_roof_tile(
            STARTER_HOUSE_ROOF)

        # Pre-scale all to 2x
        self.ground = [pygame.transform.scale2x(s) for s in self.ground]
        self.paved = [pygame.transform.scale2x(s) for s in self.paved]
        self.paved_center = [pygame.transform.scale2x(s)
                             for s in self.paved_center]
        self.path = [pygame.transform.scale2x(s) for s in self.path]
        self.grass = [pygame.transform.scale2x(s) for s in self.grass]
        self.flower = [pygame.transform.scale2x(s) for s in self.flower]
        self.tall_grass = [pygame.transform.scale2x(s)
                          for s in self.tall_grass]
        self.wall_south = pygame.transform.scale2x(self.wall_south)
        self.door = pygame.transform.scale2x(self.door)
        self.tree_trunk = pygame.transform.scale2x(self.tree_trunk)
        self.canopy = [pygame.transform.scale2x(s) for s in self.canopy]
        self.fence = pygame.transform.scale2x(self.fence)
        self.water_frames = [pygame.transform.scale2x(s)
                             for s in self.water_frames]
        self.sign = pygame.transform.scale2x(self.sign)
        for color in list(self.roof_tiles.keys()):
            self.roof_tiles[color] = pygame.transform.scale2x(
                self.roof_tiles[color])

    def get_tile(self, tile_id, row, col, tick=0, roof_color=None,
                 south_walkable=False, is_road_center=False):
        """Get the correct surface for a tile."""
        h = (col * 31 + row * 17 + col * row * 7)

        if tile_id == TILE_GROUND:
            return self.ground[h % len(self.ground)]
        elif tile_id == TILE_PAVED:
            if is_road_center:
                return self.paved_center[h % len(self.paved_center)]
            return self.paved[h % len(self.paved)]
        elif tile_id == TILE_PATH:
            return self.path[h % len(self.path)]
        elif tile_id == TILE_GRASS:
            return self.grass[h % len(self.grass)]
        elif tile_id == TILE_FLOWER:
            return self.flower[h % len(self.flower)]
        elif tile_id == TILE_TALL_GRASS:
            return self.tall_grass[h % len(self.tall_grass)]
        elif tile_id == TILE_WALL:
            if south_walkable:
                return self.wall_south
            elif roof_color and roof_color in self.roof_tiles:
                return self.roof_tiles[roof_color]
            else:
                return self.roof_tiles[ROOF_COLORS[h % len(ROOF_COLORS)]]
        elif tile_id == TILE_ROOF:
            if roof_color and roof_color in self.roof_tiles:
                return self.roof_tiles[roof_color]
            else:
                return self.roof_tiles[ROOF_COLORS[h % len(ROOF_COLORS)]]
        elif tile_id == TILE_DOOR:
            return self.door
        elif tile_id == TILE_TREE_TRUNK:
            return self.tree_trunk
        elif tile_id == TILE_FENCE:
            return self.fence
        elif tile_id == TILE_WATER:
            frame = (tick // 15) % len(self.water_frames)
            return self.water_frames[frame]
        elif tile_id == TILE_SIGN:
            return self.sign
        else:
            return self.ground[0]

    def get_canopy(self, row, col):
        h = (col * 31 + row * 17 + col * row * 7)
        return self.canopy[h % len(self.canopy)]
