# -*- coding: utf-8 -*-
"""水道经纬 · 《洛阳伽蓝记》互查数据构建（伽蓝经纬站际桥回程，方案 5.2 双向闭环）
伽蓝站已建单向桥（伽蓝→水经，tools/build_xref_sjz.py → data/xref_sjz.js）；
本脚本从**水道视角**重组该快照（LYGL 只读，绝不写入）：
  · 每水道（谷水/洛水/阳渠）→ 命中的伽蓝记名物清单（城门/伽蓝/衙署·宫室/地标分组）
    + 每名物一句谷水注/洛水注样例 + ↗伽蓝经纬深链（构建期烘焙）
  · 10 对对读样例（伽蓝记句 × 郦注句，皆伽蓝站脚本截取）
  · 无对应注记（城门仅津阳门/承明门）与 A 侧提及计数、假阳性排除
深链格式（LYGL js/app.js applyHash 实测口径）：
  · 伽蓝 → ../LYGL/#juan=<卷>#gl=<寺名>    （巡读直接落到该寺）
  · 城门 → ../LYGL/#gate=<门名>
  · 其余（衙署/地标/里坊，无专属 hash）→ ../LYGL/#m=map
  · 寺名/门名在 LYGL QLZ 表中逐一验真，验不中退化为 #m=map 并打印
输出: data/xrev_ql.js —— window.SJZ_QL（js/crosspanel.js「引伽蓝记」页签懒加载）
"""
import io
import json
import os
import re
from urllib.parse import quote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LYGL = os.path.join(os.path.dirname(ROOT), "LYGL")   # D:/W_A_W/LYGL
SITE = "../LYGL/"

KIND_ORDER = ["城门", "伽蓝", "衙署·宫室", "地标"]


def load_js_const(path, head):
    """从 LYGL 数据文件中抠出 JS 对象字面量（window.X = / const X = 两种头）。"""
    t = io.open(path, encoding="utf-8").read()
    i = t.find(head)
    assert i >= 0, f"{os.path.basename(path)} 缺 {head!r}"
    return json.loads(t[i + len(head):].rstrip().rstrip(";"))


def deep_link(kind, name, qlz, log):
    """按 LYGL applyHash 语法烘焙深链；名物须在 QLZ 表验真，验不中退化为 #m=map。"""
    if kind == "伽蓝":
        t = next((x for x in qlz["temples"] if x["name"] == name), None)
        if t:
            return f"{SITE}#juan={t['vol']}#gl={quote(name)}"
    if kind == "城门":
        g = next((x for x in qlz["gates"] if x["name"] == name), None)
        if g:
            return f"{SITE}#gate={quote(name)}"
    log.append(f"{kind}·{name} 无专属深链 → #m=map")
    return f"{SITE}#m=map"


