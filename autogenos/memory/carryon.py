"""
CarryOn Framework: Object-Oriented Context Compactor.
Folds completed operational branches into condensed, immutable task states to prune KV-cache tokens.
"""

from __future__ import annotations
import logging
from typing import Any, Dict, List
from pydantic import BaseModel, Field

logger = logging.getLogger("autogenos.carryon")


class FoldedTaskObject(BaseModel):
    """Condensed summary replacing multi-turn intermediate reasoning tokens."""
    task_id: str
    original_intent: str
    outcome_summary: str
    state_mutations: Dict[str, Any]
    reusable_variables: Dict[str, Any] = Field(default_factory=dict)
    tokens_saved: int = 0


class CarryOnCompactor:
    """
    Monitors interaction trajectory length. When subtasks complete,
    CarryOn retires raw token logs and folds them into active FoldedTaskObjects.
    """

    def __init__(self, compaction_token_threshold: int = 4000):
        self.threshold = compaction_token_threshold
        self.folded_history: List[FoldedTaskObject] = []
        self.total_tokens_pruned: int = 0

    def fold_subtask(
        self,
        task_id: str,
        intent: str,
        intermediate_turn_count: int,
        estimated_raw_tokens: int,
        final_state: Dict[str, Any]
    ) -> FoldedTaskObject:
        """
        Folds raw execution conversation into an object-oriented state representation.
        Estimated reduction is typically 50% to 80% per completed branch.
        """
        folded_obj = FoldedTaskObject(
            task_id=task_id,
            original_intent=intent,
            outcome_summary=f"Task {task_id} successfully executed in {intermediate_turn_count} internal turns.",
            state_mutations=final_state,
            tokens_saved=max(0, estimated_raw_tokens - 150)
        )
        self.folded_history.append(folded_obj)
        self.total_tokens_pruned += folded_obj.tokens_saved

        logger.info(
            f"CarryOn folded task {task_id}. Saved ~{folded_obj.tokens_saved} tokens. "
            f"Cumulative pruned: {self.total_tokens_pruned}"
        )
        return folded_obj

    def get_compact_prompt_representation(self) -> str:
        """Returns compressed history for system prompt injection."""
        if not self.folded_history:
            return "No previous tasks folded."

        lines = ["=== COMPACTED OPERATIONAL STATE (CarryOn) ==="]
        for f in self.folded_history:
            lines.append(f"- [{f.task_id}] {f.original_intent} -> {f.outcome_summary}")
        return "\n".join(lines)
