"""水道经纬 · 回归入口
python run_tests.py
  1) tools/lint.py         确定性静态检查（115+ 项）
  2) 数据断言（同 tests/assert_data.html 的 python 版）
  3) 浏览器断言页提醒（tests/assert_*.html，需 http 服务下人工/截图验看）
"""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
fails = []


def step(name, fn):
    print(f"—— {name} ——")
    try:
        fn()
        print(f"✓ {name} 通过\n")
    except AssertionError as e:
        fails.append(name)
        print(f"✗ {name} 失败：{e}\n")


def lint():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "lint.py")],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout.strip())
    assert r.returncode == 0, "lint 未全绿"


def data_asserts():
    riv = json.load(open(os.path.join(ROOT, "data/intermediate/rivers.json"), encoding="utf-8"))
    m = riv["meta"]
    assert m["water_sections"] >= 100, f"分节 {m['water_sections']} < 100"
    assert m["total_waypoints"] >= 500, f"航点 {m['total_waypoints']} < 500"
    assert 6500 <= m["jing_chars"] <= 8200, f"经文 {m['jing_chars']} 越界"
    t = open(os.path.join(ROOT, "data/river_data.js"), encoding="utf-8").read()
    sjz = json.loads(t[t.find("const SJZ = ") + len("const SJZ = "):].rstrip().rstrip(";"))
    assert sjz["meta"]["coverage"] >= 60, f"覆盖率 {sjz['meta']['coverage']}% < 60"
    hs = next(w for w in sjz["waterways"] if w["name"] == "河水")
    assert hs["stats"]["zhuChars"] > 15000
    assert sjz["meta"]["crossings"] <= 4
    cites = json.load(open(os.path.join(ROOT, "data/intermediate/citations.json"), encoding="utf-8"))
    assert len(cites["counts"]) >= 350
    xref = open(os.path.join(ROOT, "data/crossref.js"), encoding="utf-8").read()
    assert '"total":940' in xref or '"total": 940' in xref, "互文快照总数异常"
    print(f"水道 {sjz['meta']['waterways']} · 航点 {sjz['meta']['wpTotal']} · 覆盖 {sjz['meta']['coverage']}% · "
          f"引书 {len(cites['counts'])} · 自交叉 {sjz['meta']['crossings']} · 互文 940")


def calibration():
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "calibrate_jing.py"), "--strict"],
                       capture_output=True, text=True, encoding="utf-8")
    print(r.stdout.strip())
    assert r.returncode == 0, "经注分离校准未过（B1 抽样或 B2 完备性）"


def browser_pages():
    pages = [f for f in os.listdir(os.path.join(ROOT, "tests")) if f.startswith("assert_")]
    print(f"浏览器断言页 {len(pages)} 枚：{', '.join(pages)}")
    print("（serve 后逐页打开，title=PASS 即绿——截图证据见 docs/evidence/）")


def offline_check():
    """离线三验（可选步：本地服务在跑且有浏览器才执行；CI 由 audit.yml 专步硬跑不吞错）。"""
    import shutil
    import urllib.request
    base = os.environ.get("SDJW_BASE", "http://127.0.0.1:9300/")
    try:
        urllib.request.urlopen(base + "index.html", timeout=3).read()
    except Exception:
        print(f"（跳过：本地服务不可达 {base}——起服务后可单跑 python tools/offline_check.py）")
        return
    cands = [os.environ.get("SDJW_BROWSER", ""),
             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             shutil.which("google-chrome") or "", shutil.which("chromium") or ""]
    if not next((c for c in cands if c and os.path.exists(c)), None):
        print("（跳过：未找到本地浏览器——SDJW_BROWSER 可指定）")
        return
    r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "offline_check.py")],
                       capture_output=True, text=True, encoding="utf-8", timeout=300)
    print(r.stdout.strip())
    assert r.returncode == 0, f"离线三验未全绿（exit {r.returncode}）"


if __name__ == "__main__":
    step("lint", lint)
    step("数据断言", data_asserts)
    step("经注分离校准（方法 B）", calibration)
    step("浏览器断言页", browser_pages)
    step("离线三验（可选）", offline_check)
    if fails:
        print(f"✗✗ 回归失败：{', '.join(fails)}")
        sys.exit(1)
    print("═══ 全绿 ═══")
