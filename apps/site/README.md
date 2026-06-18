# fuse-site

Marketing site for [Fuse](https://fuse.bibektimilsina.tech). Next.js 16 (App Router) + Tailwind v4 + shadcn/ui.

## Run

```bash
pnpm --filter fuse-site dev      # http://localhost:3100
pnpm --filter fuse-site build
pnpm --filter fuse-site typecheck
```

## Structure

Mirrors `apps/web` — modular by feature, thin route shells.

```
src/
├── app/                 # Next.js App Router (routes only — composition)
│   ├── layout.tsx       # html shell, fonts, providers
│   ├── globals.css      # design tokens + Tailwind v4 theme
│   └── page.tsx         # landing route
├── components/ui/       # shadcn primitives (managed by shadcn CLI)
├── features/            # one folder per marketing surface
│   └── marketing/
│       ├── components/  # presentational React components
│       ├── data/        # static copy (separate from JSX)
│       └── index.ts     # public barrel — only consumers
├── shared/              # cross-feature primitives
│   ├── components/      # Container, SiteHeader, SiteFooter, ...
│   ├── layouts/         # MarketingLayout, DocsLayout, ...
│   ├── hooks/
│   ├── utils/
│   └── constants/       # routes.ts (single source of truth for URLs)
└── lib/                 # shadcn utils (cn) — leave to the CLI
```

### Adding a new section

1. Drop the component in `src/features/<feature>/components/`.
2. Co-locate any copy in `src/features/<feature>/data/`.
3. Export from `src/features/<feature>/index.ts`.
4. Import into the route under `src/app/.../page.tsx` and compose.

Do **not** import individual files from outside a feature — go through the barrel so internal renames stay free.

### Design tokens

`src/app/globals.css` defines two schemes:

- `:root` → light surface, indigo primary, slate text ramp.
- `.dark` → Linear-style near-black + muted indigo (1:1 mirror of `apps/web`'s default dark theme).

Brand tokens (`--primary` = `#5e6ad2`, `--background`, `--card`, `--ring`, etc) feed every shadcn primitive automatically, so the marketing site reads the same as the product app.

## Conventions

- `cursor-pointer` on interactive elements (shadcn provides it; keep it for raw buttons too).
- `text-balance` on hero headings.
- Use `Container` for horizontal gutters; do not roll your own `max-w-*` per page.
- Stick to the radius scale defined by `--radius` (`rounded-sm/md/lg/xl`). No `rounded-[20px]` one-offs.
- Icons via `lucide-react`. No emoji icons.
- Animations via `framer-motion`; respect `prefers-reduced-motion`.
