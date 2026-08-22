// ---------- elo ----------

function renderEloChart() {
  const tl = DATA.elo.timeline;
  const hist = tl.map(p => [p.date, p.elo]);
  const peak = DATA.elo.peak;
  const fc = DATA.elo.forecast;
  const last = tl[tl.length - 1];
  const eras = (DATA.history.coaches || [])
    .filter(r => !r.pooled && r.first_match >= "2008")
    .sort((a, b) => a.first_match.localeCompare(b.first_match));
  const series = [{
    name: t("elo_hist"), type: "line", data: hist, showSymbol: false,
    lineStyle: { color: S1, width: 2 }, itemStyle: { color: S1 },
    markArea: {
      silent: true,
      data: eras.map((r, i) => [
        { xAxis: r.first_match,
          itemStyle: { color: NEUTRAL, opacity: i % 2 ? 0.55 : 0.28 },
          label: { show: true, position: "insideTop", color: MUTED, fontSize: 10,
            formatter: r.coach.split(" ").pop() } },
        { xAxis: r.last_match },
      ]),
    },
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

