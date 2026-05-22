const fs = require('fs');
const path = require('path');

const classes = {
  shell: 'relative h-screen grid grid-cols-[244px_1fr] gap-[14px] z-10 data-[collapsed=true]:grid-cols-[64px_1fr]',
  
  sidebar: 'relative my-[14px] ml-[14px] bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[16px] flex flex-col overflow-visible shadow-[inset_0_1px_0_oklch(0.30_0.004_250/0.4),0_24px_48px_-28px_oklch(0_0_0/0.6)] z-20',
  sidebarTop: 'shrink-0 pt-[14px] px-[10px] pb-[12px] flex flex-col gap-[12px] border-b border-[var(--border-faint)] group-data-[collapsed=true]/shell:pt-[14px] group-data-[collapsed=true]/shell:px-[8px] group-data-[collapsed=true]/shell:pb-[12px] group-data-[collapsed=true]/shell:gap-[10px]',
  sidebarScroll: 'flex-1 min-h-0 overflow-y-auto pt-[8px] px-[10px] pb-[10px] flex flex-col gap-0 [&::-webkit-scrollbar]:w-[5px] [&::-webkit-scrollbar-thumb]:bg-[var(--border)] [&::-webkit-scrollbar-thumb]:rounded-full [&::-webkit-scrollbar-track]:bg-transparent group-data-[collapsed=true]/shell:px-[8px]',
  sidebarFootActions: 'shrink-0 p-[8px] border-t border-[var(--border-faint)] flex gap-[4px] group-data-[collapsed=true]/shell:hidden',
  footAction: 'flex-1 inline-flex items-center justify-center gap-[6px] py-[7px] px-[8px] rounded-[7px] text-[12px] text-[var(--text-mute)] font-medium transition-colors duration-100 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]',

  brandRow: 'flex items-center justify-between py-[2px] px-[6px] pb-[4px] group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:flex-col group-data-[collapsed=true]/shell:gap-[10px] group-data-[collapsed=true]/shell:px-[4px]',
  brand: 'inline-flex items-center gap-[9px] text-[15px] font-semibold tracking-tight text-[var(--text)] group-data-[collapsed=true]/shell:gap-0',
  brandMark: 'w-[22px] h-[22px] inline-flex items-center justify-center rounded-[6px] bg-[var(--text)] text-[var(--bg)]',
  brandText: 'inline group-data-[collapsed=true]/shell:hidden',
  brandBadge: 'font-mono text-[9.5px] tracking-[0.14em] uppercase text-[var(--text-faint)] border border-[var(--border-soft)] py-[2px] px-[6px] pb-[1px] rounded-[4px] ml-[6px] group-data-[collapsed=true]/shell:hidden',
  brandTrailBtn: 'w-[24px] h-[24px] rounded-[6px] text-[var(--text-faint)] inline-flex items-center justify-center hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[13px] [&_svg]:h-[13px]',

  cmdSearch: 'flex items-center gap-[8px] px-[10px] h-[34px] rounded-[9px] bg-[var(--bg)] border border-[var(--border-faint)] transition-colors duration-120 w-full min-w-0 hover:border-[var(--border-soft)] focus-within:border-[var(--border)] focus-within:bg-[var(--surface)] [&>svg]:w-[14px] [&>svg]:h-[14px] [&>svg]:text-[var(--text-faint)] [&>svg]:shrink-0 group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:px-0 group-data-[collapsed=true]/shell:gap-0',

  navSection: 'flex flex-col gap-[1px] pb-[4px] group-data-[collapsed=true]/shell:pb-[6px] group-data-[collapsed=true]/shell:border-t group-data-[collapsed=true]/shell:border-[var(--border-faint)] group-data-[collapsed=true]/shell:pt-[6px] first:border-none first:pt-0',
  isClosed: 'pb-0',
  navGroupHead: 'flex items-center gap-[6px] pt-[8px] px-[10px] pb-[4px] font-mono text-[10px] tracking-widest uppercase text-[var(--text-dim)] font-medium cursor-pointer w-full text-left transition-colors duration-100 hover:text-[var(--text-mute)] group-data-[collapsed=true]/shell:hidden relative',
  navGroupCaret: 'inline-flex w-[12px] h-[12px] transition-transform duration-160 [&_svg]:w-[11px] [&_svg]:h-[11px]',
  navGroupLabel: 'flex-1',
  navGroupCount: 'font-mono text-[9.5px] text-[var(--text-faint)] ml-[4px] font-medium',
  navGroupIconBtn: 'w-[20px] h-[20px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center transition-colors duration-100 shrink-0 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[12px] [&_svg]:h-[12px]',
  isOpen: 'bg-[var(--surface-2)] text-[var(--text)]',
  isWorkflows: 'relative',

  navItem: 'flex items-center gap-[10px] py-[7px] px-[10px] rounded-[8px] text-[13px] text-[var(--text-mute)] cursor-pointer transition-colors duration-100 w-full font-medium no-underline relative hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[15px] [&_svg]:h-[15px] [&_svg]:text-current [&_svg]:opacity-85 group-data-[collapsed=true]/shell:justify-center group-data-[collapsed=true]/shell:p-[9px] group-data-[collapsed=true]/shell:gap-0',
  active: 'bg-[var(--surface)] text-[var(--text)] group-data-[collapsed=true]/shell:shadow-[inset_0_0_0_1px_var(--border-soft)]',
  navLabelText: 'flex-1 group-data-[collapsed=true]/shell:hidden',
  navCount: 'ml-auto font-mono text-[10.5px] text-[var(--text-faint)] font-medium group-data-[collapsed=true]/shell:hidden',

  wfTree: 'flex flex-col gap-[1px] group-data-[collapsed=true]/shell:hidden',
  wfRowWrap: 'relative group-data-[collapsed=true]/shell:hidden',
  wfRow: 'flex items-center gap-[9px] pt-[6px] pr-[6px] pb-[6px] pl-[12px] rounded-[8px] text-[12.5px] text-[var(--text-mute)] cursor-pointer transition-colors duration-100 w-full text-left font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] group/wf',
  wfName: 'flex-1 min-w-0 whitespace-nowrap overflow-hidden text-ellipsis tracking-tight',
  rowMore: 'w-[22px] h-[22px] rounded-[5px] text-[var(--text-faint)] inline-flex items-center justify-center opacity-0 transition-all duration-100 shrink-0 hover:bg-[var(--surface-2)] hover:text-[var(--text)] group-hover/wf:opacity-100 group-hover/folder:opacity-100 [&_svg]:w-[13px] [&_svg]:h-[13px]',

  folder: 'relative group-data-[collapsed=true]/shell:hidden group/folder',
  folderHead: 'flex items-center gap-[8px] p-[6px] rounded-[8px] text-[12.5px] text-[var(--text-mute)] cursor-pointer transition-colors duration-100 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)]',
  folderCaret: 'w-[12px] h-[12px] inline-flex items-center justify-center transition-transform duration-140 text-[var(--text-faint)] shrink-0 [&_svg]:w-[10px] [&_svg]:h-[10px]',
  folderIcon: 'inline-flex text-[var(--text-mute)] shrink-0 [&_svg]:w-[14px] [&_svg]:h-[14px]',
  folderName: 'flex-1 min-w-0 whitespace-nowrap overflow-hidden text-ellipsis tracking-tight',
  folderCount: 'font-mono text-[10px] text-[var(--text-faint)] font-medium px-[2px]',
  folderBody: 'pl-[14px] flex flex-col relative before:content-[\'\'] before:absolute before:left-[11px] before:top-[4px] before:bottom-[4px] before:w-[1px] before:bg-[var(--border-faint)]',

  dropdownBackdrop: 'fixed inset-0 z-40',
  rowMenu: 'w-[240px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[11px] p-[5px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] animate-in fade-in zoom-in-95 duration-100',
  dropdownItem: 'flex items-center gap-[9px] py-[8px] px-[10px] rounded-[7px] text-[13px] text-[var(--text-mute)] w-full text-left transition-colors duration-80 font-medium hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[14px] [&_svg]:h-[14px] [&_svg]:shrink-0',
  danger: 'text-[var(--err)] hover:bg-[oklch(0.70_0.18_22/0.10)]',
  itemSub: 'ml-auto font-mono text-[10.5px] text-[var(--text-faint)]',
  dropdownSep: 'h-[1px] bg-[var(--border-faint)] my-[4px]',

  main: 'relative overflow-hidden h-screen pt-[14px] pr-[14px] pb-[14px] pl-0 flex flex-col',
  mainCard: 'bg-[var(--bg-2)] border border-[var(--border-faint)] rounded-[16px] h-full overflow-hidden shadow-[inset_0_1px_0_oklch(0.30_0.004_250/0.4),0_24px_48px_-28px_oklch(0_0_0/0.6)] flex flex-col flex-1 min-h-0',
  mainContent: 'flex-1 min-h-0 overflow-y-auto [&::-webkit-scrollbar]:w-[6px] [&::-webkit-scrollbar-thumb]:bg-[var(--border)] [&::-webkit-scrollbar-thumb]:rounded-full',

  topbar: 'flex items-center justify-between py-[14px] px-[22px] border-b border-[var(--border-faint)] shrink-0',
  crumbs: 'flex items-center gap-[8px] text-[13px] text-[var(--text-mute)]',
  sep: 'text-[var(--text-dim)]',
  cur: 'text-[var(--text)] font-medium',
  topbarActions: 'flex items-center gap-[6px]',
  iconBtn: 'w-[32px] h-[32px] inline-flex items-center justify-center rounded-[8px] text-[var(--text-mute)] relative transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)] [&_svg]:w-[16px] [&_svg]:h-[16px]',
  indicator: 'absolute top-[7px] right-[8px] w-[6px] h-[6px] rounded-full bg-[var(--accent)] border-2 border-[var(--bg-2)]',

  profileWrap: 'relative',
  avatar: 'w-[28px] h-[28px] rounded-[8px] bg-[var(--surface-3)] border border-[var(--border-soft)] cursor-pointer inline-flex items-center justify-center text-[11px] font-semibold text-[var(--text)] tracking-tight bg-cover bg-center transition-colors duration-120 hover:border-[var(--border)]',
  profileDropdown: 'absolute top-[calc(100%+8px)] right-0 w-[260px] bg-[var(--bg-2)] border border-[var(--border)] rounded-[13px] p-[6px] shadow-[0_24px_56px_-20px_oklch(0_0_0/0.7)] z-50 animate-in fade-in slide-in-from-top-2',
  profileHead: 'flex items-center gap-[10px] pt-[8px] px-[8px] pb-[10px]',
  profileAvatar: 'w-[32px] h-[32px] rounded-[9px] bg-[var(--surface-3)] border border-[var(--border-soft)] inline-flex items-center justify-center text-[13px] font-semibold text-[var(--text)] shrink-0',
  profileMeta: 'flex flex-col gap-[1px] min-w-0',
  profileName: 'text-[13px] font-medium',
  profileEmail: 'text-[11px] text-[var(--text-faint)] font-mono',
  profileWorkspace: 'flex items-center gap-[9px] py-[8px] px-[10px] rounded-[8px] bg-[var(--surface)] my-0 mx-[2px] mb-[4px] cursor-pointer [&>svg]:w-[13px] [&>svg]:h-[13px] [&>svg]:text-[var(--text-faint)] [&>svg]:ml-auto',
  workspaceAvatar: 'w-[26px] h-[26px] rounded-[7px] bg-[var(--text)] text-[var(--bg)] inline-flex items-center justify-center text-[11px] font-semibold tracking-tight shrink-0',
  workspaceAvatarSm: 'w-[22px] h-[22px] text-[10px]',
  workspaceMeta: 'flex flex-col gap-[1px] min-w-0 flex-1',
  workspaceName: 'text-[13px] font-medium text-[var(--text)] whitespace-nowrap overflow-hidden text-ellipsis tracking-tight'
};

