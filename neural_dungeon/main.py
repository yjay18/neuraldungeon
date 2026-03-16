"""Game loop, input handling, state machine (pygame version)."""
import math
import random
import pygame
from neural_dungeon.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TICK_RATE,
    ROOM_WIDTH, ROOM_HEIGHT, TOTAL_FLOORS, GAME_TITLE,
    STATE_TITLE, STATE_PLAYING, STATE_GAME_OVER, STATE_VICTORY,
    STATE_FLOOR_TRANSITION, STATE_MAP,
    STATE_LEVEL_SELECT, STATE_COLONY_OVERWORLD,
    FRAGMENTS_PER_ENEMY, FRAGMENTS_PER_ELITE, FRAGMENTS_PER_BOSS,
    ROOM_TYPE_ELITE, ROOM_TYPE_BOSS, ROOM_TYPE_SHOP, ROOM_TYPE_WEIGHT,
    NETWORK_LAYERS, PIT_DAMAGE_PER_SECOND, SLOW_MULTIPLIER,
    DOOR_GAME_X, DOOR_GAME_Y, DOOR_INTERACT_RANGE,
    FLASHLIGHT_RANGE, FLASHLIGHT_HALF_ANGLE_DEG,
    ENEMY_FOV_RANGE, ENEMY_FOV_HALF_ANGLE_DEG,
    ENEMY_AWARE_DURATION, ENEMY_SENSE_RANGE,
)
from neural_dungeon.entities.player import Player
from neural_dungeon.entities.projectiles import Projectile, ProjectileManager
from neural_dungeon.entities.items import roll_item_drop
from neural_dungeon.utils import resolve_tile_collision, distance
from neural_dungeon.world.floor import Floor
from neural_dungeon.combat.combat import (
    check_player_vs_enemy_bullets,
    check_player_bullets_vs_enemies,
    check_player_vs_enemy_contact,
)
from neural_dungeon.render.renderer import Renderer
from neural_dungeon.render.map_screen import render_map_screen
from neural_dungeon.render.particles import ParticleSystem
from neural_dungeon.render.colors import rgb
from neural_dungeon.network.dungeon_net import DungeonNet
from neural_dungeon.network.activation import compute_floor_activations


def _point_in_cone(px, py, cone_x, cone_y, cone_angle,
                   cone_half_angle_deg, cone_range):
    """Check if point (px,py) is inside a cone."""
    dx = px - cone_x
    dy = py - cone_y
    dist = math.sqrt(dx * dx + dy * dy)
    if dist > cone_range:
        return False
    if dist < 0.01:
        return True
    angle_to_point = math.atan2(dy, dx)
    diff = (angle_to_point - cone_angle + math.pi) % (2 * math.pi) - math.pi
    return abs(diff) <= math.radians(cone_half_angle_deg)


