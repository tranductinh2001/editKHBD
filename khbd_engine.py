import os
import re
import io
import copy
import shutil
import unicodedata
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter
import docx
from docx.shared import Pt, Inches, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
from datetime import datetime, timedelta

def remove_vietnamese_accents(text):
    if not text:
        return ""
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = text.replace('đ', 'd').replace('Đ', 'D')
    return text

def to_slug(text):
    if not text:
        return ""
    text = remove_vietnamese_accents(text)
    # If all uppercase, convert to Title Case
    if text.isupper():
        text = text.title()
    text = re.sub(r'[^a-zA-Z0-9\s_-]', '', text)
    text = re.sub(r'[\s_]+', '-', text.strip())
    return text.strip('-')

def set_cell_border(cell, **kwargs):
    """
    Set cell borders:
    kwargs: top, bottom, left, right, insideH, insideV
    values: {"val": "single", "sz": "4", "color": "auto", "space": "0"}
    """
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
        edge_data = kwargs.get(edge)
        if edge_data:
            tag = f'w:{edge}'
            element = tcBorders.find(qn(tag))
            if element is None:
                element = OxmlElement(tag)
                tcBorders.append(element)
            for key, attr in [("val", "w:val"), ("color", "w:color"), ("sz", "w:sz"), ("space", "w:space")]:
                if key in edge_data:
                    element.set(qn(attr), str(edge_data[key]))

def update_ppct_file_teaching_dates(file_path, start_date="2026-09-07", date_format="d2_to_d6"):
    """
    Adds or updates 'Ngày dạy theo tuần' column in a PPCT .xlsx file.
    Calculates the teaching date range (e.g. T2 - T6) for each week.
    """
    if not os.path.exists(file_path) or not file_path.endswith(".xlsx") or os.path.basename(file_path).startswith("~$"):
        return False

    fn = os.path.basename(file_path).lower()
    if "đặt tên" in fn or "folder" in fn:
        return False

    try:
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active

        # Find header row
        header_row = -1
        for r in range(1, min(15, sheet.max_row + 1)):
            row_vals = [str(sheet.cell(r, c).value or '').strip().upper() for c in range(1, 15)]
            if any("STT" in v for v in row_vals) and any("TUẦN" in v or "TUAN" in v for v in row_vals):
                header_row = r
                break

        if header_row == -1:
            return False

        col_tuan = -1
        col_ngay = -1
        col_ghi_chu = -1

        for c in range(1, sheet.max_column + 1):
            val = str(sheet.cell(header_row, c).value or '').strip().lower()
            if "ngày" in val or "ngay" in val:
                col_ngay = c
            elif "tuần" in val or "tuan" in val:
                col_tuan = c
            elif "ghi chú" in val or "ghi chu" in val:
                col_ghi_chu = c

        thin = Side(border_style='thin', color='000000')
        border = Border(top=thin, bottom=thin, left=thin, right=thin)
        header_fill = PatternFill(start_color='FFC6E0B4', end_color='FFC6E0B4', fill_type='solid')

        if col_ngay == -1:
            insert_pos = col_ghi_chu if col_ghi_chu != -1 else 5
            sheet.insert_cols(insert_pos)
            col_ngay = insert_pos

            # Update merged cells in rows 2 to 8 to cover new column width
            orig_ranges = list(sheet.merged_cells.ranges)
            for rng in orig_ranges:
                if rng.min_col == 1 and rng.max_col == (insert_pos - 1) and rng.min_row >= 2 and rng.max_row <= 8:
                    try:
                        sheet.unmerge_cells(str(rng))
                        sheet.merge_cells(start_row=rng.min_row, start_column=1, end_row=rng.max_row, end_column=sheet.max_column)
                    except Exception:
                        pass

        # Header styling
        h_cell = sheet.cell(header_row, col_ngay)
        h_cell.value = "Ngày dạy theo tuần"
        h_cell.font = Font(name="Times New Roman", size=11, bold=True)
        h_cell.fill = header_fill
        h_cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        h_cell.border = border

        col_letter = get_column_letter(col_ngay)
        sheet.column_dimensions[col_letter].width = 24.0

        if col_tuan == -1:
            col_tuan = 2

        # Populate rows
        for r in range(header_row + 1, sheet.max_row + 1):
            w_val = sheet.cell(r, col_tuan).value
            cell = sheet.cell(r, col_ngay)
            if w_val is not None and str(w_val).strip():
                d_str = calculate_week_dates(w_val, start_date, date_format)
                cell.value = d_str
            else:
                cell.value = ""
            cell.font = Font(name="Times New Roman", size=11)
            cell.alignment = Alignment(horizontal="center", vertical="center")
            cell.border = border

        wb.save(file_path)
        return True
    except Exception as e:
        print(f"Error updating PPCT dates for {file_path}: {e}")
        return False

def update_all_ppct_teaching_dates(ppct_dir, start_date="2026-09-07", date_format="d2_to_d6"):
    """
    Updates 'Ngày dạy theo tuần' column for all standard PPCT Excel files in ppct_dir.
    """
    if not os.path.exists(ppct_dir):
        return []
    updated = []
    for fn in os.listdir(ppct_dir):
        if fn.endswith(".xlsx") and not fn.startswith("~$"):
            fp = os.path.join(ppct_dir, fn)
            if update_ppct_file_teaching_dates(fp, start_date, date_format):
                updated.append(fn)
    return updated

