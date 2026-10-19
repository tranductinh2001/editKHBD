import re
import sys

file_path = r"c:\Users\Admin\Desktop\Thạc sĩ\Chương trình\Cơ sở dữ liệu nâng cao\edu_graph_tinhoc_neo4j\core\exam_builder.py"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update _apply_table_grid_and_widths to add vertical center alignment
old_valign = """                tcW = tcPr.find(qn('w:tcW'))
                if tcW is None:
                    tcW = parse_xml(f'<w:tcW {nsdecls("w")} w:w="{cell_w}" w:type="dxa"/>')
                    tcPr.append(tcW)
                else:
                    tcW.set(qn('w:w'), str(cell_w))
                    tcW.set(qn('w:type'), 'dxa')"""

new_valign = """                # Thiết lập căn giữa dọc cho ô
                vAlign = tcPr.find(qn('w:vAlign'))
                if vAlign is None:
                    tcPr.append(parse_xml(f'<w:vAlign {nsdecls("w")} w:val="center"/>'))
                else:
                    vAlign.set(qn('w:val'), 'center')

                tcW = tcPr.find(qn('w:tcW'))
                if tcW is None:
                    tcW = parse_xml(f'<w:tcW {nsdecls("w")} w:w="{cell_w}" w:type="dxa"/>')
                    tcPr.append(tcW)
                else:
                    tcW.set(qn('w:w'), str(cell_w))
                    tcW.set(qn('w:type'), 'dxa')"""

if old_valign in content:
    content = content.replace(old_valign, new_valign)
    print("1. Updated _apply_table_grid_and_widths with vAlign center!")
else:
    print("1. WARNING: old_valign not found!")

# 2. Update _render_dot_lines to use Tab Leader Dots
old_dot_lines = """    @classmethod
    def _render_dot_lines(cls, doc, count: int = 18):
        \"\"\"
        Tạo các dòng chấm thực tế chuẩn 100% file đề mẫu, lấp đầy full trang giấy A4:
        - Sử dụng chuỗi ký tự 184 dấu chấm phủ kín 100% chiều ngang (18cm / 7.09 in) sát mép lề phải.
        - Chiều cao các dòng chấm được giãn cách cân đối (line_spacing 1.40) phủ kín toàn bộ trang đến sát mép đáy.
        \"\"\"
        for i in range(count):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2.5)
            p.paragraph_format.line_spacing = 1.40
            p.paragraph_format.keep_with_next = (i < count - 1)
            r = p.add_run("." * 184)
            r.font.name = "Times New Roman"
            r.font.size = Pt(11)
            r.font.color.rgb = RGBColor(120, 120, 120)"""

new_dot_lines = """    @classmethod
    def _render_dot_lines(cls, doc, count: int = 18, width_inches: float = 7.087):
        \"\"\"
        Tạo các dòng chấm thực tế chuẩn 100% file đề mẫu, lấp đầy full trang giấy A4:
        - Sử dụng Tab Stop Right với Dot Leader (w:leader="dot") tại đúng tọa độ lề phải (7.087 in / 10206 dxa).
        - Phủ kín 100% chiều ngang sát mép lề phải giấy A4, không bao giờ bị hụt hay rớt dòng.
        - Chiều cao các dòng chấm được giãn cách cân đối (line_spacing 1.35) phủ kín trang đến sát mép đáy.
        \"\"\"
        for i in range(count):
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(2.0)
            p.paragraph_format.line_spacing = 1.35
            p.paragraph_format.keep_with_next = (i < count - 1)
            p.paragraph_format.tab_stops.add_tab_stop(Inches(width_inches), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS)
            r = p.add_run("\\t")
            r.font.name = "Times New Roman"
            r.font.size = Pt(11)
            r.font.color.rgb = RGBColor(100, 100, 100)"""

if old_dot_lines in content:
    content = content.replace(old_dot_lines, new_dot_lines)
    print("2. Updated _render_dot_lines with Tab Leader Dots!")
else:
    print("2. WARNING: old_dot_lines not found!")

# 3. Update _render_score_box signature dots (from 51 dots to 24 dots)
content = content.replace(
    't_score.cell(2, 1).text = "\\n..................................................."',
    't_score.cell(2, 1).text = "\\n........................"'
)
content = content.replace(
    't_score.cell(2, 2).text = "\\n..................................................."',
    't_score.cell(2, 2).text = "\\n........................"'
)
print("3. Updated score box signature dots!")

