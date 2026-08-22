// Chart colours are read from the CSS custom properties rather than hardcoded,
// so a theme switch repaints every chart from the same tokens the page uses.
// They stay mutable globals because every section file references them directly.
let S1, S2, S3, S4, S5, INK, INK2, MUTED, GRID, BASELINE, SURFACE, NEUTRAL;
let ST_GOOD, ST_CRIT, CHART_LINE, ON_FILL;

function readThemeTokens() {
  const cs = getComputedStyle(document.documentElement);
  const token = (name, fallback) => cs.getPropertyValue(name).trim() || fallback;
  S1 = token("--s1", "#c0142b");
  S2 = token("--s2", "#2e6da4");
  S3 = token("--s3", "#0e8a5f");
  S4 = token("--s4", "#d6a00a");
  S5 = token("--s5", "#7b4e7f");
  INK = token("--ink", "#1b1a17");
  INK2 = token("--ink-2", "#55534d");
  MUTED = token("--muted", "#6e6b64");
  GRID = token("--hair", "#e5e2db");
  BASELINE = token("--rule", "#cfcac0");
  SURFACE = token("--surface", "#ffffff");
  NEUTRAL = token("--neutral-bg", "#f0ede7");
  ST_GOOD = token("--s3", "#0e8a5f");
  ST_CRIT = token("--s1", "#c0142b");
  CHART_LINE = token("--chart-border", "rgba(27,26,23,0.10)");
  // text drawn inside a coloured fill needs to stay legible in both themes
  ON_FILL = token("--on-fill", "#ffffff");
  LEAGUE_COLOR = { top5: S1, europe_other: S2, africa: S3, home: S4,
                   world_other: S5 };
}

const POS_ORDER = ["GK", "DF", "MF", "FW"];
const PEAK = { GK: [26, 33], DF: [25, 30], MF: [24, 29], FW: [24, 29] };
const LEAGUE_ORDER = ["top5", "europe_other", "africa", "home", "world_other"];
let LEAGUE_COLOR = {};

let DATA = null;
const CHARTS = [];

const $ = id => document.getElementById(id);
const num = x => (x === "" || x === null || x === undefined) ? 0 : Number(x);

function axisX(extra) {
  return Object.assign({
    axisLine: { lineStyle: { color: BASELINE } },
    axisTick: { show: false },
    axisLabel: { color: MUTED, fontSize: 11 },
    splitLine: { show: false },
  }, extra || {});
}

function axisY(extra) {
  return Object.assign({
    axisLine: { show: false },
    axisTick: { show: false },
    axisLabel: { color: MUTED, fontSize: 11 },
    splitLine: { lineStyle: { color: GRID, width: 1 } },
  }, extra || {});
}

function tooltip(extra) {
  return Object.assign({
    backgroundColor: SURFACE,
    borderColor: CHART_LINE,
    borderWidth: 1,
    textStyle: { color: INK, fontSize: 12 },
    confine: true,
  }, extra || {});
}

function legend(extra) {
  return Object.assign({
    bottom: 0, itemWidth: 10, itemHeight: 10, icon: "roundRect",
    textStyle: { color: INK2, fontSize: 11.5 },
  }, extra || {});
}

function mkChart(id, option) {
  const el = $(id);
  if (!el) { return null; }
  const prev = echarts.getInstanceByDom(el);
  if (prev) { prev.dispose(); }
  const inst = echarts.init(el, null, { renderer: "svg" });
  inst.setOption(option);
  CHARTS.push(inst);
  return inst;
}

function tableView(cardId, headers, rows) {
  const card = $(cardId);
  if (!card) { return; }
  let d = card.querySelector("details.tv");
  if (!d) {
    d = document.createElement("details");
    d.className = "tv";
    card.appendChild(d);
  }
  const body = rows.map(r => `<tr>${r.map((c, i) =>
    `<td class="${i > 0 ? "num" : ""}">${c}</td>`).join("")}</tr>`).join("");
  d.innerHTML = `<summary>${t("show_data")}</summary><div class="tablewrap"><table>
    <tr>${headers.map((h, i) => `<th class="${i > 0 ? "num" : ""}">${h}</th>`).join("")}</tr>${body}</table></div>`;
}

// Accent-insensitive search key: "Traore" and "Traore" with an accent must
// match each other, which matters for nearly every name in this dataset.
function searchKey(text) {
  return String(text || "").normalize("NFD")
    .replace(/\p{Diacritic}/gu, "").toLowerCase();
}

// --- shared across sections (kept here so every page has them) ---


function signed(v, dec = 2) {
  if (v === "" || v === null || v === undefined) { return "–"; }
  return (v > 0 ? "+" : "") + fmt(v, dec);
}

function rgba(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

function posLabel(p) { return t("pos_" + p); }
