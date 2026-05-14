"""
main.py — Vòng lặp game chính "Ashes of the Fallen"
=====================================================
Khởi tạo Pygame, chạy game loop: Event → Update → Render.

Hướng dẫn chạy:
    pip install pygame
    python main.py

Tác giả: Antigravity AI
"""

import sys
import pygame
from settings import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE
from game_state import GameState


def main():
    """Hàm chính — khởi tạo và chạy game loop."""

    # =================== KHỞI TẠO ===================
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(TITLE)
    clock = pygame.time.Clock()

    import assets
    assets.load_all_assets()
    
    import sound
    sound.init()

    # Tạo game state manager
    game = GameState()

    # =================== GAME LOOP ===================
    running = True
    while running:
        dt = clock.tick(FPS)  # Delta time (ms)

        # ---------- EVENT HANDLING ----------
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

            result = game.handle_event(event)
            if result == "QUIT":
                running = False
                break

        if not running:
            break

        # ---------- UPDATE ----------
        keys = pygame.key.get_pressed()
        game.update(keys, dt)

        # ---------- RENDER ----------
        game.render(screen)
        pygame.display.flip()

    # =================== CLEANUP ===================
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