# 4. Replace t_grid12 with two balanced 6-column tables on Student Exam Paper
old_grid12 = """        # BẢNG ĐIỀN ĐÁP ÁN 12 CỘT CHO CẢ 4 CÂU HỎI (HIỂN THỊ ĐÚNG SỐ THỨ TỰ TIẾP NỐI)
        tf_nums = [str(tf_start + i) for i in range(len(exam_data.get("tfs", [])))]
        c1_no = tf_nums[0] if len(tf_nums) > 0 else str(tf_start)
        c2_no = tf_nums[1] if len(tf_nums) > 1 else str(tf_start + 1)
        c3_no = tf_nums[2] if len(tf_nums) > 2 else str(tf_start + 2)
        c4_no = tf_nums[3] if len(tf_nums) > 3 else str(tf_start + 3)

        headers_12 = ["Câu", "Lệnh", "Đ/S", "Câu", "Lệnh", "Đ/S", "Câu", "Lệnh", "Đ/S", "Câu", "Lệnh", "Đ/S"]
        t_grid12 = doc.add_table(rows=5, cols=12)
        t_grid12.style = 'Table Grid'
        t_grid12.alignment = WD_TABLE_ALIGNMENT.CENTER
        tblPr = t_grid12._tbl.tblPr
        tblCellMar = parse_xml(f'<w:tblCellMar {nsdecls("w")}><w:top w:w="8" w:type="dxa"/><w:bottom w:w="8" w:type="dxa"/><w:left w:w="25" w:type="dxa"/><w:right w:w="25" w:type="dxa"/></w:tblCellMar>')
        tblPr.append(tblCellMar)

        for r in t_grid12.rows:
            cls._cant_split(r)

        for ci, h in enumerate(headers_12):
            c = t_grid12.cell(0, ci)
            c.text = h
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.runs[0].font.name = "Times New Roman"
            p.runs[0].font.size = Pt(8.5)
            p.runs[0].bold = True
            cls.set_cell_shading(c, "FFFFFF")

        for ri, lbl in enumerate(["A", "B", "C", "D"], 1):
            r_vals = [c1_no, lbl, "", c2_no, lbl, "", c3_no, lbl, "", c4_no, lbl, ""]
            for ci, val in enumerate(r_vals):
                c = t_grid12.cell(ri, ci)
                c.text = val
                p = c.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(0)
                if p.runs:
                    p.runs[0].font.name = "Times New Roman"
                    p.runs[0].font.size = Pt(8.5)
        cls._set_col_widths(t_grid12, [Inches(0.42), Inches(0.42), Inches(0.85)] * 4, total_width_dxa=10206)"""

new_grid12 = """        # BẢNG ĐIỀN ĐÁP ÁN ĐÚNG/SAI CHUẨN 2 BẢNG 6 CỘT ĐỀU NHAU (THEO ĐÚNG MẪU NHÀ TRƯỜNG)
        tf_nums = [str(tf_start + i) for i in range(len(exam_data.get("tfs", [])))]
        c1_no = tf_nums[0] if len(tf_nums) > 0 else str(tf_start)
        c2_no = tf_nums[1] if len(tf_nums) > 1 else str(tf_start + 1)
        c3_no = tf_nums[2] if len(tf_nums) > 2 else str(tf_start + 2)
        c4_no = tf_nums[3] if len(tf_nums) > 3 else str(tf_start + 3)

        grid_headers_6 = ["Câu", "Lệnh hỏi", "Đáp án (Đ/S)", "Câu", "Lệnh hỏi", "Đáp án (Đ/S)"]
        col_w_6 = [Inches(0.90), Inches(1.04), Inches(1.60), Inches(0.90), Inches(1.04), Inches(1.60)]

        # Bảng 1: Cho Câu c1_no và c2_no
        t_grid_1 = doc.add_table(rows=5, cols=6)
        t_grid_1.style = 'Table Grid'
        t_grid_1.alignment = WD_TABLE_ALIGNMENT.CENTER
        for r in t_grid_1.rows:
            cls._cant_split(r)
            cls._set_row_height_exact(r, 340)

        for ci, h in enumerate(grid_headers_6):
            c = t_grid_1.cell(0, ci)
            c.text = h
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.runs[0].font.name = "Times New Roman"
            p.runs[0].font.size = Pt(10)
            p.runs[0].bold = True
            cls.set_cell_shading(c, "FFFFFF")

        for ri, lbl in enumerate(["A", "B", "C", "D"], 1):
            r_vals = [c1_no, lbl, "", c2_no, lbl, ""]
            for ci, val in enumerate(r_vals):
                c = t_grid_1.cell(ri, ci)
                c.text = val
                p = c.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                if p.runs:
                    p.runs[0].font.name = "Times New Roman"
                    p.runs[0].font.size = Pt(10)
                    if ci in [0, 1, 3, 4]:
                        p.runs[0].bold = True
        cls._set_col_widths(t_grid_1, col_w_6, total_width_dxa=10206)

        # Khoảng cách giữa 2 bảng
        p_sp_grid = doc.add_paragraph()
        p_sp_grid.paragraph_format.space_before = Pt(1)
        p_sp_grid.paragraph_format.space_after = Pt(1)
        p_sp_grid.paragraph_format.line_spacing = 0.5
        p_sp_grid.paragraph_format.keep_with_next = True

        # Bảng 2: Cho Câu c3_no và c4_no
        t_grid_2 = doc.add_table(rows=5, cols=6)
        t_grid_2.style = 'Table Grid'
        t_grid_2.alignment = WD_TABLE_ALIGNMENT.CENTER
        for r in t_grid_2.rows:
            cls._cant_split(r)
            cls._set_row_height_exact(r, 340)

        for ci, h in enumerate(grid_headers_6):
            c = t_grid_2.cell(0, ci)
            c.text = h
            p = c.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            p.runs[0].font.name = "Times New Roman"
            p.runs[0].font.size = Pt(10)
            p.runs[0].bold = True
            cls.set_cell_shading(c, "FFFFFF")

        for ri, lbl in enumerate(["A", "B", "C", "D"], 1):
            r_vals = [c3_no, lbl, "", c4_no, lbl, ""]
            for ci, val in enumerate(r_vals):
                c = t_grid_2.cell(ri, ci)
                c.text = val
                p = c.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                if p.runs:
                    p.runs[0].font.name = "Times New Roman"
                    p.runs[0].font.size = Pt(10)
                    if ci in [0, 1, 3, 4]:
                        p.runs[0].bold = True
        cls._set_col_widths(t_grid_2, col_w_6, total_width_dxa=10206)"""

