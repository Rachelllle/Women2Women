/* ════════════════════════════════════════════════════════════════════════════
   ui.js — reusable presentation components
   Icon set, the cycle dial / mini ring SVGs, the tip card, and the app shell
   (Sidebar + Topbar). No screen logic lives here.
   ════════════════════════════════════════════════════════════════════════════ */

/* ═══════════════════════ ICONS ═══════════════════════ */
const Icon = ({ name, size = 18, stroke = 1.6 }) => {
  const props = { width: size, height: size, viewBox: "0 0 24 24", fill: "none", stroke: "currentColor", strokeWidth: stroke, strokeLinecap: "round", strokeLinejoin: "round" };
  switch (name) {
    case "home":     return (<svg {...props}><path d="M4 11.5 12 4l8 7.5V20a1 1 0 0 1-1 1h-4v-6h-6v6H5a1 1 0 0 1-1-1z"/></svg>);
    case "calendar": return (<svg {...props}><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>);
    case "sparkle":  return (<svg {...props}><path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6"/><circle cx="12" cy="12" r="2.5"/></svg>);
    case "chat":     return (<svg {...props}><path d="M4 5h16a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H9l-5 4V6a1 1 0 0 1 1-1z"/></svg>);
    case "user":     return (<svg {...props}><circle cx="12" cy="8" r="4"/><path d="M4 21c1.5-4 5-6 8-6s6.5 2 8 6"/></svg>);
    case "bell":     return (<svg {...props}><path d="M6 9a6 6 0 0 1 12 0c0 5 2 6 2 7H4c0-1 2-2 2-7zM10 20a2 2 0 0 0 4 0"/></svg>);
    case "plus":     return (<svg {...props}><path d="M12 5v14M5 12h14"/></svg>);
    case "back":     return (<svg {...props}><path d="M15 18 9 12l6-6"/></svg>);
    case "forward":  return (<svg {...props}><path d="M9 18l6-6-6-6"/></svg>);
    case "arrow":    return (<svg {...props}><path d="M5 12h14M13 6l6 6-6 6"/></svg>);
    case "drop":     return (<svg {...props}><path d="M12 3s6 7 6 11a6 6 0 0 1-12 0c0-4 6-11 6-11z"/></svg>);
    case "moon":     return (<svg {...props}><path d="M20 14A8 8 0 1 1 10 4a7 7 0 0 0 10 10z"/></svg>);
    case "leaf":     return (<svg {...props}><path d="M4 20c0-8 6-14 16-16-1 10-7 16-16 16zM4 20l8-8"/></svg>);
    case "heart":    return (<svg {...props}><path d="M12 20s-7-4.5-7-10a4 4 0 0 1 7-2.6A4 4 0 0 1 19 10c0 5.5-7 10-7 10z"/></svg>);
    case "send":     return (<svg {...props}><path d="M22 2 11 13M22 2l-7 20-4-9-9-4z"/></svg>);
    case "settings": return (<svg {...props}><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.6 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 4.7 9a1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9c.4.6 1 1 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>);
    case "check":    return (<svg {...props}><path d="m5 12 5 5L20 7"/></svg>);
    case "lock":     return (<svg {...props}><rect x="5" y="11" width="14" height="10" rx="2"/><path d="M8 11V7a4 4 0 1 1 8 0v4"/></svg>);
    case "info":     return (<svg {...props}><circle cx="12" cy="12" r="9"/><path d="M12 8h.01M11 12h1v5h1"/></svg>);
    default: return null;
  }
};

/* ═══════════════════════ CYCLE DIAL (SVG) ═══════════════════════ */
function CycleDial({ day = 14, size = 300, cycle = CYCLE_LENGTH }) {
  const R_OUTER = size / 2 - 6;
  const R_INNER = R_OUTER - 22;
  const cx = size / 2, cy = size / 2;
  const angleFor = (d) => (d - 1) / cycle * 360 - 90;
  const polar = (a, r) => [cx + r * Math.cos(a * Math.PI / 180), cy + r * Math.sin(a * Math.PI / 180)];
  function arcPath(startDay, endDay) {
    const a0 = angleFor(startDay - 1);
    const a1 = angleFor(endDay);
    const large = (a1 - a0) > 180 ? 1 : 0;
    const [x0, y0] = polar(a0, R_OUTER);
    const [x1, y1] = polar(a1, R_OUTER);
    const [x2, y2] = polar(a1, R_INNER);
    const [x3, y3] = polar(a0, R_INNER);
    return `M ${x0} ${y0} A ${R_OUTER} ${R_OUTER} 0 ${large} 1 ${x1} ${y1} L ${x2} ${y2} A ${R_INNER} ${R_INNER} 0 ${large} 0 ${x3} ${y3} Z`;
  }
  const phases = phasesFor(cycle);
  const phase = phaseForDay(day, cycle);
  const daysToNext = daysUntilNextPeriod(day, cycle);
  const todayA = angleFor(day - 0.5);
  const [tx, ty] = polar(todayA, (R_OUTER + R_INNER) / 2);
  const dots = [];
  for (let d = 1; d <= cycle; d++) {
    const a = angleFor(d - 0.5);
    const [dx, dy] = polar(a, R_INNER - 12);
    dots.push(<circle key={d} cx={dx} cy={dy} r={d === day ? 2.5 : 1} fill={d === day ? "var(--ink)" : "rgba(46,27,29,0.22)"} />);
  }
  return (
    <div className="dial-wrap" style={{ width: size, height: size, position: "relative" }}>
      <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} style={{ overflow: "visible" }}>
        {phases.map(p => (
          <path key={p.id} d={arcPath(p.start, p.end)}
            fill={p.id === phase.id ? "var(--c-menstrual)" : p.color}
            opacity={p.id === phase.id ? 1 : 0.4} />
        ))}
        {phases.map(p => {
          const a = angleFor(p.start - 1);
          const [x1, y1] = polar(a, R_INNER);
          const [x2, y2] = polar(a, R_OUTER);
          return <line key={p.id+"sep"} x1={x1} y1={y1} x2={x2} y2={y2} stroke="var(--cream)" strokeWidth="2" />;
        })}
        {dots}
        <g transform={`translate(${tx} ${ty})`}>
          <circle r="9" fill="var(--ink)" />
          <circle r="3.5" fill="var(--cream)" />
        </g>
      </svg>
      <div style={{
        position: "absolute", inset: 0, display: "flex", flexDirection: "column",
        alignItems: "center", justifyContent: "center", pointerEvents: "none",
        textAlign: "center", padding: "0 18%",
      }}>
        {size >= 200 && (
          <div style={{ fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--mute)", fontWeight: 500 }}>
            Day
          </div>
        )}
        <div className="display" style={{ fontSize: size >= 200 ? size * 0.22 : size * 0.32, lineHeight: 1, marginTop: size >= 200 ? 4 : 0, color: "var(--ink)" }}>
          {day}
        </div>
        {size >= 200 && (
          <div style={{ fontSize: 12, color: "var(--mute)", marginTop: 3 }}>of {cycle} days</div>
        )}
        {size >= 200 && (
          <div style={{ fontSize: 12, color: "var(--mute)", marginTop: 4 }}>{phase.name} phase</div>
        )}
      </div>
    </div>
  );
}

function MiniRing({ day = 14, size = 44, cycle = CYCLE_LENGTH }) {
  const r = size / 2 - 3;
  const c = size / 2;
  const phase = phaseForDay(day, cycle);
  const dash = 2 * Math.PI * r;
  const filled = (day / cycle) * dash;
  return (
    <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
      <circle cx={c} cy={c} r={r} fill="none" stroke="rgba(46,27,29,0.08)" strokeWidth="3" />
      <circle cx={c} cy={c} r={r} fill="none" stroke={phase.color}
        strokeWidth="3" strokeLinecap="round"
        strokeDasharray={`${filled} ${dash - filled}`}
        transform={`rotate(-90 ${c} ${c})`} />
      <text x={c} y={c + 4} textAnchor="middle" fontSize={size * 0.32} fontWeight="600" fill="var(--ink)">{day}</text>
    </svg>
  );
}

/* ═══════════════════════ TIP CARD ═══════════════════════ */
function TipCard({ tip }) {
  return (
    <article className={`tip tip-${tip.kind}`}>
      <div className="tip-tag">{tip.tag}</div>
      <h3 className="tip-title">{tip.title}</h3>
      <p className="tip-body">{tip.body}</p>
    </article>
  );
}

/* ═══════════════════════ SIDEBAR + TOPBAR ═══════════════════════ */
function Sidebar({ route, setRoute, profile, day, alertCount }) {
  const phase = phaseForDay(day, profile.cycleLen);
  const NAV = [
    { id: "home",     label: "Today",    icon: "home" },
    { id: "calendar", label: "Calendar", icon: "calendar" },
    { id: "insights", label: "Insights", icon: "sparkle" },
    { id: "symptoms", label: "Symptoms", icon: "heart" },
    { id: "chat",     label: "Chat",     icon: "chat" },
  ];
  const META = [
    { id: "alerts",  label: "Alerts",  icon: "bell", badge: alertCount },
    { id: "profile", label: "You",     icon: "user" },
  ];

  return (
    <nav className="sidebar">
      <div className="sb-brand">
        <div className="sb-brand-mark">w<em>2</em>w</div>
        <div className="sb-brand-sub">Women2Women</div>
      </div>

      <div className="sb-section">Track</div>
      {NAV.map(n => (
        <button key={n.id} className={`sb-item ${route === n.id ? "on" : ""}`} onClick={() => setRoute(n.id)}>
          <Icon name={n.icon} size={18} />
          <span>{n.label}</span>
        </button>
      ))}

      <div className="sb-section">Account</div>
      {META.map(n => (
        <button key={n.id} className={`sb-item ${route === n.id ? "on" : ""}`} onClick={() => setRoute(n.id)}>
          <Icon name={n.icon} size={18} />
          <span>{n.label}</span>
          {n.badge ? <span className="sb-badge">{n.badge}</span> : null}
        </button>
      ))}

      <div className="sb-phase-card">
        <div className="sb-phase-mini"><MiniRing day={day} size={48} cycle={profile.cycleLen} /></div>
        <div className="sb-phase-meta">
          <div className="eyebrow">{phase.name}</div>
          <div className="display">Day {day}</div>
          <div className="muted-small">of {profile.cycleLen}</div>
        </div>
      </div>
    </nav>
  );
}

function Topbar({ route, day, cycleLen = CYCLE_LENGTH }) {
  const phase = phaseForDay(day, cycleLen);
  const titles = { home: "Today", calendar: "Calendar", insights: "Insights", symptoms: "Symptoms", history: "History", chat: "Chat", alerts: "Alerts", profile: "Profile" };
  return (
    <header className="topbar">
      <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
        <div className="eyebrow" style={{ marginRight: 4 }}>Women2Women</div>
        <div className="muted-small">/ {titles[route]}</div>
      </div>
      <div className="topbar-meta">
        <div className="phase-pill">
          <span className="phase-pill-dot" style={{ background: phase.color }} />
          <span>Day {day}</span>
          <em>· {phase.name}</em>
        </div>
      </div>
    </header>
  );
}
