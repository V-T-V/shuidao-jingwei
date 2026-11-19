"""水道经纬 · lint（确定性检查，失败即红）
用法: python tools/lint.py
类别（承方舆经纬 lint 哲学——文字指令与 lint 冲突时 lint 是对的）：
  1  版本一致性   index.html/sw.js/js 的 ?v= 全等于 sw.js VERSION
  2  资源存在性   index.html 引用的 script/css 存在；sw SHELL_FILES 全部存在
  3  数据哨兵     水道≥100 · 航点≥500 · 覆盖≥60% · 引书≥350 · 河水注字>15000 · 经文 7000±1200
  4  折线连续性   自交叉总数 ≤ 4（基线：济水二吸收泗水首段 3 + 淇水 1，不得新增）
  5  禁用模式     map.fire("click") / innerHTML.indexOf 验证 / window._ftw / git mv -q / || true
  6  Worker 纯净  ftworker.js 不引用 document/window
  7  深链一致     app.js 的 hash 语法与文档一致（#w/#r/#c/#m）
  8  manifest     icons 三枚存在，manifest 引用一致
"""
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
fails, checks = [], 0


def ok(cond, msg):
    global checks
    checks += 1
    if not cond:
        fails.append(msg)


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def main():
    # ── 1 版本一致性 ──
    sw = read("sw.js")
    mver = re.search(r'VERSION = "v(\d+)"', sw)
    ok(mver, "sw.js 缺 VERSION 常量")
    ver = mver.group(1) if mver else ""
    for f in ["index.html", "sw.js"] + ["js/" + x for x in os.listdir(os.path.join(ROOT, "js")) if x.endswith(".js")]:
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        t = open(p, encoding="utf-8").read()
        for bad in set(re.findall(r"\?v=(\d+)", t)):
            ok(bad == ver, f"{f} 含过期版本 ?v={bad}（当前 v{ver}）——请跑 tools/bump_version.py")

    # ── 2 资源存在性 ──
    idx = read("index.html")
    for src in re.findall(r'(?:src|href)="([^"#?]+)(?:\?[^"]*)?"', idx):
        if src.startswith(("http", "data:")):
            continue
        ok(os.path.exists(os.path.join(ROOT, src)), f"index.html 引用缺失: {src}")
    for m2 in re.finditer(r'"(\./[^"]+?)(?:\?[^"]*)?"', sw):
        rel = m2.group(1)[2:]
        ok(os.path.exists(os.path.join(ROOT, rel)), f"sw SHELL_FILES 缺失: {rel}")

    # ── 3 数据哨兵 ──
    riv = json.load(open(os.path.join(ROOT, "data/intermediate/rivers.json"), encoding="utf-8"))
    meta = riv["meta"]
    ok(meta["water_sections"] >= 100, f"水道分节 {meta['water_sections']} < 100")
    ok(meta["total_waypoints"] >= 500, f"航点 {meta['total_waypoints']} < 500")
    ok(6500 <= meta["jing_chars"] <= 8200, f"经文字数 {meta['jing_chars']} 越界 7000±1200")
    ok(len(json.load(open(os.path.join(ROOT, "data/intermediate/citations.json"), encoding="utf-8"))["counts"]) >= 350,
       "引书种类 < 350")
    t = read("data/river_data.js")
    sjz = json.loads(t[t.find("const SJZ = ") + len("const SJZ = "):].rstrip().rstrip(";"))
    ok(sjz["meta"]["coverage"] >= 60, f"航点覆盖率 {sjz['meta']['coverage']}% < 60%")
    heshui = next(w for w in sjz["waterways"] if w["name"] == "河水")
    ok(heshui["stats"]["zhuChars"] > 15000, f"河水注文字 {heshui['stats']['zhuChars']} ≤ 15000")

    # ── 4 折线连续性 ──
    CROSS_BASELINE = 4
    ok(sjz["meta"]["crossings"] <= CROSS_BASELINE,
       f"折线自交叉 {sjz['meta']['crossings']} > 基线 {CROSS_BASELINE}")

    # ── 5 禁用模式 ──
    banned = [
        (r'map\.fire\(\s*["\']click', "map.fire(click) 委托分发不可靠——用 canvas.dispatchEvent"),
        (r'innerHTML\.indexOf\(', "innerHTML.indexOf 验证会因 & 序列化失效——用 textContent"),
        (r'window\._ftw', "闭包 let 量不在 window 上——用存取函数"),
        (r'git mv -q', "git mv 无 -q flag"),
        (r'\|\|\s*true', "|| true 兜底吞错（教训 20）"),
    ]
    jss = ["js/" + x for x in os.listdir(os.path.join(ROOT, "js")) if x.endswith(".js")]
    for f in jss:
        t = open(os.path.join(ROOT, f), encoding="utf-8").read()
        for pat, why in banned:
            ok(not re.search(pat, t), f"{f} 触禁：{why}")

    # ── 6 Worker 纯净 ──
    w = read("js/ftworker.js")
    ok("document" not in w and "window" not in w, "ftworker.js 引用 DOM（Worker 无 DOM）")

    # ── 7 深链一致 ──
    app = read("js/app.js")
    for frag in ["#w=", "#r=", "#c=", "#m="]:
        ok(frag in app or frag.replace("#", "") in app, f"app.js 深链语法缺 {frag}")

    # ── 8 manifest ──
    mani = read("manifest.json")
    for icon in re.findall(r'"src":\s*"(icons/[^"]+)"', mani):
        ok(os.path.exists(os.path.join(ROOT, icon)), f"manifest 引用图标缺失: {icon}")

    # ── 9 3D 页引用一致（index 底栏入口 ↔ 3d.html 存在；版本同流） ──
    ok(os.path.exists(os.path.join(ROOT, "3d.html")), "3d.html 缺失（index 底栏形胜入口指向它）")
    d3 = read("3d.html") if os.path.exists(os.path.join(ROOT, "3d.html")) else ""
    ok("tdlink" in idx, "index.html 缺 3D 入口（#tdlink）")
    for bad in set(re.findall(r"\?v=(\d+)", d3)):
        ok(bad == ver, f"3d.html 含过期版本 ?v={bad}（当前 v{ver}）")

    # ── 10 论文哨兵：改 ANALYSIS.md / 管线产物后必须重排 PDF ──
    ap = os.path.join(ROOT, "docs", "ANALYSIS.md")
    pdf = os.path.join(ROOT, "docs", "水道经纬-水道网络与引书考古.pdf")
    if os.path.exists(ap) and os.path.exists(pdf):
        ok(os.path.getmtime(pdf) >= os.path.getmtime(ap),
           "docs/ANALYSIS.md 晚于论文 PDF——请重跑 python tools/build_paper_pdf.py")

    # ── 报告 ──
    print(f"lint：{checks} 项检查")
    if fails:
        print(f"✗ {len(fails)} 项失败：")
        for f in fails:
            print("  -", f)
        sys.exit(1)
    print("✓ 全绿")


if __name__ == "__main__":
    main()
