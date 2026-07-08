/* ════════════════════════════════════════════════════════════════════════════
   screens.js — the six routed screens
   Home · Calendar · Insights · Chat (Lea) · Alerts · Profile
   ════════════════════════════════════════════════════════════════════════════ */

/* ═══════════════════════ TODAY (HOME) ═══════════════════════ */
function HomeScreen({ profile, day }) {
  const today = new Date();
  const cycleLen = profile.cycleLen;
  const phase = phaseForDay(day, cycleLen);
  const cyclePhases = phasesFor(cycleLen);

  // Upcoming cycle milestones over the next ~2 cycles (soonest 5)
  const daysToPeriod = daysUntilNextPeriod(day, cycleLen);
  const events = [];
  // remaining phase changes this cycle
  cyclePhases.forEach(p => {
    if (p.start > day) events.push({ label: `${p.name} phase begins`, days: p.start - day });
  });
  // start of the next cycle
  events.push({ label: "Next period", days: daysToPeriod });
  // phase changes of the next cycle (menstrual start = the "Next period" above)
  cyclePhases.forEach(p => {
    if (p.id !== "menstrual") events.push({ label: `${p.name} phase begins`, days: daysToPeriod + (p.start - 1) });
  });
  events.sort((a, b) => a.days - b.days);
  const upcoming = events.slice(0, 5);

  return (
    <>
      <div className="screen-hd">
        <div>
          <div className="eyebrow">{fmtDate(today)}</div>
          <h1 className="screen-title display">Hello, <em>{profile.name}</em>.</h1>
        </div>
      </div>

      <div className="hero-card">
        <CycleDial day={day} size={300} cycle={profile.cycleLen} />
        <div className="hero-text">
          <div className="eyebrow">{phase.name} phase · day {day} of {profile.cycleLen}</div>
          <p className="hero-phase-blurb">{phase.blurb}</p>
          <div className="phase-mini-strip">
            {PHASES.map(p => (
              <span key={p.id} className={p.id === phase.id ? "on" : ""} style={{ background: p.color }} />
            ))}
          </div>

          <div style={{ marginTop: 22 }}>
            <div className="eyebrow" style={{ marginBottom: 6 }}>Coming up</div>
            {upcoming.map((e, i) => (
              <div key={i} style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", padding: "9px 0", borderTop: "1px solid var(--border-soft)", fontSize: 14 }}>
                <span>{e.label}</span>
                <span className="muted-small">in {e.days} {e.days === 1 ? "day" : "days"}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}

/* ═══════════════════════ CALENDAR ═══════════════════════ */
function CalendarScreen({ profile, day, onUpdateProfile, onNav }) {
  const today = new Date();
  const [viewMonth, setViewMonth] = useState(new Date(today.getFullYear(), today.getMonth(), 1));

  // Log period (Katia's feature) — lives on the Calendar page
  const todayStr = new Date().toISOString().slice(0, 10);
  const [showLog, setShowLog]   = useState(false);
  const [logDate, setLogDate]   = useState(todayStr);
  const [logError, setLogError] = useState("");
  const [logMsg, setLogMsg]     = useState("");

  const logPeriod = async () => {
    setLogError("");
    try {
      const res = await fetch(`${API_BASE}/api/period/log`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ date: logDate }),
      });
      const j = await res.json();
      if (!res.ok) { setLogError(j.error || "Could not log your period."); return; }
      // apply BOTH the new reference date and the learned cycle length
      onUpdateProfile({ ...profile, lastPeriod: j.lastPeriod, cycleLen: j.cycleLen });
      setLogMsg(j.archived
        ? `Logged. Last cycle was ${j.cycleDuration} days — average is now ${j.cycleLen} days.`
        : `Logged. Your cycle starts fresh from ${new Date(j.lastPeriod).toLocaleDateString("en-GB", { day: "numeric", month: "long" })}.`);
      setShowLog(false);
    } catch {
      setLogError("Can't reach the server. Try again.");
    }
  };

  const first = new Date(viewMonth); first.setDate(1);
  const startWeekday = (first.getDay() + 6) % 7;
  const daysInMonth = new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 0).getDate();
  const lastStart = addDays(today, -(day - 1));
  const periodStarts = [];
  for (let i = -2; i <= 2; i++) periodStarts.push(addDays(lastStart, i * profile.cycleLen));

  const sameDay = (a, b) => a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
  const dayMeta = (date) => {
    const out = { period: false, predicted: false, fertile: false, ovulation: false, today: false };
    if (sameDay(date, today)) out.today = true;
    for (const s of periodStarts) {
      for (let i = 0; i < profile.periodLen; i++) {
        if (sameDay(addDays(s, i), date)) { out.period = true; if (s > today) out.predicted = true; }
      }
      if (sameDay(addDays(s, 13), date)) out.ovulation = true;
      for (let i = 11; i <= 16; i++) if (sameDay(addDays(s, i), date)) out.fertile = true;
    }
    return out;
  };

  const cells = [];
  for (let i = 0; i < startWeekday; i++) cells.push(null);
  for (let d = 1; d <= daysInMonth; d++) cells.push(new Date(viewMonth.getFullYear(), viewMonth.getMonth(), d));

  const upcoming = [];
  for (const s of periodStarts) {
    if (s > today) upcoming.push({ date: s, title: "Next period predicted", body: `Day 1 of cycle. ${profile.periodLen}-day average flow.`, kind: "period" });
    const ov = addDays(s, 13);
    if (ov > today) upcoming.push({ date: ov, title: "Ovulation expected", body: "Verbal fluency, peak energy, fertility highest.", kind: "fertile" });
    const lf = addDays(s, 17);
    if (lf > today) upcoming.push({ date: lf, title: "Luteal phase begins", body: "Energy turns inward — expect a quieter week.", kind: "phase" });
  }
  upcoming.sort((a,b) => a.date - b.date);

  return (
    <>
      <div className="screen-hd">
        <div>
          <div className="eyebrow">Your cycle, mapped</div>
          <h1 className="screen-title display">Calendar</h1>
        </div>
        <button className="btn-outline" onClick={() => setViewMonth(new Date(today.getFullYear(), today.getMonth(), 1))}>Today</button>
      </div>

      <div className="cal-grid-2">
        <div className="cal-card">
          <div className="cal-nav">
            <button className="icon-btn-sm" onClick={() => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() - 1, 1))}><Icon name="back" size={16} /></button>
            <div className="cal-month">{viewMonth.toLocaleDateString("en-GB", { month: "long", year: "numeric" })}</div>
            <button className="icon-btn-sm" onClick={() => setViewMonth(new Date(viewMonth.getFullYear(), viewMonth.getMonth() + 1, 1))}><Icon name="forward" size={16} /></button>
          </div>
          <div className="cal-weekdays">
            {["MON","TUE","WED","THU","FRI","SAT","SUN"].map((d,i) => <span key={i}>{d}</span>)}
          </div>
          <div className="cal-days">
            {cells.map((c, i) => {
              if (!c) return <div key={i} className="cal-cell empty" />;
              const m = dayMeta(c);
              const cls = ["cal-cell"];
              if (m.period && !m.predicted) cls.push("is-period");
              if (m.predicted) cls.push("is-predicted");
              if (m.ovulation) cls.push("is-ov");
              else if (m.fertile) cls.push("is-fertile");
              if (m.today) cls.push("is-today");
              return <div key={i} className={cls.join(" ")}><span>{c.getDate()}</span></div>;
            })}
          </div>
          <div className="legend">
            <span><span className="lg-dot lg-period" /> period</span>
            <span><span className="lg-dot lg-predicted" /> predicted</span>
            <span><span className="lg-dot lg-fertile" /> fertile</span>
            <span><span className="lg-dot lg-ov" /> ovulation</span>
          </div>
        </div>

        <div className="cal-side">
          {/* Log period (Katia's feature) */}
          <div className="info-card next-period" style={{ padding: "24px 26px" }}>
            <div className="eyebrow">Track your cycle</div>
            <div style={{ fontFamily: "var(--font-sans)", fontSize: 19, fontWeight: 600, margin: "6px 0 4px", color: "var(--ink)" }}>Log your period</div>
            <div className="muted-small" style={{ marginBottom: 16 }}>
              Mark the day your period started to update predictions and build your history.
            </div>
            {!showLog ? (
              <button className="btn-primary btn-block" onClick={() => { setShowLog(true); setLogError(""); setLogMsg(""); }}>
                🩸 Log my period
              </button>
            ) : (
              <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
                <div style={{ fontSize: 13, color: "var(--mute)" }}>Period start date:</div>
                <input type="date" className="ob-input"
                  style={{ padding: "12px 14px", fontSize: 15 }}
                  value={logDate} max={todayStr}
                  onChange={e => { setLogDate(e.target.value); setLogError(""); }} />
                {logError && <div className="ob-error-box">⚠ {logError}</div>}
                <div style={{ display: "flex", gap: 8 }}>
                  <button className="btn-primary btn-sm" onClick={logPeriod} style={{ flex: 1 }}>✓ Confirm</button>
                  <button className="btn-ghost" onClick={() => { setShowLog(false); setLogError(""); }}>Cancel</button>
                </div>
              </div>
            )}
            {logMsg && !showLog && (
              <div style={{ marginTop: 12, fontSize: 12.5, color: "var(--sage)", lineHeight: 1.4 }}>✓ {logMsg}</div>
            )}
          </div>

          {/* Cycle history — opens the History screen */}
          <div className="info-card">
            <div className="eyebrow">Cycle history</div>
            <div style={{ fontFamily: "var(--font-sans)", fontSize: 15, color: "var(--mute)", margin: "6px 0 14px", lineHeight: 1.4 }}>
              See your past cycles, average length and trends over time.
            </div>
            <button className="btn-outline" style={{ width: "100%", justifyContent: "center" }} onClick={() => onNav("history")}>
              View cycle history <Icon name="arrow" size={14} />
            </button>
          </div>

          <div className="upcoming-card">
            <div className="prof-section-hd" style={{ margin: "4px 0 8px" }}>Upcoming</div>
            {upcoming.slice(0, 5).map((u, i) => (
              <div key={i} className="upcoming-row">
                <div className="upcoming-pill">
                  <div className="day">{u.date.getDate()}</div>
                  <div className="mo">{u.date.toLocaleDateString("en-GB", { month: "short" })}</div>
                </div>
                <div className="upcoming-body">
                  <span className={`upcoming-tag t-${u.kind}`}>{u.kind === "period" ? "Period" : u.kind === "fertile" ? "Fertile" : "Phase"}</span>
                  <h4 style={{ marginTop: 6 }}>{u.title}</h4>
                  <p>{u.body}</p>
                </div>
              </div>
            ))}
          </div>

        </div>
      </div>
    </>
  );
}

