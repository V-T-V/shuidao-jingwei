/* ═══════════ 水道经纬 · 互文面板（跨书互查，双页签） ═══════════
   页签一 顾祖禹引郦注：方舆经纬《读史方舆纪要》语料引《水经注》快照
     （data/crossref.js —— 省/府引用计数 + 常并提水名；省名深链方舆经纬省域）
   页签二 引伽蓝记：伽蓝经纬站际桥回程（伽蓝站已建单向桥，此补双向）——
     谷水注/洛水注命中伽蓝记名物，按水道分组（城门/伽蓝/衙署·宫室/地标）
     + 10 对对读样例 + ↗伽蓝经纬深链（data/xrev_ql.js 懒加载，相对兄弟路径） */

const SJXREF = (() => {
  /* 方舆经纬线上站（Pages 已活）与省名→站内 pid（深链 #mode=舆图&p=<pid>） */
  const FY_SITE = "https://v-t-v.github.io/fangyu-jingwei/";
  const FY_PID = {
    "北直隶": "beizhi", "南直隶": "nanzhi", "山东": "shandong", "山西": "shanxi",
    "河南": "henan", "陕西": "shanxix", "四川": "sichuan", "湖广": "huguang",
    "江西": "jiangxi", "浙江": "zhejiang", "福建": "fujian", "广东": "guangdong",
    "广西": "guangxi", "云南": "yunnan", "贵州": "guizhou",
  };

  let tab = "gu";          /* "gu" 顾祖禹 | "ql" 引伽蓝记 */
  let qlReq = null;        /* 懒加载去重（仿 stats.js inventoryList） */

  function open(which) {
    if (which) tab = which;
    SJAPP.setMode("cross");
    document.getElementById("vname").textContent = "互文 · 跨书互查";
    document.getElementById("vseal").textContent = "互文";
    document.getElementById("pmeta").innerHTML = tab === "gu"
      ? `<span>《读史方舆纪要》引《水经注》</span><span>全书引用快照</span>` +
        `<span>跨书 · 跨 1,100 年</span>`
      : `<span>谷水注 / 洛水注 × 伽蓝记名物</span><span>伽蓝经纬站际桥（回程）</span>` +
        `<span>同城异代 · 郦 527 前 → 杨 547</span>`;
    const body = document.getElementById("pbody");
    body.className = "";
    body.innerHTML =
      `<div class="xtabs">` +
      `<button class="xtab${tab === "gu" ? " cur" : ""}" data-t="gu">顾祖禹引郦注</button>` +
      `<button class="xtab${tab === "ql" ? " cur" : ""}" data-t="ql">引伽蓝记</button></div>` +
      `<div id="xbody"></div>`;
    body.querySelectorAll(".xtab").forEach(b =>
      b.addEventListener("click", () => open(b.dataset.t)));
    const host = body.querySelector("#xbody");
    if (tab === "gu") renderGu(host);
    else qlLoad(host);
    document.getElementById("panel").classList.add("open");
  }

  /* ── 页签一：顾祖禹引《水经注》（原互文面板） ── */
  function renderGu(host) {
    const data = (typeof SJZ_XREF !== "undefined") ? SJZ_XREF : { total: 0, provinces: [], waterMentions: {} };
    let html = `<div class="statgrid">
      <div class="statcard"><b>${data.total.toLocaleString()}</b><span>引用总次</span></div>
      <div class="statcard"><b>${data.provinces.length}</b><span>布政使司涉及</span></div>
      <div class="statcard"><b>1,100</b><span>年跨度（527→1692）</span></div>
    </div>`;
    html += `<div class="sect"><h3>按省分布 <span style="font-size:10px;color:var(--ink-faint)">点省名 → 方舆经纬观其省域</span></h3>`;
    const max = data.provinces.length ? data.provinces[0][1] : 1;
    data.provinces.forEach(([p, n]) => {
      const pid = FY_PID[p];
      const link = pid ? `${FY_SITE}#mode=%E8%88%86%E5%9B%BE&p=${pid}` : FY_SITE;
      html += `<div class="hbar"><span class="hn"><a href="${link}" target="_blank" rel="noopener" ` +
        `style="color:inherit;text-decoration:none;border-bottom:1px dotted rgba(74,122,155,.6)" ` +
        `title="赴方舆经纬 · ${p}">${p}</a></span>` +
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
    host.innerHTML = html;
    host.querySelectorAll(".hn[data-w]").forEach(el =>
      el.addEventListener("click", () => {
        const w = SJZ.waterways.find(x => x.name === el.dataset.w);
        if (w) SJREADER.open(w.id);
      }));
  }

  /* ── 页签二：引伽蓝记（伽蓝经纬站际桥回程） ──
     数据 data/xrev_ql.js 懒加载（tools/build_xrev_ql.py 生成，LYGL 只读）；
     深链 ../LYGL/#juan=#gl= / #gate= 为相对兄弟路径——须父目录同根服务。 */
  function qlLoad(host) {
    if (window.SJZ_QL) return renderQl(host);
    host.innerHTML = `<div class="sect"><p class="kv">互查数据装载中…</p></div>`;
    if (qlReq) return;
    qlReq = new Promise(ok => {
      const s = document.createElement("script");
      s.src = "data/xrev_ql.js?v=18";
      s.onload = ok;
      s.onerror = ok;
      document.head.appendChild(s);
    }).then(() => {
      qlReq = null;
      const h = document.getElementById("xbody");
      if (!h) return;                       /* 面板已关/已切页签 */
      if (!window.SJZ_QL) {
        h.innerHTML = `<div class="sect"><p class="kv">互查数据未载入（离线首访）——联网后重开即得。</p></div>`;
        return;
      }
      renderQl(h);
    });
  }

  function renderQl(host) {
    const d = window.SJZ_QL;
    const t = d.totals;
    const zhuSum = Object.values(t.zhuChars).reduce((a, b) => a + b, 0);
    let html = `<div class="statgrid">
      <div class="statcard"><b>${t.placeHits}</b><span>命中伽蓝记名物</span></div>
      <div class="statcard"><b>${t.pairs}</b><span>对读样例（对）</span></div>
      <div class="statcard"><b>${t.aMentions}</b><span>伽蓝记提水道（次）</span></div>
      <div class="statcard"><b>${zhuSum.toLocaleString()}</b><span>两注快照字数</span></div>
    </div>`;

    d.waters.forEach(w => {
      if (!w.kinds.length) {                 /* 阳渠：无独立分节，如实注记 */
        html += `<div class="sect"><h3>${w.name}</h3><p class="kv">${w.note}。` +
          `伽蓝记提及 <b>${w.qlMentions}</b> 次。</p></div>`;
        return;
      }
      html += `<div class="sect"><h3>${w.name}注 × 伽蓝记名物</h3>` +
        `<p class="kv">注文快照 <b>${w.zhuChars.toLocaleString()}</b> 字 · 命中 <b>${w.hitNames}</b> 名物 <b>${w.hitN}</b> 次` +
        `${w.qlNote ? `（${w.qlNote}）` : ""}——点 ↗ 赴伽蓝经纬观其城。</p>`;
      const maxN = Math.max(...w.kinds.flatMap(g => g.items.map(x => x.n)));
      w.kinds.forEach(g => {
        html += `<div class="xkind">${g.kind} · ${g.items.length}</div>`;
        g.items.forEach(x => {
          html += `<div class="hbar"><span class="hn" style="width:118px">${x.name}</span>` +
            `<span class="hv" style="width:${Math.max(2, x.n / maxN * 180)}px"></span>` +
            `<span class="hc">${x.n} 次 · <a class="xlink" href="${x.href}" target="_blank" rel="noopener" ` +
            `title="赴伽蓝经纬 · ${x.name}">↗伽蓝</a></span></div>` +
            `<div class="xsamp">…${x.sample}…${x.note ? `（${x.note}）` : ""}</div>`;
        });
      });
      html += `</div>`;
    });

    /* 对读样例：伽蓝记句深链彼站，郦注句回环本站循水 */
    html += `<div class="sect"><h3>样例对读 · ${t.pairs} 对 <span style="font-size:10px;color:var(--ink-faint)">` +
      `杨句 ↗伽蓝经纬 · 郦句 ↗本站循水</span></h3>`;
    d.pairs.forEach(p => {
      html += `<div class="xpair"><div class="xpname">${p.name}` +
        `<span class="xpk">${p.kind} · ${p.water}注</span>` +
        `<a class="xlink" href="${p.qlHref}" target="_blank" rel="noopener">↗伽蓝记</a></div>` +
        `<div class="xpq"><span class="xptag">伽蓝记</span>${p.ql}</div>` +
        `<div class="xps"><span class="xptag">${p.water}注</span>${p.sjz}` +
        ` <span class="xlink" data-r="${p.waterId}" title="循水而读 ${p.water}">↗循水</span></div></div>`;
    });
    html += `</div>`;

    const nk = Object.entries(d.noHit.byKind).sort((a, b) => b[1] - a[1])
      .map(([k, n]) => `${k} ${n}`).join(" · ");
    html += `<div class="sect"><h3>无对应注记（如实口径）</h3><p class="kv">` +
      `桥上判读名物 ${d.noHit.total + t.placeHits} 项（伽蓝经纬四表＋附加地标，同名合并），` +
      `命中 ${t.placeHits}，无对应 <b>${d.noHit.total}</b>（${nk}）——` +
      `城门仅 <b>${d.noHit.gates.join("、")}</b> 不见于两注。</p></div>`;

    const ex = d.aSide.excluded.map(e => `${e.name}(${e.n})`).join("、");
    html += `<div class="sect"><h3>伽蓝记提及本站水道 · ${d.aSide.total} 次</h3>`;
    d.aSide.waters.forEach(w => {
      html += `<div class="hbar"><span class="hn" data-r="${w.sjzId}" style="width:118px">${w.name}</span>` +
        `<span class="hc">${w.n} 次${w.note ? `（${w.note}）` : ""}</span></div>`;
    });
    html += `<p class="kv">排除同名假阳性：${ex}——皆普通词序（「决水种麦」「渡一深水」），非水道专名。</p></div>`;

    html += `<p class="kv">${d.note} <a class="xlink" href="${d.site}" target="_blank" rel="noopener">↗伽蓝经纬</a></p>`;
    host.innerHTML = html;
    host.querySelectorAll(".xlink[data-r]").forEach(el =>
      el.addEventListener("click", () => SJREADER.open(el.dataset.r)));
  }

  return { open };
})();
window.SJXREF = SJXREF;
