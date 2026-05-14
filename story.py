"""
story.py — Dữ liệu cốt truyện 5 chương + 3 kết thúc
======================================================
Chứa dialogue, cutscene triggers, và ending data.
"""

from settings import WHITE, YELLOW

# Màu cho từng nhân vật
KAEL_COLOR = (180, 160, 255)    # Tím nhạt
SERA_COLOR = (255, 200, 150)    # Cam nhạt
LYRA_COLOR = (150, 255, 200)    # Xanh lá nhạt
MALPHAS_COLOR = (255, 80, 60)   # Đỏ
NARRATOR_COLOR = (200, 200, 220)  # Xám sáng


# ======================== CHƯƠNG 1 — TRO TÀN ========================
CHAPTER_1_INTRO = [
    {"speaker": "", "text": "Vương quốc Valdris... một nơi từng tràn đầy sự sống.",
     "color": NARRATOR_COLOR},
    {"speaker": "", "text": "Cho đến khi 'Đêm Tận Thế' xảy ra — nghi lễ triệu hồi Quỷ Vương thất bại.",
     "color": NARRATOR_COLOR},
    {"speaker": "", "text": "Mặt trời biến mất. Linh hồn không siêu thoát. Quái vật tràn lan.",
     "color": NARRATOR_COLOR},
    {"speaker": "Kael", "text": "... Tôi nhớ nơi này. Làng Ashenvale. Nơi tôi lớn lên.",
     "color": KAEL_COLOR},
    {"speaker": "Kael", "text": "Giờ chỉ còn tro tàn. Và những linh hồn không yên nghỉ.",
     "color": KAEL_COLOR},
    {"speaker": "", "text": "[Hướng dẫn] WASD: Di chuyển | SPACE: Tấn công | Q: Dash | R: AoE | F: Nhặt đồ | I: Inventory",
     "color": YELLOW},
]

CHAPTER_1_DIARY = [
    {"speaker": "Kael", "text": "Cuốn nhật ký này... chữ viết của tôi.",
     "color": KAEL_COLOR},
    {"speaker": "Kael", "text": "'Nghi lễ đã sẵn sàng. Malphas sẽ ban cho ta sức mạnh vượt qua cái chết.'",
     "color": KAEL_COLOR},
    {"speaker": "Kael", "text": "'Lyra sẽ không hiểu. Nhưng đó là cái giá phải trả.'",
     "color": KAEL_COLOR},
    {"speaker": "Kael", "text": "... Không một dòng hối hận. Kẻ viết những dòng này... là tôi sao?",
     "color": KAEL_COLOR},
]

CHAPTER_1_COMPLETE = [
    {"speaker": "", "text": "Linh hồn cuối cùng đã được giải thoát. Con đường dẫn đến thành phố Valdris đã mở.",
     "color": NARRATOR_COLOR},
    {"speaker": "Kael", "text": "Lyra... em chờ anh. Anh sẽ sửa chữa tất cả.",
     "color": KAEL_COLOR},
]

# ======================== CHƯƠNG 2 — THÀNH PHỐ KHÔNG NGỦ ========================
CHAPTER_2_INTRO = [
    {"speaker": "", "text": "Thành phố Valdris — từng là trái tim vương quốc, giờ bị tay sai Malphas chiếm đóng.",
     "color": NARRATOR_COLOR},
    {"speaker": "Kael", "text": "Tay sai tuần tra khắp nơi. Phải thận trọng.",
     "color": KAEL_COLOR},
]

CHAPTER_2_MEET_SERA = [
    {"speaker": "Sera", "text": "Đứng lại! Ngươi là ai? Tại sao lại ở đây?",
     "color": SERA_COLOR},
    {"speaker": "Kael", "text": "Tôi là... chỉ là kẻ đi ngang qua.",
     "color": KAEL_COLOR},
    {"speaker": "Sera", "text": "Đi ngang qua? Trong thành phố đầy quái vật? Ngươi không bình thường.",
     "color": SERA_COLOR},
    {"speaker": "Sera", "text": "Tôi là Sera. Thám tử sống sót cuối cùng của Valdris.",
     "color": SERA_COLOR},
    {"speaker": "Sera", "text": "Em gái tôi — Lyra — mất tích kể từ Đêm Tận Thế.",
     "color": SERA_COLOR},
    {"speaker": "Kael", "text": "...! Lyra?",
     "color": KAEL_COLOR},
    {"speaker": "Sera", "text": "Ngươi biết em tôi? Nói đi!",
     "color": SERA_COLOR},
    {"speaker": "Kael", "text": "Tôi... sẽ giúp cô tìm Lyra. Nhưng trước hết phải thoát khỏi đây.",
     "color": KAEL_COLOR},
]

