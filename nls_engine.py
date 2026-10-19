# -*- coding: utf-8 -*-
"""
NLS Engine - Module Kiem tra, De xuat va Tu dong Tich hop Nang Luc So (NLS) vao KHBD
Tuan thu:
- Thong tu 02/2025/TT-BGDĐT ve Khung nang luc so cho nguoi hoc
- Cong van 3456/BGDĐT-GDPT va phu luc huong dan trien khai Khung NLS
- Cong van 5512/BGDĐT-GDTrH ve cau truc KHBD
- Chuong trinh GDPT 2018
"""

import os
import re
import json
import copy
from pathlib import Path
import docx
from docx.shared import Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph

import beeknoee_client

# Mau mau do dung de danh dau phan noi dung moi/chinh sua
COLOR_RED = RGBColor(255, 0, 0)

# Khung tham chieu Nang luc so chuan cho THCS (Tieu chuan 2 - TC2)
OFFICIAL_NLS_FRAMEWORK_THCS = {
    "1. Vận hành thiết bị và phần mềm": {
        "1.1.TC2a": "Xác định các thiết bị phần cứng, phần mềm và dịch vụ số cần thiết để thực hiện nhiệm vụ học tập.",
        "1.1.TC2b": "Vận hành thành thạo các thiết bị số thông dụng và khắc phục được các sự cố kỹ thuật đơn giản.",
        "1.2.TC2a": "Sử dụng các phần mềm chuyên dụng hoặc công cụ số phù hợp để thu thập, xử lý dữ liệu và hoàn thành nhiệm vụ.",
        "1.2.TC2b": "Cài đặt, cập nhật hoặc tùy biến các ứng dụng học tập số an toàn và đúng mục đích.",
    },
    "2. Thông tin và dữ liệu": {
        "2.1.TC2a": "Xác định nhu cầu thông tin, xây dựng từ khóa và áp dụng các chiến lược tìm kiếm thông tin hiệu quả trên Internet.",
        "2.2.TC2a": "Lựa chọn, lưu trữ và tổ chức dữ liệu số một cách khoa học trong các thư mục hoặc dịch vụ lưu trữ đám mây.",
        "2.3.TC2a": "Đánh giá độ tin cậy, tính mới, tính chính xác và tính xác thực của thông tin, dữ liệu từ các nguồn số khác nhau.",
        "2.3.TC2b": "Hiểu rõ tác động của công nghệ để tham gia vào các hoạt động học tập, trao đổi trên môi trường số có trách nhiệm.",
    },
    "3. Giao tiếp và hợp tác trong môi trường số": {
        "3.1.TC2a": "Sử dụng các công cụ truyền thông số (email, tin nhắn, diễn đàn học tập, nhóm trực tuyến) để trao đổi thông tin phù hợp.",
        "3.2.TC2a": "Chia sẻ dữ liệu và học liệu số với bạn học và giáo viên bằng các phương tiện số thích hợp.",
        "3.3.TC2a": "Hợp tác làm việc nhóm thông qua các công cụ trực tuyến để cùng hoàn thành sản phẩm học tập số.",
        "3.4.TC2a": "Tuân thủ các quy tắc ứng xử, lịch sự và văn hóa trong môi trường mạng (Netiquette).",
    },
    "4. Sáng tạo nội dung số": {
        "4.1.TC2a": "Tạo mới hoặc chỉnh sửa các nội dung số ở nhiều định dạng (văn bản, bài trình chiếu, sơ đồ tư duy số, video clip, đồ họa).",
        "4.2.TC2a": "Biết cách tích hợp, tái cấu trúc và kết hợp các học liệu số hiện có một cách sáng tạo và hợp pháp.",
        "4.3.TC2a": "Hiểu và tuân thủ các quy định về bản quyền số, sở hữu trí tuệ và trích dẫn nguồn học liệu hợp lệ.",
        "4.4.TC2a": "Áp dụng tư duy lập trình, thuật toán hoặc tự động hóa đơn giản để giải quyết vấn đề.",
    },
    "5. An toàn và an ninh số": {
        "5.1.TC2a": "Bảo vệ thiết bị số cá nhân khỏi mã độc và các nguy cơ mất an toàn thông tin cơ bản.",
        "5.2.TC2a": "Bảo vệ thông tin cá nhân và dữ liệu riêng tư trên môi trường số; nhận diện hành vi lừa đảo trực tuyến.",
        "5.3.TC2a": "Bảo vệ sức khỏe thể chất và tinh thần khi sử dụng thiết bị số (tư thế ngồi, thời gian sử dụng, phòng tránh bắt nạt mạng).",
        "5.4.TC2c": "Nhận thức được sự tác động và thay đổi của thế giới số xung quanh, từ đó chủ động cập nhật kiến thức, kỹ năng để thích ứng.",
    },
    "6. Giải quyết vấn đề trong môi trường số": {
        "6.1.TC2a": "Nhận diện các thiết bị thông minh và tính năng tự động hóa như những biểu hiện ban đầu của trí tuệ nhân tạo (AI) trong đời sống.",
        "6.2.TC2a": "Sử dụng công nghệ số và công cụ tìm kiếm để hỗ trợ giải quyết các nhiệm vụ học tập thực tiễn.",
        "6.3.TC2a": "Nhận biết các khoảng trống về năng lực số của bản thân và chủ động tìm kiếm các cơ hội nâng cao kỹ năng số.",
    }
}


