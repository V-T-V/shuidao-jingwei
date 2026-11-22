/* ═══════════ 水道经纬 · 引书考古面板 ═══════════
   428 种引书 · 频次排行 · 地域分布（哪些水道引用）· 存世/亡佚标注 */

const SJCITES = (() => {
  /* 学界公论亡佚书（水经注所引大半已亡——按通行文献学结论标注主要者） */
  const LOST = new Set([
    "地理志", "十三州志", "魏土地记", "地理风俗记", "耆旧记", "南康记", "吴录",
    "豫章记", "武昌记", "江记", "汉水记", "荆州记", "襄阳记", "南雍州记", "湘州记",
    "广州记", "交广二州春秋", "异物志", "扶南传", "林邑记", "晋中兴书", "竹书纪年",
    "山海经", "淮南子", "说文", "博物志", "华阳国志", "三秦记", "辛氏三秦记",
    "秦州记", "沙州记", "凉州记", "西河旧事", "博物记", "舆地志", "元和郡县志",
  ]);

  /* 引文全文懒加载（data/cites_quotes.js，121KB，首开后缓存） */
  function ensureQuotes() {
    if (window.SJZ_QUOTES) return Promise.resolve();
    if (ensureQuotes._p) return ensureQuotes._p;
    ensureQuotes._p = new Promise(ok => {
      const s = document.createElement("script");
      s.src = "data/cites_quotes.js?v=19";
      s.onload = ok; s.onerror = ok;
      document.head.appendChild(s);
    });
    return ensureQuotes._p;
  }

  function open(book) {
    SJAPP.setMode("cites");
    document.getElementById("vname").textContent = "引书考古";
    document.getElementById("vseal").textContent = "引书";
    const m = SJZ.meta;
    document.getElementById("pmeta").innerHTML =
      `<span>引书 ${m.citationKinds} 种</span><span>「《书》曰」句式统计</span>` +
      `<span>亡佚者标 †</span>`;
    const body = document.getElementById("pbody");
    if (book) return ensureQuotes().then(() => showBook(body, book));
    const counts = Object.entries(SJZ_CITES.counts).sort((a, b) => b[1] - a[1]);
    let html = `<div class="statgrid">
      <div class="statcard"><b>${m.citationKinds}</b><span>引书种类</span></div>
      <div class="statcard"><b>${Object.values(SJZ_CITES.counts).reduce((a, b) => a + b, 0).toLocaleString()}</b><span>引书总次</span></div>
      <div class="statcard"><b>《地理志》</b><span>被引之冠</span></div>
      <div class="statcard"><b>†</b><span>大半已亡佚</span></div>
    </div>`;
    html += `<div class="sect"><h3>频次排行 · 前六十</h3>`;
    const max = counts[0][1];
    counts.slice(0, 60).forEach(([b, n]) => {
      html += `<div class="hbar"><span class="hn" data-b="${b}">${LOST.has(b) ? "†" : ""}《${b}》</span>` +
        `<span class="hv" style="width:${Math.max(2, n / max * 300)}px"></span>` +
        `<span class="hc">${n}</span></div>`;
    });
    html += `</div><p class="kv">水经注引书逾四百种，十之六七今已亡佚——本书遂为「古籍保存器」。
    点书名看其在哪些水道被引。<b>†</b> 为主要亡佚书例举（非穷尽）。</p>`;
    body.innerHTML = html;
    body.querySelectorAll(".hn").forEach(el =>
      el.addEventListener("click", () => ensureQuotes().then(() => showBook(body, el.dataset.b))));
    document.getElementById("panel").classList.add("open");
  }

  function showBook(body, b) {
    const where = SJZ_CITES.where[b] || {};
    const rivers = Object.entries(where).sort((a, c) => c[1] - a[1]);
    const quotes = (window.SJZ_QUOTES && window.SJZ_QUOTES[b]) || [];
    const max = rivers.length ? rivers[0][1] : 1;
    let html = `<div class="sect"><h3>《${b}》 ${LOST.has(b) ? "†" : ""}</h3>` +
      `<p class="kv">全书被引 <b>${SJZ_CITES.counts[b] || 0}</b> 次 · 分布于 <b>${rivers.length}</b> 条水道` +
      `${quotes.length ? ` · 存世引文样例 <b>${quotes.length}</b> 则` : ""}</p></div>`;
    if (quotes.length) {
      html += `<div class="sect"><h3>引文辑录 <span style="font-size:10px;color:var(--ink-faint)">——郦注所存此书之文 · ${quotes.length} 则</span></h3><div class="quotes-box">`;
      quotes.forEach((it, i) => {
        html += `<div class="quotecard" data-q="${i}">` +
          `<span class="qmeta">卷${it.vol} · ${it.water}</span>${it.q}` +
          `<span class="qgo" title="循水至引文出处">↗</span></div>`;
      });
      html += `</div></div>`;
    }
    html += `<div class="sect"><h3>按水道分布</h3>`;
    rivers.slice(0, 30).forEach(([rn, n]) => {
      html += `<div class="hbar"><span class="hn">${rn}</span>` +
        `<span class="hv" style="width:${Math.max(2, n / max * 260)}px"></span><span class="hc">${n}</span></div>`;
    });
    html += `</div>`;
    html += `<p class="kv">点击水名在循水模式中查看原文引用语境。</p>`;
    body.innerHTML = html;
    body.querySelectorAll(".hn").forEach((el, i) => {
      const rn = rivers[i] && rivers[i][0];
      if (!rn) return;
      el.addEventListener("click", () => {
        const w = SJZ.waterways.find(x => x.name === rn);
        if (w) SJREADER.open(w.id);
      });
    });
    body.querySelectorAll(".quotecard").forEach(el =>
      el.addEventListener("click", () => {
        const it = quotes[+el.dataset.q];
        const w = SJZ.waterways.find(x => x.name === it.water);
        if (w) SJREADER.open(w.id);
      }));
  }

  return { open, LOST };
})();
window.SJCITES = SJCITES;
