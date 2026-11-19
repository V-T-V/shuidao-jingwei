"""水道经纬 · Phase 1 结构解析
输入: data/vol/000.txt..040.txt
输出: data/intermediate/rivers.json      —— 水道分节（经注分离 + 航点 + 拓扑）
      data/intermediate/inventory.json  —— 全书水名清单（含水经注提及而未分节者）
      data/intermediate/citations.json  —— 引书考古数据库
方法: 设计方案 2.2 方法 A（规则法）：经文程式化句式 + 无引书/无曰/无迳 判别
"""
import json
import os
import re
from collections import Counter, OrderedDict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOL_DIR = os.path.join(ROOT, "data", "vol")
OUT_DIR = os.path.join(ROOT, "data", "intermediate")
os.makedirs(OUT_DIR, exist_ok=True)

DIRS = "东南西北"

# ── 经注分离（方法 A）──────────────────────────────────────────
RE_JING_START = re.compile(
    r"^(又?([东南西北]{1,2})?，?(过|至|当|入|出|迳)|屈从|^入于?|^[东南西北]{1,2}过|^出其)"
)
RE_WATER_SOURCE = re.compile(r"^([\u4e00-\u9fff〈〉]{1,4}水)出(.{1,24}?)(山|谷|陬|都|墟|泽|乡|县|郡)?[，。]")

def is_jing(line: str) -> bool:
    """经文判别：程式化句式 + 无引书/无曰/无迳 + 短句。"""
    s = line.strip()
    if not s:
        return False
    if "《" in s or "曰" in s or "迳" in s or "径" in s:
        return False
    if len(s) > 48:
        return False
    if RE_JING_START.match(s):
        return True
    if RE_WATER_SOURCE.match(s):
        return True
    if s.startswith(("昆仑墟", "去嵩高")):
        return True
    # 拓扑收尾句（支流汇入/分流/入海）独立成行者
    if s.endswith(("注之。", "入焉。", "出焉。", "注焉。", "入之。", "流注之。")) and len(s) <= 44:
        return True
    return False

# ── 航点/拓扑提取 ─────────────────────────────────────────────
# 过境: 又东过X县南 / 东至X郡西 / 又东南当X县北 / 西过其县南 / 过敦煌、酒泉、张掖郡南
RE_PASS = re.compile(
    r"(又)?([东南西北]{1,2})?[，]?(过|至|当)(其县|之)?"
    r"([\u4e00-\u9fff]{1,8}(?:、[\u4e00-\u9fff]{1,6})*?)(县|郡|城|邑|关|津|州|山|泽|墟|坂|阙)"
    r"(之?([东南西北]{1,2}))?"
)
# 支流: X水从东南来（流）注之 / 晋水从县南，东流注之 / 洧水注之 / X水入焉
RE_TRIB_AT = re.compile(
    r"([\u4e00-\u9fff〈〉]{1,4}水)(从|自)?(县)?([东南西北]{1,2})?(，[东南西北]{1,2}流)?(来流?|流)?(注之|注焉|入之|入焉)"
)
RE_TRIB_COMING = re.compile(r"([\u4e00-\u9fff〈〉]{1,4}水)从([东南西北]{1,2})来流?(注之|入之)")
# 分流: 蒗荡渠出焉 / 夏水出焉（从当前水道分出）
RE_OUTFLOW = re.compile(r"([\u4e00-\u9fff〈〉]{1,4}水|[\u4e00-\u9fff]{1,4}渠|[\u4e00-\u9fff]{1,4}河)出焉")
# 终点: 入于海 / 入渤海 / 入河 / 东入海 / 南入于江
RE_TERMINAL = re.compile(
    r"(又)?([东南西北]{1,2})?入于?(渤海|溟海|[海河江淮济漯渭洛汾漳沁淇洹濮汶泗沂沭])"
    r"|入于([\u4e00-\u9fff]{1,3}水)"
)
# 经文中的裸方位段（无地名的续行，如「屈从其东南流入渤海」）
RE_SIDE_TAIL = re.compile(r"(县|郡|城|邑)(之?)([东南西北]{1,2})?[，。]")

# 引书: 《书名》曰/云/称/以为/说 …（《书名》后接谓词或独立成引）
RE_CITE = re.compile(r"《([\u4e00-\u9fff·]{1,12})》(?=[曰云称说为言记])")
# 引文句捕获：《书》曰 + 后续句（至 。；，顿——取 ≤90 字符）
RE_CITE_QUOTE = re.compile(
    r"《([\u4e00-\u9fff·]{1,12})》[曰云称]([^\u3000\n]{6,90}?[。；])")
RE_CITE_ANY = re.compile(r"《([\u4e00-\u9fff·]{1,12})》")

