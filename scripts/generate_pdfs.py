"""
AutogenOS Research Publication PDF Generator
Converts markdown research whitepapers into publication-grade academic PDFs.
Author: Meet Shah
"""

import os
import re
import base64
import asyncio
import markdown
from playwright.async_api import async_playwright

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAPERS_DIR = os.path.join(WORKSPACE, "papers")
DOCS_PAPERS_DIR = os.path.join(WORKSPACE, "docs", "papers")
LOGO_PATH = os.path.join(WORKSPACE, "docs", "assets", "logo.png")

# Load logo as base64
logo_b64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as f:
        logo_b64 = f"data:image/png;base64,{base64.b64encode(f.read()).decode('utf-8')}"

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{title}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,400;0,500;0,600;0,700;1,400;1,600&family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
  <style>
    @page {{
      size: A4;
      margin: 22mm 20mm 24mm 20mm;
    }}
    
    * {{
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }}

    body {{
      font-family: 'Crimson Pro', Georgia, 'Times New Roman', serif;
      font-size: 11pt;
      line-height: 1.62;
      color: #0f172a;
      background: #ffffff;
      margin: 0;
      padding: 0;
      text-rendering: optimizeLegibility;
    }}

    /* Paper Header & Identification */
    .paper-banner {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-bottom: 14px;
      margin-bottom: 24px;
      border-bottom: 1.5px solid #0f172a;
    }}
    .series-title {{
      font-family: 'Inter', sans-serif;
      font-size: 8.5pt;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: #2563eb;
    }}
    .series-meta {{
      font-family: 'Inter', sans-serif;
      font-size: 8pt;
      font-weight: 500;
      color: #64748b;
    }}
    .brand-emblem-small {{
      width: 26px;
      height: 26px;
      object-fit: contain;
    }}

    /* Paper Title & Subtitle */
    .title-block {{
      margin-bottom: 20px;
    }}
    h1.paper-title {{
      font-family: 'Inter', sans-serif;
      font-size: 21pt;
      font-weight: 800;
      line-height: 1.25;
      color: #090d16;
      margin: 0 0 14px 0;
      letter-spacing: -0.025em;
    }}

    /* Author Attribution Block */
    .author-card {{
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 6px;
      padding: 12px 18px;
      margin-bottom: 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}
    .author-main {{
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}
    .author-name {{
      font-family: 'Inter', sans-serif;
      font-size: 12.5pt;
      font-weight: 700;
      color: #0f172a;
    }}
    .author-role {{
      font-family: 'Inter', sans-serif;
      font-size: 9pt;
      font-weight: 500;
      color: #475569;
    }}
    .author-lab {{
      font-family: 'Crimson Pro', serif;
      font-size: 9.5pt;
      font-style: italic;
      color: #64748b;
    }}
    .author-links {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 7.8pt;
      color: #2563eb;
      text-align: right;
      display: flex;
      flex-direction: column;
      gap: 3px;
    }}
    .author-links a {{
      color: #2563eb;
      text-decoration: none;
    }}

    /* Abstract Block */
    .abstract-container {{
      background: #f1f5f9;
      border-left: 4px solid #2563eb;
      border-radius: 4px;
      padding: 14px 18px;
      margin: 20px 0 26px 0;
    }}
    .abstract-title {{
      font-family: 'Inter', sans-serif;
      font-size: 8.5pt;
      font-weight: 800;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: #1e3a8a;
      margin-bottom: 6px;
    }}
    .abstract-content {{
      font-size: 10.2pt;
      line-height: 1.58;
      color: #1e293b;
      text-align: justify;
      margin: 0;
    }}

    /* Headings */
    h2 {{
      font-family: 'Inter', sans-serif;
      font-size: 13.5pt;
      font-weight: 700;
      color: #0f172a;
      border-bottom: 1.2px solid #cbd5e1;
      padding-bottom: 4px;
      margin-top: 30px;
      margin-bottom: 12px;
      page-break-after: avoid;
    }}
    h3 {{
      font-family: 'Inter', sans-serif;
      font-size: 11pt;
      font-weight: 600;
      color: #1e293b;
      margin-top: 20px;
      margin-bottom: 8px;
      page-break-after: avoid;
    }}

    p {{
      margin: 0 0 12px 0;
      text-align: justify;
    }}

    /* Lists */
    ul, ol {{
      margin: 0 0 14px 0;
      padding-left: 22px;
    }}
    li {{
      margin-bottom: 5px;
    }}

    /* Code Blocks & Schemas */
    pre {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 8.2pt;
      line-height: 1.45;
      background: #0f172a;
      color: #e2e8f0;
      padding: 12px 14px;
      border-radius: 6px;
      overflow-x: auto;
      margin: 14px 0;
      page-break-inside: avoid;
      box-shadow: inset 0 1px 3px rgba(0,0,0,0.3);
    }}
    code {{
      font-family: 'JetBrains Mono', monospace;
      font-size: 8.8pt;
    }}
    p code, li code {{
      background: #f1f5f9;
      color: #0284c7;
      padding: 1.5px 4.5px;
      border-radius: 4px;
      border: 1px solid #e2e8f0;
      font-weight: 500;
    }}

    /* Tables */
    table {{
      width: 100%;
      border-collapse: collapse;
      margin: 18px 0;
      font-family: 'Inter', sans-serif;
      font-size: 8.8pt;
      page-break-inside: avoid;
    }}
    th {{
      background: #f8fafc;
      font-weight: 700;
      color: #0f172a;
      text-align: left;
      padding: 8px 10px;
      border-top: 2px solid #0f172a;
      border-bottom: 1.5px solid #0f172a;
    }}
    td {{
      padding: 8px 10px;
      border-bottom: 1px solid #e2e8f0;
      color: #1e293b;
      vertical-align: top;
    }}
    tr:nth-child(even) td {{
      background: #fbfcfe;
    }}
    table {{
      border-bottom: 2px solid #0f172a;
    }}

    /* Math Formulae */
    .katex-display {{
      margin: 16px 0 !important;
      overflow-x: auto;
      overflow-y: hidden;
      padding: 6px 0;
    }}

    /* Blockquotes / Alerts */
    blockquote {{
      border-left: 3.5px solid #3b82f6;
      background: #f8fafc;
      padding: 10px 14px;
      margin: 14px 0;
      color: #334155;
      font-style: italic;
      border-radius: 0 4px 4px 0;
    }}

    hr {{
      border: 0;
      height: 1px;
      background: #e2e8f0;
      margin: 24px 0;
    }}

    /* Micro-fine Footer Note */
    .paper-colophon {{
      margin-top: 36px;
      padding-top: 12px;
      border-top: 1px dashed #cbd5e1;
      font-family: 'Inter', sans-serif;
      font-size: 7.8pt;
      color: #94a3b8;
      display: flex;
      justify-content: space-between;
      page-break-inside: avoid;
    }}
  </style>
