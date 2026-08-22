// ---------- breakdowns ----------

function renderClubChart() {
  const counts = Object.entries(DATA.squad.stats.by_club_country)
    .sort((a, b) => b[1] - a[1]);
  const top = counts.slice(0, 12);
  const rest = counts.slice(12).reduce((s, kv) => s + kv[1], 0);
  if (rest) { top.push([LANG === "fr" ? "Autres" : "Other", rest]); }
  mkChart("c_clubs", {
    grid: { left: 8, right: 30, top: 8, bottom: 8, containLabel: true },
    tooltip: tooltip({ trigger: "item" }),
    xAxis: axisX({ type: "value", show: false }),
    yAxis: axisY({ type: "category", inverse: true, splitLine: { show: false },
      data: top.map(kv => kv[0]), axisLabel: { color: INK2, fontSize: 11.5 } }),
    series: [{
      type: "bar", data: top.map(kv => kv[1]), barMaxWidth: 14,
      itemStyle: { color: S1, borderRadius: [0, 4, 4, 0] },
      label: { show: true, position: "right", color: INK2, fontSize: 11 },
    }],
  });
  tableView("card_clubs", [t("h_country"), "N"], counts.map(kv => [kv[0], kv[1]]));
}

function renderLeagueBar() {
  const byG = DATA.squad.stats.by_league_group;
  const total = LEAGUE_ORDER.reduce((s, g) => s + (byG[g] || 0), 0);
  $("league_bar").innerHTML = LEAGUE_ORDER.filter(g => byG[g]).map(g =>
    `<div class="seg" style="width:${100 * byG[g] / total}%;background:${LEAGUE_COLOR[g]}"
      title="${t("lg_" + g)}: ${byG[g]}"></div>`).join("");
  $("league_legend").innerHTML = LEAGUE_ORDER.filter(g => byG[g]).map(g =>
    `<span class="lg-item"><span class="swatch" style="background:${LEAGUE_COLOR[g]}"></span>
     ${t("lg_" + g)} <b>${byG[g]}</b></span>`).join("");
  tableView("card_leagues", [t("c_leagues"), "N"],
    LEAGUE_ORDER.filter(g => byG[g]).map(g => [t("lg_" + g), byG[g]]));
}

// ---------- formations ----------


function formationLabel(r) {
  if (r.formation !== "others") { return r.formation; }
  const n = (r.pooled_from || "").split(";").filter(Boolean).length;
  return t("forms_other", { n });
}

function renderFormsChart() {
  const rows = DATA.team.formations;
  const cats = rows.map(formationLabel);
  const tip = r => `<b>${formationLabel(r)}</b><br/>` + t("forms_tip", {
    n: r.matches, ppg: fmt(r.ppg, 2), gf: r.gf, gfpm: fmt(r.gf_pm, 2),
    ga: r.ga, gapm: fmt(r.ga_pm, 2),
    elo: r.opp_elo_avg ? fmt(r.opp_elo_avg) : "–", nelo: r.n_elo,
  });
  const seg = (name, key, color, labelColor, radius) => ({
    name, type: "bar", stack: "wdl",
    data: rows.map(r => num(r[key])),
    barMaxWidth: 18,
    itemStyle: { color, borderColor: SURFACE, borderWidth: 1,
      borderRadius: radius || 0 },
    label: { show: true, color: labelColor, fontSize: 11,
      formatter: p => (p.value > 0 ? p.value : "") },
  });
  mkChart("c_forms", {
    grid: { left: 8, right: 30, top: 8, bottom: 28, containLabel: true },
    tooltip: tooltip({ trigger: "axis", axisPointer: { type: "shadow" },
      formatter: params => tip(rows[params[0].dataIndex]) }),
    legend: legend(),
    xAxis: axisX({ type: "value", show: false }),
    yAxis: axisY({ type: "category", inverse: true, splitLine: { show: false },
      data: cats, axisLabel: { color: INK2, fontSize: 12 } }),
    series: [
      seg(t("legend_w"), "w", ST_GOOD, "#fff"),
      seg(t("legend_d"), "d", BASELINE, INK2),
      seg(t("legend_l"), "l", ST_CRIT, "#fff", [0, 4, 4, 0]),
    ],
  });
  tableView("card_forms",
    ["", "Pld", t("legend_w"), t("legend_d"), t("legend_l"), "BM/GF", "BE/GA",
     "Pts/m", "Elo adv.", "n Elo"],
    rows.map(r => [formationLabel(r), r.matches, r.w, r.d, r.l, r.gf, r.ga,
      fmt(r.ppg, 2), r.opp_elo_avg ? fmt(r.opp_elo_avg) : "–", r.n_elo]));
}

