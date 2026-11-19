/* ═══════════ 水道经纬 · 导出（GeoJSON / KML / CSV） ═══════════
   导出对象 = 线（水道折线）+ 点（航点）；当前选中或全部 */

const SJEXPORT = (() => {
  function download(name, mime, text) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([text], { type: mime }));
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 4000);
  }

  const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");

  function menu() {
    const w = SJZ.waterways.find(x => x.id === SJMAP.selected);
    const what = w ? `当前水道（${w.name}）` : "全部水道（112 条）";
    if (!confirm(`导出${what}为 GeoJSON？\n确定=GeoJSON · 取消后用底栏其他入口导 KML/CSV`)) {
      exportAll("kml");
      return;
    }
    exportAll("geojson", w && w.id);
  }

  function collect(id) {
    return id ? SJZ.waterways.filter(w => w.id === id) : SJZ.waterways.filter(w => w.path.length > 1);
  }

  function exportAll(fmt, id) {
    const ws = collect(id);
    if (fmt === "geojson") {
      const fc = {
        type: "FeatureCollection",
        properties: { title: "水经注水道（水道经纬）", generator: "shuidao-jingwei v1" },
        features: ws.flatMap(w => [
          {
            type: "Feature",
            properties: { kind: "waterway", name: w.name, vols: w.vols.join("|"),
              zhu_chars: w.stats.zhuChars, terminal: w.terminal && w.terminal.target || "" },
            geometry: { type: "LineString", coordinates: w.path.map(p => [p[1], p[0]]) },
          },
          ...w.waypoints.filter(p => p.pos).map(p => ({
            type: "Feature",
            properties: { kind: "waypoint", water: w.name, name: p.name,
              type: p.kind, side: p.side, source: !!p.source },
            geometry: { type: "Point", coordinates: [p.pos[1], p.pos[0]] },
          })),
        ]),
      };
      download(id ? `${ws[0].name}.geojson` : "shuijingzhu-rivers.geojson",
        "application/geo+json", JSON.stringify(fc));
    } else if (fmt === "kml") {
      let kml = `<?xml version="1.0" encoding="UTF-8"?>\n<kml xmlns="http://www.opengis.net/kml/2.2">\n<Document>\n`;
      ws.forEach(w => {
        kml += `<Placemark><name>${esc(w.name)}</name><LineString><coordinates>` +
          w.path.map(p => `${p[1]},${p[0]},0`).join(" ") +
          `</coordinates></LineString></Placemark>\n`;
      });
      kml += `</Document>\n</kml>`;
      download("shuijingzhu-rivers.kml", "application/vnd.google-earth.kml+xml", kml);
    } else if (fmt === "csv") {
      let csv = "water,order,waypoint,kind,side,lat,lng,jump\n";
      ws.forEach(w => w.waypoints.filter(p => p.pos).forEach(p => {
        csv += [w.name, w.order, p.name, p.kind, p.side, p.pos[0], p.pos[1], p.jump ? 1 : 0].join(",") + "\n";
      }));
      download("shuijingzhu-waypoints.csv", "text/csv", "\ufeff" + csv);
    }
  }

  return { menu, exportAll };
})();
window.SJEXPORT = SJEXPORT;
