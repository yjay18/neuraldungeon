"""Pygame renderer for gameplay, title, game over, and transitions."""
import math
import pygame
from neural_dungeon.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, ROOM_WIDTH, ROOM_HEIGHT,
    PLAY_AREA_X, PLAY_AREA_Y, CELL_W, CELL_H,
    GAME_TITLE, STATE_TITLE, STATE_PLAYING,
    STATE_GAME_OVER, STATE_VICTORY, STATE_FLOOR_TRANSITION,
)
from neural_dungeon.render.colors import (
    rgb, glow, BG_COLOR, BORDER_COLOR, GRID_COLOR,
)
from neural_dungeon.render.hud import render_hud


class Renderer:
    def __init__(self, screen):
        self.screen = screen
        pygame.font.init()
        self.font = pygame.font.SysFont("consolas", 16)
        self.font_big = pygame.font.SysFont("consolas", 48, bold=True)
        self.font_med = pygame.font.SysFont("consolas", 24)
        self.font_sm = pygame.font.SysFont("consolas", 14)
        self.tick = 0

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
        self._draw_enemies(room.living_enemies)
        self._draw_projectiles(proj_mgr)
        self._draw_player(player)
        self._draw_door(room)
        render_hud(
            self.screen, self.font, self.font_sm,
            player, floor_num, room_progress,
        )
        if message:
            self._draw_message(message)
        elif room.cleared and room.room_type != "start":
            self._draw_message("ROOM CLEARED - press E to proceed")

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
            radius = max(3, int(e.hitbox_radius * CELL_W * 0.7))
            if e.intangible:
                color = rgb("bright_black")
            pygame.draw.circle(self.screen, glow(color), (px, py), radius + 2)
            pygame.draw.circle(self.screen, color, (px, py), radius)
            # HP bar
            if e.hp < e.max_hp:
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

    def _draw_projectiles(self, proj_mgr):
        for p in proj_mgr.projectiles:
            if not p.alive:
                continue
            px, py = self.game_to_screen(p.x, p.y)
            color = rgb(p.color)
            if p.owner == "player":
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
            ("Arrow Keys", "Aim"),
            ("J / Enter", "Shoot"),
            ("Space", "Dodge Roll"),
            ("Q", "Quit"),
        ]
        y = 340
        for key, desc in controls:
            k = self.font.render(key, True, rgb("bright_yellow"))
            d = self.font.render(f" - {desc}", True, rgb("white"))
            total_w = k.get_width() + d.get_width()
            x = (SCREEN_WIDTH - total_w) // 2
            self.screen.blit(k, (x, y))
            self.screen.blit(d, (x + k.get_width(), y))
            y += 28

        # Pulsing start prompt
        pulse = abs(math.sin(self.tick * 0.05))
        start_color = (0, int(pulse * 255), int(pulse * 128))
        start = self.font_med.render(
            "[ Press ENTER to start ]", True, start_color,
        )
        self.screen.blit(
            start, ((SCREEN_WIDTH - start.get_width()) // 2, 560),
        )

        ver = self.font_sm.render("v0.2.0", True, rgb("bright_black"))
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
            f"DESCENDING TO LAYER {floor_num + 2}",
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
