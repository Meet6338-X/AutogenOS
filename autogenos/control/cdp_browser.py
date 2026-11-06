"""
Pure WebSocket Chrome DevTools Protocol (CDP) Browser Controller.
Bypasses heavy Playwright abstractions for high-speed direct JSON-RPC browser automation.
"""

from __future__ import annotations
import json
import asyncio
import logging
from typing import Any, Dict, Optional
import websockets

logger = logging.getLogger("autogenos.cdp_browser")


class CDPBrowserClient:
    """
    Manages raw WebSocket connection to a Chrome DevTools Protocol endpoint.
    Default port: 9222 (--remote-debugging-port=9222).
    """

    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self._connection: Optional[websockets.WebSocketClientProtocol] = None
        self._msg_id = 0
        self._pending_requests: Dict[int, asyncio.Future] = {}

    async def connect(self) -> None:
        """Establishes WebSocket connection to the browser target."""
        self._connection = await websockets.connect(self.ws_url)
        logger.info(f"Connected to CDP WebSocket at {self.ws_url}")
        asyncio.create_task(self._listen_loop())

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
            logger.error(f"CDP WebSocket connection error: {e}")

    async def send_command(self, method: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
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
        result = await asyncio.wait_for(future, timeout=10.0)
        del self._pending_requests[current_id]

        if "error" in result:
            raise RuntimeError(f"CDP command {method} failed: {result['error']}")

        return result.get("result", {})

    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigates browser to target URL."""
        return await self.send_command("Page.navigate", {"url": url})

    async def evaluate_script(self, expression: str) -> Any:
        """Evaluates arbitrary JavaScript in page execution context."""
        res = await self.send_command("Runtime.evaluate", {
            "expression": expression,
            "returnByValue": True
        })
        return res.get("result", {}).get("value")

    async def close(self) -> None:
        """Closes connection."""
        if self._connection:
            await self._connection.close()
