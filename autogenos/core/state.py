"""
Global Swarm State and Causal Evidence Structures for StructAgent & SolveBind.
"""

from __future__ import annotations
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import time
import uuid


class TaskPhase(str, Enum):
    IDLE = "IDLE"
    PLANNING = "PLANNING"
    ACTING = "ACTING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REPAIR = "REPAIR"


class EvidenceType(str, Enum):
    SHELL_OUTPUT = "SHELL_OUTPUT"
    FILE_HASH = "FILE_HASH"
    DOM_TREE = "DOM_TREE"
    ACCESSIBILITY_TREE = "ACCESSIBILITY_TREE"
    DB_STATE_DIFF = "DB_STATE_DIFF"
    PROCESS_TELEMETRY = "PROCESS_TELEMETRY"


class DeterministicEvidence(BaseModel):
    """Immutable evidence produced by environment to validate a state transition."""
    evidence_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    evidence_type: EvidenceType
    timestamp: float = Field(default_factory=time.time)
    source_target: str
    raw_payload: str
    verified_hash: Optional[str] = None
    passed: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class ActionProposal(BaseModel):
    """An action proposed by an Actor subagent."""
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    actor_id: str
    worktree_path: Optional[str] = None
    description: str
    code_or_payload: str
    proposed_state_diff: Dict[str, Any] = Field(default_factory=dict)
    timestamp: float = Field(default_factory=time.time)


class SubTask(BaseModel):
    """An atomic sub-task decomposed by the Planner."""
    subtask_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intent: str
    assigned_actor_id: Optional[str] = None
    phase: TaskPhase = TaskPhase.PLANNING
    proposals: List[ActionProposal] = Field(default_factory=list)
    attached_evidence: List[DeterministicEvidence] = Field(default_factory=list)
    is_committed: bool = False


class SwarmGlobalState(BaseModel):
    """
    Central typed state managed under LangGraph and persisted via AsyncPostgresSaver.
    """
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    master_intent: str
    phase: TaskPhase = TaskPhase.PLANNING
    subtasks: List[SubTask] = Field(default_factory=list)
    active_subtask_index: int = 0
    committed_state: Dict[str, Any] = Field(default_factory=dict)
    accumulated_evidence: List[DeterministicEvidence] = Field(default_factory=list)
    step_count: int = 0
    token_usage_pruned: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def current_subtask(self) -> Optional[SubTask]:
        if 0 <= self.active_subtask_index < len(self.subtasks):
            return self.subtasks[self.active_subtask_index]
        return None
