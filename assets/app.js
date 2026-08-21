const S1 = "#2a78d6", S2 = "#eb6834", S3 = "#1baf7a", S4 = "#eda100", S5 = "#e87ba4";
const INK = "#0b0b0b", INK2 = "#52514e", MUTED = "#898781";
const GRID = "#e1e0d9", BASELINE = "#c3c2b7", SURFACE = "#fcfcfb", NEUTRAL = "#f0efec";
const POS_ORDER = ["GK", "DF", "MF", "FW"];
const PEAK = { GK: [26, 33], DF: [25, 30], MF: [24, 29], FW: [24, 29] };
const LEAGUE_ORDER = ["top5", "europe_other", "africa", "home", "world_other"];
const LEAGUE_COLOR = { top5: S1, europe_other: S2, africa: S3, home: S4, world_other: S5 };

let DATA = null;
const CHARTS = [];

const $ = id => document.getElementById(id);
const num = x => (x === "" || x === null || x === undefined) ? 0 : Number(x);

function axisX(extra) {
  return Object.assign({
    axisLine: { lineStyle: { color: BASELINE } },
    axisTick: { show: false },
    axisLabel: { color: MUTED, fontSize: 11 },
    splitLine: { show: false },
  }, extra || {});
}

function axisY(extra) {
  return Object.assign({
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: MUTED, fontSize: 11 },
    splitLine: { lineStyle: { color: GRID, width: 1 } },
  }, extra || {});
}

function tooltip(extra) {
  return Object.assign({
    backgroundColor: SURFACE,
    borderColor: "rgba(11,11,11,0.10)",
    borderWidth: 1,
    textStyle: { color: INK, fontSize: 12 },
    confine: true,
  }, extra || {});
}

function legend(extra) {
  return Object.assign({
    bottom: 0, itemWidth: 10, itemHeight: 10, icon: "roundRect",
    textStyle: { color: INK2, fontSize: 11.5 },
  }, extra || {});
}

function mkChart(id, option) {
  const el = $(id);
  if (!el) { return null; }
  const prev = echarts.getInstanceByDom(el);
  if (prev) { prev.dispose(); }
  const inst = echarts.init(el, null, { renderer: "svg" });
  inst.setOption(option);
  CHARTS.push(inst);
  return inst;
}

function tableView(cardId, headers, rows) {
  const card = $(cardId);
  if (!card) { return; }
  let d = card.querySelector("details.tv");
  if (!d) {
    d = document.createElement("details");
    d.className = "tv";
    card.appendChild(d);
  }
  const body = rows.map(r => `<tr>${r.map((c, i) =>
    `<td class="${i > 0 ? "num" : ""}">${c}</td>`).join("")}</tr>`).join("");
  d.innerHTML = `<summary>${t("show_data")}</summary><div class="tablewrap"><table>
    <tr>${headers.map((h, i) => `<th class="${i > 0 ? "num" : ""}">${h}</th>`).join("")}</tr>${body}</table></div>`;
}

// ---------- tiles ----------

function renderTiles() {
  const e = DATA.elo, s = DATA.squad.stats, h = DATA.history, p = DATA.pool;
  const tiles = [
    [t("tile_caf"), `#${e.caf_rank}`, t("tile_caf_sub", { world: e.world_rank, n: e.n_caf })],
    [t("tile_elo"), fmt(Math.round(e.current)), t("tile_elo_sub",
      { peak: fmt(Math.round(e.peak.elo)), year: e.peak.date.slice(0, 4) })],
    [t("tile_age"), fmt(s.avg_age, 1), t("tile_age_sub", { median: fmt(s.median_age, 1) })],
    [t("tile_europe"), fmt(s.pct_europe) + " %", t("tile_europe_sub",
      { top5: s.by_league_group.top5 || 0 })],
    [t("tile_record"), fmt(h.all_time.pld), t("tile_record_sub", { w: fmt(h.all_time.win_pct) })],
    [t("tile_pool"), fmt(p.n_players), t("tile_pool_sub", { events: p.coverage.events })],
  ];
  $("tiles").innerHTML = tiles.map(([label, value, sub]) =>
    `<div class="tile"><div class="label">${label}</div><div class="value">${value}</div>
     <div class="sub">${sub}</div></div>`).join("");
}

// ---------- squad section ----------

function posLabel(p) { return t("pos_" + p); }

function renderPosChart() {
  const byPos = DATA.squad.stats.by_pos;
  const cats = POS_ORDER.map(posLabel);
  const vals = POS_ORDER.map(p => byPos[p] || 0);
  mkChart("c_pos", {
    grid: { left: 8, right: 34, top: 8, bottom: 8, containLabel: true },
    tooltip: tooltip({ trigger: "item" }),
    xAxis: axisX({ type: "value", show: false }),
    yAxis: axisY({ type: "category", data: cats, inverse: true,
      splitLine: { show: false }, axisLabel: { color: INK2, fontSize: 12 } }),
    series: [{
      type: "bar", data: vals, barMaxWidth: 18,
      itemStyle: { color: S1, borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: "right", color: INK2, fontSize: 11.5 },
    }],
  });
  tableView("card_pos", [t("h_pos"), "N"], POS_ORDER.map(p => [posLabel(p), byPos[p] || 0]));
}

function renderAgeChart() {
  const buckets = ["≤20", "21–23", "24–26", "27–29", "30–32", "33+"];
  const byB = DATA.squad.stats.by_bucket;
  const vals = buckets.map(b => byB[b] || 0);
  mkChart("c_age", {
    grid: { left: 8, right: 8, top: 20, bottom: 4, containLabel: true },
    tooltip: tooltip({ trigger: "item" }),
    xAxis: axisX({ type: "category", data: buckets }),
    yAxis: axisY({ type: "value", minInterval: 1 }),
    series: [{
      type: "bar", data: vals, barMaxWidth: 22,
      itemStyle: { color: S1, borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: "top", color: INK2, fontSize: 11.5 },
    }],
  });
  tableView("card_age", [t("h_age"), "N"], buckets.map((b, i) => [b, vals[i]]));
}

