// Icon set for fuse — stroke-based, 24x24 viewBox
const Icon = {
  // brand mark — stylized filament/fuse: two arcs meeting
  FuseMark: (props) => (
    <svg viewBox="0 0 24 24" fill="none" {...props}>
      <path d="M4 12c0-4 4-4 8-4s8 0 8 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <path d="M4 12c0 4 4 4 8 4s8 0 8-4" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
      <circle cx="12" cy="12" r="1.7" fill="currentColor"/>
    </svg>
  ),
  Grid: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.6"/>
      <rect x="14" y="3" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.6"/>
      <rect x="3" y="14" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.6"/>
      <rect x="14" y="14" width="7" height="7" rx="1.5" stroke="currentColor" strokeWidth="1.6"/>
    </svg>
  ),
  Users: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <circle cx="9" cy="9" r="3" stroke="currentColor" strokeWidth="1.6"/>
      <circle cx="16" cy="10" r="2.3" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M3 19c0-3 3-5 6-5s6 2 6 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
      <path d="M16 14c2.5 0 5 1.5 5 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Search: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <circle cx="11" cy="11" r="6" stroke="currentColor" strokeWidth="1.6"/>
      <path d="m20 20-4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Phone: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="7" y="3" width="10" height="18" rx="2" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M11 18h2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Monitor: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="3" y="4" width="18" height="13" rx="2" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M9 20h6M12 17v3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Doc: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
      <path d="M14 3v5h5M9 13h6M9 17h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Gift: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M3 10h18v4H3z" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M5 14v7h14v-7M12 7v14" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M12 7c0-2-1.5-3-3-3s-3 1-3 3 3 3 6 3M12 7c0-2 1.5-3 3-3s3 1 3 3-3 3-6 3" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  More: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <circle cx="12" cy="5" r="1.3" fill="currentColor"/>
      <circle cx="12" cy="12" r="1.3" fill="currentColor"/>
      <circle cx="12" cy="19" r="1.3" fill="currentColor"/>
    </svg>
  ),
  Plus: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M12 5v14M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  ),
  Mic: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="9" y="3" width="6" height="11" rx="3" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
      <path d="M16.5 5.5l1.6-1.6M19 9h1.5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  ArrowUp: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M12 4v16M5 11l7-7 7 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Palette: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M12 3a9 9 0 1 0 0 18c1 0 1.5-.7 1.5-1.5 0-1.7 1.3-3 3-3H19a3 3 0 0 0 3-3 9 9 0 0 0-10-10.5z" stroke="currentColor" strokeWidth="1.6"/>
      <circle cx="7.5" cy="11" r="1.2" fill="currentColor"/>
      <circle cx="10" cy="7" r="1.2" fill="currentColor"/>
      <circle cx="15" cy="7.5" r="1.2" fill="currentColor"/>
      <circle cx="17.5" cy="11" r="1.2" fill="currentColor"/>
    </svg>
  ),
  Spark: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z" fill="currentColor"/>
      <path d="M19 3l.7 2L22 5.7 19.7 6.4 19 9l-.7-2.6L16 5.7 18.3 5z" fill="currentColor" opacity="0.6"/>
    </svg>
  ),
  Caret: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  CaretLeft: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M14 6l-6 6 6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  CaretRight: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M10 6l6 6-6 6" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Moon: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Sun: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <circle cx="12" cy="12" r="4" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.4 1.4M17.6 17.6 19 19M5 19l1.4-1.4M17.6 6.4 19 5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Menu: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M4 7h16M4 12h16M4 17h16" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  ),
  Export: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M14 4h5a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
      <path d="M9 8l4 4-4 4M3 12h10" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Share: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <circle cx="18" cy="5" r="2.5" stroke="currentColor" strokeWidth="1.6"/>
      <circle cx="6" cy="12" r="2.5" stroke="currentColor" strokeWidth="1.6"/>
      <circle cx="18" cy="19" r="2.5" stroke="currentColor" strokeWidth="1.6"/>
      <path d="m8 11 8-5M8 13l8 5" stroke="currentColor" strokeWidth="1.6"/>
    </svg>
  ),
  Cursor: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M5 3l4 16 3-7 7-3z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Frame: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M4 9V5h4M4 15v4h4M20 9V5h-4M20 15v4h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Pencil: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M4 20l4-1 11-11-3-3L5 16l-1 4z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Hand: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M8 11V5.5a1.5 1.5 0 0 1 3 0V11M11 11V4.5a1.5 1.5 0 0 1 3 0V11M14 11V5.5a1.5 1.5 0 0 1 3 0V13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
      <path d="M17 13v0a1.5 1.5 0 0 1 3 0v3a6 6 0 0 1-6 6h-1a6 6 0 0 1-5.5-3.6L5 13.5a1.5 1.5 0 0 1 2.7-1.3L9 14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Image: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.6"/>
      <circle cx="9" cy="10" r="1.5" stroke="currentColor" strokeWidth="1.6"/>
      <path d="m4 18 5-5 4 4 3-3 4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Star: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="m12 3 2.7 6 6.3.6-4.8 4.4L17.5 21 12 17.8 6.5 21l1.3-7L3 9.6 9.3 9z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Download: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M12 3v13m0 0-4-4m4 4 4-4M4 20h16" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Copy: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="8" y="8" width="12" height="12" rx="2" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3" stroke="currentColor" strokeWidth="1.6"/>
    </svg>
  ),
  Trash: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M4 7h16M9 7V4h6v3M6 7l1 13h10l1-13M10 11v6M14 11v6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Help: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M9.5 9a2.5 2.5 0 0 1 5 0c0 1.5-2.5 2-2.5 4M12 17.5v.1" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Settings: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Cmd: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M9 9V7a2 2 0 1 0-2 2h10a2 2 0 1 0-2-2v10a2 2 0 1 0 2-2H7a2 2 0 1 0 2 2z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Feedback: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M21 12a8 8 0 0 1-11.5 7.2L4 20l.8-5.5A8 8 0 1 1 21 12z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Edit: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M4 20h4l11-11-4-4L4 16v4z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Cloud: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M7 18a5 5 0 0 1-1-9.9 6 6 0 0 1 11.7 1.4A4 4 0 0 1 18 18z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
      <path d="m9 13 2 2 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Flow: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="3" y="4" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.6"/>
      <rect x="15" y="4" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.6"/>
      <rect x="9" y="14" width="6" height="6" rx="1.5" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M9 7h6M9 14l-3-4M15 14l3-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Clock: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M12 7v5l3 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Activity: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M3 12h4l2-6 4 12 2-6h6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Plug: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M9 2v6M15 2v6" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
      <rect x="6" y="8" width="12" height="6" rx="2" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M12 14v4a3 3 0 0 0 3 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Home: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M4 11l8-7 8 7v9a1 1 0 0 1-1 1h-4v-6h-6v6H5a1 1 0 0 1-1-1z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Layers: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="m12 3 9 5-9 5-9-5z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
      <path d="m3 13 9 5 9-5M3 17l9 5 9-5" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Terminal: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.6"/>
      <path d="m7 9 3 3-3 3M13 15h4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Bell: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M6 9a6 6 0 1 1 12 0v4l2 3H4l2-3z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
      <path d="M10 19a2 2 0 0 0 4 0" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Chevrons: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="m8 9 4-4 4 4M8 15l4 4 4-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Check: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="m4 12 5 5 11-11" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Bolt: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M13 3 4 14h7l-1 7 9-11h-7z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  PanelClose: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M10 4v16" stroke="currentColor" strokeWidth="1.6"/>
      <path d="m17 9-3 3 3 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  PanelOpen: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M10 4v16" stroke="currentColor" strokeWidth="1.6"/>
      <path d="m14 9 3 3-3 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Sort: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M7 5v14m0 0-3-3m3 3 3-3M17 19V5m0 0-3 3m3-3 3 3" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Pause: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="6" y="5" width="4" height="14" rx="1" stroke="currentColor" strokeWidth="1.6"/>
      <rect x="14" y="5" width="4" height="14" rx="1" stroke="currentColor" strokeWidth="1.6"/>
    </svg>
  ),
  Table: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="3" y="4" width="18" height="16" rx="2" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M3 10h18M3 16h18M9 4v16M15 4v16" stroke="currentColor" strokeWidth="1.6"/>
    </svg>
  ),
  Folder: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Book: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M4 5a2 2 0 0 1 2-2h13v16H6a2 2 0 0 0-2 2z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
      <path d="M4 19a2 2 0 0 0 2 2h13" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
      <path d="M8 7h7M8 11h7" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Key: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <circle cx="8" cy="14" r="4" stroke="currentColor" strokeWidth="1.6"/>
      <path d="m11 11 9-9m-3 3 2 2m-5 1 2 2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Globe: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18" stroke="currentColor" strokeWidth="1.6"/>
    </svg>
  ),
  Slack: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="3" y="10" width="8" height="3" rx="1.5" stroke="currentColor" strokeWidth="1.6"/>
      <rect x="10" y="3" width="3" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.6"/>
      <rect x="13" y="11" width="8" height="3" rx="1.5" stroke="currentColor" strokeWidth="1.6"/>
      <rect x="11" y="13" width="3" height="8" rx="1.5" stroke="currentColor" strokeWidth="1.6"/>
    </svg>
  ),
  NotionDoc: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="4" y="3" width="16" height="18" rx="2" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M8 7v10l8-10v10" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Square: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <rect x="4" y="4" width="16" height="16" rx="3" stroke="currentColor" strokeWidth="1.6"/>
    </svg>
  ),
  Eye: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7-10-7-10-7z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
      <circle cx="12" cy="12" r="3" stroke="currentColor" strokeWidth="1.6"/>
    </svg>
  ),
  EyeOff: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M3 3l18 18M10.5 6.2A10 10 0 0 1 12 6c6 0 10 6 10 6a16 16 0 0 1-3 3.8M6.6 6.6C3.4 8.6 2 12 2 12s4 6 10 6c1.7 0 3.2-.5 4.5-1.2" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M9.5 9.5a3 3 0 0 0 4 4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  SignOut: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M14 4h4a1 1 0 0 1 1 1v14a1 1 0 0 1-1 1h-4" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
      <path d="m9 8-4 4 4 4M5 12h11" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Filter: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M3 5h18l-7 9v6l-4-2v-4z" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Branch: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <circle cx="6" cy="6" r="2.2" stroke="currentColor" strokeWidth="1.6"/>
      <circle cx="6" cy="18" r="2.2" stroke="currentColor" strokeWidth="1.6"/>
      <circle cx="18" cy="18" r="2.2" stroke="currentColor" strokeWidth="1.6"/>
      <path d="M6 8v8M6 12c0-3 3-4 6-4s6 4 6 8" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round"/>
    </svg>
  ),
  Map: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="m3 6 6-2 6 2 6-2v14l-6 2-6-2-6 2zM9 4v16M15 6v16" stroke="currentColor" strokeWidth="1.6" strokeLinejoin="round"/>
    </svg>
  ),
  Minus: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M5 12h14" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  ),
  Maximize: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Code: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="m9 8-4 4 4 4M15 8l4 4-4 4M14 5l-4 14" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  ),
  Slash: (p) => (
    <svg viewBox="0 0 24 24" fill="none" {...p}>
      <path d="M15 4 9 20" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round"/>
    </svg>
  ),
};

window.Icon = Icon;
