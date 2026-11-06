"""
Comprehensive Test Suite for AutogenOS Modular Block System.
Verifies BaseBlock lifecycle, @block decorator, BlockRegistry dependency validation,
BlockManager dynamic code compilation, standard blocks, API endpoints, and CLI commands.
"""

import sys
import json
import pytest
from unittest.mock import patch
from starlette.testclient import TestClient

from autogenos.blocks import (
    BaseBlock,
    BlockType,
    BlockStatus,
    FunctionalBlock,
    block,
    BlockRegistry,
    BlockManager,
    ShellExecutionBlock,
    FileHashVerificationBlock,
    OfflineTTSBlock,
    BrowserScraperBlock,
    SystemDoctorBlock,
    BenchmarkEvalBlock,
    NotificationAlertBlock,
)
from autogenos.cli.main import main
from autogenos.api.server import app


@pytest.fixture
def client():
    return TestClient(app)


class CustomTestBlock(BaseBlock):
    def __init__(self, block_id: str = "custom.test_block", multiplier: int = 2):
        super().__init__(
            block_id=block_id,
            block_type=BlockType.TOOL,
            name="Custom Test Block",
            description="Multiplies input integer by factor",
            tags=["math", "test"]
        )
        self.multiplier = multiplier

    async def execute(self, value: int) -> int:
        return value * self.multiplier


@pytest.mark.asyncio
async def test_base_block_lifecycle():
    b = CustomTestBlock(multiplier=3)
    assert b.block_id == "custom.test_block"
    assert b.is_enabled is True

    # Test execution
    res = await b.execute(5)
    assert res == 15

    # Test disable
    b.disable()
    assert b.is_enabled is False
    assert b.metadata.status == BlockStatus.DISABLED

    # Test health check
    health = await b.health_check()
    assert health["healthy"] is False

    # Test enable
    b.enable()
    assert b.is_enabled is True
    assert (await b.health_check())["healthy"] is True

    # Test serialization
    d = b.to_dict()
    assert d["block_id"] == "custom.test_block"
    assert d["block_type"] == "TOOL"


@pytest.mark.asyncio
async def test_block_decorator_function():
    @block(block_id="tools.math.square", block_type=BlockType.TOOL, description="Squares a number")
    def square_fn(x: int) -> int:
        return x * x

    assert hasattr(square_fn, "__autogenos_block__")
    b = getattr(square_fn, "__autogenos_block__")
    assert isinstance(b, FunctionalBlock)
    assert b.block_id == "tools.math.square"

    res = await b.execute(4)
    assert res == 16


def test_block_registry_dependencies_and_cycles():
    registry = BlockRegistry()

    b1 = CustomTestBlock(block_id="block.a")
    b2 = CustomTestBlock(block_id="block.b")
    b2.metadata.dependencies = ["block.a"]

    registry.register(b1)
    registry.register(b2)

    assert registry.count() == 2
    assert registry.validate_dependencies("block.b") == []

    # Disable b1 and verify dependency warning
    registry.disable("block.a")
    missing = registry.validate_dependencies("block.b")
    assert len(missing) == 1
    assert "Disabled dependency 'block.a'" in missing[0]

    # Test cycle detection
    b1.metadata.dependencies = ["block.b"]
    cycle = registry.check_circular_dependencies()
    assert cycle is not None
    assert "block.a" in cycle and "block.b" in cycle


@pytest.mark.asyncio
async def test_block_manager_standard_and_dynamic_code():
    mgr = BlockManager(auto_load_standard=True)
    assert mgr.registry.count() >= 7

    # Execute standard shell block
    shell_res = await mgr.execute_block("tools.os.exec_shell", command="echo BLOCK_TEST_OK")
    assert shell_res["exit_code"] == 0
    assert "BLOCK_TEST_OK" in shell_res["stdout"]

    # Add dynamic block from Python code
    code = """
from autogenos.blocks import BaseBlock, BlockType

class DynamicUpperBlock(BaseBlock):
    def __init__(self):
        super().__init__(
            block_id="custom.string.uppercase",
            block_type=BlockType.TOOL,
            name="Uppercase Formatter"
        )
    async def execute(self, text: str) -> str:
        return text.upper()
"""
    dyn_block = mgr.add_block_from_code(code)
    assert dyn_block.block_id == "custom.string.uppercase"
    res = await mgr.execute_block("custom.string.uppercase", text="autogenos")
    assert res == "AUTOGENOS"

    # Remove block
    removed = mgr.remove_block("custom.string.uppercase")
    assert removed is not None
    assert mgr.get_block("custom.string.uppercase") is None


def test_api_blocks_endpoints(client):
    # 1. GET /api/v1/blocks
    resp = client.get("/api/v1/blocks")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_blocks"] >= 7

    # 2. GET /api/v1/blocks/{id}/info
    info_resp = client.get("/api/v1/blocks/tools.os.exec_shell/info")
    assert info_resp.status_code == 200
    assert info_resp.json()["block_id"] == "tools.os.exec_shell"

    # 3. POST /api/v1/blocks/{id}/disable and enable
    dis_resp = client.post("/api/v1/blocks/tools.os.exec_shell/disable")
    assert dis_resp.status_code == 200
    assert dis_resp.json()["status"] == "DISABLED"

    en_resp = client.post("/api/v1/blocks/tools.os.exec_shell/enable")
    assert en_resp.status_code == 200
    assert en_resp.json()["status"] == "ENABLED"

    # 4. POST /api/v1/blocks/{id}/execute
    exec_resp = client.post(
        "/api/v1/blocks/tools.os.exec_shell/execute",
        json={"args": [], "kwargs": {"command": "echo API_EXEC_OK"}}
    )
    assert exec_resp.status_code == 200
    assert exec_resp.json()["status"] == "SUCCESS"
    assert "API_EXEC_OK" in exec_resp.json()["result"]["stdout"]

    # 5. POST /api/v1/blocks/register
    dyn_code = """
def double_val(n: int) -> int:
    return n * 2
"""
    reg_resp = client.post(
        "/api/v1/blocks/register",
        json={"code": dyn_code, "block_id": "custom.func.double", "block_type": "TOOL"}
    )
    assert reg_resp.status_code == 200
    assert reg_resp.json()["status"] == "REGISTERED"

    # 6. DELETE /api/v1/blocks/{id}
    del_resp = client.delete("/api/v1/blocks/custom.func.double")
    assert del_resp.status_code == 200
    assert del_resp.json()["status"] == "REMOVED"


def test_cli_blocks_commands(capsys):
    # Test blocks list
    with patch.object(sys, "argv", ["autogenos", "blocks", "list"]):
        main()
    captured = capsys.readouterr()
    assert "AutogenOS Modular Feature Blocks" in captured.out
    assert "tools.os.exec_shell" in captured.out

    # Test blocks info
    with patch.object(sys, "argv", ["autogenos", "blocks", "info", "tools.os.exec_shell"]):
        main()
    captured = capsys.readouterr()
    assert "BLOCK METADATA: tools.os.exec_shell" in captured.out

    # Test blocks exec
    with patch.object(sys, "argv", ["autogenos", "blocks", "exec", "tools.os.exec_shell", "--args", '{"command": "echo CLI_BLOCK_EXEC"}']):
        main()
    captured = capsys.readouterr()
    assert "Status: SUCCESS" in captured.out
    assert "CLI_BLOCK_EXEC" in captured.out
