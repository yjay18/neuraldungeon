"""Colony overworld renderer — layers, shadows, decorations, effects."""
import pygame
from neural_dungeon.colony.config import (
    SCALED_TILE, MAP_COLS, MAP_ROWS, VIEW_W, VIEW_H,
    OVERLAY_CANOPY, WALKABLE_TILES,
    TILE_WALL, TILE_ROOF, TILE_DOOR, TILE_WATER, TILE_PAVED,
    TILE_GRASS, TILE_PATH, TILE_GROUND,
    COLOR_SKY, COLOR_WARM_TINT,
    DECO_NONE,
)
from neural_dungeon.colony.tiles import TileCache
from neural_dungeon.colony.buildings import (
    build_roof_color_map, build_south_face_map,
    draw_building_shadows, draw_building_features,
)
from neural_dungeon.colony.building_sprites import (
    load_building_sprites, load_wang_tilesets, get_building_placements,
    BUILDING_PLACEMENTS,
)
from neural_dungeon.colony.decorations import (
    compute_decorations, draw_decoration, GROUND_DECOS, TALL_DECOS,
)

# Ground color drawn under building tiles (replacing procedural roofs)
_GROUND_UNDER_BUILDING = (140, 130, 115)

STRUCTURE_TILES = {TILE_WALL, TILE_ROOF, TILE_DOOR}


