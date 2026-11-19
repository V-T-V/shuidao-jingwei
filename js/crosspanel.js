/* ═══════════ 水道经纬 · 互文面板（与方舆经纬跨书互查） ═══════════
   数据：data/crossref.js（方舆经纬《读史方舆纪要》语料中
   《水经注》引用快照——省/府 → 引用次数 + 常并提水名）
   方向二：本站水道详情的「后世引用」栏（SJXREF.waterMentions） */

const SJXREF = (() => {
  /* 方舆经纬线上站（Pages 已活）与省名→站内 pid（深链 #mode=舆图&p=<pid>） */
  const FY_SITE = "https://v-t-v.github.io/fangyu-jingwei/";
  const FY_PID = {
    "北直隶": "beizhi", "南直隶": "nanzhi", "山东": "shandong", "山西": "shanxi",
    "河南": "henan", "陕西": "shanxix", "四川": "sichuan", "湖广": "huguang",
    "江西": "jiangxi", "浙江": "zhejiang", "福建": "fujian", "广东": "guangdong",
    "广西": "guangxi", "云南": "yunnan", "贵州": "guizhou",
  };

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
