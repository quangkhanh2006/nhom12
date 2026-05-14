"""
settings.py — Hằng số và cấu hình game "Ashes of the Fallen"
=============================================================
Chứa tất cả thông số kỹ thuật, màu sắc, chỉ số nhân vật,
kẻ địch, trang bị, và các cài đặt UI.
"""

import pygame

# ======================== CỬA SỔ GAME ========================
SCREEN_WIDTH = 1280       # Chiều rộng cửa sổ (px)
SCREEN_HEIGHT = 720       # Chiều cao cửa sổ (px)
FPS = 60                  # Khung hình mỗi giây
TITLE = "Ashes of the Fallen"

# ======================== TILE MAP ========================
TILE_SIZE = 32            # Kích thước mỗi ô tile (px)
MAP_WIDTH = 50            # Số tile theo chiều ngang
MAP_HEIGHT = 50           # Số tile theo chiều dọc

# Loại tile
TILE_FLOOR = 0            # Đi được
TILE_WALL = 1             # Tường — không đi được
TILE_DOOR = 2             # Cửa chuyển chương
TILE_TRAP = 3             # Bẫy (Chapter 4)
TILE_SPECIAL = 4          # Ô đặc biệt (NPC, cutscene trigger)
TILE_WATER = 5            # Nước — không đi được

# ======================== MÀU SẮC ========================
# Màu cơ bản
BLACK       = (0, 0, 0)
WHITE       = (255, 255, 255)
RED         = (200, 50, 50)
GREEN       = (50, 200, 50)
BLUE        = (50, 100, 200)
YELLOW      = (255, 215, 0)
ORANGE      = (255, 140, 0)
PURPLE      = (150, 50, 200)
GRAY        = (128, 128, 128)
DARK_GRAY   = (64, 64, 64)
LIGHT_GRAY  = (192, 192, 192)

# Màu theme game (dark fantasy)
COLOR_BG_DARK       = (15, 10, 25)       # Nền tối chủ đạo
COLOR_BG_MENU       = (10, 5, 20)        # Nền menu
COLOR_FLOOR_1       = (45, 35, 30)       # Sàn chương 1 (làng hoang)
COLOR_FLOOR_2       = (40, 40, 50)       # Sàn chương 2 (thành phố)
COLOR_FLOOR_3       = (25, 45, 25)       # Sàn chương 3 (rừng)
COLOR_FLOOR_4       = (30, 20, 50)       # Sàn chương 4 (cõi giữa)
COLOR_FLOOR_5       = (20, 10, 10)       # Sàn chương 5 (ngai vàng)
COLOR_WALL          = (30, 25, 20)       # Tường
COLOR_WALL_ACCENT   = (50, 40, 35)       # Viền tường
COLOR_DOOR          = (180, 140, 60)     # Cửa chuyển map
COLOR_TRAP          = (120, 40, 40)      # Bẫy
COLOR_WATER         = (30, 50, 80)       # Nước

# Màu nhân vật
COLOR_PLAYER        = (60, 50, 120)      # Kael — tím đậm
COLOR_PLAYER_SKIN   = (220, 180, 140)    # Da
COLOR_PLAYER_HAIR   = (30, 20, 40)       # Tóc đen
COLOR_PLAYER_SWORD  = (180, 200, 220)    # Kiếm

# Màu kẻ địch
COLOR_SOUL          = (200, 220, 255)    # Linh Hồn Lang Thang — trắng xanh
COLOR_MINION        = (180, 50, 50)      # Tay Sai Malphas — đỏ đậm
COLOR_SHADOW        = (100, 40, 160)     # Hình Bóng Ký Ức — tím
COLOR_BOSS          = (40, 10, 10)       # Malphas — đen đỏ
COLOR_BOSS_GLOW     = (255, 60, 20)      # Glow boss

