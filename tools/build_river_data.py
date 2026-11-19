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


def seg_int(p1, p2, p3, p4):
    """两线段真相交（含参数边界收缩，排除共端点）"""
    d1x, d1y = p2[0] - p1[0], p2[1] - p1[1]
    d2x, d2y = p4[0] - p3[0], p4[1] - p3[1]
    den = d1x * d2y - d1y * d2x
    if abs(den) < 1e-12:
        return False
    t1 = ((p3[0] - p1[0]) * d2y - (p3[1] - p1[1]) * d2x) / den
    t2 = ((p3[0] - p1[0]) * d1y - (p3[1] - p1[1]) * d1x) / den
    return 0.001 < t1 < 0.999 and 0.001 < t2 < 0.999


MYTHIC_SOURCES = {"昆仑", "积石"}   # 河水卷一神话地理：作源标不入折线


def count_cross(path):
    n = 0
    for i in range(len(path) - 1):
        for j in range(i + 2, len(path) - 1):
            if seg_int(path[i], path[i + 1], path[j], path[j + 1]):
                n += 1
    return n


def uncross(path, wps):
    """两段治理：
    1) 方位偏移试探：逐点加偏移，若与近邻段（±3）相交则放弃该偏移；
    2) 2-opt 反折：交叉段 i/j 之间逆序，仅当不新增交叉且路径长度增幅 <30%。"""
    n = len(path)
    # 偏移试探
    for i, wp in enumerate(wps):
        if not wp.get("off"):
            continue
        old = path[i]
        path[i] = wp["off"]
        bad = False
        for a in range(max(0, i - 3), min(n - 1, i + 3)):
            for b in range(a + 2, min(n - 1, i + 4)):
                if seg_int(path[a], path[a + 1], path[b], path[b + 1]):
                    bad = True
                    break
            if bad:
                break
        if bad:
            path[i] = old
    # 2-opt 反折（最多 6 轮；wps 与 path 同步反序）
    def path_len(p):
        return sum(dist_km(p[k], p[k + 1]) for k in range(len(p) - 1))
    for _ in range(6):
        did = False
        base_cross = count_cross(path)
        if base_cross == 0:
            break
        for i in range(len(path) - 1):
            for j in range(i + 2, len(path) - 1):
                if not seg_int(path[i], path[i + 1], path[j], path[j + 1]):
                    continue
                cand = path[:i + 1] + path[i + 1:j + 1][::-1] + path[j + 1:]
                if count_cross(cand) < base_cross and path_len(cand) < path_len(path) * 1.3:
                    path = cand
                    wps[:] = wps[:i + 1] + wps[i + 1:j + 1][::-1] + wps[j + 1:]
                    did = True
                    break
            if did:
                break
        if not did:
            break
    return path


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
    total_cross = 0
    for m in merged:
        path, waypoints = [], []
        jumps = 0
        anchor_base = 0   # 跨卷合并时 jingIdx 平移为全局锚序
        for sec in m["sections"]:
            for w in sec["waypoints"]:
                wp_total += 1
                rr = resolve(w["name"], coords)
                wp = {"name": w["name"], "kind": w["kind"], "side": w.get("side", ""),
                      "jingIdx": w["jing_idx"] + anchor_base, "vol": int(sec["vol"])}
                if w.get("source"):
                    wp["source"] = True
                if rr:
                    wp_resolved += 1
                    base = [rr[0], rr[1]]
                    wp["pos"] = [round(base[0], 4), round(base[1], 4)]
                    if w.get("side"):
                        wp["off"] = offset_side(base[0], base[1], w.get("side", ""))
                    wp["near"] = rr[2]
                    if w["name"] in MYTHIC_SOURCES:
                        wp["mythic"] = True     # 神话地理：源标不入折线
                    else:
                        path.append(wp["pos"])
                waypoints.append(wp)
            anchor_base += len(sec["jing"])
        # 反交叉（试探偏移）+ 跳段检测（终版折线上）
        pos_wps = [wp for wp in waypoints if "pos" in wp and not wp.get("mythic")]
        path = uncross(path, pos_wps)
        jumps = 0
        for k in range(1, len(path)):
            if dist_km(path[k - 1], path[k]) > 200:
                pos_wps[k]["jump"] = True
                jumps += 1
        for wp in waypoints:
            wp.pop("off", None)
        n_cross = 0
        for i in range(len(path) - 1):
            for j in range(i + 2, len(path) - 1):
                if seg_int(path[i], path[i + 1], path[j], path[j + 1]):
                    n_cross += 1
        total_cross += n_cross
        # 支流（去重保序；jingIdx 同步平移）
        tribs, seen = [], set()
        anchor_base = 0
        for sec in m["sections"]:
            for t in sec["tributaries"]:
                key = t["name"] + t["kind"]
                if key in seen:
                    continue
                seen.add(key)
                tribs.append({"name": t["name"], "kind": t["kind"],
                              "dir": t.get("dir", ""), "src": t.get("src", "jing"),
                              "jingIdx": t.get("jing_idx", -1) + anchor_base})
            anchor_base += len(sec["jing"])
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
            "crossings": n_cross,
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
        "crossings": total_cross,
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
            # 篇前注文挂到首锚（保持锚序与 jingIdx 对齐）
            if body:
                body[0]["z"] = tail + body[0]["z"]
            else:
                body.append({"j": "（篇前）", "z": tail})
        secs[r["id"]] = {"name": r["name"], "vol": int(r["vol"]), "body": body}
    with open(os.path.join(DATA, "sections.js"), "w", encoding="utf-8") as f:
        f.write("/* 水道经纬 · 循水阅读文本 · build_river_data.py 生成 */\n")
        f.write("const SJZ_SECTIONS = " + json.dumps(secs, ensure_ascii=False, separators=(",", ":")) + ";\n")

    # ── citations.js（计数+分布，随壳常载）· cites_quotes.js（引文全文，面板懒加载）──
    with open(os.path.join(DATA, "citations.js"), "w", encoding="utf-8") as f:
        f.write("/* 水道经纬 · 引书考古数据库 · build_river_data.py 生成 */\n")
        f.write("const SJZ_CITES = " + json.dumps(
            {"counts": citations["counts"], "where": citations["where"]},
            ensure_ascii=False, separators=(",", ":")) + ";\n")
    quotes = citations.get("quotes", {})
    with open(os.path.join(DATA, "cites_quotes.js"), "w", encoding="utf-8") as f:
        f.write("/* 水道经纬 · 引文辑录全文（懒加载）· build_river_data.py 生成 */\n")
        f.write("window.SJZ_QUOTES = " + json.dumps(quotes, ensure_ascii=False, separators=(",", ":")) + ";\n")

    # ── inventory.js（水名录 · 懒加载）：名 → 次数/首见/类别（分节|支流|仅见）──
    inv = json.load(open(os.path.join(INT, "inventory.json"), encoding="utf-8"))
    section_names = {r["name"] for r in rivers if r["type"] == "water"}
    trib_names = {t["name"] for r in rivers for t in r["tributaries"]}
    inv_out = {}
    for name, n in inv["counts"].items():
        if n < 2 or len(name) < 2:
            continue
        kind = "分节" if name in section_names else ("支流" if name in trib_names else "仅见")
        fs = inv["first_seen"].get(name, "")
        if isinstance(fs, dict):
            first, fq = fs.get("loc", ""), fs.get("q", "")
        else:
            first, fq = fs, ""
        inv_out[name] = {"n": n, "first": first, "q": fq, "kind": kind}
    with open(os.path.join(DATA, "inventory.js"), "w", encoding="utf-8") as f:
        f.write("/* 水道经纬 · 水名录全书清单（懒加载）· build_river_data.py 生成 */\n")
        f.write("window.SJZ_INV = " + json.dumps(inv_out, ensure_ascii=False, separators=(",", ":")) + ";\n")

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