def main():
    xref_path = os.path.join(LYGL, "data", "xref_sjz.js")
    site_path = os.path.join(LYGL, "data", "site_data.js")
    if not os.path.exists(xref_path):
        raise SystemExit("未找到伽蓝站 data/xref_sjz.js（互查桥需要其快照，只读）")
    d = load_js_const(xref_path, "window.QL_SJZ = ")
    qlz = load_js_const(site_path, "const QLZ = ")
    log = []

    # A 侧原样口径（提及计数/排除在伽蓝站判好，此处只转述）
    a_waters = [{"name": w["name"], "n": w["n"], "sjzId": w["sjzId"],
                 "note": w.get("note", "")} for w in d["waters"]]
    a_excluded = [{"name": e["name"], "n": e["n"], "why": e["why"]}
                  for e in d["excluded"]]

    # ── 水道视角重组：每水道 → 分组名物清单 ──
    zhu_chars = d["totals"]["waterTextChars"]
    a_by_name = {w["name"]: w for w in d["waters"]}
    waters_out = []
    for wdisp in ["谷水", "洛水", "阳渠"]:
        a = a_by_name.get(wdisp, {})
        entry = {
            "name": wdisp,
            "sjzId": a.get("sjzId", ""),
            "zhuChars": zhu_chars.get(wdisp, 0),
            "qlMentions": a.get("n", 0),
            "qlNote": a.get("note", ""),
            "kinds": [],
        }
        if wdisp == "阳渠":
            # 阳渠无独立分节（行于谷水注内）——名物命中并入谷水，如实注记
            entry["note"] = ("水经注不另立阳渠卷——渠行谷水注内，名物命中并入谷水；"
                             "伽蓝记提及 4 次（卷二「东入阳渠石桥」等语境）")
            waters_out.append(entry)
            continue
        groups = {k: [] for k in KIND_ORDER}
        for p in d["places"]:
            n = (p.get("perWater") or {}).get(wdisp, 0)
            if not n:
                continue
            kinds = p["kind"].split("/")
            k = next((kk for kk in KIND_ORDER if kk in kinds), kinds[0])
            groups.setdefault(k, []).append({
                "name": p["name"], "n": n, "sample": p["sample"],
                "href": deep_link(k, p["name"], qlz, log),
                "note": p.get("note", ""),
            })
        for k in KIND_ORDER:
            if groups.get(k):
                groups[k].sort(key=lambda x: (-x["n"], x["name"]))
                entry["kinds"].append({"kind": k, "items": groups[k]})
        entry["hitNames"] = sum(len(g["items"]) for g in entry["kinds"])
        entry["hitN"] = sum(x["n"] for g in entry["kinds"] for x in g["items"])
        waters_out.append(entry)

    # ── 对读样例：伽蓝站截好的 10 对，补 ↗伽蓝深链 ──
    pairs = []
    for p in d["pairs"]:
        pairs.append({
            "name": p["name"], "kind": p["kind"], "water": p["water"],
            "waterId": p["href"].split("#r=")[-1],   # 回程循水（站内 #r=<id>）
            "ql": p["ql"], "sjz": p["sjz"],
            "qlHref": deep_link(p["kind"], p["name"], qlz, log),
        })

    t = d["totals"]
    out = {
        "site": SITE,
        "generated": "tools/build_xrev_ql.py（LYGL 只读——不写入伽蓝站）",
        "note": "郦道元谷水注（卷十六）正是北魏洛阳城的笔墨所聚，杨衒之武定重游（547）成《洛阳伽蓝记》"
                "——两书同城异代。名物判定出自伽蓝经纬站快照（xref_sjz.js），本站构建期按水道视角重组；"
                "深链为相对兄弟路径，须父目录同根服务（README 注明）。",
        "waters": waters_out,
        "pairs": pairs,
        "aSide": {"total": t["waterMentions"], "waters": a_waters,
                  "excluded": a_excluded},
        "noHit": {"total": t["placesNoHit"], "byKind": t["noHitByKind"],
                  "gates": [n["name"] for n in d["noHit"] if n["kind"] == "城门"]},
        "totals": {
            "waters": len(waters_out),
            "placeHits": t["placesHit"],
            "placeByKind": t["placeKinds"],
            "pairs": len(pairs),
            "aMentions": t["waterMentions"],
            "zhuChars": zhu_chars,
        },
    }
    path = os.path.join(ROOT, "data", "xrev_ql.js")
    with io.open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("/* 水道经纬 · 引伽蓝记互查数据 · tools/build_xrev_ql.py 生成，勿手改 */\n")
        f.write("window.SJZ_QL = " + json.dumps(out, ensure_ascii=False,
                                               separators=(",", ":")) + ";\n")

    print("✓ data/xrev_ql.js")
    for w in waters_out:
        if w["name"] == "阳渠":
            print(f"  阳渠: 无独立分节（伽蓝记提及 {w['qlMentions']} 次，名物并入谷水）")
        else:
            ks = " · ".join(f"{g['kind']} {len(g['items'])}" for g in w["kinds"])
            print(f"  {w['name']}注 {w['zhuChars']:,} 字 → 命中 {w['hitNames']} 名物 {w['hitN']} 次（{ks}）")
    print(f"  对读样例 {len(pairs)} 对 · A 侧伽蓝记提及水道 {t['waterMentions']} 次 · "
          f"无对应 {t['placesNoHit']}（城门 {'、'.join(out['noHit']['gates'])}）")
    for ln in sorted(set(log)):
        print("  深链退化：", ln)


if __name__ == "__main__":
    main()
