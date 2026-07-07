# Brand icons

Drop a `<slug>.svg` here and the `/api/v1/icons/<slug>` endpoint serves it —
no frontend change, no registry to edit.

`<slug>` is the value the UI already asks for:

- a **node**'s lowercase `icon` (e.g. a node with `icon: "youtube"` → `youtube.svg`)
- a **provider/integration**'s `icon_slug` (`credential_manager/api_keys.py`,
  e.g. `mistral_parse.svg`, `slack.svg`)

## Where icons can live

1. **This shared folder** — `node_system/icons/<slug>.svg` (wins on a clash).
2. **Colocated with a node** — `node_system/nodes/<node>/<slug>.svg`, so a node
   and its icon are one folder.

The resolver (`features/icons/service.py`) scans both by filename. A
deploy/restart picks up newly-added icons.

## Notes

- Full-colour SVG preferred (rendered as `<img>`, so CSS can't recolour it).
- Square viewBox; sized with `object-contain`.
- No local file for a slug → the UI shows a blank tile (there is **no** CDN
  fallback).
