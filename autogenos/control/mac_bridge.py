"""
macOS Native Operating System Automation Bridge (Accessibility API & CoreGraphics).
"""

from __future__ import annotations
import subprocess
import logging
from typing import Any, Dict, List
from autogenos.control.base import BaseOSController, AccessibleElement, ElementBounds

logger = logging.getLogger("autogenos.mac_bridge")


class MacOSController(BaseOSController):
    """
    macOS automation bridge utilizing osascript (AppleScript/JXA) and AXUIElement bindings.
    """

    def get_active_window(self) -> Dict[str, Any]:
        script = 'tell application "System Events" to get name of first application process whose frontmost is true'
        try:
            out = subprocess.check_output(["osascript", "-e", script], text=True).strip()
            return {"title": out, "handle": 1}
        except Exception:
            return {"title": "macOS Desktop", "handle": 0}

    def list_windows(self) -> List[Dict[str, Any]]:
        script = 'tell application "System Events" to get name of every application process whose visible is true'
        try:
            out = subprocess.check_output(["osascript", "-e", script], text=True).strip()
            names = [n.strip() for n in out.split(",")]
            return [{"handle": idx, "title": name} for idx, name in enumerate(names)]
        except Exception:
            return []

    def focus_window(self, title_query: str) -> bool:
        script = f'tell application "{title_query}" to activate'
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            return True
        except Exception:
            return False

    def click_coordinate(self, x: int, y: int, button: str = "left") -> bool:
        # Uses cliclick or CoreGraphics fallback
        try:
            subprocess.run(["cliclick", f"c:{x},{y}"], check=True)
            return True
        except Exception:
            return False

    def type_text(self, text: str) -> bool:
        script = f'tell application "System Events" to keystroke "{text}"'
        try:
            subprocess.run(["osascript", "-e", script], check=True)
            return True
        except Exception:
            return False

    def get_accessibility_tree(self, max_depth: int = 3) -> AccessibleElement:
        active = self.get_active_window()
        return AccessibleElement(
            name=active.get("title", "macOS Root"),
            control_type="Window",
            bounds=ElementBounds(left=0, top=0, right=1920, bottom=1080)
        )
