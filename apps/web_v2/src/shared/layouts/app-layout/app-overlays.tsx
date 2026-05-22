import { createPortal } from 'react-dom'
import { Icons } from '@/shared/components/icons'
import type { AppLayoutController } from './use-app-layout-controller'

interface AppOverlaysProps {
  controller: AppLayoutController
}

const SHORTCUT_GROUPS = [
  {
    group: 'Navigation',
    items: [
      { keys: ['⌘', 'K'], label: 'Command palette' },
      { keys: ['⌘', ','], label: 'Account settings' },
      { keys: ['?'], label: 'Keyboard shortcuts' },
      { keys: ['G', 'H'], label: 'Go to Home' },
      { keys: ['G', 'A'], label: 'Go to Automations' },
      { keys: ['G', 'R'], label: 'Go to Runs' },
    ],
  },
  {
    group: 'Workflows',
    items: [
      { keys: ['⌘', 'N'], label: 'New automation' },
      { keys: ['⌘', 'Enter'], label: 'Run workflow' },
      { keys: ['⌘', 'S'], label: 'Save workflow' },
      { keys: ['⌘', 'Z'], label: 'Undo' },
      { keys: ['⌘', '⇧', 'Z'], label: 'Redo' },
      { keys: ['Esc'], label: 'Close / cancel' },
    ],
  },
]

export function AppOverlays({ controller }: AppOverlaysProps) {
  return (
    <>
      <KeyboardShortcutsModal
        open={controller.shortcutsOpen}
        onClose={() => controller.setShortcutsOpen(false)}
      />
      <FeedbackModal
        open={controller.feedbackOpen}
        text={controller.feedbackText}
        sent={controller.feedbackSent}
        onTextChange={controller.setFeedbackText}
        onSend={() => {
          if (controller.feedbackText.trim()) controller.setFeedbackSent(true)
        }}
        onClose={controller.resetFeedback}
      />
    </>
  )
}

function KeyboardShortcutsModal({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null

  return createPortal(
    <>
      <div className="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed z-[9999] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[520px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[16px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-[var(--border-faint)]">
          <h3 className="text-[15px] font-semibold text-[var(--text)] tracking-tight">Keyboard shortcuts</h3>
          <button onClick={onClose} className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors text-[13px]">✕</button>
        </div>
        <div className="p-5 grid grid-cols-2 gap-x-8 gap-y-0">
          {SHORTCUT_GROUPS.map(section => (
            <div key={section.group} className="flex flex-col gap-1 pb-4">
              <span className="text-[10.5px] font-mono tracking-widest uppercase text-[var(--text-dim)] mb-2">{section.group}</span>
              {section.items.map(item => (
                <div key={item.label} className="flex items-center justify-between py-1.5">
                  <span className="text-[13px] text-[var(--text-mute)]">{item.label}</span>
                  <div className="flex items-center gap-1">
                    {item.keys.map(key => <span key={key} className="kbd">{key}</span>)}
                  </div>
                </div>
              ))}
            </div>
          ))}
        </div>
      </div>
    </>,
    document.body
  )
}

interface FeedbackModalProps {
  open: boolean
  text: string
  sent: boolean
  onTextChange: (text: string) => void
  onSend: () => void
  onClose: () => void
}

function FeedbackModal({ open, text, sent, onTextChange, onSend, onClose }: FeedbackModalProps) {
  if (!open) return null

  return createPortal(
    <>
      <div className="fixed inset-0 z-[9998] bg-black/50 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed z-[9999] top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-[420px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[16px] p-6 flex flex-col gap-5 shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)]">
        {sent ? (
          <div className="flex flex-col items-center gap-3 py-4 text-center">
            <div className="w-[44px] h-[44px] rounded-full bg-[oklch(0.78_0.14_145/0.14)] flex items-center justify-center">
              <Icons.Check className="w-[20px] h-[20px] text-[var(--ok)]" />
            </div>
            <h3 className="text-[15px] font-semibold text-[var(--text)]">Thanks for your feedback!</h3>
            <p className="text-[13px] text-[var(--text-faint)]">We read every submission and use it to improve fuse.</p>
            <button onClick={onClose} className="mt-2 px-4 py-2 rounded-[9px] bg-[var(--text)] text-[var(--bg)] text-[13px] font-medium border-none cursor-pointer hover:bg-[oklch(0.90_0.003_250)] transition-colors">
              Close
            </button>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between">
              <h3 className="text-[15px] font-semibold text-[var(--text)] tracking-tight">Send feedback</h3>
              <button onClick={onClose} className="w-[28px] h-[28px] rounded-[7px] flex items-center justify-center text-[var(--text-faint)] hover:bg-[var(--surface)] hover:text-[var(--text)] transition-colors text-[13px]">✕</button>
            </div>
            <p className="text-[12.5px] text-[var(--text-faint)] -mt-2">Found a bug? Have a suggestion? We'd love to hear it.</p>
            <textarea
              value={text}
              onChange={event => onTextChange(event.target.value)}
              placeholder="Describe what you're experiencing or what you'd like to see..."
              rows={5}
              className="w-full bg-[var(--bg)] border border-[var(--border-faint)] rounded-[10px] px-4 py-3 text-[13px] text-[var(--text)] placeholder:text-[var(--text-faint)] outline-none resize-none focus:border-[var(--border)] transition-colors"
            />
            <div className="flex items-center justify-end gap-3">
              <button onClick={onClose} className="px-4 py-2 rounded-[9px] text-[13px] font-medium text-[var(--text-mute)] bg-[var(--surface)] border border-[var(--border-faint)] hover:bg-[var(--surface-2)] transition-colors">
                Cancel
              </button>
              <button
                onClick={onSend}
                disabled={!text.trim()}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-[9px] bg-[var(--text)] text-[var(--bg)] text-[13px] font-medium border-none cursor-pointer hover:bg-[oklch(0.90_0.003_250)] transition-colors disabled:opacity-40 disabled:cursor-default"
              >
                <Icons.Feedback className="w-[13px] h-[13px]" />
                Send feedback
              </button>
            </div>
          </>
        )}
      </div>
    </>,
    document.body
  )
}
