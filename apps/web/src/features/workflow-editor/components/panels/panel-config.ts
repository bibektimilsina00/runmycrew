import {
  Sparkles,
  Blocks,
  Database,
  SlidersHorizontal,
  Play,
  Terminal,
  type LucideIcon,
} from 'lucide-react'
import type { EditorTab } from '../../stores/editorLayoutStore'

export const DRAG_MIME = 'application/x-runmycrew-tab'

export interface PanelTabMeta {
  id: EditorTab
  label: string
  Icon: LucideIcon
  /** Tabs that are pinned to one zone and cannot be dragged. */
  locked?: boolean
}

export const PANEL_TABS: readonly PanelTabMeta[] = [
  { id: 'copilot', label: 'Copilot',   Icon: Sparkles },
  { id: 'library', label: 'Library',   Icon: Blocks },
  { id: 'config',  label: 'Inspector', Icon: SlidersHorizontal },
  { id: 'memory',  label: 'Memory',    Icon: Database },
  { id: 'logs',    label: 'Logs',      Icon: Terminal, locked: true },
  { id: 'test',    label: 'Test',      Icon: Play },
] as const

export function tabMeta(id: EditorTab): PanelTabMeta | undefined {
  return PANEL_TABS.find((t) => t.id === id)
}
