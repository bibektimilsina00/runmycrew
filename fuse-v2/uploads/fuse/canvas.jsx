// Canvas screen for fuse
const { useState: useS } = React;

function Canvas({ project, onBack }) {
  const [menuOpen, setMenuOpen] = useS(false);
  const [tool, setTool] = useS("cursor");

  const tools = [
    { id: "cursor", icon: <Icon.Cursor />, label: "Select" },
    { id: "frame", icon: <Icon.Frame />, label: "Frame" },
    { id: "pencil", icon: <Icon.Pencil />, label: "Annotate" },
    { id: "hand", icon: <Icon.Hand />, label: "Pan" },
    { id: "image", icon: <Icon.Image />, label: "Image" },
    { id: "palette", icon: <Icon.Palette />, label: "Theme" },
    { id: "star", icon: <Icon.Star />, label: "Favorites" },
  ];

  const menu = [
    { icon: <Icon.CaretLeft />, label: "Go to all projects", onClick: onBack },
    null,
    { icon: <Icon.Share />, label: "Share" },
    { icon: <Icon.Download />, label: "Download project" },
    { icon: <Icon.Copy />, label: "Duplicate project" },
    null,
    { icon: <Icon.Edit />, label: "Rename" },
    { icon: <Icon.Help />, label: "Help" },
    { icon: <Icon.Settings />, label: "Settings" },
    null,
    { icon: <Icon.Trash />, label: "Delete project", danger: true },
    null,
    { icon: <Icon.Cmd />, label: "Command menu", kbd: "⌘K" },
    { icon: <Icon.Feedback />, label: "Send feedback" },
  ];

  return (
    <div className="canvas-screen" data-screen-label="02 Canvas">
      <div className="grid-bg" />

      <header className="canvas-topbar">
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <button className={"menu-trigger" + (menuOpen ? " is-open" : "")} onClick={() => setMenuOpen(v => !v)}>
            <span className="hamb"><Icon.Menu /></span>
            {project?.title || "Untitled draft"}
          </button>
        </div>
        <div className="canvas-actions">
          <button className="btn-pill"><Icon.Export /> Export</button>
          <button className="btn-pill primary"><Icon.Share /> Share</button>
          <div className="avatar" style={{ marginLeft: 4 }} />
        </div>
      </header>

      {menuOpen && (
        <div className="dropdown" onMouseLeave={() => setMenuOpen(false)}>
          {menu.map((item, i) => item === null ? (
            <div key={"sep-" + i} className="dropdown-sep" />
          ) : (
            <button
              key={item.label}
              className={"dropdown-item" + (item.danger ? " danger" : "")}
              onClick={() => { item.onClick && item.onClick(); setMenuOpen(false); }}
            >
              {item.icon}
              <span>{item.label}</span>
              {item.kbd && <span className="kbd">{item.kbd}</span>}
            </button>
          ))}
        </div>
      )}

      {/* The starter artboard placed on the canvas */}
      <div className="artboard">
        <Icon.More style={{ width: 22, height: 22 }} />
        <div className="artboard-label">Artboard 01</div>
      </div>

      {/* Right rail tools */}
      <aside className="right-rail">
        {tools.slice(0, 4).map(t => (
          <button
            key={t.id}
            className={"rail-btn" + (tool === t.id ? " active" : "")}
            onClick={() => setTool(t.id)}
            title={t.label}
          >{t.icon}</button>
        ))}
        <div className="rail-sep" />
        {tools.slice(4).map(t => (
          <button
            key={t.id}
            className={"rail-btn" + (tool === t.id ? " active" : "")}
            onClick={() => setTool(t.id)}
            title={t.label}
          >{t.icon}</button>
        ))}
      </aside>

      {/* Bottom prompt */}
      <div className="canvas-prompt-wrap">
        <div className="canvas-prompt">
          <input placeholder="What would you like to change or create?" />
          <div className="prompt-toolbar">
            <div className="prompt-tools-left">
              <button className="tool-btn" title="Attach"><Icon.Plus /></button>
              <button className="tool-btn" title="Insert prompt template"><Icon.Slash /></button>
            </div>
            <div className="prompt-tools-right">
              <button className="tool-btn" title="Theme"><Icon.Palette /></button>
              <div className="model-pill">
                <span style={{ color: "var(--accent)", display: "inline-flex" }}><Icon.Spark style={{ width: 13, height: 13 }} /></span>
                Filament 2
                <Icon.Caret style={{ width: 12, height: 12, color: "var(--text-mute)" }} />
              </div>
              <button className="tool-btn" title="Dictate"><Icon.Mic /></button>
              <button className="send-btn" title="Send"><Icon.ArrowUp /></button>
            </div>
          </div>
        </div>
      </div>

      {/* Theme toggle */}
      <button className="theme-fab" title="Toggle theme"><Icon.Moon /></button>

      {/* Status */}
      <div className="statusbar">
        <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
          <span className="dot" /> Saved
        </span>
        <span className="pct">75%</span>
        <span className="help-dot">?</span>
      </div>
    </div>
  );
}

window.Canvas = Canvas;
