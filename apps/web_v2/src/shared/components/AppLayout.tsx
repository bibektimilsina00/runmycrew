import { useState } from 'react'
import { createPortal } from 'react-dom'
import { WorkspaceSelector, useWorkspaces } from '@/features/workspaces'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '@/features/auth/hooks/useAuth'
import { ThemeToggle } from '@/shared/components'
import { Icons } from '@/shared/components/icons'
import { APP_ROUTES } from '@/shared/constants/routes'
import { cn } from '@/lib/cn'


const classes = {
  "shell": "relative h-screen grid grid-cols-[244px_1fr] gap-[14px] z-10 data-[collapsed=true]:grid-cols-[64px_1fr]",
  "sidebar": "relative my-[14px] ml-[14px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[16px] flex flex-col overflow-visible shadow-[inset_0_1px_0_oklch(0.30_0.004_250/0.4),0_24px_48px_-28px_oklch(0_0_0/0.6)] z-20",
  "sidebarTop": "shrink-0 pt-[14px] px-[10px] pb-[12px] flex flex-col gap-[12px] border-b border-[var(--border-faint)] group-data-[collapsed=true]/shell:pt-[14px] group-data-[collapsed=true]/shell:px-[8px] group-data-[collapsed=true]/shell:pb-[12px] group-data-[collapsed=true]/shell:gap-[10px]",
  "sidebarScroll": "flex-1 min-h-0 overflow-y-auto pt-[8px] px-[10px] pb-[10px] flex flex-col gap-0 [&::-webkit-scrollbar]:w-[5px] [&::-webkit-scrollbar-thumb]:bg-[var(--border)] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-transparent group-data-[collapsed=true]/shell:px-[8px]",
  "sidebarFootActions": "shrink-0 p-[8px] border-t border-[var(--border-faint)] flex gap-[4px] group-data-[collapsed=true]/shell:hidden",
  "footAction": "flex-1 inline-flex items-center justify-center gap-[6px] py-[7px] px-[8px] rounded-[7px] text-[12px] text-[var(--text-mute)] font-medium transition-colors duration-100 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]",
  "brandRow": "flex items-center justify-between py-[2px] px-[6px] pb-[4px] group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:flex-col group-data-[collapsed=true]/shell:gap-[10px] group-data-[collapsed=true]/shell:px-[4px]",
  "brand": "inline-flex items-center gap-[9px] text-[15px] font-semibold tracking-tight text-[var(--text)] group-data-[collapsed=true]/shell:gap-0",
  "brandMark": "w-[22px] h-[22px] inline-flex items-center justify-center rounded-[6px] bg-[var(--text)] text-[var(--bg)]",
  "brandText": "inline group-data-[collapsed=true]/shell:hidden",
  "brandBadge": "font-mono text-[9.5px] tracking-[0.14em] uppercase text-[var(--text-faint)] border border-[var(--border-soft)] py-[2px] px-[6px] pb-[1px] rounded-[4px] ml-[6px] group-data-[collapsed=true]/shell:hidden",
  "brandTrailBtn": "w-[24px] h-[24px] rounded-[6px] text-[var(--text-faint)] inline-flex items-center justify-center hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]",
  "cmdSearch": "flex items-center gap-[8px] px-[10px] h-[34px] rounded-[9px] bg-[var(--bg)] border border-[var(--border-faint)] transition-colors duration-120 w-full min-w-0 hover:border-[var(--border-soft)] focus-within:border-[var(--border)] focus-within:bg-[var(--surface)] [&>svg]:w-[14px] [&>svg]:h-[14px] [&>svg]:text-[var(--text-faint)] [&>svg]:shrink-0 group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:px-0 group-data-[collapsed=true]/shell:gap-0",
  "navSection": "flex flex-col gap-[1px] pb-[4px] group-data-[collapsed=true]/shell:pb-[6px] group-data-[collapsed=true]/shell:border-t group-data-[collapsed=true]/shell:border-[var(--border-faint)] group-data-[collapsed=true]/shell:pt-[6px] first:border-none first:pt-0",
  "isClosed": "pb-0",
  "navGroupHead": "flex items-center gap-[6px] pt-[8px] px-[10px] pb-[4px] font-mono text-[10px] tracking-widest uppercase text-[var(--text-dim)] font-medium cursor-pointer w-full text-left transition-colors duration-100 hover:text-[var(--text-mute)] group-data-[collapsed=true]/shell:hidden relative",
  "navGroupCaret": "inline-flex w-[12px] h-[12px] transition-transform duration-160 [&_svg]:w-[11px] [&_svg]:h-[11px]",
  "navGroupLabel": "flex-1",
  "navGroupCount": "font-mono text-[9.5px] text-[var(--text-faint)] ml-[4px] font-medium",
  "navGroupIconBtn": "w-[20px] h-[20px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center transition-colors duration-100 shrink-0 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[12px] [&_svg]:h-[12px]",
  "isOpen": "bg-[var(--surface-2)] text-[var(--text)]",
  "isWorkflows": "relative",
  "navItem": "flex items-center gap-[10px] py-[7px] px-[10px] rounded-[8px] text-[13px] text-[var(--text-mute)] cursor-pointer transition-colors duration-100 w-full font-medium no-underline relative hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[15px] [&_svg]:h-[15px] [&_svg]:text-current [&_svg]:opacity-85 group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:p-[9px] group-data-[collapsed=true]/shell:gap-0",
  "active": "bg-[var(--surface)] text-[var(--text)] group-data-[collapsed=true]/shell:shadow-[inset_0_0_0_1px_var(--border-soft)] before:content-[''] before:w-[3px] before:h-[14px] before:bg-[var(--text)] before:rounded-[0_2px_2px_0] before:absolute before:left-0 group-data-[collapsed=true]/shell:before:hidden",
  "navLabelText": "flex-1 group-data-[collapsed=true]/shell:hidden",
  "navCount": "ml-auto font-mono text-[10.5px] text-[var(--text-faint)] font-medium group-data-[collapsed=true]/shell:hidden",
  "wfTree": "flex flex-col gap-[1px] group-data-[collapsed=true]/shell:hidden",
  "wfRowWrap": "relative group-data-[collapsed=true]/shell:hidden",
  "wfRow": "flex items-center gap-[9px] pt-[6px] pr-[6px] pb-[6px] pl-[12px] rounded-[8px] text-[12.5px] text-[var(--text-mute)] cursor-pointer transition-colors duration-100 w-full text-left font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] group/wf",
  "wfName": "flex-1 min-w-0 whitespace-nowrap overflow-hidden text-ellipsis tracking-tight",
  "rowMore": "w-[22px] h-[22px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center opacity-0 transition-all duration-100 shrink-0 hover:bg-[var(--surface-2)] hover:text-[var(--text)] group-hover/wf:opacity-100 group-hover/folder:opacity-100 [&_svg]:w-[13px] [&_svg]:h-[13px]",
  "folder": "relative group-data-[collapsed=true]/shell:hidden group/folder",
  "folderHead": "flex items-center gap-[8px] p-[6px] rounded-[8px] text-[12.5px] text-[var(--text-mute)] cursor-pointer transition-colors duration-100 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)]",
  "folderCaret": "w-[12px] h-[12px] inline-flex items-center justify-center transition-transform duration-140 text-[var(--text-faint)] shrink-0 [&_svg]:w-[10px] [&_svg]:h-[10px]",
  "folderIcon": "inline-flex text-[var(--text-mute)] shrink-0 [&_svg]:w-[14px] [&_svg]:h-[14px]",
  "folderName": "flex-1 min-w-0 whitespace-nowrap overflow-hidden text-ellipsis tracking-tight",
  "folderCount": "font-mono text-[10px] text-[var(--text-faint)] font-medium px-[2px]",
  "folderBody": "pl-[14px] flex flex-col relative before:content-[''] before:absolute before:left-[11px] before:top-[4px] before:bottom-[4px] before:w-[1px] before:bg-[var(--border-faint)]",
  "dropdownBackdrop": "fixed inset-0 z-40",
  "rowMenu": "w-[240px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[11px] p-[5px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] animate-in fade-in zoom-in-95 duration-100",
  "dropdownItem": "flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0",
  "danger": "text-[var(--err)] hover:bg-[oklch(0.70_0.18_22/0.10)]",
  "itemSub": "ml-auto font-mono text-[10.5px] text-[var(--text-faint)]",
  "dropdownSep": "h-[1px] bg-[var(--border-faint)] my-[4px]",
  "main": "relative overflow-hidden h-screen pt-[14px] pr-[14px] pb-[14px] pl-0 flex flex-col",
  "mainCard": "bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[16px] h-full overflow-hidden shadow-[inset_0_1px_0_oklch(0.30_0.004_250/0.4),0_24px_48px_-28px_oklch(0_0_0/0.6)] flex flex-col flex-1 min-h-0",
  "mainContent": "flex-1 min-h-0 overflow-y-auto [&::-webkit-scrollbar]:w-[6px] [&::-webkit-scrollbar-thumb]:bg-[var(--border)] [&::-webkit-scrollbar-thumb]:rounded-full",
  "topbar": "flex items-center justify-between py-[14px] px-[22px] border-b border-[var(--border-faint)] shrink-0",
  "crumbs": "flex items-center gap-[8px] text-[13px] text-[var(--text-mute)]",
  "sep": "text-[var(--text-dim)]",
  "cur": "text-[var(--text)] font-medium",
  "topbarActions": "flex items-center gap-[6px]",
  "iconBtn": "w-[32px] h-[32px] inline-flex items-center justify-center rounded-[8px] text-[var(--text-mute)] relative transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[16px] [&_svg]:h-[16px]",
  "indicator": "absolute top-[7px] right-[8px] w-[6px] h-[6px] rounded-full bg-[var(--accent)] border-2 border-[var(--bg-2)]",
  "profileWrap": "relative",
  "avatar": "w-[28px] h-[28px] rounded-[8px] bg-[var(--surface-3)] border border-[var(--border-soft)] cursor-pointer inline-flex items-center justify-center text-[11px] font-semibold text-[var(--text)] tracking-tight bg-cover bg-center transition-colors duration-120 hover:border-[var(--border)]",
  "profileDropdown": "absolute top-[calc(100%+8px)] right-0 w-[260px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[13px] p-[6px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] z-50 animate-in fade-in slide-in-from-top-2",
  "profileHead": "flex items-center gap-[10px] pt-[8px] px-[8px] pb-[10px]",
  "profileAvatar": "w-[32px] h-[32px] rounded-[9px] bg-[var(--surface-3)] border border-[var(--border-soft)] inline-flex items-center justify-center text-[13px] font-semibold text-[var(--text)] shrink-0",
  "profileMeta": "flex flex-col gap-[1px] min-w-0",
  "profileName": "text-[13px] font-medium",
  "profileEmail": "text-[11px] text-[var(--text-faint)] font-mono",
  "profileWorkspace": "flex items-center gap-[9px] py-[8px] px-[10px] rounded-[8px] bg-[var(--surface)] my-0 mx-[2px] mb-[4px] cursor-pointer [&>svg]:w-[13px] [&>svg]:h-[13px] [&>svg]:text-[var(--text-faint)] [&>svg]:ml-auto",
  "workspaceAvatar": "w-[26px] h-[26px] rounded-[7px] bg-[var(--text)] text-[var(--bg)] inline-flex items-center justify-center text-[11px] font-semibold tracking-tight shrink-0",
  "workspaceAvatarSm": "w-[22px] h-[22px] text-[10px]",
  "workspaceMeta": "flex flex-col gap-[1px] min-w-0 flex-1",
  "workspaceName": "text-[13px] font-medium text-[var(--text)] whitespace-nowrap overflow-hidden text-ellipsis tracking-tight"
};

