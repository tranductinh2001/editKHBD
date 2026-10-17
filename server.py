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
    save_config(cfg)
    return web.json_response({"success": True, "config": cfg})

async def api_get_ppct_files(request):
    ppct_dict = khbd_engine.load_all_ppct(str(PPCT_DIR))
    file_list = []
    for fn, info in ppct_dict.items():
        file_list.append({
            "filename": fn,
            "title": info.get("title", fn),
            "type": info.get("type", "standard_ppct"),
            "item_count": len(info.get("items", [])) if "items" in info else len(info.get("columns", {}))
        })
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
    if "subject" in data:
        cfg["subject"] = data["subject"]
    if "classes" in data:
        cfg["classes"] = data["classes"]

    # Load PPCT items
    ppct_dict = khbd_engine.load_all_ppct(str(PPCT_DIR))
    ppct_data = ppct_dict.get(ppct_filename, {})
    ppct_items = ppct_data.get("items", [])

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
                    matched_ppct = khbd_engine.match_lesson_with_ppct(lesson_info, ppct_items)
                    target_fn = khbd_engine.generate_target_filename(lesson_info, matched_ppct, cfg)

                    # Compute effective teaching_date for this scanned lesson
                    teaching_date = ""
                    if matched_ppct and matched_ppct.get("ngay_day"):
                        teaching_date = matched_ppct["ngay_day"]
                    elif cfg.get("auto_calc_teaching_date", True):
                        week_val = (matched_ppct.get("tuan") if matched_ppct else None) or lesson_info.get("week") or lesson_info.get("tuan")
                        if week_val is not None and str(week_val).strip():
                            start_date = cfg.get("school_year_start_date", "2026-09-07")
                            date_fmt = cfg.get("teaching_date_format", "d2_to_d6")
                            teaching_date = khbd_engine.calculate_week_dates(week_val, start_date, date_fmt)

                    files.append({
                        "file_path": full_path,
                        "filename": entry.name,
                        "lesson_info": lesson_info,
                        "matched_ppct": matched_ppct,
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
    ppct_filename = data.get("ppct_file", cfg.get("ppct_file", "_Lop_9.xlsx"))
    ppct_items = ppct_dict.get(ppct_filename, {}).get("items", [])
    matched_ppct = khbd_engine.match_lesson_with_ppct(lesson_info, ppct_items)

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
    week = data.get("week") or (matched_ppct.get("tuan") if matched_ppct else "1")
    periods = data.get("periods") or lesson_info.get("tiet_str") or (str(matched_ppct.get("tiet")) if matched_ppct else "1, 2")

    # Teaching date calculation
    if data.get("teaching_date") and data.get("teaching_date") != "../../2026":
        teaching_date = data["teaching_date"]
    elif matched_ppct and matched_ppct.get("ngay_day"):
        teaching_date = matched_ppct["ngay_day"]
    elif cfg.get("auto_calc_teaching_date", True):
        start_date = cfg.get("school_year_start_date", "2026-09-07")
        date_fmt = cfg.get("teaching_date_format", "d2_to_d6")
        teaching_date = khbd_engine.calculate_week_dates(week, start_date, date_fmt)
    else:
        teaching_date = cfg.get("teaching_date", "../../2026")

    # Format Title
    prefix = cfg.get("title_prefix", "TÊN BÀI DẠY: ")
    if cfg.get("title_prefix_ten_bai_day", True):
        if bai_num and not f"bài {bai_num}".lower() in bai_name.lower():
            bai_title_full = f"{prefix}BÀI {bai_num}. {bai_name.upper()}"
        else:
            bai_title_full = f"{prefix}{bai_name.upper()}"
    else:
        bai_title_full = f"BÀI {bai_num}: {bai_name.upper()}" if bai_num else bai_name.upper()

    signer_school = (cfg.get("signer_school") or "").strip()
    signer_dept = (cfg.get("signer_dept") or "").strip()
    if signer_school or signer_dept:
        approval_view = {
            "col_left": {
                "title": "Duyệt của Chuyên môn",
                "note": "(Ký và ghi rõ họ tên)",
                "signer_name": signer_school
            },
            "col_right": {
                "title": "Duyệt của tổ chuyên môn",
                "note": "(Ký và ghi rõ họ tên)",
                "signer_name": signer_dept
            }
        }
    else:
        approval_view = "Duyệt của Chuyên môn\t\t\t\t        Duyệt của tổ chuyên môn"

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
    ppct_filename = cfg.get("ppct_file", "_Lop_9.xlsx")
    ppct_items = ppct_dict.get(ppct_filename, {}).get("items", [])

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
            matched_ppct = item.get("matched_ppct") or khbd_engine.match_lesson_with_ppct(lesson_info, ppct_items)

            # Target filename
            target_fn = item.get("target_filename") or khbd_engine.generate_target_filename(lesson_info, matched_ppct, cfg)

            # File-specific overrides if provided in request item
            file_cfg = dict(cfg)
            if item.get("chude"):
                file_cfg["chude"] = item["chude"]
            if item.get("bai_num"):
                file_cfg["bai_num"] = item["bai_num"]
            if item.get("bai_name"):
                file_cfg["bai_name"] = item["bai_name"]
            if item.get("week"):
                file_cfg["week"] = item["week"]
            if item.get("periods"):
                file_cfg["periods"] = item["periods"]
            if item.get("teaching_date"):
                file_cfg["teaching_date"] = item["teaching_date"]
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

            success_count += 1
            results.append({
                "original_file": os.path.basename(src_path),
                "new_file": target_fn,
                "output_path": dest_path,
                "status": "success",
                "message": "Đã sửa chuẩn mẫu & đổi tên thành công"
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

async def api_ai_analyze(request):
    data = await safe_get_json(request)
    file_path = data.get("file_path")
    if not file_path or not os.path.exists(file_path):
        return web.json_response({"success": False, "error": "File không tồn tại hoặc chưa được chọn"}, status=400)
    try:
        cfg = load_config()
        ai_cfg = cfg.get("ai_config", {})
        api_key = ai_cfg.get("api_key") or os.environ.get("BEE_API_KEY")
        model = ai_cfg.get("model") or "gemini-2.5-flash-lite"
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
        "model": ai_cfg.get("model", "gemini-2.5-flash-lite"),
        "has_key": bool(ai_cfg.get("api_key"))
    })

async def api_ai_test_connection(request):
    data = await safe_get_json(request)
    cfg = load_config()
    ai_cfg = cfg.get("ai_config", {})
    api_key = data.get("api_key") or ai_cfg.get("api_key") or os.environ.get("BEE_API_KEY")
    model = data.get("model") or ai_cfg.get("model") or "gemini-2.5-flash-lite"
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
    api_key = data.get("api_key") or ai_cfg.get("api_key") or os.environ.get("BEE_API_KEY")
    model = data.get("model") or ai_cfg.get("model") or "gemini-2.5-flash-lite"

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
    api_key = data.get("api_key") or ai_cfg.get("api_key") or os.environ.get("BEE_API_KEY")
    model = data.get("model") or ai_cfg.get("model") or "gemini-2.5-flash-lite"

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

def make_app():
    app = web.Application()
    app.router.add_get("/", index_handler)
    app.router.add_static("/static", path=str(WEB_DIR), name="static")

    # API endpoints
    app.router.add_get("/api/config", api_get_config)
    app.router.add_post("/api/config", api_save_config)
    app.router.add_get("/api/ppct/files", api_get_ppct_files)
    app.router.add_get("/api/ppct/data", api_get_ppct_data)
    app.router.add_post("/api/ppct/update_dates", api_update_ppct_dates)
    app.router.add_post("/api/scan", api_scan_folder)
    app.router.add_post("/api/preview_diff", api_preview_diff)
    app.router.add_post("/api/process_batch", api_process_batch)
    app.router.add_post("/api/open_folder", api_open_folder)
    app.router.add_get("/api/ai/status", api_ai_status)
    app.router.add_post("/api/ai/test_connection", api_ai_test_connection)
    app.router.add_post("/api/ai/analyze", api_ai_analyze)
    app.router.add_post("/api/ai/analyze_title", api_ai_analyze_title)
    app.router.add_post("/api/ai/batch_analyze_titles", api_ai_batch_analyze_titles)

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