const filePath = '/Users/bibektimilsina/projects/fuse_new/apps/web_v2/src/shared/components/AppLayout.tsx';
let content = fs.readFileSync(filePath, 'utf-8');

// Remove import styles
content = content.replace(/import styles from '\.\/AppLayout\.module\.css'\n?/g, '');
content = content.replace(/import { cn } from '@\/lib\/cn'\n?/g, ''); // We might add it back if needed
content = content.replace(/import { APP_ROUTES } from '@\/shared\/constants\/routes'/, `import { APP_ROUTES } from '@/shared/constants/routes'\nimport { cn } from '@/lib/cn'`);

content = content.replace(/className=\{`\$\{styles\.shell\}\$\{collapsed \? ' ' \+ styles\.isCollapsed : ''\}`\}/, 'className={cn("group/shell", classes.shell)} data-collapsed={collapsed}');

// We will inject classes object directly into AppLayout.tsx or inline everything.
// Since there's a lot of template literals, injecting classes object at the top of AppLayout.tsx is much cleaner.
const injectCode = `\nconst classes = ${JSON.stringify(classes, null, 2)};\n`;

content = content.replace(/const WORKFLOWS_TREE/, injectCode + '\nconst WORKFLOWS_TREE');

// Replace styles.xxx with classes.xxx
content = content.replace(/styles\.([a-zA-Z0-9_]+)/g, 'classes.$1');