# Màu UI
COLOR_HP_BAR        = (200, 30, 30)      # Thanh HP
COLOR_HP_BG         = (60, 20, 20)       # Nền thanh HP
COLOR_COOLDOWN      = (100, 100, 100)    # Cooldown xám
COLOR_COOLDOWN_READY = (50, 200, 100)    # Skill sẵn sàng
COLOR_MINIMAP_BG    = (20, 15, 30, 180)  # Nền minimap (có alpha)
COLOR_TOOLTIP_BG    = (20, 15, 35, 220)  # Nền tooltip
COLOR_INVENTORY_BG  = (25, 20, 40, 230)  # Nền inventory
COLOR_SLOT_EMPTY    = (40, 35, 55)       # Slot trống
COLOR_SLOT_HOVER    = (70, 60, 100)      # Slot hover

# Màu floating text
COLOR_DMG_NORMAL    = WHITE              # Damage thường
COLOR_DMG_CRIT      = YELLOW             # Crit damage
COLOR_DMG_PLAYER    = RED                # Player bị đánh
COLOR_HEAL          = GREEN              # Hồi HP

# Màu rarity glow
COLOR_COMMON_GLOW   = (200, 200, 200)    # Trắng
COLOR_RARE_GLOW     = (50, 150, 255)     # Xanh
COLOR_EPIC_GLOW     = (180, 50, 255)     # Tím

# ======================== PLAYER — KAEL ========================
PLAYER_HP           = 150      # Máu ban đầu (tăng từ 100 → 150)
PLAYER_MP           = 120      # Mana ban đầu (tăng từ 100 → 120)
PLAYER_DAMAGE       = 20       # Sát thương cơ bản (tăng từ 15 → 20)
PLAYER_SPEED        = 3.5      # Tốc độ di chuyển (tăng nhẹ)
PLAYER_CRIT_RATE    = 0.15     # Tỉ lệ chí mạng 15% (tăng từ 10%)
PLAYER_CRIT_MULTI   = 1.8      # Hệ số chí mạng (tăng từ 1.5x)
PLAYER_SIZE         = 28       # Kích thước sprite player (px)
PLAYER_ATTACK_RANGE = 50       # Tầm đánh (tăng nhẹ từ 45)
PLAYER_ATTACK_KNOCKBACK = 10   # Knockback khi đánh trúng (tăng nhẹ)
PLAYER_INVINCIBLE_TIME = 600   # Thời gian bất tử sau bị đánh (ms) — 0.6s
PLAYER_PICKUP_RANGE = 50       # Tầm nhặt item (px)

# ======================== SKILLS ========================
# Cấp độ yêu cầu để mở khóa kỹ năng
SKILL_UNLOCK_LEVELS = {
    "Q": 1,  # Dash
    "R": 2,  # AoE
    "Z": 3,  # Shield
    "X": 4,  # Lifesteal
    "C": 5,  # Summon
}

# Q — Dash
DASH_COOLDOWN       = 2500     # Cooldown 2.5 giây (giảm từ 3s)
DASH_COST           = 5        # MP
DASH_DISTANCE       = 130      # Khoảng cách dash (tăng nhẹ)
DASH_DURATION       = 200      # Thời gian dash (ms)
DASH_INVINCIBLE     = True     # Bất tử khi dash

# R — AoE 360°
AOE_COOLDOWN        = 6000     # Cooldown 6 giây (giảm từ 8s)
AOE_COST            = 15       # MP (giảm từ 20)
AOE_RADIUS          = 110      # Bán kính AoE (tăng nhẹ)
AOE_DAMAGE_MULTI    = 2.5      # Hệ số damage AoE (tăng từ 2.0x)
AOE_DURATION        = 350      # Thời gian hiệu ứng AoE (ms)

# E — Khiên Bóng Tối (Shadow Shield)
SHIELD_COOLDOWN     = 10000    # Cooldown 10 giây (giảm từ 12s)
SHIELD_COST         = 20       # MP (giảm từ 25)
SHIELD_DURATION     = 5000     # Thời gian tồn tại khiên (tăng 4s → 5s)
SHIELD_HP           = 50       # Lượng HP khiên hấp thụ (tăng từ 30 → 50)

