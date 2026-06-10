import type { SVGProps } from 'react'
import { Icons } from '@/shared/components/icons'
import { APP_ROUTES } from '@/shared/constants/routes'

export type NavItem = {
  id: string
  label: string
  icon: React.FC<SVGProps<SVGSVGElement>>
  to: string
}

export type NavGroup = {
  group: string
  isWorkflows?: boolean
  items?: NavItem[]
}

export const NAV_GROUPS: NavGroup[] = [
  {
    group: 'Workspace',
    items: [
      { id: 'home', label: 'Home', icon: Icons.Home, to: APP_ROUTES.DASHBOARD },
      { id: 'automations', label: 'Automations', icon: Icons.Flow, to: APP_ROUTES.AUTOMATIONS },
      { id: 'templates', label: 'Templates', icon: Icons.Layers, to: APP_ROUTES.TEMPLATES },
    ],
  },
  {
    group: 'Operate',
    items: [
      { id: 'runs', label: 'Runs', icon: Icons.Activity, to: APP_ROUTES.RUNS },
      { id: 'schedules', label: 'Schedules', icon: Icons.Clock, to: APP_ROUTES.SCHEDULES },
      { id: 'logs', label: 'Logs', icon: Icons.Terminal, to: APP_ROUTES.LOGS },
    ],
  },
  {
    group: 'Data',
    items: [
      { id: 'tables', label: 'Tables', icon: Icons.Table, to: APP_ROUTES.TABLES },
      { id: 'files', label: 'Files', icon: Icons.Folder, to: APP_ROUTES.FILES },
      { id: 'knowledge', label: 'Knowledge base', icon: Icons.Book, to: APP_ROUTES.KNOWLEDGE },
      { id: 'variables', label: 'Variables', icon: Icons.Key, to: APP_ROUTES.VARIABLES },
    ],
  },
  {
    group: 'Integrations',
    items: [
      { id: 'connections', label: 'Connections', icon: Icons.Plug, to: APP_ROUTES.CONNECTIONS },
    ],
  },
  { group: 'Workflows', isWorkflows: true },
]

export const MENU_ITEM_CLASS =
  'flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0'

export const NAV_LINK_CLASS =
  "flex items-center gap-[10px] py-[7px] px-[10px] rounded-[8px] text-[13px] text-[var(--text-mute)] cursor-pointer transition-colors duration-100 w-full font-medium no-underline relative hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[15px] [&_svg]:h-[15px] [&_svg]:text-current [&_svg]:opacity-85 group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:p-[9px] group-data-[collapsed=true]/shell:gap-0"

export const ACTIVE_NAV_LINK_CLASS =
  "bg-[var(--surface)] text-[var(--text)] group-data-[collapsed=true]/shell:shadow-[inset_0_0_0_1px_var(--border-soft)] before:content-[''] before:w-[3px] before:h-[14px] before:bg-[var(--text)] before:rounded-[0_2px_2px_0] before:absolute before:left-0 group-data-[collapsed=true]/shell:before:hidden"


