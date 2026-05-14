"""
pet.py — Hệ thống Linh thú đồng hành
====================================
Pet tự động đi theo Kael và nhặt các item rơi trên mặt đất.
Hình dáng là một Tinh Linh Ánh Sáng (Light Wisp).
"""

import pygame
import math
from ai import distance_between, get_direction_towards
from settings import (
    PET_SPEED, PET_DETECT_RANGE, PET_PICKUP_RANGE,
    COLOR_PET, COLOR_PET_GLOW
)

class Pet:
    """Tinh linh đồng hành."""

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.target_item = None
        self.particles = []
        self.spawn_time = pygame.time.get_ticks()

    def update(self, player, items, tile_map):
        """Cập nhật AI của Pet.
        
        Returns:
            Item or None: Trả về item nếu nhặt được, nếu không trả về None.
        """
        now = pygame.time.get_ticks()
        picked_item = None

        # 1. Tìm item gần nhất chưa nhặt
        if not self.target_item or self.target_item.picked_up:
            self.target_item = None
            closest_dist = PET_DETECT_RANGE
            for item in items:
                if not item.picked_up:
                    dist = distance_between(self.x, self.y, item.x, item.y)
                    if dist < closest_dist:
                        closest_dist = dist
                        self.target_item = item

        # 2. Di chuyển
        if self.target_item:
            # Lao tới nhặt đồ
            tx, ty = self.target_item.x, self.target_item.y
            dist = distance_between(self.x, self.y, tx, ty)
            
            if dist < PET_PICKUP_RANGE:
                # Đã nhặt được!
                picked_item = self.target_item
                self.target_item = None
            else:
                dx, dy = get_direction_towards(self.x, self.y, tx, ty, PET_SPEED)
                self.x += dx
                self.y += dy
        else:
            # Không có đồ thì đi theo Kael, nhưng giữ khoảng cách an toàn (40px)
            dist_to_player = distance_between(self.x, self.y, player.x, player.y)
            if dist_to_player > 50:
                dx, dy = get_direction_towards(self.x, self.y, player.x, player.y, PET_SPEED - 1)
                self.x += dx
                self.y += dy
            elif dist_to_player < 30:
                # Tránh xa ra một chút nếu quá gần
                dx, dy = get_direction_towards(self.x, self.y, player.x, player.y, -2)
                self.x += dx
                self.y += dy

        # 3. Tạo hạt (Trail particles)
        if now % 2 == 0:  # Mỗi 2 frame tạo 1 hạt
            self.particles.append([self.x, self.y, 255]) # x, y, alpha

        # Cập nhật hạt
        for p in self.particles:
            p[2] -= 15 # Giảm alpha
        self.particles = [p for p in self.particles if p[2] > 0]

        return picked_item

    def render(self, surface, camera):
        """Vẽ bé Pet (Mèo ma thuật)."""
        if not camera.is_visible(self.x, self.y):
            return

        t = (pygame.time.get_ticks() - self.spawn_time) / 1000.0
        # Mèo nhún nhẹ khi đi, không bay lơ lửng
        bob = int(2 * abs(math.sin(t * 6)))
        sx, sy = camera.apply(self.x, self.y)
        sy += bob

        # Vẽ trail (vệt sáng dấu chân mèo ma thuật)
        for p in self.particles:
            px, py = camera.apply(p[0], p[1])
            alpha = p[2]
            size = max(1, int(3 * (alpha / 255.0)))
            p_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            # Dấu chân nhỏ: màu tím nhạt
            pygame.draw.circle(p_surf, (180, 150, 220, alpha), (size, size), size)
            surface.blit(p_surf, (px - size, py - size))

        # --- Áp dụng đồ họa Ảnh (Sprite) nếu có ---
        import assets
        pet_img = assets.get_asset('pet')
        if pet_img:
            # Hào quang ma thuật nhẹ phía sau mèo
            glow_r = 18 + int(3 * math.sin(t * 4))
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 220, 100, 30), (glow_r, glow_r), glow_r)
            surface.blit(glow_surf, (sx - glow_r, sy - glow_r))

            # Blit ảnh mèo
            surface.blit(pet_img, (sx - pet_img.get_width()//2, sy - pet_img.get_height()//2))

            # Hiệu ứng mắt sáng nhấp nháy
            eye_pulse = int(30 * math.sin(t * 5))
            eye_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            ec_g = max(0, min(255, 200 + eye_pulse))
            ec_a = max(0, min(255, 100 + eye_pulse))
            pygame.draw.circle(eye_surf, (255, ec_g, 80, ec_a), (3, 3), 3)
            # Mắt trái và phải (vị trí tương đối với ảnh 24x24)
            surface.blit(eye_surf, (sx - 5, sy - 5))
            surface.blit(eye_surf, (sx + 1, sy - 5))
            return

        # --- FALLBACK: Code vẽ mèo bằng shapes ---
        # Thân mèo
        fur_color = (90, 75, 110)
        pygame.draw.ellipse(surface, fur_color, (sx - 8, sy - 4, 16, 12))
        # Đầu
        pygame.draw.circle(surface, fur_color, (int(sx), int(sy - 8)), 7)
        # Tai
        pygame.draw.polygon(surface, fur_color, [(sx - 5, sy - 13), (sx - 8, sy - 20), (sx - 1, sy - 14)])
        pygame.draw.polygon(surface, fur_color, [(sx + 5, sy - 13), (sx + 8, sy - 20), (sx + 1, sy - 14)])
        # Lòng tai hồng
        pygame.draw.polygon(surface, (180, 120, 140), [(sx - 5, sy - 14), (sx - 7, sy - 18), (sx - 2, sy - 14)])
        pygame.draw.polygon(surface, (180, 120, 140), [(sx + 5, sy - 14), (sx + 7, sy - 18), (sx + 2, sy - 14)])
        # Mắt
        eye_glow = (255, 220, 80)
        pygame.draw.circle(surface, eye_glow, (int(sx - 3), int(sy - 9)), 2)
        pygame.draw.circle(surface, eye_glow, (int(sx + 3), int(sy - 9)), 2)
        # Mũi
        pygame.draw.polygon(surface, (220, 140, 150), [(sx, sy - 6), (sx - 1, sy - 5), (sx + 1, sy - 5)])
        # Đuôi
        tail_wave = int(3 * math.sin(t * 5))
        pygame.draw.line(surface, fur_color, (sx + 7, sy), (sx + 12 + tail_wave, sy - 8), 2)

