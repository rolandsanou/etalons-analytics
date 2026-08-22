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
  ["renderPartnerships", "pairs_table"],
  ["renderSubpatterns", "subs_table"],
  ["renderRest", "rest_table"],
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
  applyTheme(effectiveTheme());   // refresh the toggle's label in this language
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

// ---------- theme ----------
//
// Default is the operating system's preference; an explicit choice is remembered
// and wins over it. Charts read their colours from the CSS tokens, so switching
// means re-reading the tokens and re-rendering.

const THEME_KEY = "ea_theme";

function effectiveTheme() {
  const stored = localStorage.getItem(THEME_KEY);
  if (stored === "dark" || stored === "light") { return stored; }
  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark" : "light";
}

function applyTheme(theme, { persist = false } = {}) {
  const root = document.documentElement;
  if (persist) {
    localStorage.setItem(THEME_KEY, theme);
    root.setAttribute("data-theme", theme);
  } else if (localStorage.getItem(THEME_KEY)) {
    root.setAttribute("data-theme", theme);
  } else {
    // no explicit choice: let the media query decide, don't pin an attribute
    root.removeAttribute("data-theme");
  }
  const button = $("theme_toggle");
  if (button) {
    const dark = theme === "dark";
    button.setAttribute("aria-pressed", String(dark));
    button.setAttribute("aria-label", t(dark ? "theme_to_light" : "theme_to_dark"));
    button.title = t(dark ? "theme_to_light" : "theme_to_dark");
  }
}

function initTheme() {
  applyTheme(effectiveTheme());
  const button = $("theme_toggle");
  if (button && !button.dataset.wired) {
    button.dataset.wired = "1";
    button.addEventListener("click", () => {
      applyTheme(effectiveTheme() === "dark" ? "light" : "dark",
                 { persist: true });
      renderAll();               // repaint every chart from the new tokens
    });
  }
  // follow the OS while the visitor has not chosen explicitly
  window.matchMedia("(prefers-color-scheme: dark)")
    .addEventListener("change", () => {
      if (localStorage.getItem(THEME_KEY)) { return; }
      applyTheme(effectiveTheme());
      renderAll();
    });
}

function renderAll() {
  CHARTS.splice(0).forEach(c => c.dispose());
  readThemeTokens();
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
  // the FR/EN control is a pair of links to the counterpart page; the active
  // one is already marked by the generator, so there is nothing to wire here
  const search = $("pool_search");
  if (search) { search.addEventListener("input", renderPoolTable); }
  document.documentElement.lang = LANG;
  initTheme();
  renderAll();
  initMotion();
  window.addEventListener("resize", () => CHARTS.forEach(c => c.resize()));
}

boot();
