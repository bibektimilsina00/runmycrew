import { useState } from 'react'
import { Maximize2, Minimize2, X } from 'lucide-react'
import { ArtifactView } from './ArtifactRenderer'
import { artifactLabel } from './ArtifactRenderer/label'
import type { Artifact } from '../types/artifactTypes'

interface CanvasViewProps {
  artifacts: Artifact[]
  onClose?: () => void
  className?: string
}

/**
 * Right-pane artifact canvas. Tab strip along the top, fullscreen toggle,
 * close (on mobile). When more than one artifact arrives, the newest is
 * auto-selected so streaming feels alive.
 */
export function CanvasView({ artifacts, onClose, className }: CanvasViewProps) {
  // Derive the active artifact from render state so streaming updates
  // (new artifact appended) auto-select the newest one without a
  // setState-in-effect.
  const [pickedId, setPickedId] = useState<string | null>(null)
  const [fullscreen, setFullscreen] = useState(false)
  const active =
    artifacts.length === 0
      ? null
      : (pickedId && artifacts.find(a => a.id === pickedId)) || artifacts[artifacts.length - 1]

  return (
    <aside
      className={
        (className ?? '') +
        ' flex h-full min-h-0 flex-col border-l border-white/5 bg-[#0e0e14]'
      }
      style={fullscreen ? { position: 'fixed', inset: 0, zIndex: 60 } : undefined}
    >
      <div className="flex items-center gap-1 border-b border-white/5 px-2 py-1.5">
        <div className="flex min-w-0 flex-1 items-center gap-1 overflow-x-auto">
          {artifacts.map(a => (
            <button
              key={a.id}
              onClick={() => setPickedId(a.id)}
              className={
                'shrink-0 whitespace-nowrap rounded-[7px] px-2.5 py-1 text-[11.5px] transition ' +
                (a.id === active?.id
                  ? 'bg-white/[0.08] text-white'
                  : 'text-white/50 hover:bg-white/[0.04] hover:text-white')
              }
              title={a.title || a.type}
            >
              <span className="mr-1.5 uppercase tracking-wider opacity-60">{a.type}</span>
              <span className="max-w-[160px] truncate align-middle">{artifactLabel(a)}</span>
            </button>
          ))}
        </div>
        <button
          onClick={() => setFullscreen(v => !v)}
          className="rounded-[6px] p-1.5 text-white/60 hover:bg-white/[0.06] hover:text-white"
          title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}
        >
          {fullscreen ? <Minimize2 size={13} /> : <Maximize2 size={13} />}
        </button>
        {onClose && (
          <button
            onClick={onClose}
            className="rounded-[6px] p-1.5 text-white/60 hover:bg-white/[0.06] hover:text-white lg:hidden"
            title="Close canvas"
          >
            <X size={13} />
          </button>
        )}
      </div>
      <div className="flex-1 overflow-hidden">
        {active ? (
          <ArtifactView artifact={active} fullscreen={fullscreen} />
        ) : (
          <div className="flex h-full items-center justify-center p-8 text-center text-[13px] text-white/40">
            Artifacts from the workflow will appear here.
          </div>
        )}
      </div>
    </aside>
  )
}
