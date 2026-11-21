# 水道经纬 · Waterway Jingwei

[![CI](https://github.com/V-T-V/shuidao-jingwei/actions/workflows/ci.yml/badge.svg)](https://github.com/V-T-V/shuidao-jingwei/actions/workflows/ci.yml)
**[▸ 线上版](https://v-t-v.github.io/shuidao-jingwei/)** · [发版 v1.2.1](https://github.com/V-T-V/shuidao-jingwei/releases/tag/v1.2.1)

北魏·郦道元《水经注》四十卷数字人文平台——方舆经纬（[D:\W_A_W\HHH](../HHH)）的姊妹项目。
同一套方法论，另一种空间诗学：彼以**点**（府治）织明末版图，此以**线**（水道）溯北魏江河。

```
水道经纬/
  index.html · 3d.html  # 七模式舆图 + 三维形胜（MapLibre 地形 + 河流线）
  data/river_data.js    # 112 条水道（折线/航点/支流拓扑/统计）· 管线生成
  data/sections.js      # 循水阅读文本（经注分离 · 1.1MB 懒加载）
  data/text/j01..j40.js # 全文检索层（懒加载）
  data/citations.js     # 引书考古数据库（428 种）
  data/crossref.js      # 互文快照（顾祖禹引《水经注》940 次）
  data/xrev_ql.js       # 引伽蓝记互查（伽蓝经纬快照·按水道重组·懒加载）
  tools/                # 管线：抓取 → 解析 → 坐标 → 构建 → lint → 分析
  tests/                # 断言页（数据 10 项 · 循水 7 项）
  docs/ANALYSIS.md      # 文本计量（凡数字必出自脚本）
```

## 快速开始

```bash
python -m http.server 9300 &      # 起本地服务
python tools/fetch_text.py        # Phase 0 抓取（断点续抓，已有则跳过）
python tools/parse_rivers.py      # Phase 1 经注分离 + 航点/支流
python tools/build_river_data.py  # Phase 2 折线 + 前端产物
python tools/build_crossref.py    # 互文快照（需方舆经纬语料）
python tools/build_xrev_ql.py     # 引伽蓝记互查（需伽蓝经纬站快照，只读不写）
python tools/build_modern_rivers.py # 今水真河线（Natural Earth 50m 缝合，需 data_raw/ne_rivers.geojson）
python tools/calibrate_jing.py      # 经注分离校准（方法 B：抽样+语法纯度硬门）
python tools/build_analysis.py    # docs/ANALYSIS.md
python tools/build_paper_pdf.py   # 研究论文 PDF（docs/水道经纬-*.pdf，lint 哨兵联动）
python run_tests.py               # lint 124 项 + 数据断言
```

## 核心体验

| # | 功能 | 入口 |
|---|---|---|
| 1 | **循水而读**——滚动文本，地图沿河飞行（昆仑→渤海 53 锚） | 点任一水道 / `#r=sjz-001` |
| 2 | **水系树**——干支拓扑层级导航 | 左列纲目 |
| 3 | **古今对照**——古线(实线) vs 今水(虚线) + 改道区(朱红) | 底栏「对照」 |
| 4 | **引书考古**——428 种引书频次与地域分布（亡佚标 †） | 「引书」/ `#c=山海经` |
| 5 | **互文（双向深链）**——双页签：① 顾祖禹 940 引省域分布，点省名 → [方舆经纬](https://v-t-v.github.io/fangyu-jingwei/) 省域视图（#mode=舆图&p=…），彼站文心「引水经注」节反向循水至此；② **引伽蓝记**——谷水注/洛水注（17,156 字快照）命中伽蓝记名物 21 处（城门 12·伽蓝 3·太仓/金墉城/翟泉等），按水道分组 + 10 对对读样例，↗伽蓝经纬深链（../LYGL/#juan=#gl=/#gate=，父目录同根服务）；伽蓝站「引水经注」页签 ↗循水至此，桥成双向 | 「互文」 |
| 6 | **计量**——注意力/传说密度/水文词/南北不对称 | 「计量」 |
| 7 | 全文检索（Worker）· 经注三态对照 · GeoJSON/KML/CSV 导出 · PWA 三级缓存离线 | 顶栏/底栏 |
| 8 | **三维形胜 + 循水飞行**——真地形沿岸逐点推进（源→委·拖拽即停·rAF 节流环境自动降级）· 点线循水 | 底栏「⛰ 形胜」 |
| 9 | Catmull-Rom 平滑 ↔ 航点实录直线（数据诚实由圆点承载） | 底栏「≈ 平滑」 |
| 10 | **引文辑录**——417 种书 1,207 则真实引文句（每书≤20·懒加载全文库），点卡循水至出处 | 「引书」任选一书 |
| 13 | **水名录**——754 水名辞典全带首见原句（分节/支流/仅见·即时过滤·点行展开） | 「计量」水名录 |
| 14 | **互文偏好**——ρ(郦注笔墨,顾祖禹引用)=0.37 双条对照，兵要剪裁自然史的量化痕迹 | 「计量」 |
| 15 | **传说地理学**——「源头多传说」假说全书证实（上游/下游密度比 1.47·67% 河流上游更浓） | ANALYSIS §六 |
| 16 | **水文生态句库**——季节水文句 28 条 + 渡津桥堰 723 次 + 鱼类 180 次（北魏径流一手计量） | ANALYSIS §十 |
| 11 | **经注并排**——左经右注四态轮换（并读/经/注/并排） | 循水条「经注」 |
| 12 | **TTS 朗读 + 夜读**——自当前锚点循水听书；墨色夜读记忆偏好 | 循水条「▷ 朗读」· 底栏「☾ 夜读」 |

## 数据边界（诚实口径）

- 文本：国学导航本（GB18030），校勘不在范围
- 经注分离：规则法（方法 A），经文 7,442 字（学界 7,000±1,000 内）
- 坐标：人工考据近似（±20km 级），航点覆盖 88.9%；「昆仑」等神话源标记 mythic 不入折线
- 折线：直线段实录 + 可选 Catmull-Rom 平滑；方位偏移试探 + 2-opt 去交叉（基线 4 处，lint 防退化）
- 今水层：Natural Earth 50m 真河线（黄/长/汉/赣/西江缝合）+ 手绘线兜底；改道区对真线重算
- 古今改道定量：ANALYSIS.md §八（河水最大偏差 1,010km=河出昆仑神话；江水偏差源出岷山导江古认知）
- 经注分离校准：B1 学理抽样 15/15 · B2a 语法纯度 100%（硬门）；B2b 骨架 101/120（报告项，docs/CALIBRATION.md）
- 水道计数：112 条分节水道 + 147 条支流边（与陈桥驿 1,252 口径差异见 ANALYSIS.md §7）

## 版本

`python tools/bump_version.py OLD NEW`——全站 `?v=` 一步到位，lint 校验一致性。
教训实录：SW 无差别缓存 + ignoreSearch 会把页面钉死成旧版（已改网络优先策略，见 sw.js 注）。