function phasePill(phase) {
  return phase ? `<span class="pill">${t("phase_" + phase)}</span>` : "";
}

function renderSquadTable() {
  const rows = [...DATA.squad.players].sort((a, b) =>
    POS_ORDER.indexOf(a.pos) - POS_ORDER.indexOf(b.pos) || b.caps - a.caps);
  $("squad_table").innerHTML = `<tr>
    <th>${t("h_player")}</th><th>${t("h_pos")}</th><th class="num">${t("h_age")}</th>
    <th class="num">${t("h_caps")}</th><th class="num">${t("h_goals")}</th>
    <th>${t("h_club")}</th><th>${t("h_country")}</th><th class="num">${t("h_age27")}</th></tr>` +
    rows.map(p => `<tr><td>${p.name}</td><td>${p.pos}</td>
      <td class="num">${fmt(p.age, 1)}</td><td class="num">${fmt(p.caps)}</td>
      <td class="num">${fmt(p.goals)}</td>
      <td>${p.club ? p.club + (p.club_verified ? ' <span class="vmark" title="' + t("club_verified_tip") + '">✓</span>' : ' <span class="wmark" title="' + t("club_wiki_tip") + '">⚠</span>') : "–"}</td>
      <td>${p.club_country || "–"}</td>
      <td class="num">${fmt(p.age_afcon27, 1)} ${phasePill(p.phase_afcon27)}</td></tr>`).join("");
  const cu = DATA.squad.callups;
  $("callups_table").innerHTML = `<tr>
    <th>${t("h_player")}</th><th>${t("h_pos")}</th><th class="num">${t("h_age")}</th>
    <th class="num">${t("h_caps")}</th><th>${t("h_club")}</th><th>${t("h_country")}</th></tr>` +
    cu.map(p => `<tr><td>${p.name}</td><td>${p.pos}</td><td class="num">${fmt(p.age, 1)}</td>
      <td class="num">${fmt(p.caps)}</td><td>${p.club || "–"}</td>
      <td>${p.club_country || "–"}</td></tr>`).join("");
}

// ---------- pool (players, 4 years) ----------

function renderMinutesChart() {
  const top = DATA.pool.profiles.slice(0, 15);
  mkChart("c_minutes", {
    grid: { left: 8, right: 44, top: 8, bottom: 8, containLabel: true },
    tooltip: tooltip({
      trigger: "item",
      formatter: p => {
        const r = top[p.dataIndex];
        return `<b>${r.name}</b> · ${r.pos}<br/>${fmt(r.minutes)} min · ${r.apps} matchs · ${fmt(num(r.rating_avg), 2)} ⌀`;
      },
    }),
    xAxis: axisX({ type: "value", show: false }),
    yAxis: axisY({ type: "category", inverse: true, splitLine: { show: false },
      data: top.map(p => p.name), axisLabel: { color: INK2, fontSize: 11.5 } }),
    series: [{
      type: "bar", data: top.map(p => num(p.minutes)), barMaxWidth: 14,
      itemStyle: { color: S1, borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: "right", color: MUTED, fontSize: 10.5,
        formatter: p => fmt(p.value) },
    }],
  });
  tableView("card_minutes", [t("h_player"), t("h_min"), t("h_apps")],
    top.map(p => [p.name, fmt(p.minutes), p.apps]));
}

function renderGoalsChart() {
  const top = [...DATA.pool.profiles]
    .filter(p => num(p.goals) + num(p.assists) > 0)
    .sort((a, b) => (num(b.goals) + num(b.assists)) - (num(a.goals) + num(a.assists)))
    .slice(0, 10);
  mkChart("c_goals", {
    grid: { left: 8, right: 34, top: 8, bottom: 28, containLabel: true },
    tooltip: tooltip({ trigger: "axis", axisPointer: { type: "shadow" } }),
    legend: legend(),
    xAxis: axisX({ type: "value", show: false }),
    yAxis: axisY({ type: "category", inverse: true, splitLine: { show: false },
      data: top.map(p => p.name), axisLabel: { color: INK2, fontSize: 11.5 } }),
    series: [
      { name: t("goals_g"), type: "bar", stack: "ga", data: top.map(p => num(p.goals)),
        barMaxWidth: 14, itemStyle: { color: S1, borderColor: SURFACE, borderWidth: 1 } },
      { name: t("goals_a"), type: "bar", stack: "ga", data: top.map(p => num(p.assists)),
        barMaxWidth: 14,
        itemStyle: { color: S2, borderColor: SURFACE, borderWidth: 1, borderRadius: [0, 4, 4, 0] },
        label: { show: true, position: "right", color: MUTED, fontSize: 10.5,
          formatter: p => fmt(num(top[p.dataIndex].goals) + num(top[p.dataIndex].assists)) } },
    ],
  });
  tableView("card_goals", [t("h_player"), t("goals_g"), t("goals_a")],
    top.map(p => [p.name, p.goals, p.assists]));
}

function statusPill(s) {
  if (!s) { return "–"; }
  const cls = { active: "active", fringe: "fringe", out: "out",
    retired_int: "retired", retired_career: "retired" }[s] || "out";
  return `<span class="pill st ${cls}">${t("st_" + s)}</span>`;
}

function clubCell(p) {
  const club = p.club_v || p.club;
  if (!club) { return "–"; }
  const mark = p.club_v
    ? `<span class="vmark" title="${t("club_verified_tip")}">✓</span>`
    : `<span class="wmark" title="${t("club_wiki_tip")}">⚠</span>`;
  return `${club} ${mark}`;
}

function mvCell(v) {
  return num(v) ? fmt(num(v) / 1e6, 1) + " M€" : "–";
}

