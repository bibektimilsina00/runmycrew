"""Unit tests for YouTube action node helpers + RSS parser."""

from __future__ import annotations

import pytest

from apps.api.app.node_system.nodes.google.gyt.gyt_node import (
    GoogleYouTubeProperties,
    _flatten_channel,
    _flatten_comment,
    _flatten_playlist,
    _flatten_subscription,
    _flatten_video,
)
from apps.api.app.node_system.nodes.google.gyt.gyt_rss import parse_feed

# ── _flatten_video ─────────────────────────────────────────────────────


def test_flatten_video_extracts_common_fields():
    video = {
        "id": "VIDEOID",
        "snippet": {
            "title": "My Video",
            "description": "desc",
            "channelId": "UCabc",
            "channelTitle": "Channel",
            "publishedAt": "2026-01-01T00:00:00Z",
            "thumbnails": {"high": {"url": "https://thumb.example/x.jpg"}},
            "tags": ["a", "b"],
            "categoryId": "22",
        },
        "statistics": {
            "viewCount": "1234",
            "likeCount": "56",
            "commentCount": "7",
        },
        "contentDetails": {"duration": "PT5M30S"},
    }
    flat = _flatten_video(video)
    assert flat["id"] == "VIDEOID"
    assert flat["title"] == "My Video"
    assert flat["channel_id"] == "UCabc"
    assert flat["view_count"] == 1234
    assert flat["like_count"] == 56
    assert flat["comment_count"] == 7
    assert flat["duration"] == "PT5M30S"
    assert flat["thumbnail_url"] == "https://thumb.example/x.jpg"
    assert flat["url"] == "https://www.youtube.com/watch?v=VIDEOID"


def test_flatten_video_handles_search_id_shape():
    """`search.list` returns `id` as a dict `{kind, videoId}` — the
    flattener should pluck the inner id rather than store the dict."""
    video = {"id": {"kind": "youtube#video", "videoId": "VID"}, "snippet": {}}
    assert _flatten_video(video)["id"] == "VID"


def test_flatten_video_falls_back_when_thumbnails_missing():
    video = {"id": "V", "snippet": {"title": "x"}}
    assert _flatten_video(video)["thumbnail_url"] == ""


def test_flatten_video_handles_missing_statistics():
    video = {"id": "V", "snippet": {}}
    flat = _flatten_video(video)
    assert flat["view_count"] == 0
    assert flat["like_count"] == 0
    assert flat["comment_count"] == 0


# ── _flatten_comment ───────────────────────────────────────────────────


def test_flatten_comment_unwraps_top_level_comment_thread():
    thread = {
        "id": "THREAD1",
        "snippet": {
            "videoId": "VID",
            "totalReplyCount": 3,
            "canReply": True,
            "topLevelComment": {
                "id": "COMMENT1",
                "snippet": {
                    "authorDisplayName": "Alice",
                    "authorChannelId": {"value": "UCalice"},
                    "textOriginal": "hello",
                    "publishedAt": "2026-01-01T00:00:00Z",
                    "likeCount": 4,
                },
            },
        },
    }
    flat = _flatten_comment(thread)
    assert flat["id"] == "COMMENT1"
    assert flat["video_id"] == "VID"
    assert flat["author"] == "Alice"
    assert flat["author_channel_id"] == "UCalice"
    assert flat["text"] == "hello"
    assert flat["like_count"] == 4
    assert flat["total_reply_count"] == 3
    assert flat["can_reply"] is True


def test_flatten_comment_handles_bare_comment_resource():
    """Replies arrive as bare `comments#comment` resources (no
    `topLevelComment` wrapper)."""
    comment = {
        "id": "REPLY1",
        "snippet": {
            "parentId": "COMMENT1",
            "authorDisplayName": "Bob",
            "textOriginal": "reply",
            "publishedAt": "2026-01-02T00:00:00Z",
            "likeCount": 0,
        },
    }
    flat = _flatten_comment(comment)
    assert flat["id"] == "REPLY1"
    assert flat["parent_id"] == "COMMENT1"
    assert flat["author"] == "Bob"


# ── _flatten_subscription ─────────────────────────────────────────────


