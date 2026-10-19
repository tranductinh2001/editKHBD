import os
import re
import io
import zipfile
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

def load_workbook_safe(file_path):
    """Mở file Excel an toàn, tự động vá lỗi cú pháp thẻ <fill/> rỗng phổ biến từ SMAS/vnEdu"""
    try:
        return openpyxl.load_workbook(file_path, data_only=True)
    except Exception as ex:
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            zin = zipfile.ZipFile(io.BytesIO(data))
            zout_buf = io.BytesIO()
            zout = zipfile.ZipFile(zout_buf, 'w')
            for item in zin.infolist():
                content = zin.read(item.filename)
                if item.filename == 'xl/styles.xml':
                    text = content.decode('utf-8', errors='ignore')
                    text = re.sub(r'<fill\s*/>', '<fill><patternFill patternType="none"/></fill>', text)
                    content = text.encode('utf-8')
                zout.writestr(item, content)
            zout.close()
            zout_buf.seek(0)
            return openpyxl.load_workbook(zout_buf, data_only=True)
        except Exception:
            raise ex

def load_all_ppct(ppct_dir):
    """
    Scans ppct_dir and parses all .xlsx files into a structured dictionary.
    Supports dynamic columns including 'Ngày dạy theo tuần'.
    Tự động trích xuất Môn học, Khối lớp và Số tiết cho từng bộ PPCT.
    """
    ppct_dict = {}
    if not os.path.exists(ppct_dir):
        return ppct_dict

    for fn in os.listdir(ppct_dir):
        if not fn.endswith(".xlsx") or fn.startswith("~$"):
            continue
        file_path = os.path.join(ppct_dir, fn)
        try:
            wb = load_workbook_safe(file_path)
            sheet = wb.active

            # Extract document title if any
            title = ""
            for r in range(1, min(10, sheet.max_row + 1)):
                val = str(sheet.cell(r, 1).value or '')
                if "Môn" in val or "PHÂN PHỐI" in val.upper() or "KẾ HOẠCH" in val.upper() or "HƯỚNG NGHIỆP" in val.upper():
                    title += " " + val

            title_clean = title.strip() or fn
            full_meta = (fn + " " + title).upper()

            # Phân loại môn học chính xác
            subject_detected = "Tin học"
            if any(k in full_meta for k in ["HĐ TN", "HDTN", "TNHN", "HOẠT ĐỘNG TRẢI NGHIỆM", "HƯỚNG NGHIỆP", "TRẢI NGHIỆM"]):
                subject_detected = "Hoạt động trải nghiệm, hướng nghiệp"
            elif any(k in full_meta for k in ["THỂ CHẤT", "GDTC", "THỂ DỤC"]):
                subject_detected = "Giáo dục thể chất"
            elif "TOÁN" in full_meta:
                subject_detected = "Toán"
            elif "CÔNG NGHỆ" in full_meta:
                subject_detected = "Công nghệ"
            elif "NGỮ VĂN" in full_meta or "VĂN" in full_meta:
                subject_detected = "Ngữ Văn"
            elif "TIN" in full_meta:
                subject_detected = "Tin học"

            # Phân loại khối lớp
            class_detected = ""
            grade_detected = "9"
            m_cls = re.search(r'(?:LỚP|LOP|KHỐI|KHOI)\s*(\d+[A-Za-z]?)', full_meta)
            if not m_cls:
                m_cls = re.search(r'(?:^|[_\s\-])(\d+[A-Za-z]?)(?:[_\s\.\-]|$)', fn)
            if m_cls:
                class_detected = m_cls.group(1).upper()
                grade_detected = re.sub(r'\D', '', class_detected) or "9"
            else:
                grade_detected = "9"
                class_detected = "9"

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
                    "subject": subject_detected,
                    "subjectName": subject_detected,
                    "grade": grade_detected,
                    "className": class_detected,
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
                "title": title_clean,
                "subject": subject_detected,
                "subjectName": subject_detected,
                "grade": grade_detected,
                "className": class_detected,
                "items": items
            }
        except Exception as e:
            try:
                print(f"Error loading PPCT {fn}: {e}")
            except Exception:
                pass

    # Tự động tích hợp toàn bộ Phân Phối Chương Trình chuẩn từ SMAS
    try:
        import smas_engine
        smas_ppcts = smas_engine.get_ppct_as_khbd_dict()
        if smas_ppcts:
            combined = dict(smas_ppcts)
            combined.update(ppct_dict)
            return combined
    except Exception as ex:
        print(f"Lỗi tích hợp PPCT từ SMAS vào load_all_ppct: {ex}")

    return ppct_dict

