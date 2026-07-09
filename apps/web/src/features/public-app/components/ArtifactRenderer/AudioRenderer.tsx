import type { RendererProps } from './types'

export function AudioRenderer({ artifact }: RendererProps) {
  const url = String(artifact.data?.url ?? '')
  return (
    <div className="flex h-full items-center justify-center p-6">
      <div className="w-full max-w-[420px] rounded-[12px] border border-white/10 bg-white/[0.03] p-4">
        {artifact.title && (
          <div className="mb-3 truncate text-[13px] font-medium text-white">{artifact.title}</div>
        )}
        <audio src={url} controls className="w-full" />
      </div>
    </div>
  )
}
