"""Colony player — grid position, smooth movement, animation frames."""
import os
import pygame
from neural_dungeon.colony.config import (
    SCALED_TILE, DIR_DOWN, DIR_UP, DIR_LEFT, DIR_RIGHT,
    WALKABLE_TILES, MAP_COLS, MAP_ROWS, PLAYER_MOVE_FRAMES,
)

# Target display height for PixelLab sprites (between 1 and 1.5 tiles)
_SPRITE_TARGET_H = 44

# Direction name -> config constant
_DIR_MAP = {
    "south": DIR_DOWN,
    "north": DIR_UP,
    "west": DIR_LEFT,
    "east": DIR_RIGHT,
}


def _load_pixellab_sprites(base_path):
    """Load PixelLab PNGs from rotations/ subfolder.

    Returns dict {DIR_DOWN: surface, ...} or None on failure.
    """
    rot_dir = os.path.join(base_path, "rotations")
    if not os.path.isdir(rot_dir):
        return None

    loaded = {}
    for filename in os.listdir(rot_dir):
        if not filename.endswith(".png"):
            continue
        name = filename[:-4].lower()  # e.g. "south", "north-east"
        if name not in _DIR_MAP:
            continue
        path = os.path.join(rot_dir, filename)
        try:
            surf = pygame.image.load(path)
            if pygame.display.get_surface() is not None:
                surf = surf.convert_alpha()
            loaded[_DIR_MAP[name]] = surf
        except pygame.error:
            continue

    # Need at least down to be usable
    if DIR_DOWN not in loaded:
        return None
    # Fill missing cardinals by flipping if possible
    if DIR_RIGHT not in loaded and DIR_LEFT in loaded:
        loaded[DIR_RIGHT] = pygame.transform.flip(
            loaded[DIR_LEFT], True, False)
    if DIR_LEFT not in loaded and DIR_RIGHT in loaded:
        loaded[DIR_LEFT] = pygame.transform.flip(
            loaded[DIR_RIGHT], True, False)
    if DIR_UP not in loaded:
        loaded[DIR_UP] = loaded[DIR_DOWN]

    # Scale to target height using nearest-neighbor
    for d in list(loaded):
        raw = loaded[d]
        ratio = _SPRITE_TARGET_H / raw.get_height()
        new_w = int(raw.get_width() * ratio)
        loaded[d] = pygame.transform.scale(raw, (new_w, _SPRITE_TARGET_H))

    return loaded


def _build_sprite_down():
    """14x20 chibi sprite facing down — big round head, small body."""
    s = pygame.Surface((14, 20), pygame.SRCALPHA)
    hair = (50, 35, 20)
    hair_h = (65, 48, 30)  # hair highlight
    skin = (215, 180, 140)
    eye = (30, 30, 35)
    vest = (80, 96, 56)
    vest_d = (60, 72, 40)
    belt = (50, 55, 35)
    pants = (70, 72, 62)
    boot = (30, 30, 30)
    # Hair top — rounded (rows 0-3)
    for x in range(4, 10):
        s.set_at((x, 0), hair)
    for x in range(3, 11):
        s.set_at((x, 1), hair)
        s.set_at((x, 2), hair)
    s.set_at((5, 0), hair_h)  # highlight strand
    # Side hair framing face
    for y in range(3, 7):
        s.set_at((3, y), hair)
        s.set_at((10, y), hair)
    # Face (rows 3-9) — rounded, inset
    for x in range(4, 10):
        for y in range(3, 9):
            s.set_at((x, y), skin)
    # Ears
    s.set_at((3, 5), skin)
    s.set_at((10, 5), skin)
    # Eyes (row 5) — 2 dots with gap
    s.set_at((5, 5), eye)
    s.set_at((8, 5), eye)
    # Mouth
    s.set_at((6, 7), (180, 120, 100))
    s.set_at((7, 7), (180, 120, 100))
    # Chin
    s.set_at((5, 9), skin)
    s.set_at((6, 9), skin)
    s.set_at((7, 9), skin)
    s.set_at((8, 9), skin)
    # Torso (rows 10-14) — narrower than head
    for x in range(4, 10):
        for y in range(10, 14):
            s.set_at((x, y), vest)
    # Shoulder pads
    s.set_at((4, 10), vest_d)
    s.set_at((9, 10), vest_d)
    s.set_at((4, 11), vest_d)
    s.set_at((9, 11), vest_d)
    # Pocket detail
    s.set_at((5, 12), vest_d)
    s.set_at((8, 12), vest_d)
    # Belt
    for x in range(4, 10):
        s.set_at((x, 14), belt)
    # Legs (rows 15-18) — 2px gap between
    for y in range(15, 19):
        for x in range(4, 6):
            s.set_at((x, y), pants)
        for x in range(8, 10):
            s.set_at((x, y), pants)
    # Boots
    for x in range(4, 6):
        s.set_at((x, 19), boot)
    for x in range(8, 10):
        s.set_at((x, 19), boot)
    return s


