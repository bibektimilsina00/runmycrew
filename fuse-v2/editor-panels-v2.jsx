// fuse v2 — editor side-panel components (Inspector, Copilot, Library, Logs, Test)
const { useState: useP_s, useRef: useP_r, useEffect: useP_e, useMemo: useP_m } = React;

// ============ DATA ============
const SLASH_COMMANDS = [
  { cmd: "/fix",      hint: "Suggest a fix for the selected node",      icon: "Bolt"   },
  { cmd: "/explain",  hint: "Explain what this node does",              icon: "Help"   },
  { cmd: "/improve",  hint: "Suggest an improvement to this workflow",  icon: "Spark"  },
  { cmd: "/test",     hint: "Generate a test payload for this trigger", icon: "Code"   },
  { cmd: "/find",     hint: "Find a tool or app to connect",            icon: "Search" },
];

const RUN_HISTORY = [
  { id: "r1", t: "Just now",  status: "ok",  duration: "2.4s", trigger: "manual",   tokens: "1,204", date: "Today 14:42" },
  { id: "r2", t: "12m ago",   status: "ok",  duration: "2.1s", trigger: "manual",   tokens: "1,180", date: "Today 14:30" },
  { id: "r3", t: "1h ago",    status: "err", duration: "0.4s", trigger: "schedule", tokens: "—",     date: "Today 13:42" },
  { id: "r4", t: "3h ago",    status: "ok",  duration: "2.6s", trigger: "manual",   tokens: "1,256", date: "Today 11:42" },
  { id: "r5", t: "Yesterday", status: "ok",  duration: "2.0s", trigger: "manual",   tokens: "1,142", date: "Yesterday 16:18" },
];

const LOG_LINES_BY_RUN = {
  r1: [
    { t: "14:42:01.218", lvl: "info", src: "trigger", msg: "Workflow started · trigger=manual" },
    { t: "14:42:01.302", lvl: "info", src: "agent",   msg: "Prompting filament-2 with 4 tools" },
    { t: "14:42:01.418", lvl: "info", src: "agent",   msg: "→ tools.lookup_customer(id=cust_201)" },
    { t: "14:42:01.620", lvl: "info", src: "agent",   msg: "← customer { tier=pro, lifetime_value=2840 }" },
    { t: "14:42:01.812", lvl: "ok",   src: "agent",   msg: "Completed · 1,204 tokens · 812ms" },
    { t: "14:42:01.815", lvl: "info", src: "branch",  msg: "priority === 'high' → yes" },
    { t: "14:42:01.901", lvl: "info", src: "slack",   msg: "Posting to #oncall-revenue" },
    { t: "14:42:02.140", lvl: "ok",   src: "slack",   msg: "Message ts=1716305922.001401" },
    { t: "14:42:02.142", lvl: "ok",   src: "system",  msg: "Run finished · 2 succeeded · 0 failed" },
  ],
  r2: [
    { t: "14:30:00.012", lvl: "info", src: "trigger", msg: "Workflow started · trigger=manual" },
    { t: "14:30:01.140", lvl: "ok",   src: "agent",   msg: "Completed · 1,180 tokens" },
    { t: "14:30:01.900", lvl: "ok",   src: "slack",   msg: "Message posted" },
  ],
  r3: [
    { t: "13:42:00.000", lvl: "info", src: "trigger", msg: "Workflow started · trigger=schedule" },
    { t: "13:42:00.412", lvl: "err",  src: "agent",   msg: "Provider credential expired (3aebc8c0…)" },
    { t: "13:42:00.414", lvl: "err",  src: "system",  msg: "Run aborted after error in node n2" },
  ],
  r4: [
    { t: "11:42:00.020", lvl: "info", src: "trigger", msg: "Workflow started · trigger=manual" },
    { t: "11:42:02.602", lvl: "ok",   src: "system",  msg: "Run finished · 2 succeeded · 0 failed" },
  ],
  r5: [
    { t: "16:18:00.020", lvl: "info", src: "trigger", msg: "Workflow started" },
    { t: "16:18:02.018", lvl: "ok",   src: "system",  msg: "Run finished" },
  ],
};