const POOL_COLS = [
  { key: "name", label: "h_player", numFmt: null },
  { key: "pos", label: "h_pos", numFmt: null },
  { key: "status", label: "h_status", numFmt: null },
  { key: "age", label: "h_age", numFmt: v => fmt(v, 1) },
  { key: "n_windows", label: "h_windows", numFmt: v => fmt(v) },
  { key: "matchday_squads", label: "h_sheets", numFmt: v => fmt(v) },
  { key: "apps", label: "h_apps", numFmt: v => fmt(v) },
  { key: "starts", label: "h_starts", numFmt: v => fmt(v) },
  { key: "minutes", label: "h_min", numFmt: v => fmt(v) },
  { key: "goals", label: "h_goals", numFmt: v => fmt(v) },
  { key: "assists", label: "h_assists", numFmt: v => fmt(v) },
  { key: "pass_pct", label: "h_passpct", numFmt: v => v ? fmt(v, 1) : "–" },
  { key: "dribbles_won", label: "h_dribbles", numFmt: null },
  { key: "interceptions", label: "h_inter", numFmt: v => fmt(v) },
  { key: "saves", label: "h_saves", numFmt: v => num(v) ? fmt(v) : "–" },
  { key: "rating_avg", label: "h_rating", numFmt: v => v ? fmt(v, 2) : "–" },
  { key: "club_v", label: "h_club", numFmt: null },
  { key: "league_v", label: "h_league", numFmt: null },
  { key: "market_value_eur", label: "h_mv", numFmt: null },
];
let poolSort = { key: "minutes", dir: -1 };

function renderPoolTable() {
  const q = ($("pool_search").value || "").toLowerCase();
  let rows = DATA.pool.profiles.filter(p => !q || p.name.toLowerCase().includes(q));
  const k = poolSort.key;
  rows = [...rows].sort((a, b) => {
    if (["name", "pos", "status", "club_v", "league_v"].includes(k)) {
      return poolSort.dir * String(a[k] || "").localeCompare(String(b[k] || ""));
    }
    return poolSort.dir * (num(a[k]) - num(b[k]));
  });
  const head = POOL_COLS.map(c =>
    `<th class="${c.key === "name" || c.key === "pos" ? "" : "num"} sortable ${poolSort.key === c.key ? "sorted" : ""}"
        data-key="${c.key}">${t(c.label)}${poolSort.key === c.key ? (poolSort.dir < 0 ? " ↓" : " ↑") : ""}</th>`).join("");
  const body = rows.map(p => "<tr>" + POOL_COLS.map(c => {
    if (c.key === "name") { return `<td>${p.name}</td>`; }
    if (c.key === "pos") { return `<td>${p.pos || "–"}</td>`; }
    if (c.key === "status") { return `<td>${statusPill(p.status)}</td>`; }
    if (c.key === "club_v") { return `<td>${clubCell(p)}</td>`; }
    if (c.key === "league_v") { return `<td>${p.league_v || "–"}</td>`; }
    if (c.key === "market_value_eur") { return `<td class="num">${mvCell(p.market_value_eur)}</td>`; }
    if (c.key === "dribbles_won") {
      const won = num(p.dribbles_won), att = num(p.dribbles_attempted);
      return `<td class="num">${att ? `${won}/${att}` : "–"}</td>`;
    }
    return `<td class="num">${c.numFmt ? c.numFmt(p[c.key]) : p[c.key]}</td>`;
  }).join("") + "</tr>").join("");
  $("pool_table").innerHTML = `<tr>${head}</tr>${body}`;
  $("pool_table").querySelectorAll("th.sortable").forEach(th => {
    th.addEventListener("click", () => {
      const key = th.dataset.key;
      poolSort = { key, dir: poolSort.key === key ? -poolSort.dir : -1 };
      renderPoolTable();
    });
  });
  const cov = DATA.pool.coverage;
  const played = DATA.pool.profiles.reduce((s, p) => s + num(p.apps), 0);
  const detailed = DATA.pool.profiles.reduce((s, p) => s + num(p.detailed_apps), 0);
  $("pool_note").textContent = t("pool_min_note", {
    pct: fmt(100 * detailed / Math.max(played, 1), 0),
    events_stats: cov.events_with_stats, events: cov.events,
  });
}

// ---------- breakdowns ----------

function renderClubChart() {
  const counts = Object.entries(DATA.squad.stats.by_club_country)
    .sort((a, b) => b[1] - a[1]);
  const top = counts.slice(0, 12);
  const rest = counts.slice(12).reduce((s, kv) => s + kv[1], 0);
  if (rest) { top.push([LANG === "fr" ? "Autres" : "Other", rest]); }
  mkChart("c_clubs", {
    grid: { left: 8, right: 30, top: 8, bottom: 8, containLabel: true },
    tooltip: tooltip({ trigger: "item" }),
    xAxis: axisX({ type: "value", show: false }),
    yAxis: axisY({ type: "category", inverse: true, splitLine: { show: false },
      data: top.map(kv => kv[0]), axisLabel: { color: INK2, fontSize: 11.5 } }),
    series: [{
      type: "bar", data: top.map(kv => kv[1]), barMaxWidth: 14,
      itemStyle: { color: S1, borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: "right", color: INK2, fontSize: 11 },
    }],
  });
  tableView("card_clubs", [t("h_country"), "N"], counts.map(kv => [kv[0], kv[1]]));
}

function renderLeagueBar() {
  const byG = DATA.squad.stats.by_league_group;
  const total = LEAGUE_ORDER.reduce((s, g) => s + (byG[g] || 0), 0);
  $("league_bar").innerHTML = LEAGUE_ORDER.filter(g => byG[g]).map(g =>
    `<div class="seg" style="width:${100 * byG[g] / total}%;background:${LEAGUE_COLOR[g]}"
      title="${t("lg_" + g)}: ${byG[g]}"></div>`).join("");
  $("league_legend").innerHTML = LEAGUE_ORDER.filter(g => byG[g]).map(g =>
    `<span class="lg-item"><span class="swatch" style="background:${LEAGUE_COLOR[g]}"></span>
     ${t("lg_" + g)} <b>${byG[g]}</b></span>`).join("");
  tableView("card_leagues", [t("c_leagues"), "N"],
    LEAGUE_ORDER.filter(g => byG[g]).map(g => [t("lg_" + g), byG[g]]));
}