def _build_sprite_up():
    """Back view sprite — all hair, back of vest."""
    s = pygame.Surface((14, 20), pygame.SRCALPHA)
    hair = (50, 35, 20)
    hair_d = (40, 28, 15)
    vest = (80, 96, 56)
    vest_d = (60, 72, 40)
    belt = (50, 55, 35)
    pants = (70, 72, 62)
    boot = (30, 30, 30)
    # Hair — rounded head
    for x in range(4, 10):
        s.set_at((x, 0), hair)
    for x in range(3, 11):
        for y in range(1, 9):
            s.set_at((x, y), hair)
    s.set_at((4, 9), hair)
    s.set_at((5, 9), hair)
    s.set_at((8, 9), hair)
    s.set_at((9, 9), hair)
    # Hair detail lines
    s.set_at((5, 3), hair_d)
    s.set_at((8, 4), hair_d)
    # Torso — narrower
    for x in range(4, 10):
        for y in range(10, 14):
            s.set_at((x, y), vest)
    s.set_at((4, 10), vest_d)
    s.set_at((9, 10), vest_d)
    s.set_at((4, 11), vest_d)
    s.set_at((9, 11), vest_d)
    for x in range(4, 10):
        s.set_at((x, 14), belt)
    # Legs — gap between
    for y in range(15, 19):
        for x in range(4, 6):
            s.set_at((x, y), pants)
        for x in range(8, 10):
            s.set_at((x, y), pants)
    for x in range(4, 6):
        s.set_at((x, 19), boot)
    for x in range(8, 10):
        s.set_at((x, 19), boot)
    return s


def _build_sprite_left():
    """Side profile facing left — narrower body, round head."""
    s = pygame.Surface((14, 20), pygame.SRCALPHA)
    hair = (50, 35, 20)
    skin = (215, 180, 140)
    eye = (30, 30, 35)
    vest = (80, 96, 56)
    vest_d = (60, 72, 40)
    belt = (50, 55, 35)
    pants = (70, 72, 62)
    boot = (30, 30, 30)
    # Hair — rounded side view
    for x in range(4, 9):
        s.set_at((x, 0), hair)
    for x in range(3, 10):
        s.set_at((x, 1), hair)
        s.set_at((x, 2), hair)
    for y in range(3, 7):
        s.set_at((3, y), hair)
        s.set_at((4, y), hair)
    # Face — visible from side
    for x in range(5, 9):
        for y in range(3, 9):
            s.set_at((x, y), skin)
    # Nose bump
    s.set_at((9, 5), skin)
    s.set_at((9, 6), skin)
    # Eye
    s.set_at((7, 5), eye)
    # Chin
    s.set_at((6, 9), skin)
    s.set_at((7, 9), skin)
    # Torso — narrower
    for x in range(5, 9):
        for y in range(10, 14):
            s.set_at((x, y), vest)
    s.set_at((5, 10), vest_d)
    s.set_at((5, 11), vest_d)
    for x in range(5, 9):
        s.set_at((x, 14), belt)
    # Legs
    for y in range(15, 19):
        for x in range(5, 8):
            s.set_at((x, y), pants)
    for x in range(5, 8):
        s.set_at((x, 19), boot)
    return s


def _build_walk_frame(base, direction, step):
    """Create walk frame by shifting leg pixels."""
    s = base.copy()
    pants = (70, 72, 62)
    boot = (30, 30, 30)
    if direction in (DIR_DOWN, DIR_UP):
        # Clear existing legs
        for y in range(15, 20):
            for x in range(0, 14):
                if s.get_at((x, y))[3] > 0:
                    c = s.get_at((x, y))
                    if c[:3] == pants or c[:3] == boot:
                        s.set_at((x, y), (0, 0, 0, 0))
        offset = 1 if step == 1 else -1
        # Left leg (shifted narrower to match new body)
        for y in range(15, 19):
            for x in range(4, 6):
                ny = y + (offset if step == 1 else 0)
                if 0 <= ny < 20:
                    s.set_at((x, ny), pants)
        # Right leg
        for y in range(15, 19):
            for x in range(8, 10):
                ny = y + (-offset if step == 1 else 0)
                if 0 <= ny < 20:
                    s.set_at((x, ny), pants)
        # Boots
        bny_l = 19 + (offset if step == 1 else 0)
        bny_r = 19 + (-offset if step == 1 else 0)
        for x in range(4, 6):
            if 0 <= bny_l < 20:
                s.set_at((x, bny_l), boot)
        for x in range(8, 10):
            if 0 <= bny_r < 20:
                s.set_at((x, bny_r), boot)
    return s


