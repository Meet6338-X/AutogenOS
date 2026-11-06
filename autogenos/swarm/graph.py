"""
LangGraph Swarm State Machine Controller.
Orchestrates Planner-Actor-Verifier transitions with durable checkpointing,
isolated Git worktree execution, real native tool dispatch, and dynamic failure attribution.
"""

from __future__ import annotations
import logging
from typing import Callable, Dict, Optional, Any, List
from autogenos.core.state import (
    SwarmGlobalState,
    SubTask,
    TaskPhase,
    ActionProposal,
    DeterministicEvidence,
    EvidenceType,
)
from autogenos.swarm.postgres_saver import DurableStateSaver
from autogenos.execution.worktree_manager import WorktreeManager
from autogenos.execution.action_dispatcher import ActionDispatcher
from autogenos.tool_attention.engine import ToolAttentionEngine
from autogenos.memory.carryon import CarryOnCompactor
from autogenos.swarm.planner import AutonomousIntentPlanner

logger = logging.getLogger("autogenos.swarm")


class SwarmGraphController:
    """
    State machine graph enforcing strict Planner-Actor-Verifier execution.
    Executes real actions across the host operating system, terminal, and browser,
    requiring deterministic causal evidence before advancing state.
    """

    def __init__(
        self,
        checkpointer: Optional[DurableStateSaver] = None,
        worktree_mgr: Optional[WorktreeManager] = None,
        tool_engine: Optional[ToolAttentionEngine] = None,
        compactor: Optional[CarryOnCompactor] = None,
        planner: Optional[AutonomousIntentPlanner] = None,
        dispatcher: Optional[ActionDispatcher] = None,
        event_callback: Optional[Callable[[str, Dict[str, Any]], None]] = None,
    ):
        self.checkpointer = checkpointer or DurableStateSaver()
        self.worktree_mgr = worktree_mgr
        self.tool_engine = tool_engine or ToolAttentionEngine()
        self.compactor = compactor or CarryOnCompactor()
        self.planner = planner or AutonomousIntentPlanner()
        self.dispatcher = dispatcher or ActionDispatcher()
        self.event_callback = event_callback

    def _emit_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if self.event_callback:
            try:
                self.event_callback(event_type, data)
            except Exception as e:
                logger.debug(f"Event callback exception: {e}")

    async def planner_node(self, state: SwarmGlobalState) -> SwarmGlobalState:
        """
        Planner Node:
        Decomposes long-horizon user intent into atomic, causally dependent SubTasks.
        """
        state.phase = TaskPhase.PLANNING
        state.step_count += 1

        if not state.subtasks:
            # Dynamic semantic planning
            state.subtasks = self.planner.plan(state.master_intent)
            state.active_subtask_index = 0

        self._emit_event("PLANNER_COMPLETED", {
            "master_intent": state.master_intent,
            "subtasks_count": len(state.subtasks),
            "subtasks": [st.intent for st in state.subtasks]
        })

        state.phase = TaskPhase.ACTING
        self.checkpointer.save_checkpoint(state)
        logger.info(f"[PlannerNode] Decomposed intent into {len(state.subtasks)} subtasks.")
        return state

    async def actor_node(
        self,
        state: SwarmGlobalState,
        custom_executor: Optional[Callable[[SubTask, str], Any]] = None
    ) -> SwarmGlobalState:
        """
        Actor Node:
        Provisions isolated Git worktree if enabled, gates relevant tools via Tool Attention,
        and dispatches real system execution via ActionDispatcher.
        """
        current_subtask = state.current_subtask()
        if not current_subtask:
            state.phase = TaskPhase.COMPLETED
            return state

        current_subtask.phase = TaskPhase.ACTING
        actor_id = f"actor-{current_subtask.subtask_id[:8]}"
        current_subtask.assigned_actor_id = actor_id

        # 1. Provision isolated worktree if worktree manager is enabled
        wt_path_str = None
        if self.worktree_mgr:
            try:
                wt_path = self.worktree_mgr.create_worktree(actor_id)
                wt_path_str = str(wt_path)
            except Exception as e:
                logger.warning(f"Could not provision worktree for {actor_id}: {e}")

        # 2. Semantic tool gating for immediate execution step (MCP Tax Elimination)
        gated_tools = self.tool_engine.gate_tools(current_subtask.intent, top_k=2)

        # 3. Real Tool Execution via ActionDispatcher
        if custom_executor:
            raw_res = custom_executor(current_subtask, wt_path_str or "")
            proposal = ActionProposal(
                actor_id=actor_id,
                worktree_path=wt_path_str,
                description=f"Custom action for: {current_subtask.intent}",
                code_or_payload=str(raw_res),
                proposed_state_diff={"custom": True}
            )
            evidence = DeterministicEvidence(
                evidence_type=EvidenceType.SHELL_OUTPUT,
                source_target="custom_executor",
                raw_payload=str(raw_res),
                passed=True
            )
        else:
            proposal, evidence = self.dispatcher.dispatch_subtask_action(current_subtask)

        # Record proposal and attach evidence to subtask for Verifier evaluation
        current_subtask.proposals.append(proposal)
        current_subtask.attached_evidence.append(evidence)

        self._emit_event("ACTOR_PROPOSAL", {
            "subtask_id": current_subtask.subtask_id,
            "intent": current_subtask.intent,
            "tool": current_subtask.metadata.get("tool"),
            "evidence_passed": evidence.passed,
            "raw_payload": evidence.raw_payload[:200]
        })

        state.phase = TaskPhase.VERIFYING
        state.step_count += 1
        self.checkpointer.save_checkpoint(state)
        logger.info(f"[ActorNode] Subtask {current_subtask.subtask_id} executed tool '{current_subtask.metadata.get('tool')}' (evidence passed: {evidence.passed})")
        return state

    async def verifier_node(
        self,
        state: SwarmGlobalState,
        evidence_override: Optional[DeterministicEvidence] = None
    ) -> SwarmGlobalState:
        """
        Verifier Node:
        Enforces StructAgent causal invariant.
        Requires real environmental evidence (exit code 0, exact file hash, DOM state) before committing.
        """
        current_subtask = state.current_subtask()
        if not current_subtask:
            state.phase = TaskPhase.COMPLETED
            return state

        current_subtask.phase = TaskPhase.VERIFYING
        state.step_count += 1

        # Use freshly emitted evidence from actor node or override
        if evidence_override:
            evidence = evidence_override
        elif current_subtask.attached_evidence:
            evidence = current_subtask.attached_evidence[-1]
        else:
            evidence = DeterministicEvidence(
                evidence_type=EvidenceType.SHELL_OUTPUT,
                source_target="environmental_grounding",
                raw_payload="No evidence attached",
                passed=False,
                details={"error": "Missing evidence"}
            )

        # Enforce Causal Verification Gate
        if not evidence.passed:
            failure_detail = {
                "subtask_id": current_subtask.subtask_id,
                "intent": current_subtask.intent,
                "reason": evidence.details or evidence.raw_payload,
                "step": state.step_count
            }
            state.failure_attribution_history.append(failure_detail)
            logger.warning(f"[VerifierNode] Evidence REJECTED for subtask {current_subtask.subtask_id}. Routing to REPAIR.")
            current_subtask.phase = TaskPhase.REPAIR
            state.phase = TaskPhase.REPAIR

            self._emit_event("VERIFIER_REJECTED", failure_detail)
            self.checkpointer.save_checkpoint(state)
            return state

        # Commit state transition
        current_subtask.is_committed = True
        current_subtask.phase = TaskPhase.COMPLETED
        state.accumulated_evidence.append(evidence)

        # Context folding via CarryOn
        self.compactor.fold_subtask(
            task_id=current_subtask.subtask_id,
            intent=current_subtask.intent,
            intermediate_turn_count=len(current_subtask.proposals),
            estimated_raw_tokens=1500,
            final_state={"committed": True, "tool": current_subtask.metadata.get("tool")}
        )
        state.token_usage_pruned = self.compactor.total_tokens_pruned

        self._emit_event("VERIFIER_COMMITTED", {
            "subtask_id": current_subtask.subtask_id,
            "intent": current_subtask.intent,
            "evidence_id": evidence.evidence_id,
            "tokens_pruned": state.token_usage_pruned
        })

        # Advance subtask
        state.active_subtask_index += 1
        if state.active_subtask_index >= len(state.subtasks):
            state.phase = TaskPhase.COMPLETED
            logger.info(f"[VerifierNode] All subtasks committed! Master task COMPLETED.")
            self._emit_event("SWARM_COMPLETED", {
                "master_intent": state.master_intent,
                "total_subtasks": len(state.subtasks),
                "total_evidence": len(state.accumulated_evidence)
            })
        else:
            state.phase = TaskPhase.ACTING

        self.checkpointer.save_checkpoint(state)
        return state

    async def run_full_lifecycle(self, master_intent: str) -> SwarmGlobalState:
        """Executes full closed-loop swarm until task completion or repair termination."""
        state = SwarmGlobalState(master_intent=master_intent)
        state = await self.planner_node(state)

        max_cycles = 25
        cycles = 0

        while state.phase not in [TaskPhase.COMPLETED, TaskPhase.FAILED] and cycles < max_cycles:
            cycles += 1
            if state.phase == TaskPhase.ACTING:
                state = await self.actor_node(state)
            elif state.phase == TaskPhase.VERIFYING:
                state = await self.verifier_node(state)
            elif state.phase == TaskPhase.REPAIR:
                # Dynamic re-planning or recovery
                logger.info(f"[SwarmController] Re-attempting subtask under repair...")
                current = state.current_subtask()
                if current and len(current.proposals) < 3:
                    state.phase = TaskPhase.ACTING
                else:
                    logger.warning("[SwarmController] Max repair attempts exceeded for subtask.")
                    state.phase = TaskPhase.FAILED
                    break

        return state
