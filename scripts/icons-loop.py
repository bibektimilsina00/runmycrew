#!/usr/bin/env python3
"""Walk node folders alphabetically and add a brand icon to each — one loop.

Starting from a given node (default: the first without an icon), it visits
every folder in `node_system/nodes/` in alphabetical order and, for each,
asks you to paste an SVG. Paste it (then a blank line) and it writes
`<icon_slug>.svg` in that folder; press Enter on an empty prompt to skip.
Folders that already have an SVG are skipped automatically. `q` quits.

Usage
-----
    python3 scripts/icons-loop.py            # start at first icon-less folder
    python3 scripts/icons-loop.py gitlab     # start at 'gitlab' onward
    python3 scripts/icons-loop.py gitlab --strip   # best-effort wordmark trim
    python3 scripts/icons-loop.py gitlab --all     # also revisit folders that already have an icon

Per folder:
  - paste the SVG, then press Enter on a BLANK line to save it
  - press Enter immediately (empty) to skip this folder
  - type `q` + Enter to quit the whole loop

The filename matches the node's `icon_slug` (from its manifest / *.py; falls
back to the folder name) so `/api/v1/icons/<slug>` resolves it.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
NODES = REPO / "apps" / "api" / "app" / "node_system" / "nodes"


def resolve_slug(node_dir: Path) -> str:
    for py in node_dir.glob("*.py"):
        m = re.search(r'icon_slug\s*=\s*["\']([^"\']+)["\']', py.read_text())
        if m:
            return m.group(1)
    return node_dir.name


def strip_wordmark(svg: str) -> tuple[str, str]:
    if "<image" in svg:
        return svg, "raster — saved as-is"
    vb = re.search(r'viewBox="([-\d.\s]+)"', svg)
    if vb:
        nums = vb.group(1).split()
        if len(nums) == 4:
            _, _, w, h = (float(x) for x in nums)
        else:
            return svg, "odd viewBox — saved as-is"
    else:
        wm, hm = re.search(r'\bwidth="([\d.]+)"', svg), re.search(r'\bheight="([\d.]+)"', svg)
        if not (wm and hm):
            return svg, "no size — saved as-is"
        w, h = float(wm.group(1)), float(hm.group(1))
    if w < h * 1.6:
        return svg, "not a wordmark — saved as-is"
    limit = h * 1.4

    def first_x(el: str) -> float:
        m = re.search(r'\bd="[Mm]\s*(-?[\d.]+)', el)
        return float(m.group(1)) if m else 1e9

    elements = re.findall(r"<path\b.*?(?:/>|</path>)", svg, re.S)
    if not elements:
        return svg, "grouped/no paths — saved as-is"
    kept = [e for e in elements if first_x(e) < limit]
    dropped = len(elements) - len(kept)
    if not kept or dropped == 0:
        return svg, f"trim skipped (kept {len(kept)}) — saved as-is"
    out = (
        f'<svg viewBox="0 0 {round(h)} {round(h)}" fill="none" '
        f'xmlns="http://www.w3.org/2000/svg">{"".join(kept)}</svg>\n'
    )
    return out, f"stripped: kept {len(kept)} / dropped {dropped} — VERIFY"


def read_paste() -> str | None:
    """Read a pasted SVG. Returns the SVG string, '' to skip, or None to quit.

    Reads the terminal in RAW mode so a long single-line SVG isn't truncated
    at the ~1024-char canonical line limit (the reason big pastes 'froze'),
    and stops the instant the SVG closes (`</svg>`) — no Enter needed after
    the paste. Enter with nothing pasted = skip; 'q' = quit. Falls back to
    reading all of stdin when piped / no tty.
    """
    import os

    fd = sys.stdin.fileno()
    if not os.isatty(fd):
        return sys.stdin.read().strip() or ""

    try:
        import termios
        import tty
    except ImportError:  # non-unix — best-effort line read
        line = sys.stdin.readline()
        return None if line.strip().lower() == "q" else line.strip()

    old = termios.tcgetattr(fd)
    buf = ""
    try:
        tty.setcbreak(fd)  # non-canonical: chars stream in immediately, no line cap
        while True:
            chunk = os.read(fd, 65536).decode("utf-8", "replace")
            if not chunk:
                return buf.strip() or None
            for ch in chunk:
                if not buf and ch in ("\r", "\n"):
                    return ""  # nothing pasted -> skip
                if not buf and ch.lower() == "q":
                    return None  # quit the loop
                buf += ch
            if "</svg" in buf.lower() and buf.rstrip().endswith(">"):
                break  # svg closed -> save
        return buf.strip()
    finally:
        termios.tcflush(fd, termios.TCIFLUSH)  # drop stray trailing newline
        termios.tcsetattr(fd, termios.TCSADRAIN, old)


def main() -> None:
    flags = {a for a in sys.argv[1:] if a.startswith("--")}
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    do_strip = "--strip" in flags
    revisit = "--all" in flags
    start = args[0] if args else ""

    folders = sorted(d for d in NODES.iterdir() if d.is_dir())
    folders = [d for d in folders if d.name >= start]
    if not revisit:
        folders = [d for d in folders if not any(d.glob("*.svg"))]

    if not folders:
        print("Nothing to do — every folder from here already has an icon.")
        return

    total = len(folders)
    print(f"{total} folder(s) to visit, starting at '{folders[0].name}'.")
    print("Paste SVG + Enter to save · Enter alone to skip · 'q' to quit.\n")

    saved = skipped = 0
    for i, node_dir in enumerate(folders, 1):
        slug = resolve_slug(node_dir)
        print(f"[{i}/{total}] {node_dir.name}  →  {slug}.svg")
        svg = read_paste()
        if svg is None:
            print("\nquit.")
            break
        if svg == "":
            skipped += 1
            print("  skipped\n")
            continue
        if not svg.lstrip().startswith("<"):
            skipped += 1
            print("  not an SVG — skipped\n")
            continue
        note = "saved as-is"
        if do_strip:
            svg, note = strip_wordmark(svg)
        (node_dir / f"{slug}.svg").write_text(svg if svg.endswith("\n") else svg + "\n")
        saved += 1
        print(f"  ✓ wrote {slug}.svg  ({note})\n")

    print(f"\ndone — {saved} saved, {skipped} skipped.")
    print("Restart the backend (make dev-all) to pick up new icons.")


if __name__ == "__main__":
    main()