CHAPTER_2_COMPLETE = [
    {"speaker": "Sera", "text": "Khu rừng phía bắc... người ta nói ký ức bị nguyền rủa hiện hình ở đó.",
     "color": SERA_COLOR},
    {"speaker": "Kael", "text": "(Ký ức... liệu đó có phải cổng vào cõi giữa?)",
     "color": KAEL_COLOR},
]

# ======================== CHƯƠNG 3 — KHU RỪNG KÝ ỨC ========================
CHAPTER_3_INTRO = [
    {"speaker": "", "text": "Khu rừng nguyền rủa — nơi ký ức tội lỗi hiện thành hình.",
     "color": NARRATOR_COLOR},
    {"speaker": "Sera", "text": "Quái vật ở đây... trông giống người thật.",
     "color": SERA_COLOR},
    {"speaker": "Kael", "text": "Đó là... hình dạng những nạn nhân của tôi.",
     "color": KAEL_COLOR},
    {"speaker": "Sera", "text": "Nạn nhân? Ngươi nói gì?",
     "color": SERA_COLOR},
]

CHAPTER_3_TRUTH = [
    {"speaker": "Sera", "text": "Tôi đã tìm hiểu về ngươi, Kael Duskborne.",
     "color": SERA_COLOR},
    {"speaker": "Sera", "text": "Cựu Pháp Sư Hắc Ám. Tay sai của Malphas. KẺ THỰC HIỆN NGHI LỄ ĐÊM TẬN THẾ.",
     "color": SERA_COLOR},
    {"speaker": "Kael", "text": "...",
     "color": KAEL_COLOR},
    {"speaker": "Sera", "text": "Ngươi giam cầm linh hồn em tôi. VÀ NGƯƠI CÒN DÁM NÓI SẼ GIÚP?!",
     "color": SERA_COLOR},
    {"speaker": "Kael", "text": "Cô nói đúng. Tôi là kẻ gây ra tất cả.",
     "color": KAEL_COLOR},
    {"speaker": "Kael", "text": "Nhưng tôi là người duy nhất có thể sửa chữa. Hãy để tôi cứu Lyra.",
     "color": KAEL_COLOR},
    {"speaker": "Sera", "text": "... Nếu ngươi dám phản bội. Tôi sẽ tự tay kết liễu ngươi.",
     "color": SERA_COLOR},
]

CHAPTER_3_COMPLETE = [
    {"speaker": "", "text": "Cổng vào cõi giữa đã mở. Ánh sáng ma quái tỏa ra từ bên trong.",
     "color": NARRATOR_COLOR},
]

# ======================== CHƯƠNG 4 — CÕI GIỮA ========================
CHAPTER_4_INTRO = [
    {"speaker": "", "text": "Cõi giữa — thế giới giữa sự sống và cái chết.",
     "color": NARRATOR_COLOR},
    {"speaker": "", "text": "Không có quái vật thường — chỉ có bẫy và câu đố.",
     "color": NARRATOR_COLOR},
    {"speaker": "Kael", "text": "Nơi này... không tuân theo quy luật nào.",
     "color": KAEL_COLOR},
]

CHAPTER_4_SHADOW_BOSS = [
    {"speaker": "", "text": "Một bóng ma xuất hiện... mang hình dạng Kael trong quá khứ.",
     "color": NARRATOR_COLOR},
    {"speaker": "Bóng Ma Kael", "text": "Ngươi nghĩ mình đã thay đổi? Ngươi VẪN là tôi.",
     "color": MALPHAS_COLOR},
    {"speaker": "Kael", "text": "Không. Tôi không còn là ngươi nữa.",
     "color": KAEL_COLOR},
]

CHAPTER_4_LYRA = [
    {"speaker": "Lyra", "text": "Anh... Kael? Anh thật sao?",
     "color": LYRA_COLOR},
    {"speaker": "Kael", "text": "Lyra! Em vẫn ổn?",
     "color": KAEL_COLOR},
    {"speaker": "Lyra", "text": "Em bị giam ở đây... là chìa khóa phong ấn của Malphas.",
     "color": LYRA_COLOR},
    {"speaker": "Lyra", "text": "Để giải phóng em... anh phải hy sinh linh hồn mình.",
     "color": LYRA_COLOR},
    {"speaker": "Kael", "text": "... Anh biết. Anh sẵn sàng.",
     "color": KAEL_COLOR},
    {"speaker": "Sera", "text": "Không! Phải có cách khác!",
     "color": SERA_COLOR},
]

CHAPTER_4_COMPLETE = [
    {"speaker": "", "text": "Phong ấn lung lay. Malphas đang chờ ở trung tâm cõi giữa.",
     "color": NARRATOR_COLOR},
]

