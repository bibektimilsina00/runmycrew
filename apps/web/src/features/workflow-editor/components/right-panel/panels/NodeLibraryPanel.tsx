import { useState } from 'react'
import { Search, ChevronDown, Zap, Play, Sparkles, Sliders, Globe, Blocks } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useNodeLibrary, CATEGORY_LABEL } from '../../../hooks/useNodeLibrary'
import { getIcon } from '../../../utils/icon-map'
import { BrandIcon } from '../../../utils/BrandIcon'
import type { NodeDefinition } from '../../../types/editorTypes'

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  trigger: <Zap className="h-3.5 w-3.5 text-emerald-400" />,
  action: <Play className="h-3.5 w-3.5 text-blue-400" />,
  ai: <Sparkles className="h-3.5 w-3.5 text-purple-400" />,
  logic: <Sliders className="h-3.5 w-3.5 text-amber-400" />,
  browser: <Globe className="h-3.5 w-3.5 text-sky-400" />,
  integration: <Blocks className="h-3.5 w-3.5 text-indigo-400" />,
}

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
  const isWhite = def.color === '#ffffff'
  return (
    <div
      draggable
      onClick={() => onSpawn(def)}
      onDragStart={e => onDrag(e, def)}
      className={cn(
        'flex cursor-pointer select-none items-center gap-2.5 rounded-[8px] px-2.5 py-1.5',
        'transition-colors hover:bg-[var(--surface)] active:bg-[var(--surface-2)] active:cursor-grabbing',
      )}
      title="Click to add · Drag to position"
    >
      <div
        className={cn(
          "flex h-7 w-7 shrink-0 items-center justify-center rounded-[6px] text-white [&_svg]:h-4 [&_svg]:w-4 [&_img]:h-4 [&_img]:w-4 [&_img]:object-contain transition-shadow duration-200",
          isWhite ? "bg-white border border-zinc-700/30 shadow-[0_1px_2px_rgba(0,0,0,0.2)]" : "shadow-sm"
        )}
        style={!isWhite ? { background: def.color ?? 'var(--surface-3)' } : undefined}
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
    <div className="mb-1">
      <button
        onClick={() => setOpen(v => !v)}
        className={cn(
          'flex w-full items-center gap-2.5 rounded-[8px] border border-[var(--border-faint)] bg-[var(--surface)]/40 px-2.5 py-1.5 text-left transition-all hover:bg-[var(--surface-2)]/60',
          open && 'bg-[var(--surface-2)]/40 border-[var(--border-soft)]'
        )}
      >
        <div className="flex h-7 w-7 shrink-0 items-center justify-center rounded-[6px] bg-[var(--surface-2)] [&_img]:h-4 [&_img]:w-4 [&_img]:object-contain">
          <BrandIcon slug={brand} />
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-[12.5px] font-medium text-[var(--text)]">{BRAND_LABEL[brand] ?? brand}</p>
        </div>
        <span className="rounded bg-white/10 px-1.5 py-0.5 text-[9.5px] font-mono text-white/70 border border-white/5 mr-1">
          {defs.length}
        </span>
        <ChevronDown
          className={cn(
            'h-3.5 w-3.5 text-[var(--text-dim)] transition-transform duration-200',
            !open && '-rotate-90'
          )}
        />
      </button>
      <div
        className={cn(
          "overflow-hidden transition-all duration-300 ease-in-out",
          open ? "max-h-[1000px] opacity-100 mt-1" : "max-h-0 opacity-0"
        )}
      >
        <div className="ml-3.5 border-l border-[var(--border-faint)] pl-1.5 py-0.5">
          {defs.map(def => (
            <NodeRow key={def.type} def={def} onSpawn={onSpawn} onDrag={onDrag} />
          ))}
        </div>
      </div>
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
                      className={cn(
                        "flex h-7 w-7 shrink-0 items-center justify-center rounded-[6px] text-white [&_svg]:h-4 [&_svg]:w-4 [&_img]:h-4 [&_img]:w-4 [&_img]:object-contain transition-shadow duration-200",
                        preset.color === '#ffffff' ? "bg-white border border-zinc-700/30 shadow-[0_1px_2px_rgba(0,0,0,0.2)]" : "shadow-sm"
                      )}
                      style={preset.color !== '#ffffff' ? { background: preset.color ?? 'var(--surface-3)' } : undefined}
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
                  className={cn(
                    "mb-1.5 flex w-full items-center gap-2.5 rounded-[8px] border border-[var(--border-soft)] bg-[var(--surface)] px-3 py-2 text-left transition-all hover:bg-[var(--surface-2)] hover:border-[var(--border-soft)]",
                    isOpen && "bg-[var(--surface-2)]/50 border-[var(--border-soft)]"
                  )}
                >
                  <div className="flex shrink-0 items-center justify-center">
                    {CATEGORY_ICONS[category] || <Blocks className="h-3.5 w-3.5 text-[var(--text-dim)]" />}
                  </div>
                  <span className="flex-1 text-[12px] font-semibold text-[var(--text)]">
                    {CATEGORY_LABEL[category] ?? category}
                  </span>
                  <span className="rounded bg-white/10 px-2 py-0.5 text-[10px] font-mono font-medium text-white/70 border border-white/5">
                    {defs.length}
                  </span>
                  <ChevronDown
                    className={cn(
                      'h-3.5 w-3.5 text-[var(--text-dim)] transition-transform duration-200',
                      !isOpen && '-rotate-90'
                    )}
                  />
                </button>
                <div
                  className={cn(
                    "overflow-hidden transition-all duration-300 ease-in-out",
                    isOpen ? "max-h-[3000px] opacity-100 mt-1.5" : "max-h-0 opacity-0"
                  )}
                >
                  {unbranded.map(def => (
                    <NodeRow key={def.type} def={def} onSpawn={spawnNode} onDrag={onDragStart} />
                  ))}
                  {brands.map(({ brand, defs }) => (
                    <BrandGroup key={brand} brand={brand} defs={defs} onSpawn={spawnNode} onDrag={onDragStart} />
                  ))}
                </div>
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}
