"""
ui.py — HUD, Minimap, Floating Text — ENHANCED VISUALS
========================================================
Glassmorphism panels, gradient HP bar, animated skill icons,
polished minimap, outlined damage numbers.
"""

import math
import random
import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    HP_BAR_WIDTH, HP_BAR_HEIGHT, HP_BAR_X, HP_BAR_Y,
    MINIMAP_WIDTH, MINIMAP_HEIGHT, MINIMAP_X, MINIMAP_Y,
    SKILL_ICON_SIZE, SKILL_BAR_Y,
    FLOAT_TEXT_DURATION, FLOAT_TEXT_SPEED,
    DASH_COOLDOWN, AOE_COOLDOWN,
    SHIELD_COOLDOWN, LIFESTEAL_COOLDOWN, SUMMON_COOLDOWN,
    COLOR_HP_BAR, COLOR_HP_BG, COLOR_COOLDOWN, COLOR_COOLDOWN_READY,
    COLOR_DMG_NORMAL, COLOR_DMG_CRIT, COLOR_DMG_PLAYER, COLOR_HEAL,
    WHITE, GRAY, YELLOW, RED, BLACK, ORANGE, GREEN,
    CHAPTER_QUESTS, COMBO_TIMEOUT, EXP_PER_LEVEL, MAX_LEVEL
)


