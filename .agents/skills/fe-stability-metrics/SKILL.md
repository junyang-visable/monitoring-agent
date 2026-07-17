---
name: fe-stability-metrics
description: 解析稳定性查询结果，计算环比与治理优先级，输出含具体错误突增与处理建议的 analysis.json。
version: 1.4.0
---

# 稳定性数据分析

## 职责边界

本 skill 负责：

1. 解析 Phase 2 全部查询结果（类型量级 + Group C 具体错误）
2. 计算 event_type 级与 **message/url 级** 环比、突增、优先级
3. 生成根因提示与 **可执行建议**（`recommendation`）
4. 写入 `{OUTPUT_DIR}/analysis-{comparison_id}.json`

**不** 负责 SQL 生成、查询执行、Markdown 渲染。

---

## 输入

- Phase 1「fe-stability-query」输出的日期变量、`IS_WEEKLY_REPORT`、`scope`（项目范围另含 `app_name`）
- Phase 1 输出的 `STABILITY_WINDOW_DAYS`、`STABLE_THROUGH`、`INCLUDES_UNSTABLE_DATA`、`IS_PROVISIONAL`、`data_as_of`
- Phase 2 全部查询结果（**必须含 Group C**：C1/C2/C3/C4/C5/C6 各 1 条合并查询，结果必须含 `period=CURR|BASE`，且只限当前范围）
- `{OUTPUT_DIR}`

若缺少 Group C、C6 白屏页面结果或任一结果缺少 CURR/BASE `period`，**阻塞并提示**编排器补跑 Phase 2 第四轮，不得仅输出类型级分析。

---

## Step 1：生成 comparison_id

规则见 [references/analysis-schema.md](references/analysis-schema.md)。

---

## Step 2：解析类型级数据

| 模块 | 来源 |
|------|------|
| `global.totals` / `daily_breakdown` | A（按 `period` 拆分） |
| `global.metrics` | B（按 `period` 拆分） |

`scope=app` 时，以上 `global` 字段表示该指定项目的汇总；不得推断或填充其他应用数据。

---

## Step 3：类型级指标计算

按 [references/metrics-rules.md](references/metrics-rules.md) 计算 `MetricItem`、`governance[]`、`app_comparison[]`、`peak_days`。

---

## Step 4：具体错误信息分析（必做）

按 [references/message-analysis.md](references/message-analysis.md) 处理 Group C：

1. 按 `period` 拆分每条 `{C_ID}` 合并查询结果（PERIOD = CURR | BASE）
2. 计算每条 `ErrorDetailItem` 的 daily、change、is_spike、priority、impact_score
3. 生成 `root_cause_hint` 与 `recommendation`
4. 填充：
   - `issues.*.details[]`；白屏页面分布写入对应 `white_screen` 明细的 `extra.page_breakdown`；仅 `scope=app` 时可填充对应单一项目的 `issues.*.by_app.{app_name}`
   - `priority_actions[]`（TOP 15，带 `rank`）
   - `spike_alerts[]`（全部突增项）
5. 将 P0 相关具体错误 id 写入 `governance[].related_errors[]`

---

## Step 5：领域解读

- `global.summary_insight`：**必须**引用 `priority_actions` TOP 1–2 与突增数量
- `issues.*.insight`：**必须**引用该类别 `details` TOP 3 的具体 message/url
- `issues.*.suggestions`：从对应 `details` 的 `recommendation` 去重提炼 2–4 条

**禁止** 只写「某类型上升 X%」而不点名具体错误。

---

## Step 6：写入 analysis.json

路径：`{OUTPUT_DIR}/analysis-{comparison_id}.json`

`meta` 必须包含：

- `schema_version: "1.1"`
- `comparison_id`、`today`、`generated_at`（ISO8601）
- 全部日期变量 + `is_weekly_report`
- `output_dir`（绝对路径）
- `stability_window_days`、`stable_through`、`includes_unstable_data`、`is_provisional`
- `data_as_of`（ISO8601，实际查询或分析时间）
- `scope: "global" | "app"`、`app_name`（仅 `scope=app`）

结构见 [references/analysis-schema.md](references/analysis-schema.md)。

---

## 输出约定

返回：

1. `analysis.json` 绝对路径
2. `comparison_id`
3. 摘要：**P0 数量**、**突增条数**、**首要处理项 display**
