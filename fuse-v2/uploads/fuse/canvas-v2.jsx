// fuse v2 — workflow editor (canvas, redesigned)
const { useState: useS_c } = React;

const NODE_W = 248;
const HEADER_H = 38;
const PROP_H = 26;

const NODES = [
  {
    id: "n1", type: "trigger", x: 60, y: 220,
    mark: <Icon.Bolt />, accent: "green",
    title: "Start",
    props: [{ k: "Start Workflow", v: "manual", chip: true }],
  },
  {
    id: "n2", type: "agent", x: 400, y: 130,
    mark: <Icon.Spark />, accent: "blue",
    title: "Agent",
    error: true,
    props: [
      { k: "Select Provider",     v: "openai" },
      { k: "Provider Credential", v: "3aebc8c0…", mono: true },
      { k: "Model",               v: "filament-2 sonnet" },
      { k: "Messages",            v: "…", expand: true },
      { k: "Tools",               v: "…", expand: true },
      { k: "Knowledge",           v: "refund_policy" },
      { k: "Skills",              v: "—", mute: true },
    ],
  },
  {
    id: "n3", type: "action", x: 760, y: 230,
    mark: <Icon.Branch />, accent: "amber",
    title: "Set Variable",
    props: [
      { k: "Variable Name", v: "refund_decision" },
      { k: "Value",         v: "{{agent.priority}}", mono: true },
    ],
  },
  {
    id: "n4", type: "action", x: 1100, y: 240,
    mark: <Icon.Slack />, accent: "pink",
    title: "Slack",
    props: [
      { k: "Channel", v: "#oncall-revenue" },
      { k: "Message", v: "…", expand: true },
      { k: "Approval", v: "yes / no buttons" },
    ],
  },
];

const EDGES = [
  { from: "n1", to: "n2", fromPort: "right", toPort: "left" },
  { from: "n2", to: "n3", fromPort: "right", toPort: "left" },
  { from: "n3", to: "n4", fromPort: "right", toPort: "left" },
];

function nodeHeight(n) {
  return HEADER_H + (n.props?.length || 0) * PROP_H + (n.error ? 4 : 0) + 4;
}

