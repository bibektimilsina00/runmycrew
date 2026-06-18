import path from 'node:path'
import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  // Self-contained production server in a single folder — Docker copies
  // `.next/standalone` + `.next/static` + `public` and runs `node
  // server.js`. Drops the runtime image from ~1.2 GB to ~180 MB.
  output: 'standalone',

  // pnpm hoists `next` into the monorepo root's `node_modules`. Turbopack
  // resolves the Next.js package from that root, so we point root at the
  // workspace top (two levels up from apps/site).
  turbopack: {
    root: path.resolve(__dirname, '..', '..'),
  },
  // Allow LAN access in dev — without this Next 16 blocks the HMR
  // WebSocket when the page is opened from a phone / another machine
  // on the same network. `*.local` covers Bonjour/mDNS hostnames.
  allowedDevOrigins: ['192.168.1.72', '*.local'],
  // typedRoutes intentionally off while routes are still being added —
  // re-enable once /pricing, /docs, /changelog exist.
}

export default nextConfig
