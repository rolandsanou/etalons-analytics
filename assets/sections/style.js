// ---------- style of play ----------

const PCT_AXES = ["possession", "pass_accuracy", "long_ball_share", "long_ball_accuracy",
                  "shots_on_target_share", "shots_inside_box_share", "dribble_success",
                  "aerial_win", "ground_duel_win"];
const VOL_AXES = ["shots_per_match", "big_chances_per_match", "dribbles_per_match",
                  "crosses_per_match", "corners_per_match", "passes_per_match",
                  "tackles_per_match", "interceptions_per_match",
                  "clearances_per_match", "fouls_per_match"];

function styleLookup(scope, scopeValue) {
  const out = {};
  DATA.team.style.axes
    .filter(r => r.scope === scope && r.scope_value === scopeValue)
    .forEach(r => { (out[r.side] = out[r.side] || {})[r.axis] = r; });
  return out;
}

function renderStylePct() {
  const o = styleLookup("overall", "all");
  if (!o.bf) { return; }
  const axes = PCT_AXES.filter(a => o.bf[a]);
  const cats = axes.map(a => t("ax_" + a));
  const bar = (name, side, color, radius) => ({
    name, type: "bar", data: axes.map(a => (o[side] && o[side][a]) ? o[side][a].value : null),
    barMaxWidth: 11, itemStyle: { color, borderRadius: radius },
    label: { show: true, position: "right", color: MUTED, fontSize: 10,
      formatter: p => fmt(p.value, 1) },
  });
  mkChart("c_style_pct", {
    grid: { left: 8, right: 44, top: 10, bottom: 28, containLabel: true },
    tooltip: tooltip({
      trigger: "axis", axisPointer: { type: "shadow" },
      formatter: params => {
        const a = axes[params[0].dataIndex];
        const n = o.bf[a] ? o.bf[a].n : "?";
        return `<b>${t("ax_" + a)}</b><br/>` +
          params.map(p => `${p.seriesName}: ${fmt(p.value, 1)} %`).join("<br/>") +
          `<br/><span style="color:${MUTED}">n = ${n} ${LANG === "fr" ? "matchs" : "matches"}</span>`;
      },
    }),
    legend: legend(),
    xAxis: axisX({ type: "value", max: 100, axisLabel: { formatter: "{value} %",
      color: MUTED, fontSize: 11 },
      splitLine: { show: true, lineStyle: { color: GRID, width: 1 } } }),
    yAxis: axisY({ type: "category", data: cats, inverse: true,
      splitLine: { show: false }, axisLabel: { color: INK2, fontSize: 11.5 } }),
    series: [bar(t("legend_bf"), "bf", S1, [0, 4, 4, 0]),
             bar(t("legend_opp"), "opp", BASELINE, [0, 4, 4, 0])],
  });
  tableView("card_style_pct", ["", t("legend_bf"), t("legend_opp"), "n"],
    axes.map(a => [t("ax_" + a), fmt(o.bf[a].value, 1),
                   o.opp[a] ? fmt(o.opp[a].value, 1) : "–", o.bf[a].n]));
}

function renderStyleVol() {
  const o = styleLookup("overall", "all");
  if (!o.bf) { return; }
  const axes = VOL_AXES.filter(a => o.bf[a] && o.opp[a] && o.opp[a].value);
  const idx = axes.map(a => Math.round(1000 * o.bf[a].value / o.opp[a].value) / 10);
  const order = axes.map((a, i) => [a, idx[i]]).sort((x, y) => y[1] - x[1]);
  mkChart("c_style_vol", {
    grid: { left: 8, right: 46, top: 10, bottom: 8, containLabel: true },
    tooltip: tooltip({
      trigger: "item",
      formatter: p => {
        const a = order[p.dataIndex][0];
        return `<b>${t("ax_" + a)}</b><br/>${t("legend_bf")}: ${fmt(o.bf[a].value, 1)}` +
          `<br/>${t("legend_opp")}: ${fmt(o.opp[a].value, 1)}` +
          `<br/><span style="color:${MUTED}">n = ${o.bf[a].n}</span>`;
      },
    }),
    xAxis: axisX({ type: "value", axisLabel: { color: MUTED, fontSize: 11 },
      splitLine: { show: true, lineStyle: { color: GRID, width: 1 } } }),
    yAxis: axisY({ type: "category", inverse: true, splitLine: { show: false },
      data: order.map(([a]) => t("ax_" + a)),
      axisLabel: { color: INK2, fontSize: 11.5 } }),
    series: [{
      type: "bar", data: order.map(([, v]) => v), barMaxWidth: 13,
      itemStyle: { color: p => (p.value >= 100 ? S1 : S2), borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: "right", color: MUTED, fontSize: 10.5,
        formatter: p => fmt(p.value, 0) },
      markLine: { silent: true, symbol: "none",
        lineStyle: { color: BASELINE, width: 1 },
        label: { color: MUTED, fontSize: 10.5, formatter: "100" },
        data: [{ xAxis: 100 }] },
    }],
  });
  tableView("card_style_vol", ["", t("legend_bf"), t("legend_opp"), "index", "n"],
    order.map(([a, v]) => [t("ax_" + a), fmt(o.bf[a].value, 1),
                           fmt(o.opp[a].value, 1), fmt(v, 0), o.bf[a].n]));
}

