/* ════════════════════════════════════════════════════════════════════════════
   app.js — root component + mount
   Owns routing and the profile session, then renders the shell + active screen.
   Loaded last, after every component it references is defined.
   ════════════════════════════════════════════════════════════════════════════ */

function App() {
  const [route, setRoute]     = useState("onboarding");
  const [profile, setProfile] = useState(null);

  // On mount: only restore the session when the profile is COMPLETE.
  // An account that never finished onboarding (no name / no last period)
  // is left on the welcome screen instead of landing on a broken home.
  useEffect(() => {
    fetch(`${API_BASE}/api/auth/me`, { credentials: "include" })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data && data.id && data.name && data.lastPeriod) {
          setProfile({ name: data.name, lastPeriod: data.lastPeriod, cycleLen: data.cycleLen, periodLen: data.periodLen, avatar: data.avatar, notifPrefs: data.notifPrefs });
          setRoute("home");
        }
      }).catch(() => {});
  }, []);

  const day = profile && profile.lastPeriod
    ? cycleDayFromDates(new Date(profile.lastPeriod), new Date(), profile.cycleLen)
    : 14;

  const finishOnboarding = (p) => {
    fetch(`${API_BASE}/api/profile`, {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(p),
    });
    setProfile(p);
    setRoute("home");
  };

  const reset = () => { setProfile(null); setRoute("onboarding"); };

  const updateProfile = (p) => {
    fetch(`${API_BASE}/api/profile`, {
      method: "POST", credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(p),
    });
    setProfile(p);
  };

  if (route === "onboarding" || !profile) {
    return (
      <div className="app onboarding-mode">
        <Onboarding onDone={finishOnboarding} />
      </div>
    );
  }

  return (
    <div className="app">
      <Sidebar route={route} setRoute={setRoute} profile={profile} day={day} alertCount={2} />
      <div className="main">
        <Topbar route={route} day={day} cycleLen={profile.cycleLen} />
        <div className="content">
          {route === "home"     && <HomeScreen     profile={profile} day={day} />}
          {route === "calendar" && <CalendarScreen profile={profile} day={day} onUpdateProfile={updateProfile} onNav={setRoute} />}
          {route === "insights" && <InsightsScreen profile={profile} day={day} onNav={setRoute} />}
          {route === "symptoms" && <LogSymptomsScreen profile={profile} day={day} />}
          {route === "history"  && <HistoryScreen  profile={profile} day={day} onNav={setRoute} />}
          {route === "chat"     && <ChatScreen     profile={profile} day={day} />}
          {route === "alerts"   && <AlertsScreen   profile={profile} day={day} />}
          {route === "profile"  && <ProfileScreen  profile={profile} day={day} onReset={reset} onUpdateProfile={updateProfile} />}
        </div>
      </div>
    </div>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