def resolve_best_ppct(ppct_dict, requested_filename=None, subject=None, grade=None):
    """
    Tìm bộ PPCT phù hợp nhất dựa trên Tệp PPCT được chọn, Môn học và Khối lớp.
    ĐẢM BẢO NGUYÊN TẮC:
    1. Nếu người dùng đã chọn một tệp PPCT cụ thể (khác file default generic '_Lop_9.xlsx'),
       tệp đó là QUYẾT ĐỊNH TUYỆT ĐỐI -> Luôn tôn trọng tệp PPCT đó 100%!
       Đồng thời bộ PPCT đó sẽ quyết định luôn Môn học và Khối lớp cho toàn hệ thống.
    2. Nếu requested_filename là '_Lop_9.xlsx' (mặc định) nhưng môn hoặc khối chỉ định môn khác (VD: HĐTN),
       hệ thống sẽ tự động tìm bộ PPCT chuẩn nhất cho môn và khối đó.
    """
    if not ppct_dict:
        return None, {}

    sub_norm = (subject or "").lower().strip()
    is_hdtn = any(k in sub_norm for k in ["hdtn", "hđ tn", "tnhn", "trải nghiệm", "hướng nghiệp"])
    is_tin = "tin" in sub_norm
    is_gdtc = any(k in sub_norm for k in ["gdtc", "thể chất", "thể dục"])
    is_toan = "toán" in sub_norm or "toan" in sub_norm
    is_cong_nghe = "công nghệ" in sub_norm or "cong nghe" in sub_norm

    grd_str = re.sub(r'\D', '', str(grade or "")) if grade else ""

    # 1. Nếu người dùng chọn một file PPCT (khác '_Lop_9.xlsx') và KHÔNG xung đột với Môn/Khối đã config
    if requested_filename and requested_filename in ppct_dict and requested_filename != "_Lop_9.xlsx":
        entry = ppct_dict[requested_filename]
        e_subj = (entry.get("subjectName") or entry.get("subject") or "").lower()
        e_grd = re.sub(r'\D', '', str(entry.get("grade") or ""))

        # Kiểm tra xem có mâu thuẫn trực tiếp với Môn/Khối người dùng đã cấu hình không
        subject_mismatch = False
        if sub_norm:
            if is_hdtn and not any(k in e_subj or k in requested_filename.lower() for k in ["hdtn", "hđ tn", "tnhn", "trải nghiệm", "hướng nghiệp"]):
                subject_mismatch = True
            elif is_tin and not ("tin" in e_subj or "tin" in requested_filename.lower() or "_lop_" in requested_filename.lower()):
                subject_mismatch = True
            elif is_toan and not ("toán" in e_subj or "toan" in requested_filename.lower()):
                subject_mismatch = True
            elif is_cong_nghe and not ("công nghệ" in e_subj or "cong nghe" in requested_filename.lower()):
                subject_mismatch = True
            elif is_gdtc and not ("gdtc" in e_subj or "thể chất" in e_subj or "gdtc" in requested_filename.lower()):
                subject_mismatch = True

        grade_mismatch = False
        if grd_str and e_grd and grd_str != e_grd:
            grade_mismatch = True

        if not subject_mismatch and not grade_mismatch:
            return requested_filename, entry

    # Nếu requested_filename là _Lop_9.xlsx và môn là Tin học khối 9 -> Đúng luôn
    if requested_filename == "_Lop_9.xlsx" and is_tin and (not grd_str or grd_str == "9") and "_Lop_9.xlsx" in ppct_dict:
        return "_Lop_9.xlsx", ppct_dict["_Lop_9.xlsx"]

    # 2. Tìm bộ khớp nhất với subject và grade trong candidates
    candidates = []
    for fn, entry in ppct_dict.items():
        if entry.get("type") == "folder_names":
            continue
        e_subj = (entry.get("subjectName") or entry.get("subject") or "").lower()
        e_grd = str(entry.get("grade") or "").strip()
        e_cls = str(entry.get("className") or "").upper()
        e_title = (entry.get("title") or "").lower()
        fn_low = fn.lower()
        full_text = f"{e_subj} {e_title} {fn_low}"

        subj_score = 0
        if is_hdtn and any(k in full_text for k in ["hdtn", "hđ tn", "tnhn", "trải nghiệm", "hướng nghiệp"]):
            subj_score = 20
        elif is_tin and "tin" in full_text:
            subj_score = 20
        elif is_gdtc and any(k in full_text for k in ["gdtc", "thể chất", "thể dục"]):
            subj_score = 20
        elif is_toan and "toán" in full_text:
            subj_score = 20
        elif is_cong_nghe and "công nghệ" in full_text:
            subj_score = 20
        elif not sub_norm:
            subj_score = 1

        if subj_score == 0:
            continue

        grade_score = 0
        if grd_str:
            if grd_str == e_grd or grd_str in e_cls or f"lớp {grd_str}" in full_text or f"lop {grd_str}" in full_text or f"_{grd_str}" in fn_low or f" {grd_str}" in fn_low:
                grade_score = 15

        item_count = len(entry.get("items", []))
        candidates.append((subj_score + grade_score + (5 if item_count > 0 else 0), item_count, fn, entry))

    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1]), reverse=True)
        best = candidates[0]
        return best[2], best[3]

    if requested_filename and requested_filename in ppct_dict:
        return requested_filename, ppct_dict[requested_filename]

    first_k = next(iter(ppct_dict))
    return first_k, ppct_dict[first_k]

