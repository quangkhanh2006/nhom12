"""
player.py — Class Player (Kael Duskborne)
==========================================
Di chuyển WASD, tấn công Space, Dash Q, AoE R, nhặt item F.
Xử lý: invincibility, knockback, crit, flash đỏ.
"""

import math
import pygame
from settings import (
    PLAYER_HP, PLAYER_MP, PLAYER_DAMAGE, PLAYER_SPEED, PLAYER_CRIT_RATE, PLAYER_CRIT_MULTI,
    PLAYER_SIZE, PLAYER_ATTACK_RANGE, PLAYER_ATTACK_KNOCKBACK, PLAYER_INVINCIBLE_TIME,
    PLAYER_PICKUP_RANGE, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    DASH_COOLDOWN, DASH_COST, DASH_DISTANCE, DASH_DURATION, DASH_INVINCIBLE,
    AOE_COOLDOWN, AOE_COST, AOE_RADIUS, AOE_DAMAGE_MULTI, AOE_DURATION,
    SHIELD_COOLDOWN, SHIELD_COST, SHIELD_DURATION, SHIELD_HP,
    LIFESTEAL_COOLDOWN, LIFESTEAL_COST, LIFESTEAL_RANGE, LIFESTEAL_SPEED, LIFESTEAL_DMG_MULTI,
    LIFESTEAL_HEAL_RATE, LIFESTEAL_PIERCE,
    SUMMON_COOLDOWN, SUMMON_COST, SUMMON_DURATION, SUMMON_DMG_MULTI, SUMMON_SPEED,
    SUMMON_ATTACK_RANGE, SUMMON_ATTACK_CD,
    COLOR_PLAYER, COLOR_PLAYER_SKIN, COLOR_PLAYER_HAIR, COLOR_PLAYER_SWORD,
    COLOR_SHIELD, COLOR_SHIELD_GLOW, COLOR_LIFESTEAL, COLOR_LIFESTEAL_HEAL,
    COLOR_SPIRIT, COLOR_SPIRIT_GLOW,
    DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT,
    EXP_PER_LEVEL, LEVEL_HP_BONUS, LEVEL_DMG_BONUS, LEVEL_MP_BONUS,
    LEVEL_SPEED_BONUS, MAX_LEVEL,
    COMBO_TIMEOUT, COMBO_DMG_BONUS, COMBO_MAX,
    TRAP_DAMAGE, TRAP_COOLDOWN, SKILL_UNLOCK_LEVELS
)
from inventory import Inventory
from ai import distance_between, get_direction_towards
import random
import sound