def test_flatten_subscription_extracts_resource_id_channel():
    sub = {
        "id": "SUB1",
        "snippet": {
            "title": "Some Subscriber",
            "publishedAt": "2026-01-01T00:00:00Z",
            "resourceId": {"channelId": "UCsubscriber"},
            "thumbnails": {"default": {"url": "https://thumb"}},
        },
    }
    flat = _flatten_subscription(sub)
    assert flat["id"] == "SUB1"
    assert flat["subscriber_channel_id"] == "UCsubscriber"
    assert flat["subscriber_title"] == "Some Subscriber"
    assert flat["thumbnail_url"] == "https://thumb"


# ── _flatten_playlist ─────────────────────────────────────────────────


def test_flatten_playlist_extracts_common_fields():
    playlist = {
        "id": "PL1",
        "snippet": {"title": "Watch later", "channelId": "UC", "channelTitle": "Ch"},
        "status": {"privacyStatus": "private"},
        "contentDetails": {"itemCount": "12"},
    }
    flat = _flatten_playlist(playlist)
    assert flat["id"] == "PL1"
    assert flat["title"] == "Watch later"
    assert flat["item_count"] == 12
    assert flat["privacy"] == "private"


# ── _flatten_channel ──────────────────────────────────────────────────


def test_flatten_channel_extracts_common_fields():
    channel = {
        "id": "UCabc",
        "snippet": {
            "title": "My channel",
            "customUrl": "@me",
            "country": "US",
        },
        "statistics": {
            "subscriberCount": "10000",
            "viewCount": "1234567",
            "videoCount": "50",
        },
    }
    flat = _flatten_channel(channel)
    assert flat["id"] == "UCabc"
    assert flat["title"] == "My channel"
    assert flat["custom_url"] == "@me"
    assert flat["subscriber_count"] == 10000
    assert flat["video_count"] == 50
    assert flat["view_count"] == 1234567


# ── resource_id coercion ──────────────────────────────────────────────


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ({"id": "VID1", "title": "X"}, "VID1"),
        ("VID2", "VID2"),
        (None, None),
        ("", None),
        ({}, None),
        ({"id": ""}, None),
    ],
)
def test_resource_id_coercion(raw, expected):
    props = GoogleYouTubeProperties(video_id=raw)
    assert props.video_id == expected


# ── RSS parser ────────────────────────────────────────────────────────


_VALID_FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns:media="http://search.yahoo.com/mf/rss/"
      xmlns="http://www.w3.org/2005/Atom">
  <link rel="self" href="http://www.youtube.com/feeds/videos.xml?channel_id=UCabc"/>
  <id>yt:channel:UCabc</id>
  <yt:channelId>UCabc</yt:channelId>
  <title>Test Channel</title>
  <entry>
    <id>yt:video:VID1</id>
    <yt:videoId>VID1</yt:videoId>
    <yt:channelId>UCabc</yt:channelId>
    <title>First video</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=VID1"/>
    <author><name>Test Channel</name><uri>http://www.youtube.com/channel/UCabc</uri></author>
    <published>2026-06-01T12:00:00+00:00</published>
    <updated>2026-06-01T12:00:00+00:00</updated>
  </entry>
  <entry>
    <id>yt:video:VID2</id>
    <yt:videoId>VID2</yt:videoId>
    <yt:channelId>UCabc</yt:channelId>
    <title>Second video</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=VID2"/>
    <author><name>Test Channel</name><uri>http://www.youtube.com/channel/UCabc</uri></author>
    <published>2026-06-02T12:00:00+00:00</published>
    <updated>2026-06-02T12:00:00+00:00</updated>
  </entry>
</feed>
"""


def test_rss_parse_extracts_each_entry():
    items = parse_feed(_VALID_FEED)
    assert len(items) == 2
    assert items[0]["video_id"] == "VID1"
    assert items[0]["title"] == "First video"
    assert items[0]["channel_id"] == "UCabc"
    assert items[0]["channel_title"] == "Test Channel"
    assert items[0]["published_at"] == "2026-06-01T12:00:00+00:00"
    assert items[0]["url"] == "https://www.youtube.com/watch?v=VID1"
    assert items[1]["video_id"] == "VID2"


def test_rss_parse_returns_empty_on_malformed_xml():
    assert parse_feed(b"not xml at all") == []


def test_rss_parse_returns_empty_on_feed_without_entries():
    feed = b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"></feed>'
    assert parse_feed(feed) == []
