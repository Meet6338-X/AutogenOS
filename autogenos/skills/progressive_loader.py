"""
Progressive Disclosure Loader for SKILLS.md specification.
Loads metadata (~100 tokens) at discovery and retrieves execution scripts lazily.
"""

from __future__ import annotations
import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class SkillMetadata(BaseModel):
    name: str
    description: str
    trigger_conditions: List[str] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    context_forking: bool = False
    file_path: Optional[str] = None


class LoadedSkill(BaseModel):
    metadata: SkillMetadata
    instructions_markdown: str
    execution_scripts: Dict[str, str] = Field(default_factory=dict)


class ProgressiveSkillLoader:
    """Manages skill discovery, YAML frontmatter parsing, and progressive loading."""

    def __init__(self, skills_dir: Optional[str] = None):
        self.skills_dir = Path(skills_dir) if skills_dir else None
        self._registry: Dict[str, SkillMetadata] = {}
        self._body_cache: Dict[str, LoadedSkill] = {}

    def scan_directory(self, base_dir: str | Path) -> Dict[str, SkillMetadata]:
        """Scans for SKILLS.md files and registers their YAML frontmatter."""
        path = Path(base_dir)
        if not path.exists():
            return {}

        for skill_file in path.glob("**/SKILLS.md"):
            meta = self._parse_frontmatter(skill_file)
            if meta:
                self._registry[meta.name] = meta

        return self._registry

    def _parse_frontmatter(self, file_path: Path) -> Optional[SkillMetadata]:
        try:
            content = file_path.read_text(encoding="utf-8")
            match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
            if match:
                raw_yaml = match.group(1)
                data = yaml.safe_load(raw_yaml)
                data["file_path"] = str(file_path)
                return SkillMetadata(**data)
        except Exception:
            return None
        return None

    def load_full_skill(self, skill_name: str) -> Optional[LoadedSkill]:
        """Lazy load: retrieves full instructions and execution scripts on demand."""
        if skill_name in self._body_cache:
            return self._body_cache[skill_name]

        meta = self._registry.get(skill_name)
        if not meta or not meta.file_path:
            return None

        content = Path(meta.file_path).read_text(encoding="utf-8")
        body = re.sub(r"^---\s*\n.*?\n---\s*\n", "", content, flags=re.DOTALL)

        loaded = LoadedSkill(metadata=meta, instructions_markdown=body)
        self._body_cache[skill_name] = loaded
        return loaded

    def get_discovery_summaries(self) -> List[str]:
        """Produces lightweight summary block for agent prompt."""
        return [
            f"{s.name}: {s.description} (allowed: {', '.join(s.allowed_tools)})"
            for s in self._registry.values()
        ]
