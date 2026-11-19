"""水道经纬 · 互文数据构建（方舆经纬快照，方案 5.2「嵌入对方数据快照」）
扫描《读史方舆纪要》全文（HHH data/text/*.js），定位全部《水经注》引用：
  - 每省引用次数 → provinces 排行
  - 引用语境 ±160 字内出现的《水经注》水名 → waterMentions（顾祖禹引此水 N 次）
输出: data/crossref.js（const SJZ_XREF = {...}）
"""
import io
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FY_TEXT = r"D:/W_A_W/HHH/data/text"

PROV = {
    "beizhi": "北直隶", "nanzhi": "南直隶", "shandong": "山东", "shanxi": "山西",
    "henan": "河南", "shanxix": "陕西", "sichuan": "四川", "huguang": "湖广",
    "jiangxi": "江西", "zhejiang": "浙江", "fujian": "福建", "guangdong": "广东",
    "guangxi": "广西", "yunnan": "云南", "guizhou": "贵州",
    "chuandu": "川渎", "xingshi": "形势", "juanshou": "卷首",
}


def main():
    # 本站水道名（112 条，长名优先匹配）
    rivers = json.load(io.open(os.path.join(ROOT, "data", "intermediate", "rivers.json"), encoding="utf-8"))
    names = sorted({r["name"] for r in rivers["rivers"] if r["type"] == "water"}, key=len, reverse=True)

    total = 0
    prov_counts = {}
    water_mentions = {}
    samples = []
    for fn in sorted(os.listdir(FY_TEXT)):
        if not fn.endswith(".js"):
            continue
        pid = fn[:-3]
        raw = io.open(os.path.join(FY_TEXT, fn), encoding="utf-8").read()
        # 取全部字符串字面量拼接（键名为拼音/卷次，不构成水名噪声）
        text = "".join(re.findall(r'"((?:[^"\\]|\\.)*)"', raw))
        n = text.count("《水经注》")
        if not n:
            continue
        total += n
        prov_counts[PROV.get(pid, pid)] = prov_counts.get(PROV.get(pid, pid), 0) + n
        # 引用语境
        for m in re.finditer("《水经注》", text):
            ctx = text[max(0, m.start() - 160):m.start() + 180]
            if len(samples) < 24:
                samples.append({"prov": PROV.get(pid, pid), "ctx": ctx.replace("\n", "")[:240]})
            for nm in names:
                if nm in ctx:
                    water_mentions[nm] = water_mentions.get(nm, 0) + 1
                    break   # 长名优先，一境计一次

    out = {
        "source": "方舆经纬（读史方舆纪要）全语料快照",
        "total": total,
        "provinces": sorted(prov_counts.items(), key=lambda kv: -kv[1]),
        "waterMentions": water_mentions,
        "samples": samples,
    }
    with io.open(os.path.join(ROOT, "data", "crossref.js"), "w", encoding="utf-8") as f:
        f.write("/* 水道经纬 · 互文快照（方舆经纬《读史方舆纪要》引《水经注》）· build_crossref.py 生成 */\n")
        f.write("const SJZ_XREF = " + json.dumps(out, ensure_ascii=False, separators=(",", ":")) + ";\n")
    print(f"《水经注》被引总次：{total}")
    print("省分布前八：", out["provinces"][:8])
    print("常并提水名前十二：", sorted(water_mentions.items(), key=lambda kv: -kv[1])[:12])


if __name__ == "__main__":
    main()
