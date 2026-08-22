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

// ---------- captains & goalkeepers ----------

function renderCaptains() {
  const rows = DATA.team.captains.filter(r => num(r.matches) >= 2);
  $("captains_table").innerHTML = `<tr><th>${t("h_player")}</th>
    <th class="num">${t("h_matches_c")}</th><th class="num">V-N-D</th>
    <th class="num">Pts/m</th><th>${t("h_period")}</th></tr>` +
    rows.map(r => `<tr><td>${r.name}</td><td class="num">${r.matches}</td>
      <td class="num">${r.w}-${r.d}-${r.l}</td><td class="num">${fmt(r.ppg, 2)}</td>
      <td>${r.first_date.slice(0, 4)}–${r.last_date.slice(0, 4)}</td></tr>`).join("");
}

function renderGoalkeepers() {
  const rows = DATA.team.goalkeepers;
  $("gk_table").innerHTML = `<tr><th>${t("h_player")}</th>
    <th class="num">${t("h_apps")}</th><th class="num">${t("h_min")}</th>
    <th class="num">${t("h_gk_ga")}</th><th class="num">${t("h_gk_ga90")}</th>
    <th class="num">${t("h_saves")}</th><th class="num">${t("h_savepct")}</th>
    <th class="num">${t("h_cs")}</th><th class="num">${t("h_claims")}</th>
    <th class="num">${t("h_rating")}</th></tr>` +
    rows.map(r => `<tr${r.gated === 1 ? "" : ' style="color:var(--muted)"'}>
      <td>${r.name}</td><td class="num">${r.apps}</td>
      <td class="num">${fmt(r.minutes)}</td><td class="num">${r.ga_on}</td>
      <td class="num">${r.ga90 === "" ? "–" : fmt(r.ga90, 2)}</td>
      <td class="num">${r.saves}</td>
      <td class="num">${r.save_pct === "" ? "–" : fmt(r.save_pct, 1) + " %"}</td>
      <td class="num">${r.clean_sheets}</td>
      <td class="num">${num(r.high_claims) + num(r.punches)}</td>
      <td class="num">${r.rating_avg === "" ? "–" : fmt(r.rating_avg, 2)}</td></tr>`).join("");
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

