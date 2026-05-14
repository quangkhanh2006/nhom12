"""
tilemap.py — Tạo & render bản đồ tile 2D
==========================================
Mỗi chương có map riêng, được sinh tự động (procedural).
Tile types: 0=floor, 1=wall, 2=door, 3=trap, 4=special, 5=water
"""

import random
import math
import pygame
from settings import (
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    TILE_FLOOR, TILE_WALL, TILE_DOOR, TILE_TRAP, TILE_SPECIAL, TILE_WATER,
    COLOR_FLOOR_1, COLOR_FLOOR_2, COLOR_FLOOR_3, COLOR_FLOOR_4, COLOR_FLOOR_5,
    COLOR_WALL, COLOR_WALL_ACCENT, COLOR_DOOR, COLOR_TRAP, DARK_GRAY,
    CRATE_HP, CRATE_SIZE
)

class Crate:
    """Thùng gỗ có thể đập vỡ."""
    def __init__(self, tx, ty):
        self.x = tx * TILE_SIZE + TILE_SIZE // 2
        self.y = ty * TILE_SIZE + TILE_SIZE // 2
        self.hp = CRATE_HP
        self.size = CRATE_SIZE
        self.alive = True
        self.hit_flash = 0
        
    def get_rect(self):
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2, self.size, self.size)
        
    def render(self, surface, camera):
        if not self.alive: return
        sx, sy = camera.apply(self.x, self.y)
        rect = pygame.Rect(sx - self.size // 2, sy - self.size // 2, self.size, self.size)
        
        if self.hit_flash > 0:
            color = (255, 200, 200)
            self.hit_flash -= 1
        else:
            color = (139, 69, 19)
            
        pygame.draw.rect(surface, color, rect, 0, 4)
        pygame.draw.rect(surface, (80, 40, 10), rect, 2, 4)
        
        # Wood details
        pygame.draw.line(surface, (80, 40, 10), (rect.left + 4, rect.top + 4), (rect.right - 4, rect.bottom - 4), 2)
        pygame.draw.line(surface, (80, 40, 10), (rect.right - 4, rect.top + 4), (rect.left + 4, rect.bottom - 4), 2)


class TileMap:
    """Quản lý bản đồ tile 2D 50x50.

    Attributes:
        grid (list[list[int]]): Mảng 2D lưu loại tile
        chapter (int): Chương hiện tại (1-5)
        floor_color (tuple): Màu sàn theo chương
        spawn_points (list): Vị trí spawn quái
        player_start (tuple): Vị trí bắt đầu player
        door_pos (tuple): Vị trí cửa chuyển chương
        npc_positions (list): Vị trí NPC
    """

    def __init__(self, chapter=1):
        self.chapter = chapter
        self.grid = [[TILE_FLOOR] * MAP_WIDTH for _ in range(MAP_HEIGHT)]
        self.spawn_points = []
        self.player_start = (3 * TILE_SIZE, 3 * TILE_SIZE)
        self.door_pos = None
        self.npc_positions = []
        self.trap_positions = []
        self.crates = []
        self.floor_colors = {
            1: COLOR_FLOOR_1, 2: COLOR_FLOOR_2, 3: COLOR_FLOOR_3,
            4: COLOR_FLOOR_4, 5: COLOR_FLOOR_5
        }
        self.floor_color = self.floor_colors.get(chapter, COLOR_FLOOR_1)
        self._generate_map()

    def _generate_map(self):
        """Sinh map tự động theo chương."""
        # Viền tường bao quanh map
        for x in range(MAP_WIDTH):
            self.grid[0][x] = TILE_WALL
            self.grid[MAP_HEIGHT - 1][x] = TILE_WALL
        for y in range(MAP_HEIGHT):
            self.grid[y][0] = TILE_WALL
            self.grid[y][MAP_WIDTH - 1] = TILE_WALL

        generators = {
            1: self._gen_village, 2: self._gen_city,
            3: self._gen_forest, 4: self._gen_limbo, 5: self._gen_throne
        }
        generators.get(self.chapter, self._gen_village)()
        
        # Sinh thùng gỗ ngẫu nhiên (trừ map 5)
        if self.chapter != 5:
            self._spawn_crates(15 + self.chapter * 5)

    def _spawn_crates(self, count):
        self.crates = []
        attempts = 0
        while len(self.crates) < count and attempts < 200:
            x, y = random.randint(2, MAP_WIDTH - 3), random.randint(2, MAP_HEIGHT - 3)
            if self.grid[y][x] == TILE_FLOOR:
                # Tránh spawn đè lên spawn points hay cửa
                px = x * TILE_SIZE + TILE_SIZE // 2
                py = y * TILE_SIZE + TILE_SIZE // 2
                valid = True
                if self.door_pos and self.door_pos == (x, y): valid = False
                for sx, sy in self.spawn_points:
                    if abs(px - sx) < TILE_SIZE and abs(py - sy) < TILE_SIZE:
                        valid = False
                        break
                if valid:
                    self.crates.append(Crate(x, y))
            attempts += 1

    def _place_room(self, x1, y1, w, h, wall_only_border=True):
        """Đặt 1 phòng hình chữ nhật lên map."""
        for dy in range(h):
            for dx in range(w):
                tx, ty = x1 + dx, y1 + dy
                if 0 < tx < MAP_WIDTH - 1 and 0 < ty < MAP_HEIGHT - 1:
                    if wall_only_border:
                        if dx == 0 or dx == w - 1 or dy == 0 or dy == h - 1:
                            self.grid[ty][tx] = TILE_WALL
                        else:
                            self.grid[ty][tx] = TILE_FLOOR
                    else:
                        self.grid[ty][tx] = TILE_WALL

    def _gen_village(self):
        """Chương 1: Làng hoang tàn — vài ngôi nhà đổ nát, đường đi rộng."""
        # Nhà đổ nát
        houses = [(5, 5, 8, 6), (20, 8, 7, 5), (35, 5, 9, 7),
                  (8, 20, 6, 6), (25, 22, 8, 5), (38, 20, 7, 6),
                  (10, 35, 7, 5), (30, 38, 6, 6)]
        for hx, hy, hw, hh in houses:
            self._place_room(hx, hy, hw, hh)
            # Mở cửa nhà (phá 1 ô tường)
            door_side = random.choice(['top', 'bottom', 'left', 'right'])
            if door_side == 'top' and hy > 1:
                self.grid[hy][hx + hw // 2] = TILE_FLOOR
            elif door_side == 'bottom' and hy + hh < MAP_HEIGHT - 1:
                self.grid[hy + hh - 1][hx + hw // 2] = TILE_FLOOR
            elif door_side == 'left' and hx > 1:
                self.grid[hy + hh // 2][hx] = TILE_FLOOR
            elif door_side == 'right' and hx + hw < MAP_WIDTH - 1:
                self.grid[hy + hh // 2][hx + hw - 1] = TILE_FLOOR

        # Rải đá / đống đổ nát
        for _ in range(40):
            rx, ry = random.randint(2, MAP_WIDTH - 3), random.randint(2, MAP_HEIGHT - 3)
            if self.grid[ry][rx] == TILE_FLOOR:
                self.grid[ry][rx] = TILE_WALL

        self.player_start = (3 * TILE_SIZE, 3 * TILE_SIZE)
        self.door_pos = (MAP_WIDTH - 3, MAP_HEIGHT - 3)
        self.grid[self.door_pos[1]][self.door_pos[0]] = TILE_DOOR
        self._gen_spawn_points(8)
        self.npc_positions = [(15 * TILE_SIZE, 15 * TILE_SIZE)]

    def _gen_city(self):
        """Chương 2: Thành phố Valdris — đường phố, tường cao, ngõ hẹp."""
        # Tường dọc tạo đường phố
        for x in [10, 20, 30, 40]:
            for y in range(2, MAP_HEIGHT - 2):
                if random.random() > 0.2:  # 80% là tường, 20% lối đi
                    self.grid[y][x] = TILE_WALL
        # Tường ngang
        for y in [10, 25, 38]:
            for x in range(2, MAP_WIDTH - 2):
                if random.random() > 0.25:
                    self.grid[y][x] = TILE_WALL
        # Đảm bảo lối đi
        for x in [10, 20, 30, 40]:
            for gap_y in random.sample(range(3, MAP_HEIGHT - 3), 5):
                self.grid[gap_y][x] = TILE_FLOOR
        for y in [10, 25, 38]:
            for gap_x in random.sample(range(3, MAP_WIDTH - 3), 5):
                self.grid[y][gap_x] = TILE_FLOOR

        self.player_start = (2 * TILE_SIZE, 2 * TILE_SIZE)
        self.door_pos = (MAP_WIDTH - 3, MAP_HEIGHT // 2)
        self.grid[self.door_pos[1]][self.door_pos[0]] = TILE_DOOR
        self._gen_spawn_points(12)
        # NPC Sera ở giữa map
        self.npc_positions = [(25 * TILE_SIZE, 20 * TILE_SIZE)]

    def _gen_forest(self):
        """Chương 3: Rừng nguyền rủa — các bãi đất trống nối với nhau."""
        # Phủ toàn bộ bằng tường (cây)
        for y in range(2, MAP_HEIGHT - 2):
            for x in range(2, MAP_WIDTH - 2):
                self.grid[y][x] = TILE_WALL
                
        # Tạo các bãi đất trống (clearings)
        clearings = []
        for _ in range(12):
            cx = random.randint(8, MAP_WIDTH - 9)
            cy = random.randint(8, MAP_HEIGHT - 9)
            radius = random.randint(4, 7)
            clearings.append((cx, cy, radius))
            
        # Đảm bảo có bãi đất ở điểm bắt đầu và cửa
        clearings.insert(0, (4, MAP_HEIGHT // 2, 5))
        clearings.append((MAP_WIDTH - 5, MAP_HEIGHT // 2, 5))
        
        # Đào các bãi đất
        for cx, cy, radius in clearings:
            for y in range(cy - radius, cy + radius + 1):
                for x in range(cx - radius, cx + radius + 1):
                    if 1 < x < MAP_WIDTH - 1 and 1 < y < MAP_HEIGHT - 1:
                        if (x - cx)**2 + (y - cy)**2 <= radius**2:
                            self.grid[y][x] = TILE_FLOOR
                            
        # Nối các bãi đất lại với nhau bằng các con đường thẳng rộng 3 ô
        for i in range(len(clearings) - 1):
            x1, y1, _ = clearings[i]
            x2, y2, _ = clearings[i+1]
            cx, cy = x1, y1
            # Đào ngang
            while cx != x2:
                for w in range(-1, 2):
                    if 1 < cy+w < MAP_HEIGHT-1 and 1 < cx < MAP_WIDTH-1:
                        self.grid[cy+w][cx] = TILE_FLOOR
                cx += 1 if cx < x2 else -1
            # Đào dọc
            while cy != y2:
                for w in range(-1, 2):
                    if 1 < cx+w < MAP_WIDTH-1 and 1 < cy < MAP_HEIGHT-1:
                        self.grid[cy][cx+w] = TILE_FLOOR
                cy += 1 if cy < y2 else -1

        self.player_start = (4 * TILE_SIZE, (MAP_HEIGHT // 2) * TILE_SIZE)
        self.door_pos = (MAP_WIDTH - 3, MAP_HEIGHT // 2)
        
        # Mở khoảng trống xung quanh cửa để chắc chắn không bị bịt
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                if 1 < self.door_pos[0]+dx < MAP_WIDTH-1 and 1 < self.door_pos[1]+dy < MAP_HEIGHT-1:
                    self.grid[self.door_pos[1]+dy][self.door_pos[0]+dx] = TILE_FLOOR
                    
        self.grid[self.door_pos[1]][self.door_pos[0]] = TILE_DOOR
        self._gen_spawn_points(15)

    def _gen_limbo(self):
        """Chương 4: Cõi giữa — nền trôi nổi, bẫy, không quái thường."""
        # Tạo "đảo nổi" bằng nhiều phòng nối nhau
        for y in range(2, MAP_HEIGHT - 2):
            for x in range(2, MAP_WIDTH - 2):
                self.grid[y][x] = TILE_WALL  # Mặc định là hư không

        # Tạo các phòng / platform
        platforms = [(3, 3, 8, 8), (15, 5, 10, 8), (30, 3, 10, 7),
                     (5, 18, 12, 8), (22, 16, 8, 10), (35, 18, 10, 8),
                     (8, 32, 10, 8), (25, 30, 12, 10), (38, 35, 8, 8)]
        for px, py, pw, ph in platforms:
            for dy in range(ph):
                for dx in range(pw):
                    tx, ty = px + dx, py + dy
                    if 1 < tx < MAP_WIDTH - 1 and 1 < ty < MAP_HEIGHT - 1:
                        self.grid[ty][tx] = TILE_FLOOR

        # Cầu nối giữa các platform (bảo đảm đường đi được liên thông)
        bridges = [((10, 7), (15, 7)), ((24, 10), (30, 5)), # Nối P1-P2, P2-P3
                   ((8, 10), (10, 18)), ((35, 9), (38, 18)), # Nối P1-P4, P3-P6 (Lỗi cũ: đứt gãy map)
                   ((16, 22), (22, 20)), ((29, 25), (35, 22)), # Nối P4-P5, P5-P6
                   ((17, 25), (15, 32)), ((33, 35), (38, 38)), # Nối P4-P7, P8-P9
                   ((36, 25), (40, 35)), ((26, 25), (28, 30))] # Nối P6-P9, P5-P8
        for (x1, y1), (x2, y2) in bridges:
            cx, cy = x1, y1
            while cx != x2 or cy != y2:
                # Vẽ cầu rộng 2x2 để đi lại dễ dàng và tránh tắc nghẽn ở đường chéo
                for b_dx in [0, 1]:
                    for b_dy in [0, 1]:
                        nx = cx + b_dx
                        ny = cy + b_dy
                        if 1 < nx < MAP_WIDTH - 1 and 1 < ny < MAP_HEIGHT - 1:
                            self.grid[ny][nx] = TILE_FLOOR
                
                if cx < x2: cx += 1
                elif cx > x2: cx -= 1
                if cy < y2: cy += 1
                elif cy > y2: cy -= 1

        # Đặt bẫy
        trap_count = 0
        for y in range(2, MAP_HEIGHT - 2):
            for x in range(2, MAP_WIDTH - 2):
                if self.grid[y][x] == TILE_FLOOR and random.random() < 0.04:
                    self.grid[y][x] = TILE_TRAP
                    self.trap_positions.append((x * TILE_SIZE, y * TILE_SIZE))
                    trap_count += 1
                    if trap_count >= 20:
                        break
            if trap_count >= 20:
                break

        self.player_start = (5 * TILE_SIZE, 5 * TILE_SIZE)
        # BUG FIX: Đặt cửa ở platform cuối cùng (đảm bảo luôn reachable)
        self.door_pos = (42, 38)
        # Đảm bảo door_pos nằm trong map
        dx = min(self.door_pos[0], MAP_WIDTH - 2)
        dy = min(self.door_pos[1], MAP_HEIGHT - 2)
        dx = max(dx, 2)
        dy = max(dy, 2)
        self.door_pos = (dx, dy)
        self.grid[dy][dx] = TILE_DOOR
        
        # Thêm kẻ địch vào map 4 (bóng tối/shadow)
        self._gen_spawn_points(20)

    def _gen_throne(self):
        """Chương 5: Ngai vàng bóng tối — phòng boss lớn, ít chướng ngại."""
        # Phòng boss lớn ở giữa
        for y in range(5, MAP_HEIGHT - 5):
            for x in range(5, MAP_WIDTH - 5):
                self.grid[y][x] = TILE_FLOOR
        # Cột trang trí
        pillars = [(10, 10), (10, 40), (40, 10), (40, 40),
                   (15, 15), (15, 35), (35, 15), (35, 35),
                   (25, 10), (25, 40)]
        for px, py in pillars:
            if 1 < px < MAP_WIDTH - 1 and 1 < py < MAP_HEIGHT - 1:
                self.grid[py][px] = TILE_WALL
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = px + dx, py + dy
                    if 1 < nx < MAP_WIDTH - 1 and 1 < ny < MAP_HEIGHT - 1:
                        self.grid[ny][nx] = TILE_WALL

        self.player_start = (7 * TILE_SIZE, MAP_HEIGHT // 2 * TILE_SIZE)
        # Boss spawn ở giữa phòng
        self.spawn_points = [(25 * TILE_SIZE, 25 * TILE_SIZE)]

    def _gen_spawn_points(self, count):
        """Tạo điểm spawn quái trên các ô floor trống."""
        self.spawn_points = []
        attempts = 0
        while len(self.spawn_points) < count and attempts < 500:
            x = random.randint(5, MAP_WIDTH - 6)
            y = random.randint(5, MAP_HEIGHT - 6)
            # Kiểm tra ô trung tâm VÀ 4 ô xung quanh đều là floor
            if (self.grid[y][x] == TILE_FLOOR and
                self.grid[y-1][x] == TILE_FLOOR and
                self.grid[y+1][x] == TILE_FLOOR and
                self.grid[y][x-1] == TILE_FLOOR and
                self.grid[y][x+1] == TILE_FLOOR):
                px, py = x * TILE_SIZE + TILE_SIZE // 2, y * TILE_SIZE + TILE_SIZE // 2
                # Không spawn quá gần player start
                dx = px - self.player_start[0]
                dy = py - self.player_start[1]
                if (dx * dx + dy * dy) > (200 * 200):
                    self.spawn_points.append((px, py))
            attempts += 1

    def is_walkable(self, x, y):
        """Kiểm tra vị trí pixel có đi được không."""
        tx, ty = int(x // TILE_SIZE), int(y // TILE_SIZE)
        if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
            return self.grid[ty][tx] in (TILE_FLOOR, TILE_DOOR, TILE_TRAP, TILE_SPECIAL)
        return False

    def is_trap(self, x, y):
        """Kiểm tra vị trí pixel có phải bẫy không."""
        tx, ty = int(x // TILE_SIZE), int(y // TILE_SIZE)
        if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
            return self.grid[ty][tx] == TILE_TRAP
        return False

    def is_door(self, x, y):
        """Kiểm tra vị trí pixel có phải cửa chuyển chương không."""
        tx, ty = int(x // TILE_SIZE), int(y // TILE_SIZE)
        if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
            return self.grid[ty][tx] == TILE_DOOR
        return False

    def get_walkable_grid(self):
        """Trả về grid cho AI pathfinding. 0=đi được, 1=tường, 20=bẫy."""
        walkable = []
        for y in range(MAP_HEIGHT):
            row = []
            for x in range(MAP_WIDTH):
                t = self.grid[y][x]
                if t in (TILE_FLOOR, TILE_DOOR, TILE_SPECIAL):
                    row.append(0)
                elif t == TILE_TRAP:
                    row.append(20) # Chi phí cao
                else:
                    row.append(1) # Tường
            walkable.append(row)
        return walkable

    def _hash(self, x, y):
        """Pseudo-random hash từ tọa độ tile (deterministic)."""
        return ((x * 73856093) ^ (y * 19349663)) & 0xFFFFFFFF

    def render(self, surface, camera):
        """Vẽ tile map lên màn hình — enhanced visuals."""
        sc, ec, sr, er = camera.get_visible_tile_range()
        now = pygame.time.get_ticks()

        for y in range(sr, er + 1):
            for x in range(sc, ec + 1):
                tile = self.grid[y][x]
                sx, sy = camera.apply(x * TILE_SIZE, y * TILE_SIZE)
                rect = pygame.Rect(sx, sy, TILE_SIZE, TILE_SIZE)
                h = self._hash(x, y)

                if tile == TILE_WALL:
                    self._render_wall(surface, sx, sy, x, y, h)
                elif tile == TILE_DOOR:
                    self._render_door(surface, sx, sy, now)
                elif tile == TILE_TRAP:
                    self._render_trap(surface, sx, sy, now, h)
                elif tile == TILE_WATER:
                    self._render_water(surface, sx, sy, now, h)
                else:
                    self._render_floor(surface, sx, sy, x, y, h)

    def _render_wall(self, surface, sx, sy, tx, ty, h):
        """Vẽ tường 2.5D (ưu tiên dùng ảnh texture nếu có)."""
        import assets
        wall_img = assets.get_asset('wall')
        if wall_img:
            # wall.png cao TILE_SIZE*1.5, ta căn phần trên cùng tương ứng với top_y
            top_y = sy - 12
            surface.blit(wall_img, (sx, top_y))
            # Vẽ bóng đổ phía sau
            shadow_rect = pygame.Rect(sx + 5, sy + 5, TILE_SIZE, TILE_SIZE + 10)
            shadow_surf = pygame.Surface((TILE_SIZE, TILE_SIZE + 10), pygame.SRCALPHA)
            shadow_surf.fill((0, 0, 0, 40))
            surface.blit(shadow_surf, shadow_rect.topleft, special_flags=pygame.BLEND_RGBA_MULT)
            return

        # --- BÓNG ĐỔ MÔI TRƯỜNG (Fallback code) ---
        shadow_rect = pygame.Rect(sx + 5, sy + 5, TILE_SIZE, TILE_SIZE + 10)
        shadow_surf = pygame.Surface((TILE_SIZE, TILE_SIZE + 10), pygame.SRCALPHA)
        shadow_surf.fill((0, 0, 0, 80))
        surface.blit(shadow_surf, shadow_rect.topleft)

        # --- MẶT HÔNG 3D CỦA TƯỜNG (FRONT FACE) ---
        depth = 12
        v = (h % 15) - 7
        base = tuple(max(0, min(255, c + v)) for c in COLOR_WALL)
        side_color = tuple(max(0, c - 40) for c in base)
        pygame.draw.rect(surface, side_color, (sx, sy + TILE_SIZE - depth, TILE_SIZE, depth * 2))
        
        # --- MẶT TRÊN CỦA TƯỜNG (TOP FACE) ---
        top_y = sy - depth
        pygame.draw.rect(surface, base, (sx, top_y, TILE_SIZE, TILE_SIZE))

        # Viền sáng mặt trên
        highlight = tuple(min(255, c + 30) for c in base)
        pygame.draw.line(surface, highlight, (sx, top_y), (sx + TILE_SIZE - 1, top_y))
        pygame.draw.line(surface, highlight, (sx, top_y), (sx, top_y + TILE_SIZE - 1))

        # Viền tối mặt trên
        shadow = tuple(max(0, c - 20) for c in base)
        pygame.draw.line(surface, shadow, (sx, top_y + TILE_SIZE - 1),
                         (sx + TILE_SIZE - 1, top_y + TILE_SIZE - 1))
        pygame.draw.line(surface, shadow, (sx + TILE_SIZE - 1, top_y),
                         (sx + TILE_SIZE - 1, top_y + TILE_SIZE - 1))

        # Phân chia gạch mặt trên
        mid_y = top_y + TILE_SIZE // 2
        mortar_color = tuple(max(0, c - 30) for c in base)
        pygame.draw.line(surface, mortar_color, (sx, mid_y), (sx + TILE_SIZE, mid_y), 2)
        off = (h * 7) % 15
        mid_x1 = sx + (TILE_SIZE // 3 + off) % TILE_SIZE
        pygame.draw.line(surface, mortar_color, (mid_x1, top_y), (mid_x1, mid_y), 2)
        mid_x2 = sx + (TILE_SIZE // 2 + off * 2) % TILE_SIZE
        pygame.draw.line(surface, mortar_color, (mid_x2, mid_y), (mid_x2, top_y + TILE_SIZE), 2)

        # Phân chia gạch mặt hông
        pygame.draw.line(surface, tuple(max(0, c-20) for c in side_color), 
                         (sx, top_y + TILE_SIZE), (sx + TILE_SIZE, top_y + TILE_SIZE), 2)
        
        # Rêu xanh bám trên tường
        if h % 3 == 0:
            moss_c = (40 + h % 30, 80 + h % 40, 40)
            pygame.draw.circle(surface, moss_c, (sx + 4 + h % 20, top_y + 4 + (h >> 2) % 10), 3 + h % 3)

    def _render_floor(self, surface, sx, sy, tx, ty, h):
        """Vẽ sàn (ưu tiên dùng texture floor.png nếu có)."""
        import assets
        floor_img = assets.get_asset('floor')
        if floor_img:
            # Tạo bóng/sáng ngẫu nhiên chút để đỡ lặp lại
            v = ((h % 11) - 5)
            tint = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            if v > 0:
                tint.fill((255, 255, 255, v * 2))
            else:
                tint.fill((0, 0, 0, -v * 2))
            
            surface.blit(floor_img, (sx, sy))
            surface.blit(tint, (sx, sy))
            return

        # --- FALLBACK CODE ---
        v1 = ((h % 11) - 5)
        v2 = (((h >> 8) % 7) - 3)
        base_color = tuple(max(0, min(255, c + v1 + v2)) for c in self.floor_color)
        
        if (tx + ty) % 2 == 0:
            base_color = tuple(max(0, c - 8) for c in base_color)
            
        pygame.draw.rect(surface, base_color, (sx, sy, TILE_SIZE, TILE_SIZE))

        # Viền đá (khớp nối)
        grid_color = tuple(max(0, c - 15) for c in base_color)
        pygame.draw.rect(surface, grid_color, (sx, sy, TILE_SIZE, TILE_SIZE), 1)
        
        # Góc bo tròn giả (vẽ 4 góc đậm)
        corner_c = tuple(max(0, c - 20) for c in base_color)
        pygame.draw.rect(surface, corner_c, (sx, sy, 3, 3))
        pygame.draw.rect(surface, corner_c, (sx + TILE_SIZE - 3, sy, 3, 3))
        pygame.draw.rect(surface, corner_c, (sx, sy + TILE_SIZE - 3, 3, 3))
        pygame.draw.rect(surface, corner_c, (sx + TILE_SIZE - 3, sy + TILE_SIZE - 3, 3, 3))

        # Vết bẩn / đốm tối ngẫu nhiên
        if h % 6 == 0:
            spot_x = sx + (h % (TILE_SIZE - 6)) + 3
            spot_y = sy + ((h >> 6) % (TILE_SIZE - 6)) + 3
            spot_r = 1 + (h >> 10) % 3
            spot_color = tuple(max(0, c - 25) for c in base_color)
            spot_surf = pygame.Surface((spot_r * 2, spot_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(spot_surf, (*spot_color, 120), (spot_r, spot_r), spot_r)
            surface.blit(spot_surf, (spot_x - spot_r, spot_y - spot_r))

        # Cỏ nhỏ (chỉ chapter 3 rừng)
        if self.chapter == 3 and h % 4 == 0:
            grass_color = (40 + (h % 20), 80 + (h % 30), 30)
            gx = sx + (h % 24) + 3
            gy = sy + TILE_SIZE - 3
            for i in range(2 + h % 3):
                tip_x = gx + i * 4 - 2 + (h >> (i + 5)) % 3
                pygame.draw.line(surface, grass_color, (gx + i * 4, gy),
                                 (tip_x, gy - 4 - (h >> (i + 8)) % 4), 1)

        # Vết nứt sàn nhẹ (chapter 1, 4)
        if self.chapter in (1, 4) and h % 12 == 0:
            crack_c = tuple(max(0, c - 15) for c in base_color)
            cx, cy = sx + 8 + h % 16, sy + 6 + (h >> 4) % 16
            pygame.draw.line(surface, crack_c, (cx, cy), (cx + 5 + h % 6, cy + 3), 1)
            pygame.draw.line(surface, crack_c, (cx + 5 + h % 6, cy + 3), (cx + 8 + h % 4, cy + 7), 1)

    def _render_door(self, surface, sx, sy, now):
        """Vẽ cửa với glow radial + khung vàng."""
        t = (now % 2000) / 2000.0

        # Nền cửa tối
        pygame.draw.rect(surface, (30, 25, 15), (sx, sy, TILE_SIZE, TILE_SIZE))

        # Glow radial pulsing
        glow_r = TILE_SIZE + int(8 * math.sin(t * 6.28))
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        glow_alpha = int(50 + 30 * math.sin(t * 6.28))
        pygame.draw.circle(glow_surf, (255, 200, 80, glow_alpha),
                           (glow_r, glow_r), glow_r)
        center_x = sx + TILE_SIZE // 2
        center_y = sy + TILE_SIZE // 2
        surface.blit(glow_surf, (center_x - glow_r, center_y - glow_r))

        # Khung cửa vàng
        inner = pygame.Rect(sx + 3, sy + 3, TILE_SIZE - 6, TILE_SIZE - 6)
        frame_color = tuple(min(255, c + int(30 * math.sin(t * 6.28)))
                            for c in COLOR_DOOR)
        pygame.draw.rect(surface, frame_color, inner, 0, 3)
        pygame.draw.rect(surface, (255, 230, 150), inner, 2, 3)

        # Vòng xoáy portal
        cx, cy = sx + TILE_SIZE // 2, sy + TILE_SIZE // 2
        for i in range(12):
            ang = t * 6.28 + i * (6.28 / 12)
            dist = TILE_SIZE // 2 - 2
            px = cx + math.cos(ang) * dist
            py = cy + math.sin(ang) * dist
            ang2 = ang + 1.0
            px2 = cx + math.cos(ang2) * (dist - 6)
            py2 = cy + math.sin(ang2) * (dist - 6)
            pygame.draw.line(surface, (255, 255, 255), (px, py), (px2, py2), 2)
        
        # Inner core
        core_r = int(6 + 2 * math.sin(t * 12))
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), core_r)

    def _render_trap(self, surface, sx, sy, now, h):
        """Vẽ bẫy với rune phát sáng."""
        # Sàn bình thường
        v = (h % 9) - 4
        color = tuple(max(0, min(255, c + v)) for c in self.floor_color)
        pygame.draw.rect(surface, color, (sx, sy, TILE_SIZE, TILE_SIZE))

        t = (now % 3000) / 3000.0
        pulse = abs(math.sin(t * 3.14 * 2))

        # Vòng tròn rune
        cx, cy = sx + TILE_SIZE // 2, sy + TILE_SIZE // 2
        rune_alpha = int(80 + 120 * pulse)
        rune_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)

        # Khung bẫy (đá nứt)
        pygame.draw.rect(surface, (40, 30, 30), (sx + 2, sy + 2, TILE_SIZE - 4, TILE_SIZE - 4), 2)
        
        # Vòng ngoài
        pygame.draw.circle(rune_surf, (*COLOR_TRAP, rune_alpha),
                           (TILE_SIZE // 2, TILE_SIZE // 2), 14, 2)
        # Magic star 5 cánh
        points = []
        for i in range(5):
            ang = -math.pi/2 + i * (4 * math.pi / 5) + t * 6.28
            px = TILE_SIZE // 2 + math.cos(ang) * 12
            py = TILE_SIZE // 2 + math.sin(ang) * 12
            points.append((px, py))
        pygame.draw.polygon(rune_surf, (*COLOR_TRAP, rune_alpha), points, 1)

        # Chữ X nhỏ ở giữa
        inner_alpha = int(100 + 155 * pulse)
        pygame.draw.line(rune_surf, (*COLOR_TRAP, inner_alpha),
                         (TILE_SIZE // 2 - 4, TILE_SIZE // 2 - 4),
                         (TILE_SIZE // 2 + 4, TILE_SIZE // 2 + 4), 2)
        pygame.draw.line(rune_surf, (*COLOR_TRAP, inner_alpha),
                         (TILE_SIZE // 2 + 4, TILE_SIZE // 2 - 4),
                         (TILE_SIZE // 2 - 4, TILE_SIZE // 2 + 4), 2)
        surface.blit(rune_surf, (sx, sy))

    def _render_water(self, surface, sx, sy, now, h):
        """Vẽ nước với sóng animation."""
        from settings import COLOR_WATER
        t = now / 1000.0
        # Base water
        wave = int(8 * math.sin(t * 2 + h * 0.01))
        water_c = tuple(max(0, min(255, c + wave)) for c in COLOR_WATER)
        pygame.draw.rect(surface, water_c, (sx, sy, TILE_SIZE, TILE_SIZE))

        # Wave lines
        for i in range(3):
            wy = sy + 8 + i * 10
            wave_off = int(3 * math.sin(t * 3 + i * 2 + h * 0.1))
            line_c = tuple(min(255, c + 20) for c in water_c)
            pygame.draw.line(surface, line_c,
                             (sx + 2, wy + wave_off),
                             (sx + TILE_SIZE - 2, wy + wave_off + 2), 1)