def clean_bai_name(text):
    """
    Chuẩn hoá triệt để tên bài học, loại bỏ hoàn toàn các tiền tố gây nhiễu:
    - Tuần: 'TUẦN 9-', 'Tuần 9:', 'Tuần 09 -'
    - Chủ đề: 'CĐ3-', 'CĐ 3 -', 'CHỦ ĐỀ 3:', 'CHỦ ĐỀ A -'
    - Bài: 'BÀI 5.', 'Bài 5:', 'BÀI 05 -'
    - Tiết: 'TIẾT 1+2:', 'Tiết 1, 2 -', 'Tiết 4:'
    - Dấu gạch nối, dấu hai chấm, dấu chấm thừa ở đầu/cuối chuỗi
    Ví dụ: 'TUẦN 9- CĐ3- SỐNG CÓ TRÁCH NHIỆM' -> 'SỐNG CÓ TRÁCH NHIỆM'
    """
    if not text:
        return ""
    s = str(text).strip()
    changed = True
    while changed:
        orig = s
        s = re.sub(r'^(?:TUẦN|TUAN)\s*\d+(?:\s*[\-–—\+và\s]+\s*\d+)?[\s\:\.\-–—_]*', '', s, flags=re.IGNORECASE).strip()
        s = re.sub(r'^(?:CĐ|CD|CHỦ\s*ĐỀ|CHU\s*DE)\s*[0-9A-Za-z]+[\s\:\.\-–—]*', '', s, flags=re.IGNORECASE).strip()
        s = re.sub(r'^(?:BÀI|BAI)\s*\d+[a-zA-Z]?[\s\:\.\-–—]*', '', s, flags=re.IGNORECASE).strip()
        s = re.sub(r'^(?:TIẾT|TIET)\s*\d+[\d\+\,\-\s]*[\:\.\-–—\s]*', '', s, flags=re.IGNORECASE).strip()
        s = re.sub(r'^[\:\.\-–—\s\+\,]+', '', s).strip()
        changed = (s != orig)
    
    s = re.sub(r'[\:\.\-–—\s]+$', '', s).strip()
    return s

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

    detected_subject = ""
    if "toán" in fn_lower or "toan" in fn_lower:
        detected_subject = "Toán"
    elif "công nghệ" in fn_lower or "cong nghe" in fn_lower:
        detected_subject = "Công Nghệ"
    elif any(k in fn_lower for k in ["hdtn", "hđtn", "trải nghiệm", "hướng nghiệp", "kinh doanh", "từ chối", "tiêu dùng"]):
        detected_subject = "Hoạt động trải nghiệm, hướng nghiệp"
    elif "tin" in fn_lower:
        detected_subject = "Tin học"

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
    full_top_lower = full_top.lower()

    # Detect subject from document content if not obvious from filename
    if any(k in full_top_lower for k in ["hoạt động trải nghiệm", "hướng nghiệp", "hđtn", "tnhn", "hđ tn", "trải nghiệm, hướng nghiệp"]):
        detected_subject = "Hoạt động trải nghiệm, hướng nghiệp"
    elif "môn: toán" in full_top_lower or "môn toán" in full_top_lower:
        detected_subject = "Toán"
    elif "công nghệ" in full_top_lower:
        detected_subject = "Công Nghệ"

    if not detected_grade:
        g_in_doc = re.search(r'(?:lớp|lop)\s*[:\.\s]*([6-9]|1[0-2])\b', full_top_lower)
        if g_in_doc:
            detected_grade = g_in_doc.group(1)

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

    # Detect Tuần (Week) from text or filename
    week = None
    week_m = re.search(r'(?:Tuần|Tuan)\s*[:\.\-–—\s]*0*(\d+)', full_top, re.IGNORECASE)
    if not week_m and bai_title:
        week_m = re.search(r'(?:tuần|tuan)\s*0*(\d+)', bai_title, re.IGNORECASE)
    if not week_m:
        week_m = re.search(r'(?:tuần|tuan|w)\s*0*(\d+)', fn_lower, re.IGNORECASE)
    if week_m:
        try:
            week = int(week_m.group(1))
        except Exception:
            pass

    # Detect Chủ Đề from bai_title if missing
    if not chude and bai_title:
        raw_cd_m = re.search(r'(?:CĐ|CD|CHỦ\s*ĐỀ|CHU\s*DE)\s*([0-9A-Za-z]+)', bai_title, re.IGNORECASE)
        if raw_cd_m:
            chude = f"CHỦ ĐỀ {raw_cd_m.group(1).upper()}"

    # Clean bai_title thoroughly with clean_bai_name
    bai_title = clean_bai_name(bai_title)

    # Detect Tiết (Periods)
    tiet_str = ""
    tiet_m = re.search(r'Tiết\s*([0-9\+\,\-\s]+)', full_top, re.IGNORECASE)
    if tiet_m:
        tiet_raw = tiet_m.group(1).strip()
        cleaned = re.sub(r'[\s\.\,]+$', '', tiet_raw)
        cleaned = re.sub(r'\s+', '', cleaned).replace('+', ', ')
        tiet_str = re.sub(r'[\,\s]+$', '', cleaned)
    elif "tiết" in fn_lower or "tiet" in fn_lower:
        fn_tiet_m = re.search(r'(?:tiết|tiet)\s*0*(\d+)', fn_lower, re.IGNORECASE)
        if fn_tiet_m:
            tiet_str = fn_tiet_m.group(1)

    period_numbers = [int(x) for x in re.findall(r'\d+', tiet_str)]
    if any(p > 35 for p in period_numbers) and detected_subject == "Tin học":
        detected_subject = "Hoạt động trải nghiệm, hướng nghiệp"

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
        "week": week,
        "period_numbers": period_numbers,
        "top_texts": top_texts[:5],
        "has_old_table": len(old_table_info) > 0,
        "old_table_sample": old_table_info[:2] if old_table_info else []
    }

