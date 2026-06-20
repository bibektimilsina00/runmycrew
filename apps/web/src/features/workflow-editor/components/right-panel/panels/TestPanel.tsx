import { Plus, Copy, Trash2, Play, Loader2 } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useTestPanel } from '../../../hooks/useTestPanel'

interface TestPanelProps {
  onRun: () => void
  isRunning: boolean
}

const standardInputCls = 'w-full rounded-[8px] border border-border-soft bg-surface px-3 py-1.5 text-[12.5px] text-[var(--text)] placeholder:text-text-faint outline-none transition-[background-color,border-color] duration-[120ms] hover:border-border hover:bg-surface-2 focus:border-accent focus:bg-surface-2'
const jsonAreaCls = 'w-full rounded-[8px] border border-border-faint bg-bg px-3 py-2.5 text-xs text-[var(--text)] font-mono placeholder:text-text-faint outline-none transition-[background-color,border-color] duration-[120ms] hover:border-border-soft focus:border-border focus:bg-surface leading-relaxed'
const iconBtnCls = 'flex h-7 w-7 shrink-0 items-center justify-center rounded-[7px] text-[var(--text-faint)] transition-colors hover:bg-[var(--surface)] hover:text-[var(--text)]'

function Field({ label, hint, children }: { label: string; hint?: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <div className="flex items-center justify-between">
        <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-[var(--text-dim)]">{label}</span>
        {hint && <span className="text-[10px] text-[var(--text-faint)]">{hint}</span>}
      </div>
      {children}
    </div>
  )
}

function CheckRow({ label, checked, onChange }: { label: string; checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <label className="flex cursor-pointer items-center gap-2">
      <input
        type="checkbox"
        checked={checked}
        onChange={e => onChange(e.target.checked)}
        className="h-3.5 w-3.5 accent-[var(--text)] cursor-pointer"
      />
      <span className="text-[12px] text-[var(--text-mute)]">{label}</span>
    </label>
  )
}

