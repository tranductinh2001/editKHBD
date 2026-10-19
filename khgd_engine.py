# -*- coding: utf-8 -*-
"""
KHGD Engine - Module Quản lý, Phân tích Kế hoạch giáo dục (KHGD môn học) của trường
và Đồng bộ Yêu cầu cần đạt (YCCĐ) vào Kế hoạch bài dạy (KHBD).
"""

import os
import re
import sys
import io
import json
import shutil
from pathlib import Path
import unicodedata
import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl

import beeknoee_client

BASE_DIR = Path(__file__).resolve().parent
KHGD_DIR = BASE_DIR / "KHGD"
KHGD_DIR.mkdir(exist_ok=True)
CACHE_FILE = KHGD_DIR / "khgd_cache.json"

def remove_vietnamese_accents(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text.lower().strip()

def convert_doc_to_docx(file_path):
    """
    Chuyển đổi file .doc (Word 97-2003) sang .docx bằng Word COM trên Windows
    Nếu file đã là .docx thì trả về chính nó.
    """
    if file_path.lower().endswith(".docx"):
        return file_path
    
    if not file_path.lower().endswith(".doc"):
        return None

    docx_path = file_path + "x"
    # Kiểm tra nếu docx đã tồn tại và mới hơn file doc thì tái sử dụng
    if os.path.exists(docx_path) and os.path.getmtime(docx_path) >= os.path.getmtime(file_path):
        return docx_path

    try:
        import win32com.client
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Open(os.path.abspath(file_path))
        doc.SaveAs2(os.path.abspath(docx_path), FileFormat=16) # 16 = wdFormatXMLDocument (.docx)
        doc.Close()
        word.Quit()
        return docx_path
    except Exception as e:
        print(f"Error converting .doc to .docx via Word COM: {e}")
        if os.path.exists(docx_path):
            return docx_path
        return None

def parse_khgd_document(file_path):
    """
    Phân tích file Kế hoạch giáo dục của trường (hỗ trợ cả .doc và .docx)
    Tách ra danh sách bài học và Yêu cầu cần đạt (YCCĐ) theo từng khối lớp (6, 7, 8, 9).
    """
    target_docx = convert_doc_to_docx(file_path)
    if not target_docx or not os.path.exists(target_docx):
        raise Exception(f"Không thể mở hoặc chuyển đổi file: {file_path}")

    doc = docx.Document(target_docx)
    grades_data = {}
    
    # 1. Lọc các bảng phân phối chương trình bài học chính:
    # - Số hàng > 10
    # - Hàng tiêu đề có 'bài học' hoặc 'tên bài'
    # - KHÔNG phải bảng kiểm tra đánh giá (loại bỏ 'bài kiểm tra')
    ppct_tables = []
    for t_idx, table in enumerate(doc.tables):
        if len(table.rows) < 10:
            continue
        hdr_texts = [c.text.strip().lower() for c in table.rows[0].cells]
        if any("kiểm tra" in h or "đánh giá" in h for h in hdr_texts):
            continue
        has_lesson = any("bài học" in h or "tên bài" in h or "nội dung" in h for h in hdr_texts)
        has_stt = any("stt" in h or "tt" in h for h in hdr_texts)
        if has_lesson or (has_stt and len(table.rows) >= 15):
            ppct_tables.append((t_idx, table))

    body = doc.element.body
    for t_idx, table in ppct_tables:
        tbl_elem = table._tbl
        tbl_pos = body.index(tbl_elem)
        
        # Xác định khối lớp (6, 7, 8, 9) bằng cách quét ngược lên trước bảng
        detected_grade = None
        for k in range(tbl_pos - 1, max(-1, tbl_pos - 35), -1):
            el = body[k]
            if el.tag.endswith('p'):
                text = el.text.strip()
                t_lower = text.lower()
                m = re.search(r'(?:tin học|khối|lớp)\s*([6789])', t_lower)
                if m:
                    detected_grade = m.group(1)
                    break
        
        # Fallback theo thứ tự bảng
        if not detected_grade:
            used_grades = list(grades_data.keys())
            for g in ["6", "7", "8", "9"]:
                if g not in used_grades:
                    detected_grade = g
                    break
        if not detected_grade:
            detected_grade = f"grade_{len(grades_data) + 1}"

        lessons = []
        current_topic = ""
        
        # Xác định cột
        hdr_cells = table.rows[0].cells
        col_stt = 0
        col_lesson = 1
        col_period = 2
        col_yccd = len(hdr_cells) - 1

        for c_i, c in enumerate(hdr_cells):
            t_low = c.text.strip().lower()
            if "stt" in t_low:
                col_stt = c_i
            elif "bài học" in t_low or "tên bài" in t_low:
                col_lesson = c_i
            elif "số tiết" in t_low:
                col_period = c_i
            elif "yêu cầu cần đạt" in t_low:
                col_yccd = c_i

        for row_idx, row in enumerate(table.rows[1:]):
            cells = row.cells
            if len(cells) <= max(col_stt, col_lesson, col_yccd):
                continue
            
            # Kiểm tra hàng gộp (Chủ đề / Học kì)
            unique_texts = []
            for c in cells:
                ct = c.text.strip()
                if not unique_texts or ct != unique_texts[-1]:
                    unique_texts.append(ct)
            
            if len(unique_texts) == 1 and any(k in unique_texts[0].lower() for k in ["chủ đề", "học kì", "học kỳ"]):
                current_topic = unique_texts[0]
                continue

            stt_val = cells[col_stt].text.strip()
            lesson_val = cells[col_lesson].text.strip().replace("\n", " ")
            period_val = cells[col_period].text.strip() if len(cells) > col_period else ""
            yccd_val = cells[col_yccd].text.strip()

            if stt_val.lower().startswith("stt") or not lesson_val:
                continue

            # Tách số bài và tên bài
            m_bai = re.search(r'b[aà]i\s*(\d+)[\.\:\s]*(.*)', lesson_val, re.IGNORECASE)
            if m_bai:
                b_num = m_bai.group(1).strip()
                b_title = m_bai.group(2).strip()
            else:
                b_num = stt_val if stt_val.isdigit() else ""
                b_title = lesson_val

            # Chuẩn hóa gạch đầu dòng YCCĐ
            formatted_yccd = []
            for line in yccd_val.split("\n"):
                line_str = line.strip()
                if line_str:
                    line_str = re.sub(r'^[˗\-\•\*\+]\s*', '', line_str)
                    formatted_yccd.append(f"- {line_str}")

            lessons.append({
                "stt": stt_val,
                "bai_num": b_num,
                "ten_bai": lesson_val,
                "bai_title": b_title,
                "so_tiet": period_val,
                "chu_de": current_topic,
                "yccd_raw": yccd_val,
                "yccd_bullets": formatted_yccd,
                "yccd_text": "\n".join(formatted_yccd)
            })

        if lessons:
            grades_data[detected_grade] = {
                "grade": detected_grade,
                "total_lessons": len(lessons),
                "lessons": lessons
            }

    result = {
        "source_file": os.path.basename(file_path),
        "source_docx": os.path.basename(target_docx),
        "grades": grades_data
    }
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print("Error saving KHGD cache:", e)

    return result

def load_cached_khgd():
    """Tải dữ liệu Kế hoạch giáo dục từ cache nếu có"""
    if CACHE_FILE.exists():
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return None
    return None

def match_lesson_in_khgd(grade, lesson_title, bai_num=None, khgd_data=None):
    """
    Tìm kiếm bài học tương ứng trong Kế hoạch giáo dục của khối lớp:
    1. So khớp theo số bài (bai_num) nếu có.
    2. So khớp theo tên bài (xâu ký tự bỏ dấu).
    """
    if not khgd_data:
        khgd_data = load_cached_khgd()
    if not khgd_data or "grades" not in khgd_data:
        return None

    grade_key = str(grade).strip()
    grade_info = khgd_data["grades"].get(grade_key)
    if not grade_info:
        for k, v in khgd_data["grades"].items():
            if grade_key in k:
                grade_info = v
                break
    if not grade_info:
        return None

    lessons = grade_info.get("lessons", [])

    # 1. Tìm theo bai_num
    if bai_num and str(bai_num).strip().isdigit():
        num_str = str(bai_num).strip()
        for item in lessons:
            if item.get("bai_num") == num_str:
                return item

    # 2. Tìm theo tên bài
    clean_search = remove_vietnamese_accents(lesson_title)
    clean_search = re.sub(r'^b[aà]i\s*\d+[\.\:\s]*', '', clean_search).strip()

    best_match = None
    best_score = 0
    for item in lessons:
        item_title = remove_vietnamese_accents(item.get("bai_title", ""))
        
        if clean_search and (clean_search in item_title or item_title in clean_search):
            return item

        words_search = set(clean_search.split())
        words_item = set(item_title.split())
        common = len(words_search.intersection(words_item))
        if common > best_score and common >= 2:
            best_score = common
            best_match = item

    return best_match

def apply_khgd_yccd_to_khbd(file_path, output_path, yccd_text, highlight_color=None):
    """
    Đồng bộ Yêu cầu cần đạt từ Kế hoạch giáo dục vào Kế hoạch bài dạy (KHBD):
    - Tìm thấy phần 'I. Mục tiêu' -> '1. Về kiến thức:'
    - Xóa các gạch đầu dòng kiến thức cũ dưới mục 1
    - Thay thế bằng các gạch đầu dòng YCCĐ mới từ Kế hoạch giáo dục
    - GIỮ NGUYÊN 100% cấu trúc còn lại: Phần 2 (Năng lực), Phần 3 (Phẩm chất), Phần II, Phần III.
    """
    doc = docx.Document(file_path)
    
    target_kienthuc_idx = -1
    for idx, p in enumerate(doc.paragraphs):
        p_text = p.text.strip().lower()
        if any(p_text.startswith(x) for x in ["1. về kiến thức", "1. kiến thức", "1.về kiến thức", "1.kiến thức"]):
            target_kienthuc_idx = idx
            break

    if target_kienthuc_idx == -1:
        for idx, p in enumerate(doc.paragraphs):
            p_text = p.text.strip().lower()
            if "i. mục tiêu" in p_text:
                target_kienthuc_idx = idx
                break

    if target_kienthuc_idx == -1:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        doc.save(output_path)
        return output_path

    paragraphs_to_remove = []
    insert_after_para = doc.paragraphs[target_kienthuc_idx]
    
    for idx in range(target_kienthuc_idx + 1, min(len(doc.paragraphs), target_kienthuc_idx + 15)):
        p = doc.paragraphs[idx]
        p_text = p.text.strip().lower()
        if any(p_text.startswith(x) for x in ["2. về năng lực", "2. năng lực", "2.1.", "3. về phẩm chất", "ii. thiết bị"]):
            break
        paragraphs_to_remove.append(p)

    body = doc.element.body
    for p in paragraphs_to_remove:
        body.remove(p._p)

    lines = [l.strip() for l in yccd_text.split("\n") if l.strip()]
    if not lines:
        lines = ["- Theo yêu cầu cần đạt của bài học trong Kế hoạch giáo dục nhà trường."]

    ref_element = insert_after_para._p
    for line in lines:
        if not line.startswith("-") and not line.startswith("+") and not line.startswith("˗"):
            line = f"- {line}"
            
        p_new = doc.add_paragraph()
        p_new.paragraph_format.line_spacing = 1.15
        p_new.paragraph_format.space_before = Pt(1)
        p_new.paragraph_format.space_after = Pt(2)
        
        run = p_new.add_run(line)
        run.font.name = "Times New Roman"
        run.font.size = Pt(13)
        if highlight_color:
            run.font.color.rgb = highlight_color

        ref_element.addnext(p_new._p)
        ref_element = p_new._p

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    doc.save(output_path)
    return output_path
