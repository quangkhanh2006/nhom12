import pygame
import os

ASSETS = {}

def load_all_assets():
    if not pygame.display.get_surface():
        return
    try:
        ASSETS['floor'] = pygame.image.load('assets/images/floor.png').convert_alpha()
        ASSETS['wall'] = pygame.image.load('assets/images/wall.png').convert_alpha()
        ASSETS['player'] = pygame.image.load('assets/images/player.png').convert_alpha()
        ASSETS['minion'] = pygame.image.load('assets/images/enemy_minion.png').convert_alpha()
        ASSETS['soul'] = pygame.image.load('assets/images/enemy_soul.png').convert_alpha()
        ASSETS['pet'] = pygame.image.load('assets/images/pet.png').convert_alpha()
    except Exception as e:
        print("Lỗi load ảnh:", e)

def get_asset(name):
    return ASSETS.get(name, None)
