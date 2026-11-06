"""
Windows Native Operating System Automation Bridge.
Leverages UI Automation (UIA) and Win32 APIs for robust screen introspection and hardware input injection.
"""

from __future__ import annotations
import sys
import ctypes
import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger("autogenos.windows_bridge")


class UIElementNode(BaseModel):
    name: str
    class_name: str
    handle: int
    bounding_box: Dict[str, int]
    is_visible: bool
    children: List[UIElementNode] = []


class WindowsAutomationBridge:
    """Provides direct Win32 and UI Automation operations."""

    def __init__(self):
        self.is_windows = sys.platform.startswith("win")
        if not self.is_windows:
            logger.warning("WindowsAutomationBridge initialized on non-Windows platform.")

    def enumerate_top_level_windows(self) -> List[Dict[str, Any]]:
        """Enumerates visible top-level windows using Win32 EnumWindows."""
        if not self.is_windows:
            return []

        user32 = ctypes.windll.user32
        windows = []

        def enum_windows_callback(hwnd, extra):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    windows.append({
                        "handle": hwnd,
                        "title": buff.value
                    })
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        user32.EnumWindows(WNDENUMPROC(enum_windows_callback), 0)
        return windows

    def find_window_by_title(self, query: str) -> Optional[Dict[str, Any]]:
        """Finds first window containing query title substring."""
        windows = self.enumerate_top_level_windows()
        q_lower = query.lower()
        for win in windows:
            if q_lower in win["title"].lower():
                return win
        return None

    def inject_keystroke(self, hwnd: int, vk_code: int) -> bool:
        """Injects keyboard input message directly into target window handle."""
        if not self.is_windows:
            return False

        user32 = ctypes.windll.user32
        WM_KEYDOWN = 0x0100
        WM_KEYUP = 0x0101

        user32.PostMessageW(hwnd, WM_KEYDOWN, vk_code, 0)
        user32.PostMessageW(hwnd, WM_KEYUP, vk_code, 0)
        return True
