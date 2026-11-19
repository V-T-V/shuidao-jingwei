/* ═══════════ 水道经纬 · 全文检索 ═══════════
   Worker 子串检索（js/ftworker.js）· 卷文本懒加载（data/text/jNN.js）
   结果：卷次 + 上下文高亮 + 定位（打开循水/卷视图） */

const SJSEARCH = (() => {
  const input = document.getElementById("search");
  const box = document.getElementById("sresults");
  let worker = null, loadedVols = new Set(), seq = 0, pending = 0;
  let lastResults = [];

  function init() {
    try {
      worker = new Worker("js/ftworker.js");
      worker.onmessage = e => {
        pending = Math.max(0, pending - 1);
        lastResults = lastResults.concat(e.data.hits || []);
        if (pending === 0) render();
      };
    } catch (_e) { worker = null; }   // file:// 下 Worker 可能被拒——退化主线程
    let timer = null;
    input.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(run, 260);
    });
    input.addEventListener("keydown", e => {
      if (e.key === "Escape") { box.style.display = "none"; input.blur(); }
    });
    document.addEventListener("click", e => {
      if (!e.target.closest("#searchwrap")) box.style.display = "none";
    });
  }

  function ensureVols() {
    for (let v = 1; v <= 40; v++) {
      if (loadedVols.has(v)) continue;
      loadedVols.add(v);
      const s = document.createElement("script");
      s.src = `data/text/j${String(v).padStart(2, "0")}.js?v=7`;
      document.head.appendChild(s);
    }
  }

  function run() {
    const q = input.value.trim();
    if (q.length < 2) { box.style.display = "none"; return; }
    ensureVols();
    lastResults = [];
    box.style.display = "block";
    const loadMsg = () => {
      const n = window.SJZTEXT ? Object.keys(window.SJZTEXT).length : 0;
      box.innerHTML = `<div class="sr"><span class="where">检索</span>四十卷加载中 ${n}/40 ……</div>`;
    };
    // 等懒加载脚本就绪（最长 15s，带进度），就绪即检索
    const t0 = performance.now();
    const go = () => {
      if (input.value.trim() !== q) return;                 // 查询已变，弃此轮
      if (!window.SJZTEXT || Object.keys(window.SJZTEXT).length < 40) {
        loadMsg();
        if (performance.now() - t0 > 15000) return;
        return requestAnimationFrame(go);
      }
      if (worker) {
        pending = 1; seq++;
        worker.postMessage({ q, texts: window.SJZTEXT, seq });
      } else {
        for (let v = 1; v <= 40; v++) lastResults.push(...mainThreadHits(q, v));
        render();
      }
    };
    go();
  }

  function mainThreadHits(q, v) {
    const t = window.SJZTEXT[v] || "";
    const hits = [];
    let i = t.indexOf(q);
    while (i >= 0 && hits.length < 4) {
      hits.push({ vol: v, ctx: t.slice(Math.max(0, i - 22), i + q.length + 30) });
      i = t.indexOf(q, i + q.length);
    }
    return hits;
  }

  function render() {
    const q = input.value.trim();
    const hits = lastResults.slice(0, 60);
    if (!hits.length) {
      box.innerHTML = `<div class="sr"><span class="where">无得</span>全书未见「${q}」</div>`;
      box.style.display = "block";
      return;
    }
    box.innerHTML = hits.map((h, i) => {
      const ctx = h.ctx.replace(/&/g, "&amp;").replace(/</g, "&lt;")
        .replace(q, `<mark>${q}</mark>`);
      return `<div class="sr" data-i="${i}"><span class="where">卷${h.vol}</span>${ctx}</div>`;
    }).join("");
    box.style.display = "block";
    box.querySelectorAll(".sr").forEach(el =>
      el.addEventListener("click", () => locate(hits[+el.dataset.i], q)));
  }

  /* 定位：命中水道分节则循水阅读；否则打开卷文本 */
  function locate(hit, q) {
    box.style.display = "none";
    const w = SJZ.waterways.find(x => x.name === q || q.endsWith(x.name));
    if (w) { SJREADER.open(w.id); return; }
    // 卷内水道表：按航点顺序打开第一个命中水
    for (const x of SJZ.waterways) {
      if ((window.SJZTEXT[hit.vol] || "").includes(x.name) && x.vols.includes(`卷${hit.vol}`)) {
        SJREADER.open(x.id);
        return;
      }
    }
    SJAPP.openVol(hit.vol, q);
  }

  return { init, run };
})();
window.SJSEARCH = SJSEARCH;
