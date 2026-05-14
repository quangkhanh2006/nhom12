"""
enemy.py — Hệ thống kẻ địch
==============================
3 loại quái: Soul (DFS), Minion (BFS), Shadow (A*).
Mỗi loại có AI, chỉ số, và visual riêng.
"""

import math
import random
import pygame
from settings import (
    SOUL_HP, SOUL_DAMAGE, SOUL_SPEED, SOUL_DETECT_RANGE,
    MINION_HP, MINION_DAMAGE, MINION_SPEED, MINION_DETECT_RANGE,
    SHADOW_HP, SHADOW_DAMAGE, SHADOW_SPEED, SHADOW_DETECT_RANGE,
    COLOR_SOUL, COLOR_MINION, COLOR_SHADOW, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    PLAYER_ATTACK_KNOCKBACK, WHITE, RED
)
from ai import (dfs_patrol, bfs_find_path, astar_find_path,
                get_direction_towards, distance_between)
from item import generate_loot


class Enemy:
    """Base class cho kẻ địch.

    Attributes:
        x, y (float): Vị trí pixel
        hp, max_hp (int): Máu
        damage (int): Sát thương
        speed (float): Tốc độ
        detect_range (int): Tầm phát hiện player
        ai_type (str): Loại AI (dfs/bfs/astar)
        alive (bool): Còn sống?
        color (tuple): Màu hiển thị
        path (list): Đường đi hiện tại
        path_index (int): Vị trí trên đường đi
    """

    def __init__(self, x, y, enemy_type="soul"):
        self.x = float(x)
        self.y = float(y)
        self.enemy_type = enemy_type
        self.size = 24
        self.alive = True
        self.hit_flash = False
        self.flash_timer = 0
        self.path = []
        self.visited = set()
        self.path_index = 0
        self.path_timer = 0
        self.path_recalc_interval = 500  # ms giữa mỗi lần tính path
        self.spawn_time = pygame.time.get_ticks()
        self.attack_cooldown = 800  # ms
        self.last_attack = 0
        self.knockback_dx = 0
        self.knockback_dy = 0
        self.knockback_timer = 0
        self.chasing = False

        # Gán chỉ số theo loại
        configs = {
            "soul":   (SOUL_HP, SOUL_DAMAGE, SOUL_SPEED, SOUL_DETECT_RANGE,
                       "dfs", COLOR_SOUL, 1200),
            "minion": (MINION_HP, MINION_DAMAGE, MINION_SPEED, MINION_DETECT_RANGE,
                       "bfs", COLOR_MINION, 600),
            "shadow": (SHADOW_HP, SHADOW_DAMAGE, SHADOW_SPEED, SHADOW_DETECT_RANGE,
                       "astar", COLOR_SHADOW, 800),
        }
        cfg = configs.get(enemy_type, configs["soul"])
        self.max_hp = cfg[0]
        self.hp = cfg[0]
        self.target_hp = self.hp  # Dùng cho animation tụt máu
        self.damage = cfg[1]
        self.speed = cfg[2]
        self.detect_range = cfg[3]
        self.ai_type = cfg[4]
        self.color = cfg[5]
        self.path_recalc_interval = cfg[6]

    def get_rect(self):
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2,
                           self.size, self.size)

    def take_damage(self, amount, knockback_dx=0, knockback_dy=0):
        """Nhận sát thương + knockback.

        Returns:
            bool: True nếu chết
        """
        self.hp -= amount
        self.hit_flash = True
        self.flash_timer = pygame.time.get_ticks()
        self.knockback_dx = knockback_dx * PLAYER_ATTACK_KNOCKBACK
        self.knockback_dy = knockback_dy * PLAYER_ATTACK_KNOCKBACK
        self.knockback_timer = pygame.time.get_ticks()
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True
        return False

    def can_attack(self):
        return pygame.time.get_ticks() - self.last_attack > self.attack_cooldown

    def do_attack(self, player):
        """Tấn công player nếu đủ gần."""
        dist = distance_between(self.x, self.y, player.x, player.y)
        if dist < 35 and self.can_attack():
            self.last_attack = pygame.time.get_ticks()
            return player.take_damage(self.damage)
        return 0

    def update(self, player, tile_map, walkable_grid):
        """Cập nhật AI + di chuyển mỗi frame."""
        if not self.alive:
            return
        now = pygame.time.get_ticks()

        # BUG FIX: Nếu quái bị kẹt trong tường → đẩy ra ô walkable gần nhất
        if not tile_map.is_walkable(self.x, self.y):
            unstuck = False
            for radius in range(1, 5):
                for dx in range(-radius, radius + 1):
                    for dy in range(-radius, radius + 1):
                        test_x = self.x + dx * TILE_SIZE
                        test_y = self.y + dy * TILE_SIZE
                        if tile_map.is_walkable(test_x, test_y):
                            self.x = test_x
                            self.y = test_y
                            unstuck = True
                            break
                    if unstuck:
                        break
                if unstuck:
                    break

        # Flash timer
        if self.hit_flash and now - self.flash_timer > 100:
            self.hit_flash = False

        # Knockback
        if now - self.knockback_timer < 100:
            half = self.size // 2
            new_x = self.x + self.knockback_dx * 0.3
            new_y = self.y + self.knockback_dy * 0.3
            if tile_map.is_walkable(new_x, new_y):
                self.x = max(half, min(MAP_WIDTH * TILE_SIZE - half, new_x))
                self.y = max(half, min(MAP_HEIGHT * TILE_SIZE - half, new_y))
            return

        # Cập nhật máu trễ
        if self.target_hp > self.hp:
            self.target_hp -= (self.target_hp - self.hp) * 0.1
            if self.target_hp - self.hp < 0.5:
                self.target_hp = self.hp
        elif self.target_hp < self.hp:
            self.target_hp = self.hp

        # Kiểm tra player trong tầm detect
        dist = distance_between(self.x, self.y, player.x, player.y)
        self.chasing = dist < self.detect_range and player.alive

        # Tính lại path theo interval
        if now - self.path_timer > self.path_recalc_interval:
            self.path_timer = now
            if self.chasing:
                self._calculate_chase_path(player, walkable_grid)
            else:
                self._calculate_patrol_path(walkable_grid)

        # Di chuyển theo path
        self._follow_path(tile_map, player)

        # Tấn công nếu đủ gần
        if self.chasing:
            self.do_attack(player)

    def _calculate_chase_path(self, player, walkable_grid):
        """Tính đường truy đuổi player."""
        if self.ai_type == "bfs":
            self.path, self.visited = bfs_find_path(self.x, self.y, player.x, player.y, walkable_grid)
        elif self.ai_type == "astar":
            self.path, self.visited = astar_find_path(self.x, self.y, player.x, player.y, walkable_grid)
        else:  # dfs khi chase → đi thẳng
            self.path = []
            self.visited = set()
        self.path_index = 0

    def _calculate_patrol_path(self, walkable_grid):
        """Tính đường tuần tra."""
        if self.ai_type == "dfs":
            if not self.path or self.path_index >= len(self.path):
                self.path, self.visited = dfs_patrol(self.x, self.y, walkable_grid, max_steps=12)
                self.path_index = 0
        else:
            # BFS/A* patrol: đi random
            if not self.path or self.path_index >= len(self.path):
                tx = self.x + random.randint(-150, 150)
                ty = self.y + random.randint(-150, 150)
                if self.ai_type == "bfs":
                    self.path, self.visited = bfs_find_path(self.x, self.y, tx, ty, walkable_grid)
                else:
                    self.path, self.visited = astar_find_path(self.x, self.y, tx, ty, walkable_grid)
                self.path_index = 0

    def _follow_path(self, tile_map, player=None):
        """Di chuyển theo path đã tính."""
        # BUG FIX: DFS khi chase → đi thẳng về phía player
        if self.chasing and self.ai_type == "dfs" and player:
            dx, dy = get_direction_towards(self.x, self.y, player.x, player.y, self.speed)
            half = self.size // 2
            new_x = self.x + dx
            new_y = self.y + dy
            if tile_map.is_walkable(new_x, new_y):
                self.x = max(half, min(MAP_WIDTH * TILE_SIZE - half, new_x))
                self.y = max(half, min(MAP_HEIGHT * TILE_SIZE - half, new_y))
            return

        if not self.path or self.path_index >= len(self.path):
            return

        target_x, target_y = self.path[self.path_index]
        dx, dy = get_direction_towards(self.x, self.y, target_x, target_y, self.speed)
        dist = distance_between(self.x, self.y, target_x, target_y)

        if dist < self.speed * 2:
            self.path_index += 1
        else:
            half = self.size // 2
            new_x = self.x + dx
            new_y = self.y + dy
            if tile_map.is_walkable(new_x, new_y):
                self.x = max(half, min(MAP_WIDTH * TILE_SIZE - half, new_x))
                self.y = max(half, min(MAP_HEIGHT * TILE_SIZE - half, new_y))

    def drop_loot(self):
        """Rơi loot khi chết.

        Returns:
            Item or None
        """
        return generate_loot(self.x, self.y)

    def render(self, surface, camera):
        """Vẽ kẻ địch."""
        if not self.alive:
            return
        if not camera.is_visible(self.x, self.y):
            return

        sx, sy = camera.apply(self.x, self.y)
        half = self.size // 2
        color = (255, 100, 100) if self.hit_flash else self.color
        t = (pygame.time.get_ticks() - self.spawn_time) / 1000.0

        # --- Áp dụng đồ họa Ảnh (Sprite) nếu có ---
        import assets
        img = None
        if self.enemy_type == "soul":
            img = assets.get_asset('soul')
        elif self.enemy_type == "minion":
            img = assets.get_asset('minion')
            
        if img:
            bob = int(4 * math.sin(t * 3)) if self.enemy_type == "soul" else (int(3 * math.sin(t * 15)) if getattr(self, 'path', None) else 0)
            if self.hit_flash:
                flash_surf = img.copy()
                flash_surf.fill((255, 100, 100, 150), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(flash_surf, (sx - img.get_width()//2, sy - img.get_height()//2 + bob))
            else:
                surface.blit(img, (sx - img.get_width()//2, sy - img.get_height()//2 + bob))
        else:
            # --- FALLBACK: Dùng code vẽ đồ họa cũ ---
            if self.enemy_type == "soul":
                # --- Soul (Linh Hồn Lang Thang) ---
                # Ghost: oval trắng xanh, "bay" lên xuống, nhiều lớp opacity
                bob = int(4 * math.sin(t * 3))
                
                # Aura
                aura_surf = pygame.Surface((self.size + 16, self.size + 16), pygame.SRCALPHA)
                pygame.draw.circle(aura_surf, (*color, 30), (self.size // 2 + 8, self.size // 2 + 8), self.size // 2 + 6)
                surface.blit(aura_surf, (sx - half - 8, sy - half + bob - 8))

                # Thân ghost (nhiều lớp)
                ghost_surf = pygame.Surface((self.size + 8, self.size + 12), pygame.SRCALPHA)
                alpha_core = 200 + int(40 * math.sin(t * 4))
                
                # Lớp ngoài mờ
                pygame.draw.ellipse(ghost_surf, (*color, 100), (2, 2, self.size + 4, self.size))
                # Lớp trong sáng
                pygame.draw.ellipse(ghost_surf, (200, 240, 255, alpha_core), (6, 4, self.size - 4, self.size - 4))
                
                # Đuôi ghost (dài và uốn lượn hơn)
                for i in range(4):
                    wave = int(4 * math.sin(t * 5 + i))
                    px = 6 + i * (self.size // 4)
                    pygame.draw.line(ghost_surf, (*color, 120 - i * 20),
                                     (px, self.size - 2), (px + wave, self.size + 8 + i * 2), 3)
                
                surface.blit(ghost_surf, (sx - half - 4, sy - half + bob - 6))
                
                # Mắt rỗng / sáng
                eye_color = (0, 255, 255) if self.chasing else (0, 50, 80)
                pygame.draw.circle(surface, eye_color, (int(sx - 4), int(sy - 3 + bob)), 2)
                pygame.draw.circle(surface, eye_color, (int(sx + 4), int(sy - 3 + bob)), 2)

            elif self.enemy_type == "minion":
                # --- Minion (Tay Sai Malphas) ---
                # Minion: Goblin-like, giáp đỏ sẫm, sừng nhỏ, chạy nhanh
                walk_bob = int(3 * math.sin(t * 15)) if self.path else 0
                
                # Shadow (BUG FIX: dùng SRCALPHA surface)
                shadow_surf = pygame.Surface((self.size, 8), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, self.size, 6))
                surface.blit(shadow_surf, (sx - half, sy + half - 2))
                
                # Body (áo giáp)
                body_color_m = (255, 100, 100) if self.hit_flash else (120, 30, 30)
                pygame.draw.rect(surface, body_color_m, (sx - 8, sy - half + 4 + walk_bob, 16, self.size - 4), 0, 4)
                
                # Giáp vai và đai
                pygame.draw.rect(surface, (80, 20, 20), (sx - 10, sy - half + 6 + walk_bob, 6, 5), 0, 1)
                pygame.draw.rect(surface, (80, 20, 20), (sx + 4, sy - half + 6 + walk_bob, 6, 5), 0, 1)
                pygame.draw.rect(surface, (60, 60, 60), (sx - 8, sy + 4 + walk_bob, 16, 4)) # Đai lưng
                
                # Đầu
                head_y = sy - half - 2 + walk_bob
                pygame.draw.circle(surface, (180, 60, 60), (int(sx), int(head_y)), 7) # Da đỏ
                
                # Sừng (horns)
                pygame.draw.polygon(surface, (200, 200, 180), [(sx - 4, head_y - 6), (sx - 8, head_y - 12), (sx - 2, head_y - 5)])
                pygame.draw.polygon(surface, (200, 200, 180), [(sx + 4, head_y - 6), (sx + 8, head_y - 12), (sx + 2, head_y - 5)])
                
                # Mắt đỏ sáng
                glow = int(200 + 55 * math.sin(t * 8))
                pygame.draw.circle(surface, (glow, 0, 0), (int(sx - 3), int(head_y)), 2)
                pygame.draw.circle(surface, (glow, 0, 0), (int(sx + 3), int(head_y)), 2)
                
                # Vũ khí (Rìu nhỏ)
                ax_x = sx + 8
                ax_y = sy + walk_bob
                pygame.draw.line(surface, (100, 80, 60), (ax_x, ax_y - 4), (ax_x, ax_y + 8), 2) # Cán
                pygame.draw.polygon(surface, (200, 200, 200), [(ax_x, ax_y - 4), (ax_x + 6, ax_y - 8), (ax_x + 8, ax_y - 2), (ax_x, ax_y)]) # Lưỡi rìu

            elif self.enemy_type == "shadow":
                # --- Shadow (Hình Bóng Ký Ức) ---
                # Shadow: Vô định hình, rung động, tia năng lượng tím
                wave1 = int(3 * math.sin(t * 4))
                wave2 = int(3 * math.cos(t * 5))
                
                # Deep Aura
                aura_surf = pygame.Surface((self.size + 24, self.size + 24), pygame.SRCALPHA)
                pygame.draw.ellipse(aura_surf, (*color, 30), (0, 0, self.size + 24, self.size + 24))
                pygame.draw.ellipse(aura_surf, (*color, 60), (4, 4, self.size + 16, self.size + 16))
                surface.blit(aura_surf, (sx - half - 12, sy - half - 12))
                
                # Thân Morphing Polygon
                points = [
                    (sx + wave1, sy - half - wave2), 
                    (sx + half + wave2, sy + wave1),
                    (sx + half - 4, sy + half + wave2), 
                    (sx - half + 4, sy + half - wave1),
                    (sx - half - wave2, sy + wave1)
                ]
                pygame.draw.polygon(surface, (40, 10, 60), points) # Core tối
                pygame.draw.polygon(surface, color, points, 2)     # Viền sáng
                
                # Ký hiệu Rune bay quanh
                for i in range(2):
                    ang = t * 3 + i * math.pi
                    rx = sx + math.cos(ang) * 14
                    ry = sy + math.sin(ang) * 14
                    pygame.draw.rect(surface, (255, 150, 255), (rx - 2, ry - 2, 4, 4), 1)
                
                # Mắt sáng chói
                eye_glow = int(200 + 55 * math.sin(t * 10))
                pygame.draw.circle(surface, (eye_glow, 200, 255), (int(sx - 5 + wave1*0.5), int(sy - 3)), 3)
                pygame.draw.circle(surface, (eye_glow, 200, 255), (int(sx + 5 + wave1*0.5), int(sy - 3)), 3)
                pygame.draw.circle(surface, (255, 255, 255), (int(sx - 5 + wave1*0.5), int(sy - 3)), 1)
                pygame.draw.circle(surface, (255, 255, 255), (int(sx + 5 + wave1*0.5), int(sy - 3)), 1)

        # HP bar nhỏ
        if self.hp < self.max_hp:
            bar_w = self.size
            bar_h = 4
            bx = sx - bar_w // 2
            by = sy - half - 8
            pygame.draw.rect(surface, (60, 20, 20), (bx, by, bar_w, bar_h))
            hp_w = int(bar_w * self.hp / self.max_hp)
            pygame.draw.rect(surface, RED, (bx, by, hp_w, bar_h))