# T — Chém Hút Máu (Lifesteal Slash)
LIFESTEAL_COOLDOWN  = 5000     # Cooldown 5 giây (giảm từ 6s)
LIFESTEAL_COST      = 12       # MP (giảm từ 15)
LIFESTEAL_RANGE     = 220      # Tầm bắn projectile (tăng nhẹ)
LIFESTEAL_SPEED     = 7        # Tốc độ bay projectile (tăng nhẹ)
LIFESTEAL_DMG_MULTI = 1.8      # Hệ số sát thương (tăng từ 1.5x)
LIFESTEAL_HEAL_RATE = 0.35     # Hồi 35% damage dưới dạng HP (tăng từ 30%)
LIFESTEAL_PIERCE    = 4        # Xuyên qua tối đa 4 enemy (tăng từ 3)

# C — Triệu Hồi Linh Hồn (Summon Spirit)
SUMMON_COOLDOWN     = 12000    # Cooldown 12 giây (giảm từ 15s)
SUMMON_COST         = 25       # MP (giảm từ 35)
SUMMON_DURATION     = 10000    # Thời gian tồn tại spirit (tăng 8s → 10s)
SUMMON_DMG_MULTI    = 0.60     # Damage = 60% player damage (tăng từ 50%)
SUMMON_SPEED        = 4        # Tốc độ bay spirit (px/frame)
SUMMON_ATTACK_RANGE = 40       # Tầm đánh spirit (tăng nhẹ)
SUMMON_ATTACK_CD    = 600      # Cooldown đánh mỗi 0.6s (giảm từ 0.8s)

# Màu skill mới
COLOR_SHIELD        = (100, 80, 200)     # Khiên tím
COLOR_SHIELD_GLOW   = (140, 100, 255)    # Glow khiên
COLOR_LIFESTEAL     = (220, 50, 80)      # Chém đỏ-hồng
COLOR_LIFESTEAL_HEAL = (80, 255, 120)    # Hồi xanh lá
COLOR_SPIRIT        = (100, 200, 255)    # Linh hồn xanh dương
COLOR_SPIRIT_GLOW   = (150, 220, 255)    # Glow linh hồn

# ======================== KẺ ĐỊCH ========================
# Linh Hồn Lang Thang (DFS patrol) — yếu nhất, dễ giết
SOUL_HP             = 60       # Tăng từ 40 → 60
SOUL_DAMAGE         = 10       # Tăng từ 6 → 10
SOUL_SPEED          = 2.5      # Tăng từ 2.0 → 2.5
SOUL_DETECT_RANGE   = 180
SOUL_EXP            = 12

# Tay Sai Malphas (BFS chase) — nhanh nhưng yếu
MINION_HP           = 50       # Tăng từ 35 → 50
MINION_DAMAGE       = 12       # Tăng từ 8 → 12
MINION_SPEED        = 4.5      # Tăng từ 4.0 → 4.5
MINION_DETECT_RANGE = 250
MINION_EXP          = 15

# Hình Bóng Ký Ức (A* smart) — mạnh, thông minh
SHADOW_HP           = 120      # Tăng từ 80 → 120
SHADOW_DAMAGE       = 15       # Tăng từ 10 → 15
SHADOW_SPEED        = 3        # Tăng từ 2.5 → 3.0
SHADOW_DETECT_RANGE = 350
SHADOW_EXP          = 30

# ======================== BOSS — MALPHAS ========================
BOSS_HP             = 600      # Tăng mạnh từ 350 → 600
BOSS_DAMAGE         = 25       # Tăng từ 15 → 25
BOSS_SPEED_P1       = 2.2      # Phase 1 nhanh hơn (tăng từ 1.8 → 2.2)
BOSS_SPEED_P2       = 4.0      # Phase 2 tốc độ ác mộng (tăng từ 3.0 → 4.0)
BOSS_DETECT_RANGE   = 500
BOSS_SUMMON_INTERVAL = 7000    # Triệu hồi quái mỗi 7 giây
BOSS_AOE_RADIUS     = 120      # Bán kính AoE boss
BOSS_AOE_COOLDOWN   = 5000     # Cooldown AoE boss
BOSS_SIZE           = 48       # Kích thước boss (px)
BOSS_EXP            = 150