const INITIAL_TESTS = [
  {
    id: "t1", name: "Standard refund · $240", desc: "Normal customer dispute flow",
    payload: `{
  "event": "charge.refunded",
  "data": {
    "amount_usd": 240,
    "customer_id": "cust_201",
    "description": "Mar 14 charge dispute"
  }
}`,
    vars: [
      { k: "REFUND_LIMIT_USD", v: "500" },
      { k: "ON_CALL_CHANNEL",  v: "#oncall-revenue" },
    ],
    lastRun: { status: "ok", t: "12m ago" },
  },
  {
    id: "t2", name: "High-value refund · $1,200", desc: "Above auto-approval limit",
    payload: `{
  "event": "charge.refunded",
  "data": {
    "amount_usd": 1200,
    "customer_id": "cust_044"
  }
}`,
    vars: [{ k: "REFUND_LIMIT_USD", v: "500" }],
    lastRun: { status: "ok", t: "2h ago" },
  },
  {
    id: "t3", name: "Fraud signal trigger", desc: "Customer flagged for review",
    payload: `{
  "event": "charge.refunded",
  "data": {
    "amount_usd": 89,
    "customer_id": "cust_999",
    "fraud_signal": true
  }
}`,
    vars: [],
    lastRun: { status: "err", t: "1d ago" },
  },
];

// ============ SHARED HELPERS ============
function Section({ title, count, open, onToggle, children, hint }) {
  return (
    <div className={"insp-section" + (open ? "" : " is-closed")}>
      <button className="insp-section-head" onClick={onToggle}>
        <span className="insp-section-caret"><Icon.Caret /></span>
        <span className="insp-section-title">{title}</span>
        {count != null && <span className="insp-section-count">{count}</span>}
        {hint && <span className="insp-section-hint">{hint}</span>}
      </button>
      {open && <div className="insp-section-body">{children}</div>}
    </div>
  );
}

function Field({ label, children, hint, error }) {
  return (
    <div className={"field" + (error ? " has-error" : "")}>
      <div className="field-label-row">
        <span className="field-label">{label}</span>
        {hint && <span className="field-hint">{hint}</span>}
      </div>
      {children}
      {error && <span className="field-error">{error}</span>}
    </div>
  );
}

function FieldRow({ prop, nodeId, setProp }) {
  const onChange = (v) => setProp(nodeId, prop.k, v);

  if (prop.kind === "select") {
    return (
      <Field label={prop.k}>
        <div className="form-select-wrap">
          <select className="form-select" value={prop.v} onChange={(e) => onChange(e.target.value)}>
            {prop.options.map(o => <option key={o} value={o}>{o}</option>)}
          </select>
          <Icon.Caret />
        </div>
      </Field>
    );
  }
  if (prop.kind === "credential") {
    return (
      <Field label={prop.k} error={"Credential expired — reconnect to continue"}>
        <button className="form-cred">
          <span className="form-cred-icon"><Icon.Key /></span>
          <span className="form-cred-name mono">{prop.v}</span>
          <span className="status-pill err">Expired</span>
          <Icon.CaretRight />
        </button>
      </Field>
    );
  }
  if (prop.kind === "textarea") {
    return (
      <Field label={prop.k} hint={`${String(prop.v).length} chars`}>
        <textarea className="form-textarea" rows={3} value={prop.v}
          onChange={(e) => onChange(e.target.value)} />
      </Field>
    );
  }
  if (prop.kind === "code") {
    return (
      <Field label={prop.k}>
        <button className="form-expand">
          <span className="form-expand-icon"><Icon.Code /></span>
          <span className="form-expand-text">{prop.v}</span>
          <span className="form-expand-trail"><Icon.CaretRight /></span>
        </button>
      </Field>
    );
  }
  if (prop.kind === "expression") {
    return (
      <Field label={prop.k} hint="Liquid template">
        <div className="form-input-wrap">
          <input className="form-input mono" value={prop.v} onChange={(e) => onChange(e.target.value)} />
          <button className="form-input-trail" title="Insert variable"><Icon.Code /></button>
        </div>
      </Field>
    );
  }
  if (prop.kind === "number") {
    return (
      <Field label={prop.k}>
        <input className="form-input mono" type="number" step="0.05" value={prop.v}
          onChange={(e) => onChange(e.target.value)} />
      </Field>
    );
  }
  if (prop.kind === "toggle") {
    const on = String(prop.v).toLowerCase() === "yes" || prop.v === true;
    return (
      <div className="field field-inline">
        <span className="field-label">{prop.k}</span>
        <button className={"form-toggle" + (on ? " on" : "")}
          onClick={() => onChange(on ? "no" : "yes")}
          aria-pressed={on}>
          <span className="form-toggle-knob" />
        </button>
      </div>
    );
  }
  return (
    <Field label={prop.k}>
      <input className="form-input" value={prop.v} onChange={(e) => onChange(e.target.value)} />
    </Field>
  );
}

