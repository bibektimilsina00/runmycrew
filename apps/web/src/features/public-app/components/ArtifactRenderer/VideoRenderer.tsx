import type { RendererProps } from './types'

export function VideoRenderer({ artifact }: RendererProps) {
  const url = String(artifact.data?.url ?? '')
  const poster = String(artifact.data?.poster_url ?? '')
  return (
    <div className="flex h-full items-center justify-center bg-black/50 p-4">
      <video
        src={url}
        poster={poster || undefined}
        controls
        playsInline
        className="max-h-full max-w-full rounded-[10px] shadow-[0_10px_40px_-16px_rgba(0,0,0,0.7)]"
      />
    </div>
  )
}
