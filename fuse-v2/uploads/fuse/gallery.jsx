// Gallery screen for fuse
const { useState } = React;

function Gallery({ onOpenProject }) {
  const [tab, setTab] = useState("mine");
  const [activeId, setActiveId] = useState(null);

  const projects = {
    Recent: [
      { id: "p1", title: "Untitled draft", date: "May 20, 2026", kind: "phone", thumb: "a" },
      { id: "p2", title: "Atlas — design tokens", date: "May 20, 2026", kind: "desktop", thumb: "b" },
      { id: "p3", title: "Quiet Field — PRD", date: "May 20, 2026", kind: "doc", thumb: "c" },
      { id: "p4", title: "Filament logomark", date: "May 20, 2026", kind: "phone", thumb: "d" },
      { id: "p5", title: "Cadence — checkout v3", date: "May 19, 2026", kind: "desktop", thumb: "e" },
    ],
    "Last 30 days": [
      { id: "p6", title: "Junction — automation graph", date: "May 7, 2026", kind: "desktop", thumb: "f" },
      { id: "p7", title: "Wren — onboarding sweep", date: "Apr 28, 2026", kind: "phone", thumb: "g" },
    ],
    "This year": [
      { id: "p8", title: "Tidepool — explore feed", date: "Apr 4, 2026", kind: "phone", thumb: "a" },
      { id: "p9", title: "Pace — product detail", date: "Apr 4, 2026", kind: "phone", thumb: "c" },
      { id: "p10", title: "Lumen — weekend mode", date: "Mar 20, 2026", kind: "phone", thumb: "e" },
      { id: "p11", title: "Ledger — profile rebuild", date: "Mar 20, 2026", kind: "phone", thumb: "b" },
    ],
  };

  const suggestions = [
    "Mobile home for a record-trading marketplace",
    "Guided meditation profile with streaks and rituals",
    "Catalog page sorted by season and field-tested gear",
  ];

  const KindIcon = ({ kind }) => {
    if (kind === "phone") return <Icon.Phone />;
    if (kind === "desktop") return <Icon.Monitor />;
    return <Icon.Doc />;
  };

  return (
    <div className="gallery" data-screen-label="01 Gallery">
      <div className="grid-bg" />
      <div style={{ position: "relative", zIndex: 3, gridColumn: "1 / -1" }}>
        <header className="topbar">
          <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
            <span className="brand">
              <span className="brand-mark"><Icon.FuseMark style={{ width: 22, height: 22 }} /></span>
              fuse
            </span>
            <span className="badge-beta">Beta</span>
          </div>
          <div className="topbar-right">
            <button className="docs-btn"><Icon.Doc /> Docs</button>
            <button className="icon-btn" title="Community"><Icon.Users /></button>
            <button className="icon-btn" title="Updates"><Icon.Spark /></button>
            <button className="icon-btn" title="Refer"><Icon.Gift /></button>
            <button className="icon-btn" title="More"><Icon.More /></button>
            <div className="avatar" />
          </div>
        </header>
      </div>

      <aside className="sidebar">
        <div className="seg">
          <button className={tab === "mine" ? "active" : ""} onClick={() => setTab("mine")}>
            <Icon.Grid /> My projects
          </button>
          <button className={tab === "shared" ? "active" : ""} onClick={() => setTab("shared")}>
            <Icon.Users /> Shared
          </button>
        </div>
        <div className="search">
          <Icon.Search />
          <input placeholder="Search projects" />
          <span className="search-kbd">⌘K</span>
        </div>

        {Object.entries(projects).map(([section, items]) => (
          <div key={section} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <div className="section-label">{section}</div>
            <div className="project-list">
              {items.map((p) => (
                <div
                  key={p.id}
                  className={"project" + (activeId === p.id ? " is-active" : "")}
                  onClick={() => setActiveId(p.id)}
                  onDoubleClick={() => onOpenProject(p)}
                >
                  <div className="project-thumb">
                    <div className={"thumb-fill " + p.thumb} />
                  </div>
                  <div className="project-meta">
                    <span className="project-title">{p.title}</span>
                    <span className="project-sub">
                      <KindIcon kind={p.kind} />
                      {p.date}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </aside>

      <main className="main">
        <div className="hero-row">
          <div>
            <h1 className="hero-title">
              Welcome to <em>fuse</em><span className="period">.</span>
            </h1>
            <p className="hero-sub">
              Sketch a screen in plain words. Wire it to a real flow. Hand it off in one file. The whole loop — collapsed into one canvas.
            </p>
          </div>
          <button className="btn-ghost" onClick={() => onOpenProject({ id: "new", title: "Untitled" })}>
            <Icon.Plus /> Start from a screen
          </button>
        </div>

        <div className="prompt">
          <textarea placeholder="Describe a screen, a flow, or a vibe. fuse will draft it." defaultValue="" />
          <div className="prompt-toolbar">
            <div className="prompt-tools-left">
              <button className="tool-btn" title="Attach"><Icon.Plus /></button>
              <div className="mode-toggle">
                <button className="active"><Icon.Phone /> App</button>
                <button><Icon.Monitor /> Web</button>
              </div>
            </div>
            <div className="prompt-tools-right">
              <button className="tool-btn" title="Theme"><Icon.Palette /></button>
              <div className="model-pill">
                <span className="spark"><Icon.Spark style={{ width: 14, height: 14 }} /></span>
                Filament 2
                <Icon.Caret style={{ width: 12, height: 12, color: "var(--text-mute)" }} />
              </div>
              <button className="tool-btn" title="Dictate"><Icon.Mic /></button>
              <button className="send-btn" onClick={() => onOpenProject({ id: "new", title: "Untitled" })} title="Generate">
                <Icon.ArrowUp />
              </button>
            </div>
          </div>
        </div>

        <div className="suggest-row">
          {suggestions.map((s, i) => (
            <button key={i} className="suggest" onClick={() => onOpenProject({ id: "new", title: s })}>{s}</button>
          ))}
        </div>

        <div className="inspo-header">
          <h2 className="inspo-title">Spark file</h2>
          <div className="inspo-arrows">
            <button className="arrow-btn"><Icon.CaretLeft /></button>
            <button className="arrow-btn"><Icon.CaretRight /></button>
          </div>
        </div>

        <div className="inspo-grid">
          {[
            { bg: "inspo-bg-1", label: "Marketing · Romer", idx: "01" },
            { bg: "inspo-bg-2", label: "Editorial · Studio K", idx: "02" },
            { bg: "inspo-bg-3", label: "Field guide · H612", idx: "03" },
          ].map((c, i) => (
            <div key={i} className={"inspo-card " + c.bg} onClick={() => onOpenProject({ id: "inspo-" + i, title: c.label })}>
              <div className="index">{c.idx}</div>
              <div className="inspo-mock">
                <div className="bar" />
                <div className="body" />
              </div>
              <div className="label">{c.label}</div>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
}

window.Gallery = Gallery;
