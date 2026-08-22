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

