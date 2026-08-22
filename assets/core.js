const S1 = "#2a78d6", S2 = "#eb6834", S3 = "#1baf7a", S4 = "#eda100", S5 = "#e87ba4";
const INK = "#0b0b0b", INK2 = "#52514e", MUTED = "#898781";
const GRID = "#e1e0d9", BASELINE = "#c3c2b7", SURFACE = "#fcfcfb", NEUTRAL = "#f0efec";
const POS_ORDER = ["GK", "DF", "MF", "FW"];
const PEAK = { GK: [26, 33], DF: [25, 30], MF: [24, 29], FW: [24, 29] };
const LEAGUE_ORDER = ["top5", "europe_other", "africa", "home", "world_other"];
const LEAGUE_COLOR = { top5: S1, europe_other: S2, africa: S3, home: S4, world_other: S5 };

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
    borderColor: "rgba(11,11,11,0.10)",
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

const ST_GOOD = "#0ca30c", ST_CRIT = "#d03b3b";

function signed(v, dec = 2) {
  if (v === "" || v === null || v === undefined) { return "–"; }
  return (v > 0 ? "+" : "") + fmt(v, dec);
}

function rgba(hex, a) {
  const n = parseInt(hex.slice(1), 16);
  return `rgba(${(n >> 16) & 255},${(n >> 8) & 255},${n & 255},${a})`;
}

function posLabel(p) { return t("pos_" + p); }
