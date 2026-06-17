"""Unit tests for the YouTube trigger diff logic.

The trigger's poll path is asynchronous and hits the YouTube API, so we
focus on the property validators here. End-to-end behaviour is covered
implicitly by the helper tests on the flatteners + RSS parser the
trigger uses.
"""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.gyt.gyt_trigger import (
    EVENT_NEW_COMMENT,
    EVENT_NEW_SUBSCRIBER,
    EVENT_NEW_VIDEO,
    EVENT_REPLY_TO_MY_COMMENT,
    EVENT_SEARCH_MATCH,
    GoogleYouTubeTriggerProperties,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (EVENT_NEW_COMMENT, EVENT_NEW_COMMENT),
        (EVENT_NEW_SUBSCRIBER, EVENT_NEW_SUBSCRIBER),
        (EVENT_NEW_VIDEO, EVENT_NEW_VIDEO),
        (EVENT_SEARCH_MATCH, EVENT_SEARCH_MATCH),
        (EVENT_REPLY_TO_MY_COMMENT, EVENT_REPLY_TO_MY_COMMENT),
        ("bogus", EVENT_NEW_COMMENT),
        ("", EVENT_NEW_COMMENT),
        (None, EVENT_NEW_COMMENT),
    ],
)
def test_event_type_coercion(raw, expected):
    props = GoogleYouTubeTriggerProperties(event_type=raw)
    assert props.event_type == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"id": "VID1", "title": "X"}, "VID1"),
        ("VID2", "VID2"),
        (None, ""),
        ("", ""),
    ],
)
def test_video_id_coercion(raw, expected):
    props = GoogleYouTubeTriggerProperties(video_id=raw)
    assert props.video_id == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"id": "UCabc", "title": "Some Channel"}, "UCabc"),
        ("UCxyz", "UCxyz"),
        (None, ""),
        ("", ""),
    ],
)
def test_watched_channel_coercion(raw, expected):
    props = GoogleYouTubeTriggerProperties(watched_channel_id=raw)
    assert props.watched_channel_id == expected
