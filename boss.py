"""
boss.py — Boss Quỷ Vương Malphas
==================================
Phase 1 (HP 100-50%): Triệu hồi quái + đạn bóng tối + dash
Phase 2 (HP <50%): A* + AoE + teleport + đạn xoáy + dash mạnh
"""

import math
import random
import pygame
from settings import (
    BOSS_HP, BOSS_DAMAGE, BOSS_SPEED_P1, BOSS_SPEED_P2, BOSS_DETECT_RANGE,
    BOSS_SUMMON_INTERVAL, BOSS_AOE_RADIUS, BOSS_AOE_COOLDOWN, BOSS_SIZE,
    COLOR_BOSS, COLOR_BOSS_GLOW, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    PLAYER_ATTACK_KNOCKBACK, RED, WHITE, YELLOW,
    BOSS_DASH_COOLDOWN, BOSS_DASH_SPEED, BOSS_DASH_DURATION, BOSS_DASH_DAMAGE, BOSS_DASH_RANGE,
    BOSS_PROJ_COOLDOWN, BOSS_PROJ_COUNT, BOSS_PROJ_SPEED, BOSS_PROJ_DAMAGE, BOSS_PROJ_RANGE,
    BOSS_TELE_COOLDOWN, BOSS_TELE_DISTANCE
)
from ai import astar_find_path, get_direction_towards, distance_between
from item import generate_loot


