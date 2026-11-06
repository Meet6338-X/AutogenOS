"""
Agent-Diff Benchmark Verification Engine.
Enforces closed-world state invariants by computing exact deterministic diffs over filesystem and database entities.
"""

from __future__ import annotations
import hashlib
from pathlib import Path
from typing import Any, Dict, List, Set
from pydantic import BaseModel, Field


class StateSnapshot(BaseModel):
    snapshot_id: str
    file_hashes: Dict[str, str] = Field(default_factory=dict)
    database_records: Dict[str, Any] = Field(default_factory=dict)


class StateDiffReport(BaseModel):
    passed: bool
    added_files: List[str] = Field(default_factory=list)
    removed_files: List[str] = Field(default_factory=list)
    modified_files: List[str] = Field(default_factory=list)
    unexpected_side_effects: List[str] = Field(default_factory=list)
    score: float = 1.0


class AgentDiffEvaluator:
    """Computes exact diffs between pre-task baseline and post-task execution state."""

    @staticmethod
    def hash_file(path: Path) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()

    def snapshot_directory(self, root_dir: str | Path, exclude_patterns: Optional[Set[str]] = None) -> StateSnapshot:
        p = Path(root_dir)
        excludes = exclude_patterns or {".git", "__pycache__", ".venv"}
        hashes = {}

        for file_path in p.rglob("*"):
            if file_path.is_file():
                if any(ex in file_path.parts for ex in excludes):
                    continue
                rel_path = str(file_path.relative_to(p))
                try:
                    hashes[rel_path] = self.hash_file(file_path)
                except Exception:
                    pass

        return StateSnapshot(snapshot_id=str(root_dir), file_hashes=hashes)

    def evaluate_diff(
        self,
        baseline: StateSnapshot,
        current: StateSnapshot,
        expected_modifications: Set[str],
        expected_additions: Set[str]
    ) -> StateDiffReport:
        """Evaluates whether state mutation precisely satisfies test invariants without unexpected side effects."""
        base_files = set(baseline.file_hashes.keys())
        curr_files = set(current.file_hashes.keys())

        added = list(curr_files - base_files)
        removed = list(base_files - curr_files)
        modified = [
            f for f in (base_files & curr_files)
            if baseline.file_hashes[f] != current.file_hashes[f]
        ]

        # Calculate unintended side effects
        unexpected = []
        for a in added:
            if a not in expected_additions:
                unexpected.append(f"Unexpected file created: {a}")
        for m in modified:
            if m not in expected_modifications:
                unexpected.append(f"Unexpected file modified: {m}")

        passed = (len(unexpected) == 0) and set(expected_additions).issubset(set(added))
        score = 1.0 if passed else max(0.0, 1.0 - (len(unexpected) * 0.2))

        return StateDiffReport(
            passed=passed,
            added_files=added,
            removed_files=removed,
            modified_files=modified,
            unexpected_side_effects=unexpected,
            score=score
        )
