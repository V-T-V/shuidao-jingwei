/* ═══════════ 水道经纬 · 水系树导航 ═══════════
   干支层级树（SJZ.tree）→ 左列纲目；点击飞至该水并打开详情 */

const SJTREE = (() => {
  const byId = {};
  SJZ.waterways.forEach(w => byId[w.id] = w);

  function build() {
    const host = document.getElementById("raillist");
    host.innerHTML = "";
    const kids = SJZ.tree.children || {};
    SJZ.tree.roots.forEach(rid => host.appendChild(node(rid, kids, 0)));
  }

  function node(rid, kids, depth) {
    const w = byId[rid];
    const el = document.createElement("div");
    el.className = "tnode";
    if (!w) return el;
    const hasKids = (kids[rid] || []).length > 0;
    const row = document.createElement("div");
    row.className = "trow" + (SJMAP.selected === rid ? " cur" : "");
    row.dataset.rid = rid;
    row.innerHTML =
      `<span class="tglyph">${hasKids ? "▸" : "·"}</span>` +
      `<span class="tname">${w.name}</span>` +
      `<span class="tchars">${(w.stats.chars / 1000).toFixed(1)}k</span>`;
    row.addEventListener("click", e => {
      if (hasKids && e.target.classList.contains("tglyph")) {
        const k = row.nextElementSibling;
        k.classList.toggle("open");
        e.target.textContent = k.classList.contains("open") ? "▾" : "▸";
        return;
      }
      SJAPP.openWater(rid);
    });
    el.appendChild(row);
    if (hasKids) {
      const box = document.createElement("div");
      box.className = "tkids";
      kids[rid].forEach(kid => box.appendChild(node(kid, kids, depth + 1)));
      el.appendChild(box);
    }
    return el;
  }

  function highlight(rid) {
    document.querySelectorAll("#raillist .trow").forEach(r =>
      r.classList.toggle("cur", r.dataset.rid === rid));
  }

  return { build, highlight };
})();
window.SJTREE = SJTREE;