def set_cell_border_simple(cell):
    """Thiết lập viền mảnh cho cell bảng Word"""
    tcPr = cell._tc.get_or_add_tcPr()
    tcBorders = tcPr.first_child_found_in("w:tcBorders")
    if tcBorders is None:
        tcBorders = OxmlElement('w:tcBorders')
        tcPr.append(tcBorders)
    for edge in ('top', 'left', 'bottom', 'right'):
        el = tcBorders.find(qn(f'w:{edge}'))
        if el is None:
            el = OxmlElement(f'w:{edge}')
            tcBorders.append(el)
        el.set(qn('w:val'), 'single')
        el.set(qn('w:sz'), '4')
        el.set(qn('w:space'), '0')
        el.set(qn('w:color'), 'auto')


def extract_khbd_core_content(doc):
    """
    Trích xuất nội dung cốt lõi của giáo án để gửi AI:
    - Đoạn mở đầu, Mục tiêu (I. Mục tiêu)
    - Thiết bị dạy học (II. Thiết bị)
    - Tên và mục tiêu các hoạt động dạy học (III. Tiến trình)
    Giới hạn độ dài để AI xử lý nhanh nhất và chính xác nhất.
    """
    lines = []
    in_activities = False
    act_count = 0

    for p in doc.paragraphs:
        t = p.text.strip()
        if not t:
            continue
        t_low = t.lower()
        if "iii. tiến trình" in t_low:
            in_activities = True
            lines.append(f"\n{t}")
            continue

        if not in_activities:
            lines.append(t)
        else:
            # Trong tiến trình dạy học, lấy tiêu đề hoạt động, mục tiêu, nội dung
            if any(t_low.startswith(x) for x in ["hoạt động", "1.", "2.", "3.", "4.", "a)", "b)", "c)"]):
                lines.append(t)
                act_count += 1
                if act_count > 30:
                    break

    # Trích xuất thêm tiêu đề các bảng nếu có
    for t_idx, table in enumerate(doc.tables):
        if table.rows:
            hdr = " | ".join([c.text.strip().replace("\n", " ") for c in table.rows[0].cells if c.text.strip()])
            if hdr:
                lines.append(f"[Bảng {t_idx+1}]: {hdr}")

    return "\n".join(lines)


