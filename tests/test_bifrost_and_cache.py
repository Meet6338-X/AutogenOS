"""
Tests for Bifrost Gateway and Dual-Layer Semantic Cache.
"""

import pytest
from autogenos.gateway.bifrost_client import BifrostGatewayClient, DualLayerSemanticCache


def test_dual_layer_exact_and_semantic_cache():
    cache = DualLayerSemanticCache(semantic_threshold=0.8)
    prompt_1 = "list all running processes on windows host"
    model = "model-alpha"

    cache.put(prompt_1, model, "Process list: [explorer.exe, python.exe]")

    # Layer 1: Exact match
    res_exact, layer_1 = cache.get(prompt_1, model)
    assert res_exact == "Process list: [explorer.exe, python.exe]"
    assert "EXACT_HASH_LAYER_1" in layer_1
    assert cache.hits_exact == 1

    # Layer 2: Semantic match with high token overlap
    prompt_2 = "list running processes on windows host"
    res_sem, layer_2 = cache.get(prompt_2, model)
    assert res_sem == "Process list: [explorer.exe, python.exe]"
    assert "SEMANTIC_SIMILARITY_LAYER_2" in layer_2
    assert cache.hits_semantic == 1


@pytest.mark.asyncio
async def test_bifrost_gateway_routing():
    client = BifrostGatewayClient()
    res = await client.complete("Decompose system task", model="fast-model")
    assert res["cached"] is False
    assert res["latency_us"] > 0

    # Repeat call should hit cache instantly
    cached_res = await client.complete("Decompose system task", model="fast-model")
    assert cached_res["cached"] is True
    assert "EXACT_HASH" in cached_res["cache_layer"]