const WORKFLOWS_TREE = [
  {
    type: 'folder' as const, id: 'f1', name: 'Revenue ops', items: [
      { id: 'wf1', name: 'Stripe refund — Slack approval', state: 'ok' },
      { id: 'wf2', name: 'Lead enrichment — Clearbit → HubSpot', state: 'ok' },
      { id: 'wf6', name: 'Invoice triage agent', state: 'ok' },
    ],
  },
  {
    type: 'folder' as const, id: 'f2', name: 'Inbox & support', items: [
      { id: 'wf3', name: 'Inbound RFP classifier', state: 'ok' },
      { id: 'wf7', name: 'Support ticket auto-tagger', state: 'warn' },
    ],
  },
  {
    type: 'folder' as const, id: 'f3', name: 'Engineering', items: [
      { id: 'wf4', name: 'Daily brief from Linear + GitHub', state: 'ok' },
      { id: 'wf9', name: 'Pager rotation handoff', state: 'warn' },
    ],
  },
  { type: 'wf' as const, id: 'wf5', name: 'Notion → Airtable nightly sync', state: 'err' },
  { type: 'wf' as const, id: 'wf8', name: 'Weekly metrics digest', state: 'ok' },
  { type: 'wf' as const, id: 'wf10', name: 'Churn-risk watchlist', state: 'ok' },
  { type: 'wf' as const, id: 'wf11', name: 'Contract redline assistant', state: 'draft' },
]

