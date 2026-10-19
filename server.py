import os
import sys
import io
import re
import copy
import json
import subprocess
import shutil
from pathlib import Path
from aiohttp import web
import khbd_engine
import beeknoee_client
import nls_engine
import khgd_engine
import smas_engine

# Ensure UTF-8 stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "config.json"
PPCT_DIR = BASE_DIR / "PPCT"
WEB_DIR = BASE_DIR / "web"

CONFIG_EXAMPLE_PATH = BASE_DIR / "config.example.json"

def load_config():
    if not CONFIG_PATH.exists() and CONFIG_EXAMPLE_PATH.exists():
        try:
            import shutil
            shutil.copyfile(CONFIG_EXAMPLE_PATH, CONFIG_PATH)
        except Exception as e:
            print("Error initializing config from example:", e)

    if CONFIG_PATH.exists():
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading config:", e)
    return {}

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print("Error saving config:", e)
        return False

# Safe JSON parser to handle encoding edge-cases seamlessly
async def safe_get_json(request):
    try:
        return await request.json()
    except Exception:
        try:
            raw = await request.read()
            return json.loads(raw.decode("utf-8", errors="replace"))
        except Exception:
            return {}

# Web Handlers
async def index_handler(request):
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return web.FileResponse(index_file)
    return web.Response(text="Web UI index.html not found.", status=404)

async def api_get_config(request):
    cfg = load_config()
    return web.json_response({"success": True, "config": cfg})

async def api_save_config(request):
    data = await safe_get_json(request)
    cfg = load_config()
    cfg.update(data)

    # Tự động đồng bộ Token dùng chung cho toàn bộ hệ thống
    tok = (
        data.get("token") or 
        data.get("bearerToken") or 
        data.get("bearer_token") or 
        data.get("smas", {}).get("bearerToken") or 
        cfg.get("token") or 
        cfg.get("bearerToken")
    )
    if tok:
        tok = str(tok).strip()
        cfg["token"] = tok
        cfg["bearer_token"] = tok
        cfg["bearerToken"] = tok
        if "smas" not in cfg:
            cfg["smas"] = {}
        cfg["smas"]["bearerToken"] = tok
        try:
            smas_engine.sync_token_to_system(tok)
            cfg = load_config()
        except Exception as e:
            print("Lỗi đồng bộ token trong api_save_config:", e)

    save_config(cfg)
    return web.json_response({"success": True, "config": cfg})

async def api_get_ppct_files(request):
    ppct_dict = khbd_engine.load_all_ppct(str(PPCT_DIR))
    file_list = []
    for fn, info in ppct_dict.items():
        # Bỏ qua alias nội bộ
        if fn.startswith("SMAS_"):
            continue
        is_smas = fn.startswith("[SMAS]") or info.get("source") == "smas"
        file_list.append({
            "filename": fn,
            "title": info.get("title", fn),
            "type": info.get("type", "standard_ppct"),
            "subject": info.get("subjectName") or info.get("subject") or "Tin học",
            "grade": str(info.get("grade") or "9"),
            "className": str(info.get("className") or ""),
            "item_count": len(info.get("items", [])) if "items" in info else len(info.get("columns", {})),
            "is_smas": is_smas
        })
    # Ưu tiên xếp các bộ PPCT SMAS chính thức lên đầu
    file_list.sort(key=lambda x: (0 if x.get("is_smas") else 1, x["filename"]))
    return web.json_response({"success": True, "files": file_list})

async def api_get_ppct_data(request):
    filename = request.query.get("file", "_Lop_9.xlsx")
    ppct_dict = khbd_engine.load_all_ppct(str(PPCT_DIR))
    if filename in ppct_dict:
        data = copy.deepcopy(ppct_dict[filename])
        cfg = load_config()
        start_date = cfg.get("school_year_start_date", "2026-09-07")
        date_fmt = cfg.get("teaching_date_format", "d2_to_d6")
        if "items" in data:
            for item in data["items"]:
                if not item.get("ngay_day"):
                    w = item.get("tuan")
                    if w is not None:
                        item["ngay_day"] = khbd_engine.calculate_week_dates(w, start_date, date_fmt)
        return web.json_response({"success": True, "data": data})
    return web.json_response({"success": False, "error": f"File {filename} not found"}, status=404)

async def api_update_ppct_dates(request):
    data = await safe_get_json(request)
    cfg = load_config()
    start_date = data.get("school_year_start_date") or cfg.get("school_year_start_date", "2026-09-07")
    date_fmt = data.get("teaching_date_format") or cfg.get("teaching_date_format", "d2_to_d6")
    filename = data.get("file")

    cfg["school_year_start_date"] = start_date
    cfg["teaching_date_format"] = date_fmt
    save_config(cfg)

    if filename:
        file_path = PPCT_DIR / filename
        if not file_path.exists():
            return web.json_response({"success": False, "error": f"File {filename} không tồn tại"}, status=404)
        success = khbd_engine.update_ppct_file_teaching_dates(str(file_path), start_date, date_fmt)
        return web.json_response({
            "success": success,
            "updated_files": [filename] if success else [],
            "message": f"Đã cập nhật ngày dạy cho {filename}" if success else "Không thể cập nhật file này"
        })
    else:
        updated = khbd_engine.update_all_ppct_teaching_dates(str(PPCT_DIR), start_date, date_fmt)
        return web.json_response({
            "success": True,
            "updated_files": updated,
            "message": f"Đã cập nhật ngày dạy thành công cho {len(updated)} file PPCT trong thư mục PPCT!"
        })