class ColonyRenderer:
    def __init__(self, base_layer, overlay_layer):
        self.base = base_layer
        self.overlay = overlay_layer
        self.tiles = TileCache()
        self.roof_colors = build_roof_color_map(base_layer)
        self.south_faces = build_south_face_map(base_layer)
        self.decorations = compute_decorations(base_layer)
        self.road_centers = self._compute_road_centers(base_layer)

        # Load PixelLab building sprites (one per building, 64x64)
        bld_sprites = load_building_sprites()
        self.building_renders = get_building_placements(bld_sprites)
        self._has_building_sprites = len(self.building_renders) > 0
        self._bld_sprites = bld_sprites

        # Pre-compute tile positions covered by building sprites (2x2 each)
        self.building_sprite_tiles = set()
        for col, row, _key in BUILDING_PLACEMENTS:
            for dr in range(2):
                for dc in range(2):
                    self.building_sprite_tiles.add((col + dc, row + dr))

        # Load Wang tilesets for terrain transitions
        self.wang_tilesets = load_wang_tilesets()
        self._has_wang = len(self.wang_tilesets) > 0

        # Pre-build ground surface for under buildings
        self._ground_fill = pygame.Surface(
            (SCALED_TILE, SCALED_TILE))
        self._ground_fill.fill(_GROUND_UNDER_BUILDING)

        # Pre-build shadow strip for building sprites
        self._bld_shadow = pygame.Surface((64, 5), pygame.SRCALPHA)
        for i in range(5):
            pygame.draw.rect(
                self._bld_shadow, (0, 0, 0, max(0, 35 - i * 7)),
                (0, i, 64, 1))

        # Pre-build warm tint overlay
        self.warm_tint = pygame.Surface((VIEW_W, VIEW_H))
        self.warm_tint.fill(COLOR_WARM_TINT)

        # Pre-build vignette
        self.vignette = self._build_vignette()

        # Pre-build dappled light spots per canopy tile
        self.dapple_surf = self._build_dapple()

        # Pre-build water glow
        self.water_glow = self._build_glow((80, 130, 255, 10), 32)

        # Player aura
        self.player_aura = self._build_radial_glow(
            (0, 200, 255), max_alpha=8, radius=24)

    def _compute_road_centers(self, base_layer):
        centers = set()
        for r in range(MAP_ROWS):
            for c in range(MAP_COLS):
                if base_layer[r][c] != TILE_PAVED:
                    continue
                above = (r > 0 and base_layer[r - 1][c] == TILE_PAVED)
                below = (r < MAP_ROWS - 1
                         and base_layer[r + 1][c] == TILE_PAVED)
                if above and below:
                    centers.add((c, r))
        return centers

    # -- Simple tileset lookup (no Wang indexing) --

    def _get_tileset_tile(self, col, row):
        """Pick a tileset tile for this position using simple logic.

        Uses center tile for interior, edge tile otherwise.
        Returns Surface or None (fall back to procedural).
        """
        if not self._has_wang:
            return None

        tile_id = self.base[row][col]

        if tile_id in (TILE_PAVED, TILE_GROUND):
            ts = self.wang_tilesets.get("road-grass")
            if ts:
                return ts[5]  # center/interior road tile

        elif tile_id == TILE_PATH:
            ts = self.wang_tilesets.get("cobblestone-grass")
            if ts:
                return ts[5]

        elif tile_id == TILE_WATER:
            ts = self.wang_tilesets.get("water-grass")
            if ts:
                return ts[5]

        elif tile_id == TILE_GRASS:
            # Grass near road/path — use outer grass tile
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = row + dr, col + dc
                if 0 <= nr < MAP_ROWS and 0 <= nc < MAP_COLS:
                    nb = self.base[nr][nc]
                    if nb in (TILE_GROUND, TILE_PAVED, TILE_PATH):
                        ts = self.wang_tilesets.get("road-grass")
                        if ts:
                            return ts[0]  # outer/grass edge tile
                        break

        return None

    # -- Pre-built overlays --

    def _build_vignette(self):
        vig = pygame.Surface((VIEW_W, VIEW_H), pygame.SRCALPHA)
        cx, cy = VIEW_W // 2, VIEW_H // 2
        max_dist = 600.0
        for y in range(0, VIEW_H, 2):
            for x in range(0, VIEW_W, 2):
                dist = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
                alpha = int(max(0, min(60, (dist / max_dist - 0.4) * 100)))
                if alpha > 0:
                    pygame.draw.rect(vig, (0, 0, 0, alpha), (x, y, 2, 2))
        return vig

    def _build_dapple(self):
        s = pygame.Surface((SCALED_TILE, SCALED_TILE), pygame.SRCALPHA)
        import random
        random.seed(9999)
        for _ in range(3):
            x = random.randint(4, SCALED_TILE - 4)
            y = random.randint(4, SCALED_TILE - 4)
            pygame.draw.circle(s, (255, 242, 192, 25), (x, y),
                               random.randint(4, 5))
        return s

    def _build_glow(self, color, radius):
        size = radius * 2
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(s, color, (radius, radius), radius)
        return s

    def _build_radial_glow(self, color, max_alpha, radius):
        size = radius * 2
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            t = r / radius
            a = int(max_alpha * (1.0 - t))
            pygame.draw.circle(s, color + (a,), (radius, radius), r)
        return s

    # -- Main render --

    def render(self, screen, camera, player, textbox, tick):
        cam_x, cam_y = camera.x, camera.y
        st = SCALED_TILE

        # 1. Sky fill
        screen.fill((45, 42, 58))

        # Tile range visible
        start_col = max(0, int(cam_x // st) - 1)
        end_col = min(MAP_COLS, int((cam_x + VIEW_W) // st) + 2)
        start_row = max(0, int(cam_y // st) - 1)
        end_row = min(MAP_ROWS, int((cam_y + VIEW_H) // st) + 2)

        # 2. Ground tiles — skip building sprite tiles, draw ground
        #    under structure tiles, use tilesets for terrain
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                px = int(c * st - cam_x)
                py = int(r * st - cam_y)

                # Tiles covered by a building sprite → skip entirely
                if (c, r) in self.building_sprite_tiles:
                    continue

                tile_id = self.base[r][c]

                # Structure tiles (not covered by sprite) → ground fill
                if tile_id in STRUCTURE_TILES:
                    screen.blit(self._ground_fill, (px, py))
                    continue

                # Try tileset tile
                ts_tile = self._get_tileset_tile(c, r)
                if ts_tile is not None:
                    screen.blit(ts_tile, (px, py))
                else:
                    # Procedural fallback
                    roof_color = self.roof_colors.get((c, r))
                    south_w = (c, r) in self.south_faces
                    road_ctr = (c, r) in self.road_centers
                    surf = self.tiles.get_tile(
                        tile_id, r, c, tick, roof_color, south_w, road_ctr)
                    screen.blit(surf, (px, py))

        # 3. Ground decorations
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                deco_id = self.decorations[r][c]
                if deco_id != DECO_NONE and deco_id in GROUND_DECOS:
                    px = int(c * st - cam_x)
                    py = int(r * st - cam_y)
                    draw_decoration(screen, deco_id, px, py)

        # Non-ground, non-tall decorations
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                deco_id = self.decorations[r][c]
                if (deco_id != DECO_NONE
                        and deco_id not in GROUND_DECOS
                        and deco_id not in TALL_DECOS):
                    px = int(c * st - cam_x)
                    py = int(r * st - cam_y)
                    draw_decoration(screen, deco_id, px, py)

        # Tall decorations (street lamps)
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                deco_id = self.decorations[r][c]
                if deco_id in TALL_DECOS:
                    px = int(c * st - cam_x)
                    py = int(r * st - cam_y)
                    draw_decoration(screen, deco_id, px, py)

        # 4. Buildings + Player — Y-sorted
        if self._has_building_sprites:
            drawables = []
            for col, row, key in BUILDING_PLACEMENTS:
                surf = self._bld_sprites.get(key)
                if surf is None:
                    continue
                sort_y = (row + 2) * st  # bottom edge of 2x2 footprint
                drawables.append(("bld", col, row, surf, sort_y))

            # Player sort position: feet Y
            pcx, pcy = player.get_pixel_pos()
            drawables.append(("player", 0, 0, None, pcy))

            drawables.sort(key=lambda d: d[4])

            for item in drawables:
                if item[0] == "bld":
                    _, bc, br, bsurf, _ = item
                    bpx = int(bc * st - cam_x)
                    bpy = int(br * st - cam_y)
                    # Cull off-screen
                    if bpx + 64 < 0 or bpx > VIEW_W:
                        continue
                    if bpy + 64 < 0 or bpy > VIEW_H:
                        continue
                    # Shadow below building
                    screen.blit(self._bld_shadow, (bpx, bpy + 64))
                    # Building sprite
                    screen.blit(bsurf, (bpx, bpy))
                else:
                    # Player
                    self._draw_player(screen, player, cam_x, cam_y)
        else:
            # No building sprites — draw buildings procedurally then player
            draw_building_shadows(screen, self.base, cam_x, cam_y,
                                  VIEW_W, VIEW_H)
            draw_building_features(screen, self.base, self.roof_colors,
                                   self.south_faces, cam_x, cam_y,
                                   VIEW_W, VIEW_H)
            self._draw_player(screen, player, cam_x, cam_y)

        # 5. Overlay layer (tree canopies — render OVER player)
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                if self.overlay[r][c] == OVERLAY_CANOPY:
                    px = int(c * st - cam_x)
                    py = int(r * st - cam_y)
                    canopy = self.tiles.get_canopy(r, c)
                    screen.blit(canopy, (px, py))
                    if (0 <= r < MAP_ROWS and 0 <= c < MAP_COLS
                            and self.base[r][c] in WALKABLE_TILES):
                        screen.blit(self.dapple_surf, (px, py),
                                     special_flags=pygame.BLEND_RGB_ADD)

        # Water glow
        for r in range(start_row, end_row):
            for c in range(start_col, end_col):
                if self.base[r][c] == TILE_WATER:
                    px = int(c * st - cam_x)
                    py = int(r * st - cam_y)
                    screen.blit(self.water_glow,
                                (px - 16, py - 16),
                                special_flags=pygame.BLEND_RGB_ADD)

        # 6. Text box
        textbox.draw(screen)

        # 7. Warm screen tint
        screen.blit(self.warm_tint, (0, 0),
                     special_flags=pygame.BLEND_RGB_MULT)

        # 8. Vignette
        screen.blit(self.vignette, (0, 0))

    def _draw_player(self, screen, player, cam_x, cam_y):
        pcx, pcy = player.get_pixel_pos()
        spx = int(pcx - cam_x)
        spy = int(pcy - cam_y)

        sprite = player.get_sprite()
        sw = sprite.get_width()
        sh = sprite.get_height()
        shadow_w = player.shadow.get_width()

        screen.blit(player.shadow, (spx - shadow_w // 2, spy - 3))
        screen.blit(self.player_aura, (spx - 24, spy - sh // 2 - 24),
                     special_flags=pygame.BLEND_RGB_ADD)
        screen.blit(sprite, (spx - sw // 2, spy - sh))
