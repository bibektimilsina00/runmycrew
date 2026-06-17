"""YouTube channel RSS feed parser — zero-quota new-video detection.

Every public YouTube channel exposes an Atom feed at
``https://www.youtube.com/feeds/videos.xml?channel_id={ID}`` that lists
the channel's most recent ~15 uploads. The feed updates within ~10
minutes of an upload and costs no Data API quota — perfect for the
`new_video` trigger when watching other channels.

The parser intentionally keeps Python's stdlib `xml.etree` rather than
pulling lxml — the feed is small (<30KB) and well-formed by YouTube.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

# YouTube uses the Atom + Media namespaces. We pre-register the prefixes
# so XPath strings stay readable.
_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mf/rss/",
}


def channel_feed_url(channel_id: str) -> str:
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def parse_feed(xml_bytes: bytes | str) -> list[dict[str, Any]]:
    """Parse a YouTube channel RSS feed → list of video dicts.

    Returns `[]` on malformed XML rather than raising — the trigger
    falls back to "nothing new this tick" instead of hard-failing the
    workflow."""
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError:
        return []
    entries = root.findall("atom:entry", _NS)
    out: list[dict[str, Any]] = []
    for entry in entries:
        video_id_el = entry.find("yt:videoId", _NS)
        channel_id_el = entry.find("yt:channelId", _NS)
        title_el = entry.find("atom:title", _NS)
        published_el = entry.find("atom:published", _NS)
        updated_el = entry.find("atom:updated", _NS)
        link_el = entry.find("atom:link", _NS)
        author_el = entry.find("atom:author/atom:name", _NS)

        if video_id_el is None or video_id_el.text is None:
            continue

        out.append(
            {
                "video_id": video_id_el.text.strip(),
                "channel_id": channel_id_el.text.strip()
                if channel_id_el is not None and channel_id_el.text
                else "",
                "title": title_el.text.strip() if title_el is not None and title_el.text else "",
                "published_at": published_el.text.strip()
                if published_el is not None and published_el.text
                else "",
                "updated_at": updated_el.text.strip()
                if updated_el is not None and updated_el.text
                else "",
                "url": link_el.get("href")
                if link_el is not None
                else f"https://www.youtube.com/watch?v={video_id_el.text.strip()}",
                "channel_title": author_el.text.strip()
                if author_el is not None and author_el.text
                else "",
            }
        )
    return out
