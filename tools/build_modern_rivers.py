"""水道经纬 · Natural Earth 真实河线提取 → data/modern_rivers.js
从 data_raw/ne_rivers.geojson（10m rivers lake centerlines）提取中国主要河流
现代轨迹（真实河线替代手工近似），简化至 ≤140 点/条。
输出: data/modern_rivers.js —— const SJZ_MODERN = [{key, linkTo, color, pts}]
前置: ne 文件由 jsdelivr/raw 下载（网络不稳时脚本给出明确指引）。
"""
import io
import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NE = os.path.join(ROOT, "data_raw", "ne_rivers.geojson")

# 目标河流：key, linkTo(水经注水名), 色, 匹配词（50m 命名为短名：Huang/Han/Gan…）, 中国 bbox
# 注：淮/渭/湘/钱塘/汾等 50m 未收——由 js/config.js 手绘线兜底（map.js 按 linkTo 合并）
TARGETS = [
    ("黄河", "河水", "#c96f4a", ["Huang"], (95, 119, 32, 42)),
    ("长江", "江水", "#4a7a9b", ["Yangtze", "Chang Jiang"], (90, 122, 24, 36)),
    ("汉水", "沔水", "#3d7a72", ["Han"], (104, 115, 30, 34)),
    ("赣江", "赣水", "#3d7a72", ["Gan"], (113, 117, 24, 30)),
    ("西江", "〈氵买〉水", "#44719b", ["Xi"], (104, 117, 21, 26)),
]


def in_box(lon, lat, box):
    x0, x1, y0, y1 = box
    return x0 <= lon <= x1 and y0 <= lat <= y1


def simplify(pts, cap=140):
    """等距抽稀至 ≤cap 点（保首尾）"""
    if len(pts) <= cap:
        return pts
    step = (len(pts) - 1) / (cap - 1)
    return [pts[round(i * step)] for i in range(cap)]


def stitch(frags):
    """碎片河段 → 单条连续折线：取最长段为骨干，按端点最近贪婪延伸（两端均可接）。"""
    if not frags:
        return []
    frags = [list(f) for f in frags]
    frags.sort(key=len, reverse=True)
    line = frags.pop(0)
    used = True
    while used and frags:
        used = False
        for i, f in enumerate(frags):
            if not f:
                continue
            def d(a, b):
                return (a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
            if d(line[-1], f[0]) < 1e-4:
                line += f[1:]
            elif d(line[-1], f[-1]) < 1e-4:
                line += f[::-1][1:]
            elif d(line[0], f[-1]) < 1e-4:
                line = f[:-1] + line
            elif d(line[0], f[0]) < 1e-4:
                line = f[1:][::-1] + line
            else:
                continue
            frags.pop(i)
            used = True
            break
    return line


def main():
    if not os.path.exists(NE):
        raise SystemExit("缺 data_raw/ne_rivers.geojson——请先下载（jsdelivr/raw 均可），见 README")
    d = json.load(io.open(NE, encoding="utf-8"))
    out = []
    for key, link_to, color, keys, box in TARGETS:
        frags = []
        for f in d["features"]:
            p = f.get("properties") or {}
            hay = " ".join(str(p.get(k) or "") for k in ("name", "name_en", "name_alt"))
            if not any(k in hay for k in keys):
                continue
            g = f.get("geometry") or {}
            coords = g.get("coordinates") or []
            if g.get("type") == "MultiLineString":
                coords = max(coords, key=len)
            pts = [(round(c[1], 3), round(c[0], 3)) for c in coords if in_box(c[0], c[1], box)]
            if len(pts) >= 2:
                frags.append(pts)
        line = stitch(frags)
        if len(line) >= 8:
            out.append({"key": key, "linkTo": link_to, "color": color,
                        "pts": simplify(line), "src": "Natural Earth 50m"})
            print(f"  {key}: {len(frags)} 段缝合 {len(line)} 点（{link_to}）")
        else:
            print(f"  {key}: 未匹配（≥8 点方收）")
    with io.open(os.path.join(ROOT, "data", "modern_rivers.js"), "w", encoding="utf-8") as f:
        f.write("/* 水道经纬 · 今水参照线（Natural Earth 50m 真实河线缝合）· build_modern_rivers.py 生成 */\n")
        f.write("const SJZ_MODERN = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"合计 {len(out)} 条 → data/modern_rivers.js")


if __name__ == "__main__":
    main()