class FloatingText:
    """Text bay lên khi damage/heal — có outline để dễ đọc."""

    def __init__(self, x, y, text, color, camera, big=False):
        sx, sy = camera.apply(x, y)
        self.x = sx
        self.y = sy
        self.text = str(text)
        self.color = color
        self.spawn_time = pygame.time.get_ticks()
        self.alive = True
        self.big = big  # Crit text lớn hơn
        self.start_x = sx + (-15 + hash(text) % 30)  # Random X offset

    def update(self):
        elapsed = pygame.time.get_ticks() - self.spawn_time
        if elapsed > FLOAT_TEXT_DURATION:
            self.alive = False
        self.y -= FLOAT_TEXT_SPEED
        # Ease-out movement
        progress = elapsed / FLOAT_TEXT_DURATION if FLOAT_TEXT_DURATION > 0 else 1
        self.x = self.start_x + math.sin(progress * 3) * 3

    def render(self, surface, font, big_font):
        if not self.alive:
            return
        elapsed = pygame.time.get_ticks() - self.spawn_time
        alpha = max(0, 255 - int(255 * elapsed / FLOAT_TEXT_DURATION))
        progress = elapsed / FLOAT_TEXT_DURATION

        # Scale effect cho crit
        use_font = big_font if self.big else font
        scale = 1.0 + (0.5 * (1 - progress)) if self.big else 1.0

        # BUG FIX: import random đã được move lên đầu file
        shake_x = random.randint(-2, 2) if self.big and progress < 0.2 else 0
        shake_y = random.randint(-2, 2) if self.big and progress < 0.2 else 0

        # Outline (vẽ text đen xung quanh trước)
        for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]:
            outline = use_font.render(self.text, True, BLACK)
            outline.set_alpha(alpha)
            surface.blit(outline, (int(self.x) - outline.get_width() // 2 + ox + shake_x,
                                   int(self.y) + oy + shake_y))

        text_surf = use_font.render(self.text, True, self.color)
        text_surf.set_alpha(alpha)
        surface.blit(text_surf, (int(self.x) - text_surf.get_width() // 2 + shake_x, int(self.y) + shake_y))

class ActionLog:
    """Hiển thị nhật ký sự kiện ở góc trái màn hình."""
    def __init__(self):
        self.logs = []
        self._font = None
    
    def add(self, text, color=WHITE):
        self.logs.append({"text": text, "color": color, "time": pygame.time.get_ticks()})
        if len(self.logs) > 6:
            self.logs.pop(0)
            
    def update(self):
        now = pygame.time.get_ticks()
        self.logs = [log for log in self.logs if now - log["time"] < 5000]
        
    def render(self, surface):
        if not self._font:
            self._font = pygame.font.SysFont("consolas", 14)
        now = pygame.time.get_ticks()
        y = SCREEN_HEIGHT - 120
        for log in reversed(self.logs):
            elapsed = now - log["time"]
            alpha = max(0, 255 - int(255 * elapsed / 5000))
            text = self._font.render(log["text"], True, log["color"])
            text.set_alpha(alpha)
            # Outline
            for ox, oy in [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1), (-1, 0), (1, 0)]:
                outline = self._font.render(log["text"], True, BLACK)
                outline.set_alpha(alpha)
                surface.blit(outline, (20 + ox, y + oy))
            surface.blit(text, (20, y))
            y -= 22


class UI:
    """Quản lý toàn bộ UI/HUD — premium design."""

    def __init__(self):
        self.floating_texts = []
        self._font = None
        self._small_font = None
        self._big_font = None
        self._title_font = None
        self._dmg_font = None
        self._dmg_big_font = None
        self.minimap_surface = pygame.Surface((MINIMAP_WIDTH, MINIMAP_HEIGHT), pygame.SRCALPHA)
        # Cache cho glassmorphism panels
        self._hud_panel = None
        self._minimap_frame = None
        self.action_log = ActionLog()
        # Fog of War: track explored tiles
        self.explored = set()
        self.fog_radius = 8  # Bán kính khám phá (tiles)

    def _init_fonts(self):
        if self._font is None:
            self._font = pygame.font.SysFont("consolas", 16)
            self._small_font = pygame.font.SysFont("consolas", 12)
            self._big_font = pygame.font.SysFont("consolas", 22, bold=True)
            self._title_font = pygame.font.SysFont("consolas", 48, bold=True)
            self._dmg_font = pygame.font.SysFont("consolas", 18, bold=True)
            self._dmg_big_font = pygame.font.SysFont("consolas", 26, bold=True)

    def _create_glass_panel(self, w, h, color=(15, 12, 30), alpha=160, border_color=(80, 70, 120)):
        """Tạo panel glassmorphism."""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        surf.fill((*color, alpha))
        # Viền gradient
        pygame.draw.rect(surf, (*border_color, 180), (0, 0, w, h), 1, 6)
        # Highlight trên cùng
        for i in range(3):
            a = 40 - i * 12
            pygame.draw.line(surf, (200, 200, 255, a), (3, i + 1), (w - 3, i + 1))
        return surf

    def add_floating_text(self, x, y, text, color, camera, big=False):
        self.floating_texts.append(FloatingText(x, y, text, color, camera, big))

    def add_damage_text(self, x, y, damage, is_crit, camera):
        color = COLOR_DMG_CRIT if is_crit else COLOR_DMG_NORMAL
        prefix = "CRIT! " if is_crit else ""
        self.add_floating_text(x, y - 20, f"{prefix}{damage}", color, camera, big=is_crit)

    def add_player_damage_text(self, x, y, damage, camera):
        self.add_floating_text(x, y - 20, f"-{damage}", COLOR_DMG_PLAYER, camera)

    def add_heal_text(self, x, y, amount, camera):
        self.add_floating_text(x, y - 20, f"+{amount}", COLOR_HEAL, camera, big=True)

    def update(self):
        for ft in self.floating_texts:
            ft.update()
        self.floating_texts = [ft for ft in self.floating_texts if ft.alive]
        self.action_log.update()

    def render_hud(self, surface, player, chapter):
        """Vẽ HUD chính — glassmorphism style."""
        self._init_fonts()

        # ===== Glass panel nền HUD =====
        panel_w, panel_h = 230, 180
        panel = self._create_glass_panel(panel_w, panel_h)
        surface.blit(panel, (8, 8))

        px, py = 15, 16  # Offset trong panel

        # ===== HP Bar gradient =====
        bar_w, bar_h = 200, 18
        # Nền HP
        bg_rect = pygame.Rect(px, py, bar_w, bar_h)
        pygame.draw.rect(surface, (30, 12, 12), bg_rect, 0, 4)

        # Cập nhật catchup HP từ từ
        if not hasattr(self, 'catchup_hp'):
            self.catchup_hp = player.hp
        if self.catchup_hp < player.hp:
            self.catchup_hp = player.hp # Hồi máu thì cập nhật ngay
        elif self.catchup_hp > player.hp:
            self.catchup_hp -= max(0.5, (self.catchup_hp - player.hp) * 0.05)
            
        catchup_ratio = max(0, min(1, self.catchup_hp / player.max_hp))
        catchup_w = int(bar_w * catchup_ratio)
        
        # Vẽ thanh catch-up
        if catchup_w > 0:
            pygame.draw.rect(surface, (255, 255, 180), (px, py, catchup_w, bar_h), 0, 4)

        hp_ratio = max(0, player.hp / player.max_hp)
        hp_w = int(bar_w * hp_ratio)
        if hp_w > 0:
            # Gradient HP (đỏ → cam khi thấp)
            hp_surf = pygame.Surface((hp_w, bar_h), pygame.SRCALPHA)
            for i in range(hp_w):
                prog = i / bar_w
                if hp_ratio > 0.3:
                    r = int(180 + 40 * prog)
                    g = int(30 + 20 * prog)
                    b = 30
                else:
                    r = int(255)
                    g = int(60 + 60 * prog)
                    b = 20
                pygame.draw.line(hp_surf, (r, g, b, 230), (i, 0), (i, bar_h))
            surface.blit(hp_surf, (px, py))
            # Shine effect trên HP bar
            shine_surf = pygame.Surface((hp_w, bar_h // 3), pygame.SRCALPHA)
            shine_surf.fill((255, 255, 255, 30))
            surface.blit(shine_surf, (px, py))

        # Viền HP
        pygame.draw.rect(surface, (140, 120, 160), bg_rect, 1, 4)
        # Text HP
        hp_text = self._small_font.render(f"HP {int(player.hp)}/{int(player.max_hp)}", True, WHITE)
        surface.blit(hp_text, (px + bar_w // 2 - hp_text.get_width() // 2, py + 2))

        # ===== MP Bar =====
        py_mp = py + bar_h + 4
        mp_bg_rect = pygame.Rect(px, py_mp, bar_w, 12)
        pygame.draw.rect(surface, (12, 20, 40), mp_bg_rect, 0, 4)

        mp_ratio = max(0, player.mp / player.max_mp) if player.max_mp > 0 else 0
        mp_w = int(bar_w * mp_ratio)
        if mp_w > 0:
            mp_surf = pygame.Surface((mp_w, 12), pygame.SRCALPHA)
            for i in range(mp_w):
                prog = i / bar_w
                r = int(20 + 20 * prog)
                g = int(80 + 40 * prog)
                b = int(180 + 75 * prog)
                pygame.draw.line(mp_surf, (r, g, b, 230), (i, 0), (i, 12))
            surface.blit(mp_surf, (px, py_mp))
            
        pygame.draw.rect(surface, (80, 120, 180), mp_bg_rect, 1, 4)
        mp_text = self._small_font.render(f"MP {int(player.mp)}/{int(player.max_mp)}", True, WHITE)
        surface.blit(mp_text, (px + bar_w // 2 - mp_text.get_width() // 2, py_mp - 1))

        # ===== Stats =====
        stats_y = 77  # Dịch xuống dưới EXP bar (EXP bar ở y=65)
        stats = [
            (f"⚔ {player.damage}", (220, 200, 180)),
            (f"◈ {player.speed:.1f}", (180, 220, 200)),
            (f"✦ {int(player.crit_rate * 100)}%", (220, 200, 120)),
        ]
        for i, (stat_text, color) in enumerate(stats):
            text = self._small_font.render(stat_text, True, color)
            surface.blit(text, (px + i * 72, stats_y))

        # ===== Tiêu hao & Vàng =====
        cons_y = stats_y + 18
        cons = [
            (f"💰 {getattr(player, 'gold', 0)}", YELLOW),
            (f"♥[1] {getattr(player, 'health_potions', 0)}", RED),
            (f"♦[2] {getattr(player, 'mana_potions', 0)}", (100, 150, 255)),
        ]
        for i, (cons_text, color) in enumerate(cons):
            text = self._small_font.render(cons_text, True, color)
            surface.blit(text, (px + i * 72, cons_y))

        # ===== Equip icons =====
        equip_y = cons_y + 18
        slot_s = 26
        for idx, slot in enumerate(player.inventory.equipped):
            ex = px + idx * (slot_s + 6)
            ey = equip_y
            rect = pygame.Rect(ex, ey, slot_s, slot_s)
            if player.inventory.equipped[slot]:
                item = player.inventory.equipped[slot]
                bg = tuple(max(0, c // 4) for c in item.color)
                pygame.draw.rect(surface, bg, rect, 0, 4)
                pygame.draw.rect(surface, item.color, rect, 1, 4)
                # Glow nhẹ
                glow = pygame.Surface((slot_s + 4, slot_s + 4), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*item.color, 30), (0, 0, slot_s + 4, slot_s + 4), 0, 5)
                surface.blit(glow, (ex - 2, ey - 2))
            else:
                pygame.draw.rect(surface, (35, 30, 50), rect, 0, 4)
                pygame.draw.rect(surface, (60, 55, 80), rect, 1, 4)

        # Equip labels
        labels = ["W", "A", "B", "R"]
        for idx, lbl in enumerate(labels):
            ex = px + idx * (slot_s + 6)
            t = self._small_font.render(lbl, True, (80, 75, 100))
            surface.blit(t, (ex + slot_s // 2 - t.get_width() // 2, equip_y + slot_s + 2))

        # ===== Chapter name (góc trên giữa) =====
        if chapter < 5:
            from settings import CHAPTER_NAMES
            ch_name = CHAPTER_NAMES.get(chapter, "")
            ch_panel = self._create_glass_panel(280, 28, alpha=120)
            surface.blit(ch_panel, (SCREEN_WIDTH // 2 - 140, 6))
            ch_text = self._font.render(f"Ch.{chapter} — {ch_name}", True, (200, 190, 230))
            surface.blit(ch_text, (SCREEN_WIDTH // 2 - ch_text.get_width() // 2, 11))

        # ===== Skill bar (góc dưới giữa) =====
        self._render_skill_bar(surface, player)

        # ===== Floating texts =====
        for ft in self.floating_texts:
            ft.render(surface, self._dmg_font, self._dmg_big_font)

        # ===== Action Log =====
        self.action_log.render(surface)

        # ===== Combo Counter =====
        self._render_combo(surface, player)

        # ===== Level Up Flash =====
        self._render_level_up(surface, player)

    def _render_combo(self, surface, player):
        """Vẽ combo counter khi combo > 1."""
        now = pygame.time.get_ticks()
        if player.combo_count < 2 or now - player.combo_timer > COMBO_TIMEOUT:
            return

        elapsed = now - player.combo_timer
        # Fade out gần hết timeout
        alpha = 255
        if elapsed > COMBO_TIMEOUT - 500:
            alpha = int(255 * (COMBO_TIMEOUT - elapsed) / 500)

        combo = player.combo_count
        # Màu theo mức combo
        if combo >= 20:
            color = (255, 50, 50)    # Đỏ rực
        elif combo >= 10:
            color = (255, 180, 50)   # Vàng cam
        elif combo >= 5:
            color = (255, 255, 100)  # Vàng
        else:
            color = (200, 200, 255)  # Trắng xanh

        # Scale effect
        scale_pulse = 1.0 + 0.1 * math.sin(now * 0.01)
        combo_text = f"COMBO x{combo}"
        font_size = int(28 * scale_pulse)

        # Vẽ combo text
        combo_font = self._big_font
        text_surf = combo_font.render(combo_text, True, color)
        text_surf.set_alpha(alpha)

        # Outline
        outline_surf = combo_font.render(combo_text, True, BLACK)
        outline_surf.set_alpha(alpha)

        cx = SCREEN_WIDTH - 200
        cy = SCREEN_HEIGHT // 2 - 50
        for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            surface.blit(outline_surf, (cx + ox, cy + oy))
        surface.blit(text_surf, (cx, cy))

        # Multiplier text
        multi = player.get_combo_multiplier()
        multi_text = self._small_font.render(f"DMG x{multi:.1f}", True, (180, 255, 180))
        multi_text.set_alpha(alpha)
        surface.blit(multi_text, (cx + 10, cy + 28))

    def _render_level_up(self, surface, player):
        """Vẽ hiệu ứng LEVEL UP! flash."""
        if player.level_up_flash == 0:
            return
        now = pygame.time.get_ticks()
        elapsed = now - player.level_up_flash
        if elapsed > 2500:
            player.level_up_flash = 0
            return

        alpha = max(0, 255 - int(255 * elapsed / 2500))
        progress = elapsed / 2500

        # Flash overlay
        if elapsed < 200:
            flash = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_a = int(80 * (1 - elapsed / 200))
            flash.fill((255, 255, 200, flash_a))
            surface.blit(flash, (0, 0))

        # Text "LEVEL UP!"
        scale = 1.0 + 0.5 * (1 - progress)
        text = self._big_font.render(f"★ LEVEL {player.level} ★", True, (255, 230, 100))
        text.set_alpha(alpha)

        # Rise animation
        y_offset = int(30 * progress)
        tx = SCREEN_WIDTH // 2 - text.get_width() // 2
        ty = SCREEN_HEIGHT // 2 - 80 - y_offset

        # Outline
        outline = self._big_font.render(f"★ LEVEL {player.level} ★", True, (60, 40, 0))
        outline.set_alpha(alpha)
        for ox, oy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
            surface.blit(outline, (tx + ox, ty + oy))
        surface.blit(text, (tx, ty))

        # Sub text
        sub = self._font.render("HP & MP hồi đầy! Stats tăng!", True, (200, 255, 200))
        sub.set_alpha(alpha)
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, ty + 30))

    def _render_skill_bar(self, surface, player):
        """Vẽ thanh skill 5 ô — enhanced."""
        now = pygame.time.get_ticks()
        center_x = SCREEN_WIDTH // 2
        icon_s = SKILL_ICON_SIZE
        gap = 10
        from settings import DASH_COST, AOE_COST, SHIELD_COST, LIFESTEAL_COST, SUMMON_COST, SKILL_UNLOCK_LEVELS

        skills = [
            ("Q", "Dash", DASH_COOLDOWN, player.dash_cooldown_timer, (80, 160, 255), DASH_COST),
            ("R", "AoE", AOE_COOLDOWN, player.aoe_cooldown_timer, (200, 80, 255), AOE_COST),
            ("Z", "Shield", SHIELD_COOLDOWN, player.shield_cooldown_timer, (100, 80, 200), SHIELD_COST),
            ("X", "Steal", LIFESTEAL_COOLDOWN, player.lifesteal_cooldown_timer, (220, 50, 80), LIFESTEAL_COST),
            ("C", "Summon", SUMMON_COOLDOWN, player.summon_cooldown_timer, (100, 200, 255), SUMMON_COST),
        ]
        num = len(skills)

        # Panel nền
        panel_w = (icon_s + gap) * num + gap
        panel = self._create_glass_panel(panel_w, icon_s + 30, alpha=140)
        surface.blit(panel, (center_x - panel_w // 2, SKILL_BAR_Y - 8))

        for idx, (key, name, cd, last_used, skill_color, cost) in enumerate(skills):
            x = center_x - panel_w // 2 + gap + idx * (icon_s + gap)
            y = SKILL_BAR_Y
            rect = pygame.Rect(x, y, icon_s, icon_s)

            elapsed = now - last_used
            ready = elapsed >= cd
            has_mp = player.mp >= cost
            req_lv = SKILL_UNLOCK_LEVELS.get(key, 1)
            unlocked = player.level >= req_lv

            # Nền skill
            if not unlocked:
                bg = (15, 12, 20)
            elif ready and has_mp:
                pulse = 0.5 + 0.5 * math.sin(now * 0.005)
                bg = tuple(int(c * 0.3 * pulse) for c in skill_color)
            else:
                bg = (25, 20, 35)
            pygame.draw.rect(surface, bg, rect, 0, 8)

            # Cooldown sweep (Radial pie chart)
            if not ready:
                progress = elapsed / cd
                angle = progress * 360
                
                cd_surf = pygame.Surface((icon_s, icon_s), pygame.SRCALPHA)
                
                cx, cy = icon_s // 2, icon_s // 2
                radius = icon_s * 1.5
                points = [(cx, cy), (cx, 0)]
                for a in range(int(angle), 361, 5):
                    rad = math.radians(a - 90)
                    px = cx + math.cos(rad) * radius
                    py = cy + math.sin(rad) * radius
                    points.append((px, py))
                
                if len(points) > 2:
                    pygame.draw.polygon(cd_surf, (0, 0, 0, 180), points)
                surface.blit(cd_surf, (x, y))

                remaining = max(0, (cd - elapsed) / 1000)
                cd_text = self._font.render(f"{remaining:.1f}", True, WHITE)
                surface.blit(cd_text, (x + icon_s // 2 - cd_text.get_width() // 2,
                                       y + icon_s // 2 - cd_text.get_height() // 2))

            # Active indicator for shield
            if not unlocked:
                pygame.draw.rect(surface, (40, 35, 50), rect, 2, 8)
                lock_text = self._font.render(f"Lv.{req_lv}", True, (150, 100, 100))
                surface.blit(lock_text, (x + icon_s // 2 - lock_text.get_width() // 2, y + icon_s // 2 - lock_text.get_height() // 2))
            else:
                if key == "Z" and player.shield_active:
                    pygame.draw.rect(surface, (100, 200, 100), rect, 2, 8)
                elif key == "C" and player.spirit is not None:
                    pygame.draw.rect(surface, (100, 200, 255), rect, 2, 8)
                else:
                    border_color = skill_color if ready else (60, 55, 75)
                    pygame.draw.rect(surface, border_color, rect, 2, 8)

                # Ready glow
                if ready:
                    glow_surf = pygame.Surface((icon_s + 8, icon_s + 8), pygame.SRCALPHA)
                    pulse_a = int(30 + 20 * math.sin(now * 0.006))
                    pygame.draw.rect(glow_surf, (*skill_color, pulse_a),
                                     (0, 0, icon_s + 8, icon_s + 8), 0, 10)
                    surface.blit(glow_surf, (x - 4, y - 4))

            # Key label
            if not unlocked:
                key_color = (60, 55, 70)
            elif not has_mp and ready:
                key_color = (255, 80, 80) # Đỏ nếu không đủ mana
            else:
                key_color = YELLOW if ready else (80, 75, 95)
            key_text = self._font.render(key, True, key_color)
            surface.blit(key_text, (x + icon_s // 2 - key_text.get_width() // 2, y - 18))

            # Name + Cost
            name_text = self._small_font.render(name, True, (120, 115, 140) if unlocked else (60, 55, 70))
            surface.blit(name_text, (x + icon_s // 2 - name_text.get_width() // 2, y + icon_s + 4))
            
            # MP Cost
            if unlocked:
                cost_color = (100, 150, 255) if has_mp else (255, 50, 50)
                cost_text = self._small_font.render(f"{cost}", True, cost_color)
                surface.blit(cost_text, (x + icon_s - cost_text.get_width() - 2, y + icon_s - cost_text.get_height() - 2))

    def render_minimap(self, surface, tile_map, player, enemies, boss_ref, items):
        """Vẽ minimap — enhanced với khung đẹp."""
        self.minimap_surface.fill((12, 8, 22, 200))

        scale_x = MINIMAP_WIDTH / (MAP_WIDTH * TILE_SIZE)
        scale_y = MINIMAP_HEIGHT / (MAP_HEIGHT * TILE_SIZE)

        # Vẽ tường
        for y in range(MAP_HEIGHT):
            for x in range(MAP_WIDTH):
                if tile_map.grid[y][x] == 1:
                    mx = int(x * TILE_SIZE * scale_x)
                    my = int(y * TILE_SIZE * scale_y)
                    mw = max(1, int(TILE_SIZE * scale_x))
                    mh = max(1, int(TILE_SIZE * scale_y))
                    pygame.draw.rect(self.minimap_surface, (45, 38, 55), (mx, my, mw, mh))

        # Items — chấm vàng phát sáng
        now = pygame.time.get_ticks()
        for item in items:
            if not item.picked_up:
                ix = int(item.x * scale_x)
                iy = int(item.y * scale_y)
                pulse = int(2 + math.sin(now * 0.005) * 1)
                pygame.draw.circle(self.minimap_surface, (*item.color, 180), (ix, iy), pulse)

        # Enemies — chấm đỏ
        for enemy in enemies:
            if enemy.alive:
                ex = int(enemy.x * scale_x)
                ey = int(enemy.y * scale_y)
                pygame.draw.circle(self.minimap_surface, (220, 60, 60), (ex, ey), 2)

        # Boss — chấm cam lớn pulsing
        if boss_ref and boss_ref.alive:
            bx = int(boss_ref.x * scale_x)
            by = int(boss_ref.y * scale_y)
            pulse = int(4 + 2 * math.sin(now * 0.004))
            pygame.draw.circle(self.minimap_surface, (255, 100, 30, 180), (bx, by), pulse)
            pygame.draw.circle(self.minimap_surface, ORANGE, (bx, by), 3)

        # Player — chấm trắng sáng
        px = int(player.x * scale_x)
        py_m = int(player.y * scale_y)
        pygame.draw.circle(self.minimap_surface, (180, 220, 255), (px, py_m), 3)
        pygame.draw.circle(self.minimap_surface, WHITE, (px, py_m), 2)

        # ===== Fog of War =====
        # Cập nhật explored tiles
        ptx = int(player.x // TILE_SIZE)
        pty = int(player.y // TILE_SIZE)
        for dy in range(-self.fog_radius, self.fog_radius + 1):
            for dx in range(-self.fog_radius, self.fog_radius + 1):
                if dx*dx + dy*dy <= self.fog_radius * self.fog_radius:
                    self.explored.add((ptx + dx, pty + dy))

        # Vẽ fog overlay
        fog_surf = pygame.Surface((MINIMAP_WIDTH, MINIMAP_HEIGHT), pygame.SRCALPHA)
        fog_surf.fill((0, 0, 0, 200))
        # Đục lỗ các tile đã khám phá
        mw = max(1, int(TILE_SIZE * scale_x))
        mh = max(1, int(TILE_SIZE * scale_y))
        for (ex, ey) in self.explored:
            if 0 <= ex < MAP_WIDTH and 0 <= ey < MAP_HEIGHT:
                mx = int(ex * TILE_SIZE * scale_x)
                my = int(ey * TILE_SIZE * scale_y)
                pygame.draw.rect(fog_surf, (0, 0, 0, 0), (mx, my, mw, mh))
        self.minimap_surface.blit(fog_surf, (0, 0))

        # Viền minimap đẹp
        pygame.draw.rect(self.minimap_surface, (90, 80, 130),
                         (0, 0, MINIMAP_WIDTH, MINIMAP_HEIGHT), 2, 5)
        # Highlight trên
        pygame.draw.line(self.minimap_surface, (120, 110, 170, 100),
                         (3, 1), (MINIMAP_WIDTH - 3, 1))

        surface.blit(self.minimap_surface, (MINIMAP_X, MINIMAP_Y))

        # Label
        self._init_fonts()
        label = self._small_font.render("MAP", True, (100, 95, 130))
        surface.blit(label, (MINIMAP_X + MINIMAP_WIDTH // 2 - label.get_width() // 2,
                             MINIMAP_Y + MINIMAP_HEIGHT + 3))

    def render_boss_hp_bar(self, surface, boss):
        """Vẽ thanh HP boss — dramatic style."""
        if not boss or not boss.alive:
            return
        self._init_fonts()

        bar_w = 450
        bar_h = 18
        bx = SCREEN_WIDTH // 2 - bar_w // 2
        by = 20  # Đặt lên góc trên cùng màn hình

        # Panel nền
        panel = self._create_glass_panel(bar_w + 20, bar_h + 30, alpha=180)
        surface.blit(panel, (bx - 10, by - 20))

        # HP bar
        pygame.draw.rect(surface, (40, 12, 12), (bx, by, bar_w, bar_h), 0, 4)
        hp_ratio = max(0, boss.hp / boss.max_hp)
        hp_w = int(bar_w * hp_ratio)
        if hp_w > 0:
            # Gradient đỏ → cam
            hp_surf = pygame.Surface((hp_w, bar_h), pygame.SRCALPHA)
            for i in range(hp_w):
                prog = i / bar_w
                if boss.phase == 2:
                    r, g, b = 255, int(40 + 60 * prog), int(10 + 20 * prog)
                else:
                    r, g, b = int(180 + 50 * prog), 25, 25
                pygame.draw.line(hp_surf, (r, g, b), (i, 0), (i, bar_h))
            surface.blit(hp_surf, (bx, by))
            # Shine
            shine = pygame.Surface((hp_w, bar_h // 3), pygame.SRCALPHA)
            shine.fill((255, 255, 255, 25))
            surface.blit(shine, (bx, by))

        pygame.draw.rect(surface, (180, 140, 100), (bx, by, bar_w, bar_h), 1, 4)

        # Tên boss
        name = "◆ MALPHAS" + (" — PHASE 2" if boss.phase == 2 else "") + " ◆"
        name_color = (255, 120, 60) if boss.phase == 2 else (255, 200, 150)
        name_text = self._font.render(name, True, name_color)
        surface.blit(name_text, (SCREEN_WIDTH // 2 - name_text.get_width() // 2, by - 18))

    def render_floating_texts(self, surface):
        self._init_fonts()
        for ft in self.floating_texts:
            ft.render(surface, self._dmg_font, self._dmg_big_font)

    def render_chapter_title(self, surface, chapter, alpha=255):
        """Vẽ title chương — cinematic style."""
        self._init_fonts()
        from settings import CHAPTER_NAMES, CHAPTER_DESCRIPTIONS
        name = CHAPTER_NAMES.get(chapter, "")
        desc = CHAPTER_DESCRIPTIONS.get(chapter, "")

        # Nền tối overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, min(200, alpha)))
        surface.blit(overlay, (0, 0))

        # Decorative line
        line_w = int(300 * min(1, alpha / 128))
        cy = SCREEN_HEIGHT // 2 - 40
        line_color = (120, 100, 180, alpha)
        line_surf = pygame.Surface((line_w, 2), pygame.SRCALPHA)
        line_surf.fill(line_color)
        surface.blit(line_surf, (SCREEN_WIDTH // 2 - line_w // 2, cy - 10))

        # Chapter number
        ch_text = self._big_font.render(f"— Chương {chapter} —", True, (160, 140, 200))
        ch_text.set_alpha(alpha)
        surface.blit(ch_text, (SCREEN_WIDTH // 2 - ch_text.get_width() // 2, cy))

        # Chapter name
        title = self._title_font.render(name, True, (240, 220, 255))
        title.set_alpha(alpha)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, cy + 35))

        # Description
        desc_text = self._font.render(desc, True, (160, 150, 190))
        desc_text.set_alpha(alpha)
        surface.blit(desc_text, (SCREEN_WIDTH // 2 - desc_text.get_width() // 2, cy + 90))

        # Bottom line
        surface.blit(line_surf, (SCREEN_WIDTH // 2 - line_w // 2, cy + 120))

    def render_controls_hint(self, surface):
        """Vẽ hint controls nhỏ ở góc dưới trái."""
        self._init_fonts()
        hints = "WASD Move | SPACE Attack | Q Dash | R AoE | Z Shield | X Steal | C Summon | F Pickup | I Inv | P Auto"
        text = self._small_font.render(hints, True, (70, 65, 90))
        surface.blit(text, (10, SCREEN_HEIGHT - 18))

    def render_quest_tracker(self, surface, chapter, quest_states):
        """Vẽ quest tracker ở góc phải màn hình."""
        self._init_fonts()
        quests = CHAPTER_QUESTS.get(chapter, [])
        if not quests:
            return

        # Panel nền
        panel_w = 260
        panel_h = 30 + len(quests) * 24
        panel_x = SCREEN_WIDTH - panel_w - 15
        panel_y = MINIMAP_Y + MINIMAP_HEIGHT + 30

        panel = self._create_glass_panel(panel_w, panel_h, alpha=130)
        surface.blit(panel, (panel_x, panel_y))

        # Tiêu đề
        title = self._small_font.render("◆ MỤC TIÊU ◆", True, (200, 190, 230))
        surface.blit(title, (panel_x + panel_w // 2 - title.get_width() // 2, panel_y + 5))

        # Danh sách quest
        for i, quest in enumerate(quests):
            qy = panel_y + 24 + i * 24
            completed = quest_states.get(i, False)

            if completed:
                icon = "✓"
                color = (100, 255, 100)
                text_color = (120, 180, 120)
            else:
                icon = "○"
                color = YELLOW
                text_color = (200, 195, 220)

            icon_surf = self._small_font.render(icon, True, color)
            surface.blit(icon_surf, (panel_x + 10, qy))

            text_surf = self._small_font.render(quest["text"], True, text_color)
            surface.blit(text_surf, (panel_x + 26, qy))

    def render_exp_bar(self, surface, player):
        """Vẽ thanh EXP nhỏ dưới HP bar."""
        self._init_fonts()
        if player.level >= MAX_LEVEL:
            return

        px, py = 15, 65  # Ngay dưới MP bar
        bar_w = 200
        bar_h = 6

        # Nền
        pygame.draw.rect(surface, (20, 15, 30), (px, py, bar_w, bar_h), 0, 3)

        # EXP fill
        exp_needed = EXP_PER_LEVEL[player.level] if player.level < len(EXP_PER_LEVEL) else 999
        exp_ratio = min(1.0, player.exp / exp_needed) if exp_needed > 0 else 0
        exp_w = int(bar_w * exp_ratio)
        if exp_w > 0:
            exp_surf = pygame.Surface((exp_w, bar_h), pygame.SRCALPHA)
            for i in range(exp_w):
                prog = i / bar_w
                r = int(180 + 75 * prog)
                g = int(200 + 55 * prog)
                b = int(50 + 50 * prog)
                pygame.draw.line(exp_surf, (r, g, b, 220), (i, 0), (i, bar_h))
            surface.blit(exp_surf, (px, py))

        pygame.draw.rect(surface, (120, 140, 80), (px, py, bar_w, bar_h), 1, 3)

        # Label
        exp_text = self._small_font.render(
            f"Lv.{player.level} EXP {player.exp}/{exp_needed}", True, (180, 200, 120))
        # Đặt text lên trên bar một chút
        surface.blit(exp_text, (px + bar_w // 2 - exp_text.get_width() // 2, py - 12))

    def reset_fog(self):
        """Reset fog of war khi chuyển chương."""
        self.explored = set()
