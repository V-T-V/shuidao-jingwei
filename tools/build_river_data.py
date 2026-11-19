"""水道经纬 · Phase 2 数据产物构建
输入: data/intermediate/rivers.json · tools/gazetteer.py · data/vol/*.txt
输出: data/river_data.js   —— 水道结构（折线/航点/支流/终点/统计/水系树）
      data/sections.js     —— 循水阅读文本（经注分离 · 按锚分段）
      data/citations.js    —— 引书考古
      data/text/j01..j40.js —— 全文懒加载（检索层）
      data/build_report.json
算法: 设计方案 2.3 —— 文本顺序连线 · 方位偏移 5km · >200km 跳段标记
"""
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gazetteer import all_coords, resolve

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INT = os.path.join(ROOT, "data", "intermediate")
DATA = os.path.join(ROOT, "data")
coords = all_coords()

SIDE_OFFSET_DEG = 0.045       # 约 5km
SIDE_OFFSET_LNG = 0.060


def offset_side(lat, lng, side):
    if not side:
        return [round(lat, 4), round(lng, 4)]
    dlat, dlng = 0.0, 0.0
    if "南" in side: dlat -= SIDE_OFFSET_DEG
    if "北" in side: dlat += SIDE_OFFSET_DEG
    if "东" in side: dlng += SIDE_OFFSET_LNG
    if "西" in side: dlng -= SIDE_OFFSET_LNG
    return [round(lat + dlat, 4), round(lng + dlng, 4)]


def dist_km(a, b):
    R = 6371.0
    la1, lo1, la2, lo2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * R * math.asin(math.sqrt(h))


def base_name(header):
    m = re.match(r"^([\u4e00-\u9fff〈〉]{1,6}?水)([一二三四五六七八九十]+)?", header)
    return m.group(1) if m else header.split()[0]


