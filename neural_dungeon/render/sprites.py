"""Sprite loading and caching for entity rendering."""
import os
import pygame

# Resolve asset path relative to project root
_SPRITE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "assets", "sprites",
)

# Enemy class name -> sprite filename (without .png)
ENEMY_SPRITE_MAP = {
    "Perceptron": "perceptron",
    "Token": "token",
    "BitShifter": "bit_shifter",
    "Convolver": "convolver",
    "DropoutPhantom": "dropout",
    "Pooler": "pooler",
    "AttentionHead": "attention_head",
    "GradientGhost": "gradient_ghost",
    "OverfittingMimic": "mimic",
    "ReLUGuardian": "relu_guardian",
    # Bosses
    "TheClassifier": "boss_classifier",
    "TheAutoencoder": "boss_autoencoder",
    "GANGenerator": "boss_gan_gen",
    "GANDiscriminator": "boss_gan_disc",
    "TheTransformer": "boss_transformer",
    "TransformerHead": "attention_head",  # reuse attention sprite
    "TheLossFunction": "boss_loss_function",
}


class SpriteCache:
    """Loads and caches scaled sprites."""

    def __init__(self):
        self._cache: dict[tuple[str, int, int], pygame.Surface] = {}
        self._raw: dict[str, pygame.Surface] = {}

    def _load_raw(self, name: str) -> pygame.Surface | None:
        if name in self._raw:
            return self._raw[name]
        path = os.path.join(_SPRITE_DIR, f"{name}.png")
        if not os.path.exists(path):
            self._raw[name] = None
            return None
        surf = pygame.image.load(path).convert_alpha()
        self._raw[name] = surf
        return surf

    def get(self, name: str, width: int, height: int) -> pygame.Surface | None:
        """Get a sprite scaled to (width, height). Returns None if not found."""
        key = (name, width, height)
        if key in self._cache:
            return self._cache[key]

        raw = self._load_raw(name)
        if raw is None:
            self._cache[key] = None
            return None

        scaled = pygame.transform.scale(raw, (width, height))
        self._cache[key] = scaled
        return scaled

    def get_player(self, size: int) -> pygame.Surface | None:
        return self.get("player", size, size)

    def get_enemy(self, enemy, size: int) -> pygame.Surface | None:
        class_name = type(enemy).__name__
        sprite_name = ENEMY_SPRITE_MAP.get(class_name)
        if sprite_name is None:
            return None
        return self.get(sprite_name, size, size)

    def get_bullet(self, owner: str, size: int) -> pygame.Surface | None:
        name = "bullet_player" if owner == "player" else "bullet_enemy"
        return self.get(name, size, size)
