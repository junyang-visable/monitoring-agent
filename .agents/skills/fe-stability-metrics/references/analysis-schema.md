# analysis.json Schema

`fe-stability-metrics` 输出、`fe-stability-report-writer` 输入的唯一契约。

**当前版本**：`1.1`（新增具体错误信息分析字段）

## comparison_id 生成规则

```
若 CURR_START = CURR_END 且 BASE_START = BASE_END:
  comparison_id = "{CURR_END}_vs_{BASE_END}"
否则:
  comparison_id = "{CURR_START}-{CURR_END}_vs_{BASE_START}-{BASE_END}"
```

## 输出文件

```
{OUTPUT_DIR}/analysis-{comparison_id}.json
```

## 顶层结构

```yaml
meta:
  schema_version: "1.1"
  comparison_id: string
  today: yyyyMMdd                 # 跑批当日
  includes_today: boolean         # CURR 或 BASE 是否含 today
  generated_at: string            # ISO8601，写入 analysis.json 的时刻
  curr_start / curr_end / base_start / base_end: yyyyMMdd
  curr_days / base_days: number
  curr_start_fmt / curr_end_fmt / base_start_fmt / base_end_fmt: string
  is_weekly_report: boolean
  scope: global | app
  app_name: string | null         # 仅 scope=app 时为指定项目
  output_dir: string

global:
  totals: { base_total, curr_total, base_daily, curr_daily, change_pct, trend }
  daily_breakdown: { base: [{ds, count}], curr: [{ds, count}] }
  peak_days: [{ ds, count, note }]
  metrics: [ MetricItem ]
  summary_insight: string

by_app:                           # 仅 scope=app 时可选，且只允许一个 app_name
  {app_name}:
    desc: string
    totals: { ... }
    daily: [{ ds, count }]
    metrics: [ MetricItem ]
    metric_share: { "event:error": 0.96 }

issues:
  resource_load_failed / api_errors / white_screen / js_runtime / ssr / custom:
    title_suffix: string
    global: MetricItem
    top_items: [{ key, count, note }]          # 兼容旧字段，取 details TOP
    details: [ ErrorDetailItem ]               # 按 impact_score 降序
    by_app: { {app_name}: [ ErrorDetailItem ] }
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

## MetricItem

```yaml
key: "script_error:resource_load_failed"
base_total: number
curr_total: number
base_daily: number
curr_daily: number
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
base_daily: number
curr_daily: number
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
