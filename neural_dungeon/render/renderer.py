"""Pygame renderer for gameplay, title, game over, and transitions."""
import math
import pygame
from neural_dungeon.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, ROOM_WIDTH, ROOM_HEIGHT,
    PLAY_AREA_X, PLAY_AREA_Y, CELL_W, CELL_H,
    GAME_TITLE, STATE_TITLE, STATE_PLAYING,
    STATE_GAME_OVER, STATE_VICTORY, STATE_FLOOR_TRANSITION,
    ROOM_TYPE_SHOP, ROOM_TYPE_WEIGHT,
    DOOR_GAME_X, DOOR_GAME_Y, DOOR_INTERACT_RANGE,
    FLASHLIGHT_RANGE, FLASHLIGHT_HALF_ANGLE_DEG,
    ENEMY_FOV_RANGE, ENEMY_FOV_HALF_ANGLE_DEG,
)
from neural_dungeon.render.colors import (
    rgb, glow, BG_COLOR, BORDER_COLOR, GRID_COLOR,
)
from neural_dungeon.render.hud import render_hud
from neural_dungeon.render.sprites import SpriteCache
from neural_dungeon.render.effects import ScreenEffects
from neural_dungeon.world.room_layouts import Tile
from neural_dungeon.utils import distance


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 16)
        self.font_big = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_med = pygame.font.SysFont("consolas", 24)
        self.font_sm = pygame.font.SysFont("consolas", 14)
        self.tick = 0
        self.sprites = SpriteCache()
        self.effects = ScreenEffects(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Pre-build floor pattern surface
        self._floor_pattern = self._build_floor_pattern()

    def _build_floor_pattern(self):
        """Circuit-board pattern for the floor background."""
        w = int((ROOM_WIDTH + 2) * CELL_W)
        h = int((ROOM_HEIGHT + 2) * CELL_H)
        surf = pygame.Surface((w, h), pygame.SRCALPHA)

        # Subtle grid with varying opacity
        for x in range(0, w, CELL_W):
            alpha = 12 if (x // CELL_W) % 4 == 0 else 6
            pygame.draw.line(surf, (0, 60, 80, alpha), (x, 0), (x, h))
        for y in range(0, h, CELL_H):
            alpha = 12 if (y // CELL_H) % 4 == 0 else 6
            pygame.draw.line(surf, (0, 60, 80, alpha), (0, y), (w, y))

        # Circuit traces — horizontal and vertical lines with nodes
        import random
        rng = random.Random(42)  # Fixed seed for consistent pattern
        for _ in range(20):
            sx = rng.randint(0, w)
            sy = rng.randint(0, h)
            length = rng.randint(30, 120)
            if rng.random() < 0.5:
                pygame.draw.line(surf, (0, 30, 40, 15),
                                 (sx, sy), (sx + length, sy))
                # Node at end
                pygame.draw.circle(surf, (0, 40, 50, 20),
                                   (sx + length, sy), 2)
            else:
                pygame.draw.line(surf, (0, 30, 40, 15),
                                 (sx, sy), (sx, sy + length))
                pygame.draw.circle(surf, (0, 40, 50, 20),
                                   (sx, sy + length), 2)

        return surf

    def game_to_screen(self, gx, gy):
        """Convert game-unit coords to pixel coords."""
        px = PLAY_AREA_X + int((gx + 1) * CELL_W)
        py = PLAY_AREA_Y + int((gy + 1) * CELL_H)
        return px, py

    def render_frame(self, player, room, proj_mgr,
                     floor_num, room_progress,
                     game_state, message="",
                     particles=None,
                     is_dark=False, show_controls=False,
                     show_flashlight_hint=False):
        self.tick += 1
        self.screen.fill(BG_COLOR)

        if game_state == STATE_TITLE:
            self._render_title()
        elif game_state == STATE_GAME_OVER:
            self._render_game_over(player)
        elif game_state == STATE_VICTORY:
            self._render_victory(player)
        elif game_state == STATE_FLOOR_TRANSITION:
            self._render_floor_transition(floor_num, message)
        elif game_state == STATE_PLAYING and room:
            self._render_gameplay(
                player, room, proj_mgr,
                floor_num, room_progress, message,
                particles, is_dark, show_controls,
                show_flashlight_hint,
            )

    def _render_gameplay(self, player, room, proj_mgr,
                         floor_num, room_progress, message,
                         particles=None, is_dark=False,
                         show_controls=False,
                         show_flashlight_hint=False):
        # Floor pattern instead of plain grid
        self.screen.blit(self._floor_pattern, (PLAY_AREA_X, PLAY_AREA_Y))
        self._draw_border()

        if room.layout_grid is not None:
            self._draw_room_layout(room.layout_grid)

        # Ambient data streams in background
        self._draw_data_streams()

        # Particles behind entities
        if particles:
            particles.draw(self.screen, self.game_to_screen)

        self._draw_enemies(room.living_enemies)
        self._draw_projectiles(proj_mgr)
        self._draw_player(player)
        self._draw_door(room)

        # Boss HP bar
        for e in room.living_enemies:
            if e.is_boss:
                self._draw_boss_hp_bar(e)
                break

        # Lighting pass — non-dark rooms are well-lit, dark rooms need flashlights
        ambient = 8 if is_dark else 235
        lights = self._collect_lights(player, room, proj_mgr, is_dark)
        poly_lights = self._collect_cone_lights(player, room, is_dark)
        self.effects.draw_lighting(
            self.screen, lights, ambient=ambient,
            poly_lights=poly_lights if poly_lights else None,
        )

        # Post-processing
        self.effects.draw_scanlines(self.screen)
        self.effects.draw_vignette(self.screen)

        # Shop / Weight room overlays (drawn after effects so they're readable)
        if room.room_type == ROOM_TYPE_SHOP:
            self._draw_shop(room, player)
        elif room.room_type == ROOM_TYPE_WEIGHT:
            self._draw_weight_room(room)

        render_hud(
            self.screen, self.font, self.font_sm,
            player, floor_num, room_progress,
        )

        # Controls overlay in first room
        if show_controls:
            self._draw_controls_overlay()

        # Flashlight hint in first dark room
        if show_flashlight_hint:
            self._draw_flashlight_hint()

        if message:
            self._draw_message(message)
        elif room.cleared and room.room_type != "start":
            dist = distance(player.x, player.y, DOOR_GAME_X, DOOR_GAME_Y)
            if dist <= DOOR_INTERACT_RANGE:
                self._draw_message("Press E to advance")
            else:
                self._draw_message("ROOM CLEARED - go to the door")

    def _collect_lights(self, player, room, proj_mgr, is_dark=False):
        """Build list of (px, py, radius, color, intensity) for lighting."""
        lights = []

        # Player light — smaller in dark rooms (body glow only)
        if player.alive:
            px, py = self.game_to_screen(player.x, player.y)
            if is_dark:
                # Small body glow so player can see themselves
                r = 40 if player.flashlight_on else 25
                lights.append((px, py, r, (60, 200, 120), 0.5))
            elif player.invulnerable or player.dodging:
                lights.append((px, py, 120, (100, 255, 255), 0.9))
            else:
                lights.append((px, py, 100, (80, 255, 150), 0.75))

        # Enemy lights — dimmer in dark rooms
        for e in room.living_enemies:
            ex, ey = self.game_to_screen(e.x, e.y)
            c = rgb(e.color)
            if is_dark:
                r = 20 if e.is_boss else 12
                intensity = 0.25 if not e.intangible else 0.08
            else:
                r = 50 if e.is_boss else 35
                intensity = 0.5 if not e.intangible else 0.15
            lights.append((ex, ey, r, c, intensity))

        # Bullet lights — larger radius for readability
        for p in proj_mgr.projectiles:
            if not p.alive:
                continue
            bx, by = self.game_to_screen(p.x, p.y)
            c = rgb(p.color)
            if p.owner == "player":
                lights.append((bx, by, 30, c, 0.55))
            else:
                lights.append((bx, by, 25, c, 0.5))

        # Door light
        if room.cleared and room.room_type != "start":
            dx, dy = self.game_to_screen(DOOR_GAME_X, DOOR_GAME_Y)
            pulse = 0.5 + 0.3 * math.sin(self.tick * 0.08)
            lights.append((dx, dy, 50, (0, 255, 120), pulse))

        return lights

    def _raycast_cone(self, gx, gy, angle, half_angle_deg, max_range, grid):
        """Cast rays from (gx,gy) to build wall-occluded cone polygon in game units."""
        segments = 12
        half_rad = math.radians(half_angle_deg)
        points = [(gx, gy)]
        for i in range(segments + 1):
            a = angle - half_rad + (2 * half_rad * i / segments)
            dx = math.cos(a)
            dy = math.sin(a)
            hit_dist = max_range
            if grid is not None:
                dist = 0.0
                step = 0.5
                while dist < max_range:
                    dist += step
                    rx = gx + dx * dist
                    ry = gy + dy * dist
                    tx, ty = int(rx), int(ry)
                    if tx < 0 or tx >= ROOM_WIDTH or ty < 0 or ty >= ROOM_HEIGHT:
                        hit_dist = dist
                        break
                    if grid[ty][tx] in (Tile.WALL, Tile.COVER):
                        hit_dist = dist
                        break
            points.append((gx + dx * hit_dist, gy + dy * hit_dist))
        return points

    def _collect_cone_lights(self, player, room, is_dark):
        """Build polygon cone lights with wall occlusion."""
        poly_lights = []
        grid = room.layout_grid

        # Player flashlight cone — always available
        if player.alive and player.flashlight_on:
            aim_angle = math.atan2(player.aim_dy, player.aim_dx)
            poly = self._raycast_cone(
                player.x, player.y, aim_angle,
                FLASHLIGHT_HALF_ANGLE_DEG, FLASHLIGHT_RANGE, grid,
            )
            poly_px = [self.game_to_screen(px, py) for px, py in poly]
            poly_lights.append((poly_px, (200, 255, 220), 0.7))

        # Enemy flashlight cones (dark rooms only)
        if not is_dark:
            return poly_lights
        for e in room.living_enemies:
            if not e.alive:
                continue
            poly = self._raycast_cone(
                e.x, e.y, e.facing_angle,
                ENEMY_FOV_HALF_ANGLE_DEG, ENEMY_FOV_RANGE, grid,
            )
            poly_px = [self.game_to_screen(px, py) for px, py in poly]
            c = rgb(e.color)
            intensity = 0.6 if e.aware_timer > 0 else 0.4
            if e.intangible:
                intensity *= 0.5
            poly_lights.append((poly_px, c, intensity))

        return poly_lights

    def _draw_data_streams(self):
        """Animated vertical data streams in the background (matrix-rain style)."""
        t = self.tick * 0.03
        for i in range(8):
            # Fixed x positions, scrolling y
            x = PLAY_AREA_X + CELL_W + int(i * ROOM_WIDTH * CELL_W / 8)
            for j in range(6):
                offset = (t * 30 + i * 47 + j * 80) % (ROOM_HEIGHT * CELL_H)
                y = PLAY_AREA_Y + CELL_H + int(offset)
                alpha = int(15 + 10 * math.sin(t + i + j * 0.5))
                char = chr(0x30 + ((i * 7 + j * 3 + int(t * 2)) % 10))
                color = (0, alpha, alpha + 5)
                surf = self.font_sm.render(char, True, color)
                self.screen.blit(surf, (x, y))

    def _draw_room_layout(self, grid):
        tile_colors = {
            Tile.WALL: ((30, 50, 80), (70, 110, 160)),
            Tile.COVER: ((15, 60, 45), (30, 120, 90)),
            Tile.PIT: ((60, 10, 35), (120, 25, 70)),
            Tile.SLOW: ((15, 25, 60), (40, 65, 120)),
            Tile.VENT: ((8, 50, 50), (15, 95, 95)),
        }
        for y in range(ROOM_HEIGHT):
            for x in range(ROOM_WIDTH):
                tile = grid[y][x]
                if tile == Tile.FLOOR:
                    continue
                colors = tile_colors.get(tile)
                if not colors:
                    continue
                fill, border = colors
                sx, sy = self.game_to_screen(x, y)
                sx2, sy2 = self.game_to_screen(x + 1, y + 1)
                w = sx2 - sx
                h = sy2 - sy
                rect = pygame.Rect(sx, sy, w, h)

                if tile == Tile.PIT:
                    pulse = 0.6 + 0.4 * math.sin(self.tick * 0.1 + x * 0.3)
                    fill = (
                        int(fill[0] * pulse),
                        int(fill[1] * pulse),
                        int(fill[2] * pulse),
                    )
                    # Pit glow edge
                    glow_rect = rect.inflate(2, 2)
                    glow_c = (int(border[0] * pulse * 0.3),
                              int(border[1] * pulse * 0.3),
                              int(border[2] * pulse * 0.3))
                    pygame.draw.rect(self.screen, glow_c, glow_rect)

                pygame.draw.rect(self.screen, fill, rect)
                pygame.draw.rect(self.screen, border, rect, 1)

                # Wall top highlight for 3D-ish effect
                if tile == Tile.WALL:
                    highlight = (
                        min(255, border[0] + 30),
                        min(255, border[1] + 30),
                        min(255, border[2] + 30),
                    )
                    pygame.draw.line(
                        self.screen, highlight,
                        (sx, sy), (sx + w, sy), 1,
                    )

    def _draw_border(self):
        rect = pygame.Rect(
            PLAY_AREA_X + CELL_W, PLAY_AREA_Y + CELL_H,
            ROOM_WIDTH * CELL_W, ROOM_HEIGHT * CELL_H,
        )
        # Outer glow
        glow_rect = rect.inflate(4, 4)
        pygame.draw.rect(self.screen, glow(BORDER_COLOR, 0.3), glow_rect, 2)
        # Main border
        pygame.draw.rect(self.screen, BORDER_COLOR, rect, 2)

    def _draw_player(self, player):
        if not player.alive:
            return
        px, py = self.game_to_screen(player.x, player.y)
        color = rgb("green")
        radius = max(4, CELL_W // 2 - 1)
        if player.invulnerable or player.dodging:
            color = rgb("bright_cyan")

        size = radius * 2 + 2
        sprite = self.sprites.get_player(size)
        if sprite:
            if player.invulnerable or player.dodging:
                tinted = sprite.copy()
                tinted.fill((0, 200, 255, 100), special_flags=pygame.BLEND_RGBA_ADD)
                self.screen.blit(tinted, (px - size // 2, py - size // 2))
            else:
                self.screen.blit(sprite, (px - size // 2, py - size // 2))
        else:
            # Outer glow halo
            glow_c = glow(color, 0.2)
            pygame.draw.circle(self.screen, glow_c, (px, py), radius + 6)
            # Inner glow
            pygame.draw.circle(self.screen, glow(color), (px, py), radius + 3)
            # Core
            pygame.draw.circle(self.screen, color, (px, py), radius)

        # Aim line with gradient
        aim_len = radius + 8
        ax = px + int(player.aim_dx * aim_len)
        ay = py + int(player.aim_dy * aim_len)
        pygame.draw.line(self.screen, glow(color, 0.5), (px, py), (ax, ay), 2)
        pygame.draw.line(self.screen, color, (px, py), (ax, ay), 1)

    def _draw_enemies(self, enemies):
        for e in enemies:
            px, py = self.game_to_screen(e.x, e.y)
            color = rgb(e.color)
            base_radius = max(3, int(e.hitbox_radius * CELL_W * 0.7))
            radius = int(base_radius * 1.5) if e.is_boss else base_radius
            if e.intangible:
                color = rgb("bright_black")
            if e.frozen_timer > 0:
                color = rgb("bright_cyan")

            size = radius * 2 + 2
            sprite = self.sprites.get_enemy(e, size)
            if sprite:
                drawn = sprite
                if e.frozen_timer > 0:
                    drawn = sprite.copy()
                    drawn.fill((0, 200, 255, 80), special_flags=pygame.BLEND_RGBA_ADD)
                elif e.intangible:
                    drawn = sprite.copy()
                    drawn.set_alpha(100)
                self.screen.blit(drawn, (px - size // 2, py - size // 2))
            else:
                # Glow aura
                glow_c = glow(color, 0.15)
                pygame.draw.circle(self.screen, glow_c, (px, py), radius + 5)
                pygame.draw.circle(self.screen, glow(color), (px, py), radius + 2)
                pygame.draw.circle(self.screen, color, (px, py), radius)

            # HP bar (non-boss only)
            if e.hp < e.max_hp and not e.is_boss:
                bar_w = radius * 2
                bar_h = 3
                bx = px - radius
                by = py - radius - 6
                ratio = e.hp / e.max_hp
                pygame.draw.rect(
                    self.screen, (60, 0, 0), (bx, by, bar_w, bar_h),
                )
                pygame.draw.rect(
                    self.screen, color,
                    (bx, by, int(bar_w * ratio), bar_h),
                )

    def _draw_boss_hp_bar(self, boss):
        """Draw boss HP bar across top of play area."""
        bar_x = PLAY_AREA_X + CELL_W + 10
        bar_y = PLAY_AREA_Y + CELL_H + 6
        bar_w = ROOM_WIDTH * CELL_W - 20
        bar_h = 14

        ratio = boss.hp / boss.max_hp if boss.max_hp > 0 else 0
        fill_w = int(bar_w * ratio)

        # Boss name with glow
        name_color = rgb("bright_magenta")
        name = self.font_sm.render(boss.boss_name, True, name_color)
        # Name shadow
        shadow = self.font_sm.render(boss.boss_name, True, glow(name_color, 0.3))
        self.screen.blit(shadow, (bar_x + 1, bar_y - 15))
        self.screen.blit(name, (bar_x, bar_y - 16))

        # Background
        pygame.draw.rect(self.screen, (40, 0, 0), (bar_x, bar_y, bar_w, bar_h))

        # Fill with gradient-like look
        color = rgb("bright_magenta")
        if ratio < 0.25:
            color = rgb("bright_red")
        elif ratio < 0.5:
            color = rgb("bright_yellow")

        if fill_w > 0:
            pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_w, bar_h))
            # Bright top edge
            highlight = (
                min(255, color[0] + 50),
                min(255, color[1] + 50),
                min(255, color[2] + 50),
            )
            pygame.draw.line(
                self.screen, highlight,
                (bar_x, bar_y), (bar_x + fill_w, bar_y),
            )

        # Border with glow
        pygame.draw.rect(
            self.screen, glow(rgb("magenta"), 0.3),
            (bar_x - 1, bar_y - 1, bar_w + 2, bar_h + 2), 1,
        )
        pygame.draw.rect(self.screen, rgb("magenta"), (bar_x, bar_y, bar_w, bar_h), 1)

        # HP text
        hp_text = self.font_sm.render(
            f"{boss.hp}/{boss.max_hp}", True, rgb("white"),
        )
        self.screen.blit(hp_text, (bar_x + bar_w // 2 - hp_text.get_width() // 2, bar_y))

    def _draw_shop(self, room, player):
        """Draw shop item boxes."""
        if not room.shop_items:
            msg = self.font_med.render("SOLD OUT", True, rgb("bright_black"))
            self.screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 300))
            return

        start_x = SCREEN_WIDTH // 2 - len(room.shop_items) * 110
        y = SCREEN_HEIGHT // 2 - 40

        for i, item in enumerate(room.shop_items):
            x = start_x + i * 220
            can_afford = player.data_fragments >= item["cost"]
            border_color = rgb("bright_green") if can_afford else rgb("bright_red")
            bg = (15, 30, 15) if can_afford else (30, 15, 15)

            box = pygame.Rect(x, y, 200, 80)
            # Glow border
            glow_box = box.inflate(4, 4)
            pygame.draw.rect(self.screen, glow(border_color, 0.2), glow_box)
            pygame.draw.rect(self.screen, bg, box)
            pygame.draw.rect(self.screen, border_color, box, 2)

            key_label = self.font_sm.render(f"[{i + 1}]", True, rgb("bright_yellow"))
            self.screen.blit(key_label, (x + 5, y + 5))

            name = self.font_sm.render(item["name"], True, rgb("bright_white"))
            self.screen.blit(name, (x + 30, y + 5))

            desc = self.font_sm.render(item["desc"], True, rgb("white"))
            self.screen.blit(desc, (x + 10, y + 30))

            cost_color = rgb("bright_green") if can_afford else rgb("bright_red")
            cost = self.font_sm.render(f"Cost: {item['cost']}", True, cost_color)
            self.screen.blit(cost, (x + 10, y + 55))

    def _draw_weight_room(self, room):
        """Draw weight room buff options."""
        if room.weight_used:
            msg = self.font_med.render("BUFF SELECTED", True, rgb("bright_green"))
            self.screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 300))
            return

        title = self.font_med.render("WEIGHT ROOM", True, rgb("bright_yellow"))
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 250))

        sub = self.font_sm.render("Choose a buff (1/2/3):", True, rgb("white"))
        self.screen.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 280))

        y = 310
        for i, opt in enumerate(room.weight_options):
            color = rgb("bright_cyan")
            text = f"[{i + 1}] {opt['name']} - {opt['desc']}"
            surf = self.font.render(text, True, color)
            self.screen.blit(surf, (SCREEN_WIDTH // 2 - surf.get_width() // 2, y))
            y += 30

    def _draw_projectiles(self, proj_mgr):
        for p in proj_mgr.projectiles:
            if not p.alive:
                continue
            px, py = self.game_to_screen(p.x, p.y)
            color = rgb(p.color)

            # Universal glow halo on every projectile for readability
            glow_c = glow(color, 0.15)
            pygame.draw.circle(self.screen, glow_c, (px, py), 10)

            if p.owner == "player":
                self._draw_player_bullet(px, py, p, color)
            else:
                # Enemy bullets
                sprite = self.sprites.get_bullet("enemy", 8)
                if sprite:
                    self.screen.blit(sprite, (px - 4, py - 4))
                else:
                    pygame.draw.circle(self.screen, glow(color, 0.2), (px, py), 7)
                    pygame.draw.circle(self.screen, glow(color), (px, py), 5)
                    pygame.draw.circle(self.screen, color, (px, py), 3)

    def _draw_player_bullet(self, px, py, bullet, color):
        """Weapon-specific bullet visuals."""
        char = bullet.char

        if char == "\u25cf":  # ● pulse_cannon — large glowing orb
            pulse = 0.8 + 0.2 * math.sin(self.tick * 0.2)
            r = int(8 * pulse)
            pygame.draw.circle(self.screen, glow(color, 0.2), (px, py), r + 4)
            pygame.draw.circle(self.screen, glow(color, 0.5), (px, py), r + 2)
            pygame.draw.circle(self.screen, color, (px, py), r)
            pygame.draw.circle(self.screen, (255, 255, 255), (px, py),
                               max(1, r // 3))

        elif char == "\u2500":  # ─ piercing_ray — elongated beam
            dx, dy = bullet.dx, bullet.dy
            length = 10
            ex = px + int(dx * length)
            ey = py + int(dy * length)
            pygame.draw.line(self.screen, glow(color, 0.3),
                             (px, py), (ex, ey), 4)
            pygame.draw.line(self.screen, color, (px, py), (ex, ey), 2)
            pygame.draw.circle(self.screen, (255, 255, 255), (ex, ey), 2)

        elif char == "\u2014":  # — sniper — long bright tracer
            dx, dy = bullet.dx, bullet.dy
            length = 14
            ex = px + int(dx * length)
            ey = py + int(dy * length)
            pygame.draw.line(self.screen, glow(color, 0.2),
                             (px, py), (ex, ey), 5)
            pygame.draw.line(self.screen, color, (px, py), (ex, ey), 2)
            pygame.draw.line(self.screen, (255, 255, 255),
                             (px + int(dx * 4), py + int(dy * 4)),
                             (ex, ey), 1)

        elif char == "\u25e6":  # ◦ homing_burst — diamond
            s = 5
            points = [
                (px, py - s), (px + s, py),
                (px, py + s), (px - s, py),
            ]
            glow_pts = [
                (px, py - s - 2), (px + s + 2, py),
                (px, py + s + 2), (px - s - 2, py),
            ]
            pygame.draw.polygon(self.screen, glow(color, 0.3), glow_pts)
            pygame.draw.polygon(self.screen, color, points)
            pygame.draw.circle(self.screen, (255, 255, 255), (px, py), 2)

        elif char == "\u2218":  # ∘ scatter/shotgun — small pellet
            pygame.draw.circle(self.screen, glow(color, 0.3), (px, py), 4)
            pygame.draw.circle(self.screen, color, (px, py), 2)

        else:  # · default (gradient_beam, rapid_fire)
            sprite = self.sprites.get_bullet("player", 6)
            if sprite:
                self.screen.blit(sprite, (px - 3, py - 3))
            else:
                pygame.draw.circle(self.screen, glow(color, 0.3), (px, py), 5)
                pygame.draw.circle(self.screen, color, (px, py), 3)

    def _draw_door(self, room):
        if room.cleared and room.room_type != "start":
            cx = PLAY_AREA_X + (ROOM_WIDTH // 2 + 1) * CELL_W
            dy = PLAY_AREA_Y + CELL_H
            color = rgb("bright_green")
            pulse = 0.6 + 0.4 * math.sin(self.tick * 0.08)

            # Outer glow
            glow_c = (0, int(60 * pulse), int(30 * pulse))
            pygame.draw.rect(
                self.screen, glow_c, (cx - 22, dy - 8, 44, 16),
            )
            # Door
            pygame.draw.rect(
                self.screen, color, (cx - 15, dy - 3, 30, 6),
            )
            # Border
            pygame.draw.rect(
                self.screen, glow(color), (cx - 18, dy - 5, 36, 10), 2,
            )

    def _draw_message(self, text):
        color = rgb("bright_yellow")
        # Shadow
        shadow = self.font.render(text, True, glow(color, 0.3))
        sx = (SCREEN_WIDTH - shadow.get_width()) // 2 + 1
        self.screen.blit(shadow, (sx, SCREEN_HEIGHT - 39))
        # Text
        surf = self.font.render(text, True, color)
        x = (SCREEN_WIDTH - surf.get_width()) // 2
        y = SCREEN_HEIGHT - 40
        self.screen.blit(surf, (x, y))

    def _draw_controls_overlay(self):
        """Pulsing controls overlay for the first room."""
        pulse = 0.5 + 0.5 * abs(math.sin(self.tick * 0.04))
        w, h = 360, 260
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        bg_alpha = int(160 * pulse)
        overlay.fill((5, 5, 20, bg_alpha))

        # Border
        ba = int(200 * pulse)
        pygame.draw.rect(overlay, (0, ba, int(ba * 0.8), ba), (0, 0, w, h), 2)

        # Title
        tc = (0, int(255 * pulse), int(255 * pulse))
        title = self.font_med.render("CONTROLS", True, tc)
        overlay.blit(title, (w // 2 - title.get_width() // 2, 12))

        controls = [
            ("WASD", "Move"),
            ("Mouse", "Aim"),
            ("Left Click / J", "Shoot"),
            ("Space", "Dodge Roll"),
            ("F", "Use Active Item"),
            ("E", "Interact / Advance"),
            ("T", "Toggle Flashlight"),
        ]
        y = 52
        for key, desc in controls:
            kc = (int(255 * pulse), int(255 * pulse), int(100 * pulse))
            dc = (int(200 * pulse), int(200 * pulse), int(200 * pulse))
            k = self.font_sm.render(key, True, kc)
            d = self.font_sm.render(f" - {desc}", True, dc)
            total = k.get_width() + d.get_width()
            x = (w - total) // 2
            overlay.blit(k, (x, y))
            overlay.blit(d, (x + k.get_width(), y))
            y += 24

        # "Move to start" prompt
        pc = (0, int(200 * pulse), int(130 * pulse))
        prompt = self.font_sm.render("Move to begin...", True, pc)
        overlay.blit(prompt, (w // 2 - prompt.get_width() // 2, h - 28))

        ox = (SCREEN_WIDTH - w) // 2
        oy = (SCREEN_HEIGHT - h) // 2
        self.screen.blit(overlay, (ox, oy))

    def _draw_flashlight_hint(self):
        """Pulsing flashlight control hint for first dark room."""
        pulse = 0.5 + 0.5 * abs(math.sin(self.tick * 0.06))
        tc = (int(255 * pulse), int(255 * pulse), int(100 * pulse))
        text = self.font.render("Press T to toggle flashlight", True, tc)
        x = (SCREEN_WIDTH - text.get_width()) // 2
        y = SCREEN_HEIGHT - 70
        # Background strip
        bg = pygame.Surface((text.get_width() + 20, 28), pygame.SRCALPHA)
        bg.fill((5, 5, 20, int(140 * pulse)))
        self.screen.blit(bg, (x - 10, y - 4))
        self.screen.blit(text, (x, y))

    # -- Screen states --------------------------------------------------------

    def _render_title(self):
        self._draw_neural_bg()

        # Title with glow effect
        title_text = GAME_TITLE
        shadow = self.font_big.render(title_text, True, glow(rgb("bright_cyan"), 0.3))
        title = self.font_big.render(title_text, True, rgb("bright_cyan"))
        tx = (SCREEN_WIDTH - title.get_width()) // 2
        self.screen.blit(shadow, (tx + 2, 142))
        self.screen.blit(title, (tx, 140))

        # Underline with glow
        uw = title.get_width()
        pygame.draw.line(
            self.screen, glow(rgb("cyan"), 0.3), (tx, 197), (tx + uw, 197), 3,
        )
        pygame.draw.line(
            self.screen, rgb("cyan"), (tx, 195), (tx + uw, 195), 2,
        )

        sub = self.font_med.render(
            "The dungeon IS a neural network", True, rgb("white"),
        )
        self.screen.blit(sub, ((SCREEN_WIDTH - sub.get_width()) // 2, 220))

        sub2 = self.font.render(
            "You are trapped inside an AI", True, rgb("bright_black"),
        )
        self.screen.blit(sub2, ((SCREEN_WIDTH - sub2.get_width()) // 2, 260))

        # Pulsing start prompt
        pulse = abs(math.sin(self.tick * 0.05))
        start_color = (0, int(pulse * 255), int(pulse * 128))
        start = self.font_med.render(
            "[ Press ENTER to start ]", True, start_color,
        )
        self.screen.blit(
            start, ((SCREEN_WIDTH - start.get_width()) // 2, 380),
        )

        ver = self.font_sm.render("v0.4.0", True, rgb("bright_black"))
        self.screen.blit(ver, ((SCREEN_WIDTH - ver.get_width()) // 2, 660))

        # Apply effects to title screen too
        self.effects.draw_scanlines(self.screen)

    def _draw_neural_bg(self):
        t = self.tick * 0.02
        nodes = []
        for i in range(30):
            x = int(
                SCREEN_WIDTH * 0.1
                + (SCREEN_WIDTH * 0.8) * ((i % 6) / 5)
            )
            y = int(
                100 + 500 * ((i // 6) / 4)
                + math.sin(t + i * 0.7) * 15
            )
            nodes.append((x, y))
            a = int(30 + 20 * math.sin(t + i))
            # Glow halo
            pygame.draw.circle(self.screen, (0, a // 3, a // 3), (x, y), 8)
            pygame.draw.circle(self.screen, (0, a, a), (x, y), 3)

        for i in range(len(nodes) - 6):
            c = int(15 + 10 * math.sin(t + i * 0.3))
            pygame.draw.line(
                self.screen, (0, c, c), nodes[i], nodes[i + 6], 1,
            )

    def _render_game_over(self, player):
        # Animated background — dim neural net
        self._draw_neural_bg()

        bx, by, bw, bh = 280, 150, 400, 200
        # Red glow behind box
        glow_rect = pygame.Rect(bx - 6, by - 6, bw + 12, bh + 12)
        pygame.draw.rect(self.screen, (60, 0, 0), glow_rect)
        pygame.draw.rect(self.screen, (40, 0, 0), (bx, by, bw, bh))
        pygame.draw.rect(self.screen, rgb("red"), (bx, by, bw, bh), 2)

        title = self.font_big.render("NEURAL DEATH", True, rgb("red"))
        # Flicker effect
        pulse = 0.7 + 0.3 * abs(math.sin(self.tick * 0.06))
        flicker_c = (int(255 * pulse), int(50 * pulse), int(50 * pulse))
        title = self.font_big.render("NEURAL DEATH", True, flicker_c)
        self.screen.blit(
            title, ((SCREEN_WIDTH - title.get_width()) // 2, 170),
        )

        sub = self.font.render(
            "The AI has claimed you.", True, rgb("bright_red"),
        )
        self.screen.blit(sub, ((SCREEN_WIDTH - sub.get_width()) // 2, 240))

        stats = [
            f"Enemies defeated: {player.enemies_killed}",
            f"Damage dealt: {player.damage_dealt}",
            f"Rooms cleared: {player.rooms_cleared}",
            f"Data fragments: {player.data_fragments}",
        ]
        y = 400
        for s in stats:
            surf = self.font.render(s, True, rgb("white"))
            self.screen.blit(
                surf, ((SCREEN_WIDTH - surf.get_width()) // 2, y),
            )
            y += 25

        prompt = self.font_med.render(
            "[ R ] Retry   [ Q ] Quit", True, rgb("bright_yellow"),
        )
        self.screen.blit(
            prompt, ((SCREEN_WIDTH - prompt.get_width()) // 2, 550),
        )

        self.effects.draw_scanlines(self.screen)

    def _render_victory(self, player):
        self._draw_neural_bg()

        bx, by, bw, bh = 260, 140, 440, 220
        glow_rect = pygame.Rect(bx - 6, by - 6, bw + 12, bh + 12)
        pygame.draw.rect(self.screen, (0, 40, 0), glow_rect)
        pygame.draw.rect(self.screen, (0, 30, 0), (bx, by, bw, bh))
        pygame.draw.rect(self.screen, rgb("green"), (bx, by, bw, bh), 2)

        title = self.font_big.render("SYSTEM OVERRIDE", True, rgb("green"))
        self.screen.blit(
            title, ((SCREEN_WIDTH - title.get_width()) // 2, 160),
        )

        lines = [
            ("You have escaped the AI.", 230),
            ("The neural network is free.", 260),
        ]
        for text, yy in lines:
            surf = self.font.render(text, True, rgb("bright_green"))
            self.screen.blit(
                surf, ((SCREEN_WIDTH - surf.get_width()) // 2, yy),
            )

        stats = [
            f"Enemies defeated: {player.enemies_killed}",
            f"Floors cleared: {player.floors_cleared}",
            f"Data fragments: {player.data_fragments}",
        ]
        y = 400
        for s in stats:
            surf = self.font.render(s, True, rgb("white"))
            self.screen.blit(
                surf, ((SCREEN_WIDTH - surf.get_width()) // 2, y),
            )
            y += 25

        prompt = self.font_med.render(
            "[ R ] Play Again   [ Q ] Quit", True, rgb("bright_yellow"),
        )
        self.screen.blit(
            prompt, ((SCREEN_WIDTH - prompt.get_width()) // 2, 550),
        )

        self.effects.draw_scanlines(self.screen)

    def _render_floor_transition(self, floor_num, message):
        self._draw_neural_bg()

        title = self.font_big.render(
            f"DESCENDING TO LAYER {floor_num + 1}",
            True, rgb("bright_cyan"),
        )
        self.screen.blit(
            title, ((SCREEN_WIDTH - title.get_width()) // 2, 260),
        )

        if message:
            msg = self.font_med.render(message, True, rgb("bright_yellow"))
            self.screen.blit(
                msg, ((SCREEN_WIDTH - msg.get_width()) // 2, 340),
            )

        cont = self.font.render(
            "Press ENTER to continue...", True, rgb("white"),
        )
        self.screen.blit(
            cont, ((SCREEN_WIDTH - cont.get_width()) // 2, 420),
        )

        self.effects.draw_scanlines(self.screen)