function Editor({ project, onBack }) {
  const [navOpen, setNavOpen] = useS_c(false);
  const [side, setSide] = useS_c("toolbar"); // toolbar | inspector | logs | test
  const [selected, setSelected] = useS_c("n2");
  const [running, setRunning] = useS_c(false);
  const [zoom, setZoom] = useS_c(100);
  const [bottomOpen, setBottomOpen] = useS_c(true);
  const [tool, setTool] = useS_c("select");
  const [menuOpen, setMenuOpen] = useS_c(false);

  const node = NODES.find(n => n.id === selected) || NODES[1];

  const edgePath = (a, b) => {
    const x1 = a.x + NODE_W;
    const y1 = a.y + HEADER_H / 2 + (a.props.length * PROP_H) / 2;
    const x2 = b.x;
    const y2 = b.y + HEADER_H / 2 + (b.props.length * PROP_H) / 2;
    const dx = Math.max(40, (x2 - x1) * 0.4);
    return `M ${x1} ${y1} C ${x1 + dx} ${y1}, ${x2 - dx} ${y2}, ${x2} ${y2}`;
  };

  const minX = Math.min(...NODES.map(n => n.x)) - 80;
  const maxX = Math.max(...NODES.map(n => n.x + NODE_W)) + 80;
  const minY = Math.min(...NODES.map(n => n.y)) - 80;
  const maxY = Math.max(...NODES.map(n => n.y + nodeHeight(n))) + 80;

  return (
    <div className="editor" data-screen-label="02 Editor">
      <div className="grid-bg" />

      {/* ===== TOP BAR ===== */}
      <header className="editor-topbar">
        <div className="editor-tb-left">
          <button className={"hamb-btn" + (navOpen ? " is-open" : "")} onClick={() => setNavOpen(v => !v)} title="Menu">
            <Icon.Menu />
          </button>
          <div className="editor-crumb">
            <span className="crumb-folder">Revenue ops</span>
            <span className="crumb-sep">/</span>
            <button className={"crumb-title" + (menuOpen ? " is-open" : "")} onClick={() => setMenuOpen(v => !v)}>
              {project?.title || "Stripe refund — Slack approval"}
              <Icon.Caret style={{ width: 12, height: 12, marginLeft: 4 }} />
            </button>
            <span className="status-pill warn">Draft</span>
          </div>
          {menuOpen && (
            <React.Fragment>
              <div className="dropdown-backdrop" onClick={() => setMenuOpen(false)} />
              <div className="workflow-menu">
                <button className="dropdown-item"><Icon.Edit /> Rename workflow</button>
                <button className="dropdown-item"><Icon.Copy /> Duplicate</button>
                <button className="dropdown-item"><Icon.Folder /> Move to folder</button>
                <button className="dropdown-item"><Icon.Download /> Export as JSON</button>
                <div className="dropdown-sep" />
                <button className="dropdown-item"><Icon.Activity /> View runs</button>
                <button className="dropdown-item"><Icon.Clock /> Versions <span className="item-sub">v0.14</span></button>
                <button className="dropdown-item"><Icon.Pause /> Pause workflow</button>
                <div className="dropdown-sep" />
                <button className="dropdown-item danger"><Icon.Trash /> Delete</button>
              </div>
            </React.Fragment>
          )}
        </div>

        <div className="editor-tb-mid">
          <span className="editor-meta">
            <span className="editor-meta-item"><Icon.Clock />Saved 2m ago</span>
            <span className="editor-meta-sep">·</span>
            <span className="editor-meta-item mono">v0.14</span>
            <span className="editor-meta-sep">·</span>
            <span className="editor-meta-item"><span className="status-dot ok" />Connected</span>
          </span>
        </div>

        <div className="editor-tb-right">
          <button className="icon-btn" title="History"><Icon.Activity /></button>
          <button className="icon-btn" title="Share"><Icon.Share /></button>
          <div className="profile-wrap">
            <button className="avatar" aria-label="Account" />
          </div>
        </div>
      </header>

      {/* ===== NAV DRAWER ===== */}
      {navOpen && (
        <React.Fragment>
          <div className="dropdown-backdrop" onClick={() => setNavOpen(false)} />
          <div className="nav-drawer">
            <div className="nav-drawer-head">
              <span className="brand">
                <span className="brand-mark"><Icon.FuseMark style={{ width: 14, height: 14 }} /></span>
                <span className="brand-text">fuse</span>
              </span>
              <button className="icon-btn" onClick={() => setNavOpen(false)}><Icon.PanelClose /></button>
            </div>
            <button className="workspace">
              <span className="workspace-avatar">M</span>
              <span className="workspace-meta">
                <span className="workspace-name">Mahesh's workspace</span>
                <span className="workspace-sub"><span className="plan-dot" />Pro · 4 seats</span>
              </span>
              <Icon.Chevrons />
            </button>
            <div className="cmd-search">
              <Icon.Search />
              <input placeholder="Search" autoFocus />
              <span className="kbd">⌘K</span>
            </div>
            <div className="nav-drawer-body">
              <button className="nav-item" onClick={() => onBack && onBack()}><Icon.Home /><span className="nav-label-text">Home</span></button>
              <button className="nav-item"><Icon.Flow /><span className="nav-label-text">Automations</span><span className="count">47</span></button>
              <button className="nav-item"><Icon.Activity /><span className="nav-label-text">Runs</span><span className="count">1.2k</span></button>
              <button className="nav-item"><Icon.Clock /><span className="nav-label-text">Schedules</span><span className="count">6</span></button>
              <div className="nav-drawer-label">Data</div>
              <button className="nav-item"><Icon.Table /><span className="nav-label-text">Tables</span><span className="count">8</span></button>
              <button className="nav-item"><Icon.Folder /><span className="nav-label-text">Files</span><span className="count">124</span></button>
              <button className="nav-item"><Icon.Book /><span className="nav-label-text">Knowledge base</span></button>
              <button className="nav-item"><Icon.Key /><span className="nav-label-text">Variables</span></button>
              <button className="nav-item"><Icon.Plug /><span className="nav-label-text">Connections</span><span className="count">18</span></button>
              <div className="nav-drawer-label">Workflow</div>
              <button className="nav-item active"><Icon.Edit /><span className="nav-label-text">Editor</span></button>
              <button className="nav-item" onClick={() => setSide("logs")}><Icon.Terminal /><span className="nav-label-text">Logs</span></button>
              <button className="nav-item" onClick={() => setSide("test")}><Icon.Bolt /><span className="nav-label-text">Test runs</span></button>
            </div>
          </div>
        </React.Fragment>
      )}

      {/* ===== CANVAS ===== */}
      <div className="editor-canvas">
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
              const a = NODES.find(n => n.id === e.from);
              const b = NODES.find(n => n.id === e.to);
              if (!a || !b) return null;
              const active = running && (a.id === selected || b.id === selected || (e.from === "n1" && e.to === "n2"));
              return (
                <path key={i} className={"edge-path" + (active ? " active" : "")}
                  d={edgePath(a, b)} fill="none" strokeWidth="1.5" markerEnd="url(#arrow-h)" />
              );
            })}
          </svg>

          {NODES.map(n => (
            <NodeCard key={n.id} n={n}
              selected={selected === n.id}
              running={running && (n.id === "n2" || n.id === "n1")}
              onSelect={() => { setSelected(n.id); setSide("inspector"); }}
            />
          ))}
        </div>

        {/* canvas tool fab */}
        <div className="canvas-fab">
          <button className={"canvas-fab-btn" + (tool === "select" ? " active" : "")} onClick={() => setTool("select")} title="Select">
            <Icon.Cursor />
          </button>
          <button className={"canvas-fab-btn" + (tool === "pan" ? " active" : "")} onClick={() => setTool("pan")} title="Pan">
            <Icon.Hand />
          </button>
          <div className="canvas-fab-sep" />
          <button className="canvas-fab-btn" onClick={() => setZoom(100)} title="Fit">
            <Icon.Maximize />
          </button>
          <button className="canvas-fab-btn" onClick={() => setZoom(z => Math.max(40, z - 10))}><Icon.Minus /></button>
          <span className="canvas-fab-num mono">{zoom}%</span>
          <button className="canvas-fab-btn" onClick={() => setZoom(z => Math.min(200, z + 10))}><Icon.Plus /></button>
        </div>

        <div className="canvas-active">
          <span className="status-dot ok" />
          <span>Workflow valid · {NODES.length} nodes · {EDGES.length} edges</span>
        </div>
      </div>

      {/* ===== RIGHT PANEL ===== */}
      <aside className={"editor-side" + (bottomOpen ? "" : " full-height")}>
        <div className="side-actions">
          <button className="btn btn-secondary side-act-btn"><Icon.Plug /> Deploy</button>
          <button className="btn btn-primary side-act-btn" onClick={() => { setRunning(true); setSide("logs"); setTimeout(() => setRunning(false), 2400); }}>
            {running ? <React.Fragment><span className="status-dot run" /> Running</React.Fragment> : <React.Fragment><Icon.Bolt /> Run</React.Fragment>}
          </button>
        </div>
        <div className="side-tabs-row">
          <div className="side-tabs">
            <button className={"side-tab" + (side === "inspector" ? " active" : "")} onClick={() => setSide("inspector")}>Inspector</button>
            <button className={"side-tab" + (side === "toolbar"   ? " active" : "")} onClick={() => setSide("toolbar")}>Toolbar</button>
            <button className={"side-tab" + (side === "logs"      ? " active" : "")} onClick={() => setSide("logs")}>Logs</button>
            <button className={"side-tab" + (side === "test"      ? " active" : "")} onClick={() => setSide("test")}>Test</button>
          </div>
        </div>

        <div className="side-body">
          {side === "inspector" && <InspectorPanel node={node} />}
          {side === "toolbar" && <ToolbarPanel />}
          {side === "logs" && <LogsPanel running={running} />}
          {side === "test" && <TestPanel />}
        </div>
      </aside>

      {/* ===== BOTTOM PANEL ===== */}
      {bottomOpen && (
        <div className="bottom-panel">
          <div className="bottom-pane bottom-logs">
            <div className="bottom-head">
              <div className="bottom-title">Logs</div>
              <div className="bottom-actions">
                <button className="icon-btn-sm"><Icon.Search /></button>
                <button className="icon-btn-sm" onClick={() => setBottomOpen(false)}><Icon.Caret style={{ transform: "rotate(180deg)" }} /></button>
              </div>
            </div>
            <div className="bottom-body empty">
              <span className="empty-text">No executions yet</span>
            </div>
          </div>
          <div className="bottom-pane bottom-output">
            <div className="bottom-head">
              <div className="bottom-title">Output</div>
              <div className="bottom-actions">
                <button className="icon-btn-sm"><Icon.Search /></button>
                <button className="icon-btn-sm"><Icon.Copy /></button>
                <button className="icon-btn-sm"><Icon.Download /></button>
                <button className="icon-btn-sm"><Icon.Trash /></button>
                <button className="icon-btn-sm"><Icon.More /></button>
              </div>
            </div>
            <div className="bottom-body empty">
              <span className="empty-text">Select a log entry to view details</span>
            </div>
          </div>
        </div>
      )}
      {!bottomOpen && (
        <button className="bottom-reopen" onClick={() => setBottomOpen(true)}>
          <Icon.Terminal /> Show logs & output
        </button>
      )}
    </div>
  );
}