class ColonyPlayer:
    def __init__(self, tile_x, tile_y):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.direction = DIR_DOWN

        # Smooth movement
        self.moving = False
        self.move_progress = 0  # 0 to PLAYER_MOVE_FRAMES
        self.target_tile_x = tile_x
        self.target_tile_y = tile_y
        self.walk_frame = 0  # 0=stand, 1=left step, 2=right step
        self._step_toggle = False

        # Build sprites
        self._build_sprites()

    def _build_sprites(self):
        # Try loading PixelLab PNGs — resolve relative to project root
        project_root = os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))))
        sprite_path = os.path.join(project_root, "assets", "two_player")
        pixellab = _load_pixellab_sprites(sprite_path)
        if pixellab is not None:
            self.sprites = {}
            self._use_pixellab = True
            for d in (DIR_DOWN, DIR_UP, DIR_LEFT, DIR_RIGHT):
                surf = pixellab.get(d, pixellab[DIR_DOWN])
                # Single frame — use same sprite for all walk frames
                self.sprites[d] = [surf, surf, surf]
            # Compute sprite dimensions for rendering offsets
            ref = self.sprites[DIR_DOWN][0]
            self._sprite_w = ref.get_width()
            self._sprite_h = ref.get_height()
        else:
            # Fallback: procedural sprites
            self._use_pixellab = False
            down = _build_sprite_down()
            up = _build_sprite_up()
            left = _build_sprite_left()
            right = pygame.transform.flip(left, True, False)
            self.sprites = {}
            for d, s in [(DIR_DOWN, down), (DIR_UP, up),
                         (DIR_LEFT, left), (DIR_RIGHT, right)]:
                stand = pygame.transform.scale(s, (28, 40))
                w1 = pygame.transform.scale(
                    _build_walk_frame(s, d, 1), (28, 40))
                w2 = pygame.transform.scale(
                    _build_walk_frame(s, d, 2), (28, 40))
                self.sprites[d] = [stand, w1, w2]
            self._sprite_w = 28
            self._sprite_h = 40

        # Shadow — sized relative to sprite
        sw = max(16, self._sprite_w // 2)
        self.shadow = pygame.Surface((sw, 6), pygame.SRCALPHA)
        pygame.draw.ellipse(self.shadow, (0, 0, 0, 50), (0, 0, sw, 6))

    def try_move(self, direction, base_layer):
        """Try to start moving in direction. Returns True if move started."""
        if self.moving:
            return False

        self.direction = direction
        dx, dy = 0, 0
        if direction == DIR_UP:
            dy = -1
        elif direction == DIR_DOWN:
            dy = 1
        elif direction == DIR_LEFT:
            dx = -1
        elif direction == DIR_RIGHT:
            dx = 1

        nx = self.tile_x + dx
        ny = self.tile_y + dy

        # Bounds check
        if nx < 0 or nx >= MAP_COLS or ny < 0 or ny >= MAP_ROWS:
            return False

        # Walkability check
        if base_layer[ny][nx] not in WALKABLE_TILES:
            return False

        self.target_tile_x = nx
        self.target_tile_y = ny
        self.moving = True
        self.move_progress = 0
        self._step_toggle = not self._step_toggle
        self.walk_frame = 1 if self._step_toggle else 2
        return True

    def update(self):
        """Update smooth movement. Call at 60fps."""
        if not self.moving:
            return
        self.move_progress += 1
        if self.move_progress >= PLAYER_MOVE_FRAMES:
            self.tile_x = self.target_tile_x
            self.tile_y = self.target_tile_y
            self.moving = False
            self.move_progress = 0
            self.walk_frame = 0

    def get_pixel_pos(self):
        """Get pixel position (center-bottom of sprite) for rendering."""
        if self.moving:
            t = self.move_progress / PLAYER_MOVE_FRAMES
            px = (self.tile_x + (self.target_tile_x - self.tile_x) * t)
            py = (self.tile_y + (self.target_tile_y - self.tile_y) * t)
        else:
            px = float(self.tile_x)
            py = float(self.tile_y)
        # Center of tile in pixels
        cx = px * SCALED_TILE + SCALED_TILE // 2
        cy = py * SCALED_TILE + SCALED_TILE  # bottom of tile
        return cx, cy

    def get_center_pixel(self):
        """Center pixel for camera targeting."""
        cx, cy = self.get_pixel_pos()
        return cx, cy - 20  # roughly center of sprite

    def get_facing_tile(self):
        """Return (col, row) of the tile the player is facing."""
        dx, dy = 0, 0
        if self.direction == DIR_UP:
            dy = -1
        elif self.direction == DIR_DOWN:
            dy = 1
        elif self.direction == DIR_LEFT:
            dx = -1
        elif self.direction == DIR_RIGHT:
            dx = 1
        return self.tile_x + dx, self.tile_y + dy

    def get_sprite(self):
        """Get current animation frame."""
        return self.sprites[self.direction][self.walk_frame]
