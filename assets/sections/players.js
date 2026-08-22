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
  { key: "club_minutes_season", label: "h_club_min", numFmt: null },
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
    if (c.key === "club_minutes_season") {
      const v = p.club_minutes_season;
      const title = p.club_season ? ` title="${p.club_season} · ${p.club_form_as_of}"` : "";
      return `<td class="num"${title}>${v === "" || v === undefined ? "–" : fmt(v)}</td>`;
    }
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

