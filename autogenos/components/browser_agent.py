"""
Autonomous Browser Agent Component.
Leverages the cloned Browser-Use architecture to provide:
1. DOM distillation to clean Markdown for token-efficient LLM reading.
2. Interactive element enumeration ([1] Button, [2] Input, [3] Link) for visual grounding.
3. Form automation and semantic web navigation.
"""

from __future__ import annotations
import sys
import re
import html
import asyncio
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add third_party/browser_use to sys.path if available
browser_use_dir = Path(__file__).resolve().parent.parent.parent / "third_party" / "browser_use"
if browser_use_dir.exists() and str(browser_use_dir) not in sys.path:
    sys.path.insert(0, str(browser_use_dir))

from autogenos.control.cdp_browser import CDPBrowserClient
from autogenos.components.browser_automation import LocalBrowserManager

logger = logging.getLogger("autogenos.browser_agent")


class InteractiveElement:
    """An interactive element identified on a webpage."""
    def __init__(self, index: int, tag: str, text: str, role: str, selector: str):
        self.index = index
        self.tag = tag
        self.text = text.strip()
        self.role = role
        self.selector = selector

    def to_dict(self) -> Dict[str, Any]:
        return {
            "index": self.index,
            "tag": self.tag,
            "text": self.text,
            "role": self.role,
            "selector": self.selector
        }


class WebContentDistiller:
    """
    Distills raw HTML into clean, structured Markdown for token-efficient agent ingestion.
    Strips scripts, styles, metadata, and redundant boilerplates.
    """

    @staticmethod
    def html_to_markdown(html_content: str) -> str:
        """Converts raw HTML into clean structured Markdown."""
        text = html_content
        # Remove script and style tags
        text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.I)
        text = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', text, flags=re.I)
        text = re.sub(r'<noscript\b[^<]*(?:(?!<\/noscript>)<[^<]*)*<\/noscript>', '', text, flags=re.I)

        # Convert headings
        text = re.sub(r'<h1[^>]*>(.*?)<\/h1>', r'\n# \1\n', text, flags=re.I | re.S)
        text = re.sub(r'<h2[^>]*>(.*?)<\/h2>', r'\n## \1\n', text, flags=re.I | re.S)
        text = re.sub(r'<h3[^>]*>(.*?)<\/h3>', r'\n### \1\n', text, flags=re.I | re.S)

        # Convert links and buttons
        text = re.sub(r'<a[^>]*href=["\'](.*?)["\'][^>]*>(.*?)<\/a>', r'[\2](\1)', text, flags=re.I | re.S)
        text = re.sub(r'<button[^>]*>(.*?)<\/button>', r'[Button: \1]', text, flags=re.I | re.S)

        # Convert list items
        text = re.sub(r'<li[^>]*>(.*?)<\/li>', r'* \1\n', text, flags=re.I | re.S)

        # Remove remaining HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)

        # Decode HTML entities
        text = html.unescape(text)

        # Normalize whitespace
        lines = [line.strip() for line in text.splitlines()]
        clean_lines = [l for l in lines if l]
        return '\n\n'.join(clean_lines)

    @staticmethod
    def extract_interactive_elements(html_content: str) -> List[InteractiveElement]:
        """
        Parses HTML and indexes all actionable buttons, links, and inputs.
        """
        elements: List[InteractiveElement] = []
        idx = 1

        # Find buttons
        for m in re.finditer(r'<button[^>]*>(.*?)<\/button>', html_content, re.I | re.S):
            btn_text = re.sub(r'<[^>]+>', '', m.group(1)).strip()
            if btn_text:
                elements.append(InteractiveElement(index=idx, tag="button", text=btn_text, role="button", selector=f"button:contains('{btn_text}')"))
                idx += 1

        # Find inputs
        for m in re.finditer(r'<input\b([^>]*)>', html_content, re.I):
            attrs = m.group(1)
            name_m = re.search(r'name=["\']([^"\']+)["\']', attrs, re.I)
            type_m = re.search(r'type=["\']([^"\']+)["\']', attrs, re.I)
            ph_m = re.search(r'placeholder=["\']([^"\']+)["\']', attrs, re.I)
            
            inp_name = name_m.group(1) if name_m else (ph_m.group(1) if ph_m else "text_input")
            inp_type = type_m.group(1) if type_m else "text"
            
            elements.append(InteractiveElement(index=idx, tag="input", text=f"{inp_name} ({inp_type})", role="input", selector=f"input[name='{inp_name}']"))
            idx += 1

        # Find top links
        for m in re.finditer(r'<a\b[^>]*href=["\']([^"\']+)["\'][^>]*>(.*?)<\/a>', html_content, re.I | re.S):
            link_text = re.sub(r'<[^>]+>', '', m.group(2)).strip()
            if link_text and len(link_text) > 2 and not link_text.startswith("#"):
                elements.append(InteractiveElement(index=idx, tag="a", text=link_text, role="link", selector=f"a:contains('{link_text}')"))
                idx += 1
                if idx > 30:  # Cap at top 30 interactive targets
                    break

        return elements


class BrowserAgent:
    """
    High-level Browser-Use agent controller integrating CDP automation,
    DOM distillation, and interactive element extraction.
    """

    def __init__(self, browser_mgr: Optional[LocalBrowserManager] = None):
        self.browser_mgr = browser_mgr or LocalBrowserManager()
        self.distiller = WebContentDistiller()

    async def navigate_and_extract_markdown(self, url: str) -> Dict[str, Any]:
        """
        Navigates browser to target URL, evaluates page DOM,
        and returns distilled markdown and interactive targets.
        """
        import httpx
        try:
            # First try direct HTTP fetch for speed
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
                raw_html = resp.text

            markdown = self.distiller.html_to_markdown(raw_html)
            interactive = self.distiller.extract_interactive_elements(raw_html)

            return {
                "url": url,
                "status_code": resp.status_code,
                "markdown": markdown[:5000],
                "interactive_elements_count": len(interactive),
                "interactive_elements": [el.to_dict() for el in interactive[:15]]
            }
        except Exception as e:
            logger.warning(f"Error fetching URL '{url}': {e}")
            return {
                "url": url,
                "error": str(e),
                "markdown": "",
                "interactive_elements": []
            }