async def api_scan_folder(request):
    data = await safe_get_json(request)
    folder_path = data.get("folder", str(BASE_DIR)).strip()
    ppct_filename = data.get("ppct_file", "_Lop_9.xlsx")

    if not os.path.exists(folder_path):
        return web.json_response({"success": False, "error": f"Thư mục không tồn tại: {folder_path}"}, status=400)

    cfg = load_config()
    cfg["ppct_file"] = ppct_filename
    if "naming_scheme" in data:
        cfg["naming_scheme"] = data["naming_scheme"]
    if "custom_pattern" in data:
        cfg["custom_pattern"] = data["custom_pattern"]
    if "teacher_name" in data:
        cfg["teacher_name"] = data["teacher_name"]
    if "subject" in data:
        cfg["subject"] = data["subject"]
    if "classes" in data:
        cfg["classes"] = data["classes"]

    # Load PPCT items (Tự động resolve chính xác theo môn và khối)
    ppct_dict = khbd_engine.load_all_ppct(str(PPCT_DIR))
    sub_cfg = str(cfg.get("subject", "Tin học"))
    grade_cfg = str(cfg.get("classes") or cfg.get("grade") or "9")

    resolved_fn, ppct_data = khbd_engine.resolve_best_ppct(
        ppct_dict,
        requested_filename=ppct_filename,
        subject=sub_cfg,
        grade=grade_cfg
    )
    ppct_filename = resolved_fn
    cfg["ppct_file"] = resolved_fn
    ppct_items = ppct_data.get("items", [])
    if ppct_data.get("subjectName") or ppct_data.get("subject"):
        sub_cfg = data.get("subject") or cfg.get("subject") or ppct_data.get("subjectName") or ppct_data.get("subject")
        cfg["subject"] = sub_cfg
    if ppct_data.get("grade"):
        grade_cfg = data.get("classes") or data.get("grade") or cfg.get("classes") or cfg.get("grade") or str(ppct_data.get("grade"))
        cfg["classes"] = grade_cfg
        cfg["grade"] = grade_cfg

    files = []
    try:
        for entry in os.scandir(folder_path):
            if entry.is_file() and entry.name.endswith(".docx") and not entry.name.startswith("~$"):
                # Skip template itself unless requested
                if entry.name.lower() in ["mẫu.docx", "mau.docx"]:
                    continue

                full_path = entry.path
                try:
                    lesson_info = khbd_engine.parse_docx_file(full_path)
                    cur_items = ppct_items
                    matched_ppct = khbd_engine.match_lesson_with_ppct(lesson_info, cur_items)
                    target_fn = khbd_engine.generate_target_filename(lesson_info, matched_ppct, cfg)

                    # Compute effective teaching_date for this scanned lesson
                    teaching_date = ""
                    if matched_ppct and matched_ppct.get("ngay_day"):
                        teaching_date = matched_ppct["ngay_day"]
                    elif cfg.get("auto_calc_teaching_date", True):
                        week_val = (matched_ppct.get("tuan") if matched_ppct else None) or lesson_info.get("week") or lesson_info.get("tuan")
                        if week_val is not None and str(week_val).strip():
                            start_date = cfg.get("school_year_start_date", "2026-09-07")
                            date_fmt = cfg.get("teaching_date_format", "smas_exact")
                            c_name = lesson_info.get("detected_grade") or cfg.get("classes") or cfg.get("grade") or ""
                            teaching_date = khbd_engine.calculate_week_dates(week_val, start_date, date_fmt, class_name=c_name)

                    files.append({
                        "file_path": full_path,
                        "filename": entry.name,
                        "lesson_info": lesson_info,
                        "matched_ppct": matched_ppct,
                        "week": (matched_ppct.get("tuan") if matched_ppct else None) or lesson_info.get("week") or "1",
                        "periods": (matched_ppct.get("tiet") if matched_ppct else None) or lesson_info.get("tiet_str") or "1",
                        "bai_name": (matched_ppct.get("ten_bai") if matched_ppct else None) or lesson_info.get("bai_title") or "",
                        "teaching_date": teaching_date,
                        "target_filename": target_fn,
                        "status": "ready"
                    })
                except Exception as ex:
                    print(f"Error parsing file {entry.name}: {ex}")
                    files.append({
                        "file_path": full_path,
                        "filename": entry.name,
                        "error": str(ex),
                        "status": "error"
                    })
    except Exception as e:
        return web.json_response({"success": False, "error": f"Lỗi đọc thư mục: {str(e)}"}, status=500)

    # Sort files by lesson number if possible
    def sort_key(f):
        bai_num = f.get("lesson_info", {}).get("bai_num", "")
        m = re.search(r'\d+', str(bai_num))
        return int(m.group(0)) if m else 999
    files.sort(key=sort_key)

    return web.json_response({
        "success": True,
        "folder": folder_path,
        "total_files": len(files),
        "files": files,
        "ppct_file": ppct_filename
    })

async def api_recalc_filenames(request):
    """
    Tái tạo tên file đích cho danh sách giáo án đang quét theo quy tắc đặt tên mới
    """
    try:
        data = await safe_get_json(request)
        files = data.get("files", [])
        cfg = load_config()
        if "naming_scheme" in data:
            cfg["naming_scheme"] = data["naming_scheme"]
        if "custom_pattern" in data:
            cfg["custom_pattern"] = data["custom_pattern"]
        if "grade" in data:
            cfg["grade"] = data["grade"]
        if "classes" in data:
            cfg["classes"] = data["classes"]
        if "subject" in data:
            cfg["subject"] = data["subject"]
        if "teacher_name" in data:
            cfg["teacher_name"] = data["teacher_name"]
            
        save_config(cfg)

        results = []
        for f in files:
            lesson_info = f.get("lesson_info") or {
                "bai_num": f.get("bai_num") or f.get("lesson_num") or (f.get("lesson_info", {}).get("bai_num") if isinstance(f.get("lesson_info"), dict) else ""),
                "bai_title": f.get("bai_name") or f.get("lesson_name") or (f.get("lesson_info", {}).get("bai_title") if isinstance(f.get("lesson_info"), dict) else ""),
                "week": f.get("week"),
                "tiet_str": f.get("periods"),
                "detected_grade": cfg.get("grade") or cfg.get("classes")
            }
            matched_ppct = f.get("matched_ppct")
            new_fn = khbd_engine.generate_target_filename(lesson_info, matched_ppct, cfg)
            results.append({
                "filename": f.get("filename"),
                "target_filename": new_fn
            })

        return web.json_response({"success": True, "files": results})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_preview_diff(request):
    data = await safe_get_json(request)
    file_path = data.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return web.json_response({"success": False, "error": "File không tồn tại"}, status=404)

    cfg = load_config()
    if "config" in data:
        cfg.update(data["config"])

    lesson_info = khbd_engine.parse_docx_file(file_path)
    
    # PPCT matching
    ppct_dict = khbd_engine.load_all_ppct(str(PPCT_DIR))
    sub_cfg = str(cfg.get("subject", "Tin học"))
    grade_cfg = str(cfg.get("classes") or cfg.get("grade") or "9")
    ppct_filename = data.get("ppct_file", cfg.get("ppct_file", "_Lop_9.xlsx"))
    resolved_fn, ppct_data = khbd_engine.resolve_best_ppct(
        ppct_dict,
        requested_filename=ppct_filename,
        subject=sub_cfg,
        grade=grade_cfg
    )
    cfg["ppct_file"] = resolved_fn
    cur_items = ppct_data.get("items", [])
    matched_ppct = khbd_engine.match_lesson_with_ppct(lesson_info, cur_items)

    target_fn = khbd_engine.generate_target_filename(lesson_info, matched_ppct, cfg)

    # Build 'Before' representation
    before_view = {
        "filename": os.path.basename(file_path),
        "header_texts": lesson_info.get("top_texts", []),
        "has_old_table": lesson_info.get("has_old_table", False),
        "old_table_rows": lesson_info.get("old_table_sample", []),
        "footer": "(Chưa chuẩn hoá / Trống)"
    }

    # Build 'After' representation matching Mau KHBD THCS.docx
    chude = data.get("chude") or lesson_info.get("chude") or ""
    bai_num = data.get("bai_num") or lesson_info.get("bai_num") or "1"
    bai_name = data.get("bai_name") or lesson_info.get("bai_title") or (matched_ppct.get("ten_bai") if matched_ppct else "")
    subject = data.get("subject") or cfg.get("subject", "Tin học")
    classes = data.get("classes") or cfg.get("classes", "9")
    duration = data.get("duration") or cfg.get("duration", "2")
    school_year = cfg.get("school_year", "2025-2026")
    teacher_name = cfg.get("teacher_name", "Lê Thị Phương Thảo")
    department = cfg.get("department", "Tổ Tự Nhiên")
    school_name = cfg.get("school_name", "Trường TH&THCS Đăk Trôi")
    week = data.get("week") or (matched_ppct.get("tuan") if matched_ppct else None) or lesson_info.get("week") or "1"
    periods = data.get("periods") or (str(matched_ppct.get("tiet")) if matched_ppct else None) or lesson_info.get("tiet_str") or "1"

    # Teaching date calculation
    data_date = data.get("teaching_date")
    if data_date and str(data_date).strip() not in ["../../2026", ""]:
        teaching_date = str(data_date).strip()
    elif matched_ppct and matched_ppct.get("ngay_day"):
        teaching_date = matched_ppct["ngay_day"]
    elif cfg.get("auto_calc_teaching_date", True):
        start_date = cfg.get("school_year_start_date", "2026-09-07")
        date_fmt = cfg.get("teaching_date_format", "smas_exact")
        c_name = cfg.get("classes") or cfg.get("grade") or ""
        teaching_date = khbd_engine.calculate_week_dates(week, start_date, date_fmt, class_name=c_name)
    else:
        teaching_date = cfg.get("teaching_date", "../../2026")

    # Format Title
    bai_name = khbd_engine.clean_bai_name(bai_name)
    prefix = cfg.get("title_prefix", "TÊN BÀI DẠY: ")
    if cfg.get("title_prefix_ten_bai_day", True):
        if bai_num and not f"bài {bai_num}".lower() in bai_name.lower():
            bai_title_full = f"{prefix}BÀI {bai_num}. {bai_name.upper()}"
        else:
            bai_title_full = f"{prefix}{bai_name.upper()}"
    else:
        bai_title_full = f"BÀI {bai_num}: {bai_name.upper()}" if bai_num else bai_name.upper()

    title_school = (cfg.get("title_signer_school") or cfg.get("title_signer_left") or "Duyệt của tổ chuyên môn").strip()
    signer_school = (cfg.get("signer_school") or cfg.get("signer_left") or "").strip()
    title_dept = (cfg.get("title_signer_dept") or cfg.get("title_signer_right") or "Người thực hiện").strip()
    signer_dept = (cfg.get("signer_dept") or cfg.get("signer_right") or "").strip()
    if signer_school or signer_dept:
        approval_view = {
            "col_left": {
                "title": title_school,
                "note": "(Ký và ghi rõ họ tên)",
                "signer_name": signer_school
            },
            "col_right": {
                "title": title_dept,
                "note": "(Ký và ghi rõ họ tên)",
                "signer_name": signer_dept
            }
        }
    else:
        approval_view = f"{title_school}\t\t\t\t        {title_dept}"

    after_view = {
        "filename": target_fn,
        "header_top": f"Kế hoạch bài dạy {subject} {classes}, năm học {school_year}",
        "table_top": {
            "col_left": [
                f"Tuần:\t{week}",
                f"Tiết: {periods}",
                f"Ngày dạy: {teaching_date}"
            ],
            "col_right": [
                f"Họ và tên giáo viên: {teacher_name}",
                f"Tổ chuyên môn: {department}"
            ]
        },
        "title_block": [
            {"text": bai_title_full, "bold": True, "align": "center"},
            {"text": f"{khbd_engine.get_subject_type_label(subject, cfg)}: {subject}; lớp: {classes}", "bold": False, "align": "center"},
            {"text": f"Thời gian thực hiện: {duration} tiết", "bold": False, "align": "center"}
        ],
        "approval_block": approval_view,
        "footer": f"{teacher_name} - {school_name}",
        "margins": "Trên: 2.0cm | Dưới: 2.0cm | Trái: 2.0cm | Phải: 1.5cm (Khổ A4)"
    }

    return web.json_response({
        "success": True,
        "before": before_view,
        "after": after_view
    })

