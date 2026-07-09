/* ════════════════════════════════════════════════════════════════════════════
   onboarding.js — Onboarding component
   Welcome / login / forgot-password / multi-step register flow.
   ════════════════════════════════════════════════════════════════════════════ */

function Onboarding({ onDone }) {
  const [mode, setMode]               = useState("welcome"); // "welcome" | "login" | "register" | "forgot"
  const [step, setStep]               = useState(0);         // register steps 0-3
  const [email, setEmail]             = useState("");
  const [password, setPassword]       = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [forgotDone, setForgotDone]   = useState(false);
  const [fieldErrors, setFieldErrors] = useState({});
  const [authError, setAuthError]     = useState("");
  const [authLoading, setAuthLoading] = useState(false);
  const [name, setName]               = useState("");
  const [lastPeriod, setLastPeriod]   = useState("");
  const [cycleLen, setCycleLen]       = useState(28);
  const [periodLen, setPeriodLen]     = useState(5);

  const setFE = (key, msg) => setFieldErrors(p => ({ ...p, [key]: msg }));
  const clearFE = (key) => setFieldErrors(p => { const n = { ...p }; delete n[key]; return n; });

  // ── Login (existing account) ──────────────────────────────
  const handleLogin = async () => {
    if (!email.includes("@")) { setAuthError("Please enter a valid email address."); return; }
    if (!password)             { setAuthError("Please enter your password."); return; }
    setAuthLoading(true); setAuthError("");
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (res.status === 401) { setAuthError("Wrong email or password. Try again."); setAuthLoading(false); return; }
      if (!res.ok)            { setAuthError("Something went wrong. Please try again."); setAuthLoading(false); return; }
      const me = await fetch(`${API_BASE}/api/auth/me`, { credentials: "include" }).then(r => r.json());
      if (me.id && me.name && me.lastPeriod) {
        // complete profile → straight into the app
        onDone({ name: me.name, lastPeriod: me.lastPeriod, cycleLen: me.cycleLen || 28, periodLen: me.periodLen || 5, avatar: me.avatar, notifPrefs: me.notifPrefs });
      } else if (me.id) {
        // logged in but onboarding was never finished → collect what's missing
        setName(me.name || "");
        setCycleLen(me.cycleLen || 28);
        setPeriodLen(me.periodLen || 5);
        setMode("register");
        setStep(me.name ? 2 : 1); // have a name already? skip to "last period"
      } else {
        setAuthError("Something went wrong. Please try again.");
      }
    } catch { setAuthError("Cannot reach the server. Make sure the backend is running."); }
    setAuthLoading(false);
  };

  // ── Forgot password ──────────────────────────────────────
  const handleForgot = async () => {
    if (!email.includes("@")) { setAuthError("Please enter a valid email address."); return; }
    if (newPassword.length < 6) { setAuthError("New password must be at least 6 characters."); return; }
    setAuthLoading(true); setAuthError("");
    try {
      const res = await fetch(`${API_BASE}/api/auth/reset-password`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password: newPassword }),
      });
      const j = await res.json();
      if (!res.ok) { setAuthError(j.error || "Reset failed."); setAuthLoading(false); return; }
      setForgotDone(true);
    } catch { setAuthError("Cannot reach the server."); }
    setAuthLoading(false);
  };

  // ── Register step 0: create account ──────────────────────
  const handleRegister = async () => {
    if (!email.includes("@"))  { setAuthError("Please enter a valid email address."); return; }
    if (password.length < 6)   { setAuthError("Password must be at least 6 characters."); return; }
    setAuthLoading(true); setAuthError("");
    try {
      const reg = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (reg.status === 409) { setAuthError("This email is already registered. Log in instead."); setAuthLoading(false); return; }
      if (!reg.ok)            { const j = await reg.json(); setAuthError(j.error || "Registration failed."); setAuthLoading(false); return; }
      await fetch(`${API_BASE}/api/auth/login`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      setStep(1); // move to name step
    } catch { setAuthError("Cannot reach the server. Make sure the backend is running."); }
    setAuthLoading(false);
  };

  const canRegisterAdvance = () => {
    if (step === 0) return email.includes("@") && password.length >= 6;
    if (step === 1) return name.trim().length > 0;
    if (step === 2) return !!lastPeriod;
    return true;
  };
  const registerNext = () => {
    if (step === 0) { handleRegister(); return; }
    if (step < 3) setStep(step + 1);
    else onDone({ name: name.trim() || "friend", lastPeriod, cycleLen, periodLen });
  };

  const registerSteps = ["account","name","last period","cycle"];
  const switchMode = (m) => { setMode(m); setAuthError(""); setEmail(""); setPassword(""); };

  return (
    <div className="onboarding">
      <div className="ob-decor-panel">
        <div className="ob-wheel">
          <div className="ob-wheel-ring" />
          <div className="ob-wheel-text">w<em>2</em>w</div>
        </div>
        <div className="ob-quote">A quiet companion for your cycle — predictions, gentle alerts, and a kind ear when you need one.</div>
      </div>

      <div className="ob-form-panel">
        <div className="ob-form-hd">
          <div className="ob-brand">
            <div className="ob-brand-mark">w<em>2</em>w</div>
            <div className="ob-brand-sub">Women2Women</div>
          </div>
          {mode === "register" && (
            <div className="ob-dots">
              {registerSteps.map((_, i) => <span key={i} className={`ob-dot ${i <= step ? "on" : ""}`} />)}
            </div>
          )}
        </div>

        <div className="ob-body">

          {/* ── Welcome ── */}
          {mode === "welcome" && (<>
            <h1 className="ob-title">Women, <em>knowing</em> women.</h1>
            <p className="ob-sub">Track your cycle. Get personalised recommendations, predict your next period, and talk to a companion who understands your body.</p>
            <div className="ob-actions">
              <button className="btn-primary" onClick={() => switchMode("register")}>Create my profile <Icon name="arrow" size={16} /></button>
              <button className="btn-ghost" onClick={() => switchMode("login")}>Log in to existing account</button>
            </div>
          </>)}

          {/* ── Log in ── */}
          {mode === "login" && (<>
            <h1 className="ob-title">Welcome <em>back</em>.</h1>
            <p className="ob-sub">Sign in to pick up where you left off.</p>
            <input className={`ob-input${fieldErrors.email ? " input-error" : ""}`} type="email" placeholder="Email address" value={email}
              onChange={e => { setEmail(e.target.value); clearFE("email"); setAuthError(""); }} autoFocus
              onBlur={() => { if (email && !email.includes("@")) setFE("email", "Please enter a valid email address."); }}
              onKeyDown={e => e.key === "Enter" && handleLogin()} />
            {fieldErrors.email && <p className="ob-field-error">{fieldErrors.email}</p>}
            <input className={`ob-input${fieldErrors.password ? " input-error" : ""}`} type="password" placeholder="Password" value={password}
              onChange={e => { setPassword(e.target.value); clearFE("password"); setAuthError(""); }} style={{ marginTop: 10 }}
              onBlur={() => { if (password && password.length < 6) setFE("password", "Password must be at least 6 characters."); }}
              onKeyDown={e => e.key === "Enter" && handleLogin()} />
            {fieldErrors.password && <p className="ob-field-error">{fieldErrors.password}</p>}
            {authError && <div className="ob-error-box">⚠ {authError}</div>}
            <div className="ob-actions">
              <button className="ob-back" onClick={() => switchMode("welcome")}>← Back</button>
              <button className="btn-primary" disabled={authLoading} onClick={handleLogin}>
                {authLoading ? "Signing in…" : <>Sign in <Icon name="arrow" size={16} /></>}
              </button>
            </div>
            <p style={{ fontSize: 12, color: "#999", marginTop: 16 }}>
              No account yet? <button className="btn-ghost" style={{ fontSize: 12, padding: "2px 6px" }} onClick={() => switchMode("register")}>Create one</button>
            </p>
            <p style={{ fontSize: 12, color: "#999", marginTop: 6 }}>
              Forgot your password? <button className="btn-ghost" style={{ fontSize: 12, padding: "2px 6px" }} onClick={() => { switchMode("forgot"); setForgotDone(false); setNewPassword(""); }}>Reset it</button>
            </p>
          </>)}

          {/* ── Forgot password ── */}
          {mode === "forgot" && (<>
            <h1 className="ob-title">Reset your <em>password</em>.</h1>
            {forgotDone ? (<>
              <p className="ob-sub" style={{ color: "var(--sage)" }}>Password updated! You can now sign in.</p>
              <div className="ob-actions">
                <button className="btn-primary" onClick={() => switchMode("login")}>Sign in <Icon name="arrow" size={16} /></button>
              </div>
            </>) : (<>
              <p className="ob-sub">Enter your email and choose a new password.</p>
              <input className={`ob-input${fieldErrors.email ? " input-error" : ""}`} type="email" placeholder="Email address" value={email}
                onChange={e => { setEmail(e.target.value); clearFE("email"); setAuthError(""); }} autoFocus
                onBlur={() => { if (email && !email.includes("@")) setFE("email", "Please enter a valid email address."); }} />
              {fieldErrors.email && <p className="ob-field-error">{fieldErrors.email}</p>}
              <input className={`ob-input${fieldErrors.newPassword ? " input-error" : ""}`} type="password" placeholder="New password (min. 6 characters)" value={newPassword}
                onChange={e => { setNewPassword(e.target.value); clearFE("newPassword"); setAuthError(""); }} style={{ marginTop: 10 }}
                onBlur={() => { if (newPassword && newPassword.length < 6) setFE("newPassword", "Password must be at least 6 characters."); }}
                onKeyDown={e => e.key === "Enter" && handleForgot()} />
              {fieldErrors.newPassword && <p className="ob-field-error">{fieldErrors.newPassword}</p>}
              {authError && <div className="ob-error-box">⚠ {authError}</div>}
              <div className="ob-actions">
                <button className="ob-back" onClick={() => switchMode("login")}>← Back</button>
                <button className="btn-primary" disabled={authLoading} onClick={handleForgot}>
                  {authLoading ? "Resetting…" : <>Reset password <Icon name="arrow" size={16} /></>}
                </button>
              </div>
            </>)}
          </>)}

          {/* ── Register step 0: account ── */}
          {mode === "register" && step === 0 && (<>
            <h1 className="ob-title">Create your <em>account</em>.</h1>
            <p className="ob-sub">Your data stays yours. We use this to save and restore your cycle across devices.</p>
            <input className={`ob-input${fieldErrors.email ? " input-error" : ""}`} type="email" placeholder="Email address" value={email}
              onChange={e => { setEmail(e.target.value); clearFE("email"); setAuthError(""); }} autoFocus
              onBlur={() => { if (email && !email.includes("@")) setFE("email", "Please enter a valid email address."); }} />
            {fieldErrors.email && <p className="ob-field-error">{fieldErrors.email}</p>}
            <input className={`ob-input${fieldErrors.password ? " input-error" : ""}`} type="password" placeholder="Password (min 6 characters)" value={password}
              onChange={e => { setPassword(e.target.value); clearFE("password"); setAuthError(""); }} style={{ marginTop: 10 }}
              onBlur={() => { if (password && password.length < 6) setFE("password", "Password must be at least 6 characters."); }} />
            {fieldErrors.password && <p className="ob-field-error">{fieldErrors.password}</p>}
            {authError && <div className="ob-error-box">⚠ {authError}</div>}
            <div className="ob-actions">
              <button className="ob-back" onClick={() => switchMode("welcome")}>← Back</button>
              <button className="btn-primary" disabled={!canRegisterAdvance() || authLoading} onClick={registerNext}>
                {authLoading ? "Creating account…" : <>Continue <Icon name="arrow" size={16} /></>}
              </button>
            </div>
            <p style={{ fontSize: 12, color: "#999", marginTop: 16 }}>
              Already have an account? <button className="btn-ghost" style={{ fontSize: 12, padding: "2px 6px" }} onClick={() => switchMode("login")}>Log in</button>
            </p>
          </>)}

          {/* ── Register step 1: name ── */}
          {mode === "register" && step === 1 && (<>
            <h1 className="ob-title">What should we <em>call you</em>?</h1>
            <p className="ob-sub">First name only.</p>
            <input className="ob-input" placeholder="Your name" value={name}
              onChange={e => setName(e.target.value)} autoFocus
              onKeyDown={e => e.key === "Enter" && canRegisterAdvance() && registerNext()} />
            <div className="ob-actions">
              <button className="ob-back" onClick={() => setStep(0)}>← Back</button>
              <button className="btn-primary" disabled={!canRegisterAdvance()} onClick={registerNext}>Continue <Icon name="arrow" size={16} /></button>
            </div>
          </>)}

          {/* ── Register step 2: last period ── */}
          {mode === "register" && step === 2 && (<>
            <h1 className="ob-title">When did your <em>last period</em> start?</h1>
            <p className="ob-sub">A rough date is fine — you can refine it later in the log.</p>
            <input type="date" className="ob-input" value={lastPeriod}
              max={new Date().toISOString().slice(0,10)} onChange={e => setLastPeriod(e.target.value)} />
            <div className="ob-actions">
              <button className="ob-back" onClick={() => setStep(1)}>← Back</button>
              <button className="btn-primary" disabled={!canRegisterAdvance()} onClick={registerNext}>Continue <Icon name="arrow" size={16} /></button>
            </div>
          </>)}

          {/* ── Register step 3: cycle length ── */}
          {mode === "register" && step === 3 && (<>
            <h1 className="ob-title">How long is your <em>cycle</em>?</h1>
            <p className="ob-sub">From day 1 of one period to day 1 of the next. Average is 28 days.</p>
            <div className="ob-stepper-grid">
              <div className="ob-stepper">
                <div className="ob-stepper-lbl">Cycle</div>
                <div className="ob-stepper-row">
                  <button onClick={() => setCycleLen(Math.max(20, cycleLen - 1))}>−</button>
                  <span className="display">{cycleLen}<small>days</small></span>
                  <button onClick={() => setCycleLen(Math.min(40, cycleLen + 1))}>+</button>
                </div>
              </div>
              <div className="ob-stepper">
                <div className="ob-stepper-lbl">Period</div>
                <div className="ob-stepper-row">
                  <button onClick={() => setPeriodLen(Math.max(2, periodLen - 1))}>−</button>
                  <span className="display">{periodLen}<small>days</small></span>
                  <button onClick={() => setPeriodLen(Math.min(10, periodLen + 1))}>+</button>
                </div>
              </div>
            </div>
            <div className="ob-actions">
              <button className="ob-back" onClick={() => setStep(2)}>← Back</button>
              <button className="btn-primary" onClick={registerNext}>Begin <Icon name="arrow" size={16} /></button>
            </div>
          </>)}

        </div>
      </div>
    </div>
  );
}
