"""
Test Suite for AutogenOS Cross-Platform Notifications and Interactive REPL Cockpit.
"""

import sys
import pytest
from unittest.mock import patch
from starlette.testclient import TestClient

from autogenos.notifications.dispatcher import (
    NotificationDispatcher,
    DesktopNotifier,
    WebhookNotifier,
    NotificationMessage,
    NotificationSeverity,
)
from autogenos.cli.repl import InteractiveCockpitREPL
from autogenos.cli.main import main
from autogenos.api.server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_notification_dispatcher_lifecycle():
    dispatcher = NotificationDispatcher()
    results = dispatcher.dispatch(
        title="Benchmark Completed",
        body="OSWorld Composite evaluation passed at 100%",
        severity=NotificationSeverity.SUCCESS,
        channels=["desktop"]
    )

    assert "desktop" in results
    assert len(dispatcher.dispatch_history) == 1
    assert dispatcher.dispatch_history[0].title == "Benchmark Completed"
    assert dispatcher.dispatch_history[0].severity == "SUCCESS"


def test_webhook_notifier_safeguard():
    msg = NotificationMessage(
        title="Warning Alert",
        body="Verifier rejected subtask attempt",
        severity=NotificationSeverity.WARNING
    )
    # Empty webhook should return False
    assert WebhookNotifier.post_webhook("", msg) is False
    # Unreachable webhook should gracefully return False without raising
    assert WebhookNotifier.post_webhook("http://127.0.0.1:59999/nonexistent", msg, timeout=0.5) is False


def test_interactive_cockpit_repl_methods(capsys):
    repl = InteractiveCockpitREPL()
    repl.print_help()
    captured = capsys.readouterr()
    assert "/doctor" in captured.out
    assert "/eval" in captured.out
    assert "/train" in captured.out
    assert "/tools" in captured.out

    repl.print_welcome()
    captured2 = capsys.readouterr()
    assert "AUTOGENOS INTERACTIVE TERMINAL COCKPIT" in captured2.out


def test_api_notification_endpoint(client):
    resp = client.post(
        "/api/v1/notifications/send",
        json={
            "title": "Mission Accomplished",
            "message": "All 10/10 metrics green",
            "severity": "SUCCESS",
            "channels": ["desktop"]
        }
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "DISPATCHED"
    assert "desktop" in data["results"]


def test_cli_notify_command(capsys):
    with patch.object(sys, "argv", ["autogenos", "notify", "Task completed", "--title", "CLI Test Alert", "--severity", "SUCCESS"]):
        main()
    captured = capsys.readouterr()
    assert "Dispatching Notification" in captured.out
    assert "CLI Test Alert" in captured.out
    assert "Channel: desktop" in captured.out
