// fuse v2 — data views (Tables, Files, Knowledge, Variables, Schedules)
const { useState: useS_d } = React;

// ============ TABLES ============
function TablesView({ onOpen }) {
  const tables = [
    { name: "customer_lookup",   rows: "12,481", cols: 9,  source: "stripe + hubspot", updated: "2m ago",  owner: "Mahesh" },
    { name: "refund_log",        rows: "1,284",  cols: 6,  source: "stripe.refund",    updated: "2m ago",  owner: "Mahesh" },
    { name: "rfp_classifications",rows: "489",   cols: 11, source: "rfp agent",        updated: "5m ago",  owner: "Priya" },
    { name: "invoice_vendors",   rows: "201",    cols: 7,  source: "invoice agent",    updated: "3h ago",  owner: "Mahesh" },
    { name: "churn_signals",     rows: "97",     cols: 14, source: "churn agent",      updated: "1d ago",  owner: "Priya" },
    { name: "pager_history",     rows: "342",    cols: 8,  source: "pagerduty",        updated: "1d ago",  owner: "Devon" },
    { name: "weekly_metrics",    rows: "52",     cols: 22, source: "metrics digest",   updated: "5h ago",  owner: "Priya" },
    { name: "contract_redlines", rows: "18",     cols: 12, source: "redline agent",    updated: "2d ago",  owner: "Mahesh" },
  ];
  return (
    <div className="body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Data · 8 tables · 14,872 rows</span>
          <h1>Tables</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icon.Doc /> Import CSV</button>
          <button className="btn btn-primary"><Icon.Plus /> New table</button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          <button className="filter-tab active">All <span className="filter-count">{tables.length}</span></button>
          <button className="filter-tab">Live</button>
          <button className="filter-tab">Static</button>
          <button className="filter-tab">Archived</button>
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icon.Search />
            <input placeholder="Filter tables" />
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="table table-tables">
          <div className="table-head">
            <span></span>
            <span>Name</span>
            <span>Rows</span>
            <span>Cols</span>
            <span>Source</span>
            <span>Updated</span>
            <span>Owner</span>
            <span></span>
          </div>
          {tables.map((t, i) => (
            <div key={i} className="table-row" onClick={() => onOpen({ id: "tbl-" + i, title: t.name })}>
              <span className="row-leading"><Icon.Table /></span>
              <span className="row-name mono">{t.name}</span>
              <span className="row-mono">{t.rows}</span>
              <span className="row-mono">{t.cols}</span>
              <span className="row-owner">{t.source}</span>
              <span className="row-mono">{t.updated}</span>
              <span className="row-owner">{t.owner}</span>
              <span className="caret"><Icon.CaretRight /></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============ FILES ============
function FilesView({ onOpen }) {
  const files = [
    { name: "RFP_acme_2026Q2.pdf", ext: "pdf", size: "1.2 MB", uploaded: "14:38", source: "rfp agent" },
    { name: "invoice_linear_apr.pdf", ext: "pdf", size: "84 KB", uploaded: "11:14", source: "gmail invoice" },
    { name: "stripe_export_may.csv", ext: "csv", size: "412 KB", uploaded: "09:00", source: "stripe.export" },
    { name: "contract_acme_v3.docx", ext: "doc", size: "2.4 MB", uploaded: "Mon 16:02", source: "redline agent" },
    { name: "pager_log_2026.json", ext: "json", size: "92 KB", uploaded: "Mon 14:12", source: "pagerduty" },
    { name: "churn_signals_dump.parquet", ext: "data", size: "3.8 MB", uploaded: "Sun 22:00", source: "churn agent" },
    { name: "screenshot-rfp-form.png", ext: "img", size: "780 KB", uploaded: "Sun 18:31", source: "Mahesh" },
    { name: "metrics_template.xlsx", ext: "xls", size: "210 KB", uploaded: "Sat 09:00", source: "metrics digest" },
  ];
  return (
    <div className="body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace · 124 files · 412 MB used</span>
          <h1>Files</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icon.Folder /> New folder</button>
          <button className="btn btn-primary"><Icon.Plus /> Upload</button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          <button className="filter-tab active">All</button>
          <button className="filter-tab">Generated</button>
          <button className="filter-tab">Uploaded</button>
          <button className="filter-tab">Attachments</button>
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icon.Search />
            <input placeholder="Filter files" />
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="table table-files">
          <div className="table-head">
            <span></span>
            <span>Name</span>
            <span>Size</span>
            <span>Source</span>
            <span>Uploaded</span>
            <span></span>
          </div>
          {files.map((f, i) => (
            <div key={i} className="table-row" onClick={() => onOpen({ id: "file-" + i, title: f.name })}>
              <span className={"file-icon " + f.ext}>{f.ext.toUpperCase()}</span>
              <span className="row-name">{f.name}</span>
              <span className="row-mono">{f.size}</span>
              <span className="row-owner">{f.source}</span>
              <span className="row-mono">{f.uploaded}</span>
              <span className="caret"><Icon.CaretRight /></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============ KNOWLEDGE ============
function KnowledgeView({ onOpen }) {
  const sources = [
    { name: "Refund policy",        kind: "doc",    items: 1,   tokens: "2.4k",  used: 14, updated: "Apr 2",  state: "indexed" },
    { name: "RFP playbook",         kind: "doc",    items: 1,   tokens: "11.8k", used: 42, updated: "Apr 12", state: "indexed" },
    { name: "Help center",          kind: "site",   items: 318, tokens: "1.2M",  used: 86, updated: "1h ago", state: "syncing" },
    { name: "Linear specs",         kind: "linear", items: 412, tokens: "840k",  used: 31, updated: "12m ago",state: "indexed" },
    { name: "Engineering notes",    kind: "notion", items: 96,  tokens: "320k",  used: 22, updated: "3h ago", state: "indexed" },
    { name: "Vendor catalog",       kind: "csv",    items: 1,   tokens: "48k",   used: 9,  updated: "Mon",    state: "indexed" },
    { name: "Slack #revenue",       kind: "slack",  items: 1200,tokens: "2.8M",  used: 12, updated: "2m ago", state: "syncing" },
    { name: "Onboarding script",    kind: "doc",    items: 1,   tokens: "5.6k",  used: 4,  updated: "Mar 30", state: "stale" },
  ];
  const kindIcon = (k) => k === "site" ? <Icon.Globe /> : k === "slack" ? <Icon.Slack /> : k === "notion" ? <Icon.NotionDoc /> : k === "linear" ? <Icon.Square /> : k === "csv" ? <Icon.Table /> : <Icon.Doc />;
  return (
    <div className="body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Retrieval · 4.2M tokens indexed</span>
          <h1>Knowledge base</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icon.Plug /> Add source</button>
          <button className="btn btn-primary"><Icon.Plus /> Upload document</button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          <button className="filter-tab active">All <span className="filter-count">{sources.length}</span></button>
          <button className="filter-tab">Documents</button>
          <button className="filter-tab">Live sources</button>
          <button className="filter-tab">Stale</button>
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icon.Search />
            <input placeholder="Search sources" />
          </div>
        </div>
      </div>

      <div className="kn-grid">
        {sources.map((s, i) => (
          <div key={i} className="kn-card" onClick={() => onOpen({ id: "kn-" + i, title: s.name })}>
            <div className="kn-head">
              <span className="kn-kind">{kindIcon(s.kind)}</span>
              <span className={"kn-state " + s.state}>{s.state}</span>
            </div>
            <div className="kn-body">
              <div className="kn-name">{s.name}</div>
              <div className="kn-meta-row">
                <span>{s.items === 1 ? "1 item" : `${s.items} items`}</span>
                <span>·</span>
                <span>{s.tokens} tokens</span>
              </div>
            </div>
            <div className="kn-foot">
              <div className="kn-usage">
                <div className="kn-usage-bar"><span style={{ width: Math.min(s.used, 100) + "%" }} /></div>
                <span className="kn-usage-num">{s.used} retrievals</span>
              </div>
              <span className="kn-updated">{s.updated}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ============ VARIABLES ============
function VariablesView() {
  const [reveal, setReveal] = useS_d({});
  const env = [
    { key: "STRIPE_SECRET_KEY",     val: "sk_live_51N8········PvK4", scope: "production", updated: "Apr 12" },
    { key: "STRIPE_WEBHOOK_SECRET", val: "whsec_8K7g········nQ2X",  scope: "production", updated: "Apr 12" },
    { key: "SLACK_BOT_TOKEN",       val: "xoxb-2840········ZJ9P",   scope: "production", updated: "Mar 20" },
    { key: "HUBSPOT_PAT",           val: "pat-na1-········cQ7T",    scope: "production", updated: "May 02" },
    { key: "NOTION_TOKEN",          val: "secret_kL2········vR8M",  scope: "production", updated: "Apr 29" },
    { key: "DEFAULT_APPROVER",      val: "mahesh@fuse.io",          scope: "shared",     updated: "Apr 02", plain: true },
    { key: "REFUND_LIMIT_USD",      val: "500",                     scope: "shared",     updated: "Apr 02", plain: true },
    { key: "ON_CALL_CHANNEL",       val: "#oncall-revenue",         scope: "shared",     updated: "Mar 30", plain: true },
  ];
  return (
    <div className="body">
      <div className="page-head">
        <div>
          <span className="eyebrow">Workspace · 18 variables · 5 secrets</span>
          <h1>Variables</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icon.Download /> Export</button>
          <button className="btn btn-primary"><Icon.Plus /> New variable</button>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-tabs">
          <button className="filter-tab active">All</button>
          <button className="filter-tab">Secrets</button>
          <button className="filter-tab">Shared</button>
          <button className="filter-tab">Production</button>
        </div>
        <div className="filter-tools">
          <div className="cmd-search inline-search">
            <Icon.Search />
            <input placeholder="Filter by key" />
          </div>
        </div>
      </div>

      <div className="panel">
        <div className="table table-vars">
          <div className="table-head">
            <span>Key</span>
            <span>Value</span>
            <span>Scope</span>
            <span>Updated</span>
            <span></span>
          </div>
          {env.map((v, i) => (
            <div key={i} className="table-row">
              <span className="row-name mono">{v.key}</span>
              <span className="row-mono var-val">
                {v.plain || reveal[i] ? v.val : v.val.replace(/[^·]/g, "•")}
                {!v.plain && (
                  <button className="reveal-btn" onClick={(e) => { e.stopPropagation(); setReveal(r => ({ ...r, [i]: !r[i] })); }}>
                    {reveal[i] ? <Icon.EyeOff /> : <Icon.Eye />}
                  </button>
                )}
              </span>
              <span className={"status-pill " + (v.scope === "production" ? "warn" : "ok")}>{v.scope}</span>
              <span className="row-mono">{v.updated}</span>
              <span className="caret"><Icon.More /></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ============ SCHEDULES ============
function SchedulesView({ onOpen }) {
  const sched = [
    { name: "Daily brief from Linear + GitHub", cron: "0 9 * * *",  next: "Tomorrow 09:00", last: "8.7s · ok",  state: "active" },
    { name: "Notion → Airtable nightly sync",   cron: "0 2 * * *",  next: "Tomorrow 02:00", last: "12.4s · err", state: "error" },
    { name: "Weekly metrics digest",            cron: "0 9 * * MON",next: "Mon 09:00",      last: "11.0s · ok", state: "active" },
    { name: "EOD pager rotation handoff",       cron: "0 18 * * FRI",next:"Fri 18:00",      last: "1.2s · ok",  state: "active" },
    { name: "Churn-risk watchlist refresh",     cron: "0 6 * * *",  next: "Tomorrow 06:00", last: "22.1s · ok", state: "active" },
    { name: "Monthly billing reconciliation",   cron: "0 0 1 * *",  next: "Jun 01 00:00",   last: "—",          state: "paused" },
  ];
  return (
    <div className="body">
      <div className="page-head">
        <div>
          <span className="eyebrow"><span className="dot" />6 schedules · timezone America/New_York</span>
          <h1>Schedules</h1>
        </div>
        <div className="btn-group">
          <button className="btn btn-secondary"><Icon.Clock /> Timezone</button>
          <button className="btn btn-primary"><Icon.Plus /> New schedule</button>
        </div>
      </div>

      <div className="panel">
        <div className="table table-sched">
          <div className="table-head">
            <span></span>
            <span>Name</span>
            <span>Cron</span>
            <span>Next run</span>
            <span>Last run</span>
            <span>State</span>
            <span></span>
          </div>
          {sched.map((s, i) => (
            <div key={i} className="table-row" onClick={() => onOpen({ id: "sch-" + i, title: s.name })}>
              <span className={"status-dot " + (s.state === "error" ? "err" : s.state === "paused" ? "warn" : "ok")} />
              <span className="row-name">{s.name}</span>
              <span className="row-mono">{s.cron}</span>
              <span className="row-mono">{s.next}</span>
              <span className="row-mono">{s.last}</span>
              <span className={"status-pill " + (s.state === "error" ? "err" : s.state === "paused" ? "warn" : "ok")}>{s.state}</span>
              <span className="caret"><Icon.CaretRight /></span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

Object.assign(window, { TablesView, FilesView, KnowledgeView, VariablesView, SchedulesView });
