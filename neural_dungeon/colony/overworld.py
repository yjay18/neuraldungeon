"""Overworld class — update loop, state management for colony mode."""
import pygame
from neural_dungeon.colony.config import (
    DIR_DOWN, DIR_UP, DIR_LEFT, DIR_RIGHT,
    TILE_SIGN, TILE_DOOR, TILE_PAVED,
    MAP_COLS, MAP_ROWS, SCALED_TILE,
)
from neural_dungeon.colony.player_colony import ColonyPlayer
from neural_dungeon.colony.camera import Camera
from neural_dungeon.colony.textbox import TextBox
from neural_dungeon.colony.renderer_colony import ColonyRenderer
from neural_dungeon.colony.maps.the_lanes import (
    LANES_BASE, LANES_OVERLAY, LOCATIONS, SIGN_LOCATIONS,
)


class Overworld:
    def __init__(self):
        # Player starts near the starter house (col 7, row 49)
        self.player = ColonyPlayer(7, 49)
        self.camera = Camera()
        self.textbox = TextBox()
        self.renderer = ColonyRenderer(LANES_BASE, LANES_OVERLAY)
        self.tick = 0

        # Snap camera to player start
        pcx, pcy = self.player.get_center_pixel()
        self.camera.snap_to(pcx, pcy)

        # Movement input state
        self._held_dir = None
        self._move_cooldown = 0

    def handle_event(self, event):
        """Handle a single pygame event. Returns 'exit' to go back."""
        if event.type != pygame.KEYDOWN:
            return None

        key = event.key

        # Text box active — dismiss on Enter/Space
        if self.textbox.active:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.textbox.dismiss()
            return None

        # Escape — back to level select
        if key == pygame.K_ESCAPE:
            return "exit"

        # Interaction — Enter/Space
        if key in (pygame.K_RETURN, pygame.K_SPACE):
            self._try_interact()
            return None

        return None

    def process_held_keys(self, keys):
        """Process held movement keys (called at 60fps)."""
        if self.textbox.active:
            return

        direction = None
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            direction = DIR_UP
        elif keys[pygame.K_DOWN] or keys[pygame.K_s]:
            direction = DIR_DOWN
        elif keys[pygame.K_LEFT] or keys[pygame.K_a]:
            direction = DIR_LEFT
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            direction = DIR_RIGHT

        if direction is not None:
            self.player.try_move(direction, LANES_BASE)

    def update(self):
        """Update at 60fps."""
        self.tick += 1
        self.player.update()

        # Camera follow
        pcx, pcy = self.player.get_center_pixel()
        self.camera.update(pcx, pcy)

        # Check bridge exit trigger
        if not self.textbox.active:
            px, py = self.player.tile_x, self.player.tile_y
            if 77 <= px <= 79 and 28 <= py <= 30:
                self.textbox.show("The Crossing \u2014 Coming Soon!")

    def render(self, screen):
        """Render the colony overworld."""
        self.renderer.render(screen, self.camera, self.player,
                             self.textbox, self.tick)

    def _try_interact(self):
        """Check if facing an interactable tile and show text."""
        fc, fr = self.player.get_facing_tile()
        if fc < 0 or fc >= MAP_COLS or fr < 0 or fr >= MAP_ROWS:
            return

        tile = LANES_BASE[fr][fc]
        if tile == TILE_SIGN or tile == TILE_DOOR:
            # Look up in sign_locations
            loc = SIGN_LOCATIONS.get((fc, fr))
            if loc:
                self.textbox.show(loc["text"])
            elif tile == TILE_DOOR:
                self.textbox.show("The door is locked.")
            elif tile == TILE_SIGN:
                self.textbox.show("...")
