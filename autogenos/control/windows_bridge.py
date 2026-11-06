"""
Windows Native Operating System Automation Bridge.
Leverages Win32 APIs and UI Automation (UIA) for robust desktop control and introspection.
"""

from __future__ import annotations
import sys
import time
import ctypes
try:
    import ctypes.wintypes
except ImportError:
    pass
import logging
from typing import Any, Dict, List, Optional
from autogenos.control.base import BaseOSController, AccessibleElement, ElementBounds

logger = logging.getLogger("autogenos.windows_bridge")


class WindowsOSController(BaseOSController):
    """
    Windows implementation of BaseOSController using ctypes Win32 user32 APIs.
    """

    def __init__(self):
        self.is_windows = sys.platform.startswith("win")
        if not self.is_windows:
            logger.warning("WindowsOSController instantiated on non-Windows host.")

    def get_active_window(self) -> Dict[str, Any]:
        if not self.is_windows:
            return {"handle": 0, "title": "Mock Windows Host"}

        user32 = ctypes.windll.user32
        hwnd = user32.GetForegroundWindow()
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)

        rect = ctypes.wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(rect))

        return {
            "handle": hwnd,
            "title": buff.value,
            "bounds": {"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom}
        }

    def list_windows(self) -> List[Dict[str, Any]]:
        if not self.is_windows:
            return []

        user32 = ctypes.windll.user32
        results = []

        def enum_handler(hwnd, _):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    title = buff.value.strip()
                    if title:
                        rect = ctypes.wintypes.RECT()
                        user32.GetWindowRect(hwnd, ctypes.byref(rect))
                        results.append({
                            "handle": hwnd,
                            "title": title,
                            "bounds": {"left": rect.left, "top": rect.top, "right": rect.right, "bottom": rect.bottom}
                        })
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        user32.EnumWindows(WNDENUMPROC(enum_handler), 0)
        return results

    def focus_window(self, title_query: str) -> bool:
        if not self.is_windows:
            return False

        windows = self.list_windows()
        q = title_query.lower()
        target_hwnd = None
        for w in windows:
            if q in w["title"].lower():
                target_hwnd = w["handle"]
                break

        if not target_hwnd:
            return False

        user32 = ctypes.windll.user32
        SW_RESTORE = 9
        user32.ShowWindow(target_hwnd, SW_RESTORE)
        user32.SetForegroundWindow(target_hwnd)
        return True

    def click_coordinate(self, x: int, y: int, button: str = "left") -> bool:
        if not self.is_windows:
            return False

        user32 = ctypes.windll.user32
        user32.SetCursorPos(x, y)
        time.sleep(0.05)

        MOUSEEVENTF_LEFTDOWN = 0x0002
        MOUSEEVENTF_LEFTUP = 0x0004
        MOUSEEVENTF_RIGHTDOWN = 0x0008
        MOUSEEVENTF_RIGHTUP = 0x0010

        if button == "left":
            user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        elif button == "right":
            user32.mouse_event(MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            user32.mouse_event(MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        return True

    def type_text(self, text: str) -> bool:
        if not self.is_windows:
            return False

        user32 = ctypes.windll.user32
        KEYEVENTF_UNICODE = 0x0004
        KEYEVENTF_KEYUP = 0x0002

        for char in text:
            code = ord(char)
            # Press char
            user32.keybd_event(0, code, KEYEVENTF_UNICODE, 0)
            # Release char
            user32.keybd_event(0, code, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0)
            time.sleep(0.01)
        return True

    def get_accessibility_tree(self, max_depth: int = 3) -> AccessibleElement:
        active = self.get_active_window()
        bounds = active.get("bounds", {"left": 0, "top": 0, "right": 1920, "bottom": 1080})
        
        root = AccessibleElement(
            name=active.get("title", "Root Desktop"),
            control_type="Window",
            bounds=ElementBounds(**bounds),
            automation_id=str(active.get("handle", "0"))
        )
        return root