async def api_process_batch(request):
    data = await safe_get_json(request)
    files_to_process = data.get("files", [])
    cfg_override = data.get("config", {})
    output_mode = data.get("output_mode", "new_folder") # 'new_folder' or 'inplace'
    custom_output_folder = data.get("output_folder", "").strip()

    cfg = load_config()
    cfg.update(cfg_override)

    results = []
    success_count = 0
    fail_count = 0

    # Determine output directory
    if output_mode == "new_folder":
        if custom_output_folder:
            out_dir = Path(custom_output_folder)
        else:
            first_folder = Path(files_to_process[0]["file_path"]).parent if files_to_process else BASE_DIR
            out_dir = first_folder / cfg.get("output_folder_name", "KHBD_DaSua")
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = None

    # Load PPCT for matching if needed
    ppct_dict = khbd_engine.load_all_ppct(str(PPCT_DIR))
    sub_cfg = str(cfg.get("subject", "Tin học"))
    grade_cfg = str(cfg.get("classes") or cfg.get("grade") or "9")
    ppct_filename = cfg.get("ppct_file", "_Lop_9.xlsx")
    resolved_fn, ppct_data = khbd_engine.resolve_best_ppct(
        ppct_dict,
        requested_filename=ppct_filename,
        subject=sub_cfg,
        grade=grade_cfg
    )
    cfg["ppct_file"] = resolved_fn
    ppct_items = ppct_data.get("items", [])
    if ppct_data.get("subjectName") or ppct_data.get("subject"):
        sub_cfg = cfg_override.get("subject") or cfg.get("subject") or ppct_data.get("subjectName") or ppct_data.get("subject")
        cfg["subject"] = sub_cfg
    if ppct_data.get("grade"):
        grade_cfg = cfg_override.get("classes") or cfg_override.get("grade") or cfg.get("classes") or cfg.get("grade") or str(ppct_data.get("grade"))
        cfg["classes"] = grade_cfg
        cfg["grade"] = grade_cfg

    for item in files_to_process:
        src_path = item.get("file_path")
        if not src_path or not os.path.exists(src_path):
            results.append({
                "file_path": src_path,
                "status": "error",
                "message": "File không tồn tại"
            })
            fail_count += 1
            continue

        try:
            lesson_info = khbd_engine.parse_docx_file(src_path)
            # Khớp chính xác với bộ PPCT đã giải quyết
            matched_ppct = khbd_engine.match_lesson_with_ppct(lesson_info, ppct_items)
            if not matched_ppct and item.get("matched_ppct"):
                matched_ppct = item.get("matched_ppct")

            # File-specific overrides if provided in request item
            file_cfg = dict(cfg)
            file_cfg["subject"] = cfg["subject"]
            file_cfg["classes"] = cfg["classes"]
            file_cfg["grade"] = cfg["grade"]

            if item.get("chude"):
                file_cfg["chude"] = item["chude"]

            if matched_ppct:
                file_cfg["bai_name"] = matched_ppct.get("ten_bai") or lesson_info.get("bai_title") or ""
                file_cfg["bai_num"] = str(matched_ppct.get("so_bai") or matched_ppct.get("bai_num") or matched_ppct.get("tiet") or "1")
                file_cfg["periods"] = str(matched_ppct.get("tiet_range") or matched_ppct.get("tiet") or "1")
                file_cfg["week"] = str(matched_ppct.get("tuan") if matched_ppct.get("tuan") is not None else "1")
                file_cfg["duration"] = str(matched_ppct.get("so_tiet") or matched_ppct.get("duration") or "1")
            else:
                if item.get("bai_name"):
                    file_cfg["bai_name"] = item["bai_name"]
                if item.get("bai_num"):
                    file_cfg["bai_num"] = item["bai_num"]
                file_cfg["week"] = item.get("week") or lesson_info.get("week") or "1"
                file_cfg["periods"] = item.get("periods") or lesson_info.get("tiet_str") or "1"
                file_cfg["duration"] = item.get("duration") or cfg.get("duration") or "1"

            # Tự động tính target_fn chuẩn theo bộ PPCT hiện hành
            target_fn = khbd_engine.generate_target_filename(lesson_info, matched_ppct, file_cfg)

            item_date = item.get("teaching_date")
            if item_date and str(item_date).strip() not in ["../../2026", ""]:
                file_cfg["teaching_date"] = str(item_date).strip()
            elif matched_ppct and matched_ppct.get("ngay_day"):
                file_cfg["teaching_date"] = matched_ppct["ngay_day"]

            if output_mode == "new_folder":
                dest_path = str(out_dir / target_fn)
                khbd_engine.transform_khbd_file(src_path, dest_path, lesson_info, matched_ppct, file_cfg)
            else: # inplace with backup
                src_p = Path(src_path)
                backup_dir = src_p.parent / "_backup_KHBD"
                backup_dir.mkdir(exist_ok=True)
                backup_file = backup_dir / src_p.name
                shutil.copy2(src_path, backup_file)

                # If renaming inplace
                dest_path = str(src_p.parent / target_fn)
                # If target is different, save to temp then rename
                temp_dest = dest_path + ".tmp"
                khbd_engine.transform_khbd_file(src_path, temp_dest, lesson_info, matched_ppct, file_cfg)
                if os.path.exists(src_path) and src_path != dest_path:
                    os.remove(src_path)
                if os.path.exists(dest_path):
                    os.remove(dest_path)
                os.rename(temp_dest, dest_path)

            # 1. Tự động đồng bộ Yêu cầu cần đạt (YCCĐ) từ Kế hoạch giáo dục (KHGD) nếu được bật
            khgd_synced = False
            matched_khgd_name = None
            if data.get("sync_khgd_yccd", True):
                try:
                    sub_val = file_cfg.get("subject", "Tin học")
                    grade_val = file_cfg.get("classes", file_cfg.get("grade", "9"))
                    title_val = file_cfg.get("bai_name") or lesson_info.get("bai_title", "")
                    bai_num_val = file_cfg.get("bai_num") or lesson_info.get("bai_num", "")
                    
                    matched_khgd = khgd_engine.match_lesson_in_khgd(grade=grade_val, lesson_title=title_val, bai_num=bai_num_val)
                    if matched_khgd and matched_khgd.get("yccd_text"):
                        khgd_engine.apply_khgd_yccd_to_khbd(dest_path, dest_path, matched_khgd["yccd_text"])
                        khgd_synced = True
                        matched_khgd_name = matched_khgd.get("ten_bai")
                except Exception as khgd_err:
                    print(f"Lỗi đồng bộ KHGD YCCĐ cho {dest_path}: {khgd_err}")

            # 2. Tự động tích hợp Năng lực số (NLS) sau khi format nếu được kích hoạt
            nls_info = None
            if data.get("auto_integrate_nls", False):
                try:
                    highlight_red = data.get("highlight_red", True)
                    sub_val = file_cfg.get("subject", "Tin học")
                    grade_val = file_cfg.get("classes", file_cfg.get("grade", "9"))
                    title_val = file_cfg.get("bai_name") or lesson_info.get("bai_title", "")
                    nls_res = nls_engine.integrate_khbd_nls(
                        file_path=dest_path,
                        output_path=dest_path,
                        subject=sub_val,
                        grade=grade_val,
                        lesson_title=title_val,
                        highlight_red=highlight_red
                    )
                    nls_info = nls_res
                except Exception as nls_err:
                    print(f"Lỗi tích hợp NLS cho {dest_path}: {nls_err}")
                    nls_info = {"status": "error", "message": str(nls_err)}

            success_count += 1
            msg_parts = ["Đã sửa chuẩn mẫu & đổi tên thành công"]
            if khgd_synced:
                msg_parts.append(f"Mục tiêu: Đã khớp KHGD ({matched_khgd_name})")
            if nls_info:
                msg_parts.append(f"NLS: {nls_info.get('status')}")

            results.append({
                "original_file": os.path.basename(src_path),
                "new_file": target_fn,
                "output_path": dest_path,
                "status": "success",
                "message": " • ".join(msg_parts),
                "khgd_synced": khgd_synced,
                "matched_khgd": matched_khgd_name,
                "nls_info": nls_info
            })
        except Exception as e:
            print(f"Error processing {src_path}: {e}")
            fail_count += 1
            results.append({
                "original_file": os.path.basename(src_path),
                "status": "error",
                "message": str(e)
            })

    return web.json_response({
        "success": True,
        "output_mode": output_mode,
        "output_directory": str(out_dir) if out_dir else "inplace",
        "total": len(files_to_process),
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results
    })

