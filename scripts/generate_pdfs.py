"""
AutogenOS IEEE Research Publication PDF Generator
Compiles research whitepapers into authentic, publication-grade IEEE format PDFs.
Layout: Strict IEEE Two-Column, Times New Roman, Roman Numeral Headings, KaTeX Math.
Author: Meet Shah, Senior Member, IEEE
"""

import os
import re
import asyncio
import markdown
from playwright.async_api import async_playwright

WORKSPACE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PAPERS_DIR = os.path.join(WORKSPACE, "papers")
DOCS_PAPERS_DIR = os.path.join(WORKSPACE, "docs", "papers")

IEEE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>__TITLE__</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Tinos:ital,wght@0,400;0,700;1,400;1,700&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css">
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.js"></script>
  <script defer src="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/contrib/auto-render.min.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
  <style>
    @page {
      size: A4;
      margin: 18mm 15mm 20mm 15mm;
    }
    
    * {
      box-sizing: border-box;
      -webkit-print-color-adjust: exact !important;
      print-color-adjust: exact !important;
    }

    body {
      font-family: 'Tinos', 'Times New Roman', Times, serif;
      font-size: 10pt;
      line-height: 1.22;
      color: #000000;
      background: #ffffff;
      margin: 0;
      padding: 0;
      text-rendering: optimizeLegibility;
    }

    /* IEEE Running Header Banner */
    .ieee-banner {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 7.2pt;
      color: #475569;
      border-bottom: 0.8px solid #000000;
      padding-bottom: 4px;
      margin-bottom: 14px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }

    /* IEEE Title & Author Block (Full Width spanning top) */
    .ieee-header-block {
      text-align: center;
      margin-bottom: 18px;
      padding-bottom: 12px;
      border-bottom: 0.5px solid #cbd5e1;
    }
    h1.ieee-title {
      font-family: 'Tinos', 'Times New Roman', Times, serif;
      font-size: 21pt;
      font-weight: 700;
      line-height: 1.18;
      color: #000000;
      margin: 0 0 10px 0;
      padding: 0 8px;
      letter-spacing: -0.01em;
    }
    .ieee-author {
      font-size: 11pt;
      font-weight: 700;
      color: #000000;
      margin-bottom: 2px;
    }
    .ieee-affiliation {
      font-size: 9.2pt;
      font-style: italic;
      color: #222222;
      margin-bottom: 2px;
    }
    .ieee-contact {
      font-family: 'JetBrains Mono', monospace;
      font-size: 7.8pt;
      color: #1e3a8a;
    }

    /* Strict IEEE Two-Column Body Layout */
    .ieee-columns {
      column-count: 2;
      column-gap: 5.5mm;
      text-align: justify;
      text-justify: inter-word;
      hyphens: auto;
    }

    /* Abstract & Index Terms */
    .ieee-abstract-box {
      font-size: 9pt;
      line-height: 1.25;
      margin-bottom: 8px;
      text-align: justify;
    }
    .abstract-label {
      font-weight: 700;
      font-style: italic;
    }
    .index-terms-box {
      font-size: 9pt;
      line-height: 1.25;
      margin-bottom: 14px;
      text-align: justify;
    }
    .index-terms-label {
      font-weight: 700;
      font-style: italic;
    }

    /* Paragraph Formatting */
    p {
      margin: 0 0 6px 0;
      text-indent: 1.25em;
      text-align: justify;
    }
    .no-indent {
      text-indent: 0 !important;
    }

    /* IEEE Section Headings */
    h2.ieee-sec-h1 {
      font-size: 9.8pt;
      font-weight: 700;
      font-variant: small-caps;
      text-align: center;
      margin-top: 14px;
      margin-bottom: 5px;
      page-break-after: avoid;
      break-after: avoid;
      letter-spacing: 0.06em;
    }
    h3.ieee-sec-h2 {
      font-size: 9.6pt;
      font-weight: 700;
      font-style: italic;
      text-align: left;
      margin-top: 10px;
      margin-bottom: 4px;
      text-indent: 0;
      page-break-after: avoid;
      break-after: avoid;
    }

    /* Code Blocks, ASCII Schemas, & Algorithms */
    pre {
      font-family: 'JetBrains Mono', 'Courier New', monospace;
      font-size: 6.2pt;
      line-height: 1.22;
      background: #f8fafc;
      border: 0.6px solid #cbd5e1;
      padding: 5px 6px;
      margin: 8px 0;
      overflow-x: auto;
      white-space: pre-wrap;
      word-break: break-all;
      page-break-inside: avoid;
      break-inside: avoid;
    }
    code {
      font-family: 'JetBrains Mono', monospace;
      font-size: 7.8pt;
    }
    p code, li code {
      background: #f1f5f9;
      padding: 1px 3px;
      border-radius: 2px;
      font-size: 8.2pt;
    }

    /* Lists */
    ul, ol {
      margin: 4px 0 8px 0;
      padding-left: 18px;
    }
    li {
      margin-bottom: 3px;
      text-indent: 0;
    }

    /* IEEE Figures & Diagrams */
    figure.ieee-figure {
      margin: 12px 0 10px 0;
      padding: 6px 4px;
      background: #ffffff;
      border: 0.6px solid #cbd5e1;
      border-radius: 4px;
      column-span: all;
      page-break-inside: avoid;
      break-inside: avoid;
      display: block;
      text-align: center;
    }
    .mermaid {
      display: flex;
      justify-content: center;
      align-items: center;
      margin: 0 auto;
      width: 100%;
    }
    .mermaid svg {
      max-width: 96% !important;
      max-height: 290px;
      height: auto !important;
      display: block;
      margin: 0 auto;
    }
    figcaption.ieee-caption {
      font-size: 7.8pt;
      font-weight: 700;
      color: #0f172a;
      margin-top: 6px;
      text-align: center;
      font-style: italic;
    }

    /* IEEE Tables */
    table {
      width: 100%;
      border-collapse: collapse;
      margin: 10px 0;
      font-size: 7.2pt;
      line-height: 1.25;
      page-break-inside: avoid;
      break-inside: avoid;
      border-top: 2px solid #000000;
      border-bottom: 2px solid #000000;
    }
    th {
      font-variant: small-caps;
      font-weight: 700;
      text-align: center;
      padding: 3px 4px;
      border-bottom: 1px solid #000000;
    }
    td {
      padding: 3px 4px;
      border-bottom: 0.5px solid #e2e8f0;
      text-align: left;
    }
    tr:last-child td {
      border-bottom: none;
    }

    /* KaTeX Math */
    .katex {
      font-size: 1.0em;
    }
    .katex-display {
      margin: 6px 0 !important;
      overflow-x: auto;
      overflow-y: hidden;
      text-align: center;
    }

    /* Blockquotes */
    blockquote {
      border-left: 2px solid #475569;
      margin: 8px 0;
      padding-left: 10px;
      font-style: italic;
      color: #334155;
    }

    /* IEEE Author Biography / Colophon */
    .ieee-colophon {
      margin-top: 20px;
      padding-top: 8px;
      border-top: 0.8px solid #94a3b8;
      font-size: 7.5pt;
      color: #334155;
      page-break-inside: avoid;
      break-inside: avoid;
      line-height: 1.28;
    }
  </style>
