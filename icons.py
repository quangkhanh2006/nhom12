"""
icons.py — Module vẽ icon bằng pygame.draw
===========================================
"""
import pygame
import math

def draw_play(surface, x, y, size, color):
    """Vẽ icon Play (Tam giác)"""
    points = [
        (x, y),
        (x, y + size),
        (x + int(size * 0.866), y + size // 2)
    ]
    pygame.draw.polygon(surface, color, points)

def draw_refresh(surface, x, y, size, color, thickness=2):
    """Vẽ icon Refresh (Mũi tên cong)"""
    r = size // 2
    cx = x + r
    cy = y + r
    pygame.draw.arc(surface, color, (x, y, size, size), math.pi/4, 7*math.pi/4, thickness)
    # Mũi tên
    p1 = (x + size - thickness, cy - r//2)
    p2 = (x + size + thickness*2, cy - r//2)
    p3 = (x + size, cy + thickness)
    pygame.draw.polygon(surface, color, [p1, p2, p3])

def draw_gear(surface, x, y, size, color):
    """Vẽ icon Gear (Bánh răng)"""
    r = size // 2
    cx = x + r
    cy = y + r
    inner_r = int(r * 0.5)
    outer_r = int(r * 0.8)
    teeth_r = r
    
    # Vẽ các răng cưa
    num_teeth = 8
    for i in range(num_teeth):
        angle = i * (2 * math.pi / num_teeth)
        dx = math.cos(angle)
        dy = math.sin(angle)
        p1 = (cx + dx * outer_r, cy + dy * outer_r)
        p2 = (cx + dx * teeth_r, cy + dy * teeth_r)
        pygame.draw.line(surface, color, p1, p2, max(2, size // 4))
        
    pygame.draw.circle(surface, color, (cx, cy), outer_r, max(2, size // 6))
    pygame.draw.circle(surface, (0, 0, 0, 0), (cx, cy), inner_r) # Trong suốt ở giữa (nếu vẽ lên surface có alpha thì sẽ bị đè màu color)
    # Để chắc chắn giữa rỗng, vẽ solid ring
    # Thay vì vẽ circle có độ dày, ta vẽ outer và để trống inner.

def draw_save(surface, x, y, size, color):
    """Vẽ icon Save (Đĩa mềm)"""
    pygame.draw.rect(surface, color, (x, y, size, size), 2, 2)
    # Label trắng/nhãn
    label_w = int(size * 0.6)
    label_h = int(size * 0.4)
    lx = x + (size - label_w) // 2
    ly = y + 2
    pygame.draw.rect(surface, color, (lx, ly, label_w, label_h))
    # Phần quét (dưới)
    sw = int(size * 0.4)
    sh = int(size * 0.3)
    sx = x + (size - sw) // 2
    sy = y + size - sh
    pygame.draw.rect(surface, color, (sx, sy, sw, sh), 2)

def draw_close(surface, x, y, size, color, thickness=3):
    """Vẽ icon Close (Dấu X)"""
    pygame.draw.line(surface, color, (x, y), (x + size, y + size), thickness)
    pygame.draw.line(surface, color, (x + size, y), (x, y + size), thickness)

def draw_sword(surface, x, y, size, color):
    """Vẽ icon Sword"""
    # Cán kiếm
    pygame.draw.line(surface, color, (x + size*0.2, y + size*0.8), (x + size*0.4, y + size*0.6), max(2, size//8))
    # Chuôi (crossguard)
    pygame.draw.line(surface, color, (x + size*0.25, y + size*0.75), (x + size*0.5, y + size*0.5), max(2, size//10))
    # Lưỡi kiếm
    pygame.draw.line(surface, color, (x + size*0.4, y + size*0.6), (x + size*0.9, y + size*0.1), max(2, size//6))
    
def draw_shield(surface, x, y, size, color):
    """Vẽ icon Shield"""
    w = size
    h = size
    points = [
        (x + w * 0.1, y + h * 0.1),
        (x + w * 0.9, y + h * 0.1),
        (x + w * 0.9, y + h * 0.5),
        (x + w * 0.5, y + h * 0.9),
        (x + w * 0.1, y + h * 0.5)
    ]
    pygame.draw.polygon(surface, color, points, 2)
    # Đường chéo/thập tự
    pygame.draw.line(surface, color, (x + w*0.5, y + h*0.1), (x + w*0.5, y + h*0.8), 2)
    pygame.draw.line(surface, color, (x + w*0.1, y + h*0.3), (x + w*0.9, y + h*0.3), 2)