def load_all_ppct(ppct_dir):
    """
    Scans ppct_dir and parses all .xlsx files into a structured dictionary.
    Supports dynamic columns including 'Ngày dạy theo tuần'.
    """
    ppct_dict = {}
    if not os.path.exists(ppct_dir):
        return ppct_dict

    for fn in os.listdir(ppct_dir):
        if not fn.endswith(".xlsx") or fn.startswith("~$"):
            continue
        file_path = os.path.join(ppct_dir, fn)
        try:
            wb = openpyxl.load_workbook(file_path, data_only=True)
            sheet = wb.active

            # Extract document title if any
            title = ""
            for r in range(1, min(10, sheet.max_row + 1)):
                val = str(sheet.cell(r, 1).value or '')
                if "Môn" in val or "PHÂN PHỐI" in val.upper() or "KẾ HOẠCH" in val.upper():
                    title += " " + val

            # Check if this is the multi-column 'đặt tên folder.xlsx'
            if fn.lower() == "đặt tên folder.xlsx" or "đặt tên" in fn.lower():
                headers = [sheet.cell(1, c).value for c in range(1, sheet.max_column + 1)]
                col_data = {}
                for c_idx, h in enumerate(headers, start=1):
                    if h is not None:
                        h_str = str(h).strip()
                        names = []
                        for r in range(2, sheet.max_row + 1):
                            v = sheet.cell(r, c_idx).value
                            if v:
                                names.append(str(v).strip())
                        col_data[h_str] = names
                ppct_dict[fn] = {
                    "type": "folder_names",
                    "title": "Bảng đặt tên file/folder theo khối lớp",
                    "columns": col_data
                }
                continue

            # Standard PPCT table: look for header row with STT, Tuần, Tiết
            header_row = -1
            for r in range(1, min(15, sheet.max_row + 1)):
                row_vals = [str(sheet.cell(r, c).value or '').strip().upper() for c in range(1, 15)]
                if any("STT" in v for v in row_vals) and any("TUẦN" in v or "TUAN" in v for v in row_vals):
                    header_row = r
                    break

            items = []
            if header_row != -1:
                # Dynamic column mapping
                col_stt = 1
                col_tuan = 2
                col_tiet = 3
                col_ten_bai = 4
                col_ngay_day = None
                col_ghi_chu = 5

                for c in range(1, sheet.max_column + 1):
                    val = str(sheet.cell(header_row, c).value or '').strip().lower()
                    if "stt" in val:
                        col_stt = c
                    elif "ngày" in val or "ngay" in val:
                        col_ngay_day = c
                    elif "tuần" in val or "tuan" in val:
                        col_tuan = c
                    elif "tiết" in val or "tiet" in val:
                        col_tiet = c
                    elif "tên bài" in val or "ten bai" in val or "bài học" in val or "bai hoc" in val:
                        col_ten_bai = c
                    elif "ghi chú" in val or "ghi chu" in val:
                        col_ghi_chu = c

                for r in range(header_row + 1, sheet.max_row + 1):
                    stt = sheet.cell(r, col_stt).value if col_stt else None
                    tuan = sheet.cell(r, col_tuan).value if col_tuan else None
                    tiet = sheet.cell(r, col_tiet).value if col_tiet else None
                    ten_bai = sheet.cell(r, col_ten_bai).value if col_ten_bai else None
                    ngay_day_val = sheet.cell(r, col_ngay_day).value if col_ngay_day else None
                    ghi_chu = sheet.cell(r, col_ghi_chu).value if col_ghi_chu else None

                    ngay_day_str = str(ngay_day_val or '').strip()
                    if not ngay_day_str and tuan is not None:
                        ngay_day_str = calculate_week_dates(tuan)

                    if ten_bai or ghi_chu:
                        items.append({
                            "stt": stt,
                            "tuan": tuan,
                            "tiet": tiet,
                            "ten_bai": str(ten_bai or '').strip(),
                            "ngay_day": ngay_day_str,
                            "ghi_chu": str(ghi_chu or '').strip()
                        })

            ppct_dict[fn] = {
                "type": "standard_ppct",
                "title": title.strip() or fn,
                "items": items
            }
        except Exception as e:
            print(f"Error loading PPCT {fn}: {e}")

    return ppct_dict

