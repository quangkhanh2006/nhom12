"""
game_state.py — Quản lý trạng thái game
==========================================
States: MENU → GAMEPLAY → PAUSE / GAME_OVER / VICTORY
Quản lý chuyển chương, spawn quái, combat, ending.
"""

import math
import random
import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CHAPTER_ENEMIES, TILE_SIZE,
    AOE_RADIUS, AOE_DAMAGE_MULTI, PLAYER_PICKUP_RANGE, PLAYER_ATTACK_KNOCKBACK,
    SUMMON_SPEED, SUMMON_ATTACK_RANGE, SUMMON_ATTACK_CD,
    WHITE, YELLOW, GRAY, RED, BLACK, GREEN, ORANGE,
    SOUL_EXP, MINION_EXP, SHADOW_EXP, BOSS_EXP,
    INVENTORY_SIZE, EQUIP_SLOTS,
    SLOW_MO_DURATION, SLOW_MO_FACTOR,
    NG_PLUS_HP_MULTI, NG_PLUS_DMG_MULTI, NG_PLUS_DROP_BONUS,
    CHAPTER_QUESTS, COMBO_TIMEOUT, SKILL_UNLOCK_LEVELS
)
from pet import Pet
from tilemap import TileMap
from player import Player
from enemy import Enemy
from boss import Boss
from camera import Camera
from ui import UI
from dialogue import DialogueBox
from item import generate_loot
from story import CHAPTER_DIALOGUES, ENDINGS
from ai import distance_between
from effects import ParticleSystem, ScreenEffects
import sound
import os
from save_manager import save_game, load_game

# Game states
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_PAUSE = "pause"
STATE_GAME_OVER = "game_over"
STATE_VICTORY = "victory"
STATE_ENDING = "ending"
STATE_CREDITS = "credits"
STATE_CHAPTER_INTRO = "chapter_intro"
STATE_DIALOGUE = "dialogue"
STATE_SETTINGS = "settings"
STATE_DIFFICULTY_SELECT = "difficulty_select"

import icons


