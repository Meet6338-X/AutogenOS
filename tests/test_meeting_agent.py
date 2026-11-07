"""
Tests for AutogenOS Autonomous Meeting Agent & Meet Joiner.
Verifies multi-platform URL parsing, browser detection, configuration schemas,
modular block registration, and REST API endpoints.
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from autogenos.components.meeting_agent import (
    MeetingAgent,
    MeetingConfig,
    MeetingPlatform,
    MeetingJoinResult,
)
from autogenos.blocks import BlockManager
from autogenos.api.server import app

client = TestClient(app)


def test_meeting_url_parsing_google_meet():
    # Direct format
    platform, mid, url = MeetingAgent.parse_meeting_url("https://meet.google.com/hsw-hmdc-gqc")
    assert platform == MeetingPlatform.GOOGLE_MEET
    assert mid == "hsw-hmdc-gqc"
    assert url == "https://meet.google.com/hsw-hmdc-gqc"

    # Embedded /meet/ format
    platform2, mid2, url2 = MeetingAgent.parse_meeting_url("meet.google.com/meet/abc-defg-hij")
    assert platform2 == MeetingPlatform.GOOGLE_MEET
    assert mid2 == "abc-defg-hij"
    assert url2 == "https://meet.google.com/abc-defg-hij"


def test_meeting_url_parsing_zoom_and_teams():
    # Zoom format
    p_zoom, mid_zoom, url_zoom = MeetingAgent.parse_meeting_url("https://zoom.us/j/1234567890")
    assert p_zoom == MeetingPlatform.ZOOM
    assert mid_zoom == "1234567890"

    # Teams format
    p_teams, mid_teams, url_teams = MeetingAgent.parse_meeting_url("https://teams.microsoft.com/l/meetup-join/19%3ameeting")
    assert p_teams == MeetingPlatform.MICROSOFT_TEAMS

    # Unknown
    p_unk, _, _ = MeetingAgent.parse_meeting_url("https://randomservice.com/room123")
    assert p_unk == MeetingPlatform.UNKNOWN


def test_meeting_config_defaults():
    cfg = MeetingConfig(url="https://meet.google.com/hsw-hmdc-gqc")
    assert cfg.display_name == "Meet Shah"
    assert cfg.mute_mic is True
    assert cfg.disable_camera is False
    assert cfg.auto_join is True
    assert cfg.browser == "auto"


def test_meeting_browser_locator():
    browser = MeetingAgent.locate_browser_binary()
    if browser:
        assert isinstance(browser, str)
        assert len(browser) > 0


@pytest.mark.asyncio
async def test_meeting_join_fast_invalid_url():
    cfg = MeetingConfig(url="https://invalid-non-meeting-site.com/nothing")
    res = await MeetingAgent.join_meeting_fast(cfg)
    assert res.success is False
    assert res.platform == MeetingPlatform.UNKNOWN
    assert res.status == "UNSUPPORTED_URL"


def test_meeting_joiner_block_in_registry():
    mgr = BlockManager(auto_load_standard=True)
    block = mgr.get_block("actions.meeting.joiner")
    assert block is not None
    assert block.metadata.name == "Meeting Joiner Block"
    assert block.is_enabled is True


def test_api_meeting_join_endpoint():
    mock_res = MeetingJoinResult(
        success=True,
        platform=MeetingPlatform.GOOGLE_MEET,
        meeting_id="hsw-hmdc-gqc",
        normalized_url="https://meet.google.com/hsw-hmdc-gqc",
        status="JOINED_MOCK",
        message="Mock joined successfully",
        duration_ms=45.2
    )
    with patch("autogenos.components.meeting_agent.MeetingAgent.join_meeting_fast", new_callable=AsyncMock) as mock_join:
        mock_join.return_value = mock_res
        resp = client.post(
            "/api/v1/meet/join",
            json={
                "url": "https://meet.google.com/hsw-hmdc-gqc",
                "display_name": "Meet Shah",
                "mute_mic": True
            }
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["platform"] == "google_meet"
        assert data["meeting_id"] == "hsw-hmdc-gqc"