def parse_docx_file(doc_path):
    """
    Parses a KHBD .docx file to detect:
    - Chủ đề (Theme)
    - Số thứ tự bài (e.g. 1, 2, 3...)
    - Tên bài (Lesson title)
    - Tiết học (Periods, e.g. 1, 2, 1+2, 4+5)
    - Lớp & Môn (from filename or content)
    - Original header texts & tables before 'I. Mục tiêu'
    """
    fn = os.path.basename(doc_path)
    fn_lower = fn.lower()

    # Detect Grade and Subject from filename
    detected_grade = ""
    grade_m = re.search(r'(?:lớp|lop|tin|toán|toan)\s*([3-9]|1[0-2])\b', fn_lower)
    if not grade_m:
        grade_m = re.search(r'\b([3-9])\b', fn_lower)
    if grade_m:
        detected_grade = grade_m.group(1)

    detected_subject = "Tin học"
    if "toán" in fn_lower or "toan" in fn_lower:
        detected_subject = "Toán"
    elif "công nghệ" in fn_lower or "cong nghe" in fn_lower:
        detected_subject = "Công Nghệ"
    elif "hdtn" in fn_lower or "hđtn" in fn_lower or "trải nghiệm" in fn_lower:
        detected_subject = "Hoạt Động Trải Nghiệm"

    lesson_num_from_fn = ""
    fn_bai_m = re.search(r'b[aà]i\s*(\d+[a-zA-Z]?)', fn_lower)
    if fn_bai_m:
        lesson_num_from_fn = fn_bai_m.group(1)

    # Read paragraphs and tables
    doc = docx.Document(doc_path)
    top_texts = []
    has_target = False

    for p in doc.paragraphs[:35]:
        t = p.text.strip()
        if t:
            top_texts.append(t)
            if any(t.lower().startswith(x) for x in ["i. mục tiêu", "i. muc tieu", "1. mục tiêu", "i.mục tiêu"]) or (t.lower().startswith("i.") and "mục tiêu" in t.lower()):
                has_target = True
                break

    # Also scan top tables for header metadata (Trường, Môn, Bài, Tiết, etc.)
    for tbl in doc.tables[:3]:
        for row in tbl.rows:
            for cell in row.cells:
                ct = cell.text.strip()
                if ct and ct not in top_texts:
                    top_texts.append(ct)

    full_top = "\n".join(top_texts)

    # Detect Chủ Đề
    chude = ""
    chude_m = re.search(r'(Chủ đề|CHỦ ĐỀ)\s*([0-9A-Za-z]+)\s*[:\.\-]\s*([^\n\r]+)', full_top)
    if chude_m:
        chude = f"CHỦ ĐỀ {chude_m.group(2).upper()}: {chude_m.group(3).strip().upper()}"

    # Detect Lesson Number and Title from body
    bai_num = lesson_num_from_fn
    bai_title = ""

    bai_m = re.search(r'B[àa]i\s*(\d+[a-zA-Z]?)\s*[:\.\-–—]\s*([^\n\r]+)', full_top, re.IGNORECASE)
    if bai_m:
        bai_num = bai_m.group(1).strip()
        raw_name = bai_m.group(2).strip()
        bai_title = re.sub(r'[\.\,]+$', '', raw_name).strip()

    if not bai_title:
        ten_bai_m = re.search(r'(?:TÊN BÀI DẠY|TEN BAI DAY|BÀI DẠY|KẾ HOẠCH BÀI DẠY)\s*[:\.\-–—]\s*([^\n\r]+)', full_top, re.IGNORECASE)
        if ten_bai_m:
            cand = ten_bai_m.group(1).strip()
            cand_clean = re.sub(r'^[…\.\s\-_]+$', '', cand).strip()
            if cand_clean:
                bai_title = cand_clean

    if not bai_title and lesson_num_from_fn:
        for t in top_texts:
            if "bài" in t.lower() and ":" in t:
                parts = t.split(":", 1)
                cand = parts[1].strip()
                if cand and not re.match(r'^[…\.\s\-_]+$', cand):
                    bai_title = cand
                    break

    if not bai_title:
        clean_fn = re.sub(r'\.(docx|doc)$', '', fn, flags=re.IGNORECASE).strip()
        clean_fn = re.sub(r'^(?:KHBD|giao\s*an|kế\s*hoạch\s*bài\s*dạy)[\s_\-]*', '', clean_fn, flags=re.IGNORECASE).strip()
        bai_title = clean_fn
    # Clean bai_title if it has prefix like 'Tiết 1+2 :'
    if "tiết" in bai_title.lower() or "tiet" in bai_title.lower():
        bai_title = re.sub(r'Tiết\s*[0-9\+\,\-\s]+[\:\.\,]*', '', bai_title, flags=re.IGNORECASE).strip()

    # Detect Tiết (Periods)
    tiet_str = ""
    tiet_m = re.search(r'Tiết\s*([0-9\+\,\-\s]+)', full_top, re.IGNORECASE)
    if tiet_m:
        tiet_raw = tiet_m.group(1).strip()
        cleaned = re.sub(r'[\s\.\,]+$', '', tiet_raw)
        cleaned = re.sub(r'\s+', '', cleaned).replace('+', ', ')
        tiet_str = re.sub(r'[\,\s]+$', '', cleaned)

    # Inferred Chủ Đề if missing from text
    if not chude:
        b_num_int = None
        try:
            b_num_int = int(re.search(r'\d+', str(bai_num)).group(0))
        except Exception:
            pass

        if detected_subject == "Tin học" and detected_grade == "9" and b_num_int:
            if b_num_int == 1:
                chude = "CHỦ ĐỀ 1: MÁY TÍNH VÀ CỘNG ĐỒNG"
            elif b_num_int in [2, 3]:
                chude = "CHỦ ĐỀ 2: TỔ CHỨC LƯU TRỮ, TÌM KIẾM VÀ TRAO ĐỔI THÔNG TIN"
            elif b_num_int == 4:
                chude = "CHỦ ĐỀ 3: ĐẠO ĐỨC, PHÁP LUẬT VÀ VĂN HOÁ TRONG MÔI TRƯỜNG SỐ"
            elif 5 <= b_num_int <= 11:
                chude = "CHỦ ĐỀ 4: ỨNG DỤNG TIN HỌC"
            elif 12 <= b_num_int <= 16:
                chude = "CHỦ ĐỀ 5: GIẢI QUYẾT VẤN ĐỀ VỚI SỰ TRỢ GIÚP CỦA MÁY TÍNH"
            elif b_num_int == 17:
                chude = "CHỦ ĐỀ 6: TIN HỌC VÀ THẾ GIỚI NGHỀ NGHIỆP"

    # Check if there's an attendance table at top
    old_table_info = []
    if len(doc.tables) > 0:
        t0 = doc.tables[0]
        # Check if this table appears before 'I. Mục tiêu'
        for r in t0.rows:
            old_table_info.append([c.text.strip().replace('\n', ' ') for c in r.cells])

    return {
        "file_path": doc_path,
        "filename": fn,
        "detected_grade": detected_grade,
        "detected_subject": detected_subject,
        "chude": chude,
        "bai_num": bai_num,
        "bai_title": bai_title,
        "tiet_str": tiet_str,
        "top_texts": top_texts[:5],
        "has_old_table": len(old_table_info) > 0,
        "old_table_sample": old_table_info[:2] if old_table_info else []
    }

