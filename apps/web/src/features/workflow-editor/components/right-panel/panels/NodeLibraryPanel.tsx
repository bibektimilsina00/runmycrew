import { useState } from 'react'
import { Search } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useNodeLibrary, CATEGORY_LABEL } from '../../../hooks/useNodeLibrary'
import { getIcon } from '../../../utils/icon-map'
import { BrandIcon } from '../../../utils/BrandIcon'
import type { NodeDefinition } from '../../../types/editorTypes'

const BRAND_LABEL: Record<string, string> = {
  google: 'Google',
  aws: 'AWS',
  microsoft: 'Microsoft',
  atlassian: 'Atlassian',
  twilio: 'Twilio',
  sap: 'SAP',
  meta: 'Meta',
  ai: 'AI',
}

function NodeRow({ def, onSpawn, onDrag }: {
  def: NodeDefinition
  onSpawn: (def: NodeDefinition) => void
  onDrag: (e: React.DragEvent, def: NodeDefinition) => void
}) {
  const Icon = getIcon(def.icon)
  return (
    <div
      draggable
      onClick={() => onSpawn(def)}
      onDragStart={e => onDrag(e, def)}
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
}

function BrandGroup({ brand, defs, onSpawn, onDrag }: {
  brand: string
  defs: NodeDefinition[]
  onSpawn: (def: NodeDefinition) => void
  onDrag: (e: React.DragEvent, def: NodeDefinition) => void
}) {
  const [open, setOpen] = useState(false)
  return (
    <div className="mb-0.5">
      <button
        onClick={() => setOpen(v => !v)}
        className={cn(
          'flex w-full items-center gap-2.5 rounded-[8px] px-2.5 py-2 text-left',
          'transition-colors hover:bg-[var(--surface)]',
        )}
      >
        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px] bg-[var(--surface-2)] [&_img]:h-3.5 [&_img]:w-3.5 [&_img]:object-contain">
          <BrandIcon slug={brand} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[12.5px] font-medium text-[var(--text)]">{BRAND_LABEL[brand] ?? brand}</p>
        </div>
        <span className="shrink-0 rounded bg-[var(--surface-2)] px-1.5 py-0.5 text-[10px] font-mono text-[var(--text-dim)]">
          {defs.length}
        </span>
        <span className={cn('shrink-0 text-[10px] text-[var(--text-dim)] transition-transform', open && 'rotate-90')}>▶</span>
      </button>
      {open && (
        <div className="ml-4 border-l border-[var(--border-faint)] pl-1">
          {defs.map(def => (
            <NodeRow key={def.type} def={def} onSpawn={onSpawn} onDrag={onDrag} />
          ))}
        </div>
      )}
    </div>
  )
}

export function NodeLibraryPanel() {
  const {
    query, setQuery, grouped, spawnNode, onDragStart,
    loopMode, presets, spawnPreset, onDragStartPreset,
  } = useNodeLibrary()

  // Track which categories the user collapsed. Everything starts open;
  // a click on the category header toggles just that section. Search
  // forces every category open so results stay visible.
  const [collapsed, setCollapsed] = useState<Set<string>>(new Set())
  const toggleCategory = (c: string) => setCollapsed(prev => {
    const next = new Set(prev)
    if (next.has(c)) next.delete(c); else next.add(c)
    return next
  })
  const searching = query.trim().length > 0

  return (
    <div className="flex h-full flex-col">
      <div className="shrink-0 border-b border-[var(--border-faint)] p-3">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-[var(--text-faint)]" />
          <input
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder={loopMode ? 'Search crew…' : 'Search nodes…'}
            className={cn(
              'h-8 w-full rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)]',
              'pl-8 pr-3 text-[12.5px] text-[var(--text)] placeholder:text-[var(--text-dim)]',
              'outline-none transition-colors focus:border-[var(--border-soft)] focus:bg-[var(--bg-2)]',
            )}
          />
        </div>
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-2 [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        {loopMode ? (
          presets.length === 0 ? (
            <p className="py-8 text-center text-[12px] text-[var(--text-faint)]">No crew found</p>
          ) : (
            <div className="mb-3">
              <p className="mb-1 px-2 text-[10.5px] font-semibold uppercase tracking-widest text-[var(--text-dim)]">
                Crew
              </p>
              {presets.map(preset => {
                const Icon = getIcon(preset.icon)
                return (
                  <div
                    key={preset.id}
                    draggable
                    onClick={() => spawnPreset(preset)}
                    onDragStart={e => onDragStartPreset(e, preset)}
                    className={cn(
                      'flex cursor-pointer select-none items-center gap-2.5 rounded-[8px] px-2.5 py-2',
                      'transition-colors hover:bg-[var(--surface)] active:bg-[var(--surface-2)] active:cursor-grabbing',
                    )}
                    title="Click to add · Drag to position"
                  >
                    <div
                      className="flex h-6 w-6 shrink-0 items-center justify-center rounded-[6px] text-white [&_svg]:h-3 [&_svg]:w-3 [&_img]:h-3 [&_img]:w-3 [&_img]:object-contain"
                      style={{ background: preset.color ?? 'var(--surface-3)' }}
                    >
                      {Icon}
                    </div>
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-[12.5px] font-medium text-[var(--text)]">{preset.label}</p>
                      <p className="truncate text-[11px] text-[var(--text-dim)]">{preset.description}</p>
                    </div>
                  </div>
                )
              })}
            </div>
          )
        ) : grouped.length === 0 ? (
          <p className="py-8 text-center text-[12px] text-[var(--text-faint)]">No nodes found</p>
        ) : (
          grouped.map(({ category, unbranded, brands, defs }) => {
            const isOpen = searching || !collapsed.has(category)
            return (
              <div key={category} className="mb-3">
                <button
                  onClick={() => toggleCategory(category)}
                  className="mb-1 flex w-full items-center gap-1.5 px-2 text-[10.5px] font-semibold uppercase tracking-widest text-[var(--text-dim)] hover:text-[var(--text)] transition-colors"
                >
                  <span className={cn('text-[9px] transition-transform', isOpen && 'rotate-90')}>▶</span>
                  <span className="flex-1 text-left">{CATEGORY_LABEL[category] ?? category}</span>
                  <span className="rounded bg-[var(--surface-2)] px-1.5 py-0.5 text-[9.5px] font-mono normal-case tracking-normal text-[var(--text-dim)]">
                    {defs.length}
                  </span>
                </button>
                {isOpen && (
                  <>
                    {unbranded.map(def => (
                      <NodeRow key={def.type} def={def} onSpawn={spawnNode} onDrag={onDragStart} />
                    ))}
                    {brands.map(({ brand, defs }) => (
                      <BrandGroup key={brand} brand={brand} defs={defs} onSpawn={spawnNode} onDrag={onDragStart} />
                    ))}
                  </>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
