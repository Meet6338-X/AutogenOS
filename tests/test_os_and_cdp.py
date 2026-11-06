"""
Tests for Cross-Platform OS Controller, Window Introspection, and CDP Browser Controller.
"""

import pytest
from autogenos.control.os_controller import OSController
from autogenos.control.cdp_browser import CDPBrowserClient


def test_os_controller_introspection():
    ctrl = OSController()
    assert ctrl.platform_name in ["windows", "linux", "macos", "generic"]

    active_win = ctrl.get_active_window()
    assert "title" in active_win

    tree = ctrl.get_accessibility_tree()
    assert tree.control_type == "Window"
    assert tree.name is not None


@pytest.mark.asyncio
async def test_cdp_browser_client_unconnected_guard():
    client = CDPBrowserClient("ws://127.0.0.1:9299/nonexistent")
    # Should safely fail connection without crashing
    connected = await client.connect(timeout=0.2)
    assert connected is False

    # Calling commands on unconnected client must raise RuntimeError
    with pytest.raises(RuntimeError):
        await client.navigate("https://example.com")