def match_lesson_with_ppct(lesson_info, ppct_items, grade=None):
    """
    Matches parsed lesson info against PPCT items list with intelligent scoring.
    Accurately distinguishes multi-period lessons, week, period, and exact teaching date.
    """
    if not ppct_items:
        return None

    bai_num_raw = str(lesson_info.get("bai_num", "")).strip()
    m_b = re.search(r'\d+', bai_num_raw)
    bai_num = int(m_b.group(0)) if m_b else None
    bai_title = remove_vietnamese_accents(str(lesson_info.get("bai_title", ""))).strip().lower()

    tiet_numbers = lesson_info.get("period_numbers") or []
    if not tiet_numbers and lesson_info.get("tiet_str"):
        tiet_numbers = [int(x) for x in re.findall(r'\d+', str(lesson_info.get("tiet_str")))]

    parsed_week = lesson_info.get("week")
    filename = lesson_info.get("filename", "")

    scored = []
    for item in ppct_items:
        score = 0
        tb = remove_vietnamese_accents(str(item.get("ten_bai", ""))).strip().lower()
        gc = remove_vietnamese_accents(str(item.get("ghi_chu", ""))).strip().lower()

        it_tiet = item.get("tiet")
        it_tuan = item.get("tuan")

        # 1. Lesson number matching (Bài số)
        if bai_num is not None:
            if f"bai {bai_num}." in tb or f"bai {bai_num}:" in tb or f"bai {bai_num} " in tb:
                score += 50
            elif f"bai{bai_num:02d}" in gc or f"bai{bai_num}" in gc or f"bai {bai_num}" in gc:
                score += 40

        # 2. Title matching (Tên bài) - Trọng số cao nhất để luôn khớp đúng bài học
        if bai_title:
            if bai_title in tb or tb in bai_title:
                score += 150
            else:
                w_user = set(bai_title.split())
                w_tb = set(tb.split())
                overlap = len(w_user.intersection(w_tb))
                if overlap >= 2:
                    score += overlap * 25

        # 3. Period (Tiết) matching - HIGHEST WEIGHT for distinguishing multi-period lessons
        if it_tiet is not None and tiet_numbers:
            try:
                t_val = int(it_tiet)
                if t_val in tiet_numbers:
                    score += 120
                elif t_val == tiet_numbers[0]:
                    score += 100
            except Exception:
                pass

        # 4. Week (Tuần) matching
        if it_tuan is not None and parsed_week is not None:
            try:
                if int(it_tuan) == int(parsed_week):
                    score += 80
            except Exception:
                pass

        # 5. Filename keyword matching in ghi_chu
        if filename:
            fn_clean = to_slug(filename).lower()
            if fn_clean and (fn_clean in gc or to_slug(gc) in fn_clean):
                score += 35

        if score > 0:
            scored.append((score, item))

    if scored:
        scored.sort(key=lambda x: x[0], reverse=True)
        best_match = dict(scored[0][1])

        # Tự động tính chính xác số tiết (duration) và dải tiết (tiet_range) từ PPCT
        tb_norm = clean_bai_name(best_match.get("ten_bai", "")).lower()
        matched_week = best_match.get("tuan")

        # Tìm tất cả các dòng cùng bài học này trong bộ PPCT
        same_lesson_items = [
            it for it in ppct_items
            if clean_bai_name(it.get("ten_bai", "")).lower() == tb_norm
        ]

        # Kiểm tra xem tài liệu dạy theo tuần này hay gộp nhiều tuần/nhiều tiết
        doc_explicit_periods = None
        if filename:
            m_tiet_cnt = re.search(r'(\d+)\s*(?:tiết|tiet)\b', filename, re.IGNORECASE)
            if m_tiet_cnt:
                doc_explicit_periods = int(m_tiet_cnt.group(1))

        week_matching_items = [it for it in same_lesson_items if it.get("tuan") == matched_week]

        effective_items = []
        if doc_explicit_periods and len(same_lesson_items) >= doc_explicit_periods:
            effective_items = same_lesson_items
        elif week_matching_items:
            effective_items = week_matching_items
        else:
            effective_items = same_lesson_items or [best_match]

        tiets = []
        for it in effective_items:
            if it.get("tiet") is not None:
                try:
                    tiets.append(int(it["tiet"]))
                except Exception:
                    pass
        tiets = sorted(list(set(tiets)))

        so_tiet = len(tiets) if tiets else (doc_explicit_periods or 1)
        if len(tiets) > 1:
            if tiets[-1] - tiets[0] + 1 == len(tiets):
                tiet_range_str = f"{tiets[0]} - {tiets[-1]}"
            else:
                tiet_range_str = ", ".join(str(t) for t in tiets)
        elif len(tiets) == 1:
            tiet_range_str = str(tiets[0])
        else:
            tiet_range_str = str(best_match.get("tiet", "1"))

        best_match["so_tiet"] = str(so_tiet)
        best_match["duration"] = str(so_tiet)
        best_match["tiet_range"] = tiet_range_str
        best_match["tiets"] = tiets
        return best_match

    return None