/* ═══════════════════════ INSIGHTS (RECOMMENDATIONS) ═══════════════════════ */
const FEELINGS = ["Tired", "Energetic", "Bloated", "Calm", "Low", "Crampy", "Anxious", "Bright"];

function InsightsScreen({ profile, day, onNav }) {
  const phase = phaseForDay(day, profile.cycleLen);
  const [tips, setTips] = useState(TIPS_BY_PHASE[phase.id]);
  const [filter, setFilter] = useState("all");
  const [feelings, setFeelings] = useState([]);

  const toggleFeeling = (f) => setFeelings(prev =>
    prev.includes(f) ? prev.filter(x => x !== f) : [...prev, f]
  );

  useEffect(() => {
    const feeling = feelings.join(" ").toLowerCase();
    api.fetchRecommendations({ day, phase: phase.id, profile, feeling }).then(setTips);
  }, [day, phase.id, feelings]);

  const visible = filter === "all" ? tips : tips.filter(t => t.kind === filter);

  return (
    <>
      <div className="screen-hd">
        <div>
          <div className="eyebrow">For your {phase.name.toLowerCase()} phase · day {day}</div>
          <h1 className="screen-title display">Today's <em>recommendations</em></h1>
        </div>
      </div>

      <p className="lede">{phase.blurb}</p>

      <div style={{ marginTop: 36 }}>
        <div className="eyebrow" style={{ marginBottom: 12 }}>How are you feeling today?</div>
        <div className="filter-row" style={{ marginBottom: 0 }}>
          {FEELINGS.map(f => (
            <button key={f} className={`filter-chip ${feelings.includes(f) ? "on" : ""}`}
              onClick={() => toggleFeeling(f)}>{f}</button>
          ))}
        </div>
      </div>

      <div style={{ marginTop: 30 }}>
        <div className="eyebrow" style={{ marginBottom: 12 }}>Show</div>
        <div className="filter-row" style={{ marginBottom: 0 }}>
          {[["all","All"],["food","Nourish"],["move","Move"],["mood","Mind"],["care","Care"]].map(([id,label]) => (
            <button key={id} className={`filter-chip ${filter === id ? "on" : ""}`} onClick={() => setFilter(id)}>{label}</button>
          ))}
        </div>
      </div>

      <div className="tip-grid-4" style={{ marginTop: 32 }}>
        {visible.map(t => <TipCard key={t.title} tip={t} />)}
      </div>

      <div className="insight-banner" style={{ marginTop: 36 }}>
        <div>
          <div className="eyebrow">Want to go deeper?</div>
          <div className="insight-banner-text">Talk to Lea, your cycle companion</div>
        </div>
        <button className="btn-primary" onClick={() => onNav("chat")}>Open chat <Icon name="arrow" size={16} /></button>
      </div>
    </>
  );
}

