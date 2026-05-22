// fuse v2 — view implementations
const { useState: useS_v } = React;

// shared subcomponents
function Sparkline({ data, color = "currentColor" }) {
  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;
  const w = 70, h = 28;
  const pts = data.map((v, i) => {
    const x = (i / (data.length - 1)) * w;
    const y = h - ((v - min) / range) * (h - 4) - 2;
    return `${x},${y}`;
  }).join(" ");
  return (
    <svg viewBox={`0 0 ${w} ${h}`} fill="none" className="stat-spark">
      <polyline points={pts} stroke={color} strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round" opacity="0.9"/>
      <circle cx={w} cy={h - ((data[data.length-1] - min) / range) * (h - 4) - 2} r="1.8" fill={color}/>
    </svg>
  );
}

function PanelHead({ icon, title, count, action }) {
  return (
    <div className="panel-head">
      <div className="panel-title">{icon} {title}{count && <span className="count">{count}</span>}</div>
      {action && <div className="panel-actions">{action}</div>}
    </div>
  );
}

// ============ HOME ============
function HomeView({ onOpen, goTo }) {
  const stats = [
    { label: "Runs today", value: "1,284", unit: "", delta: "+18%", deltaDir: "up", spark: [4,5,3,6,4,7,8,6,9,11,9,12], icon: <Icon.Activity /> },
    { label: "Success rate", value: "99.2", unit: "%", delta: "+0.4pp", deltaDir: "up", spark: [98,97.8,98.2,98.5,98.6,99,99.1,99.2,99.1,99.2,99.2,99.2], icon: <Icon.Check /> },
    { label: "Time saved", value: "14.2", unit: "hr", delta: "+2.1hr", deltaDir: "up", spark: [6,7,8,8,9,10,11,12,13,13,14,14.2], icon: <Icon.Clock /> },
    { label: "Active steps", value: "312", unit: "", delta: "-4", deltaDir: "down", spark: [340,338,336,334,330,324,320,318,316,314,313,312], icon: <Icon.Layers /> },
  ];

  const runs = [
    { status: "ok",  name: "Stripe refund — Slack approval", trigger: "stripe.charge.refunded", duration: "1.4s",  ago: "2m ago" },
    { status: "ok",  name: "Lead enrichment — Clearbit → HubSpot", trigger: "hubspot.contact.created", duration: "3.1s",  ago: "4m ago" },
    { status: "run", name: "Inbound RFP classifier", trigger: "imap.inbox.new", duration: "running", ago: "now" },
    { status: "ok",  name: "Daily brief from Linear + GitHub", trigger: "schedule.daily", duration: "8.7s",  ago: "1h ago" },
    { status: "err", name: "Notion → Airtable nightly sync", trigger: "schedule.0_2_*_*_*", duration: "12.4s", ago: "2h ago" },
    { status: "ok",  name: "Invoice triage agent", trigger: "gmail.label.invoice", duration: "5.9s",  ago: "3h ago" },
    { status: "warn",name: "Support ticket auto-tagger", trigger: "zendesk.ticket.new", duration: "2.2s",  ago: "4h ago" },
    { status: "ok",  name: "Weekly metrics digest", trigger: "schedule.weekly", duration: "11.0s", ago: "5h ago" },
  ];

  const schedule = [
    { time: "14:30", name: "Weekly metrics digest", sub: "linear · github · stripe" },
    { time: "16:00", name: "Churn-risk watchlist refresh", sub: "agent · 6 sources" },
    { time: "18:00", name: "EOD pager rotation handoff", sub: "pagerduty · slack" },
    { time: "02:00", name: "Notion → Airtable sync", sub: "scheduled · last failed" },
  ];

  const connections = [
    { id: "stripe", name: "Stripe", sub: "12 endpoints · 4 webhooks", state: "ok" },
    { id: "slack", name: "Slack",  sub: "3 workspaces", state: "ok" },
    { id: "linear", name: "Linear", sub: "fuse-engineering", state: "ok" },
    { id: "notion", name: "Notion", sub: "token expires in 4d", state: "warn" },
    { id: "hub", name: "HubSpot", sub: "auth failed · re-link", state: "err" },
  ];

  return (
    <div className="body">
      <div className="greeting-row">
        <div className="greeting">
          <span className="eyebrow"><span className="dot" /> All systems operational · Wed, May 21</span>
          <h1>Good evening, Mahesh<span style={{ color: "var(--accent)" }}>.</span></h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary" onClick={() => goTo("connections")}><Icon.Plug /> Connect app</button>
          <button className="btn btn-primary" onClick={() => onOpen({ id: "new", title: "Untitled automation" })}>
            <Icon.Plus /> New automation
          </button>
        </div>
      </div>

      <div className="stats">
        {stats.map((s, i) => (
          <div key={i} className="stat">
            <span className="stat-label">{s.icon} {s.label}</span>
            <span className="stat-value">{s.value}{s.unit && <span className="unit">{s.unit}</span>}</span>
            <span className={"stat-delta " + s.deltaDir}>
              {s.deltaDir === "up" ? "↑" : s.deltaDir === "down" ? "↓" : "—"} {s.delta}
            </span>
            <Sparkline data={s.spark} color={s.deltaDir === "down" ? "oklch(0.70 0.18 22)" : "oklch(0.78 0.14 145)"} />
          </div>
        ))}
      </div>

      <div className="prompt-card">
        <textarea placeholder="Describe an automation. fuse drafts the flow, wires the connectors, and tests it before shipping."></textarea>
        <div className="prompt-foot">
          <div className="prompt-tools">
            <button className="tool-btn" title="Attach"><Icon.Plus /></button>
            <div className="mode-toggle">
              <button className="active"><Icon.Flow /> Flow</button>
              <button><Icon.Spark /> Agent</button>
            </div>
          </div>
          <div className="prompt-tools">
            <button className="tool-btn" title="Connections"><Icon.Plug /></button>
            <div className="model-pill">
              <span className="spark"><Icon.Spark style={{ width: 12, height: 12 }} /></span>
              Filament 2
              <Icon.Caret style={{ width: 11, height: 11, color: "var(--text-mute)" }} />
            </div>
            <button className="tool-btn" title="Dictate"><Icon.Mic /></button>
            <button className="send-btn" onClick={() => onOpen({ id: "new", title: "Untitled automation" })}>
              <Icon.ArrowUp />
            </button>
          </div>
        </div>
      </div>

      <div className="split">
        <div className="panel">
          <PanelHead icon={<Icon.Activity />} title="Recent runs" count="1,284 today"
            action={<button className="link-btn" onClick={() => goTo("runs")}>View all <Icon.CaretRight /></button>} />
          <div className="runs">
            {runs.map((r, i) => (
              <div key={i} className="run-row" onClick={() => onOpen({ id: "run-" + i, title: r.name })}>
                <span className={"status-dot " + r.status} />
                <span className="run-name">{r.name}</span>
                <span className="run-trigger"><Icon.Bolt />{r.trigger}</span>
                <span className="run-meta">{r.duration}</span>
                <span className="run-meta">{r.ago}</span>
                <span className="caret"><Icon.CaretRight /></span>
              </div>
            ))}
          </div>
        </div>

        <div className="side-stack">
          <div className="panel">
            <PanelHead icon={<Icon.Clock />} title="Next 12 hours"
              action={<button className="link-btn">All <Icon.CaretRight /></button>} />
            {schedule.map((s, i) => (
              <div key={i} className="schedule-row">
                <span className="schedule-time">{s.time}</span>
                <span className="schedule-meta">
                  <span className="schedule-name">{s.name}</span>
                  <span className="schedule-sub">{s.sub}</span>
                </span>
              </div>
            ))}
          </div>

          <div className="panel">
            <PanelHead icon={<Icon.Plug />} title="Connections" count="18 active"
              action={<button className="link-btn" onClick={() => goTo("connections")}>Manage <Icon.CaretRight /></button>} />
            {connections.map((c, i) => (
              <div key={i} className="conn-row">
                <span className={"conn-icon " + c.id}>{c.name.slice(0, 2)}</span>
                <span className="conn-meta">
                  <span className="conn-name">{c.name}</span>
                  <span className="conn-sub">{c.sub}</span>
                </span>
                <span className={"conn-state " + c.state}>{c.state}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ============ AUTOMATIONS ============
function AutomationsView({ onOpen }) {
  const [filter, setFilter] = useS_v("all");
  const all = [
    { id: 1, name: "Stripe refund — Slack approval", kind: "flow",     status: "active", runs: "1,284", last: "2m ago",  owner: "Mahesh" },
    { id: 2, name: "Lead enrichment — Clearbit → HubSpot", kind: "flow", status: "active", runs: "812",   last: "4m ago",  owner: "Mahesh" },
    { id: 3, name: "Daily brief from Linear + GitHub", kind: "agent",  status: "active", runs: "302",   last: "1h ago",  owner: "Priya" },
    { id: 4, name: "Inbound RFP classifier", kind: "agent",            status: "active", runs: "489",   last: "now",     owner: "Mahesh" },
    { id: 5, name: "Notion → Airtable nightly sync", kind: "schedule", status: "error",  runs: "67",    last: "2h ago",  owner: "Priya" },
    { id: 6, name: "Invoice triage agent", kind: "agent",              status: "active", runs: "201",   last: "3h ago",  owner: "Mahesh" },
    { id: 7, name: "Support ticket auto-tagger", kind: "agent",        status: "active", runs: "1,012", last: "4h ago",  owner: "Devon" },
    { id: 8, name: "Weekly metrics digest", kind: "schedule",          status: "active", runs: "52",    last: "5h ago",  owner: "Priya" },
    { id: 9, name: "Pager rotation handoff", kind: "flow",             status: "paused", runs: "146",   last: "1d ago",  owner: "Devon" },
    { id: 10,name: "Churn-risk watchlist", kind: "agent",              status: "active", runs: "97",    last: "1d ago",  owner: "Priya" },
    { id: 11,name: "Contract redline assistant", kind: "agent",        status: "draft",  runs: "—",     last: "—",       owner: "Mahesh" },
  ];

  const filtered = filter === "all" ? all :
                   filter === "paused" ? all.filter(a => a.status === "paused") :
                   all.filter(a => a.kind === filter);

  const filters = [
    { id: "all", label: "All", count: all.length },
    { id: "flow", label: "Flows", count: all.filter(a => a.kind === "flow").length },
    { id: "agent", label: "Agents", count: all.filter(a => a.kind === "agent").length },
    { id: "schedule", label: "Scheduled", count: all.filter(a => a.kind === "schedule").length },
    { id: "paused", label: "Paused", count: all.filter(a => a.status === "paused").length },
  ];

  return (
    <div className="body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace · 47 total</span>
          <h1>Automations</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icon.Doc /> Import</button>
          <button className="btn btn-primary" onClick={() => onOpen({ id: "new", title: "Untitled automation" })}>
            <Icon.Plus /> New automation
          </button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          {filters.map(f => (
            <button key={f.id} className={"filter-tab" + (filter === f.id ? " active" : "")} onClick={() => setFilter(f.id)}>
              {f.label} <span className="filter-count">{f.count}</span>
            </button>
          ))}
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icon.Search />
            <input placeholder="Filter by name, trigger, or owner" />
          </div>
          <button className="icon-btn" title="Sort"><Icon.Sort /></button>
        </div>
      </div>

      <div className="panel">
        <div className="table">
          <div className="table-head">
            <span></span>
            <span>Name</span>
            <span>Kind</span>
            <span>Runs</span>
            <span>Last run</span>
            <span>Owner</span>
            <span>Status</span>
            <span></span>
          </div>
          {filtered.map(a => (
            <div key={a.id} className="table-row" onClick={() => onOpen({ id: "a-" + a.id, title: a.name })}>
              <span className={"status-dot " + (a.status === "error" ? "err" : a.status === "paused" ? "warn" : a.status === "draft" ? "draft" : "ok")} />
              <span className="row-name">{a.name}</span>
              <span className="row-kind">
                {a.kind === "agent" ? <Icon.Spark /> : a.kind === "schedule" ? <Icon.Clock /> : <Icon.Flow />}
                {a.kind}
              </span>
              <span className="row-mono">{a.runs}</span>
              <span className="row-mono">{a.last}</span>
              <span className="row-owner">{a.owner}</span>
              <span className={"status-pill " + (a.status === "error" ? "err" : a.status === "paused" ? "warn" : a.status === "draft" ? "draft" : "ok")}>
                {a.status}
              </span>
              <span className="caret"><Icon.CaretRight /></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============ RUNS ============
function RunsView({ onOpen }) {
  const [filter, setFilter] = useS_v("all");
  const runs = [
    { id: 1, status: "ok",   name: "Stripe refund — Slack approval", trigger: "stripe.charge.refunded", started: "14:42:01", duration: "1.4s" },
    { id: 2, status: "ok",   name: "Lead enrichment — Clearbit → HubSpot", trigger: "hubspot.contact.created", started: "14:39:18", duration: "3.1s" },
    { id: 3, status: "run",  name: "Inbound RFP classifier", trigger: "imap.inbox.new", started: "14:38:44", duration: "running" },
    { id: 4, status: "ok",   name: "Daily brief from Linear + GitHub", trigger: "schedule.daily", started: "13:30:00", duration: "8.7s" },
    { id: 5, status: "err",  name: "Notion → Airtable nightly sync", trigger: "schedule.0_2_*_*_*", started: "02:00:14", duration: "12.4s" },
    { id: 6, status: "ok",   name: "Invoice triage agent", trigger: "gmail.label.invoice", started: "11:14:09", duration: "5.9s" },
    { id: 7, status: "warn", name: "Support ticket auto-tagger", trigger: "zendesk.ticket.new", started: "10:02:33", duration: "2.2s" },
    { id: 8, status: "ok",   name: "Weekly metrics digest", trigger: "schedule.weekly", started: "09:00:00", duration: "11.0s" },
    { id: 9, status: "ok",   name: "Stripe refund — Slack approval", trigger: "stripe.charge.refunded", started: "08:51:22", duration: "1.6s" },
    { id: 10,status: "err",  name: "Pager rotation handoff", trigger: "schedule.0_18_*_*_5", started: "08:30:01", duration: "0.4s" },
    { id: 11,status: "ok",   name: "Lead enrichment — Clearbit → HubSpot", trigger: "hubspot.contact.created", started: "08:12:48", duration: "3.4s" },
    { id: 12,status: "ok",   name: "Churn-risk watchlist", trigger: "schedule.daily", started: "06:00:00", duration: "22.1s" },
  ];
  const filtered = filter === "all" ? runs : runs.filter(r => r.status === filter);
  const counts = {
    all: runs.length,
    ok: runs.filter(r => r.status === "ok").length,
    err: runs.filter(r => r.status === "err").length,
    warn: runs.filter(r => r.status === "warn").length,
    run: runs.filter(r => r.status === "run").length,
  };

  return (
    <div className="body">
      <div className="page-head">
        <div>
          <span className="eyebrow"><span className="dot" />Live · streaming</span>
          <h1>Runs</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icon.Download /> Export</button>
          <button className="btn btn-secondary"><Icon.Pause /> Pause stream</button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          <button className={"filter-tab" + (filter === "all" ? " active" : "")} onClick={() => setFilter("all")}>All <span className="filter-count">{counts.all}</span></button>
          <button className={"filter-tab" + (filter === "ok" ? " active" : "")} onClick={() => setFilter("ok")}>Success <span className="filter-count">{counts.ok}</span></button>
          <button className={"filter-tab" + (filter === "err" ? " active" : "")} onClick={() => setFilter("err")}>Failed <span className="filter-count">{counts.err}</span></button>
          <button className={"filter-tab" + (filter === "warn" ? " active" : "")} onClick={() => setFilter("warn")}>Warning <span className="filter-count">{counts.warn}</span></button>
          <button className={"filter-tab" + (filter === "run" ? " active" : "")} onClick={() => setFilter("run")}>Running <span className="filter-count">{counts.run}</span></button>
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icon.Search />
            <input placeholder="Filter runs" />
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="table runs-table">
          <div className="table-head">
            <span></span>
            <span>Automation</span>
            <span>Trigger</span>
            <span>Started</span>
            <span>Duration</span>
            <span></span>
          </div>
          {filtered.map(r => (
            <div key={r.id} className="table-row" onClick={() => onOpen({ id: "run-" + r.id, title: r.name })}>
              <span className={"status-dot " + r.status} />
              <span className="row-name">{r.name}</span>
              <span className="run-trigger"><Icon.Bolt />{r.trigger}</span>
              <span className="row-mono">{r.started}</span>
              <span className="row-mono">{r.duration}</span>
              <span className="caret"><Icon.CaretRight /></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============ CONNECTIONS ============
function ConnectionsView() {
  const all = [
    { id: "stripe", name: "Stripe", sub: "Payments & billing", state: "ok", endpoints: 12, last: "2m ago" },
    { id: "slack", name: "Slack", sub: "Team messaging", state: "ok", endpoints: 4, last: "just now" },
    { id: "linear", name: "Linear", sub: "Issue tracking", state: "ok", endpoints: 6, last: "5m ago" },
    { id: "notion", name: "Notion", sub: "Knowledge base", state: "warn", endpoints: 3, last: "1h ago" },
    { id: "hub", name: "HubSpot", sub: "CRM", state: "err", endpoints: 8, last: "auth failed" },
    { id: "stripe", name: "GitHub", sub: "Code & releases", state: "ok", endpoints: 9, last: "12m ago" },
    { id: "slack", name: "Zendesk", sub: "Support tickets", state: "ok", endpoints: 5, last: "1m ago" },
    { id: "linear", name: "Airtable", sub: "Operational data", state: "ok", endpoints: 11, last: "3m ago" },
    { id: "notion", name: "PagerDuty", sub: "On-call", state: "ok", endpoints: 2, last: "30m ago" },
  ];
  return (
    <div className="body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace · 18 active</span>
          <h1>Connections</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icon.Doc /> Audit log</button>
          <button className="btn btn-primary"><Icon.Plus /> Connect app</button>
        </div>
      </div>

      <div className="conn-grid">
        {all.map((c, i) => (
          <div key={i} className="conn-card">
            <div className="conn-card-head">
              <span className={"conn-icon " + c.id}>{c.name.slice(0, 2)}</span>
              <span className={"conn-state " + c.state}>{c.state}</span>
            </div>
            <div className="conn-card-body">
              <div className="conn-card-name">{c.name}</div>
              <div className="conn-card-sub">{c.sub}</div>
            </div>
            <div className="conn-card-foot">
              <span>{c.endpoints} endpoints</span>
              <span>{c.last}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============ TEMPLATES ============
function TemplatesView({ onOpen }) {
  const cats = ["All", "Revenue ops", "Engineering", "Inbox", "Reporting"];
  const tpl = [
    { idx: "01", label: "Revenue ops", title: "Stripe failure recovery loop", kind: "Flow", steps: 7, bg: "inspo-bg-1" },
    { idx: "02", label: "Inbox", title: "Inbound RFP triage agent", kind: "Agent", steps: 5, bg: "inspo-bg-2" },
    { idx: "03", label: "Engineering", title: "Weekly Linear → Notion digest", kind: "Scheduled", steps: 4, bg: "inspo-bg-3" },
    { idx: "04", label: "Reporting", title: "Daily revenue snapshot to Slack", kind: "Scheduled", steps: 6, bg: "inspo-bg-1" },
    { idx: "05", label: "Engineering", title: "PagerDuty incident → war room", kind: "Flow", steps: 9, bg: "inspo-bg-2" },
    { idx: "06", label: "Inbox", title: "Auto-classify support emails", kind: "Agent", steps: 4, bg: "inspo-bg-3" },
  ];
  return (
    <div className="body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Curated · by fuse team</span>
          <h1>Templates</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icon.Doc /> Submit one</button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          {cats.map((c, i) => (
            <button key={c} className={"filter-tab" + (i === 0 ? " active" : "")}>{c}</button>
          ))}
        </div>
      </div>

      <div className="tpl-grid">
        {tpl.map((c, i) => (
          <div key={i} className="inspo-card" onClick={() => onOpen({ id: "t-" + i, title: c.title })}>
            <div className={"inspo-art " + c.bg}>
              <div className="index">{c.idx}</div>
              <div className="inspo-mock">
                <div className="bar" />
                <div className="body-mock" />
              </div>
              <div className="label">{c.label}</div>
            </div>
            <div className="inspo-meta">
              <div className="inspo-meta-title">{c.title}</div>
              <div className="inspo-meta-row">
                <span><Icon.Flow /> {c.kind}</span>
                <span>{c.steps} steps</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============ LOGS ============
function LogsView() {
  const lines = [
    { t: "14:42:01.218", lvl: "ok",   src: "stripe.refund",     msg: "ch_3O9XQ1 — webhook received, signature verified" },
    { t: "14:42:01.305", lvl: "info", src: "stripe.refund",     msg: "→ slack.chat.postMessage #revenue with approval buttons" },
    { t: "14:42:01.620", lvl: "ok",   src: "stripe.refund",     msg: "completed in 1.4s · 2 steps" },
    { t: "14:39:18.014", lvl: "info", src: "hubspot.enrich",    msg: "contact 30201 — calling clearbit.person.find" },
    { t: "14:39:18.412", lvl: "warn", src: "clearbit",          msg: "rate limit · 87/100 in current window" },
    { t: "14:39:21.108", lvl: "ok",   src: "hubspot.enrich",    msg: "merged 14 fields into contact 30201" },
    { t: "14:38:44.001", lvl: "info", src: "imap.rfp",          msg: "new message from procurement@acme.co · subject contains 'RFP'" },
    { t: "14:38:44.802", lvl: "info", src: "imap.rfp",          msg: "agent running · model=filament-2" },
    { t: "13:30:00.000", lvl: "info", src: "schedule.daily",    msg: "trigger fired — running 'Daily brief'" },
    { t: "13:30:08.703", lvl: "ok",   src: "schedule.daily",    msg: "completed in 8.7s · 4 steps" },
    { t: "02:00:14.221", lvl: "err",  src: "notion.airtable",   msg: "AirtableAuthError: token rotation required" },
    { t: "02:00:14.222", lvl: "err",  src: "notion.airtable",   msg: "step 3 failed · retry exhausted (3/3)" },
    { t: "11:14:09.991", lvl: "info", src: "gmail.invoice",     msg: "label matched · 1 attachment" },
    { t: "11:14:15.444", lvl: "ok",   src: "gmail.invoice",     msg: "PDF parsed · vendor=Linear · amount=$420.00" },
    { t: "10:02:33.500", lvl: "warn", src: "zendesk.tag",       msg: "low-confidence classification · routed to human" },
  ];
  return (
    <div className="body">
      <div className="page-head">
        <div>
          <span className="eyebrow"><span className="dot" />Live tail · last 60 min</span>
          <h1>Logs</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icon.Download /> Download</button>
          <button className="btn btn-secondary"><Icon.Pause /> Pause</button>
        </div>
      </div>

      <div className="panel logs-panel">
        <div className="log-toolbar">
          <div className="filter-tabs">
            <button className="filter-tab active">All</button>
            <button className="filter-tab">Errors</button>
            <button className="filter-tab">Warnings</button>
            <button className="filter-tab">Info</button>
          </div>
          <div className="cmd-search inline-search" style={{ maxWidth: 280 }}>
            <Icon.Search />
            <input placeholder="grep" />
          </div>
        </div>
        <div className="log-stream">
          {lines.map((l, i) => (
            <div key={i} className={"log-line " + l.lvl}>
              <span className="log-time">{l.t}</span>
              <span className={"log-lvl " + l.lvl}>{l.lvl.toUpperCase()}</span>
              <span className="log-src">{l.src}</span>
              <span className="log-msg">{l.msg}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { HomeView, AutomationsView, RunsView, ConnectionsView, TemplatesView, LogsView });
