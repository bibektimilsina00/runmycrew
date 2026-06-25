import { Search } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useNodeLibrary, CATEGORY_LABEL } from '../../../hooks/useNodeLibrary'
import { getIcon } from '../../../utils/icon-map'

export function NodeLibraryPanel() {
  const { query, setQuery, grouped, spawnNode, onDragStart } = useNodeLibrary()

  return (
    <div className="flex h-full flex-col">
      <div className="shrink-0 border-b border-[var(--border-faint)] p-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-faint)]" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search nodes…"
            className={cn(
              'h-8 w-full rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)]',
              'pl-8 pr-3 text-[12.5px] text-[var(--text)] placeholder:text-[var(--text-dim)]',
              'outline-none transition-colors focus:border-[var(--border-soft)] focus:bg-[var(--bg-2)]',
            )}
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {grouped.length === 0 ? (
          <p className="py-8 text-center text-[12px] text-[var(--text-faint)]">No nodes found</p>
        ) : (
          grouped.map(({ category, defs }) => (
            <div key={category} className="mb-3">
              <p className="mb-1 px-2 text-[10.5px] font-semibold uppercase tracking-widest text-[var(--text-dim)]">
                {CATEGORY_LABEL[category] ?? category}
              </p>
              {defs.map(def => {
                const Icon = getIcon(def.icon)
                return (
                  <div
                    key={def.type}
                    draggable
                    onClick={() => spawnNode(def)}
                    onDragStart={e => onDragStart(e, def)}
                    className={cn(
                      'flex cursor-pointer select-none items-center gap-2.5 rounded-[8px] px-2.5 py-2',
                      'transition-colors hover:bg-[var(--surface)] active:bg-[var(--surface-2)] active:cursor-grabbing',
                    )}
                    title="Click to add · Drag to position"
                  >
                    <div
                      className="flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px] text-white [&_svg]:h-3 [&_svg]:w-3 [&_img]:h-3 [&_img]:w-3 [&_img]:object-contain"
                      style={{ background: def.color ?? 'var(--surface-3)' }}
                    >
                      {Icon}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[12.5px] font-medium text-[var(--text)]">{def.name}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          ))
        )}
      </div>
    </div>
  )
}