// ---------- formations ----------

const ST_GOOD = "#0ca30c", ST_CRIT = "#d03b3b";

function formationLabel(r) {
  if (r.formation !== "others") { return r.formation; }
  const n = (r.pooled_from || "").split(";").filter(Boolean).length;
  return t("forms_other", { n });
}

function renderFormsChart() {
  const rows = DATA.team.formations;
  const cats = rows.map(formationLabel);
  const tip = r => `<b>${formationLabel(r)}</b><br/>` + t("forms_tip", {
    n: r.matches, ppg: fmt(r.ppg, 2), gf: r.gf, gfpm: fmt(r.gf_pm, 2),
    ga: r.ga, gapm: fmt(r.ga_pm, 2),
    elo: r.opp_elo_avg ? fmt(r.opp_elo_avg) : "–", nelo: r.n_elo,
  });
  const seg = (name, key, color, labelColor, radius) => ({
    name, type: "bar", stack: "wdl",
    data: rows.map(r => num(r[key])),
    barMaxWidth: 18,
    itemStyle: { color, borderColor: SURFACE, borderWidth: 1,
      borderRadius: radius || 0 },
    label: { show: true, color: labelColor, fontSize: 11,
      formatter: p => (p.value > 0 ? p.value : "") },
  });
  mkChart("c_forms", {
    grid: { left: 8, right: 30, top: 8, bottom: 28, containLabel: true },
    tooltip: tooltip({ trigger: "axis", axisPointer: { type: "shadow" },
      formatter: params => tip(rows[params[0].dataIndex]) }),
    legend: legend(),
    xAxis: axisX({ type: "value", show: false }),
    yAxis: axisY({ type: "category", inverse: true, splitLine: { show: false },
      data: cats, axisLabel: { color: INK2, fontSize: 12 } }),
    series: [
      seg(t("legend_w"), "w", ST_GOOD, "#fff"),
      seg(t("legend_d"), "d", BASELINE, INK2),
      seg(t("legend_l"), "l", ST_CRIT, "#fff", [0, 4, 4, 0]),
    ],
  });
  tableView("card_forms",
    ["", "Pld", t("legend_w"), t("legend_d"), t("legend_l"), "BM/GF", "BE/GA",
     "Pts/m", "Elo adv.", "n Elo"],
    rows.map(r => [formationLabel(r), r.matches, r.w, r.d, r.l, r.gf, r.ga,
      fmt(r.ppg, 2), r.opp_elo_avg ? fmt(r.opp_elo_avg) : "–", r.n_elo]));
}

// ---------- tempo (goal timing & game states) ----------

