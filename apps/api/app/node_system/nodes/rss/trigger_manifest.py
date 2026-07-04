"""RSS / Atom polling trigger — manifest form.

No credential — RSS feeds are public URLs. Ships as an unauthenticated
poller by setting `credential_type=None` on the manifest and
`token_field=[]` so the scheduler's cred lookup is bypassed.

Parses RSS 2.0 + Atom 1.0 via stdlib `xml.etree.ElementTree` — no
new dependency. Handles the common cases; unusual feeds with custom
namespaces or heavy CDATA may lose fields but the id + link + title
survive.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Any

import httpx

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)
from apps.api.app.node_system.scaffolds.field_resolvers import resolve_template

# Atom namespace — used for prefix-agnostic tag matching.
_ATOM_NS = "http://www.w3.org/2005/Atom"


def _local(tag: str) -> str:
    """Strip any XML namespace prefix so we can match on local name."""
    return tag.split("}", 1)[1] if "}" in tag else tag


def _text(elem: ET.Element | None) -> str:
    if elem is None:
        return ""
    return (elem.text or "").strip()


def _link_from_atom(entry: ET.Element) -> str:
    """Atom entries have <link href="..." rel="alternate"/> — pull the
    first alternate (or the first link) so downstream code sees a URL,
    not the raw element."""
    best = ""
    for child in entry:
        if _local(child.tag) != "link":
            continue
        href = child.attrib.get("href") or ""
        rel = child.attrib.get("rel") or "alternate"
        if rel == "alternate" and href:
            return href
        if not best and href:
            best = href
    return best


def _parse_rss_item(item: ET.Element) -> dict[str, Any]:
    """RSS 2.0 <item>. Fields: title, link, description, pubDate, guid."""
    fields = {_local(c.tag): c for c in item}
    guid_elem = fields.get("guid")
    guid = _text(guid_elem)
    link = _text(fields.get("link"))
    return {
        "id": guid or link,
        "title": _text(fields.get("title")),
        "link": link,
        "description": _text(fields.get("description")),
        "published": _text(fields.get("pubDate")),
        "author": _text(fields.get("author")) or _text(fields.get("creator")),
        "categories": [(c.text or "").strip() for c in item if _local(c.tag) == "category"],
        "guid": guid,
    }


def _parse_atom_entry(entry: ET.Element) -> dict[str, Any]:
    """Atom 1.0 <entry>. Fields: id, title, link, summary/content, updated, published."""
    fields = {_local(c.tag): c for c in entry}
    entry_id = _text(fields.get("id"))
    link = _link_from_atom(entry)
    published = _text(fields.get("published")) or _text(fields.get("updated"))
    author_elem = fields.get("author")
    author_name = ""
    if author_elem is not None:
        name_elem = author_elem.find(f"{{{_ATOM_NS}}}name")
        if name_elem is None:
            for c in author_elem:
                if _local(c.tag) == "name":
                    name_elem = c
                    break
        author_name = _text(name_elem)
    return {
        "id": entry_id or link,
        "title": _text(fields.get("title")),
        "link": link,
        "description": _text(fields.get("summary")) or _text(fields.get("content")),
        "published": published,
        "author": author_name,
        "categories": [
            (c.attrib.get("term") or "").strip() for c in entry if _local(c.tag) == "category"
        ],
        "guid": entry_id,
    }


def _flatten_item(item):
    # Items are already flat when they come from our parser — pass through.
    return dict(item) if isinstance(item, dict) else {}


register_flatten("rss.item", _flatten_item)


async def _walk_rss(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,  # noqa: ARG001 — unauthenticated
    props: Any,
) -> list[dict[str, Any]]:
    """Fetch the feed URL and parse either RSS 2.0 or Atom 1.0.
    Detects feed kind by root tag."""
    feed_url = resolve_template("{feed_url}", props) or ""
    if not feed_url:
        return []
    resp = await client.get(
        feed_url,
        headers={
            "User-Agent": "RunMyCrew RSS Poller/1.0",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
        },
        timeout=30,
        follow_redirects=True,
    )
    resp.raise_for_status()
    try:
        root = ET.fromstring(resp.content)
    except ET.ParseError as exc:
        raise RuntimeError(f"RSS feed parse failed: {exc}") from exc
    root_local = _local(root.tag)
    items: list[dict[str, Any]] = []
    if root_local == "rss":
        # <rss><channel><item>...</item></channel></rss>
        for channel in root:
            if _local(channel.tag) != "channel":
                continue
            for item in channel:
                if _local(item.tag) == "item":
                    items.append(_parse_rss_item(item))
    elif root_local == "feed":
        # Atom: <feed><entry>...</entry></feed>
        for entry in root:
            if _local(entry.tag) == "entry":
                items.append(_parse_atom_entry(entry))
    elif root_local == "rdf" or root_local == "RDF":
        # RSS 1.0 (RDF-based) — items are direct children of <rdf:RDF>.
        for child in root:
            if _local(child.tag) == "item":
                items.append(_parse_rss_item(child))
    return items


MANIFEST = PollingTriggerManifest(
    type="trigger.rss",
    name="RSS Feed",
    description=(
        "Poll any RSS 2.0, Atom 1.0, or RSS 1.0 feed for new items. "
        "Public URL only — no credential required."
    ),
    icon_slug="rss",
    color="#1c1c1c",
    base_url="",
    # `credential_type=None` — unauthenticated poller. Factory skips
    # the credential inspector row; scheduler skips the cred lookup.
    credential_type=None,
    token_field=[],
    auth="none",
    provider="rss",
    default_poll_interval_seconds=300,  # 5 min — most feeds are slow
    min_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="feed_url",
            label="Feed URL",
            type="string",
            required=True,
            placeholder="https://example.com/feed.xml",
        ),
    ],
    events=[
        PollingEvent(
            id="new_item",
            label="New Feed Item",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="rss.item",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "link", "type": "string"},
        {"label": "description", "type": "string"},
        {"label": "published", "type": "string"},
        {"label": "author", "type": "string"},
        {"label": "categories", "type": "array"},
    ],
    paginate_fn=_walk_rss,
)
