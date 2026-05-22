// fuse v2 — workflow editor shell
const { useState: useS_c, useRef: useR_c, useEffect: useE_c, useMemo: useM_c } = React;

const NODE_W = 248;
const HEADER_H = 38;
const PROP_H = 26;
const SIDE_MIN = 360;
const SIDE_MAX = 640;
const SIDE_DEFAULT = 400;

const INITIAL_NODES = [
  {
    id: "n1", type: "trigger", x: 60, y: 220,
    mark: <Icon.Bolt />, accent: "green",
    title: "Start",
    description: "Manually start this workflow from the editor or API.",
    props: [
      { k: "Trigger type", v: "Manual", kind: "select", options: ["Manual", "On schedule", "Webhook", "Email"] },
      { k: "Allow API",    v: "yes",    kind: "toggle" },
    ],
  },
  {
    id: "n2", type: "agent", x: 400, y: 130,
    mark: <Icon.Spark />, accent: "blue",
    title: "Agent",
    description: "Classifies the refund request and decides whether to approve.",
    error: true,
    errorMsg: "Provider credential is invalid or has expired.",
    props: [
      { k: "Provider",      v: "OpenAI",                kind: "select",     options: ["OpenAI", "Anthropic", "Filament", "Google"] },
      { k: "Credential",    v: "3aebc8c0…",             kind: "credential" },
      { k: "Model",         v: "filament-2 sonnet",     kind: "select",     options: ["filament-2 opus", "filament-2 sonnet", "filament-2 haiku"] },
      { k: "System prompt", v: "You are a refund analyst. Decide whether each request is high or low priority.", kind: "textarea" },
      { k: "Messages",      v: "1 user message",        kind: "code" },
      { k: "Tools",         v: "4 tools attached",      kind: "code" },
      { k: "Knowledge",     v: "refund_policy",         kind: "select",     options: ["—", "refund_policy", "support_kb"] },
      { k: "Temperature",   v: "0.2",                   kind: "number" },
    ],
  },
  {
    id: "n3", type: "action", x: 760, y: 230,
    mark: <Icon.Branch />, accent: "amber",
    title: "Set Variable",
    description: "Stores the agent's decision in workflow scope.",
    props: [
      { k: "Variable name", v: "refund_decision",    kind: "text" },
      { k: "Value",         v: "{{agent.priority}}", kind: "expression" },
    ],
  },
  {
    id: "n4", type: "action", x: 1100, y: 240,
    mark: <Icon.Slack />, accent: "pink",
    title: "Slack message",
    description: "Posts an approval request to the on-call channel.",
    props: [
      { k: "Channel", v: "#oncall-revenue", kind: "select", options: ["#oncall-revenue", "#general", "#refunds"] },
      { k: "Message", v: "Markdown body",   kind: "textarea" },
      { k: "Buttons", v: "approve, decline", kind: "text" },
    ],
  },
];

const EDGES = [
  { from: "n1", to: "n2" },
  { from: "n2", to: "n3" },
  { from: "n3", to: "n4" },
];

function nodeHeight(n) {
  return HEADER_H + (n.props?.length || 0) * PROP_H + (n.error ? 4 : 0) + 4;
}