def detect_existing_nls(doc):
    """
    Kiểm tra toàn diện xem tài liệu Word đã có NLS hay chưa:
    - Quét cả Paragraphs và Tables
    - Tìm mục '2.3' hoặc 'Các NLS được phát triển'
    - Tìm 'Bảng Phân tích Phát triển NLS cho Học sinh'
    - Tìm các mã NLS chuẩn: X.Y.TC2z
    """
    found_codes = set()
    has_nls_heading = False
    has_nls_table = False

    # 1. Quét Paragraphs
    for p in doc.paragraphs:
        t = p.text.strip()
        t_low = t.lower()
        if "2.3" in t_low and ("nls" in t_low or "năng lực số" in t_low):
            has_nls_heading = True
        if "bảng phân tích phát triển nls" in t_low:
            has_nls_table = True
        
        codes = re.findall(r'\b\d\.\d\.TC[123][a-z]\b', t, re.IGNORECASE)
        for c in codes:
            found_codes.add(c)

    # 2. Quét Tables
    for t in doc.tables:
        for row in t.rows:
            for cell in row.cells:
                ct = cell.text.strip()
                if "năng lực số" in ct.lower() and ("tt" in ct.lower() or "hoạt động" in ct.lower()):
                    has_nls_table = True
                codes = re.findall(r'\b\d\.\d\.TC[123][a-z]\b', ct, re.IGNORECASE)
                for c in codes:
                    found_codes.add(c)

    codes_list = sorted(list(found_codes))
    is_fully_integrated = (has_nls_heading and len(codes_list) >= 2) or (has_nls_table and len(codes_list) >= 2)
    is_partially_integrated = bool(has_nls_heading or has_nls_table or len(codes_list) > 0) and not is_fully_integrated

    return {
        "has_nls_heading": has_nls_heading,
        "has_nls_table": has_nls_table,
        "found_codes": codes_list,
        "is_fully_integrated": is_fully_integrated,
        "is_partially_integrated": is_partially_integrated
    }