WATER_NAME_RE = re.compile(r"([\u4e00-\u9fff]{1,3}(?:水|水|澞))|([\u4e00-\u9fff]{2,4}(?:河|江|溪|川))")

# 传说/水文词表（设计方案 4.2）
LEGEND_WORDS = ["相传", "昔", "黄帝", "禹", "神", "龙", "怪", "仙", "异", "俗说", "世语", "古老"]
HYDRO_WORDS = ["源", "流", "注", "决", "溢", "涸", "涨", "泝", "渡", "津", "堰", "堤", "渠", "灌", "渊", "潭", "浦"]
FLOW_VERBS = ["出", "过", "迳", "历", "经", "至", "入", "注", "合", "会", "决", "溢"]

# 注文支流：句首 X水 …… 句尾 注之/入焉（郦注标准叙事句：「湟水出…东南流…注之。」）
RE_ZHU_TRIB = re.compile(
    r"(?:^|[。；])\s*([\u4e00-\u9fff〈〉]{1,3}水)[^。；]{0,80}?(注之|注焉|入焉|入之)[。；]"
)

# 水名清单误收过滤：前接动词/指代/数词者非专名；整体为泛称者剔除
INV_PREV_EXCL = list("出入过流渡济泛汎沿顺下上至会合注得有其之于一二三四五六七八九以于自从及与为无涨滥涌潦盛涸溢决返还率被名曰云称")
INV_STOP = {"山水", "泉水", "大水", "洪水", "积水", "秋水", "之水", "其水", "一水", "二水", "三水",
            "有水", "得水", "出水", "入水", "过水", "流水", "下水", "上水", "中水", "引水", "通水",
            "汇水", "无水", "故水", "今水", "此水", "是水", "彼水", "众水", "诸水", "百水", "万水",
            "川水", "止水", "活水", "死水", "为水", "即水", "乃水"}


def split_water_names(text: str):
    """从头标记行提取水名序列（最短优先：「桓水若水」→[桓水,若水]；「延江水」→[延江水]）。"""
    names = []
    i = 0
    while i < len(text):
        c = text[i]
        if i + 1 < len(text) and text[i + 1] == "水":
            names.append(c + "水"); i += 2
        elif i + 2 < len(text) and text[i + 1] != "水" and text[i + 2] == "水":
            names.append(text[i:i + 3]); i += 3
        elif i + 3 < len(text) and text[i + 3] == "水" and "水" not in text[i:i + 3]:
            names.append(text[i:i + 4]); i += 4
        else:
            i += 1
    return [n for i, n in enumerate(names) if n not in names[:i]]


def split_sections(text: str):
    """按 ○ 分节；○ 前的卷首文本归入上一节或卷序言。
    复合头（卷36「青衣水 桓水若水…」/卷40「渐江水 斤江水」）按「X水出…」界拆子节。"""
    lines = text.split("\n")
    sections, cur, preamble = [], None, []
    for ln in lines:
        if ln.startswith("○"):
            if cur:
                sections.append(cur)
            cur = {"header": ln[1:].strip(), "lines": []}
        elif cur:
            cur["lines"].append(ln)
        else:
            preamble.append(ln)
    if cur:
        sections.append(cur)
    # 复合头子分节
    out = []
    for sec in sections:
        names = split_water_names(sec["header"])
        if len(names) <= 1:
            out.append(sec)
            continue
        joined = "\n".join(sec["lines"])
        cur_name, cur_lines, started = names[0], [], False
        for ln in sec["lines"]:
            m = re.match(r"^([\u4e00-\u9fff〈〉]{1,4}水)出", ln)
            is_new = False
            if m:
                nm = m.group(1)
                if nm in names and nm != cur_name and started:
                    is_new = True
                elif nm != cur_name and started and len(nm) >= 2 and re.search(re.escape(nm) + r"(又|东|南|西|北|迳|历)", joined):
                    is_new = True   # 头漏列而正文自成体系者（如侵离水）
            if is_new:
                out.append({"header": cur_name, "lines": cur_lines})
                cur_name, cur_lines = m.group(1), [ln]
            else:
                cur_lines.append(ln)
                started = True
        out.append({"header": cur_name, "lines": cur_lines})
    return out, preamble


