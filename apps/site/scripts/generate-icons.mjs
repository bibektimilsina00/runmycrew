#!/usr/bin/env node
/**
 * Generate PNG icon variants + OG image from the brand SVG.
 *
 * Run from repo root:
 *   pnpm --filter runmycrew-site exec node scripts/generate-icons.mjs
 *
 * Outputs into apps/site/public/:
 *   - favicon-16x16.png
 *   - favicon-32x32.png
 *   - apple-touch-icon.png         (180x180, iOS home screen)
 *   - icon-192.png                 (PWA manifest)
 *   - icon-512.png                 (PWA manifest, maskable)
 *   - og-default.png               (1200x630, Open Graph + Twitter card)
 *
 * Source of truth: apps/site/public/favicon.svg.
 * Re-run any time the brand mark changes.
 */
import sharp from 'sharp'
import { readFile, writeFile, mkdir } from 'node:fs/promises'
import { join, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const PUBLIC = join(HERE, '..', 'public')

const BG = '#08090a'
const BRAND_PURPLE = '#5e6ad2'
const TEXT_PRIMARY = '#edeef0'
const TEXT_MUTED = '#8a8f98'

// Three-petal spinner brand mark. Petal source path:
//   M16 16 C 12.4 13, 12.4 6.4, 16 3 C 19.6 6.4, 19.6 13, 16 16 Z
// Renders the petal pointing up from the centre, then duplicates at
// rotations 0/120/240 with descending opacity (1.0 / 0.66 / 0.4) for
// the "spinning" look. The centre `<circle>` caps the petal bases so
// the focal point reads as a single dot instead of three overlapping
// curves.
const PETAL = 'M16 16 C 12.4 13, 12.4 6.4, 16 3 C 19.6 6.4, 19.6 13, 16 16 Z'
const MARK_GROUP = ({ centerFill = BG } = {}) => `
  <g>
    <path d="${PETAL}" fill="${BRAND_PURPLE}"/>
    <path d="${PETAL}" fill="${BRAND_PURPLE}" opacity="0.66" transform="rotate(120 16 16)"/>
    <path d="${PETAL}" fill="${BRAND_PURPLE}" opacity="0.4"  transform="rotate(240 16 16)"/>
  </g>
  <circle cx="16" cy="16" r="2.4" fill="${centerFill}"/>`

// Transparent — for favicons, app-store icons, and any surface where
// the host UI provides the background. The centre cap is the brand-bg
// colour so the overlap of the three petal bases still reads as a
// single accent dot on dark surfaces; on light surfaces it presents as
// a small dark dot, which is consistent with the wordmark.
const TRANSPARENT_SVG = (size) => `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="${size}" height="${size}" fill="none">
${MARK_GROUP()}
</svg>`.trim()

// Maskable variant — REQUIRES an opaque background because Android
// masks the icon to a circle / squircle / teardrop and any transparent
// pixel inside the safe area shows the OS background. Safe-area scaled
// to 87.5% per the maskable-icon spec.
const MASKABLE_SVG = (size) => `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32" width="${size}" height="${size}">
  <rect width="32" height="32" fill="${BG}"/>
  <g transform="translate(2 2) scale(0.875)">
    <g>
      <path d="${PETAL}" fill="${BRAND_PURPLE}"/>
      <path d="${PETAL}" fill="${BRAND_PURPLE}" opacity="0.66" transform="rotate(120 16 16)"/>
      <path d="${PETAL}" fill="${BRAND_PURPLE}" opacity="0.4"  transform="rotate(240 16 16)"/>
    </g>
    <circle cx="16" cy="16" r="2.4" fill="${BG}"/>
  </g>
</svg>`.trim()

// Open Graph card — 1200x630. Brand mark on the left, headline + tagline
// stacked on the right. Stays under Twitter's 1MB cap easily.
const OG_SVG = `
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 630" width="1200" height="630">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%"  stop-color="#0c0d0f"/>
      <stop offset="100%" stop-color="${BG}"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.18" cy="0.42" r="0.55">
      <stop offset="0%"  stop-color="${BRAND_PURPLE}" stop-opacity="0.35"/>
      <stop offset="100%" stop-color="${BRAND_PURPLE}" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <rect width="1200" height="630" fill="url(#bg)"/>
  <rect width="1200" height="630" fill="url(#glow)"/>

  <!-- Brand mark, 140px tall, vertically centred at y≈315. The mark
       SVG is 32 units across, so scale 4.375x to land at 140px. -->
  <g transform="translate(120 245) scale(4.375)">
    <path d="${PETAL}" fill="${BRAND_PURPLE}"/>
    <path d="${PETAL}" fill="${BRAND_PURPLE}" opacity="0.66" transform="rotate(120 16 16)"/>
    <path d="${PETAL}" fill="${BRAND_PURPLE}" opacity="0.4"  transform="rotate(240 16 16)"/>
    <circle cx="16" cy="16" r="2.4" fill="${BG}"/>
  </g>

  <!-- Wordmark + tagline -->
  <text x="280" y="284"
        font-family="Inter, system-ui, -apple-system, sans-serif"
        font-size="78" font-weight="600"
        letter-spacing="-2"
        fill="${TEXT_PRIMARY}">RunMyCrew</text>
  <text x="280" y="334"
        font-family="Inter, system-ui, -apple-system, sans-serif"
        font-size="30" font-weight="500"
        fill="${TEXT_MUTED}">Build workflows in plain English.</text>

  <!-- Bottom-rule + URL -->
  <line x1="120" y1="540" x2="1080" y2="540" stroke="${TEXT_MUTED}" stroke-opacity="0.18"/>
  <text x="120" y="585"
        font-family="JetBrains Mono, ui-monospace, monospace"
        font-size="22" font-weight="500"
        fill="${TEXT_MUTED}">runmycrew.com</text>
  <text x="1080" y="585" text-anchor="end"
        font-family="JetBrains Mono, ui-monospace, monospace"
        font-size="22" font-weight="500"
        fill="${TEXT_MUTED}">Crew AI · 80+ integrations · self-hostable</text>
</svg>`.trim()

const targets = [
  // Transparent — browser tabs let the chrome bleed through.
  { name: 'favicon-16x16.png',     svg: TRANSPARENT_SVG(64),   resize: 16   },
  { name: 'favicon-32x32.png',     svg: TRANSPARENT_SVG(128),  resize: 32   },
  // Transparent — iOS will round-corner and (on older iOS) apply gloss
  // over whatever wallpaper is behind it. Newer iOS keeps transparency.
  { name: 'apple-touch-icon.png',  svg: TRANSPARENT_SVG(360),  resize: 180  },
  // PWA maskable — opaque required so the Android safe-area mask never
  // exposes the OS background.
  { name: 'icon-192.png',          svg: MASKABLE_SVG(384),     resize: 192  },
  { name: 'icon-512.png',          svg: MASKABLE_SVG(1024),    resize: 512  },
  // Transparent — Meta App Dashboard renders against its own canvas;
  // also accepted by Google OAuth consent screen app-logo upload.
  { name: 'icon-1024.png',         svg: TRANSPARENT_SVG(2048), resize: 1024 },
  // OG card stays JPEG — gradient backgrounds compress poorly as PNG,
  // and every social network accepts JPEG up to 5MB.
  { name: 'og-default.jpg',        svg: OG_SVG,                resize: 1200, height: 630, format: 'jpeg' },
]

await mkdir(PUBLIC, { recursive: true })

for (const t of targets) {
  const buf = Buffer.from(t.svg)
  let pipeline = sharp(buf, { density: 384 })

  if (t.resize) {
    // `fit: contain` pads to the target dimensions; without an explicit
    // background it uses opaque black, which clobbers SVG transparency.
    // Force fully-transparent padding so transparent SVGs stay transparent.
    pipeline = pipeline.resize(t.resize, t.height ?? t.resize, {
      fit: 'contain',
      background: { r: 0, g: 0, b: 0, alpha: 0 },
    })
  }

  if (t.format === 'jpeg') {
    // JPEG has no alpha — flatten over the brand-bg color so the
    // transparent areas become the dark surface, not white.
    pipeline = pipeline
      .flatten({ background: BG })
      .jpeg({ quality: 85, mozjpeg: true, chromaSubsampling: '4:4:4' })
  } else {
    // Don't ask Sharp to palette-encode; it strips the alpha channel
    // when the colour count exceeds 256 + alpha. Truecolour+alpha
    // round-trips losslessly for our two-tone mark.
    pipeline = pipeline.png({
      compressionLevel: 9,
      effort: 10,
      palette: false,
    })
  }

  await pipeline.toFile(join(PUBLIC, t.name))
  console.log(`  ✓ ${t.name}`)
}

console.log('\nAll icon variants written to apps/site/public/.')