def match_lesson_with_ppct(lesson_info, ppct_items, grade=None):
    """
    Matches parsed lesson info against PPCT items list.
    Returns the best matching PPCT item or None.
    """
    if not ppct_items:
        return None

    bai_num = str(lesson_info.get("bai_num", "")).strip().lower()
    bai_title = str(lesson_info.get("bai_title", "")).strip().lower()
    tiet_str = str(lesson_info.get("tiet_str", "")).strip()

    # Try matching by lesson number in ten_bai
    best_match = None
    for item in ppct_items:
        tb = item.get("ten_bai", "").lower()
        gc = item.get("ghi_chu", "").lower()

        # Check if lesson number matches: e.g. "Bài 1" or "bai01"
        if bai_num:
            bai_pattern = f"bài {bai_num}."
            bai_pattern2 = f"bài {bai_num}:"
            bai_pattern3 = f"bài {bai_num} "
            bai_pattern4 = f"bai{int(bai_num) if bai_num.isdigit() else bai_num:02d}"

            if bai_pattern in tb or bai_pattern2 in tb or bai_pattern3 in tb or (bai_pattern4 in gc):
                # If lesson has a title, check title similarity
                if bai_title and remove_vietnamese_accents(bai_title) in remove_vietnamese_accents(tb):
                    return item
                if best_match is None:
                    best_match = item

    if best_match:
        return best_match

    # Try matching by title keyword
    if bai_title:
        title_slug = to_slug(bai_title)
        for item in ppct_items:
            tb_slug = to_slug(item.get("ten_bai", ""))
            gc_slug = to_slug(item.get("ghi_chu", ""))
            if title_slug in tb_slug or tb_slug in title_slug or title_slug in gc_slug:
                return item

    # Try matching by period (tiết)
    if tiet_str:
        # e.g. "1, 2" or "1"
        first_tiet = re.search(r'\d+', tiet_str)
        if first_tiet:
            t_num = int(first_tiet.group(0))
            for item in ppct_items:
                if item.get("tiet") == t_num:
                    return item

    return None

