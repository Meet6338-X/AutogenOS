"""
Test for isolated Git Worktree concurrency manager.
"""

from pathlib import Path
from autogenos.execution.worktree_manager import WorktreeManager


def test_worktree_creation_and_removal(tmp_path):
    repo_root = Path(".").resolve()
    manager = WorktreeManager(repo_root=repo_root, worktrees_dir=tmp_path / "worktrees")
    
    agent_id = "test-agent-alpha"
    wt_path = manager.create_worktree(agent_id=agent_id)
    assert wt_path.exists()
    assert (wt_path / ".git").exists() or (wt_path / "README.md").exists()

    # Verify listing
    active = manager.list_worktrees()
    assert agent_id in active

    # Verify removal
    success = manager.remove_worktree(agent_id=agent_id, force=True)
    assert success is True
    assert agent_id not in manager.list_worktrees()