function renderStyleTerciles() {
  const tercs = ["weak", "mid", "strong"];
  const groups = tercs.map(x => styleLookup("opp_elo", x));
  if (!groups.some(g => g.bf)) { return; }
  const axes = ["possession", "long_ball_share", "pass_accuracy"];
  const series = axes.map((a, i) => ({
    name: t("ax_" + a), type: "bar", barMaxWidth: 18,
    data: groups.map(g => (g.bf && g.bf[a]) ? g.bf[a].value : null),
    itemStyle: { color: [S1, S2, S3][i], borderRadius: [4, 4, 0, 0] },
    label: { show: true, position: "top", color: INK2, fontSize: 10.5,
      formatter: p => fmt(p.value, 0) },
  }));
  const labels = tercs.map((x, i) => {
    const g = groups[i];
    const n = g.bf ? Object.values(g.bf)[0].matches : 0;
    return `${t("terc_" + x)} (${n})`;
  });
  mkChart("c_style_terc", {
    grid: { left: 8, right: 8, top: 20, bottom: 28, containLabel: true },
    tooltip: tooltip({ trigger: "axis", axisPointer: { type: "shadow" },
      valueFormatter: v => fmt(v, 1) + " %" }),
    legend: legend(),
    xAxis: axisX({ type: "category", data: labels,
      axisLabel: { color: MUTED, fontSize: 11, interval: 0 } }),
    yAxis: axisY({ type: "value", max: 100,
      axisLabel: { formatter: "{value} %", color: MUTED, fontSize: 11 } }),
    series,
  });
  tableView("card_style_terc", [""].concat(axes.map(a => t("ax_" + a))).concat(["n"]),
    tercs.map((x, i) => {
      const g = groups[i].bf || {};
      return [t("terc_" + x)].concat(axes.map(a => g[a] ? fmt(g[a].value, 1) : "–"))
        .concat([g[axes[0]] ? g[axes[0]].matches : 0]);
    }));
}

function renderStyleHalves() {
  const halves = DATA.team.style.halves;
  if (!halves.length) { return; }
  const keys = ["possession", "passes_per_match", "shots_per_match",
                "big_chances_per_match", "dribbles_per_match"];
  $("half_table").innerHTML = `<tr><th></th>${halves.map(h =>
    `<th class="num">${t("half_" + h.half)}</th>`).join("")}</tr>` +
    keys.filter(k => halves.some(h => h[k] !== undefined)).map(k =>
      `<tr><td>${t("ax_" + k)}</td>${halves.map(h =>
        `<td class="num">${h[k] === undefined ? "–" : fmt(h[k], 1)}</td>`).join("")}</tr>`).join("");
}

function renderStyle() {
  const cov = DATA.team.coverage;
  $("lead_style").textContent = t("s_style_lead",
    { n: cov.with_full_stats || 0, tot: cov.events });
  renderStylePct();
  renderStyleVol();
  renderStyleTerciles();
  renderStyleHalves();
}

// ---------- resilience ----------

function resMetric(metric, scope) {
  return DATA.team.resilience.metrics.find(m => m.metric === metric && m.scope === scope);
}