def generate_target_filename(lesson_info, matched_ppct, config):
    """
    Generates new target filename based on chosen naming scheme.
    Options:
    - 'ppct_slug': e.g. tinhoc9_tuan01_Bai01_The-gioi-ki-thuat-so_Tiet01.docx
    - 'ppct_exact': e.g. from PPCT ghi_chu column if available
    - 'teacher': e.g. Le Thi Phuong Thao_Tin 9_Tuan 01_Bai 01.docx
    - 'custom': custom pattern
    """
    scheme = config.get("naming_scheme", "ppct_slug")
    grade = config.get("grade", lesson_info.get("detected_grade", "9"))
    subject = config.get("subject", lesson_info.get("detected_subject", "Tin học"))
    teacher_ascii = config.get("teacher_ascii", remove_vietnamese_accents(config.get("teacher_name", "Lê Thị Phương Thảo")))

    bai_num = lesson_info.get("bai_num") or "01"
    try:
        bai_num_int = int(re.search(r'\d+', str(bai_num)).group(0))
        bai_str = f"{bai_num_int:02d}"
    except Exception:
        bai_str = str(bai_num)

    # Week (Tuần)
    week = "01"
    if matched_ppct and matched_ppct.get("tuan"):
        try:
            week = f"{int(matched_ppct['tuan']):02d}"
        except Exception:
            week = str(matched_ppct['tuan'])
    elif config.get("default_week"):
        week = str(config.get("default_week"))

    # Period (Tiết)
    period = "01"
    if matched_ppct and matched_ppct.get("tiet"):
        try:
            period = f"{int(matched_ppct['tiet']):02d}"
        except Exception:
            period = str(matched_ppct['tiet'])
    elif lesson_info.get("tiet_str"):
        first_t = re.search(r'\d+', lesson_info.get("tiet_str", ""))
        if first_t:
            period = f"{int(first_t.group(0)):02d}"

    # Lesson Title Slug
    lesson_name = lesson_info.get("bai_title") or (matched_ppct.get("ten_bai") if matched_ppct else "")
    # Remove "Bài X." from lesson_name if present
    lesson_name = re.sub(r'^b[aà]i\s*\d+[\.\:\s]*', '', lesson_name, flags=re.IGNORECASE).strip()
    slug_name = to_slug(lesson_name) or "Bai-hoc"

    # Subject prefix
    sub_lower = remove_vietnamese_accents(subject).lower().replace(" ", "")
    if "tinhoc" in sub_lower or "tin" in sub_lower:
        sub_code = "tinhoc"
        sub_short = "Tin"
    elif "toan" in sub_lower:
        sub_code = "toan"
        sub_short = "Toan"
    elif "congnghe" in sub_lower:
        sub_code = "congnghe"
        sub_short = "Cong Nghe"
    elif "hdtn" in sub_lower or "trainghiem" in sub_lower:
        sub_code = "hdtnhn"
        sub_short = "HDTN"
    else:
        sub_code = sub_lower
        sub_short = subject

    if scheme == "ppct_exact" and matched_ppct and matched_ppct.get("ghi_chu"):
        fn = matched_ppct["ghi_chu"]
        if not fn.endswith(".docx"):
            fn += ".docx"
        return fn

    elif scheme == "teacher":
        return f"{teacher_ascii}_{sub_short} {grade}_Tuan {week}_Bai {bai_str}.docx"

    elif scheme == "custom":
        pattern = config.get("custom_pattern", "{sub_code}{grade}_tuan{week}_Bai{bai_str}_{slug_name}_Tiet{period}.docx")
        out_name = pattern.format(
            sub_code=sub_code,
            sub_short=sub_short,
            grade=grade,
            week=week,
            bai_str=bai_str,
            slug_name=slug_name,
            period=period,
            teacher=teacher_ascii
        )
        if not out_name.endswith(".docx"):
            out_name += ".docx"
        return out_name

    else: # ppct_slug (Default & recommended)
        return f"{sub_code}{grade}_tuan{week}_Bai{bai_str}_{slug_name}_Tiet{period}.docx"

def get_subject_type_label(subject_name, config=None):
    """
    Returns 'Hoạt động giáo dục' if subject is HDTN/Hoạt động trải nghiệm,
    otherwise 'Môn học' for regular subjects.
    If config explicitly sets subject_type to 'hoat_dong_giao_duc' or 'mon_hoc', respects that.
    """
    if config:
        st = config.get("subject_type")
        if st in ["hoat_dong_giao_duc", "hdtn"]:
            return "Hoạt động giáo dục"
        elif st == "mon_hoc":
            return "Môn học"

    s = (subject_name or "").lower().strip()
    hdtn_keywords = [
        "hdtn", "hđtn", "tnhn", "trải nghiệm", "trai nghiem",
        "hướng nghiệp", "huong nghiep", "hoạt động trải nghiệm", "hoạt động giáo dục"
    ]
    if any(k in s for k in hdtn_keywords):
        return "Hoạt động giáo dục"
    return "Môn học"

def calculate_week_dates(week_num, start_date_str="2026-09-07", date_format="d2_to_d6"):
    """
    Calculates actual teaching dates for a given week from Monday to Friday (T2 đến T6).
    - week_num: week number (e.g. 1, 2, '01', ...)
    - start_date_str: Monday of week 1 (YYYY-MM-DD or DD/MM/YYYY)
    - date_format:
        'd2_to_d6': '07/09/2026 - 11/09/2026'
        'tu_den': 'Từ 07/09 đến 11/09/2026'
        'd2_only': '07/09/2026'
    """
    try:
        m = re.search(r'\d+', str(week_num or '1'))
        week = int(m.group(0)) if m else 1
        if week < 1:
            week = 1

        s = str(start_date_str or "2026-09-07").strip()
        if "-" in s:
            parts = s.split("-")
            if len(parts[0]) == 4: # YYYY-MM-DD
                dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
            else: # DD-MM-YYYY
                dt = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        elif "/" in s:
            parts = s.split("/")
            if len(parts[0]) == 4: # YYYY/MM/DD
                dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
            else: # DD/MM/YYYY
                dt = datetime(int(parts[2]), int(parts[1]), int(parts[0]))
        else:
            dt = datetime(2026, 9, 7)

        # Snap to Monday of week 1 (Monday is weekday 0)
        mon_w1 = dt - timedelta(days=dt.weekday())

        # Monday of week W
        mon_w = mon_w1 + timedelta(weeks=(week - 1))
        # Friday of week W (4 days after Monday)
        fri_w = mon_w + timedelta(days=4)

        if date_format == "tu_den":
            return f"Từ {mon_w.strftime('%d/%m')} đến {fri_w.strftime('%d/%m/%Y')}"
        elif date_format == "d2_only":
            return mon_w.strftime("%d/%m/%Y")
        else: # d2_to_d6 (default)
            return f"{mon_w.strftime('%d/%m/%Y')} - {fri_w.strftime('%d/%m/%Y')}"
    except Exception:
        return "../../2026"

