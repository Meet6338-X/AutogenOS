"""
Autonomous Meeting Agent Component for AutogenOS.
High-speed automated meeting joiner supporting Google Meet, Zoom, and Microsoft Teams.
Handles URL normalization, device permissions, lobby pre-configuration (mute mic, disable cam),
display name entry, and algorithmic clicking of "Join now" / "Ask to join" buttons.
"""

from __future__ import annotations
import os
import re
import sys
import time
import shutil
import asyncio
import logging
import subprocess
from enum import Enum
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field

logger = logging.getLogger("autogenos.meeting_agent")


class MeetingPlatform(str, Enum):
    GOOGLE_MEET = "google_meet"
    ZOOM = "zoom"
    MICROSOFT_TEAMS = "microsoft_teams"
    UNKNOWN = "unknown"


class MeetingConfig(BaseModel):
    """Configuration for autonomous meeting joining."""
    url: str
    display_name: str = Field(default="Meet Shah", description="Display name for guest lobbies")
    mute_mic: bool = Field(default=True, description="Mute microphone upon entering lobby")
    disable_camera: bool = Field(default=False, description="Disable camera upon entering lobby")
    auto_join: bool = Field(default=True, description="Algorithmically click Join/Ask to join button")
    browser: str = Field(default="auto", description="'auto', 'brave', 'chrome', 'edge', or 'playwright'")
    headless: bool = Field(default=False, description="Run browser headfully so user sees meeting")
    timeout_seconds: float = Field(default=20.0, description="Max seconds to wait for lobby/join")


class MeetingJoinResult(BaseModel):
    """Result of meeting join operation."""
    success: bool
    platform: MeetingPlatform
    meeting_id: str
    normalized_url: str
    status: str
    message: str
    duration_ms: float = 0.0