// ============ INSPECTOR ============
function InspectorPanel({ node, setProp, setField, onJumpToCopilot }) {
  const [open, setOpen] = useP_s({
    general: true, config: true, when: false, errors: false, output: false,
  });
  const [menuOpen, setMenuOpen] = useP_s(false);
  const toggle = (k) => setOpen(s => ({ ...s, [k]: !s[k] }));

  return (
    <div className="insp">
      <div className="insp-head">
        <span className={"node-mark accent-" + node.accent}>{node.mark}</span>
        <div className="insp-head-titles">
          <input
            className="insp-name-input"
            value={node.title}
            onChange={(e) => setField(node.id, "title", e.target.value)}
            spellCheck={false}
          />
          <div className="insp-head-meta">
            <span className="insp-head-id mono">{node.id}</span>
            <span className="insp-head-sep">·</span>
            <span className="insp-head-type">{node.type}</span>
            <span className="insp-head-sep">·</span>
            {node.error
              ? <span className="status-pill err">Needs config</span>
              : <span className="status-pill ok">Ready</span>}
          </div>
        </div>
        <button className={"icon-btn-sm" + (menuOpen ? " is-active" : "")} onClick={() => setMenuOpen(v => !v)} title="More">
          <Icon.More />
        </button>
        {menuOpen && (
          <React.Fragment>
            <div className="dropdown-backdrop" onClick={() => setMenuOpen(false)} />
            <div className="insp-head-menu">
              <button className="dropdown-item" onClick={() => setMenuOpen(false)}><Icon.Copy /> Duplicate node</button>
              <button className="dropdown-item" onClick={() => setMenuOpen(false)}><Icon.Doc /> View docs</button>
              <button className="dropdown-item" onClick={() => setMenuOpen(false)}><Icon.Code /> View as JSON</button>
              <button className="dropdown-item" onClick={() => setMenuOpen(false)}><Icon.Pause /> Disable node</button>
              <div className="dropdown-sep" />
              <button className="dropdown-item danger" onClick={() => setMenuOpen(false)}><Icon.Trash /> Delete node</button>
            </div>
          </React.Fragment>
        )}
      </div>

      {node.error && (
        <div className="insp-error">
          <span className="insp-error-icon"><Icon.Bell /></span>
          <div className="insp-error-body">
            <div className="insp-error-title">Node has errors</div>
            <div className="insp-error-msg">{node.errorMsg}</div>
          </div>
          <button className="insp-error-cta" onClick={onJumpToCopilot}>
            <Icon.Spark /> Fix with Copilot
          </button>
        </div>
      )}

      <div className="insp-body">
        <Section title="General" open={open.general} onToggle={() => toggle("general")}>
          <Field label="Label">
            <input className="form-input" value={node.title}
              onChange={(e) => setField(node.id, "title", e.target.value)} />
          </Field>
          <Field label="Description" hint="Optional">
            <textarea className="form-textarea" rows={3}
              placeholder="What does this step do?"
              value={node.description || ""}
              onChange={(e) => setField(node.id, "description", e.target.value)} />
          </Field>
        </Section>

        <Section title="Configuration" count={node.props.length} open={open.config} onToggle={() => toggle("config")}>
          {node.props.map((p, i) => <FieldRow key={i} prop={p} nodeId={node.id} setProp={setProp} />)}
        </Section>

        <Section title="When this runs" hint="conditional" open={open.when} onToggle={() => toggle("when")}>
          <Field label="Run only if" hint="Liquid expression">
            <div className="form-input-wrap">
              <input className="form-input mono" placeholder="{{ trigger.amount_usd }} > 0" />
              <button className="form-input-trail" title="Insert variable"><Icon.Code /></button>
            </div>
          </Field>
          <Field label="Wait before running">
            <input className="form-input mono" placeholder="0s" />
          </Field>
        </Section>

        <Section title="Error handling" hint="retries · fallback" open={open.errors} onToggle={() => toggle("errors")}>
          <Field label="On error">
            <div className="form-select-wrap">
              <select className="form-select" defaultValue="retry">
                <option value="retry">Retry up to 3 times</option>
                <option value="continue">Continue workflow</option>
                <option value="stop">Stop workflow</option>
                <option value="fallback">Go to fallback node</option>
              </select>
              <Icon.Caret />
            </div>
          </Field>
          <Field label="Timeout">
            <input className="form-input mono" defaultValue="30s" />
          </Field>
          <Field label="Alert on failure">
            <div className="form-input-wrap">
              <input className="form-input mono" placeholder="#alerts" />
              <button className="form-input-trail"><Icon.Slack /></button>
            </div>
          </Field>
        </Section>

        <Section title="Output" hint="schema · sample" open={open.output} onToggle={() => toggle("output")}>
          <span className="eyebrow">Last run output</span>
          <div className="code-block mono">{`{
  "priority": "high",
  "category": "fraud_dispute",
  "confidence": 0.94,
  "summary": "Customer disputes Mar 14 charge…"
}`}</div>
          <div className="insp-output-meta">
            <span><span className="status-dot ok" />Succeeded · 812ms · 1,204 tokens</span>
          </div>
        </Section>
      </div>

      <div className="insp-foot">
        <button className="btn btn-secondary insp-foot-btn"><Icon.Bolt /> Test this node</button>
      </div>
    </div>
  );
}

