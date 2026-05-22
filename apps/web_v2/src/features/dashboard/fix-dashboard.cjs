const fs = require('fs');
const path = require('path');

const classes = {
  // dashboard page layout
  body: 'p-[24px_28px_28px] flex flex-col gap-[24px] max-w-[1240px] w-full mx-auto flex-1',
  split: 'grid grid-cols-[minmax(0,1fr)_320px] gap-[24px]',
  sideStack: 'flex flex-col gap-[16px]',
  
  // greeting
  greetingRow: 'flex items-end justify-between gap-[24px]',
  greeting: 'flex flex-col', // removed extra h1 styling
  eyebrow: 'inline-flex items-center gap-[8px] font-mono text-[10.5px] tracking-widest uppercase text-[var(--text-faint)] font-medium',
  eyebrowDot: 'w-[6px] h-[6px] rounded-full bg-[var(--ok)] shadow-[0_0_6px_oklch(0.78_0.14_145/0.6)]',
  btnGroup: 'flex items-center gap-[8px]',
  btn: 'inline-flex items-center gap-[7px] py-[8px] px-[14px] rounded-[9px] text-[13px] font-medium transition-colors duration-120',
  btnSecondary: 'bg-[var(--surface)] border border-[var(--border-faint)] text-[var(--text)] hover:bg-[var(--surface-2)]',
  btnPrimary: 'bg-[var(--text)] text-[var(--bg)] border border-[var(--text)] hover:bg-[oklch(0.90_0.003_250)]',
  
  // stats
  stats: 'grid grid-cols-4 bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden',
  stat: 'pt-[16px] px-[18px] pb-[18px] border-r border-[var(--border-faint)] flex flex-col gap-[6px] relative last:border-r-0',
  statLabel: 'text-[12px] text-[var(--text-mute)] flex items-center gap-[7px]',
  statValue: 'text-[26px] font-medium tracking-tight text-[var(--text)] mt-[2px]', // font-feature-settings not exactly tailwind without custom arbitrary variant, can skip or use class
  unit: 'text-[14px] text-[var(--text-faint)] ml-[3px]',
  statDelta: 'font-mono text-[11px] inline-flex items-center gap-[4px]',
  up: 'text-[var(--ok)]',
  down: 'text-[var(--err)]',
  flat: 'text-[var(--text-faint)]',
  statSpark: 'absolute right-[14px] top-[14px] w-[70px] h-[28px] opacity-[0.85]',
  
  // prompt
  promptCard: 'bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] pt-[16px] px-[18px] pb-[12px] transition-colors duration-200 focus-within:border-[var(--accent-line)]',
  promptFoot: 'flex items-center justify-between mt-[6px] gap-[8px]',
  promptTools: 'flex items-center gap-[4px]',
  toolBtn: 'w-[28px] h-[28px] inline-flex items-center justify-center rounded-[7px] text-[var(--text-mute)] transition-colors duration-120 hover:bg-[var(--surface)] hover:text-[var(--text)]',
  modeToggle: 'inline-flex bg-[var(--surface)] rounded-[7px] p-[2px] ml-[4px]',
  modeActive: 'bg-[var(--surface-2)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)]',
  modelPill: 'inline-flex items-center gap-[6px] py-[5px] pr-[9px] pl-[8px] rounded-[7px] bg-[var(--surface)] text-[12px] text-[var(--text)] border border-[var(--border-faint)] font-medium',
  spark: 'text-[var(--accent)] inline-flex',
  sendBtn: 'w-[28px] h-[28px] rounded-[7px] bg-[var(--text)] text-[var(--bg)] inline-flex items-center justify-center hover:bg-[var(--accent)] hover:text-[oklch(0.18_0.02_250)]',
  
  // panel
  panel: 'bg-[var(--bg)] border border-[var(--border-faint)] rounded-[12px] overflow-hidden flex flex-col',
  panelHead: 'flex items-center justify-between py-[12px] px-[16px] border-b border-[var(--border-faint)]',
  panelTitle: 'flex items-center gap-[8px] text-[13px] font-medium',
  panelCount: 'font-mono text-[11px] text-[var(--text-faint)] bg-[var(--surface)] py-[2px] px-[6px] pb-[1px] rounded-[4px] border border-[var(--border-faint)]',
  panelActions: 'flex items-center gap-[4px]',
  linkBtn: 'text-[12px] text-[var(--text-mute)] py-[4px] px-[8px] rounded-[6px] transition-colors duration-120 inline-flex items-center gap-[4px] hover:text-[var(--text)] hover:bg-[var(--surface)]',
  
  // runs
  runs: 'flex flex-col',
  runRow: 'grid grid-cols-[22px_1fr_180px_80px_80px_22px] gap-[12px] items-center py-[10px] px-[16px] border-b border-[var(--border-faint)] text-[13px] cursor-pointer transition-colors duration-100 last:border-b-0 hover:bg-[var(--surface)]',
  runName: 'font-medium whitespace-nowrap overflow-hidden text-ellipsis',
  runTrigger: 'inline-flex items-center gap-[6px] font-mono text-[11px] text-[var(--text-mute)]',
  runMeta: 'font-mono text-[11px] text-[var(--text-faint)]',
  caret: 'text-[var(--text-dim)] inline-flex',
  
  // schedule
  scheduleRow: 'flex items-center gap-[12px] py-[10px] px-[16px] border-b border-[var(--border-faint)] cursor-pointer transition-colors duration-100 last:border-b-0 hover:bg-[var(--surface)]',
  scheduleTime: 'font-mono text-[11px] text-[var(--text)] w-[56px] shrink-0',
  ampm: 'text-[var(--text-faint)] text-[10px] ml-[2px]',
  scheduleMeta: 'flex flex-col gap-[2px] min-w-0 flex-1',
  scheduleName: 'text-[12.5px] font-medium whitespace-nowrap overflow-hidden text-ellipsis',
  scheduleSub: 'text-[11px] text-[var(--text-faint)] font-mono',
  
  // conn
  connRow: 'flex items-center gap-[12px] py-[10px] px-[16px] border-b border-[var(--border-faint)] last:border-b-0',
  connIcon: 'w-[28px] h-[28px] rounded-[7px] inline-flex items-center justify-center text-[11px] font-semibold shrink-0 text-[var(--text)] tracking-tight',
  stripe: 'bg-[linear-gradient(135deg,oklch(0.50_0.10_280),oklch(0.36_0.08_270))]',
  slack: 'bg-[linear-gradient(135deg,oklch(0.55_0.12_35),oklch(0.40_0.08_25))]',
  linear: 'bg-[linear-gradient(135deg,oklch(0.50_0.10_250),oklch(0.36_0.08_240))]',
  notion: 'bg-[linear-gradient(135deg,oklch(0.45_0.02_60),oklch(0.32_0.01_50))]',
  hub: 'bg-[linear-gradient(135deg,oklch(0.50_0.10_35),oklch(0.36_0.08_25))]',
  connMeta: 'flex flex-col gap-[2px] min-w-0 flex-1',
  connName: 'text-[12.5px] font-medium whitespace-nowrap overflow-hidden text-ellipsis',
  connSub: 'text-[11px] text-[var(--text-faint)] font-mono',
  connState: 'font-mono text-[10px] tracking-widest uppercase py-[3px] px-[7px] pb-[2px] rounded-[4px] font-medium',
  ok: 'bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]',
  warn: 'bg-[oklch(0.82_0.14_80/0.16)] text-[var(--warn)]',
  err: 'bg-[oklch(0.70_0.18_22/0.16)] text-[var(--err)]'
};