def sanitize_target_filename(filename):
    """
    Sanitizes string to be valid Windows filename:
    Removes invalid characters \ / : * ? " < > |
    """
    if not filename:
        return "KHBD.docx"
    cleaned = re.sub(r'[\\/*?:"<>|]', '-', str(filename))
    cleaned = re.sub(r'\s+', ' ', cleaned)
    cleaned = re.sub(r'-{2,}', '-', cleaned)
    cleaned = cleaned.strip('. ')
    if not cleaned.lower().endswith(".docx"):
        cleaned += ".docx"
    return cleaned

def generate_target_filename(lesson_info, matched_ppct, config):
    """
    Generates new target filename based on chosen naming scheme.
    Options:
    - 'vietnamese_standard': Tuần {tuan} - Tiết {tiet} - Bài {bai_num} - {ten_bai}.docx
    - 'vietnamese_simple': {mon_short} {lop} - Tuần {tuan} - Tiết {tiet} - {ten_bai}.docx
    - 'period_lesson': Tiết {tiet} - {ten_bai}.docx
    - 'ppct_slug': {mon_code}{grade}_tuan{week}_Bai{bai_str}_{slug_name}_Tiet{period}.docx
    - 'teacher': {teacher}_{mon_short} {grade}_Tuan {week}_Bai {bai_str}.docx
    - 'ppct_exact': PPCT ghi_chu column
    - 'custom': User-defined custom pattern with flexible tokens
    """
    scheme = config.get("naming_scheme", "vietnamese_standard")
    grade = str(config.get("classes") or config.get("grade") or lesson_info.get("detected_grade") or "9").strip()
    subject = config.get("subject", lesson_info.get("detected_subject", "Tin học"))
    teacher_name = config.get("teacher_name", "Lê Thị Phương Thảo")
    teacher_ascii = config.get("teacher_ascii") or remove_vietnamese_accents(teacher_name)

    # Lesson number (bai_num / bai_str)
    bai_raw = lesson_info.get("bai_num") or (matched_ppct.get("stt") if matched_ppct else "") or "1"
    bai_match = re.search(r'\d+', str(bai_raw))
    if bai_match:
        bai_int = int(bai_match.group(0))
        bai_str = f"{bai_int:02d}"
        bai_num = str(bai_int)
    else:
        bai_str = str(bai_raw).strip() or "01"
        bai_num = bai_str

    # Week (Tuần)
    week_val = (matched_ppct.get("tuan") if matched_ppct else None) or lesson_info.get("week") or lesson_info.get("tuan") or config.get("default_week") or 1
    w_match = re.search(r'\d+', str(week_val))
    if w_match:
        w_int = int(w_match.group(0))
        tuan = f"{w_int:02d}"
        tuan_1 = str(w_int)
    else:
        tuan = str(week_val).strip() or "01"
        tuan_1 = tuan

    # Period (Tiết)
    period_val = (matched_ppct.get("tiet") if matched_ppct else None) or lesson_info.get("tiet_str") or "1"
    p_match = re.search(r'\d+', str(period_val))
    if p_match:
        p_int = int(p_match.group(0))
        tiet = f"{p_int:02d}"
        tiet_1 = str(p_int)
    else:
        tiet = str(period_val).strip() or "01"
        tiet_1 = tiet
    if "+" in str(period_val) or "," in str(period_val) or "-" in str(period_val):
        tiet_display = str(period_val).replace(" ", "")
    else:
        tiet_display = tiet

    # Lesson title (clean thoroughly!)
    raw_title = (matched_ppct.get("ten_bai") if matched_ppct else "") or lesson_info.get("bai_title") or ""
    ten_bai = clean_bai_name(raw_title)
    if not ten_bai:
        ten_bai = f"Bài {bai_num}"
    
    slug_name = to_slug(ten_bai) or f"Bai-{bai_num}"
    ten_khong_dau = remove_vietnamese_accents(ten_bai)

    # Subject code & short
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
        return sanitize_target_filename(matched_ppct["ghi_chu"])

    # Token dictionary for variable substitution
    tokens = {
        "tuan": tuan,
        "week": tuan,
        "tuan_1": tuan_1,
        "week_1": tuan_1,
        "tiet": tiet_display,
        "period": tiet_display,
        "tiet_1": tiet_1,
        "bai": bai_str,
        "bai_str": bai_str,
        "bai_num": bai_num,
        "ten_bai": ten_bai,
        "lesson_name": ten_bai,
        "ten_khong_dau": ten_khong_dau,
        "slug_name": slug_name,
        "mon": subject,
        "mon_code": sub_code,
        "sub_code": sub_code,
        "mon_short": sub_short,
        "sub_short": sub_short,
        "lop": grade,
        "grade": grade,
        "gv": teacher_name,
        "teacher": teacher_ascii
    }

    if scheme == "vietnamese_standard":
        pattern = "Tuần {tuan} - Tiết {tiet} - Bài {bai_num} - {ten_bai}.docx"
    elif scheme == "vietnamese_simple":
        pattern = "{mon_short} {lop} - Tuần {tuan} - Tiết {tiet} - {ten_bai}.docx"
    elif scheme == "period_lesson":
        pattern = "Tiết {tiet} - {ten_bai}.docx"
    elif scheme == "ppct_slug":
        pattern = "{mon_code}{grade}_tuan{week}_Bai{bai_str}_{slug_name}_Tiet{period}.docx"
    elif scheme == "teacher":
        pattern = "{teacher}_{mon_short} {grade}_Tuan {week}_Bai {bai_str}.docx"
    elif scheme == "custom":
        pattern = config.get("custom_pattern") or "Tuần {tuan} - Tiết {tiet} - Bài {bai_num} - {ten_bai}.docx"
    else:
        pattern = "Tuần {tuan} - Tiết {tiet} - Bài {bai_num} - {ten_bai}.docx"

    # Replace tokens safely
    result = pattern
    for k, v in tokens.items():
        result = result.replace(f"{{{k}}}", str(v))

    return sanitize_target_filename(result)

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