const TOTAL_WFS = WORKFLOWS_TREE.reduce(
  (n, node) => n + (node.type === 'folder' ? node.items.length : 1),
  0
)

type NavGroup = {
  group: string
  isWorkflows?: boolean
  items?: { id: string; label: string; icon: React.FC<React.SVGProps<SVGSVGElement>>; count?: string; to: string }[]
}

const NAV: NavGroup[] = [
  {
    group: 'Workspace', items: [
      { id: 'home', label: 'Home', icon: Icons.Home, to: APP_ROUTES.DASHBOARD },
      { id: 'automations', label: 'Automations', icon: Icons.Flow, count: '47', to: APP_ROUTES.AUTOMATIONS },
      { id: 'templates', label: 'Templates', icon: Icons.Layers, to: APP_ROUTES.TEMPLATES },
    ],
  },
  {
    group: 'Operate', items: [
      { id: 'runs', label: 'Runs', icon: Icons.Activity, count: '1.2k', to: APP_ROUTES.RUNS },
      { id: 'schedules', label: 'Schedules', icon: Icons.Clock, count: '6', to: APP_ROUTES.SCHEDULES },
      { id: 'logs', label: 'Logs', icon: Icons.Terminal, to: APP_ROUTES.LOGS },
    ],
  },
  {
    group: 'Data', items: [
      { id: 'tables', label: 'Tables', icon: Icons.Table, count: '8', to: APP_ROUTES.TABLES },
      { id: 'files', label: 'Files', icon: Icons.Folder, count: '124', to: APP_ROUTES.FILES },
      { id: 'knowledge', label: 'Knowledge base', icon: Icons.Book, count: '8', to: APP_ROUTES.KNOWLEDGE },
      { id: 'variables', label: 'Variables', icon: Icons.Key, to: APP_ROUTES.VARIABLES },
    ],
  },
  {
    group: 'Integrations', items: [
      { id: 'connections', label: 'Connections', icon: Icons.Plug, count: '18', to: APP_ROUTES.CONNECTIONS },
    ],
  },
  { group: 'Workflows', isWorkflows: true },
]