</head>
<body>

  <!-- Academic Banner -->
  <div class="paper-banner">
    <div style="display:flex; align-items:center; gap:8px;">
      <img src="{logo_b64}" class="brand-emblem-small" alt="AutogenOS Logo">
      <div>
        <div class="series-title">AutogenOS Autonomous Research Series</div>
        <div class="series-meta">Theoretical Foundation & Empirical Systems Engineering</div>
      </div>
    </div>
    <div style="text-align:right;">
      <div class="series-meta">Paper Ref: <strong>{paper_id}</strong></div>
      <div class="series-meta">Published: November 2026</div>
    </div>
  </div>

  <!-- Title -->
  <div class="title-block">
    <h1 class="paper-title">{paper_title}</h1>
  </div>

  <!-- Author Attribution Card -->
  <div class="author-card">
    <div class="author-main">
      <div class="author-name">Meet Shah</div>
      <div class="author-role">Chief Architect & Lead Researcher</div>
      <div class="author-lab">Autonomous Systems & Swarm Intelligence Lab &bull; AutogenOS Foundation</div>
    </div>
    <div class="author-links">
      <div><a href="mailto:meet@autogenos.org">meet@autogenos.org</a></div>
      <div><a href="https://github.com/Meet6338-X/AutogenOS">github.com/Meet6338-X/AutogenOS</a></div>
      <div style="color:#64748b;">San Francisco / Distributed</div>
    </div>
  </div>

  <!-- Abstract (if present) -->
  {abstract_block}

  <!-- Body Content -->
  <div class="paper-body">
    {body_content}
  </div>

  <!-- Colophon -->
  <div class="paper-colophon">
    <div>&copy; 2026 Meet Shah. Licensed under Apache 2.0 / Creative Commons BY-4.0.</div>
    <div>AutogenOS Multi-Agent Operating System Framework</div>
  </div>

  <script>
    document.addEventListener("DOMContentLoaded", function() {{
      if (typeof renderMathInElement !== 'undefined') {{
        renderMathInElement(document.body, {{
          delimiters: [
            {{left: "$$", right: "$$", display: true}},
            {{left: "$", right: "$", display: false}}
          ],
          throwOnError: false
        }});
      }}
    }});
  </script>
