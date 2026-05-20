import type { ComponentType } from 'react'
import { 
  Table, 
  Files, 
  Database, 
  Calendar, 
  ScrollText,
  User,
  Puzzle,
  Key,
  Wrench,
  Lightbulb,
  Layers,
  KeyRound,
  Server,
  Trash2,
  Cpu,
  Bot,
  Users
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export interface NavItem {
  id: string
  label: string
  href: string
  icon: LucideIcon | ComponentType<{ className?: string }>
}

export interface NavSection {
  id: string
  label: string
  items: NavItem[]
}

/**
 * Main application navigation configuration.
 */
export const MAIN_NAV: NavSection[] = [
  {
    id: "workspace",
    label: "Workspace",
    items: [
      { id: "tables", label: "Tables", href: "/tables", icon: Table },
      { id: "files", label: "Files", href: "/files", icon: Files },
      { id: "kb", label: "Knowledge Base", href: "/kb", icon: Database },
      { id: "scheduled", label: "Scheduled Tasks", href: "/scheduled", icon: Calendar },
      { id: "logs", label: "Logs", href: "/logs", icon: ScrollText },
    ]
  }
]

/**
 * Settings-specific navigation configuration.
 */
export const SETTINGS_NAV: NavSection[] = [
  {
    id: "account",
    label: "Account",
    items: [
      { id: "general", label: "General", href: "/settings/general", icon: User },
      { id: "team", label: "Team", href: "/settings/team", icon: Users },
      { id: "integrations", label: "Integrations", href: "/settings/integrations", icon: Puzzle },
      { id: "secrets", label: "Secrets", href: "/settings/secrets", icon: Key },
    ]
  },
  {
    id: "tools",
    label: "Tools",
    items: [
      { id: "skills", label: "Tools", href: "/settings/skills", icon: Lightbulb },
    ]
  },
  {
    id: "system",
    label: "System",
    items: [
      { id: "keys", label: "Fuse Keys", href: "/settings/keys", icon: KeyRound },
      { id: "mcp-servers", label: "MCP Servers", href: "/settings/mcp-servers", icon: Server },
      { id: "byok", label: "BYOK", href: "/settings/byok", icon: Cpu },
      { id: "copilot-keys", label: "Copilot Keys", href: "/settings/copilot-keys", icon: Bot },
      { id: "recently-deleted", label: "Recently Deleted", href: "/settings/deleted", icon: Trash2 },
    ]
  }
]