function renderResilience() {
  const R = DATA.team.resilience;
  $("lead_res").textContent = t("s_res_lead", { n: DATA.team.timeline.summary.matches });
  const mt = (label, m, cls) => {
    if (!m) { return ""; }
    return `<div class="mt"><div class="label">${label}</div>
      <div class="value">${m.value === "" ? "–" : fmt(m.value, 2)}</div>
      <div class="sub">${m.detail} · ${m.n} m</div></div>`;
  };
  $("deficit_tiles").innerHTML =
    mt(t("def_never"), resMetric("deficit", "never_trailed")) +
    mt(t("def_1"), resMetric("deficit", "trailed_1")) +
    mt(t("def_2"), resMetric("deficit", "trailed_2plus"));
  const g = resMetric("late_swing", "points_gained"), l = resMetric("late_swing", "points_lost");
  $("late_swing_note").textContent = t("late_swing_note",
    { gained: g ? g.n : 0, lost: l ? l.n : 0 });

  // reply buckets
  const buckets = ["within_10", "11_20", "21_plus", "never"];
  const rows = buckets.map(b => resMetric("reply", b)).filter(Boolean);
  const total = rows.reduce((s, r) => s + r.n, 0);
  $("reply_sub").textContent = t("c_reply_sub", { n: total });
  mkChart("c_reply", {
    grid: { left: 8, right: 44, top: 8, bottom: 8, containLabel: true },
    tooltip: tooltip({ trigger: "item",
      formatter: p => `<b>${t("rep_" + buckets[p.dataIndex])}</b><br/>${rows[p.dataIndex].detail}` }),
    xAxis: axisX({ type: "value", show: false }),
    yAxis: axisY({ type: "category", inverse: true, splitLine: { show: false },
      data: buckets.map(b => t("rep_" + b)),
      axisLabel: { color: INK2, fontSize: 11.5 } }),
    series: [{
      type: "bar", data: rows.map(r => r.n), barMaxWidth: 14,
      itemStyle: { color: p => (buckets[p.dataIndex] === "never" ? BASELINE : S1),
        borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: "right", color: MUTED, fontSize: 10.5,
        formatter: p => `${p.value} (${fmt(rows[p.dataIndex].value, 0)} %)` },
    }],
  });
  const med = resMetric("reply", "median_minutes");
  $("reply_median").textContent = med && med.value !== ""
    ? t("reply_median", { v: fmt(med.value, 0), n: med.n }) : "";

  // output by game state
  const states = ["leading", "level", "trailing"];
  const scored = states.map(s => resMetric("scored_per90", s));
  const conceded = states.map(s => resMetric("conceded_per90", s));
  mkChart("c_state_out", {
    grid: { left: 8, right: 8, top: 20, bottom: 28, containLabel: true },
    tooltip: tooltip({ trigger: "axis", axisPointer: { type: "shadow" },
      formatter: params => {
        const i = params[0].dataIndex;
        return `<b>${t("st_" + states[i])}</b><br/>` +
          `${t("legend_gf")}: ${fmt(scored[i].value, 2)} /90 (${scored[i].detail})<br/>` +
          `${t("legend_ga")}: ${fmt(conceded[i].value, 2)} /90 (${conceded[i].detail})`;
      } }),
    legend: legend(),
    xAxis: axisX({ type: "category", data: states.map(s => t("st_" + s)) }),
    yAxis: axisY({ type: "value" }),
    series: [
      { name: t("legend_gf"), type: "bar", barMaxWidth: 16,
        data: scored.map(m => m ? m.value : null),
        itemStyle: { color: S1, borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: "top", color: INK2, fontSize: 10.5,
          formatter: p => fmt(p.value, 2) } },
      { name: t("legend_ga"), type: "bar", barMaxWidth: 16,
        data: conceded.map(m => m ? m.value : null),
        itemStyle: { color: S2, borderRadius: [4, 4, 0, 0] },
        label: { show: true, position: "top", color: INK2, fontSize: 10.5,
          formatter: p => fmt(p.value, 2) } },
    ],
  });

  const clutch = R.clutch.filter(c => c.goals >= 2).slice(0, 12);
  $("clutch_table").innerHTML = `<tr><th>${t("h_player")}</th>
    <th class="num">${t("h_goals")}</th><th class="num">${t("h_open")}</th>
    <th class="num">${t("h_eq")}</th><th class="num">${t("h_go")}</th>
    <th class="num">${t("h_late")}</th><th class="num">${t("h_trailing")}</th>
    <th class="num">${t("h_sub_goals")}</th></tr>` +
    clutch.map(c => `<tr><td>${c.name}</td><td class="num">${c.goals}</td>
      <td class="num">${c.openers || "–"}</td><td class="num">${c.equalizers || "–"}</td>
      <td class="num">${c.go_ahead || "–"}</td><td class="num">${c.late_goals || "–"}</td>
      <td class="num">${c.goals_when_trailing || "–"}</td>
      <td class="num">${c.as_sub_goals || "–"}</td></tr>`).join("");
}