</body>
</html>
"""

def extract_and_protect_math(md_text):
    """
    Protects KaTeX math formulas from markdown parser manipulation.
    """
    display_math = []
    inline_math = []

    def disp_sub(m):
        display_math.append(m.group(0))
        return f"@@DISPLAY_MATH_{len(display_math)-1}@@"

    def inline_sub(m):
        inline_math.append(m.group(0))
        return f"@@INLINE_MATH_{len(inline_math)-1}@@"

    # Protect display math ($$ ... $$)
    text = re.sub(r'\$\$([\s\S]+?)\$\$', disp_sub, md_text)
    # Protect inline math ($ ... $)
    text = re.sub(r'(?<!\$)\$(?!\$)([^\n\$]+?)(?<!\$)\$(?!\$)', inline_sub, text)

    return text, display_math, inline_math

def restore_math(html_text, display_math, inline_math):
    for i, m in enumerate(display_math):
        html_text = html_text.replace(f"@@DISPLAY_MATH_{i}@@", m)
    for i, m in enumerate(inline_math):
        html_text = html_text.replace(f"@@INLINE_MATH_{i}@@", m)
    return html_text

def process_markdown_file(file_path, paper_id):
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    lines = raw_text.splitlines()

    # Extract paper title from first # Header
    paper_title = "AutogenOS Research Paper"
    body_lines = []
    found_title = False
    for line in lines:
        if line.startswith("# ") and not found_title:
            paper_title = line[2:].strip()
            found_title = True
        else:
            body_lines = lines[lines.index(line):]
            break

    remaining_text = "\n".join(body_lines)

    # Remove author block from body if it was inserted as markdown text
    remaining_text = re.sub(r'\*\*Author:\*\*[\s\S]+?\*Published:[\s\S]+?\*\n\n', '', remaining_text)

    # Extract abstract if present
    abstract_block = ""
    abstract_match = re.search(r'\*\*Abstract\*\*\s*([\s\S]+?)(?=\n---|\n## 1|\Z)', remaining_text)
    if abstract_match:
        abstract_text = abstract_match.group(1).strip()
        abstract_block = f"""
        <div class="abstract-container">
          <div class="abstract-title">Abstract</div>
          <p class="abstract-content">{abstract_text}</p>
        </div>
        """
        # Remove abstract from remaining text
        remaining_text = remaining_text[:abstract_match.start()] + remaining_text[abstract_match.end():]

    # Clean up leading horizontal rules or dividers
    remaining_text = re.sub(r'^\s*---\s*', '', remaining_text.strip())

    # Protect math before Markdown parsing
    protected_text, display_math, inline_math = extract_and_protect_math(remaining_text)

    # Convert to HTML with tables and fenced code blocks
    raw_html = markdown.markdown(
        protected_text,
        extensions=['tables', 'fenced_code', 'nl2br']
    )

    # Restore math
    final_body_html = restore_math(raw_html, display_math, inline_math)

    full_html = HTML_TEMPLATE.format(
        title=paper_title,
        paper_id=paper_id,
        paper_title=paper_title,
        logo_b64=logo_b64,
        abstract_block=abstract_block,
        body_content=final_body_html
    )

    return full_html, paper_title

async def generate_pdf(browser, html_content, output_pdf_path, paper_title):
    page = await browser.new_page()
    await page.set_content(html_content, wait_until="networkidle")
    
    # Wait for KaTeX to finish rendering math
    await page.evaluate("""() => {
      if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(document.body, {
          delimiters: [
            {left: '$$', right: '$$', display: true},
            {left: '$', right: '$', display: false}
          ],
          throwOnError: false
        });
      }
    }""")
    await page.wait_for_timeout(1200)

    # Header and Footer templates
    header_html = f'''
    <div style="font-size: 7.5pt; color: #94a3b8; font-family: 'Inter', sans-serif; width: 100%; display: flex; justify-content: space-between; padding: 0 20mm;">
      <span>AutogenOS Research Publication &bull; Meet Shah</span>
      <span>{paper_title[:45]}...</span>
    </div>
    '''
    footer_html = '''
    <div style="font-size: 7.5pt; color: #94a3b8; font-family: 'Inter', sans-serif; width: 100%; display: flex; justify-content: space-between; padding: 0 20mm;">
      <span>AutogenOS Framework v0.1.0</span>
      <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
    </div>
    '''

    pdf_bytes = await page.pdf(
        format="A4",
        print_background=True,
        display_header_footer=True,
        header_template=header_html,
        footer_template=footer_html,
        margin={
            "top": "22mm",
            "bottom": "24mm",
            "left": "20mm",
            "right": "20mm"
        }
    )
    await page.close()

    with open(output_pdf_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"Generated: {output_pdf_path} ({len(pdf_bytes):,} bytes)")

async def main():
    os.makedirs(DOCS_PAPERS_DIR, exist_ok=True)

    papers = [
        ("00_master_architecture_blueprint.md", "00_autogenos_master_blueprint.pdf", "AUTOGEN-00-BLUEPRINT"),
        ("01_rsi_agent_broad_deep_exploration.md", "01_rsi_agent_broad_deep_exploration.pdf", "AUTOGEN-01-RSI"),
        ("02_eliminating_the_mcp_tax_tool_attention.md", "02_eliminating_the_mcp_tax_tool_attention.pdf", "AUTOGEN-02-ATTN"),
        ("03_struct_agent_deterministic_causal_evidence.md", "03_struct_agent_deterministic_causal_evidence.pdf", "AUTOGEN-03-STRUCT"),
        ("04_echopath_ui_evol_execution_replay.md", "04_echopath_ui_evol_execution_replay.pdf", "AUTOGEN-04-ECHO"),
        ("05_carryon_object_oriented_context_compaction.md", "05_carryon_object_oriented_context_compaction.pdf", "AUTOGEN-05-CARRY")
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for md_file, pdf_name, paper_id in papers:
            md_path = os.path.join(PAPERS_DIR, md_file)
            if not os.path.exists(md_path):
                print(f"Skipping {md_file}: not found")
                continue

            html_content, paper_title = process_markdown_file(md_path, paper_id)

            # Output paths: both in papers/ and docs/papers/
            root_pdf_path = os.path.join(PAPERS_DIR, pdf_name)
            docs_pdf_path = os.path.join(DOCS_PAPERS_DIR, pdf_name)

            await generate_pdf(browser, html_content, docs_pdf_path, paper_title)
            
            # Also copy to root papers/ directory
            with open(docs_pdf_path, "rb") as src, open(root_pdf_path, "wb") as dst:
                dst.write(src.read())

        await browser.close()

    print("\nAll academic research PDFs compiled successfully!")

if __name__ == "__main__":
    asyncio.run(main())