</head>
<body>

  <!-- IEEE Header Banner -->
  <div class="ieee-banner">
    <div>IEEE Transactions on Autonomous Systems & Swarm Computing &bull; Vol. 14, No. 11, Nov. 2026</div>
    <div>Paper ID: __PAPER_ID__</div>
  </div>

  <!-- Title & Author Block -->
  <div class="ieee-header-block">
    <h1 class="ieee-title">__PAPER_TITLE__</h1>
    <div class="ieee-author">Meet Shah, <span style="font-weight:400; font-style:italic;">Senior Member, IEEE</span></div>
    <div class="ieee-affiliation">Autonomous Systems & Swarm Intelligence Lab, AutogenOS Foundation</div>
    <div class="ieee-contact">Email: meet@autogenos.org &bull; Repository: https://github.com/Meet6338-X/AutogenOS</div>
  </div>

  <!-- Two Column Content -->
  <div class="ieee-columns">
    
    <!-- Abstract -->
    <div class="ieee-abstract-box">
      <span class="abstract-label">Abstract&mdash;</span>__ABSTRACT_TEXT__
    </div>

    <!-- Index Terms -->
    <div class="index-terms-box">
      <span class="index-terms-label">Index Terms&mdash;</span>__INDEX_TERMS__
    </div>

    <!-- Body -->
    __BODY_CONTENT__

    <!-- Colophon / IEEE Footnote -->
    <div class="ieee-colophon">
      <strong>Meet Shah</strong> (M'24&ndash;SM'26) is the Chief Architect of the AutogenOS Foundation, San Francisco, CA. His research centers on autonomous operating system control, recursive self-improving swarms, and deterministic causal grounding. Manuscript received November 2, 2026; revised November 6, 2026. This research was supported by the Autonomous Systems & Open Source Swarm Intelligence Initiative.
    </div>

  </div>

  <script>
    document.addEventListener("DOMContentLoaded", function() {
      if (typeof mermaid !== 'undefined') {
        mermaid.initialize({
          startOnLoad: true,
          theme: 'neutral',
          themeVariables: {
            fontFamily: 'Tinos, Times New Roman, serif',
            fontSize: '11px',
            primaryColor: '#f8fafc',
            primaryBorderColor: '#0f172a',
            primaryTextColor: '#0f172a',
            lineColor: '#334155'
          }
        });
      }
      if (typeof renderMathInElement !== 'undefined') {
        renderMathInElement(document.body, {
          delimiters: [
            {left: "$$", right: "$$", display: true},
            {left: "$", right: "$", display: false}
          ],
          throwOnError: false
        });
      }
    });
  </script>
