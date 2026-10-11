# Conference Atlas v4 — 会议数据扩充与自动监测

**截至 2026-10-12 的编辑核查快照。** 该日期代表整理时点；打开本地 HTML 不会实时抓取任何官网。

## 本轮已经实现

- 由 **9 届**增加到 **21 届会议**（2026–2028），以官方学会/主办方网页为来源：新增 NISPAcee 2027、ECPR General Conference 2027、ECPR Joint Sessions 2027、IPSA World Congress 2027、APSA 2027/2028、EGPA 2027、ARNOVA 2026，以及与环境政策相关的 EGU 2027/2028、IAEE Madrid 2027 和 IAEE Nanjing 2027。
- 4 个页面从同一份 `data/conferences.json` 读取会议信息；改动 JSON 后需要运行 `python scripts/export_data.py` 才会更新浏览器端副本。地图定位精度为**举办城市**，不是会议场馆。
- Panel、Section、Paper、Abstract 分别记录截止日期；未知日期用 `null`，**不会按往年日期推断**。
- 针对个别会议的例外规则增加说明，例如 NISPAcee 2027 的 Full Paper 截止日期只适用于奖项竞赛；APPAM 2026 的 Late registration 价格区间结束日并非最终报名截止日。
- 自动更新分成两级：`sync_conferences.py` 用针对性规则检查已确认的关键日期，较大的变更进入待核验队列；`monitor_sources.py` 对14个官方入口监测新链接和日期段落变化，输出供核查的记录，**不直接发布它猜测的日期**。
- GitHub Actions 每天计划运行一次（GitHub 定时任务可能延迟），但**必须部署到你自己的 GitHub 仓库并开启 Actions 权限后才会运行**。本地 Demo 完全离线。

## 重要文件

- `data/conferences.json` — 会议主表，附官方链接与上次编辑核查时间
- `data/monitor_sources.json` — 14 个经过选择的官方监测入口，不应添加会议聚合站
- `data/pending_changes.json` — 日期提取异常/大幅更改待核验
- `data/source_changes.json` — 官网内容变化（待人工核验）
- `data/candidates.json` — 自动发现但尚未人工确认的新会议链接
- `data/source_health.json` — 官网抓取成功/失败状态
- `data/change_log.json` — 已自动更新的日期历史
- `scripts/sync_conferences.py` / `scripts/monitor_sources.py` — 两个监测脚本
- `.github/workflows/refresh.yml` — 每天运行的计划任务

## 在本地运行

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python scripts/export_data.py
python scripts/sync_conferences.py --dry-run
python scripts/monitor_sources.py --dry-run
python -m http.server 8000
```

然后打开 `http://localhost:8000`。也可以直接双击 `index.html` 浏览静态快照。

## 如何人工核验变更

1. 检查 `data/pending_changes.json` 和 `data/source_changes.json` 中的 `needs_manual_review` 记录。
2. 打开对应官网核对具体会议年份、投稿类型、时间和时区。不要把 hotel booking / travel / grant deadline 当成 CFP。
3. 将已确认信息编辑到 `data/conferences.json`，确认 `source` / `verifiedAt` / `editorialNote` 等字段同步更新。
4. 运行 `python scripts/export_data.py` 和 `python -m unittest discover -s tests -v`。
5. 发布网站。新日期会同步出现在 Home、Explore、Calendar 和 Map。

## 尚未实现

- 正式公网部署、实时数据库、自动发送邮件提醒和新会议无需人工确认的自动发布。
- 对任何官网都适用的通用 CFP 解析（受网页结构、PDF、登录和反机器人限制）。
- 已经在用户账户中开启的定时任务。GitHub 的工作流文件不等于后台已经启动。

## 信息真实性

会议内容取自各主办方的公开官方网页，仍可能发生更改；直接投稿或支付前应核对官网。部分官网阻止脚本抓取，这种情况记为未成功检查，不能把本地数据标记为“实时已核实”。
