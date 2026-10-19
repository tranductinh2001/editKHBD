# -*- coding: utf-8 -*-
"""
SMAS Engine for editKHBD
Tích hợp đồng bộ Thời Khóa Biểu, Lịch Báo Giảng và Phân Phối Chương Trình SMAS.
Đồng bộ thông tin giáo viên, năm học và ngày dạy thực tế chuẩn xác cho KHBD.
Cung cấp Token cấu hình dùng chung toàn hệ thống để lấy data khi cần.
"""

import os
import sys
import io
import json
import re
import base64
import datetime
import urllib.request
import urllib.error
import xlrd
import openpyxl
from pathlib import Path
from typing import Dict, List, Any, Optional

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
SCHEDULE_PATH = BASE_DIR / "schedule.json"
DEFAULT_SCHEDULE_PATH = BASE_DIR / "default_schedule.json"
ALL_CLASSES_PATH = BASE_DIR / "all_classes.json"
SMAS_PPCT_DB_PATH = BASE_DIR / "smas_ppct_db.json"
SMAS_SUBJECTS_PATH = BASE_DIR / "smas_subjects.json"

DEFAULT_SMAS_CONFIG = {
    "bearerToken": "",
    "employeeName": "Trần Đức Tình",
    "employeeId": "3a2367a5-d6aa-00d3-be30-777cebff2be1",
    "employeeCode": "64629602-01-97",
    "phoneNumber": "0352911750",
    "schoolYearCode": "2026-2027",
    "schoolYearId": "4e3f2957-5e33-11f1-80d6-fa163e7dd11b",
    "schoolYearStartDate": "2026-09-07",
    "syncSettings": {
        "distributeProgramId": "3a2367a5-efd9-2a99-b1be-b9415c898c69",
        "divisiveConfigurationName": "Chính",
        "status": 3
    }
}

# 16 target classes / subjects của Thầy Trần Đức Tình
TARGET_SUBJECTS = [
    {"className": "3A", "subjectCode": "1024", "gradeCode": "03", "subjectName": "Tin học"},
    {"className": "3B", "subjectCode": "1024", "gradeCode": "03", "subjectName": "Tin học"},
    {"className": "3C", "subjectCode": "1024", "gradeCode": "03", "subjectName": "Tin học"},
    {"className": "4A", "subjectCode": "1024", "gradeCode": "04", "subjectName": "Tin học"},
    {"className": "4B", "subjectCode": "1024", "gradeCode": "04", "subjectName": "Tin học"},
    {"className": "5A", "subjectCode": "1024", "gradeCode": "05", "subjectName": "Tin học"},
    {"className": "5B", "subjectCode": "1024", "gradeCode": "05", "subjectName": "Tin học"},
    {"className": "6A", "subjectCode": "1044", "gradeCode": "06", "subjectName": "Tin học"},
    {"className": "6B", "subjectCode": "1044", "gradeCode": "06", "subjectName": "Tin học"},
    {"className": "7A", "subjectCode": "1044", "gradeCode": "07", "subjectName": "Tin học"},
    {"className": "7B", "subjectCode": "1044", "gradeCode": "07", "subjectName": "Tin học"},
    {"className": "8",  "subjectCode": "1044", "gradeCode": "08", "subjectName": "Tin học"},
    {"className": "9",  "subjectCode": "1044", "gradeCode": "09", "subjectName": "Tin học"},
    {"className": "6A", "subjectCode": "1795", "gradeCode": "06", "subjectName": "Giáo dục thể chất"},
    {"className": "6B", "subjectCode": "1795", "gradeCode": "06", "subjectName": "Giáo dục thể chất"},
    {"className": "8",  "subjectCode": "1796", "gradeCode": "08", "subjectName": "HĐ TN, hướng nghiệp"}
]

def read_json_file(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading JSON from {path}: {e}")
        return default

def write_json_file(path: Path, data: Any):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error writing JSON to {path}: {e}")
        return False

# ==========================================
# CẤU HÌNH TOKEN DÙNG CHUNG CẢ HỆ THỐNG
# ==========================================

def get_system_token() -> str:
    """Lấy token SMAS dùng chung toàn hệ thống từ config.json"""
    cfg = read_json_file(CONFIG_PATH, {})
    return (
        cfg.get("token") or
        cfg.get("bearer_token") or
        cfg.get("bearerToken") or
        cfg.get("smas", {}).get("bearerToken", "")
    ).strip()

def get_smas_config() -> Dict[str, Any]:
    cfg = read_json_file(CONFIG_PATH, {})
    smas_cfg = cfg.get("smas", {})
    # Merge with default
    merged = dict(DEFAULT_SMAS_CONFIG)
    merged.update(smas_cfg)
    # Ensure bearerToken is synced from top-level token if missing
    sys_tok = get_system_token()
    if sys_tok and not merged.get("bearerToken"):
        merged["bearerToken"] = sys_tok
    return merged

def save_smas_config(smas_cfg: Dict[str, Any]):
    cfg = read_json_file(CONFIG_PATH, {})
    cfg["smas"] = smas_cfg
    # Đồng bộ token lên top-level để toàn bộ hệ thống dùng chung
    tok = smas_cfg.get("bearerToken", "").strip()
    if tok:
        cfg["token"] = tok
        cfg["bearer_token"] = tok
        cfg["bearerToken"] = tok
    write_json_file(CONFIG_PATH, cfg)

def decode_jwt(token: str) -> Dict[str, Any]:
    """Giải mã payload của Token JWT không cần thư viện ngoài"""
    try:
        parts = token.strip().split(".")
        if len(parts) < 2:
            return {}
        payload_b64 = parts[1]
        rem = len(payload_b64) % 4
        if rem > 0:
            payload_b64 += "=" * (4 - rem)
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes.decode("utf-8", errors="ignore"))
    except Exception as e:
        print(f"Lỗi giải mã JWT token: {e}")
        return {}

def sync_token_to_system(token: str) -> Dict[str, Any]:
    """
    Khi nhận Token SMAS, giải mã JWT và tự động đồng bộ DÙNG CHUNG TOÀN HỆ THỐNG:
    - Lưu token vào 'token', 'bearer_token', 'bearerToken', và 'smas.bearerToken'
    - Cập nhật tên giáo viên ('Trần Đức Tình'), mã cán bộ, số điện thoại
    - Cập nhật năm học ('2026-2027')
    - Cập nhật danh sách người ký duyệt KHBD
    - Tự động nạp PPCT nếu chưa có
    """
    token = token.strip()
    payload = decode_jwt(token)
    
    fullname = payload.get("fullname") or "Trần Đức Tình"
    employee_id = payload.get("employeeid") or "3a2367a5-d6aa-00d3-be30-777cebff2be1"
    employee_code = payload.get("name") or "64629602-01-97"
    phone_number = payload.get("phone_number") or ""
    school_year = "2026-2027"

    cfg = read_json_file(CONFIG_PATH, {})
    
    # 1. Cấu hình dùng chung
    cfg["token"] = token
    cfg["bearer_token"] = token
    cfg["bearerToken"] = token
    cfg["teacher_name"] = fullname
    cfg["school_year"] = school_year
    cfg["ppct_source"] = "smas"
    cfg["teaching_date_format"] = "smas_exact"
    cfg["auto_calc_teaching_date"] = True

    # 2. Cấu hình nhánh SMAS
    smas_cfg = cfg.get("smas", dict(DEFAULT_SMAS_CONFIG))
    smas_cfg["bearerToken"] = token
    smas_cfg["employeeName"] = fullname
    smas_cfg["employeeId"] = employee_id
    smas_cfg["employeeCode"] = employee_code
    smas_cfg["phoneNumber"] = phone_number
    smas_cfg["schoolYearCode"] = school_year
    smas_cfg["schoolYearId"] = smas_cfg.get("schoolYearId") or "4e3f2957-5e33-11f1-80d6-fa163e7dd11b"
    cfg["smas"] = smas_cfg

    # 3. Cập nhật danh sách người ký
    signers = cfg.get("signers_list", [])
    if fullname not in signers:
        signers.insert(0, fullname)
        cfg["signers_list"] = signers

    write_json_file(CONFIG_PATH, cfg)

    # 4. Tự động kiểm tra và đảm bảo PPCT đã được tải
    try:
        ensure_ppct_db(token)
    except Exception as e:
        print("Cảnh báo khi nạp PPCT tự động:", e)

    return {
        "success": True,
        "fullname": fullname,
        "employeeId": employee_id,
        "employeeCode": employee_code,
        "phoneNumber": phone_number,
        "schoolYear": school_year,
        "message": f"Đã đồng bộ Token & Hồ sơ giáo viên {fullname} ({school_year}) dùng chung toàn hệ thống!"
    }

