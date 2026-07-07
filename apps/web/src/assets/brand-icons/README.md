# Local brand icons

Hand-curated brand SVGs that **override** the `thesvg` CDN in `BrandIcon`.

## How to add one

Drop an SVG file here named after the **slug**, lowercase:

```
apps/web/src/assets/brand-icons/<slug>.svg
```

The slug is:

- for **integrations/credentials** — the provider's `icon_slug`
  (backend `apps/api/app/credential_manager/api_keys.py`), e.g. `mistral_parse.svg`, `slack.svg`.
- for **nodes** — the node's lowercase/kebab `icon` value
  (e.g. a node with `icon: "youtube"` → `youtube.svg`).

Resolution order in `BrandIcon` (`../../features/workflow-editor/utils/BrandIcon.tsx`):

1. **Local SVG here** (this folder) — if a matching `<slug>.svg` exists, it wins.
2. **`thesvg` CDN** — fallback for slugs with no local file.
3. **Blank tile** — if both miss.

Files here are bundled at build time via `import.meta.glob`, so after adding one,
rebuild (or the dev server hot-reloads). No registry/import to edit — the filename
is the key.

## Tips

- Prefer the full-colour SVG (icons sit on a neutral tile; CSS can't recolour an `<img>`).
- Keep viewBox square; the renderer sizes with `object-contain`.
