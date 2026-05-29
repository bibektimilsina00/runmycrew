import React, { useState } from 'react'
import { Icons, useToast } from '@/shared/components'

interface PromptCardProps {
  onSubmit: (prompt: string, mode: 'flow' | 'agent') => void
}

export function PromptCard({ onSubmit }: PromptCardProps) {
  const { toast } = useToast()
  const [prompt, setPrompt] = useState('')
  const [mode, setMode] = useState<'flow' | 'agent'>('flow')

  const handleSend = () => {
    onSubmit(prompt, mode)
    setPrompt('')
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] pt-[16px] px-[18px] pb-[12px] transition-colors duration-200 focus-within:border-[var(--accent-line)]">
      <textarea className="w-full bg-transparent border-none outline-none resize-none text-[14.5px] text-[var(--text)] min-h-[60px] leading-[1.5] placeholder:text-[var(--text-faint)]"
        value={prompt}
        onChange={(e) => setPrompt(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Describe an automation. fuse drafts the flow, wires the connectors, and tests it before shipping."
      />
      <div className="flex items-center justify-between mt-[6px] gap-[8px]">
        <div className="flex items-center gap-[4px]">
          <button
            className="w-[28px] h-[28px] inline-flex items-center justify-center rounded-[7px] text-[var(--text-mute)] transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)]"
            title="Attach"
            onClick={() => toast('Attachment feature', { description: 'File uploads will be available in the next release.' })}
          >
            <Icons.Plus className="w-3.5 h-3.5" />
          </button>
          <div className="inline-flex bg-[var(--surface)] rounded-[7px] p-[2px] ml-[4px]">
            <button
              className={mode === 'flow' ? "bg-[var(--surface-2)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)] flex items-center gap-[6px] py-[5px] px-[10px] text-[12px] rounded-[5px] font-medium" : "flex items-center gap-[6px] py-[5px] px-[10px] text-[12px] text-[var(--text-mute)] rounded-[5px] font-medium"}
              onClick={() => setMode('flow')}
            >
              <Icons.Flow className="w-3 h-3" />
              <span>Flow</span>
            </button>
            <button
              className={mode === 'agent' ? "bg-[var(--surface-2)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)] flex items-center gap-[6px] py-[5px] px-[10px] text-[12px] rounded-[5px] font-medium" : "flex items-center gap-[6px] py-[5px] px-[10px] text-[12px] text-[var(--text-mute)] rounded-[5px] font-medium"}
              onClick={() => setMode('agent')}
            >
              <Icons.Spark className="w-3 h-3 text-accent" />
              <span>Agent</span>
            </button>
          </div>
        </div>
        <div className="flex items-center gap-[4px]">
          <button
            className="w-[28px] h-[28px] inline-flex items-center justify-center rounded-[7px] text-[var(--text-mute)] transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)]"
            title="Connections"
            onClick={() => toast('Quick connections view', { description: 'Showing 18 active connectors.' })}
          >
            <Icons.Plug className="w-3.5 h-3.5" />
          </button>
          <div
            className={`inline-flex items-center gap-[6px] py-[5px] pr-[9px] pl-[8px] rounded-[7px] bg-[var(--surface)] text-[12px] text-[var(--text)] border border-[var(--border-faint)] font-medium cursor-pointer`}
            onClick={() => toast('Model selected', { description: 'Currently utilizing Filament 2 for generation.' })}
          >
            <span className="text-[var(--accent)] inline-flex">
              <Icons.Spark style={{ width: 12, height: 12 }} />
            </span>
            <span>Filament 2</span>
            <Icons.Caret style={{ width: 11, height: 11, color: 'var(--text-mute)' }} />
          </div>
          <button
            className="w-[28px] h-[28px] inline-flex items-center justify-center rounded-[7px] text-[var(--text-mute)] transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)]"
            title="Dictate"
            onClick={() => toast('Voice Input', { description: 'Speech-to-text is currently being trained.' })}
          >
            <Icons.Mic className="w-3.5 h-3.5" />
          </button>
          <button className="w-[28px] h-[28px] rounded-[7px] bg-[var(--text)] text-[var(--bg)] inline-flex items-center justify-center hover:bg-[var(--accent)] hover:text-[oklch(0.18_0.02_250)]" onClick={handleSend} title="Send prompt">
            <Icons.ArrowUp className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  )
}
