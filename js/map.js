/* ═══════════ 水道经纬 · 地图（河流折线渲染器） ═══════════
   折线（线宽=注文字数） · 方向箭头 · 航点 · 支流拓扑 · 终点旗
   古今对照双线层 + 改道区检测 */

const SJMAP = (() => {
  let map, tileLayer = null, tileMode = "physical", tileErrs = 0;
  const rivLayer = L.layerGroup();
  const wpLayer = L.layerGroup();
  const modernLayer = L.layerGroup();
  const devLayer = L.layerGroup();
  let selId = null;
  let onSelect = null;         // 回调：水道被点选
  let onWpClick = null;

  function init() {
    map = L.map("map", {
      attributionControl: false, zoomControl: true,
      center: [34.5, 111.5], zoom: 5,
      maxBounds: SJZ_CONF.bounds, maxBoundsViscosity: .6,
    });
    setBasemap("physical");
    modernLayer.addTo(map);
    devLayer.addTo(map);
    rivLayer.addTo(map);
    wpLayer.addTo(map);
  }

  function setBasemap(mode) {
    if (tileLayer) map.removeLayer(tileLayer);
    tileMode = mode; tileErrs = 0;
    const conf = BASEMAPS[mode];
    tileLayer = L.tileLayer(conf.url, { maxZoom: conf.maxZoom, maxNativeZoom: conf.maxNative }).addTo(map);
    tileLayer.on("tileerror", () => {
      if (++tileErrs > 6 && tileMode !== "physical") setBasemap("physical");  // 瓦片兜底
    });
  }

  const lineWeight = w => Math.max(1.6, Math.min(6, Math.sqrt(w.stats.zhuChars / 2600)));
  const colorOf = w => BASIN_COLORS[w.name] || "#2f5d70";
  let smoothing = false;

  /* Catmull-Rom 平滑（方案 2.3 进阶项）：航点折线 → 曲线细分；
     数据诚实由航点圆点承载——线为插值，点为实录 */
  function smoothPath(pts, seg = 6) {
    if (pts.length < 3 || !smoothing) return pts;
    const out = [];
    const P = i => pts[Math.max(0, Math.min(pts.length - 1, i))];
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = P(i - 1), p1 = P(i), p2 = P(i + 1), p3 = P(i + 2);
      for (let t = 0; t < seg; t++) {
        const s = t / seg, s2 = s * s, s3 = s2 * s;
        out.push([
          .5 * ((2 * p1[0]) + (-p0[0] + p2[0]) * s + (2 * p0[0] - 5 * p1[0] + 4 * p2[0] - p3[0]) * s2 + (-p0[0] + 3 * p1[0] - 3 * p2[0] + p3[0]) * s3),
          .5 * ((2 * p1[1]) + (-p0[1] + p2[1]) * s + (2 * p0[1] - 5 * p1[1] + 4 * p2[1] - p3[1]) * s2 + (-p0[1] + 3 * p1[1] - 3 * p2[1] + p3[1]) * s3),
        ]);
      }
    }
    out.push(pts[pts.length - 1]);
    return out;
  }

  /* ── 水道折线 + 航点 ─────────────────────────────── */
  function render() {
    rivLayer.clearLayers(); wpLayer.clearLayers();
    SJZ.waterways.forEach(w => {
      if (!w.path || w.path.length < 2) return;
      const sel = w.id === selId;
      const line = L.polyline(smoothPath(w.path), {
        className: "rivline",
        color: sel ? "#b23a2e" : colorOf(w),
        weight: sel ? lineWeight(w) + 2.4 : lineWeight(w),
        opacity: sel ? 1 : .82,
        dashArray: w.stats.jumps > 2 ? "10 5" : null,
      });
      line.on("click", () => select(w.id, {fly:false}));
      line.bindTooltip(`${w.name} · ${w.stats.chars} 字 · ${w.waypoints.length} 航点`,
        { direction: "top", opacity: .95, className: "ftip" });
      line.addTo(rivLayer);
    });
  }

  function renderWaypoints(w) {
    wpLayer.clearLayers();
    w.waypoints.forEach((p, i) => {
      if (!p.pos) return;
      const dot = L.circleMarker(p.pos, {
        radius: p.source ? 4.5 : 3,
        color: "#f6f3e6", weight: 1.5, fillColor: p.jump ? "#b23a2e" : "#24495a", fillOpacity: 1,
      });
      dot.bindTooltip(`${p.name}${p.side ? " · " + p.side : ""}（${p.kind}）${p.jump ? " ⚠跳段" : ""}`,
        { direction: "top", opacity: .95 });
      dot.on("click", () => onWpClick && onWpClick(w, i));
      dot.addTo(wpLayer);
    });
    if (w.terminal && w.terminal.pos) {
      L.marker(w.terminal.pos, {
        icon: L.divIcon({ className: "", html: `<span class="termflag">入${w.terminal.target}</span>`, iconSize: null }),
      }).addTo(wpLayer);
    }
  }

  /* ── 古今对照：今水层 + 改道区 ─────────────────────
     NE 真实河线（data/modern_rivers.js）优先，config 手绘线兜底（按 linkTo 合并去重） */
  function modernSet() {
    const ne = (typeof SJZ_MODERN !== "undefined") ? SJZ_MODERN : [];
    const neLinks = new Set(ne.map(x => x.linkTo));
    return ne.concat(MODERN_RIVERS.filter(x => !neLinks.has(x.linkTo)));
  }

  function renderModern(on) {
    modernLayer.clearLayers(); devLayer.clearLayers();
    if (!on) return;
    const MS = modernSet();
    MS.forEach(m => {
      L.polyline(m.pts, { className: "modernline", color: m.color, weight: 3.4, opacity: .9, dashArray: "2 7" })
        .bindTooltip(`今·${m.key}`, { direction: "top" }).addTo(modernLayer);
    });
    // 改道区：古折线（对应水道）每段中点距今水线垂距 > DEVIATION_KM → 朱红高亮
    SJZ.waterways.forEach(w => {
      const m = MS.find(x => x.linkTo === w.name || x.linkTo === w.name.slice(0, -1));
      if (!m || w.path.length < 2) return;
      for (let i = 0; i < w.path.length - 1; i++) {
        const mid = [(w.path[i][0] + w.path[i + 1][0]) / 2, (w.path[i][1] + w.path[i + 1][1]) / 2];
        if (distToPolyline(mid, m.pts) > DEVIATION_KM) {
          L.polyline([w.path[i], w.path[i + 1]], {
            className: "devzone", color: "#b23a2e", weight: 7, opacity: .55,
          }).bindTooltip(`改道区 · ${w.name}（古今偏差 > ${DEVIATION_KM}km）`, { direction: "top" })
            .addTo(devLayer);
        }
      }
    });
  }

  function distToPolyline(pt, pts) {
    let best = 1e9;
    const R = 6371;
    const toXY = p => [R * p[1] * Math.PI / 180 * Math.cos(p[0] * Math.PI / 180), R * p[0] * Math.PI / 180];
    const [x, y] = toXY(pt);
    for (let i = 0; i < pts.length - 1; i++) {
      const [x1, y1] = toXY(pts[i]), [x2, y2] = toXY(pts[i + 1]);
      const dx = x2 - x1, dy = y2 - y1;
      const t = Math.max(0, Math.min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy || 1)));
      best = Math.min(best, Math.hypot(x - (x1 + t * dx), y - (y1 + t * dy)));
    }
    return best;
  }

  /* ── 选中与飞行 ──────────────────────────────────── */
  function select(id, opt = {}) {
    selId = id;
    render();
    const w = SJZ.waterways.find(x => x.id === id);
    if (w) {
      renderWaypoints(w);
      if (opt.fly !== false && w.path.length > 1) {
        map.fitBounds(L.latLngBounds(w.path).pad(.25), { animate: true, duration: 1.1 });
      }
    }
    onSelect && onSelect(w);
  }

  function flyTo(pos, zoom = 8) {
    map.flyTo(pos, zoom, { duration: 1.0 });
  }

  return {
    init, render, select, flyTo, renderModern, setBasemap,
    get map() { return map; },
    set onSelect(fn) { onSelect = fn; },
    set onWpClick(fn) { onWpClick = fn; },
    get selected() { return selId; },
    toggleSmooth() { smoothing = !smoothing; render(); return smoothing; },
    get smoothing() { return smoothing; },
  };
})();
window.SJMAP = SJMAP;
