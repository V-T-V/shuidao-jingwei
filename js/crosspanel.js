/* ═══════════ 水道经纬 · 互文面板（与方舆经纬跨书互查） ═══════════
   数据：data/crossref.js（方舆经纬《读史方舆纪要》语料中
   《水经注》引用快照——省/府 → 引用次数 + 常并提水名）
   方向二：本站水道详情的「后世引用」栏（SJXREF.waterMentions） */

const SJXREF = (() => {
  function open() {
    SJAPP.setMode("cross");
    document.getElementById("vname").textContent = "互文 · 顾祖禹引郦道元";
    document.getElementById("vseal").textContent = "互文";
    const data = (typeof SJZ_XREF !== "undefined") ? SJZ_XREF : { total: 0, provinces: [], waterMentions: {} };
    document.getElementById("pmeta").innerHTML =
      `<span>《读史方舆纪要》引《水经注》</span><span>全书引用快照</span>` +
      `<span>跨书 · 跨 1,100 年</span>`;
    const body = document.getElementById("pbody");
    let html = `<div class="statgrid">
      <div class="statcard"><b>${data.total.toLocaleString()}</b><span>引用总次</span></div>
      <div class="statcard"><b>${data.provinces.length}</b><span>布政使司涉及</span></div>
      <div class="statcard"><b>1,100</b><span>年跨度（527→1692）</span></div>
    </div>`;
    html += `<div class="sect"><h3>按省分布</h3>`;
    const max = data.provinces.length ? data.provinces[0][1] : 1;
    data.provinces.forEach(([p, n]) => {
      html += `<div class="hbar"><span class="hn">${p}</span>` +
        `<span class="hv" style="width:${Math.max(2, n / max * 300)}px"></span><span class="hc">${n}</span></div>`;
    });
    html += `</div>`;
    html += `<div class="sect"><h3>纪要常提之水（与本书对读）</h3>`;
    const wm = Object.entries(data.waterMentions || {}).sort((a, b) => b[1] - a[1]).slice(0, 24);
    const wmMax = wm.length ? wm[0][1] : 1;
    wm.forEach(([n, c]) => {
      html += `<div class="hbar"><span class="hn" data-w="${n}">${n}</span>` +
        `<span class="hv" style="width:${Math.max(2, c / wmMax * 300)}px;background:linear-gradient(90deg,#5a8368,#7fae8d)"></span>` +
        `<span class="hc">${c}</span></div>`;
    });
    html += `</div><p class="kv">顾祖禹（1631-1692）作《读史方舆纪要》遍引前世地志，
    《水经注》为其中古地理引用之冠。点击水名循水而读——同一江河，北魏注家与明末史家的双重目光。</p>`;
    body.innerHTML = html;
    body.querySelectorAll(".hn[data-w]").forEach(el =>
      el.addEventListener("click", () => {
        const w = SJZ.waterways.find(x => x.name === el.dataset.w);
        if (w) SJREADER.open(w.id);
      }));
    document.getElementById("panel").classList.add("open");
  }

  return { open };
})();
window.SJXREF = SJXREF;