def calculate_week_dates(week_num, start_date_str="2026-09-07", date_format="d2_to_d6", class_name=None):
    if date_format == "smas_exact":
        try:
            import smas_engine
            return smas_engine.get_exact_teaching_date_from_tkb(class_name or "", week_num, date_format="smas_exact")
        except Exception as e:
            pass
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

def format_cv5512_standard(doc, config):
    """
    Chuẩn hoá toàn bộ định dạng giáo án theo Công văn 5512/BGDĐT-GDTrH:
    - Font chữ: Times New Roman thống nhất toàn văn bản.
    - Cỡ chữ & Giãn dòng:
      + Đề mục La Mã (I. MỤC TIÊU, II. THIẾT BỊ DẠY HỌC, III. TIẾN TRÌNH DẠY HỌC, IV. PHỤ LỤC): 14pt, Bold, giãn dòng 1.15, trước 8pt, sau 4pt.
      + Đề mục 1, 2, 3 (1. Kiến thức, 2. Năng lực, 3. Phẩm chất): 13pt, Bold, trước 4pt, sau 2pt.
      + Hoạt động dạy học (Hoạt động 1, Hoạt động 2...): 13pt, Bold, trước 6pt, sau 2pt.
      + 4 bước CV 5512 (a) Mục tiêu, b) Nội dung, c) Sản phẩm, d) Tổ chức thực hiện): 13pt, Bold, trước 3pt, sau 2pt.
      + Đoạn văn bản nội dung: 13pt, căn đều 2 bên (Justify), giãn dòng 1.15, sau 3pt.
      + Bảng biểu: Căn giữa, chữ 12-13pt, header in đậm.
      + Giữ nguyên màu đỏ nếu là nội dung tích hợp NLS.
    """
    try:
        # 1. Format all body paragraphs (bỏ qua header table và signature table ở cuối)
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue

            # Bỏ qua các đoạn trong bảng duyệt hoặc tiêu đề đầu đã định dạng
            if any(text.startswith(x) for x in ["TÊN BÀI DẠY:", "Tuần:", "Tiết:", "Họ và tên giáo viên:", "Tổ chuyên môn:"]):
                continue

            p.paragraph_format.line_spacing = 1.15

            # Phân loại đề mục
            is_roman_header = bool(re.match(r'^(?:[I|V|X]+)\.\s*(?:MỤC TIÊU|THIẾT BỊ|TIẾN TRÌNH|PHỤ LỤC|ĐÁNH GIÁ)', text, re.IGNORECASE))
            is_sub_header = bool(re.match(r'^(?:1|2|3|4)\.\s*(?:Kiến thức|Năng lực|Phẩm chất|Mục tiêu)', text, re.IGNORECASE))
            is_activity = bool(re.match(r'^(?:Hoạt động|HOẠT ĐỘNG)\s*\d+', text, re.IGNORECASE)) or bool(re.match(r'^[A-D]\.\s*(?:HOẠT ĐỘNG|TIẾN TRÌNH)', text, re.IGNORECASE))
            is_step = bool(re.match(r'^[a-d]\)\s*(?:Mục tiêu|Nội dung|Sản phẩm|Tổ chức thực hiện)', text, re.IGNORECASE))

            if is_roman_header:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(8)
                p.paragraph_format.space_after = Pt(4)
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(14)
                    r.font.bold = True
            elif is_activity:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(6)
                p.paragraph_format.space_after = Pt(2)
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(13)
                    r.font.bold = True
            elif is_sub_header:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(4)
                p.paragraph_format.space_after = Pt(2)
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(13)
                    r.font.bold = True
            elif is_step:
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p.paragraph_format.space_before = Pt(3)
                p.paragraph_format.space_after = Pt(2)
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(13)
                    r.font.bold = True
            else:
                # Nội dung thường: căn đều 2 bên
                if p.alignment != WD_ALIGN_PARAGRAPH.CENTER:
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(3)
                for r in p.runs:
                    r.font.name = "Times New Roman"
                    if not r.font.size:
                        r.font.size = Pt(13)
                    elif r.font.size > Pt(14):
                        r.font.size = Pt(13.5)
                    elif r.font.size < Pt(12):
                        r.font.size = Pt(13)

        # 2. Format tables (ngoại trừ bảng header 1x2 đầu tiên và bảng signature cuối cùng)
        tables_to_format = doc.tables[1:-1] if len(doc.tables) > 2 else doc.tables
        for tbl in tables_to_format:
            tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
            for r_idx, row in enumerate(tbl.rows):
                for cell in row.cells:
                    for cp in cell.paragraphs:
                        cp.paragraph_format.line_spacing = 1.15
                        for cr in cp.runs:
                            cr.font.name = "Times New Roman"
                            if not cr.font.size:
                                cr.font.size = Pt(12)
                            if r_idx == 0 and not cr.font.bold:
                                cr.font.bold = True
    except Exception as fmt_err:
        print(f"Format CV5512 warning: {fmt_err}")

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
    subject = config.get("subject") or (matched_ppct.get("subjectName") or matched_ppct.get("subject") if matched_ppct else None) or lesson_info.get("detected_subject") or "Tin học"
    classes = config.get("classes") or config.get("grade") or (str(matched_ppct.get("grade")) if matched_ppct and matched_ppct.get("grade") else None) or lesson_info.get("detected_grade") or "9"

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

    week = config.get("week") or (str(matched_ppct.get("tuan")) if matched_ppct and matched_ppct.get("tuan") is not None else "") or lesson_info.get("week") or "1"
    periods = config.get("periods") or (matched_ppct.get("tiet_range") if matched_ppct else None) or (str(matched_ppct.get("tiet")) if matched_ppct and matched_ppct.get("tiet") is not None else None) or lesson_info.get("tiet_str") or "1"

    # Teaching date calculation: explicit valid config > matched_ppct['ngay_day'] > auto calc > default
    cfg_date = config.get("teaching_date")
    if cfg_date and str(cfg_date).strip() not in ["../../2026", ""]:
        teaching_date = str(cfg_date).strip()
    elif matched_ppct and matched_ppct.get("ngay_day"):
        teaching_date = matched_ppct["ngay_day"]
    elif config.get("auto_calc_teaching_date", True) and week:
        start_date = config.get("school_year_start_date", "2026-09-07")
        date_fmt = config.get("teaching_date_format", "smas_exact")
        c_name = config.get("classes") or config.get("grade") or ""
        teaching_date = calculate_week_dates(week, start_date, date_fmt, class_name=c_name)
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

    # Thoroughly clean bai_name of any week/chude/tiet/symbol artifacts
    bai_name = clean_bai_name(bai_name)

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

    # 3.4 Thời gian thực hiện: (số tiết) - Tự động tính chuẩn xác theo PPCT từng bài
    duration = (matched_ppct.get("so_tiet") or matched_ppct.get("duration") if matched_ppct else None) or config.get("duration") or "1"
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

    # 4. Clean up any existing approval signatures at bottom of document to avoid duplication
    approval_keywords = [
        "duyệt của chuyên môn", "duyệt của tổ chuyên môn", "duyệt của bgh",
        "người thực hiện", "tổ trưởng chuyên môn", "tổ trưởng cm",
        "ký và ghi rõ họ tên", "ký, ghi rõ họ tên", "giáo viên thực hiện",
        "giáo viên soạn", "người soạn", "bgh duyệt", "ban giám hiệu duyệt",
        "chuyên môn duyệt"
    ]
    
    body_elements = list(body)
    to_remove_approval = []
    
    # Scan from end backwards (up to 30 elements)
    for el in reversed(body_elements[-30:]):
        if el.tag.endswith('p'):
            p = Paragraph(el, doc)
            text_low = p.text.strip().lower()
            if any(kw in text_low for kw in approval_keywords):
                to_remove_approval.append(el)
            elif not text_low and to_remove_approval:
                to_remove_approval.append(el)
        elif el.tag.endswith('tbl'):
            tbl = Table(el, doc)
            tbl_text = ' '.join(c.text.strip().lower() for row in tbl.rows for c in row.cells)
            if any(kw in tbl_text for kw in approval_keywords):
                to_remove_approval.append(el)

    for el in to_remove_approval:
        if el in body:
            body.remove(el)

    # 5. Format whole document according to CV 5512 if enabled
    if config.get("format_5512", True):
        format_cv5512_standard(doc, config)

    # 6. Now add standardized approval block according to config with ample spacing
    if config.get("enable_approval_block", True):
        title_school = (config.get("title_signer_school") or config.get("title_signer_left") or "Duyệt của tổ chuyên môn").strip()
        signer_school = (config.get("signer_school") or config.get("signer_left") or "").strip()
        title_dept = (config.get("title_signer_dept") or config.get("title_signer_right") or "Người thực hiện").strip()
        signer_dept = (config.get("signer_dept") or config.get("signer_right") or "").strip()

        # Add generous separator paragraph so signature table never attaches directly to NLS table or content
        p_sep = doc.add_paragraph()
        p_sep.paragraph_format.space_before = Pt(24)
        p_sep.paragraph_format.space_after = Pt(14)

        tbl_app = doc.add_table(rows=1, cols=2)
        tbl_app.alignment = WD_TABLE_ALIGNMENT.CENTER
        tbl_app.autofit = False
        tbl_app.rows[0].cells[0].width = Pt(240)
        tbl_app.rows[0].cells[1].width = Pt(240)

        # Cell 0: Left side (Duyệt của tổ chuyên môn / Duyệt của Chuyên môn)
        c0 = tbl_app.cell(0, 0)
        p0 = c0.paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0.paragraph_format.space_before = Pt(8)
        p0.paragraph_format.space_after = Pt(2)
        r0 = p0.add_run(title_school)
        r0.font.name = "Times New Roman"
        r0.font.size = Pt(14)
        r0.font.bold = True

        p0_sub = c0.add_paragraph()
        p0_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p0_sub.paragraph_format.space_after = Pt(48)  # Spacious 48pt for physical signature/stamp
        r0_sub = p0_sub.add_run("(Ký và ghi rõ họ tên)")
        r0_sub.font.name = "Times New Roman"
        r0_sub.font.size = Pt(11)
        r0_sub.font.italic = True

        p0_name = c0.add_paragraph()
        p0_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r0_name = p0_name.add_run(signer_school if signer_school else "                     ")
        r0_name.font.name = "Times New Roman"
        r0_name.font.size = Pt(14)
        r0_name.font.bold = True

        # Cell 1: Right side (Người thực hiện / Giáo viên soạn)
        c1 = tbl_app.cell(0, 1)
        p1 = c1.paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1.paragraph_format.space_before = Pt(8)
        p1.paragraph_format.space_after = Pt(2)
        r1 = p1.add_run(title_dept)
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(14)
        r1.font.bold = True

        p1_sub = c1.add_paragraph()
        p1_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p1_sub.paragraph_format.space_after = Pt(48)  # Spacious 48pt for physical signature/stamp
        r1_sub = p1_sub.add_run("(Ký và ghi rõ họ tên)")
        r1_sub.font.name = "Times New Roman"
        r1_sub.font.size = Pt(11)
        r1_sub.font.italic = True

        p1_name = c1.add_paragraph()
        p1_name.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r1_name = p1_name.add_run(signer_dept if signer_dept else "                     ")
        r1_name.font.name = "Times New Roman"
        r1_name.font.size = Pt(14)
        r1_name.font.bold = True

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    
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