// ============ EDITOR SHELL ============
function Editor({ project, onBack }) {
  const [navOpen, setNavOpen]       = useS_c(false);
  const [side, setSide]             = useS_c("inspector");
  const [selected, setSelected]     = useS_c("n2");
  const [running, setRunning]       = useS_c(false);
  const [zoom, setZoom]             = useS_c(100);
  const [tool, setTool]             = useS_c("select");
  const [crumbMenu, setCrumbMenu]   = useS_c(false);
  const [stateMenu, setStateMenu]   = useS_c(false);
  const [actMenu, setActMenu]       = useS_c(false);
  const [nodes, setNodes]           = useS_c(INITIAL_NODES);
  const [active, setActive]         = useS_c(true);
  const [sideWidth, setSideWidth]   = useS_c(() => {
    try { return Math.min(SIDE_MAX, Math.max(SIDE_MIN, parseInt(localStorage.getItem("fuse_side_w") || SIDE_DEFAULT))); }
    catch { return SIDE_DEFAULT; }
  });
  const [dragging, setDragging]     = useS_c(false);

  const node = nodes.find(n => n.id === selected) || nodes[1];
  const errorCount = nodes.filter(n => n.error).length;

  const setProp  = (id, k, v) => setNodes(ns => ns.map(n => n.id === id ? { ...n, props: n.props.map(p => p.k === k ? { ...p, v } : p) } : n));
  const setField = (id, k, v) => setNodes(ns => ns.map(n => n.id === id ? { ...n, [k]: v } : n));

  // ===== resize side panel =====
  useE_c(() => {
    if (!dragging) return;
    const onMove = (e) => {
      const w = Math.min(SIDE_MAX, Math.max(SIDE_MIN, window.innerWidth - e.clientX));
      setSideWidth(w);
    };
    const onUp = () => {
      setDragging(false);
      try { localStorage.setItem("fuse_side_w", String(sideWidth)); } catch {}
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    document.body.style.cursor = "ew-resize";
    document.body.style.userSelect = "none";
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [dragging, sideWidth]);

  // ===== keyboard shortcuts =====
  useE_c(() => {
    const onKey = (e) => {
      const isMod = e.metaKey || e.ctrlKey;
      if (isMod && e.key === "Enter") { e.preventDefault(); runWorkflow(); }
      if (isMod && e.key.toLowerCase() === "k") { e.preventDefault(); setSide("copilot"); }
      if (isMod && e.key === "/") { e.preventDefault(); setSide("copilot"); }
      if (e.key === "Escape") { setCrumbMenu(false); setActMenu(false); setStateMenu(false); }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  const runWorkflow = () => {
    setRunning(true);
    setSide("logs");
    setTimeout(() => setRunning(false), 2400);
  };

  const edgePath = (a, b) => {
    const x1 = a.x + NODE_W;
    const y1 = a.y + HEADER_H / 2 + (a.props.length * PROP_H) / 2;
    const x2 = b.x;
    const y2 = b.y + HEADER_H / 2 + (b.props.length * PROP_H) / 2;
    const dx = Math.max(40, (x2 - x1) * 0.4);
    return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
  };

  const minX = Math.min(...nodes.map(n => n.x)) - 80;
  const maxX = Math.max(...nodes.map(n => n.x + NODE_W)) + 80;
  const minY = Math.min(...nodes.map(n => n.y)) - 80;
  const maxY = Math.max(...nodes.map(n => n.y + nodeHeight(n))) + 80;

  return (
    <div className={"editor" + (dragging ? " is-dragging" : "")} data-screen-label="02 Editor">
      <div className="grid-bg" />

      {/* ===== TOP BAR ===== */}
      <header className="editor-topbar">
        <div className="editor-tb-left">
          <button className={"hamb-btn" + (navOpen ? " is-open" : "")} onClick={() => setNavOpen(v => !v)} title="Workspace menu">
            <Icon.Menu />
          </button>

          <div className="editor-crumb">
            <button className="crumb-folder-btn" onClick={() => onBack && onBack()} title="Back to workspace">
              <Icon.CaretLeft />
            </button>
            <span className="crumb-folder">Revenue ops</span>
            <span className="crumb-sep">/</span>
            <button className={"crumb-title" + (crumbMenu ? " is-open" : "")} onClick={() => setCrumbMenu(v => !v)}>
              <span className="crumb-title-text">{project?.title || "Stripe refund — Slack approval"}</span>
              <Icon.Caret />
            </button>

            <button className={"state-pill " + (active ? "ok" : "warn") + (stateMenu ? " is-open" : "")}
              onClick={() => setStateMenu(v => !v)}>
              <span className={"status-dot " + (active ? "ok" : "warn")} />
              <span>{active ? "Active" : "Paused"}</span>
              <Icon.Caret />
            </button>
          </div>

          {crumbMenu && (
            <React.Fragment>
              <div className="dropdown-backdrop" onClick={() => setCrumbMenu(false)} />
              <div className="workflow-menu">
                <button className="dropdown-item" onClick={() => setCrumbMenu(false)}><Icon.Edit /> Rename workflow</button>
                <button className="dropdown-item" onClick={() => setCrumbMenu(false)}><Icon.Copy /> Duplicate</button>
                <button className="dropdown-item" onClick={() => setCrumbMenu(false)}><Icon.Folder /> Move to folder</button>
                <button className="dropdown-item" onClick={() => setCrumbMenu(false)}><Icon.Download /> Export as JSON</button>
                <div className="dropdown-sep" />
                <button className="dropdown-item" onClick={() => setCrumbMenu(false)}><Icon.Activity /> View runs</button>
                <button className="dropdown-item" onClick={() => setCrumbMenu(false)}><Icon.Clock /> Versions <span className="item-sub">v0.14</span></button>
                <div className="dropdown-sep" />
                <button className="dropdown-item danger" onClick={() => setCrumbMenu(false)}><Icon.Trash /> Delete workflow</button>
              </div>
            </React.Fragment>
          )}

          {stateMenu && (
            <React.Fragment>
              <div className="dropdown-backdrop" onClick={() => setStateMenu(false)} />
              <div className="state-menu">
                <button className="state-menu-item" onClick={() => { setActive(true); setStateMenu(false); }}>
                  <span className="status-dot ok" />
                  <div className="state-menu-meta">
                    <span className="state-menu-title">Active</span>
                    <span className="state-menu-sub">Triggers will fire</span>
                  </div>
                  {active && <Icon.Check />}
                </button>
                <button className="state-menu-item" onClick={() => { setActive(false); setStateMenu(false); }}>
                  <span className="status-dot warn" />
                  <div className="state-menu-meta">
                    <span className="state-menu-title">Paused</span>
                    <span className="state-menu-sub">Triggers ignored, can still test</span>
                  </div>
                  {!active && <Icon.Check />}
                </button>
              </div>
            </React.Fragment>
          )}
        </div>

        <div className="editor-tb-mid">
          <span className="editor-meta">
            <span className="editor-meta-item"><span className="status-dot ok" />Synced</span>
            <span className="editor-meta-sep">·</span>
            <span className="editor-meta-item"><Icon.Clock />Saved 2m ago</span>
            <span className="editor-meta-sep">·</span>
            <span className="editor-meta-item mono">v0.14</span>
          </span>
        </div>

        <div className="editor-tb-right">
          <button className="icon-btn" title="Undo (⌘Z)"><Icon.CaretLeft style={{ transform: "rotate(-90deg)" }} /></button>
          <button className="icon-btn" title="Redo (⌘⇧Z)"><Icon.CaretLeft style={{ transform: "rotate(90deg)" }} /></button>
          <span className="tb-sep" />
          <button className="icon-btn" title="Run history"><Icon.Activity /></button>
          <button className="icon-btn" title="Share"><Icon.Share /></button>
          <div className="profile-wrap">
            <button className="avatar" aria-label="Account" />
          </div>
        </div>
      </header>

      {/* ===== SIDEBAR DRAWER ===== */}
      {navOpen && <EditorSidebar onClose={() => setNavOpen(false)} onBack={onBack} />}

      {/* ===== CANVAS ===== */}
      <div className="editor-canvas" style={{ right: sideWidth }}>
        <div className="canvas-inner" style={{
          width: maxX - minX, height: maxY - minY,
          transform: `translate(${-minX + 40}px, ${-minY + 40}px) scale(${zoom / 100})`,
          transformOrigin: "0 0",
        }}>
          <svg className="edges" width={maxX - minX} height={maxY - minY}
            style={{ position: "absolute", left: 0, top: 0, pointerEvents: "none" }}>
            <defs>
              <marker id="arrow-h" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M0,0 L10,5 L0,10 z" fill="currentColor" />
              </marker>
            </defs>
            {EDGES.map((e, i) => {
              const a = nodes.find(n => n.id === e.from);
              const b = nodes.find(n => n.id === e.to);
              if (!a || !b) return null;
              return (
                <path key={i} className={"edge-path" + (running ? " active" : "")}
                  d={edgePath(a, b)} fill="none" strokeWidth="1.5" markerEnd="url(#arrow-h)" />
              );
            })}
          </svg>

          {nodes.map(n => (
            <NodeCard key={n.id} n={n}
              selected={selected === n.id}
              running={running}
              onSelect={() => { setSelected(n.id); setSide("inspector"); }}
            />
          ))}
        </div>

        <div className="canvas-fab">
          <button className={"canvas-fab-btn" + (tool === "select" ? " active" : "")} onClick={() => setTool("select")} title="Select (V)">
            <Icon.Cursor />
          </button>
          <button className={"canvas-fab-btn" + (tool === "pan" ? " active" : "")} onClick={() => setTool("pan")} title="Pan (H)">
            <Icon.Hand />
          </button>
          <div className="canvas-fab-sep" />
          <button className="canvas-fab-btn" onClick={() => setZoom(100)} title="Fit (F)">
            <Icon.Maximize />
          </button>
          <button className="canvas-fab-btn" onClick={() => setZoom(z => Math.max(40, z - 10))}><Icon.Minus /></button>
          <span className="canvas-fab-num mono">{zoom}%</span>
          <button className="canvas-fab-btn" onClick={() => setZoom(z => Math.min(200, z + 10))}><Icon.Plus /></button>
        </div>

        <div className="canvas-stat">
          {errorCount > 0
            ? <React.Fragment><span className="status-dot err" /> {errorCount} {errorCount === 1 ? "error" : "errors"} · {nodes.length} nodes</React.Fragment>
            : <React.Fragment><span className="status-dot ok" /> Workflow valid · {nodes.length} nodes · {EDGES.length} edges</React.Fragment>}
        </div>
      </div>

      {/* ===== RIGHT SIDE PANEL ===== */}
      <aside className="editor-side" style={{ width: sideWidth }}>
        <div className="side-resize-handle" onMouseDown={(e) => { e.preventDefault(); setDragging(true); }} />

        <div className="side-actions">
          <button className={"side-mini" + (actMenu ? " is-open" : "")} onClick={() => setActMenu(v => !v)} title="More actions">
            <Icon.More />
          </button>
          <button className={"side-mini" + (side === "copilot" ? " is-active" : "")} onClick={() => setSide("copilot")} title="Open Copilot (⌘K)">
            <Icon.Chat />
          </button>
          <div className="side-save mono" title="Last saved">
            <Icon.Cloud /><span>2m</span>
          </div>
          <div className="side-act-spacer" />
          <button className="btn btn-secondary side-act-btn-sm" title="Deploy this version">
            <Icon.Cloud /> Deploy
          </button>
          <button className="btn btn-primary side-act-btn-sm" onClick={runWorkflow} title="Run workflow (⌘↩)">
            {running
              ? <React.Fragment><span className="status-dot run" /> Running</React.Fragment>
              : <React.Fragment><Icon.Bolt /> Run</React.Fragment>}
          </button>

          {actMenu && (
            <React.Fragment>
              <div className="dropdown-backdrop" onClick={() => setActMenu(false)} />
              <div className="side-act-menu">
                <button className="dropdown-item" onClick={() => setActMenu(false)}><Icon.Download /> Export workflow</button>
                <button className="dropdown-item" onClick={() => setActMenu(false)}><Icon.Doc /> Open docs</button>
                <button className="dropdown-item" onClick={() => setActMenu(false)}><Icon.Cmd /> Shortcuts <span className="kbd">?</span></button>
                <div className="dropdown-sep" />
                <button className="dropdown-item" onClick={() => setActMenu(false)}><Icon.Settings /> Workflow settings</button>
              </div>
            </React.Fragment>
          )}
        </div>

        <nav className="side-tabs-row">
          {[
            { id: "copilot",   label: "Copilot",   icon: Icon.Chat },
            { id: "inspector", label: "Inspector", icon: Icon.Settings, badge: errorCount },
            { id: "library",   label: "Library",   icon: Icon.Grid },
            { id: "logs",      label: "Logs",      icon: Icon.Terminal },
            { id: "test",      label: "Test",      icon: Icon.Bolt },
          ].map(t => {
            const IconT = t.icon;
            return (
              <button key={t.id}
                className={"side-tab" + (side === t.id ? " active" : "")}
                onClick={() => setSide(t.id)}>
                <IconT />
                <span>{t.label}</span>
                {t.badge ? <span className="side-tab-badge">{t.badge}</span> : null}
              </button>
            );
          })}
        </nav>

        <div className="side-body">
          {side === "copilot"   && <CopilotPanel node={node} nodes={nodes} />}
          {side === "inspector" && <InspectorPanel node={node} setProp={setProp} setField={setField} onJumpToCopilot={() => setSide("copilot")} />}
          {side === "library"   && <LibraryPanel />}
          {side === "logs"      && <LogsPanel running={running} />}
          {side === "test"      && <TestPanel onRun={runWorkflow} />}
        </div>
      </aside>
    </div>
  );
}

// ============ SIDEBAR DRAWER (dashboard-style) ============
function EditorSidebar({ onClose, onBack }) {
  const [openGroups, setOpenGroups] = useS_c({ Workspace: true, Operate: true, Workflows: true, Data: false, Integrations: false });
  const [folderOpen, setFolderOpen] = useS_c({ f1: true, f2: false, f3: false });
  const toggleGroup  = (g) => setOpenGroups(s => ({ ...s, [g]: !s[g] }));
  const toggleFolder = (f) => setFolderOpen(s => ({ ...s, [f]: !s[f] }));

  const workflowsTree = [
    { type: "folder", id: "f1", name: "Revenue ops", items: [
      { id: "wf1", name: "Stripe refund — Slack approval", state: "ok",  current: true },
      { id: "wf2", name: "Lead enrichment — Clearbit → HubSpot", state: "ok" },
      { id: "wf6", name: "Invoice triage agent", state: "ok" },
    ]},
    { type: "folder", id: "f2", name: "Inbox & support", items: [
      { id: "wf3", name: "Inbound RFP classifier", state: "ok" },
      { id: "wf7", name: "Support ticket auto-tagger", state: "warn" },
    ]},
    { type: "wf", id: "wf5", name: "Notion → Airtable nightly sync", state: "err" },
    { type: "wf", id: "wf8", name: "Weekly metrics digest", state: "ok" },
  ];
  const totalWorkflows = workflowsTree.reduce((n, x) => n + (x.type === "folder" ? x.items.length : 1), 0);

  const nav = [
    { group: "Workspace", items: [
      { id: "home",        label: "Home",        icon: <Icon.Home />,    onClick: onBack },
      { id: "automations", label: "Automations", icon: <Icon.Flow />,    count: "47", onClick: onBack },
      { id: "templates",   label: "Templates",   icon: <Icon.Layers />,  onClick: onBack },
    ]},
    { group: "Operate", items: [
      { id: "runs",       label: "Runs",      icon: <Icon.Activity />, count: "1.2k", onClick: onBack },
      { id: "schedules",  label: "Schedules", icon: <Icon.Clock />,    count: "6",   onClick: onBack },
      { id: "logs",       label: "Logs",      icon: <Icon.Terminal />, onClick: onBack },
    ]},
    { group: "Data", items: [
      { id: "tables",    label: "Tables",         icon: <Icon.Table />,  count: "8",   onClick: onBack },
      { id: "files",     label: "Files",          icon: <Icon.Folder />, count: "124", onClick: onBack },
      { id: "knowledge", label: "Knowledge base", icon: <Icon.Book />,   count: "8",   onClick: onBack },
      { id: "variables", label: "Variables",      icon: <Icon.Key />,    onClick: onBack },
    ]},
    { group: "Integrations", items: [
      { id: "connections", label: "Connections", icon: <Icon.Plug />, count: "18", onClick: onBack },
    ]},
  ];

  const renderWfRow = (w) => (
    <button key={w.id} className={"wf-row" + (w.current ? " is-current" : "")} onClick={onClose}>
      <span className={"status-dot " + w.state} />
      <span className="wf-name">{w.name}</span>
    </button>
  );

  return (
    <React.Fragment>
      <div className="dropdown-backdrop" onClick={onClose} />
      <aside className="editor-drawer">
        <div className="drawer-top">
          <div className="brand-row">
            <span className="brand">
              <span className="brand-mark"><Icon.FuseMark style={{ width: 14, height: 14 }} /></span>
              <span className="brand-text">fuse</span>
              <span className="brand-badge">Beta</span>
            </span>
            <button className="brand-trail-btn" onClick={onClose} title="Close menu">
              <Icon.PanelClose />
            </button>
          </div>
          <button className="workspace" title="Mahesh's workspace">
            <span className="workspace-avatar">M</span>
            <span className="workspace-meta">
              <span className="workspace-name">Mahesh's workspace</span>
              <span className="workspace-sub"><span className="plan-dot" />Pro · 4 seats</span>
            </span>
            <Icon.Chevrons />
          </button>
          <div className="cmd-search">
            <Icon.Search />
            <input placeholder="Search workspace" autoFocus />
            <span className="kbd">⌘K</span>
          </div>
        </div>

        <div className="drawer-scroll">
          {nav.map((section) => {
            const open = openGroups[section.group];
            return (
              <div key={section.group} className={"nav-section" + (open ? "" : " is-closed")}>
                <div className="nav-group-head" onClick={() => toggleGroup(section.group)}>
                  <span className="nav-group-caret"><Icon.Caret /></span>
                  <span className="nav-group-label">{section.group}</span>
                </div>
                {open && section.items.map(n => (
                  <button key={n.id} className="nav-item" onClick={n.onClick}>
                    {n.icon}
                    <span className="nav-label-text">{n.label}</span>
                    {n.count && <span className="count">{n.count}</span>}
                  </button>
                ))}
              </div>
            );
          })}

          <div className={"nav-section is-workflows" + (openGroups.Workflows ? "" : " is-closed")}>
            <div className="nav-group-head" onClick={() => toggleGroup("Workflows")}>
              <span className="nav-group-caret"><Icon.Caret /></span>
              <span className="nav-group-label">Workflows</span>
              <span className="nav-group-count">{totalWorkflows}</span>
            </div>
            {openGroups.Workflows && (
              <div className="wf-tree">
                {workflowsTree.map(node => {
                  if (node.type !== "folder") return renderWfRow(node);
                  const open = folderOpen[node.id];
                  return (
                    <div key={node.id} className="folder">
                      <div className={"folder-head" + (open ? "" : " is-closed")} onClick={() => toggleFolder(node.id)}>
                        <span className="folder-caret"><Icon.Caret /></span>
                        <span className="folder-icon"><Icon.Folder /></span>
                        <span className="folder-name">{node.name}</span>
                        <span className="folder-count">{node.items.length}</span>
                      </div>
                      {open && <div className="folder-body">{node.items.map(renderWfRow)}</div>}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <div className="drawer-foot">
          <button className="foot-action"><Icon.Help /> Help & docs</button>
          <button className="foot-action"><Icon.Feedback /> Feedback</button>
        </div>
      </aside>
    </React.Fragment>
  );
}

// ============ NODE CARD (unchanged) ============
function NodeCard({ n, selected, running, onSelect }) {
  return (
    <div className={"node-card" + (selected ? " is-selected" : "") + (running ? " is-running" : "") + (n.error ? " has-error" : "")}
      style={{ left: n.x, top: n.y, width: NODE_W }}
      onClick={onSelect}>
      <span className="port port-left" />
      <span className="port port-right" />

      <div className="node-card-head">
        <span className={"node-mark accent-" + n.accent}>{n.mark}</span>
        <span className="node-title">{n.title}</span>
        <button className="node-more" onClick={(e) => e.stopPropagation()}><Icon.More /></button>
      </div>
      <div className="node-card-body">
        {n.props.map((p, i) => (
          <div key={i} className="node-prop">
            <span className="prop-key">{p.k}</span>
            <span className={"prop-val" + (p.kind === "expression" || p.kind === "credential" ? " mono" : "")}>
              {p.kind === "code" || p.kind === "textarea"
                ? <span className="prop-expand">{p.v}</span>
                : p.kind === "chip"
                  ? <span className="prop-chip">{p.v}</span>
                  : p.v
              }
            </span>
          </div>
        ))}
      </div>
      {n.error && <span className="node-error-bar" />}
    </div>
  );
}

window.Canvas = Editor;
