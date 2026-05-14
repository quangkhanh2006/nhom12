"""
generate_assets.py — Tạo ảnh đồ họa chất lượng cao cho Ashes of the Fallen
==========================================================================
Dùng Pygame để vẽ Pixel Art chi tiết và lưu thành file PNG.
"""
import pygame
import math
import random
import os

pygame.init()
pygame.display.set_mode((1, 1), pygame.HIDDEN)

os.makedirs("assets/images", exist_ok=True)

TILE_SIZE = 40


# ============================================================
# FLOOR TILE — Gạch đá hầm ngục, có vân đá, vết nứt, rêu mốc
# ============================================================
def generate_floor():
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    # Nền đá xám tối
    for x in range(TILE_SIZE):
        for y in range(TILE_SIZE):
            noise = random.randint(-8, 8)
            # Tạo vân đá bằng sin wave
            wave = int(5 * math.sin(x * 0.3 + y * 0.2))
            r = max(0, min(255, 42 + noise + wave))
            g = max(0, min(255, 46 + noise + wave))
            b = max(0, min(255, 52 + noise + wave))
            surf.set_at((x, y), (r, g, b))

    # Viền gạch (mortar lines)
    mortar = (30, 33, 38)
    pygame.draw.rect(surf, mortar, (0, 0, TILE_SIZE, TILE_SIZE), 1)
    # Đường ngang giữa
    for x in range(TILE_SIZE):
        n = random.randint(-3, 3)
        surf.set_at((x, TILE_SIZE // 2 + (n if abs(n) < 2 else 0)), mortar)

    # Vết nứt ngẫu nhiên
    cx, cy = random.randint(8, 32), random.randint(8, 32)
    for _ in range(random.randint(3, 8)):
        cx2 = cx + random.randint(-4, 4)
        cy2 = cy + random.randint(-4, 4)
        pygame.draw.line(surf, (25, 28, 32), (cx, cy), (cx2, cy2), 1)
        cx, cy = cx2, cy2

    # Đốm rêu xanh
    if random.random() < 0.4:
        mx, my = random.randint(5, 35), random.randint(5, 35)
        for dx in range(-2, 3):
            for dy in range(-2, 3):
                if random.random() < 0.4:
                    nx, ny = mx + dx, my + dy
                    if 0 <= nx < TILE_SIZE and 0 <= ny < TILE_SIZE:
                        surf.set_at((nx, ny), (35 + random.randint(0, 15), 55 + random.randint(0, 20), 30))

    pygame.image.save(surf, "assets/images/floor.png")
    print("  ✔ floor.png")


# ============================================================
# WALL TILE — Tường đá 3D giả lập, có chiều sâu
# ============================================================
def generate_wall():
    depth = 16
    total_h = TILE_SIZE + depth
    surf = pygame.Surface((TILE_SIZE, total_h), pygame.SRCALPHA)

    # --- MẶT TRƯỚC (FRONT FACE) — phần tối hơn ---
    for x in range(TILE_SIZE):
        for y in range(depth):
            noise = random.randint(-6, 6)
            gradient = int(y * 1.5)  # Gradient tối dần xuống dưới
            r = max(0, min(255, 35 + noise - gradient))
            g = max(0, min(255, 38 + noise - gradient))
            b = max(0, min(255, 48 + noise - gradient))
            surf.set_at((x, TILE_SIZE + y), (r, g, b))

    # --- MẶT TRÊN (TOP FACE) — phần sáng hơn ---
    for x in range(TILE_SIZE):
        for y in range(TILE_SIZE):
            noise = random.randint(-8, 8)
            wave = int(4 * math.sin(x * 0.25) * math.cos(y * 0.3))
            r = max(0, min(255, 58 + noise + wave))
            g = max(0, min(255, 62 + noise + wave))
            b = max(0, min(255, 72 + noise + wave))
            surf.set_at((x, y), (r, g, b, 255))

    # Viền sáng (highlight) — mặt trên
    highlight = (85, 90, 100, 255)
    pygame.draw.line(surf, highlight, (0, 0), (TILE_SIZE - 1, 0), 2)
    pygame.draw.line(surf, highlight, (0, 0), (0, TILE_SIZE - 1), 2)

    # Viền tối — mặt trên
    shadow_c = (30, 33, 42, 255)
    pygame.draw.line(surf, shadow_c, (0, TILE_SIZE - 1), (TILE_SIZE - 1, TILE_SIZE - 1), 2)
    pygame.draw.line(surf, shadow_c, (TILE_SIZE - 1, 0), (TILE_SIZE - 1, TILE_SIZE - 1), 2)

    # Đường gạch nối (mortar joints)
    mortar = (40, 43, 52, 255)
    mid_y = TILE_SIZE // 2
    pygame.draw.line(surf, mortar, (0, mid_y), (TILE_SIZE, mid_y), 2)
    pygame.draw.line(surf, mortar, (TILE_SIZE // 3, 0), (TILE_SIZE // 3, mid_y), 2)
    pygame.draw.line(surf, mortar, (TILE_SIZE * 2 // 3, mid_y), (TILE_SIZE * 2 // 3, TILE_SIZE), 2)

    # Viền chia front/top
    pygame.draw.line(surf, shadow_c, (0, TILE_SIZE), (TILE_SIZE, TILE_SIZE), 2)

    # Rêu bám tường
    if random.random() < 0.5:
        mx = random.randint(3, TILE_SIZE - 5)
        for dy in range(random.randint(2, 5)):
            for dx in range(-1, 2):
                nx, ny = mx + dx, dy + 1
                if 0 <= nx < TILE_SIZE and 0 <= ny < TILE_SIZE:
                    surf.set_at((nx, ny), (40, 75 + random.randint(0, 20), 35, 255))

    pygame.image.save(surf, "assets/images/wall.png")
    print("  ✔ wall.png")


# ============================================================
# PLAYER — Kael, Kiếm sĩ với áo choàng tím, tóc trắng xám
# ============================================================
def generate_player():
    # Vẽ lớn rồi scale xuống cho mượt (anti-alias thủ công)
    s = 4  # Scale factor
    W, H = 32 * s, 32 * s
    surf = pygame.Surface((W, H), pygame.SRCALPHA)

    cx, cy = W // 2, H // 2

    # === Bóng đổ mặt đất ===
    pygame.draw.ellipse(surf, (0, 0, 0, 60), (cx - 14 * s, cy + 10 * s, 28 * s, 6 * s))

    # === Áo choàng (Cape) phía sau ===
    cape_pts = [
        (cx - 8 * s, cy - 4 * s),
        (cx + 8 * s, cy - 4 * s),
        (cx + 11 * s, cy + 14 * s),
        (cx + 4 * s, cy + 15 * s),
        (cx, cy + 12 * s),
        (cx - 4 * s, cy + 15 * s),
        (cx - 11 * s, cy + 14 * s),
    ]
    pygame.draw.polygon(surf, (40, 18, 65), cape_pts)
    # Nếp gấp áo choàng
    pygame.draw.line(surf, (55, 30, 80), (cx - 3 * s, cy), (cx - 5 * s, cy + 13 * s), max(1, 2 * s // 3))
    pygame.draw.line(surf, (55, 30, 80), (cx + 3 * s, cy), (cx + 5 * s, cy + 13 * s), max(1, 2 * s // 3))

    # === Thân (Body / Armor) ===
    body_rect = pygame.Rect(cx - 8 * s, cy - 6 * s, 16 * s, 16 * s)
    pygame.draw.rect(surf, (65, 30, 95), body_rect, 0, 3 * s)

    # Giáp ngực (Chest plate)
    chest_pts = [
        (cx, cy - 5 * s),
        (cx + 6 * s, cy),
        (cx + 4 * s, cy + 6 * s),
        (cx, cy + 8 * s),
        (cx - 4 * s, cy + 6 * s),
        (cx - 6 * s, cy),
    ]
    pygame.draw.polygon(surf, (100, 65, 140), chest_pts)
    # Viền giáp
    pygame.draw.polygon(surf, (130, 90, 170), chest_pts, max(1, s))

    # Vai giáp (Shoulder pads)
    pygame.draw.rect(surf, (90, 55, 130), (cx - 10 * s, cy - 5 * s, 6 * s, 5 * s), 0, 2 * s)
    pygame.draw.rect(surf, (90, 55, 130), (cx + 4 * s, cy - 5 * s, 6 * s, 5 * s), 0, 2 * s)
    # Highlight vai
    pygame.draw.rect(surf, (120, 80, 160), (cx - 10 * s, cy - 5 * s, 6 * s, 5 * s), max(1, s // 2), 2 * s)
    pygame.draw.rect(surf, (120, 80, 160), (cx + 4 * s, cy - 5 * s, 6 * s, 5 * s), max(1, s // 2), 2 * s)

    # Đai lưng
    pygame.draw.rect(surf, (50, 45, 35), (cx - 7 * s, cy + 5 * s, 14 * s, 3 * s), 0, s)
    # Khóa đai (buckle)
    pygame.draw.rect(surf, (200, 180, 100), (cx - 2 * s, cy + 5 * s, 4 * s, 3 * s), 0, s)

    # === Đầu (Head) ===
    head_y = cy - 10 * s
    # Tóc phía sau
    pygame.draw.circle(surf, (30, 25, 40), (cx, head_y), 8 * s)
    # Mặt
    pygame.draw.circle(surf, (235, 210, 190), (cx, head_y + s), 6 * s)
    # Tóc phía trước (fringe)
    pygame.draw.arc(surf, (30, 25, 40), (cx - 8 * s, head_y - 7 * s, 16 * s, 12 * s), 0, math.pi, 3 * s)

    # Mắt phát sáng
    eye_color = (120, 220, 255)
    pygame.draw.circle(surf, eye_color, (cx - 3 * s, head_y), 2 * s)
    pygame.draw.circle(surf, (255, 255, 255), (cx - 3 * s, head_y), s)
    pygame.draw.circle(surf, eye_color, (cx + 3 * s, head_y), 2 * s)
    pygame.draw.circle(surf, (255, 255, 255), (cx + 3 * s, head_y), s)

    # === Kiếm bên hông phải ===
    sword_x = cx + 10 * s
    pygame.draw.line(surf, (180, 200, 220), (sword_x, cy - 3 * s), (sword_x, cy + 12 * s), 3 * s // 2)
    # Tay cầm kiếm
    pygame.draw.rect(surf, (80, 60, 40), (sword_x - s, cy + 12 * s, 2 * s, 3 * s))
    # Đầu kiếm sáng
    pygame.draw.circle(surf, (200, 220, 255), (sword_x, cy - 3 * s), s)

    # Scale xuống 32x32
    result = pygame.transform.smoothscale(surf, (32, 32))
    pygame.image.save(result, "assets/images/player.png")
    print("  ✔ player.png")


# ============================================================
# ENEMY MINION — Quỷ lùn giáp đỏ sẫm, có sừng
# ============================================================
def generate_enemy_minion():
    s = 4
    W, H = 32 * s, 32 * s
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    cx, cy = W // 2, H // 2

    # Bóng
    pygame.draw.ellipse(surf, (0, 0, 0, 60), (cx - 10 * s, cy + 10 * s, 20 * s, 5 * s))

    # Thân (áo giáp đỏ sẫm)
    body_rect = pygame.Rect(cx - 7 * s, cy - 4 * s, 14 * s, 14 * s)
    pygame.draw.rect(surf, (110, 28, 28), body_rect, 0, 3 * s)
    # Giáp vai
    pygame.draw.rect(surf, (80, 18, 18), (cx - 9 * s, cy - 3 * s, 5 * s, 4 * s), 0, 2 * s)
    pygame.draw.rect(surf, (80, 18, 18), (cx + 4 * s, cy - 3 * s, 5 * s, 4 * s), 0, 2 * s)
    # Đai lưng
    pygame.draw.rect(surf, (55, 55, 55), (cx - 6 * s, cy + 6 * s, 12 * s, 3 * s))

    # Đầu (da đỏ)
    head_y = cy - 8 * s
    pygame.draw.circle(surf, (170, 55, 55), (cx, head_y), 6 * s)
    # Sừng
    horn_c = (200, 195, 170)
    pygame.draw.polygon(surf, horn_c, [
        (cx - 4 * s, head_y - 5 * s), (cx - 7 * s, head_y - 12 * s), (cx - 2 * s, head_y - 4 * s)
    ])
    pygame.draw.polygon(surf, horn_c, [
        (cx + 4 * s, head_y - 5 * s), (cx + 7 * s, head_y - 12 * s), (cx + 2 * s, head_y - 4 * s)
    ])
    # Mắt đỏ rực
    pygame.draw.circle(surf, (255, 40, 0), (cx - 3 * s, head_y), 2 * s)
    pygame.draw.circle(surf, (255, 200, 0), (cx - 3 * s, head_y), s)
    pygame.draw.circle(surf, (255, 40, 0), (cx + 3 * s, head_y), 2 * s)
    pygame.draw.circle(surf, (255, 200, 0), (cx + 3 * s, head_y), s)

    # Rìu
    ax_x = cx + 10 * s
    pygame.draw.line(surf, (90, 70, 50), (ax_x, cy - 4 * s), (ax_x, cy + 8 * s), 2 * s)
    pygame.draw.polygon(surf, (180, 180, 190), [
        (ax_x, cy - 4 * s), (ax_x + 6 * s, cy - 8 * s), (ax_x + 7 * s, cy - 1 * s), (ax_x, cy)
    ])

    result = pygame.transform.smoothscale(surf, (32, 32))
    pygame.image.save(result, "assets/images/enemy_minion.png")
    print("  ✔ enemy_minion.png")


# ============================================================
# ENEMY SOUL — Linh hồn ma xanh, bay lơ lửng, có đuôi
# ============================================================
def generate_enemy_soul():
    s = 4
    W, H = 32 * s, 36 * s
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    cx = W // 2
    cy = H // 2 - 2 * s

    # Hào quang ngoài
    for i in range(5, 0, -1):
        alpha = 25 * i
        r = 6 * s + i * 3 * s
        glow = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (100, 200, 255, alpha), (r, r), r)
        surf.blit(glow, (cx - r, cy - r))

    # Thân ghost (hình oval)
    pygame.draw.ellipse(surf, (160, 220, 255, 180), (cx - 8 * s, cy - 7 * s, 16 * s, 14 * s))
    # Lớp trong sáng
    pygame.draw.ellipse(surf, (200, 240, 255, 220), (cx - 5 * s, cy - 5 * s, 10 * s, 10 * s))

    # Đuôi ghost (lượn sóng)
    for i in range(5):
        wave = int(3 * s * math.sin(i * 1.5))
        px = cx - 6 * s + i * 3 * s
        alpha = max(10, 180 - i * 35)
        pygame.draw.line(surf, (130, 200, 255, alpha),
                         (px, cy + 5 * s), (px + wave, cy + 12 * s + i * s), max(1, 3 * s // 2))

    # Mắt (rỗng / phát sáng)
    pygame.draw.circle(surf, (0, 255, 255), (cx - 3 * s, cy - s), 2 * s)
    pygame.draw.circle(surf, (255, 255, 255), (cx - 3 * s, cy - s), s)
    pygame.draw.circle(surf, (0, 255, 255), (cx + 3 * s, cy - s), 2 * s)
    pygame.draw.circle(surf, (255, 255, 255), (cx + 3 * s, cy - s), s)

    result = pygame.transform.smoothscale(surf, (32, 36))
    pygame.image.save(result, "assets/images/enemy_soul.png")
    print("  ✔ enemy_soul.png")


# ============================================================
# PET — Mèo ma thuật dễ thương, lông xám tím, mắt phát sáng
# ============================================================
def generate_pet():
    s = 5  # Scale factor lớn hơn để vẽ chi tiết
    W, H = 24 * s, 24 * s
    surf = pygame.Surface((W, H), pygame.SRCALPHA)
    cx, cy = W // 2, H // 2 + 2 * s

    # Màu lông mèo
    fur_main = (90, 75, 110)      # Tím xám
    fur_light = (120, 105, 145)   # Highlight
    fur_dark = (60, 50, 80)       # Shadow
    belly = (140, 130, 160)       # Bụng sáng
    eye_glow = (255, 220, 80)     # Mắt vàng phát sáng
    nose_c = (220, 140, 150)      # Mũi hồng

    # === Bóng đổ ===
    pygame.draw.ellipse(surf, (0, 0, 0, 50), (cx - 8 * s, cy + 6 * s, 16 * s, 4 * s))

    # === Đuôi (vẽ trước để nằm phía sau) ===
    tail_pts = [
        (cx + 6 * s, cy + 3 * s),
        (cx + 10 * s, cy),
        (cx + 11 * s, cy - 4 * s),
        (cx + 10 * s, cy - 7 * s),
        (cx + 8 * s, cy - 8 * s),
    ]
    # Vẽ đuôi bằng nhiều đoạn tròn mượt
    for i in range(len(tail_pts) - 1):
        pygame.draw.line(surf, fur_main, tail_pts[i], tail_pts[i + 1], 3 * s)
    # Đầu đuôi sáng hơn
    pygame.draw.circle(surf, fur_light, tail_pts[-1], 2 * s)

    # === Thân mèo (hình oval nằm ngang - mèo ngồi) ===
    body_rect = (cx - 7 * s, cy - 2 * s, 14 * s, 12 * s)
    pygame.draw.ellipse(surf, fur_main, body_rect)
    # Bụng sáng
    pygame.draw.ellipse(surf, belly, (cx - 4 * s, cy + 1 * s, 8 * s, 7 * s))

    # === Chân trước ===
    # Chân trái
    pygame.draw.ellipse(surf, fur_dark, (cx - 6 * s, cy + 6 * s, 4 * s, 5 * s))
    pygame.draw.ellipse(surf, belly, (cx - 5 * s, cy + 8 * s, 3 * s, 2 * s))  # Bàn chân
    # Chân phải
    pygame.draw.ellipse(surf, fur_dark, (cx + 2 * s, cy + 6 * s, 4 * s, 5 * s))
    pygame.draw.ellipse(surf, belly, (cx + 3 * s, cy + 8 * s, 3 * s, 2 * s))  # Bàn chân

    # === Đầu mèo ===
    head_y = cy - 6 * s
    head_r = 6 * s
    pygame.draw.circle(surf, fur_main, (cx, head_y), head_r)
    # Má sáng
    pygame.draw.circle(surf, fur_light, (cx - 3 * s, head_y + s), 3 * s)
    pygame.draw.circle(surf, fur_light, (cx + 3 * s, head_y + s), 3 * s)

    # === Tai mèo (tam giác nhọn) ===
    # Tai trái
    pygame.draw.polygon(surf, fur_main, [
        (cx - 5 * s, head_y - 4 * s),
        (cx - 8 * s, head_y - 11 * s),
        (cx - 1 * s, head_y - 5 * s),
    ])
    # Lòng tai trái (hồng)
    pygame.draw.polygon(surf, (180, 120, 140), [
        (cx - 5 * s, head_y - 5 * s),
        (cx - 7 * s, head_y - 9 * s),
        (cx - 2 * s, head_y - 5 * s),
    ])
    # Tai phải
    pygame.draw.polygon(surf, fur_main, [
        (cx + 5 * s, head_y - 4 * s),
        (cx + 8 * s, head_y - 11 * s),
        (cx + 1 * s, head_y - 5 * s),
    ])
    # Lòng tai phải (hồng)
    pygame.draw.polygon(surf, (180, 120, 140), [
        (cx + 5 * s, head_y - 5 * s),
        (cx + 7 * s, head_y - 9 * s),
        (cx + 2 * s, head_y - 5 * s),
    ])

    # === Mắt mèo (to, phát sáng ma thuật) ===
    # Viền mắt tối
    pygame.draw.circle(surf, (30, 20, 40), (cx - 3 * s, head_y - s), int(2.5 * s))
    pygame.draw.circle(surf, (30, 20, 40), (cx + 3 * s, head_y - s), int(2.5 * s))
    # Mắt phát sáng
    pygame.draw.circle(surf, eye_glow, (cx - 3 * s, head_y - s), 2 * s)
    pygame.draw.circle(surf, eye_glow, (cx + 3 * s, head_y - s), 2 * s)
    # Con ngươi dọc (mèo!)
    pygame.draw.ellipse(surf, (20, 15, 30), (cx - 3 * s - s // 2, head_y - s - int(1.5 * s), s, 3 * s))
    pygame.draw.ellipse(surf, (20, 15, 30), (cx + 3 * s - s // 2, head_y - s - int(1.5 * s), s, 3 * s))
    # Highlight mắt
    pygame.draw.circle(surf, (255, 255, 255), (cx - 3 * s + s // 2, head_y - s - s // 2), s // 2)
    pygame.draw.circle(surf, (255, 255, 255), (cx + 3 * s + s // 2, head_y - s - s // 2), s // 2)

    # === Mũi (tam giác nhỏ hồng) ===
    pygame.draw.polygon(surf, nose_c, [
        (cx, head_y + s),
        (cx - s, head_y + 2 * s),
        (cx + s, head_y + 2 * s),
    ])

    # === Miệng (cười nhẹ kiểu mèo :3) ===
    pygame.draw.arc(surf, fur_dark, (cx - 2 * s, head_y + s, 2 * s, 2 * s), math.pi, 2 * math.pi, max(1, s // 2))
    pygame.draw.arc(surf, fur_dark, (cx, head_y + s, 2 * s, 2 * s), math.pi, 2 * math.pi, max(1, s // 2))

    # === Ria mép (whiskers) ===
    whisker_c = (180, 170, 200)
    # Trái
    pygame.draw.line(surf, whisker_c, (cx - 4 * s, head_y + s), (cx - 9 * s, head_y - s), max(1, s // 3))
    pygame.draw.line(surf, whisker_c, (cx - 4 * s, head_y + 2 * s), (cx - 9 * s, head_y + 2 * s), max(1, s // 3))
    pygame.draw.line(surf, whisker_c, (cx - 4 * s, head_y + 3 * s), (cx - 9 * s, head_y + 4 * s), max(1, s // 3))
    # Phải
    pygame.draw.line(surf, whisker_c, (cx + 4 * s, head_y + s), (cx + 9 * s, head_y - s), max(1, s // 3))
    pygame.draw.line(surf, whisker_c, (cx + 4 * s, head_y + 2 * s), (cx + 9 * s, head_y + 2 * s), max(1, s // 3))
    pygame.draw.line(surf, whisker_c, (cx + 4 * s, head_y + 3 * s), (cx + 9 * s, head_y + 4 * s), max(1, s // 3))

    # === Hào quang ma thuật nhẹ xung quanh ===
    glow_surf = pygame.Surface((W, H), pygame.SRCALPHA)
    pygame.draw.circle(glow_surf, (255, 220, 100, 25), (cx, cy - 2 * s), 10 * s)
    surf.blit(glow_surf, (0, 0))

    # Scale xuống 24x24
    result = pygame.transform.smoothscale(surf, (24, 24))
    pygame.image.save(result, "assets/images/pet.png")
    print("  ✔ pet.png (🐱 Mèo ma thuật)")


# ============================================================
# RUN
# ============================================================
print("🎨 Đang tạo đồ họa Ashes of the Fallen...")
random.seed(42)  # Cho kết quả ổn định
generate_floor()
generate_wall()
generate_player()
generate_enemy_minion()
generate_enemy_soul()
generate_pet()
print("✅ Hoàn tất! Tất cả ảnh đã được lưu vào assets/images/")