class Game:
    def __init__(self):
        pygame.init()
        # Logical surface — all game rendering targets this
        self.logical_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.fullscreen = False
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.renderer = Renderer(self.logical_surface)

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

        # Firewall (invulnerability) active item timer
        self.firewall_timer = 0

        # Visual effects
        self.particles = ParticleSystem()
        self.ambient_timer = 0

        # Controls overlay / flashlight hint state
        self.controls_dismissed = False
        self.flashlight_hint_dismissed = False
        self.flashlight_hint_seen = False

        # Pending item drop (boss drops — player chooses to equip or skip)
        self.pending_drop = None  # dict or None

        # Level select state
        self.level_select_cursor = 0  # 0-15: ch1 floors, 16-21: ch2 zones
        self.level_select_section = 0  # 0=ch1, 1=ch2

        # Colony overworld (lazy-loaded)
        self.colony = None

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode(
                (0, 0), pygame.FULLSCREEN | pygame.SCALED,
            )
        else:
            self.screen = pygame.display.set_mode(
                (SCREEN_WIDTH, SCREEN_HEIGHT),
            )

    def _screen_to_logical(self, sx, sy):
        """Convert display pixel coords to logical surface coords."""
        if not self.fullscreen:
            return sx, sy
        sw, sh = self.screen.get_size()
        scale = min(sw / SCREEN_WIDTH, sh / SCREEN_HEIGHT)
        ow = int(SCREEN_WIDTH * scale)
        oh = int(SCREEN_HEIGHT * scale)
        ox = (sw - ow) // 2
        oy = (sh - oh) // 2
        lx = (sx - ox) / scale
        ly = (sy - oy) / scale
        return lx, ly

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
        self.firewall_timer = 0
        self.particles = ParticleSystem()
        self.ambient_timer = 0
        self.controls_dismissed = False
        self.flashlight_hint_dismissed = False
        self.flashlight_hint_seen = False
        self.pending_drop = None

        self.dungeon_net = DungeonNet()
        activations = compute_floor_activations(self.dungeon_net)

        self.floors = []
        num_floors = TOTAL_FLOORS
        for i in range(num_floors):
            layer_idx = i % len(NETWORK_LAYERS)
            weight_matrix = self.dungeon_net.get_weight_matrix(layer_idx)
            floor = Floor.from_network(i, activations[layer_idx], weight_matrix)
            self.floors.append(floor)

        self.state = STATE_MAP

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self._process_events()
            self._process_held_keys()

            # Colony overworld updates at 60fps for smooth movement
            if self.state == STATE_COLONY_OVERWORLD and self.colony:
                self.colony.update()
            else:
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

            # Fullscreen toggle: F11 or Alt+Enter
            if key == pygame.K_F11 or (
                key == pygame.K_RETURN
                and event.mod & pygame.KMOD_ALT
            ):
                self.toggle_fullscreen()
                continue

            if self.state == STATE_TITLE:
                if key == pygame.K_RETURN:
                    self.state = STATE_LEVEL_SELECT
                    self.level_select_cursor = 0
                    self.level_select_section = 0
                elif key == pygame.K_q:
                    self.running = False

            elif self.state == STATE_LEVEL_SELECT:
                self._handle_level_select_key(key)

            elif self.state == STATE_COLONY_OVERWORLD:
                if self.colony:
                    result = self.colony.handle_event(event)
                    if result == "exit":
                        self.state = STATE_LEVEL_SELECT

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

        room = self.current_room

        # Pending boss drop — [1] equip, [2] skip
        if self.pending_drop is not None:
            if key == pygame.K_1:
                drop = self.pending_drop
                p = self.player
                if drop["type"] == "weapon":
                    p.weapon = drop["id"]
                elif drop["type"] == "passive":
                    p.add_passive(drop["id"])
                elif drop["type"] == "active":
                    p.active_item = drop["id"]
                    p.active_item_cooldown = 0
                self.message = f"Equipped {drop['name']}!"
                self.message_timer = 60
                self.pending_drop = None
                return
            elif key == pygame.K_2:
                self.message = "Skipped drop."
                self.message_timer = 60
                self.pending_drop = None
                return

        if key == pygame.K_SPACE:
            self.player.start_dodge()

        # Door interaction — must be near the door
        if key in (pygame.K_e, pygame.K_RETURN):
            if room and room.cleared and room.room_type != "start":
                dist = distance(
                    self.player.x, self.player.y,
                    DOOR_GAME_X, DOOR_GAME_Y,
                )
                if dist <= DOOR_INTERACT_RANGE:
                    self._advance()

        # Flashlight toggle
        if key == pygame.K_t:
            if self.player:
                self.player.flashlight_on = not self.player.flashlight_on
                self.flashlight_hint_dismissed = True

        # Active item (F key)
        if key == pygame.K_f:
            self._use_active_item()

        # Shop / Weight room selection (1/2/3)
        if key in (pygame.K_1, pygame.K_2, pygame.K_3):
            idx = key - pygame.K_1  # 0, 1, 2
            if room:
                if room.room_type == ROOM_TYPE_SHOP:
                    msg = room.shop_buy(idx, self.player)
                    if msg:
                        self.message = msg
                        self.message_timer = 60
                elif room.room_type == ROOM_TYPE_WEIGHT:
                    msg = room.weight_pick(idx, self.player)
                    if msg:
                        self.message = msg
                        self.message_timer = 60

        if key == pygame.K_q:
            self.state = STATE_TITLE

    def _handle_level_select_key(self, key):
        max_ch1 = TOTAL_FLOORS  # 10
        ch2_zones = 6

        if key == pygame.K_ESCAPE:
            self.state = STATE_TITLE
            return

        if key == pygame.K_UP:
            if self.level_select_section == 0:
                if self.level_select_cursor > 0:
                    self.level_select_cursor -= 1
            else:
                if self.level_select_cursor > 0:
                    self.level_select_cursor -= 1
                else:
                    self.level_select_section = 0
                    self.level_select_cursor = max_ch1 - 1

        elif key == pygame.K_DOWN:
            if self.level_select_section == 0:
                if self.level_select_cursor < max_ch1 - 1:
                    self.level_select_cursor += 1
                else:
                    self.level_select_section = 1
                    self.level_select_cursor = 0
            else:
                if self.level_select_cursor < ch2_zones - 1:
                    self.level_select_cursor += 1

        elif key == pygame.K_LEFT:
            if self.level_select_section == 0:
                # In ch1, move left within row (5 per row)
                if self.level_select_cursor > 0:
                    self.level_select_cursor -= 1

        elif key == pygame.K_RIGHT:
            if self.level_select_section == 0:
                if self.level_select_cursor < max_ch1 - 1:
                    self.level_select_cursor += 1

        elif key == pygame.K_RETURN:
            if self.level_select_section == 0:
                # Start Chapter 1 at selected floor
                self._start_at_floor(self.level_select_cursor)
            else:
                if self.level_select_cursor == 0:
                    # The Lanes — start colony
                    self._start_colony()
                else:
                    # Coming Soon — show message
                    self.message = "Coming Soon!"
                    self.message_timer = 60

    def _start_at_floor(self, floor_index):
        """Start Chapter 1 at a specific floor."""
        self.player = Player(ROOM_WIDTH / 2, ROOM_HEIGHT - 3)
        self.proj_mgr = ProjectileManager()
        self.current_floor_index = floor_index
        self.message = ""
        self.firewall_timer = 0
        self.particles = ParticleSystem()
        self.ambient_timer = 0
        self.controls_dismissed = False
        self.flashlight_hint_dismissed = False
        self.flashlight_hint_seen = False
        self.pending_drop = None

        self.dungeon_net = DungeonNet()
        activations = compute_floor_activations(self.dungeon_net)

        self.floors = []
        for i in range(TOTAL_FLOORS):
            layer_idx = i % len(NETWORK_LAYERS)
            weight_matrix = self.dungeon_net.get_weight_matrix(layer_idx)
            floor = Floor.from_network(i, activations[layer_idx],
                                       weight_matrix)
            self.floors.append(floor)

        self.state = STATE_MAP

    def _start_colony(self):
        """Enter the colony overworld."""
        from neural_dungeon.colony.overworld import Overworld
        self.colony = Overworld()
        self.state = STATE_COLONY_OVERWORLD

    def _use_active_item(self):
        p = self.player
        if not p:
            return
        item_id = p.use_active()
        if item_id is None:
            return

        room = self.current_room

        if item_id == "memory_dump":
            # Clear all enemy bullets
            self.proj_mgr.projectiles = [
                b for b in self.proj_mgr.projectiles if b.owner != "enemy"
            ]
            self.message = "Memory Dump!"

        elif item_id == "fork_bomb":
            # 8 bullets outward from player
            for i in range(8):
                angle = i * math.pi / 4
                dx = math.cos(angle)
                dy = math.sin(angle)
                bullet = Projectile(
                    x=p.x, y=p.y, dx=dx, dy=dy,
                    speed=0.8, damage=15, owner="player",
                    char="*", color="bright_yellow",
                    max_range=30,
                )
                self.proj_mgr.spawn(bullet)
            self.message = "Fork Bomb!"

        elif item_id == "firewall":
            self.firewall_timer = 90  # 3 seconds at 30 TPS
            p.iframes = max(p.iframes, 90)
            self.message = "Firewall Active!"

        elif item_id == "heap_overflow":
            if room:
                for enemy in room.living_enemies:
                    enemy.take_damage(20)
            self.message = "Heap Overflow!"

        elif item_id == "stack_trace":
            # Teleport to random walkable spot
            if room and room.layout_grid is not None:
                from neural_dungeon.world.room_layouts import (
                    get_valid_spawn_positions,
                )
                positions = get_valid_spawn_positions(
                    room.layout_grid, 1, avoid_center=False,
                )
                if positions:
                    p.x, p.y = positions[0]
            self.message = "Stack Trace!"

        elif item_id == "debugger":
            if room:
                for enemy in room.living_enemies:
                    enemy.frozen_timer = 60  # 2 seconds
            self.message = "Debugger!"

        self.message_timer = 45

    def _process_held_keys(self):
        if self.state == STATE_COLONY_OVERWORLD:
            if self.colony:
                keys = pygame.key.get_pressed()
                self.colony.process_held_keys(keys)
            return

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

        # Dismiss controls overlay on first movement
        if (mx != 0.0 or my != 0.0) and not self.controls_dismissed:
            self.controls_dismissed = True

        # Mouse aiming — convert mouse pixel pos to game coords
        raw_mx, raw_my = pygame.mouse.get_pos()
        mouse_px, mouse_py = self._screen_to_logical(raw_mx, raw_my)
        player_px, player_py = self.renderer.game_to_screen(p.x, p.y)
        aim_dx = mouse_px - player_px
        aim_dy = mouse_py - player_py
        if aim_dx != 0.0 or aim_dy != 0.0:
            p.set_aim(aim_dx, aim_dy)

        mouse_buttons = pygame.mouse.get_pressed()
        p.shooting = (
            mouse_buttons[0]
            or keys[pygame.K_j]
            or keys[pygame.K_RETURN]
        )

    def _start_floor_gameplay(self):
        floor = self.current_floor
        if not floor:
            return
        floor.build_rooms_from_path()
        self.state = STATE_PLAYING
        room = self.current_room
        if room:
            room.enter(player=self.player)
            if self.player:
                px, py = room.get_player_start()
                self.player.reset_for_room(px, py)

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
            next_room.enter(player=self.player)
            if self.player:
                px, py = next_room.get_player_start()
                self.player.reset_for_room(px, py)

    def _spawn_player_bullets(self):
        """Spawn player bullets with spread/multi-projectile support."""
        p = self.player
        winfo = p.weapon_info
        num = winfo.get("projectiles", 1)
        spread_deg = winfo.get("spread", 0.0)
        base_damage = p.get_effective_damage(winfo["damage"])
        base_range = p.get_effective_range(winfo["range"])

        base_angle = math.atan2(p.aim_dy, p.aim_dx)

        for i in range(num):
            if num > 1 and spread_deg > 0:
                spread_rad = math.radians(spread_deg)
                offset = -spread_rad / 2 + spread_rad * i / (num - 1)
            else:
                offset = 0.0
            angle = base_angle + offset
            dx = math.cos(angle)
            dy = math.sin(angle)

            bullet = Projectile(
                x=p.x, y=p.y, dx=dx, dy=dy,
                speed=winfo["bullet_speed"],
                damage=base_damage,
                owner="player",
                char=winfo["bullet_char"],
                color=winfo["bullet_color"],
                max_range=base_range,
                piercing=winfo.get("piercing", False),
                homing=winfo.get("homing", False),
                turn_rate=winfo.get("turn_rate", 0.0),
            )
            self.proj_mgr.spawn(bullet)

        p.on_shoot()

    def _steer_player_homing(self, room):
        """Steer player homing bullets toward nearest enemy."""
        enemies = room.living_enemies
        if not enemies:
            return
        for bullet in self.proj_mgr.get_player_bullets():
            if not bullet.homing or not bullet.alive:
                continue
            # Find nearest enemy
            best_dist = float("inf")
            best_ex, best_ey = bullet.x, bullet.y
            for e in enemies:
                d = distance(bullet.x, bullet.y, e.x, e.y)
                if d < best_dist:
                    best_dist = d
                    best_ex, best_ey = e.x, e.y
            bullet.steer_toward(best_ex, best_ey)

    def _update(self):
        self.tick_count += 1

        if self.state != STATE_PLAYING:
            return

        p = self.player
        room = self.current_room
        if not p or not room:
            return

        grid = room.layout_grid

        # Firewall timer
        if self.firewall_timer > 0:
            self.firewall_timer -= 1
            p.iframes = max(p.iframes, 1)

        # Player update with tile collision
        p.update(room_grid=grid)

        # Pit damage to player
        if grid is not None and p.alive:
            from neural_dungeon.world.room_layouts import Tile
            gx, gy = int(p.x), int(p.y)
            if (0 <= gx < ROOM_WIDTH and 0 <= gy < ROOM_HEIGHT
                    and grid[gy][gx] == Tile.PIT):
                ticks_per_hit = max(1, TICK_RATE // PIT_DAMAGE_PER_SECOND)
                if self.tick_count % ticks_per_hit == 0:
                    p.take_damage(1)

        if p.can_shoot():
            self._spawn_player_bullets()

        is_dark = room.is_dark

        for enemy in room.living_enemies:
            enemy.blocked_set = room.blocked_set

            # Dark room awareness check
            if is_dark:
                can_see = False
                edist = distance(enemy.x, enemy.y, p.x, p.y)

                # 1. Close range sense
                if edist <= ENEMY_SENSE_RANGE:
                    can_see = True
                # 2. Enemy FOV cone check
                elif _point_in_cone(p.x, p.y, enemy.x, enemy.y,
                                    enemy.facing_angle,
                                    ENEMY_FOV_HALF_ANGLE_DEG,
                                    ENEMY_FOV_RANGE):
                    can_see = True
                # 3. Player flashlight illuminates enemy
                elif p.flashlight_on:
                    aim_angle = math.atan2(p.aim_dy, p.aim_dx)
                    if _point_in_cone(enemy.x, enemy.y, p.x, p.y,
                                      aim_angle,
                                      FLASHLIGHT_HALF_ANGLE_DEG,
                                      FLASHLIGHT_RANGE):
                        can_see = True

                if can_see:
                    enemy.aware_timer = ENEMY_AWARE_DURATION
                elif enemy.aware_timer > 0:
                    enemy.aware_timer -= 1

                # Update facing angle
                if enemy.aware_timer > 0:
                    enemy.facing_angle = math.atan2(
                        p.y - enemy.y, p.x - enemy.x,
                    )
                # else keep current facing (set during wander below)

            else:
                # Non-dark rooms: always aware, face player
                enemy.aware_timer = ENEMY_AWARE_DURATION
                enemy.facing_angle = math.atan2(
                    p.y - enemy.y, p.x - enemy.x,
                )

            # SLOW tile check
            old_speed = enemy.speed
            if grid is not None:
                from neural_dungeon.world.room_layouts import Tile
                egx, egy = int(enemy.x), int(enemy.y)
                if (0 <= egx < ROOM_WIDTH and 0 <= egy < ROOM_HEIGHT
                        and grid[egy][egx] == Tile.SLOW):
                    enemy.speed *= SLOW_MULTIPLIER

            old_ex, old_ey = enemy.x, enemy.y

            # Dark room: unaware enemies wander instead of tracking
            if is_dark and enemy.aware_timer <= 0:
                if not hasattr(enemy, '_wander_angle'):
                    enemy._wander_angle = random.uniform(0, math.tau)
                    enemy._wander_cd = 0
                enemy._wander_cd -= 1
                if enemy._wander_cd <= 0:
                    enemy._wander_angle = random.uniform(0, math.tau)
                    enemy._wander_cd = random.randint(60, 150)
                enemy.x += math.cos(enemy._wander_angle) * enemy.speed * 0.3
                enemy.y += math.sin(enemy._wander_angle) * enemy.speed * 0.3
                enemy.facing_angle = enemy._wander_angle
                enemy._clamp_to_room()
                new_bullets = []
            else:
                new_bullets = enemy.update(
                    p.x, p.y, room.enemies,
                    player_vx=p.move_dx, player_vy=p.move_dy,
                    player_speed=p.speed,
                )
            for b in new_bullets:
                self.proj_mgr.spawn(b)

            enemy.speed = old_speed

            # Tile collision for enemies
            if grid is not None:
                enemy.x, enemy.y = resolve_tile_collision(
                    old_ex, old_ey, enemy.x, enemy.y,
                    enemy.hitbox_radius, grid, block_vent=True,
                )

            # GAN Generator spawn_queue
            if hasattr(enemy, "spawn_queue") and enemy.spawn_queue:
                for fake in enemy.spawn_queue:
                    room.enemies.append(fake)
                enemy.spawn_queue.clear()

        # Steer player homing bullets
        self._steer_player_homing(room)

        # Projectile update with tile collision
        cover_hits = self.proj_mgr.update(p.x, p.y, room_grid=grid)
        for gx, gy, dmg in cover_hits:
            room.damage_cover(gx, gy, dmg)

        prev_hp = p.hp
        check_player_vs_enemy_bullets(p, self.proj_mgr)
        killed = check_player_bullets_vs_enemies(
            room.living_enemies, self.proj_mgr,
        )
        check_player_vs_enemy_contact(p, room.enemies)

        # Player damage particles + screen shake
        if p.hp < prev_hp:
            self.particles.emit_player_damage(p.x, p.y)
            self.renderer.effects.trigger_shake(4)

        for enemy in killed:
            p.enemies_killed += 1
            p.damage_dealt += enemy.max_hp
            if enemy.is_boss:
                p.data_fragments += FRAGMENTS_PER_BOSS
            elif room.room_type == ROOM_TYPE_ELITE:
                p.data_fragments += FRAGMENTS_PER_ELITE
            else:
                p.data_fragments += FRAGMENTS_PER_ENEMY

            # Death explosion particles
            color = rgb(enemy.color)
            count = 25 if enemy.is_boss else 14
            self.particles.emit_explosion(enemy.x, enemy.y, color, count)
            if enemy.is_boss:
                self.renderer.effects.trigger_shake(10)

        just_cleared = room.update_clear_state()
        if just_cleared:
            p.rooms_cleared += 1
            self.message = f"{room.display_name} cleared!"
            self.message_timer = 60
            self.particles.emit_room_clear(ROOM_WIDTH, ROOM_HEIGHT)

            # Error correction passive: heal 5 on clear
            if p.has_passive("error_correction"):
                p.heal(5)

            # Item drop
            drop = roll_item_drop(
                room.room_type, p.weapon, p.passive_items, p.active_item,
            )
            if drop:
                if room.room_type == ROOM_TYPE_BOSS:
                    # Boss drops: offer choice to equip or skip
                    self.pending_drop = drop
                    self.message = f"Dropped: {drop['name']}! [1] Equip  [2] Skip"
                    self.message_timer = 0  # stays until resolved
                elif drop["type"] == "passive":
                    p.add_passive(drop["id"])
                    self.message += f" Got {drop['name']}!"
                elif drop["type"] == "active":
                    p.active_item = drop["id"]
                    p.active_item_cooldown = 0
                    self.message += f" Got {drop['name']}!"

        # Dodge trail particles
        if p.dodging:
            self.particles.emit_dodge_trail(p.x, p.y)

        # Bullet trail particles (every other tick to limit count)
        if self.tick_count % 2 == 0:
            for b in self.proj_mgr.projectiles:
                if b.alive and b.owner == "player":
                    self.particles.emit_trail(b.x, b.y, rgb(b.color))

        # Ambient floating data particles
        self.ambient_timer += 1
        if self.ambient_timer >= 8:
            self.ambient_timer = 0
            self.particles.emit_ambient(ROOM_WIDTH, ROOM_HEIGHT)

        self.particles.update()

        if not p.alive:
            self.state = STATE_GAME_OVER

        if self.message_timer > 0:
            self.message_timer -= 1
            if self.message_timer <= 0 and self.pending_drop is None:
                self.message = ""

    def _render(self):
        p = self.player
        floor = self.current_floor

        if self.state == STATE_LEVEL_SELECT:
            self._render_level_select()
        elif self.state == STATE_COLONY_OVERWORLD:
            if self.colony:
                self.colony.render(self.logical_surface)
        elif self.state == STATE_MAP:
            if floor and floor.floor_map:
                render_map_screen(
                    self.logical_surface, floor.floor_map,
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
            is_dark = room.is_dark if room else False

            # Controls overlay: show in first room until player moves
            show_controls = (
                not self.controls_dismissed
                and self.current_floor_index == 0
                and floor is not None
                and floor.current_room_index == 0
            )

            # Flashlight hint: show in first dark room until toggle
            show_flashlight_hint = False
            if is_dark and not self.flashlight_hint_dismissed:
                if not self.flashlight_hint_seen:
                    self.flashlight_hint_seen = True
                show_flashlight_hint = True

            self.renderer.render_frame(
                player=p or Player(0, 0),
                room=room,
                proj_mgr=self.proj_mgr,
                floor_num=self.current_floor_index,
                room_progress=floor.progress if floor else "",
                game_state=STATE_PLAYING,
                message=self.message,
                particles=self.particles,
                is_dark=is_dark,
                show_controls=show_controls,
                show_flashlight_hint=show_flashlight_hint,
            )

        # Screen shake offset
        shake_x, shake_y = self.renderer.effects.get_shake_offset()

        # Scale logical surface to display
        if self.fullscreen:
            sw, sh = self.screen.get_size()
            scale = min(sw / SCREEN_WIDTH, sh / SCREEN_HEIGHT)
            ow = int(SCREEN_WIDTH * scale)
            oh = int(SCREEN_HEIGHT * scale)
            self.screen.fill((0, 0, 0))
            scaled = pygame.transform.smoothscale(
                self.logical_surface, (ow, oh),
            )
            self.screen.blit(
                scaled,
                ((sw - ow) // 2 + shake_x, (sh - oh) // 2 + shake_y),
            )
        else:
            self.screen.blit(
                self.logical_surface, (shake_x, shake_y),
            )

        pygame.display.flip()


    def _render_level_select(self):
        """Render the level select menu."""
        screen = self.logical_surface
        screen.fill((5, 5, 15))
        font_title = self.renderer.font_big
        font_section = self.renderer.font_med
        font_item = self.renderer.font

        # Title
        title = font_title.render("THE FUN GAME", True, (0, 255, 255))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))

        # Divider
        pygame.draw.line(screen, (0, 100, 120),
                         (100, 90), (SCREEN_WIDTH - 100, 90), 1)

        # Chapter 1
        ch1 = font_section.render("CHAPTER 1 \u2014 NEURAL DUNGEON", True,
                                  (0, 200, 200))
        screen.blit(ch1, (60, 110))

        for i in range(TOTAL_FLOORS):
            col = i % 5
            row = i // 5
            x = 80 + col * 160
            y = 150 + row * 40

            selected = (self.level_select_section == 0
                        and self.level_select_cursor == i)
            color = (255, 255, 255) if selected else (120, 120, 120)
            prefix = "> " if selected else "  "
            label = f"{prefix}Floor {i + 1}"
            text = font_item.render(label, True, color)
            screen.blit(text, (x, y))

            if selected:
                pygame.draw.rect(screen, (0, 255, 255),
                                 (x - 4, y - 2,
                                  text.get_width() + 8,
                                  text.get_height() + 4), 1)

        # Chapter 2
        ch2_y = 260
        ch2 = font_section.render("CHAPTER 2 \u2014 COLONY CREATURES", True,
                                  (0, 200, 200))
        screen.blit(ch2, (60, ch2_y))

        ch2_zones = [
            ("The Lanes", "(Zone 1)", True),
            ("The Crossing", "[Coming Soon]", False),
            ("Green Enclave", "[Coming Soon]", False),
            ("The Deep Woods", "[Coming Soon]", False),
            ("Old Town", "[Coming Soon]", False),
            ("The Facility", "[Coming Soon]", False),
        ]

        for i, (name, tag, available) in enumerate(ch2_zones):
            y = ch2_y + 40 + i * 32
            selected = (self.level_select_section == 1
                        and self.level_select_cursor == i)
            if selected:
                color = (255, 255, 255)
                prefix = "> "
            elif available:
                color = (160, 160, 160)
                prefix = "  "
            else:
                color = (80, 80, 80)
                prefix = "  "

            label = f"{prefix}{name}"
            text = font_item.render(label, True, color)
            screen.blit(text, (80, y))

            tag_color = (100, 200, 100) if available else (80, 80, 80)
            tag_surf = font_item.render(f"  {tag}", True, tag_color)
            screen.blit(tag_surf, (80 + text.get_width(), y))

            if selected:
                total_w = text.get_width() + tag_surf.get_width()
                pygame.draw.rect(screen, (0, 255, 255),
                                 (76, y - 2, total_w + 8,
                                  text.get_height() + 4), 1)

        # Controls hint
        hint = font_item.render(
            "[Arrow Keys] Navigate   [Enter] Select   [Esc] Back",
            True, (60, 60, 80))
        screen.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                           SCREEN_HEIGHT - 40))

        # Coming soon message
        if self.message and self.message_timer > 0:
            msg = font_section.render(self.message, True, (255, 200, 50))
            screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2,
                              SCREEN_HEIGHT - 80))
            self.message_timer -= 1
            if self.message_timer <= 0:
                self.message = ""


def main():
    game = Game()
    try:
        game.run()
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()
