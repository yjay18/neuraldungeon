"""Camera — follow player, clamp to map edges, smooth lerp."""
from neural_dungeon.colony.config import (
    MAP_PIXEL_W, MAP_PIXEL_H, VIEW_W, VIEW_H, CAMERA_LERP,
)


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0

    def update(self, target_x, target_y):
        """Lerp toward target (pixel coords of player center)."""
        self.x += (target_x - VIEW_W / 2 - self.x) * CAMERA_LERP
        self.y += (target_y - VIEW_H / 2 - self.y) * CAMERA_LERP
        # Clamp to map edges
        self.x = max(0, min(self.x, MAP_PIXEL_W - VIEW_W))
        self.y = max(0, min(self.y, MAP_PIXEL_H - VIEW_H))

    def snap_to(self, target_x, target_y):
        """Instantly center on target."""
        self.x = target_x - VIEW_W / 2
        self.y = target_y - VIEW_H / 2
        self.x = max(0, min(self.x, MAP_PIXEL_W - VIEW_W))
        self.y = max(0, min(self.y, MAP_PIXEL_H - VIEW_H))

    def apply(self, world_x, world_y):
        """Convert world pixel coords to screen coords."""
        return world_x - self.x, world_y - self.y

    @property
    def view_rect(self):
        """Return (x, y, w, h) of visible area in world coords."""
        return (self.x, self.y, VIEW_W, VIEW_H)
