"""
inventory.py — Hệ thống Inventory & Equip
==========================================
Túi đồ 10 ô + 4 slot trang bị (Weapon/Armor/Boots/Ring).
Click chuột để equip/unequip, hover hiện tooltip.
"""

import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, INVENTORY_SIZE, EQUIP_SLOTS,
    SLOT_SIZE, SLOT_PADDING, COLOR_INVENTORY_BG, COLOR_SLOT_EMPTY,
    COLOR_SLOT_HOVER, WHITE, GRAY, YELLOW, RARITY_COLORS,
    EQUIP_WEAPON, EQUIP_ARMOR, EQUIP_BOOTS, EQUIP_RING
)


class Inventory:
    """Hệ thống túi đồ và trang bị.

    Attributes:
        bag (list): 10 ô chứa item (None = trống)
        equipped (dict): 4 slot trang bị {type: Item or None}
        is_open (bool): Inventory đang mở?
        hovered_slot (int or None): Slot đang hover
        hovered_equip (str or None): Equip slot đang hover
        notification (str): Thông báo tạm thời
        notif_timer (int): Thời gian hiển thị notification
    """

    def __init__(self):
        self.bag = [None] * INVENTORY_SIZE
        self.equipped = {slot: None for slot in EQUIP_SLOTS}
        self.is_open = False
        self.hovered_slot = None
        self.hovered_equip = None
        self.notification = ""
        self.notif_timer = 0
        self._font = None
        self._small_font = None

    def _init_fonts(self):
        if self._font is None:
            self._font = pygame.font.SysFont("consolas", 16)
            self._small_font = pygame.font.SysFont("consolas", 13)

    def toggle(self):
        """Mở/đóng inventory."""
        self.is_open = not self.is_open

    def add_item(self, item):
        """Thêm item vào túi đồ. Nếu túi đầy, vứt đồ yếu nhất đi để lấy chỗ.
        Nếu item nhặt được cùi hơn đồ đang mặc và túi đầy, bỏ qua luôn.

        Returns:
            bool: True nếu thao tác xử lý xong (nhặt hoặc chủ động vứt bỏ)
        """
        # Nếu còn chỗ trống thì nhét vào luôn
        for i in range(INVENTORY_SIZE):
            if self.bag[i] is None:
                self.bag[i] = item
                item.picked_up = True
                self.show_notification(f"Nhặt được {item.name}")
                return True

        # Nếu túi đầy:
        rarity_val = {"Common": 1, "Rare": 2, "Epic": 3}
        new_val = rarity_val.get(item.rarity, 0)
        
        # Kiểm tra xem đồ mới có xịn hơn đồ đang mặc không
        equipped = self.equipped.get(item.equip_type)
        eq_val = rarity_val.get(equipped.rarity, 0) if equipped else 0
        
        # Nếu đồ mới cùi hơn hoặc bằng đồ đang mặc -> Đồ rác rưởi, vứt luôn không nhặt
        if new_val <= eq_val:
            item.picked_up = True # Đánh dấu là đã xử lý (vứt đi) để AI không bị kẹt
            self.show_notification(f"Đã vứt bỏ {item.name} (Đồ yếu/Đã có)")
            return True

        # Nếu đồ mới xịn hơn đồ đang mặc -> Bắt buộc phải nhặt!
        # Tìm món đồ cùi nhất trong túi để vứt
        weakest_idx = -1
        lowest_val = 999
        for i in range(INVENTORY_SIZE):
            if self.bag[i]:
                bag_val = rarity_val.get(self.bag[i].rarity, 0)
                if bag_val < lowest_val:
                    lowest_val = bag_val
                    weakest_idx = i

        if weakest_idx != -1:
            dropped_name = self.bag[weakest_idx].name
            self.bag[weakest_idx] = item
            item.picked_up = True
            self.show_notification(f"Bỏ {dropped_name} để nhặt {item.name}")
            return True

        return False

    def remove_item(self, index):
        """Xóa item khỏi slot túi đồ."""
        if 0 <= index < INVENTORY_SIZE:
            self.bag[index] = None

    def equip_item(self, bag_index):
        """Trang bị item từ túi đồ vào slot equip.
        Nếu slot đã có item → swap (tráo đổi).

        Returns:
            dict or None: Chỉ số thay đổi {stat: delta}
        """
        if bag_index < 0 or bag_index >= INVENTORY_SIZE:
            return None
        item = self.bag[bag_index]
        if item is None:
            return None

        slot = item.equip_type
        stat_delta = {}

        # Nếu slot đã có item → swap
        old_item = self.equipped[slot]
        if old_item:
            # Trừ chỉ số cũ
            for key, val in old_item.stats.items():
                stat_delta[key] = stat_delta.get(key, 0) - val
            self.bag[bag_index] = old_item  # Trả về túi
        else:
            self.bag[bag_index] = None

        # Equip item mới
        self.equipped[slot] = item
        for key, val in item.stats.items():
            stat_delta[key] = stat_delta.get(key, 0) + val

        return stat_delta

    def unequip_item(self, slot):
        """Tháo trang bị, trả về túi đồ.

        Returns:
            dict or None: Chỉ số thay đổi (âm)
        """
        if slot not in self.equipped or self.equipped[slot] is None:
            return None

        # Kiểm tra túi có chỗ trống không
        empty_slot = None
        for i in range(INVENTORY_SIZE):
            if self.bag[i] is None:
                empty_slot = i
                break
        if empty_slot is None:
            self.show_notification("Inventory Full!")
            return None

        item = self.equipped[slot]
        self.equipped[slot] = None
        self.bag[empty_slot] = item

        stat_delta = {}
        for key, val in item.stats.items():
            stat_delta[key] = -val
        return stat_delta

    def show_notification(self, text):
        self.notification = text
        self.notif_timer = pygame.time.get_ticks()
        if hasattr(self, 'action_log') and self.action_log:
            self.action_log.add(text)

    def handle_click(self, mouse_x, mouse_y):
        """Xử lý click chuột trong inventory.

        Returns:
            dict or None: Chỉ số thay đổi nếu equip/unequip
        """
        if not self.is_open:
            return None

        # Tính vị trí inventory UI
        inv_x = SCREEN_WIDTH // 2 - (5 * (SLOT_SIZE + SLOT_PADDING)) // 2
        inv_y = SCREEN_HEIGHT // 2 - 60

        # Check bag slots (2 hàng x 5 cột)
        for i in range(INVENTORY_SIZE):
            row, col = i // 5, i % 5
            sx = inv_x + col * (SLOT_SIZE + SLOT_PADDING)
            sy = inv_y + row * (SLOT_SIZE + SLOT_PADDING)
            if sx <= mouse_x <= sx + SLOT_SIZE and sy <= mouse_y <= sy + SLOT_SIZE:
                if self.bag[i] is not None:
                    return self.equip_item(i)

        # Check equip slots
        equip_y = inv_y + 2.5 * (SLOT_SIZE + SLOT_PADDING) + 30
        for idx, slot in enumerate(EQUIP_SLOTS):
            sx = inv_x + idx * (SLOT_SIZE + SLOT_PADDING + 10)
            sy = equip_y
            if sx <= mouse_x <= sx + SLOT_SIZE and sy <= mouse_y <= sy + SLOT_SIZE:
                return self.unequip_item(slot)

        return None

    def update_hover(self, mouse_x, mouse_y):
        """Cập nhật slot đang hover (cho tooltip)."""
        self.hovered_slot = None
        self.hovered_equip = None
        if not self.is_open:
            return

        inv_x = SCREEN_WIDTH // 2 - (5 * (SLOT_SIZE + SLOT_PADDING)) // 2
        inv_y = SCREEN_HEIGHT // 2 - 60

        for i in range(INVENTORY_SIZE):
            row, col = i // 5, i % 5
            sx = inv_x + col * (SLOT_SIZE + SLOT_PADDING)
            sy = inv_y + row * (SLOT_SIZE + SLOT_PADDING)
            if sx <= mouse_x <= sx + SLOT_SIZE and sy <= mouse_y <= sy + SLOT_SIZE:
                self.hovered_slot = i
                return

        equip_y = inv_y + 2.5 * (SLOT_SIZE + SLOT_PADDING) + 30
        for idx, slot in enumerate(EQUIP_SLOTS):
            sx = inv_x + idx * (SLOT_SIZE + SLOT_PADDING + 10)
            sy = equip_y
            if sx <= mouse_x <= sx + SLOT_SIZE and sy <= mouse_y <= sy + SLOT_SIZE:
                self.hovered_equip = slot
                return

    def render(self, surface):
        """Vẽ inventory UI."""
        if not self.is_open:
            self._render_notification(surface)
            return
        self._init_fonts()

        # Overlay tối nền
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        surface.blit(overlay, (0, 0))

        inv_x = SCREEN_WIDTH // 2 - (5 * (SLOT_SIZE + SLOT_PADDING)) // 2
        inv_y = SCREEN_HEIGHT // 2 - 60

        # Tiêu đề
        title = self._font.render("INVENTORY", True, WHITE)
        surface.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, inv_y - 30))

        # Bag slots (2 hàng x 5 cột)
        for i in range(INVENTORY_SIZE):
            row, col = i // 5, i % 5
            sx = inv_x + col * (SLOT_SIZE + SLOT_PADDING)
            sy = inv_y + row * (SLOT_SIZE + SLOT_PADDING)
            rect = pygame.Rect(sx, sy, SLOT_SIZE, SLOT_SIZE)

            color = COLOR_SLOT_HOVER if self.hovered_slot == i else COLOR_SLOT_EMPTY
            pygame.draw.rect(surface, color, rect, 0, 4)
            pygame.draw.rect(surface, GRAY, rect, 1, 4)

            if self.bag[i]:
                self.bag[i].render_icon(surface, sx + 5, sy + 5, SLOT_SIZE - 10)

        # Equip slots
        equip_y = inv_y + 2.5 * (SLOT_SIZE + SLOT_PADDING) + 30
        equip_labels = {"Weapon": "⚔", "Armor": "🛡", "Boots": "👢", "Ring": "💍"}
        label_text = {"Weapon": "WPN", "Armor": "ARM", "Boots": "BTS", "Ring": "RNG"}

        for idx, slot in enumerate(EQUIP_SLOTS):
            sx = inv_x + idx * (SLOT_SIZE + SLOT_PADDING + 10)
            sy = equip_y
            rect = pygame.Rect(sx, sy, SLOT_SIZE, SLOT_SIZE)

            color = COLOR_SLOT_HOVER if self.hovered_equip == slot else (50, 45, 65)
            pygame.draw.rect(surface, color, rect, 0, 4)
            pygame.draw.rect(surface, (100, 90, 140), rect, 2, 4)

            if self.equipped[slot]:
                self.equipped[slot].render_icon(surface, sx + 5, sy + 5, SLOT_SIZE - 10)
            else:
                lbl = self._small_font.render(label_text[slot], True, GRAY)
                surface.blit(lbl, (sx + SLOT_SIZE // 2 - lbl.get_width() // 2,
                                   sy + SLOT_SIZE // 2 - lbl.get_height() // 2))

            name_lbl = self._small_font.render(slot, True, GRAY)
            surface.blit(name_lbl, (sx + SLOT_SIZE // 2 - name_lbl.get_width() // 2, sy + SLOT_SIZE + 4))

        # Tooltip
        self._render_tooltip(surface)
        self._render_notification(surface)

    def _render_tooltip(self, surface):
        """Vẽ tooltip khi hover item."""
        item = None
        if self.hovered_slot is not None and self.bag[self.hovered_slot]:
            item = self.bag[self.hovered_slot]
        elif self.hovered_equip and self.equipped.get(self.hovered_equip):
            item = self.equipped[self.hovered_equip]

        if not item:
            return

        mx, my = pygame.mouse.get_pos()
        lines = [item.name, f"[{item.rarity}] {item.equip_type}", item.get_stat_text()]
        tooltip_w, tooltip_h = 220, len(lines) * 22 + 16
        tx = min(mx + 15, SCREEN_WIDTH - tooltip_w - 10)
        ty = min(my + 15, SCREEN_HEIGHT - tooltip_h - 10)

        tooltip_surf = pygame.Surface((tooltip_w, tooltip_h), pygame.SRCALPHA)
        tooltip_surf.fill((20, 15, 35, 230))
        pygame.draw.rect(tooltip_surf, item.color, (0, 0, tooltip_w, tooltip_h), 1, 4)
        surface.blit(tooltip_surf, (tx, ty))

        for i, line in enumerate(lines):
            color = item.color if i == 0 else (YELLOW if i == 1 else WHITE)
            text = self._small_font.render(line, True, color)
            surface.blit(text, (tx + 8, ty + 8 + i * 22))

    def _render_notification(self, surface):
        """Vẽ thông báo tạm thời (VD: Inventory Full)."""
        if not self.notification:
            return
        elapsed = pygame.time.get_ticks() - self.notif_timer
        if elapsed > 2000:
            self.notification = ""
            return
        self._init_fonts()
        alpha = max(0, 255 - int(elapsed / 2000 * 255))
        text = self._font.render(self.notification, True, YELLOW)
        text.set_alpha(alpha)
        surface.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT - 120))