def main():
    rivers = json.load(open(os.path.join(INT, "rivers.json"), encoding="utf-8"))["rivers"]
    citations = json.load(open(os.path.join(INT, "citations.json"), encoding="utf-8"))

    # ── 合并跨卷同名水（河水一~五 → 河水）──
    merged, order_seq = [], []
    for r in rivers:
        if r["type"] != "water":
            continue
        bn = base_name(r["header"])
        found = None
        for m in merged:
            if m["name"] == bn:
                found = m
                break
        if found is None:
            found = {"id": r["id"], "name": bn, "header": r["header"], "vols": [],
                     "sections": [], "order": len(merged) + 1}
            merged.append(found)
        found["vols"].append(f"卷{int(r['vol'])}")
        found["sections"].append(r)

    # ── 逐水解析航点 → 折线 ──
    waterways = []
    wp_total = wp_resolved = 0
    for m in merged:
        path, waypoints = [], []
        jumps = 0
        for sec in m["sections"]:
            for w in sec["waypoints"]:
                wp_total += 1
                rr = resolve(w["name"], coords)
                wp = {"name": w["name"], "kind": w["kind"], "side": w.get("side", ""),
                      "jingIdx": w["jing_idx"], "vol": int(sec["vol"])}
                if w.get("source"):
                    wp["source"] = True
                if rr:
                    wp_resolved += 1
                    base = [rr[0], rr[1]]
                    wp["pos"] = offset_side(base[0], base[1], w.get("side", ""))
                    wp["near"] = rr[2]
                    if path and dist_km(path[-1], wp["pos"]) > 200:
                        wp["jump"] = True
                        jumps += 1
                    path.append(wp["pos"])
                waypoints.append(wp)
        # 支流（去重保序）
        tribs, seen = [], set()
        for sec in m["sections"]:
            for t in sec["tributaries"]:
                key = t["name"] + t["kind"]
                if key in seen:
                    continue
                seen.add(key)
                tribs.append({"name": t["name"], "kind": t["kind"],
                              "dir": t.get("dir", ""), "src": t.get("src", "jing"),
                              "jingIdx": t.get("jing_idx", -1)})
        terminal = next((s["terminal"] for s in reversed(m["sections"]) if s["terminal"]), None)
        stats = {
            "chars": sum(s["stats"]["chars"] for s in m["sections"]),
            "zhuChars": sum(s["stats"]["zhu_chars"] for s in m["sections"]),
            "jingChars": sum(s["stats"]["jing_chars"] for s in m["sections"]),
            "citations": sum(s["stats"]["citations"] for s in m["sections"]),
            "citationKinds": sum(s["stats"]["citation_kinds"] for s in m["sections"]),
            "legendHits": sum(s["stats"]["legend_hits"] for s in m["sections"]),
            "hydroHits": sum(s["stats"]["hydro_hits"] for s in m["sections"]),
            "jumps": jumps,
        }
        # 终点坐标（若有）
        if terminal:
            term_pos = None
            tgt = terminal["target"]
            for key in (tgt, tgt + "水", "海"):
                if key in coords:
                    term_pos = coords[key][:2]
                    break
            if term_pos:
                terminal = dict(terminal, pos=term_pos)
        waterways.append({
            "id": m["id"], "name": m["name"], "vols": m["vols"], "order": m["order"],
            "path": path, "waypoints": waypoints, "tributaries": tribs,
            "terminal": terminal, "stats": stats,
            "secIds": [s["id"] for s in m["sections"]],
        })

    # ── 水系树：支流边 → 父子（有分节者入树）──
    name2id = {w["name"]: w["id"] for w in waterways}
    children = {w["id"]: [] for w in waterways}
    roots = []
    for w in waterways:
        parent = None
        for t in w["tributaries"]:
            pass
        roots.append(w["id"])
    # 由「谁的支流列表里有我」定父（首次出现者优先）
    for w in waterways:
        for host in waterways:
            if host["id"] == w["id"]:
                continue
            for t in host["tributaries"]:
                if t["kind"] == "in" and (t["name"] == w["name"] or t["name"].endswith(w["name"]) or w["name"].endswith(t["name"])):
                    if len(t["name"]) >= 2:
                        children[host["id"]].append(w["id"])
                        w["parent"] = host["name"]
                        break
            if "parent" in w:
                break
    for w in waterways:
        if "parent" not in w:
            roots.append(w["id"])
        else:
            if w["id"] in roots:
                roots.remove(w["id"])

    tree_meta = {"roots": roots, "children": {k: v for k, v in children.items() if v}}

    meta = {
        "title": "水经注", "author": "郦道元", "vols": 40,
        "sections": len(rivers), "waterways": len(waterways),
        "waypointNames": len({w["name"] for w in waterways for w in w["waypoints"]}),
        "wpTotal": wp_total, "wpResolved": wp_resolved,
        "coverage": round(wp_resolved / max(wp_total, 1) * 100, 1),
        "citationKinds": len(citations["counts"]),
    }

    out = {"meta": meta, "tree": tree_meta, "waterways": waterways}
    with open(os.path.join(DATA, "river_data.js"), "w", encoding="utf-8") as f:
        f.write("/* 水道经纬 · 水道结构数据 · build_river_data.py 生成，勿手改 */\n")
        f.write("const SJZ = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")

    # ── sections.js（循水阅读：经文锚 + 其后注文段）──
    secs = {}
    for r in rivers:
        if r["type"] != "water":
            continue
        body = []
        for i, j in enumerate(r["jing"]):
            blk = [b["text"] for b in r["blocks"] if b["after"] == i]
            body.append({"j": j["text"], "z": blk})
        tail = [b["text"] for b in r["blocks"] if b["after"] == -1]
        if tail:
            body.insert(0, {"j": "", "z": tail})
        secs[r["id"]] = {"name": r["name"], "vol": int(r["vol"]), "body": body}
    with open(os.path.join(DATA, "sections.js"), "w", encoding="utf-8") as f:
        f.write("/* 水道经纬 · 循水阅读文本 · build_river_data.py 生成 */\n")
        f.write("const SJZ_SECTIONS = " + json.dumps(secs, ensure_ascii=False, separators=(",", ":")) + ";\n")

    # ── citations.js ──
    with open(os.path.join(DATA, "citations.js"), "w", encoding="utf-8") as f:
        f.write("/* 水道经纬 · 引书考古数据库 · build_river_data.py 生成 */\n")
        f.write("const SJZ_CITES = " + json.dumps(citations, ensure_ascii=False, separators=(",", ":")) + ";\n")

    # ── 全文懒加载（检索层，按卷）──
    os.makedirs(os.path.join(DATA, "text"), exist_ok=True)
    for vi in range(1, 41):
        txt = open(os.path.join(ROOT, "data", "vol", f"{vi:03d}.txt"), encoding="utf-8").read()
        with open(os.path.join(DATA, "text", f"j{vi:02d}.js"), "w", encoding="utf-8") as f:
            f.write(f'/* 水经注·卷{vi} · 懒加载 */\n')
            f.write(f'(window.SJZTEXT=window.SJZTEXT||{{}})[{vi}]=' +
                    json.dumps(txt, ensure_ascii=False) + ';\n')

    report = {"meta": meta, "top_by_chars": [
        {"name": w["name"], "chars": w["stats"]["chars"], "vols": w["vols"],
         "wps": len([x for x in w["waypoints"] if "pos" in x])}
        for w in sorted(waterways, key=lambda x: -x["stats"]["chars"])[:30]]}
    with open(os.path.join(DATA, "build_report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)

    print(f"水道 {len(waterways)} 条（合并跨卷）· 航点 {wp_total} · 解析 {wp_resolved} · 覆盖率 {meta['coverage']}%")
    print("字数前十：")
    for t in report["top_by_chars"][:10]:
        print(f"   {t['name']}: {t['chars']} 字 · {t['wps']} 航点 · {'/'.join(t['vols'])}")


if __name__ == "__main__":
    main()
