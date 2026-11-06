"""
AutogenOS Cross-Platform Notification and Incident Dispatcher.
Dispatches mission-critical alerts, completion notices, and failure telemetry
to Native Desktop Toasts (Windows, macOS, Linux), Slack, Discord, and Generic Webhooks.
"""

from __future__ import annotations
import os
import sys
import json
import logging
import platform
import subprocess
import urllib.request
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger("autogenos.notifications")


class NotificationSeverity:
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class NotificationMessage(BaseModel):
    title: str
    body: str
    severity: str = NotificationSeverity.INFO
    category: str = "Swarm"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DesktopNotifier:
    """Dispatches native desktop notifications across Windows, Linux, and macOS."""

    @staticmethod
    def notify(message: NotificationMessage) -> bool:
        plat = platform.system().lower()
        title = message.title.replace('"', '\\"')
        body = message.body.replace('"', '\\"')

        try:
            if "windows" in plat:
                # PowerShell notification via Windows Toast or tray balloon
                ps_script = f"""
                [void] [System.Reflection.Assembly]::LoadWithPartialName("System.Windows.Forms")
                $objNotifyIcon = New-Object System.Windows.Forms.NotifyIcon
                $objNotifyIcon.Icon = [System.Drawing.SystemIcons]::Information
                $objNotifyIcon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
                $objNotifyIcon.BalloonTipTitle = "{title}"
                $objNotifyIcon.BalloonTipText = "{body}"
                $objNotifyIcon.Visible = $True
                $objNotifyIcon.ShowBalloonTip(5000)
                """
                subprocess.run(
                    ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script],
                    capture_output=True,
                    timeout=5.0,
                    check=False
                )
                return True
            elif "darwin" in plat:
                # macOS AppleScript notification
                apple_script = f'display notification "{body}" with title "{title}"'
                subprocess.run(["osascript", "-e", apple_script], capture_output=True, timeout=5.0, check=False)
                return True
            else:
                # Linux notify-send
                subprocess.run(["notify-send", title, body], capture_output=True, timeout=5.0, check=False)
                return True
        except Exception as e:
            logger.debug(f"Desktop notification error: {e}")
            return False


class WebhookNotifier:
    """Dispatches notifications to Slack, Discord, or generic JSON HTTP webhooks."""

    @staticmethod
    def post_webhook(url: str, message: NotificationMessage, timeout: float = 8.0) -> bool:
        if not url:
            return False

        # Detect Discord or Slack vs generic
        payload: Dict[str, Any] = {}
        if "discord.com" in url:
            payload = {
                "content": f"**[{message.severity}] {message.title}**\n{message.body}",
                "username": "AutogenOS Swarm Monitor"
            }
        elif "hooks.slack.com" in url:
            payload = {
                "text": f"*{message.title}* ({message.severity})\n{message.body}"
            }
        else:
            payload = message.model_dump()

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json", "User-Agent": "AutogenOS-Notifier/0.1.0"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.status in [200, 204]
        except Exception as e:
            logger.debug(f"Webhook dispatch failed to {url}: {e}")
            return False


class NotificationDispatcher:
    """
    Unified manager for event-driven agent notifications.
    """

    def __init__(self, default_webhook_url: Optional[str] = None):
        self.default_webhook_url = default_webhook_url or os.getenv("AUTOGENOS_WEBHOOK_URL")
        self.dispatch_history: List[NotificationMessage] = []

    def dispatch(
        self,
        title: str,
        body: str,
        severity: str = NotificationSeverity.INFO,
        channels: Optional[List[str]] = None,
        webhook_url: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Dispatches notification across requested channels ("desktop", "webhook").
        """
        target_channels = channels or ["desktop"]
        msg = NotificationMessage(title=title, body=body, severity=severity)
        self.dispatch_history.append(msg)

        results = {}
        if "desktop" in target_channels:
            results["desktop"] = DesktopNotifier.notify(msg)

        if "webhook" in target_channels:
            wh_url = webhook_url or self.default_webhook_url
            if wh_url:
                results["webhook"] = WebhookNotifier.post_webhook(wh_url, msg)
            else:
                results["webhook"] = False

        return results