// ============ COPILOT ============
function CopilotPanel({ node, nodes, onApplySuggestion }) {
  const [msgs, setMsgs] = useP_s([
    { role: "assistant", content: "Hi — I can fix node errors, explain steps, generate test payloads, or suggest tools. Try a slash command, or just ask." },
  ]);
  const [input, setInput] = useP_s("");
  const [busy, setBusy] = useP_s(false);
  const [showSlash, setShowSlash] = useP_s(false);
  const [slashIdx, setSlashIdx] = useP_s(0);
  const streamRef = useP_r(null);
  const inputRef = useP_r(null);

  useP_e(() => {
    const el = streamRef.current;
    if (el) el.scrollTop = el.scrollHeight;
  }, [msgs, busy]);

  const slashFilter = input.startsWith("/") && !input.includes(" ")
    ? SLASH_COMMANDS.filter(c => c.cmd.startsWith(input))
    : [];

  useP_e(() => {
    setShowSlash(slashFilter.length > 0);
    setSlashIdx(0);
  }, [input]);

  const send = async (text) => {
    const t = (text ?? input).trim();
    if (!t || busy) return;
    setMsgs(m => [...m, { role: "user", content: t }]);
    setInput("");
    setBusy(true);
    try {
      const slash = SLASH_COMMANDS.find(c => t.startsWith(c.cmd));
      const slashHint = slash ? `User invoked slash command "${slash.cmd}" (${slash.hint}). ` : "";
      const ctx = [
        `You are a copilot inside a low-code workflow editor called fuse.`,
        `User is editing workflow "Stripe refund — Slack approval".`,
        `Nodes (in order): ${nodes.map(n => `${n.title} (${n.type})`).join(" → ")}.`,
        `Currently selected node: "${node.title}" (${node.type})${node.error ? ` — has error: ${node.errorMsg}` : ""}.`,
        slashHint,
        `Keep replies 1-3 sentences. No markdown headers, just plain text. Be concrete and friendly.`,
      ].join(" ");
      const reply = await window.claude.complete({
        messages: [{ role: "user", content: `${ctx}\n\nUser: ${t}` }],
      });
      setMsgs(m => [...m, { role: "assistant", content: reply }]);
    } catch (e) {
      setMsgs(m => [...m, { role: "assistant", content: "Sorry — I couldn't reach the model right now. Try again in a moment." }]);
    } finally {
      setBusy(false);
    }
  };

  const onKeyDown = (e) => {
    if (showSlash) {
      if (e.key === "ArrowDown") { e.preventDefault(); setSlashIdx(i => Math.min(slashFilter.length - 1, i + 1)); return; }
      if (e.key === "ArrowUp")   { e.preventDefault(); setSlashIdx(i => Math.max(0, i - 1)); return; }
      if (e.key === "Tab" || (e.key === "Enter" && slashFilter[slashIdx])) {
        e.preventDefault();
        const cmd = slashFilter[slashIdx];
        setInput(cmd.cmd + " ");
        setShowSlash(false);
        return;
      }
      if (e.key === "Escape") { e.preventDefault(); setShowSlash(false); return; }
    }
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  };

  const quickActions = node.error
    ? [{ label: "Fix this node", text: "/fix " + node.title }, { label: "Explain the error", text: "/explain why the agent has an error" }, { label: "Suggest tools", text: "/find tools for refund verification" }]
    : [{ label: "Explain this node", text: "/explain " + node.title }, { label: "Generate test", text: "/test " + node.title }, { label: "Improve workflow", text: "/improve the refund workflow" }];

  return (
    <div className="copilot">
      <div className="copilot-stream" ref={streamRef}>
        {msgs.map((m, i) => (
          <div key={i} className={"copilot-msg " + m.role}>
            {m.role === "assistant" && <span className="copilot-mark"><Icon.Spark /></span>}
            <div className="copilot-bubble">{m.content}</div>
          </div>
        ))}
        {busy && (
          <div className="copilot-msg assistant">
            <span className="copilot-mark"><Icon.Spark /></span>
            <div className="copilot-bubble"><span className="dots"><span /><span /><span /></span></div>
          </div>
        )}
      </div>

      <div className="copilot-quick">
        {quickActions.map((qa, i) => (
          <button key={i} className="suggest-chip" onClick={() => send(qa.text)} disabled={busy}>
            {qa.label}
          </button>
        ))}
      </div>

      <div className="copilot-composer-wrap">
        {showSlash && (
          <div className="slash-pop">
            {slashFilter.map((c, i) => {
              const IconC = Icon[c.icon] || Icon.Spark;
              return (
                <button key={c.cmd}
                  className={"slash-item" + (i === slashIdx ? " active" : "")}
                  onMouseEnter={() => setSlashIdx(i)}
                  onClick={() => { setInput(c.cmd + " "); setShowSlash(false); inputRef.current?.focus(); }}>
                  <IconC />
                  <span className="slash-cmd mono">{c.cmd}</span>
                  <span className="slash-hint">{c.hint}</span>
                </button>
              );
            })}
          </div>
        )}
        <div className="copilot-composer">
          <button className="copilot-context-btn" title="Currently scoped to selected node">
            <Icon.Spark />
            <span className="copilot-context-name">@{node.title}</span>
          </button>
          <input
            ref={inputRef}
            className="copilot-input"
            placeholder="Ask Copilot, or type / for commands"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={onKeyDown}
            disabled={busy}
          />
          <button className="copilot-send" onClick={() => send()} disabled={!input.trim() || busy} title="Send (↩)">
            <Icon.ArrowUp />
          </button>
        </div>
      </div>
    </div>
  );
}

