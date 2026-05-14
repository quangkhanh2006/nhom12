"""
save_manager.py — Hệ thống Lưu/Tải Trò chơi
===========================================
Ghi/đọc trạng thái game (Player, Inventory, Quest, Chapter) thành file JSON.
"""

import json
import os
from item import Item

SAVE_FILE = "save.json"

def save_game(game_state):
    """Lưu toàn bộ trạng thái hiện tại vào file JSON."""
    if not game_state.player:
        return False
        
    p = game_state.player
    
    # Serialize bag
    bag_data = []
    for item in p.inventory.bag:
        if item:
            bag_data.append({"type": item.equip_type, "rarity": item.rarity})
        else:
            bag_data.append(None)
            
    # Serialize equipped
    equipped_data = {}
    for slot, item in p.inventory.equipped.items():
        if item:
            equipped_data[slot] = {"type": item.equip_type, "rarity": item.rarity}
        else:
            equipped_data[slot] = None

    data = {
        "chapter": game_state.chapter,
        "total_kills": game_state.total_kills,
        "quest_states": game_state.quest_states,
        "ng_plus": game_state.ng_plus,
        "ng_plus_count": game_state.ng_plus_count,
        "player": {
            "level": p.level,
            "exp": p.exp,
            "hp": p.hp,
            "mp": p.mp,
            "gold": p.gold,
            "health_potions": getattr(p, 'health_potions', 0),
            "mana_potions": getattr(p, 'mana_potions', 0),
        },
        "inventory": {
            "bag": bag_data,
            "equipped": equipped_data
        }
    }
    
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"Lỗi khi lưu game: {e}")
        return False


def load_game(game_state):
    """Tải trạng thái từ JSON vào game_state."""
    if not os.path.exists(SAVE_FILE):
        return False
        
    try:
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        # Tải tiến trình
        game_state.chapter = data.get("chapter", 1)
        game_state.total_kills = data.get("total_kills", 0)
        game_state.quest_states = data.get("quest_states", {})
        game_state.ng_plus = data.get("ng_plus", False)
        game_state.ng_plus_count = data.get("ng_plus_count", 0)
        
        # Load chapter sẽ tự động tạo Player (Máu, vị trí)
        game_state.load_chapter(game_state.chapter)
        
        # Cập nhật thông số Player
        p = game_state.player
        p_data = data.get("player", {})
        
        # Cần level_up () để cập nhật max_hp, max_mp theo level hiện tại
        target_level = p_data.get("level", 1)
        # Giả lập tăng cấp (không dùng check_level_up vì không muốn báo hiệu ứng liên tục)
        from settings import LEVEL_HP_BONUS, LEVEL_MP_BONUS, LEVEL_DMG_BONUS, LEVEL_SPEED_BONUS
        
        # Khôi phục base stats theo level
        level_diff = target_level - 1
        p.max_hp += LEVEL_HP_BONUS * level_diff
        p.max_mp += LEVEL_MP_BONUS * level_diff
        p.damage += LEVEL_DMG_BONUS * level_diff
        p.speed += LEVEL_SPEED_BONUS * level_diff
        p.level = target_level
        
        p.exp = p_data.get("exp", 0)
        p.hp = p_data.get("hp", p.max_hp)
        p.mp = p_data.get("mp", p.max_mp)
        p.gold = p_data.get("gold", 0)
        p.health_potions = p_data.get("health_potions", 0)
        p.mana_potions = p_data.get("mana_potions", 0)
        
        # Cập nhật Inventory
        inv_data = data.get("inventory", {})
        
        # Khôi phục Bag
        for i, item_data in enumerate(inv_data.get("bag", [])):
            if item_data and i < len(p.inventory.bag):
                item = Item(item_data["type"], item_data["rarity"])
                item.picked_up = True
                p.inventory.bag[i] = item
                
        # Khôi phục Equipped
        for slot, item_data in inv_data.get("equipped", {}).items():
            if item_data:
                item = Item(item_data["type"], item_data["rarity"])
                item.picked_up = True
                p.inventory.equipped[slot] = item
                # Add stats
                for key, val in item.stats.items():
                    if key == "max_hp": p.max_hp += val
                    elif key == "max_mp": p.max_mp += val
                    elif key == "damage": p.damage += val
                    elif key == "speed": p.speed += val
                    elif key == "crit_rate": p.crit_rate += val
                    elif key == "hp_regen": p.hp_regen += val
                    elif key == "mp_regen": p.mp_regen += val
                    
        return True
    except Exception as e:
        print(f"Lỗi khi tải game: {e}")
        return False
