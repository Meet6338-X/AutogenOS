"""
Tool Registry and Metadata Definitions for Lazy Schema Resolution.
"""

from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolMetadata(BaseModel):
    """
    Lightweight tool representation (~100 tokens).
    Only this metadata is initially exposed to the model context.
    """
    name: str
    summary: str
    tags: List[str] = Field(default_factory=list)
    parameters_schema: Dict[str, Any] = Field(default_factory=dict, alias="schema")
    allowed_roles: List[str] = Field(default_factory=lambda: ["Actor"])
    requires_sandboxing: bool = False
    rate_limit_per_min: Optional[int] = None


class ToolRegistry:
    """In-memory or vector-backed registry for thousands of tools."""

    def __init__(self):
        self._tools: Dict[str, ToolMetadata] = {}

    def register(self, tool: ToolMetadata) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[ToolMetadata]:
        return self._tools.get(name)

    def list_all(self) -> List[ToolMetadata]:
        return list(self._tools.values())

    def get_summary_texts(self) -> List[str]:
        return [f"{t.name}: {t.summary} (tags: {', '.join(t.tags)})" for t in self._tools.values()]