const BASE_DIR = '/Users/bibektimilsina/projects/fuse_new/apps/web_v2/src/features/dashboard';

const files = [
  'components/ConnectionsPanel.tsx',
  'components/SchedulePanel.tsx',
  'components/RecentRuns.tsx',
  'components/PanelHead.tsx',
  'components/PromptCard.tsx',
  'components/StatsGrid.tsx',
  'components/GreetingRow.tsx',
  'pages/Dashboard.tsx'
];

for (const file of files) {
  const filePath = path.join(BASE_DIR, file);
  let content = fs.readFileSync(filePath, 'utf-8');
  
  // Remove CSS import
  content = content.replace(/import styles from '..\/dashboard\.module\.css'\n?/g, '');
  
  // Replace styles.xxx inside template literals like `${styles.xxx}`
  content = content.replace(/\$\{styles\.([a-zA-Z0-9_]+)\}/g, (match, p1) => {
    return classes[p1] ? classes[p1] : match;
  });

  // Replace styles[c.state] and styles[c.id as keyof typeof styles]
  content = content.replace(/\$\{styles\[([a-zA-Z0-9_\. ]+)\]\}/g, (match, expr) => {
    // This is tricky, we'll manually replace it by creating cn mapping or doing it dynamically in react.
    // Given the specific files, we can just replace styles[x] with something else or use inline logic.
    return match; // We'll fix these separately
  });
  
  // Replace className={styles.xxx}
  content = content.replace(/className=\{styles\.([a-zA-Z0-9_]+)\}/g, (match, p1) => {
    return classes[p1] ? `className="${classes[p1]}"` : match;
  });

  // Special cases for Dashboard:
  // .greeting h1
  if (file === 'components/GreetingRow.tsx') {
    content = content.replace('<h1>', '<h1 className="text-[26px] mt-[6px] font-medium tracking-tight">');
  }
  
  // promptCard textarea
  if (file === 'components/PromptCard.tsx') {
    content = content.replace('<textarea', '<textarea className="w-full bg-transparent border-none outline-none resize-none text-[14.5px] text-[var(--text)] min-h-[60px] leading-[1.5] placeholder:text-[var(--text-faint)]"');
    content = content.replace(/className=\{mode === 'flow' \? styles\.modeActive : ''\}/g, 'className={mode === \'flow\' ? "bg-[var(--surface-2)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)] flex items-center gap-[6px] py-[5px] px-[10px] text-[12px] rounded-[5px] font-medium" : "flex items-center gap-[6px] py-[5px] px-[10px] text-[12px] text-[var(--text-mute)] rounded-[5px] font-medium"}');
    content = content.replace(/className=\{mode === 'agent' \? styles\.modeActive : ''\}/g, 'className={mode === \'agent\' ? "bg-[var(--surface-2)] text-[var(--text)] shadow-[inset_0_0_0_1px_var(--border-faint)] flex items-center gap-[6px] py-[5px] px-[10px] text-[12px] rounded-[5px] font-medium" : "flex items-center gap-[6px] py-[5px] px-[10px] text-[12px] text-[var(--text-mute)] rounded-[5px] font-medium"}');
    
  }

  // ConnectionsPanel
  if (file === 'components/ConnectionsPanel.tsx') {
    content = content.replace('import { Icons } from \'@/shared/components\'', 'import { Icons } from \'@/shared/components\'\nimport { cn } from \'@/lib/cn\'');
    content = content.replace(/className=\{\`\$\{styles\.connIcon\} \$\{styles\[c\.id as keyof typeof styles\]\}\`\}/g, 'className={cn("w-[28px] h-[28px] rounded-[7px] inline-flex items-center justify-center text-[11px] font-semibold shrink-0 text-[var(--text)] tracking-tight", c.id === "stripe" && "bg-[linear-gradient(135deg,oklch(0.50_0.10_280),oklch(0.36_0.08_270))]", c.id === "slack" && "bg-[linear-gradient(135deg,oklch(0.55_0.12_35),oklch(0.40_0.08_25))]", c.id === "linear" && "bg-[linear-gradient(135deg,oklch(0.50_0.10_250),oklch(0.36_0.08_240))]", c.id === "notion" && "bg-[linear-gradient(135deg,oklch(0.45_0.02_60),oklch(0.32_0.01_50))]", c.id === "hub" && "bg-[linear-gradient(135deg,oklch(0.50_0.10_35),oklch(0.36_0.08_25))]")}');
    content = content.replace(/className=\{\`\$\{styles\.connState\} \$\{styles\[c\.state\]\}\`\}/g, 'className={cn("font-mono text-[10px] tracking-widest uppercase py-[3px] px-[7px] pb-[2px] rounded-[4px] font-medium", c.state === "ok" && "bg-[oklch(0.78_0.14_145/0.14)] text-[var(--ok)]", c.state === "warn" && "bg-[oklch(0.82_0.14_80/0.16)] text-[var(--warn)]", c.state === "err" && "bg-[oklch(0.70_0.18_22/0.16)] text-[var(--err)]")}');
  }

  // StatsGrid
  if (file === 'components/StatsGrid.tsx') {
    content = content.replace('import { Sparkline } from \'./Sparkline\'', 'import { Sparkline } from \'./Sparkline\'\nimport { cn } from \'@/lib/cn\'');
    content = content.replace(/className=\{\`\$\{styles\.statDelta\} \$\{styles\[s\.deltaDir\]\}\`\}/g, 'className={cn("font-mono text-[11px] inline-flex items-center gap-[4px]", s.deltaDir === "up" && "text-[var(--ok)]", s.deltaDir === "down" && "text-[var(--err)]", s.deltaDir === "flat" && "text-[var(--text-faint)]")}');
  }

  fs.writeFileSync(filePath, content);
}
console.log("Done updating dashboard components");
