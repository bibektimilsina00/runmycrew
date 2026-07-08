import { useReactFlow } from 'reactflow'
import { useShallow } from 'zustand/react/shallow'
import { useCollaborationStore } from '../collaborationStore'

/**
 * Renders peer cursors as colored arrows + name labels at the peers'
 * stored canvas-space positions. Mounts inside ReactFlow so the cursor
 * tracks pan + zoom — coordinates broadcast over the wire are always
 * in canvas (flow) coordinates, and we let `useReactFlow().flowToScreen`
 * convert them to screen pixels on each render.
 */
export function PeerCursors() {
  const peers = useCollaborationStore(useShallow((s) => Object.values(s.peers)))
  const { flowToScreenPosition } = useReactFlow()

  if (peers.length === 0) return null

  return (
    <div className="pointer-events-none absolute inset-0 z-50">
      {peers.map(({ session, cursor }) => {
        if (!cursor) return null
        const screen = flowToScreenPosition(cursor)
        return (
          <div
            key={session.session_id}
            // ~120ms transition smooths cursor between 25fps wire updates
            // without lagging noticeably behind the peer's actual mouse.
            className="absolute will-change-transform transition-transform [transition-duration:120ms] ease-out"
            style={{
              transform: `translate3d(${screen.x}px, ${screen.y}px, 0)`,
            }}
          >
            {/* Arrow — refined Figma-style glyph with a tinted soft
                halo for visibility against dark and light surfaces. */}
            <svg
              width="22"
              height="26"
              viewBox="0 0 22 26"
              fill="none"
              style={{
                filter: `drop-shadow(0 4px 10px ${session.color}55) drop-shadow(0 1px 2px rgba(0,0,0,0.25))`,
              }}
            >
              <path
                d="M3 2.4L18.6 11.2C19.5 11.7 19.4 13 18.4 13.3L11.6 15.1L8.4 21.3C7.9 22.2 6.6 22 6.4 21L3 2.4Z"
                fill={session.color}
                strokeLinejoin="round"
              />
            </svg>
            {/* Name pill — slight gradient + matching shadow so the
                label reads as part of the cursor, not a sticker. */}
            <span
              className="absolute left-[18px] top-[18px] inline-flex items-center gap-1 rounded-full px-2 py-[3px] text-[11px] font-semibold text-white whitespace-nowrap"
              style={{
                backgroundColor: session.color,
                boxShadow: `0 2px 8px ${session.color}55, 0 0 0 1.5px rgba(255,255,255,0.12)`,
                letterSpacing: '-0.005em',
              }}
            >
              {session.user_name}
            </span>
          </div>
        )
      })}
    </div>
  )
}
