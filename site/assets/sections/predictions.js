// ---------- Elo expectations vs CAF rivals ----------

function renderPredictions() {
  const p = (DATA.elo || {}).predictions;
  if (!p || !p.matchups || !p.matchups.length) { return; }
  const rows = p.matchups;
  const seg = (name, key, color, radius) => ({
    name, type: "bar", stack: "wdl",
    data: rows.map(r => Math.round(100 * r[key])),
    barMaxWidth: 15,
    itemStyle: { color, borderColor: SURFACE, borderWidth: 1, borderRadius: radius || 0 },
    label: { show: true, color: key === "draw" ? INK2 : ON_FILL, fontSize: 10.5,
      formatter: q => (q.value >= 8 ? q.value + " %" : "") },
  });
  mkChart("c_pred", {
    grid: { left: 8, right: 30, top: 8, bottom: 28, containLabel: true },
    tooltip: tooltip({
      trigger: "axis", axisPointer: { type: "shadow" },
      formatter: params => {
        const r = rows[params[0].dataIndex];
        return `<b>${r.opponent}</b> — Elo ${fmt(r.opp_elo)} (${signed(r.diff, 0)})<br/>` +
          `${t("pred_w")}: ${fmt(100 * r.win, 0)} %<br/>` +
          `${t("pred_d")}: ${fmt(100 * r.draw, 0)} %<br/>` +
          `${t("pred_l")}: ${fmt(100 * r.loss, 0)} %`;
      },
    }),
    legend: legend(),
    xAxis: axisX({ type: "value", max: 100, show: false }),
    yAxis: axisY({ type: "category", inverse: true, splitLine: { show: false },
      data: rows.map(r => r.opponent),
      axisLabel: { color: INK2, fontSize: 11.5 } }),
    series: [
      seg(t("pred_w"), "win", ST_GOOD),
      seg(t("pred_d"), "draw", BASELINE),
      seg(t("pred_l"), "loss", ST_CRIT, [0, 4, 4, 0]),
    ],
  });
  tableView("card_pred", ["", "Elo", "Δ", t("pred_w"), t("pred_d"), t("pred_l")],
    rows.map(r => [r.opponent, fmt(r.opp_elo), signed(r.diff, 0),
                   fmt(100 * r.win, 0) + " %", fmt(100 * r.draw, 0) + " %",
                   fmt(100 * r.loss, 0) + " %"]));

  const c = p.calibration;
  const box = $("pred_note");
  if (box) {
    box.innerHTML = `<p class="sub">${t("pred_calib", {
      peak: fmt(100 * c.draw_peak, 1), n: c.n_close_matches, total: c.n_samples,
    })}</p><p class="sub">${t("pred_caveat")}</p>` +
      (p.fixtures && p.fixtures.length
        ? ""
        : `<p class="sub">${t("pred_no_fixtures")}</p>`);
  }
}