async def api_fast_rename(request):
    """Đổi tên file cực nhanh không cần mở và can thiệp cấu trúc XML của DOCX"""
    data = await safe_get_json(request)
    files_to_process = data.get("files", [])
    cfg_override = data.get("config", {})
    output_mode = data.get("output_mode", "new_folder") # 'new_folder' or 'inplace'
    custom_output_folder = data.get("output_folder", "").strip()

    cfg = load_config()
    cfg.update(cfg_override)

    results = []
    success_count = 0
    fail_count = 0

    if output_mode == "new_folder":
        if custom_output_folder:
            out_dir = Path(custom_output_folder)
        else:
            first_folder = Path(files_to_process[0]["file_path"]).parent if files_to_process else BASE_DIR
            out_dir = first_folder / cfg.get("output_folder_name", "KHBD_DaDoiTen")
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = None

    ppct_dict = khbd_engine.load_all_ppct(str(PPCT_DIR))
    sub_cfg = str(cfg.get("subject", "Tin học"))
    grade_cfg = str(cfg.get("classes") or cfg.get("grade") or "9")
    ppct_filename = cfg.get("ppct_file", "_Lop_9.xlsx")
    resolved_fn, ppct_data = khbd_engine.resolve_best_ppct(
        ppct_dict,
        requested_filename=ppct_filename,
        subject=sub_cfg,
        grade=grade_cfg
    )
    cfg["ppct_file"] = resolved_fn
    ppct_items = ppct_data.get("items", [])
    if ppct_data.get("subjectName") or ppct_data.get("subject"):
        sub_cfg = cfg_override.get("subject") or cfg.get("subject") or ppct_data.get("subjectName") or ppct_data.get("subject")
        cfg["subject"] = sub_cfg
    if ppct_data.get("grade"):
        grade_cfg = cfg_override.get("classes") or cfg_override.get("grade") or cfg.get("classes") or cfg.get("grade") or str(ppct_data.get("grade"))
        cfg["classes"] = grade_cfg
        cfg["grade"] = grade_cfg

    for item in files_to_process:
        src_path = item.get("file_path")
        if not src_path or not os.path.exists(src_path):
            fail_count += 1
            results.append({
                "original_file": os.path.basename(src_path) if src_path else "",
                "status": "error",
                "message": "File không tồn tại"
            })
            continue

        try:
            file_cfg = dict(cfg)
            lesson_info = khbd_engine.parse_docx_file(src_path)
            matched_ppct = khbd_engine.match_lesson_with_ppct(lesson_info, ppct_items)
            if not matched_ppct and item.get("matched_ppct"):
                matched_ppct = item.get("matched_ppct")
            if matched_ppct:
                file_cfg["bai_name"] = matched_ppct.get("ten_bai") or lesson_info.get("bai_title") or ""
                file_cfg["bai_num"] = str(matched_ppct.get("so_bai") or matched_ppct.get("bai_num") or matched_ppct.get("tiet") or "1")
                file_cfg["periods"] = str(matched_ppct.get("tiet_range") or matched_ppct.get("tiet") or "1")
                file_cfg["week"] = str(matched_ppct.get("tuan") if matched_ppct.get("tuan") is not None else "1")
                file_cfg["duration"] = str(matched_ppct.get("so_tiet") or matched_ppct.get("duration") or "1")
            target_fn = khbd_engine.generate_target_filename(lesson_info, matched_ppct, file_cfg)

            if output_mode == "new_folder":
                dest_path = str(out_dir / target_fn)
                shutil.copy2(src_path, dest_path)
            else: # inplace
                src_p = Path(src_path)
                backup_dir = src_p.parent / "_backup_KHBD"
                backup_dir.mkdir(exist_ok=True)
                shutil.copy2(src_path, backup_dir / src_p.name)

                dest_path = str(src_p.parent / target_fn)
                if os.path.abspath(src_path) != os.path.abspath(dest_path):
                    if os.path.exists(dest_path):
                        os.remove(dest_path)
                    os.rename(src_path, dest_path)

            success_count += 1
            results.append({
                "original_file": os.path.basename(src_path),
                "new_file": target_fn,
                "output_path": dest_path,
                "status": "success",
                "message": f"Đã đổi tên: {target_fn}"
            })
        except Exception as e:
            fail_count += 1
            results.append({
                "original_file": os.path.basename(src_path),
                "status": "error",
                "message": str(e)
            })

    return web.json_response({
        "success": True,
        "output_mode": output_mode,
        "output_directory": str(out_dir) if out_dir else "inplace",
        "total": len(files_to_process),
        "success_count": success_count,
        "fail_count": fail_count,
        "results": results
    })