export function AppLayout() {
  const { user, logout } = useAuth()
  const location = useLocation()
  useWorkspaces() // bootstrap workspace list + auto-select

  const [collapsed, setCollapsed] = useState(false)
  const [profileOpen, setProfileOpen] = useState(false)
  const [openGroups, setOpenGroups] = useState<Record<string, boolean>>({
    Workspace: true, Operate: true, Workflows: true, Data: false, Integrations: false,
  })
  const [folderOpen, setFolderOpen] = useState<Record<string, boolean>>({
    f1: true, f2: false, f3: false,
  })
  const [menuOpen, setMenuOpen] = useState<string | null>(null)
  const [menuPos, setMenuPos] = useState<{ top: number; left: number } | null>(null)

  const toggleGroup = (g: string) => setOpenGroups(s => ({ ...s, [g]: !s[g] }))
  const toggleFolder = (f: string) => setFolderOpen(s => ({ ...s, [f]: !s[f] }))
  const closeMenus = () => { setMenuOpen(null); setMenuPos(null) }
  const stopAndOpen = (e: React.MouseEvent, id: string) => {
    e.stopPropagation()
    e.preventDefault()
    if (menuOpen === id) {
      setMenuOpen(null)
      setMenuPos(null)
    } else {
      const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
      setMenuPos({ top: rect.top, left: rect.right + 4 })
      setMenuOpen(id)
    }
  }

  const pageName = location.pathname.substring(1) || 'dashboard'
  const pageLabel = pageName.charAt(0).toUpperCase() + pageName.slice(1)

  const DropdownMenu = ({ id, children }: { id: string; children: React.ReactNode }) => {
    if (menuOpen !== id || !menuPos) return null
    return createPortal(
      <>
        <div
          style={{ position: 'fixed', inset: 0, zIndex: 9998 }}
          onClick={e => { e.stopPropagation(); closeMenus() }}
        />
        <div
          className={classes.rowMenu}
          style={{ position: 'fixed', top: menuPos.top, left: menuPos.left, zIndex: 9999 }}
          onClick={e => e.stopPropagation()}
        >
          {children}
        </div>
      </>,
      document.body
    )
  }

  const renderWfRow = (wf: { id: string; name: string; state: string }) => (
    <div key={wf.id} className={classes.wfRowWrap}>
      <div className={classes.wfRow} title={wf.name}>
        <span className={`status-dot ${wf.state}`} />
        <span className={classes.wfName}>{wf.name}</span>
        <button
          className={`${classes.rowMore}${menuOpen === `wf-${wf.id}` ? ' ' + classes.isOpen : ''}`}
          onClick={e => stopAndOpen(e, `wf-${wf.id}`)}
          title="More"
        >
          <Icons.More />
        </button>
      </div>
      <DropdownMenu id={`wf-${wf.id}`}>
        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Edit /> Open in canvas</button>
        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Activity /> View runs</button>
        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Edit /> Rename</button>
        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Copy /> Duplicate</button>
        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Folder /> Move to folder</button>
        <div className={classes.dropdownSep} />
        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Pause /> Pause</button>
        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Download /> Export</button>
        <div className={classes.dropdownSep} />
        <button className={`${classes.dropdownItem} ${classes.danger}`} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Trash /> Delete</button>
      </DropdownMenu>
    </div>
  )

  const renderFolder = (folder: typeof WORKFLOWS_TREE[0] & { type: 'folder' }) => {
    const open = folderOpen[folder.id]
    return (
      <div key={folder.id} className={classes.folder}>
        <div
          className={`${classes.folderHead}${open ? '' : ' ' + classes.isClosed}`}
          onClick={() => toggleFolder(folder.id)}
        >
          <span className={classes.folderCaret}><Icons.Caret /></span>
          <span className={classes.folderIcon}><Icons.Folder /></span>
          <span className={classes.folderName}>{folder.name}</span>
          <span className={classes.folderCount}>{folder.items.length}</span>
          <button
            className={`${classes.rowMore}${menuOpen === `folder-${folder.id}` ? ' ' + classes.isOpen : ''}`}
            onClick={e => stopAndOpen(e, `folder-${folder.id}`)}
            title="More"
          >
            <Icons.More />
          </button>
          <DropdownMenu id={`folder-${folder.id}`}>
            <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Plus /> New workflow in folder</button>
            <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Folder /> New subfolder</button>
            <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Edit /> Rename folder</button>
            <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Copy /> Duplicate folder</button>
            <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Download /> Export workflows</button>
            <div className={classes.dropdownSep} />
            <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Sort /> Sort A → Z</button>
            <div className={classes.dropdownSep} />
            <button className={`${classes.dropdownItem} ${classes.danger}`} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Trash /> Delete folder</button>
          </DropdownMenu>
        </div>
        {open && (
          <div className={classes.folderBody}>
            {folder.items.map(renderWfRow)}
          </div>
        )}
      </div>
    )
  }

  return (
    <div className={cn("group/shell", classes.shell)} data-collapsed={collapsed}>
      <div className="dot-grid" />

      {/* ── Sidebar ── */}
      <aside className={classes.sidebar}>
        <div className={classes.sidebarTop}>
          <div className={classes.brandRow}>
            <span className={classes.brand}>
              <span className={classes.brandMark}><Icons.FuseMark style={{ width: 14, height: 14 }} /></span>
              <span className={classes.brandText}>fuse</span>
              <span className={classes.brandBadge}>Beta</span>
            </span>
            <button
              className={classes.brandTrailBtn}
              onClick={() => setCollapsed(c => !c)}
              title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            >
              {collapsed ? <Icons.PanelOpen /> : <Icons.PanelClose />}
            </button>
          </div>

          <WorkspaceSelector />

          <div className={classes.cmdSearch}>
            <Icons.Search />
            <input placeholder="Search" className="bg-transparent border-none outline-none flex-1 min-w-0 text-[13px] text-[var(--text)] tracking-tight p-0 placeholder:text-[var(--text-faint)] group-data-[collapsed=true]/shell:hidden" />
            <span className="kbd group-data-[collapsed=true]/shell:hidden">⌘K</span>
          </div>
        </div>

        {/* Nav groups */}
        <div className={classes.sidebarScroll}>
          {NAV.map((section, gi) => {
            const open = openGroups[section.group]
            return (
              <div
                key={gi}
                className={[
                  classes.navSection,
                  open ? '' : classes.isClosed,
                  section.isWorkflows ? classes.isWorkflows : '',
                ].filter(Boolean).join(' ')}
              >
                <div className={classes.navGroupHead} onClick={() => toggleGroup(section.group)}>
                  <span className={classes.navGroupCaret}><Icons.Caret /></span>
                  <span className={classes.navGroupLabel}>{section.group}</span>

                  {section.isWorkflows && (
                    <>
                      <span className={classes.navGroupCount}>{TOTAL_WFS}</span>
                      <button
                        className={`${classes.navGroupIconBtn}${menuOpen === 'group' ? ' ' + classes.isOpen : ''}`}
                        onClick={e => stopAndOpen(e, 'group')}
                        title="More"
                      >
                        <Icons.More />
                      </button>
                      <button className={classes.navGroupIconBtn} title="New workflow">
                        <Icons.Plus />
                      </button>
                      <DropdownMenu id="group">
                        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Plus /> New workflow</button>
                        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Folder /> Create folder</button>
                        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Doc /> Import workflow</button>
                        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Download /> Export all</button>
                        <div className={classes.dropdownSep} />
                        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Sort /> Sort A → Z</button>
                        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Activity /> Sort by status</button>
                        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Clock /> Sort by recent</button>
                        <div className={classes.dropdownSep} />
                        <button className={classes.dropdownItem} onClick={e => { e.stopPropagation(); closeMenus() }}><Icons.Settings /> Workflow settings</button>
                      </DropdownMenu>
                    </>
                  )}
                </div>

                {open && !section.isWorkflows && section.items?.map(n => (
                  <NavLink
                    key={n.id}
                    to={n.to}
                    className={({ isActive }) =>
                      `${classes.navItem}${isActive && n.to !== '#' ? ' ' + classes.active : ''}`
                    }
                    title={n.label}
                  >
                    <n.icon />
                    <span className={classes.navLabelText}>{n.label}</span>
                    {n.count && <span className={classes.navCount}>{n.count}</span>}
                  </NavLink>
                ))}

                {open && section.isWorkflows && (
                  <div className={classes.wfTree}>
                    {WORKFLOWS_TREE.map(node =>
                      node.type === 'folder'
                        ? renderFolder(node)
                        : renderWfRow(node)
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>

        <div className={classes.sidebarFootActions}>
          <button className={classes.footAction} type="button"><Icons.Help /> Help &amp; docs</button>
          <button className={classes.footAction} type="button"><Icons.Feedback /> Feedback</button>
        </div>
      </aside>

      {/* ── Main column ── */}
      <div className={classes.main}>
        <div className={classes.mainCard}>
          <header className={classes.topbar}>
            <div className={classes.crumbs}>
              <span>{user?.full_name ? `${user.full_name.split(' ')[0]}'s workspace` : 'My workspace'}</span>
              <span className={classes.sep}>/</span>
              <span className={classes.cur}>{pageLabel}</span>
            </div>

            <div className={classes.topbarActions}>
              <button className={classes.iconBtn} title="Activity"><Icons.Activity /></button>
              <button className={classes.iconBtn} title="Help"><Icons.Help /></button>
              <ThemeToggle />

              <div className={classes.profileWrap}>
                <button
                  className={`${classes.avatar}${profileOpen ? ' ' + classes.isOpen : ''}`}
                  onClick={() => setProfileOpen(v => !v)}
                  aria-label="Account"
                  style={{
                    backgroundImage: user?.avatar_url ? `url(${user.avatar_url})` : undefined,
                  }}
                >
                  {!user?.avatar_url && (user?.full_name || user?.email || '?').slice(0, 1).toUpperCase()}
                </button>

                {profileOpen && (
                  <>
                    <div className={classes.dropdownBackdrop} onClick={() => setProfileOpen(false)} />
                    <div className={classes.profileDropdown}>
                      <div className={classes.profileHead}>
                        <span className={classes.profileAvatar}>
                          {(user?.full_name || user?.email || '?').slice(0, 1).toUpperCase()}
                        </span>
                        <span className={classes.profileMeta}>
                          <span className={classes.profileName}>{user?.full_name || 'Anonymous'}</span>
                          <span className={classes.profileEmail}>{user?.email}</span>
                        </span>
                      </div>
                      <div className={classes.profileWorkspace}>
                        <span className={`${classes.workspaceAvatar} ${classes.workspaceAvatarSm}`}>
                          {(user?.full_name || 'U').slice(0, 1).toUpperCase()}
                        </span>
                        <span className={classes.workspaceMeta}>
                          <span className={classes.workspaceName}>
                            {user?.full_name ? `${user.full_name.split(' ')[0]}'s workspace` : 'My workspace'}
                          </span>
                        </span>
                        <Icons.Chevrons />
                      </div>
                      <div className={classes.dropdownSep} />
                      <button className={classes.dropdownItem} onClick={() => setProfileOpen(false)}>
                        <Icons.Settings /> Account settings <span className="kbd">⌘,</span>
                      </button>
                      <button className={classes.dropdownItem} onClick={() => setProfileOpen(false)}>
                        <Icons.Users /> Workspace members
                      </button>
                      <NavLink
                        to={APP_ROUTES.WORKSPACE_SETTINGS}
                        className={classes.dropdownItem}
                        onClick={() => setProfileOpen(false)}
                      >
                        <Icons.Settings /> Workspace settings
                      </NavLink>
                      <button className={classes.dropdownItem} onClick={() => setProfileOpen(false)}>
                        <Icons.Plug /> Connected apps
                      </button>
                      <button className={classes.dropdownItem} onClick={() => setProfileOpen(false)}>
                        <Icons.Activity /> Run usage <span className={classes.itemSub}>2,012 / 5,000</span>
                      </button>
                      <div className={classes.dropdownSep} />
                      <button className={classes.dropdownItem} onClick={() => setProfileOpen(false)}>
                        <Icons.Moon /> Appearance <span className={classes.itemSub}>Dark</span>
                      </button>
                      <button className={classes.dropdownItem} onClick={() => setProfileOpen(false)}>
                        <Icons.Cmd /> Keyboard shortcuts <span className="kbd">?</span>
                      </button>
                      <button className={classes.dropdownItem} onClick={() => setProfileOpen(false)}>
                        <Icons.Doc /> Documentation
                      </button>
                      <button className={classes.dropdownItem} onClick={() => setProfileOpen(false)}>
                        <Icons.Feedback /> Send feedback
                      </button>
                      <div className={classes.dropdownSep} />
                      <button className={`${classes.dropdownItem} ${classes.danger}`} onClick={() => { setProfileOpen(false); logout() }}>
                        <Icons.SignOut /> Sign out
                      </button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </header>

          <div className={classes.mainContent}>
            <Outlet />
          </div>
        </div>
      </div>
    </div>
  )
}
