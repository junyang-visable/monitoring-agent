---
name: fe-stability-metrics
description: 解析稳定性查询结果，计算环比与治理优先级，输出全局总览与每项目独立 JSON，含具体错误突增与处理建议。
version: 2.3.0
---

# 稳定性数据分析

## 职责边界

本 skill 负责：

1. 解析 Phase 2 全部查询结果（类型量级 + Group C 具体错误）
2. 计算 event_type 级与 **message/url 级** 环比、突增、优先级
3. 生成根因提示与 **可执行建议**（`recommendation`）
4. 写入一个总览 JSON 和每个项目各自的 JSON

**不** 负责 SQL 生成、查询执行、Markdown 渲染。

---

## 输入

- Phase 1「fe-stability-query」输出的日期/小时变量、`time_granularity`、`partition_timezone`、`IS_WEEKLY_REPORT`、`app_names`
- Phase 1 输出的日或小时稳定窗口参数、`INCLUDES_UNSTABLE_DATA`、`IS_PROVISIONAL`、`data_as_of`
- Phase 2 全部查询结果（**必须含 Group C**：C1/C2/C3/C4/C5/C6 各 1 条合并查询，结果必须含 `period=CURR|BASE`，且只限当前范围）
- `{OUTPUT_DIR}`、当前 `run_id`、`cache_key`、`cache_key_input` 与 `cache_index_file`

若缺少 Group C、C6 白屏页面结果或任一结果缺少 CURR/BASE `period`，**阻塞并提示**编排器补跑 Phase 2 第四轮，不得仅输出类型级分析。

---

## Step 1：生成 comparison_id

规则见 [references/analysis-schema.md](references/analysis-schema.md)。

---

## Step 2：解析类型级数据

| 模块 | 来源 |
|------|------|
| `global.totals` / `daily_breakdown` / `hourly_breakdown` | A（按 `period` 拆分） |
| `global.metrics` | B（按 `period` 拆分） |

按 `app_name` 拆分 A/B 结果，构建总览的 `global` 合计与每个项目自己的独立结果。`time_granularity=hour` 时 A 必须含 `ds,hh`，生成 `hourly_breakdown`，并可由其汇总 `daily_breakdown`。不得推断或填充未传入的应用数据。

---

## Step 3：类型级指标计算

按 [references/metrics-rules.md](references/metrics-rules.md) 计算 `MetricItem`、`governance[]`、`app_comparison[]`、`peak_days`。

---

## Step 4：具体错误信息分析（必做）

按 [references/message-analysis.md](references/message-analysis.md) 处理 Group C：

1. 先按 `app_name` 再按 `period` 拆分每条 `{C_ID}` 合并查询结果（PERIOD = CURR | BASE）
2. 计算每条 `ErrorDetailItem` 的 rate、change、is_spike、priority、impact_score；`rate_unit` 取 `day` 或 `hour`
3. 生成 `root_cause_hint` 与 `recommendation`
4. 填充：
   - 总览的 `issues.*.details[]`；白屏页面分布写入对应 `white_screen` 明细的 `extra.page_breakdown`
   - 每个项目 JSON 自己的 `issues.*.details[]`，不得再写 `issues.*.by_app`
   - 总览和每个项目各自的 `priority_actions[]`（TOP 15，带 `rank`）与 `spike_alerts[]`
5. 将 P0 相关具体错误 id 写入 `governance[].related_errors[]`

---

## Step 5：领域解读

- `global.summary_insight`：**必须**引用 `priority_actions` TOP 1–2 与突增数量
- `issues.*.insight`：**必须**引用该类别 `details` TOP 3 的具体 message/url
- `issues.*.suggestions`：从对应 `details` 的 `recommendation` 去重提炼 2–4 条

**禁止** 只写「某类型上升 X%」而不点名具体错误。

---

## Step 6：写入分析产物

路径：

```text
{OUTPUT_DIR}/overview.json
{OUTPUT_DIR}/{app_name}/fe-stability-analysis.json
```

`scope_key` 为项目按字典序拼接后 SHA-256 前 12 位的 `apps-<hash>`。

总览 `meta` 必须包含：

- `schema_version: "2.0"`
- `comparison_id`、`run_id`、`today`、`generated_at`（ISO8601）
- 全部日期/小时变量、`time_granularity`、`partition_timezone` 和 `is_weekly_report`
- `output_dir`（绝对路径）
- 日或小时稳定窗口参数、`includes_unstable_data`、`is_provisional`
- `data_as_of`（ISO8601，实际查询或分析时间）
- `app_names`、`scope_key` 和每个项目 JSON 的相对路径映射 `project_files`（`{app_name}/fe-stability-analysis.json`）
- `cache_key`（由 Phase 1 计算；不稳定数据也可记录但不得写缓存索引）

每个项目 JSON 复用相同时间、粒度与稳定窗口 `meta`，并额外包含唯一 `app_name`；只包含该项目的 totals、breakdowns、metrics、issues、priority_actions、spike_alerts 与 governance。

所有 JSON 写入成功后，仅当 `includes_unstable_data=false`、`is_provisional=false` 且未要求刷新时，按 [cache-policy.md](../fe-stability-analysis/references/cache-policy.md) 原子更新 `cache_index_file` 的 `entries[cache_key]`。索引只能记录当前 run 的绝对路径，不得复制 JSON 或覆盖其他 `cache_key` 的条目。

结构见 [references/analysis-schema.md](references/analysis-schema.md)。

---

## 输出约定

返回：

1. 总览 JSON 绝对路径
2. `app_name → 项目 JSON 绝对路径` 映射
3. `comparison_id`
4. 摘要：**P0 数量**、**突增条数**、**首要处理项 display**
