/**
 * Component representing the loading indicator for the workflow editor.
 */
export function EditorLoading() {
  return (
    <div className="flex h-full w-full items-center justify-center bg-[var(--bg)]">
      <div className="w-8 h-8 border-2 border-[var(--border)] border-t-[var(--text-mute)] rounded-full animate-spin" />
    </div>
  )
}
