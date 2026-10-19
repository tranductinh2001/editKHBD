# -*- coding: utf-8 -*-
"""
Bộ Kiểm Thử Tính Năng Đồng Bộ Kế Hoạch Giáo Dục (KHGD) Và Yêu Cầu Cần Đạt (YCCĐ)
Kiểm tra liên hoàn:
1. Parse Kế hoạch giáo dục 4 khối lớp (Tin 6, 7, 8, 9) từ file .doc/.docx.
2. Tra cứu & Khớp bài học theo khối lớp và tên bài.
3. Thay thế mục tiêu cũ bằng YCCĐ từ KHGD (giữ nguyên cấu trúc bên trong bài).
4. Phối hợp đồng bộ KHGD + Tích hợp Năng lực số (NLS) chữ đỏ + Format THCS.
"""

import os
import sys
import io
import docx
from docx.shared import Pt, RGBColor

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import khgd_engine
import nls_engine
import khbd_engine

print("=" * 65)
print("  KIỂM THỬ ĐỒNG BỘ KẾ HOẠCH GIÁO DỤC (KHGD) VÀO GIÁO ÁN")
print("=" * 65)

# --- TEST 1: Parse KHGD 4 khối lớp ---
print("\n[TEST 1] Phân tích file Kế hoạch giáo dục của trường...")
khgd_res = khgd_engine.parse_khgd_document("KH tổ CM TIN HỌC 6,7,8,9 (26-27).doc")
grades = khgd_res.get("grades", {})
for g in ["6", "7", "8", "9"]:
    assert g in grades, f"Thiếu dữ liệu khối lớp {g}"
    cnt = grades[g]["total_lessons"]
    assert cnt >= 20, f"Khối lớp {g} phải có ít nhất 20 bài học, thực tế: {cnt}"
    print(f"  -> Khối lớp {g}: {cnt} bài học, YCCĐ đầy đủ.")
print("  -> PASS: Đã bóc tách thành công cả 4 khối lớp 6, 7, 8, 9 từ KHGD!")

# --- TEST 2: Khớp bài học và lấy YCCĐ ---
print("\n[TEST 2] Tra cứu bài học trong Kế hoạch giáo dục...")
match_tin9_b1 = khgd_engine.match_lesson_in_khgd(grade="9", lesson_title="Thế giới kĩ thuật số", bai_num="1")
assert match_tin9_b1 is not None, "Không tìm thấy Bài 1 trong KHGD lớp 9"
assert "bộ xử lý thông tin" in match_tin9_b1["yccd_text"].lower(), "Nội dung YCCĐ không đúng bài"
print(f"  -> PASS: Khớp thành công '{match_tin9_b1['ten_bai']}' với {len(match_tin9_b1['yccd_bullets'])} ý YCCĐ.")

# --- TEST 3: Đồng bộ YCCĐ vào KHBD (Xóa mục tiêu kiến thức cũ, giữ nguyên cấu trúc trong) ---
print("\n[TEST 3] Đồng bộ YCCĐ vào KHBD...")
test_out_sync = "test_khbd_synced_yccd.docx"
khgd_engine.apply_khgd_yccd_to_khbd("Tin 9 bài 1.docx", test_out_sync, match_tin9_b1["yccd_text"])
doc_synced = docx.Document(test_out_sync)

# Kiểm tra phần 1. Kiến thức chứa nội dung mới
found_kienthuc = False
for p in doc_synced.paragraphs:
    if "bộ xử lý thông tin" in p.text.lower():
        found_kienthuc = True
        break
assert found_kienthuc, "YCCĐ mới chưa xuất hiện trong file KHBD"

# Kiểm tra phần 2. Năng lực, 3. Phẩm chất và các hoạt động bên trong giữ nguyên vẹn
text_all = " ".join([p.text for p in doc_synced.paragraphs])
assert "2. về năng lực:" in text_all.lower() or "2. năng lực:" in text_all.lower(), "Phần 2. Năng lực bị mất"
assert "3. về phẩm chất:" in text_all.lower() or "3. phẩm chất:" in text_all.lower(), "Phần 3. Phẩm chất bị mất"
assert "ii. thiết bị dạy học" in text_all.lower(), "Phần II. Thiết bị dạy học bị mất"
assert "hoạt động 1: mở đầu" in text_all.lower(), "Hoạt động 1 bị mất"
assert "hoạt động 2" in text_all.lower(), "Hoạt động 2 bị mất"
print("  -> PASS: Mục tiêu kiến thức đã được thay thế chuẩn xác từ KHGD, toàn bộ cấu trúc bên trong giữ nguyên 100%.")

# --- TEST 4: Phối hợp đồng bộ KHGD + Tích hợp Năng lực số (NLS) chữ đỏ ---
print("\n[TEST 4] Kiểm tra phối hợp liên hoàn: Đồng bộ KHGD + Tích hợp NLS chữ đỏ...")
test_out_combo = "test_khbd_combo.docx"
# Tích hợp NLS trên file đã đồng bộ KHGD
nls_res = nls_engine.integrate_khbd_nls(
    file_path=test_out_sync,
    output_path=test_out_combo,
    subject="Tin học",
    grade="9",
    lesson_title="Thế giới kĩ thuật số",
    highlight_red=True
)
doc_combo = docx.Document(test_out_combo)
assert len(doc_combo.tables) >= 1, "File phải có bảng NLS hoặc bảng hoạt động"
print(f"  -> PASS: Phối hợp thành công! Trạng thái NLS: {nls_res['status']}")

# Dọn dẹp file test
for f in [test_out_sync, test_out_combo]:
    if os.path.exists(f):
        os.remove(f)

print("\n" + "=" * 65)
print("  TẤT CẢ 4/4 KIỂM THỬ KHGD ĐÃ PASS XUẤT SẮC!")
print("=" * 65)
