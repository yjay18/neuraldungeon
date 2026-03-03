"""Game loop, input handling, state machine (pygame version)."""
import pygame
from neural_dungeon.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TICK_RATE,
    ROOM_WIDTH, ROOM_HEIGHT, TOTAL_FLOORS, GAME_TITLE,
    STATE_TITLE, STATE_PLAYING, STATE_GAME_OVER, STATE_VICTORY,
    STATE_FLOOR_TRANSITION, STATE_MAP,
    FRAGMENTS_PER_ENEMY, FRAGMENTS_PER_ELITE, ROOM_TYPE_ELITE,
    NETWORK_LAYERS,
)
from neural_dungeon.entities.player import Player
from neural_dungeon.entities.projectiles import Projectile, ProjectileManager
from neural_dungeon.world.floor import Floor
from neural_dungeon.combat.combat import (
    check_player_vs_enemy_bullets,
    check_player_bullets_vs_enemies,
    check_player_vs_enemy_contact,
)
from neural_dungeon.render.renderer import Renderer
from neural_dungeon.render.map_screen import render_map_screen
from neural_dungeon.network.dungeon_net import DungeonNet
from neural_dungeon.network.activation import compute_floor_activations


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.screen)

        self.state = STATE_TITLE
        self.running = True
        self.message = ""
        self.message_timer = 0
        self.tick_count = 0

        self.player = None
        self.floors = []
        self.current_floor_index = 0
        self.proj_mgr = ProjectileManager()
        self.dungeon_net = None

        self.tick_accumulator = 0.0
        self.tick_duration = 1.0 / TICK_RATE

    @property
    def current_floor(self):
        if 0 <= self.current_floor_index < len(self.floors):
            return self.floors[self.current_floor_index]
        return None

    @property
    def current_room(self):
        f = self.current_floor
        return f.current_room if f else None

    def new_game(self):
        self.player = Player(ROOM_WIDTH / 2, ROOM_HEIGHT - 3)
        self.proj_mgr = ProjectileManager()
        self.current_floor_index = 0
        self.message = ""

        self.dungeon_net = DungeonNet()
        activations = compute_floor_activations(self.dungeon_net)

        self.floors = []
        num_floors = min(TOTAL_FLOORS, len(NETWORK_LAYERS))
        for i in range(num_floors):
            weight_matrix = self.dungeon_net.get_weight_matrix(i)
            floor = Floor.from_network(i, activations[i], weight_matrix)
            self.floors.append(floor)

        self.state = STATE_MAP

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._process_events()
            self._process_held_keys()

            self.tick_accumulator += dt
            while self.tick_accumulator >= self.tick_duration:
                self._update()
                self.tick_accumulator -= self.tick_duration

            self._render()

        pygame.quit()

    def _process_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return

            if event.type != pygame.KEYDOWN:
                continue

            key = event.key

            if self.state == STATE_TITLE:
                if key == pygame.K_RETURN:
                    self.new_game()
                elif key == pygame.K_q:
                    self.running = False

            elif self.state == STATE_MAP:
                self._handle_map_key(key)

            elif self.state == STATE_PLAYING:
                self._handle_play_key(key)

            elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
                if key == pygame.K_r:
                    self.new_game()
                elif key == pygame.K_q:
                    self.running = False

            elif self.state == STATE_FLOOR_TRANSITION:
                if key == pygame.K_RETURN:
                    self.state = STATE_MAP

    def _handle_map_key(self, key):
        floor = self.current_floor
        if not floor or not floor.floor_map:
            return
        fmap = floor.floor_map

        if key == pygame.K_LEFT:
            row_nodes = fmap.get_row_nodes(fmap.cursor_row)
            if row_nodes:
                cols = [n.col for n in row_nodes]
                if fmap.cursor_col in cols:
                    idx = cols.index(fmap.cursor_col)
                    idx = (idx - 1) % len(cols)
                    fmap.cursor_col = cols[idx]

        elif key == pygame.K_RIGHT:
            row_nodes = fmap.get_row_nodes(fmap.cursor_row)
            if row_nodes:
                cols = [n.col for n in row_nodes]
                if fmap.cursor_col in cols:
                    idx = cols.index(fmap.cursor_col)
                    idx = (idx + 1) % len(cols)
                    fmap.cursor_col = cols[idx]

        elif key in (pygame.K_UP, pygame.K_RETURN):
            fmap.confirm_selection()
            if fmap.is_complete:
                self._start_floor_gameplay()
                return
            fmap.move_cursor("up")

        elif key == pygame.K_q:
            self.state = STATE_TITLE

    def _handle_play_key(self, key):
        if not self.player or not self.player.alive:
            return

        if key == pygame.K_SPACE:
            self.player.start_dodge()

        if key in (pygame.K_e, pygame.K_RETURN):
            room = self.current_room
            if room and room.cleared and room.room_type != "start":
                self._advance()

        if key == pygame.K_q:
            self.state = STATE_TITLE

    def _process_held_keys(self):
        if self.state != STATE_PLAYING:
            return
        if not self.player or not self.player.alive:
            return

        keys = pygame.key.get_pressed()
        p = self.player

        mx, my = 0.0, 0.0
        if keys[pygame.K_w]:
            my = -1.0
        if keys[pygame.K_s]:
            my = 1.0
        if keys[pygame.K_a]:
            mx = -1.0
        if keys[pygame.K_d]:
            mx = 1.0
        p.set_move(mx, my)

        ax, ay = 0.0, 0.0
        if keys[pygame.K_UP]:
            ay = -1.0
        if keys[pygame.K_DOWN]:
            ay = 1.0
        if keys[pygame.K_LEFT]:
            ax = -1.0
        if keys[pygame.K_RIGHT]:
            ax = 1.0
        if ax != 0.0 or ay != 0.0:
            p.set_aim(ax, ay)

        p.shooting = keys[pygame.K_j] or keys[pygame.K_RETURN]

    def _start_floor_gameplay(self):
        floor = self.current_floor
        if not floor:
            return
        floor.build_rooms_from_path()
        self.state = STATE_PLAYING
        if self.player:
            self.player.reset_for_room(ROOM_WIDTH / 2, ROOM_HEIGHT - 3)
        room = self.current_room
        if room:
            room.enter()

    def _advance(self):
        self.proj_mgr.clear()
        floor = self.current_floor
        if not floor:
            return

        next_room = floor.advance_room()
        if next_room is None:
            if self.player:
                self.player.floors_cleared += 1
            self.current_floor_index += 1
            if self.current_floor_index >= len(self.floors):
                self.state = STATE_VICTORY
                return
            self.state = STATE_FLOOR_TRANSITION
            self.message = f"Layer {self.current_floor_index} cleared."
        else:
            next_room.enter()
            if self.player:
                self.player.reset_for_room(ROOM_WIDTH / 2, ROOM_HEIGHT - 3)

    def _update(self):
        self.tick_count += 1

        if self.state != STATE_PLAYING:
            return

        p = self.player
        room = self.current_room
        if not p or not room:
            return

        p.update()

        if p.can_shoot():
            winfo = p.weapon_info
            bullet = Projectile(
                x=p.x, y=p.y,
                dx=p.aim_dx, dy=p.aim_dy,
                speed=winfo["bullet_speed"],
                damage=winfo["damage"],
                owner="player",
                char=winfo["bullet_char"],
                color=winfo["bullet_color"],
                max_range=winfo["range"],
            )
            self.proj_mgr.spawn(bullet)
            p.on_shoot()

        for enemy in room.living_enemies:
            new_bullets = enemy.update(p.x, p.y, room.enemies)
            for b in new_bullets:
                self.proj_mgr.spawn(b)

        self.proj_mgr.update(p.x, p.y)

        check_player_vs_enemy_bullets(p, self.proj_mgr)
        killed = check_player_bullets_vs_enemies(
            room.living_enemies, self.proj_mgr,
        )
        check_player_vs_enemy_contact(p, room.enemies)

        for enemy in killed:
            p.enemies_killed += 1
            p.damage_dealt += enemy.max_hp
            frags = (
                FRAGMENTS_PER_ELITE if room.room_type == ROOM_TYPE_ELITE
                else FRAGMENTS_PER_ENEMY
            )
            p.data_fragments += frags

        just_cleared = room.update_clear_state()
        if just_cleared:
            p.rooms_cleared += 1
            self.message = f"{room.display_name} cleared!"
            self.message_timer = 60

        if not p.alive:
            self.state = STATE_GAME_OVER

        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer <= 0:
                self.message = ""

    def _render(self):
        p = self.player
        floor = self.current_floor

        if self.state == STATE_MAP:
            if floor and floor.floor_map:
                render_map_screen(
                    self.screen, floor.floor_map,
                    self.current_floor_index,
                    tick=self.tick_count,
                )
        elif self.state == STATE_TITLE:
            self.renderer.render_frame(
                player=Player(0, 0),
                room=None,
                proj_mgr=self.proj_mgr,
                floor_num=0,
                room_progress="",
                game_state=STATE_TITLE,
            )
        elif self.state in (STATE_GAME_OVER, STATE_VICTORY):
            self.renderer.render_frame(
                player=p or Player(0, 0),
                room=None,
                proj_mgr=self.proj_mgr,
                floor_num=self.current_floor_index,
                room_progress="",
                game_state=self.state,
            )
        elif self.state == STATE_FLOOR_TRANSITION:
            self.renderer.render_frame(
                player=p or Player(0, 0),
                room=None,
                proj_mgr=self.proj_mgr,
                floor_num=self.current_floor_index,
                room_progress="",
                game_state=STATE_FLOOR_TRANSITION,
                message=self.message,
            )
        else:
            room = self.current_room
            self.renderer.render_frame(
                player=p or Player(0, 0),
                room=room,
                proj_mgr=self.proj_mgr,
                floor_num=self.current_floor_index,
                room_progress=floor.progress if floor else "",
                game_state=STATE_PLAYING,
                message=self.message,
            )

        pygame.display.flip()


def main():
    game = Game()
    try:
        game.run()
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()
