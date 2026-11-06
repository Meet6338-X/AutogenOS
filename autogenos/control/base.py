"""
Abstract Base Operating System Automation Controller.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel


class ElementBounds(BaseModel):
    left: int
    top: int
    right: int
    bottom: int

    @property
    def center(self) -> Tuple[int, int]:
        return (self.left + (self.right - self.left) // 2, self.top + (self.bottom - self.top) // 2)


class AccessibleElement(BaseModel):
    name: str
    control_type: str
    bounds: ElementBounds
    is_enabled: bool = True
    is_offscreen: bool = False
    automation_id: Optional[str] = None
    children: List[AccessibleElement] = []


class BaseOSController(ABC):
    """Abstract interface across Windows, Linux, and macOS platforms."""

    @abstractmethod
    def get_active_window(self) -> Dict[str, Any]:
        """Returns details of the currently focused window."""
        pass

    @abstractmethod
    def list_windows(self) -> List[Dict[str, Any]]:
        """Lists all open windows."""
        pass

    @abstractmethod
    def focus_window(self, title_query: str) -> bool:
        """Brings target window to the foreground."""
        pass

    @abstractmethod
    def click_coordinate(self, x: int, y: int, button: str = "left") -> bool:
        """Injects hardware-level mouse click."""
        pass

    @abstractmethod
    def type_text(self, text: str) -> bool:
        """Injects keystrokes."""
        pass

    @abstractmethod
    def get_accessibility_tree(self, max_depth: int = 3) -> AccessibleElement:
        """Extracts native UI accessibility tree for visual-free spatial grounding."""
        pass
