"""HUD rendering — HP bar, weapon, floor info."""
import pygame
from neural_dungeon.config import SCREEN_WIDTH
from neural_dungeon.render.colors import hp_color, rgb


def render_hud(screen, font, font_sm, player, floor_num, room_progress):
    """Draw HUD bar at top of screen."""
    # Background strip
    pygame.draw.rect(screen, (10, 10, 25), (0, 0, SCREEN_WIDTH, 70))
    pygame.draw.line(
        screen, (0, 60, 80), (0, 70), (SCREEN_WIDTH, 70), 1,
    )

    # HP bar
    bar_x, bar_y = 20, 12
    bar_w, bar_h = 200, 18
    hp_ratio = player.hp / player.max_hp if player.max_hp > 0 else 0
    fill_w = int(bar_w * hp_ratio)
    color = hp_color(player.hp, player.max_hp)

    pygame.draw.rect(screen, (30, 30, 30), (bar_x, bar_y, bar_w, bar_h))
    pygame.draw.rect(screen, color, (bar_x, bar_y, fill_w, bar_h))
    pygame.draw.rect(screen, (80, 80, 80), (bar_x, bar_y, bar_w, bar_h), 1)

    hp_text = font_sm.render(
        f"HP {player.hp}/{player.max_hp}", True, rgb("white"),
    )
    screen.blit(hp_text, (bar_x + 5, bar_y + 2))

    # Weapon
    weapon_name = player.weapon_info["name"]
    wep = font.render(weapon_name, True, rgb("cyan"))
    screen.blit(wep, (240, 12))

    # Dodge status
    if player.dodge_cooldown <= 0 and not player.dodging:
        dodge = font_sm.render("DODGE READY", True, rgb("bright_cyan"))
    else:
        dodge = font_sm.render("DODGE", True, rgb("bright_black"))
    screen.blit(dodge, (240, 35))

    # Floor + room
    floor_text = font.render(f"Floor {floor_num + 1}", True, rgb("yellow"))
    screen.blit(floor_text, (450, 12))

    if room_progress:
        prog = font_sm.render(room_progress, True, rgb("white"))
        screen.blit(prog, (450, 35))

    # Data fragments + kills
    frag = font_sm.render(
        f"Data: {player.data_fragments}", True, rgb("bright_green"),
    )
    screen.blit(frag, (620, 12))

    kills = font_sm.render(
        f"Kills: {player.enemies_killed}", True, rgb("bright_red"),
    )
    screen.blit(kills, (620, 30))
