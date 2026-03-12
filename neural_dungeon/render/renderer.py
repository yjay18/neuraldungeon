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
)
from neural_dungeon.render.colors import (
    rgb, glow, BG_COLOR, BORDER_COLOR, GRID_COLOR,
)
from neural_dungeon.render.hud import render_hud
from neural_dungeon.render.sprites import SpriteCache
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

    def game_to_screen(self, gx, gy):
        """Convert game-unit coords to pixel coords."""
        px = PLAY_AREA_X + int((gx + 1) * CELL_W)
        py = PLAY_AREA_Y + int((gy + 1) * CELL_H)
        return px, py

    def render_frame(self, player, room, proj_mgr,
                     floor_num, room_progress,
                     game_state, message=""):
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
            )

    def _render_gameplay(self, player, room, proj_mgr,
                         floor_num, room_progress, message):
        self._draw_grid()
        self._draw_border()
        if room.layout_grid is not None:
            self._draw_room_layout(room.layout_grid)
        self._draw_enemies(room.living_enemies)
        self._draw_projectiles(proj_mgr)
        self._draw_player(player)
        self._draw_door(room)

        # Boss HP bar
        for e in room.living_enemies:
            if e.is_boss:
                self._draw_boss_hp_bar(e)
                break

        # Shop / Weight room overlays
        if room.room_type == ROOM_TYPE_SHOP:
            self._draw_shop(room, player)
        elif room.room_type == ROOM_TYPE_WEIGHT:
            self._draw_weight_room(room)

        render_hud(
            self.screen, self.font, self.font_sm,
            player, floor_num, room_progress,
        )
        if message:
            self._draw_message(message)
        elif room.cleared and room.room_type != "start":
            dist = distance(player.x, player.y, DOOR_GAME_X, DOOR_GAME_Y)
            if dist <= DOOR_INTERACT_RANGE:
                self._draw_message("Press E to advance")
            else:
                self._draw_message("ROOM CLEARED - go to the door")

    def _draw_grid(self):
        for x in range(ROOM_WIDTH + 3):
            px = PLAY_AREA_X + x * CELL_W
            pygame.draw.line(
                self.screen, GRID_COLOR,
                (px, PLAY_AREA_Y),
                (px, PLAY_AREA_Y + (ROOM_HEIGHT + 2) * CELL_H),
            )
        for y in range(ROOM_HEIGHT + 3):
            py = PLAY_AREA_Y + y * CELL_H
            pygame.draw.line(
                self.screen, GRID_COLOR,
                (PLAY_AREA_X, py),
                (PLAY_AREA_X + (ROOM_WIDTH + 2) * CELL_W, py),
            )

    def _draw_room_layout(self, grid):
        tile_colors = {
            Tile.WALL: ((30, 45, 75), (60, 90, 130)),
            Tile.COVER: ((20, 55, 45), (35, 110, 85)),
            Tile.PIT: ((55, 12, 35), (110, 25, 65)),
            Tile.SLOW: ((18, 30, 55), (45, 70, 110)),
            Tile.VENT: ((10, 45, 45), (20, 85, 85)),
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
                    pulse = 0.7 + 0.3 * math.sin(self.tick * 0.1)
                    fill = (
                        int(fill[0] * pulse),
                        int(fill[1] * pulse),
                        int(fill[2] * pulse),
                    )
                pygame.draw.rect(self.screen, fill, rect)
                pygame.draw.rect(self.screen, border, rect, 1)

    def _draw_border(self):
        rect = pygame.Rect(
            PLAY_AREA_X + CELL_W, PLAY_AREA_Y + CELL_H,
            ROOM_WIDTH * CELL_W, ROOM_HEIGHT * CELL_H,
        )
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
                # Cyan tint overlay
                tinted = sprite.copy()
                tinted.fill((0, 200, 255, 100), special_flags=pygame.BLEND_RGBA_ADD)
                self.screen.blit(tinted, (px - size // 2, py - size // 2))
            else:
                self.screen.blit(sprite, (px - size // 2, py - size // 2))
        else:
            pygame.draw.circle(self.screen, glow(color), (px, py), radius + 3)
            pygame.draw.circle(self.screen, color, (px, py), radius)

        # Aim line
        aim_len = radius + 6
        ax = px + int(player.aim_dx * aim_len)
        ay = py + int(player.aim_dy * aim_len)
        pygame.draw.line(self.screen, color, (px, py), (ax, ay), 2)

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
                pygame.draw.circle(self.screen, glow(color), (px, py), radius + 2)
                pygame.draw.circle(self.screen, color, (px, py), radius)

            # HP bar (non-boss only; boss uses big bar)
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
        bar_h = 12

        ratio = boss.hp / boss.max_hp if boss.max_hp > 0 else 0
        fill_w = int(bar_w * ratio)

        # Boss name
        name = self.font_sm.render(boss.boss_name, True, rgb("bright_magenta"))
        self.screen.blit(name, (bar_x, bar_y - 16))

        # Background
        pygame.draw.rect(self.screen, (40, 0, 0), (bar_x, bar_y, bar_w, bar_h))
        # Fill
        color = rgb("bright_magenta")
        if ratio < 0.25:
            color = rgb("bright_red")
        elif ratio < 0.5:
            color = rgb("bright_yellow")
        pygame.draw.rect(self.screen, color, (bar_x, bar_y, fill_w, bar_h))
        # Border
        pygame.draw.rect(self.screen, rgb("magenta"), (bar_x, bar_y, bar_w, bar_h), 1)

        # HP text
        hp_text = self.font_sm.render(
            f"{boss.hp}/{boss.max_hp}", True, rgb("white"),
        )
        self.screen.blit(hp_text, (bar_x + bar_w // 2 - hp_text.get_width() // 2, bar_y - 1))

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
            pygame.draw.rect(self.screen, bg, box)
            pygame.draw.rect(self.screen, border_color, box, 2)

            # Key label
            key_label = self.font_sm.render(f"[{i + 1}]", True, rgb("bright_yellow"))
            self.screen.blit(key_label, (x + 5, y + 5))

            # Name
            name = self.font_sm.render(item["name"], True, rgb("bright_white"))
            self.screen.blit(name, (x + 30, y + 5))

            # Desc
            desc = self.font_sm.render(item["desc"], True, rgb("white"))
            self.screen.blit(desc, (x + 10, y + 30))

            # Cost
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
            size = 6 if p.owner == "player" else 8
            sprite = self.sprites.get_bullet(p.owner, size)
            if sprite:
                self.screen.blit(sprite, (px - size // 2, py - size // 2))
            elif p.owner == "player":
                pygame.draw.circle(self.screen, color, (px, py), 3)
            else:
                pygame.draw.circle(self.screen, glow(color), (px, py), 5)
                pygame.draw.circle(self.screen, color, (px, py), 3)

    def _draw_door(self, room):
        if room.cleared and room.room_type != "start":
            cx = PLAY_AREA_X + (ROOM_WIDTH // 2 + 1) * CELL_W
            dy = PLAY_AREA_Y + CELL_H
            color = rgb("bright_green")
            pygame.draw.rect(
                self.screen, color, (cx - 15, dy - 3, 30, 6),
            )
            pygame.draw.rect(
                self.screen, glow(color), (cx - 18, dy - 5, 36, 10), 2,
            )

    def _draw_message(self, text):
        color = rgb("bright_yellow")
        surf = self.font.render(text, True, color)
        x = (SCREEN_WIDTH - surf.get_width()) // 2
        y = SCREEN_HEIGHT - 40
        self.screen.blit(surf, (x, y))

    # -- Screen states --------------------------------------------------------

    def _render_title(self):
        self._draw_neural_bg()

        title = self.font_big.render(GAME_TITLE, True, rgb("bright_cyan"))
        tx = (SCREEN_WIDTH - title.get_width()) // 2
        self.screen.blit(title, (tx, 140))

        uw = title.get_width()
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

        controls = [
            ("WASD", "Move"),
            ("Mouse", "Aim"),
            ("Left Click / J", "Shoot"),
            ("Space", "Dodge Roll"),
            ("F", "Use Active Item"),
            ("E", "Interact / Advance"),
            ("Q", "Quit"),
        ]
        y = 330
        for key, desc in controls:
            k = self.font.render(key, True, rgb("bright_yellow"))
            d = self.font.render(f" - {desc}", True, rgb("white"))
            total_w = k.get_width() + d.get_width()
            x = (SCREEN_WIDTH - total_w) // 2
            self.screen.blit(k, (x, y))
            self.screen.blit(d, (x + k.get_width(), y))
            y += 25

        # Pulsing start prompt
        pulse = abs(math.sin(self.tick * 0.05))
        start_color = (0, int(pulse * 255), int(pulse * 128))
        start = self.font_med.render(
            "[ Press ENTER to start ]", True, start_color,
        )
        self.screen.blit(
            start, ((SCREEN_WIDTH - start.get_width()) // 2, 560),
        )

        ver = self.font_sm.render("v0.3.0", True, rgb("bright_black"))
        self.screen.blit(ver, ((SCREEN_WIDTH - ver.get_width()) // 2, 660))

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
            pygame.draw.circle(self.screen, (0, a, a), (x, y), 3)

        for i in range(len(nodes) - 6):
            c = int(15 + 10 * math.sin(t + i * 0.3))
            pygame.draw.line(
                self.screen, (0, c, c), nodes[i], nodes[i + 6], 1,
            )

    def _render_game_over(self, player):
        bx, by, bw, bh = 280, 150, 400, 200
        pygame.draw.rect(self.screen, (40, 0, 0), (bx, by, bw, bh))
        pygame.draw.rect(self.screen, rgb("red"), (bx, by, bw, bh), 2)

        title = self.font_big.render("NEURAL DEATH", True, rgb("red"))
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

    def _render_victory(self, player):
        bx, by, bw, bh = 260, 140, 440, 220
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

    def _render_floor_transition(self, floor_num, message):
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