# ======================== CHƯƠNG 5 — BOSS CUỐI ========================
CHAPTER_5_INTRO = [
    {"speaker": "", "text": "Ngai vàng bóng tối. Trung tâm cõi giữa.",
     "color": NARRATOR_COLOR},
    {"speaker": "Malphas", "text": "Cuối cùng ngươi cũng đến, Kael.",
     "color": MALPHAS_COLOR},
    {"speaker": "Malphas", "text": "Ta đã chờ đợi khoảnh khắc này... từ rất lâu.",
     "color": MALPHAS_COLOR},
    {"speaker": "Kael", "text": "Malphas. Mọi thứ kết thúc ở đây.",
     "color": KAEL_COLOR},
    {"speaker": "Malphas", "text": "Kết thúc? Không, đây mới là khởi đầu thật sự.",
     "color": MALPHAS_COLOR},
    {"speaker": "Malphas", "text": "Ta chỉ là một ông già hấp hối... dùng ngươi như công cụ để trốn cái chết.",
     "color": MALPHAS_COLOR},
    {"speaker": "Kael", "text": "Thì giờ... cái chết đến đón ngươi.",
     "color": KAEL_COLOR},
]

# ======================== 3 KẾT THÚC ========================
ENDING_TRAGIC = [
    {"speaker": "", "text": "=== KẾT THÚC: BI KỊCH ===", "color": MALPHAS_COLOR},
    {"speaker": "", "text": "Kael hy sinh linh hồn mình để phá dấu ấn.",
     "color": NARRATOR_COLOR},
    {"speaker": "Lyra", "text": "Anh... không! Anh Kael!",
     "color": LYRA_COLOR},
    {"speaker": "Kael", "text": "Sống tốt nhé, Lyra. Anh xin lỗi... vì tất cả.",
     "color": KAEL_COLOR},
    {"speaker": "", "text": "Ánh sáng trở lại Valdris. Kael biến mất vĩnh viễn.",
     "color": NARRATOR_COLOR},
    {"speaker": "", "text": "Lyra tự do. Nhưng cái giá là mãi mãi mất đi người anh.",
     "color": NARRATOR_COLOR},
]

ENDING_NEUTRAL = [
    {"speaker": "", "text": "=== KẾT THÚC: TRUNG LẬP ===", "color": YELLOW},
    {"speaker": "", "text": "Kael phá dấu ấn mà không hy sinh — nhưng không hoàn toàn.",
     "color": NARRATOR_COLOR},
    {"speaker": "", "text": "Một nửa Valdris phục hồi. Nửa còn lại vẫn chìm trong bóng tối.",
     "color": NARRATOR_COLOR},
    {"speaker": "Kael", "text": "Chưa đủ... nhưng ít nhất Lyra đã an toàn.",
     "color": KAEL_COLOR},
    {"speaker": "Sera", "text": "Chúng ta sẽ tìm cách cứu phần còn lại. Cùng nhau.",
     "color": SERA_COLOR},
]

ENDING_REDEMPTION = [
    {"speaker": "", "text": "=== KẾT THÚC: CỨU CHUỘC ===", "color": LYRA_COLOR},
    {"speaker": "Sera", "text": "Kael... để tôi.",
     "color": SERA_COLOR},
    {"speaker": "Kael", "text": "Sera?! Không, cô không thể—",
     "color": KAEL_COLOR},
    {"speaker": "Sera", "text": "Lyra cần anh trai. Valdris cần người chuộc lỗi. Tôi... đã tìm thấy ý nghĩa.",
     "color": SERA_COLOR},
    {"speaker": "", "text": "Sera hy sinh thay Kael. Ánh sáng hoàn toàn trở lại.",
     "color": NARRATOR_COLOR},
    {"speaker": "", "text": "Kael dành cả đời còn lại để chuộc lỗi — và nhớ về Sera.",
     "color": NARRATOR_COLOR},
]

# Mapping cho dễ truy cập
CHAPTER_DIALOGUES = {
    1: {"intro": CHAPTER_1_INTRO, "special": CHAPTER_1_DIARY, "complete": CHAPTER_1_COMPLETE},
    2: {"intro": CHAPTER_2_INTRO, "special": CHAPTER_2_MEET_SERA, "complete": CHAPTER_2_COMPLETE},
    3: {"intro": CHAPTER_3_INTRO, "special": CHAPTER_3_TRUTH, "complete": CHAPTER_3_COMPLETE},
    4: {"intro": CHAPTER_4_INTRO, "special": CHAPTER_4_SHADOW_BOSS,
        "lyra": CHAPTER_4_LYRA, "complete": CHAPTER_4_COMPLETE},
    5: {"intro": CHAPTER_5_INTRO},
}

ENDINGS = {
    "tragic": ENDING_TRAGIC,
    "neutral": ENDING_NEUTRAL,
    "redemption": ENDING_REDEMPTION,
}