def parse_waypoints(jing_text: str, ctx, water_name: str = ""):
    """从一行经文提取航点与拓扑事件。ctx 携带 last_county 等状态。
    支流句常跨逗号（「晋水从县南，东流注之」），故拓扑事件先整行匹配，航点再按子句匹配。"""
    events = []
    # ── 拓扑事件（整行匹配，可跨逗号）──
    for m in RE_TRIB_COMING.finditer(jing_text):
        if m.group(1) != water_name:
            events.append({"t": "trib", "name": m.group(1), "dir": m.group(2)})
    for m in RE_TRIB_AT.finditer(jing_text):
        if m.group(1) != water_name and not any(e["t"] == "trib" and e["name"] == m.group(1) for e in events):
            events.append({"t": "trib", "name": m.group(1), "dir": m.group(4) or ""})
    for m in RE_OUTFLOW.finditer(jing_text):
        if m.group(1) != water_name:
            events.append({"t": "outflow", "name": m.group(1)})
    # ── 源头句：X水出Y县Z山 → 源头航点 + 记县名 ──
    m = RE_WATER_SOURCE.match(jing_text)
    if m and m.group(1) == water_name:
        src = m.group(2)
        mtn = re.search(r"([\u4e00-\u9fff]{1,4})(山|谷|陬|都|墟)$", src)
        county = re.search(r"([\u4e00-\u9fff]{1,4})(县|郡)", src)
        if county:
            ctx["last_county"] = county.group(1)
        events.append({"t": "pass", "name": (mtn.group(1) if mtn else src)[:8],
                       "kind": mtn.group(2) if mtn else "源", "side": "", "source": True})
    # 河水特例：昆仑墟节「出其东北陬」
    if jing_text.startswith("出其"):
        events.append({"t": "pass", "name": "昆仑", "kind": "墟", "side": "", "source": True})
    # ── 过境航点（按子句）──
    for clause in re.split(r"[，。；]", jing_text):
        clause = clause.strip()
        if not clause:
            continue
        m = RE_PASS.search(clause)
        if m and (m.group(5) or m.group(4) == "其县"):
            side = m.group(8) or ""
            kind = m.group(6)
            if m.group(4) == "其县" or m.group(5) == "其":
                names = [ctx.get("last_county") or "前县"]
            else:
                names = m.group(5).split("、")
            for name in names:
                events.append({"t": "pass", "name": name, "kind": kind, "side": side})
                ctx["last_county"] = name
            continue
        m = RE_TERMINAL.search(clause)
        if m:
            tgt = m.group(3) or m.group(4) or ""
            events.append({"t": "term", "target": tgt})
    return events