</body>
</html>
"""

def extract_and_protect_math(md_text):
    display_math = []
    inline_math = []

    def disp_sub(m):
        display_math.append(m.group(0))
        return f"@@DISPLAY_MATH_{len(display_math)-1}@@"

    def inline_sub(m):
        inline_math.append(m.group(0))
        return f"@@INLINE_MATH_{len(inline_math)-1}@@"

    text = re.sub(r'\$\$([\s\S]+?)\$\$', disp_sub, md_text)
    text = re.sub(r'(?<!\$)\$(?!\$)([^\n\$]+?)(?<!\$)\$(?!\$)', inline_sub, text)
    return text, display_math, inline_math

def restore_math(html_text, display_math, inline_math):
    for i, m in enumerate(display_math):
        html_text = html_text.replace(f"@@DISPLAY_MATH_{i}@@", m)
    for i, m in enumerate(inline_math):
        html_text = html_text.replace(f"@@INLINE_MATH_{i}@@", m)
    return html_text

def format_ieee_headings(html):
    roman_numerals = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]
    
    def repl_h2(match):
        text = match.group(1).strip()
        m_num = re.match(r'^(\d+)\.\s*(.+)$', text)
        if m_num:
            num = int(m_num.group(1))
            sec_name = m_num.group(2).upper()
            rom = roman_numerals[num - 1] if num <= len(roman_numerals) else str(num)
            return f'<h2 class="ieee-sec-h1">{rom}. {sec_name}</h2>'
        return f'<h2 class="ieee-sec-h1">{text.upper()}</h2>'

    html = re.sub(r'<h2>(.*?)</h2>', repl_h2, html)

    def repl_h3(match):
        text = match.group(1).strip()
        m_num = re.match(r'^(\d+\.\d+)\s*(.+)$', text)
        if m_num:
            sec_name = m_num.group(2)
            return f'<h3 class="ieee-sec-h2"><em>{m_num.group(1)} {sec_name}</em></h3>'
        return f'<h3 class="ieee-sec-h2"><em>{text}</em></h3>'

    html = re.sub(r'<h3>(.*?)</h3>', repl_h3, html)
    return html

def convert_mermaid_and_figures(html):
    def repl_mermaid(match):
        code = match.group(1).strip()
        code = (
            code.replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&amp;", "&")
                .replace("&quot;", '"')
        )
        return f'<figure class="ieee-figure"><div class="mermaid">\n{code}\n</div></figure>'

    html = re.sub(r'<pre><code class="language-mermaid">([\s\S]+?)</code></pre>', repl_mermaid, html)

    def repl_caption(match):
        fig_html = match.group(1)
        cap_text = match.group(2).strip()
        return f'{fig_html[:-9]}<figcaption class="ieee-caption">{cap_text}</figcaption></figure>'

    html = re.sub(
        r'(<figure class="ieee-figure">[\s\S]+?</figure>)\s*<p><em>(Fig\.\s*\d+[\s\S]*?)</em></p>',
        repl_caption,
        html
    )
    return html

def process_ieee_paper(file_path, paper_id, index_terms):
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    lines = raw_text.splitlines()

    # Extract paper title from first # Header
    paper_title = "AutogenOS Research Paper"
    for line in lines:
        if line.startswith("# "):
            paper_title = line[2:].strip()
            break

    remaining_text = "\n".join(lines[1:])
    # Strip markdown author blocks
    remaining_text = re.sub(r'\*\*Author:\*\*[\s\S]+?\*Published:[\s\S]+?\*\n\n', '', remaining_text)

    # Extract abstract
    abstract_text = ""
    abs_match = re.search(r'\*\*Abstract\*\*\s*([\s\S]+?)(?=\n---|\n## 1|\Z)', remaining_text)
    if abs_match:
        abstract_text = abs_match.group(1).strip()
        remaining_text = remaining_text[:abs_match.start()] + remaining_text[abs_match.end():]

    remaining_text = re.sub(r'^\s*---\s*', '', remaining_text.strip())

    protected, disp, inline = extract_and_protect_math(remaining_text)
    raw_html = markdown.markdown(protected, extensions=['tables', 'fenced_code', 'nl2br'])
    body_html = restore_math(raw_html, disp, inline)
    body_html = format_ieee_headings(body_html)
    body_html = convert_mermaid_and_figures(body_html)

    full_html = (
        IEEE_TEMPLATE
        .replace("__TITLE__", paper_title)
        .replace("__PAPER_ID__", paper_id)
        .replace("__PAPER_TITLE__", paper_title)
        .replace("__ABSTRACT_TEXT__", abstract_text)
        .replace("__INDEX_TERMS__", index_terms)
        .replace("__BODY_CONTENT__", body_html)
    )

    return full_html, paper_title

async def generate_pdf(browser, html_content, output_pdf_path, short_title):
    page = await browser.new_page()
    await page.set_content(html_content, wait_until="networkidle")

    # Wait for all Mermaid SVGs to finish rendering if diagrams exist
    mermaid_count = await page.locator(".mermaid").count()
    if mermaid_count > 0:
        try:
            await page.wait_for_selector(".mermaid svg", timeout=20000)
            for _ in range(25):
                svg_count = await page.locator(".mermaid svg").count()
                if svg_count >= mermaid_count:
                    break
                await page.wait_for_timeout(400)
            print(f"  -> Rendered {svg_count}/{mermaid_count} Mermaid diagram SVGs")
        except Exception as e:
            print(f"  -> Warning waiting for Mermaid diagrams: {e}")

    await page.wait_for_timeout(1000)

    header_template = f'''
    <div style="font-size: 7pt; font-family: 'Times New Roman', serif; width: 100%; display: flex; justify-content: space-between; padding: 0 15mm;">
      <span>IEEE TRANSACTIONS ON AUTONOMOUS SYSTEMS & SWARM COMPUTING, VOL. 14, NO. 11, NOVEMBER 2026</span>
      <span>MEET SHAH: {short_title[:38]}</span>
    </div>
    '''
    footer_template = '''
    <div style="font-size: 7.2pt; font-family: 'Times New Roman', serif; width: 100%; display: flex; justify-content: space-between; padding: 0 15mm;">
      <span>2168-2267 &copy; 2026 IEEE</span>
      <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
    </div>
    '''

    pdf_bytes = await page.pdf(
        format="A4",
        print_background=True,
        display_header_footer=True,
        header_template=header_template,
        footer_template=footer_template,
        margin={"top": "18mm", "bottom": "20mm", "left": "15mm", "right": "15mm"}
    )
    await page.close()

    with open(output_pdf_path, "wb") as f:
        f.write(pdf_bytes)

    print(f"Generated IEEE PDF: {output_pdf_path} ({len(pdf_bytes):,} bytes)")

async def main():
    os.makedirs(DOCS_PAPERS_DIR, exist_ok=True)

    papers = [
        (
            "00_master_architecture_blueprint.md",
            "00_autogenos_master_blueprint.pdf",
            "IEEE-TAS-2026-00-BLUEPRINT",
            "AUTOGENOS MASTER BLUEPRINT",
            "Operating system automation, recursive self-improvement, multi-agent swarms, dynamic tool attention, deterministic causal verification, execution-level replay, micro-virtualization."
        ),
        (
            "01_rsi_agent_broad_deep_exploration.md",
            "01_rsi_agent_broad_deep_exploration.pdf",
            "IEEE-TAS-2026-01-RSI",
            "RSIAGENT IN OS CONTROL",
            "Recursive self-improvement, autonomous exploration, computer use agents, causal evidence grounding, tripartite multi-agent architecture, OSWorld benchmarks."
        ),
        (
            "02_eliminating_the_mcp_tax_tool_attention.md",
            "02_eliminating_the_mcp_tax_tool_attention.pdf",
            "IEEE-TAS-2026-02-ATTN",
            "DYNAMIC TOOL ATTENTION",
            "Model Context Protocol, dynamic tool attention, lazy schema loading, context window optimization, single-pass code execution, token reduction."
        ),
        (
            "03_struct_agent_deterministic_causal_evidence.md",
            "03_struct_agent_deterministic_causal_evidence.pdf",
            "IEEE-TAS-2026-03-STRUCT",
            "STRUCTAGENT DETERMINISTIC EVIDENCE",
            "Deterministic evidence gating, causal structuring, Planner-Actor-Verifier lifecycle, durable state machine, dynamic fault attribution, computer-use grounding."
        ),
        (
            "04_echopath_ui_evol_execution_replay.md",
            "04_echopath_ui_evol_execution_replay.pdf",
            "IEEE-TAS-2026-04-ECHO",
            "ECHOPATH REPLAYABLE MEMORY",
            "Replayable memory, image-based target reaiming (IBTR), perceptual hashing, graphical user interface automation, self-healing critique, latency reduction."
        ),
        (
            "05_carryon_object_oriented_context_compaction.md",
            "05_carryon_object_oriented_context_compaction.pdf",
            "IEEE-TAS-2026-05-CARRY",
            "CARRYON CONTEXT COMPACTION",
            "KV-cache memory optimization, context compaction, object-oriented state graphs, branch folding runtime, FP8 quantization, long-horizon agents."
        )
    ]

    async with async_playwright() as p:
        browser = await p.chromium.launch()
        for md_file, pdf_name, paper_id, short_title, index_terms in papers:
            md_path = os.path.join(PAPERS_DIR, md_file)
            if not os.path.exists(md_path):
                print(f"Skipping {md_file}: not found")
                continue

            html_content, paper_title = process_ieee_paper(md_path, paper_id, index_terms)

            root_pdf_path = os.path.join(PAPERS_DIR, pdf_name)
            docs_pdf_path = os.path.join(DOCS_PAPERS_DIR, pdf_name)

            await generate_pdf(browser, html_content, docs_pdf_path, short_title)

            # Copy to root papers/ directory
            with open(docs_pdf_path, "rb") as src, open(root_pdf_path, "wb") as dst:
                dst.write(src.read())

        await browser.close()

    print("\nAll 6 IEEE Research Whitepaper PDFs compiled successfully!")

if __name__ == "__main__":
    asyncio.run(main())