def transform_to_thcs_template(file_path, output_path, lesson_info, matched_ppct, config):
    """
    Formats the KHBD document to match Mau KHBD THCS.docx standards:
    - Table 1x2 at the very top (Tuần, Tiết, Ngày dạy | Họ tên GV, Tổ CM)
    - TÊN BÀI DẠY: ... (Bold, 14pt, Center)
    - Môn học/Hoạt động giáo dục: ...; lớp: ... (14pt, Center)
    - Thời gian thực hiện: ... tiết (14pt, Center)
    - I. Mục tiêu ...
    - Bottom approval block (Duyệt của Chuyên môn / Duyệt của tổ chuyên môn)
    - Page margins: Top 2.0cm, Bottom 2.0cm, Left 2.0cm, Right 1.5cm
    - Header: Kế hoạch bài dạy [Môn] [Lớp], năm học [Năm học]
    - Footer: [Tên GV] - [Tên trường]
    """
    doc = docx.Document(file_path)

    # 1. Margins & Header/Footer
    top_pt = config.get("margin_top_pt", 56.7)
    bot_pt = config.get("margin_bottom_pt", 56.7)
    left_pt = config.get("margin_left_pt", 56.7)
    right_pt = config.get("margin_right_pt", 42.55)

    teacher_name = config.get("teacher_name", "Lê Thị Phương Thảo")
    school_name = config.get("school_name", "Trường TH&THCS Đăk Trôi")
    department = config.get("department", "Tổ Tự Nhiên")
    school_year = config.get("school_year", "2025-2026")
    subject = config.get("subject") or lesson_info.get("detected_subject", "Tin học")
    classes = config.get("classes") or config.get("grade", lesson_info.get("detected_grade", "9"))

    for s in doc.sections:
        s.top_margin = Pt(top_pt)
        s.bottom_margin = Pt(bot_pt)
        s.left_margin = Pt(left_pt)
        s.right_margin = Pt(right_pt)

        # Header
        if config.get("enable_header", True):
            header = s.header
            for p in header.paragraphs:
                p.text = ""
            hp = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
            hp.text = f"Kế hoạch bài dạy {subject} {classes}, năm học {school_year}"
            hp.alignment = WD_ALIGN_PARAGRAPH.LEFT
            if hp.runs:
                hp.runs[0].font.name = "Times New Roman"
                hp.runs[0].font.size = Pt(11)
                hp.runs[0].font.italic = True

        # Footer
        if config.get("enable_footer", True):
            footer = s.footer
            for p in footer.paragraphs:
                p.text = ""
            fp = footer.paragraphs[0] if footer.paragraphs else footer.add_paragraph()
            fp.text = f"{teacher_name} - {school_name}"
            fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            if fp.runs:
                fp.runs[0].font.name = "Times New Roman"
                fp.runs[0].font.size = Pt(10)
                fp.runs[0].font.italic = True

    # 2. Identify elements to remove before "I. Mục tiêu"
    body = doc.element.body
    elements_to_remove = []
    found_target = False

    for child in list(body):
        if isinstance(child, CT_P):
            p = Paragraph(child, doc)
            text_strip = p.text.strip().lower()
            if any(text_strip.startswith(x) for x in ["i. mục tiêu", "i. muc tieu", "1. mục tiêu", "i.mục tiêu"]) or (text_strip.startswith("i.") and "mục tiêu" in text_strip):
                found_target = True
                break
            else:
                elements_to_remove.append(child)
        elif isinstance(child, CT_Tbl):
            if not found_target:
                elements_to_remove.append(child)

    for el in elements_to_remove:
        body.remove(el)

    # 3. Create standardized elements according to Mau KHBD THCS.docx
    new_elements = []

    # 3.1 TABLE 0 (1x2): AT THE VERY TOP
    table = doc.add_table(rows=1, cols=2)
    table.alignment = None
    table.autofit = False

    # Widths: ~3.8 in / 2.85 in
    table.rows[0].cells[0].width = Pt(274.75)
    table.rows[0].cells[1].width = Pt(205.55)

    c0 = table.cell(0, 0)
    c1 = table.cell(0, 1)

    week = config.get("week") or (matched_ppct.get("tuan") if matched_ppct else "") or "1"
    periods = config.get("periods") or lesson_info.get("tiet_str") or (str(matched_ppct.get("tiet")) if matched_ppct else "1, 2")

    # Teaching date calculation: explicit > matched_ppct['ngay_day'] > auto calc > default
    if config.get("teaching_date") and config.get("teaching_date") != "../../2026":
        teaching_date = config["teaching_date"]
    elif matched_ppct and matched_ppct.get("ngay_day"):
        teaching_date = matched_ppct["ngay_day"]
    elif config.get("auto_calc_teaching_date", True) and week:
        start_date = config.get("school_year_start_date", "2026-09-07")
        date_fmt = config.get("teaching_date_format", "d2_to_d6")
        teaching_date = calculate_week_dates(week, start_date, date_fmt)
    else:
        teaching_date = config.get("teaching_date", "../../2026")

    # Cell 0 (Left)
    p_tuan = c0.paragraphs[0]
    p_tuan.paragraph_format.line_spacing = 1.15
    p_tuan.paragraph_format.space_after = Pt(2)
    run = p_tuan.add_run(f"Tuần:\t{week}")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.italic = True

    p_tiet = c0.add_paragraph()
    p_tiet.paragraph_format.line_spacing = 1.15
    p_tiet.paragraph_format.space_after = Pt(2)
    run = p_tiet.add_run(f"Tiết: {periods}")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.italic = True

    p_date = c0.add_paragraph()
    p_date.paragraph_format.line_spacing = 1.15
    p_date.paragraph_format.space_after = Pt(2)
    run = p_date.add_run(f"Ngày dạy: {teaching_date}")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.italic = True

    # Cell 1 (Right)
    p_gv = c1.paragraphs[0]
    p_gv.paragraph_format.line_spacing = 1.15
    p_gv.paragraph_format.space_after = Pt(2)
    run = p_gv.add_run(f"Họ và tên giáo viên: {teacher_name}")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.italic = True

    p_to = c1.add_paragraph()
    p_to.paragraph_format.line_spacing = 1.15
    p_to.paragraph_format.space_after = Pt(2)
    run = p_to.add_run(f"Tổ chuyên môn: {department}")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.italic = True

    # Borders for table (default borderless as in Mau KHBD THCS, or light border if enabled)
    if config.get("table_border", False):
        border_kwargs = {"val": "single", "sz": "4", "color": "auto", "space": "0"}
        set_cell_border(c0, top=border_kwargs, bottom=border_kwargs, left=border_kwargs, right=border_kwargs)
        set_cell_border(c1, top=border_kwargs, bottom=border_kwargs, left=border_kwargs, right=border_kwargs)

    new_elements.append(table._tbl)

    # Blank separator after table
    p_sep = doc.add_paragraph()
    p_sep.paragraph_format.space_after = Pt(4)
    new_elements.append(p_sep._p)

    # 3.2 TÊN BÀI DẠY: ...
    bai_num = config.get("bai_num") or lesson_info.get("bai_num", "")
    bai_name = config.get("bai_name") or lesson_info.get("bai_title", "")
    if not bai_name and matched_ppct:
        bai_name = re.sub(r'^b[aà]i\s*\d+[\.\:\s]*', '', matched_ppct.get("ten_bai", ""), flags=re.IGNORECASE)

    prefix = config.get("title_prefix", "TÊN BÀI DẠY: ")
    if config.get("title_prefix_ten_bai_day", True):
        if bai_num and not f"bài {bai_num}".lower() in bai_name.lower():
            bai_title_full = f"{prefix}BÀI {bai_num}. {bai_name.upper()}"
        else:
            bai_title_full = f"{prefix}{bai_name.upper()}"
    else:
        bai_title_full = f"BÀI {bai_num}: {bai_name.upper()}" if bai_num else bai_name.upper()

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(4)
    p_title.paragraph_format.space_after = Pt(2)
    p_title.paragraph_format.line_spacing = 1.15
    run = p_title.add_run(bai_title_full)
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    run.font.bold = True
    new_elements.append(p_title._p)

    # 3.3 Môn học hoặc Hoạt động giáo dục: ...; lớp: ...
    sub_label = get_subject_type_label(subject, config)
    p_sub = doc.add_paragraph()
    p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_sub.paragraph_format.space_before = Pt(0)
    p_sub.paragraph_format.space_after = Pt(2)
    p_sub.paragraph_format.line_spacing = 1.15
    run = p_sub.add_run(f"{sub_label}: {subject}; lớp: {classes}")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    new_elements.append(p_sub._p)

    # 3.4 Thời gian thực hiện: (số tiết)
    duration = config.get("duration", "2")
    p_dur = doc.add_paragraph()
    p_dur.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_dur.paragraph_format.space_before = Pt(0)
    p_dur.paragraph_format.space_after = Pt(6)
    p_dur.paragraph_format.line_spacing = 1.15
    run = p_dur.add_run(f"Thời gian thực hiện: {duration} tiết")
    run.font.name = "Times New Roman"
    run.font.size = Pt(14)
    new_elements.append(p_dur._p)

    # Prepend new header elements to body
    for el in reversed(new_elements):
        body.remove(el)
        body.insert(0, el)

    # 4. Approval block at end of document
    if config.get("enable_approval_block", True):
        last_texts = [p.text.lower() for p in doc.paragraphs[-5:] if p.text.strip()]
        has_approval = any("duyệt của chuyên môn" in t or "duyệt của tổ chuyên môn" in t for t in last_texts)
        if not has_approval:
            signer_school = (config.get("signer_school") or "").strip()
            signer_dept = (config.get("signer_dept") or "").strip()

            if signer_school or signer_dept:
                tbl_app = doc.add_table(rows=1, cols=2)
                tbl_app.alignment = None
                tbl_app.autofit = False
                tbl_app.rows[0].cells[0].width = Pt(240)
                tbl_app.rows[0].cells[1].width = Pt(240)

                # Cell 0: Duyệt của Chuyên môn
                c0 = tbl_app.cell(0, 0)
                p0 = c0.paragraphs[0]
                p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p0.paragraph_format.space_before = Pt(14)
                p0.paragraph_format.space_after = Pt(2)
                r0 = p0.add_run("Duyệt của Chuyên môn")
                r0.font.name = "Times New Roman"
                r0.font.size = Pt(14)
                r0.font.bold = True

                p0_sub = c0.add_paragraph()
                p0_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p0_sub.paragraph_format.space_after = Pt(36)
                r0_sub = p0_sub.add_run("(Ký và ghi rõ họ tên)")
                r0_sub.font.name = "Times New Roman"
                r0_sub.font.size = Pt(11)
                r0_sub.font.italic = True

                p0_name = c0.add_paragraph()
                p0_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r0_name = p0_name.add_run(signer_school)
                r0_name.font.name = "Times New Roman"
                r0_name.font.size = Pt(14)
                r0_name.font.bold = True

                # Cell 1: Duyệt của tổ chuyên môn
                c1 = tbl_app.cell(0, 1)
                p1 = c1.paragraphs[0]
                p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p1.paragraph_format.space_before = Pt(14)
                p1.paragraph_format.space_after = Pt(2)
                r1 = p1.add_run("Duyệt của tổ chuyên môn")
                r1.font.name = "Times New Roman"
                r1.font.size = Pt(14)
                r1.font.bold = True

                p1_sub = c1.add_paragraph()
                p1_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p1_sub.paragraph_format.space_after = Pt(36)
                r1_sub = p1_sub.add_run("(Ký và ghi rõ họ tên)")
                r1_sub.font.name = "Times New Roman"
                r1_sub.font.size = Pt(11)
                r1_sub.font.italic = True

                p1_name = c1.add_paragraph()
                p1_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
                r1_name = p1_name.add_run(signer_dept)
                r1_name.font.name = "Times New Roman"
                r1_name.font.size = Pt(14)
                r1_name.font.bold = True
            else:
                p_app = doc.add_paragraph()
                p_app.paragraph_format.space_before = Pt(20)
                p_app.paragraph_format.space_after = Pt(10)
                p_app.paragraph_format.line_spacing = 1.15
                run1 = p_app.add_run("Duyệt của Chuyên môn\t\t\t\t        Duyệt của tổ chuyên môn")
                run1.font.name = "Times New Roman"
                run1.font.size = Pt(14)
                run1.font.bold = True

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # 3. Add AI Pedagogical Enrichment (NLS & CV 5512) if enabled
    ai_cfg = config.get("ai_config", {})
    if ai_cfg.get("enabled", False) and ai_cfg.get("add_nls", True):
        try:
            # Check if NLS is already in document
            has_nls = any("năng lực số" in p.text.lower() or "nls" in p.text.lower() for p in doc.paragraphs)
            if not has_nls:
                # Find paragraph '2. Về năng lực' or '2.1' or '2.2'
                target_para_idx = -1
                for p_idx, p in enumerate(doc.paragraphs):
                    p_lower = p.text.lower()
                    if "2. về năng lực" in p_lower or "2. năng lực" in p_lower or "2.2. năng lực" in p_lower:
                        target_para_idx = p_idx
                        break
                
                if target_para_idx != -1:
                    # Generate or fetch NLS text
                    lesson_name_for_ai = bai_name if 'bai_name' in locals() else (lesson_info.get("bai_title") or "Bài học")
                    import beeknoee_client
                    bee = beeknoee_client.BeeknoeeClient(api_key=ai_cfg.get("api_key"), model=ai_cfg.get("model"))
                    nls_text = bee.generate_nls_objectives(subject, classes, lesson_name_for_ai)
                    
                    # Insert new paragraph right after target
                    new_p = doc.paragraphs[target_para_idx]._p.addnext(doc.paragraphs[target_para_idx]._p)
                    # Use docx API to populate
                    ins_p = doc.paragraphs[target_para_idx].insert_paragraph_before(nls_text)
                    if ins_p.runs:
                        ins_p.runs[0].font.name = "Times New Roman"
                        ins_p.runs[0].font.size = Pt(13)
                        ins_p.runs[0].font.bold = False
        except Exception as e:
            print(f"AI NLS enrichment notice: {e}")
    doc.save(output_path)
    return output_path

def transform_khbd_file(file_path, output_path, lesson_info, matched_ppct, config):
    """
    Main dispatcher: Formats KHBD document according to chosen template style.
    Default: 'mau_thcs' (Mau KHBD THCS.docx)
    """
    style = config.get("template_style", "mau_thcs")
    if style == "mau_thcs":
        return transform_to_thcs_template(file_path, output_path, lesson_info, matched_ppct, config)
    else:
        return transform_to_thcs_template(file_path, output_path, lesson_info, matched_ppct, config)