// Replace styles['some']
content = content.replace(/styles\[/g, 'classes[');

// Fix shell classes to use the data attribute logic
content = content.replace(/className=\{classes\.shell\}/, 'className={cn("group/shell", classes.shell)} data-collapsed={collapsed}');

// Fix input cmd search issue (hidden when collapsed)
content = content.replace(/<input placeholder="Search" \/>/, '<input placeholder="Search" className="bg-transparent border-none outline-none flex-1 min-w-0 text-[13px] text-[var(--text)] tracking-tight p-0 placeholder:text-[var(--text-faint)] group-data-[collapsed=true]/shell:hidden" />');
content = content.replace(/<span className="kbd">/, '<span className="kbd group-data-[collapsed=true]/shell:hidden">');

// Active navItem pseudo-element: we can just add a pseudo-element class: 'before:content-[""] before:w-[3px] before:h-[14px] before:bg-[var(--text)] before:rounded-[0_2px_2px_0] before:absolute before:left-0 group-data-[collapsed=true]/shell:before:hidden'
// I've put group-data-[collapsed=true]/shell:shadow-[inset_0_0_0_1px_var(--border-soft)] for active.
// Let's add the before logic to 'active' class
classes.active = 'bg-[var(--surface)] text-[var(--text)] group-data-[collapsed=true]/shell:shadow-[inset_0_0_0_1px_var(--border-soft)] before:content-[\'\'] before:w-[3px] before:h-[14px] before:bg-[var(--text)] before:rounded-[0_2px_2px_0] before:absolute before:left-0 group-data-[collapsed=true]/shell:before:hidden';

// Re-inject the updated classes object
content = content.replace(/const classes = \{[\s\S]*?\};\n/, `const classes = ${JSON.stringify(classes, null, 2)};\n`);

fs.writeFileSync(filePath, content);
console.log('AppLayout migrated');