def analyze_and_plan_nls(core_text, filename="", subject="Tin học", grade="9", lesson_title="", client=None):
    """
    Gửi nội dung KHBD qua API PicOne / Beeknoee để AI phân tích chuyên sâu và lập kế hoạch tích hợp NLS.
    """
    if client is None:
        cfg = {}
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
        except Exception:
            pass
        ai_cfg = cfg.get("ai_config", {})
        client = beeknoee_client.BeeknoeeClient(
            api_key=ai_cfg.get("api_key"),
            model=ai_cfg.get("model") or "gemini-3.1-flash-lite",
            base_url=ai_cfg.get("base_url")
        )

    framework_summary = json.dumps(OFFICIAL_NLS_FRAMEWORK_THCS, ensure_ascii=False, indent=2)

    system_prompt = (
        "Bạn là Chuyên gia Thẩm định Sư phạm của Bộ GD&ĐT Việt Nam, am hiểu sâu sắc:\n"
        "- Thông tư 02/2025/TT-BGDĐT về Khung năng lực số cho người học.\n"
        "- Công văn 3456/BGDĐT-GDPT và phụ lục hướng dẫn triển khai NLS cho học sinh phổ thông.\n"
        "- Công văn 5512/BGDĐT-GDTrH về xây dựng và tổ chức Kế hoạch bài dạy (KHBD).\n\n"
        "Quy tắc tối thượng:\n"
        "1. KHÔNG tự bịa mã NLS. Chỉ sử dụng đúng mã và mô tả chuẩn trong danh mục chính thức được cung cấp.\n"
        "2. Cấp THCS bắt buộc sử dụng tiêu chuẩn TC2 (ví dụ: 1.1.TC2a, 5.4.TC2c, 6.1.TC2a,...).\n"
        "3. Nếu bài học ĐÃ CÓ NLS đầy đủ, giữ nguyên (status: 'already_integrated').\n"
        "4. Nếu chưa có, đề xuất 2-3 mã NLS phù hợp nhất với bài học cùng Bảng Phân tích NLS.\n"
        "5. Chỉ trả về DUY NHẤT một khối JSON hợp lệ theo đúng schema quy định, không kèm văn bản giải thích bên ngoài."
    )

    prompt = f"""Hãy phân tích nội dung Kế hoạch bài dạy (KHBD) dưới đây và xây dựng kế hoạch tích hợp Năng lực số (NLS) chính xác:

Tên file: {filename}
Môn học: {subject}
Khối lớp: {grade} (Cấp THCS - Áp dụng tiêu chuẩn TC2)
Tên bài: {lesson_title}

### KHUNG MÃ NĂNG LỰC SỐ THCS (THÔNG TƯ 02/2025/TT-BGDĐT & CV 3456/BGDĐT-GDPT):
{framework_summary}

### NỘI DUNG CỐT LÕI KHBD CẦN THẨM ĐỊNH:
{core_text[:4000]}

### YÊU CẦU:
Trả về DUY NHẤT một khối JSON hợp lệ theo cấu trúc sau:
{{
  "status": "not_integrated",
  "reason": "Bài học cần tích hợp Năng lực số về nhận diện thiết bị thông minh và thích ứng công nghệ...",
  "detected_codes": [],
  "should_modify": true,
  "nls_objectives": [
    {{
      "code": "6.1.TC2a",
      "text": "6.1.TC2a: HS nhận diện được các thiết bị thông minh (ô tô tự lái, robot) có khả năng xử lý thông tin tự động là những biểu hiện ban đầu của trí tuệ nhân tạo (AI) trong đời sống."
    }},
    {{
      "code": "5.4.TC2c",
      "text": "5.4.TC2c: HS nhận biết được sự thay đổi của thế giới xung quanh nhờ công nghệ số, từ đó xác định nhu cầu phải cập nhật kiến thức và kỹ năng mới để thích nghi."
    }}
  ],
  "device_addition": "Máy tính, máy chiếu, bài trình chiếu điện tử, phiếu học tập số.",
  "nls_table_rows": [
    {{
      "tt": "1",
      "ten_hoat_dong": "Hình thành kiến thức: Tìm hiểu thế giới kĩ thuật số",
      "to_chuc_day_hoc": "GV giao nhiệm vụ cho HS quan sát hình ảnh thiết bị thông minh, thảo luận nhóm để xác định thông tin đầu vào, đầu ra và cơ chế xử lý tự động.",
      "nang_luc_so": "6.1.TC2a: HS nhận diện được các thiết bị thông minh có bộ xử lý tự động."
    }},
    {{
      "tt": "2",
      "ten_hoat_dong": "Vận dụng",
      "to_chuc_day_hoc": "GV giao nhiệm vụ cho HS tìm hiểu thiết bị đeo thông minh (Smartwatch) và chia sẻ cách sử dụng thiết bị an toàn, hiệu quả trong cuộc sống.",
      "nang_luc_so": "5.4.TC2c: HS thể hiện sự thích nghi với công nghệ mới thông qua tìm hiểu thiết bị thông minh."
    }}
  ]
}}
"""

    raw_response = client.chat(prompt, system_prompt=system_prompt, temperature=0.1, max_tokens=2500)
    clean = re.sub(r"^```json\s*", "", raw_response.strip(), flags=re.MULTILINE)
    clean = re.sub(r"^```\s*", "", clean, flags=re.MULTILINE).strip()
    
    m = re.search(r"\{.*\}", clean, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception as e:
            print("Lỗi parse JSON NLS plan:", e)
    
    return {
        "status": "error",
        "reason": f"Không thể phân tích phản hồi JSON từ AI: {raw_response[:200]}",
        "should_modify": False,
        "nls_objectives": [],
        "nls_table_rows": []
    }


def apply_nls_to_docx(input_path, output_path, nls_plan, highlight_red=True):
    """
    Áp dụng kế hoạch NLS vào file Word:
    1. Giữ nguyên cấu trúc, căn lề, font chữ (Times New Roman), cỡ chữ (13/14pt), header/footer.
    2. Bổ sung mục '2.3. Các NLS được phát triển:' vào dưới phần '2. Về năng lực:'.
    3. Bổ sung thiết bị/học liệu nếu có.
    4. Bổ sung 'Bảng Phân tích Phát triển NLS cho Học sinh' ở cuối hoặc sau tiến trình dạy học.
    5. ĐẶC BIỆT: Tô đỏ (RGBColor(255, 0, 0)) cho TẤT CẢ các chữ mới được chèn vào (nếu highlight_red=True).
    6. Bảo toàn các đoạn văn bản gốc không bị ảnh hưởng.
    """
    doc = docx.Document(input_path)

    # 1. Bổ sung mục tiêu NLS
    nls_objectives = nls_plan.get("nls_objectives", [])
    if nls_objectives:
        existing_23_idx = -1
        for idx, p in enumerate(doc.paragraphs):
            p_text = p.text.strip().lower()
            if "2.3. các nls" in p_text or "2.3. năng lực số" in p_text or "2.3. các năng lực số" in p_text:
                existing_23_idx = idx
                break

        if existing_23_idx == -1:
            # Tìm vị trí sau mục "2. Về năng lực:" hoặc trước mục "3. Về phẩm chất:"
            insert_before_idx = -1
            for idx, p in enumerate(doc.paragraphs):
                p_text = p.text.strip().lower()
                if "3. về phẩm chất" in p_text or "3. phẩm chất" in p_text:
                    insert_before_idx = idx
                    break

            if insert_before_idx == -1:
                for idx, p in enumerate(doc.paragraphs):
                    p_text = p.text.strip().lower()
                    if "ii. thiết bị" in p_text:
                        insert_before_idx = idx
                        break

            if insert_before_idx != -1:
                ref_para = doc.paragraphs[insert_before_idx]

                # Tiêu đề mục 2.3
                p_title = ref_para.insert_paragraph_before()
                p_title.paragraph_format.line_spacing = 1.15
                p_title.paragraph_format.space_before = Pt(3)
                p_title.paragraph_format.space_after = Pt(2)
                run_title = p_title.add_run("2.3. Các NLS được phát triển:")
                run_title.font.name = "Times New Roman"
                run_title.font.size = Pt(13)
                run_title.font.bold = True
                if highlight_red:
                    run_title.font.color.rgb = COLOR_RED

                # Các gạch đầu dòng mục tiêu NLS
                for item in nls_objectives:
                    obj_text = item.get("text") or item.get("code", "")
                    p_item = ref_para.insert_paragraph_before()
                    p_item.paragraph_format.line_spacing = 1.15
                    p_item.paragraph_format.space_before = Pt(1)
                    p_item.paragraph_format.space_after = Pt(2)
                    run_item = p_item.add_run(f"- {obj_text}")
                    run_item.font.name = "Times New Roman"
                    run_item.font.size = Pt(13)
                    run_item.font.bold = False
                    if highlight_red:
                        run_item.font.color.rgb = COLOR_RED

    # 2. Bổ sung Thiết bị dạy học số nếu được yêu cầu
    dev_addition = nls_plan.get("device_addition", "").strip()
    if dev_addition:
        for idx, p in enumerate(doc.paragraphs):
            p_text = p.text.strip().lower()
            if "1. thiết bị dạy học" in p_text or "thiết bị dạy học:" in p_text:
                if dev_addition.lower() not in p.text.lower():
                    run_add = p.add_run(f", {dev_addition}")
                    run_add.font.name = "Times New Roman"
                    run_add.font.size = Pt(13)
                    if highlight_red:
                        run_add.font.color.rgb = COLOR_RED
                break

    # 3. Bổ sung Bảng Phân tích Phát triển NLS cho Học sinh
    nls_table_rows = nls_plan.get("nls_table_rows", [])
    if nls_table_rows:
        has_nls_table = False
        for t in doc.tables:
            header_texts = [c.text.strip().lower() for c in t.rows[0].cells] if t.rows else []
            if any("năng lực số" in h for h in header_texts) and any("hoạt động" in h for h in header_texts):
                has_nls_table = True
                break

        if not has_nls_table:
            p_tbl_title = doc.add_paragraph()
            p_tbl_title.paragraph_format.space_before = Pt(12)
            p_tbl_title.paragraph_format.space_after = Pt(4)
            p_tbl_title.paragraph_format.line_spacing = 1.15
            run_tbl_title = p_tbl_title.add_run("Bảng Phân tích Phát triển NLS cho Học sinh")
            run_tbl_title.font.name = "Times New Roman"
            run_tbl_title.font.size = Pt(13)
            run_tbl_title.font.bold = True
            if highlight_red:
                run_tbl_title.font.color.rgb = COLOR_RED

            # Bảng 4 cột chuẩn
            col_widths = [Pt(36), Pt(130), Pt(185), Pt(145)]
            tbl = doc.add_table(rows=1, cols=4)
            tbl.autofit = False

            headers = ["TT", "Tên hoạt động", "Tổ chức dạy học", "Năng lực số"]
            hdr_cells = tbl.rows[0].cells
            for c_idx, title in enumerate(headers):
                cell = hdr_cells[c_idx]
                cell.width = col_widths[c_idx]
                set_cell_border_simple(cell)
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.line_spacing = 1.15
                r = p.add_run(title)
                r.font.name = "Times New Roman"
                r.font.size = Pt(13)
                r.font.bold = True
                if highlight_red:
                    r.font.color.rgb = COLOR_RED

            for row_data in nls_table_rows:
                row_cells = tbl.add_row().cells
                vals = [
                    str(row_data.get("tt", "")),
                    str(row_data.get("ten_hoat_dong", "")),
                    str(row_data.get("to_chuc_day_hoc", "")),
                    str(row_data.get("nang_luc_so", ""))
                ]
                for c_idx, val in enumerate(vals):
                    cell = row_cells[c_idx]
                    cell.width = col_widths[c_idx]
                    set_cell_border_simple(cell)
                    p = cell.paragraphs[0]
                    p.paragraph_format.space_before = Pt(2)
                    p.paragraph_format.space_after = Pt(2)
                    p.paragraph_format.line_spacing = 1.15
                    if c_idx == 0:
                        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    else:
                        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                    r = p.add_run(val)
                    r.font.name = "Times New Roman"
                    r.font.size = Pt(12)
                    r.font.bold = (c_idx == 0)
                    if highlight_red:
                        r.font.color.rgb = COLOR_RED

            p_after = doc.add_paragraph()
            p_after.paragraph_format.space_before = Pt(14)
            p_after.paragraph_format.space_after = Pt(24)

            # Safeguard: If the document already contains an approval/signature block at the end,
            # relocate the NLS table BEFORE the signature block, leaving the signature block at the bottom
            approval_keywords = [
                "duyệt của", "ký và ghi rõ họ tên", "ký, ghi rõ họ tên",
                "người thực hiện", "giáo viên thực hiện", "người soạn", "bgh duyệt"
            ]
            body = doc._body._element
            body_els = list(body)
            first_app_el = None
            # Scan backwards from bottom (last 12 elements)
            for el in reversed(body_els[-12:]):
                text_low = ""
                if el.tag.endswith('p'):
                    text_low = Paragraph(el, doc).text.strip().lower()
                elif el.tag.endswith('tbl'):
                    t_item = Table(el, doc)
                    text_low = ' '.join(c.text.strip().lower() for row in t_item.rows for c in row.cells)
                
                # Must NOT match the top header table
                if "họ và tên giáo viên" in text_low or "tổ chuyên môn:" in text_low:
                    continue
                if any(kw in text_low for kw in approval_keywords):
                    first_app_el = el

            if first_app_el is not None:
                app_idx = body.index(first_app_el)
                for el in [p_tbl_title._p, tbl._tbl, p_after._p]:
                    if el in body:
                        body.remove(el)
                        body.insert(app_idx, el)
                        app_idx += 1

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    doc.save(output_path)
    return output_path


def audit_khbd_nls(file_path, subject="Tin học", grade="9", lesson_title="", client=None):
    """
    Kiểm tra nhanh (Audit) KHBD:
    1. Kiểm tra tài liệu gốc xem đã có NLS hay chưa.
    2. Nếu đã có đầy đủ: phản hồi ngay lập tức without AI latency!
    3. Nếu chưa có hoặc một phần: gọi AI phân tích cốt lõi bài học.
    """
    if not os.path.exists(file_path):
        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "status": "error",
            "message": "File không tồn tại"
        }

    try:
        doc = docx.Document(file_path)
        quick_check = detect_existing_nls(doc)
        filename = os.path.basename(file_path)

        # Nếu tài liệu đã có đầy đủ NLS (mục 2.3 và mã chuẩn / bảng NLS)
        if quick_check["is_fully_integrated"]:
            return {
                "file_path": file_path,
                "filename": filename,
                "status": "already_integrated",
                "message": f"KHBD đã tích hợp Năng lực số đầy đủ ({', '.join(quick_check['found_codes'])}). Không cần chèn thêm.",
                "detected_codes": quick_check["found_codes"],
                "reason": "Đã có mục tiêu NLS và bảng phân tích phát triển NLS cho học sinh",
                "should_modify": False,
                "plan": None
            }

        # Chưa có hoặc chỉ mới có 1 phần -> gọi AI
        core_text = extract_khbd_core_content(doc)
        plan = analyze_and_plan_nls(core_text, filename=filename, subject=subject, grade=grade, lesson_title=lesson_title, client=client)

        if plan.get("status") == "already_integrated":
            return {
                "file_path": file_path,
                "filename": filename,
                "status": "already_integrated",
                "message": "KHBD đã tích hợp Năng lực số phù hợp",
                "detected_codes": plan.get("detected_codes") or quick_check["found_codes"],
                "reason": plan.get("reason", "Đã có các mã NLS"),
                "should_modify": False,
                "plan": plan
            }

        return {
            "file_path": file_path,
            "filename": filename,
            "status": plan.get("status", "not_integrated"),
            "message": plan.get("reason", "Cần bổ sung Năng lực số phù hợp"),
            "detected_codes": plan.get("detected_codes") or quick_check["found_codes"],
            "should_modify": plan.get("should_modify", True),
            "plan": plan
        }

    except Exception as e:
        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "status": "error",
            "message": str(e)
        }


