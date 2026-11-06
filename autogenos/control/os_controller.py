"""
Unified Cross-Platform OS Controller Facade.
Auto-detects host operating system (Windows, Linux, macOS) and instantiates the appropriate native bridge.
"""

from __future__ import annotations
import sys
import logging
from typing import Any, Dict, List
from autogenos.control.base import BaseOSController, AccessibleElement
from autogenos.control.windows_bridge import WindowsOSController
from autogenos.control.linux_bridge import LinuxOSController
from autogenos.control.mac_bridge import MacOSController

logger = logging.getLogger("autogenos.os_controller")


class OSController(BaseOSController):
    """
    Unified OS automation facade.
    Dispatches hardware input and accessibility queries to the host platform bridge.
    """

    def __init__(self):
        self.platform = sys.platform
        if self.platform.startswith("win"):
            self._bridge: BaseOSController = WindowsOSController()
            self.platform_name = "windows"
        elif self.platform.startswith("linux"):
            self._bridge = LinuxOSController()
            self.platform_name = "linux"
        elif self.platform.startswith("darwin"):
            self._bridge = MacOSController()
            self.platform_name = "macos"
        else:
            self._bridge = WindowsOSController()
            self.platform_name = "generic"

        logger.info(f"Initialized OSController for platform: {self.platform_name}")

    def get_active_window(self) -> Dict[str, Any]:
        return self._bridge.get_active_window()

    def list_windows(self) -> List[Dict[str, Any]]:
        return self._bridge.list_windows()

    def focus_window(self, title_query: str) -> bool:
        return self._bridge.focus_window(title_query)

    def click_coordinate(self, x: int, y: int, button: str = "left") -> bool:
        return self._bridge.click_coordinate(x, y, button)

    def type_text(self, text: str) -> bool:
        return self._bridge.type_text(text)

    def get_accessibility_tree(self, max_depth: int = 3) -> AccessibleElement:
        return self._bridge.get_accessibility_tree(max_depth)
