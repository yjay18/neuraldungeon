"""Screen-level visual effects: lighting, scanlines, shake, vignette."""
import math
import random
import pygame


class ScreenEffects:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        # Screen shake state
        self.shake_intensity = 0.0
        self.shake_decay = 0.82

        # Pre-built overlays (built once)
        self._scanlines = self._build_scanlines()
        self._vignette = self._build_vignette()

        # Lighting surface (reused each frame)
        self._light_surf = pygame.Surface((width, height))

    def _build_scanlines(self):
        """Semi-transparent horizontal lines for CRT feel."""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(0, self.height, 3):
            pygame.draw.line(surf, (0, 0, 0, 25), (0, y), (self.width, y))
        return surf

    def _build_vignette(self):
        """Dark gradient from edges inward."""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cx, cy = self.width // 2, self.height // 2
        max_r = math.sqrt(cx * cx + cy * cy)
        steps = 15
        for i in range(steps):
            ratio = i / steps
            alpha = int(90 * (1 - ratio))
            rx = int(cx * (0.5 + ratio * 0.7))
            ry = int(cy * (0.5 + ratio * 0.7))
            rect = pygame.Rect(cx - rx, cy - ry, rx * 2, ry * 2)
            thick = max(2, int(max_r / steps))
            pygame.draw.ellipse(surf, (0, 0, 0, alpha), rect, thick)
        return surf

    def trigger_shake(self, intensity=6):
        self.shake_intensity = max(self.shake_intensity, intensity)

    def get_shake_offset(self):
        if self.shake_intensity < 0.5:
            self.shake_intensity = 0
            return 0, 0
        mag = int(self.shake_intensity)
        ox = random.randint(-mag, mag)
        oy = random.randint(-mag, mag)
        self.shake_intensity *= self.shake_decay
        return ox, oy

    def draw_scanlines(self, screen):
        screen.blit(self._scanlines, (0, 0))

    def draw_vignette(self, screen):
        screen.blit(self._vignette, (0, 0))

    def draw_lighting(self, screen, lights, ambient=20, poly_lights=None):
        """Multiplicative lighting overlay.

        lights: list of (px, py, radius, color_rgb, intensity_0to1)
        poly_lights: list of (polygon_screen_points, color_rgb, intensity_0to1)
        """
        amb = ambient
        self._light_surf.fill((amb, amb, amb + 5))

        for lx, ly, radius, color, intensity in lights:
            steps = 4
            for s in range(steps):
                frac = (steps - s) / steps
                r = int(radius * frac)
                if r < 1:
                    continue
                brightness = intensity * (1 - frac * 0.6)
                c = (
                    min(255, int(color[0] * brightness) + amb),
                    min(255, int(color[1] * brightness) + amb),
                    min(255, int(color[2] * brightness) + amb),
                )
                pygame.draw.circle(self._light_surf, c, (lx, ly), r)

        if poly_lights:
            for points, color, intensity in poly_lights:
                self._draw_poly_light(points, color, intensity, amb)

        screen.blit(self._light_surf, (0, 0), special_flags=pygame.BLEND_MULT)

    def _draw_poly_light(self, points, color, intensity, amb):
        """Draw a wall-occluded cone polygon on the light surface."""
        if len(points) < 3:
            return
        apex = points[0]
        steps = 3
        for s in range(steps):
            frac = (steps - s) / steps
            brightness = intensity * (1 - frac * 0.5)
            c = (
                min(255, int(color[0] * brightness) + amb),
                min(255, int(color[1] * brightness) + amb),
                min(255, int(color[2] * brightness) + amb),
            )
            # Scale polygon toward apex for gradient effect
            scaled = [apex]
            for p in points[1:]:
                sx = apex[0] + int((p[0] - apex[0]) * frac)
                sy = apex[1] + int((p[1] - apex[1]) * frac)
                scaled.append((sx, sy))
            if len(scaled) >= 3:
                pygame.draw.polygon(self._light_surf, c, scaled)
