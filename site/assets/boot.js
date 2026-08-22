// ---------- page-aware boot ----------
//
// Every page declares the data documents it needs (body[data-needs]) and loads
// only the section scripts it uses. A renderer runs only when its anchor element
// exists, so one script can serve several pages without guards of its own.

const RENDERERS = [
  ["renderTiles", "tiles"],
  ["renderPosChart", "c_pos"],
  ["renderAgeChart", "c_age"],
  ["renderSquadTable", "squad_table"],
  ["renderMinutesChart", "c_minutes"],
  ["renderGoalsChart", "c_goals"],
  ["renderPoolTable", "pool_table"],
  ["renderRoster", "roster_search"],
  ["renderBacktest", "backtest_table"],
  ["renderStability", "stability_table"],
  ["renderClubChart", "c_clubs"],
  ["renderLeagueBar", "league_bar"],
  ["renderFormsChart", "c_forms"],
  ["renderStyle", "c_style_pct"],
  ["renderResilience", "c_reply"],
  ["renderTempo", "c_bins"],
  ["renderImportance", "imp_table"],
  ["renderBench", "c_bench"],
  ["renderCaptains", "captains_table"],
  ["renderGoalkeepers", "gk_table"],
  ["renderStatusStrip", "c_strip"],
  ["renderDecadeChart", "c_decades"],
  ["renderFormChart", "c_form"],
  ["renderAfconChart", "c_afcon"],
  ["renderLegendsTables", "capped_table"],
  ["renderShootouts", "shootout_table"],
  ["renderPenalties", "pens_tiles"],
  ["renderCoaches", "coaches_table"],
  ["renderVenues", "c_venues"],
  ["renderEloChart", "c_elo_tl"],
  ["renderWinexpChart", "c_winexp"],
  ["renderPredictions", "c_pred"],
  ["renderProjChart", "c_proj_age"],
  ["renderPipeline", "pipeline_table"],
];

function setText(id, value) {
  const el = $(id);
  if (el) { el.textContent = value; }
}

function renderStatic() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.innerHTML = t(el.dataset.i18n);
  });
  if (DATA.history) {
    const h = DATA.history;
    setText("lead_history", t("s_history_lead",
      { pld: fmt(h.all_time.pld), first_year: h.first_match.slice(0, 4) }));
    setText("title_history", t("s_history",
      { last_year: h.last_match.slice(0, 4) }));
  }
  if (DATA.squad) {
    const asof = DATA.squad.as_of || "";
    const m = asof.match(/as of (.+?)(?:,|\.)/i);
    setText("lead_squad", t("s_squad_lead", { asof_short: m ? m[1] : "2026" }));
  }
  const search = $("pool_search");
  if (search) { search.placeholder = t("pool_search"); }
  const methodo = $("methodo");
  if (methodo) { methodo.innerHTML = t("method_html"); }
  if (DATA.meta) {
    const footer = $("footer_text");
    if (footer) {
      footer.innerHTML = t("footer", {
        date: DATA.meta.updated_on || DATA.meta.generated_at.slice(0, 10),
        mail: DATA.meta.contact,
      });
    }
  }
}

function renderAll() {
  CHARTS.splice(0).forEach(c => c.dispose());
  renderStatic();
  for (const [name, anchor] of RENDERERS) {
    const fn = window[name];
    if (typeof fn !== "function" || !document.getElementById(anchor)) { continue; }
    try {
      fn();
    } catch (err) {
      console.error(`${name} failed`, err);
    }
  }
}
window.renderAll = renderAll;

// reveal-on-scroll for cards and sections, disabled when the visitor asks for
// reduced motion
function initMotion() {
  if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) { return; }
  const targets = document.querySelectorAll(
    "main section, .card, .pcard, .mrow, .roster > *");
  if (!("IntersectionObserver" in window) || !targets.length) { return; }

  document.documentElement.classList.add("js-anim");
  targets.forEach(el => el.classList.add("reveal"));

  const show = (el, i) => {
    el.style.animationDelay = `${Math.min(i * 40, 240)}ms`;
    el.classList.add("in");
  };
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry, i) => {
      if (!entry.isIntersecting) { return; }
      show(entry.target, i);
      io.unobserve(entry.target);
    });
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.04 });
  targets.forEach(el => io.observe(el));

  // safety net: if the observer never reports (hidden tab, odd viewport), show
  // everything anyway rather than leave the page blank
  setTimeout(() => {
    document.querySelectorAll(".reveal:not(.in)").forEach((el, i) => show(el, i));
  }, 1200);
}

async function boot() {
  const base = document.body.dataset.base || "";
  const needs = (document.body.dataset.needs || "").split(",").filter(Boolean);
  DATA = {};
  if (needs.length) {
    const loaded = await Promise.all(needs.map(name =>
      fetch(`${base}data/${name}.json`).then(r => r.json()).catch(() => null)));
    needs.forEach((name, i) => { DATA[name] = loaded[i]; });
  }
  document.querySelectorAll(".lang button").forEach(b => {
    b.addEventListener("click", () => setLang(b.dataset.lang));
    b.classList.toggle("on", b.dataset.lang === LANG);
  });
  const search = $("pool_search");
  if (search) { search.addEventListener("input", renderPoolTable); }
  document.documentElement.lang = LANG;
  renderAll();
  initMotion();
  window.addEventListener("resize", () => CHARTS.forEach(c => c.resize()));
}

boot();
