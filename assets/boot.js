// ---------- static text & boot ----------

function renderStatic() {
  document.querySelectorAll("[data-i18n]").forEach(el => {
    el.innerHTML = t(el.dataset.i18n);
  });
  const h = DATA.history;
  $("lead_history").textContent = t("s_history_lead",
    { pld: fmt(h.all_time.pld), first_year: h.first_match.slice(0, 4) });
  $("title_history").textContent = t("s_history", { last_year: h.last_match.slice(0, 4) });
  const asof = DATA.squad.as_of || "";
  const m = asof.match(/as of (.+?)(?:,|\.)/i);
  $("lead_squad").textContent = t("s_squad_lead", { asof_short: m ? m[1] : "2026" });
  $("pool_search").placeholder = t("pool_search");
  $("methodo").innerHTML = t("method_html");
  const d = DATA.meta.generated_at.slice(0, 10);
  $("footer_text").innerHTML = t("footer", { date: d });
}

function renderAll() {
  CHARTS.splice(0).forEach(c => c.dispose());
  renderStatic();
  renderTiles();
  renderPosChart();
  renderAgeChart();
  renderSquadTable();
  renderMinutesChart();
  renderGoalsChart();
  renderPoolTable();
  renderClubChart();
  renderLeagueBar();
  renderFormsChart();
  renderStyle();
  renderResilience();
  renderTempo();
  renderImportance();
  renderBench();
  renderCaptains();
  renderGoalkeepers();
  renderStatusStrip();
  renderDecadeChart();
  renderFormChart();
  renderAfconChart();
  renderLegendsTables();
  renderShootouts();
  renderPenalties();
  renderCoaches();
  renderVenues();
  renderEloChart();
  renderWinexpChart();
  renderProjChart();
  renderPipeline();
}
window.renderAll = renderAll;

async function boot() {
  const names = ["squad", "pool", "history", "elo", "team", "meta"];
  const res = await Promise.all(names.map(n => fetch(`data/${n}.json`).then(r => r.json())));
  DATA = Object.fromEntries(names.map((n, i) => [n, res[i]]));
  document.querySelectorAll(".lang button").forEach(b => {
    b.addEventListener("click", () => setLang(b.dataset.lang));
    b.classList.toggle("on", b.dataset.lang === LANG);
  });
  $("pool_search").addEventListener("input", renderPoolTable);
  document.documentElement.lang = LANG;
  renderAll();
  window.addEventListener("resize", () => CHARTS.forEach(c => c.resize()));
}

boot();
