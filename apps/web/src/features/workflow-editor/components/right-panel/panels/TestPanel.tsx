import { Plus, Copy, Trash2, Play,  ChevronDown } from 'lucide-react'
import { cn } from '@/lib/cn'
import { useTestPanel } from '../../../hooks/useTestPanel'
import { Button } from '@/shared/components'
import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface TestPanelProps {
  onRun: () => void
  isRunning: boolean
}

const standardInputCls = 'w-full rounded-[8px] border border-border-soft bg-surface px-3 py-1.5 text-[12.5px] text-[var(--text)] placeholder:text-text-faint outline-none transition-[background-color,border-color] [transition-duration:120ms] hover:border-border hover:bg-surface-2 focus:border-accent focus:bg-surface-2'
const jsonAreaCls = 'w-full rounded-[8px] border border-border-faint bg-bg px-3 py-2.5 text-xs text-[var(--text)] font-mono placeholder:text-text-faint outline-none transition-[background-color,border-color] [transition-duration:120ms] hover:border-border-soft focus:border-border focus:bg-surface leading-relaxed'

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
    patchSelected, setVar, addVar, removeVar,
    addScenario, duplicateScenario, deleteScenario, runScenario,
  } = useTestPanel(onRun)

  const [scenariosOpen, setScenariosOpen] = useState(true)

  return (
    <div className="flex h-full flex-col overflow-hidden bg-[var(--bg-2)]">
      {/* Collapsible Scenarios List */}
      <div className="shrink-0 border-b border-[var(--border-faint)] bg-[var(--bg-2)]">
        <div className="flex items-center justify-between px-4 py-2">
          <Button
            type="button"
            variant="ghost"
            onClick={() => setScenariosOpen(!scenariosOpen)}
            className="flex items-center gap-1.5 text-[10.5px] font-bold uppercase tracking-[0.08em] text-[var(--text-dim)] hover:text-[var(--text)] transition-colors h-auto p-0 hover:bg-transparent active:scale-100"
          >
            <span>Saved Scenarios ({scenarios.length})</span>
            <ChevronDown
              className={cn(
                "h-3.5 w-3.5 text-[var(--text-faint)] transition-transform duration-150",
                scenariosOpen && "rotate-180"
              )}
            />
          </Button>
          <div className="flex items-center gap-1">
            <Button
              variant="icon-sm"
              onClick={addScenario}
              title="New scenario"
              className="h-6 w-6 p-0 bg-transparent border-none hover:bg-[var(--surface)] hover:text-[var(--text)]"
            >
              <Plus className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        <AnimatePresence initial={false}>
          {scenariosOpen && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.18, ease: 'easeInOut' }}
              className="overflow-hidden"
            >
              <div className="flex flex-col gap-1 px-3 pb-3 max-h-[200px] overflow-y-auto">
                {scenarios.map(s => {
                  const isActive = s.id === selectedId
                  return (
                    <div
                      key={s.id}
                      onClick={() => {
                        setSelectedId(s.id)
                      }}
                      className={cn(
                        'group relative flex h-8 w-full items-center justify-between gap-2.5 rounded-[6px] px-2.5 text-left transition-all [transition-duration:120ms] cursor-pointer select-none',
                        isActive
                          ? 'bg-[var(--surface)] text-[var(--text)] border-l-2 border-[var(--accent)] pl-2'
                          : 'text-[var(--text-mute)] hover:bg-[var(--surface)]/30 hover:text-[var(--text)] border-l-2 border-transparent pl-2',
                      )}
                    >
                      <span className="truncate text-[12.5px] min-w-0 flex-1">{s.name}</span>

                      <span className="text-[10px] text-[var(--text-faint)] shrink-0 font-medium font-mono group-hover:opacity-0 transition-opacity [transition-duration:120ms]">
                        {s.lastRun ? s.lastRun.t : 'never'}
                      </span>

                      <div className="absolute right-2.5 opacity-0 pointer-events-none group-hover:opacity-100 group-hover:pointer-events-auto flex items-center gap-1 shrink-0 transition-opacity [transition-duration:120ms]">
                        <Button
                          variant="icon-sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            duplicateScenario(s.id)
                          }}
                          title="Duplicate scenario"
                          className="h-5.5 w-5.5 p-0 bg-transparent border-none text-[var(--text-faint)] hover:bg-[var(--surface-2)] hover:text-[var(--text)]"
                        >
                          <Copy className="h-3 w-3" />
                        </Button>
                        <Button
                          variant="icon-sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            deleteScenario(s.id)
                          }}
                          disabled={scenarios.length <= 1}
                          title="Delete scenario"
                          className="h-5.5 w-5.5 p-0 bg-transparent border-none text-[var(--text-faint)] hover:bg-[var(--surface-2)] hover:text-[var(--err)] disabled:opacity-30"
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Editor */}
      <div className="min-h-0 flex-1 overflow-y-auto [scrollbar-width:none] [&::-webkit-scrollbar]:hidden">
        <div className="flex flex-col gap-4 p-4">
          {/* Scenario Name */}
          <Field label="Scenario name">
            <input
              value={selected.name}
              onChange={e => patchSelected({ name: e.target.value })}
              placeholder="Enter scenario name"
              className={standardInputCls}
            />
          </Field>

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
                    <Button
                      variant="icon-sm"
                      onClick={() => removeVar(i)}
                      className="hover:text-[var(--err)]"
                    >
                      <Trash2 />
                    </Button>
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
        <Button
          onClick={runScenario}
          disabled={isRunning}
          loading={isRunning}
          variant="primary"
          className="w-full font-semibold"
          leftIcon={<Play className="h-3.5 w-3.5 fill-current" />}
        >
          Run scenario
        </Button>
      </div>
    </div>
  )
}