class MeetingAgent:
    """
    Autonomous multi-platform meeting connector and agent.
    Provides sub-second URL parsing, native browser orchestration, and DOM-level auto-joining.
    """

    KNOWN_BROWSERS = {
        "brave": [
            r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
            r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe")
        ],
        "chrome": [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ],
        "edge": [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
    }

    @classmethod
    def parse_meeting_url(cls, raw_url: str) -> Tuple[MeetingPlatform, str, str]:
        """
        Parses and normalizes meeting URL into (platform, meeting_id, clean_url).
        """
        clean = raw_url.strip()
        if not clean.startswith("http://") and not clean.startswith("https://"):
            clean = "https://" + clean

        # Google Meet: meet.google.com/xyz-abcd-efg or meet.google.com/meet/xyz-abcd-efg
        m_meet = re.search(r'meet\.google\.com/(?:meet/)?([a-z0-9]{3}-[a-z0-9]{4}-[a-z0-9]{3})', clean, re.I)
        if m_meet:
            meet_id = m_meet.group(1).lower()
            return MeetingPlatform.GOOGLE_MEET, meet_id, f"https://meet.google.com/{meet_id}"

        # Zoom: zoom.us/j/123456789
        m_zoom = re.search(r'zoom\.us/j/(\d+)', clean, re.I)
        if m_zoom:
            zoom_id = m_zoom.group(1)
            return MeetingPlatform.ZOOM, zoom_id, f"https://zoom.us/j/{zoom_id}"

        # Teams: teams.microsoft.com
        if "teams.microsoft.com" in clean or "teams.live.com" in clean:
            return MeetingPlatform.MICROSOFT_TEAMS, "teams-call", clean

        return MeetingPlatform.UNKNOWN, "unknown", clean

    @classmethod
    def locate_browser_binary(cls, preferred: str = "auto") -> Optional[str]:
        """Locates the highest-priority installed browser on Windows."""
        pref = preferred.lower()
        search_order = []
        if pref in cls.KNOWN_BROWSERS:
            search_order.append(pref)

        # Default preference: brave -> chrome -> edge
        for b in ["brave", "chrome", "edge"]:
            if b not in search_order:
                search_order.append(b)

        for b_name in search_order:
            for path in cls.KNOWN_BROWSERS.get(b_name, []):
                if os.path.exists(path):
                    return path

        for binary in ["brave", "google-chrome", "chrome", "msedge"]:
            found = shutil.which(binary)
            if found:
                return found

        return None

    @classmethod
    async def join_meeting_fast(cls, config: MeetingConfig) -> MeetingJoinResult:
        """
        Ultra-fast primary join method.
        Launches the meeting in the native browser (Brave/Chrome), maximizes the window,
        focuses it, and triggers auto-join via keyboard shortcuts and Playwright assistance.
        """
        start_time = time.time()
        platform, meet_id, normalized_url = cls.parse_meeting_url(config.url)

        if platform == MeetingPlatform.UNKNOWN:
            return MeetingJoinResult(
                success=False,
                platform=platform,
                meeting_id=meet_id,
                normalized_url=normalized_url,
                status="UNSUPPORTED_URL",
                message=f"Unsupported or invalid meeting URL: {config.url}",
                duration_ms=(time.time() - start_time) * 1000
            )

        logger.info(f"Joining {platform.value} meeting: {normalized_url} (ID: {meet_id})")

        # 1. Attempt Native Desktop Launch with window focus
        browser_exe = cls.locate_browser_binary(config.browser)
        if browser_exe:
            try:
                # Launch new window in foreground
                cmd = [browser_exe, "--new-window", normalized_url]
                subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                logger.info(f"Launched native browser ({browser_exe}) to {normalized_url}")
            except Exception as e:
                logger.warning(f"Native browser launch failed: {e}")

        # 2. Window focusing and auto-join via WindowsOSController
        try:
            from autogenos.control.windows_bridge import WindowsOSController
            import ctypes
            import ctypes.wintypes

            controller = WindowsOSController()
            # Give browser a moment to initialize the window
            await asyncio.sleep(1.2)

            # Poll for the newly created or updated meeting window
            target_win = None
            for _ in range(16):
                wins = controller.list_windows()
                for w in wins:
                    t = w.get("title", "").strip().lower()
                    if "bugslayermeet" in t:
                        continue
                    # Match exact meeting ID, Google Meet prefix, or Zoom/Teams title
                    if (meet_id in t) or t.startswith("meet - ") or t.startswith("meet – ") or ("google meet" in t) or ("zoom meeting" in t) or ("microsoft teams" in t):
                        target_win = w
                        break
                if target_win:
                    break
                await asyncio.sleep(0.4)

            # Fallback: if no dedicated title found yet, target the first Brave/Chrome window
            if not target_win:
                for w in wins:
                    t = w.get("title", "").strip().lower()
                    if ("brave" in t or "chrome" in t or "edge" in t) and ("whatsapp" not in t):
                        target_win = w
                        break

            if target_win:
                hwnd = target_win["handle"]
                user32 = ctypes.windll.user32
                SW_RESTORE = 9
                SW_MAXIMIZE = 3
                user32.ShowWindow(hwnd, SW_RESTORE)
                user32.ShowWindow(hwnd, SW_MAXIMIZE)
                user32.SetForegroundWindow(hwnd)
                logger.info(f"Maximized and focused meeting window: {target_win['title']} (HWND: {hwnd})")

                # If auto_join requested, wait briefly for lobby load and send join shortcuts
                if config.auto_join:
                    await asyncio.sleep(2.0)
                    
                    # Mute mic (Ctrl+D) if requested
                    if config.mute_mic:
                        user32.keybd_event(0x11, 0, 0, 0) # Ctrl down
                        user32.keybd_event(0x44, 0, 0, 0) # D down
                        user32.keybd_event(0x44, 0, 2, 0) # D up
                        user32.keybd_event(0x11, 0, 2, 0) # Ctrl up
                        await asyncio.sleep(0.3)

                    # Turn off cam (Ctrl+E) if requested
                    if config.disable_camera:
                        user32.keybd_event(0x11, 0, 0, 0) # Ctrl down
                        user32.keybd_event(0x45, 0, 0, 0) # E down
                        user32.keybd_event(0x45, 0, 2, 0) # E up
                        user32.keybd_event(0x11, 0, 2, 0) # Ctrl up
                        await asyncio.sleep(0.3)

                    # Press Tab multiple times or Enter to activate "Join now"
                    # In Meet, pressing Enter or Space on focused button joins
                    user32.keybd_event(0x0D, 0, 0, 0) # Enter down
                    user32.keybd_event(0x0D, 0, 2, 0) # Enter up

                duration = (time.time() - start_time) * 1000
                return MeetingJoinResult(
                    success=True,
                    platform=platform,
                    meeting_id=meet_id,
                    normalized_url=normalized_url,
                    status="JOINED_NATIVE",
                    message=f"Meeting opened and focused in native browser window (HWND: {hwnd}) with auto-join triggered.",
                    duration_ms=duration
                )
        except Exception as e:
            logger.warning(f"Native window orchestration notice: {e}")

        # 3. Fallback to Playwright headful automation if native bridge didn't resolve
        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=config.headless,
                    args=[
                        "--use-fake-ui-for-media-stream",
                        "--use-fake-device-for-media-stream",
                        "--disable-blink-features=AutomationControlled",
                        "--no-first-run",
                        "--no-default-browser-check"
                    ]
                )
                context = await browser.new_context(
                    permissions=["microphone", "camera"],
                    viewport={"width": 1280, "height": 720}
                )
                page = await context.new_page()
                await page.goto(normalized_url, wait_until="domcontentloaded", timeout=config.timeout_seconds * 1000)
                await page.wait_for_timeout(2000)

                # Check if name input exists
                name_input = page.locator("input[type='text'], input[aria-label*='name' i], input[placeholder*='name' i]").first
                if await name_input.is_visible():
                    await name_input.fill(config.display_name)
                    await page.wait_for_timeout(400)

                if config.auto_join:
                    join_btn = page.locator("button:has-text('Join now'), button:has-text('Ask to join'), [role='button']:has-text('Join now'), [role='button']:has-text('Ask to join')").first
                    if await join_btn.is_visible():
                        await join_btn.click()
                        await page.wait_for_timeout(1500)

                duration = (time.time() - start_time) * 1000
                return MeetingJoinResult(
                    success=True,
                    platform=platform,
                    meeting_id=meet_id,
                    normalized_url=normalized_url,
                    status="JOINED_AUTOMATION",
                    message="Meeting opened and joined via autonomous browser automation session.",
                    duration_ms=duration
                )
        except Exception as e:
            logger.error(f"Meeting join failed: {e}")
            duration = (time.time() - start_time) * 1000
            return MeetingJoinResult(
                success=False,
                platform=platform,
                meeting_id=meet_id,
                normalized_url=normalized_url,
                status="ERROR",
                message=str(e),
                duration_ms=duration
            )
