"""
camera.py — Camera Follow Player
==================================
Camera cuộn theo nhân vật, giữ player ở giữa màn hình.
Chuyển đổi tọa độ thế giới (world) ↔ tọa độ màn hình (screen).
"""

from settings import SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, MAP_WIDTH, MAP_HEIGHT


class Camera:
    """Camera viewport cuộn theo player.

    Camera lưu offset (dịch chuyển) so với góc trên trái của map.
    Khi render, mọi object đều trừ đi offset để "cuộn" theo player.

    Attributes:
        offset_x (float): Dịch chuyển X (pixel)
        offset_y (float): Dịch chuyển Y (pixel)
        width (int): Chiều rộng viewport
        height (int): Chiều cao viewport
    """

    def __init__(self):
        """Khởi tạo camera ở góc trên trái map."""
        self.offset_x = 0
        self.offset_y = 0
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        # Giới hạn map tính bằng pixel
        self.map_pixel_width = MAP_WIDTH * TILE_SIZE
        self.map_pixel_height = MAP_HEIGHT * TILE_SIZE
        # BUG FIX: Screen shake offset
        self.shake_offset_x = 0
        self.shake_offset_y = 0

    def update(self, target_x, target_y):
        """Cập nhật camera để theo dõi đối tượng (thường là player).
        Camera giữ target ở giữa màn hình, clamped trong biên map.

        Args:
            target_x (float): Tọa độ X pixel của target
            target_y (float): Tọa độ Y pixel của target
        """
        # Đặt target ở giữa màn hình
        self.offset_x = target_x - self.width // 2
        self.offset_y = target_y - self.height // 2

        # Giới hạn camera không vượt ra ngoài map
        self.offset_x = max(0, min(self.offset_x, self.map_pixel_width - self.width))
        self.offset_y = max(0, min(self.offset_y, self.map_pixel_height - self.height))

    def apply(self, world_x, world_y):
        """Chuyển tọa độ thế giới → tọa độ màn hình.
        Dùng khi render object lên màn hình.

        Args:
            world_x (float): Tọa độ X trong thế giới
            world_y (float): Tọa độ Y trong thế giới

        Returns:
            tuple: (screen_x, screen_y) — tọa độ trên màn hình
        """
        return (world_x - self.offset_x + self.shake_offset_x,
                world_y - self.offset_y + self.shake_offset_y)

    def apply_rect(self, rect):
        """Chuyển pygame.Rect từ tọa độ thế giới → màn hình.

        Args:
            rect (pygame.Rect): Rect trong tọa độ thế giới

        Returns:
            pygame.Rect: Rect mới trong tọa độ màn hình
        """
        return rect.move(-self.offset_x + self.shake_offset_x,
                         -self.offset_y + self.shake_offset_y)

    def is_visible(self, world_x, world_y, margin=64):
        """Kiểm tra điểm có nằm trong viewport không (có margin).
        Dùng để tối ưu — chỉ render object trong viewport.

        Args:
            world_x (float): Tọa độ X thế giới
            world_y (float): Tọa độ Y thế giới
            margin (int): Biên mở rộng (px) — object ngoài viewport
                          nhưng trong margin vẫn render (tránh pop-in)

        Returns:
            bool: True nếu object nên được render
        """
        screen_x = world_x - self.offset_x
        screen_y = world_y - self.offset_y
        return (-margin <= screen_x <= self.width + margin and
                -margin <= screen_y <= self.height + margin)

    def screen_to_world(self, screen_x, screen_y):
        """Chuyển tọa độ màn hình → tọa độ thế giới.
        Dùng khi xử lý click chuột.

        Args:
            screen_x (float): Tọa độ X trên màn hình
            screen_y (float): Tọa độ Y trên màn hình

        Returns:
            tuple: (world_x, world_y) — tọa độ trong thế giới
        """
        return screen_x + self.offset_x, screen_y + self.offset_y

    def get_visible_tile_range(self):
        """Lấy range tile hiện đang hiển thị trên viewport.
        Dùng để tối ưu render — chỉ vẽ tile trong viewport.

        Returns:
            tuple: (start_col, end_col, start_row, end_row) — inclusive range
        """
        start_col = max(0, int(self.offset_x // TILE_SIZE))
        end_col = min(MAP_WIDTH - 1, int((self.offset_x + self.width) // TILE_SIZE) + 1)
        start_row = max(0, int(self.offset_y // TILE_SIZE))
        end_row = min(MAP_HEIGHT - 1, int((self.offset_y + self.height) // TILE_SIZE) + 1)
        return start_col, end_col, start_row, end_row