async def api_open_folder(request):
    data = await request.json()
    folder_path = data.get("path", str(BASE_DIR)).strip()
    if not os.path.exists(folder_path):
        folder_path = str(BASE_DIR)

    try:
        # On Windows, open via explorer.exe
        subprocess.Popen(f'explorer "{os.path.abspath(folder_path)}"')
        return web.json_response({"success": True, "path": folder_path})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

def get_effective_ai_key(provided_key=None, ai_cfg=None):
    if provided_key and provided_key.strip() and not provided_key.startswith("YOUR_"):
        return provided_key.strip()
    if ai_cfg is None:
        cfg = load_config()
        ai_cfg = cfg.get("ai_config", {})
    key = ai_cfg.get("api_key", "").strip()
    if key and not key.startswith("YOUR_"):
        return key
    env_key = os.environ.get("BEE_API_KEY", "").strip()
    if env_key:
        return env_key
    return beeknoee_client.DEFAULT_API_KEY

async def api_ai_analyze(request):
    data = await safe_get_json(request)
    file_path = data.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return web.json_response({"success": False, "error": "File không tồn tại hoặc chưa được chọn"}, status=400)
    try:
        cfg = load_config()
        ai_cfg = cfg.get("ai_config", {})
        api_key = get_effective_ai_key(ai_cfg=ai_cfg)
        model = ai_cfg.get("model") or "gemini-3.1-flash-lite"
        client = beeknoee_client.BeeknoeeClient(api_key=api_key, model=model)
        text = beeknoee_client.extract_docx_text(file_path)
        eval_result = client.analyze_khbd(text)
        return web.json_response({
            "success": True,
            "filename": os.path.basename(file_path),
            "evaluation": eval_result
        })
    except Exception as e:
        print(f"AI analyze error: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_ai_status(request):
    cfg = load_config()
    ai_cfg = cfg.get("ai_config", {})
    return web.json_response({
        "success": True,
        "enabled": ai_cfg.get("enabled", False),
        "model": ai_cfg.get("model", "gemini-3.1-flash-lite"),
        "has_key": bool(ai_cfg.get("api_key"))
    })

async def api_ai_test_connection(request):
    data = await safe_get_json(request)
    cfg = load_config()
    ai_cfg = cfg.get("ai_config", {})
    api_key = get_effective_ai_key(data.get("api_key"), ai_cfg)
    model = data.get("model") or ai_cfg.get("model") or "gemini-3.1-flash-lite"
    base_url = data.get("base_url") or ai_cfg.get("base_url") or "https://platform.beeknoee.com/api/v1"

    if not api_key:
        return web.json_response({"success": False, "error": "Chưa có Beekone API Key"}, status=400)

    import time
    t0 = time.time()
    try:
        client = beeknoee_client.BeeknoeeClient(api_key=api_key, base_url=base_url, model=model)
        resp = client.chat("Phản hồi chính xác: BEEKONE_OK", system_prompt="Test kết nối nhanh.", temperature=0.1, max_tokens=20)
        latency = int((time.time() - t0) * 1000)
        return web.json_response({
            "success": True,
            "message": "Kết nối Beekone AI thành công!",
            "model": model,
            "latency_ms": latency,
            "sample_response": resp.strip()
        })
    except Exception as e:
        return web.json_response({
            "success": False,
            "error": f"Lỗi kết nối Beekone AI: {str(e)}"
        }, status=500)

async def api_ai_analyze_title(request):
    data = await safe_get_json(request)
    file_path = data.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return web.json_response({"success": False, "error": "File không tồn tại hoặc chưa được chỉ định"}, status=400)

    cfg = load_config()
    ai_cfg = cfg.get("ai_config", {})
    api_key = get_effective_ai_key(data.get("api_key"), ai_cfg)
    model = data.get("model") or ai_cfg.get("model") or "gemini-3.1-flash-lite"

    # Load PPCT items
    ppct_dict = khbd_engine.load_all_ppct(str(PPCT_DIR))
    ppct_filename = data.get("ppct_file") or cfg.get("ppct_file", "_Lop_9.xlsx")
    ppct_data = ppct_dict.get(ppct_filename, {})
    ppct_items = ppct_data.get("items", [])

    try:
        client = beeknoee_client.BeeknoeeClient(api_key=api_key, model=model)
        doc_text = beeknoee_client.extract_docx_text(file_path)
        filename = os.path.basename(file_path)

        ai_res = client.analyze_lesson_title_with_ppct(doc_text, ppct_items=ppct_items, filename=filename)
        if not ai_res or "error" in ai_res:
            err = ai_res.get("error", "Không nhận được phản hồi hợp lệ từ AI")
            return web.json_response({"success": False, "error": err}, status=500)

        # Parse & format
        bai_num = str(ai_res.get("bai_num") or "1").strip()
        bai_title = str(ai_res.get("bai_title") or "").strip()
        chude = str(ai_res.get("chude") or "").strip()
        tuan = str(ai_res.get("tuan") or "1").strip()
        tiet = str(ai_res.get("tiet") or "1, 2").strip()
        matched_ppct = ai_res.get("matched_ppct")

        # Fallback to local match if AI didn't provide matched_ppct
        temp_info = {
            "bai_num": bai_num,
            "bai_title": bai_title,
            "tiet_str": tiet,
            "detected_grade": cfg.get("grade", "9"),
            "detected_subject": cfg.get("subject", "Tin học")
        }
        if not matched_ppct:
            matched_ppct = khbd_engine.match_lesson_with_ppct(temp_info, ppct_items)

        # Calculate effective teaching date
        teaching_date = ""
        if matched_ppct and matched_ppct.get("ngay_day"):
            teaching_date = matched_ppct["ngay_day"]
        elif cfg.get("auto_calc_teaching_date", True):
            start_date = cfg.get("school_year_start_date", "2026-09-07")
            date_fmt = cfg.get("teaching_date_format", "d2_to_d6")
            teaching_date = khbd_engine.calculate_week_dates(tuan, start_date, date_fmt)

        # Target filename
        target_fn = khbd_engine.generate_target_filename(temp_info, matched_ppct, cfg)

        return web.json_response({
            "success": True,
            "result": {
                "file_path": file_path,
                "filename": filename,
                "bai_num": bai_num,
                "bai_title": bai_title,
                "chude": chude,
                "tuan": tuan,
                "tiet": tiet,
                "matched_ppct": matched_ppct,
                "teaching_date": teaching_date,
                "target_filename": target_fn,
                "confidence": ai_res.get("confidence", "high"),
                "explanation": ai_res.get("explanation", "")
            }
        })
    except Exception as e:
        print(f"Error in api_ai_analyze_title: {e}")
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_ai_batch_analyze_titles(request):
    data = await safe_get_json(request)
    files = data.get("files", [])
    if not files:
        return web.json_response({"success": False, "error": "Danh sách file trống"}, status=400)

    cfg = load_config()
    ai_cfg = cfg.get("ai_config", {})
    api_key = get_effective_ai_key(data.get("api_key"), ai_cfg)
    model = data.get("model") or ai_cfg.get("model") or "gemini-3.1-flash-lite"

    ppct_dict = khbd_engine.load_all_ppct(str(PPCT_DIR))
    ppct_filename = data.get("ppct_file") or cfg.get("ppct_file", "_Lop_9.xlsx")
    ppct_items = ppct_dict.get(ppct_filename, {}).get("items", [])

    client = beeknoee_client.BeeknoeeClient(api_key=api_key, model=model)
    results = []

    for f_item in files:
        file_path = f_item.get("file_path")
        if not file_path or not os.path.exists(file_path):
            results.append({
                "file_path": file_path,
                "filename": f_item.get("filename", ""),
                "status": "error",
                "error": "File không tồn tại"
            })
            continue

        try:
            doc_text = beeknoee_client.extract_docx_text(file_path)
            fn = os.path.basename(file_path)
            ai_res = client.analyze_lesson_title_with_ppct(doc_text, ppct_items=ppct_items, filename=fn)
            if not ai_res or "error" in ai_res:
                results.append({
                    "file_path": file_path,
                    "filename": fn,
                    "status": "error",
                    "error": ai_res.get("error", "AI không trả về kết quả")
                })
                continue

            bai_num = str(ai_res.get("bai_num") or "1").strip()
            bai_title = str(ai_res.get("bai_title") or "").strip()
            chude = str(ai_res.get("chude") or "").strip()
            tuan = str(ai_res.get("tuan") or "1").strip()
            tiet = str(ai_res.get("tiet") or "1, 2").strip()
            matched_ppct = ai_res.get("matched_ppct")

            temp_info = {
                "bai_num": bai_num,
                "bai_title": bai_title,
                "tiet_str": tiet,
                "detected_grade": cfg.get("grade", "9"),
                "detected_subject": cfg.get("subject", "Tin học")
            }
            if not matched_ppct:
                matched_ppct = khbd_engine.match_lesson_with_ppct(temp_info, ppct_items)

            teaching_date = ""
            if matched_ppct and matched_ppct.get("ngay_day"):
                teaching_date = matched_ppct["ngay_day"]
            elif cfg.get("auto_calc_teaching_date", True):
                start_date = cfg.get("school_year_start_date", "2026-09-07")
                date_fmt = cfg.get("teaching_date_format", "d2_to_d6")
                teaching_date = khbd_engine.calculate_week_dates(tuan, start_date, date_fmt)

            target_fn = khbd_engine.generate_target_filename(temp_info, matched_ppct, cfg)

            results.append({
                "file_path": file_path,
                "filename": fn,
                "status": "success",
                "bai_num": bai_num,
                "bai_title": bai_title,
                "chude": chude,
                "tuan": tuan,
                "tiet": tiet,
                "matched_ppct": matched_ppct,
                "teaching_date": teaching_date,
                "target_filename": target_fn,
                "confidence": ai_res.get("confidence", "high"),
                "explanation": ai_res.get("explanation", "")
            })
        except Exception as ex:
            results.append({
                "file_path": file_path,
                "filename": os.path.basename(file_path),
                "status": "error",
                "error": str(ex)
            })

    return web.json_response({
        "success": True,
        "total": len(files),
        "results": results
    })

# --- NLS (Năng Lực Số) Handlers ---
async def api_nls_audit(request):
    data = await safe_get_json(request)
    file_path = data.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return web.json_response({"success": False, "error": "File không tồn tại"}, status=400)

    cfg = load_config()
    subject = data.get("subject") or cfg.get("subject", "Tin học")
    grade = data.get("grade") or cfg.get("grade", "9")
    lesson_title = data.get("lesson_title", "")

    result = nls_engine.audit_khbd_nls(file_path, subject=subject, grade=grade, lesson_title=lesson_title)
    return web.json_response({"success": True, "result": result})

async def api_nls_integrate(request):
    data = await safe_get_json(request)
    file_path = data.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return web.json_response({"success": False, "error": "File không tồn tại"}, status=400)

    cfg = load_config()
    output_path = data.get("output_path") or file_path
    subject = data.get("subject") or cfg.get("subject", "Tin học")
    grade = data.get("grade") or cfg.get("grade", "9")
    lesson_title = data.get("lesson_title", "")
    highlight_red = data.get("highlight_red", True)

    result = nls_engine.integrate_khbd_nls(
        file_path=file_path,
        output_path=output_path,
        subject=subject,
        grade=grade,
        lesson_title=lesson_title,
        highlight_red=highlight_red
    )
    return web.json_response({"success": True, "result": result})

async def api_nls_batch_integrate(request):
    data = await safe_get_json(request)
    files = data.get("files", [])
    if not files:
        return web.json_response({"success": False, "error": "Danh sách file trống"}, status=400)

    cfg = load_config()
    output_mode = data.get("output_mode", "new_folder") # 'new_folder' or 'inplace'
    custom_output_folder = data.get("output_folder", "").strip()
    highlight_red = data.get("highlight_red", True)
    only_audit = data.get("only_audit", False)

    if output_mode == "new_folder":
        if custom_output_folder:
            out_dir = Path(custom_output_folder)
        else:
            first_parent = Path(files[0]["file_path"]).parent if files else BASE_DIR
            out_dir = first_parent / "KHBD_DaTichHop_NLS"
        out_dir.mkdir(parents=True, exist_ok=True)
    else:
        out_dir = None

    results = []
    stats = {
        "total": len(files),
        "already_integrated": 0,
        "integrated": 0,
        "need_review": 0,
        "error": 0
    }

    for item in files:
        src_path = item.get("file_path")
        if not src_path or not os.path.exists(src_path):
            results.append({
                "file_path": src_path,
                "filename": item.get("filename", ""),
                "status": "error",
                "message": "File không tồn tại"
            })
            stats["error"] += 1
            continue

        try:
            sub = item.get("subject") or cfg.get("subject", "Tin học")
            grd = item.get("grade") or cfg.get("grade", "9")
            title = item.get("lesson_title") or item.get("bai_name") or ""

            if only_audit:
                res = nls_engine.audit_khbd_nls(src_path, subject=sub, grade=grd, lesson_title=title)
            else:
                if output_mode == "new_folder":
                    dest_p = str(out_dir / os.path.basename(src_path))
                else:
                    dest_p = src_path
                res = nls_engine.integrate_khbd_nls(
                    file_path=src_path,
                    output_path=dest_p,
                    subject=sub,
                    grade=grd,
                    lesson_title=title,
                    highlight_red=highlight_red
                )

            st = res.get("status", "error")
            if st in stats:
                stats[st] += 1
            else:
                stats["error"] += 1

            results.append(res)
        except Exception as e:
            stats["error"] += 1
            results.append({
                "file_path": src_path,
                "filename": os.path.basename(src_path),
                "status": "error",
                "message": str(e)
            })

    return web.json_response({
        "success": True,
        "output_directory": str(out_dir) if out_dir else "inplace",
        "stats": stats,
        "results": results
    })

# --- KHGD (Kế Hoạch Giáo Dục Trường) Handlers ---
async def api_khgd_status(request):
    cache = khgd_engine.load_cached_khgd()
    available_files = []
    
    # Tìm các file KHGD tiềm năng trong thư mục gốc và thư mục KHGD
    scan_dirs = [BASE_DIR, khgd_engine.KHGD_DIR]
    for d in scan_dirs:
        if d.exists():
            for f in d.iterdir():
                if f.is_file() and f.suffix.lower() in [".doc", ".docx"] and not f.name.startswith("~$"):
                    f_low = f.name.lower()
                    if any(k in f_low for k in ["khgd", "kế hoạch", "ke hoach", "tổ cm", "to cm", "kh tổ"]):
                        available_files.append({
                            "filename": f.name,
                            "path": str(f),
                            "size_bytes": f.stat().st_size
                        })

    return web.json_response({
        "success": True,
        "has_cache": bool(cache),
        "cache": cache,
        "available_files": available_files
    })

async def api_khgd_parse(request):
    data = await safe_get_json(request)
    file_path = data.get("file_path")
    if not file_path:
        # Nếu không truyền đường dẫn, tự tìm file có sẵn trong thư mục
        for f in BASE_DIR.iterdir():
            if f.is_file() and "kh tổ cm" in f.name.lower() and f.suffix.lower() in [".doc", ".docx"]:
                file_path = str(f)
                break

    if not file_path or not os.path.exists(file_path):
        return web.json_response({"success": False, "error": "Chưa chọn file Kế hoạch giáo dục"}, status=400)

    try:
        result = khgd_engine.parse_khgd_document(file_path)
        return web.json_response({
            "success": True,
            "message": f"Đã phân tích thành công Kế hoạch giáo dục từ file: {os.path.basename(file_path)}",
            "data": result
        })
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_khgd_upload(request):
    reader = await request.multipart()
    saved_files = []

    while True:
        part = await reader.next()
        if part is None:
            break
        if part.filename:
            fn = part.filename
            if fn.lower().endswith(".doc") or fn.lower().endswith(".docx"):
                dest = khgd_engine.KHGD_DIR / fn
                with open(dest, "wb") as f:
                    while True:
                        chunk = await part.read_chunk()
                        if not chunk:
                            break
                        f.write(chunk)
                saved_files.append(str(dest))

    if not saved_files:
        return web.json_response({"success": False, "error": "Không có file .doc hoặc .docx hợp lệ"}, status=400)

    # Tự động parse file vừa upload
    try:
        result = khgd_engine.parse_khgd_document(saved_files[0])
        return web.json_response({
            "success": True,
            "message": f"Đã tải lên và phân tích thành công {os.path.basename(saved_files[0])}!",
            "data": result
        })
    except Exception as e:
        return web.json_response({"success": False, "error": f"Lỗi phân tích file: {str(e)}"}, status=500)


# ==========================================
# SMAS & TKB API HANDLERS
# ==========================================

async def api_smas_get_config(request):
    try:
        cfg = smas_engine.get_smas_config()
        return web.json_response({"success": True, "config": cfg})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_save_config(request):
    try:
        data = await safe_get_json(request)
        smas_engine.save_smas_config(data)
        return web.json_response({"success": True, "message": "Đã lưu cấu hình SMAS!", "config": data})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_sync_token(request):
    try:
        data = await safe_get_json(request)
        token = data.get("token") or smas_engine.get_smas_config().get("bearerToken", "")
        if not token:
            return web.json_response({"success": False, "error": "Chưa có Bearer Token!"}, status=400)
        res = smas_engine.sync_token_to_system(token)
        return web.json_response(res)
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_check_token(request):
    try:
        data = await safe_get_json(request)
        token = data.get("token")
        res = smas_engine.check_smas_token(token)
        return web.json_response(res)
    except Exception as e:
        return web.json_response({"valid": False, "message": str(e)}, status=500)

async def api_smas_get_schedule(request):
    try:
        slots = smas_engine.load_schedule()
        return web.json_response({"success": True, "slots": slots, "count": len(slots)})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_save_schedule(request):
    try:
        slots = await safe_get_json(request)
        if isinstance(slots, dict) and "slots" in slots:
            slots = slots["slots"]
        smas_engine.save_schedule(slots)
        return web.json_response({"success": True, "message": f"Đã lưu {len(slots)} tiết thời khóa biểu!"})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_reset_schedule(request):
    try:
        slots = smas_engine.reset_schedule()
        return web.json_response({"success": True, "message": "Đã khôi phục TKB mặc định!", "slots": slots})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_import_schedule_excel(request):
    try:
        content_type = request.headers.get("Content-Type", "")
        file_bytes = None
        teacher_name = None
        file_path = None

        if "multipart/form-data" in content_type:
            reader = await request.multipart()
            while True:
                part = await reader.next()
                if part is None:
                    break
                if part.name == "teacherName":
                    teacher_name = (await part.text()).strip()
                elif part.name in ["file", "excelFile"]:
                    fn = part.filename or "upload_tkb.xls"
                    buf = bytearray()
                    while True:
                        chunk = await part.read_chunk()
                        if not chunk:
                            break
                        buf.extend(chunk)
                    file_bytes = bytes(buf)
                    dest = BASE_DIR / fn
                    try:
                        with open(dest, "wb") as f:
                            f.write(file_bytes)
                    except Exception:
                        pass
        else:
            data = await safe_get_json(request)
            teacher_name = data.get("teacherName")
            fp = data.get("filePath")
            if fp:
                target_p = BASE_DIR / fp if not os.path.isabs(fp) else Path(fp)
                if target_p.exists():
                    file_path = str(target_p)
                else:
                    return web.json_response({"success": False, "error": f"Không tìm thấy file: {fp}"}, status=400)
            else:
                def_tkb = BASE_DIR / "thơi khóa biểu 1.xls"
                if def_tkb.exists():
                    file_path = str(def_tkb)
                else:
                    return web.json_response({"success": False, "error": "Chưa chọn file TKB Excel để nhập!"}, status=400)

        source = file_bytes if file_bytes is not None else file_path
        res = smas_engine.parse_tkb_excel(source, teacher_name=teacher_name, save_to_schedule=True)
        return web.json_response(res)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return web.json_response({"success": False, "error": f"Lỗi đọc file Excel TKB: {str(e)}"}, status=500)

async def api_smas_get_ppct_db(request):
    try:
        ppct_db = smas_engine.load_smas_ppct()
        return web.json_response({"success": True, "ppct": ppct_db, "count": len(ppct_db)})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_refresh_ppct(request):
    try:
        data = await safe_get_json(request)
        token = data.get("token")
        res = smas_engine.refresh_ppct_from_smas(token)
        return web.json_response({"success": True, "data": res, "message": f"Đã cập nhật PPCT từ SMAS cho {res.get('updatedClasses', 0)} môn/lớp!"})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_generate_payloads(request):
    try:
        data = await safe_get_json(request)
        start_week = int(data.get("startWeek", 1))
        end_week = int(data.get("endWeek", 1))
        start_date = data.get("startDate", "2026-09-07")
        offsets = data.get("startPeriodOffset", {})
        weeks = smas_engine.generate_weekly_payloads(start_week, end_week, start_date, offsets)
        return web.json_response({"success": True, "totalWeeks": len(weeks), "weeks": weeks})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_sync(request):
    try:
        data = await safe_get_json(request)
        weeks = data.get("weeks", [])
        token = data.get("bearerToken")
        level = data.get("level", "all")
        if not weeks:
            return web.json_response({"success": False, "error": "Chưa có danh sách tuần cần đồng bộ!"}, status=400)
        res = smas_engine.sync_smas_weeks(weeks, token, level)
        return web.json_response({"success": True, "results": res})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_get_classes(request):
    try:
        cls_data = smas_engine.read_json_file(smas_engine.ALL_CLASSES_PATH, [])
        return web.json_response({"success": True, "classes": cls_data})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_get_exact_date(request):
    try:
        data = await safe_get_json(request)
        c_name = data.get("className", "")
        week = int(data.get("week", 1))
        fmt = data.get("dateFormat", "smas_exact")
        d_str = smas_engine.get_exact_teaching_date_from_tkb(c_name, week, date_format=fmt)
        return web.json_response({"success": True, "date": d_str})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_get_subjects(request):
    try:
        subs = smas_engine.get_all_smas_subjects()
        return web.json_response({"success": True, "subjects": subs, "count": len(subs)})
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)

