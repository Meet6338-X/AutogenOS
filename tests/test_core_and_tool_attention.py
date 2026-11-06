"""
Integration test verifying Master Prompt, Tool Attention gating, and PAV lifecycle.
"""

import pytest
from autogenos.core.prompt_protocol import OrchestratorProtocol, MASTER_OPERATIONAL_PROMPT
from autogenos.core.orchestrator import SwarmOrchestrator
from autogenos.tool_attention.engine import ToolAttentionEngine
from autogenos.tool_attention.registry import ToolMetadata
from autogenos.skills.progressive_loader import ProgressiveSkillLoader


def test_master_prompt_integrity():
    prompt = OrchestratorProtocol.get_system_prompt()
    assert "SYSTEM INITIALIZATION PROTOCOL: ORCHESTRATOR NODE" in prompt
    assert "CAUSAL VERIFICATION REQUIREMENT" in prompt
    assert "ISOLATED EXECUTION" in prompt
    assert "TOOL GATING AND DEPENDENCY INJECTION" in prompt
    assert "RECURSIVE SELF-IMPROVEMENT" in prompt
    assert "CONTEXT COMPACTION" in prompt


def test_tool_attention_gating():
    engine = ToolAttentionEngine()
    engine.register_tool(ToolMetadata(
        name="calc_sha256",
        summary="Compute SHA-256 hash of a file or byte stream",
        tags=["crypto", "hash", "checksum"],
        schema={"type": "object", "properties": {"file": {"type": "string"}}}
    ))

    # Test gating with relevant intent
    promoted = engine.gate_tools("Check hash checksum of output artifact", top_k=2)
    names = [t.name for t in promoted]
    assert "calc_sha256" in names or "verifier_assert_hash" in names

    # Assert schemas can be rendered
    schemas = engine.generate_active_prompt_schemas("Compute sha256 hash", top_k=1)
    assert len(schemas) > 0
    assert "name" in schemas[0]


@pytest.mark.asyncio
async def test_orchestrator_pav_flow():
    orchestrator = SwarmOrchestrator()
    result = await orchestrator.dispatch_intent("Verify file system structure")
    assert result["status"] == "ACTING" or result["status"] == "COMPLETED"
    assert result["subtasks_total"] > 0
    assert result["evidence_count"] >= 1
