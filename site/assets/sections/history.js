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

// ---------- coaches ----------

function renderCoaches() {
  const rows = DATA.history.coaches;
  $("coaches_table").innerHTML = `<tr><th>${t("h_coach")}</th><th>${t("h_period")}</th>
    <th class="num">Pld</th><th class="num">V-N-D</th><th class="num">Pts/m</th>
    <th class="num">BM/m</th><th class="num">BE/m</th><th class="num">${t("h_elo_delta")}</th></tr>` +
    rows.map(r => {
      const small = !r.pooled && r.matches < 10;
      const name = r.pooled ? t("coaches_pooled")
        : r.coach + (r.current ? ` <span class="pill st active">${t("coach_current")}</span>` : "");
      const style = r.pooled ? ' style="color:var(--muted)"' : "";
      const delta = r.elo_delta === "" || r.pooled ? "–" : signed(r.elo_delta, 0);
      const span = r.first_match.slice(0, 4) === r.last_match.slice(0, 4)
        ? r.first_match.slice(0, 4)
        : `${r.first_match.slice(0, 4)}–${r.last_match.slice(0, 4)}`;
      const note = small ? ` <span class="pill">${t("small_sample")}</span>` : "";
      return `<tr${style}><td>${name}</td>
        <td>${span}${r.current ? "–" : ""}</td>
        <td class="num">${r.matches}${note}</td><td class="num">${r.w}-${r.d}-${r.l}</td>
        <td class="num">${fmt(r.ppg, 2)}</td><td class="num">${fmt(r.gf_pm, 2)}</td>
        <td class="num">${fmt(r.ga_pm, 2)}</td><td class="num">${delta}</td></tr>`;
    }).join("");
}

// ---------- venues ----------

function renderVenues() {
  const v = DATA.history.venues;
  const classes = ["home_bf", "home_delocalized", "neutral", "away"];
  const byClass = period => classes.map(c =>
    (v[period].find(r => r.venue_class === c) || {}));
  const all = byClass("all_time"), recent = byClass("since_2015");
  const mk = (name, rows, color) => ({
    name, type: "bar", data: rows.map(r => r.ppg ?? 0), barMaxWidth: 20,
    itemStyle: { color, borderRadius: [4, 4, 0, 0] },
    label: { show: true, position: "top", color: INK2, fontSize: 11,
      formatter: p => fmt(p.value, 2) },
  });
  mkChart("c_venues", {
    grid: { left: 8, right: 8, top: 24, bottom: 30, containLabel: true },
    tooltip: tooltip({
      trigger: "axis", axisPointer: { type: "shadow" },
      formatter: params => {
        const i = params[0].dataIndex;
        const line = (label, r) => `${label}: ${fmt(r.ppg, 2)} pts/m — ${r.w}V-${r.d}N-${r.l}D (${r.pld} m)`;
        return `<b>${t("vc_" + classes[i])}</b><br/>${line(t("venues_alltime"), all[i])}<br/>${line(t("venues_2015"), recent[i])}`;
      },
    }),
    legend: legend(),
    xAxis: axisX({ type: "category", data: classes.map(c => t("vc_" + c)) }),
    yAxis: axisY({ type: "value" }),
    series: [mk(t("venues_alltime"), all, S1), mk(t("venues_2015"), recent, S2)],
  });
  $("venues_note").textContent = t("venues_note", {
    hosts: v.delocalized_hosts.map(h => `${h.city} (${h.n})`).join(", "),
  });
  tableView("card_venues", ["", "Pld", "V/W", "N/D", "D/L", "Pts/m", "BM/GF", "BE/GA"],
    v.all_time.map(r => [t("vc_" + r.venue_class), r.pld, r.w, r.d, r.l,
                         fmt(r.ppg, 2), r.gf, r.ga]));
}

// ---------- penalties & shootouts ----------

function renderShootouts() {
  const so = DATA.history.shootouts;
  if (!so || !so.matches.length) { return; }
  const res = { "1": t("win_result"), "0": t("loss_result") };
  $("shootout_rec").textContent = t("shootout_rec",
    { w: so.w, l: so.l, y: so.matches[0].date.slice(0, 4) });
  $("shootout_table").innerHTML = `<tr><th>${t("h_date")}</th><th></th>
    <th>${t("h_opp")}</th></tr>` +
    [...so.matches].reverse().map(m =>
      `<tr><td>${m.date}</td>
       <td><span class="chip ${m.winner_is_bf === "1" ? "W" : "L"}">${res[m.winner_is_bf] || res["0"]}</span></td>
       <td>${m.opponent}</td></tr>`).join("");
}

function renderPenalties() {
  const p = DATA.team.penalties;
  const mt = (label, s, m) => {
    const n = s + m;
    return `<div class="mt"><div class="label">${label}</div>
      <div class="value">${t("pens_conv", { s, n })}</div>
      <div class="sub">${t("pens_scored_sub", { s, m })}</div></div>`;
  };
  $("pens_tiles").innerHTML =
    mt(t("pens_for"), p.ingame_for.scored, p.ingame_for.missed) +
    mt(t("pens_against"), p.ingame_against.scored, p.ingame_against.missed) +
    mt(t("pens_so_for"), p.shootout_for.scored, p.shootout_for.missed) +
    mt(t("pens_so_against"), p.shootout_against.scored, p.shootout_against.missed);
  $("takers_table").innerHTML = `<tr><th>${t("h_taker")}</th>
    <th class="num">${t("h_scored")}</th><th class="num">${t("h_missed")}</th></tr>` +
    p.takers.map(x => `<tr><td>${x.name}</td><td class="num">${x.scored}</td>
      <td class="num">${x.missed || "–"}</td></tr>`).join("");
  $("pens_gk_note").textContent = t("pens_gk_note", { n: p.gk_shootout_saves });
}

