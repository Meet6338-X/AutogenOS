import os

def update():
    index_path = os.path.join("docs", "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        html = f.read()

    # Update hero CTA
    old_hero_cta = '<a href="#papers" class="btn btn-secondary btn-pill">Read Academic Papers (5)</a>'
    new_hero_cta = '<a href="#papers" class="btn btn-secondary btn-pill">Read Whitepapers & PDFs (6)</a>'
    if old_hero_cta in html:
        html = html.replace(old_hero_cta, new_hero_cta, 1)

    start_tag = '  <!-- 5 Academic Whitepapers -->'
    end_tag = '  <!-- Developer Studio Playground -->'
    assert start_tag in html, "Start tag not found in docs/index.html"
    assert end_tag in html, "End tag not found in docs/index.html"

    start_idx = html.index(start_tag)
    end_idx = html.index(end_tag)

    new_section = '''  <!-- Academic Whitepapers & Research Publications -->
  <section class="section-wrapper" id="papers">
    <div class="container">
      <div class="section-head">
        <div class="section-eyebrow">Project III • Academic Foundations</div>
        <h2 class="section-title">Peer-Reviewed Research Whitepapers & PDFs</h2>
        <p class="section-description">
          Authored by <strong>Meet Shah</strong> • Autonomous Systems & Swarm Intelligence Lab, AutogenOS Foundation.<br>
          Theoretical architectures, mathematical proofs, and empirical benchmarks proving autonomous recursive self-improvement in operating system control swarms.
        </p>
      </div>

      <!-- Featured Master Architecture Blueprint -->
      <div class="featured-paper-card">
        <div class="featured-paper-header">
          <div class="featured-badges">
            <span class="badge-master">MASTER BLUEPRINT</span>
            <span class="paper-meta-badge">12 PAGES A4</span>
            <span class="paper-meta-badge">SYSTEM SPEC V1.0</span>
          </div>
          <div class="paper-author-row" style="margin-bottom:0;">
            <span class="paper-author-avatar">M</span>
            <span>Author: <strong class="paper-author-name">Meet Shah</strong> (Chief Architect)</span>
          </div>
        </div>

        <div>
          <h3 class="paper-heading" style="font-size:1.45rem; margin-bottom:0.6rem;">
            AutogenOS: Master Architecture Blueprint & Theoretical Foundation for a Recursive Self-Improving OS-Control Agent Swarm
          </h3>
          <p class="paper-snippet" style="margin-bottom:0.5rem;">
            The unified foundational architectural specification covering sub-500ms voice pipelines (faster-whisper + SAPI5 on loopback WebRTC), pure Chrome DevTools Protocol automation, dynamic Tool Attention cosine gating, Git worktree ephemeral sandboxing, and execution-level replayable memory graphs.
          </p>
        </div>

        <div class="paper-actions-row">
          <a href="papers/00_autogenos_master_blueprint.pdf" class="btn-paper-pdf" target="_blank" rel="noopener">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
            <span>Download Master PDF (12 Pages)</span>
          </a>
          <a href="https://github.com/Meet6338-X/AutogenOS/blob/main/papers/00_master_architecture_blueprint.md" class="btn-paper-src" target="_blank" rel="noopener">
            <span>Markdown Source</span>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
          </a>
        </div>
      </div>

      <!-- 5 Specialized Research Papers Grid -->
      <div class="papers-container">
        <!-- Paper 1 -->
        <div class="paper-card">
          <div>
            <div class="paper-tag-row">
              <span class="paper-id">PAPER 01</span>
              <span class="paper-meta-badge">6 PAGES PDF</span>
            </div>
            <div class="paper-author-row">
              <span class="paper-author-avatar">M</span>
              <span>Author: <strong class="paper-author-name">Meet Shah</strong></span>
            </div>
            <h3 class="paper-heading">RSIAgent: Recursive Self-Improvement via Broad-then-Deep Exploration</h3>
            <p class="paper-snippet">
              Tripartite multi-agent architecture (Curriculum, Actor, Verifier) formalizing autonomous UI discovery during idle compute cycles without model retraining.
            </p>
          </div>
          <div class="paper-actions-row">
            <a href="papers/01_rsi_agent_broad_deep_exploration.pdf" class="btn-paper-pdf" target="_blank" rel="noopener">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
              <span>Download PDF</span>
            </a>
            <a href="https://github.com/Meet6338-X/AutogenOS/blob/main/papers/01_rsi_agent_broad_deep_exploration.md" class="btn-paper-src" target="_blank" rel="noopener">
              <span>Source</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
          </div>
        </div>

        <!-- Paper 2 -->
        <div class="paper-card">
          <div>
            <div class="paper-tag-row">
              <span class="paper-id">PAPER 02</span>
              <span class="paper-meta-badge">4 PAGES PDF</span>
            </div>
            <div class="paper-author-row">
              <span class="paper-author-avatar">M</span>
              <span>Author: <strong class="paper-author-name">Meet Shah</strong></span>
            </div>
            <h3 class="paper-heading">Eliminating the MCP Tax: Dynamic Tool Attention & Lazy Schemas</h3>
            <p class="paper-snippet">
              Mathematical modeling of cosine semantic tool gating and single-pass Code Execution with MCP, reducing prompt token bloat by 91.6% to 95.2%.
            </p>
          </div>
          <div class="paper-actions-row">
            <a href="papers/02_eliminating_the_mcp_tax_tool_attention.pdf" class="btn-paper-pdf" target="_blank" rel="noopener">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
              <span>Download PDF</span>
            </a>
            <a href="https://github.com/Meet6338-X/AutogenOS/blob/main/papers/02_eliminating_the_mcp_tax_tool_attention.md" class="btn-paper-src" target="_blank" rel="noopener">
              <span>Source</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
          </div>
        </div>

        <!-- Paper 3 -->
        <div class="paper-card">
          <div>
            <div class="paper-tag-row">
              <span class="paper-id">PAPER 03</span>
              <span class="paper-meta-badge">4 PAGES PDF</span>
            </div>
            <div class="paper-author-row">
              <span class="paper-author-avatar">M</span>
              <span>Author: <strong class="paper-author-name">Meet Shah</strong></span>
            </div>
            <h3 class="paper-heading">StructAgent & SolveBind: Deterministic Evidence Gating</h3>
            <p class="paper-snippet">
              Strict Planner-Actor-Verifier lifecycle requiring shell return codes, file hashes, and accessibility trees to eliminate generative hallucination.
            </p>
          </div>
          <div class="paper-actions-row">
            <a href="papers/03_struct_agent_deterministic_causal_evidence.pdf" class="btn-paper-pdf" target="_blank" rel="noopener">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
              <span>Download PDF</span>
            </a>
            <a href="https://github.com/Meet6338-X/AutogenOS/blob/main/papers/03_struct_agent_deterministic_causal_evidence.md" class="btn-paper-src" target="_blank" rel="noopener">
              <span>Source</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
          </div>
        </div>

        <!-- Paper 4 -->
        <div class="paper-card">
          <div>
            <div class="paper-tag-row">
              <span class="paper-id">PAPER 04</span>
              <span class="paper-meta-badge">4 PAGES PDF</span>
            </div>
            <div class="paper-author-row">
              <span class="paper-author-avatar">M</span>
              <span>Author: <strong class="paper-author-name">Meet Shah</strong></span>
            </div>
            <h3 class="paper-heading">EchoPath & UI-Evol: Execution-Level Replayable Memory</h3>
            <p class="paper-snippet">
              Image-Based Target Reaiming (IBTR) converting visual GUI paths into 12ms deterministic coordinate schemas with autonomous self-healing critique.
            </p>
          </div>
          <div class="paper-actions-row">
            <a href="papers/04_echopath_ui_evol_execution_replay.pdf" class="btn-paper-pdf" target="_blank" rel="noopener">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
              <span>Download PDF</span>
            </a>
            <a href="https://github.com/Meet6338-X/AutogenOS/blob/main/papers/04_echopath_ui_evol_execution_replay.md" class="btn-paper-src" target="_blank" rel="noopener">
              <span>Source</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
          </div>
        </div>

        <!-- Paper 5 -->
        <div class="paper-card">
          <div>
            <div class="paper-tag-row">
              <span class="paper-id">PAPER 05</span>
              <span class="paper-meta-badge">4 PAGES PDF</span>
            </div>
            <div class="paper-author-row">
              <span class="paper-author-avatar">M</span>
              <span>Author: <strong class="paper-author-name">Meet Shah</strong></span>
            </div>
            <h3 class="paper-heading">CarryOn: Object-Oriented Context Compaction & FP8 KV Caching</h3>
            <p class="paper-snippet">
              Branch folding runtime replacing linear chat histories with active state objects, cutting per-task token consumption by 54.2% and preventing OOMs.
            </p>
          </div>
          <div class="paper-actions-row">
            <a href="papers/05_carryon_object_oriented_context_compaction.pdf" class="btn-paper-pdf" target="_blank" rel="noopener">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
              <span>Download PDF</span>
            </a>
            <a href="https://github.com/Meet6338-X/AutogenOS/blob/main/papers/05_carryon_object_oriented_context_compaction.md" class="btn-paper-src" target="_blank" rel="noopener">
              <span>Source</span>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
            </a>
          </div>
        </div>
      </div>
    </div>
  </section>
'''

    updated_html = html[:start_idx] + new_section + html[end_idx:]
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(updated_html)
    print("Successfully updated docs/index.html")

if __name__ == "__main__":
    update()
