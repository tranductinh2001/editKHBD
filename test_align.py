import sys, os
proj_dir = r'c:\Users\Admin\Desktop\Thạc sĩ\Chương trình\Cơ sở dữ liệu nâng cao\edu_graph_tinhoc_neo4j'
if proj_dir not in sys.path: sys.path.insert(0, proj_dir)

from core.exam_builder import ExamDocxExporter, ExamMatrixEngine
import win32com.client

# Cập nhật thử nghiệm trong memory hoặc test
engine = ExamMatrixEngine(grade_level="Lớp 9")
dossier = engine.generate_exam_dossier()

out_test = os.path.join(proj_dir, "output", "test_align.docx")
ExamDocxExporter.export(dossier, out_test)

# Đo vị trí cắt kéo
word = win32com.client.Dispatch('Word.Application')
word.Visible = False
doc = word.Documents.Open(os.path.abspath(out_test))

try:
    cuts = []
    for p in doc.Paragraphs:
        if '✂' in p.Range.Text:
            page_no = p.Range.Information(3)
            y_pos = p.Range.Information(6)
            cuts.append((page_no, y_pos, p.Range.Text[:20].strip()))
    for c in cuts:
        print(f'Page {c[0]}: Y = {c[1]:.2f} pt ({c[1]*20:.0f} dxa)')
finally:
    doc.Close(False)
    word.Quit()