function rgba(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

function renderTempo() {
  const tl = DATA.team.timeline;
  const bins = tl.bins, s = tl.summary;
  $("lead_tempo").textContent = t("s_tempo_lead", { n: s.matches });
  const cats = bins.map(b => t("bin_" + b.bin));
  const seg = (name, data, color, stack, label) => ({
    name, type: "bar", stack, data, barMaxWidth: 16,
    itemStyle: { color, borderColor: SURFACE, borderWidth: 1 },
    label: label ? { show: true, position: "inside", fontSize: 10.5,
      color: "#fff", formatter: p => (p.value > 0 ? p.value : "") } : { show: false },
  });
  mkChart("c_bins", {
    grid: { left: 8, right: 8, top: 12, bottom: 56, containLabel: true },
    tooltip: tooltip({
      trigger: "axis", axisPointer: { type: "shadow" },
      formatter: params => {
        const b = bins[params[0].dataIndex];
        return `<b>${t("bin_" + b.bin)}</b><br/>${t("legend_gf")}: ${b.gf}` +
          (b.gf_stoppage ? ` (${b.gf_stoppage} 90+/45+)` : "") +
          `<br/>${t("legend_ga")}: ${b.ga}` +
          (b.ga_stoppage ? ` (${b.ga_stoppage} 90+/45+)` : "");
      },
    }),
    legend: legend({ data: [t("legend_gf"), t("legend_gf_stop"),
                            t("legend_ga"), t("legend_ga_stop")] }),
    xAxis: axisX({ type: "category", data: cats }),
    yAxis: axisY({ type: "value", minInterval: 1 }),
    series: [
      seg(t("legend_gf"), bins.map(b => b.gf - b.gf_stoppage), S1, "gf", true),
      seg(t("legend_gf_stop"), bins.map(b => b.gf_stoppage), rgba(S1, 0.45), "gf"),
      seg(t("legend_ga"), bins.map(b => b.ga - b.ga_stoppage), S2, "ga", true),
      seg(t("legend_ga_stop"), bins.map(b => b.ga_stoppage), rgba(S2, 0.45), "ga"),
    ],
  });
  const chi = side => {
    const c = s.chi2[side];
    if (!c.significant) { return null; }
    return t(c.direction === "low" ? "chi_low" : "chi_high",
      { side: t("side_" + side), bin: t("bin_" + c.bin), stat: fmt(c.stat, 1) });
  };
  const notes = [chi("gf"), chi("ga")].filter(Boolean);
  $("chi_note").textContent = notes.length ? notes.join(" ") : t("chi_none");
  tableView("card_bins", ["", t("legend_gf"), t("legend_gf_stop"), t("legend_ga"), t("legend_ga_stop")],
    bins.map(b => [t("bin_" + b.bin), b.gf, b.gf_stoppage, b.ga, b.ga_stoppage]));

  const rec = r => `${r.w}V-${r.d}N-${r.l}D`;
  const mt = (label, value, sub) =>
    `<div class="mt"><div class="label">${label}</div><div class="value">${value}</div>
     <div class="sub">${sub}</div></div>`;
  $("tempo_tiles").innerHTML =
    mt(t("t_scored_first"), `${fmt(s.scored_first.ppg, 2)} ${t("pts_per_match")}`,
       `${rec(s.scored_first)} (${s.scored_first.n})`) +
    mt(t("t_conceded_first"), `${fmt(s.conceded_first.ppg, 2)} ${t("pts_per_match")}`,
       `${rec(s.conceded_first)} (${s.conceded_first.n})`) +
    mt(t("t_comebacks"), `${s.comeback_wins} V · ${s.rescued_draws} N`, "&nbsp;") +
    mt(t("t_blown"), `${s.blown_leads} D · ${s.dropped_leads} N`, "&nbsp;");
  const states = [["leading", ST_GOOD], ["level", BASELINE], ["trailing", ST_CRIT]];
  $("state_bar").innerHTML = states.map(([k, c]) =>
    `<div class="seg" style="width:${s.minutes["pct_" + k]}%;background:${c}"></div>`).join("");
  $("state_legend").innerHTML = states.map(([k, c]) =>
    `<span class="lg-item"><span class="swatch" style="background:${c}"></span>
     ${t("st_" + k)} <b>${fmt(s.minutes["pct_" + k])} %</b></span>`).join("");
}

// ---------- player importance & bench ----------

let impSelected = null;

function signed(v, dec = 2) {
  if (v === "" || v === null || v === undefined) { return "–"; }
  return (v > 0 ? "+" : "") + fmt(v, dec);
}

function tierChip(tier) {
  if (!tier) { return "–"; }
  return `<span class="chip tier-${tier}">${t("tier_" + tier)}</span>`;
}

function renderImportance() {
  const imp = DATA.pool.importance.filter(r => r.window_matches >= 8);
  $("pilier_note").textContent =
    imp.some(r => r.tier === "pilier") ? "" : t("no_pilier_note");
  const top = imp.slice(0, 18);
  $("imp_table").innerHTML = `<tr>
    <th>${t("h_player")}</th><th>${t("h_tier")}</th><th class="num">${t("h_share")}</th>
    <th class="num">${t("h_min")}</th><th class="num">${t("h_starts")}</th>
    <th class="num">${t("h_onoff")}</th><th class="num">${t("h_ppgdiff")}</th>
    <th class="num">${t("h_ga90")}</th><th class="num">${t("h_rating")}</th></tr>` +
    top.map(r => `<tr><td>${r.name}</td><td>${tierChip(r.tier)}</td>
      <td class="num">${fmt(100 * r.minutes_share)} %</td>
      <td class="num">${fmt(r.on_min)}</td>
      <td class="num">${r.starts}/${r.squad_matches}</td>
      <td class="num">${signed(r.onoff_diff)}</td>
      <td class="num">${signed(r.ppg_diff)}</td>
      <td class="num">${r.ga90 === "" ? "–" : fmt(r.ga90, 2)}</td>
      <td class="num">${r.rating_avg === "" ? "–" : fmt(r.rating_avg, 2)}</td></tr>`).join("");

  const picker = $("imp_picker");
  const options = imp.slice(0, 25);
  if (!impSelected || !options.some(r => r.player_id === impSelected)) {
    impSelected = options.length ? options[0].player_id : null;
  }
  picker.innerHTML = options.map(r =>
    `<option value="${r.player_id}" ${r.player_id === impSelected ? "selected" : ""}>${r.name}</option>`).join("");
  picker.onchange = () => { impSelected = picker.value; renderProfChart(); };
  renderProfChart();
}

const PROF_COMPONENTS = [
  ["comp_share", "pct_minutes_share"],
  ["comp_onoff", "pct_onoff"],
  ["comp_ppg", "pct_ppg"],
  ["comp_ga90", "pct_ga90"],
  ["comp_rating", "pct_rating"],
];

function renderProfChart() {
  const imp = DATA.pool.importance.filter(r => r.window_matches >= 8);
  const sel = imp.find(r => r.player_id === impSelected);
  if (!sel) { return; }
  const peers = [], mine = [];
  PROF_COMPONENTS.forEach(([_, key], i) => {
    imp.forEach(r => {
      if (r[key] !== "" && r.player_id !== sel.player_id) {
        peers.push([num(r[key]), i, r.name]);
      }
    });
    if (sel[key] !== "") { mine.push([num(sel[key]), i]); }
  });
  mkChart("c_prof", {
    grid: { left: 8, right: 24, top: 10, bottom: 6, containLabel: true },
    tooltip: tooltip({
      trigger: "item",
      formatter: p => p.seriesIndex === 0
        ? `${peers[p.dataIndex][2]} — ${peers[p.dataIndex][0]}e pct`
        : `<b>${sel.name}</b> — ${mine.find(m => m[1] === p.value[1])[0]}e pct`,
    }),
    xAxis: axisX({ type: "value", min: 0, max: 100,
      axisLabel: { color: MUTED, fontSize: 11 },
      splitLine: { show: true, lineStyle: { color: GRID, width: 1 } } }),
    yAxis: axisY({ type: "value", min: -1, max: PROF_COMPONENTS.length,
      interval: 1, splitLine: { show: false },
      axisLabel: { color: INK2, fontSize: 11.5,
        formatter: v => (Number.isInteger(v) && PROF_COMPONENTS[v])
          ? t(PROF_COMPONENTS[v][0]) : "" } }),
    series: [
      { type: "scatter", symbolSize: 7, data: peers,
        itemStyle: { color: BASELINE, opacity: 0.7 } },
      { type: "scatter", symbolSize: 13, data: mine,
        itemStyle: { color: S1, borderColor: SURFACE, borderWidth: 2 } },
    ],
  });
}

function renderBench() {
  const rows = DATA.pool.bench.filter(r => num(r.sub_apps) >= 3).slice(0, 8);
  mkChart("c_bench", {
    grid: { left: 8, right: 110, top: 8, bottom: 8, containLabel: true },
    tooltip: tooltip({
      trigger: "item",
      formatter: p => {
        const r = rows[p.dataIndex];
        const per90 = r.sub_ga90 === "" ? "–" : fmt(r.sub_ga90, 2) + " /90";
        return `<b>${r.name}</b><br/>${r.sub_apps} ${t("h_subs").toLowerCase()} · ${fmt(r.sub_min)} min<br/>` +
          `${r.sub_goals} ${t("goals_g").toLowerCase()} + ${r.sub_assists} ${t("goals_a").toLowerCase()} (${per90})<br/>` +
          `${t("h_entry")}: ${fmt(r.entry_avg)}' · L/N/T ${r.entries_leading}/${r.entries_level}/${r.entries_trailing}`;
      },
    }),
    xAxis: axisX({ type: "value", show: false, max: v => v.max + 1 }),
    yAxis: axisY({ type: "category", inverse: true, splitLine: { show: false },
      data: rows.map(r => r.name), axisLabel: { color: INK2, fontSize: 11.5 } }),
    series: [{
      type: "bar", data: rows.map(r => num(r.sub_ga)), barMaxWidth: 14,
      itemStyle: { color: S1, borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: "right", color: MUTED, fontSize: 10.5,
        formatter: p => t("bench_bar_label",
          { ga: rows[p.dataIndex].sub_ga, min: fmt(rows[p.dataIndex].sub_min) }) },
    }],
  });
  const b = DATA.team.timeline.summary.post60;
  $("bench_note").textContent = t("bench_baseline",
    { gd90: signed(b.gd90), gf: b.gf, ga: b.ga, min: fmt(b.minutes) });
}

// ---------- status strip ----------

const STRIP_STATUSES = [
  ["active", "#0ca30c"], ["fringe", "#fab219"], ["out", "#898781"],
  ["retired_career", "#52514e"], ["retired_int", "#52514e"],
];

function renderStatusStrip() {
  const profs = DATA.pool.profiles.filter(p => p.last_seen);
  const series = STRIP_STATUSES
    .map(([status, color], si) => ({
      name: t("st_" + status), type: "scatter", symbolSize: 9,
      itemStyle: { color, borderColor: SURFACE, borderWidth: 1.5 },
      data: profs.filter(p => p.status === status)
        .map((p, i) => ({ value: [p.last_seen, ((i * 37) % 100) / 12.5 - 4 + si * 0.13],
                          name: p.name, club: p.club_v || p.club })),
    }))
    .filter(s => s.data.length);
  mkChart("c_strip", {
    grid: { left: 8, right: 16, top: 10, bottom: 30, containLabel: true },
    tooltip: tooltip({
      trigger: "item",
      formatter: p => `<b>${p.data.name}</b><br/>${p.value[0]}` +
        (p.data.club ? ` · ${p.data.club}` : ""),
    }),
    legend: legend(),
    xAxis: axisX({ type: "time" }),
    yAxis: axisY({ type: "value", min: -5, max: 5, show: false }),
    series,
  });
}

// ---------- history ----------

function renderDecadeChart() {
  const rows = DATA.history.by_decade;
  mkChart("c_decades", {
    grid: { left: 8, right: 8, top: 20, bottom: 4, containLabel: true },
    tooltip: tooltip({
      trigger: "item",
      formatter: p => {
        const r = rows[p.dataIndex];
        return `<b>${r.decade}s</b><br/>${r.pld} m · ${r.w}V ${r.d}N ${r.l}D · ${fmt(r.win_pct, 1)} %`;
      },
    }),
    xAxis: axisX({ type: "category", data: rows.map(r => r.decade + "s") }),
    yAxis: axisY({ type: "value", axisLabel: { formatter: "{value} %", color: MUTED, fontSize: 11 } }),
    series: [{
      type: "bar", data: rows.map(r => r.win_pct), barMaxWidth: 22,
      itemStyle: { color: S1, borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: "top", color: INK2, fontSize: 11,
        formatter: p => fmt(p.value, 0) },
    }],
  });
  tableView("card_decades", ["", "Pld", "V/W", "N/D", "D/L", "%"],
    rows.map(r => [r.decade + "s", r.pld, r.w, r.d, r.l, fmt(r.win_pct, 1)]));
}

function renderFormChart() {
  const byYear = DATA.history.by_year;
  const years = byYear.map(r => r.year);
  const data = [];
  for (let i = 0; i < byYear.length; i++) {
    const win = byYear.filter(r => r.year >= years[i] - 4 && r.year <= years[i]);
    const pld = win.reduce((s, r) => s + r.pld, 0);
    const w = win.reduce((s, r) => s + r.w, 0);
    if (pld >= 10) { data.push([years[i], Math.round(1000 * w / pld) / 10]); }
  }
  mkChart("c_form", {
    grid: { left: 8, right: 16, top: 12, bottom: 4, containLabel: true },
    tooltip: tooltip({ trigger: "axis", valueFormatter: v => fmt(v, 1) + " %" }),
    xAxis: axisX({ type: "value", min: "dataMin", max: "dataMax",
      axisLabel: { color: MUTED, fontSize: 11, formatter: v => v } }),
    yAxis: axisY({ type: "value", axisLabel: { formatter: "{value} %", color: MUTED, fontSize: 11 } }),
    series: [{
      type: "line", data, showSymbol: false, symbolSize: 8,
      lineStyle: { color: S1, width: 2, cap: "round", join: "round" },
      itemStyle: { color: S1, borderColor: SURFACE, borderWidth: 2 },
      areaStyle: { color: S1, opacity: 0.1 },
      name: LANG === "fr" ? "% victoires (5 ans)" : "Win % (5 yrs)",
    }],
  });
}

const ROUND_PATTERNS = [
  [/champion/i, 7], [/runner/i, 6], [/third/i, 5],
  [/fourth|semi/i, 4], [/quarter/i, 3], [/round of 16/i, 2], [/group/i, 1],
];

function roundLevel(round) {
  for (const [re, lvl] of ROUND_PATTERNS) {
    if (re.test(round)) { return lvl; }
  }
  return null;
}

function renderAfconChart() {
  const recs = {};
  DATA.history.afcon_editions.forEach(e => { recs[e.year] = e; });
  const pts = DATA.history.afcon_record
    .map(r => ({ year: r.year, level: roundLevel(r.round), round: r.round }))
    .filter(p => p.level);
  mkChart("c_afcon", {
    grid: { left: 8, right: 20, top: 12, bottom: 4, containLabel: true },
    tooltip: tooltip({
      trigger: "item",
      formatter: p => {
        const d = pts[p.dataIndex];
        const rec = recs[d.year];
        const wdl = rec ? `<br/>${rec.pld} m · ${rec.w}V ${rec.d}N ${rec.l}D · ${rec.gf}-${rec.ga}` : "";
        return `<b>CAN ${d.year}</b> — ${t("round_" + d.level)}${wdl}`;
      },
    }),
    xAxis: axisX({ type: "value", min: 1975, max: 2028,
      axisLabel: { color: MUTED, fontSize: 11, formatter: v => v } }),
    yAxis: axisY({ type: "value", min: 0, max: 8, interval: 1,
      axisLabel: { color: INK2, fontSize: 11,
        formatter: v => Number.isInteger(v) && v >= 1 && v <= 7 ? t("round_" + v) : "" } }),
    series: [{
      type: "scatter", symbolSize: 12,
      data: pts.map(p => [p.year, p.level]),
      itemStyle: { color: S1, borderColor: SURFACE, borderWidth: 2 },
      label: { show: true, position: "top", color: INK2, fontSize: 10.5,
        formatter: p => (pts[p.dataIndex].level >= 5 ? pts[p.dataIndex].year : "") },
    }],
  });
  tableView("card_afcon", ["CAN", LANG === "fr" ? "Stade" : "Stage", "Pld", "V/W", "N/D", "D/L"],
    pts.map(p => {
      const rec = recs[p.year] || {};
      return [p.year, t("round_" + p.level), rec.pld ?? "–", rec.w ?? "–", rec.d ?? "–", rec.l ?? "–"];
    }));
}

function renderLegendsTables() {
  $("capped_table").innerHTML = `<tr><th>${t("h_rank")}</th><th>${t("h_player")}</th>
    <th class="num">${t("h_caps")}</th><th class="num">${t("h_goals")}</th><th>${t("h_career")}</th></tr>` +
    DATA.history.most_capped.slice(0, 10).map(r =>
      `<tr><td>${r.rank}</td><td>${r.name}</td><td class="num">${r.caps ?? "–"}</td>
       <td class="num">${r.goals ?? "–"}</td><td>${r.career}</td></tr>`).join("");
  $("scorers_table").innerHTML = `<tr><th>${t("h_rank")}</th><th>${t("h_player")}</th>
    <th class="num">${t("h_goals")}</th><th class="num">${t("h_caps")}</th><th>${t("h_career")}</th></tr>` +
    DATA.history.top_scorers.slice(0, 10).map(r =>
      `<tr><td>${r.rank}</td><td>${r.name}</td><td class="num">${r.goals ?? "–"}</td>
       <td class="num">${r.caps ?? "–"}</td><td>${r.career}</td></tr>`).join("");
  const res = { W: t("win_result"), D: t("draw_result"), L: t("loss_result") };
  $("last10_table").innerHTML = `<tr><th>${t("h_date")}</th><th></th><th>${t("h_opp")}</th>
    <th class="num">${t("h_score")}</th><th>${t("h_comp")}</th></tr>` +
    DATA.history.last10.map(m =>
      `<tr><td>${m.date}</td><td><span class="chip ${m.result}">${res[m.result]}</span></td>
       <td>${m.opponent}</td><td class="num">${m.score}</td><td>${m.tournament}</td></tr>`).join("");
}

// ---------- elo ----------

function renderEloChart() {
  const tl = DATA.elo.timeline;
  const hist = tl.map(p => [p.date, p.elo]);
  const peak = DATA.elo.peak;
  const fc = DATA.elo.forecast;
  const last = tl[tl.length - 1];
  const series = [{
    name: t("elo_hist"), type: "line", data: hist, showSymbol: false,
    lineStyle: { color: S1, width: 2 }, itemStyle: { color: S1 },
    markPoint: {
      symbol: "circle", symbolSize: 9,
      itemStyle: { color: S1, borderColor: SURFACE, borderWidth: 2 },
      label: { color: INK2, fontSize: 11, position: "top",
        formatter: () => `${t("elo_peak")} ${Math.round(peak.elo)} · ${peak.date.slice(0, 4)}` },
      data: [{ coord: [peak.date, peak.elo] }],
    },
  }];
  if (fc) {
    const t1 = "2027-07-01", t2 = "2030-06-15";
    const [f27, f30] = fc.targets;
    series.push({
      name: t("elo_proj"), type: "line",
      data: [[last.date, last.elo], [t1, f27.mid], [t2, f30.mid]],
      showSymbol: false, lineStyle: { color: S1, width: 2, type: "dashed" },
      itemStyle: { color: S1 },
    });
    series.push({
      name: "lo", type: "line", stack: "band", silent: true,
      data: [[last.date, last.elo], [t1, f27.lo], [t2, f30.lo]],
      showSymbol: false, lineStyle: { opacity: 0 }, tooltip: { show: false },
    });
    series.push({
      name: "band", type: "line", stack: "band", silent: true,
      data: [[last.date, 0], [t1, f27.hi - f27.lo], [t2, f30.hi - f30.lo]],
      showSymbol: false, lineStyle: { opacity: 0 },
      areaStyle: { color: S1, opacity: 0.1 }, tooltip: { show: false },
    });
  }
  mkChart("c_elo_tl", {
    grid: { left: 8, right: 24, top: 26, bottom: 30, containLabel: true },
    tooltip: tooltip({
      trigger: "axis",
      formatter: params => {
        const px = params.filter(p => p.seriesName === t("elo_hist") || p.seriesName === t("elo_proj"));
        if (!px.length) { return ""; }
        const d = new Date(px[0].value[0]);
        return `<b>${d.getFullYear()}</b><br/>` +
          px.map(p => `${p.seriesName}: ${fmt(Math.round(p.value[1]))}`).join("<br/>");
      },
    }),
    legend: legend({ data: [t("elo_hist"), t("elo_proj")] }),
    xAxis: axisX({ type: "time" }),
    yAxis: axisY({ type: "value", min: 1150, scale: true }),
    series,
  });
  const c10 = DATA.elo.caf_top10;
  tableView("card_elo", ["#", LANG === "fr" ? "Équipe (CAF)" : "Team (CAF)", "Elo"],
    c10.map((r, i) => [i + 1, r.team, fmt(Math.round(r.elo))]));
}

function renderWinexpChart() {
  const rows = [...DATA.elo.win_expectancy].sort((a, b) => b.expected - a.expected);
  mkChart("c_winexp", {
    grid: { left: 8, right: 40, top: 8, bottom: 22, containLabel: true },
    tooltip: tooltip({
      trigger: "item",
      formatter: p => {
        const r = rows[p.dataIndex];
        return `<b>${r.opponent}</b> (Elo ${fmt(Math.round(r.opp_elo))})<br/>${t("c_winexp_sub")}: ${fmt(r.expected, 2)}`;
      },
    }),
    xAxis: axisX({ type: "value", min: 0, max: 1,
      axisLabel: { color: MUTED, fontSize: 11 } }),
    yAxis: axisY({ type: "category", inverse: true, splitLine: { show: false },
      data: rows.map(r => r.opponent), axisLabel: { color: INK2, fontSize: 11.5 } }),
    series: [{
      type: "bar", data: rows.map(r => r.expected), barMaxWidth: 14,
      itemStyle: { color: S1, borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: "right", color: INK2, fontSize: 11,
        formatter: p => fmt(p.value, 2) },
      markLine: {
        silent: true, symbol: "none",
        lineStyle: { color: BASELINE, width: 1, type: "solid" },
        label: { color: MUTED, fontSize: 10.5, formatter: "50/50" },
        data: [{ xAxis: 0.5 }],
      },
    }],
  });
  $("winexp_note").textContent = t("winexp_note");
}

// ---------- projections ----------

function renderProjChart() {
  const players = DATA.squad.players.filter(p => p.age_afcon27);
  const rows = ["FW", "MF", "DF", "GK"];
  const pts = players.map((p, i) => ({
    value: [p.age_afcon27, rows.indexOf(p.pos) + ((i % 5) - 2) * 0.09],
    p,
  }));
  const bands = rows.map((pos, i) => [
    { xAxis: PEAK[pos][0], yAxis: i - 0.34, itemStyle: { color: NEUTRAL, opacity: 0.7 } },
    { xAxis: PEAK[pos][1] + 1, yAxis: i + 0.34 },
  ]);
  mkChart("c_proj_age", {
    grid: { left: 8, right: 20, top: 12, bottom: 24, containLabel: true },
    tooltip: tooltip({
      trigger: "item",
      formatter: q => {
        const p = pts[q.dataIndex].p;
        return `<b>${p.name}</b> · ${p.pos} · ${p.club || ""}<br/>` +
          `${fmt(p.age_afcon27, 1)} ${LANG === "fr" ? "ans à la CAN 2027" : "yrs at AFCON 2027"} — ${t("phase_" + p.phase_afcon27)}`;
      },
    }),
    xAxis: axisX({ type: "value", min: 17, max: 38,
      axisLabel: { color: MUTED, fontSize: 11 },
      splitLine: { show: true, lineStyle: { color: GRID, width: 1 } } }),
    yAxis: axisY({ type: "value", min: -1, max: 4, interval: 1,
      splitLine: { show: false },
      axisLabel: { color: INK2, fontSize: 12,
        formatter: v => Number.isInteger(v) && rows[v] ? posLabel(rows[v]) : "" } }),
    series: [{
      type: "scatter", symbolSize: 11,
      data: pts.map(x => x.value),
      itemStyle: { color: S1, borderColor: SURFACE, borderWidth: 2 },
      markArea: { silent: true, data: bands,
        label: { show: false } },
    }],
  });
  const core = DATA.squad.core_generation;
  if (core) {
    $("core_box").innerHTML = `<b>${t("core_title")}</b> — ` + t("core_text", {
      n: core.n, age_now: fmt(core.avg_age_now, 1),
      age_27: fmt(core.avg_age_afcon27, 1), in_peak: core.in_peak_afcon27,
    }) + `<br/><span class="sub">${core.names.slice(0, 9).join(" · ")}</span>`;
  }
  tableView("card_proj", [t("h_player"), t("h_pos"), t("h_age27"), ""],
    [...players].sort((a, b) => a.age_afcon27 - b.age_afcon27)
      .map(p => [p.name, p.pos, fmt(p.age_afcon27, 1), t("phase_" + p.phase_afcon27)]));
}

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
  renderTempo();
  renderImportance();
  renderBench();
  renderStatusStrip();
  renderDecadeChart();
  renderFormChart();
  renderAfconChart();
  renderLegendsTables();
  renderEloChart();
  renderWinexpChart();
  renderProjChart();
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