# Boss Skills
BOSS_DASH_COOLDOWN  = 4000     # Cooldown lao tới (ms)
BOSS_DASH_SPEED     = 10       # Tốc độ lao tới
BOSS_DASH_DURATION  = 400      # Thời gian lao (ms)
BOSS_DASH_DAMAGE    = 35       # Tăng mạnh sát thương lao từ 20 → 35
BOSS_DASH_RANGE     = 250      # Tầm kích hoạt dash (chỉ dash khi đủ gần)

BOSS_PROJ_COOLDOWN  = 3000     # Cooldown bắn đạn (ms)
BOSS_PROJ_COUNT     = 5        # Số đạn mỗi lần bắn (Phase 1: 3, Phase 2: 5)
BOSS_PROJ_SPEED     = 4        # Tốc độ đạn
BOSS_PROJ_DAMAGE    = 18       # Tăng sát thương mỗi viên đạn từ 10 → 18
BOSS_PROJ_RANGE     = 300      # Tầm bắn đạn

BOSS_TELE_COOLDOWN  = 8000     # Cooldown teleport (ms) — chỉ Phase 2
BOSS_TELE_DISTANCE  = 60       # Khoảng cách xuất hiện sau lưng player

# ======================== TRANG BỊ & LOOT ========================
# Tỉ lệ rơi theo rarity
RARITY_COMMON  = "Common"
RARITY_RARE    = "Rare"
RARITY_EPIC    = "Epic"

DROP_RATES = {
    RARITY_COMMON: 0.70,   # 70%
    RARITY_RARE:   0.25,   # 25%
    RARITY_EPIC:   0.05,   # 5%
}

# Loại trang bị
EQUIP_WEAPON = "Weapon"
EQUIP_ARMOR  = "Armor"
EQUIP_BOOTS  = "Boots"
EQUIP_RING   = "Ring"

# Consumables & Tiền tệ
EQUIP_POTION_HP = "Potion_HP"
EQUIP_POTION_MP = "Potion_MP"
EQUIP_GOLD      = "Gold"

# Thùng gỗ (Crate)
CRATE_HP = 20
CRATE_SIZE = 30
CRATE_LOOT_GOLD_CHANCE    = 0.50   # 50% rớt vàng
CRATE_LOOT_POTION_CHANCE  = 0.30   # 30% rớt bình máu/mana
CRATE_GOLD_AMOUNT_MIN     = 10
CRATE_GOLD_AMOUNT_MAX     = 50

# Chỉ số trang bị theo loại và rarity
ITEM_STATS = {
    EQUIP_WEAPON: {
        RARITY_COMMON: {"damage": 5},
        RARITY_RARE:   {"damage": 10},
        RARITY_EPIC:   {"damage": 15},
    },
    EQUIP_ARMOR: {
        RARITY_COMMON: {"max_hp": 20, "hp_regen": 0.5},
        RARITY_RARE:   {"max_hp": 40, "hp_regen": 1.0},
        RARITY_EPIC:   {"max_hp": 60, "hp_regen": 2.0},
    },
    EQUIP_BOOTS: {
        RARITY_COMMON: {"speed": 0.5, "mp_regen": 2.0},
        RARITY_RARE:   {"speed": 1.0, "mp_regen": 4.0},
        RARITY_EPIC:   {"speed": 1.5, "mp_regen": 6.0},
    },
    EQUIP_RING: {
        RARITY_COMMON: {"crit_rate": 0.05, "max_mp": 20},
        RARITY_RARE:   {"crit_rate": 0.10, "max_mp": 40},
        RARITY_EPIC:   {"crit_rate": 0.15, "max_mp": 60},
    },
}

