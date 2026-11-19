"""水道经纬 · Phase 0 文本抓取
数据源: http://www.guoxue123.com/shibu/0301/00sjz/  (国学导航 · 水经注)
输出:   data_raw/NNN.html  原始页面(GB18030 原样保存)
        data/vol/NNN.txt   每卷纯净 UTF-8 文本（段落以 \n 分隔）
        data/fetch_report.json  字数/段落盘点
用法:   python tools/fetch_text.py          # 断点续抓（已存在且非空则跳过）
        python tools/fetch_text.py --force # 全部重抓
"""
import json
import os
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

BASE = "http://www.guoxue123.com/shibu/0301/00sjz"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(ROOT, "data_raw")
VOL_DIR = os.path.join(ROOT, "data", "vol")
os.makedirs(RAW_DIR, exist_ok=True)
os.makedirs(VOL_DIR, exist_ok=True)

JUAN_NAMES = {}  # 000 -> 原序, 001..040

# 页面噪音行（导航/版权）——按精确匹配剔除
NOISE_EXACT = {
    "上一页", "目录页", "下一页", "首页", "国学导航", "经部", "史部", "子部", "集部",
    "专题", "今人新著", "图文本导航：水经注", "",
}
NOISE_RE = re.compile(
    r"^(卷[一二三四五六七八九十百零〇]+_水经注|水经注（北魏）郦道元_?|图文本导航)"
)


def clean_html(html: str, num: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    text = soup.get_text("\n")
    lines = []
    for ln in text.split("\n"):
        ln = ln.replace("\u3000", "").replace("\xa0", "").strip()
        if ln in NOISE_EXACT or NOISE_RE.match(ln):
            continue
        # 剔除“卷X”独立行（标题已由文件名承载）
        if re.fullmatch(r"卷[一二三四五六七八九十百零〇]+", ln):
            continue
        if ln:
            lines.append(ln)
    return "\n".join(lines)


def fetch_one(num: str, force: bool) -> dict:
    txt_path = os.path.join(VOL_DIR, f"{num}.txt")
    raw_path = os.path.join(RAW_DIR, f"{num}.html")
    if not force and os.path.exists(txt_path) and os.path.getsize(txt_path) > 200:
        with open(txt_path, encoding="utf-8") as f:
            body = f.read()
        return {"num": num, "chars": len(body.replace("\n", "")),
                "paras": body.count("\n") + 1, "cached": True}
    url = f"{BASE}/{num}.htm"
    for attempt in range(3):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt == 2:
                raise
            print(f"  重试 {num}: {e}")
            time.sleep(3 * (attempt + 1))
    resp.encoding = "gb18030"
    with open(raw_path, "w", encoding="utf-8") as f:
        f.write(resp.text)          # 保留原始页面（转码后）供复查
    body = clean_html(resp.text, num)
    if len(body) < 300:
        raise RuntimeError(f"{num}.htm 清洗后仅 {len(body)} 字，疑似版式变化，请人工检查 {raw_path}")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(body)
    return {"num": num, "chars": len(body.replace("\n", "")),
            "paras": body.count("\n") + 1, "cached": False}


def main():
    force = "--force" in sys.argv
    report = []
    nums = ["000"] + [f"{i:03d}" for i in range(1, 41)]
    for num in nums:
        info = fetch_one(num, force)
        tag = "缓存" if info["cached"] else "抓取"
        print(f"[{tag}] {num}  {info['chars']:>6} 字  {info['paras']:>3} 段")
        report.append(info)
        if not info["cached"]:
            time.sleep(1.0)   # 礼貌抓取
    total = sum(r["chars"] for r in report)
    out = {"source": BASE, "vols": report,
           "total_chars": total,
           "fetched_at": time.strftime("%Y-%m-%d %H:%M:%S")}
    with open(os.path.join(ROOT, "data", "fetch_report.json"), "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"\n合计 {total} 字（40 卷 + 原序）→ data/fetch_report.json")


if __name__ == "__main__":
    main()