export function TestPanel({ onRun, isRunning }: TestPanelProps) {
  const {
    scenarios, selected, selectedId, setSelectedId,
    renameId, setRenameId, renameScenario, patchSelected,
    setVar, addVar, removeVar,
    addScenario, duplicateScenario, deleteScenario, runScenario,
  } = useTestPanel(onRun)

  return (
    <div className="flex h-full flex-col overflow-hidden bg-[var(--bg-2)]">
      {/* Scenario list */}
      <div className="shrink-0 border-b border-[var(--border-faint)] bg-[var(--bg-2)]">
        <div className="flex items-center justify-between px-4 py-2.5">
          <span className="text-[10.5px] font-semibold uppercase tracking-widest text-[var(--text-dim)]">Saved scenarios</span>
          <button
            onClick={addScenario}
            className="flex items-center gap-1 text-[11.5px] text-[var(--text-mute)] transition-colors hover:text-[var(--text)]"
          >
            <Plus className="h-3 w-3" /> New
          </button>
        </div>

        <div className="flex flex-col gap-1 px-3 pb-3">
          {scenarios.map(s => {
            const isActive = s.id === selectedId
            return (
              <button
                key={s.id}
                onClick={() => setSelectedId(s.id)}
                className={cn(
                  'flex w-full items-center gap-2.5 rounded-[8px] px-3 py-2 text-left transition-all duration-[120ms] border',
                  isActive
                    ? 'bg-[var(--surface)] border-[var(--border-soft)] shadow-[var(--shadow-float)]'
                    : 'bg-transparent border-transparent hover:bg-[var(--surface)]/30 hover:text-[var(--text)]',
                )}
              >
                <span className={cn(
                  'h-1.5 w-1.5 shrink-0 rounded-full',
                  s.lastRun?.status === 'ok'  ? 'bg-[var(--ok)]'         :
                  s.lastRun?.status === 'err' ? 'bg-[var(--err)]'        :
                  'bg-[var(--border-soft)]',
                )} />
                <span className="min-w-0 flex-1">
                  {renameId === s.id ? (
                    <input
                      autoFocus
                      value={s.name}
                      onChange={e => renameScenario(s.id, e.target.value)}
                      onBlur={() => setRenameId(null)}
                      onKeyDown={e => { if (e.key === 'Enter' || e.key === 'Escape') setRenameId(null) }}
                      onClick={e => e.stopPropagation()}
                      className="w-full bg-transparent text-[12.5px] text-[var(--text)] outline-none border-b border-[var(--border)]"
                    />
                  ) : (
                    <span className="block truncate text-[12.5px] font-medium text-[var(--text)]">{s.name}</span>
                  )}
                  <span className="block text-[10.5px] text-[var(--text-faint)] mt-0.5">
                    {s.lastRun ? `Ran ${s.lastRun.t}` : 'Never run'}
                  </span>
                </span>
              </button>
            )
          })}
        </div>
      </div>

      {/* Editor */}
      <div className="min-h-0 flex-1 overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <div className="flex flex-col gap-4 p-4">

          {/* Name + actions */}
          <div className="flex items-center gap-1.5">
            <input
              value={selected.name}
              onChange={e => patchSelected({ name: e.target.value })}
              placeholder="Scenario name"
              className="flex-1 bg-transparent text-[13.5px] font-semibold text-[var(--text)] outline-none border-b border-transparent focus:border-[var(--border-soft)] py-0.5 placeholder:text-[var(--text-dim)]"
            />
            <button onClick={duplicateScenario} title="Duplicate" className={iconBtnCls}>
              <Copy className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={deleteScenario}
              disabled={scenarios.length <= 1}
              title="Delete"
              className={cn(iconBtnCls, 'hover:text-[var(--err)] disabled:pointer-events-none disabled:opacity-30')}
            >
              <Trash2 className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Description */}
          <Field label="Description" hint="Optional">
            <input
              value={selected.desc}
              onChange={e => patchSelected({ desc: e.target.value })}
              placeholder="When does this scenario apply?"
              className={standardInputCls}
            />
          </Field>

          {/* Trigger payload */}
          <Field label="Trigger payload" hint="JSON">
            <textarea
              value={selected.payload}
              onChange={e => patchSelected({ payload: e.target.value })}
              rows={7}
              placeholder="{}"
              className={jsonAreaCls}
            />
          </Field>

          {/* Variables */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between">
              <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-[var(--text-dim)]">Variables</span>
              <button
                onClick={addVar}
                className="flex items-center gap-0.5 text-[11px] text-[var(--text-faint)] transition-colors hover:text-[var(--text)]"
              >
                <Plus className="h-3 w-3" /> Add
              </button>
            </div>
            {selected.vars.length === 0 ? (
              <p className="text-[11.5px] italic text-[var(--text-faint)]">No variables set.</p>
            ) : (
              <div className="flex flex-col gap-2">
                {selected.vars.map((row, i) => (
                  <div key={i} className="flex items-center gap-2">
                    <input
                      value={row.k}
                      onChange={e => setVar(i, 'k', e.target.value)}
                      placeholder="KEY"
                      className={cn(standardInputCls, 'flex-1 font-mono text-[11.5px]')}
                    />
                    <span className="text-[var(--text-faint)] font-mono">=</span>
                    <input
                      value={row.v}
                      onChange={e => setVar(i, 'v', e.target.value)}
                      placeholder="value"
                      className={cn(standardInputCls, 'flex-1 font-mono text-[11.5px]')}
                    />
                    <button
                      onClick={() => removeVar(i)}
                      className={cn(iconBtnCls, 'hover:text-[var(--err)]')}
                    >
                      <Trash2 className="h-3 w-3" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Options */}
          <div className="flex flex-col gap-2">
            <span className="text-[11px] font-bold uppercase tracking-[0.08em] text-[var(--text-dim)]">Options</span>
            <div className="flex flex-col gap-2 mt-1">
              <CheckRow label="Mock external calls" checked={selected.mockCalls} onChange={v => patchSelected({ mockCalls: v })} />
              <CheckRow label="Replay last successful run" checked={selected.replayLast} onChange={v => patchSelected({ replayLast: v })} />
            </div>
          </div>
        </div>
      </div>

      {/* Footer run button */}
      <div className="shrink-0 border-t border-[var(--border-faint)] p-4 bg-[var(--bg-2)]">
        <button
          onClick={runScenario}
          disabled={isRunning}
          className={cn(
            'flex w-full items-center justify-center gap-2 rounded-[8px] bg-[var(--text)] py-2 text-[13px] font-semibold text-[var(--bg)] transition-opacity',
            'hover:opacity-90 disabled:pointer-events-none disabled:opacity-40',
          )}
        >
          {isRunning
            ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
            : <Play className="h-3.5 w-3.5 fill-current" />}
          {isRunning ? 'Running…' : 'Run scenario'}
        </button>
      </div>
    </div>
  )
}