# Tên lore cho item
ITEM_NAMES = {
    EQUIP_WEAPON: {
        RARITY_COMMON: "Mảnh Ký Ức Mờ Nhạt",
        RARITY_RARE:   "Kiếm Oan Hồn",
        RARITY_EPIC:   "Lưỡi Hái Bóng Tối",
    },
    EQUIP_ARMOR: {
        RARITY_COMMON: "Áo Giáp Rỉ Sét",
        RARITY_RARE:   "Giáp Hộ Mệnh",
        RARITY_EPIC:   "Áo Choàng Linh Hồn",
    },
    EQUIP_BOOTS: {
        RARITY_COMMON: "Giày Lữ Khách",
        RARITY_RARE:   "Ủng Bóng Đêm",
        RARITY_EPIC:   "Giày Hư Không",
    },
    EQUIP_RING: {
        RARITY_COMMON: "Nhẫn Thề Phai",
        RARITY_RARE:   "Nhẫn Định Mệnh",
        RARITY_EPIC:   "Nhẫn Huyết Nguyệt",
    },
}

# Màu item theo rarity
RARITY_COLORS = {
    RARITY_COMMON: COLOR_COMMON_GLOW,
    RARITY_RARE:   COLOR_RARE_GLOW,
    RARITY_EPIC:   COLOR_EPIC_GLOW,
}

# Xác suất drop item khi quái chết
ENEMY_DROP_CHANCE = 0.40  # 40% quái chết rơi đồ

# ======================== INVENTORY ========================
INVENTORY_SIZE       = 10      # Số ô túi đồ
EQUIP_SLOTS          = [EQUIP_WEAPON, EQUIP_ARMOR, EQUIP_BOOTS, EQUIP_RING]
SLOT_SIZE            = 50      # Kích thước ô inventory (px)
SLOT_PADDING         = 5       # Khoảng cách giữa các ô (px)

# ======================== UI / HUD ========================
HP_BAR_WIDTH         = 200     # Chiều rộng thanh HP (px)
HP_BAR_HEIGHT        = 20      # Chiều cao thanh HP (px)
HP_BAR_X             = 15      # Vị trí X thanh HP
HP_BAR_Y             = 15      # Vị trí Y thanh HP

MINIMAP_WIDTH        = 180     # Chiều rộng minimap (px)
MINIMAP_HEIGHT       = 180     # Chiều cao minimap (px)
MINIMAP_X            = SCREEN_WIDTH - MINIMAP_WIDTH - 15   # Góc phải
MINIMAP_Y            = 15      # Góc trên

SKILL_ICON_SIZE      = 45      # Kích thước icon skill (px)
SKILL_BAR_Y          = SCREEN_HEIGHT - 70   # Vị trí Y thanh skill

# Floating text
FLOAT_TEXT_DURATION  = 800     # Thời gian hiển thị (ms)
FLOAT_TEXT_SPEED     = 1.5     # Tốc độ bay lên

# ======================== CHAPTER INFO ========================
CHAPTER_NAMES = {
    1: "Tro Tàn",
    2: "Thành Phố Không Ngủ",
    3: "Khu Rừng Ký Ức",
    4: "Cõi Giữa",
    5: "Quỷ Vương Malphas",
}

CHAPTER_DESCRIPTIONS = {
    1: "Làng hoang tàn — nơi bắt đầu hành trình chuộc lỗi",
    2: "Thành phố Valdris bị chiếm đóng — gặp Sera",
    3: "Rừng nguyền rủa — đối mặt quá khứ tội lỗi",
    4: "Thế giới giữa sự sống và cái chết",
    5: "Đối đầu Quỷ Vương Malphas — trận chiến cuối cùng",
}

# Số quái mỗi chương
CHAPTER_ENEMIES = {
    1: {"soul": 5, "minion": 0, "shadow": 0},
    2: {"soul": 3, "minion": 5, "shadow": 0},
    3: {"soul": 4, "minion": 6, "shadow": 5},    # Tăng quái để farm EXP
    4: {"soul": 6, "minion": 5, "shadow": 12},   # Tăng quái để đảm bảo lên đủ level 5
    5: {"soul": 0, "minion": 0, "shadow": 0},
}

