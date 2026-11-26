#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tạo 4 ảnh minh họa & ảnh chụp màn hình tin nhắn cho Video Tập 1 v3 ("2 cánh 2 hướng vân")
1. door_mismatch.png: Cửa thép vân gỗ 2 cánh (trái vân dọc, phải vân ngang, khoanh đỏ)
2. msg_khach_sang.png: Ảnh chụp tin nhắn khách hàng có chữ "cho nó sang"
3. msg_truong_ok.png: Ảnh chụp tin nhắn cũ của Trưởng: "OK làm đi, khách gấp"
4. msg_thuhoi_capture.png: Ảnh chụp tin nhắn "Lỗi này bộ phận nào tự xử nhé" trước khi thu hồi
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent / "assets" / "ep1_v3"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def font(size: int, bold: bool = False):
    path = r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf"
    if not os.path.exists(path):
        path = r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf"
    return ImageFont.truetype(path, size)


def make_door_mismatch():
    """Cửa 2 cánh vân gỗ: cánh trái vân dọc, cánh phải vân ngang, khoanh đỏ chỗ lệch"""
    W, H = 680, 480
    im = Image.new("RGB", (W, H), (235, 232, 226))
    d = ImageDraw.Draw(im)

    # Tường sáng nhẹ + nền gạch
    d.rectangle([0, 410, W, H], fill=(195, 190, 182))
    # Khung bao cửa thép nâu đậm
    d.rectangle([120, 35, 560, 420], fill=(88, 42, 24), outline=(55, 25, 14), width=5)

    # Cánh trái (vân chạy DỌC)
    lx0, ly0, lx1, ly1 = 142, 56, 336, 412
    d.rectangle([lx0, ly0, lx1, ly1], fill=(154, 78, 42), outline=(72, 32, 16), width=3)
    for x in range(lx0 + 10, lx1 - 6, 12):
        col = (130, 62, 32) if (x // 12) % 2 == 0 else (168, 92, 52)
        d.line([(x, ly0 + 6), (x, ly1 - 6)], fill=col, width=3)
    # Pano dọc bên trái
    d.rectangle([lx0 + 26, ly0 + 36, lx1 - 26, ly0 + 170], outline=(95, 42, 20), width=4)
    d.rectangle([lx0 + 26, ly0 + 195, lx1 - 26, ly1 - 32], outline=(95, 42, 20), width=4)

    # Cánh phải (vân chạy NGANG)
    rx0, ry0, rx1, ry1 = 344, 56, 538, 412
    d.rectangle([rx0, ry0, rx1, ry1], fill=(154, 78, 42), outline=(72, 32, 16), width=3)
    for y in range(ry0 + 10, ry1 - 6, 12):
        col = (126, 60, 30) if (y // 12) % 2 == 0 else (172, 95, 54)
        d.line([(rx0 + 6, y), (rx1 - 6, y)], fill=col, width=3)
    # Pano bên phải
    d.rectangle([rx0 + 26, ry0 + 36, rx1 - 26, ry0 + 170], outline=(95, 42, 20), width=4)
    d.rectangle([rx0 + 26, ry0 + 195, rx1 - 26, ry1 - 32], outline=(95, 42, 20), width=4)

    # Tay nắm cửa giữa
    d.rounded_rectangle([322, 215, 332, 275], radius=4, fill=(225, 195, 110))
    d.rounded_rectangle([348, 215, 358, 275], radius=4, fill=(225, 195, 110))

    # Khoanh đỏ chỗ khác nhau ở cả 2 cánh + nhãn DỌC / NGANG
    d.ellipse([156, 76, 322, 224], outline=(239, 68, 68), width=7)
    d.ellipse([358, 76, 524, 224], outline=(239, 68, 68), width=7)

    f_lbl = font(24, bold=True)
    d.rounded_rectangle([166, 22, 314, 58], radius=10, fill=(220, 38, 38))
    d.text((190, 26), "VÂN DỌC", font=f_lbl, fill=(255, 255, 255))

    d.rounded_rectangle([356, 22, 526, 58], radius=10, fill=(220, 38, 38))
    d.text((374, 26), "VÂN NGANG", font=f_lbl, fill=(255, 255, 255))

    # Mũi tên chỉ 2 hướng vân
    d.line([(239, 105), (239, 195)], fill=(254, 240, 138), width=5)
    d.polygon([(239, 95), (229, 113), (249, 113)], fill=(254, 240, 138))
    d.polygon([(239, 205), (229, 187), (249, 187)], fill=(254, 240, 138))

    d.line([(395, 150), (485, 150)], fill=(254, 240, 138), width=5)
    d.polygon([(385, 150), (403, 140), (403, 160)], fill=(254, 240, 138))
    d.polygon([(495, 150), (477, 140), (477, 160)], fill=(254, 240, 138))

    im.save(OUT_DIR / "door_mismatch.png")


def make_chat_screenshot(filename: str, sender: str, badge_text: str, time_str: str, msg_text: str, highlight_sub: str = None, avatar_col=(30, 58, 138), initials="AK"):
    """Tạo ảnh chụp màn hình đoạn chat Zalo/Messenger chân thật"""
    W, H = 640, 210
    im = Image.new("RGB", (W, H), (241, 245, 249))
    d = ImageDraw.Draw(im)

    # Viền khung screenshot nhẹ
    d.rounded_rectangle([4, 4, W - 5, H - 5], radius=20, fill=(248, 250, 252), outline=(203, 213, 225), width=2)

    # Header nhỏ "Ảnh chụp màn hình"
    d.text((22, 14), f"{sender} • {time_str}", font=font(20, bold=True), fill=(71, 85, 105))
    if badge_text:
        bb = d.textbbox((0, 0), badge_text, font=font(18, bold=True))
        bw = bb[2] - bb[0] + 20
        d.rounded_rectangle([W - bw - 18, 12, W - 18, 40], radius=8, fill=(226, 232, 240))
        d.text((W - bw - 8, 14), badge_text, font=font(18, bold=True), fill=(51, 65, 85))

    # Avatar tròn
    d.ellipse([20, 64, 84, 128], fill=avatar_col)
    f_av = font(26, bold=True)
    ab = d.textbbox((0, 0), initials, font=f_av)
    d.text((52 - (ab[2] - ab[0]) // 2, 96 - (ab[3] - ab[1]) // 2 - 4), initials, font=f_av, fill=(255, 255, 255))

    # Bong bóng tin nhắn trắng
    bx0, by0, bx1, by1 = 100, 62, W - 24, 178
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=22, fill=(255, 255, 255), outline=(226, 232, 240), width=2)

    f_msg = font(27, bold=False)
    if highlight_sub and highlight_sub in msg_text:
        pre, mid, post = msg_text.partition(highlight_sub)
        cx, cy = bx0 + 22, by0 + 38
        for seg, is_hl in [(pre, False), (mid, True), (post, False)]:
            if not seg:
                continue
            sb = d.textbbox((0, 0), seg, font=font(27, bold=is_hl))
            sw = sb[2] - sb[0]
            if cx + sw > bx1 - 18:
                cx = bx0 + 22
                cy += 38
            if is_hl:
                d.rounded_rectangle([cx - 5, cy - 2, cx + sw + 5, cy + 36], radius=6, fill=(254, 240, 138))
                d.text((cx, cy), seg, font=font(27, bold=True), fill=(185, 28, 28))
            else:
                d.text((cx, cy), seg, font=f_msg, fill=(15, 23, 42))
            cx += sw
    else:
        d.text((bx0 + 22, by0 + 38), msg_text, font=font(28, bold=True), fill=(15, 23, 42))

    im.save(OUT_DIR / filename)


if __name__ == "__main__":
    make_door_mismatch()
    make_chat_screenshot(
        "msg_khach_sang.png",
        sender="Anh Khánh (Khách)",
        badge_text="Tin nhắn cũ",
        time_str="T2 14:20",
        msg_text='Làm mẫu nào "cho nó sang" em nhé',
        highlight_sub='"cho nó sang"',
        avatar_col=(14, 116, 144),
        initials="AK",
    )
    make_chat_screenshot(
        "msg_truong_ok.png",
        sender="Trưởng phòng TK",
        badge_text="Đã duyệt",
        time_str="Thứ 3 • 09:15",
        msg_text="OK làm đi, khách gấp",
        highlight_sub="OK làm đi",
        avatar_col=(30, 58, 138),
        initials="TP",
    )
    make_chat_screenshot(
        "msg_thuhoi_capture.png",
        sender="Trưởng phòng TK",
        badge_text="Đã chụp lại",
        time_str="16:50",
        msg_text="Chắc Hải chụp ngược sáng nhìn lú đấy",
        highlight_sub="chụp ngược sáng",
        avatar_col=(30, 58, 138),
        initials="TP",
    )
    print("Created all 4 ep1_v3 assets in:", OUT_DIR)
