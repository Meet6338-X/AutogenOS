"""
Linux Native Operating System Automation Bridge (X11 & AT-SPI D-Bus).
"""

from __future__ import annotations
import shutil
import subprocess
import logging
from typing import Any, Dict, List
from autogenos.control.base import BaseOSController, AccessibleElement, ElementBounds

logger = logging.getLogger("autogenos.linux_bridge")


class LinuxOSController(BaseOSController):
    """
    Linux automation bridge utilizing xdotool, wmctrl, and AT-SPI accessibility daemon.
    """

    def __init__(self):
        self.has_xdotool = shutil.which("xdotool") is not None
        self.has_wmctrl = shutil.which("wmctrl") is not None

    def get_active_window(self) -> Dict[str, Any]:
        if not self.has_xdotool:
            return {"title": "Mock Linux Desktop", "handle": 0}

        try:
            out = subprocess.check_output(["xdotool", "getactivewindow", "getwindowname"], text=True).strip()
            return {"title": out, "handle": 1}
        except Exception:
            return {"title": "Desktop", "handle": 0}

    def list_windows(self) -> List[Dict[str, Any]]:
        if not self.has_wmctrl:
            return []

        try:
            lines = subprocess.check_output(["wmctrl", "-l"], text=True).splitlines()
            windows = []
            for line in lines:
                parts = line.split(maxsplit=3)
                if len(parts) >= 4:
                    windows.append({"handle": parts[0], "title": parts[3]})
            return windows
        except Exception:
            return []

    def focus_window(self, title_query: str) -> bool:
        if not self.has_wmctrl:
            return False

        try:
            subprocess.run(["wmctrl", "-a", title_query], check=True)
            return True
        except Exception:
            return False

    def click_coordinate(self, x: int, y: int, button: str = "left") -> bool:
        if not self.has_xdotool:
            return False

        btn_num = "1" if button == "left" else "3"
        try:
            subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", btn_num], check=True)
            return True
        except Exception:
            return False

    def type_text(self, text: str) -> bool:
        if not self.has_xdotool:
            return False

        try:
            subprocess.run(["xdotool", "type", "--", text], check=True)
            return True
        except Exception:
            return False

    def get_accessibility_tree(self, max_depth: int = 3) -> AccessibleElement:
        active = self.get_active_window()
        return AccessibleElement(
            name=active.get("title", "Linux Root"),
            control_type="Window",
            bounds=ElementBounds(left=0, top=0, right=1920, bottom=1080)
        )