def check_smas_token(token: str = None) -> Dict[str, Any]:
    """Kiểm tra token còn hạn hay không qua API SMAS"""
    tok = (token or get_system_token()).strip()
    if not tok:
        return {"valid": False, "message": "Chưa có Bearer Token! Vui lòng nhập token SMAS."}

    smas_cfg = get_smas_config()
    url = "https://gateway.vtsmas.vn/api/abp/application-configuration"
    headers = {
        "authorization": f"Bearer {tok}",
        "schoolyear": smas_cfg.get("schoolYearCode", "2026-2027"),
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi",
        "origin": "https://vtsmas.vn",
        "referer": "https://vtsmas.vn/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status == 200:
                sync_token_to_system(tok)
                return {"valid": True, "message": "Token hợp lệ và đang hoạt động tốt trên hệ thống SMAS!"}
    except urllib.error.HTTPError as e:
        if e.code == 401:
            return {"valid": False, "message": "Token đã hết hạn hoặc không hợp lệ (HTTP 401). Vui lòng copy token mới từ F12."}
        return {"valid": False, "message": f"SMAS phản hồi mã lỗi HTTP {e.code}"}
    except Exception as e:
        return {"valid": False, "message": f"Không thể kết nối đến SMAS: {str(e)}"}

# ----------------- Thời Khóa Biểu -----------------
def load_schedule() -> List[Dict[str, Any]]:
    slots = read_json_file(SCHEDULE_PATH, [])
    if not slots and DEFAULT_SCHEDULE_PATH.exists():
        slots = read_json_file(DEFAULT_SCHEDULE_PATH, [])
        write_json_file(SCHEDULE_PATH, slots)
    return slots

def save_schedule(slots: List[Dict[str, Any]]):
    return write_json_file(SCHEDULE_PATH, slots)

def reset_schedule() -> List[Dict[str, Any]]:
    slots = read_json_file(DEFAULT_SCHEDULE_PATH, [])
    write_json_file(SCHEDULE_PATH, slots)
    return slots

def parse_tkb_excel(file_source: Any, teacher_name: str = None, save_to_schedule: bool = True) -> Dict[str, Any]:
    """
    Trích xuất Thời Khóa Biểu tự động từ file Excel (.xls hoặc .xlsx).
    Hỗ trợ cả trường THCS (Tin học, GDTC, HĐTN) và Tiểu học (Tin học khối 3, 4, 5).
    file_source: Đường dẫn file (str/Path) hoặc bytes/io.BytesIO
    """
    raw_bytes = None
    file_str = str(file_source) if isinstance(file_source, (str, Path)) else ""
    if isinstance(file_source, (str, Path)):
        p = Path(file_source)
        if not p.exists():
            raise FileNotFoundError(f"Không tìm thấy file TKB: {file_source}")
        with open(p, "rb") as f:
            raw_bytes = f.read()
    elif isinstance(file_source, (bytes, bytearray)):
        raw_bytes = bytes(file_source)
    elif hasattr(file_source, "read"):
        raw_bytes = file_source.read()
    else:
        raise ValueError("file_source không hợp lệ (phải là đường dẫn file hoặc bytes)")

    if not raw_bytes:
        raise ValueError("Dữ liệu file Excel rỗng!")

    grid = []
    # Kiểm tra BIFF8 .xls OLE2 signature hoặc đuôi mở rộng
    is_xls = raw_bytes.startswith(b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1') or file_str.lower().endswith(".xls")
    if is_xls:
        wb = xlrd.open_workbook(file_contents=raw_bytes)
        sheet = wb.sheet_by_index(0)
        for r in range(sheet.nrows):
            grid.append([sheet.cell_value(r, c) for c in range(sheet.ncols)])
    else:
        wb = openpyxl.load_workbook(io.BytesIO(raw_bytes), data_only=True)
        sheet = wb.active
        for row in sheet.iter_rows(values_only=True):
            grid.append(list(row))

    if not grid:
        raise ValueError("Sheet Excel không chứa dòng dữ liệu nào!")

    # Lấy thông tin lớp học từ all_classes.json
    classes_list = read_json_file(ALL_CLASSES_PATH, [])
    cls_map = {c["className"]: c for c in classes_list}

    # Xác định tên giáo viên
    if not teacher_name or not teacher_name.strip():
        smas_cfg = get_smas_config()
        teacher_name = smas_cfg.get("employeeName", "Trần Đức Tình")
    if not teacher_name or not teacher_name.strip():
        teacher_name = "Trần Đức Tình"

    t_clean = teacher_name.strip()
    t_parts = [p for p in t_clean.split() if len(p) >= 2]
    t_last = t_parts[-1].lower() if t_parts else "tình"
    t_pattern = re.compile(re.escape(t_clean), re.IGNORECASE)

    day_map = {
        '2': (1, 'Thứ Hai'), 'hai': (1, 'Thứ Hai'), 'thứ hai': (1, 'Thứ Hai'),
        '3': (2, 'Thứ Ba'), 'ba': (2, 'Thứ Ba'), 'thứ ba': (2, 'Thứ Ba'),
        '4': (3, 'Thứ Tư'), 'tư': (3, 'Thứ Tư'), 'thứ tư': (3, 'Thứ Tư'), 'bốn': (3, 'Thứ Tư'),
        '5': (4, 'Thứ Năm'), 'năm': (4, 'Thứ Năm'), 'thứ năm': (4, 'Thứ Năm'),
        '6': (5, 'Thứ Sáu'), 'sáu': (5, 'Thứ Sáu'), 'thứ sáu': (5, 'Thứ Sáu'),
        '7': (6, 'Thứ Bảy'), 'bảy': (6, 'Thứ Bảy'), 'thứ bảy': (6, 'Thứ Bảy')
    }

    def normalize_day(val):
        if val is None or val == '': return None
        s = str(val).strip().lower()
        if s.endswith('.0'): s = s[:-2]
        return day_map.get(s)

    def normalize_buoi(val):
        if not val: return None
        s = str(val).strip().lower()
        if 'sáng' in s: return (0, 'Sáng')
        if 'chiều' in s: return (1, 'Chiều')
        return None

    def normalize_period(val):
        if val is None or val == '': return None
        try:
            return int(float(str(val).strip()))
        except:
            return None

    num_rows = len(grid)
    num_cols = max(len(r) for r in grid) if grid else 0

    def get_val(r, c):
        if 0 <= r < len(grid) and 0 <= c < len(grid[r]):
            v = grid[r][c]
            return "" if v is None else str(v).strip()
        return ""

    # 1. Phát hiện hàng tiêu đề THCS và các cột lớp
    thcs_header_row = -1
    thcs_class_cols = {}
    for r in range(min(15, num_rows)):
        for c in range(min(12, num_cols)):
            v = get_val(r, c).replace('.0', '')
            if v in ['6A', '6B', '7A', '7B', '8', '9']:
                thcs_class_cols[c] = v
                if thcs_header_row == -1:
                    thcs_header_row = r

    if thcs_header_row == -1:
        thcs_header_row = 5 # Default row index

    slots = []
    seen_slots = set() # (dayOfWeek, section, period)

    # 2. Quét THCS
    cur_day = None
    cur_buoi = None
    # THCS nằm từ thcs_header_row + 1 đến khoảng dòng 37 (trước bảng Tiểu học in riêng)
    thcs_end_row = min(38, num_rows)
    for r in range(thcs_header_row + 1, thcs_end_row):
        d_val = normalize_day(get_val(r, 1))
        if d_val: cur_day = d_val
        b_val = normalize_buoi(get_val(r, 2))
        if b_val: cur_buoi = b_val
        p_val = normalize_period(get_val(r, 3))

        if not cur_day or not cur_buoi or not p_val:
            continue

        for c, cname in thcs_class_cols.items():
            cell_val = get_val(r, c)
            if not cell_val: continue

            # Kiểm tra tên GV
            is_match = False
            if t_pattern.search(cell_val) or (t_last in cell_val.lower()):
                is_match = True

            if is_match:
                key = (cur_day[0], cur_buoi[0], p_val)
                if key in seen_slots:
                    continue
                seen_slots.add(key)

                lines = [l.strip() for l in cell_val.split('\n') if l.strip()]
                raw_mon = lines[0] if lines else ''
                cls_info = cls_map.get(cname, {})

                if 'gdtc' in raw_mon.lower() or 'thể chất' in raw_mon.lower():
                    s_name = 'Giáo dục thể chất'
                    s_code = '1795'
                    t_name = 'Sân tập, còi, bóng'
                    tot_tool = 10
                elif 'hđtn' in raw_mon.lower() or 'hướng nghiệp' in raw_mon.lower() or 'hdtn' in raw_mon.lower():
                    s_name = 'HĐ TN, hướng nghiệp'
                    s_code = '1796'
                    t_name = 'Loa, micro'
                    tot_tool = 1
                else:
                    s_name = 'Tin học'
                    s_code = '1044'
                    t_name = 'Phòng máy tính'
                    tot_tool = 40

                sec_str = 'sang' if cur_buoi[0] == 0 else 'chieu'
                slot_id = f"slot_{cur_day[0] + 1}_{sec_str}_{p_val}"
                slots.append({
                    'id': slot_id,
                    'dayOfWeek': cur_day[0],
                    'dayName': cur_day[1],
                    'section': cur_buoi[0],
                    'sectionName': cur_buoi[1],
                    'period': p_val,
                    'className': cname,
                    'subjectName': s_name,
                    'subjectCode': s_code,
                    'schoolLevelCode': cls_info.get('schoolLevelCode', '03'),
                    'gradeCode': cls_info.get('gradeLevelCode', f"0{cname[0]}"),
                    'gradeName': cls_info.get('gradeLevel', f"Khối {cname[0]}"),
                    'toolName': t_name,
                    'totalTool': tot_tool,
                    'toolType': 1,
                    'isRegisterLearningTool': True,
                    'classId': cls_info.get('id', '')
                })

    # 3. Quét Tiểu Học (tìm các khối 3A, 3B, 3C, 4A, 4B, 5A, 5B)
    th_blocks = []
    # Tìm các cột có header là lớp tiểu học ở nửa bên phải (từ cột 10 trở đi)
    for c in range(10, num_cols):
        for r_hdr in [thcs_header_row, thcs_header_row - 1, thcs_header_row + 1]:
            if 0 <= r_hdr < num_rows:
                v = get_val(r_hdr, c).replace('.0', '')
                if v in ['3A', '3B', '3C', '4A', '4B', '5A', '5B']:
                    # Cột c là Môn học, c + 1 là GV dạy
                    # Dò ngược về trước để tìm cột Thứ, Buổi, Tiết của khối đó
                    thu_c, buoi_c, tiet_c = None, None, None
                    for prev_c in range(c, max(9, c - 8), -1):
                        hdr_val = get_val(thcs_header_row + 1, prev_c).lower()
                        if 'thứ' in hdr_val: thu_c = prev_c
                        elif 'buổi' in hdr_val: buoi_c = prev_c
                        elif 'tiết' in hdr_val: tiet_c = prev_c
                    th_blocks.append((v, c, c + 1, thu_c, buoi_c, tiet_c))

    # Quét dữ liệu Tiểu học ở bảng trên (dòng thcs_header_row + 1 đến 37)
    for cname, m_col, gv_col, thu_c, buoi_c, tiet_c in th_blocks:
        cur_d = None
        cur_b = None
        for r in range(thcs_header_row + 1, thcs_end_row):
            if thu_c is not None:
                d_val = normalize_day(get_val(r, thu_c))
                if d_val: cur_d = d_val
            if buoi_c is not None:
                b_val = normalize_buoi(get_val(r, buoi_c))
                if b_val: cur_b = b_val
            p_val = normalize_period(get_val(r, tiet_c)) if tiet_c is not None else None

            if not cur_d or not cur_b or not p_val:
                continue

            gv_val = get_val(r, gv_col)
            m_val = get_val(r, m_col)

            is_match = False
            if t_pattern.search(gv_val) or t_pattern.search(m_val) or (t_last in gv_val.lower()) or (t_last in m_val.lower()):
                is_match = True

            if is_match:
                key = (cur_d[0], cur_b[0], p_val)
                if key in seen_slots:
                    continue
                seen_slots.add(key)

                cls_info = cls_map.get(cname, {})
                sec_str = 'sang' if cur_b[0] == 0 else 'chieu'
                slot_id = f"slot_{cur_d[0] + 1}_{sec_str}_{p_val}"
                slots.append({
                    'id': slot_id,
                    'dayOfWeek': cur_d[0],
                    'dayName': cur_d[1],
                    'section': cur_b[0],
                    'sectionName': cur_b[1],
                    'period': p_val,
                    'className': cname,
                    'subjectName': 'Tin học',
                    'subjectCode': '1024',
                    'schoolLevelCode': cls_info.get('schoolLevelCode', '02'),
                    'gradeCode': cls_info.get('gradeLevelCode', f"0{cname[0]}"),
                    'gradeName': cls_info.get('gradeLevel', f"Khối {cname[0]}"),
                    'toolName': 'Máy tính',
                    'totalTool': 40,
                    'toolType': 1,
                    'isRegisterLearningTool': True,
                    'classId': cls_info.get('id', '')
                })

    # 4. Dự phòng nếu chưa đủ tiết Tiểu học: quét tiếp bảng in riêng bên dưới (dòng 38 trở đi)
    th_count = sum(1 for s in slots if s.get("schoolLevelCode") == "02")
    if th_count < 7 and num_rows > 38:
        # Tìm header ở dòng >= 38
        btm_header_row = -1
        btm_blocks = []
        for r in range(38, min(48, num_rows)):
            for c in range(10, num_cols):
                v = get_val(r, c).replace('.0', '')
                if v in ['3A', '3B', '3C', '4A', '4B', '5A', '5B']:
                    if btm_header_row == -1: btm_header_row = r
                    thu_c, buoi_c, tiet_c = None, None, None
                    for prev_c in range(c, max(9, c - 8), -1):
                        hdr_val = get_val(r + 1, prev_c).lower()
                        if 'thứ' in hdr_val: thu_c = prev_c
                        elif 'buổi' in hdr_val: buoi_c = prev_c
                        elif 'tiết' in hdr_val: tiet_c = prev_c
                    btm_blocks.append((v, c, c + 1, thu_c, buoi_c, tiet_c))

        if btm_blocks and btm_header_row != -1:
            for cname, m_col, gv_col, thu_c, buoi_c, tiet_c in btm_blocks:
                # Kiểm tra lớp này đã có trong slots chưa
                if any(s.get("className") == cname for s in slots):
                    continue
                cur_d = None
                cur_b = None
                for r in range(btm_header_row + 1, num_rows):
                    if thu_c is not None:
                        d_val = normalize_day(get_val(r, thu_c))
                        if d_val: cur_d = d_val
                    if buoi_c is not None:
                        b_val = normalize_buoi(get_val(r, buoi_c))
                        if b_val: cur_b = b_val
                    p_val = normalize_period(get_val(r, tiet_c)) if tiet_c is not None else None

                    if not cur_d or not cur_b or not p_val:
                        continue

                    gv_val = get_val(r, gv_col)
                    m_val = get_val(r, m_col)
                    if t_pattern.search(gv_val) or t_pattern.search(m_val) or (t_last in gv_val.lower()):
                        key = (cur_d[0], cur_b[0], p_val)
                        if key in seen_slots:
                            continue
                        seen_slots.add(key)
                        cls_info = cls_map.get(cname, {})
                        sec_str = 'sang' if cur_b[0] == 0 else 'chieu'
                        slot_id = f"slot_{cur_d[0] + 1}_{sec_str}_{p_val}"
                        slots.append({
                            'id': slot_id,
                            'dayOfWeek': cur_d[0],
                            'dayName': cur_d[1],
                            'section': cur_b[0],
                            'sectionName': cur_b[1],
                            'period': p_val,
                            'className': cname,
                            'subjectName': 'Tin học',
                            'subjectCode': '1024',
                            'schoolLevelCode': cls_info.get('schoolLevelCode', '02'),
                            'gradeCode': cls_info.get('gradeLevelCode', f"0{cname[0]}"),
                            'gradeName': cls_info.get('gradeLevel', f"Khối {cname[0]}"),
                            'toolName': 'Máy tính',
                            'totalTool': 40,
                            'toolType': 1,
                            'isRegisterLearningTool': True,
                            'classId': cls_info.get('id', '')
                        })

    # Sắp xếp danh sách tiết
    slots.sort(key=lambda s: (s['dayOfWeek'], s['section'], s['period']))

    if save_to_schedule and slots:
        save_schedule(slots)
        # Đồng thời cập nhật default_schedule.json làm mẫu chuẩn nếu muốn
        write_json_file(DEFAULT_SCHEDULE_PATH, slots)

    thcs_cnt = sum(1 for s in slots if s.get("schoolLevelCode") == "03")
    th_cnt = sum(1 for s in slots if s.get("schoolLevelCode") == "02")
    msg = f"Đã trích xuất thành công {len(slots)} tiết TKB của giáo viên {teacher_name} ({thcs_cnt} tiết THCS, {th_cnt} tiết Tiểu học)!"

    return {
        "success": True,
        "total": len(slots),
        "thcsCount": thcs_cnt,
        "thCount": th_cnt,
        "slots": slots,
        "teacherName": teacher_name,
        "message": msg
    }

# ----------------- PPCT SMAS -----------------
def load_smas_ppct() -> Dict[str, Any]:
    return read_json_file(SMAS_PPCT_DB_PATH, {})

def ensure_ppct_db(token: str = None) -> Dict[str, Any]:
    """Đảm bảo PPCT DB đã có dữ liệu; nếu chưa có, tự động dùng Token chung để tải từ SMAS"""
    db = load_smas_ppct()
    if db and len(db) >= 10:
        return db
    tok = token or get_system_token()
    if tok:
        try:
            print("Đang tự động tải PPCT từ SMAS API bằng Token chung...")
            refresh_ppct_from_smas(tok)
            return load_smas_ppct()
        except Exception as e:
            print(f"Không thể tải PPCT tự động: {e}")
    return db

def refresh_ppct_from_smas(token: str = None) -> Dict[str, Any]:
    """Tải và cập nhật toàn bộ 16 PPCT thật từ SMAS cho tài khoản đang đăng nhập"""
    tok = (token or get_system_token()).strip()
    if not tok:
        raise ValueError("Chưa có Bearer Token trong cấu hình hệ thống!")

    smas_cfg = get_smas_config()
    classes = read_json_file(ALL_CLASSES_PATH, [])
    classes_map = {c['className']: c for c in classes}
    school_year_id = smas_cfg.get("schoolYearId", "4e3f2957-5e33-11f1-80d6-fa163e7dd11b")

    headers = {
        'authorization': f'Bearer {tok}',
        'schoolyear': smas_cfg.get('schoolYearCode', '2026-2027'),
        'content-type': 'application/json',
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'vi',
        'origin': 'https://vtsmas.vn',
        'referer': 'https://vtsmas.vn/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    url = 'https://gateway.vtsmas.vn/api/can-bo/phan-phoi-chuong-trinh/phan-trang'
    ppct_db = load_smas_ppct()
    updated_count = 0

    for t in TARGET_SUBJECTS:
        cls_obj = classes_map.get(t['className'])
        if not cls_obj:
            continue
        class_id = cls_obj['id']
        payload = {
            "filterItems": [
                {"value": str(t['subjectCode']), "propertyName": "subjectCode", "comparison": 0},
                {"value": None, "propertyName": "divisiveConfigurationId", "comparison": 0},
                {"value": str(t['gradeCode']), "propertyName": "gradeCode", "comparison": 0},
                {"value": class_id, "propertyName": "classId", "comparison": 0},
                {"value": school_year_id, "propertyName": "schoolYearId", "comparison": 0}
            ],
            "sortThenByItems": [
                {"sort": "period", "sortDirection": 0, "isSortByLastWord": True}
            ],
            "skipCount": 0,
            "sort": "period",
            "maxResultCount": 200,
            "sortDirection": 0
        }

        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method='POST')
        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                items = data.get('items', [])
                key = f"{t['className']}_{t['subjectCode']}"
                ppct_db[key] = {
                    "className": t['className'],
                    "classId": class_id,
                    "subjectCode": t['subjectCode'],
                    "subjectName": t['subjectName'],
                    "gradeCode": t['gradeCode'],
                    "totalCount": data.get('totalCount', len(items)),
                    "lessons": [
                        {
                            "id": item.get('id'),
                            "period": item.get('period'),
                            "name": item.get('name'),
                            "weekNumber": item.get('weekNumber'),
                            "weekValue": item.get('weekValue')
                        }
                        for item in items
                    ]
                }
                updated_count += 1
        except Exception as e:
            print(f"Lỗi tải PPCT lớp {t['className']}: {e}")

    write_json_file(SMAS_PPCT_DB_PATH, ppct_db)
    return {"status": "ok", "updatedClasses": updated_count, "totalClasses": len(ppct_db)}

# ----------------- Danh Mục Môn Học & Tải PPCT Động Từ SMAS -----------------

def get_all_smas_subjects(token: Optional[str] = None, refresh: bool = False) -> List[Dict[str, Any]]:
    """Lấy danh mục tất cả môn học chuẩn của SMAS"""
    if not refresh and SMAS_SUBJECTS_PATH.exists():
        subs = read_json_file(SMAS_SUBJECTS_PATH, [])
        if subs and len(subs) > 0:
            return subs

    tok = (token or get_system_token()).strip()
    if not tok:
        return read_json_file(SMAS_SUBJECTS_PATH, [])

    url = "https://gateway.vtsmas.vn/api/cau-hinh/danh-muc/loai-danh-muc/DM_MON_HOC/03?IsSort=true"
    headers = {
        "authorization": f"Bearer {tok}",
        "schoolyear": get_smas_config().get("schoolYearCode", "2026-2027"),
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi",
        "origin": "https://vtsmas.vn",
        "referer": "https://vtsmas.vn/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, list):
                write_json_file(SMAS_SUBJECTS_PATH, data)
                return data
    except Exception as e:
        print(f"Lỗi tải danh mục môn học từ SMAS: {e}")

    return read_json_file(SMAS_SUBJECTS_PATH, [])

def resolve_subject_code(subject_query: str, grade_code: str = "09") -> Dict[str, Any]:
    """
    Tự động chuẩn hóa và ánh xạ tên môn sang subjectCode chuẩn của SMAS:
    Ví dụ: 'Tin học', 'Tin 9', 'Toán', 'Ngữ Văn', 'KHTN', 'Công nghệ'...
    """
    q = str(subject_query or "Tin học").strip().lower()
    # Loại bỏ các từ thừa như 'môn', 'bài', số lớp
    q_clean = re.sub(r'^(môn\s*|mon\s*)', '', q)
    q_clean = re.sub(r'\s*\d+$', '', q_clean).strip()

    # Ánh xạ thông dụng ưu tiên
    COMMON_MAP = {
        "tin": {"code": "1044", "name": "Tin học"},
        "tin học": {"code": "1044", "name": "Tin học"},
        "th": {"code": "1044", "name": "Tin học"},
        "văn": {"code": "19", "name": "Ngữ Văn"},
        "ngữ văn": {"code": "19", "name": "Ngữ Văn"},
        "ngu van": {"code": "19", "name": "Ngữ Văn"},
        "toán": {"code": "15", "name": "Toán"},
        "toan": {"code": "15", "name": "Toán"},
        "khtn": {"code": "66", "name": "Khoa học Tự nhiên"},
        "khoa học tự nhiên": {"code": "66", "name": "Khoa học Tự nhiên"},
        "khoa hoc tu nhien": {"code": "66", "name": "Khoa học Tự nhiên"},
        "lsdl": {"code": "1783", "name": "Lịch sử và Địa lí"},
        "lịch sử và địa lí": {"code": "1783", "name": "Lịch sử và Địa lí"},
        "công nghệ": {"code": "27", "name": "Công nghệ"},
        "cong nghe": {"code": "27", "name": "Công nghệ"},
        "tiếng anh": {"code": "22", "name": "Tiếng Anh"},
        "tieng anh": {"code": "22", "name": "Tiếng Anh"},
        "anh": {"code": "22", "name": "Tiếng Anh"},
        "gdtc": {"code": "1795", "name": "Giáo dục thể chất"},
        "thể dục": {"code": "1795", "name": "Giáo dục thể chất"},
        "hdtn": {"code": "1796", "name": "HĐ TN, hướng nghiệp"},
        "hoạt động trải nghiệm": {"code": "1796", "name": "HĐ TN, hướng nghiệp"},
        "gddp": {"code": "1798", "name": "Giáo dục địa phương"},
        "âm nhạc": {"code": "1043", "name": "Âm nhạc"},
        "mĩ thuật": {"code": "1051", "name": "Mĩ Thuật"},
        "gdcd": {"code": "26", "name": "GDCD"}
    }

    # Tiểu học (khối 3, 4, 5) môn Tin học có mã 1024
    is_primary = str(grade_code) in ["01", "02", "03", "04", "05", "1", "2", "3", "4", "5"]
    if is_primary and q_clean in ["tin", "tin học", "th"]:
        return {"subjectCode": "1024", "subjectName": "Tin học"}

    if q_clean in COMMON_MAP:
        return {"subjectCode": COMMON_MAP[q_clean]["code"], "subjectName": COMMON_MAP[q_clean]["name"]}

    # Tra trong danh mục môn học của SMAS
    subs = get_all_smas_subjects()
    for s in subs:
        c_name = str(s.get("cateName", "")).lower()
        a_name = str(s.get("acronymName", "")).lower()
        if q_clean == c_name or q_clean == a_name or q_clean in c_name:
            return {"subjectCode": str(s.get("cateCode")), "subjectName": s.get("cateName")}

    return {"subjectCode": "1044", "subjectName": "Tin học"}

def resolve_class_info(class_query: str, grade_code: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Tra cứu classId, className, gradeCode từ all_classes.json"""
    classes = read_json_file(ALL_CLASSES_PATH, [])
    if not classes:
        return None

    raw = str(class_query or "").strip().upper()
    # Chuẩn hóa ví dụ 'LỚP 6A' -> '6A', 'LỚP 9' -> '9'
    raw = re.sub(r'^(LỚP|LOP|KHỐI|KHOI)\s*', '', raw).strip()

    # 1. Tìm chính xác className
    for c in classes:
        if c.get("className", "").upper() == raw:
            return {
                "classId": c.get("id"),
                "className": c.get("className"),
                "gradeCode": c.get("gradeLevelCode")
            }

    # 2. Tìm theo số khối (ví dụ raw='6' hoặc grade_code='06')
    target_grade = grade_code or (f"0{raw}" if len(raw) == 1 and raw.isdigit() else raw)
    for c in classes:
        if c.get("gradeLevelCode") == target_grade or c.get("className", "").startswith(raw):
            return {
                "classId": c.get("id"),
                "className": c.get("className"),
                "gradeCode": c.get("gradeLevelCode")
            }

    return None

def fetch_smas_ppct_on_demand(grade: str, subject: str = "Tin học", class_name: Optional[str] = None, token: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Tự động kết nối SMAS lấy dữ liệu PPCT động khi hệ thống cần.
    - Tự động tra cứu mã môn học và mã lớp học.
    - Gọi API SMAS phân trang lấy toàn bộ số tiết.
    - Lưu vào smas_ppct_db.json để dùng lại.
    """
    tok = (token or get_system_token()).strip()
    if not tok:
        print("fetch_smas_ppct_on_demand: Chưa có Bearer Token hệ thống!")
        return None

    # Xác định khối lớp
    m = re.search(r'\d+', str(class_name or grade or "9"))
    num_grade = m.group(0) if m else "9"
    grade_code = f"0{num_grade}" if len(num_grade) == 1 else num_grade

    # Ánh xạ môn học & lớp
    sub_info = resolve_subject_code(subject, grade_code=grade_code)
    cls_info = resolve_class_info(class_name or num_grade, grade_code=grade_code)
    if not cls_info:
        # Fallback thử với tên lớp ghép A ví dụ '6A', '7A', '9'
        cls_info = resolve_class_info(f"{num_grade}A", grade_code=grade_code) or resolve_class_info(num_grade, grade_code=grade_code)

    if not cls_info:
        print(f"fetch_smas_ppct_on_demand: Không tìm thấy thông tin lớp {class_name or grade} trong all_classes.json")
        return None

    smas_cfg = get_smas_config()
    school_year_id = smas_cfg.get("schoolYearId", "4e3f2957-5e33-11f1-80d6-fa163e7dd11b")
    class_id = cls_info["classId"]
    c_name = cls_info["className"]
    sub_code = sub_info["subjectCode"]
    sub_name = sub_info["subjectName"]

    url = "https://gateway.vtsmas.vn/api/can-bo/phan-phoi-chuong-trinh/phan-trang"
    headers = {
        "authorization": f"Bearer {tok}",
        "schoolyear": smas_cfg.get("schoolYearCode", "2026-2027"),
        "content-type": "application/json",
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi",
        "origin": "https://vtsmas.vn",
        "referer": "https://vtsmas.vn/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    payload = {
        "filterItems": [
            {"value": str(sub_code), "propertyName": "subjectCode", "comparison": 0},
            {"value": None, "propertyName": "divisiveConfigurationId", "comparison": 0},
            {"value": str(grade_code), "propertyName": "gradeCode", "comparison": 0},
            {"value": class_id, "propertyName": "classId", "comparison": 0},
            {"value": school_year_id, "propertyName": "schoolYearId", "comparison": 0}
        ],
        "sortThenByItems": [
            {"sort": "period", "sortDirection": 0, "isSortByLastWord": True}
        ],
        "skipCount": 0,
        "sort": "period",
        "maxResultCount": 200,
        "sortDirection": 0
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            items = data.get("items", [])
            key = f"{c_name}_{sub_code}"
            ppct_db = load_smas_ppct()
            ppct_db[key] = {
                "className": c_name,
                "classId": class_id,
                "subjectCode": sub_code,
                "subjectName": sub_name,
                "gradeCode": grade_code,
                "totalCount": data.get("totalCount", len(items)),
                "lessons": [
                    {
                        "id": it.get("id"),
                        "period": it.get("period"),
                        "name": it.get("name"),
                        "weekNumber": it.get("weekNumber"),
                        "weekValue": it.get("weekValue")
                    }
                    for it in items
                ]
            }
            write_json_file(SMAS_PPCT_DB_PATH, ppct_db)
            print(f"fetch_smas_ppct_on_demand: Đã tải thành công {len(items)} tiết PPCT môn {sub_name} Lớp {c_name} từ SMAS!")
            return ppct_db[key]
    except Exception as e:
        print(f"fetch_smas_ppct_on_demand: Lỗi kết nối SMAS: {e}")
        return None

# ----------------- Hợp nhất PPCT SMAS vào định dạng hệ thống KHBD -----------------

def get_ppct_as_khbd_dict() -> Dict[str, Any]:
    """
    Chuyển đổi toàn bộ dữ liệu 16 môn/lớp từ SMAS PPCT thành định dạng chuẩn của KHBD
    để khbd_engine, server.py và giao diện web sử dụng trực tiếp làm nguồn PPCT chính!
    """
    smas_db = load_smas_ppct()
    if not smas_db:
        smas_db = ensure_ppct_db()

    khbd_ppct_dict = {}

    for k, v in smas_db.items():
        c_name = v.get("className", "")
        s_name = v.get("subjectName", "")
        lessons = v.get("lessons", [])

        # Tạo key thân thiện để hiển thị trên dropdown giao diện
        display_key = f"[SMAS] {s_name} {c_name}.smas"

        items = []
        for les in lessons:
            period = les.get("period", 1)
            w_num = les.get("weekNumber") or 1
            # Tự động tính ngày dạy chuẩn từ TKB SMAS
            teaching_d = get_exact_teaching_date_from_tkb(c_name, w_num, date_format="smas_exact")

            items.append({
                "stt": period,
                "tuan": w_num,
                "tiet": period,
                "ten_bai": les.get("name") or f"Tiết {period}",
                "ngay_day": teaching_d,
                "ghi_chu": f"SMAS GUID: {les.get('id')}",
                "program_id": les.get("id"),
                "source": "smas",
                "class_name": c_name,
                "subject_name": s_name
            })

        # Extract grade number from className (e.g. 8, 7A, 6B)
        grd_m = re.search(r'\d+', c_name)
        grd_num = grd_m.group(0) if grd_m else "9"

        khbd_ppct_dict[display_key] = {
            "type": "standard_ppct",
            "source": "smas",
            "title": f"Phân phối chương trình SMAS: Lớp {c_name} - Môn {s_name} ({len(items)} tiết)",
            "className": c_name,
            "subject": s_name,
            "subjectName": s_name,
            "grade": grd_num,
            "items": items
        }

        # Tạo thêm alias tiện lợi theo số lớp: ví dụ `SMAS_9` hoặc `_Lop_9.xlsx` fallback
        alias_key = f"SMAS_{c_name}_{v.get('subjectCode')}"
        khbd_ppct_dict[alias_key] = khbd_ppct_dict[display_key]

    return khbd_ppct_dict

def get_best_ppct_items_for_grade(grade: str, subject: str = "Tin học") -> List[Dict[str, Any]]:
    """
    Tra cứu danh sách items PPCT SMAS tốt nhất cho một khối lớp.
    Nếu chưa có trong DB, tự động dùng Token chung kết nối SMAS tải về ngay khi cần!
    """
    smas_dict = get_ppct_as_khbd_dict()
    norm_grade = str(grade or "9").upper().replace("LỚP", "").replace("LOP", "").strip()

    # 1. Tìm chính xác theo tên lớp và môn
    for k, v in smas_dict.items():
        if k.startswith("[SMAS]") and norm_grade == str(v.get("className", "")).upper():
            if not subject or subject.lower() in str(v.get("subjectName", "")).lower():
                return v.get("items", [])

    # 2. Fallback tìm kiếm tương đối trong DB hiện có
    for k, v in smas_dict.items():
        if k.startswith("[SMAS]") and norm_grade in str(v.get("className", "")).upper():
            if not subject or subject.lower() in str(v.get("subjectName", "")).lower():
                return v.get("items", [])

    # 3. Nếu chưa có, TỰ ĐỘNG DÙNG TOKEN CHUNG TẢI VỀ TỪ SMAS ON-DEMAND
    try:
        print(f"Chưa có PPCT môn '{subject}' cho lớp '{grade}', đang tự động kết nối SMAS để tải về...")
        fetched = fetch_smas_ppct_on_demand(norm_grade, subject)
        if fetched and fetched.get("lessons"):
            # Nạp lại từ điển đã cập nhật
            fresh_dict = get_ppct_as_khbd_dict()
            for k, v in fresh_dict.items():
                if k.startswith("[SMAS]") and (norm_grade == str(v.get("className", "")).upper() or norm_grade in str(v.get("className", "")).upper()):
                    if not subject or subject.lower() in str(v.get("subjectName", "")).lower():
                        return v.get("items", [])
    except Exception as ex:
        print(f"Lỗi tải tự động PPCT từ SMAS cho lớp {grade}: {ex}")

    return []

# ----------------- Hợp nhất Ngày Dạy (teaching_date) chuẩn SMAS -----------------
def get_week_monday_sunday(week_num: int, start_date_str: str = "2026-09-07"):
    """Tính ngày Thứ Hai và Chủ Nhật của tuần `week_num` (1-indexed)"""
    try:
        s = str(start_date_str or "2026-09-07").strip()
        if "-" in s:
            parts = s.split("-")
            dt = datetime.date(int(parts[0]), int(parts[1]), int(parts[2])) if len(parts[0]) == 4 else datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
        elif "/" in s:
            parts = s.split("/")
            dt = datetime.date(int(parts[0]), int(parts[1]), int(parts[2])) if len(parts[0]) == 4 else datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
        else:
            dt = datetime.date(2026, 9, 7)
    except Exception:
        dt = datetime.date(2026, 9, 7)

    w = max(1, int(week_num or 1))
    monday = dt + datetime.timedelta(days=(w - 1) * 7)
    sunday = monday + datetime.timedelta(days=6)
    return monday, sunday

def get_exact_teaching_date_from_tkb(class_name: str, week_num: int, period_num: Optional[int] = None, date_format: str = "smas_exact") -> str:
    """
    Tính chính xác ngày học của lớp dựa theo Thời Khóa Biểu SMAS.
    - class_name: Tên lớp (ví dụ: '9', 'Lớp 9', '3A', '6B'...)
    - week_num: Số tuần (ví dụ: 1, 2, 3...)
    - date_format:
        'smas_exact': Ngày học chính xác của lớp (ví dụ '22/09/2026' hoặc '22/09/2026, 24/09/2026')
        'd2_to_d6': '21/09/2026 - 25/09/2026'
        'tu_den': 'Từ 21/09 đến 25/09/2026'
    """
    smas_cfg = get_smas_config()
    start_date_str = smas_cfg.get("schoolYearStartDate", "2026-09-07")
    monday, sunday = get_week_monday_sunday(week_num, start_date_str)

    if date_format == "d2_to_d6":
        friday = monday + datetime.timedelta(days=4)
        return f"{monday.strftime('%d/%m/%Y')} - {friday.strftime('%d/%m/%Y')}"
    elif date_format == "tu_den":
        friday = monday + datetime.timedelta(days=4)
        return f"Từ {monday.strftime('%d/%m')} đến {friday.strftime('%d/%m/%Y')}"

    # Lấy các slot của lớp này trong TKB
    slots = load_schedule()
    norm_class = str(class_name or "").upper().replace("LỚP", "").replace("LOP", "").strip()
    if not norm_class:
        cfg = read_json_file(CONFIG_PATH, {})
        norm_class = str(cfg.get("classes") or cfg.get("grade") or "").upper().replace("LỚP", "").replace("LOP", "").strip()

    matched_slots = []
    grade_digits = re.findall(r'\d+', norm_class)
    grade_num = grade_digits[0] if grade_digits else ""

    for s in slots:
        sc = str(s.get("className", "")).upper().strip()
        if sc == norm_class or (norm_class and (norm_class in sc or sc in norm_class)):
            matched_slots.append(s)
        elif grade_num and (sc == grade_num or sc.startswith(grade_num)):
            matched_slots.append(s)

    if not matched_slots:
        # Fallback về Thứ 2 đến Thứ 6 nếu không có slot trong TKB
        friday = monday + datetime.timedelta(days=4)
        return f"{monday.strftime('%d/%m/%Y')} - {friday.strftime('%d/%m/%Y')}"

    # Sắp xếp các slot theo thứ trong tuần, buổi, tiết
    matched_slots.sort(key=lambda s: (s.get("dayOfWeek", 1), s.get("section", 0), s.get("period", 1)))

    exact_dates = []
    for s in matched_slots:
        day_offset = int(s.get("dayOfWeek", 1)) - 1
        slot_date = monday + datetime.timedelta(days=day_offset)
        d_str = slot_date.strftime("%d/%m/%Y")
        if d_str not in exact_dates:
            exact_dates.append(d_str)

    if len(exact_dates) == 1:
        return exact_dates[0]
    elif len(exact_dates) > 1:
        return ", ".join(exact_dates)

    return monday.strftime("%d/%m/%Y")

# ----------------- Sinh Payload Lịch Báo Giảng SMAS -----------------
def generate_weekly_payloads(start_week: int = 1, end_week: int = 1, start_date_str: str = "2026-09-07", start_period_offset: Dict[str, int] = None) -> List[Dict[str, Any]]:
    cfg = get_smas_config()
    slots = load_schedule()
    smas_ppct_db = load_smas_ppct()
    start_period_offset = start_period_offset or {}

    slots = sorted(slots, key=lambda s: (s.get("dayOfWeek", 1), s.get("section", 0), s.get("period", 1)))

    period_counters = {}
    for s in slots:
        k = f"{s.get('className')}_{s.get('subjectCode')}"
        if k not in period_counters:
            custom_start = start_period_offset.get(k)
            if custom_start is not None:
                period_counters[k] = int(custom_start)
            else:
                class_slots = sum(1 for sl in slots if sl.get('className') == s.get('className') and sl.get('subjectCode') == s.get('subjectCode'))
                periods_per_w = max(class_slots, 1)
                period_counters[k] = (start_week - 1) * periods_per_w + 1

    weeks_data = []

    for w in range(start_week, end_week + 1):
        monday, sunday = get_week_monday_sunday(w, start_date_str)
        date_from_str = monday.strftime("%Y-%m-%d")
        date_to_str = sunday.strftime("%Y-%m-%d")

        level02_details = []
        level03_details = []

        for s in slots:
            day_offset = int(s.get("dayOfWeek", 1)) - 1
            slot_date = monday + datetime.timedelta(days=day_offset)
            date_study_str = slot_date.strftime("%d/%m/%Y")

            k = f"{s.get('className')}_{s.get('subjectCode')}"
            current_ppct_period = period_counters.get(k, 1)

            program_id = cfg.get("syncSettings", {}).get("distributeProgramId", "3a2367a5-efd9-2a99-b1be-b9415c898c69")
            lesson_name = f"Tiết {current_ppct_period}"

            smas_class_ppct = smas_ppct_db.get(k, {})
            smas_lessons = smas_class_ppct.get("lessons", [])
            for les in smas_lessons:
                if les.get("period") == current_ppct_period:
                    program_id = les.get("id") or program_id
                    lesson_name = les.get("name") or lesson_name
                    break

            tool_name = "máy tính" if "Tin" in s.get("subjectName", "") else "còi, bóng"
            total_tool = "40" if "Tin" in s.get("subjectName", "") else "2"

            detail_item = {
                "dayOfWeek": int(s.get("dayOfWeek", 1)),
                "section": int(s.get("section", 0)),
                "period": int(s.get("period", 1)),
                "classId": s.get("classId", ""),
                "className": s.get("className", ""),
                "gradeCode": s.get("gradeCode", ""),
                "gradeName": s.get("gradeName", ""),
                "subjectCode": str(s.get("subjectCode", "")),
                "subjectName": s.get("subjectName", ""),
                "description": None,
                "divisiveConfigurationId": None,
                "divisiveConfigurationName": cfg.get("syncSettings", {}).get("divisiveConfigurationName", "Chính"),
                "distributeProgramId": program_id,
                "distributeProgramPeriod": str(current_ppct_period),
                "isRegisterLearningTool": True,
                "toolName": s.get("toolName", tool_name),
                "totalTool": str(s.get("totalTool", total_tool)),
                "toolType": 1,
                "distributeProgramName": lesson_name,
                "status": int(cfg.get("syncSettings", {}).get("status", 3)),
                "employeeSubstituteId": None,
                "dateStudy": date_study_str
            }

            level = s.get("schoolLevelCode", "02")
            if level == "02":
                level02_details.append(detail_item)
            else:
                level03_details.append(detail_item)

            period_counters[k] = current_ppct_period + 1

        p02 = {
            "employeeName": cfg.get("employeeName", "Trần Đức Tình"),
            "employeeId": cfg.get("employeeId", "3a2367a5-d6aa-00d3-be30-777cebff2be1"),
            "employeeCode": cfg.get("employeeCode", "64629602-01-97"),
            "phoneNumber": cfg.get("phoneNumber", ""),
            "schoolYearId": cfg.get("schoolYearId", "4e3f2957-5e33-11f1-80d6-fa163e7dd11b"),
            "schoolLevelCode": "02",
            "schoolYearCode": cfg.get("schoolYearCode", "2026-2027"),
            "dateFrom": date_from_str,
            "dateTo": date_to_str,
            "teachingScheduleDetails": level02_details
        }

        p03 = {
            "employeeName": cfg.get("employeeName", "Trần Đức Tình"),
            "employeeId": cfg.get("employeeId", "3a2367a5-d6aa-00d3-be30-777cebff2be1"),
            "employeeCode": cfg.get("employeeCode", "64629602-01-97"),
            "phoneNumber": cfg.get("phoneNumber", ""),
            "schoolYearId": cfg.get("schoolYearId", "4e3f2957-5e33-11f1-80d6-fa163e7dd11b"),
            "schoolLevelCode": "03",
            "schoolYearCode": cfg.get("schoolYearCode", "2026-2027"),
            "dateFrom": date_from_str,
            "dateTo": date_to_str,
            "teachingScheduleDetails": level03_details
        }

        weeks_data.append({
            "weekNumber": w,
            "dateFrom": date_from_str,
            "dateTo": date_to_str,
            "dateRangeLabel": f"Tuần {w} ({monday.strftime('%d/%m/%Y')} - {sunday.strftime('%d/%m/%Y')})",
            "level02_count": len(level02_details),
            "level03_count": len(level03_details),
            "total_slots": len(level02_details) + len(level03_details),
            "payload_level02": p02,
            "payload_level03": p03
        })

    return weeks_data

# ----------------- Đẩy Lịch Báo Giảng Lên SMAS API -----------------
def sync_smas_weeks(weeks_to_sync: List[Dict[str, Any]], token: Optional[str] = None, selected_level: str = "all") -> List[Dict[str, Any]]:
    tok = (token or get_system_token()).strip()
    if not tok:
        raise ValueError("Chưa có Bearer Token! Vui lòng nhập token SMAS.")

    smas_cfg = get_smas_config()
    headers = {
        "authorization": f"Bearer {tok}",
        "schoolyear": smas_cfg.get("schoolYearCode", "2026-2027"),
        "content-type": "application/json",
        "accept": "application/json, text/plain, */*",
        "accept-language": "vi",
        "origin": "https://vtsmas.vn",
        "referer": "https://vtsmas.vn/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    url = "https://gateway.vtsmas.vn/api/can-bo/lich-bao-giang/tao"
    emp_id = smas_cfg.get("employeeId", "3a2367a5-d6aa-00d3-be30-777cebff2be1")
    sy_id = smas_cfg.get("schoolYearId", "4e3f2957-5e33-11f1-80d6-fa163e7dd11b")
    results = []

    def get_existing_week_id(date_from: str, date_to: str, level: str) -> Optional[str]:
        check_url = f"https://gateway.vtsmas.vn/api/can-bo/lich-bao-giang/theo-tuan/{date_from}/{date_to}/{emp_id}/{sy_id}/{level}"
        chk_req = urllib.request.Request(check_url, headers=headers)
        try:
            with urllib.request.urlopen(chk_req, timeout=10) as chk_resp:
                if chk_resp.status == 200:
                    body = chk_resp.read()
                    if body:
                        d = json.loads(body.decode("utf-8", errors="ignore"))
                        return d.get("id")
        except Exception:
            pass
        return None

    for w in weeks_to_sync:
        week_num = w.get("weekNumber")
        date_label = w.get("dateRangeLabel")
        date_from = w.get("dateFrom")
        date_to = w.get("dateTo")

        week_res = {
            "weekNumber": week_num,
            "label": date_label,
            "level02": None,
            "level03": None
        }

        # Cấp Tiểu học (02)
        if selected_level in ("all", "02") and w.get("payload_level02"):
            p02 = dict(w["payload_level02"])
            existing_id = get_existing_week_id(date_from, date_to, "02")
            if existing_id:
                p02["id"] = existing_id

            req = urllib.request.Request(url, data=json.dumps(p02).encode("utf-8"), headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_body = resp.read().decode("utf-8") if resp.status != 204 else ""
                    week_res["level02"] = {"success": True, "code": resp.status, "message": f"Thành công (HTTP {resp.status})", "updated": bool(existing_id)}
            except urllib.error.HTTPError as e:
                err_content = e.read().decode("utf-8", errors="ignore")
                week_res["level02"] = {"success": False, "code": e.code, "message": f"Lỗi HTTP {e.code}: {err_content[:200]}"}
            except Exception as e:
                week_res["level02"] = {"success": False, "code": 500, "message": f"Lỗi kết nối: {str(e)}"}

        # Cấp THCS (03)
        if selected_level in ("all", "03") and w.get("payload_level03"):
            p03 = dict(w["payload_level03"])
            existing_id = get_existing_week_id(date_from, date_to, "03")
            if existing_id:
                p03["id"] = existing_id

            req = urllib.request.Request(url, data=json.dumps(p03).encode("utf-8"), headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=15) as resp:
                    resp_body = resp.read().decode("utf-8") if resp.status != 204 else ""
                    week_res["level03"] = {"success": True, "code": resp.status, "message": f"Thành công (HTTP {resp.status})", "updated": bool(existing_id)}
            except urllib.error.HTTPError as e:
                err_content = e.read().decode("utf-8", errors="ignore")
                week_res["level03"] = {"success": False, "code": e.code, "message": f"Lỗi HTTP {e.code}: {err_content[:200]}"}
            except Exception as e:
                week_res["level03"] = {"success": False, "code": 500, "message": f"Lỗi kết nối: {str(e)}"}

        results.append(week_res)

    return results
