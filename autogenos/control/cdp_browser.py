"""
Pure WebSocket Chrome DevTools Protocol (CDP) Browser Controller.
Bypasses heavy Playwright abstractions for high-speed direct JSON-RPC browser automation.
Supports AX tree grounding, screenshot captures, DOM manipulation, and input dispatch.
"""

from __future__ import annotations
import json
import base64
import asyncio
import logging
from typing import Any, Dict, Optional, List
import websockets

logger = logging.getLogger("autogenos.cdp_browser")


class CDPBrowserClient:
    """
    Direct WebSocket client connecting to Chrome remote debugging port (default 9222).
    """

    def __init__(self, ws_url: str = "ws://127.0.0.1:9222/devtools/browser"):
        self.ws_url = ws_url
        self._connection: Optional[websockets.WebSocketClientProtocol] = None
        self._msg_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}
        self._is_listening = False

    async def connect(self, timeout: float = 5.0) -> bool:
        """Establishes WebSocket connection to the browser target."""
        try:
            self._connection = await asyncio.wait_for(
                websockets.connect(self.ws_url), timeout=timeout
            )
            self._is_listening = True
            asyncio.create_task(self._listen_loop())
            logger.info(f"Connected to CDP WebSocket at {self.ws_url}")
            return True
        except Exception as e:
            logger.warning(f"Could not connect to CDP target at {self.ws_url}: {e}")
            return False

    async def _listen_loop(self) -> None:
        """Background listener for incoming JSON-RPC responses and events."""
        if not self._connection:
            return

        try:
            async for raw_msg in self._connection:
                data = json.loads(raw_msg)
                msg_id = data.get("id")
                if msg_id in self._pending_requests:
                    self._pending_requests[msg_id].set_result(data)
        except Exception as e:
            logger.debug(f"CDP WebSocket listen loop finished: {e}")
        finally:
            self._is_listening = False

    async def send_command(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0) -> Dict[str, Any]:
        """Dispatches a JSON-RPC command to the browser."""
        if not self._connection:
            raise RuntimeError("CDP client is not connected.")

        self._msg_id += 1
        current_id = self._msg_id

        payload = {
            "id": current_id,
            "method": method,
            "params": params or {}
        }

        loop = asyncio.get_running_loop()
        future = loop.create_future()
        self._pending_requests[current_id] = future

        await self._connection.send(json.dumps(payload))
        result = await asyncio.wait_for(future, timeout=timeout)
        del self._pending_requests[current_id]

        if "error" in result:
            raise RuntimeError(f"CDP command {method} failed: {result['error']}")

        return result.get("result", {})

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigates browser page to target URL."""
        return await self.send_command("Page.navigate", {"url": url})

    async def evaluate_script(self, expression: str) -> Any:
        """Evaluates arbitrary JavaScript in page execution context."""
        res = await self.send_command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True
        })
        return res.get("result", {}).get("value")

    async def get_accessibility_tree(self) -> List[Dict[str, Any]]:
        """
        Extracts full accessibility tree via Accessibility.getFullAXTree
        for low-token spatial element grounding.
        """
        res = await self.send_command("Accessibility.getFullAXTree")
        return res.get("nodes", [])

    async def capture_screenshot(self, format: str = "png") -> bytes:
        """Captures page screenshot, returning raw bytes."""
        res = await self.send_command("Page.captureScreenshot", {"format": format})
        data_base64 = res.get("data", "")
        return base64.b64decode(data_base64)

    async def click(self, x: int, y: int) -> None:
        """Dispatches hardware-level mouse click via Input.dispatchMouseEvent."""
        await self.send_command("Input.dispatchMouseEvent", {
            "type": "mousePressed",
            "x": x,
            "y": y,
            "button": "left",
            "clickCount": 1
        })
        await self.send_command("Input.dispatchMouseEvent", {
            "type": "mouseReleased",
            "x": x,
            "y": y,
            "button": "left",
            "clickCount": 1
        })

    async def type_text(self, text: str) -> None:
        """Inserts text directly into the focused element."""
        for char in text:
            await self.send_command("Input.insertText", {"text": char})

    async def close(self) -> None:
        """Closes WebSocket connection cleanly."""
        self._is_listening = False
        if self._connection:
            await self._connection.close()
