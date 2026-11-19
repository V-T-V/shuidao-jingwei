/* ═══════════ 水道经纬 · 应用装配（boot / 模式 / 深链 / PWA） ═══════════ */

const SJAPP = (() => {
  let mode = "map";
  const MODE_NOTE = {
    map: "百十二水 · 沿岸县邑见于图",
    read: "循水而读 · 滚动文本，地图随行",
    compare: "古=实线沧浪 · 今=虚线 · 朱红=改道区",
    cites: "引书考古 · 四百二十八种",
    stats: "文本计量 · 注意力/引书/传说/南北",
    cross: "互文 · 顾祖禹九百廿四引",
    about: "关于 · 数据与校勘说明",
  };

  function boot() {
    SJMAP.init();
    SJMAP.onSelect = onRiverClick;
    SJMAP.onWpClick = (w, i) => SJREADER.open(w.id) || SJREADER.gotoAnchor(anchorIndexOf(w, i), true);
    SJMAP.render();
    SJTREE.build();
    SJSEARCH.init();
    bindUI();
    // 序幕
    document.querySelector("#boot .go").addEventListener("click", () => {
      document.getElementById("boot").classList.add("off");
      setTimeout(() => document.getElementById("boot").remove(), 700);
    });
    // 版本行
    document.getElementById("bookstat").textContent =
      `${SJZ.meta.waterways} 水 · ${SJZ.meta.wpTotal} 航点 · 覆盖 ${SJZ.meta.coverage}%`;
    applyHash();
    window.addEventListener("hashchange", applyHash);
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("sw.js").then(() => {
        const el = document.getElementById("swstate");
        el.style.display = ""; el.textContent = "离线就绪";
      }).catch(() => {});
    }
  }

  function anchorIndexOf(w, wpIdx) {
    // 航点 → 全局锚序（循水阅读锚 = 分节内 jingIdx + 前卷偏移）
    const p = w.waypoints[wpIdx];
    let base = 0;
    for (const sid of w.secIds) {
      if (sid === w.id) break;
      base += (SJZ_SECTIONS[sid] || { body: [] }).body.length;
    }
    return base + p.jingIdx;
  }

  function bindUI() {
    document.querySelectorAll("#modes .mode").forEach(b =>
      b.addEventListener("click", () => act(b.dataset.mode)));
    document.getElementById("pclose").addEventListener("click", closePanel);
    document.getElementById("wanderlink").addEventListener("click", () => {
      const ws = SJZ.waterways.filter(w => w.path.length > 3);
      openWater(ws[Math.floor(Math.random() * ws.length)].id);
    });
    document.getElementById("exportlink").addEventListener("click", () => SJEXPORT.menu());
    document.getElementById("smoothlink").addEventListener("click", () => {
      const on = SJMAP.toggleSmooth();
      document.getElementById("smoothlink").textContent = on ? "≈ 平滑·" : "≈ 平滑";
    });
    document.getElementById("tdlink").addEventListener("click", () => {
      location.href = "3d.html?v=10";
    });
    document.getElementById("rtts").addEventListener("click", () => SJREADER.ttsToggle());
    const nightBtn = document.getElementById("nightlink");
    const nightApply = on => {
      document.body.classList.toggle("night", on);
      nightBtn.textContent = on ? "☀ 昼" : "☾ 夜读";
      try { localStorage.setItem("sjzNight", on ? "1" : ""); } catch (e) {}
    };
    nightBtn.addEventListener("click", () => nightApply(!document.body.classList.contains("night")));
    try { if (localStorage.getItem("sjzNight")) nightApply(true); } catch (e) {}
    document.getElementById("rprev").addEventListener("click", () => SJREADER.gotoAnchor(Math.max(0, curAnchorI() - 1), true));
    document.getElementById("rnext").addEventListener("click", () => SJREADER.gotoAnchor(curAnchorI() + 1, true));
    document.getElementById("rjingzhu").addEventListener("click", () => SJREADER.cycleJz());
    window.addEventListener("keydown", e => {
      if (e.key === "Escape") closePanel();
      if ((e.key === "ArrowDown" || e.key === "ArrowUp") && SJREADER.current && e.altKey) {
        e.preventDefault();
        SJREADER.gotoAnchor(curAnchorI() + (e.key === "ArrowDown" ? 1 : -1), true);
      }
    });
    document.getElementById("pbody").addEventListener("click", e => {
      const c = e.target.closest(".cite");
      if (c) SJCITES.open(c.dataset.cite);
    });
  }

  const curAnchorI = () => +([...document.querySelectorAll("#pbody .anchor")].findIndex(a => a.classList.contains("cur")) || 0);

  function onRiverClick(w) {
    if (!w) return;
    if (mode === "map") openWater(w.id, false);
    SJTREE.highlight(w.id);
  }

  function setMode(m) {
    mode = m;
    document.querySelectorAll("#modes .mode").forEach(b =>
      b.classList.toggle("active", b.dataset.mode === m));
    document.getElementById("modelabel").textContent =
      document.querySelector(`#modes .mode[data-mode="${m}"]`).textContent;
    document.getElementById("modenote").textContent = MODE_NOTE[m] || "";
    if (m === "compare") SJMAP.renderModern(true);
    else if (mode !== "compare") SJMAP.renderModern(false);
    if (m === "about") openAbout();
  }

  function act(m) {
    if (m === "cites") return SJCITES.open();
    if (m === "stats") return SJSTATS.open();
    if (m === "cross") return SJXREF.open();
    if (m === "about") return openAbout();
    setMode(m);
    if (m === "map") closePanel();
  }

  function openWater(id, read = true) {
    const w = SJZ.waterways.find(x => x.id === id);
    if (!w) return;
    if (read) {
      SJREADER.open(id);          // 循水而读（含详情）
    } else {
      SJMAP.select(id, { fly: true });
      SJTREE.highlight(id);
      showDetail(w);
    }
    location.hash = (read ? "#r=" : "#w=") + id;
  }

  function showDetail(w) {
    SJAPP.setMode("map");
    document.getElementById("vname").textContent = w.name;
    document.getElementById("vseal").textContent = "水经";
    document.getElementById("pmeta").innerHTML =
      `<span>卷次 ${w.vols.join(" · ")}</span><span>注 ${w.stats.zhuChars.toLocaleString()} 字</span>` +
      `<span>航点 ${w.waypoints.filter(p => p.pos).length}/${w.waypoints.length}</span>` +
      (w.terminal ? `<span>入 ${w.terminal.target}</span>` : "");
    const body = document.getElementById("pbody");
    let html = "";
    const wpList = w.waypoints.filter(p => p.pos);
    if (wpList.length) {
      html += `<div class="sect"><h3>流经</h3><p class="kv">` +
        wpList.map(p => `${p.name}${p.side || ""}`).join(" → ") + `</p></div>`;
    }
    if (w.tributaries.length) {
      const ins = w.tributaries.filter(t => t.kind === "in");
      const outs = w.tributaries.filter(t => t.kind === "out");
      html += `<div class="sect"><h3>支流（汇入 ${ins.length}）</h3><p class="kv">` +
        ins.map(t => `<span class="tribchip" data-trib="${t.name}">↓ ${t.name}</span>`).join("") + `</p>`;
      if (outs.length) html += `<h3 style="margin-top:10px">分出（${outs.length}）</h3><p class="kv">` +
        outs.map(t => `<span class="tribchip out" data-trib="${t.name}">↑ ${t.name}</span>`).join("") + `</p></div>`;
    }
    html += `<div class="sect"><h3>统计</h3><p class="kv">` +
      `注文字数 <b>${w.stats.zhuChars.toLocaleString()}</b> · 经文 <b>${w.stats.jingChars}</b> 字<br>` +
      `引书 <b>${w.stats.citationKinds}</b> 种 <b>${w.stats.citations}</b> 次 · 传说命中 <b>${w.stats.legendHits}</b><br>` +
      `水文词命中 <b>${w.stats.hydroHits}</b>${w.stats.jumps ? ` · ⚠ 可疑跳段 <b>${w.stats.jumps}</b>` : ""}</p></div>`;
    // 后世引用（互文）
    const xm = (typeof SJZ_XREF !== "undefined" && SJZ_XREF.waterMentions && SJZ_XREF.waterMentions[w.name]) || 0;
    if (xm) html += `<div class="sect"><h3>后世引用</h3><p class="kv">《读史方舆纪要》提及此水 <b>${xm}</b> 次 ` +
      `<span class="tribchip" data-cross="1">→ 互文面板</span> ` +
      `<a href="https://v-t-v.github.io/fangyu-jingwei/" target="_blank" rel="noopener" ` +
      `style="color:var(--cinnabar-d,#b23a2e);text-decoration:none;border-bottom:1px dotted;margin-left:4px">方舆经纬对读 ↗</a></p></div>`;
    html += `<button class="ftool" id="goread" style="margin-top:6px">▸ 循水而读</button>`;
    body.innerHTML = html;
    body.className = "";
    body.querySelectorAll(".tribchip[data-trib]").forEach(c =>
      c.addEventListener("click", () => {
        const t = SJZ.waterways.find(x => x.name === c.dataset.trib);
        t ? openWater(t.id) : SJAPP.searchFor(c.dataset.trib);
      }));
    const gr = body.querySelector("#goread");
    if (gr) gr.addEventListener("click", () => openWater(w.id, true));
    const cx = body.querySelector("[data-cross]");
    if (cx) cx.addEventListener("click", () => SJXREF.open());
    document.getElementById("panel").classList.add("open");
    location.hash = "#w=" + w.id;
  }

  function openVol(v, q) {
    setMode("map");
    document.getElementById("vname").textContent = `卷 ${v}`;
    document.getElementById("vseal").textContent = "水经";
    document.getElementById("pmeta").innerHTML = `<span>原文浏览${q ? " · 检索定位" : ""}</span>`;
    const body = document.getElementById("pbody");
    let t = (window.SJZTEXT && window.SJZTEXT[v]) || "";
    if (!t) {
      body.innerHTML = `<p class="kv">加载中……</p>`;
      const s = document.createElement("script");
      s.src = `data/text/j${String(v).padStart(2, "0")}.js?v=10`;
      s.onload = () => openVol(v, q);
      document.head.appendChild(s);
      return;
    }
    if (q) t = t.split(q).join(`<mark style="background:rgba(178,58,46,.25)">${q}</mark>`);
    body.className = "";
    body.innerHTML = t.split("\n").map(ln =>
      ln.startsWith("○") ? `<div class="termcard" style="background:rgba(47,93,112,.06);border-color:rgba(47,93,112,.3);color:var(--wave-d)">${ln.slice(1)}</div>` :
      `<p class="zhu" style="text-indent:0">${ln}</p>`).join("");
    document.getElementById("panel").classList.add("open");
  }

  function openAbout() {
    const m = SJZ.meta;
    setMode("about");
    document.getElementById("vname").textContent = "关于";
    document.getElementById("vseal").textContent = "叙";
    document.getElementById("pmeta").innerHTML = `<span>数据管线 · 方法与边界</span>`;
    const body = document.getElementById("pbody");
    body.className = "";
    body.innerHTML = `
<div class="sect"><h3>水道经纬</h3>
<p class="kv">北魏郦道元《水经注》四十卷数字人文平台。方舆经纬（读史方舆纪要）姊妹项目：
彼以<b>点</b>（府治）织明末版图，此以<b>线</b>（水道）溯北魏江河。</p></div>
<div class="sect"><h3>数据与方法</h3><p class="kv">
· 文本：国学导航本（GB18030 抓取，382,329 字），校勘不在本项目范围<br>
· 经注分离：规则法（方法 A）——程式化句式 + 无引书/无曰/无迳判别；经文 7,442 字（学界预期 7 千 ± 1 千吻合）<br>
· 航点：经文「又东过 X 县南」句式提取，${m.wpTotal} 个；坐标为人工考据近似（±20km 级），覆盖 ${m.coverage}%<br>
· 折线：文本顺序直线连接 + 方位偏移 5km 校正；>200km 跳段标可疑（虚线）<br>
· 引书：《书名》曰/云/称句式，${m.citationKinds} 种<br>
· 「昆仑」等为神话地理坐标，仅示意文本世界</p></div>
<div class="sect"><h3>复用与致谢</h3><p class="kv">
基建承方舆经纬（八件兵器 · 二十五条教训）：PWA 三级缓存 · 全文检索 Worker · 底图兜底 · 深链/分享。
底图 Esri World Physical / Imagery。文本源：国学导航。</p></div>
<div class="sect"><h3>路线图</h3><p class="kv">
Catmull-Rom 平滑 · Natural Earth 真实河线校正 · 3D 河谷（MapLibre 地形）· 经文单辑本校准（方法 B）</p></div>`;
    document.getElementById("panel").classList.add("open");
  }

  function closePanel() {
    document.getElementById("panel").classList.remove("open");
    if (SJREADER.current) SJREADER.close();
    wpLayerSafe();
    location.hash = "#m=map";
  }
  function wpLayerSafe() { /* 航点层保留——水道选中态不因关面板清除 */ }

  function searchFor(q) {
    const el = document.getElementById("search");
    el.value = q;
    el.focus();
    SJSEARCH.run();
  }

  /* 深链：#w=id #r=id #c=书 #m=mode */
  function applyHash() {
    const h = location.hash.slice(1);
    const [k, v] = h.split("=");
    if (k === "w") openWater(v, false);
    else if (k === "r") SJREADER.open(v);
    else if (k === "c") SJCITES.open(decodeURIComponent(v || ""));
    else if (k === "m") setMode(v || "map");
  }

  document.addEventListener("DOMContentLoaded", boot);
  return { openWater, setMode, searchFor, openVol, get mode() { return mode; } };
})();
window.SJAPP = SJAPP;
