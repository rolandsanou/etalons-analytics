// ---------- partnerships, substitution patterns, rest days ----------

function renderPartnerships() {
  const p = (DATA.team || {}).partnerships;
  const table = $("pairs_table");
  if (!p || !table) { return; }
  const rows = p.most_used;
  table.innerHTML = `<tr><th>${t("pr_pair")}</th><th>${t("pr_type")}</th>
    <th class="num">${t("h_matches_c")}</th><th class="num">${t("h_min")}</th>
    <th class="num">${t("pr_gf")}</th><th class="num">${t("pr_ga")}</th>
    <th class="num">${t("pr_gd90")}</th></tr>` +
    rows.map(r => `<tr><td>${r.name_a} · ${r.name_b}</td>
      <td>${r.pair_type}</td><td class="num">${r.matches}</td>
      <td class="num">${fmt(r.minutes)}</td><td class="num">${r.gf}</td>
      <td class="num">${r.ga}</td>
      <td class="num">${r.gd90 === "" ? "–" : signed(r.gd90)}</td></tr>`).join("");
  setText("pairs_note", t("pr_note", {
    qualified: p.qualified, seen: p.pairs_seen,
    min: p.min_minutes, matches: p.min_matches,
  }));

  const extremes = $("pairs_extremes");
  if (extremes) {
    const line = (label, list) => `<tr><td colspan="2"><b>${label}</b></td></tr>` +
      list.map(r => `<tr><td>${r.name_a.split(" ").pop()} · ${r.name_b.split(" ").pop()}
        <span class="sub">${fmt(r.minutes)}'</span></td>
        <td class="num">${signed(r.gd90)}</td></tr>`).join("");
    extremes.innerHTML = line(t("pr_best"), p.best_gd.slice(0, 5))
      + line(t("pr_worst"), p.worst_gd.slice(0, 5));
  }
}

function renderSubpatterns() {
  const s = (DATA.team || {}).subpatterns;
  const table = $("subs_table");
  if (!s || !table) { return; }
  table.innerHTML = `<tr><th>${t("h_coach")}</th><th class="num">${t("h_matches_c")}</th>
    <th class="num">${t("sb_subs")}</th><th class="num">${t("sb_per_match")}</th>
    <th class="num">${t("sb_first")}</th><th class="num">${t("sb_injury")}</th>
    <th class="num">${t("st_leading")}</th><th class="num">${t("st_level")}</th>
    <th class="num">${t("st_trailing")}</th></tr>` +
    s.by_scope.map(r => {
      const thin = r.gated !== 1;
      return `<tr${thin ? ' style="color:var(--muted)"' : ""}>
      <td>${r.scope}</td><td class="num">${r.matches}</td>
      <td class="num">${r.subs}</td><td class="num">${fmt(r.subs_per_match, 2)}</td>
      <td class="num">${r.first_sub_avg === "" ? "–" : fmt(r.first_sub_avg, 0) + "'"}</td>
      <td class="num">${r.injury_subs}</td>
      <td class="num">${r.entries_leading}</td><td class="num">${r.entries_level}</td>
      <td class="num">${r.entries_trailing}</td></tr>`;
    }).join("");

  const dist = s.distribution;
  mkChart("c_subs_dist", {
    grid: { left: 8, right: 12, top: 14, bottom: 24, containLabel: true },
    tooltip: tooltip({ trigger: "axis", axisPointer: { type: "shadow" } }),
    xAxis: axisX({ type: "category", data: dist.map(d => t("sb_band_" + d.band)) }),
    yAxis: axisY({ type: "value", minInterval: 1 }),
    series: [{
      type: "bar", data: dist.map(d => d.n), barMaxWidth: 26,
      itemStyle: { color: S1 },
      label: { show: true, position: "top", color: INK2, fontSize: 11 },
    }],
  });
  tableView("card_subs_dist", [t("sb_when"), t("sb_subs")],
    dist.map(d => [t("sb_band_" + d.band), d.n]));
}

function renderRest() {
  const rows = (DATA.team || {}).rest;
  const table = $("rest_table");
  if (!rows || !table) { return; }
  table.innerHTML = `<tr><th>${t("rd_band")}</th><th class="num">${t("h_matches_c")}</th>
    <th class="num">V-N-D</th><th class="num">${t("pts_per_match")}</th>
    <th class="num">${t("rd_gf")}</th><th class="num">${t("rd_ga")}</th>
    <th class="num">${t("rd_opp_elo")}</th></tr>` +
    rows.map(r => {
      const thin = r.gated !== 1;
      return `<tr${thin ? ' style="color:var(--muted)"' : ""}>
      <td>${t("rd_" + r.band)}</td><td class="num">${r.matches}</td>
      <td class="num">${r.w}-${r.d}-${r.l}</td>
      <td class="num">${fmt(r.ppg, 2)}</td>
      <td class="num">${fmt(r.gf_pm, 2)}</td><td class="num">${fmt(r.ga_pm, 2)}</td>
      <td class="num">${r.opp_elo_avg === null ? "–" : fmt(r.opp_elo_avg)}</td></tr>`;
    }).join("");
  setText("rest_note", t("rd_note"));
}
