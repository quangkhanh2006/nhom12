"""
dialogue.py — Hệ thống hộp thoại & cutscene — ENHANCED
========================================================
Premium dialogue box với ornate frame, gradient nền,
speaker highlight, typewriter effect.
"""

import math
import pygame
from settings import (
    SCREEN_WIDTH, SCREEN_HEIGHT, DIALOGUE_BOX_HEIGHT,
    DIALOGUE_PADDING, DIALOGUE_TEXT_SPEED, WHITE, YELLOW, GRAY
)
import sound


class DialogueBox:
    """Hộp thoại NPC / cutscene — premium design.

    Attributes:
        lines (list[dict]): [{speaker, text, color}]
        current_line (int): Dòng hiện tại
        char_index (int): Ký tự đã hiển thị (typewriter)
        active (bool): Đang hiển thị?
        finished_line (bool): Dòng hiện tại đã hiện hết chữ?
    """

    def __init__(self):
        self.lines = []
        self.current_line = 0
        self.char_index = 0
        self.active = False
        self.finished_line = False
        self._font = None
        self._name_font = None
        self._hint_font = None
        self.frame_count = 0
        self._bg_cache = None

    def _init_fonts(self):
        if self._font is None:
            self._font = pygame.font.SysFont("consolas", 16)
            self._name_font = pygame.font.SysFont("consolas", 18, bold=True)
            self._hint_font = pygame.font.SysFont("consolas", 12)

    def _create_bg(self, w, h):
        """Tạo nền dialogue với gradient + ornate frame."""
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        # Gradient từ tối → sáng hơn
        for i in range(h):
            progress = i / h
            r = int(12 + 8 * progress)
            g = int(8 + 6 * progress)
            b = int(25 + 15 * progress)
            a = int(230 - 20 * progress)
            pygame.draw.line(surf, (r, g, b, a), (0, i), (w, i))

        # Viền ngoài
        pygame.draw.rect(surf, (90, 70, 140, 200), (0, 0, w, h), 2, 8)

        # Highlight trên
        for i in range(2):
            alpha = 50 - i * 20
            pygame.draw.line(surf, (180, 160, 230, alpha), (8, i + 2), (w - 8, i + 2))

        # Ornate corners
        corner_color = (120, 100, 180, 180)
        corner_size = 12
        for cx, cy, fx, fy in [(0, 0, 1, 1), (w, 0, -1, 1), (0, h, 1, -1), (w, h, -1, -1)]:
            pygame.draw.line(surf, corner_color,
                             (cx + 4 * fx, cy + 2 * fy),
                             (cx + corner_size * fx, cy + 2 * fy), 2)
            pygame.draw.line(surf, corner_color,
                             (cx + 2 * fx, cy + 4 * fy),
                             (cx + 2 * fx, cy + corner_size * fy), 2)

        return surf

    def start(self, lines):
        """Bắt đầu chuỗi dialogue."""
        self.lines = lines
        self.current_line = 0
        self.char_index = 0
        self.active = True
        self.finished_line = False
        self._bg_cache = None

    def advance(self):
        """Tiến tới dòng tiếp theo hoặc kết thúc."""
        if not self.active:
            return False
        if not self.finished_line:
            self.char_index = len(self.lines[self.current_line]["text"])
            self.finished_line = True
            return True
        self.current_line += 1
        self.char_index = 0
        self.finished_line = False
        if self.current_line >= len(self.lines):
            self.active = False
            return False
        return True

    def update(self):
        """Cập nhật typewriter effect."""
        if not self.active or self.finished_line:
            return
        self.frame_count += 1
        if self.frame_count >= DIALOGUE_TEXT_SPEED:
            self.frame_count = 0
            self.char_index += 1
            sound.play("dialogue")
            current_text = self.lines[self.current_line]["text"]
            if self.char_index >= len(current_text):
                self.char_index = len(current_text)
                self.finished_line = True

    def render(self, surface):
        """Vẽ hộp thoại — premium."""
        if not self.active:
            return
        self._init_fonts()

        box_w = SCREEN_WIDTH - 60
        box_h = DIALOGUE_BOX_HEIGHT + 10
        box_x = 30
        box_y = SCREEN_HEIGHT - box_h - 15

        # Cache background
        if self._bg_cache is None or self._bg_cache.get_size() != (box_w, box_h):
            self._bg_cache = self._create_bg(box_w, box_h)
        surface.blit(self._bg_cache, (box_x, box_y))

        line = self.lines[self.current_line]
        speaker = line.get("speaker", "")
        text = line.get("text", "")
        color = line.get("color", WHITE)

        # Speaker name với background tag
        if speaker:
            name_surf = self._name_font.render(speaker, True, YELLOW)
            # Name tag background
            tag_w = name_surf.get_width() + 16
            tag_h = name_surf.get_height() + 6
            tag_surf = pygame.Surface((tag_w, tag_h), pygame.SRCALPHA)
            tag_surf.fill((40, 30, 70, 180))
            pygame.draw.rect(tag_surf, (120, 100, 180, 150), (0, 0, tag_w, tag_h), 1, 4)
            surface.blit(tag_surf, (box_x + DIALOGUE_PADDING - 4, box_y + 8))
            surface.blit(name_surf, (box_x + DIALOGUE_PADDING + 4, box_y + 11))

        # Text với typewriter effect
        visible_text = text[:self.char_index]
        words = visible_text.split(" ")
        lines_wrapped = []
        current = ""
        max_w = box_w - DIALOGUE_PADDING * 2 - 10
        for word in words:
            test = current + " " + word if current else word
            if self._font.size(test)[0] > max_w:
                lines_wrapped.append(current)
                current = word
            else:
                current = test
        if current:
            lines_wrapped.append(current)

        text_y = box_y + 40
        for i, wrapped_line in enumerate(lines_wrapped):
            # Shadow text
            shadow = self._font.render(wrapped_line, True, (0, 0, 0))
            surface.blit(shadow, (box_x + DIALOGUE_PADDING + 1, text_y + i * 22 + 1))
            # Main text
            text_surf = self._font.render(wrapped_line, True, color)
            surface.blit(text_surf, (box_x + DIALOGUE_PADDING, text_y + i * 22))

        # Cursor nhấp nháy cuối text
        if not self.finished_line and lines_wrapped:
            last_line = lines_wrapped[-1]
            cursor_x = box_x + DIALOGUE_PADDING + self._font.size(last_line)[0] + 2
            cursor_y = text_y + (len(lines_wrapped) - 1) * 22
            t = pygame.time.get_ticks() % 600
            if t < 400:
                pygame.draw.rect(surface, color, (cursor_x, cursor_y + 2, 8, 14))

        # Hint — animated
        now = pygame.time.get_ticks()
        if self.finished_line:
            t = (now % 1500) / 1500.0
            hint_alpha = int(140 + 115 * abs(math.sin(t * 3.14)))
            # Arrow icon ▶
            arrow = "▶ [Space]"
            hint_surf = self._hint_font.render(arrow, True, (180, 170, 220))
            hint_surf.set_alpha(hint_alpha)
            surface.blit(hint_surf, (box_x + box_w - hint_surf.get_width() - 18,
                                     box_y + box_h - 24))

        # Page counter
        page = self._hint_font.render(
            f"{self.current_line + 1}/{len(self.lines)}", True, (80, 75, 110))
        surface.blit(page, (box_x + 18, box_y + box_h - 24))

        # Separator line dưới speaker
        if speaker:
            sep_y = box_y + 34
            sep_surf = pygame.Surface((box_w - DIALOGUE_PADDING * 2, 1), pygame.SRCALPHA)
            for i in range(box_w - DIALOGUE_PADDING * 2):
                progress = i / (box_w - DIALOGUE_PADDING * 2)
                a = int(60 * (1 - abs(progress - 0.5) * 2))
                sep_surf.set_at((i, 0), (120, 100, 180, a))
            surface.blit(sep_surf, (box_x + DIALOGUE_PADDING, sep_y))
