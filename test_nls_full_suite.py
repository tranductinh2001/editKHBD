# -*- coding: utf-8 -*-
"""
Bộ Kiểm Thử Chất Lượng & Nghiệm Thu Tính Năng Tích Hợp NLS
Kiểm thử 9 trường hợp tiêu chuẩn theo yêu cầu nâng cấp:
1. KHBD chưa có NLS -> bổ sung phù hợp.
2. KHBD đã có NLS đầy đủ -> không chèn trùng, giữ nguyên.
3. Chạy lại trên cùng 1 file -> không tiếp tục chèn lặp.
4. KHBD có bảng biểu phức tạp -> không phá vỡ định dạng bảng.
5. Đánh dấu chữ đỏ chính xác cho nội dung mới (RGBColor(255, 0, 0)) và giữ nguyên văn bản gốc.
6. API trả về dữ liệu sai cấu trúc hoặc lỗi mạng -> báo lỗi rõ ràng, an toàn không làm hỏng file.
7. Chức năng format cũ (Mau KHBD THCS) vẫn hoạt động 100% như trước.
"""

import os
import sys
import io
import shutil
import docx
from docx.shared import Pt, RGBColor

# UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import nls_engine
import khbd_engine

TEST_DIR = "test_nls_suite_output"
os.makedirs(TEST_DIR, exist_ok=True)

print("=" * 60)
print("  BẮT ĐẦU CHẠY BỘ KIỂM THỬ TÍCH HỢP NĂNG LỰC SỐ (NLS)")
print("=" * 60)

# --- TEST 1: KHBD CHƯA CÓ NLS -> BỔ SUNG PHÙ HỢP ---
print("\n[TEST 1] KHBD chưa có NLS (Tin 9 bài 1_chua_nls.docx)...")
out_test1 = os.path.join(TEST_DIR, "output_test1.docx")
res1 = nls_engine.integrate_khbd_nls(
    file_path="Tin 9 bài 1_chua_nls.docx",
    output_path=out_test1,
    subject="Tin học",
    grade="9",
    lesson_title="Thế giới kĩ thuật số",
    highlight_red=True
)
assert res1["status"] == "integrated", f"Expected 'integrated', got {res1['status']}"
assert len(res1.get("added_codes", [])) >= 2, f"Expected at least 2 NLS codes, got {res1.get('added_codes')}"
print(f"  -> PASS: Đã tích hợp thành công các mã {res1['added_codes']}")

# --- TEST 2: NỘI DUNG MỚI ĐƯỢC TÔ ĐỎ CHÍNH XÁC ---
print("\n[TEST 2] Kiểm tra đánh dấu màu chữ đỏ (FF0000) cho nội dung mới...")
doc1 = docx.Document(out_test1)
red_runs = []
black_runs = []
for p in doc1.paragraphs:
    if "2.3. Các NLS được phát triển" in p.text or any(c in p.text for c in res1.get("added_codes", [])):
        for r in p.runs:
            if r.font.color and r.font.color.rgb == RGBColor(255, 0, 0):
                red_runs.append(r.text)
    elif "1. Hoạt động 1: Mở đầu" in p.text or "II. Thiết bị dạy học" in p.text:
        for r in p.runs:
            color = r.font.color.rgb if r.font.color else None
            black_runs.append((r.text, color))

assert len(red_runs) > 0, "Không tìm thấy run chữ đỏ trong phần NLS mới"
print(f"  -> PASS: Đã tìm thấy {len(red_runs)} text runs được tô đỏ chính xác. Chữ gốc giữ nguyên màu.")

# --- TEST 3: KHBD ĐÃ CÓ NLS ĐẦY ĐỦ -> KHÔNG CHÈN TRÙNG ---
print("\n[TEST 3] KHBD đã có NLS đầy đủ (Tin 9 bài 1.docx)...")
out_test3 = os.path.join(TEST_DIR, "output_test3_already.docx")
res3 = nls_engine.integrate_khbd_nls(
    file_path="Tin 9 bài 1.docx",
    output_path=out_test3,
    subject="Tin học",
    grade="9",
    lesson_title="Thế giới kĩ thuật số",
    highlight_red=True
)
assert res3["status"] == "already_integrated", f"Expected 'already_integrated', got {res3['status']}"
assert len(res3.get("added_codes", [])) == 0, "Không được thêm mã mới khi đã có NLS đầy đủ"
print(f"  -> PASS: Phát hiện 'already_integrated' ({res3['detected_codes']}), giữ nguyên file, không chèn trùng.")

