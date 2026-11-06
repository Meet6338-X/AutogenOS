"""
Local Browser Automation Component.
Launches local Chromium/Edge with remote debugging enabled and binds to pure WebSocket CDP.
Zero heavy Playwright/Puppeteer wrappers.
"""

from __future__ import annotations
import os
import shutil
import subprocess
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from autogenos.control.cdp_browser import CDPBrowserClient

logger = logging.getLogger("autogenos.browser_automation")


class LocalBrowserManager:
    """
    Finds and launches installed Chrome or Edge binaries with remote debugging enabled.
    """

    WINDOWS_CHROME_PATHS = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    def __init__(self, debug_port: int = 9222, headless: bool = True):
        self.port = debug_port
        self.headless = headless
        self.process: Optional[subprocess.Popen] = None
        self.cdp_client: Optional[CDPBrowserClient] = None

    def find_browser_executable(self) -> Optional[str]:
        """Locates Chrome or Edge binary on host system."""
        for p in self.WINDOWS_CHROME_PATHS:
            if os.path.exists(p):
                return p

        # Check standard PATH
        for binary in ["google-chrome", "chrome", "chromium", "msedge", "brave"]:
            found = shutil.which(binary)
            if found:
                return found

        return None

    def launch_browser(self, user_data_dir: Optional[str] = None) -> bool:
        """Starts browser process with --remote-debugging-port."""
        exe = self.find_browser_executable()
        if not exe:
            logger.warning("No Chrome/Edge browser binary found on host system.")
            return False

        u_dir = user_data_dir or str(Path(".autogenos/browser_profile").resolve())
        cmd = [
            exe,
            f"--remote-debugging-port={self.port}",
            f"--user-data-dir={u_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-background-networking",
        ]
        if self.headless:
            cmd.append("--headless=new")

        try:
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            logger.info(f"Launched browser ({exe}) on remote debugging port {self.port}")
            return True
        except Exception as e:
            logger.error(f"Failed to launch browser: {e}")
            return False

    async def get_connected_cdp_client(self, timeout: float = 3.0) -> Optional[CDPBrowserClient]:
        """Connects CDP client to the launched browser target, preferring active page session."""
        # 1. Try connecting directly to active page target
        client = await CDPBrowserClient.connect_to_active_page(port=self.port, timeout=timeout)
        if client:
            self.cdp_client = client
            return client

        # 2. Fallback to direct browser target
        ws_url = f"ws://127.0.0.1:{self.port}/devtools/browser"
        fallback = CDPBrowserClient(ws_url=ws_url)
        connected = await fallback.connect(timeout=timeout)
        if connected:
            self.cdp_client = fallback
            return fallback
        return None

    def stop_browser(self) -> None:
        """Terminates browser process."""
        if self.process:
            self.process.terminate()
            self.process = None
            logger.info("Stopped browser process.")
