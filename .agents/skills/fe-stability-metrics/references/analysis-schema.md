# 稳定性分析 JSON Schema

`fe-stability-metrics` 输出、`fe-stability-report-writer` 输入的唯一契约。

**当前版本**：`2.0`（总览与项目分析文件拆分）

## comparison_id 生成规则

```
若 time_granularity = day 且 CURR_START = CURR_END 且 BASE_START = BASE_END:
  comparison_id = "{CURR_END}_vs_{BASE_END}"
若 time_granularity = hour:
  comparison_id = "{CURR_START_AT}_to_{CURR_END_AT}_vs_{BASE_START_AT}_to_{BASE_END_AT}"
否则:
  comparison_id = "{CURR_START}-{CURR_END}_vs_{BASE_START}-{BASE_END}"
```

## 输出文件

```
{OUTPUT_DIR}/overview.json
{OUTPUT_DIR}/{app_name}.json
```

## 顶层结构

```yaml
meta:
  schema_version: "2.0"
  comparison_id: string
  cache_key: string | null        # Phase 1 缓存索引键
  run_id: string                  # 输出目录名
  today: yyyyMMdd                 # 跑批当日
  stability_window_days: number | null
  stability_window_hours: number | null
  stable_through: yyyyMMdd | null
  stable_through_at: ISO8601 | null
  includes_unstable_data: boolean # CURR 或 BASE 是否覆盖不稳定数据日
  is_provisional: boolean         # 是否为临时结果
  data_as_of: string              # ISO8601，实际查询/分析时间
  generated_at: string            # ISO8601，写入分析文件的时刻
  time_granularity: day | hour
  partition_timezone: string
  curr_start / curr_end / base_start / base_end: yyyyMMdd # 日模式
  curr_days / base_days: number                           # 日模式
  curr_start_at / curr_end_at / base_start_at / base_end_at: ISO8601 # 小时模式，半开区间
  curr_hours / base_hours: number                         # 小时模式
  curr_start_fmt / curr_end_fmt / base_start_fmt / base_end_fmt: string
  is_weekly_report: boolean
  scope_key: string                # apps-<sorted-app-names 的 SHA-256 前 12 位>
  app_names: [string]              # 传入或默认解析出的去重标准项目名
  project_files: { app_name: "{app_name}.json" } # 仅总览
  app_name: string | null          # 仅项目 JSON；总览为 null
  output_dir: string

global:
  totals: { base_total, curr_total, base_rate, curr_rate, rate_unit, change_pct, trend }
  daily_breakdown: { base: [{ds, count}], curr: [{ds, count}] }
  hourly_breakdown: { base: [{ds, hh, count}], curr: [{ds, hh, count}] }
  peak_days: [{ ds, count, note }]
  metrics: [ MetricItem ]
  summary_insight: string

issues:
  resource_load_failed / api_errors / white_screen / js_runtime / ssr / custom:
    title_suffix: string
    global: MetricItem
    details: [ ErrorDetailItem ]               # 按 impact_score 降序
    insight: string
    governance: string
    suggestions: [ string ]

priority_actions: [ ErrorDetailItem ]          # 全域 TOP 15，含 rank
spike_alerts: [ ErrorDetailItem ]              # is_spike=true，最多 30 条

governance:
  - { priority: P0|P1|P2, title, metric, change_pct, action, related_errors[] }

app_comparison:
  - { app, curr_total, change_pct, trend, drivers, improved[], worsened[], top_priority }
```

总览包含跨项目汇总字段 `global`、`app_comparison`、跨项目 `priority_actions` 与 `issues.*.details`。

每个项目 JSON 的顶层结构为：

```yaml
meta: { schema_version: "2.0", app_name: string, ... }
totals: { base_total, curr_total, base_rate, curr_rate, rate_unit, change_pct, trend }
daily_breakdown: { base: [{ds, count}], curr: [{ds, count}] }
hourly_breakdown: { base: [{ds, hh, count}], curr: [{ds, hh, count}] }
metrics: [ MetricItem ]
issues:                         # 与总览相同的类别键，但仅含本项目明细
  resource_load_failed:
    title_suffix: string
    global: MetricItem
    details: [ ErrorDetailItem ]
    insight: string
    governance: string
    suggestions: [ string ]
priority_actions: [ ErrorDetailItem ]
spike_alerts: [ ErrorDetailItem ]
governance: [ { priority, title, metric, change_pct, action, related_errors[] } ]
```

项目 JSON 不含 `global`、`app_comparison`、`project_files` 或任何 `by_app`；`details` 是唯一的错误明细列表，按 `impact_score` 降序；不得输出 `top_items`。

## MetricItem

```yaml
key: "script_error:resource_load_failed"
base_total: number
curr_total: number
base_rate: number
curr_rate: number
rate_unit: day | hour
change_pct: number | null
trend: string
title_suffix: string
```

## ErrorDetailItem

```yaml
rank: number                    # 仅 priority_actions 使用
app: string
category: string                # resource_load_failed | api_error | js_runtime | ...
key: string                     # resource_url 或 message 原文
display: string                 # 报告展示用短文本
base_count: number
curr_count: number
base_rate: number
curr_rate: number
rate_unit: day | hour
change_pct: number | null
trend: string
is_new: boolean
is_spike: boolean
spike_reason: string
priority: P0 | P1 | P2
impact_score: number
root_cause_hint: string
recommendation: string
extra: object                   # 可选，如 white_screen 的 page_breakdown
```