/* ═══════════════════════ HISTORY (Katia's feature) ═══════════════════════ */
const BLANK_CYCLE = { startDate: "", cycleLen: 28, periodLen: 5 };

function HistoryScreen({ profile, day, onNav }) {
  const [history, setHistory]   = useState([]);
  const [mode, setMode]         = useState(null);   // null | "add" | editId
  const [form, setForm]         = useState(BLANK_CYCLE);
  const [error, setError]       = useState("");
  const setF = (k, v) => { setForm(f => ({ ...f, [k]: v })); setError(""); };
  const todayStr = new Date().toISOString().slice(0, 10);

  const loadHistory = () =>
    fetch(`${API_BASE}/api/cycle/history`, { credentials: "include" })
      .then(r => r.json())
      .then(data => setHistory(Array.isArray(data) ? data : []));

  useEffect(() => { loadHistory(); }, []);

  const openAdd  = () => { setForm(BLANK_CYCLE); setError(""); setMode("add"); };
  const openEdit = (h) => { setForm({ startDate: h.startDate, cycleLen: h.cycleLen || 28, periodLen: h.periodLen || 5 }); setError(""); setMode(h.id); };
  const closeForm = () => { setMode(null); setError(""); };

  const submit = async () => {
    if (!form.startDate) { setError("Please pick a start date."); return; }
    const url  = mode === "add" ? "/api/cycle/history/add" : "/api/cycle/history/update";
    const body = mode === "add" ? form : { ...form, id: mode };
    const res  = await fetch(`${API_BASE}${url}`, {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await res.json();
    if (!res.ok) { setError(j.error || "Couldn't save."); return; }
    closeForm();
    loadHistory();
  };

  const del = async (id) => {
    await fetch(`${API_BASE}/api/cycle/history/delete`, {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id }),
    });
    loadHistory();
  };

  const lastPeriodDate = profile.lastPeriod ? new Date(profile.lastPeriod) : null;

  const DotsRow = ({ cycleLen, periodLen = profile.periodLen }) => {
    const total = Math.min(cycleLen || 28, 40);
    return (
      <div style={{ display: "flex", gap: 3, flexWrap: "wrap", marginTop: 8 }}>
        {Array.from({ length: total }).map((_, i) => {
          let color = "var(--border)";
          if (i < (periodLen || 5)) color = "var(--c-menstrual)";
          else if (i >= 6 && i <= 10) color = "var(--c-follicular)";
          else if (i >= 11 && i <= 15) color = "var(--sage)";
          else if (i >= 16) color = "color-mix(in oklab, var(--c-luteal) 60%, transparent)";
          return <span key={i} style={{ width: 10, height: 10, borderRadius: "50%", background: color, display: "inline-block" }} />;
        })}
      </div>
    );
  };

  const Stepper = ({ label, hint, value, min, max, onChange }) => (
    <div>
      <div style={{ fontSize: 12, color: "var(--mute)", marginBottom: 4 }}>{label}</div>
      <div className="ob-stepper-row" style={{ gap: 12, justifyContent: "flex-start" }}>
        <button onClick={() => onChange(Math.max(min, value - 1))}>−</button>
        <span className="display" style={{ fontSize: 26 }}>{value}</span>
        <button onClick={() => onChange(Math.min(max, value + 1))}>+</button>
        <span style={{ fontSize: 12, color: "var(--mute)", marginLeft: 4 }}>{hint}</span>
      </div>
    </div>
  );

  const CycleForm = ({ title }) => (
    <div className="card" style={{ marginTop: 14 }}>
      <div className="eyebrow" style={{ marginBottom: 14 }}>{title}</div>
      <div style={{ display: "flex", flexDirection: "column", gap: 14 }}>
        <div>
          <div style={{ fontSize: 12, color: "var(--mute)", marginBottom: 4 }}>Period start date</div>
          <input type="date" className="ob-input" style={{ padding: "8px 12px", fontSize: 14, maxWidth: 200 }}
            value={form.startDate} max={todayStr} onChange={e => setF("startDate", e.target.value)} />
        </div>
        <Stepper label="Cycle length" hint="days between two periods" value={form.cycleLen} min={15} max={60} onChange={v => setF("cycleLen", v)} />
        <Stepper label="Period length" hint="days of bleeding" value={form.periodLen} min={2} max={12} onChange={v => setF("periodLen", v)} />
        {error && <div className="ob-error-box">⚠ {error}</div>}
        <div style={{ display: "flex", gap: 8, marginTop: 4 }}>
          <button className="btn-primary btn-sm" onClick={submit} style={{ flex: 1 }}>✓ Save cycle</button>
          <button className="btn-ghost" onClick={closeForm}>Cancel</button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <div className="screen-hd">
        <div>
          <div className="eyebrow">Your cycle over time</div>
          <h1 className="screen-title display">Cycle <em>History</em></h1>
        </div>
        <button className="btn-outline" onClick={() => onNav("calendar")}>
          <Icon name="back" size={14} /> Back to calendar
        </button>
      </div>

      {/* Current cycle */}
      <div className="card" style={{ marginBottom: 12 }}>
        <div style={{ fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--mute)", marginBottom: 12, fontWeight: 500 }}>Current cycle</div>
        <div>
          <div style={{ fontSize: 20, fontWeight: 600 }}>Day {day}</div>
          <div style={{ fontSize: 13, color: "var(--mute)", marginTop: 2 }}>
            Started {lastPeriodDate ? lastPeriodDate.toLocaleDateString("en-GB", { day: "numeric", month: "short" }) : "—"}
          </div>
          <DotsRow cycleLen={profile.cycleLen} periodLen={profile.periodLen} />
        </div>
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", margin: "20px 0 10px" }}>
        <span style={{ fontSize: 11, letterSpacing: "0.14em", textTransform: "uppercase", color: "var(--mute)", fontWeight: 500 }}>Previous cycles</span>
        {mode !== "add" && (
          <button className="btn-outline" style={{ padding: "6px 14px" }} onClick={openAdd}>
            <Icon name="plus" size={14} /> Add a cycle
          </button>
        )}
      </div>

      {mode === "add" && <CycleForm title="Add a past cycle" />}

      {history.length === 0 && mode !== "add" ? (
        <div className="card" style={{ textAlign: "center", padding: 40 }}>
          <Icon name="calendar" size={28} />
          <p style={{ marginTop: 12, color: "var(--mute)" }}>
            No previous cycles yet. Log your next period on the Calendar page, or add a past cycle.
          </p>
        </div>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: 10, marginTop: 10 }}>
          {history.map((h) => {
            if (mode === h.id) return <CycleForm key={h.id} title="Edit cycle" />;
            const start = new Date(h.startDate);
            const end = h.cycleLen ? new Date(new Date(h.startDate).setDate(start.getDate() + h.cycleLen - 1)) : null;
            const fmt = (d) => d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
            return (
              <div key={h.id} className="cycle-card">
                {/* details */}
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 15, fontWeight: 600 }}>
                    {fmt(start)}{end ? ` – ${fmt(end)}` : ""}
                  </div>
                  <div style={{ display: "flex", gap: 8, marginTop: 6, flexWrap: "wrap" }}>
                    <span className="cycle-tag"><span className="dot-menstrual" />{h.cycleLen || "—"}-day cycle</span>
                    {h.periodLen ? <span className="cycle-tag">{h.periodLen}-day period</span> : null}
                  </div>
                  <DotsRow cycleLen={h.cycleLen} periodLen={h.periodLen} />
                </div>
                {/* actions */}
                <div style={{ display: "flex", gap: 6, flexShrink: 0 }}>
                  <button className="icon-btn-sm" title="Edit" onClick={() => openEdit(h)}><Icon name="settings" size={14} /></button>
                  <button className="icon-btn-sm cycle-del" title="Delete" onClick={() => del(h.id)}>×</button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </>
  );
}

/* ═══════════════════════ CHAT (Lea) ═══════════════════════ */
const QUICK_PROMPTS = [
  "Why am I so tired today?",
  "What should I eat?",
  "Is this cramping normal?",
  "I feel low — what helps?",
  "Should I work out today?",
];

function ChatScreen({ profile, day }) {
  const [messages, setMessages] = useState([
    { who: "bot", text: "Hi — I'm Lea. I can help you make sense of what you're feeling, suggest small things to try, or just listen. What's on your mind today?" },
  ]);
  const [input, setInput] = useState("");
  const [typing, setTyping] = useState(false);
  const scrollRef = useRef(null);
  const phase = phaseForDay(day, profile.cycleLen);

  useEffect(() => {
    if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
  }, [messages, typing]);

  async function send(text) {
    if (!text.trim() || typing) return;
    const userMsg = { who: "me", text };
    const history = [...messages, userMsg];
    setMessages(history);
    setInput("");
    setTyping(true);
    const reply = await api.veraReply(text, {
      day, phase: phase.name.toLowerCase(), profile, history,
    });
    setMessages(m => [...m, { who: "bot", text: reply }]);
    setTyping(false);
  }

  return (
    <div className="chat-wrap">
      <div className="chat-header">
        <div className="chat-avatar">L</div>
        <div>
          <h1>Lea</h1>
          <div className="chat-status"><span className="chat-dot" /> Online · cycle companion</div>
        </div>
      </div>

      <div className="chat-thread" ref={scrollRef}>
        {messages.map((m, i) => (
          <div key={i} className={`bubble bubble-${m.who}`}>
            {m.who === "bot" && <div className="bubble-avatar">L</div>}
            <div className="bubble-text">{m.text}</div>
          </div>
        ))}
        {typing && (
          <div className="bubble bubble-bot">
            <div className="bubble-avatar">L</div>
            <div className="bubble-text typing"><span/><span/><span/></div>
          </div>
        )}
      </div>

      <div className="chat-prompts">
        {QUICK_PROMPTS.map(q => (
          <button key={q} className="chip" onClick={() => send(q)}>{q}</button>
        ))}
      </div>

      <form className="chat-input" onSubmit={e => { e.preventDefault(); send(input); }}>
        <input value={input} onChange={e => setInput(e.target.value)} placeholder="Tell Lea how you're feeling…" />
        <button type="submit" className="icon-btn-solid" aria-label="Send"><Icon name="send" size={16} /></button>
      </form>
    </div>
  );
}

/* ═══════════════════════ ALERTS (Nadia's feature: ML + rule-based) ═══════════════════════ */
const ALERT_TITLES = {
  missed_log:    "Reminder to log your period",
  late_period:   "Your cycle ran a little long",
  irregularity:  "Cycle variation noticed",
  abnormal_pain: "Pain level higher than usual",
};
const ALERT_LEVEL_META = {
  info:           { dot: "🟢", label: "Info",             color: "var(--sage)" },
  attention:      { dot: "🟡", label: "Attention",        color: "var(--ochre)" },
  recommandation: { dot: "🔴", label: "Talk to a doctor", color: "var(--primary)" },
};
const ALERT_KIND_ICON = { missed_log: "calendar", late_period: "drop", irregularity: "moon", abnormal_pain: "sparkle" };

function AlertsScreen({ profile, day }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    // generate fresh alerts on demand (same logic as the WhatsApp job), then read them
    fetch(`${API_BASE}/api/alerting/refresh`, { method: "POST", credentials: "include" })
      .catch(() => {})
      .finally(() => {
        fetch(`${API_BASE}/api/alerting/alerts`, { credentials: "include" })
          .then(r => r.json())
          .then(data => setItems(Array.isArray(data) ? data : []))
          .catch(() => setItems([]))
          .finally(() => setLoading(false));
      });
  };

  useEffect(() => { load(); }, [day]);

  const sendFeedback = async (id, feedback) => {
    setItems(items.map(a => a.id === id ? { ...a, feedback } : a));
    try {
      await fetch(`${API_BASE}/api/alerting/alerts/${id}/feedback`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ feedback }),
      });
    } catch {}
  };

  const timeAgo = (isoDate) => {
    const days = Math.floor((Date.now() - new Date(isoDate).getTime()) / 86400000);
    if (days <= 0) return "today";
    if (days === 1) return "yesterday";
    return `${days} days ago`;
  };

  return (
    <>
      <div className="screen-hd">
        <div>
          <div className="eyebrow">Quiet, considered</div>
          <h1 className="screen-title display">Alerts</h1>
        </div>
      </div>

      <p className="lede" style={{ marginBottom: 24 }}>
        These flag statistical patterns in what you've logged — not a diagnosis.
        If something feels off, it's always worth a conversation with a professional.
      </p>

      <div className="alerts-wrap">
        {items.map(a => {
          const meta = ALERT_LEVEL_META[a.level] || ALERT_LEVEL_META.info;
          return (
            <article key={a.id} className="alert-row">
              <div className="alert-icon" style={{ background: `color-mix(in oklab, ${meta.color} 18%, transparent)`, color: meta.color }}>
                <Icon name={ALERT_KIND_ICON[a.type] || "info"} size={16} />
              </div>
              <div className="alert-body">
                <div className="alert-meta">
                  <span>{meta.dot} {meta.label}</span>
                  <span>· {timeAgo(a.sentAt)}</span>
                </div>
                <h3 className="alert-title">{ALERT_TITLES[a.type] || "Alert"}</h3>
                <p className="alert-text">{a.message}</p>
                <div style={{ display: "flex", gap: 8, marginTop: 10 }}>
                  <button className="chip"
                    style={a.feedback === "utile" ? { background: "var(--ink)", color: "var(--cream)", borderColor: "var(--ink)" } : {}}
                    onClick={() => sendFeedback(a.id, "utile")}>Helpful</button>
                  <button className="chip"
                    style={a.feedback === "pas_pertinent" ? { background: "var(--ink)", color: "var(--cream)", borderColor: "var(--ink)" } : {}}
                    onClick={() => sendFeedback(a.id, "pas_pertinent")}>Not relevant</button>
                </div>
              </div>
            </article>
          );
        })}
        {!loading && items.length === 0 && (
          <div className="info-card" style={{ textAlign: "center", padding: 48 }}>
            <Icon name="check" size={24} /><p style={{ marginTop: 12, color: "var(--mute)" }}>All clear. We'll let you know.</p>
          </div>
        )}
      </div>
    </>
  );
}

