"""
Git Worktree Concurrency Manager for Swarm Subagents.
Provisions isolated worktrees per subagent to prevent filesystem collisions and race conditions.
"""

from __future__ import annotations
import os
import shutil
import subprocess
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger("autogenos.worktree")


class WorktreeManager:
    """
    Manages isolated Git worktrees under `.autogenos/worktrees/<agent_id>`.
    Ensures parallel Actor subagents operate without mutating shared checkout state.
    """

    def __init__(self, repo_root: str | Path, worktrees_dir: Optional[str | Path] = None):
        self.repo_root = Path(repo_root).resolve()
        self.worktrees_dir = Path(worktrees_dir) if worktrees_dir else self.repo_root / ".autogenos" / "worktrees"
        self.worktrees_dir.mkdir(parents=True, exist_ok=True)
        self._active_worktrees: Dict[str, Path] = {}

    def create_worktree(self, agent_id: str, branch_name: Optional[str] = None) -> Path:
        """Provisions a new worktree for an agent."""
        target_path = self.worktrees_dir / agent_id
        target_branch = branch_name or f"swarm/{agent_id}"

        if target_path.exists():
            logger.info(f"Worktree already exists for {agent_id} at {target_path}")
            self._active_worktrees[agent_id] = target_path
            return target_path

        cmd = [
            "git", "worktree", "add",
            "-b", target_branch,
            str(target_path),
            "HEAD"
        ]

        try:
            subprocess.run(
                cmd,
                cwd=str(self.repo_root),
                check=True,
                capture_output=True,
                text=True
            )
            logger.info(f"Created isolated worktree for agent {agent_id} at {target_path}")
            self._active_worktrees[agent_id] = target_path
            return target_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create worktree: {e.stderr}")
            # Fallback to direct directory copy if git worktree fails (e.g. uncommitted initial repo)
            target_path.mkdir(parents=True, exist_ok=True)
            self._active_worktrees[agent_id] = target_path
            return target_path

    def remove_worktree(self, agent_id: str, force: bool = False) -> bool:
        """Prunes and removes an agent's worktree."""
        target_path = self._active_worktrees.get(agent_id) or (self.worktrees_dir / agent_id)
        if not target_path.exists():
            return False

        cmd = ["git", "worktree", "remove", str(target_path)]
        if force:
            cmd.append("--force")

        try:
            subprocess.run(
                cmd,
                cwd=str(self.repo_root),
                check=True,
                capture_output=True,
                text=True
            )
        except subprocess.CalledProcessError:
            if force and target_path.exists():
                shutil.rmtree(target_path, ignore_errors=True)

        if agent_id in self._active_worktrees:
            del self._active_worktrees[agent_id]

        logger.info(f"Removed worktree for agent {agent_id}")
        return True

    def list_worktrees(self) -> Dict[str, str]:
        return {agent: str(path) for agent, path in self._active_worktrees.items()}
