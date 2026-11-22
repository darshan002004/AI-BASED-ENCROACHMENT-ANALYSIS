"""
EncroWatch AI — Academic Thesis & Research Paper DOCX Generator
==============================================================
Compiles ENCROWATCH_AI_FINAL_RESEARCH_PAPER.md into an IEEE/ACM styled,
publication-quality Microsoft Word (.docx) document.
"""

import os
import re
import sys
import shutil

def generate_docx():
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
    from docx.oxml import OxmlElement, parse_xml
    from docx.oxml.ns import nsdecls, qn

    base_dir = r"C:\Users\Darshan B\.gemini\antigravity\scratch\encrowatch-ai"
    md_path = os.path.join(base_dir, "ENCROWATCH_AI_FINAL_RESEARCH_PAPER.md")
    docx_workspace_path = os.path.join(base_dir, "ENCROWATCH_AI_FINAL_RESEARCH_PAPER.docx")
    docx_brain_path = r"C:\Users\Darshan B\.gemini\antigravity\brain\cb519cdb-5935-42b4-88b0-d7dba4b5e06e\ENCROWATCH_AI_FINAL_RESEARCH_PAPER.docx"

    print(f"Reading markdown source from: {md_path}")
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    doc = docx.Document()

    # Configure A4 Page Setup
    for section in doc.sections:
        section.page_width = Inches(8.27)   # A4 width
        section.page_height = Inches(11.69) # A4 height
        section.top_margin = Inches(0.75)
        section.bottom_margin = Inches(0.75)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)

        # Header / Footer
        footer = section.footer
        f_p = footer.paragraphs[0]
        f_p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        f_run = f_p.add_run("EncroWatch AI Research Initiative | Major Thesis")
        f_run.font.name = "Times New Roman"
        f_run.font.size = Pt(8.5)
        f_run.font.color.rgb = RGBColor(120, 120, 120)

    # Styles helper
    def format_run(run, font_name="Times New Roman", size_pt=10, bold=False, italic=False, color=RGBColor(20, 20, 20)):
        run.font.name = font_name
        run.font.size = Pt(size_pt)
        run.bold = bold
        run.italic = italic
        run.font.color.rgb = color

    def add_p_border_bottom(p, color="000000", sz="12"):
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        bottom = OxmlElement('w:bottom')
        bottom.set(qn('w:val'), 'single')
        bottom.set(qn('w:sz'), sz)
        bottom.set(qn('w:space'), '4')
        bottom.set(qn('w:color'), color)
        pBdr.append(bottom)
        pPr.append(pBdr)

    def set_cell_shading(cell, color_hex="F2F2F2"):
        shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
        cell._tc.get_or_add_tcPr().append(shading)

    def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
        tcPr = cell._tc.get_or_add_tcPr()
        tcMar = OxmlElement('w:tcMar')
        for m, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
            node = OxmlElement(f'w:{m}')
            node.set(qn('w:w'), str(val))
            node.set(qn('w:type'), 'dxa')
            tcMar.append(node)
        tcPr.append(tcMar)

    lines = md_text.splitlines()
    in_code_block = False
    code_lines = []
    in_table = False
    table_lines = []

    def flush_table(lines_to_flush):
        if not lines_to_flush:
            return
        rows = []
        for l in lines_to_flush:
            parts = [c.strip() for c in l.strip().split('|')[1:-1]]
            # Skip separator line (e.g. |:---|:---|)
            if parts and all(re.match(r'^:?-+:?$', p) for p in parts if p):
                continue
            rows.append(parts)

        if not rows:
            return

        cols_count = max(len(r) for r in rows)
        t = doc.add_table(rows=len(rows), cols=cols_count)
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        t.autofit = True

        for r_idx, r in enumerate(rows):
            is_header = (r_idx == 0)
            for c_idx in range(cols_count):
                cell = t.cell(r_idx, c_idx)
                cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
                set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
                text_val = r[c_idx] if c_idx < len(r) else ""
                
                # Clean markdown bold/code from cell text
                clean_text = text_val.replace('**', '').replace('`', '')
                
                cp = cell.paragraphs[0]
                cp.alignment = WD_ALIGN_PARAGRAPH.LEFT
                cp.paragraph_format.space_before = Pt(1)
                cp.paragraph_format.space_after = Pt(1)
                
                run = cp.add_run(clean_text)
                format_run(run, font_name="Times New Roman", size_pt=8.5, bold=is_header)

                if is_header:
                    set_cell_shading(cell, "EAEAEA")
                else:
                    if r_idx % 2 == 0:
                        set_cell_shading(cell, "FBFBFB")

        # Add thin spacing after table
        post_p = doc.add_paragraph()
        post_p.paragraph_format.space_before = Pt(4)
        post_p.paragraph_format.space_after = Pt(4)

    def flush_code(lines_to_flush):
        if not lines_to_flush:
            return
        code_text = "\n".join(lines_to_flush)
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(4)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Inches(0.2)
        p.paragraph_format.right_indent = Inches(0.2)

        # Style as preformatted box
        run = p.add_run(code_text)
        format_run(run, font_name="Consolas", size_pt=7.5, color=RGBColor(30, 30, 30))
        
        # Border box around pre
        pPr = p._p.get_or_add_pPr()
        pBdr = OxmlElement('w:pBdr')
        for b_name in ['top', 'left', 'bottom', 'right']:
            b = OxmlElement(f'w:{b_name}')
            b.set(qn('w:val'), 'single')
            b.set(qn('w:sz'), '4')
            b.set(qn('w:color'), 'CCCCCC')
            pBdr.append(b)
        pPr.append(pBdr)
        
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F8F8F8"/>')
        pPr.append(shd)

    i = 0
    total_lines = len(lines)
    while i < total_lines:
        line = lines[i]

        # Handle code blocks
        if line.strip().startswith("```"):
            if in_code_block:
                flush_code(code_lines)
                code_lines = []
                in_code_block = False
            else:
                if in_table:
                    flush_table(table_lines)
                    table_lines = []
                    in_table = False
                in_code_block = True
                code_lines = []
            i += 1
            continue

        if in_code_block:
            code_lines.append(line)
            i += 1
            continue

        # Handle tables
        if line.strip().startswith("|") and line.strip().endswith("|"):
            if not in_table:
                in_table = True
                table_lines = []
            table_lines.append(line)
            i += 1
            continue
        else:
            if in_table:
                flush_table(table_lines)
                table_lines = []
                in_table = False

        stripped = line.strip()

        # Blank line
        if not stripped:
            i += 1
            continue

        # Horizontal rule
        if stripped in ["---", "***", "___"]:
            i += 1
            continue

        # Title
        if stripped.startswith("# ") and not stripped.startswith("# Section"):
            title_text = stripped[2:].strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(10)
            run = p.add_run(title_text)
            format_run(run, font_name="Times New Roman", size_pt=18, bold=True, color=RGBColor(0, 0, 0))
            i += 1
            continue

        # Author / Metadata blocks
        if stripped.startswith("**Author:**") or stripped.startswith("**Degree") or stripped.startswith("**Department") or stripped.startswith("**Academic") or stripped.startswith("**Research Initiative") or stripped.startswith("**Computational Environment"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(1)
            # Parse bold prefix
            clean = stripped.replace('**', '')
            parts = clean.split(':', 1)
            if len(parts) == 2:
                r1 = p.add_run(parts[0] + ": ")
                format_run(r1, font_name="Times New Roman", size_pt=9.5, bold=True, color=RGBColor(40, 40, 40))
                r2 = p.add_run(parts[1].strip())
                format_run(r2, font_name="Times New Roman", size_pt=9.5, color=RGBColor(60, 60, 60))
            else:
                r = p.add_run(clean)
                format_run(r, font_name="Times New Roman", size_pt=9.5, color=RGBColor(60, 60, 60))
            i += 1
            continue

        # Major Headings (Section 1 to 26)
        if stripped.startswith("## Section ") or stripped.startswith("## "):
            sec_text = stripped.lstrip('#').strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(14)
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(sec_text.upper())
            format_run(run, font_name="Times New Roman", size_pt=12, bold=True, color=RGBColor(0, 0, 0))
            add_p_border_bottom(p, color="000000", sz="12")
            i += 1
            continue

        # Level 2 / 3 Headings
        if stripped.startswith("### "):
            sub_text = stripped[4:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(10)
            p.paragraph_format.space_after = Pt(4)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(sub_text)
            format_run(run, font_name="Times New Roman", size_pt=10.5, bold=True, color=RGBColor(20, 20, 20))
            i += 1
            continue

        if stripped.startswith("#### "):
            sub_text = stripped[5:].strip()
            p = doc.add_paragraph()
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(3)
            p.paragraph_format.keep_with_next = True
            run = p.add_run(sub_text)
            format_run(run, font_name="Times New Roman", size_pt=10, bold=True, italic=True, color=RGBColor(30, 30, 30))
            i += 1
            continue

        # Bullet List Items
        if stripped.startswith("* ") or stripped.startswith("- "):
            b_text = stripped[2:].strip()
            p = doc.add_paragraph(style='List Bullet')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Inches(0.25)
            # Parse bold elements
            tokens = re.split(r'(\*\*.*?\*\*)', b_text)
            for t in tokens:
                if t.startswith('**') and t.endswith('**'):
                    run = p.add_run(t[2:-2])
                    format_run(run, font_name="Times New Roman", size_pt=10, bold=True)
                else:
                    run = p.add_run(t)
                    format_run(run, font_name="Times New Roman", size_pt=10)
            i += 1
            continue

        # Numbered List Items
        m_num = re.match(r'^(\d+)\.\s+(.*)$', stripped)
        if m_num:
            n_num = m_num.group(1)
            n_text = m_num.group(2)
            p = doc.add_paragraph(style='List Number')
            p.paragraph_format.space_before = Pt(1)
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.left_indent = Inches(0.25)
            tokens = re.split(r'(\*\*.*?\*\*)', n_text)
            for t in tokens:
                if t.startswith('**') and t.endswith('**'):
                    run = p.add_run(t[2:-2])
                    format_run(run, font_name="Times New Roman", size_pt=10, bold=True)
                else:
                    run = p.add_run(t)
                    format_run(run, font_name="Times New Roman", size_pt=10)
            i += 1
            continue

        # Display Math Equations ($$...$$)
        if stripped.startswith("$$") and stripped.endswith("$$") and len(stripped) > 4:
            math_text = stripped[2:-2].strip()
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(6)
            p.paragraph_format.space_after = Pt(6)
            run = p.add_run(math_text)
            format_run(run, font_name="Cambria Math", size_pt=10.5, italic=True, color=RGBColor(0, 0, 100))
            i += 1
            continue

        # Normal Paragraph
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(5)
        p.paragraph_format.line_spacing = 1.15

        # Check if Abstract block
        is_abstract = "Pedestrian footpaths in high-density" in stripped
        if is_abstract:
            p.paragraph_format.left_indent = Inches(0.3)
            p.paragraph_format.right_indent = Inches(0.3)

        tokens = re.split(r'(\*\*.*?\*\*|\*.*?\*|`.*?`)', stripped)
        for t in tokens:
            if t.startswith('**') and t.endswith('**'):
                run = p.add_run(t[2:-2])
                format_run(run, font_name="Times New Roman", size_pt=9.5 if is_abstract else 10, bold=True, italic=is_abstract)
            elif t.startswith('*') and t.endswith('*'):
                run = p.add_run(t[1:-1])
                format_run(run, font_name="Times New Roman", size_pt=9.5 if is_abstract else 10, italic=True)
            elif t.startswith('`') and t.endswith('`'):
                run = p.add_run(t[1:-1])
                format_run(run, font_name="Consolas", size_pt=9, color=RGBColor(40, 40, 40))
            else:
                run = p.add_run(t)
                format_run(run, font_name="Times New Roman", size_pt=9.5 if is_abstract else 10, italic=is_abstract)

        i += 1

    # End of document flush
    if in_table:
        flush_table(table_lines)
    if in_code_block:
        flush_code(code_lines)

    print(f"Writing compiled DOCX to: {docx_workspace_path}")
    doc.save(docx_workspace_path)

    if os.path.exists(docx_workspace_path) and os.path.getsize(docx_workspace_path) > 0:
        size_kb = os.path.getsize(docx_workspace_path) / 1024
        print(f"SUCCESS: Generated {docx_workspace_path} ({size_kb:.2f} KB)")
        shutil.copy2(docx_workspace_path, docx_brain_path)
        print(f"SUCCESS: Synced DOCX to brain artifact repository: {docx_brain_path}")
        return True
    else:
        print("Error: DOCX was not created or has 0 bytes.")
        return False

if __name__ == "__main__":
    success = generate_docx()
    sys.exit(0 if success else 1)
