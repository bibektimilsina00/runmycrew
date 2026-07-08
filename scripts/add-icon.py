#!/usr/bin/env python3
"""Add a brand icon SVG to a node folder — paste, done.

The backend serves icons by filename (the slug): a node's `icon_slug`
resolves to `<slug>.svg` under its node folder (or `node_system/icons/`).
See `apps/api/app/features/icons/`. This script drops a pasted SVG in the
right place with the right name so `/api/v1/icons/<slug>` picks it up.

Usage
-----
    python3 scripts/add-icon.py <node>          # then paste SVG, Ctrl-D
    python3 scripts/add-icon.py <node> --strip  # best-effort wordmark trim
    pbpaste | python3 scripts/add-icon.py <node>   # pipe from clipboard (macOS)

If <node> is omitted it prompts for it. The file is written as
`apps/api/app/node_system/nodes/<node>/<icon_slug>.svg` (icon_slug read
from the node's manifest.py / *.py; falls back to the folder name).

--strip is a BEST-EFFORT trim of a horizontal wordmark down to its left
mark (keeps <path>/<g> whose first coordinate sits in the left square,
crops the viewBox). It only helps vector logos with the mark on the left;
verify the result. Rasters (embedded <image>) can't be stripped.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NODES = REPO / "apps" / "api" / "app" / "node_system" / "nodes"


def die(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    raise SystemExit(1)


def resolve_slug(node_dir: Path, node: str) -> str:
    """icon_slug="..." from any .py in the node folder, else the folder name."""
    for py in node_dir.glob("*.py"):
        m = re.search(r'icon_slug\s*=\s*["\']([^"\']+)["\']', py.read_text())
        if m:
            return m.group(1)
    return node


def strip_wordmark(svg: str) -> tuple[str, str]:
    """Best-effort: keep the left mark, drop wordmark text. Returns (svg, note)."""
    if "<image" in svg:
        return svg, "raster (<image>) — can't strip; saved as-is"

    vb = re.search(r'viewBox="([-\d.\s]+)"', svg)
    if vb:
        _, _, w, h = (float(x) for x in vb.group(1).split())
    else:
        wm = re.search(r'\bwidth="([\d.]+)"', svg)
        hm = re.search(r'\bheight="([\d.]+)"', svg)
        if not (wm and hm):
            return svg, "no viewBox/size — saved as-is"
        w, h = float(wm.group(1)), float(hm.group(1))

    if w < h * 1.6:
        return svg, "not a wide wordmark — saved as-is"

    # Keep elements whose first coordinate is in the left ~square (the mark).
    limit = h * 1.4
    kept, dropped = [], 0

    def first_x(el: str) -> float:
        m = re.search(r'\bd="[Mm]\s*(-?[\d.]+)', el)
        return float(m.group(1)) if m else 1e9

    elements = re.findall(r"<path\b.*?(?:/>|</path>)", svg, re.S)
    if not elements:
        return svg, "no <path> elements — saved as-is (may be grouped/raster)"
    for el in elements:
        if first_x(el) < limit:
            kept.append(el)
        else:
            dropped += 1

    if not kept or dropped == 0:
        return svg, f"trim skipped (kept {len(kept)}, dropped {dropped}) — saved as-is"

    body = "".join(kept)
    out = (
        f'<svg viewBox="0 0 {round(h)} {round(h)}" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg">{body}</svg>\n'
    )
    return out, f"stripped: kept {len(kept)} mark path(s), dropped {dropped} text path(s) — VERIFY"


def tty_prompt(msg: str) -> str | None:
    """Ask on the controlling terminal, not stdin (stdin carries the pasted
    SVG / may be a pipe). Returns None when there is no tty."""
    try:
        with open("/dev/tty", "r+") as tty:
            tty.write(msg)
            tty.flush()
            return tty.readline().strip()
    except OSError:
        return None


def main() -> None:
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    do_strip = "--strip" in flags
    force = "--force" in flags

    node = args[0] if args else (tty_prompt("Node folder: ") or die("no node given"))
    node_dir = NODES / node
    if not node_dir.is_dir():
        die(f"no node folder: {node_dir.relative_to(REPO)}")

    slug = resolve_slug(node_dir, node)
    out_path = node_dir / f"{slug}.svg"

    # Decide overwrite BEFORE consuming stdin (so no prompt fights the paste).
    if out_path.exists() and not force:
        ans = tty_prompt(f"{out_path.name} exists — overwrite? [y/N] ")
        if ans is None:
            die(f"{out_path.name} exists — re-run with --force")
        if ans.lower() != "y":
            die("aborted")

    if sys.stdin.isatty():
        print(f"→ will write {out_path.relative_to(REPO)}")
        print("Paste the SVG, then press Ctrl-D:")
    svg = sys.stdin.read().strip()
    if not svg.startswith("<") or "svg" not in svg[:200].lower():
        die("that doesn't look like an SVG")

    note = "saved as-is"
    if do_strip:
        svg, note = strip_wordmark(svg)

    out_path.write_text(svg if svg.endswith("\n") else svg + "\n")
    print(f"✓ wrote {out_path.relative_to(REPO)}  (slug: {slug})")
    print(f"  {note}")
    print(
        "  served at /api/v1/icons/" + slug + " (backend restart / next `make api` picks it up)"
    )


if __name__ == "__main__":
    main()