async def api_smas_fetch_subject_ppct(request):
    try:
        data = await safe_get_json(request)
        sub = data.get("subject", "Tin học")
        grade = str(data.get("grade", "9"))
        c_name = data.get("className")
        token = data.get("token")
        res = smas_engine.fetch_smas_ppct_on_demand(grade, subject=sub, class_name=c_name, token=token)
        if res:
            return web.json_response({
                "success": True,
                "message": f"Đã tải thành công PPCT môn {res.get('subjectName')} lớp {res.get('className')} từ SMAS ({res.get('totalCount')} tiết)!",
                "data": res
            })
        else:
            return web.json_response({"success": False, "error": f"Không thể tải PPCT môn {sub} lớp {grade} từ SMAS."}, status=400)
    except Exception as e:
        return web.json_response({"success": False, "error": str(e)}, status=500)


@web.middleware
async def no_cache_middleware(request, handler):
    response = await handler(request)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

def make_app():
    app = web.Application(middlewares=[no_cache_middleware])
    app.router.add_get("/", index_handler)
    app.router.add_static("/static", path=str(WEB_DIR), name="static")

    # API endpoints
    app.router.add_get("/api/config", api_get_config)
    app.router.add_post("/api/config", api_save_config)
    app.router.add_get("/api/ppct/files", api_get_ppct_files)
    app.router.add_get("/api/ppct/data", api_get_ppct_data)
    app.router.add_post("/api/ppct/update_dates", api_update_ppct_dates)
    app.router.add_post("/api/scan", api_scan_folder)
    app.router.add_post("/api/recalc_filenames", api_recalc_filenames)
    app.router.add_post("/api/preview_diff", api_preview_diff)
    app.router.add_post("/api/process_batch", api_process_batch)
    app.router.add_post("/api/fast_rename", api_fast_rename)
    app.router.add_post("/api/open_folder", api_open_folder)
    app.router.add_get("/api/ai/status", api_ai_status)
    app.router.add_post("/api/ai/test_connection", api_ai_test_connection)
    app.router.add_post("/api/ai/analyze", api_ai_analyze)
    app.router.add_post("/api/ai/analyze_title", api_ai_analyze_title)
    app.router.add_post("/api/ai/batch_analyze_titles", api_ai_batch_analyze_titles)

    # NLS endpoints
    app.router.add_post("/api/nls/audit", api_nls_audit)
    app.router.add_post("/api/nls/integrate", api_nls_integrate)
    app.router.add_post("/api/nls/batch_integrate", api_nls_batch_integrate)

    # KHGD endpoints
    app.router.add_get("/api/khgd/status", api_khgd_status)
    app.router.add_post("/api/khgd/parse", api_khgd_parse)
    app.router.add_post("/api/khgd/upload", api_khgd_upload)

    
    # SMAS & TKB endpoints
    app.router.add_get("/api/smas/config", api_smas_get_config)
    app.router.add_post("/api/smas/config", api_smas_save_config)
    app.router.add_post("/api/smas/token-sync", api_smas_sync_token)
    app.router.add_post("/api/smas/check-token", api_smas_check_token)
    app.router.add_get("/api/smas/schedule", api_smas_get_schedule)
    app.router.add_post("/api/smas/schedule", api_smas_save_schedule)
    app.router.add_post("/api/smas/schedule/reset", api_smas_reset_schedule)
    app.router.add_post("/api/smas/schedule/import-excel", api_smas_import_schedule_excel)
    app.router.add_get("/api/smas/ppct-db", api_smas_get_ppct_db)
    app.router.add_post("/api/smas/refresh-ppct", api_smas_refresh_ppct)
    app.router.add_post("/api/smas/generate-payloads", api_smas_generate_payloads)
    app.router.add_post("/api/smas/sync", api_smas_sync)
    app.router.add_get("/api/smas/classes", api_smas_get_classes)
    app.router.add_get("/api/smas/subjects", api_smas_get_subjects)
    app.router.add_post("/api/smas/fetch-subject-ppct", api_smas_fetch_subject_ppct)
    app.router.add_post("/api/smas/get-exact-date", api_smas_get_exact_date)

    return app

if __name__ == "__main__":
    port = 8765
    print(f"Starting KHBD Pro Server on http://localhost:{port} ...")
    app = make_app()
    try:
        web.run_app(app, host="127.0.0.1", port=port, reuse_address=True)
    except OSError:
        port = 8766
        print(f"Port 8765 busy, using http://localhost:{port} ...")
        web.run_app(app, host="127.0.0.1", port=port, reuse_address=True)