def integrate_khbd_nls(file_path, output_path, subject="Tin học", grade="9", lesson_title="", highlight_red=True, client=None):
    """
    Tích hợp NLS hoàn chỉnh:
    1. Kiểm tra tài liệu.
    2. Nếu đã có đầy đủ: giữ nguyên, không chèn trùng, lưu ra output_path.
    3. Nếu chưa có: gọi AI lập kế hoạch, áp dụng vào DOCX với chữ đỏ.
    """
    if not os.path.exists(file_path):
        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "status": "error",
            "message": "File không tồn tại"
        }

    try:
        audit_res = audit_khbd_nls(file_path, subject=subject, grade=grade, lesson_title=lesson_title, client=client)
        if audit_res.get("status") == "error":
            return audit_res

        filename = os.path.basename(file_path)
        plan = audit_res.get("plan")

        # Đã có đầy đủ NLS
        if audit_res.get("status") == "already_integrated" or not audit_res.get("should_modify"):
            import shutil
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            if os.path.abspath(file_path) != os.path.abspath(output_path):
                shutil.copy2(file_path, output_path)
            return {
                "file_path": file_path,
                "filename": filename,
                "output_path": output_path,
                "status": "already_integrated",
                "message": f"KHBD đã có sẵn NLS đầy đủ ({', '.join(audit_res.get('detected_codes', []))}) - Giữ nguyên định dạng gốc, không chèn trùng lặp.",
                "detected_codes": audit_res.get("detected_codes", []),
                "added_codes": [],
                "highlight_red": highlight_red
            }

        # Cần kiểm tra thủ công
        if audit_res.get("status") == "need_review":
            import shutil
            out_dir = os.path.dirname(output_path)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            if os.path.abspath(file_path) != os.path.abspath(output_path):
                shutil.copy2(file_path, output_path)
            return {
                "file_path": file_path,
                "filename": filename,
                "output_path": output_path,
                "status": "need_review",
                "message": f"Chưa đủ căn cứ tích hợp NLS tự động ({audit_res.get('message')}) - Giữ nguyên tài liệu để GV xem xét.",
                "detected_codes": audit_res.get("detected_codes", []),
                "added_codes": [],
                "highlight_red": highlight_red
            }

        if not plan:
            return {
                "file_path": file_path,
                "filename": filename,
                "status": "error",
                "message": "Không thể lập kế hoạch tích hợp NLS từ AI"
            }

        # Bổ sung vào DOCX
        apply_nls_to_docx(file_path, output_path, plan, highlight_red=highlight_red)

        added_codes = [x.get("code") for x in plan.get("nls_objectives", []) if x.get("code")]

        return {
            "file_path": file_path,
            "filename": filename,
            "output_path": output_path,
            "status": "integrated",
            "message": f"Đã tích hợp thành công {len(added_codes)} mã Năng lực số chuẩn (Thông tư 02/2025/TT-BGDĐT) và đánh dấu đỏ phần thay đổi",
            "detected_codes": audit_res.get("detected_codes", []),
            "added_codes": added_codes,
            "highlight_red": highlight_red,
            "plan_summary": {
                "objectives_count": len(plan.get("nls_objectives", [])),
                "table_rows_count": len(plan.get("nls_table_rows", []))
            }
        }

    except Exception as e:
        return {
            "file_path": file_path,
            "filename": os.path.basename(file_path),
            "status": "error",
            "message": f"Lỗi tích hợp NLS: {str(e)}"
        }
