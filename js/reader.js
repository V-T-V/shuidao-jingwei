/* ═══════════ 水道经纬 · 循水阅读器（核心体验） ═══════════
   右幅 = 该水经注文本（经文锚 + 其后注文段）
   滚动文本 → 地图飞至当前锚点航点；点击锚点 → 地图跟随
   支流汇入点 → 通行片可切换水道；终点 → 终点卡 + 邻水推荐
   经注对照：经 / 注 / 并排 三态 */

const SJREADER = (() => {
  let curId = null, curAnchor = -1, jzMode = "both";   // both | jing | zhu
  const pbody = () => document.getElementById("pbody");

  /* 锚点 → 航点位置（build 时 jingIdx 已平移为跨卷全局锚序） */
  function anchorPos(w, bodyIdx) {
    for (const p of w.waypoints) {
      if (p.jingIdx === bodyIdx && p.pos) return p;
    }
    // 兜底：就近向前找有坐标的航点
    for (let i = w.waypoints.length - 1; i >= 0; i--) {
      const p = w.waypoints[i];
      if (p.pos && p.jingIdx <= bodyIdx) return p;
    }
    return w.waypoints.find(p => p.pos) || null;
  }

  /* 懒加载循水文本（data/sections.js，1.1MB，首开后离线） */
  function ensureSections() {
    if (typeof SJZ_SECTIONS !== "undefined") return Promise.resolve();
    if (ensureSections._p) return ensureSections._p;
    ensureSections._p = new Promise((ok, bad) => {
      const s = document.createElement("script");
      s.src = "data/sections.js?v=5";
      s.onload = ok;
      s.onerror = () => bad(new Error("sections.js 加载失败"));
      document.head.appendChild(s);
    });
    return ensureSections._p;
  }

  async function open(id) {
    curId = id;
    const w = SJZ.waterways.find(x => x.id === id);
    if (!w) return;
    try { await ensureSections(); } catch (e) { /* 正文暂缺——骨架仍可展示 */ }
    SJAPP.setMode("read");
    SJMAP.select(id, { fly: true });
    SJTREE.highlight(id);
    document.getElementById("vname").textContent = w.name;
    document.getElementById("vseal").textContent = "循水";
    document.getElementById("pmeta").innerHTML = metaHTML(w);
    renderBody(w);
    document.getElementById("panel").classList.add("open");
    document.getElementById("readerbar").classList.remove("hidden");
    curAnchor = -1;
    gotoAnchor(0, false);
  }

  function metaHTML(w) {
    const bits = [];
    bits.push(`<span>卷次 ${w.vols.join(" · ")}</span>`);
    bits.push(`<span>注 ${w.stats.zhuChars.toLocaleString()} 字</span>`);
    bits.push(`<span>经 ${w.stats.jingChars} 字</span>`);
    bits.push(`<span>航点 ${w.waypoints.filter(p => p.pos).length}/${w.waypoints.length}</span>`);
    if (w.stats.citations) bits.push(`<span>引书 ${w.stats.citationKinds} 种 ${w.stats.citations} 次</span>`);
    if (w.terminal) bits.push(`<span>入 ${w.terminal.target}</span>`);
    return bits.join("");
  }

  function renderBody(w) {
    const sec = SJZ_SECTIONS[w.id];
    const host = pbody();
    host.className = jzClass();
    if (!sec) { host.innerHTML = "<p class='kv'>此水分节无文本。</p>"; return; }
    // 跨卷：拼接各分节
    let html = "", bodyBase = 0;
    for (const sid of w.secIds) {
      const s = SJZ_SECTIONS[sid];
      if (!s) continue;
      if (w.secIds.length > 1) html += `<div class="termcard" style="background:rgba(47,93,112,.06);border-color:rgba(47,93,112,.3);color:var(--wave-d)">${s.name} · 卷${s.vol}</div>`;
      html += `<div class="secwrap" data-sec="${sid}">`;
      s.body.forEach((item, i) => {
        const gi = bodyBase + i;
        html += `<div class="anchor" data-i="${gi}">◦ ${item.j || "（篇首）"}<span class="side">${wpSide(w, gi)}</span></div>`;
        // 支流通行片（挂在对应锚）
        const tribsHere = w.tributaries.filter(t => t.jingIdx === i && t.src === "jing");
        if (tribsHere.length) {
          html += `<div>${tribsHere.map(t =>
            `<span class="tribchip ${t.kind === "out" ? "out" : ""}" data-trib="${t.name}" title="${t.kind === "out" ? "从此水分出" : "汇入此水"}${t.dir ? " · " + t.dir : ""}">${t.kind === "out" ? "↑" : "↓"} ${t.name}</span>`).join("")}</div>`;
        }
        (item.z || []).forEach(z => {
          html += `<p class="zhu">${citeLinks(z)}</p>`;
        });
      });
      html += `</div>`;
      bodyBase += s.body.length;
    }
    // 终点卡 + 邻水推荐
    if (w.terminal) {
      const near = neighbors(w);
      html += `<div class="termcard">◆ 入${w.terminal.target} —— ${w.name}之终${w.terminal.pos ? " · 旗标见图" : ""}</div>`;
      if (near.length) {
        html += `<div class="kv" style="margin-top:8px">邻水推荐：${near.map(n =>
          `<span class="tribchip" data-trib="${n}">→ ${n}</span>`).join("")}</div>`;
      }
    }
    host.innerHTML = html;
    // 交互绑定
    host.querySelectorAll(".anchor").forEach(a =>
      a.addEventListener("click", () => gotoAnchor(+a.dataset.i, true)));
    host.querySelectorAll(".tribchip").forEach(c =>
      c.addEventListener("click", () => jumpTrib(c.dataset.trib)));
    host.addEventListener("scroll", onScroll, { passive: true });
  }

  const jzClass = () => jzMode === "jing" ? "readonly-jing" : jzMode === "zhu" ? "readonly-zhu" : "";

  function wpSide(w, gi) {
    const p = w.waypoints.find(x => x.jingIdx === gi);
    return p && p.pos ? `${p.name}${p.side || ""}` : "";
  }

  /* 引书句式 → 可点击（跳引书面板） */
  function citeLinks(z) {
    return z.replace(/《([\u4e00-\u9fff·]{1,12})》(?=[曰云称说])/g,
      (m, b) => `<span class="cite" data-cite="${b}">《${b}》</span>`);
  }

  function neighbors(w) {
    if (!w.terminal) return [];
    const tgt = w.terminal.target;
    if (tgt === "海") return ["江水", "河水", "淮水"].filter(n => n !== w.name);
    const host = SJZ.waterways.find(x => x.name === tgt + "水" || x.name === tgt);
    return host ? [host.name] : [];
  }

  function jumpTrib(name) {
    const t = SJZ.waterways.find(x => x.name === name || name.endsWith(x.name) || x.name.endsWith(name));
    if (t) { open(t.id); return; }
    // 无分节支流 → 全文检索该水名定位卷次
    SJAPP.searchFor(name);
  }

  /* ── 锚点导航与地图跟随 ─────────────────────────── */
  function gotoAnchor(i, fly) {
    const w = SJZ.waterways.find(x => x.id === curId);
    if (!w) return;
    const anchors = pbody().querySelectorAll(".anchor");
    if (!anchors.length) return;
    i = Math.max(0, Math.min(i, anchors.length - 1));
    curAnchor = i;
    anchors.forEach((a, k) => a.classList.toggle("cur", k === i));
    anchors[i].scrollIntoView({ block: "center", behavior: "smooth" });
    const wp = anchorPos(w, i);
    if (wp && wp.pos && fly !== false) {
      SJMAP.flyTo(wp.pos, Math.max(SJMAP.map.getZoom(), 7));
    }
    updateProg(w, i, anchors.length);
  }

  function updateProg(w, i, total) {
    const pct = total > 1 ? Math.round(i / (total - 1) * 100) : 100;
    document.getElementById("rprog").textContent =
      `${w.name} · 源→终 ${pct}%`;
  }

  /* 滚动跟随：可视区中点最近的锚即当前锚（轻量节流） */
  let scrollTimer = null;
  function onScroll() {
    if (scrollTimer) return;
    scrollTimer = setTimeout(() => {
      scrollTimer = null;
      const host = pbody();
      const mid = host.scrollTop + host.clientHeight * .4;
      const anchors = [...host.querySelectorAll(".anchor")];
      let best = 0;
      anchors.forEach((a, k) => { if (a.offsetTop <= mid) best = k; });
      if (best !== curAnchor) {
        curAnchor = best;
        anchors.forEach((a, k) => a.classList.toggle("cur", k === best));
        const w = SJZ.waterways.find(x => x.id === curId);
        if (w) {
          const wp = anchorPos(w, best);
          if (wp && wp.pos) SJMAP.flyTo(wp.pos, Math.max(SJMAP.map.getZoom(), 7));
          updateProg(w, best, anchors.length);
        }
      }
    }, 240);
  }

  function setJzMode(m) {
    jzMode = m;
    const w = SJZ.waterways.find(x => x.id === curId);
    if (w) renderBody(w);
  }
  function cycleJz() {
    setJzMode(jzMode === "both" ? "jing" : jzMode === "jing" ? "zhu" : "both");
  }

  function close() {
    curId = null;
    document.getElementById("readerbar").classList.add("hidden");
  }

  return { open, close, gotoAnchor, cycleJz, get current() { return curId; } };
})();
window.SJREADER = SJREADER;
