interface EditorErrorProps {
  /**
   * Callback triggered when the user clicks the back button.
   */
  onBack: () => void
}

/**
 * Component representing the error state screen for the workflow editor.
 */
export function EditorError({ onBack }: EditorErrorProps) {
  return (
    <div className="flex h-full w-full flex-col items-center justify-center bg-[var(--bg)] gap-4">
      <p className="text-[14px] text-[var(--err)]">Failed to load workflow</p>
      <button
        onClick={onBack}
        className="btn btn-secondary"
      >
        Back to automations
      </button>
    </div>
  )
}
