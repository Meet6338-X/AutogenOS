"""
Central Orchestrator Node implementing the Planner-Actor-Verifier Lifecycle.
Executes real operations against the system runtime and enforces deterministic causal grounding.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List, Optional
from autogenos.core.state import (
    SwarmGlobalState,
    SubTask,
    TaskPhase,
    ActionProposal,
    DeterministicEvidence,
    EvidenceType,
)
from autogenos.core.prompt_protocol import OrchestratorProtocol
from autogenos.swarm.planner import AutonomousIntentPlanner
from autogenos.execution.action_dispatcher import ActionDispatcher

logger = logging.getLogger("autogenos.orchestrator")


class SwarmOrchestrator:
    """
    Coordinates subagents across Planner, Actor, and Verifier roles.
    Enforces causal verification invariants: progress is only committed
    when deterministic environmental evidence is validated by the Verifier.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        planner: Optional[AutonomousIntentPlanner] = None,
        dispatcher: Optional[ActionDispatcher] = None
    ):
        self.session_id = session_id
        self.protocol = OrchestratorProtocol()
        self.planner = planner or AutonomousIntentPlanner()
        self.dispatcher = dispatcher or ActionDispatcher()

    async def initialize_state(self, master_intent: str) -> SwarmGlobalState:
        """Instantiate new thread-scoped global state."""
        state = SwarmGlobalState(master_intent=master_intent)
        logger.info(f"Initialized swarm session: {state.session_id} for intent: {master_intent}")
        return state

    async def plan_subtasks(self, state: SwarmGlobalState) -> List[SubTask]:
        """
        Planner Stage:
        Decomposes high-level intent into atomic, causally dependent subtasks.
        """
        state.phase = TaskPhase.PLANNING
        decomposed = self.planner.plan(state.master_intent)
        state.subtasks = decomposed
        state.phase = TaskPhase.ACTING
        return decomposed

    async def verify_and_commit(
        self,
        state: SwarmGlobalState,
        subtask: SubTask,
        evidence: DeterministicEvidence
    ) -> bool:
        """
        Verifier Stage:
        Enforces StructAgent causal gate. Only commits state when evidence passes.
        """
        state.phase = TaskPhase.VERIFYING
        if not evidence.passed:
            logger.warning(
                f"Verifier REJECTED subtask {subtask.subtask_id}. "
                f"Evidence: {evidence.evidence_type} failed."
            )
            subtask.phase = TaskPhase.REPAIR
            state.phase = TaskPhase.REPAIR
            return False

        # Attach validated evidence to subtask and global state
        subtask.attached_evidence.append(evidence)
        subtask.is_committed = True
        subtask.phase = TaskPhase.COMPLETED
        state.accumulated_evidence.append(evidence)

        # Advance subtask index
        state.active_subtask_index += 1
        if state.active_subtask_index >= len(state.subtasks):
            state.phase = TaskPhase.COMPLETED
        else:
            state.phase = TaskPhase.ACTING

        logger.info(f"Verifier COMMITTED subtask {subtask.subtask_id} with evidence {evidence.evidence_id}")
        return True

    async def dispatch_intent(self, intent: str) -> Dict[str, Any]:
        """Executes full intent through the real Planner-Actor-Verifier pipeline."""
        state = await self.initialize_state(intent)
        subtasks = await self.plan_subtasks(state)

        for subtask in subtasks:
            # Actor turn: real execution via ActionDispatcher
            proposal, evidence = self.dispatcher.dispatch_subtask_action(subtask)
            subtask.proposals.append(proposal)

            # Verifier turn: causal commitment
            await self.verify_and_commit(state, subtask, evidence)

        return {
            "session_id": state.session_id,
            "status": state.phase.value,
            "subtasks_total": len(state.subtasks),
            "subtasks_executed": len(state.subtasks),
            "evidence_count": len(state.accumulated_evidence),
            "accumulated_evidence": [e.model_dump() for e in state.accumulated_evidence]
        }
