import { useEffect, useMemo, useRef, useState } from 'react'
import { AlertTriangle, Check, ChevronDown, ExternalLink, Loader2, Plus, RefreshCw, Search, Sparkles, X } from 'lucide-react'
import { cn } from '@/lib/cn'
import { APP_ROUTES } from '@/shared/constants/routes'
import { useSkills, SkillIconBadge, type SkillMeta } from '@/features/skills'
import type { RendererProps } from '../types'

/**
 * Multi-select picker for agent skills.
 *
 * Saved shape (per item):
 *   { skillId: string, name: string, description: string, updated_at: string }
 *
 * Bare UUID strings are accepted for backward compat with the pre-snapshot
 * format — they're treated as "no snapshot" entries (can't be marked stale,
 * since there's nothing to compare). Saving any change rewrites the entire
 * array in the rich format.
 *
 * The runtime only reads `skillId`; the snapshot fields exist so the
 * inspector can show drift (description or content edits made elsewhere)
 * without round-tripping every saved skill on every editor render.
 *
 * UX: collapsed by default — the closed state shows a count chip + the
 * selected skill rows. Clicking the trigger opens a searchable dropdown
 * with the full catalog. This keeps the inspector panel scannable when a
 * workspace has dozens of skills.
 */

interface SkillSnapshot {
  skillId: string
  name: string
  description: string
  updated_at: string
}

type SavedEntry = string | SkillSnapshot

function getId(entry: SavedEntry): string {
  return typeof entry === 'string' ? entry : entry.skillId
}

function asSnapshot(entry: SavedEntry): SkillSnapshot | null {
  return typeof entry === 'string' ? null : entry
}

function buildSnapshot(skill: SkillMeta): SkillSnapshot {
  return {
    skillId: skill.id,
    name: skill.name,
    description: skill.description,
    updated_at: skill.updated_at,
  }
}

function isStaleSnapshot(snapshot: SkillSnapshot, live: SkillMeta): boolean {
  return new Date(live.updated_at).getTime() > new Date(snapshot.updated_at).getTime()
}

function toEntryArray(value: unknown): SavedEntry[] {
  if (!value) return []
  let arr: unknown = value
  if (typeof arr === 'string') {
    try {
      arr = JSON.parse(arr)
    } catch {
      return []
    }
  }
  if (!Array.isArray(arr)) return []
  const out: SavedEntry[] = []
  for (const item of arr) {
    if (typeof item === 'string' && item) {
      out.push(item)
    } else if (item && typeof item === 'object' && typeof (item as { skillId?: unknown }).skillId === 'string') {
      const i = item as Record<string, unknown>
      out.push({
        skillId: String(i.skillId),
        name: typeof i.name === 'string' ? i.name : '',
        description: typeof i.description === 'string' ? i.description : '',
        updated_at: typeof i.updated_at === 'string' ? i.updated_at : '',
      })
    }
  }
  return out
}