// ============ NODE CARD ============
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
          <div key={i} className={"node-prop" + (p.mute ? " is-mute" : "")}>
            <span className="prop-key">{p.k}</span>
            <span className={"prop-val" + (p.mono ? " mono" : "")}>
              {p.expand
                ? <span className="prop-expand">…</span>
                : p.chip
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

// ============ MINIMAP ============
function Minimap({ nodes, edges, minX, minY, maxX, maxY }) {
  const W = 180, H = 110;
  const bw = maxX - minX, bh = maxY - minY;
  const scale = Math.min((W - 16) / bw, (H - 16) / bh);
  const ox = (W - bw * scale) / 2;
  const oy = (H - bh * scale) / 2;
  return (
    <div className="minimap">
      <svg width={W} height={H}>
        {edges.map((e, i) => {
          const a = nodes.find(n => n.id === e.from);
          const b = nodes.find(n => n.id === e.to);
          if (!a || !b) return null;
          return (
            <line key={i}
              x1={ox + (a.x + NODE_W - minX) * scale} y1={oy + (a.y - minY) * scale + 16}
              x2={ox + (b.x - minX) * scale}          y2={oy + (b.y - minY) * scale + 16}
              stroke="var(--border)" strokeWidth="1" />
          );
        })}
        {nodes.map(n => (
          <rect key={n.id}
            x={ox + (n.x - minX) * scale} y={oy + (n.y - minY) * scale}
            width={NODE_W * scale} height={nodeHeight(n) * scale}
            rx="2" fill="var(--surface-2)" stroke="var(--border-faint)" strokeWidth="1" />
        ))}
        <rect x="6" y="6" width={W - 12} height={H - 12} rx="4"
          fill="none" stroke="var(--accent-line)" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" />
      </svg>
    </div>
  );
}

// ============ INSPECTOR ============
function InspectorPanel({ node }) {
  const stateBadge = node.error
    ? <span className="status-pill err">needs config</span>
    : <span className="status-pill ok">configured</span>;

  // group props into sections — first 3 = primary, rest = advanced
  const primary = (node.props || []).slice(0, 3);
  const advanced = (node.props || []).slice(3);

  return (
    <React.Fragment>
      <div className="insp-header">
        <div className="insp-header-top">
          <span className={"node-mark accent-" + node.accent}>{node.mark}</span>
          <div className="insp-header-titles">
            <div className="insp-header-title">{node.title}</div>
            <div className="insp-header-sub mono">{node.id} · {node.type}</div>
          </div>
          {stateBadge}
        </div>
        <div className="insp-header-meta">
          <span className="insp-meta-item"><Icon.Clock /> last run 812ms</span>
          <span className="insp-meta-sep">·</span>
          <span className="insp-meta-item"><Icon.Activity /> 1,204 runs</span>
          <span className="insp-meta-sep">·</span>
          <span className="insp-meta-item"><span className="status-dot ok" />99.4% ok</span>
        </div>
        <div className="insp-header-actions">
          <button className="btn btn-secondary insp-act"><Icon.Bolt /> Test node</button>
          <button className="icon-btn-sm" title="Duplicate"><Icon.Copy /></button>
          <button className="icon-btn-sm" title="Docs"><Icon.Doc /></button>
          <button className="icon-btn-sm danger" title="Delete"><Icon.Trash /></button>
        </div>
      </div>

      <div className="insp-form">
        <div className="insp-section">
          <div className="insp-section-head">
            <span className="eyebrow">Identity</span>
          </div>
          <div className="form-row">
            <label>Label</label>
            <input className="form-input" defaultValue={node.title} />
          </div>
          <div className="form-row">
            <label>Description</label>
            <input className="form-input" placeholder="Optional — describe what this step does" />
          </div>
        </div>

        {primary.length > 0 && (
          <div className="insp-section">
            <div className="insp-section-head">
              <span className="eyebrow">Configuration</span>
            </div>
            {primary.map((p, i) => (
              <div key={i} className="form-row">
                <label>{p.k}</label>
                {p.expand ? (
                  <button className="form-expand">
                    <Icon.Code /> Open {p.k.toLowerCase()} editor
                    <Icon.CaretRight style={{ marginLeft: "auto", width: 12, height: 12, color: "var(--text-faint)" }} />
                  </button>
                ) : (
                  <div className="form-pill">
                    <span className={p.mono ? "mono" : ""}>{p.v}</span>
                    <Icon.Caret style={{ width: 11, height: 11, marginLeft: "auto", color: "var(--text-faint)" }} />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {advanced.length > 0 && (
          <div className="insp-section">
            <div className="insp-section-head">
              <span className="eyebrow">Advanced</span>
              <span className="insp-section-count">{advanced.length} fields</span>
            </div>
            {advanced.map((p, i) => (
              <div key={i} className="form-row">
                <label>{p.k}</label>
                {p.expand ? (
                  <button className="form-expand">
                    <Icon.Code /> Open {p.k.toLowerCase()} editor
                    <Icon.CaretRight style={{ marginLeft: "auto", width: 12, height: 12, color: "var(--text-faint)" }} />
                  </button>
                ) : (
                  <div className="form-pill">
                    <span className={p.mono ? "mono" : ""}>{p.v}</span>
                    <Icon.Caret style={{ width: 11, height: 11, marginLeft: "auto", color: "var(--text-faint)" }} />
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        <div className="insp-section">
          <div className="insp-section-head">
            <span className="eyebrow">Last test output</span>
            <button className="link-btn">Run again <Icon.CaretRight /></button>
          </div>
          <div className="code-block mono">{`{
  "priority": "high",
  "category": "fraud_dispute",
  "confidence": 0.94,
  "summary": "Customer disputes Mar 14 charge…"
}`}</div>
          <div className="insp-output-meta">
            <span><span className="status-dot ok" />Succeeded · 812ms · 1,204 tokens</span>
          </div>
        </div>
      </div>
    </React.Fragment>
  );
}

// ============ TOOLBAR (NODE LIB) ============
function ToolbarPanel() {
  const lib = [
    { group: "Triggers", count: 4, items: [
      { kind: "trigger", accent: "green", title: "Start",    sub: "Manual trigger" },
      { kind: "trigger", accent: "green", title: "Schedule", sub: "Cron expression" },
      { kind: "trigger", accent: "green", title: "Webhook",  sub: "HTTP POST" },
      { kind: "trigger", accent: "green", title: "Email",    sub: "IMAP / Gmail" },
    ]},
    { group: "AI", count: 6, items: [
      { kind: "agent", accent: "blue", title: "Agent",      sub: "Tool-using LLM" },
      { kind: "agent", accent: "blue", title: "LLM call",   sub: "One-shot completion" },
      { kind: "agent", accent: "blue", title: "Classify",   sub: "Label input" },
      { kind: "agent", accent: "blue", title: "Extract",    sub: "Structured fields" },
      { kind: "agent", accent: "blue", title: "Embed",      sub: "Vector embedding" },
      { kind: "agent", accent: "blue", title: "Vision",     sub: "Read images" },
    ]},
    { group: "Logic", count: 4, items: [
      { kind: "logic", accent: "amber", title: "Branch", sub: "If / else split" },
      { kind: "logic", accent: "amber", title: "Filter", sub: "Skip on condition" },
      { kind: "logic", accent: "amber", title: "Loop",   sub: "Iterate array" },
      { kind: "logic", accent: "amber", title: "Set variable", sub: "Assign value" },
    ]},
    { group: "Apps", count: 5, items: [
      { kind: "action", accent: "pink", title: "Slack",   sub: "Post · approve" },
      { kind: "action", accent: "pink", title: "Stripe",  sub: "Refund · charge" },
      { kind: "action", accent: "pink", title: "Notion",  sub: "Page · DB" },
      { kind: "action", accent: "pink", title: "HubSpot", sub: "Contact · deal" },
      { kind: "action", accent: "pink", title: "Linear",  sub: "Issue · cycle" },
    ]},
  ];
  return (
    <React.Fragment>
      <div className="side-section-head">
        <div className="side-section-title">Toolbar</div>
      </div>
      <div className="side-search">
        <Icon.Search />
        <input placeholder="Search nodes" />
      </div>
      <div className="lib-scroll">
        {lib.map(g => (
          <div key={g.group} className="lib-group">
            <div className="lib-group-head">
              <span>{g.group}</span>
              <span className="lib-group-count">{g.count}</span>
            </div>
            <div className="lib-items">
              {g.items.map((it, i) => (
                <button key={i} className="lib-item">
                  <span className={"node-mark sm accent-" + it.accent}>
                    {it.kind === "trigger" ? <Icon.Bolt /> : it.kind === "agent" ? <Icon.Spark /> : it.kind === "logic" ? <Icon.Branch /> : <Icon.Plug />}
                  </span>
                  <span className="lib-meta">
                    <span className="lib-title">{it.title}</span>
                    <span className="lib-sub">{it.sub}</span>
                  </span>
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </React.Fragment>
  );
}

// ============ LOGS ============
function LogsPanel({ running }) {
  const live = [
    { t: "14:42:01.218", lvl: "info", src: "trigger", msg: "Workflow started · trigger=manual" },
    { t: "14:42:01.302", lvl: "info", src: "agent",   msg: "Prompting filament-2 with 4 tools" },
    { t: "14:42:01.418", lvl: "info", src: "agent",   msg: "→ tools.lookup_customer(id=cust_201)" },
    { t: "14:42:01.812", lvl: "ok",   src: "agent",   msg: "Completed · 1,204 tokens · 812ms" },
    { t: "14:42:01.815", lvl: "info", src: "branch",  msg: "priority === 'high' → yes" },
    { t: "14:42:01.901", lvl: "info", src: "slack",   msg: "Posting to #oncall-revenue" },
    { t: "14:42:02.140", lvl: "ok",   src: "slack",   msg: "Message ts=1716305922.001401" },
  ];
  return (
    <React.Fragment>
      <div className="side-section-head">
        <div className="side-section-title">
          {running ? <React.Fragment><span className="status-dot run" /> Running…</React.Fragment> : <React.Fragment><span className="status-dot ok" /> Last run</React.Fragment>}
          <span className="status-pill ok">2.4s</span>
        </div>
        <button className="icon-btn-sm"><Icon.Download /></button>
      </div>
      <div className="side-search">
        <Icon.Search />
        <input placeholder="Filter logs" />
      </div>
      <div className="logs-stream">
        {live.map((l, i) => (
          <div key={i} className={"log-line " + l.lvl}>
            <span className="log-time">{l.t}</span>
            <span className={"log-lvl " + l.lvl}>{l.lvl.toUpperCase()}</span>
            <span className="log-src">{l.src}</span>
            <span className="log-msg">{l.msg}</span>
          </div>
        ))}
      </div>
    </React.Fragment>
  );
}

// ============ TEST ============
function TestPanel() {
  return (
    <React.Fragment>
      <div className="side-section-head">
        <div className="side-section-title">Test runner</div>
      </div>
      <div className="test-body">
        <span className="eyebrow">Trigger payload</span>
        <div className="code-block mono">{`{
  "event": "charge.refunded",
  "data": {
    "amount_usd": 240,
    "customer_id": "cust_201",
    "description": "Mar 14 charge dispute"
  }
}`}</div>

        <span className="eyebrow">Variables</span>
        <div className="kv-list">
          <div className="kv-row"><span className="kv-key mono">REFUND_LIMIT_USD</span><span className="kv-eq">=</span><span className="kv-val mono">500</span></div>
          <div className="kv-row"><span className="kv-key mono">ON_CALL_CHANNEL</span><span className="kv-eq">=</span><span className="kv-val mono">#oncall-revenue</span></div>
        </div>

        <span className="eyebrow">Options</span>
        <label className="test-check"><input type="checkbox" defaultChecked /> Mock external calls</label>
        <label className="test-check"><input type="checkbox" /> Replay last successful run</label>

        <button className="btn btn-primary test-run-btn"><Icon.Bolt /> Run test</button>
      </div>
    </React.Fragment>
  );
}

window.Canvas = Editor;
