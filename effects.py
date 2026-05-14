"""
effects.py — Hệ thống hiệu ứng đặc biệt
==========================================
Particles, vignette, screen shake, ambient effects.
"""

import math
import random
import pygame


class Particle:
    """Một hạt particle đơn lẻ."""

    def __init__(self, x, y, dx, dy, color, size, life, gravity=0, fade=True, glow=False):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.color = color
        self.size = size
        self.max_life = life
        self.life = life
        self.gravity = gravity
        self.fade = fade
        self.glow = glow
        self.alive = True

    def update(self):
        self.x += self.dx
        self.y += self.dy
        self.dy += self.gravity
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def render(self, surface, offset_x=0, offset_y=0):
        if not self.alive:
            return
        sx = int(self.x - offset_x)
        sy = int(self.y - offset_y)
        progress = 1 - self.life / self.max_life
        alpha = int(255 * (1 - progress)) if self.fade else 255
        current_size = max(1, int(self.size * (1 - progress * 0.5)))

        if self.glow and current_size > 2:
            glow_r = current_size * 3
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            glow_alpha = max(5, alpha // 4)
            pygame.draw.circle(glow_surf, (*self.color[:3], glow_alpha),
                               (glow_r, glow_r), glow_r)
            surface.blit(glow_surf, (sx - glow_r, sy - glow_r))

        p_surf = pygame.Surface((current_size * 2, current_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(p_surf, (*self.color[:3], alpha),
                           (current_size, current_size), current_size)
        surface.blit(p_surf, (sx - current_size, sy - current_size))


class ParticleSystem:
    """Quản lý toàn bộ particles trong game."""

    def __init__(self):
        self.particles = []
        self.ambient_timer = 0

    def emit(self, x, y, color, count=5, speed=2.0, size=3, life=30,
             gravity=0, spread=6.28, angle=0, fade=True, glow=False):
        """Phát ra nhóm particles tại vị trí."""
        for _ in range(count):
            a = angle + random.uniform(-spread / 2, spread / 2)
            s = speed * random.uniform(0.3, 1.0)
            dx = math.cos(a) * s
            dy = math.sin(a) * s
            sz = max(1, size + random.randint(-1, 1))
            lf = life + random.randint(-5, 5)
            c = tuple(max(0, min(255, ch + random.randint(-15, 15))) for ch in color[:3])
            self.particles.append(Particle(x, y, dx, dy, c, sz, lf, gravity, fade, glow))

    def emit_blood(self, x, y):
        """Hiệu ứng máu khi enemy/player bị đánh."""
        self.emit(x, y, (200, 50, 50), count=8, speed=3, size=2,
                  life=20, gravity=0.15, glow=False)

    def emit_death(self, x, y, color):
        """Hiệu ứng khi enemy chết — bùng nổ hạt."""
        self.emit(x, y, color, count=20, speed=3.5, size=4,
                  life=35, gravity=-0.05, glow=True)
        # Thêm tia sáng
        for _ in range(6):
            a = random.uniform(0, 6.28)
            self.emit(x, y, (255, 255, 220), count=1, speed=5,
                      size=2, life=15, angle=a, spread=0.3, glow=True)

    def emit_pickup(self, x, y, color):
        """Hiệu ứng hạt khi nhặt item (Pet nhặt)."""
        self.emit(x, y, color, count=12, speed=2.5, size=3,
                  life=25, gravity=-0.1, glow=True)

    def emit_dash_trail(self, x, y):
        """Trail khi dash."""
        self.emit(x, y, (120, 100, 220), count=3, speed=0.5,
                  size=4, life=15, glow=True)

    def emit_aoe_burst(self, x, y):
        """Bùng nổ AoE."""
        self.emit(x, y, (180, 80, 255), count=30, speed=4,
                  size=3, life=25, glow=True)
        self.emit(x, y, (255, 200, 255), count=15, speed=6,
                  size=2, life=18, glow=True)

    def emit_pickup(self, x, y, color):
        """Nhặt item."""
        self.emit(x, y, color, count=12, speed=2.5, size=3,
                  life=25, gravity=-0.1, glow=True)

    def emit_heal(self, x, y):
        """Hồi HP."""
        for i in range(8):
            a = (i / 8) * 6.28
            self.emit(x, y, (80, 255, 120), count=1, speed=1.5,
                      size=3, life=30, angle=a, spread=0.3,
                      gravity=-0.08, glow=True)

    def emit_footstep(self, x, y):
        """Bước chân nhẹ."""
        self.emit(x, y + 10, (100, 90, 70), count=2, speed=0.5,
                  size=2, life=10, gravity=0.05)

    def emit_shield_break(self, x, y):
        """Khiên vỡ."""
        self.emit(x, y, (100, 80, 200), count=15, speed=3, size=3,
                  life=25, glow=True)
        self.emit(x, y, (140, 100, 255), count=10, speed=4, size=2,
                  life=18, glow=True)

    def emit_shield_pulse(self, x, y):
        """Shield đang active — hạt xoay quanh."""
        import math
        a = (pygame.time.get_ticks() * 0.01) % (2 * math.pi)
        px = x + math.cos(a) * 20
        py = y + math.sin(a) * 20
        self.emit(px, py, (120, 100, 220), count=1, speed=0.3,
                  size=2, life=15, glow=True)

    def emit_lifesteal_hit(self, x, y):
        """Lifesteal trúng enemy."""
        self.emit(x, y, (220, 50, 80), count=8, speed=2.5, size=3,
                  life=20, glow=True)

    def emit_spirit_spawn(self, x, y):
        """Triệu hồi spirit."""
        self.emit(x, y, (100, 200, 255), count=20, speed=3, size=4,
                  life=30, gravity=-0.05, glow=True)
        self.emit(x, y, (150, 220, 255), count=10, speed=5, size=2,
                  life=20, glow=True)

    def emit_ambient(self, camera, chapter):
        """Tạo hạt ambient theo chương (Thời tiết, Bụi, Đom đóm)."""
        self.ambient_timer += 1
        
        # Tần suất xuất hiện tùy chapter
        if chapter == 2 and self.ambient_timer % 1 != 0: # Mưa liên tục
            return
        elif chapter != 2 and self.ambient_timer % 3 != 0:
            return

        # Random vị trí trong viewport (hoặc ngay trên mép trên cho mưa/tuyết)
        if chapter in (2, 3): # Mưa / Lá rơi từ trên xuống
            wx = camera.offset_x + random.randint(-200, camera.width + 200)
            wy = camera.offset_y - 20
        else:
            wx = camera.offset_x + random.randint(0, camera.width)
            wy = camera.offset_y + random.randint(0, camera.height)

        if chapter == 1:
            # Tro bụi bay ngang — làng hoang tàn
            self.emit(wx, wy, (160, 150, 140), count=1, speed=0.5,
                      size=2, life=80, gravity=-0.01, angle=0.2, spread=0.5, glow=False)
        elif chapter == 2:
            # Mưa — thành phố (rơi nhanh, xéo)
            self.emit(wx, wy, (150, 180, 255), count=2, speed=12,
                      size=1, life=30, gravity=0, angle=1.2, spread=0.1, glow=False)
        elif chapter == 3:
            # Lá rơi & Đom đóm — rừng
            if random.random() < 0.6:
                # Lá
                leaf_color = random.choice([(80, 150, 60), (120, 180, 50), (150, 200, 80)])
                self.emit(wx, wy, leaf_color, count=1, speed=1.5,
                          size=random.randint(2, 4), life=120, gravity=0.02, angle=1.5, spread=1.0, fade=True, glow=False)
            else:
                # Đom đóm (từ dưới lên)
                hx = camera.offset_x + random.randint(0, camera.width)
                hy = camera.offset_y + camera.height + 20
                self.emit(hx, hy, (180, 255, 100), count=1, speed=0.5,
                          size=2, life=100, gravity=-0.02, angle=-1.5, spread=2.0, glow=True)
        elif chapter == 4:
            # Hạt năng lượng tím (hút vào tâm)
            self.emit(wx, wy, (200, 100, 255), count=1, speed=0.8,
                      size=random.randint(2, 4), life=60, gravity=-0.03, glow=True)
        elif chapter == 5:
            # Tàn lửa đỏ rực — ngai vàng (bay lên mạnh)
            if random.random() < 0.5:
                self.emit(wx, wy + 200, (255, 80, 20), count=1, speed=2.5,
                          size=3, life=60, gravity=-0.1, angle=-1.5, spread=0.5, glow=True)
                # Khói mờ
                self.emit(wx, wy + 200, (80, 40, 40), count=1, speed=1.0,
                          size=6, life=80, gravity=-0.05, angle=-1.5, spread=1.0, glow=False)

    def update(self):
        for p in self.particles:
            p.update()
        self.particles = [p for p in self.particles if p.alive]
        # Giới hạn để tránh lag
        if len(self.particles) > 500:
            self.particles = self.particles[-500:]

    def render(self, surface, camera):
        """Render particles (world space)."""
        for p in self.particles:
            p.render(surface, camera.offset_x, camera.offset_y)

    def render_screen(self, surface):
        """Render particles (screen space — cho menu etc.)."""
        for p in self.particles:
            p.render(surface)


class ScreenEffects:
    """Hiệu ứng toàn màn hình: vignette, shake, flash."""

    def __init__(self, width, height):
        self.width = width
        self.height = height
        # Vignette (tạo 1 lần, cache lại)
        self.vignette = self._create_vignette()
        # Screen shake
        self.shake_intensity = 0
        self.shake_timer = 0
        self.shake_offset_x = 0
        self.shake_offset_y = 0
        # Flash
        self.flash_alpha = 0
        self.flash_color = (255, 255, 255)
        self.flash_timer = 0

    def _create_vignette(self):
        """Tạo overlay vignette gradient tối ở viền."""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        cx, cy = self.width // 2, self.height // 2
        max_dist = (cx ** 2 + cy ** 2) ** 0.5
        # Vẽ từ ngoài vào
        for radius in range(int(max_dist), 0, -8):
            progress = radius / max_dist
            if progress < 0.4:
                alpha = 0
            else:
                alpha = int(120 * ((progress - 0.4) / 0.6) ** 1.5)
            alpha = min(alpha, 120)
            pygame.draw.circle(surf, (0, 0, 0, alpha), (cx, cy), radius)
        return surf

    def shake(self, intensity=5, duration=200):
        """Rung màn hình."""
        self.shake_intensity = intensity
        self.shake_timer = pygame.time.get_ticks()

    def flash(self, color=(255, 255, 255), intensity=80):
        """Flash màn hình."""
        self.flash_color = color
        self.flash_alpha = intensity
        self.flash_timer = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        # Shake
        if self.shake_intensity > 0:
            elapsed = now - self.shake_timer
            if elapsed < 200:
                decay = 1 - elapsed / 200
                self.shake_offset_x = random.randint(-int(self.shake_intensity * decay),
                                                      int(self.shake_intensity * decay))
                self.shake_offset_y = random.randint(-int(self.shake_intensity * decay),
                                                      int(self.shake_intensity * decay))
            else:
                self.shake_intensity = 0
                self.shake_offset_x = 0
                self.shake_offset_y = 0
        # Flash
        if self.flash_alpha > 0:
            elapsed = now - self.flash_timer
            self.flash_alpha = max(0, self.flash_alpha - 3)

    def apply(self, surface):
        """Áp dụng vignette + flash overlay."""
        surface.blit(self.vignette, (0, 0))
        if self.flash_alpha > 0:
            flash_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            flash_surf.fill((*self.flash_color, self.flash_alpha))
            surface.blit(flash_surf, (0, 0))

    def get_offset(self):
        """Lấy offset shake cho camera."""
        return self.shake_offset_x, self.shake_offset_y