/* ═══════════════════════ SYMPTOM CATALOG + LOG SYMPTOMS (Nadia's feature) ═══════════════════════ */
const PAIN_LABEL = (v) => v === 0 ? "None" : v <= 3 ? "Mild" : v <= 6 ? "Moderate" : v <= 8 ? "Severe" : "Very severe";
const SYMPTOM_CATALOG = {
  Physical:         { icon: "heart",   items: ["Cramps", "Headache", "Backache", "Tender breasts", "Bloating", "Nausea"] },
  Mood:             { icon: "sparkle", items: ["Mood swings", "Anxious", "Irritable", "Low energy", "Happy", "Sensitive"] },
  "Skin & Hair":    { icon: "leaf",    items: ["Acne", "Oily skin", "Dry skin", "Hair changes"] },
  "Sleep & Energy": { icon: "moon",    items: ["Fatigue", "Insomnia", "Cravings", "Restless"] },
  Digestion:        { icon: "drop",    items: ["Constipation", "Diarrhea", "Gas", "Appetite changes"] },
};

function LogSymptomsScreen({ profile, day }) {
  const phase = phaseForDay(day, profile.cycleLen);
  const [suggestions, setSuggestions] = useState([]);
  const [selected, setSelected] = useState([]);
  const [painScore, setPainScore] = useState(3);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    setSaved(false);
    fetch(`${API_BASE}/api/alerting/suggestions?phase=${phase.id}`, { credentials: "include" })
      .then(r => r.json())
      .then(data => setSuggestions(Array.isArray(data) ? data : []))
      .catch(() => setSuggestions([]));
  }, [phase.id]);

  const toggle = (symptom) => setSelected(prev =>
    prev.includes(symptom) ? prev.filter(s => s !== symptom) : [...prev, symptom]
  );

  const save = async () => {
    setSaving(true); setError("");
    try {
      const res = await fetch(`${API_BASE}/api/alerting/symptom`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          date: new Date().toISOString().slice(0, 10),
          phase: phase.id, painScore, symptoms: selected,
        }),
      });
      if (!res.ok) throw new Error();
      setSaved(true); setSelected([]);
    } catch {
      setError("Couldn't save right now. Check the backend is running.");
    }
    setSaving(false);
  };

  return (
    <>
      <div className="screen-hd">
        <div>
          <div className="eyebrow">{phase.name} phase · day {day}</div>
          <h1 className="screen-title display">Log how you <em>feel</em>.</h1>
        </div>
      </div>
      <p className="lede">Tap everything that applies today — as few or as many as you like.</p>

      <div className="card" style={{ marginTop: 24 }}>
        {suggestions.length > 0 && (<>
          <div className="eyebrow" style={{ marginBottom: 12 }}>Suggested for your phase</div>
          <div className="chip-grid" style={{ marginBottom: 26 }}>
            {suggestions.map(s => (
              <button key={s.symptom} className={`chip ${selected.includes(s.symptom) ? "on" : ""}`}
                onClick={() => toggle(s.symptom)}>{s.symptom}</button>
            ))}
          </div>
        </>)}

        {Object.entries(SYMPTOM_CATALOG).map(([category, { icon, items }]) => (
          <div key={category} style={{ marginBottom: 22 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10 }}>
              <div className="tip-icon" style={{ width: 26, height: 26, marginBottom: 0 }}>
                <Icon name={icon} size={14} />
              </div>
              <span className="eyebrow" style={{ padding: 0 }}>{category}</span>
            </div>
            <div className="chip-grid">
              {items.map(symptom => (
                <button key={symptom} className={`chip ${selected.includes(symptom) ? "on" : ""}`}
                  onClick={() => toggle(symptom)}>{symptom}</button>
              ))}
            </div>
          </div>
        ))}

        <div className="eyebrow" style={{ marginTop: 10, marginBottom: 10, display: "flex", justifyContent: "space-between" }}>
          <span>Pain level</span>
          <span style={{ color: "var(--primary)" }}>{PAIN_LABEL(painScore)}</span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <input type="range" min="0" max="10" value={painScore}
            onChange={e => setPainScore(Number(e.target.value))}
            className="pain-slider"
            style={{ flex: 1, background: `linear-gradient(to right, var(--sage), var(--ochre) 55%, var(--primary)) 0/ ${painScore * 10}% 100% no-repeat, var(--border)` }} />
          <span className="display" style={{ fontSize: 26, width: 34, textAlign: "center", color: "var(--primary-deep)" }}>{painScore}</span>
        </div>

        {error && <p style={{ color: "var(--primary)", fontSize: 13, marginTop: 14 }}>{error}</p>}
        {saved && <p style={{ color: "var(--sage)", fontSize: 13, marginTop: 14 }}>Saved — thank you.</p>}

        <button className="btn-primary btn-block" style={{ marginTop: 20 }}
          disabled={saving} onClick={save}>
          {saving ? "Saving…" : <>Save entry{selected.length ? ` (${selected.length})` : ""} <Icon name="check" size={16} /></>}
        </button>
      </div>
    </>
  );
}

