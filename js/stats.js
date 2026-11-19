/* ═══════════ 水道经纬 · 计量面板（文本分析层） ═══════════
   卷帙分布 · 水道注意力（字数/航点/引书/传说四维）· 传说密度
   · 水文语汇 · 南北不对称 —— 纯 CSS 条形，无图表库 */

const SJSTATS = (() => {
  function open() {
    SJAPP.setMode("stats");
    document.getElementById("vname").textContent = "文本计量";
    document.getElementById("vseal").textContent = "计量";
    const m = SJZ.meta;
    document.getElementById("pmeta").innerHTML =
      `<span>全书 ${m.sections} 分节</span><span>注文 373,587 字</span>` +
      `<span>经文 7,442 字</span><span>经注比 1 : 50</span>`;
    const body = document.getElementById("pbody");
    body.innerHTML = "";
    overview(body);
    attention(body);
    legendDensity(body);
    hydroWords(body);
    northSouth(body);
    document.getElementById("panel").classList.add("open");
  }

  const bar = (label, val, max, w = 260, cls = "hv") =>
    `<div class="hbar"><span class="hn">${label}</span>` +
    `<span class="${cls}" style="width:${Math.max(2, val / max * w)}px"></span>` +
    `<span class="hc">${typeof val === "number" ? val.toLocaleString() : val}</span></div>`;

  function overview(body) {
    const m = SJZ.meta;
    const html = `<div class="statgrid">
      <div class="statcard"><b>${m.waterways}</b><span>水道（合并跨卷）</span></div>
      <div class="statcard"><b>${m.wpTotal}</b><span>航点</span></div>
      <div class="statcard"><b>${m.coverage}%</b><span>航点坐标覆盖</span></div>
      <div class="statcard"><b>${m.citationKinds}</b><span>引书种类</span></div>
    </div>`;
    body.insertAdjacentHTML("beforeend", `<div class="sect"><h3>总览</h3>${html}</div>`);
  }

  /* 水道注意力：字数前 25 */
  function attention(body) {
    const top = [...SJZ.waterways].sort((a, b) => b.stats.zhuChars - a.stats.zhuChars).slice(0, 25);
    const max = top[0].stats.zhuChars;
    let html = `<p class="kv">郦道元的注意力分配——河水独占五卷（<b>${(top[0].stats.zhuChars / 373587 * 100).toFixed(1)}%</b> 全书），长尾极重：前八水已近半部。</p>`;
    top.forEach(w => {
      html += `<div class="hbar"><span class="hn" data-r="${w.id}">${w.name}</span>` +
        `<span class="hv" style="width:${Math.max(2, w.stats.zhuChars / max * 300)}px"></span>` +
        `<span class="hc">${w.stats.zhuChars.toLocaleString()} 字 · 引 ${w.stats.citations} · 传说 ${w.stats.legendHits}</span></div>`;
    });
    body.insertAdjacentHTML("beforeend", `<div class="sect"><h3>水道注意力 · 注文字数前二十五</h3>${html}</div>`);
  }

  /* 传说密度：传说命中/千字 排行（干流 vs 支流分野可见） */
  function legendDensity(body) {
    const arr = SJZ.waterways.filter(w => w.stats.chars > 800)
      .map(w => ({ name: w.name, id: w.id, d: w.stats.legendHits / w.stats.chars * 1000 }))
      .sort((a, b) => b.d - a.d).slice(0, 20);
    const max = arr[0].d;
    let html = `<p class="kv">每千字传说词命中（相传/昔/黄帝/禹/神/龙/仙/怪……）——源头与边地传说浓，中下游漕运实录多。</p>`;
    arr.forEach(x => {
      html += bar(x.name, x.d.toFixed(1), max, 300);
    });
    body.insertAdjacentHTML("beforeend", `<div class="sect"><h3>传说密度 · 千字命中前二十</h3>${html}</div>`);
  }

  /* 水文语汇：16 水文词全书频次 */
  function hydroWords(body) {
    // 用水道级 hydroHits 反推不出词频——改为从词表估读：直接扫 sections 需懒加载，
    // 这里以水道 hydroHits 聚合呈现词族总量 + 语汇密度排行
    const total = SJZ.waterways.reduce((a, w) => a + w.stats.hydroHits, 0);
    const arr = SJZ.waterways.filter(w => w.stats.chars > 800)
      .map(w => ({ name: w.name, d: w.stats.hydroHits / w.stats.chars * 1000 }))
      .sort((a, b) => b.d - a.d).slice(0, 15);
    const max = arr[0].d;
    let html = `<p class="kv">水文词族（源·流·注·决·溢·涸·涨·泝·渡·津·堰·堤·渠·灌·渊·潭·浦）全书命中 <b>${total.toLocaleString()}</b> 次——北魏水文的一手观察密度。</p>`;
    arr.forEach(x => html += bar(x.name, x.d.toFixed(1), max, 300));
    body.insertAdjacentHTML("beforeend", `<div class="sect"><h3>水文语汇密度 · 千字命中前十五</h3>${html}</div>`);
  }

  /* 南北不对称：以航点中位纬度分南北，比字数/引书/传说 */
  function northSouth(body) {
    const north = { chars: 0, cites: 0, legend: 0, n: 0 };
    const south = { chars: 0, cites: 0, legend: 0, n: 0 };
    SJZ.waterways.forEach(w => {
      const lats = w.waypoints.filter(p => p.pos).map(p => p.pos[0]);
      if (!lats.length) return;
      lats.sort((a, b) => a - b);
      const mid = lats[Math.floor(lats.length / 2)];
      const t = mid >= 33 ? north : south;
      t.chars += w.stats.chars; t.cites += w.stats.citations; t.legend += w.stats.legendHits; t.n++;
    });
    const rows = [
      ["水道数", north.n, south.n],
      ["注文字数", north.chars, south.chars],
      ["引书次数", north.cites, south.cites],
      ["传说命中", north.legend, south.legend],
    ];
    let html = `<p class="kv">以航点中位纬度 33° 分界（淮渭一线）。郦道元北人，南方记述多据文献——引书密度南高，亲历细节北多。</p>`;
    rows.forEach(([label, a, b]) => {
      const m = Math.max(a, b) || 1;
      html += `<div class="hbar"><span class="hn">${label}</span>` +
        `<span class="hv" style="width:${a / m * 170}px;background:linear-gradient(90deg,#24495a,#4a7a9b)"></span>` +
        `<span class="hc">北 ${a.toLocaleString()}</span>` +
        `<span class="hv" style="width:${b / m * 170}px;background:linear-gradient(90deg,#3d7a72,#5f9d8f)"></span>` +
        `<span class="hc">南 ${b.toLocaleString()}</span></div>`;
    });
    body.insertAdjacentHTML("beforeend", `<div class="sect"><h3>南北不对称</h3>${html}</div>`);
  }

  return { open };
})();
window.SJSTATS = SJSTATS;