class Player:
    """Nhân vật chính Kael Duskborne.

    Attributes:
        x, y (float): Vị trí pixel (tâm nhân vật)
        hp, max_hp (int): Máu hiện tại và tối đa
        damage (int): Sát thương cơ bản
        speed (float): Tốc độ di chuyển
        crit_rate (float): Tỉ lệ chí mạng
        crit_multi (float): Hệ số chí mạng
        facing (tuple): Hướng nhìn (dx, dy)
        inventory (Inventory): Hệ thống trang bị
        is_attacking (bool): Đang tấn công?
        is_dashing (bool): Đang dash?
        is_invincible (bool): Đang bất tử?
        alive (bool): Còn sống?
    """

    def __init__(self, x, y):
        # Vị trí
        self.x = float(x)
        self.y = float(y)
        self.size = PLAYER_SIZE

        # Chỉ số cơ bản
        self.max_hp = PLAYER_HP
        self.hp = self.max_hp
        self.max_mp = PLAYER_MP
        self.mp = self.max_mp
        self.damage = PLAYER_DAMAGE
        self.speed = PLAYER_SPEED
        self.crit_rate = PLAYER_CRIT_RATE
        self.crit_multi = PLAYER_CRIT_MULTI
        self.hp_regen = 0.0
        self.mp_regen = 2.5

        # Trạng thái
        self.facing = DIR_DOWN
        self.alive = True
        self.moving = False

        # Tấn công
        self.is_attacking = False
        self.attack_timer = 0
        self.attack_duration = 200  # ms

        # Dash (Q)
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown_timer = 0
        self.dash_dx = 0
        self.dash_dy = 0

        # AoE (R)
        self.aoe_active = False
        self.aoe_timer = 0
        self.aoe_cooldown_timer = 0

        # Invincibility
        self.is_invincible = False
        self.invincible_timer = 0
        self.hit_flash = False
        self.flash_timer = 0

        # Inventory & Tài sản
        self.inventory = Inventory()
        self.gold = 0
        self.health_potions = 3  # Bắt đầu với 3 bình
        self.mana_potions = 3

        # Animation
        self.anim_frame = 0
        self.anim_timer = 0

        # BUG FIX: Trap cooldown (tránh damage mỗi frame)
        self.trap_cooldown_timer = 0

        # === NEW SKILLS ===
        # Z — Shadow Shield
        self.shield_active = False
        self.shield_hp = 0
        self.shield_timer = 0
        self.shield_cooldown_timer = 0

        # X — Lifesteal Slash
        self.projectiles = []  # list of Projectile
        self.lifesteal_cooldown_timer = 0

        # C — Summon Spirit
        self.spirit = None  # SummonSpirit or None
        self.summon_cooldown_timer = 0

        # === EXP & LEVEL UP ===
        self.exp = 0
        self.level = 1
        self.level_up_flash = 0  # Timer for level up visual

        # === COMBO SYSTEM ===
        self.combo_count = 0
        self.combo_timer = 0
        self.best_combo = 0

    def get_rect(self):
        """Trả về hitbox player."""
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2,
                           self.size, self.size)

    def handle_input(self, keys, tile_map):
        """Xử lý input di chuyển WASD.

        Args:
            keys: pygame.key.get_pressed()
            tile_map: TileMap để kiểm tra collision
        """
        if not self.alive or self.is_dashing or self.inventory.is_open:
            return

        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy = -1
            self.facing = DIR_UP
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy = 1
            self.facing = DIR_DOWN
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx = -1
            self.facing = DIR_LEFT
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx = 1
            self.facing = DIR_RIGHT

        self.moving = dx != 0 or dy != 0

        if self.moving:
            # Normalize diagonal
            if dx != 0 and dy != 0:
                dx *= 0.707
                dy *= 0.707
            new_x = self.x + dx * self.speed
            new_y = self.y + dy * self.speed
            # Collision check
            half = self.size // 2
            if tile_map.is_walkable(new_x - half, self.y) and tile_map.is_walkable(new_x + half, self.y):
                self.x = new_x
            if tile_map.is_walkable(self.x, new_y - half) and tile_map.is_walkable(self.x, new_y + half):
                self.y = new_y
            # Clamp trong map
            self.x = max(half, min(MAP_WIDTH * TILE_SIZE - half, self.x))
            self.y = max(half, min(MAP_HEIGHT * TILE_SIZE - half, self.y))

    def attack(self):
        """Tấn công thường (Space)."""
        if not self.alive or self.is_attacking or self.is_dashing or self.inventory.is_open:
            return
        self.is_attacking = True
        self.attack_timer = pygame.time.get_ticks()
        sound.play("attack")

    def dash(self):
        """Skill Dash (Q) — lao về phía trước, bất tử."""
        if self.level < SKILL_UNLOCK_LEVELS["Q"]:
            if not self.inventory.is_open:
                self.inventory.show_notification(f"Cần Level {SKILL_UNLOCK_LEVELS['Q']} để mở khóa Dash!")
            return
        now = pygame.time.get_ticks()
        if not self.alive or self.is_dashing or self.inventory.is_open:
            return
        if now - self.dash_cooldown_timer < DASH_COOLDOWN:
            return
        if self.mp < DASH_COST:
            return
        self.mp -= DASH_COST
        self.is_dashing = True
        self.dash_timer = now
        self.dash_cooldown_timer = now
        self.dash_dx = self.facing[0] * (DASH_DISTANCE / (DASH_DURATION / 16))
        self.dash_dy = self.facing[1] * (DASH_DISTANCE / (DASH_DURATION / 16))
        if DASH_INVINCIBLE:
            self.is_invincible = True
        sound.play("dash")

    def use_aoe(self):
        """Skill AoE 360° (R) — bùng phát sát thương xung quanh."""
        if self.level < SKILL_UNLOCK_LEVELS["R"]:
            if not self.inventory.is_open:
                self.inventory.show_notification(f"Cần Level {SKILL_UNLOCK_LEVELS['R']} để mở khóa Xoay Kiếm!")
            return
        now = pygame.time.get_ticks()
        if not self.alive or self.aoe_active or self.inventory.is_open:
            return
        if now - self.aoe_cooldown_timer < AOE_COOLDOWN:
            return
        if self.mp < AOE_COST:
            return
        self.mp -= AOE_COST

        self.aoe_active = True
        self.aoe_timer = now
        self.aoe_cooldown_timer = now
        sound.play("aoe")

    def use_shield(self):
        """Skill Shadow Shield (Z) — tạo khiên hấp thụ damage."""
        if self.level < SKILL_UNLOCK_LEVELS["Z"]:
            if not self.inventory.is_open:
                self.inventory.show_notification(f"Cần Level {SKILL_UNLOCK_LEVELS['Z']} để mở khóa Khiên!")
            return
        now = pygame.time.get_ticks()
        if not self.alive or self.shield_active or self.inventory.is_open:
            return
        if now - self.shield_cooldown_timer < SHIELD_COOLDOWN:
            return
        if self.mp < SHIELD_COST:
            return
        self.mp -= SHIELD_COST

        self.shield_active = True
        self.shield_hp = SHIELD_HP
        self.shield_timer = now
        self.shield_cooldown_timer = now
        sound.play("shield")

    def use_lifesteal(self):
        """Skill Lifesteal Slash (X) — phóng lưỡi kiếm năng lượng."""
        if self.level < SKILL_UNLOCK_LEVELS["X"]:
            if not self.inventory.is_open:
                self.inventory.show_notification(f"Cần Level {SKILL_UNLOCK_LEVELS['X']} để mở khóa Hút Máu!")
            return
        now = pygame.time.get_ticks()
        if not self.alive or self.inventory.is_open:
            return
        if now - self.lifesteal_cooldown_timer < LIFESTEAL_COOLDOWN:
            return
        if self.mp < LIFESTEAL_COST:
            return
        self.mp -= LIFESTEAL_COST

        self.lifesteal_cooldown_timer = now
        dmg = int(self.damage * LIFESTEAL_DMG_MULTI)
        proj = {
            'x': float(self.x), 'y': float(self.y),
            'dx': self.facing[0] * LIFESTEAL_SPEED,
            'dy': self.facing[1] * LIFESTEAL_SPEED,
            'damage': dmg, 'heal_rate': LIFESTEAL_HEAL_RATE,
            'max_range': LIFESTEAL_RANGE, 'traveled': 0.0,
            'pierce_left': LIFESTEAL_PIERCE, 'hit_ids': set(),
        }
        # Nếu facing (0,0) → mặc định bắn xuống
        if proj['dx'] == 0 and proj['dy'] == 0:
            proj['dy'] = LIFESTEAL_SPEED
        self.projectiles.append(proj)
        sound.play("lifesteal")

    def use_summon(self):
        """Skill Summon Spirit (C) — triệu hồi linh hồn đồng minh."""
        if self.level < SKILL_UNLOCK_LEVELS["C"]:
            if not self.inventory.is_open:
                self.inventory.show_notification(f"Cần Level {SKILL_UNLOCK_LEVELS['C']} để mở khóa Triệu Hồi!")
            return
        now = pygame.time.get_ticks()
        if not self.alive or self.spirit is not None or self.inventory.is_open:
            return
        if now - self.summon_cooldown_timer < SUMMON_COOLDOWN:
            return
        if self.mp < SUMMON_COST:
            return
        self.mp -= SUMMON_COST

        self.summon_cooldown_timer = now
        self.spirit = {
            'x': float(self.x), 'y': float(self.y),
            'damage': int(self.damage * SUMMON_DMG_MULTI),
            'spawn_time': now, 'last_attack': 0,
            'target': None, 'alive': True,
        }
        sound.play("summon")

    def calculate_damage(self):
        """Tính sát thương (có xét crit).

        Returns:
            tuple: (damage, is_crit)
        """
        is_crit = random.random() < self.crit_rate
        dmg = self.damage
        if is_crit:
            dmg = int(dmg * self.crit_multi)
        return dmg, is_crit

    def take_damage(self, amount):
        """Nhận sát thương. Shield hấp thụ trước."""
        if not self.alive or self.is_invincible:
            return 0
        # Shield absorb
        if self.shield_active and self.shield_hp > 0:
            absorbed = min(amount, self.shield_hp)
            self.shield_hp -= absorbed
            amount -= absorbed
            if self.shield_hp <= 0:
                self.shield_active = False
            if amount <= 0:
                return absorbed
        self.hp -= amount
        self.hit_flash = True
        self.flash_timer = pygame.time.get_ticks()
        self.is_invincible = True
        self.invincible_timer = pygame.time.get_ticks()
        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            sound.play("player_death")
        else:
            sound.play("player_hurt")
        return amount

    def heal(self, amount):
        """Hồi HP."""
        self.hp = min(self.max_hp, self.hp + amount)

    def recalculate_stats(self):
        """Tính lại toàn bộ chỉ số từ base + equipment + level."""
        # Base stats + level bonus
        level_bonus = self.level - 1
        self.max_hp = PLAYER_HP + level_bonus * LEVEL_HP_BONUS
        self.max_mp = PLAYER_MP + level_bonus * LEVEL_MP_BONUS
        self.damage = PLAYER_DAMAGE + level_bonus * LEVEL_DMG_BONUS
        self.speed = PLAYER_SPEED + level_bonus * LEVEL_SPEED_BONUS
        self.crit_rate = PLAYER_CRIT_RATE
        self.hp_regen = 0.0
        self.mp_regen = 2.5

        for slot in self.inventory.equipped.values():
            if slot:
                self.max_hp += slot.stats.get("max_hp", 0)
                self.max_mp += slot.stats.get("max_mp", 0)
                self.damage += slot.stats.get("damage", 0)
                self.speed += slot.stats.get("speed", 0)
                self.crit_rate += slot.stats.get("crit_rate", 0)
                self.hp_regen += slot.stats.get("hp_regen", 0)
                self.mp_regen += slot.stats.get("mp_regen", 0)

        self.hp = min(self.hp, self.max_hp)
        self.mp = min(self.mp, self.max_mp)

    def gain_exp(self, amount):
        """Nhận EXP và check level up.

        Returns:
            bool: True nếu level up
        """
        if self.level >= MAX_LEVEL:
            return False
        self.exp += amount
        # Check level up
        if self.level < len(EXP_PER_LEVEL) and self.exp >= EXP_PER_LEVEL[self.level]:
            self.exp -= EXP_PER_LEVEL[self.level]
            self.level_up()
            return True
        return False

    def use_health_potion(self):
        """Bơm máu (Hồi 30% HP max)."""
        if self.health_potions > 0 and self.hp < self.max_hp:
            self.health_potions -= 1
            heal = int(self.max_hp * 0.3)
            self.hp = min(self.max_hp, self.hp + heal)
            sound.play("pickup")
            return True, heal
        return False, 0

    def use_mana_potion(self):
        """Bơm Mana (Hồi 30% MP max)."""
        if self.mana_potions > 0 and self.mp < self.max_mp:
            self.mana_potions -= 1
            mana = int(self.max_mp * 0.3)
            self.mp = min(self.max_mp, self.mp + mana)
            sound.play("pickup")
            return True, mana
        return False, 0

    def pickup_gold(self, amount):
        self.gold += amount
        sound.play("pickup")

    def level_up(self):
        """Tăng level và cập nhật stats."""
        if self.level >= MAX_LEVEL:
            return
        self.level += 1
        self.recalculate_stats()
        self.hp = self.max_hp
        self.mp = self.max_mp
        self.level_up_flash = pygame.time.get_ticks()
        sound.play("levelup")

    def add_combo(self):
        """Tăng combo counter khi đánh trúng."""
        now = pygame.time.get_ticks()
        self.combo_count = min(COMBO_MAX, self.combo_count + 1)
        self.combo_timer = now
        if self.combo_count > self.best_combo:
            self.best_combo = self.combo_count

    def get_combo_multiplier(self):
        """Trả về hệ số damage bonus từ combo."""
        now = pygame.time.get_ticks()
        if now - self.combo_timer > COMBO_TIMEOUT:
            self.combo_count = 0
            return 1.0
        return 1.0 + self.combo_count * COMBO_DMG_BONUS

    def get_attack_rect(self):
        """Trả về hitbox tấn công (bao phủ cả cự ly gần để tránh lỗi không trúng)."""
        # Đưa tâm hitbox về giữa khoảng cách tấn công
        ax = self.x + self.facing[0] * (PLAYER_ATTACK_RANGE / 2)
        ay = self.y + self.facing[1] * (PLAYER_ATTACK_RANGE / 2)
        # Mở rộng size để bao phủ từ người chơi tới rìa ngoài
        size = PLAYER_ATTACK_RANGE + 15
        return pygame.Rect(ax - size // 2, ay - size // 2, size, size)

    def update(self, tile_map):
        """Cập nhật trạng thái mỗi frame."""
        now = pygame.time.get_ticks()

        # Hồi phục
        self.hp = min(self.max_hp, self.hp + self.hp_regen / 60.0)
        self.mp = min(self.max_mp, self.mp + self.mp_regen / 60.0)

        # Dash update
        if self.is_dashing:
            if now - self.dash_timer < DASH_DURATION:
                half = self.size // 2
                new_x = self.x + self.dash_dx
                new_y = self.y + self.dash_dy
                if tile_map.is_walkable(new_x - half, new_y) and tile_map.is_walkable(new_x + half, new_y):
                    self.x = new_x
                if tile_map.is_walkable(self.x, new_y - half) and tile_map.is_walkable(self.x, new_y + half):
                    self.y = new_y
                self.x = max(half, min(MAP_WIDTH * TILE_SIZE - half, self.x))
                self.y = max(half, min(MAP_HEIGHT * TILE_SIZE - half, self.y))
            else:
                self.is_dashing = False

        # Attack timer
        if self.is_attacking and now - self.attack_timer > self.attack_duration:
            self.is_attacking = False

        # AoE timer
        if self.aoe_active and now - self.aoe_timer > AOE_DURATION:
            self.aoe_active = False

        # Invincibility timer
        if self.is_invincible and not self.is_dashing:
            if now - self.invincible_timer > PLAYER_INVINCIBLE_TIME:
                self.is_invincible = False

        # Flash timer
        if self.hit_flash and now - self.flash_timer > 150:
            self.hit_flash = False

        # Animation
        if self.moving:
            self.anim_timer += 1
            if self.anim_timer > 8:
                self.anim_frame = (self.anim_frame + 1) % 4
                self.anim_timer = 0

        # Trap damage (BUG FIX: có cooldown, import đã ở đầu file)
        if tile_map.is_trap(self.x, self.y):
            now_trap = pygame.time.get_ticks()
            if now_trap - self.trap_cooldown_timer >= TRAP_COOLDOWN:
                self.trap_cooldown_timer = now_trap
                self.take_damage(TRAP_DAMAGE)

        # === Shield timer ===
        if self.shield_active:
            if now - self.shield_timer > SHIELD_DURATION:
                self.shield_active = False
                self.shield_hp = 0

        # === Projectile update ===
        for proj in self.projectiles:
            proj['x'] += proj['dx']
            proj['y'] += proj['dy']
            speed = (proj['dx']**2 + proj['dy']**2)**0.5
            proj['traveled'] += speed
        self.projectiles = [p for p in self.projectiles
                           if p['traveled'] < p['max_range'] and p['pierce_left'] > 0]

        # === Spirit update ===
        if self.spirit:
            if now - self.spirit['spawn_time'] > SUMMON_DURATION:
                self.spirit = None

    def render(self, surface, camera):
        """Vẽ player lên màn hình."""
        if not self.alive:
            return
        sx, sy = camera.apply(self.x, self.y)
        half = self.size // 2

        # Blink khi invincible
        if self.is_invincible and not self.is_dashing:
            if (pygame.time.get_ticks() // 80) % 2 == 0:
                return

        # Dash trail
        if self.is_dashing:
            trail_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.rect(trail_surf, (*COLOR_PLAYER, 80),
                             (0, 0, self.size, self.size), 0, 4)
            for i in range(3):
                tx = sx - self.dash_dx * (i + 1) * 2
                ty = sy - self.dash_dy * (i + 1) * 2
                trail_surf.set_alpha(60 - i * 20)
                surface.blit(trail_surf, (tx - half, ty - half))

        # --- Áp dụng đồ họa Ảnh (Sprite) nếu có ---
        import assets
        player_img = assets.get_asset('player')
        
        now = pygame.time.get_ticks()
        is_moving = self.moving
        bob = int(2 * math.sin(now * 0.015)) if is_moving else int(1 * math.sin(now * 0.003))

        if player_img:
            # Lật ảnh nếu đang đi sang trái
            img = player_img
            if self.facing[0] < 0:
                img = pygame.transform.flip(player_img, True, False)
            
            # Hit flash
            if self.hit_flash:
                flash_surf = img.copy()
                flash_surf.fill((255, 100, 100, 150), special_flags=pygame.BLEND_RGBA_MULT)
                surface.blit(flash_surf, (sx - img.get_width()//2, sy - img.get_height()//2 + bob))
            else:
                surface.blit(img, (sx - img.get_width()//2, sy - img.get_height()//2 + bob))
            
            # Vẽ kiếm
            if self.is_attacking:
                swing = (pygame.time.get_ticks() - self.attack_timer) / self.attack_duration
                angle = swing * math.pi * 0.8
                sw_x = sx + self.facing[0] * 20 + math.cos(angle) * 15 * (1 if self.facing[0] >= 0 else -1)
                sw_y = sy + self.facing[1] * 20 + math.sin(angle) * 15
                pygame.draw.line(surface, COLOR_PLAYER_SWORD, (sx, sy + bob), (int(sw_x), int(sw_y)), 4)
                pygame.draw.circle(surface, (200, 220, 255), (int(sw_x), int(sw_y)), 3)
            else:
                sword_offset_x = 11 if self.facing[0] >= 0 else -11
                pygame.draw.line(surface, COLOR_PLAYER_SWORD,
                                 (sx + sword_offset_x, sy - 2 + bob),
                                 (sx + sword_offset_x, sy + 12 + bob), 3)

            # AoE effect
            if self.aoe_active:
                progress = min(1.0, max(0.0, (pygame.time.get_ticks() - self.aoe_timer) / AOE_DURATION))
                radius = max(1, int(AOE_RADIUS * progress))
                aoe_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                alpha = max(0, min(255, int(120 * (1 - progress))))
                pygame.draw.circle(aoe_surf, (150, 50, 200, alpha), (radius, radius), radius)
                pygame.draw.circle(aoe_surf, (200, 100, 255, alpha), (radius, radius), radius, 2)
                surface.blit(aoe_surf, (sx - radius, sy - radius))

            # Shield visual
            if self.shield_active:
                shield_r = half + 12
                s_surf = pygame.Surface((shield_r * 2, shield_r * 2), pygame.SRCALPHA)
                pulse = 0.5 + 0.5 * math.sin(now * 0.008)
                s_alpha = int(50 + 40 * pulse)
                pygame.draw.circle(s_surf, (*COLOR_SHIELD, s_alpha), (shield_r, shield_r), shield_r)
                pygame.draw.circle(s_surf, (*COLOR_SHIELD_GLOW, s_alpha + 30), (shield_r, shield_r), shield_r, 2)
                surface.blit(s_surf, (sx - shield_r, sy - shield_r))

            # Lifesteal projectiles
            for proj in self.projectiles:
                px, py = camera.apply(proj['x'], proj['y'])
                p_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (*COLOR_LIFESTEAL, 200), (8, 8), 6)
                pygame.draw.circle(p_surf, (255, 100, 130, 120), (8, 8), 8)
                surface.blit(p_surf, (px - 8, py - 8))

            # Summon Spirit
            if self.spirit:
                sp = self.spirit
                spx, spy = camera.apply(sp['x'], sp['y'])
                sp_bob = int(3 * math.sin(now * 0.005))
                sp_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
                sp_alpha = int(150 + 50 * math.sin(now * 0.006))
                pygame.draw.circle(sp_surf, (*COLOR_SPIRIT, sp_alpha), (12, 12), 10)
                pygame.draw.circle(sp_surf, (*COLOR_SPIRIT_GLOW, sp_alpha // 2), (12, 12), 12)
                surface.blit(sp_surf, (spx - 12, spy - 12 + sp_bob))
                pygame.draw.circle(surface, (255, 255, 255), (int(spx - 3), int(spy - 2 + sp_bob)), 2)
                pygame.draw.circle(surface, (255, 255, 255), (int(spx + 3), int(spy - 2 + sp_bob)), 2)

            return

        # --- FALLBACK: Dùng code vẽ đồ họa cũ ---
        # --- Shadow ---
        shadow_surf = pygame.Surface((self.size + 10, self.size // 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 80), (0, 0, self.size + 10, self.size // 2))
        surface.blit(shadow_surf, (sx - half - 5, sy + half - 4))

        # --- Ambient Glow ---
        glow_surf = pygame.Surface((self.size * 2, self.size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (*COLOR_PLAYER, 20), (self.size, self.size), self.size)
        surface.blit(glow_surf, (sx - self.size, sy - self.size))

        # Animation state
        cape_wave = int(4 * math.sin(now * 0.01)) if is_moving else int(2 * math.sin(now * 0.004))

        # Colors
        body_color = (255, 80, 80) if self.hit_flash else (70, 30, 100) # Dark purple armor
        armor_color = (255, 150, 150) if self.hit_flash else (110, 70, 150) # Light purple plates
        cape_color = (40, 15, 60)

        # --- Cape ---
        # Draw cape behind body
        cape_points = [
            (sx - 7, sy - 5 + bob), 
            (sx + 7, sy - 5 + bob),
            (sx + 10 + cape_wave, sy + half + 6),
            (sx - 10 + cape_wave, sy + half + 6)
        ]
        pygame.draw.polygon(surface, cape_color, cape_points)

        # --- Body (Armor) ---
        body_rect = pygame.Rect(sx - 9, sy - half + 6 + bob, 18, self.size - 8)
        pygame.draw.rect(surface, body_color, body_rect, 0, 3)
        
        # Armor plates
        pygame.draw.rect(surface, armor_color, (sx - 10, sy - half + 7 + bob, 6, 6), 0, 2) # Left shoulder
        pygame.draw.rect(surface, armor_color, (sx + 4, sy - half + 7 + bob, 6, 6), 0, 2)  # Right shoulder
        pygame.draw.rect(surface, armor_color, (sx - 5, sy - half + 11 + bob, 10, 8), 0, 2) # Chest

        # --- Head ---
        head_y = sy - half - 3 + bob
        # Hair back
        pygame.draw.circle(surface, (25, 20, 35), (int(sx), int(head_y)), 8)
        # Face
        pygame.draw.circle(surface, COLOR_PLAYER_SKIN, (int(sx), int(head_y + 1)), 6)
        # Eyes (glowing)
        eye_color = (150, 255, 255)
        if self.facing[0] >= 0: # Right or vertical
            pygame.draw.circle(surface, eye_color, (int(sx + 2), int(head_y)), 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(sx + 2), int(head_y)), 1)
        if self.facing[0] <= 0: # Left or vertical
            pygame.draw.circle(surface, eye_color, (int(sx - 2), int(head_y)), 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(sx - 2), int(head_y)), 1)
        # Hair front
        pygame.draw.arc(surface, (25, 20, 35), (sx - 8, head_y - 8, 16, 12), 0, math.pi, 3)

        # Sword
        if self.is_attacking:
            swing = (pygame.time.get_ticks() - self.attack_timer) / self.attack_duration
            angle = swing * math.pi * 0.8
            sw_x = sx + self.facing[0] * 20 + math.cos(angle) * 15 * (1 if self.facing[0] >= 0 else -1)
            sw_y = sy + self.facing[1] * 20 + math.sin(angle) * 15
            pygame.draw.line(surface, COLOR_PLAYER_SWORD, (sx, sy + bob), (int(sw_x), int(sw_y)), 4)
            # Glowing sword tip
            pygame.draw.circle(surface, (200, 220, 255), (int(sw_x), int(sw_y)), 3)
            
            # Hiệu ứng cung tấn công
            atk_rect = self.get_attack_rect()
            atk_screen = camera.apply_rect(atk_rect)
            arc_surf = pygame.Surface((atk_screen.w, atk_screen.h), pygame.SRCALPHA)
            pygame.draw.arc(arc_surf, (200, 220, 255, 150),
                            (0, 0, atk_screen.w, atk_screen.h), 0, math.pi, 4)
            surface.blit(arc_surf, atk_screen.topleft)
        else:
            # Kiếm bên hông
            sword_offset_x = 11 if self.facing[0] >= 0 else -11
            pygame.draw.line(surface, COLOR_PLAYER_SWORD,
                             (sx + sword_offset_x, sy - 2 + bob),
                             (sx + sword_offset_x, sy + 12 + bob), 3)
            pygame.draw.circle(surface, (200, 220, 255), (int(sx + sword_offset_x), int(sy + 12 + bob)), 2)

        # AoE effect
        if self.aoe_active:
            progress = min(1.0, max(0.0, (pygame.time.get_ticks() - self.aoe_timer) / AOE_DURATION))
            radius = max(1, int(AOE_RADIUS * progress))
            aoe_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            alpha = max(0, min(255, int(120 * (1 - progress))))
            pygame.draw.circle(aoe_surf, (150, 50, 200, alpha), (radius, radius), radius)
            pygame.draw.circle(aoe_surf, (200, 100, 255, alpha), (radius, radius), radius, 2)
            surface.blit(aoe_surf, (sx - radius, sy - radius))

        # === Shield visual ===
        if self.shield_active:
            now = pygame.time.get_ticks()
            shield_r = half + 12
            s_surf = pygame.Surface((shield_r * 2, shield_r * 2), pygame.SRCALPHA)
            pulse = 0.5 + 0.5 * math.sin(now * 0.008)
            s_alpha = int(50 + 40 * pulse)
            pygame.draw.circle(s_surf, (*COLOR_SHIELD, s_alpha), (shield_r, shield_r), shield_r)
            pygame.draw.circle(s_surf, (*COLOR_SHIELD_GLOW, s_alpha + 30), (shield_r, shield_r), shield_r, 2)
            surface.blit(s_surf, (sx - shield_r, sy - shield_r))

        # === Lifesteal projectiles ===
        for proj in self.projectiles:
            px, py = camera.apply(proj['x'], proj['y'])
            p_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(p_surf, (*COLOR_LIFESTEAL, 200), (8, 8), 6)
            pygame.draw.circle(p_surf, (255, 100, 130, 120), (8, 8), 8)
            surface.blit(p_surf, (px - 8, py - 8))

        # === Summon Spirit ===
        if self.spirit:
            sp = self.spirit
            spx, spy = camera.apply(sp['x'], sp['y'])
            now = pygame.time.get_ticks()
            bob = int(3 * math.sin(now * 0.005))
            sp_surf = pygame.Surface((24, 24), pygame.SRCALPHA)
            sp_alpha = int(150 + 50 * math.sin(now * 0.006))
            pygame.draw.circle(sp_surf, (*COLOR_SPIRIT, sp_alpha), (12, 12), 10)
            pygame.draw.circle(sp_surf, (*COLOR_SPIRIT_GLOW, sp_alpha // 2), (12, 12), 12)
            surface.blit(sp_surf, (spx - 12, spy - 12 + bob))
            # Eyes
            pygame.draw.circle(surface, (255, 255, 255), (int(spx - 3), int(spy - 2 + bob)), 2)
            pygame.draw.circle(surface, (255, 255, 255), (int(spx + 3), int(spy - 2 + bob)), 2)
