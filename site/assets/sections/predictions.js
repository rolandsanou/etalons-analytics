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
  let prevComp = "";
  const box = $("pred_note");
  if (box) {
    box.innerHTML = `<p class="sub">${t("pred_calib", {
      peak: fmt(100 * c.draw_peak, 1), n: c.n_close_matches, total: c.n_samples,
    })}</p><p class="sub">${t("pred_caveat")}</p>` +
      (p.fixtures && p.fixtures.length
        // list them rather than only noting their absence: the whole point of
        // the calibration above is to read the next matches against it
        // CAF sets pairings and windows before dates, so a fixture shows
        // whichever it has. A window is never printed as if it were a date.
        ? `<p class="sub">${t("pred_fixtures")}</p><ul class="fixlist">` +
          p.fixtures.map(f => {
            const when = f.date_confirmed === "1" && f.date
              ? f.date
              : t("fx_window", { start: f.window_start, end: f.window_end });
            const md = f.matchday ? t("fx_md", { n: f.matchday }) + " · " : "";
            // name the competition only when it changes, so a single-campaign
            // list does not repeat it on every line
            const comp = f.tournament && f.tournament !== prevComp
              ? " · " + f.tournament : "";
            prevComp = f.tournament;
            return `<li><strong>${f.opponent}</strong> · ${md}${when}${comp}` +
              ` <span class="season">${t("venue_" + (f.venue || "N"))}</span></li>`;
          }).join("") + "</ul>" +
          `<p class="sub">${t("fx_home_caveat")}</p>`
        : `<p class="sub">${t("pred_no_fixtures")}</p>`);
  }
}
