"""HUD rendering — HP bar, weapon, floor info, active item."""
import pygame
from neural_dungeon.config import SCREEN_WIDTH
from neural_dungeon.render.colors import hp_color, rgb, glow


def render_hud(screen, font, font_sm, player, floor_num, room_progress):
    """Draw HUD bar at top of screen."""
    # Background strip with gradient feel
    pygame.draw.rect(screen, (8, 8, 20), (0, 0, SCREEN_WIDTH, 70))
    # Bottom separator with glow
    pygame.draw.line(
        screen, (0, 30, 40), (0, 71), (SCREEN_WIDTH, 71), 1,
    )
    pygame.draw.line(
        screen, (0, 70, 90), (0, 70), (SCREEN_WIDTH, 70), 1,
    )

    # HP bar with glow
    bar_x, bar_y = 20, 12
    bar_w, bar_h = 200, 18
    hp_ratio = player.hp / player.max_hp if player.max_hp > 0 else 0
    fill_w = int(bar_w * hp_ratio)
    color = hp_color(player.hp, player.max_hp)

    # Glow behind bar
    glow_rect = pygame.Rect(bar_x - 2, bar_y - 2, bar_w + 4, bar_h + 4)
    pygame.draw.rect(screen, glow(color, 0.15), glow_rect)
    # Background
    pygame.draw.rect(screen, (25, 25, 35), (bar_x, bar_y, bar_w, bar_h))
    # Fill
    if fill_w > 0:
        pygame.draw.rect(screen, color, (bar_x, bar_y, fill_w, bar_h))
        # Highlight on top edge
        highlight = (
            min(255, color[0] + 60),
            min(255, color[1] + 60),
            min(255, color[2] + 60),
        )
        pygame.draw.line(
            screen, highlight,
            (bar_x, bar_y), (bar_x + fill_w, bar_y),
        )
    # Border
    pygame.draw.rect(screen, (80, 80, 100), (bar_x, bar_y, bar_w, bar_h), 1)

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

    # Active item
    if player.active_item:
        from neural_dungeon.entities.items import ACTIVE_ITEMS
        ainfo = ACTIVE_ITEMS.get(player.active_item, {})
        aname = ainfo.get("name", player.active_item)
        if player.active_item_cooldown <= 0:
            act_color = rgb("bright_green")
            act_text = f"[F] {aname}"
        else:
            act_color = rgb("bright_black")
            act_text = f"[F] {aname} ({player.active_item_cooldown})"
        act = font_sm.render(act_text, True, act_color)
        screen.blit(act, (240, 50))

    # Floor + room
    floor_text = font.render(f"Floor {floor_num + 1}", True, rgb("yellow"))
    screen.blit(floor_text, (450, 12))

    if room_progress:
        prog = font_sm.render(room_progress, True, rgb("white"))
        screen.blit(prog, (450, 35))

    # Passive count
    if player.passive_items:
        pcount = font_sm.render(
            f"Passives: {len(player.passive_items)}", True, rgb("bright_cyan"),
        )
        screen.blit(pcount, (450, 50))

    # Data fragments + kills with icons
    frag = font_sm.render(
        f"Data: {player.data_fragments}", True, rgb("bright_green"),
    )
    screen.blit(frag, (620, 12))

    kills = font_sm.render(
        f"Kills: {player.enemies_killed}", True, rgb("bright_red"),
    )
    screen.blit(kills, (620, 30))

    # Separator lines between sections
    sep_color = (0, 40, 50)
    pygame.draw.line(screen, sep_color, (230, 8), (230, 62), 1)
    pygame.draw.line(screen, sep_color, (440, 8), (440, 62), 1)
    pygame.draw.line(screen, sep_color, (610, 8), (610, 62), 1)
