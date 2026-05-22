// Gallery v2 — shell + sidebar + view router
const { useState } = React;

function Gallery({ onOpenProject }) {
  const [tab, setTab] = useState("home");
  const [collapsed, setCollapsed] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);
  const [openGroups, setOpenGroups] = useState({ Workspace: true, Operate: true, Workflows: true, Data: false, Integrations: false });
  const [folderOpen, setFolderOpen] = useState({ f1: true, f2: false, f3: false });
  const [menuOpen, setMenuOpen] = useState(null);

  const workflowsTree = [
    { type: "folder", id: "f1", name: "Revenue ops", items: [
      { id: "wf1", name: "Stripe refund — Slack approval", state: "ok" },
      { id: "wf2", name: "Lead enrichment — Clearbit → HubSpot", state: "ok" },
      { id: "wf6", name: "Invoice triage agent", state: "ok" },
    ]},
    { type: "folder", id: "f2", name: "Inbox & support", items: [
      { id: "wf3", name: "Inbound RFP classifier", state: "ok" },
      { id: "wf7", name: "Support ticket auto-tagger", state: "warn" },
    ]},
    { type: "folder", id: "f3", name: "Engineering", items: [
      { id: "wf4", name: "Daily brief from Linear + GitHub", state: "ok" },
      { id: "wf9", name: "Pager rotation handoff", state: "warn" },
    ]},
    { type: "wf", id: "wf5", name: "Notion → Airtable nightly sync", state: "err" },
    { type: "wf", id: "wf8", name: "Weekly metrics digest", state: "ok" },
    { type: "wf", id: "wf10", name: "Churn-risk watchlist", state: "ok" },
    { type: "wf", id: "wf11", name: "Contract redline assistant", state: "draft" },
  ];
  const totalWorkflows = workflowsTree.reduce((n, node) =>
    n + (node.type === "folder" ? node.items.length : 1), 0);

  const nav = [
    { group: "Workspace", items: [
      { id: "home", label: "Home", icon: <Icon.Home /> },
      { id: "automations", label: "Automations", icon: <Icon.Flow />, count: "47" },
      { id: "templates", label: "Templates", icon: <Icon.Layers /> },
    ]},
    { group: "Operate", items: [
      { id: "runs", label: "Runs", icon: <Icon.Activity />, count: "1.2k" },
      { id: "schedules", label: "Schedules", icon: <Icon.Clock />, count: "6" },
      { id: "logs", label: "Logs", icon: <Icon.Terminal /> },
    ]},
    { group: "Data", items: [
      { id: "tables", label: "Tables", icon: <Icon.Table />, count: "8" },
      { id: "files", label: "Files", icon: <Icon.Folder />, count: "124" },
      { id: "knowledge", label: "Knowledge base", icon: <Icon.Book />, count: "8" },
      { id: "variables", label: "Variables", icon: <Icon.Key /> },
    ]},
    { group: "Integrations", items: [
      { id: "connections", label: "Connections", icon: <Icon.Plug />, count: "18" },
    ]},
    { group: "Workflows", isWorkflows: true },
  ];
  const flatNav = nav.filter(g => !g.isWorkflows).flatMap(g => g.items);
  const toggleGroup = (g) => setOpenGroups(s => ({ ...s, [g]: !s[g] }));
  const toggleFolder = (f) => setFolderOpen(s => ({ ...s, [f]: !s[f] }));
  const closeMenus = () => setMenuOpen(null);
  const stopAndOpen = (e, id) => {
    e.stopPropagation();
    setMenuOpen(m => m === id ? null : id);
  };
  const crumbLabel = flatNav.find(n => n.id === tab)?.label || "Home";

  const Menu = ({ id, children }) => menuOpen === id && (
    <React.Fragment>
      <div className="dropdown-backdrop" onClick={closeMenus} />
      <div className="row-menu" onClick={(e) => e.stopPropagation()}>{children}</div>
    </React.Fragment>
  );

  const renderWorkflowRow = (w) => (
    <div key={w.id} className="wf-row-wrap">
      <div className="wf-row" onClick={() => onOpenProject({ id: w.id, title: w.name })} title={w.name}>
        <span className={"status-dot " + w.state} />
        <span className="wf-name">{w.name}</span>
        <button className={"row-more" + (menuOpen === "wf-" + w.id ? " is-open" : "")}
          onClick={(e) => stopAndOpen(e, "wf-" + w.id)} title="More">
          <Icon.More />
        </button>
      </div>
      <Menu id={"wf-" + w.id}>
        <button className="dropdown-item" onClick={() => { onOpenProject({ id: w.id, title: w.name }); closeMenus(); }}>
          <Icon.Edit /> Open in canvas
        </button>
        <button className="dropdown-item" onClick={closeMenus}><Icon.Activity /> View runs</button>
        <button className="dropdown-item" onClick={closeMenus}><Icon.Edit /> Rename</button>
        <button className="dropdown-item" onClick={closeMenus}><Icon.Copy /> Duplicate</button>
        <button className="dropdown-item" onClick={closeMenus}><Icon.Folder /> Move to folder</button>
        <div className="dropdown-sep" />
        <button className="dropdown-item" onClick={closeMenus}><Icon.Pause /> Pause</button>
        <button className="dropdown-item" onClick={closeMenus}><Icon.Download /> Export</button>
        <div className="dropdown-sep" />
        <button className="dropdown-item danger" onClick={closeMenus}><Icon.Trash /> Delete</button>
      </Menu>
    </div>
  );

  const renderFolder = (folder) => {
    const open = folderOpen[folder.id];
    return (
      <div key={folder.id} className="folder">
        <div className={"folder-head" + (open ? "" : " is-closed")} onClick={() => toggleFolder(folder.id)}>
          <span className="folder-caret"><Icon.Caret /></span>
          <span className="folder-icon"><Icon.Folder /></span>
          <span className="folder-name">{folder.name}</span>
          <span className="folder-count">{folder.items.length}</span>
          <button className={"row-more" + (menuOpen === "folder-" + folder.id ? " is-open" : "")}
            onClick={(e) => stopAndOpen(e, "folder-" + folder.id)} title="More">
            <Icon.More />
          </button>
          <Menu id={"folder-" + folder.id}>
            <button className="dropdown-item" onClick={() => { onOpenProject({ id: "new", title: "Untitled" }); closeMenus(); }}>
              <Icon.Plus /> New workflow in folder
            </button>
            <button className="dropdown-item" onClick={closeMenus}><Icon.Folder /> New subfolder</button>
            <button className="dropdown-item" onClick={closeMenus}><Icon.Edit /> Rename folder</button>
            <button className="dropdown-item" onClick={closeMenus}><Icon.Copy /> Duplicate folder</button>
            <button className="dropdown-item" onClick={closeMenus}><Icon.Download /> Export workflows</button>
            <div className="dropdown-sep" />
            <button className="dropdown-item" onClick={closeMenus}><Icon.Sort /> Sort A → Z</button>
            <button className="dropdown-item" onClick={closeMenus}><Icon.Activity /> Sort by status</button>
            <div className="dropdown-sep" />
            <button className="dropdown-item danger" onClick={closeMenus}><Icon.Trash /> Delete folder</button>
          </Menu>
        </div>
        {open && (
          <div className="folder-body">
            {folder.items.map(renderWorkflowRow)}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={"shell" + (collapsed ? " is-collapsed" : "")} data-screen-label={"01 " + crumbLabel}>
      <div className="grid-bg" />

      <aside className="sidebar">
        <div className="sidebar-top">
          <div className="brand-row">
            <span className="brand">
              <span className="brand-mark"><Icon.FuseMark style={{ width: 14, height: 14 }} /></span>
              <span className="brand-text">fuse</span>
              <span className="brand-badge">Beta</span>
            </span>
            <button className="brand-trail-btn" onClick={() => setCollapsed(c => !c)} title={collapsed ? "Expand sidebar" : "Collapse sidebar"}>
              {collapsed ? <Icon.PanelOpen /> : <Icon.PanelClose />}
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

          <div className="cmd-search" title="Search">
            <Icon.Search />
            <input placeholder="Search" />
            <span className="kbd">⌘K</span>
          </div>
        </div>

        <div className="sidebar-scroll">
          {nav.map((section, gi) => {
            const open = openGroups[section.group];
            return (
              <div key={gi} className={"nav-section" + (open ? "" : " is-closed") + (section.isWorkflows ? " is-workflows" : "")}>
                <div className="nav-group-head" onClick={() => toggleGroup(section.group)}>
                  <span className="nav-group-caret"><Icon.Caret /></span>
                  <span className="nav-group-label">{section.group}</span>
                  {section.isWorkflows && (
                    <React.Fragment>
                      <span className="nav-group-count">{totalWorkflows}</span>
                      <button className={"nav-group-icon-btn" + (menuOpen === "group" ? " is-open" : "")}
                        onClick={(e) => stopAndOpen(e, "group")} title="More">
                        <Icon.More />
                      </button>
                      <button className="nav-group-icon-btn"
                        onClick={(e) => { e.stopPropagation(); onOpenProject({ id: "new", title: "Untitled automation" }); }} title="New workflow">
                        <Icon.Plus />
                      </button>
                      <Menu id="group">
                        <button className="dropdown-item" onClick={() => { onOpenProject({ id: "new", title: "Untitled" }); closeMenus(); }}>
                          <Icon.Plus /> New workflow
                        </button>
                        <button className="dropdown-item" onClick={closeMenus}><Icon.Folder /> Create folder</button>
                        <button className="dropdown-item" onClick={closeMenus}><Icon.Doc /> Import workflow</button>
                        <button className="dropdown-item" onClick={closeMenus}><Icon.Download /> Export all</button>
                        <div className="dropdown-sep" />
                        <button className="dropdown-item" onClick={closeMenus}><Icon.Sort /> Sort A → Z</button>
                        <button className="dropdown-item" onClick={closeMenus}><Icon.Activity /> Sort by status</button>
                        <button className="dropdown-item" onClick={closeMenus}><Icon.Clock /> Sort by recent</button>
                        <div className="dropdown-sep" />
                        <button className="dropdown-item" onClick={closeMenus}><Icon.Settings /> Workflow settings</button>
                      </Menu>
                    </React.Fragment>
                  )}
                </div>
                {open && !section.isWorkflows && section.items.map(n => (
                  <button
                    key={n.id}
                    className={"nav-item" + (tab === n.id ? " active" : "")}
                    onClick={() => setTab(n.id)}
                    title={n.label}
                  >
                    {n.icon}
                    <span className="nav-label-text">{n.label}</span>
                    {n.count && <span className="count">{n.count}</span>}
                  </button>
                ))}
                {open && section.isWorkflows && (
                  <div className="wf-tree">
                    {workflowsTree.map(node =>
                      node.type === "folder" ? renderFolder(node) : renderWorkflowRow(node)
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        <div className="sidebar-foot-actions">
          <button className="foot-action"><Icon.Help /> Help & docs</button>
          <button className="foot-action"><Icon.Feedback /> Feedback</button>
        </div>
      </aside>

      <main className="main">
        <div className="main-card">
          <header className="topbar">
            <div className="crumbs">
              <span>Mahesh's workspace</span>
              <span className="sep">/</span>
              <span className="cur">{crumbLabel}</span>
            </div>
            <div className="topbar-actions">
              <button className="link-btn"><Icon.Doc /> Docs</button>
              <button className="icon-btn" title="Activity"><Icon.Activity /><span className="indicator" /></button>
              <button className="icon-btn" title="Help"><Icon.Help /></button>
              <div className="profile-wrap">
                <button className={"avatar" + (profileOpen ? " is-open" : "")} onClick={() => setProfileOpen(v => !v)} aria-label="Account" />
                {profileOpen && (
                  <React.Fragment>
                    <div className="dropdown-backdrop" onClick={() => setProfileOpen(false)} />
                    <div className="profile-dropdown">
                      <div className="profile-head">
                        <span className="profile-avatar">M</span>
                        <span className="profile-meta">
                          <span className="profile-name">Mahesh Shimpi</span>
                          <span className="profile-email">mahesh@gmail.com</span>
                        </span>
                      </div>
                      <div className="profile-workspace">
                        <span className="workspace-avatar small">M</span>
                        <span className="workspace-meta">
                          <span className="workspace-name">Mahesh's workspace</span>
                          <span className="workspace-sub"><span className="plan-dot" />Pro · 4 seats</span>
                        </span>
                        <Icon.Chevrons />
                      </div>
                      <div className="dropdown-sep" />
                      <button className="dropdown-item"><Icon.Settings /> Account settings <span className="kbd">⌘,</span></button>
                      <button className="dropdown-item"><Icon.Users /> Workspace members</button>
                      <button className="dropdown-item"><Icon.Plug /> Connected apps</button>
                      <button className="dropdown-item"><Icon.Activity /> Run usage <span className="item-sub">2,012 / 5,000</span></button>
                      <div className="dropdown-sep" />
                      <button className="dropdown-item"><Icon.Moon /> Appearance <span className="item-sub">Dark</span></button>
                      <button className="dropdown-item"><Icon.Cmd /> Keyboard shortcuts <span className="kbd">?</span></button>
                      <button className="dropdown-item"><Icon.Doc /> Documentation</button>
                      <button className="dropdown-item"><Icon.Feedback /> Send feedback</button>
                      <div className="dropdown-sep" />
                      <button className="dropdown-item danger"><Icon.SignOut /> Sign out</button>
                    </div>
                  </React.Fragment>
                )}
              </div>
            </div>
          </header>

          {tab === "home" && <HomeView onOpen={onOpenProject} goTo={setTab} />}
          {tab === "automations" && <AutomationsView onOpen={onOpenProject} />}
          {tab === "runs" && <RunsView onOpen={onOpenProject} />}
          {tab === "schedules" && <SchedulesView onOpen={onOpenProject} />}
          {tab === "logs" && <LogsView />}
          {tab === "tables" && <TablesView onOpen={onOpenProject} />}
          {tab === "files" && <FilesView onOpen={onOpenProject} />}
          {tab === "knowledge" && <KnowledgeView onOpen={onOpenProject} />}
          {tab === "variables" && <VariablesView />}
          {tab === "connections" && <ConnectionsView />}
          {tab === "templates" && <TemplatesView onOpen={onOpenProject} />}
        </div>
      </main>
    </div>
  );
}

window.Gallery = Gallery;
