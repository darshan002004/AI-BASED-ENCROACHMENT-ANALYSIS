"""
EncroWatch AI — Academic Thesis & Research Paper PDF Generator
==============================================================
Compiles ENCROWATCH_AI_FINAL_RESEARCH_PAPER.md into an IEEE/ACM styled,
publication-quality PDF document using Headless Google Chrome.
"""

import os
import sys
import subprocess
import shutil
import markdown

def generate_pdf():
    base_dir = r"C:\Users\Darshan B\.gemini\antigravity\scratch\encrowatch-ai"
    md_path = os.path.join(base_dir, "ENCROWATCH_AI_FINAL_RESEARCH_PAPER.md")
    output_html_dir = os.path.join(base_dir, "results", "paper")
    os.makedirs(output_html_dir, exist_ok=True)
    html_path = os.path.join(output_html_dir, "ENCROWATCH_AI_FINAL_RESEARCH_PAPER.html")
    pdf_workspace_path = os.path.join(base_dir, "ENCROWATCH_AI_FINAL_RESEARCH_PAPER.pdf")
    pdf_brain_path = r"C:\Users\Darshan B\.gemini\antigravity\brain\cb519cdb-5935-42b4-88b0-d7dba4b5e06e\ENCROWATCH_AI_FINAL_RESEARCH_PAPER.pdf"

    print(f"Reading markdown source from: {md_path}")
    with open(md_path, "r", encoding="utf-8") as f:
        md_text = f.read()

    # Convert markdown to HTML
    html_body = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "toc"]
    )

    # Academic styling template
    full_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EncroWatch AI: Research Paper</title>
<!-- KaTeX for math rendering -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
<script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"
    onload="renderMathInElement(document.body, {{
        delimiters: [
            {{left: '$$', right: '$$', display: true}},
            {{left: '$', right: '$', display: false}},
            {{left: '\\\\(', right: '\\\\)', display: false}},
            {{left: '\\\\[', right: '\\\\]', display: true}}
        ]
    }});"></script>
<style>
    @page {{
        size: A4;
        margin: 18mm 16mm 20mm 16mm;
        @bottom-right {{
            content: "Page " counter(page);
            font-size: 8pt;
            font-family: 'Times New Roman', Times, serif;
        }}
    }}
    
    body {{
        font-family: 'Times New Roman', Times, 'Nimbus Roman No9 L', serif;
        font-size: 10pt;
        line-height: 1.45;
        color: #111111;
        background: #ffffff;
        margin: 0;
        padding: 0;
    }}

    .container {{
        width: 100%;
        max-width: 100%;
        margin: 0 auto;
    }}

    /* Paper Header */
    h1 {{
        font-size: 17pt;
        font-weight: bold;
        text-align: center;
        margin-top: 0;
        margin-bottom: 8pt;
        line-height: 1.25;
        color: #000000;
    }}

    .authors-block {{
        text-align: center;
        font-size: 9.5pt;
        margin-bottom: 14pt;
        color: #222222;
        line-height: 1.35;
    }}

    /* Section Headings */
    h2 {{
        font-size: 12pt;
        font-weight: bold;
        text-transform: uppercase;
        border-bottom: 1.5px solid #000000;
        padding-bottom: 2pt;
        margin-top: 14pt;
        margin-bottom: 6pt;
        color: #000000;
        page-break-after: avoid;
    }}

    h3 {{
        font-size: 10.5pt;
        font-weight: bold;
        margin-top: 10pt;
        margin-bottom: 4pt;
        color: #111111;
        page-break-after: avoid;
    }}

    h4 {{
        font-size: 10pt;
        font-weight: bold;
        font-style: italic;
        margin-top: 8pt;
        margin-bottom: 3pt;
        page-break-after: avoid;
    }}

    p {{
        margin-top: 0;
        margin-bottom: 6pt;
        text-align: justify;
        text-justify: inter-word;
    }}

    /* Abstract Block */
    blockquote, .abstract {{
        font-style: italic;
        margin: 10pt 20pt;
        padding: 6pt 10pt;
        background: #fbfbfb;
        border-left: 3px solid #333333;
    }}

    /* Tables */
    table {{
        width: 100%;
        border-collapse: collapse;
        margin: 10pt 0;
        font-size: 8.5pt;
        page-break-inside: avoid;
    }}

    th, td {{
        border: 1px solid #777777;
        padding: 4pt 6pt;
        text-align: left;
    }}

    th {{
        background-color: #f0f0f0;
        font-weight: bold;
        color: #000000;
    }}

    tr:nth-child(even) {{
        background-color: #fafafa;
    }}

    /* Code & ASCII Diagrams */
    pre {{
        background-color: #f7f7f7;
        border: 1px solid #cccccc;
        border-radius: 3px;
        padding: 6pt 8pt;
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 7.5pt;
        line-height: 1.25;
        overflow-x: auto;
        page-break-inside: avoid;
        margin: 8pt 0;
    }}

    code {{
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 8.5pt;
        background: #f2f2f2;
        padding: 1pt 3pt;
        border-radius: 2px;
    }}

    pre code {{
        background: transparent;
        padding: 0;
    }}

    hr {{
        border: 0;
        height: 1px;
        background: #cccccc;
        margin: 12pt 0;
    }}

    ul, ol {{
        margin-top: 0;
        margin-bottom: 6pt;
        padding-left: 20pt;
    }}

    li {{
        margin-bottom: 2pt;
        text-align: justify;
    }}

    .footer-note {{
        font-size: 8pt;
        color: #555555;
        border-top: 1px solid #cccccc;
        padding-top: 4pt;
        margin-top: 20pt;
        text-align: center;
    }}
</style>
</head>
<body>
<div class="container">
{html_body}
<div class="footer-note">
    EncroWatch AI Research Initiative &bull; Department of Computer Applications &bull; Academic Year 2026–2027 &bull; Candidate: Darshan B
</div>
</div>
</body>
</html>
"""

    print(f"Writing rendered HTML to: {html_path}")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if not os.path.exists(chrome_path):
        print(f"Error: Chrome executable not found at {chrome_path}")
        return False

    cmd = [
        chrome_path,
        "--headless=new",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_workspace_path}",
        html_path
    ]

    print(f"Executing Headless Chrome PDF compiler...")
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        print(f"Chrome PDF generation failed with code {res.returncode}")
        print(f"STDERR: {res.stderr}")
        return False

    if os.path.exists(pdf_workspace_path) and os.path.getsize(pdf_workspace_path) > 0:
        size_kb = os.path.getsize(pdf_workspace_path) / 1024
        print(f"SUCCESS: Generated {pdf_workspace_path} ({size_kb:.2f} KB)")
        
        # Sync to brain artifacts directory
        shutil.copy2(pdf_workspace_path, pdf_brain_path)
        print(f"SUCCESS: Synced PDF to brain artifact repository: {pdf_brain_path}")
        return True
    else:
        print("Error: PDF file was not created or has 0 bytes.")
        return False

if __name__ == "__main__":
    success = generate_pdf()
    sys.exit(0 if success else 1)