# ======================== DIALOGUE ========================
DIALOGUE_BOX_HEIGHT  = 150     # Chiều cao hộp thoại (px)
DIALOGUE_PADDING     = 20      # Padding text trong hộp thoại
DIALOGUE_TEXT_SPEED  = 2       # Ký tự mỗi frame (typewriter effect)

# ======================== TRAP (Chapter 4) ========================
TRAP_DAMAGE          = 10      # Sát thương bẫy (giảm từ 15)
TRAP_COOLDOWN        = 2500    # Cooldown bẫy (tăng từ 2s → 2.5s)

# ======================== DIRECTIONS ========================
DIR_UP    = (0, -1)
DIR_DOWN  = (0, 1)
DIR_LEFT  = (-1, 0)
DIR_RIGHT = (1, 0)
DIRECTIONS = [DIR_UP, DIR_DOWN, DIR_LEFT, DIR_RIGHT]

# ======================== EXP & LEVEL UP ========================
EXP_PER_LEVEL = [0, 50, 120, 220, 350, 500, 700, 950, 1250, 1600]  # EXP cần cho mỗi level (max 10)
LEVEL_HP_BONUS = 15           # +HP mỗi level
LEVEL_DMG_BONUS = 3           # +Damage mỗi level
LEVEL_MP_BONUS = 10           # +MP mỗi level
LEVEL_SPEED_BONUS = 0.1       # +Speed mỗi level
MAX_LEVEL = 10

# ======================== COMBO SYSTEM ========================
COMBO_TIMEOUT = 2000          # Thời gian reset combo (ms)
COMBO_DMG_BONUS = 0.15        # +15% damage mỗi bậc combo
COMBO_MAX = 50                # Combo tối đa

# ======================== QUEST TRACKER ========================
CHAPTER_QUESTS = {
    1: [
        {"type": "kill_all", "text": "Giải phóng linh hồn", "target": "enemies"},
        {"type": "find_npc", "text": "Tìm cuốn nhật ký", "target": "npc"},
        {"type": "reach_door", "text": "Tìm đường ra khỏi làng", "target": "door"},
    ],
    2: [
        {"type": "kill_all", "text": "Dọn sạch tay sai Malphas", "target": "enemies"},
        {"type": "find_npc", "text": "Tìm gặp Sera", "target": "npc"},
        {"type": "reach_door", "text": "Đi đến khu rừng phía bắc", "target": "door"},
    ],
    3: [
        {"type": "kill_all", "text": "Tiêu diệt ký ức tội lỗi", "target": "enemies"},
        {"type": "reach_door", "text": "Mở cổng vào cõi giữa", "target": "door"},
    ],
    4: [
        {"type": "kill_all", "text": "Vượt qua bóng tối", "target": "enemies"},
        {"type": "find_npc", "text": "Tìm Lyra", "target": "npc"},
        {"type": "reach_door", "text": "Tiến vào Ngai Vàng", "target": "door"},
    ],
    5: [
        {"type": "kill_boss", "text": "Tiêu diệt Quỷ Vương Malphas", "target": "boss"},
    ],
}

# ======================== DEATH SLOW-MO ========================
SLOW_MO_DURATION = 300        # Thời gian slow-mo (ms)
SLOW_MO_FACTOR = 0.3          # Tốc độ game khi slow-mo (30%)

# ======================== NEW GAME+ ========================
NG_PLUS_HP_MULTI = 1.5        # Quái có 150% HP
NG_PLUS_DMG_MULTI = 1.3       # Quái có 130% damage
NG_PLUS_DROP_BONUS = 0.15     # +15% drop rate Epic

# ======================== PET ========================
PET_SPEED = 5                 # Tốc độ di chuyển của Pet
PET_DETECT_RANGE = 350        # Tầm phát hiện item rơi
PET_PICKUP_RANGE = 20         # Tầm nhặt item
COLOR_PET = (255, 230, 100)   # Màu vàng kim
COLOR_PET_GLOW = (255, 200, 50)

