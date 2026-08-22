// ---------- projections ----------

function renderProjChart() {
  const players = DATA.squad.players.filter(p => p.age_afcon27);
  const rows = ["FW", "MF", "DF", "GK"];
  const pts = players.map((p, i) => ({
    value: [p.age_afcon27, rows.indexOf(p.pos) + ((i % 5) - 2) * 0.09],
    p,
  }));
  const bands = rows.map((pos, i) => [
    { xAxis: PEAK[pos][0], yAxis: i - 0.34, itemStyle: { color: NEUTRAL, opacity: 0.7 } },
    { xAxis: PEAK[pos][1] + 1, yAxis: i + 0.34 },
  ]);
  mkChart("c_proj_age", {
    grid: { left: 8, right: 20, top: 12, bottom: 24, containLabel: true },
    tooltip: tooltip({
      trigger: "item",
      formatter: q => {
        const p = pts[q.dataIndex].p;
        return `<b>${p.name}</b> · ${p.pos} · ${p.club || ""}<br/>` +
          `${fmt(p.age_afcon27, 1)} ${LANG === "fr" ? "ans à la CAN 2027" : "yrs at AFCON 2027"} — ${t("phase_" + p.phase_afcon27)}`;
      },
    }),
    xAxis: axisX({ type: "value", min: 17, max: 38,
      axisLabel: { color: MUTED, fontSize: 11 },
      splitLine: { show: true, lineStyle: { color: GRID, width: 1 } } }),
    yAxis: axisY({ type: "value", min: -1, max: 4, interval: 1,
      splitLine: { show: false },
      axisLabel: { color: INK2, fontSize: 12,
        formatter: v => Number.isInteger(v) && rows[v] ? posLabel(rows[v]) : "" } }),
    series: [{
      type: "scatter", symbolSize: 11,
      data: pts.map(x => x.value),
      itemStyle: { color: S1, borderColor: SURFACE, borderWidth: 2 },
      markArea: { silent: true, data: bands,
        label: { show: false } },
    }],
  });
  const core = DATA.squad.core_generation;
  if (core) {
    $("core_box").innerHTML = `<b>${t("core_title")}</b> — ` + t("core_text", {
      n: core.n, age_now: fmt(core.avg_age_now, 1),
      age_27: fmt(core.avg_age_afcon27, 1), in_peak: core.in_peak_afcon27,
    }) + `<br/><span class="sub">${core.names.slice(0, 9).join(" · ")}</span>`;
  }
  tableView("card_proj", [t("h_player"), t("h_pos"), t("h_age27"), ""],
    [...players].sort((a, b) => a.age_afcon27 - b.age_afcon27)
      .map(p => [p.name, p.pos, fmt(p.age_afcon27, 1), t("phase_" + p.phase_afcon27)]));
  // a just-started season legitimately has 0 apps; only flag finished seasons
  const y = new Date(DATA.meta.generated_at).getFullYear();
  const current = new RegExp(`${y % 100}/${(y + 1) % 100}|\\b${y}\\b`);
  const idle = DATA.pool.profiles.filter(p =>
    p.status === "active" && p.club_form_as_of
    && num(p.club_apps_season) === 0 && !current.test(p.club_season || ""));
  $("readiness_note").textContent = idle.length
    ? t("readiness_note", { list: idle.map(p => p.name).join(", ") })
    : t("readiness_all_ok");
}

// ---------- youth pipeline ----------

function renderPipeline() {
  const p = DATA.team.pipeline;
  const label = LANG === "fr"
    ? { u17: "CAN U-17", u20: "CAN U-20" } : { u17: "U-17 AFCON", u20: "U-20 AFCON" };
  $("pipeline_table").innerHTML = `<tr><th>${t("h_cohort")}</th>
    <th class="num">${t("h_squad_size")}</th><th class="num">${t("h_linked")}</th>
    <th class="num">${t("h_with_apps")}</th><th class="num">${t("h_debut_days")}</th></tr>` +
    p.cohorts.map(c => `<tr>
      <td>${label[c.level.toLowerCase()] || c.level} ${c.window_date.slice(0, 4)}</td>
      <td class="num">${c.squad_size}</td><td class="num">${c.linked}</td>
      <td class="num">${c.with_senior_apps}</td>
      <td class="num">${c.median_days_to_debut === "" ? "–" : fmt(c.median_days_to_debut)}</td></tr>`).join("");
  const top = p.prospects.slice(0, 8);
  $("prospects_note").textContent = t("prospects_note", {
    n: p.prospects.length,
    list: top.map(x => `${x.name} (${x.level}, ${fmt(x.age, 0)}${x.club ? ", " + x.club : ""})`).join(" · "),
  });
}