/* ═══════════════════════ PROFILE ═══════════════════════ */
function ProfileScreen({ profile, day, onReset, onUpdateProfile }) {
  const phase = phaseForDay(day, profile.cycleLen);
  const [editing, setEditing] = useState(false);
  const [avatarUrl, setAvatarUrl] = useState(profile.avatar || null);
  const [cycleCount, setCycleCount] = useState(0);
  const [draft, setDraft] = useState(null);
  const [alerting, setAlerting] = useState({ birthDate: "", phoneNumber: "", whatsappConsent: false });
  const setD = (key, val) => setDraft(d => ({ ...d, [key]: val }));

  useEffect(() => {
    fetch(`${API_BASE}/api/cycle/history`, { credentials: "include" })
      .then(r => r.json())
      .then(d => setCycleCount(Array.isArray(d) ? d.length : 0))
      .catch(() => {});
    fetch(`${API_BASE}/api/alerting/profile`, { credentials: "include" })
      .then(r => r.json())
      .then(d => setAlerting({ birthDate: d.birthDate || "", phoneNumber: d.phoneNumber || "", whatsappConsent: !!d.whatsappConsent }))
      .catch(() => {});
  }, []);

  const handleAvatarChange = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const form = new FormData();
    form.append("avatar", file);
    const res = await fetch(`${API_BASE}/api/profile/avatar`, { method: "POST", credentials: "include", body: form });
    const j = await res.json();
    if (j.url) { setAvatarUrl(j.url); onUpdateProfile({ ...profile, avatar: j.url }); }
  };

  const startEdit = () => {
    setDraft({
      name: profile.name, cycleLen: profile.cycleLen, periodLen: profile.periodLen, lastPeriod: profile.lastPeriod || "",
      birthDate: alerting.birthDate || "", phoneNumber: alerting.phoneNumber || "", whatsappConsent: alerting.whatsappConsent,
    });
    setEditing(true);
  };

  const cancelEdit = () => {
    setDraft(null);
    setEditing(false);
  };

  const save = () => {
    onUpdateProfile({ ...profile, name: draft.name.trim() || profile.name, cycleLen: draft.cycleLen, periodLen: draft.periodLen, lastPeriod: draft.lastPeriod });
    // save the alerting profile (age + WhatsApp) via the same top button
    fetch(`${API_BASE}/api/alerting/profile`, {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ birthDate: draft.birthDate || null, phoneNumber: draft.phoneNumber || null, whatsappConsent: draft.whatsappConsent }),
    }).catch(() => {});
    setAlerting({ birthDate: draft.birthDate, phoneNumber: draft.phoneNumber, whatsappConsent: draft.whatsappConsent });
    setDraft(null);
    setEditing(false);
  };

  const logout = async () => {
    try { await fetch(`${API_BASE}/api/auth/logout`, { method: "POST", credentials: "include" }); } catch {}
    onReset();
  };

  return (
    <>
      <div className="screen-hd">
        <div>
          <div className="eyebrow">Your cycle, your data</div>
          <h1 className="screen-title display">{profile.name}</h1>
        </div>
        {editing ? (
          <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
            <button className="btn-ghost" style={{ padding: "10px 14px" }} onClick={cancelEdit}>Cancel</button>
            <button className="btn-primary btn-sm" onClick={save}>Save changes</button>
          </div>
        ) : (
          <button className="btn-outline" onClick={startEdit}>
            <Icon name="settings" size={14} /> Edit profile
          </button>
        )}
      </div>

      <div className="prof-grid">
        <div>
          <div className="prof-hero">
            <div className="prof-avatar-wrap">
              {avatarUrl
                ? <img className="prof-avatar" src={avatarUrl} alt={profile.name} />
                : <div className="prof-avatar">{profile.name[0]}</div>}
              <label className="prof-avatar-edit" title="Change photo">
                <Icon name="plus" size={14} />
                <input type="file" accept="image/*" style={{ display: "none" }} onChange={handleAvatarChange} />
              </label>
            </div>
            <h2 className="prof-name display">{profile.name}</h2>
            <div className="prof-sub">{phase.name} phase · Day {day} of {profile.cycleLen}</div>
            <div className="stats-grid">
              <div className="stat"><div className="stat-val">{profile.cycleLen}</div><div className="stat-label">Avg cycle</div></div>
              <div className="stat"><div className="stat-val">{profile.periodLen}</div><div className="stat-label">Avg period</div></div>
              <div className="stat"><div className="stat-val">{cycleCount}</div><div className="stat-label">Cycles</div></div>
            </div>
          </div>
        </div>

        <div>
          <div className="prof-section">
            <div className="prof-section-hd">Profile</div>
            {editing && draft ? (<>
              <div className="prof-row">
                <span>Name</span>
                <input className="ob-input" style={{ width: 160, padding: "6px 10px", fontSize: 14 }} value={draft.name} onChange={e => setD("name", e.target.value)} />
              </div>
              <div className="prof-row">
                <span>Date of birth</span>
                <input type="date" className="ob-input" style={{ width: 160, padding: "6px 10px", fontSize: 14 }}
                  value={draft.birthDate || ""} max={new Date().toISOString().slice(0, 10)}
                  onChange={e => setD("birthDate", e.target.value)} />
              </div>
              <div className="prof-row">
                <span>Cycle length</span>
                <div className="ob-stepper-row" style={{ gap: 8 }}>
                  <button onClick={() => setD("cycleLen", Math.max(20, draft.cycleLen - 1))}>−</button>
                  <span>{draft.cycleLen} days</span>
                  <button onClick={() => setD("cycleLen", Math.min(40, draft.cycleLen + 1))}>+</button>
                </div>
              </div>
              <div className="prof-row">
                <span>Period length</span>
                <div className="ob-stepper-row" style={{ gap: 8 }}>
                  <button onClick={() => setD("periodLen", Math.max(2, draft.periodLen - 1))}>−</button>
                  <span>{draft.periodLen} days</span>
                  <button onClick={() => setD("periodLen", Math.min(10, draft.periodLen + 1))}>+</button>
                </div>
              </div>
            </>) : ([
              ["Name", profile.name || "—"],
              ["Date of birth", alerting.birthDate ? new Date(alerting.birthDate).toLocaleDateString("en-GB", { day:"numeric", month:"long", year:"numeric" }) : "—"],
              ["Cycle length", `${profile.cycleLen} days`],
              ["Period length", `${profile.periodLen} days`],
            ].map(([k,v]) => (
              <div key={k} className="prof-row"><span>{k}</span><span className="muted-small">{v}</span></div>
            )))}
          </div>

          <div className="prof-section">
            <div className="prof-section-hd">WhatsApp alerts</div>
            <p className="muted-small" style={{ margin: "0 0 4px" }}>Optional — get gentle cycle alerts on WhatsApp. Your age tunes the alert thresholds.</p>
            {editing && draft ? (<>
              <div className="prof-row">
                <span>WhatsApp number</span>
                <input type="tel" className="ob-input" style={{ width: 160, padding: "6px 10px", fontSize: 14 }}
                  placeholder="+33…" value={draft.phoneNumber || ""} onChange={e => setD("phoneNumber", e.target.value)} />
              </div>
              <div className="prof-row">
                <span>WhatsApp alerts</span>
                <select className="form-input" style={{ width: 100, padding: "4px 8px", fontSize: 13 }}
                  value={draft.whatsappConsent ? "On" : "Off"} onChange={e => setD("whatsappConsent", e.target.value === "On")}>
                  <option>Off</option><option>On</option>
                </select>
              </div>
            </>) : (<>
              <div className="prof-row"><span>WhatsApp number</span><span className="muted-small">{alerting.phoneNumber || "—"}</span></div>
              <div className="prof-row"><span>WhatsApp alerts</span><span className="muted-small">{alerting.whatsappConsent ? "On" : "Off"}</span></div>
            </>)}
          </div>

          <div className="prof-privacy">
            <Icon name="lock" size={18} />
            <div>
              <div className="prof-section-hd" style={{ margin: 0 }}>Your data stays yours</div>
              <p className="muted-small" style={{ margin: "4px 0 0" }}>All cycle data is stored on your device. We never share, sell, or use it to train models.</p>
            </div>
          </div>

          <div style={{ display: "flex", gap: 12, marginTop: 16 }}>
            <button className="btn-ghost" onClick={logout}>Sign out</button>
            <button className="btn-ghost" onClick={onReset}>Reset & re-onboard</button>
          </div>
        </div>
      </div>
    </>
  );
}