if old_grid12 in content:
    content = content.replace(old_grid12, new_grid12)
    print("4. Replaced t_grid12 with two balanced 6-column tables!")
else:
    print("4. WARNING: old_grid12 not found!")

# 5. In _render_scoring_guide: synchronize t_ans2_1 and t_ans2_2 to use col_w_6
old_guide_t2 = """            cls._set_col_widths(t_ans2_1, [Inches(0.85), Inches(1.15), Inches(1.545), Inches(0.85), Inches(1.15), Inches(1.545)], total_width_dxa=10206)"""
new_guide_t2 = """            for r in t_ans2_1.rows: cls._set_row_height_exact(r, 340)
            cls._set_col_widths(t_ans2_1, [Inches(0.90), Inches(1.04), Inches(1.60), Inches(0.90), Inches(1.04), Inches(1.60)], total_width_dxa=10206)"""
content = content.replace(old_guide_t2, new_guide_t2)

old_guide_t2_2 = """            cls._set_col_widths(t_ans2_2, [Inches(0.85), Inches(1.15), Inches(1.545), Inches(0.85), Inches(1.15), Inches(1.545)], total_width_dxa=10206)"""
new_guide_t2_2 = """            for r in t_ans2_2.rows: cls._set_row_height_exact(r, 340)
            cls._set_col_widths(t_ans2_2, [Inches(0.90), Inches(1.04), Inches(1.60), Inches(0.90), Inches(1.04), Inches(1.60)], total_width_dxa=10206)"""
content = content.replace(old_guide_t2_2, new_guide_t2_2)

# Also ensure t_ans1 (MCQ scoring guide) has exact row height
old_ans1_w = """            cls._set_col_widths(t_ans1, [Inches(0.97)] + [Inches(0.51)] * len(exam["mcqs"]), total_width_dxa=10206)"""
new_ans1_w = """            for r in t_ans1.rows: cls._set_row_height_exact(r, 380)
            cls._set_col_widths(t_ans1, [Inches(0.97)] + [Inches(0.51)] * len(exam["mcqs"]), total_width_dxa=10206)"""
content = content.replace(old_ans1_w, new_ans1_w)

# Also ensure t_ans3 (Essay scoring guide)
old_ans3_w = """            cls._set_col_widths(t_ans3, [Inches(1.2), Inches(4.9), Inches(0.99)], total_width_dxa=10206)"""
new_ans3_w = """            cls._set_col_widths(t_ans3, [Inches(0.90), Inches(5.21), Inches(0.97)], total_width_dxa=10206)"""
content = content.replace(old_ans3_w, new_ans3_w)
print("5. Synchronized scoring guide tables!")

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("SUCCESS: Finished patching exam_builder.py!")