export function SkillSelectorRenderer({ value, onChange }: RendererProps) {
  const entries = useMemo(() => toEntryArray(value), [value])
  const selectedIds = useMemo(() => entries.map(getId), [entries])
  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds])
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')

  const containerRef = useRef<HTMLDivElement>(null)
  const searchRef = useRef<HTMLInputElement>(null)

  const { data: skills = [], isLoading } = useSkills()

  const liveById = useMemo(() => {
    const m = new Map<string, SkillMeta>()
    for (const s of skills) m.set(s.id, s)
    return m
  }, [skills])

  // Drift = saved snapshot diverges from live skill. Stale = saved id has
  // no live row anymore. The two are mutually exclusive per id.
  const driftIds = useMemo(() => {
    if (isLoading) return [] as string[]
    const out: string[] = []
    for (const entry of entries) {
      const snap = asSnapshot(entry)
      if (!snap) continue
      const live = liveById.get(snap.skillId)
      if (live && isStaleSnapshot(snap, live)) out.push(snap.skillId)
    }
    return out
  }, [isLoading, entries, liveById])

  const staleIds = useMemo(
    () => (isLoading ? [] : selectedIds.filter(id => !liveById.has(id))),
    [isLoading, selectedIds, liveById],
  )

  // Dropdown list: filtered + alpha-sorted + selected pinned to top.
  const dropdownRows = useMemo(() => {
    const q = query.trim().toLowerCase()
    const filtered = q
      ? skills.filter(s =>
          s.name.toLowerCase().includes(q) || s.description.toLowerCase().includes(q),
        )
      : skills
    const sorted = [...filtered].sort((a, b) => a.name.localeCompare(b.name))
    return [
      ...sorted.filter(s => selectedSet.has(s.id)),
      ...sorted.filter(s => !selectedSet.has(s.id)),
    ]
  }, [skills, query, selectedSet])

  // Closed-state list: only the user's current selection, in selection order.
  const selectedRows = useMemo(() => {
    return selectedIds
      .map(id => liveById.get(id))
      .filter((s): s is SkillMeta => Boolean(s))
  }, [selectedIds, liveById])

  // Close on outside click + Escape, focus search when opening.
  useEffect(() => {
    if (!open) return
    const onClick = (e: MouseEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false)
        setQuery('')
      }
    }
    document.addEventListener('mousedown', onClick)
    document.addEventListener('keydown', onKey)
    queueMicrotask(() => searchRef.current?.focus())
    return () => {
      document.removeEventListener('mousedown', onClick)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const writeIds = (ids: string[]) => {
    onChange(
      ids.map(id => {
        const live = liveById.get(id)
        if (live) return buildSnapshot(live)
        const existing = entries.find(e => getId(e) === id)
        return existing ?? id
      }),
    )
  }

  const toggle = (id: string) => {
    writeIds(selectedSet.has(id) ? selectedIds.filter(s => s !== id) : [...selectedIds, id])
  }

  const remove = (id: string) => writeIds(selectedIds.filter(s => s !== id))

  const clearAll = () => onChange([])

  const pruneStale = () => {
    if (!staleIds.length) return
    writeIds(selectedIds.filter(id => !staleIds.includes(id)))
  }

  const refreshDrift = () => {
    if (!driftIds.length) return
    writeIds(selectedIds)
  }

  if (isLoading) {
    return (
      <div className="flex h-9 items-center gap-2 text-[12px] text-text-faint">
        <Loader2 size={13} className="animate-spin" /> Loading skills…
      </div>
    )
  }

  // Workspace has no skills at all — point users to creation.
  if (skills.length === 0) {
    return (
      <div className="flex flex-col items-start gap-2 rounded-[8px] border border-dashed border-border-faint bg-bg p-4">
        <div className="flex items-center gap-2 text-[12px] text-text-mute">
          <Sparkles size={13} className="text-text-faint" />
          No skills yet.
        </div>
        <p className="text-[11px] text-text-faint">
          Skills are reusable markdown bodies an agent can load on demand instead of
          carrying them in every prompt.
        </p>
        <a
          href={APP_ROUTES.SKILL_NEW}
          target="_blank"
          rel="noreferrer"
          className="inline-flex items-center gap-1.5 rounded-[6px] border border-border-faint bg-bg2 px-2.5 py-1 text-[11.5px] text-text hover:bg-surface"
        >
          <Plus size={12} />
          Create your first skill
          <ExternalLink size={10} className="text-text-faint" />
        </a>
      </div>
    )
  }

  return (
    <div ref={containerRef} className="relative flex flex-col gap-2">
      {/* Stale + drift banners stay visible whether the dropdown is open or
          closed — they're actionable even when the user isn't editing the
          selection. */}
      {staleIds.length > 0 && (
        <div className="flex items-start gap-2 rounded-[7px] border border-warn/30 bg-warn/10 px-2.5 py-1.5 text-[11px] text-warn">
          <AlertTriangle size={12} className="mt-0.5 shrink-0" />
          <div className="flex-1">
            {staleIds.length} selected {staleIds.length === 1 ? 'skill no longer exists' : 'skills no longer exist'}.
          </div>
          <button
            type="button"
            onClick={pruneStale}
            className="rounded-[5px] border border-warn/40 bg-bg px-1.5 py-0.5 text-[10.5px] text-warn hover:bg-surface"
          >
            Remove
          </button>
        </div>
      )}
      {driftIds.length > 0 && (
        <div className="flex items-start gap-2 rounded-[7px] border border-[var(--accent-line)]/40 bg-[var(--accent-line)]/10 px-2.5 py-1.5 text-[11px] text-text-mute">
          <RefreshCw size={12} className="mt-0.5 shrink-0 text-[var(--accent)]" />
          <div className="flex-1">
            {driftIds.length} selected {driftIds.length === 1 ? 'skill has' : 'skills have'} been edited since this snapshot was taken.
          </div>
          <button
            type="button"
            onClick={refreshDrift}
            className="rounded-[5px] border border-[var(--accent-line)]/40 bg-bg px-1.5 py-0.5 text-[10.5px] text-[var(--accent)] hover:bg-surface"
          >
            Refresh
          </button>
        </div>
      )}

      {/* Trigger button */}
      <button
        type="button"
        onClick={() => setOpen(v => !v)}
        className={cn(
          'flex h-9 items-center gap-2 rounded-[7px] border px-2.5 transition-colors',
          open
            ? 'border-border bg-surface'
            : 'border-border-faint bg-bg hover:border-border-soft hover:bg-surface',
        )}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <Sparkles size={13} className="text-text-faint" />
        <span className="flex-1 text-left text-[12px] text-text-mute">
          {selectedIds.length === 0
            ? 'Select skills…'
            : `${selectedIds.length} skill${selectedIds.length === 1 ? '' : 's'} selected`}
        </span>
        <ChevronDown
          size={13}
          className={cn('text-text-faint transition-transform', open && 'rotate-180')}
        />
      </button>

      {/* Closed-state selection summary — only when at least one is picked
          and the dropdown is closed. Lets users see what's wired in without
          opening the picker. */}
      {!open && selectedRows.length > 0 && (
        <div className="flex flex-col gap-1">
          {selectedRows.map(skill => (
            <div
              key={skill.id}
              className="flex items-center gap-2 rounded-[7px] border border-border-faint bg-bg px-2 py-1.5"
            >
              <SkillIconBadge iconName={skill.icon} size="sm" />
              <div className="min-w-0 flex-1">
                <div className="truncate text-[12px] font-medium text-text">{skill.name}</div>
                {skill.description && (
                  <div className="truncate text-[10.5px] text-text-faint">{skill.description}</div>
                )}
              </div>
              <button
                type="button"
                onClick={() => remove(skill.id)}
                className="text-text-faint hover:text-err"
                aria-label={`Remove ${skill.name}`}
              >
                <X size={12} />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Dropdown popover */}
      {open && (
        <div className="absolute left-0 right-0 top-11 z-30 flex flex-col overflow-hidden rounded-[10px] border border-border-faint bg-bg2 shadow-[0_12px_32px_-8px_oklch(0_0_0/0.55)]">
          {/* Search + count + clear */}
          <div className="flex items-center gap-2 border-b border-border-faint px-2.5 py-2">
            <Search size={12} className="shrink-0 text-text-faint" />
            <input
              ref={searchRef}
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Filter skills…"
              className="min-w-0 flex-1 bg-transparent text-[12px] text-text outline-none placeholder:text-text-faint"
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                aria-label="Clear filter"
                className="text-text-faint hover:text-text"
              >
                <X size={11} />
              </button>
            )}
            {selectedIds.length > 0 && (
              <button
                type="button"
                onClick={clearAll}
                className="rounded-[5px] border border-border-faint bg-bg px-1.5 py-0.5 text-[10.5px] text-text-mute hover:text-text"
              >
                Clear ({selectedIds.length})
              </button>
            )}
          </div>

          {/* List */}
          {dropdownRows.length === 0 ? (
            <p className="px-3 py-4 text-center text-[11.5px] text-text-faint">
              No skills match &ldquo;{query}&rdquo;.
            </p>
          ) : (
            <div className="flex max-h-[280px] flex-col gap-1 overflow-y-auto p-1.5">
              {dropdownRows.map(skill => (
                <SkillRow
                  key={skill.id}
                  skill={skill}
                  active={selectedSet.has(skill.id)}
                  stale={driftIds.includes(skill.id)}
                  onToggle={toggle}
                />
              ))}
            </div>
          )}

          {/* Footer */}
          <div className="flex items-center justify-between gap-2 border-t border-border-faint px-2.5 py-1.5 text-[11px]">
            <a
              href={APP_ROUTES.SKILL_NEW}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-text-mute hover:text-text"
            >
              <Plus size={11} />
              New skill
              <ExternalLink size={9} className="text-text-faint" />
            </a>
            <a
              href={APP_ROUTES.SKILLS}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1 text-text-faint hover:text-text-mute"
            >
              Manage all
              <ExternalLink size={9} />
            </a>
          </div>
        </div>
      )}
    </div>
  )
}

interface SkillRowProps {
  skill: SkillMeta
  active: boolean
  stale: boolean
  onToggle: (id: string) => void
}

function SkillRow({ skill, active, stale, onToggle }: SkillRowProps) {
  return (
    <button
      type="button"
      onClick={() => onToggle(skill.id)}
      className={cn(
        'group flex items-center gap-2.5 rounded-[7px] border px-2 py-1.5 text-left transition-colors',
        active
          ? 'border-[var(--accent-line)]/40 bg-[var(--accent-line)]/10'
          : 'border-transparent bg-transparent hover:bg-surface',
      )}
      aria-pressed={active}
    >
      <SkillIconBadge iconName={skill.icon} size="sm" />
      <div className="min-w-0 flex-1">
        <div className="flex items-center gap-1.5">
          <div className="truncate text-[12px] font-medium text-text">{skill.name}</div>
          {stale && (
            <span
              className="rounded-[3px] bg-[var(--accent)]/15 px-1 py-px text-[9px] font-medium uppercase tracking-wide text-[var(--accent)]"
              title="Snapshot is stale — the source skill was edited"
            >
              Updated
            </span>
          )}
        </div>
        {skill.description ? (
          <div className="truncate text-[10.5px] text-text-faint">{skill.description}</div>
        ) : (
          <div className="text-[10.5px] italic text-text-faint">No description</div>
        )}
      </div>
      <div
        className={cn(
          'flex h-4 w-4 shrink-0 items-center justify-center rounded-[4px] border transition-colors',
          active ? 'border-[var(--accent)] bg-[var(--accent)] text-bg' : 'border-border-faint',
        )}
      >
        {active && <Check size={10} />}
      </div>
    </button>
  )
}
