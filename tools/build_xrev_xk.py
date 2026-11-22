# -*- coding: utf-8 -*-
"""水道经纬 · 引霞客互查数据构建（霞客经纬站际桥回程；XXK 只读，绝不写入）
霞客桥（XXK data/xref_sjz.js）反转重组为水道视角 + 经行判定：
  · 提及数/样例句取自霞客桥快照（同口径，不重扫语料）
  · 经行判定：XXK 全部锚点（trips.json，只读）× 本站水道折线（SJZ.waterways.path）
    点到折线最短距离 ≤30km 即「霞客经行」，记最近锚点（程/日/地名）与距离；
    判不了的（无折线/无锚）只计提及——如实分栏
  · 对读特辑三对（岷山/禹贡/导江）随桥携带
输出: data/xrev_xk.js —— window.SJZ_XK（js/crosspanel.js「引霞客」页签懒加载）
深链: ../XXK/#trip=<tid>&d=<day>（相对兄弟路径——父目录同根服务约定）
"""
import io
import json
import math
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
XXK = os.path.join(os.path.dirname(ROOT), "XXK")   # 只读
SITE = "../XXK/"
VISIT_KM = 30.0


def load_const(path, const):
    """const X = / window.X = 两种载体皆认（本站 const、霞客站 window）"""
    t = io.open(path, encoding="utf-8").read()
    for head in (f"const {const} = ", f"window.{const} = "):
        i = t.find(head)
        if i >= 0:
            return json.loads(t[i + len(head):].rstrip().rstrip(";"))
    raise AssertionError(f"{path} 缺 {const}")


def hav_km(a, b):
    la1, lo1, la2, lo2 = map(math.radians, [a[0], a[1], b[0], b[1]])
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(h))


def pt_seg_km(p, a, b):
    """点到线段近似距离（局部平面投影，水道尺度足够）"""
    kx, ky = 111.32, 111.32 * math.cos(math.radians((a[0] + b[0] + p[0]) / 3))
    px, py = p[1] * kx, p[0] * ky
    ax, ay = a[1] * kx, a[0] * ky
    bx, by = b[1] * kx, b[0] * ky
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    qx, qy = ax + t * dx, ay + t * dy
    return math.hypot(px - qx, py - qy)


def pt_path_km(p, path):
    if len(path) < 2:
        return hav_km(p, path[0]) if path else 9e9
    return min(pt_seg_km(p, path[i], path[i + 1]) for i in range(len(path) - 1))


def main():
    if not os.path.isdir(XXK):
        raise SystemExit("未找到姊妹站 D:/W_A_W/XXK（互查桥需要其数据，只读）")
    sjz = load_const(os.path.join(ROOT, "data", "river_data.js"), "SJZ")
    by_id = {w["id"]: w for w in sjz["waterways"]}

    bridge = load_const(os.path.join(XXK, "data", "xref_sjz.js"), "XXK_SJZ")
    trips = json.load(io.open(os.path.join(XXK, "data", "intermediate", "trips.json"),
                              encoding="utf-8"))
    anchors = []                      # (tripId, dayIdx, title, placeName, pos)
    for t in trips["trips"]:
        for i, d in enumerate(t["days"]):
            if d["anchor"]:
                anchors.append((t["id"], i, t["title"], d["anchor"]["name"], d["anchor"]["pos"]))

    waters_out, n_visited = [], 0
    for w in bridge["waters"]:
        sjw = by_id.get(w["sjzId"])
        best = None
        if sjw and sjw.get("path"):
            for tid, di, title, place, pos in anchors:
                km = pt_path_km(pos, sjw["path"])
                if best is None or km < best["km"]:
                    best = {"km": round(km, 1), "trip": tid, "day": di,
                            "title": title, "place": place}
        visited = bool(best and best["km"] <= VISIT_KM)
        if visited:
            n_visited += 1
            best["href"] = f"{SITE}#trip={best['trip']}&d={best['day']}"
        near_note = ""
        if not visited and best and best["km"] < 120:
            near_note = (f"霞客锚点距本折线最近 {best['km']}km（{best['place']}）——"
                         "郦注江水折线走彭蠡北线，与霞客所经浔阳今道异线，如实不计经行")
        waters_out.append({
            "name": w["name"], "sjzId": w["sjzId"], "vols": w["vols"],
            "xkMentions": w["n"], "forms": w["forms"], "note": w["note"],
            "visited": visited,
            "visit": best if visited else None,
            "near": None if visited else best,          # 有最近点但超阈——如实展示距离
            "nearNote": near_note,
            "samples": w["samples"],
        })

    feature = bridge["feature"]
    for p in feature["pairs"]:
        p["xkHref"] = f"{SITE}#trip=t44&d=0"

    t = bridge["totals"]
    out = {
        "site": SITE,
        "generated": "tools/build_xrev_xk.py（XXK 只读——不写入霞客站）",
        "note": "郦道元（卒 527）注水经，徐霞客（1587-1641）行万里——"
                "霞客桥（xref_sjz.js）快照反转重组为水道视角；经行=霞客锚点距水道折线 "
                f"≤{VISIT_KM:.0f}km（脚本判定）。深链为相对兄弟路径，须父目录同根服务（README 注明）。",
        "xkMeta": {"pieces": trips["meta"]["pieces"], "days": trips["meta"]["days"],
                   "anchors": trips["meta"]["anchored"], "km": trips["meta"]["kmTotal"]},
        "totals": {"waters": t["watersMatched"], "mentions": t["waterMentions"],
                   "visited": n_visited, "noCorr": t["noCorr"], "pairs": t["pairs"]},
        "waters": waters_out,
        "feature": feature,
        "noCorrespondence": bridge["noCorrespondence"],
        "excluded": bridge["excluded"],
    }
    with io.open(os.path.join(ROOT, "data", "xrev_xk.js"), "w", encoding="utf-8", newline="\n") as f:
        f.write("/* 水道经纬 · 引霞客互查数据 · tools/build_xrev_xk.py 生成，勿手改（XXK 只读） */\n")
        f.write("window.SJZ_XK = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")

    tt = out["totals"]
    print(f"✓ data/xrev_xk.js")
    print(f"  水道 {tt['waters']} · 霞客提及 {tt['mentions']} 次 · "
          f"经行 {tt['visited']}（≤{VISIT_KM:.0f}km 判定） · 对读 {tt['pairs']} 对")
    for w in waters_out:
        v = "经行" if w["visited"] else (f"最近 {w['near']['km']}km" if w["near"] else "无折线")
        print(f"    {w['name']:<4} 提及 {w['xkMentions']:>3} · {v}")


if __name__ == "__main__":
    main()