class Boss:
    """Boss Malphas — con người già hấp hối dùng Kael như công cụ.

    Attributes:
        phase (int): 1 hoặc 2
        summon_timer (int): Timer triệu hồi quái
        aoe_timer (int): Timer AoE
        summoned_enemies (list): Quái được triệu hồi
    """

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.size = BOSS_SIZE
        self.max_hp = BOSS_HP
        self.hp = BOSS_HP
        self.target_hp = self.hp
        self.damage = BOSS_DAMAGE
        self.speed = BOSS_SPEED_P1
        self.detect_range = BOSS_DETECT_RANGE
        self.alive = True
        self.phase = 1
        self.color = COLOR_BOSS

        # Timers
        self.summon_timer = pygame.time.get_ticks()
        self.aoe_timer = 0
        self.aoe_active = False
        self.aoe_progress = 0
        self.last_attack = 0
        self.attack_cooldown = 1000
        self.hit_flash = False
        self.flash_timer = 0
        self.spawn_time = pygame.time.get_ticks()

        # --- Skill: Dash ---
        self.dash_timer = pygame.time.get_ticks()
        self.is_dashing = False
        self.dash_dx = 0
        self.dash_dy = 0
        self.dash_start = 0
        self.dash_hit = False  # Đã đánh trúng player trong lần dash này chưa

        # --- Skill: Projectiles ---
        self.proj_timer = pygame.time.get_ticks()
        self.projectiles = []  # [{'x','y','dx','dy','traveled'}]

        # --- Skill: Teleport (Phase 2 only) ---
        self.tele_timer = pygame.time.get_ticks()
        self.tele_flash = 0  # Hiệu ứng flash khi teleport

        # Pathfinding
        self.path = []
        self.visited = set()
        self.path_index = 0
        self.path_timer = 0

        # Phase transition
        self.phase_transition = False
        self.transition_timer = 0
        self.transition_duration = 2000

        # Summoned enemies (returned to game_state for management)
        self.pending_summons = []

        # Knockback
        self.knockback_dx = 0
        self.knockback_dy = 0
        self.knockback_timer = 0

        # BUG FIX: Cache font (tránh tạo mới mỗi frame)
        self._transition_font = None

    def get_rect(self):
        return pygame.Rect(self.x - self.size // 2, self.y - self.size // 2,
                           self.size, self.size)

    def take_damage(self, amount, knockback_dx=0, knockback_dy=0):
        """Nhận sát thương. Kiểm tra phase transition."""
        self.hp -= amount
        self.hit_flash = True
        self.flash_timer = pygame.time.get_ticks()
        if not self.is_dashing:  # Không bị knockback khi đang dash
            self.knockback_dx = knockback_dx * (PLAYER_ATTACK_KNOCKBACK * 0.3)
            self.knockback_dy = knockback_dy * (PLAYER_ATTACK_KNOCKBACK * 0.3)
            self.knockback_timer = pygame.time.get_ticks()

        # Phase transition: HP < 50%
        if self.phase == 1 and self.hp <= self.max_hp * 0.5:
            self.phase = 2
            self.speed = BOSS_SPEED_P2
            self.phase_transition = True
            self.transition_timer = pygame.time.get_ticks()

        if self.hp <= 0:
            self.hp = 0
            self.alive = False
            return True
        return False

    def update(self, player, tile_map, walkable_grid):
        """Cập nhật boss AI mỗi frame."""
        if not self.alive:
            return
        now = pygame.time.get_ticks()

        # Cập nhật máu trễ
        if self.target_hp > self.hp:
            self.target_hp -= (self.target_hp - self.hp) * 0.05
            if self.target_hp - self.hp < 0.5:
                self.target_hp = self.hp
        elif self.target_hp < self.hp:
            self.target_hp = self.hp

        # Flash
        if self.hit_flash and now - self.flash_timer > 100:
            self.hit_flash = False

        # Teleport flash
        if self.tele_flash > 0:
            self.tele_flash -= 1

        # Phase transition animation
        if self.phase_transition:
            if now - self.transition_timer > self.transition_duration:
                self.phase_transition = False
            return  # Pause during transition

        # --- Cập nhật Dash ---
        if self.is_dashing:
            if now - self.dash_start > BOSS_DASH_DURATION:
                self.is_dashing = False
            else:
                new_x = self.x + self.dash_dx
                new_y = self.y + self.dash_dy
                half = self.size // 2
                if tile_map.is_walkable(new_x - half, new_y) and tile_map.is_walkable(new_x + half, new_y):
                    self.x = new_x
                if tile_map.is_walkable(self.x, new_y - half) and tile_map.is_walkable(self.x, new_y + half):
                    self.y = new_y
                # Gây sát thương khi lao trúng
                if not self.dash_hit:
                    dist_p = distance_between(self.x, self.y, player.x, player.y)
                    if dist_p < self.size:
                        player.take_damage(BOSS_DASH_DAMAGE)
                        self.dash_hit = True
                return  # Không làm gì khác khi đang dash

        # Knockback
        if now - self.knockback_timer < 80:
            new_x = self.x + self.knockback_dx
            new_y = self.y + self.knockback_dy
            if tile_map.is_walkable(new_x, new_y):
                self.x = new_x
                self.y = new_y
            return

        # --- Cập nhật Projectiles ---
        for proj in self.projectiles:
            proj['x'] += proj['dx']
            proj['y'] += proj['dy']
            proj['traveled'] += (proj['dx']**2 + proj['dy']**2)**0.5
            # Kiểm tra trúng player
            d = distance_between(proj['x'], proj['y'], player.x, player.y)
            if d < 18:
                player.take_damage(BOSS_PROJ_DAMAGE)
                proj['traveled'] = BOSS_PROJ_RANGE + 1  # Xóa đạn
        self.projectiles = [p for p in self.projectiles if p['traveled'] < BOSS_PROJ_RANGE]

        dist = distance_between(self.x, self.y, player.x, player.y)

        if self.phase == 1:
            self._phase1_ai(player, tile_map, walkable_grid, now, dist)
        else:
            self._phase2_ai(player, tile_map, walkable_grid, now, dist)

    def _fire_projectiles(self, player, count):
        """Bắn đạn bóng tối về phía player."""
        angle_to_player = math.atan2(player.y - self.y, player.x - self.x)
        spread = math.pi / 6  # 30 độ spread
        for i in range(count):
            offset = (i - count // 2) * (spread / max(1, count - 1))
            ang = angle_to_player + offset
            self.projectiles.append({
                'x': self.x,
                'y': self.y,
                'dx': math.cos(ang) * BOSS_PROJ_SPEED,
                'dy': math.sin(ang) * BOSS_PROJ_SPEED,
                'traveled': 0
            })

    def _start_dash(self, player):
        """Lao tới phía player."""
        angle = math.atan2(player.y - self.y, player.x - self.x)
        self.dash_dx = math.cos(angle) * BOSS_DASH_SPEED
        self.dash_dy = math.sin(angle) * BOSS_DASH_SPEED
        self.is_dashing = True
        self.dash_start = pygame.time.get_ticks()
        self.dash_hit = False

    def _teleport_behind(self, player, tile_map):
        """Teleport ra sau lưng player."""
        fx, fy = player.facing
        # Xuất hiện phía sau player
        tx = player.x - fx * BOSS_TELE_DISTANCE
        ty = player.y - fy * BOSS_TELE_DISTANCE
        # Kiểm tra vị trí hợp lệ
        if tile_map.is_walkable(tx, ty):
            self.x = tx
            self.y = ty
            self.tele_flash = 15  # 15 frame flash effect

    def _phase1_ai(self, player, tile_map, walkable_grid, now, dist):
        """Phase 1: Triệu hồi quái + đạn bóng tối + dash."""
        # Triệu hồi quái mỗi N giây
        if now - self.summon_timer > BOSS_SUMMON_INTERVAL:
            self.summon_timer = now
            # Spawn 1-2 souls gần boss
            for _ in range(random.randint(1, 2)):
                for _ in range(5):  # Thử tìm vị trí hợp lệ 5 lần
                    sx = self.x + random.randint(-80, 80)
                    sy = self.y + random.randint(-80, 80)
                    if tile_map.is_walkable(sx, sy):
                        self.pending_summons.append(("soul", sx, sy))
                        break

        # --- Skill: Bắn đạn bóng tối ---
        if now - self.proj_timer > BOSS_PROJ_COOLDOWN and dist < BOSS_PROJ_RANGE:
            self.proj_timer = now
            self._fire_projectiles(player, 3)  # Phase 1: 3 viên

        # --- Skill: Dash lao tới ---
        if now - self.dash_timer > BOSS_DASH_COOLDOWN and BOSS_DASH_RANGE * 0.4 < dist < BOSS_DASH_RANGE:
            self.dash_timer = now
            self._start_dash(player)
            return

        # Di chuyển chậm về phía player
        if dist > 60:
            dx, dy = get_direction_towards(self.x, self.y, player.x, player.y, self.speed)
            half = self.size // 2
            new_x = self.x + dx
            new_y = self.y + dy
            if tile_map.is_walkable(new_x - half, new_y) and tile_map.is_walkable(new_x + half, new_y):
                self.x = new_x
            if tile_map.is_walkable(self.x, new_y - half) and tile_map.is_walkable(self.x, new_y + half):
                self.y = new_y

        # Tấn công melee
        if dist < 50 and now - self.last_attack > self.attack_cooldown:
            self.last_attack = now
            player.take_damage(self.damage)

    def _phase2_ai(self, player, tile_map, walkable_grid, now, dist):
        """Phase 2: A* pathfinding + AoE + teleport + đạn xoáy + dash mạnh."""
        # A* pathfinding
        if now - self.path_timer > 400:
            self.path_timer = now
            self.path, self.visited = astar_find_path(self.x, self.y, player.x, player.y, walkable_grid)
            self.path_index = 0

        # Follow path
        if self.path and self.path_index < len(self.path):
            tx, ty = self.path[self.path_index]
            d = distance_between(self.x, self.y, tx, ty)
            if d < self.speed * 2:
                self.path_index += 1
            else:
                dx, dy = get_direction_towards(self.x, self.y, tx, ty, self.speed)
                half = self.size // 2
                new_x = self.x + dx
                new_y = self.y + dy
                # BUG FIX: Check 4 góc thay vì chỉ tâm
                if tile_map.is_walkable(new_x - half, new_y) and tile_map.is_walkable(new_x + half, new_y):
                    self.x = max(half, min(MAP_WIDTH * TILE_SIZE - half, new_x))
                if tile_map.is_walkable(self.x, new_y - half) and tile_map.is_walkable(self.x, new_y + half):
                    self.y = max(half, min(MAP_HEIGHT * TILE_SIZE - half, new_y))

        # --- Skill: AoE attack ---
        if now - self.aoe_timer > BOSS_AOE_COOLDOWN:
            self.aoe_timer = now
            self.aoe_active = True
            self.aoe_progress = 0

        if self.aoe_active:
            self.aoe_progress += 0.02
            if self.aoe_progress >= 1.0:
                self.aoe_active = False
                # Deal AoE damage
                if dist < BOSS_AOE_RADIUS:
                    player.take_damage(self.damage)

        # --- Skill: Bắn đạn bóng tối (5 viên xoáy) ---
        if now - self.proj_timer > BOSS_PROJ_COOLDOWN * 0.7 and dist < BOSS_PROJ_RANGE:
            self.proj_timer = now
            self._fire_projectiles(player, BOSS_PROJ_COUNT)

        # --- Skill: Dash lao tới (nhanh hơn Phase 1) ---
        if now - self.dash_timer > BOSS_DASH_COOLDOWN * 0.7 and BOSS_DASH_RANGE * 0.3 < dist < BOSS_DASH_RANGE:
            self.dash_timer = now
            self._start_dash(player)
            return

        # --- Skill: Teleport sau lưng player ---
        if now - self.tele_timer > BOSS_TELE_COOLDOWN and dist > 150:
            self.tele_timer = now
            self._teleport_behind(player, tile_map)

        # Melee attack
        if dist < 50 and now - self.last_attack > self.attack_cooldown * 0.7:
            self.last_attack = now
            player.take_damage(self.damage)

        # Triệu hồi ít hơn nhưng mạnh hơn
        if now - self.summon_timer > BOSS_SUMMON_INTERVAL * 1.5:
            self.summon_timer = now
            for _ in range(5):  # Thử 5 lần để tìm vị trí hợp lệ
                sx = self.x + random.randint(-100, 100)
                sy = self.y + random.randint(-100, 100)
                if tile_map.is_walkable(sx, sy):
                    self.pending_summons.append(("minion", sx, sy))
                    break

    def get_pending_summons(self):
        """Lấy và xóa danh sách quái chờ triệu hồi."""
        summons = self.pending_summons.copy()
        self.pending_summons.clear()
        return summons

    def drop_loot(self):
        """Boss luôn rơi Epic item."""
        return generate_loot(self.x, self.y, boss_drop=True)

    def render(self, surface, camera):
        """Vẽ boss Malphas."""
        if not self.alive:
            return
        sx, sy = camera.apply(self.x, self.y)
        half = self.size // 2
        t = (pygame.time.get_ticks() - self.spawn_time) / 1000.0

        # Phase transition effect
        if self.phase_transition:
            progress = (pygame.time.get_ticks() - self.transition_timer) / self.transition_duration
            radius = int(120 * progress)
            flash_surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            alpha = int(max(0, min(255, 200 * (1 - progress))))
            pygame.draw.circle(flash_surf, (255, 60, 20, alpha), (radius, radius), radius)
            surface.blit(flash_surf, (sx - radius, sy - radius))
            # Text "PHASE 2" (BUG FIX: dùng cached font)
            if self._transition_font is None:
                self._transition_font = pygame.font.SysFont("consolas", 28, bold=True)
            text = self._transition_font.render("PHASE 2", True, (255, 100, 50))
            text.set_alpha(alpha)
            surface.blit(text, (sx - text.get_width() // 2, sy - 80))
            return

        # Aura glow
        glow_r = half + 15 + int(5 * math.sin(t * 2))
        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
        glow_color = COLOR_BOSS_GLOW if self.phase == 2 else (80, 30, 30)
        glow_alpha = 50 + int(20 * math.sin(t * 3))
        pygame.draw.circle(glow_surf, (*glow_color, glow_alpha), (glow_r, glow_r), glow_r)
        surface.blit(glow_surf, (sx - glow_r, sy - glow_r))

        # Hit flash
        body_color = (255, 100, 100) if self.hit_flash else (20, 20, 30) # Dark cloak
        armor_color = (255, 150, 150) if self.hit_flash else (100, 20, 30) # Red armor

        # Shadow
        shadow_surf = pygame.Surface((self.size + 40, self.size), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 100), (0, 0, self.size + 40, self.size))
        surface.blit(shadow_surf, (sx - half - 20, sy + half - 10))

        # --- Wings ---
        flap = math.sin(t * (4 if self.phase == 2 else 2))
        wing_span = 40 if self.phase == 2 else 25
        wing_color = (150, 40, 40) if self.phase == 2 else (60, 40, 50)
        wing_alpha = 180 if self.phase == 2 else 120
        
        wings_surf = pygame.Surface((self.size + 120, self.size + 60), pygame.SRCALPHA)
        wx = self.size // 2 + 60
        wy = self.size // 2 + 30
        # Left wing
        l_wing_points = [
            (wx - 10, wy), 
            (wx - 20 - wing_span, wy - 30 - int(10 * flap)),
            (wx - 30 - wing_span, wy - 10),
            (wx - 15, wy + 20)
        ]
        pygame.draw.polygon(wings_surf, (*wing_color, wing_alpha), l_wing_points)
        pygame.draw.polygon(wings_surf, (30, 10, 10, wing_alpha), l_wing_points, 2)
        # Right wing
        r_wing_points = [
            (wx + 10, wy), 
            (wx + 20 + wing_span, wy - 30 - int(10 * flap)),
            (wx + 30 + wing_span, wy - 10),
            (wx + 15, wy + 20)
        ]
        pygame.draw.polygon(wings_surf, (*wing_color, wing_alpha), r_wing_points)
        pygame.draw.polygon(wings_surf, (30, 10, 10, wing_alpha), r_wing_points, 2)
        surface.blit(wings_surf, (sx - wx, sy - wy - 10))

        # --- Body (Cloak & Armor) ---
        bob = int(4 * math.sin(t * 3))
        body_points = [
            (sx, sy - half + bob),           # Top
            (sx + half + 5, sy + half + 10), # Bottom right flare
            (sx + half - 10, sy + half + 5), 
            (sx - half + 10, sy + half + 5), 
            (sx - half - 5, sy + half + 10), # Bottom left flare
        ]
        pygame.draw.polygon(surface, body_color, body_points)
        pygame.draw.polygon(surface, (10, 10, 15), body_points, 2)

        # Chest Armor
        pygame.draw.polygon(surface, armor_color, [
            (sx, sy - half + 8 + bob),
            (sx + 12, sy - half + 18 + bob),
            (sx, sy + 5 + bob),
            (sx - 12, sy - half + 18 + bob)
        ])
        
        # Shoulder Armor
        pygame.draw.rect(surface, armor_color, (sx - half - 4, sy - half + 10 + bob, 10, 12), 0, 3)
        pygame.draw.rect(surface, armor_color, (sx + half - 6, sy - half + 10 + bob, 10, 12), 0, 3)

        # --- Head & Horns ---
        head_y = sy - half - 8 + bob
        # Face (dark void)
        pygame.draw.circle(surface, (15, 10, 20), (int(sx), int(head_y)), 12)
        
        # Horns
        horn_color = (80, 20, 20) if self.phase == 2 else (60, 50, 50)
        horn_len = 18 if self.phase == 2 else 12
        pygame.draw.polygon(surface, horn_color, [(sx - 8, head_y - 8), (sx - 16, head_y - 8 - horn_len), (sx - 4, head_y - 12)])
        pygame.draw.polygon(surface, horn_color, [(sx + 8, head_y - 8), (sx + 16, head_y - 8 - horn_len), (sx + 4, head_y - 12)])
        
        # Crown floating above
        crown_y = head_y - 16 + int(2 * math.sin(t * 5))
        pygame.draw.rect(surface, YELLOW, (sx - 10, crown_y, 20, 4))
        for i in [-8, 0, 8]:
            pygame.draw.polygon(surface, YELLOW, [(sx + i - 3, crown_y), (sx + i, crown_y - 8), (sx + i + 3, crown_y)])

        # Glowing eyes
        eye_glow = int(200 + 55 * math.sin(t * 8))
        eye_color = (eye_glow, 20, 20) if self.phase == 2 else (eye_glow, eye_glow, 100)
        pygame.draw.circle(surface, eye_color, (int(sx - 5), int(head_y - 2)), 3)
        pygame.draw.circle(surface, eye_color, (int(sx + 5), int(head_y - 2)), 3)
        pygame.draw.circle(surface, (255, 255, 255), (int(sx - 5), int(head_y - 2)), 1)
        pygame.draw.circle(surface, (255, 255, 255), (int(sx + 5), int(head_y - 2)), 1)

        # AoE warning ring (Phase 2)
        if self.aoe_active:
            r = int(BOSS_AOE_RADIUS * self.aoe_progress)
            aoe_surf = pygame.Surface((BOSS_AOE_RADIUS * 2, BOSS_AOE_RADIUS * 2), pygame.SRCALPHA)
            aoe_alpha = int(100 * (1 - self.aoe_progress))
            # Vòng tròn chính
            pygame.draw.circle(aoe_surf, (255, 60, 20, aoe_alpha), (BOSS_AOE_RADIUS, BOSS_AOE_RADIUS), r, 3)
            pygame.draw.circle(aoe_surf, (255, 100, 50, aoe_alpha // 3), (BOSS_AOE_RADIUS, BOSS_AOE_RADIUS), r)
            
            # Ký hiệu ma thuật (ngôi sao / rune) bên trong
            if self.phase == 2:
                points = []
                for i in range(5):
                    ang = -math.pi/2 + i * (4 * math.pi / 5) + (t * 2)
                    px = BOSS_AOE_RADIUS + math.cos(ang) * r * 0.8
                    py = BOSS_AOE_RADIUS + math.sin(ang) * r * 0.8
                    points.append((px, py))
                if len(points) >= 3:
                    pygame.draw.polygon(aoe_surf, (255, 50, 50, aoe_alpha // 2), points, 2)
            
            surface.blit(aoe_surf, (sx - BOSS_AOE_RADIUS, sy - BOSS_AOE_RADIUS))

        # --- Vẽ Đạn Bóng Tối ---
        for proj in self.projectiles:
            px, py = camera.apply(proj['x'], proj['y'])
            # Core đạn
            proj_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(proj_surf, (200, 40, 40, 200), (8, 8), 6)
            pygame.draw.circle(proj_surf, (255, 100, 50, 150), (8, 8), 8)
            pygame.draw.circle(proj_surf, (255, 200, 100), (8, 8), 3)
            surface.blit(proj_surf, (px - 8, py - 8))

        # --- Vẽ hiệu ứng Dash ---
        if self.is_dashing:
            # Trail đỏ phía sau
            for i in range(4):
                trail_x = sx - self.dash_dx * (i + 1) * 1.5
                trail_y = sy - self.dash_dy * (i + 1) * 1.5
                trail_alpha = max(10, 100 - i * 25)
                trail_surf = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
                pygame.draw.circle(trail_surf, (255, 40, 20, trail_alpha),
                                   (self.size // 2, self.size // 2), self.size // 2)
                surface.blit(trail_surf, (trail_x - self.size // 2, trail_y - self.size // 2))

        # --- Vẽ hiệu ứng Teleport flash ---
        if self.tele_flash > 0:
            flash_r = 40 + (15 - self.tele_flash) * 3
            flash_surf = pygame.Surface((flash_r * 2, flash_r * 2), pygame.SRCALPHA)
            flash_alpha = int(self.tele_flash * 15)
            pygame.draw.circle(flash_surf, (180, 50, 255, flash_alpha), (flash_r, flash_r), flash_r)
            pygame.draw.circle(flash_surf, (255, 100, 255, flash_alpha), (flash_r, flash_r), flash_r, 3)
            surface.blit(flash_surf, (sx - flash_r, sy - flash_r))

        # (Bỏ thanh máu nhỏ trên đầu boss vì đã có thanh máu UI lớn trên cùng màn hình)