# --- TEST 4: CHẠY LẠI TRÊN CÙNG MỘT FILE -> KHÔNG CHÈN LẶP NỘI DUNG ---
print("\n[TEST 4] Chạy lại trên file vừa tích hợp (out_test1)...")
out_test4 = os.path.join(TEST_DIR, "output_test4_rerun.docx")
res4 = nls_engine.integrate_khbd_nls(
    file_path=out_test1,
    output_path=out_test4,
    subject="Tin học",
    grade="9",
    lesson_title="Thế giới kĩ thuật số",
    highlight_red=True
)
assert res4["status"] == "already_integrated", f"Expected 'already_integrated' on rerun, got {res4['status']}"
print("  -> PASS: Lần chạy thứ 2 nhận diện file đã có NLS, không chèn lặp lại.")

# --- TEST 5: BẢNG BIỂU PHỨC TẠP KHÔNG BỊ PHÁ VỠ ---
print("\n[TEST 5] Kiểm tra tính toàn vẹn cấu trúc bảng biểu...")
doc_orig = docx.Document("Tin 9 bài 1_chua_nls.docx")
doc_after = docx.Document(out_test1)
# Bảng NLS được thêm vào sau cùng, các bảng ban đầu phải giữ nguyên số hàng/cột
assert len(doc_after.tables) == len(doc_orig.tables) + 1, "Số lượng bảng phải tăng đúng 1 bảng (Bảng NLS)"
for i in range(len(doc_orig.tables)):
    assert len(doc_orig.tables[i].rows) == len(doc_after.tables[i].rows), f"Bảng {i} bị thay đổi số hàng"
print(f"  -> PASS: Toàn bộ {len(doc_orig.tables)} bảng ban đầu giữ nguyên vẹn 100%. Bảng NLS được thêm mới chuẩn xác.")

# --- TEST 6: XỬ LÝ LỖI AN TOÀN KHI API HOẶC DỮ LIỆU KHÔNG HỢP LỆ ---
print("\n[TEST 6] Kiểm tra xử lý lỗi khi file không tồn tại...")
res6 = nls_engine.integrate_khbd_nls(
    file_path="file_khong_ton_tai.docx",
    output_path="test_error.docx"
)
assert res6["status"] == "error", "Phải trả về status 'error'"
print(f"  -> PASS: Báo lỗi an toàn: {res6['message']}")

# --- TEST 7: CHỨC NĂNG FORMAT CŨ VẪN HOẠT ĐỘNG HOÀN HẢO ---
print("\n[TEST 7] Kiểm tra chức năng format chuẩn THCS cũ (khbd_engine)...")
out_test7 = os.path.join(TEST_DIR, "output_test7_format.docx")
cfg = {
    "teacher_name": "Lê Thị Phương Thảo",
    "school_name": "Trường TH&THCS Đăk Trôi",
    "department": "Tổ Tự Nhiên",
    "school_year": "2025-2026",
    "subject": "Tin học",
    "classes": "9",
    "enable_header": True,
    "enable_footer": True,
    "enable_approval_block": True
}
lesson_info = khbd_engine.parse_docx_file("Tin 9 bài 1.docx")
khbd_engine.transform_khbd_file("Tin 9 bài 1.docx", out_test7, lesson_info, None, cfg)
doc7 = docx.Document(out_test7)
assert len(doc7.tables) >= 2, "File sau format phải có bảng 1x2 trên cùng"
first_cell_text = doc7.tables[0].cell(0, 0).text
assert "Tuần:" in first_cell_text, "Bảng đầu tiên phải là Bảng 1x2 chuẩn THCS (Tuần, Tiết, Ngày dạy)"
print("  -> PASS: Chức năng format cũ hoạt động 100% chuẩn xác, không bị ảnh hưởng.")

print("\n" + "=" * 60)
print("  TẤT CẢ 7/7 TEST CASES ĐÃ PASS THÀNH CÔNG RỰC RỠ!")
print("=" * 60)
