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

