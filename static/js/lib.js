/* ════════════════════════════════════════════════════════════════════════════
   lib.js — shared foundation
   React hooks, cycle math, the API layer, and stub recommendation copy.
   Loaded first; everything below is shared with the other script files.
   ════════════════════════════════════════════════════════════════════════════ */

const { useState, useEffect, useRef } = React;

/* ═══════════════════════ CYCLE MATH ═══════════════════════ */
const CYCLE_LENGTH = 28;

const PHASE_META = [
  { id: "menstrual",  name: "Menstrual",  blurb: "Rest. Replenish. Honour the slow.", color: "var(--c-menstrual)"  },
  { id: "follicular", name: "Follicular", blurb: "Energy rising. Build, plan, begin.", color: "var(--c-follicular)" },
  { id: "ovulation",  name: "Ovulation",  blurb: "Peak. Connect, create, shine.",      color: "var(--c-ovulation)"  },
  { id: "luteal",     name: "Luteal",     blurb: "Slow turn inward. Finish & tidy.",   color: "var(--c-luteal)"     },
];

// Phase boundaries SCALE with cycle length: the luteal phase stays ~14 days
// (physiological constant), so ovulation lands ~14 days before the next period
// and the follicular phase absorbs the difference. This keeps the dial full for
// any cycle length instead of leaving a gap past day 28.
function phasesFor(cycle = CYCLE_LENGTH) {
  const ovStart = Math.max(7, cycle - 14);   // 14 for a 28-day cycle (matches the classic model)
  const bounds = [
    [1, 5],                    // menstrual
    [6, ovStart - 1],          // follicular
    [ovStart, ovStart + 2],    // ovulation (3 days)
    [ovStart + 3, cycle],      // luteal → always ends exactly at cycle length
  ];
  return PHASE_META.map((m, i) => ({ ...m, start: bounds[i][0], end: bounds[i][1] }));
}

const PHASES = phasesFor(CYCLE_LENGTH);   // default 28-day set, for static strips/legend
const phaseForDay = (day, cycle = CYCLE_LENGTH) => {
  const ph = phasesFor(cycle);
  return ph.find(p => day >= p.start && day <= p.end) || ph[0];
};
const daysUntilNextPeriod = (day, cycle = CYCLE_LENGTH) => ((cycle - day) % cycle) + 1;
const fmtDate = (d) => d.toLocaleDateString("en-GB", { weekday: "short", day: "numeric", month: "short" });
const addDays = (d, n) => { const r = new Date(d); r.setDate(r.getDate() + n); return r; };
const cycleDayFromDates = (lastStart, today, cycle = CYCLE_LENGTH) => {
  const days = Math.floor((today - lastStart) / 86400000);
  return ((days % cycle) + cycle) % cycle + 1;
};

/* ═══════════════════════ API LAYER ═══════════════════════
   Each function returns a Promise. Recommendations call the live Flask
   backend; the others fall back to local stubs so the UI works offline.
*/
const API_BASE = "";

const api = {
  // chatbot reply — calls the live Python backend (Qwen + LoRA + RAG).
  // ctx = { day, phase, profile, history }
  async veraReply(message, ctx) {
    try {
      const data = await fetch(`${API_BASE}/api/chat`, {
        method: "POST", credentials: "include",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message, ctx: { day: ctx.day, phase: ctx.phase } }),
      }).then(r => r.json());
      return data.reply || "Sorry, I couldn't come up with an answer just now.";
    } catch {
      return "I can't reach the server right now. Make sure the backend is running and try again.";
    }
  },

  // phase-aware recommendations — live call to the Python model
  async fetchRecommendations(ctx) {
    try {
      const feeling   = ctx.feeling || "";
      const cycleLen  = ctx.profile?.cycleLen  || 28;
      const periodLen = ctx.profile?.periodLen || 5;
      const data = await fetch(
        `${API_BASE}/api/recommendations?day=${ctx.day}&phase=${ctx.phase}&feeling=${encodeURIComponent(feeling)}&cycleLen=${cycleLen}&periodLen=${periodLen}`,
        { credentials: 'include' }
      ).then(r => r.json());
      return Array.isArray(data) ? data : TIPS_BY_PHASE[ctx.phase] || [];
    } catch {
      return TIPS_BY_PHASE[ctx.phase] || [];
    }
  },

  // next-period prediction (stub)
  async predictNextPeriod(ctx) {
    const daysToNext = daysUntilNextPeriod(ctx.day, ctx.profile.cycleLen);
    return {
      date: addDays(new Date(), daysToNext - 1).toISOString().slice(0, 10),
      daysToNext,
      confidence: 0.82
    };
  },
};

/* ═══════════════════════ TIP COPY (offline fallback) ═══════════════════════ */
const TIPS_BY_PHASE = {
  menstrual: [
    { kind: "food", title: "Iron-rich plates",      body: "Lentils, dark greens, beets. Pair with vitamin C to absorb more.", tag: "Nourish" },
    { kind: "move", title: "Slow movement",         body: "Gentle yin yoga or a long walk. Skip the HIIT today.", tag: "Move" },
    { kind: "mood", title: "Permission to rest",    body: "Your body is doing real work. Lights low, hot water bottle, kind self-talk.", tag: "Mind" },
    { kind: "care", title: "Cramp comfort",         body: "Magnesium-rich snacks (dark chocolate, pumpkin seeds) can take the edge off.", tag: "Care" },
  ],
  follicular: [
    { kind: "move", title: "Build the strength",    body: "Energy is climbing — a great week to add resistance work or try a new class.", tag: "Move" },
    { kind: "food", title: "Fresh and bright",      body: "Light proteins, fermented foods, citrus. Your gut is more receptive now.", tag: "Nourish" },
    { kind: "mood", title: "Start the thing",       body: "Better focus and risk tolerance — pitch the idea, send the message.", tag: "Mind" },
    { kind: "care", title: "Skin loves you back",   body: "Estrogen rising means clearer skin. Light moisturizer, SPF, leave it alone.", tag: "Care" },
  ],
  ovulation: [
    { kind: "mood", title: "Speak up",              body: "Verbal fluency peaks. Schedule the talk, the date, the interview.", tag: "Mind" },
    { kind: "food", title: "Antioxidants",          body: "Berries, cruciferous veg, plenty of water — support egg health and hydration.", tag: "Nourish" },
    { kind: "care", title: "Notice the signs",      body: "Egg-white cervical mucus, tender breasts, light twinges. All normal markers.", tag: "Care" },
    { kind: "move", title: "Train hard, recover well", body: "Strength gains are highest now. Lift heavy, then prioritize sleep.", tag: "Move" },
  ],
  luteal: [
    { kind: "food", title: "Steady your blood sugar", body: "Complex carbs plus protein every few hours keeps the mood swings smaller.", tag: "Nourish" },
    { kind: "mood", title: "Edit, don't begin",     body: "Better at finishing than starting now. Use it — close open loops.", tag: "Mind" },
    { kind: "move", title: "Walks > sprints",       body: "Pilates, walking, mobility work. Heavy cardio can spike cortisol.", tag: "Move" },
    { kind: "care", title: "Hydrate generously",    body: "Bloating eases with more water and less salt, not the other way round.", tag: "Care" },
  ],
};
