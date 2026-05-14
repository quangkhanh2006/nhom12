"""
ai.py — Thuật toán AI Pathfinding cho kẻ địch
===============================================
Triển khai 3 thuật toán tìm đường trên lưới tile 2D:
  - DFS  : Tuần tra vô định (Linh Hồn Lang Thang)
  - BFS  : Truy đuổi đường ngắn nhất (Tay Sai Malphas)
  - A*   : Tìm đường tối ưu (Hình Bóng Ký Ức, Boss Phase 2)

Lưới tile: 0 = đi được, 1 = tường (không đi được)
"""

import heapq
import random
import math
from settings import TILE_SIZE, MAP_WIDTH, MAP_HEIGHT, DIRECTIONS

# Biến toàn cục để đổi Heuristic khi Debug
CURRENT_HEURISTIC = "manhattan"


def world_to_tile(x, y):
    """Chuyển tọa độ pixel sang tọa độ tile.

    Args:
        x (float): Tọa độ X pixel
        y (float): Tọa độ Y pixel

    Returns:
        tuple: (tile_x, tile_y) — vị trí trên lưới tile
    """
    return int(x // TILE_SIZE), int(y // TILE_SIZE)


def tile_to_world(tx, ty):
    """Chuyển tọa độ tile sang tọa độ pixel (tâm tile).

    Args:
        tx (int): Tọa độ X tile
        ty (int): Tọa độ Y tile

    Returns:
        tuple: (pixel_x, pixel_y) — tâm của tile
    """
    return tx * TILE_SIZE + TILE_SIZE // 2, ty * TILE_SIZE + TILE_SIZE // 2


def is_valid_tile(tx, ty, tile_map):
    """Kiểm tra tile có hợp lệ (trong map và đi được) không.

    Args:
        tx (int): Tọa độ X tile
        ty (int): Tọa độ Y tile
        tile_map (list[list[int]]): Mảng 2D lưới tile

    Returns:
        bool: True nếu tile hợp lệ và đi được
    """
    if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
        return tile_map[ty][tx] == 0  # 0 = đi được
    return False


def get_neighbors(tx, ty, tile_map):
    """Lấy danh sách tile lân cận đi được (4 hướng).

    Args:
        tx (int): Tọa độ X tile hiện tại
        ty (int): Tọa độ Y tile hiện tại
        tile_map (list[list[int]]): Lưới tile

    Returns:
        list[tuple]: Danh sách (nx, ny) tile lân cận hợp lệ
    """
    neighbors = []
    for dx, dy in DIRECTIONS:
        nx, ny = tx + dx, ty + dy
        if is_valid_tile(nx, ny, tile_map):
            neighbors.append((nx, ny))
    return neighbors


# =============================================================
#  DFS — Depth-First Search (Tuần tra vô định)
# =============================================================
def dfs_patrol(start_x, start_y, tile_map, max_steps=15):
    """Tạo đường tuần tra bằng DFS — đi sâu theo 1 hướng cho đến
    khi bí, rồi quay lại (backtrack). Kẻ địch dùng thuật toán này
    sẽ di chuyển theo pattern khó đoán, tạo cảm giác "lang thang".

    Args:
        start_x (float): Vị trí X pixel hiện tại
        start_y (float): Vị trí Y pixel hiện tại
        tile_map (list[list[int]]): Lưới tile
        max_steps (int): Số bước tối đa (giới hạn để không đi quá xa)

    Returns:
        list[tuple]: Danh sách (pixel_x, pixel_y) các điểm trên đường đi

    Thuật toán:
        1. Bắt đầu từ tile hiện tại
        2. Chọn ngẫu nhiên 1 hướng chưa đi
        3. Đi sâu theo hướng đó (push vào stack)
        4. Nếu bí → backtrack (pop stack)
        5. Lặp cho đến khi đủ max_steps hoặc hết đường
    """
    sx, sy = world_to_tile(start_x, start_y)

    # Stack cho DFS: mỗi phần tử là (tile_x, tile_y)
    stack = [(sx, sy)]
    visited = {(sx, sy)}
    path = [(sx, sy)]

    while stack and len(path) < max_steps:
        current = stack[-1]  # Peek đỉnh stack
        cx, cy = current

        # Lấy các ô lân cận chưa thăm
        unvisited_neighbors = [
            (nx, ny) for nx, ny in get_neighbors(cx, cy, tile_map)
            if (nx, ny) not in visited
        ]

        if unvisited_neighbors:
            # Chọn ngẫu nhiên 1 hướng → tạo pattern khó đoán
            next_tile = random.choice(unvisited_neighbors)
            visited.add(next_tile)
            stack.append(next_tile)
            path.append(next_tile)
        else:
            # Bí → quay lại (backtrack)
            stack.pop()

    # Chuyển path tile sang pixel (tâm tile)
    return [tile_to_world(tx, ty) for tx, ty in path], visited


# =============================================================
#  BFS — Breadth-First Search (Truy đuổi đường ngắn nhất)
# =============================================================
def bfs_find_path(start_x, start_y, target_x, target_y, tile_map, max_search=500):
    """Tìm đường ngắn nhất từ start đến target bằng BFS.
    Kẻ địch dùng BFS sẽ luôn chọn đường ngắn nhất (tính theo
    số ô), nhưng không tối ưu nếu có địa hình phức tạp.

    Args:
        start_x (float): Vị trí X pixel xuất phát
        start_y (float): Vị trí Y pixel xuất phát
        target_x (float): Vị trí X pixel đích
        target_y (float): Vị trí Y pixel đích
        tile_map (list[list[int]]): Lưới tile
        max_search (int): Giới hạn số ô tìm kiếm (tránh lag)

    Returns:
        list[tuple]: Đường đi [(pixel_x, pixel_y), ...],
                     rỗng nếu không tìm được

    Thuật toán:
        1. Đặt start vào queue
        2. Mở rộng theo 4 hướng (FIFO → đảm bảo ngắn nhất)
        3. Khi tìm thấy target → truy ngược lại đường đi
    """
    sx, sy = world_to_tile(start_x, start_y)
    tx, ty = world_to_tile(target_x, target_y)

    # Nếu đích trùng xuất phát hoặc đích là tường
    if (sx, sy) == (tx, ty):
        return [], set()
    if not is_valid_tile(tx, ty, tile_map):
        return [], set()

    # Queue cho BFS: (tile_x, tile_y)
    from collections import deque
    queue = deque([(sx, sy)])
    visited = {(sx, sy)}
    came_from = {}  # Để truy ngược đường đi
    search_count = 0

    while queue and search_count < max_search:
        cx, cy = queue.popleft()
        search_count += 1

        # Tìm thấy đích!
        if (cx, cy) == (tx, ty):
            # Truy ngược đường đi
            path = []
            current = (tx, ty)
            while current != (sx, sy):
                path.append(current)
                current = came_from[current]
            path.reverse()
            return [tile_to_world(px, py) for px, py in path], visited

        # Mở rộng 4 hướng
        for nx, ny in get_neighbors(cx, cy, tile_map):
            if (nx, ny) not in visited:
                visited.add((nx, ny))
                came_from[(nx, ny)] = (cx, cy)
                queue.append((nx, ny))

    # Không tìm được đường
    return [], visited


# =============================================================
#  A* — A-Star (Tìm đường tối ưu vượt chướng ngại vật)
# =============================================================
def heuristic(a, b):
    """Hàm heuristic cho A*.
    Có thể đổi qua lại giữa các thuật toán để demo.

    Args:
        a (tuple): (x1, y1) tile
        b (tuple): (x2, y2) tile

    Returns:
        float: Giá trị heuristic
    """
    if CURRENT_HEURISTIC == "euclidean":
        # Khoảng cách đường chim bay (Euclidean)
        return math.sqrt((a[0] - b[0])**2 + (a[1] - b[1])**2)
    elif CURRENT_HEURISTIC == "dijkstra":
        # Dijkstra (Không có heuristic)
        return 0
    else:
        # Khoảng cách Manhattan (Mặc định, tốt nhất cho lưới 4 hướng)
        return abs(a[0] - b[0]) + abs(a[1] - b[1])


def astar_find_path(start_x, start_y, target_x, target_y, tile_map, max_search=2500):
    """Tìm đường tối ưu bằng A* — kết hợp chi phí thực (g)
    và ước lượng (h) để chọn đường ngắn nhất.
    Kẻ địch dùng A* rất thông minh, luôn tìm đường vòng qua
    chướng ngại vật hiệu quả nhất.

    Args:
        start_x (float): Vị trí X pixel xuất phát
        start_y (float): Vị trí Y pixel xuất phát
        target_x (float): Vị trí X pixel đích
        target_y (float): Vị trí Y pixel đích
        tile_map (list[list[int]]): Lưới tile
        max_search (int): Giới hạn số ô tìm kiếm

    Returns:
        list[tuple]: Đường đi [(pixel_x, pixel_y), ...],
                     rỗng nếu không tìm được

    Thuật toán:
        1. Dùng priority queue (min-heap) sắp xếp theo f = g + h
        2. g = chi phí thực từ start → hiện tại
        3. h = ước lượng (Manhattan) từ hiện tại → đích
        4. Mỗi bước chọn ô có f nhỏ nhất → đảm bảo tối ưu
    """
    sx, sy = world_to_tile(start_x, start_y)
    tx, ty = world_to_tile(target_x, target_y)

    if (sx, sy) == (tx, ty):
        return [], set()
    if not is_valid_tile(tx, ty, tile_map):
        return [], set()

    # Priority queue: (f_score, counter, (tile_x, tile_y))
    # counter để tránh so sánh tuple khi f bằng nhau
    counter = 0
    open_set = [(heuristic((sx, sy), (tx, ty)), counter, (sx, sy))]
    came_from = {}
    g_score = {(sx, sy): 0}
    closed_set = set()
    search_count = 0

    while open_set and search_count < max_search:
        # Lấy ô có f nhỏ nhất
        f, _, current = heapq.heappop(open_set)
        search_count += 1

        if current in closed_set:
            continue
        closed_set.add(current)

        # Tìm thấy đích!
        if current == (tx, ty):
            path = []
            while current != (sx, sy):
                path.append(current)
                current = came_from[current]
            path.reverse()
            return [tile_to_world(px, py) for px, py in path], closed_set

        # Mở rộng các ô lân cận
        for nx, ny in [(current[0] + dx, current[1] + dy) for dx, dy in DIRECTIONS]:
            if not (0 <= nx < MAP_WIDTH and 0 <= ny < MAP_HEIGHT):
                continue
            
            if (nx, ny) in closed_set:
                continue

            cell_cost = tile_map[ny][nx]
            if cell_cost == 1: # 1 là tường (không đi được)
                continue

            # Chi phí thực = g hiện tại + 1 (bước cơ bản) + chi phí thêm của ô (ví dụ: bẫy = 20)
            tentative_g = g_score[current] + 1 + (cell_cost if cell_cost > 1 else 0)

            if tentative_g < g_score.get((nx, ny), float('inf')):
                came_from[(nx, ny)] = current
                g_score[(nx, ny)] = tentative_g
                f_score = tentative_g + heuristic((nx, ny), (tx, ty))
                counter += 1
                heapq.heappush(open_set, (f_score, counter, (nx, ny)))

    # Không tìm được đường
    return [], closed_set


# =============================================================
#  HELPER: Tính hướng di chuyển từ A đến B
# =============================================================
def get_direction_towards(from_x, from_y, to_x, to_y, speed):
    """Tính vector di chuyển từ điểm A đến điểm B với tốc độ cho trước.

    Args:
        from_x (float): Vị trí X hiện tại
        from_y (float): Vị trí Y hiện tại
        to_x (float): Vị trí X đích
        to_y (float): Vị trí Y đích
        speed (float): Tốc độ di chuyển

    Returns:
        tuple: (dx, dy) vector di chuyển đã normalize theo speed
    """
    dx = to_x - from_x
    dy = to_y - from_y
    distance = max((dx ** 2 + dy ** 2) ** 0.5, 0.001)  # Tránh chia 0

    # Normalize rồi nhân với speed
    return (dx / distance) * speed, (dy / distance) * speed


def distance_between(x1, y1, x2, y2):
    """Tính khoảng cách Euclidean giữa 2 điểm.

    Args:
        x1, y1 (float): Điểm 1
        x2, y2 (float): Điểm 2

    Returns:
        float: Khoảng cách
    """
    return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
