# 项目范围报告模板

> 数据来源：`analysis.json` 的 `meta.app_names`、`by_app`、`issues.*.by_app` 与 `priority_actions`。单项目和多项目均使用本模板。

## 前端稳定性报告 — 项目范围（{CURR_START_FMT} - {CURR_END_FMT} vs {BASE_START_FMT} - {BASE_END_FMT}）

数据来源：`icbu_de.visable_fe_full_monitoring_data_v1`，仅统计 production、`level=error`，并排除 `api_slow`。对比采用与 `meta.time_granularity` 一致的单位速率归一化；小时模式明确标注“每小时”。

### 优先处理项

按 `priority_actions[]` 展示 TOP 15；必须包含应用、类别、具体错误、基线/天、当前/天、变化和建议。

### 按项目明细

按 `meta.app_names` 的排序逐个渲染以下章节，不得包含范围外项目：

#### {APP_NAME}

- 总量与核心指标：`by_app.{APP_NAME}.totals`、`by_app.{APP_NAME}.metrics`
- 本项目 TOP 5：`priority_actions[]` 中 `app={APP_NAME}`，或 `issues.*.by_app.{APP_NAME}`
- 资源、JS、API、白屏、SSR/自定义错误：对应 `issues.*.by_app.{APP_NAME}`，列出基线/天、当前/天、变化和建议。

每个项目均须点名至少一条具体错误；没有数据时如实标记为空，不得编造。
