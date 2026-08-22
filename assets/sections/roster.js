// ---------- roster filter (players index) ----------

function renderRoster() {
  const search = $("roster_search");
  const hideChan = $("hide_chan");
  const count = $("roster_count");
  const cards = Array.from(document.querySelectorAll(".pcard[data-name]"));
  if (!cards.length) { return; }

  function apply() {
    const q = searchKey((search && search.value || "").trim());
    const skipChan = hideChan && hideChan.checked;
    let shown = 0;
    cards.forEach(card => {
      const match = (!q || card.dataset.name.includes(q))
        && !(skipChan && card.dataset.chan === "1");
      card.style.display = match ? "" : "none";
      if (match) { shown++; }
    });
    // hide a position block that has nothing left to show
    document.querySelectorAll("section[data-pos]").forEach(section => {
      const any = Array.from(section.querySelectorAll(".pcard"))
        .some(c => c.style.display !== "none");
      section.style.display = any ? "" : "none";
    });
    if (count) {
      count.textContent = t("roster_count", { shown, total: cards.length });
    }
  }

  if (search && !search.dataset.wired) {
    search.addEventListener("input", apply);
    search.dataset.wired = "1";
  }
  if (hideChan && !hideChan.dataset.wired) {
    hideChan.addEventListener("change", apply);
    hideChan.dataset.wired = "1";
  }
  if (search) { search.placeholder = t("roster_search"); }
  apply();
}
