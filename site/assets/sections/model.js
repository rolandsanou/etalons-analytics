// ---------- model backtest & squad stability ----------

function renderBacktest() {
  const b = (DATA.elo || {}).backtest;
  const table = $("backtest_table");
  if (!b || !table) { return; }
  if (!b.available) {
    table.innerHTML = `<tr><td>${t("bt_unavailable")}</td></tr>`;
    return;
  }
  const rows = [
    [t("bt_brier_model"), fmt(b.brier.model, 3), t("bt_lower_better")],
    [t("bt_brier_base"), fmt(b.brier.base_rates, 3), t("bt_base_note")],
    [t("bt_brier_uniform"), fmt(b.brier.uniform, 3), t("bt_uniform_note")],
    [t("bt_skill"), fmt(b.brier.skill_vs_base, 1) + " %", t("bt_skill_note")],
    [t("bt_accuracy"), `${b.accuracy.hits}/${b.accuracy.n}`,
     fmt(b.accuracy.pct, 1) + " %"],
  ];
  table.innerHTML = rows.map(([a, v, note]) =>
    `<tr><td>${a}</td><td class="num">${v}</td>
     <td class="sub" style="white-space:normal">${note}</td></tr>`).join("");

  setText("bt_scope", t("bt_scope", {
    train: b.train.matches, until: b.train.until.slice(0, 4),
    test: b.test.matches, from: b.test.from.slice(0, 4),
  }));

  // calibration: predicted win probability vs what actually happened
  const cal = b.calibration;
  mkChart("c_calibration", {
    grid: { left: 8, right: 14, top: 14, bottom: 26, containLabel: true },
    tooltip: tooltip({
      trigger: "axis",
      formatter: params => {
        const c = cal[params[0].dataIndex];
        return `<b>${c.band}</b><br/>${t("bt_predicted")}: ${fmt(c.predicted, 1)} %<br/>` +
          `${t("bt_observed")}: ${fmt(c.observed, 1)} %<br/>` +
          `<span style="color:${MUTED}">n = ${c.n}</span>`;
      },
    }),
    legend: legend(),
    xAxis: axisX({ type: "category", data: cal.map(c => c.band) }),
    yAxis: axisY({ type: "value", max: 100,
      axisLabel: { formatter: "{value} %", color: MUTED, fontSize: 11 } }),
    series: [
      { name: t("bt_predicted"), type: "bar", barMaxWidth: 16,
        data: cal.map(c => c.predicted), itemStyle: { color: BASELINE } },
      { name: t("bt_observed"), type: "bar", barMaxWidth: 16,
        data: cal.map(c => c.observed), itemStyle: { color: S1 } },
    ],
  });
  tableView("card_calibration",
    [t("bt_band"), t("bt_predicted"), t("bt_observed"), "n"],
    cal.map(c => [c.band, fmt(c.predicted, 1) + " %", fmt(c.observed, 1) + " %", c.n]));

  const surprises = $("bt_surprises");
  if (surprises) {
    surprises.innerHTML = b.biggest_surprises.map(s =>
      `<tr><td>${s.date}</td><td>${s.opponent}</td>
       <td class="num">${fmt(100 * s.win, 0)} %</td>
       <td class="num"><span class="chip ${s.result}">${
         { W: t("win_result"), D: t("draw_result"), L: t("loss_result") }[s.result]
       }</span></td></tr>`).join("");
  }
}

function renderStability() {
  const rows = (DATA.team || {}).stability;
  const table = $("stability_table");
  if (!rows || !table) { return; }
  // a value is shown only when the era cleared the lineup-coverage gate
  const cell = (v, dec, unit) => (v === "" || v === null || v === undefined)
    ? "–" : fmt(v, dec) + (unit || "");
  table.innerHTML = `<tr><th>${t("h_coach")}</th><th>${t("h_period")}</th>
    <th class="num">${t("h_matches_c")}</th><th class="num">${t("st_with_xi")}</th>
    <th class="num">${t("st_used")}</th>
    <th class="num">${t("st_changes")}</th><th class="num">${t("st_churn")}</th>
    <th class="num">${t("st_top11")}</th><th class="num">${t("st_xis")}</th></tr>` +
    rows.map(r => {
      const thin = r.gated !== 1;
      return `<tr${thin ? ' style="color:var(--muted)"' : ""}>
      <td>${r.coach}</td>
      <td>${r.first_match.slice(0, 7)} → ${r.last_match.slice(0, 7)}</td>
      <td class="num">${r.matches}</td>
      <td class="num">${r.matches_with_xi}</td>
      <td class="num">${r.players_used}</td>
      <td class="num">${cell(r.avg_changes, 2)}</td>
      <td class="num">${cell(r.churn_pct, 1, " %")}</td>
      <td class="num">${cell(r.top11_share, 1, " %")}</td>
      <td class="num">${r.unique_xis}</td></tr>`;
    }).join("");
}
