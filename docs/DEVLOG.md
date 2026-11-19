# 水道经纬 · 建造账（DEVLOG）

> 承方舆经纬治理文化：教训入账，追加不改写。凡本条目皆为实测所得，附验证方式。
> 格式：`日期 · 主题 —— 教训 · 验证`。

## 一纪 · 缓存三重门（2026-11-19）

**主题**：本地迭代中"改了没生效"的三大元凶，逐一门槛踩过。

1. **SW 无差别缓存 + `ignoreSearch`**：初版 sw.js 把一切同源响应塞 SHELL 缓存且忽略查询串——
   `?bust=` 失效、测试页被钉死成旧版、`unregister + caches.delete` 后 hash 跳转根本没重载页面（同文档导航）。
   修正：同源改**网络优先**，仅版本化资源（`?v=`）随取随存。验证：净环境重载断言页 PASS。
2. **HTTP 启发式缓存**：python http.server 带 Last-Modified，浏览器会再验证——但**同 URL 不换内容**
   （`?v=1` 装着 v3 代码）造成"文件名没变、内容变了"的幽灵态。修正：改资产必 bump（工具化 `tools/bump_version.py`）。
3. **懒加载数据也要挂版本**：`data/sjz_xref.js` 无版本参数 → 修正后数据不达。懒加载 URL 一律 `?v=N`。

**铁律**：改任何被引用的资产 → `bump_version.py` → 重验证。与 lint 的版本一致性检查互为表里。

## 二纪 · 深链的合并主键（2026-11-19）

同名跨卷分节（河水一~五）合并后只保留**首节 id**（sjz-001）为水道主键；用末节 id（sjz-005）构造深链
在姊妹站是断链。方舆经纬侧 `build_sjz_xref.py` 初版即踩中——`id_by_name.setdefault` 保首弃末。
验证：河南引文样例 `#r=sjz-005` → 修正 `#r=sjz-001`，线上 53 锚打开。

## 三纪 · YAML 块标与假触发器（2026-11-19）

audit.yml 的 heredoc 步骤漏 `run: |` 块标 → YAML 第 23 行起解析失败 → GitHub 收文件但**编译不出任何
触发器** → `workflow_dispatch` 422 "Workflow does not have ... trigger"（报错误导人去查触发器语法，
真因在文件他处）。且空花括号 `workflow_dispatch: {}` 亦是非标准写法。
修正：本地 `yaml.safe_load` 过验再推；标准无值键写法。
验证：dispatch 即跑，[run 44520582743](https://github.com/V-T-V/shuidao-jingwei/actions/runs/44520582743) 7 秒全绿。

## 四纪 · rAF 节流环境的动画假死（2026-11-19）

嵌入式 webview 会挂起 requestAnimationFrame（document.hidden=false 亦然）：Leaflet `flyTo` 排队不动、
MapLibre `easeTo` 同病。**诊断指纹**：`map._flyToFrame` 挂起 + `setView(animate:false)` 正常。
修正：3D 循飞加动画探测——首点 easeTo 后量位移，未动则自动降级 `jumpTo` 逐点推进。
教训：任何 rAF 依赖都应有非动画兜底路径；验证时先探 rAF 是否真的在跑。

## 五纪 · 跨窗口拿不到 const（2026-11-19）

script 作用域 `const SJZ` / `function` 声明不在 `window` 上：父页访问 iframe 的 `W.SJZ` 恒 undefined。
修正：断言页以 `window.SJREADER`（显式挂载）为准；数据模块约定 `window.XXX =` 导出或 typeof 守卫裸引用。

## 六纪 · 折线自交叉的分层治理（2026-11-19）

初版 44 处自交叉。盲改方位偏移无效（44→40）；分层定位真因：①神话源重复入线（昆仑/积石在汉代河道前
重现）→ 标 `mythic` 不入折线；②偏移越轴 → 试探法（先全线无偏移，逐点试加、近邻段相交即放弃）；
③坐标噪声折返 → 2-opt 反折（长度增幅<30% 约束）。44 → 4，残留已诊断（济水二吸收泗水首段 3 + 淇水 1）
入 lint 基线防退化。

## 七纪 · 方舆经纬账本纪律的咬合（2026-11-19）

给姊妹仓加文件：`verify.py` 的 SHA256SUMS 全目录在账会咬新文件；Git Bash `sha256sum` 输出带二进制
`*` 标记且行尾 CRLF 害 sed 锚点失灵——账本行一律 Python 写（两空格分隔）。跨仓协作先读对方 AGENTS.md
的账本/版本/lint 规则，再动手。

## 八纪 · 网络窗口（2026-11-19）

github.com:443 时通时断（SSL_read reset / connect timeout 交替），api.github.com 反而稳。
git push 需带重试循环（实测最长第 8 次窗口重开）；gh api 操作（建仓/发版/Pages/workflow）几乎不受影响。
大文件单次成功率高：主干+tags 一次 12MB 推成，单 commit 重试可达 8 轮。

## 九纪 · 数据诚实口径（2026-11-19）

- 陈桥驿 1,252 水道 ≠ 本站 112 分节：定义差，非缺漏（ANALYSIS §七说明，不硬凑数）
- 考据坐标宁缺毋滥：单字占位（前县/上/乡）与存疑（郭落/卢聚）不录，覆盖 95.4% 是可辩护数字
- 骨架完备 101/120 是报告项不是门槛；硬门只设语法纯度（100%）与学理抽样（15/15）
- 神话地理（昆仑 88.2°E）入图但标 `mythic`——文本世界与地理世界分层呈现