class GameState:
    """Quản lý toàn bộ trạng thái game.

    Attributes:
        state (str): Trạng thái hiện tại
        chapter (int): Chương hiện tại (1-5)
        player (Player): Nhân vật chính
        enemies (list[Enemy]): Danh sách kẻ địch
        boss (Boss): Boss (chỉ chương 5)
        items (list): Items trên map
        tile_map (TileMap): Bản đồ
        camera (Camera): Camera
        ui (UI): HUD
        dialogue_box (DialogueBox): Hộp thoại
    """

    def __init__(self):
        self.state = STATE_MENU
        self.chapter = 1
        self.player = None
        self.enemies = []
        self.boss = None
        self.items = []
        self.corpses = []
        self.tile_map = None
        self.camera = Camera()
        self.ui = UI()
        self.dialogue_box = DialogueBox()
        self.walkable_grid = None

        # Visual effects
        self.particles = ParticleSystem()
        self.screen_fx = ScreenEffects(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Chapter intro
        self.intro_timer = 0
        self.intro_duration = 3000

        # Dialogue triggers
        self.special_triggered = False
        self.complete_triggered = False
        self.npc_dialogue_done = False

        # Ending
        self.selected_ending = None

        # Fonts
        self._font = None
        self._big_font = None
        self._title_font = None
        self._small_font = None

        # Menu animation
        self.menu_time = 0

        # BUG FIX: track single-hit per attack swing
        self.attack_hit_this_swing = False
        # BUG FIX: track AoE damage dealt (separate from visual)
        self.aoe_damage_dealt = False
        # BUG FIX: prevent boss loot dropping every frame
        self.boss_loot_dropped = False
        # Track if chapter advance is pending (wait for dialogue)
        self.chapter_advance_pending = False

        # Auto-play AI
        self.auto_play = False
        self.auto_play_attack_timer = 0
        self.auto_play_path = []
        self.auto_play_path_timer = 0

        # === NEW: Death Slow-Mo ===
        self.slow_mo_active = False
        self.slow_mo_timer = 0

        # === NEW: New Game+ ===
        self.ng_plus = False
        self.ng_plus_count = 0  # Số lần chơi NG+

        # === NEW: Quest Tracker ===
        self.quest_states = {}  # {quest_index: completed}

        # === NEW: Kill counter ===
        self.total_kills = 0

        # === NEW: Pet ===
        self.pet = None

        # Debug AI
        self.debug_ai = False

        self.sfx_muted = False
        self.bgm_muted = False
        self._dragging_sfx = False
        self._dragging_bgm = False

        # Difficulty
        self.difficulty = "Normal"

    def _init_fonts(self):
        if self._font is None:
            self._font = pygame.font.SysFont("consolas", 18)
            self._big_font = pygame.font.SysFont("consolas", 24, bold=True)
            self._title_font = pygame.font.SysFont("consolas", 52, bold=True)
            self._small_font = pygame.font.SysFont("consolas", 14)

    def start_new_game(self):
        """Bắt đầu game mới từ chương 1."""
        self.chapter = 1
        if not self.ng_plus:
            self.player = None  # Force reset player (mất hết đồ)
        # Nếu NG+ thì giữ nguyên player + trang bị
        self.corpses = []   # Xóa xác cũ
        self.total_kills = 0
        self.quest_states = {}
        self.ui.reset_fog()
        self.load_chapter(1)

    def load_chapter(self, chapter):
        """Tải chương mới: map, player, quái."""
        self.chapter = chapter
        self.tile_map = TileMap(chapter)
        self.walkable_grid = self.tile_map.get_walkable_grid()

        # Player
        px, py = self.tile_map.player_start
        if self.player is None:
            self.player = Player(px, py)
        else:
            self.player.x = px
            self.player.y = py
            self.player.alive = True
            # BUG FIX: Hồi đầy HP khi retry/chuyển chương
            self.player.hp = self.player.max_hp
        self.player.inventory.action_log = self.ui.action_log

        # Enemies
        self.enemies = []
        self.boss = None
        self.items = []
        self.corpses = []
        self.special_triggered = False
        self.complete_triggered = False
        self.npc_dialogue_done = False
        self.boss_loot_dropped = False
        self.chapter_advance_pending = False

        # Pet initialization
        if self.pet is None:
            self.pet = Pet(px, py)
        else:
            self.pet.x = px
            self.pet.y = py

        if chapter == 5:
            # Boss chapter
            if self.tile_map.spawn_points:
                bx, by = self.tile_map.spawn_points[0]
            else:
                bx, by = 25 * 32, 25 * 32
            from settings import DIFFICULTY_CONFIGS
            diff_cfg = DIFFICULTY_CONFIGS.get(self.difficulty)
            self.boss = Boss(bx, by, difficulty_cfg=diff_cfg)
        else:
            # Spawn quái theo config chương
            cfg = CHAPTER_ENEMIES.get(chapter, {})
            from settings import DIFFICULTY_CONFIGS
            diff_cfg = DIFFICULTY_CONFIGS.get(self.difficulty)
            spawn_idx = 0
            spawns = self.tile_map.spawn_points

            for etype, count in [("soul", cfg.get("soul", 0)),
                                  ("minion", cfg.get("minion", 0)),
                                  ("shadow", cfg.get("shadow", 0))]:
                for _ in range(count):
                    if spawn_idx < len(spawns):
                        ex, ey = spawns[spawn_idx]
                        spawn_idx += 1
                    else:
                        # Fallback: tìm vị trí walkable ngẫu nhiên
                        ex, ey = 200, 200
                        for _attempt in range(100):
                            _ex = random.randint(200, 1400)
                            _ey = random.randint(200, 1400)
                            if self.tile_map.is_walkable(_ex, _ey):
                                ex, ey = _ex, _ey
                                break
                    enemy = Enemy(ex, ey, etype, difficulty_cfg=diff_cfg)
                    # NEW GAME+: Scale quái mạnh hơn
                    if self.ng_plus:
                        scale = 1 + self.ng_plus_count * 0.5
                        enemy.max_hp = int(enemy.max_hp * NG_PLUS_HP_MULTI * scale)
                        enemy.hp = enemy.max_hp
                        enemy.target_hp = enemy.hp
                        enemy.damage = int(enemy.damage * NG_PLUS_DMG_MULTI * scale)
                    self.enemies.append(enemy)

        # Chapter intro
        self.state = STATE_CHAPTER_INTRO
        self.intro_timer = pygame.time.get_ticks()
        sound.play_music(chapter)

        # Reset quest states cho chương mới
        self.quest_states = {}
        self.ui.reset_fog()

        # Start intro dialogue after delay
        if chapter in CHAPTER_DIALOGUES:
            intro = CHAPTER_DIALOGUES[chapter].get("intro", [])
            if intro:
                self.dialogue_box.start(intro)
                self.chapter_advance_pending = False

    def respawn_player(self):
        """Hồi sinh player tại điểm xuất phát mà không load lại map."""
        px, py = self.tile_map.player_start
        self.player.x = px
        self.player.y = py
        self.player.hp = self.player.max_hp
        self.player.alive = True
        self.state = STATE_PLAYING

    def update(self, keys, dt):
        """Cập nhật game mỗi frame."""
        if self.state == STATE_CHAPTER_INTRO:
            elapsed = pygame.time.get_ticks() - self.intro_timer
            if elapsed > self.intro_duration and not self.dialogue_box.active:
                self.state = STATE_PLAYING
            if self.dialogue_box.active:
                # Auto-play: tự advance dialogue
                if self.auto_play:
                    self.dialogue_box.advance()
                self.dialogue_box.update()
            return

        if self.state == STATE_DIALOGUE:
            self.dialogue_box.update()
            # Auto-play: tự advance dialogue
            if self.auto_play and self.dialogue_box.active:
                self.dialogue_box.advance()
            if not self.dialogue_box.active:
                if self.chapter_advance_pending:
                    self.chapter_advance_pending = False
                    self.advance_chapter()
                else:
                    self.state = STATE_PLAYING
            return

        if self.state != STATE_PLAYING:
            # Auto-play: tự retry khi chết, tự chọn ending khi thắng
            if self.auto_play:
                if self.state == STATE_GAME_OVER:
                    self.respawn_player()
                    return
                elif self.state == STATE_VICTORY:
                    self.selected_ending = "redemption"
                    self.state = STATE_ENDING
                    self.dialogue_box.start(ENDINGS["redemption"])
                    return
                elif self.state == STATE_ENDING:
                    if self.dialogue_box.active:
                        self.dialogue_box.advance()
                    else:
                        self.state = STATE_CREDITS
                    return
                elif self.state == STATE_CREDITS:
                    self.state = STATE_MENU
                    self.auto_play = False
                    return
            return

        # === Auto-play AI ===
        if self.auto_play:
            self._auto_play_update()

        # Cập nhật quest states để UI hiển thị real-time
        self._update_quest_states()

        # Player update
        # === Death Slow-Mo ===
        slow_factor = 1.0
        if self.slow_mo_active:
            elapsed_sm = pygame.time.get_ticks() - self.slow_mo_timer
            if elapsed_sm < SLOW_MO_DURATION:
                slow_factor = SLOW_MO_FACTOR
            else:
                self.slow_mo_active = False

        if not self.auto_play:
            self.player.handle_input(keys, self.tile_map)
        self.player.update(self.tile_map)

        # Camera
        self.camera.update(self.player.x, self.player.y)

        # Check player death
        if not self.player.alive:
            if self.state == STATE_PLAYING:
                # Tạo Corpse và rớt đồ
                corpse_items = []
                inv = self.player.inventory
                from settings import INVENTORY_SIZE, EQUIP_SLOTS as _EQUIP_SLOTS
                for i in range(INVENTORY_SIZE):
                    if inv.bag[i]:
                        corpse_items.append(inv.bag[i])
                        inv.bag[i] = None
                for slot in EQUIP_SLOTS:
                    if inv.equipped.get(slot):
                        corpse_items.append(inv.equipped[slot])
                        inv.equipped[slot] = None
                
                if corpse_items:
                    self.corpses.append({'x': self.player.x, 'y': self.player.y, 'items': corpse_items})
                    
                self.player.recalculate_stats()
                self.state = STATE_GAME_OVER
            return

        # === Update quest states ===
        self._update_quest_states()

        # === Pet update ===
        if self.pet:
            picked_item = self.pet.update(self.player, self.items, self.tile_map)
            if picked_item:
                if self.player.inventory.add_item(picked_item):
                    self.player.recalculate_stats()
                    if hasattr(self.ui, 'action_log'):
                        self.ui.action_log.add(f"Pet nhặt: {picked_item.name}!", (255, 230, 100))
                    self.particles.emit_pickup(picked_item.x, picked_item.y, picked_item.color)
                    sound.play("pickup")

        # Enemies update + effects
        for enemy in self.enemies:
            if enemy.alive:
                old_hp = self.player.hp
                enemy.update(self.player, self.tile_map, self.walkable_grid)
                dmg_taken = old_hp - self.player.hp
                if dmg_taken > 0:
                    self.ui.add_player_damage_text(self.player.x, self.player.y, dmg_taken, self.camera)
                    self.particles.emit_blood(self.player.x, self.player.y)
                    self.screen_fx.shake(4, 150)

        # Boss update + effects
        if self.boss and self.boss.alive:
            old_hp = self.player.hp
            self.boss.update(self.player, self.tile_map, self.walkable_grid)
            dmg_taken = old_hp - self.player.hp
            if dmg_taken > 0:
                self.ui.add_player_damage_text(self.player.x, self.player.y, dmg_taken, self.camera)
                self.particles.emit_blood(self.player.x, self.player.y)
                self.screen_fx.shake(6, 200)
            # Handle summons
            for etype, sx, sy in self.boss.get_pending_summons():
                from settings import DIFFICULTY_CONFIGS
                diff_cfg = DIFFICULTY_CONFIGS.get(self.difficulty)
                self.enemies.append(Enemy(sx, sy, etype, difficulty_cfg=diff_cfg))

        # BUG FIX: Reset attack hit flag khi attack kết thúc
        if not self.player.is_attacking:
            self.attack_hit_this_swing = False

        # Combat: player attack hits enemies (CHỈ 1 LẦN mỗi swing)
        if self.player.is_attacking and not self.attack_hit_this_swing:
            self._handle_player_attack()
            self.attack_hit_this_swing = True  # Đánh trúng rồi → không đánh nữa

        # BUG FIX: Reset AoE damage flag khi AoE kết thúc
        if not self.player.aoe_active:
            self.aoe_damage_dealt = False

        # Combat: player AoE hits enemies (damage 1 lần, visual vẫn chạy)
        if self.player.aoe_active and not self.aoe_damage_dealt:
            self._handle_player_aoe()
            self.aoe_damage_dealt = True

        # Check door (chuyển chương)
        if self.tile_map.is_door(self.player.x, self.player.y):
            self._update_quest_states()
            
            # Kiểm tra xem TẤT CẢ các nhiệm vụ (trừ reach_door) đã hoàn thành chưa
            quests = CHAPTER_QUESTS.get(self.chapter, [])
            all_completed = True
            for i, quest in enumerate(quests):
                if quest["type"] != "reach_door" and not self.quest_states.get(i, False):
                    all_completed = False
                    break
            
            if not all_completed:
                alive_enemies = sum(1 for e in self.enemies if e.alive)
                if alive_enemies > 0:
                    self.player.inventory.show_notification(f"Diệt sạch quái! (Còn {alive_enemies})")
                else:
                    self.player.inventory.show_notification("Chưa hoàn thành hết mục tiêu!")
                # Đẩy nhẹ player ra để không bị kẹt liên tục spam thông báo
                self.player.x -= self.player.facing[0] * 5
                self.player.y -= self.player.facing[1] * 5
            else:
                self._handle_chapter_complete()

        # Trigger special dialogue
        self._check_special_triggers()

        # Boss death → victory
        if self.boss and not self.boss.alive and self.chapter == 5 and not self.boss_loot_dropped:
            self.boss_loot_dropped = True
            loot = self.boss.drop_loot()
            if loot:
                self.items.append(loot)
            self.state = STATE_VICTORY

        # Dash particles
        if self.player.is_dashing:
            self.particles.emit_dash_trail(self.player.x, self.player.y)

        # Footstep particles
        if self.player.moving and not self.player.is_dashing:
            if random.random() < 0.15:
                self.particles.emit_footstep(self.player.x, self.player.y)

        # Ambient particles
        self.particles.emit_ambient(self.camera, self.chapter)

        # === Lifesteal projectile collision ===
        for proj in self.player.projectiles[:]:
            proj_rect = pygame.Rect(proj['x'] - 8, proj['y'] - 8, 16, 16)
            for enemy in self.enemies:
                if enemy.alive and id(enemy) not in proj['hit_ids']:
                    if proj_rect.colliderect(enemy.get_rect()):
                        proj['hit_ids'].add(id(enemy))
                        proj['pierce_left'] -= 1
                        died = enemy.take_damage(proj['damage'], 0, 0)
                        self.ui.add_damage_text(enemy.x, enemy.y, proj['damage'], False, self.camera)
                        self.particles.emit_blood(enemy.x, enemy.y)
                        heal_amt = int(proj['damage'] * proj['heal_rate'])
                        if heal_amt > 0:
                            self.player.heal(heal_amt)
                            self.ui.add_heal_text(self.player.x, self.player.y, heal_amt, self.camera)
                        if died:
                            self.particles.emit_death(enemy.x, enemy.y, enemy.color)
                            loot = enemy.drop_loot()
                            if loot:
                                self.items.append(loot)
            if self.boss and self.boss.alive and id(self.boss) not in proj['hit_ids']:
                if proj_rect.colliderect(self.boss.get_rect()):
                    proj['hit_ids'].add(id(self.boss))
                    proj['pierce_left'] -= 1
                    self.boss.take_damage(proj['damage'], 0, 0)
                    self.ui.add_damage_text(self.boss.x, self.boss.y, proj['damage'], False, self.camera)
                    heal_amt = int(proj['damage'] * proj['heal_rate'])
                    if heal_amt > 0:
                        self.player.heal(heal_amt)
                        self.ui.add_heal_text(self.player.x, self.player.y, heal_amt, self.camera)

        # === Spirit AI ===
        if self.player.spirit:
            sp = self.player.spirit
            now = pygame.time.get_ticks()
            # Find nearest enemy
            nearest = None
            nearest_dist = 9999
            for enemy in self.enemies:
                if enemy.alive:
                    d = distance_between(sp['x'], sp['y'], enemy.x, enemy.y)
                    if d < nearest_dist:
                        nearest_dist = d
                        nearest = enemy
            if self.boss and self.boss.alive:
                d = distance_between(sp['x'], sp['y'], self.boss.x, self.boss.y)
                if d < nearest_dist:
                    nearest_dist = d
                    nearest = self.boss
            # Move towards target
            if nearest:
                from ai import get_direction_towards
                dx, dy = get_direction_towards(sp['x'], sp['y'], nearest.x, nearest.y, SUMMON_SPEED)
                sp['x'] += dx
                sp['y'] += dy
                # Attack if close
                if nearest_dist < SUMMON_ATTACK_RANGE and now - sp['last_attack'] > SUMMON_ATTACK_CD:
                    sp['last_attack'] = now
                    if hasattr(nearest, 'take_damage'):
                        nearest.take_damage(sp['damage'], 0, 0)
                        self.ui.add_damage_text(nearest.x, nearest.y, sp['damage'], False, self.camera)
                        self.particles.emit_blood(nearest.x, nearest.y)

        # Update effects
        self.particles.emit_ambient(self.camera, self.chapter)
        self.particles.update()
        self.screen_fx.update()
        self.ui.update()

    def _handle_player_attack(self):
        """Xử lý tấn công thường đánh trúng quái."""
        atk_rect = self.player.get_attack_rect()
        # Combo multiplier áp dụng vào damage
        combo_multi = self.player.get_combo_multiplier()
        base_dmg, is_crit = self.player.calculate_damage()
        dmg = int(base_dmg * combo_multi)
        fx, fy = self.player.facing

        hit_something = False

        # Hit enemies
        for enemy in self.enemies:
            if enemy.alive and atk_rect.colliderect(enemy.get_rect()):
                died = enemy.take_damage(dmg, fx, fy)
                self.ui.add_damage_text(enemy.x, enemy.y, dmg, is_crit, self.camera)
                self.particles.emit_blood(enemy.x, enemy.y)
                hit_something = True
                if died:
                    self.particles.emit_death(enemy.x, enemy.y, enemy.color)
                    sound.play("enemy_death")
                    loot = enemy.drop_loot()
                    if loot:
                        self.items.append(loot)
                    # === EXP gain ===
                    exp_map = {"soul": SOUL_EXP, "minion": MINION_EXP, "shadow": SHADOW_EXP}
                    exp = exp_map.get(enemy.enemy_type, 10)
                    leveled = self.player.gain_exp(exp)
                    self.ui.action_log.add(f"+{exp} EXP", (200, 255, 100))
                    self.total_kills += 1
                    # === Death Slow-Mo ===
                    self.slow_mo_active = True
                    self.slow_mo_timer = pygame.time.get_ticks()
                    self.screen_fx.flash((255, 255, 200), 30)

        # Hit boss
        if self.boss and self.boss.alive and atk_rect.colliderect(self.boss.get_rect()):
            self.boss.take_damage(dmg, fx, fy)
            self.ui.add_damage_text(self.boss.x, self.boss.y, dmg, is_crit, self.camera)
            self.particles.emit_blood(self.boss.x, self.boss.y)
            self.screen_fx.shake(3, 100)
            hit_something = True
            sound.play("boss_hit")
            # === Boss dead → EXP ===
            if not self.boss.alive:
                sound.play("boss_roar")
                leveled = self.player.gain_exp(BOSS_EXP)
                self.ui.action_log.add(f"+{BOSS_EXP} EXP (BOSS)", (255, 200, 50))
                self.total_kills += 1
                self.slow_mo_active = True
                self.slow_mo_timer = pygame.time.get_ticks()

        # Hit crates
        for crate in getattr(self.tile_map, 'crates', []):
            if crate.alive and atk_rect.colliderect(crate.get_rect()):
                crate.hp -= dmg
                crate.hit_flash = 5
                hit_something = True
                sound.play("hit")
                if crate.hp <= 0:
                    crate.alive = False
                    from settings import DIFFICULTY_CONFIGS
                    diff_cfg = DIFFICULTY_CONFIGS.get(self.difficulty)
                    loot = generate_loot(crate.x, crate.y, is_crate=True, diff_cfg=diff_cfg)
                    if loot:
                        self.items.append(loot)

        # === Combo ===
        if hit_something:
            sound.play("crit" if is_crit else "hit")
            self.player.add_combo()

    def _handle_player_aoe(self):
        """Xử lý AoE 360° đánh trúng quái (chỉ gây damage 1 lần, visual vẫn chạy)."""
        aoe_dmg = int(self.player.damage * AOE_DAMAGE_MULTI)

        self.particles.emit_aoe_burst(self.player.x, self.player.y)
        self.screen_fx.flash((180, 80, 255), 40)

        for enemy in self.enemies:
            if enemy.alive:
                dist = distance_between(self.player.x, self.player.y, enemy.x, enemy.y)
                if dist < AOE_RADIUS:
                    dx = enemy.x - self.player.x
                    dy = enemy.y - self.player.y
                    d = max(dist, 0.1)
                    died = enemy.take_damage(aoe_dmg, dx / d, dy / d)
                    self.ui.add_damage_text(enemy.x, enemy.y, aoe_dmg, False, self.camera)
                    self.player.add_combo()
                    if died:
                        self.particles.emit_death(enemy.x, enemy.y, enemy.color)
                        sound.play("enemy_death")
                        loot = enemy.drop_loot()
                        if loot: self.items.append(loot)
                        exp_map = {"soul": SOUL_EXP, "minion": MINION_EXP, "shadow": SHADOW_EXP}
                        exp = exp_map.get(enemy.enemy_type, 10)
                        self.player.gain_exp(exp)
                        self.ui.action_log.add(f"+{exp} EXP", (200, 255, 100))
                        self.total_kills += 1
                        self.slow_mo_active = True
                        self.slow_mo_timer = pygame.time.get_ticks()

        # Hit crates (AoE)
        for crate in getattr(self.tile_map, 'crates', []):
            if crate.alive:
                dist = distance_between(self.player.x, self.player.y, crate.x, crate.y)
                if dist < AOE_RADIUS:
                    crate.hp -= aoe_dmg
                    crate.hit_flash = 5
                    if crate.hp <= 0:
                        crate.alive = False
                        from settings import DIFFICULTY_CONFIGS
                        diff_cfg = DIFFICULTY_CONFIGS.get(self.difficulty)
                        loot = generate_loot(crate.x, crate.y, is_crate=True, diff_cfg=diff_cfg)
                        if loot: self.items.append(loot)

        if self.boss and self.boss.alive:
            dist = distance_between(self.player.x, self.player.y, self.boss.x, self.boss.y)
            if dist < AOE_RADIUS:
                self.boss.take_damage(aoe_dmg, 0, 0)
                self.ui.add_damage_text(self.boss.x, self.boss.y, aoe_dmg, False, self.camera)
        # BUG FIX: KHÔNG tắt aoe_active ở đây → để visual effect chạy hết

    def pickup_items(self):
        """Nhặt đồ dưới đất và Corpse."""
        # Nhặt Corpse (Xác)
        for corpse in self.corpses[:]:
            if distance_between(self.player.x, self.player.y, corpse['x'], corpse['y']) < PLAYER_PICKUP_RANGE:
                # Trả lại đồ
                for item in corpse['items']:
                    self.player.inventory.add_item(item)
                self.player.recalculate_stats()
                if hasattr(self.ui, 'action_log'):
                    self.ui.action_log.add("Đã thu hồi đồ từ thi thể!", (100, 255, 100))
                self.particles.emit_heal(self.player.x, self.player.y)
                sound.play("pickup")
                self.corpses.remove(corpse)

        # Nhặt items thường
        for item in self.items:
            if item.picked_up:
                continue
            dist = distance_between(self.player.x, self.player.y, item.x, item.y)
            if dist < PLAYER_PICKUP_RANGE:
                if self.player.inventory.add_item(item):
                    self.player.recalculate_stats()
                    sound.play("pickup")
                    return True
        return False

    def _handle_chapter_complete(self):
        """Xử lý khi player chạm cửa chuyển chương."""
        if self.complete_triggered:
            return
        self.complete_triggered = True

        # Hồi HP khi hoàn thành chương (healing mechanic)
        heal_amount = int(self.player.max_hp * 0.3)
        self.player.heal(heal_amount)
        self.ui.add_heal_text(self.player.x, self.player.y, heal_amount, self.camera)

        # Show complete dialogue
        has_dialogue = False
        if self.chapter in CHAPTER_DIALOGUES:
            complete = CHAPTER_DIALOGUES[self.chapter].get("complete", [])
            if complete:
                self.dialogue_box.start(complete)
                self.state = STATE_DIALOGUE
                has_dialogue = True

        # Chuyển chương
        if self.chapter < 5:
            sound.play("door")
            if has_dialogue:
                self.chapter_advance_pending = True  # Chờ dialogue xong
            else:
                self.advance_chapter()  # Không có dialogue → chuyển ngay
        # Chapter 5 kết thúc bằng boss fight, không có door

    def advance_chapter(self):
        """Chuyển sang chương tiếp theo."""
        if self.chapter < 5:
            self.load_chapter(self.chapter + 1)

    def _update_quest_states(self):
        """Cập nhật trạng thái các quest hiện tại."""
        quests = CHAPTER_QUESTS.get(self.chapter, [])
        if not quests:
            return

        for i, quest in enumerate(quests):
            qtype = quest["type"]
            target = quest.get("target")

            if qtype == "kill_all" and target == "enemies":
                all_dead = all(not e.alive for e in self.enemies)
                if len(self.enemies) > 0 and all_dead:
                    self.quest_states[i] = True

            elif qtype == "find_npc" and target == "npc":
                if self.special_triggered or self.npc_dialogue_done:
                    self.quest_states[i] = True

            elif qtype == "reach_door" and target == "door":
                if self.complete_triggered:
                    self.quest_states[i] = True

            elif qtype == "kill_boss" and target == "boss":
                if self.boss and not self.boss.alive:
                    self.quest_states[i] = True

    def _check_special_triggers(self):
        """Kiểm tra trigger dialogue đặc biệt."""
        if self.special_triggered:
            return

        # Trigger khi đến gần NPC
        if self.tile_map.npc_positions:
            for npc_x, npc_y in self.tile_map.npc_positions:
                dist = distance_between(self.player.x, self.player.y, npc_x, npc_y)
                if dist < 80:
                    self.special_triggered = True
                    if self.chapter in CHAPTER_DIALOGUES:
                        special = CHAPTER_DIALOGUES[self.chapter].get("special", [])
                        if special:
                            self.dialogue_box.start(special)
                            self.state = STATE_DIALOGUE
                    break

        # Chapter 3: trigger truth midway
        if self.chapter == 3 and not self.special_triggered:
            alive_enemies = sum(1 for e in self.enemies if e.alive)
            total = len(self.enemies)
            if total > 0 and alive_enemies <= total // 2:
                self.special_triggered = True
                truth = CHAPTER_DIALOGUES[3].get("special", [])
                if truth:
                    self.dialogue_box.start(truth)
                    self.state = STATE_DIALOGUE

        # Chapter 4: trigger lyra dialogue khi đến gần door
        if self.chapter == 4 and not self.special_triggered and self.tile_map.door_pos:
            door_px = self.tile_map.door_pos[0] * TILE_SIZE
            door_py = self.tile_map.door_pos[1] * TILE_SIZE
            dist = distance_between(self.player.x, self.player.y, door_px, door_py)
            if dist < 150:
                self.special_triggered = True
                lyra = CHAPTER_DIALOGUES[4].get("lyra", [])
                if lyra:
                    self.dialogue_box.start(lyra)
                    self.state = STATE_DIALOGUE

    def _auto_play_update(self):
        """AI tự chơi — di chuyển, tấn công, dùng skill, nhặt đồ."""
        if not self.player.alive or self.player.inventory.is_open:
            return
        now = pygame.time.get_ticks()
        p = self.player
        from ai import get_direction_towards

        # --- Tìm mục tiêu: Ưu tiên Xác (Corpse) -> Quái -> Cửa ---
        target_x, target_y = None, None
        
        nearest_corpse = None
        nearest_corpse_dist = 9999
        for corpse in self.corpses:
            d = distance_between(p.x, p.y, corpse['x'], corpse['y'])
            if d < nearest_corpse_dist:
                nearest_corpse_dist = d
                nearest_corpse = corpse

        nearest_enemy = None
        nearest_dist = 9999
        alive_near_count = 0  # Đếm quái gần để quyết định AoE

        for enemy in self.enemies:
            if enemy.alive:
                d = distance_between(p.x, p.y, enemy.x, enemy.y)
                if d < nearest_dist:
                    nearest_dist = d
                    nearest_enemy = enemy
                if d < 120:
                    alive_near_count += 1

        if self.boss and self.boss.alive:
            d = distance_between(p.x, p.y, self.boss.x, self.boss.y)
            if d < nearest_dist:
                nearest_dist = d
                nearest_enemy = self.boss
            if d < 120:
                alive_near_count += 1

        # --- Tìm item gần nhất ---
        nearest_item = None
        nearest_item_dist = 9999
        for item in self.items:
            if not item.picked_up:
                d = distance_between(p.x, p.y, item.x, item.y)
                if d < nearest_item_dist:
                    nearest_item_dist = d
                    nearest_item = item

        # --- Nhặt item nếu rất gần ---
        if nearest_item and nearest_item_dist < 50:
            # Code nhặt đồ giống nút F
            from settings import EQUIP_GOLD, EQUIP_POTION_HP, EQUIP_POTION_MP
            if nearest_item.equip_type == EQUIP_GOLD:
                p.pickup_gold(nearest_item.amount)
                nearest_item.picked_up = True
            elif nearest_item.equip_type == EQUIP_POTION_HP:
                p.health_potions += 1
                self.ui.action_log.add("+1 Bình Máu", RED)
                nearest_item.picked_up = True
            elif nearest_item.equip_type == EQUIP_POTION_MP:
                p.mana_potions += 1
                self.ui.action_log.add("+1 Bình Năng Lượng", (100, 150, 255))
                nearest_item.picked_up = True
            else:
                if p.inventory.add_item(nearest_item):
                    p.recalculate_stats()
                    import sound
                    sound.play("item")

        # --- Tự động trang bị đồ tốt hơn ---
        rarity_val = {"Common": 1, "Rare": 2, "Epic": 3}
        for i, bag_item in enumerate(p.inventory.bag):
            if bag_item:
                slot = bag_item.equip_type
                if slot in p.inventory.equipped:
                    equipped_item = p.inventory.equipped[slot]
                    if not equipped_item or rarity_val.get(bag_item.rarity, 0) > rarity_val.get(equipped_item.rarity, 0):
                        delta = p.inventory.equip_item(i)
                        if delta:
                            p.recalculate_stats()

        # --- Dùng skill thông minh (Chỉ dùng khi có quái) ---
        if nearest_enemy:
            hp_ratio = p.hp / p.max_hp if p.max_hp > 0 else 1

            # Shield khi HP thấp
            if hp_ratio < 0.5 and not p.shield_active and p.level >= SKILL_UNLOCK_LEVELS.get("Z", 1):
                p.use_shield()

            # Summon spirit nếu chưa có
            if p.spirit is None and p.level >= SKILL_UNLOCK_LEVELS.get("C", 1):
                p.use_summon()

            # AoE khi nhiều quái gần (>= 2)
            if alive_near_count >= 2 and nearest_dist < 100 and p.level >= SKILL_UNLOCK_LEVELS.get("R", 1):
                p.use_aoe()

            # Lifesteal khi có quái trong tầm
            if nearest_dist < 200 and p.level >= SKILL_UNLOCK_LEVELS.get("X", 1):
                p.use_lifesteal()

        # --- Di chuyển ---
        target_x, target_y = None, None

        # --- Tìm NPC gần nhất ---
        nearest_npc = None
        nearest_npc_dist = 9999
        if not self.special_triggered and self.tile_map.npc_positions:
            for npc_x, npc_y in self.tile_map.npc_positions:
                d = distance_between(p.x, p.y, npc_x, npc_y)
                if d < nearest_npc_dist:
                    nearest_npc_dist = d
                    nearest_npc = (npc_x, npc_y)

        # --- Lựa chọn mục tiêu di chuyển ---
        if nearest_corpse:
            target_x, target_y = nearest_corpse['x'], nearest_corpse['y']
        elif nearest_enemy and nearest_dist > 40:
            # Đi về phía quái ưu tiên số 1
            target_x, target_y = nearest_enemy.x, nearest_enemy.y
        elif nearest_npc and not nearest_enemy:
            # Đi tìm NPC / Mục tiêu ẩn
            target_x, target_y = nearest_npc[0], nearest_npc[1]
        elif nearest_item and not nearest_enemy:
            # Đã diệt sạch quái → đi nhặt TẤT CẢ đồ trên map
            target_x, target_y = nearest_item.x, nearest_item.y
        elif not nearest_enemy and self.tile_map.door_pos:
            # Không quái, không đồ → đi tới cửa
            dx_door = self.tile_map.door_pos[0] * TILE_SIZE + TILE_SIZE // 2
            dy_door = self.tile_map.door_pos[1] * TILE_SIZE + TILE_SIZE // 2
            target_x, target_y = dx_door, dy_door

        if target_x is not None:
            # Dùng A* để tránh kẹt tường
            from ai import astar_find_path
            
            # Cập nhật đường đi mỗi 300ms
            if now - self.auto_play_path_timer > 300 or not self.auto_play_path:
                self.auto_play_path_timer = now
                path_result = astar_find_path(
                    p.x, p.y, target_x, target_y, 
                    self.walkable_grid if self.walkable_grid else self.tile_map.get_walkable_grid()
                )
                self.auto_play_path = path_result[0] if path_result else []
            
            # Nếu có đường đi, hướng tới waypoint đầu tiên
            next_x, next_y = target_x, target_y
            if self.auto_play_path:
                next_x, next_y = self.auto_play_path[0]
                d_waypoint = distance_between(p.x, p.y, next_x, next_y)
                if d_waypoint < p.speed * 1.5:
                    self.auto_play_path.pop(0)
                    if self.auto_play_path:
                        next_x, next_y = self.auto_play_path[0]

            dx, dy = get_direction_towards(p.x, p.y, next_x, next_y, p.speed)
            # Giảm kích thước hitbox một chút để AI không bị kẹt góc khi đi chéo
            half = p.size // 2 - 4 
            new_x = p.x + dx
            new_y = p.y + dy
            if self.tile_map.is_walkable(new_x - half, p.y) and self.tile_map.is_walkable(new_x + half, p.y):
                p.x = new_x
            if self.tile_map.is_walkable(p.x, new_y - half) and self.tile_map.is_walkable(p.x, new_y + half):
                p.y = new_y
            
            p.moving = (dx != 0 or dy != 0)
            
            # Cập nhật facing
            move_dx = target_x - p.x
            move_dy = target_y - p.y
            if abs(move_dx) > abs(move_dy):
                p.facing = (1, 0) if move_dx > 0 else (-1, 0)
            else:
                p.facing = (0, 1) if move_dy > 0 else (0, -1)
        else:
            p.moving = False

        # --- Tấn công khi đủ gần ---
        if nearest_enemy and nearest_dist < 50:
            # Dash vào rồi đánh
            if nearest_dist > 35:
                p.dash()
            if now - self.auto_play_attack_timer > 250:
                self.auto_play_attack_timer = now
                p.attack()

    def handle_event(self, event):
        """Xử lý events (input, timer)."""
        if self.state == STATE_MENU:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.state = STATE_DIFFICULTY_SELECT
                elif event.key == pygame.K_c and os.path.exists("save.json"):
                    if load_game(self):
                        self.state = STATE_PLAYING
                elif event.key == pygame.K_s:
                    self.state = STATE_SETTINGS
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # Nút bắt đầu
                start_rect = pygame.Rect(SCREEN_WIDTH // 2 - 130, 408, 260, 42)
                if start_rect.collidepoint(mx, my):
                    self.state = STATE_DIFFICULTY_SELECT
                    return
                # Nút Tiếp tục (nếu có save)
                if os.path.exists("save.json"):
                    cont_rect = pygame.Rect(SCREEN_WIDTH // 2 - 130, 460, 260, 42)
                    if cont_rect.collidepoint(mx, my):
                        if load_game(self):
                            self.state = STATE_PLAYING
                        return
                # Nút Cài đặt
                settings_y = 512 if os.path.exists("save.json") else 460
                settings_rect = pygame.Rect(SCREEN_WIDTH // 2 - 130, settings_y, 260, 42)
                if settings_rect.collidepoint(mx, my):
                    self.state = STATE_SETTINGS
            return

        if self.state == STATE_DIFFICULTY_SELECT:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # Close button
                close_rect = pygame.Rect(SCREEN_WIDTH // 2 + 300, SCREEN_HEIGHT // 2 - 220, 40, 40)
                if close_rect.collidepoint(mx, my):
                    self.state = STATE_MENU
                    return
                # Difficulty cards
                from settings import DIFFICULTY_CONFIGS
                cards = list(DIFFICULTY_CONFIGS.keys())
                card_w, card_h = 160, 240
                gap = 20
                total_w = len(cards) * card_w + (len(cards) - 1) * gap
                start_x = SCREEN_WIDTH // 2 - total_w // 2
                cy = SCREEN_HEIGHT // 2 - 50
                for i, diff in enumerate(cards):
                    rect = pygame.Rect(start_x + i * (card_w + gap), cy, card_w, card_h)
                    if rect.collidepoint(mx, my):
                        self.difficulty = diff
                        self.start_new_game()
                        return
            return

        if self.state == STATE_SETTINGS:
            rects = self.ui.get_settings_rects(SCREEN_WIDTH, SCREEN_HEIGHT)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = STATE_MENU if self.player is None else STATE_PAUSE
                    self._dragging_sfx = False
                    self._dragging_bgm = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                # Close button
                if rects['close'].collidepoint(mx, my):
                    self.state = STATE_MENU if self.player is None else STATE_PAUSE
                # Mute buttons
                elif rects['sfx_mute'].collidepoint(mx, my):
                    self.sfx_muted = not self.sfx_muted
                    sound.SFX_VOLUME = 0.0 if self.sfx_muted else 0.45
                elif rects['bgm_mute'].collidepoint(mx, my):
                    self.bgm_muted = not self.bgm_muted
                    sound.MUSIC_VOLUME = 0.0 if self.bgm_muted else 0.20
                    sound.set_music_volume(sound.MUSIC_VOLUME)
                # Start drag on track
                elif rects['sfx_track'].inflate(0, 20).collidepoint(mx, my):
                    self._dragging_sfx = True
                elif rects['bgm_track'].inflate(0, 20).collidepoint(mx, my):
                    self._dragging_bgm = True
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self._dragging_sfx = False
                self._dragging_bgm = False
            elif event.type == pygame.MOUSEMOTION:
                mx, my = event.pos
                if self._dragging_sfx:
                    tr = rects['sfx_track']
                    ratio = max(0.0, min(1.0, (mx - tr.x) / tr.width))
                    sound.SFX_VOLUME = round(ratio, 2)
                    self.sfx_muted = (ratio == 0.0)
                elif self._dragging_bgm:
                    tr = rects['bgm_track']
                    ratio = max(0.0, min(1.0, (mx - tr.x) / tr.width))
                    sound.MUSIC_VOLUME = round(ratio, 2)
                    self.bgm_muted = (ratio == 0.0)
                    sound.set_music_volume(sound.MUSIC_VOLUME)
            return

        if self.state in (STATE_CHAPTER_INTRO, STATE_DIALOGUE):
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self.dialogue_box.active:
                    self.dialogue_box.advance()
                elif self.state == STATE_CHAPTER_INTRO:
                    self.state = STATE_PLAYING
            return

        if self.state == STATE_PLAYING:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    self.auto_play = not self.auto_play
                elif event.key == pygame.K_F3:
                    self.debug_ai = not self.debug_ai
                elif event.key == pygame.K_h and getattr(self, 'debug_ai', False):
                    import ai
                    types = ["manhattan", "euclidean", "dijkstra"]
                    curr_idx = types.index(ai.CURRENT_HEURISTIC)
                    ai.CURRENT_HEURISTIC = types[(curr_idx + 1) % len(types)]
                    if hasattr(self.ui, 'action_log'):
                        self.ui.action_log.add(f"Heuristic: {ai.CURRENT_HEURISTIC.upper()}", (255, 255, 100))
                elif event.key == pygame.K_ESCAPE:
                    self.state = STATE_PAUSE
                elif event.key == pygame.K_SPACE:
                    if self.dialogue_box.active:
                        self.dialogue_box.advance()
                    else:
                        self.player.attack()
                elif event.key == pygame.K_1:
                    success, amount = self.player.use_health_potion()
                    if success:
                        self.ui.add_heal_text(self.player.x, self.player.y, amount, self.camera)
                elif event.key == pygame.K_2:
                    success, amount = self.player.use_mana_potion()
                    if success:
                        self.ui.add_floating_text(self.player.x, self.player.y, f"+{amount} MP", (100, 150, 255), self.camera, True)
                elif event.key == pygame.K_q:
                    self.player.dash()
                elif event.key == pygame.K_r:
                    self.player.use_aoe()
                elif event.key == pygame.K_z:
                    self.player.use_shield()
                elif event.key == pygame.K_x:
                    self.player.use_lifesteal()
                elif event.key == pygame.K_c:
                    self.player.use_summon()
                elif event.key == pygame.K_f:
                    self.pickup_items()
                elif event.key == pygame.K_i:
                    self.player.inventory.toggle()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.player.inventory.is_open:
                    mx, my = event.pos
                    delta = self.player.inventory.handle_click(mx, my)
                    if delta:
                        self.player.recalculate_stats()
            elif event.type == pygame.MOUSEMOTION:
                if self.player.inventory.is_open:
                    self.player.inventory.update_hover(*event.pos)
            return

        if self.state == STATE_PAUSE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = STATE_PLAYING
                elif event.key == pygame.K_s:
                    self.state = STATE_SETTINGS
                elif event.key == pygame.K_f:
                    save_game(self)
                    if hasattr(self.ui, 'action_log'):
                        self.ui.action_log.add("Game Saved!", YELLOW)
                    self.state = STATE_PLAYING
                elif event.key == pygame.K_q:
                    return "QUIT"
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                cx, cy = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
                # Danh sách nút Pause (khớp với vị trí trong _render_pause)
                resume_rect  = pygame.Rect(cx - 120, cy + 5,  240, 34)
                save_rect    = pygame.Rect(cx - 120, cy + 44, 240, 34)
                settings_rect = pygame.Rect(cx - 120, cy + 83, 240, 34)
                quit_rect    = pygame.Rect(cx - 120, cy + 122, 240, 34)
                if resume_rect.collidepoint(mx, my):
                    self.state = STATE_PLAYING
                elif save_rect.collidepoint(mx, my):
                    save_game(self)
                    if hasattr(self.ui, 'action_log'):
                        self.ui.action_log.add("Game Saved!", YELLOW)
                    self.state = STATE_PLAYING
                elif settings_rect.collidepoint(mx, my):
                    self.state = STATE_SETTINGS
                elif quit_rect.collidepoint(mx, my):
                    return "QUIT"
            return

        if self.state == STATE_GAME_OVER:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.respawn_player()
                elif event.key == pygame.K_q:
                    return "QUIT"
            return

        if self.state == STATE_VICTORY:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_RETURN, pygame.K_SPACE, pygame.K_ESCAPE]:
                    self.state = STATE_CREDITS
            return

        if self.state == STATE_ENDING:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE]:
                    if self.dialogue_box.active:
                        self.dialogue_box.advance()
                    else:
                        self.state = STATE_CREDITS
            return

        if self.state == STATE_CREDITS:
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE]:
                    self.state = STATE_MENU
                    self.auto_play = False
                elif event.key == pygame.K_n:
                    # Bắt đầu New Game+
                    self.ng_plus = True
                    self.ng_plus_count += 1
                    self.start_new_game()
                    self.state = STATE_PLAYING
            return

    def render(self, surface):
        """Render toàn bộ game — enhanced visuals."""
        self._init_fonts()

        if self.state == STATE_MENU or (self.state == STATE_SETTINGS and self.player is None) or self.state == STATE_DIFFICULTY_SELECT:
            self._render_menu(surface)
            if self.state == STATE_SETTINGS:
                self._render_settings(surface)
            elif self.state == STATE_DIFFICULTY_SELECT:
                self._render_difficulty_select(surface)
            return

        # Nền
        surface.fill((8, 4, 14))

        if self.state in (STATE_PLAYING, STATE_PAUSE, STATE_SETTINGS, STATE_CHAPTER_INTRO,
                          STATE_DIALOGUE, STATE_GAME_OVER, STATE_VICTORY, STATE_ENDING):
            # Apply screen shake offset
            shake_x, shake_y = self.screen_fx.get_offset()
            self.camera.shake_offset_x = shake_x
            self.camera.shake_offset_y = shake_y

            # Render game world
            if self.tile_map:
                self.tile_map.render(surface, self.camera)

            # Items
            for item in self.items:
                if not item.picked_up and self.camera.is_visible(item.x, item.y):
                    item.render(surface, self.camera)

            # Xác (Corpse)
            for corpse in self.corpses:
                if self.camera.is_visible(corpse['x'], corpse['y']):
                    cx, cy = self.camera.apply(corpse['x'], corpse['y'])
                    # Vẽ biểu tượng mộ bia
                    pygame.draw.circle(surface, (100, 30, 30), (int(cx), int(cy)), 10)
                    pygame.draw.circle(surface, (255, 100, 100), (int(cx), int(cy)), 10, 2)
                    now = pygame.time.get_ticks()
                    float_y = int(4 * math.sin(now * 0.005))
                    tomb_text = self._font.render("RIP", True, (255, 150, 150))
                    surface.blit(tomb_text, (int(cx) - tomb_text.get_width()//2, int(cy) - 25 + float_y))

            # NPC markers — enhanced with glow
            now = pygame.time.get_ticks()
            if self.tile_map:
                for npc_x, npc_y in self.tile_map.npc_positions:
                    if self.camera.is_visible(npc_x, npc_y):
                        nx, ny = self.camera.apply(npc_x, npc_y)
                        # Glow halo
                        glow_r = 20 + int(5 * math.sin(now * 0.004))
                        glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                        glow_a = int(30 + 15 * math.sin(now * 0.003))
                        pygame.draw.circle(glow_surf, (255, 220, 80, glow_a),
                                           (glow_r, glow_r), glow_r)
                        surface.blit(glow_surf, (nx - glow_r, ny - glow_r))
                        # Diamond body
                        pygame.draw.polygon(surface, (255, 230, 100), [
                            (nx, ny - 14), (nx + 8, ny), (nx, ny + 14), (nx - 8, ny)])
                        pygame.draw.polygon(surface, (255, 180, 50), [
                            (nx, ny - 14), (nx + 8, ny), (nx, ny + 14), (nx - 8, ny)], 2)
                        # "!" floating marker
                        if not self.special_triggered:
                            bounce = int(3 * math.sin(now * 0.005))
                            shadow = self._big_font.render("!", True, (60, 50, 20))
                            surface.blit(shadow, (nx - 4, ny - 33 + bounce))
                            text = self._big_font.render("!", True, YELLOW)
                            surface.blit(text, (nx - 5, ny - 34 + bounce))

            # Enemies
            for enemy in self.enemies:
                enemy.render(surface, self.camera)

            # Boss
            if self.boss:
                self.boss.render(surface, self.camera)

            # --- DEBUG AI (Pathfinding Visualizer) ---
            if self.debug_ai:
                debug_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                
                def draw_visited(visited, color, alpha=80):
                    if not visited: return
                    for vx, vy in visited:
                        wx, wy = vx * TILE_SIZE, vy * TILE_SIZE
                        if self.camera.is_visible(wx, wy):
                            cx, cy = self.camera.apply(wx, wy)
                            pygame.draw.rect(debug_surf, (*color, alpha), (cx, cy, TILE_SIZE, TILE_SIZE))
                            pygame.draw.rect(debug_surf, (*color, 180), (cx, cy, TILE_SIZE, TILE_SIZE), 1)

                def draw_path(path):
                    if not path or len(path) < 2: return
                    pts = []
                    for px, py in path:
                        if self.camera.is_visible(px, py):
                            cx, cy = self.camera.apply(px, py)
                            pts.append((cx, cy))
                    if len(pts) > 1:
                        pygame.draw.lines(debug_surf, (0, 255, 0, 200), False, pts, 3)

                for enemy in self.enemies:
                    if not enemy.alive: continue
                    color = (200, 0, 200) if enemy.ai_type == "dfs" else (0, 100, 255) if enemy.ai_type == "bfs" else (255, 200, 0)
                    if hasattr(enemy, 'visited'): draw_visited(enemy.visited, color)
                    if hasattr(enemy, 'path'): draw_path(enemy.path)
                
                if self.boss and self.boss.alive:
                    if hasattr(self.boss, 'visited'): draw_visited(self.boss.visited, (255, 200, 0))
                    if hasattr(self.boss, 'path'): draw_path(self.boss.path)
                
                surface.blit(debug_surf, (0, 0))
                
                import ai
                h_text = self._small_font.render(f"A* Heuristic (Nhấn H): {ai.CURRENT_HEURISTIC.upper()}", True, (255, 255, 100))
                h_bg = pygame.Surface((h_text.get_width() + 16, h_text.get_height() + 8), pygame.SRCALPHA)
                h_bg.fill((0, 0, 0, 180))
                pygame.draw.rect(h_bg, (255, 255, 100, 100), (0, 0, h_bg.get_width(), h_bg.get_height()), 1)
                hx = SCREEN_WIDTH // 2 - h_bg.get_width() // 2
                hy = 80
                surface.blit(h_bg, (hx, hy))
                surface.blit(h_text, (hx + 8, hy + 4))

            # Particles (world space)
            self.particles.render(surface, self.camera)

            # Pet
            if self.pet:
                self.pet.render(surface, self.camera)

            # Player
            self.player.render(surface, self.camera)

            # Vignette + flash
            self.screen_fx.apply(surface)

            # --- Ánh sáng động (Dynamic Lighting / Dark Mode) ---
            light_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            light_mask.fill((6, 4, 12, 220))  # Màn đêm u ám

            def draw_light(x, y, max_radius, intensity=255):
                hole = pygame.Surface((max_radius * 2, max_radius * 2), pygame.SRCALPHA)
                for r in range(max_radius, 0, -4):
                    alpha = int(intensity * (1 - r / max_radius))
                    pygame.draw.circle(hole, (255, 255, 255, alpha), (max_radius, max_radius), r)
                light_mask.blit(hole, (int(x) - max_radius, int(y) - max_radius), special_flags=pygame.BLEND_RGBA_SUB)

            # Sáng quanh Kael
            px_scr, py_scr = self.camera.apply(self.player.x, self.player.y)
            draw_light(px_scr, py_scr, 250, 255)

            # Sáng quanh quái
            for enemy in self.enemies:
                if enemy.alive and self.camera.is_visible(enemy.x, enemy.y):
                    ex, ey = self.camera.apply(enemy.x, enemy.y)
                    draw_light(ex, ey, 60, 180)
                    
            if self.boss and self.boss.alive and self.camera.is_visible(self.boss.x, self.boss.y):
                bx, by = self.camera.apply(self.boss.x, self.boss.y)
                draw_light(bx, by, 200, 255)
                
            # Đục lỗ sáng quanh cửa (door) nếu có
            if self.tile_map.door_pos:
                dx, dy = self.tile_map.door_pos
                if self.camera.is_visible(dx * TILE_SIZE, dy * TILE_SIZE):
                    sx, sy = self.camera.apply(dx * TILE_SIZE + TILE_SIZE//2, dy * TILE_SIZE + TILE_SIZE//2)
                    draw_light(sx, sy, 120, 200)

            surface.blit(light_mask, (0, 0))

            # HUD
            self.ui.render_hud(surface, self.player, self.chapter)
            self.ui.render_exp_bar(surface, self.player)
            self.ui.render_minimap(surface, self.tile_map, self.player,
                                   self.enemies, self.boss, self.items)
            self.ui.render_quest_tracker(surface, self.chapter, self.quest_states)
            if self.boss and self.boss.alive:
                self.ui.render_boss_hp_bar(surface, self.boss)

            # AI debug overlay (vẽ trước HUD)
            if self.debug_ai:
                self.ui.render_algo_overlay(
                    surface, self.enemies, self.boss, self.camera, self.tile_map)
                self.ui.render_ai_legend(surface)

            # Auto-play indicator
            if self.auto_play:
                now = pygame.time.get_ticks()
                pulse = int(180 + 75 * math.sin(now * 0.005))
                ap_font = self._big_font if self._big_font else pygame.font.SysFont("consolas", 24, bold=True)
                ap_text = ap_font.render("⚡ AUTO-PLAY [P]", True, (pulse, 255, 100))
                ap_bg = pygame.Surface((ap_text.get_width() + 16, ap_text.get_height() + 8), pygame.SRCALPHA)
                ap_bg.fill((10, 30, 10, 160))
                pygame.draw.rect(ap_bg, (50, 200, 80, 180), (0, 0, ap_bg.get_width(), ap_bg.get_height()), 1, 6)
                surface.blit(ap_bg, (SCREEN_WIDTH // 2 - ap_bg.get_width() // 2, 38))
                surface.blit(ap_text, (SCREEN_WIDTH // 2 - ap_text.get_width() // 2, 42))

            # Inventory overlay
            self.player.inventory.render(surface)

            # Dialogue
            self.dialogue_box.render(surface)

        # Overlays
        if self.state == STATE_CHAPTER_INTRO:
            elapsed = pygame.time.get_ticks() - self.intro_timer
            alpha = max(0, 255 - int(255 * elapsed / self.intro_duration))
            self.ui.render_chapter_title(surface, self.chapter, alpha)

        elif self.state == STATE_PAUSE:
            self._render_pause(surface)

        elif self.state == STATE_SETTINGS:
            self.ui.render_settings_mouse(
                surface, sound.SFX_VOLUME, sound.MUSIC_VOLUME,
                self.sfx_muted, self.bgm_muted)

        elif self.state == STATE_GAME_OVER:
            self._render_game_over(surface)

        elif self.state == STATE_VICTORY:
            self._render_victory(surface)

        elif self.state == STATE_ENDING:
            pass

        elif self.state == STATE_CREDITS:
            self._render_credits(surface)

    def _render_menu(self, surface):
        """Vẽ menu chính — cinematic design."""
        if sound._current_chapter_music != "menu":
            sound.play_music("menu")

        self.menu_time += 1
        t = self.menu_time

        # Gradient background
        for y in range(SCREEN_HEIGHT):
            progress = y / SCREEN_HEIGHT
            r = int(8 + 10 * progress)
            g = int(4 + 3 * progress)
            b = int(18 + 12 * progress)
            pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

        # Star field
        for i in range(40):
            h = ((i * 73856093 + i * 19349663) ^ (i * 83492791)) & 0xFFFFFFFF
            sx = h % SCREEN_WIDTH
            sy = (h >> 10) % SCREEN_HEIGHT
            blink = 0.5 + 0.5 * math.sin(t * 0.01 + i * 0.7)
            star_a = int(30 + 50 * blink)
            star_surf = pygame.Surface((3, 3), pygame.SRCALPHA)
            star_surf.fill((200, 180, 255, star_a))
            surface.blit(star_surf, (sx, sy))

        # Ember particles
        for i in range(15):
            seed = i * 37
            px = (seed * 97 + int(t * (0.5 + i * 0.1))) % SCREEN_WIDTH
            py = SCREEN_HEIGHT - (int(t * (0.8 + i * 0.15) + seed * 43) % (SCREEN_HEIGHT + 100))
            ember_a = int(50 + 40 * math.sin(t * 0.02 + i * 1.3))
            size = 2 + (seed % 3)
            er, eg, eb = 255, 120 + (seed % 80), 30 + (seed % 40)
            ember_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(ember_surf, (er, eg, eb, ember_a), (size, size), size)
            surface.blit(ember_surf, (px, py))

        # Decorative line
        cy = 155
        line_w = 400
        line_surf = pygame.Surface((line_w, 1), pygame.SRCALPHA)
        for i in range(line_w):
            prog = i / line_w
            a = int(60 * (1 - abs(prog - 0.5) * 2))
            line_surf.set_at((i, 0), (140, 100, 200, a))
        surface.blit(line_surf, (SCREEN_WIDTH // 2 - line_w // 2, cy))

        # Title
        title_text = "ASHES OF THE FALLEN"
        ty = 170
        glow_pulse = 0.5 + 0.5 * math.sin(t * 0.025)
        glow_surf = self._title_font.render(title_text, True, (120, 60, 200))
        glow_surf.set_alpha(int(25 + 20 * glow_pulse))
        gx = SCREEN_WIDTH // 2 - glow_surf.get_width() // 2
        for ox, oy in [(-3, -3), (3, -3), (-3, 3), (3, 3)]:
            surface.blit(glow_surf, (gx + ox, ty + oy))
        shadow = self._title_font.render(title_text, True, (30, 15, 50))
        surface.blit(shadow, (gx + 2, ty + 2))
        main_r = int(200 + 30 * math.sin(t * 0.02))
        main_g = int(170 + 20 * math.sin(t * 0.025 + 1))
        title = self._title_font.render(title_text, True, (main_r, main_g, 255))
        surface.blit(title, (gx, ty))

        # Subtitle
        sub = self._big_font.render("Tàn Tro Của Những Kẻ Sa Ngã", True, (140, 130, 175))
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, ty + 62))
        surface.blit(line_surf, (SCREEN_WIDTH // 2 - line_w // 2, ty + 95))

        # Lore text
        lore_lines = [
            "Vương quốc Valdris chìm trong bóng tối vĩnh cửu...",
            "Kael Duskborne — cựu Pháp Sư Hắc Ám, kẻ gây ra Đêm Tận Thế.",
            "Giờ đây, anh tìm cách chuộc lỗi... bằng mọi giá.",
        ]
        for i, line in enumerate(lore_lines):
            fade = min(255, max(0, (t - i * 30) * 4))
            text = self._small_font.render(line, True, (110, 100, 140))
            text.set_alpha(int(fade))
            surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 310 + i * 24))

        # Menu buttons
        has_save = os.path.exists("save.json")
        mx_cur, my_cur = pygame.mouse.get_pos()

        def draw_menu_btn(label, rect, base_color, hover_color, icon_fn=None):
            hovered = rect.collidepoint(mx_cur, my_cur)
            col = hover_color if hovered else base_color
            btn_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            btn_surf.fill((*col, 200))
            pygame.draw.rect(btn_surf, (200, 190, 255, 220), (0, 0, rect.width, rect.height), 2, 10)
            if hovered:
                glow = pygame.Surface((rect.width + 12, rect.height + 12), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*col, 40), (0, 0, glow.get_width(), glow.get_height()), 0, 12)
                surface.blit(glow, (rect.x - 6, rect.y - 6))
            surface.blit(btn_surf, (rect.topleft))
            
            # Vẽ icon nếu có
            text_x = rect.x + rect.width // 2
            if icon_fn:
                ix = rect.x + 20
                iy = rect.y + rect.height // 2 - 10
                icon_fn(surface, ix, iy, 20, (240, 235, 255) if hovered else (200, 195, 230))
                # text_x lùi lại xíu
                text_x += 10
                
            txt = self._big_font.render(label, True, (240, 235, 255) if hovered else (200, 195, 230))
            surface.blit(txt, (text_x - txt.get_width() // 2,
                               rect.y + rect.height // 2 - txt.get_height() // 2))

        cx_btn = SCREEN_WIDTH // 2 - 130
        draw_menu_btn("Bắt Đầu",  pygame.Rect(cx_btn, 408, 260, 42), (40, 28, 70), (80, 50, 130), icon_fn=icons.draw_sword)
        if has_save:
            draw_menu_btn("Tiếp Tục", pygame.Rect(cx_btn, 460, 260, 42), (28, 40, 70), (40, 70, 140), icon_fn=icons.draw_refresh)
            draw_menu_btn("Cài Đặt",  pygame.Rect(cx_btn, 512, 260, 42), (25, 35, 55), (45, 60, 100), icon_fn=icons.draw_gear)
        else:
            draw_menu_btn("Cài Đặt",  pygame.Rect(cx_btn, 460, 260, 42), (25, 35, 55), (45, 60, 100), icon_fn=icons.draw_gear)

        # Controls hint (small, below buttons)
        ctrl_panel = pygame.Surface((520, 50), pygame.SRCALPHA)
        ctrl_panel.fill((15, 10, 30, 100))
        pygame.draw.rect(ctrl_panel, (60, 50, 90, 120), (0, 0, 520, 50), 1, 8)
        surface.blit(ctrl_panel, (SCREEN_WIDTH // 2 - 260, 575))
        controls = [
            ("WASD", "Di chuyển"), ("SPACE", "Tấn công"), ("Q", "Dash"),
            ("R", "AoE"), ("F", "Nhặt đồ"), ("I", "Inv"), ("ESC", "Pause"),
        ]
        for i, (key, desc) in enumerate(controls):
            kx = SCREEN_WIDTH // 2 - 240 + i * 73
            key_text = self._small_font.render(key, True, YELLOW)
            surface.blit(key_text, (kx, 583))
            desc_text = self._small_font.render(desc, True, (90, 85, 120))
            surface.blit(desc_text, (kx, 597))

        ver = self._small_font.render("v1.0 — Pygame 2D RPG", True, (50, 45, 70))
        surface.blit(ver, (SCREEN_WIDTH - ver.get_width() - 10, SCREEN_HEIGHT - 20))

    def _render_pause(self, surface):
        """Vẽ màn hình pause với các nút click."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        pw, ph = 320, 270
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((15, 12, 30, 210))
        pygame.draw.rect(panel, (100, 80, 160, 180), (0, 0, pw, ph), 2, 12)
        for i in range(3):
            pygame.draw.line(panel, (160, 140, 220, 30 - i * 10), (8, i + 2), (pw - 8, i + 2))
        px = SCREEN_WIDTH // 2 - pw // 2
        py_panel = SCREEN_HEIGHT // 2 - ph // 2
        surface.blit(panel, (px, py_panel))

        title = self._title_font.render("PAUSE", True, (200, 190, 240))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2,
                             py_panel + 16))

        sep_w = 200
        sep = pygame.Surface((sep_w, 1), pygame.SRCALPHA)
        for i in range(sep_w):
            a = int(80 * (1 - abs(i / sep_w - 0.5) * 2))
            sep.set_at((i, 0), (140, 120, 200, a))
        surface.blit(sep, (SCREEN_WIDTH // 2 - sep_w // 2, py_panel + 70))

        cx = SCREEN_WIDTH // 2
        cy = SCREEN_HEIGHT // 2
        mx_cur, my_cur = pygame.mouse.get_pos()

        def draw_pause_btn(label, rect, base_col, hover_col, icon_fn=None):
            hov = rect.collidepoint(mx_cur, my_cur)
            col = hover_col if hov else base_col
            btn = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            btn.fill((*col, 200))
            pygame.draw.rect(btn, (180, 170, 220, 180), (0, 0, rect.width, rect.height), 1, 8)
            surface.blit(btn, (rect.topleft))
            
            text_x = rect.x + rect.width // 2
            if icon_fn:
                ix = rect.x + 20
                iy = rect.y + rect.height // 2 - 10
                icon_fn(surface, ix, iy, 20, (240, 235, 255) if hov else (185, 180, 220))
                text_x += 10
            
            txt = self._font.render(label, True, (240, 235, 255) if hov else (185, 180, 220))
            surface.blit(txt, (text_x - txt.get_width() // 2,
                               rect.y + rect.height // 2 - txt.get_height() // 2))

        draw_pause_btn("Tiếp tục",     pygame.Rect(cx - 120, cy + 5,  240, 32), (30, 50, 30),  (50, 100, 50), icon_fn=icons.draw_play)
        draw_pause_btn("Lưu Game",      pygame.Rect(cx - 120, cy + 44, 240, 32), (50, 50, 20),  (100, 100, 30), icon_fn=icons.draw_save)
        draw_pause_btn("Cài Đặt",       pygame.Rect(cx - 120, cy + 83, 240, 32), (20, 40, 60),  (40, 80, 130), icon_fn=icons.draw_gear)
        draw_pause_btn("Thoát Game",     pygame.Rect(cx - 120, cy + 122, 240, 32), (60, 20, 20), (130, 40, 40), icon_fn=icons.draw_close)

        hint = self._small_font.render("ESC: Tiếp tục  •  Click để chọn", True, (90, 85, 120))
        surface.blit(hint, (SCREEN_WIDTH // 2 - hint.get_width() // 2,
                            SCREEN_HEIGHT // 2 + ph // 2 - 20))

    def _render_difficulty_select(self, surface):
        """Vẽ màn hình chọn độ khó."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        surface.blit(overlay, (0, 0))

        title = self._title_font.render("CHỌN ĐỘ KHÓ", True, (255, 215, 0))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 120))

        from settings import DIFFICULTY_CONFIGS
        cards = list(DIFFICULTY_CONFIGS.keys())
        card_w, card_h = 160, 240
        gap = 20
        total_w = len(cards) * card_w + (len(cards) - 1) * gap
        start_x = SCREEN_WIDTH // 2 - total_w // 2
        cy = SCREEN_HEIGHT // 2 - 50

        mx, my = pygame.mouse.get_pos()

        for i, diff in enumerate(cards):
            cfg = DIFFICULTY_CONFIGS[diff]
            rect = pygame.Rect(start_x + i * (card_w + gap), cy, card_w, card_h)
            hov = rect.collidepoint(mx, my)

            # Card BG
            card_surf = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
            bg_alpha = 200 if hov else 120
            card_surf.fill((20, 20, 30, bg_alpha))
            
            border_col = cfg["color"] if hov else (100, 100, 120)
            pygame.draw.rect(card_surf, border_col, (0, 0, card_w, card_h), 2 if hov else 1, 10)
            
            if hov:
                glow = pygame.Surface((card_w, card_h), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*cfg["color"], 30), (0, 0, card_w, card_h), 0, 10)
                card_surf.blit(glow, (0, 0))

            surface.blit(card_surf, rect.topleft)

            # Icon
            icons.draw_shield(surface, rect.x + card_w//2 - 20, rect.y + 20, 40, cfg["color"] if hov else (150, 150, 150))

            # Name
            name_txt = self._big_font.render(diff, True, cfg["color"] if hov else (200, 200, 200))
            surface.blit(name_txt, (rect.x + card_w//2 - name_txt.get_width()//2, rect.y + 75))

            # Stats
            stat_y = rect.y + 120
            def draw_stat(text, val_str, is_pos):
                s1 = self._small_font.render(text, True, (150, 150, 150))
                s2 = self._small_font.render(val_str, True, (100, 255, 100) if is_pos else (255, 100, 100) if is_pos is False else (200, 200, 200))
                surface.blit(s1, (rect.x + 10, stat_y))
                surface.blit(s2, (rect.x + card_w - 10 - s2.get_width(), stat_y))
            
            draw_stat("HP/Dmg:", f"x{cfg['hp_mult']}", cfg['hp_mult'] < 1.0 if cfg['hp_mult'] != 1.0 else None)
            stat_y += 25
            draw_stat("Speed:", f"x{cfg['speed_mult']}", cfg['speed_mult'] < 1.0 if cfg['speed_mult'] != 1.0 else None)
            stat_y += 25
            draw_stat("Rare:", f"{int(cfg['rare_bonus']*100):+d}%", cfg['rare_bonus'] > 0 if cfg['rare_bonus'] != 0 else None)
            stat_y += 25
            draw_stat("Epic:", f"{int(cfg['epic_bonus']*100):+d}%", cfg['epic_bonus'] > 0 if cfg['epic_bonus'] != 0 else None)

        # Close button
        close_rect = pygame.Rect(SCREEN_WIDTH // 2 + 300, SCREEN_HEIGHT // 2 - 220, 40, 40)
        c_hov = close_rect.collidepoint(mx, my)
        c_col = (255, 100, 100) if c_hov else (150, 100, 100)
        pygame.draw.rect(surface, (40, 20, 20) if c_hov else (30, 20, 20), close_rect, 0, 8)
        pygame.draw.rect(surface, c_col, close_rect, 2, 8)
        icons.draw_close(surface, close_rect.x + 10, close_rect.y + 10, 20, c_col)

    def _render_settings(self, surface):
        """Vẽ màn hình Cài đặt."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surface.blit(overlay, (0, 0))

        pw, ph = 400, 300
        panel = pygame.Surface((pw, ph), pygame.SRCALPHA)
        panel.fill((20, 25, 40, 220))
        pygame.draw.rect(panel, (120, 150, 200, 180), (0, 0, pw, ph), 2, 15)
        surface.blit(panel, (SCREEN_WIDTH // 2 - pw // 2, SCREEN_HEIGHT // 2 - ph // 2))

        title = self._title_font.render("CÀI ĐẶT", True, (220, 230, 255))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, SCREEN_HEIGHT // 2 - 120))

        import sound
        sfx_vol = int(sound.SFX_VOLUME * 100)
        bgm_vol = int(sound.MUSIC_VOLUME * 100)

        texts = [
            f"SFX Volume  [1] < {sfx_vol:3d}% > [2]",
            f"BGM Volume  [3] < {bgm_vol:3d}% > [4]",
            "",
            "Nhấn ESC để quay lại"
        ]
        
        for i, line in enumerate(texts):
            color = WHITE if i < 2 else (150, 150, 150)
            rendered = self._font.render(line, True, color)
            surface.blit(rendered, (SCREEN_WIDTH // 2 - rendered.get_width() // 2,
                                    SCREEN_HEIGHT // 2 - 20 + i * 35))

    def _render_game_over(self, surface):
        """Vẽ màn hình Game Over — dramatic."""
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(SCREEN_HEIGHT):
            prog = y / SCREEN_HEIGHT
            r = int(40 + 30 * (1 - prog))
            line_s = pygame.Surface((SCREEN_WIDTH, 1), pygame.SRCALPHA)
            line_s.fill((r, 0, 0, 180))
            overlay.blit(line_s, (0, y))
        surface.blit(overlay, (0, 0))

        shadow = self._title_font.render("GAME OVER", True, (80, 0, 0))
        surface.blit(shadow, (SCREEN_WIDTH // 2 - shadow.get_width() // 2 + 3, 253))
        title = self._title_font.render("GAME OVER", True, (255, 60, 50))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 250))

        sub = self._font.render("Kael đã gục ngã...", True, (200, 150, 150))
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 320))

        opts = [("[R] Thử lại", (180, 230, 180)), ("[Q] Thoát", (200, 160, 160))]
        for i, (text, color) in enumerate(opts):
            rendered = self._font.render(text, True, color)
            surface.blit(rendered, (SCREEN_WIDTH // 2 - rendered.get_width() // 2,
                                    380 + i * 30))

    def _render_victory(self, surface):
        """Vẽ màn hình Victory — đơn giản, vinh danh người chơi."""
        now = pygame.time.get_ticks()
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 20, 180))
        surface.blit(overlay, (0, 0))

        pulse = 0.5 + 0.5 * math.sin(now * 0.003)
        glow = self._title_font.render("VICTORY", True, (180, 150, 50))
        glow.set_alpha(int(40 + 30 * pulse))
        gx = SCREEN_WIDTH // 2 - glow.get_width() // 2
        surface.blit(glow, (gx - 2, 148))
        surface.blit(glow, (gx + 2, 152))
        title = self._title_font.render("VICTORY", True, (255, 230, 100))
        surface.blit(title, (gx, 150))

        sub = self._big_font.render("Quỷ Vương Malphas đã bị tiêu diệt!", True, (200, 200, 220))
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 220))

        msg = self._font.render("Thế giới đã được cứu rỗi nhờ lòng dũng cảm của Kael.", True, (160, 155, 190))
        surface.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 270))

        # Nhấp nháy nút Continue
        continue_text = self._big_font.render("[ENTER] Để Tiếp Tục", True, (100, 255, 180))
        continue_text.set_alpha(int(100 + 155 * pulse))
        surface.blit(continue_text, (SCREEN_WIDTH // 2 - continue_text.get_width() // 2, 350))

    def _render_credits(self, surface):
        """Vẽ màn hình Game Cleared (Credits)."""
        now = pygame.time.get_ticks()
        
        # Nền tối
        surface.fill((10, 5, 15))
        
        # Ngôi sao lấp lánh (starfield) — BUG FIX: dùng SRCALPHA surface
        star_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(50):
            h = ((i * 73856093) ^ (i * 83492791)) & 0xFFFFFFFF
            sx = h % SCREEN_WIDTH
            sy = (h >> 10) % SCREEN_HEIGHT
            blink = 0.5 + 0.5 * math.sin(now * 0.001 + i * 0.7)
            pygame.draw.circle(star_surf, (150, 150, 200, int(100 * blink)), (sx, sy), 1 + (i % 2))
        surface.blit(star_surf, (0, 0))
            
        # Tiêu đề GAME CLEARED
        pulse = 0.5 + 0.5 * math.sin(now * 0.003)
        title = self._title_font.render("GAME CLEARED", True, (255, 215, 0))
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 140))
        
        # Glow cho tiêu đề
        glow = self._title_font.render("GAME CLEARED", True, (200, 150, 50))
        glow.set_alpha(int(40 + 40 * pulse))
        surface.blit(glow, (SCREEN_WIDTH // 2 - title.get_width() // 2, 140))

        # Phụ đề
        sub = self._font.render("Cảm ơn bạn đã chơi Ashes of the Fallen!", True, (200, 200, 220))
        surface.blit(sub, (SCREEN_WIDTH // 2 - sub.get_width() // 2, 230))
        
        # Stats
        stats_lines = [
            f"Level: {self.player.level if self.player else 1}",
            f"Kills: {self.total_kills}",
            f"Best Combo: {self.player.best_combo if self.player else 0}",
        ]
        if self.ng_plus:
            stats_lines.append(f"New Game+ #{self.ng_plus_count}")
        for i, line in enumerate(stats_lines):
            stat = self._font.render(line, True, (180, 180, 200))
            surface.blit(stat, (SCREEN_WIDTH // 2 - stat.get_width() // 2, 270 + i * 25))
        
        # Tác giả
        author = self._font.render("Phát triển bởi: AI Assistant", True, (150, 150, 180))
        surface.blit(author, (SCREEN_WIDTH // 2 - author.get_width() // 2, 390))
        
        # NEW GAME+ option
        ng_prompt = self._big_font.render("▶  [N] New Game+  |  [ESC] Về Menu  ◀", True, (200, 190, 200))
        pulse_start = 0.5 + 0.5 * math.sin(now * 0.005)
        start_alpha = int(120 + 135 * pulse_start)
        ng_prompt.set_alpha(start_alpha)
        surface.blit(ng_prompt, (SCREEN_WIDTH // 2 - ng_prompt.get_width() // 2, 450))
