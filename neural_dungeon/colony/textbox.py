"""Pokemon-style text box — show/dismiss."""
import pygame


class TextBox:
    def __init__(self):
        self.active = False
        self.text = ""
        self._font = None

    def _get_font(self):
        if self._font is None:
            self._font = pygame.font.SysFont("couriernew", 20)
        return self._font

    def show(self, text):
        self.active = True
        self.text = text

    def dismiss(self):
        self.active = False
        self.text = ""

    def draw(self, screen):
        if not self.active:
            return
        box = pygame.Surface((860, 100), pygame.SRCALPHA)
        pygame.draw.rect(box, (0, 0, 0, 220), (0, 0, 860, 100),
                         border_radius=12)
        pygame.draw.rect(box, (200, 200, 200), (0, 0, 860, 100),
                         2, border_radius=12)
        screen.blit(box, (50, 570))
        font = self._get_font()
        text_surf = font.render(self.text, True, (255, 255, 255))
        screen.blit(text_surf, (70, 595))
        # Dismiss hint
        hint = font.render("[Enter] to close", True, (150, 150, 150))
        screen.blit(hint, (660, 640))