// ============ LIBRARY ============
function LibraryPanel({ recentTitles }) {
  const [q, setQ] = useP_s("");
  const [filter, setFilter] = useP_s("all");

  const lib = [
    { group: "Triggers", kind: "trigger", items: [
      { kind: "trigger", accent: "green", title: "Manual",   sub: "Start from editor or API" },
      { kind: "trigger", accent: "green", title: "Schedule", sub: "Cron expression" },
      { kind: "trigger", accent: "green", title: "Webhook",  sub: "HTTP POST" },
      { kind: "trigger", accent: "green", title: "Email",    sub: "IMAP / Gmail" },
      { kind: "trigger", accent: "green", title: "On record change", sub: "Table or DB" },
    ]},
    { group: "AI",       kind: "agent",   items: [
      { kind: "agent", accent: "blue", title: "Agent",      sub: "Tool-using LLM" },
      { kind: "agent", accent: "blue", title: "LLM call",   sub: "One-shot completion" },
      { kind: "agent", accent: "blue", title: "Classify",   sub: "Label input" },
      { kind: "agent", accent: "blue", title: "Extract",    sub: "Structured fields" },
      { kind: "agent", accent: "blue", title: "Embed",      sub: "Vector embedding" },
      { kind: "agent", accent: "blue", title: "Vision",     sub: "Read images" },
    ]},
    { group: "Logic",    kind: "logic",   items: [
      { kind: "logic", accent: "amber", title: "Branch",       sub: "If / else split" },
      { kind: "logic", accent: "amber", title: "Filter",       sub: "Skip on condition" },
      { kind: "logic", accent: "amber", title: "Loop",         sub: "Iterate array" },
      { kind: "logic", accent: "amber", title: "Set variable", sub: "Assign value" },
      { kind: "logic", accent: "amber", title: "Delay",        sub: "Wait then continue" },
      { kind: "logic", accent: "amber", title: "Merge",        sub: "Combine branches" },
    ]},
    { group: "Apps",     kind: "action",  items: [
      { kind: "action", accent: "pink", title: "Slack",   sub: "Post · approve" },
      { kind: "action", accent: "pink", title: "Stripe",  sub: "Refund · charge" },
      { kind: "action", accent: "pink", title: "Notion",  sub: "Page · DB" },
      { kind: "action", accent: "pink", title: "HubSpot", sub: "Contact · deal" },
      { kind: "action", accent: "pink", title: "Linear",  sub: "Issue · cycle" },
      { kind: "action", accent: "pink", title: "Gmail",   sub: "Send email" },
    ]},
  ];

  const filters = [
    { id: "all",     label: "All",     icon: Icon.Grid },
    { id: "trigger", label: "Triggers", icon: Icon.Bolt },
    { id: "agent",   label: "AI",      icon: Icon.Spark },
    { id: "logic",   label: "Logic",   icon: Icon.Branch },
    { id: "action",  label: "Apps",    icon: Icon.Plug },
  ];

  const ql = q.trim().toLowerCase();
  const filtered = lib
    .filter(g => filter === "all" || g.kind === filter)
    .map(g => ({
      ...g,
      items: g.items.filter(it => !ql || it.title.toLowerCase().includes(ql) || it.sub.toLowerCase().includes(ql)),
    }))
    .filter(g => g.items.length);

  const allItems = lib.flatMap(g => g.items);
  const recent = (recentTitles || ["Agent", "Slack", "Branch"])
    .map(t => allItems.find(it => it.title === t))
    .filter(Boolean);

  const renderItem = (it, key) => (
    <button key={key} className="lib-item" draggable>
      <span className={"node-mark sm accent-" + it.accent}>
        {it.kind === "trigger" ? <Icon.Bolt /> : it.kind === "agent" ? <Icon.Spark /> : it.kind === "logic" ? <Icon.Branch /> : <Icon.Plug />}
      </span>
      <span className="lib-meta">
        <span className="lib-title">{it.title}</span>
        <span className="lib-sub">{it.sub}</span>
      </span>
      <span className="lib-drag" title="Drag to canvas"><Icon.Grid /></span>
    </button>
  );

  return (
    <div className="lib-panel">
      <div className="side-section-head">
        <div className="side-section-title">Node library</div>
        <span className="side-section-sub mono">{lib.reduce((n, g) => n + g.items.length, 0)} blocks</span>
      </div>
      <div className="side-search">
        <Icon.Search />
        <input placeholder="Search nodes…" value={q} onChange={(e) => setQ(e.target.value)} />
        {q && <button className="side-search-clear" onClick={() => setQ("")}><Icon.Plus style={{ transform: "rotate(45deg)" }} /></button>}
      </div>
      <div className="lib-filters">
        {filters.map(f => {
          const IconF = f.icon;
          return (
            <button key={f.id} className={"lib-filter-chip" + (filter === f.id ? " active" : "")}
              onClick={() => setFilter(f.id)}>
              <IconF />
              <span>{f.label}</span>
            </button>
          );
        })}
      </div>
      <div className="lib-scroll">
        {filter === "all" && !ql && recent.length > 0 && (
          <div className="lib-group">
            <div className="lib-group-head">
              <span>Recently used</span>
              <span className="lib-group-count">{recent.length}</span>
            </div>
            <div className="lib-items">
              {recent.map((it, i) => renderItem(it, "recent-" + i))}
            </div>
          </div>
        )}

        {filtered.length === 0 && (
          <div className="lib-empty">
            <span>No nodes match{ql ? ` "${q}"` : ""}.</span>
            {(ql || filter !== "all") && (
              <button className="link-btn" onClick={() => { setQ(""); setFilter("all"); }}>Clear filters</button>
            )}
          </div>
        )}

        {filtered.map(g => (
          <div key={g.group} className="lib-group">
            <div className="lib-group-head">
              <span>{g.group}</span>
              <span className="lib-group-count">{g.items.length}</span>
            </div>
            <div className="lib-items">
              {g.items.map((it, i) => renderItem(it, g.group + "-" + i))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============ LOGS ============
function LogsPanel({ running }) {
  const [runId, setRunId] = useP_s(RUN_HISTORY[0].id);
  const [q, setQ] = useP_s("");
  const [level, setLevel] = useP_s("all");
  const [runMenu, setRunMenu] = useP_s(false);
  const [expanded, setExpanded] = useP_s(null);

  const run = RUN_HISTORY.find(r => r.id === runId) || RUN_HISTORY[0];
  const lines = LOG_LINES_BY_RUN[runId] || [];
  const ql = q.trim().toLowerCase();
  const filtered = lines.filter(l =>
    (level === "all" || l.lvl === level) &&
    (!ql || l.msg.toLowerCase().includes(ql) || l.src.toLowerCase().includes(ql))
  );

  return (
    <div className="logs-panel">
      <div className="side-section-head">
        <div className="logs-run-pick">
          <button className={"logs-run-btn" + (runMenu ? " is-open" : "")} onClick={() => setRunMenu(v => !v)}>
            <span className={"status-dot " + (running ? "run" : run.status)} />
            <span className="logs-run-label">{running ? "Running…" : run.t}</span>
            <span className="logs-run-meta mono">{running ? "—" : run.duration}</span>
            <Icon.Caret />
          </button>
          {runMenu && (
            <React.Fragment>
              <div className="dropdown-backdrop" onClick={() => setRunMenu(false)} />
              <div className="logs-run-menu">
                <div className="logs-run-menu-head mono">Recent runs</div>
                {RUN_HISTORY.map(r => (
                  <button key={r.id}
                    className={"logs-run-item" + (r.id === runId ? " is-current" : "")}
                    onClick={() => { setRunId(r.id); setRunMenu(false); }}>
                    <span className={"status-dot " + r.status} />
                    <div className="logs-run-item-meta">
                      <span className="logs-run-item-t">{r.t}</span>
                      <span className="logs-run-item-sub mono">{r.trigger} · {r.duration}</span>
                    </div>
                    <span className="logs-run-item-tokens mono">{r.tokens}</span>
                  </button>
                ))}
              </div>
            </React.Fragment>
          )}
        </div>
        <button className="icon-btn-sm" title="Download log"><Icon.Download /></button>
      </div>

      <div className="logs-stats">
        <div className="logs-stat">
          <span className="logs-stat-label mono">Duration</span>
          <span className="logs-stat-val">{running ? "—" : run.duration}</span>
        </div>
        <div className="logs-stat">
          <span className="logs-stat-label mono">Tokens</span>
          <span className="logs-stat-val mono">{run.tokens}</span>
        </div>
        <div className="logs-stat">
          <span className="logs-stat-label mono">Trigger</span>
          <span className="logs-stat-val">{run.trigger}</span>
        </div>
        <div className="logs-stat">
          <span className="logs-stat-label mono">Lines</span>
          <span className="logs-stat-val mono">{lines.length}</span>
        </div>
      </div>

      <div className="logs-toolbar">
        <div className="side-search compact">
          <Icon.Search />
          <input placeholder="Filter log lines…" value={q} onChange={(e) => setQ(e.target.value)} />
          {q && <button className="side-search-clear" onClick={() => setQ("")}><Icon.Plus style={{ transform: "rotate(45deg)" }} /></button>}
        </div>
        <div className="logs-levels">
          {["all", "info", "ok", "warn", "err"].map(l => (
            <button key={l} className={"logs-level-chip" + (level === l ? " active" : "") + " " + l}
              onClick={() => setLevel(l)}>{l.toUpperCase()}</button>
          ))}
        </div>
      </div>

      <div className="logs-stream">
        {filtered.length === 0 && (
          <div className="logs-empty">
            {lines.length === 0
              ? "No log lines for this run."
              : <React.Fragment>No matching lines. <button className="link-btn" onClick={() => { setQ(""); setLevel("all"); }}>Clear filters</button></React.Fragment>}
          </div>
        )}
        {filtered.map((l, i) => {
          const key = runId + ":" + i;
          const isOpen = expanded === key;
          return (
            <div key={key} className={"log-line " + l.lvl + (isOpen ? " is-open" : "")}
              onClick={() => setExpanded(isOpen ? null : key)}>
              <span className="log-time">{l.t}</span>
              <span className={"log-lvl " + l.lvl}>{l.lvl.toUpperCase()}</span>
              <span className="log-src">{l.src}</span>
              <span className="log-msg">{l.msg}</span>
              {isOpen && (
                <div className="log-detail mono">
                  {`source: ${l.src}\nlevel:  ${l.lvl}\ntime:   ${l.t}\nrun_id: ${runId}\nmessage:\n  ${l.msg}`}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ============ TEST ============
function TestPanel({ onRun }) {
  const [tests, setTests] = useP_s(INITIAL_TESTS);
  const [selectedId, setSelectedId] = useP_s(tests[0].id);
  const [mock, setMock] = useP_s(true);
  const [replay, setReplay] = useP_s(false);
  const [renameId, setRenameId] = useP_s(null);

  const t = tests.find(x => x.id === selectedId) || tests[0];

  const setT = (patch) => setTests(ts => ts.map(x => x.id === t.id ? { ...x, ...patch } : x));
  const setVar = (i, field, v) => setT({ vars: t.vars.map((row, idx) => idx === i ? { ...row, [field]: v } : row) });
  const addVar = () => setT({ vars: [...t.vars, { k: "", v: "" }] });
  const removeVar = (i) => setT({ vars: t.vars.filter((_, idx) => idx !== i) });

  const addTest = () => {
    const id = "t" + Date.now();
    const nt = { id, name: "Untitled scenario", desc: "", payload: "{}", vars: [], lastRun: null };
    setTests(ts => [...ts, nt]);
    setSelectedId(id);
    setRenameId(id);
  };
  const dupTest = () => {
    const id = "t" + Date.now();
    const nt = { ...t, id, name: t.name + " (copy)", lastRun: null };
    setTests(ts => [...ts, nt]);
    setSelectedId(id);
  };
  const delTest = () => {
    if (tests.length <= 1) return;
    setTests(ts => ts.filter(x => x.id !== t.id));
    setSelectedId(tests.find(x => x.id !== t.id).id);
  };

  return (
    <div className="test-panel">
      <div className="side-section-head">
        <div className="side-section-title">Saved scenarios</div>
        <button className="link-btn" onClick={addTest}><Icon.Plus /> New</button>
      </div>

      <div className="test-list">
        {tests.map(x => (
          <button key={x.id}
            className={"test-list-item" + (x.id === selectedId ? " is-current" : "")}
            onClick={() => setSelectedId(x.id)}>
            <span className={"status-dot " + (x.lastRun?.status || "draft")} />
            <span className="test-list-meta">
              {renameId === x.id ? (
                <input
                  className="test-list-name-input"
                  autoFocus
                  value={x.name}
                  onChange={(e) => setTests(ts => ts.map(y => y.id === x.id ? { ...y, name: e.target.value } : y))}
                  onBlur={() => setRenameId(null)}
                  onKeyDown={(e) => { if (e.key === "Enter") setRenameId(null); }}
                  onClick={(e) => e.stopPropagation()}
                />
              ) : (
                <span className="test-list-name">{x.name}</span>
              )}
              <span className="test-list-sub">{x.lastRun ? `Ran ${x.lastRun.t}` : "Never run"}</span>
            </span>
          </button>
        ))}
      </div>

      <div className="test-divider" />

      <div className="test-edit">
        <div className="test-edit-head">
          <input className="test-edit-name" value={t.name}
            onChange={(e) => setT({ name: e.target.value })}
            placeholder="Scenario name" />
          <button className="icon-btn-sm" onClick={dupTest} title="Duplicate"><Icon.Copy /></button>
          <button className="icon-btn-sm" onClick={delTest} title="Delete" disabled={tests.length <= 1}><Icon.Trash /></button>
        </div>

        <Field label="Description" hint="Optional">
          <input className="form-input" value={t.desc} onChange={(e) => setT({ desc: e.target.value })}
            placeholder="When does this scenario apply?" />
        </Field>

        <Field label="Trigger payload" hint="JSON">
          <textarea className="form-textarea mono" rows={8} value={t.payload}
            onChange={(e) => setT({ payload: e.target.value })} />
        </Field>

        <div className="field">
          <div className="field-label-row">
            <span className="field-label">Variables</span>
            <button className="link-btn" onClick={addVar}><Icon.Plus /> Add</button>
          </div>
          {t.vars.length === 0 && <div className="kv-empty">No variables set.</div>}
          <div className="kv-list">
            {t.vars.map((row, i) => (
              <div key={i} className="kv-row">
                <input className="kv-input mono" value={row.k} placeholder="KEY" onChange={(e) => setVar(i, "k", e.target.value)} />
                <span className="kv-eq">=</span>
                <input className="kv-input mono" value={row.v} placeholder="value" onChange={(e) => setVar(i, "v", e.target.value)} />
                <button className="icon-btn-sm" onClick={() => removeVar(i)} title="Remove"><Icon.Trash /></button>
              </div>
            ))}
          </div>
        </div>

        <div className="field">
          <span className="field-label">Options</span>
          <label className="test-check"><input type="checkbox" checked={mock} onChange={(e) => setMock(e.target.checked)} /> Mock external calls</label>
          <label className="test-check"><input type="checkbox" checked={replay} onChange={(e) => setReplay(e.target.checked)} /> Replay last successful run</label>
        </div>
      </div>

      <div className="test-foot">
        <button className="btn btn-primary test-run-btn" onClick={onRun}>
          <Icon.Bolt /> Run scenario
        </button>
      </div>
    </div>
  );
}

Object.assign(window, { InspectorPanel, CopilotPanel, LibraryPanel, LogsPanel, TestPanel });
