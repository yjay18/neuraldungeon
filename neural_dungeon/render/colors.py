"""Neon color palette. Maps blessed-style names to RGB tuples."""
from neural_dungeon.config import (
    ACTIVATION_COLORS, ACTIVATION_DEAD, ACTIVATION_LOW, ACTIVATION_HIGH,
)

# Blessed name -> neon RGB
NEON = {
    "black": (0, 0, 0),
    "red": (255, 50, 50),
    "green": (0, 255, 100),
    "yellow": (255, 255, 0),
    "blue": (50, 100, 255),
    "magenta": (255, 0, 255),
    "cyan": (0, 255, 255),
    "white": (220, 220, 220),
    "bright_black": (80, 80, 80),
    "bright_red": (255, 80, 80),
    "bright_green": (0, 255, 120),
    "bright_yellow": (255, 255, 100),
    "bright_blue": (80, 140, 255),
    "bright_magenta": (255, 100, 255),
    "bright_cyan": (100, 255, 255),
    "bright_white": (255, 255, 255),
    "on_black": (0, 0, 0),
    "bright_white_on_blue": (255, 255, 255),
}

BG_COLOR = (5, 5, 15)
BORDER_COLOR = (0, 80, 100)
GRID_COLOR = (15, 15, 30)
HUD_BG = (10, 10, 25)


def rgb(name):
    """Get RGB tuple from a blessed-style color name."""
    return NEON.get(name, (200, 200, 200))


def activation_to_color(activation):
    if activation < ACTIVATION_DEAD:
        return rgb(ACTIVATION_COLORS["dead"])
    elif activation < ACTIVATION_LOW:
        return rgb(ACTIVATION_COLORS["low"])
    elif activation < ACTIVATION_HIGH:
        return rgb(ACTIVATION_COLORS["mid"])
    elif activation < 0.9:
        return rgb(ACTIVATION_COLORS["high"])
    else:
        return rgb(ACTIVATION_COLORS["max"])


def hp_color(hp, max_hp):
    ratio = hp / max_hp if max_hp > 0 else 0
    if ratio > 0.6:
        return rgb("green")
    elif ratio > 0.3:
        return rgb("yellow")
    else:
        return rgb("red")


def glow(color, factor=0.4):
    """Dimmer version for glow outlines."""
    return tuple(max(0, int(c * factor)) for c in color)