def main():
    rivers, inventory_counter = [], Counter()
    first_seen = {}
    citation_counter = Counter()
    citation_where = {}   # book -> {water: n}
    citation_quotes = {}  # book -> [{q, water, vol}] ≤4 条（引书-引文数据库）
    appendix_texts = []

    order = 0
    for vi in range(1, 41):
        vol = f"{vi:03d}"
        text = open(os.path.join(VOL_DIR, f"{vol}.txt"), encoding="utf-8").read()
        sections, preamble = split_sections(text)
        if preamble:
            appendix_texts.append({"vol": vol, "kind": "preamble", "text": "\n".join(preamble)})
        for sec in sections:
            order += 1
            header = sec["header"]
            # 主水名 = 头部去「一/二/三」
            m = re.match(r"^([\u4e00-\u9fff〈〉]{1,6}?水)([一二三四五六七八九十]+)?", header)
            water_name = m.group(1) if m else header.split()[0]
            is_appendix = ("禹贡" in header) or ("日南郡" in header)
            rid = f"sjz-{order:03d}"

            river = {
                "id": rid, "name": water_name, "header": header,
                "vol": vol, "order": order, "type": "appendix" if is_appendix else "water",
                "jing": [],            # [{text, events}]
                "blocks": [],          # 注文段（挂到最近经文锚）: {after: jing_idx, text}
                "waypoints": [],       # 扁平航点（pass）
                "tributaries": [],     # 支流/分流事件
                "terminal": None,
            }
            ctx = {"last_county": None}
            cur_jing_idx = -1
            for ln in sec["lines"]:
                s = ln.strip()
                if not s:
                    continue
                if is_jing(s):
                    events = [] if is_appendix else parse_waypoints(s, ctx, water_name)
                    river["jing"].append({"text": s, "events": events})
                    cur_jing_idx = len(river["jing"]) - 1
                    for ev in events:
                        if ev["t"] == "pass":
                            wp = {"name": ev["name"], "kind": ev["kind"],
                                  "side": ev["side"], "jing_idx": cur_jing_idx}
                            if ev.get("source"):
                                wp["source"] = True
                            river["waypoints"].append(wp)
                        elif ev["t"] == "trib":
                            river["tributaries"].append({"name": ev["name"], "dir": ev.get("dir", ""),
                                                         "kind": "in", "jing_idx": cur_jing_idx})
                        elif ev["t"] == "outflow":
                            river["tributaries"].append({"name": ev["name"], "dir": "", "kind": "out",
                                                         "jing_idx": cur_jing_idx})
                        elif ev["t"] == "term":
                            river["terminal"] = {"target": ev["target"], "jing_idx": cur_jing_idx}
                else:
                    river["blocks"].append({"after": cur_jing_idx, "text": s})
                    # 注文引书（只统计曰/云/称等真引用 + 全提及两类由调用方取）
                    for b in RE_CITE.finditer(s):
                        citation_counter[b.group(1)] += 1
                        citation_where.setdefault(b.group(1), {})
                        citation_where[b.group(1)][water_name] = (
                            citation_where[b.group(1)].get(water_name, 0) + 1)
                    # 引文句捕获（每书 ≤4 条，存水道与卷次出处）
                    for q in RE_CITE_QUOTE.finditer(s):
                        bk = q.group(1)
                        qs = citation_quotes.setdefault(bk, [])
                        text = q.group(2).lstrip("：，、； ")
                        if len(qs) < 4 and not any(x["q"] == text for x in qs):
                            qs.append({"q": text, "water": water_name, "vol": vol})
                    # 注文支流：句首水名 + 句尾注之/入焉 → 汇入当前水
                    for m4 in RE_ZHU_TRIB.finditer(s):
                        tn = m4.group(1)
                        if tn == water_name or any(t["name"] == tn for t in river["tributaries"]):
                            continue
                        river["tributaries"].append({"name": tn, "dir": "", "kind": "in",
                                                     "jing_idx": cur_jing_idx, "src": "zhu"})
            # 全节水名提及（含注文）→ 全书水道清单
            # 排除动词/指代/泛数 +「水」的误收（出水、大水、之水……）
            joined = "\n".join(sec["lines"])
            for m2 in re.finditer(r"(?<!" + "|".join(INV_PREV_EXCL) + r")([\u4e00-\u9fff]{1,3}水)(?!名)", joined):
                nm = m2.group(1)
                if nm in INV_STOP or len(nm) < 2:
                    continue
                inventory_counter[nm] += 1
                if nm not in first_seen:
                    first_seen[nm] = f"{vol}/{water_name}"
            # 统计
            zhu_chars = sum(len(b["text"]) for b in river["blocks"])
            jing_chars = sum(len(j["text"]) for j in river["jing"])
            sec_cites = Counter()
            for b in river["blocks"]:
                for m3 in RE_CITE.finditer(b["text"]):
                    sec_cites[m3.group(1)] += 1
            river["stats"] = {
                "chars": zhu_chars + jing_chars,
                "zhu_chars": zhu_chars,
                "jing_chars": jing_chars,
                "citations": sum(sec_cites.values()),
                "citation_kinds": len(sec_cites),
                "legend_hits": sum(joined.count(w) for w in LEGEND_WORDS),
                "hydro_hits": sum(joined.count(w) for w in HYDRO_WORDS),
            }
            river["sec_cites"] = dict(sec_cites)
            rivers.append(river)

    # ── 全书级统计 ──
    jing_total = sum(len(j["text"]) for r in rivers for j in r["jing"])
    zhu_total = sum(len(b["text"]) for r in rivers for b in r["blocks"])
    wp_rivers = [r for r in rivers if r["waypoints"]]
    out = {
        "meta": {
            "vols": 40,
            "sections": len(rivers),
            "water_sections": len([r for r in rivers if r["type"] == "water"]),
            "jing_chars": jing_total,
            "zhu_chars": zhu_total,
            "rivers_with_waypoints": len(wp_rivers),
            "total_waypoints": sum(len(r["waypoints"]) for r in rivers),
            "distinct_water_names": len(inventory_counter),
            "distinct_citations": len(citation_counter),
        },
        "rivers": rivers,
    }
    with open(os.path.join(OUT_DIR, "rivers.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    with open(os.path.join(OUT_DIR, "inventory.json"), "w", encoding="utf-8") as f:
        json.dump({"counts": dict(inventory_counter.most_common()),
                   "first_seen": first_seen}, f, ensure_ascii=False)
    with open(os.path.join(OUT_DIR, "citations.json"), "w", encoding="utf-8") as f:
        json.dump({"counts": dict(citation_counter.most_common()),
                   "where": citation_where,
                   "quotes": citation_quotes}, f, ensure_ascii=False)

    m = out["meta"]
    print(f"分节 {m['sections']}（水道 {m['water_sections']}）")
    print(f"经文 {m['jing_chars']} 字 · 注文 {m['zhu_chars']} 字 · 经注比 1 : {m['zhu_chars']/max(m['jing_chars'],1):.1f}")
    print(f"含航点水道 {m['rivers_with_waypoints']} · 航点总数 {m['total_waypoints']}")
    print(f"全书出现的水名 {m['distinct_water_names']} 种")
    print(f"引书（曰/云/称句式）{m['distinct_citations']} 种，前 10：")
    for bk, n in citation_counter.most_common(10):
        print(f"   {bk}: {n}")


if __name__ == "__main__":
    main()
