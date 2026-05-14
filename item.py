"""
item.py — Hệ thống Item & Loot
================================
Item rơi từ quái, có rarity (Common/Rare/Epic), glow effect.
4 loại: Weapon, Armor, Boots, Ring.
"""

import random
import math
import pygame
from settings import (
    TILE_SIZE, RARITY_COMMON, RARITY_RARE, RARITY_EPIC,
    DROP_RATES, EQUIP_WEAPON, EQUIP_ARMOR, EQUIP_BOOTS, EQUIP_RING,
    EQUIP_POTION_HP, EQUIP_POTION_MP, EQUIP_GOLD,
    ITEM_STATS, ITEM_NAMES, RARITY_COLORS, ENEMY_DROP_CHANCE,
    COLOR_COMMON_GLOW, COLOR_RARE_GLOW, COLOR_EPIC_GLOW, WHITE, YELLOW, RED
)


class Item:
    """Một item trang bị trong game.

    Attributes:
        equip_type (str): Loại trang bị (Weapon/Armor/Boots/Ring)
        rarity (str): Độ hiếm (Common/Rare/Epic)
        name (str): Tên lore
        stats (dict): Chỉ số cộng thêm
        color (tuple): Màu glow theo rarity
        x, y (float): Vị trí trên map (khi chưa nhặt)
        picked_up (bool): Đã nhặt chưa
    """

    def __init__(self, equip_type, rarity=RARITY_COMMON, x=0, y=0, amount=1):
        self.equip_type = equip_type
        self.rarity = rarity
        self.amount = amount  # Dùng cho Gold
        
        if equip_type in [EQUIP_POTION_HP, EQUIP_POTION_MP, EQUIP_GOLD]:
            if equip_type == EQUIP_POTION_HP:
                self.name = "Bình Máu"
                self.color = RED
            elif equip_type == EQUIP_POTION_MP:
                self.name = "Bình Năng Lượng"
                self.color = (50, 150, 255)
            elif equip_type == EQUIP_GOLD:
                self.name = f"{amount} Vàng"
                self.color = YELLOW
            self.stats = {}
        else:
            self.name = ITEM_NAMES[equip_type][rarity]
            self.stats = ITEM_STATS[equip_type][rarity].copy()
            self.color = RARITY_COLORS[rarity]
            
        self.x = x
        self.y = y
        self.picked_up = False
        self.spawn_time = pygame.time.get_ticks()

    def get_stat_text(self):
        """Trả về chuỗi mô tả chỉ số."""
        parts = []
        for key, val in self.stats.items():
            if key == "damage":
                parts.append(f"+{val} Damage")
            elif key == "max_hp":
                parts.append(f"+{val} Max HP")
            elif key == "max_mp":
                parts.append(f"+{val} Max MP")
            elif key == "speed":
                parts.append(f"+{val} Speed")
            elif key == "crit_rate":
                parts.append(f"+{int(val * 100)}% Crit")
            elif key == "hp_regen":
                parts.append(f"+{val} HP/s")
            elif key == "mp_regen":
                parts.append(f"+{val} MP/s")
        return ", ".join(parts)

    def render(self, surface, camera):
        """Vẽ item trên map với glow animation."""
        if self.picked_up:
            return
        sx, sy = camera.apply(self.x, self.y)
        t = (pygame.time.get_ticks() - self.spawn_time) / 1000.0

        # BUG FIX: Bobbing animation (lên xuống nhẹ) — áp dụng vào sy
        bob = int(3 * math.sin(t * 2.5))
        sy += bob

        # Glow pulsing
        glow_radius = 14 + int(3 * math.sin(t * 3))
        glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        alpha = int(60 + 30 * math.sin(t * 4))
        pygame.draw.circle(glow_surf, (*self.color, alpha), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow_surf, (sx - glow_radius, sy - glow_radius))

        # Item icon
        size = 10
        icon_colors = {
            EQUIP_WEAPON: (200, 200, 220), EQUIP_ARMOR: (150, 160, 180),
            EQUIP_BOOTS: (160, 140, 120), EQUIP_RING: (220, 200, 100)
        }
        color = icon_colors.get(self.equip_type, WHITE)
        if self.equip_type == EQUIP_WEAPON:
            # Kiếm nhỏ
            pygame.draw.line(surface, color, (sx, sy - size), (sx, sy + size), 3)
            pygame.draw.line(surface, color, (sx - 4, sy - 2), (sx + 4, sy - 2), 2)
        elif self.equip_type == EQUIP_ARMOR:
            pygame.draw.rect(surface, color, (sx - 5, sy - 6, 10, 12), 0, 2)
        elif self.equip_type == EQUIP_BOOTS:
            pygame.draw.ellipse(surface, color, (sx - 5, sy - 3, 10, 8))
        elif self.equip_type == EQUIP_RING:
            pygame.draw.circle(surface, color, (sx, sy), 5, 2)
        elif self.equip_type in [EQUIP_POTION_HP, EQUIP_POTION_MP]:
            pygame.draw.rect(surface, self.color, (sx - 4, sy - 6, 8, 10), 0, 2)
            pygame.draw.rect(surface, (200, 200, 200), (sx - 2, sy - 9, 4, 3)) # Nút chai
        elif self.equip_type == EQUIP_GOLD:
            pygame.draw.circle(surface, YELLOW, (sx - 3, sy + 2), 4)
            pygame.draw.circle(surface, (255, 220, 50), (sx + 4, sy - 1), 5)
            pygame.draw.circle(surface, (220, 180, 20), (sx, sy - 3), 3)

    def render_icon(self, surface, x, y, size=40):
        """Vẽ icon item trong inventory."""
        rect = pygame.Rect(x, y, size, size)
        # Nền theo rarity
        bg_color = tuple(max(0, c // 3) for c in self.color)
        pygame.draw.rect(surface, bg_color, rect, 0, 4)
        pygame.draw.rect(surface, self.color, rect, 2, 4)

        cx, cy = x + size // 2, y + size // 2
        icon_colors = {
            EQUIP_WEAPON: (200, 200, 220), EQUIP_ARMOR: (150, 160, 180),
            EQUIP_BOOTS: (160, 140, 120), EQUIP_RING: (220, 200, 100)
        }
        color = icon_colors.get(self.equip_type, WHITE)

        if self.equip_type == EQUIP_WEAPON:
            pygame.draw.line(surface, color, (cx, cy - 12), (cx, cy + 12), 3)
            pygame.draw.line(surface, color, (cx - 6, cy - 4), (cx + 6, cy - 4), 2)
        elif self.equip_type == EQUIP_ARMOR:
            pygame.draw.rect(surface, color, (cx - 8, cy - 10, 16, 20), 0, 3)
        elif self.equip_type == EQUIP_BOOTS:
            pygame.draw.ellipse(surface, color, (cx - 8, cy - 5, 16, 12))
        elif self.equip_type == EQUIP_RING:
            pygame.draw.circle(surface, color, (cx, cy), 8, 3)


def roll_rarity(boss_drop=False, diff_cfg=None):
    """Random rarity item theo tỉ lệ rơi, cộng bonus từ độ khó."""
    if boss_drop:
        return RARITY_EPIC
    roll = random.random()
    
    rare_bonus = diff_cfg["rare_bonus"] if diff_cfg else 0.0
    epic_bonus = diff_cfg["epic_bonus"] if diff_cfg else 0.0
    
    epic_chance = DROP_RATES[RARITY_EPIC] + epic_bonus
    rare_chance = DROP_RATES[RARITY_RARE] + rare_bonus
    
    if roll < epic_chance:
        return RARITY_EPIC
    elif roll < epic_chance + rare_chance:
        return RARITY_RARE
    return RARITY_COMMON


def generate_loot(x, y, boss_drop=False, is_crate=False, diff_cfg=None):
    """Tạo item loot tại vị trí cho trước. Thùng gỗ ưu tiên rớt vàng/máu."""
    if is_crate:
        # Crate drop rates
        roll = random.random()
        if roll < 0.4:
            return Item(EQUIP_GOLD, amount=random.randint(5, 15), x=x, y=y)
        elif roll < 0.6:
            return Item(EQUIP_POTION_HP, x=x, y=y)
        elif roll < 0.8:
            return Item(EQUIP_POTION_MP, x=x, y=y)
        return None

    if not boss_drop and random.random() > ENEMY_DROP_CHANCE:
        return None
        
    # Enemy có thể rớt vàng, potion, hoặc trang bị
    roll = random.random()
    if not boss_drop and roll < 0.3:
        return Item(EQUIP_GOLD, amount=random.randint(10, 30), x=x, y=y)
    elif not boss_drop and roll < 0.45:
        return Item(EQUIP_POTION_HP, x=x, y=y)
    elif not boss_drop and roll < 0.6:
        return Item(EQUIP_POTION_MP, x=x, y=y)
        
    equip_type = random.choice([EQUIP_WEAPON, EQUIP_ARMOR, EQUIP_BOOTS, EQUIP_RING])
    rarity = roll_rarity(boss_drop, diff_cfg)
    return Item(equip_type, rarity, x, y)
