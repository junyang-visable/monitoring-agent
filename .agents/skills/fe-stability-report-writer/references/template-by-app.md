# 按应用维度报告模板

> 数据来源：`analysis.json`。占位符映射见 `fe-stability-report-writer/SKILL.md` Step 3。

## 前端稳定性报告 — 按应用维度（{CURR_START_FMT} - {CURR_END_FMT} vs {BASE_START_FMT} - {BASE_END_FMT}）

数据来源：`icbu_de.visable_fe_full_monitoring_data_v1`，仅统计 **production** 环境，已排除 `api_slow`，仅统计 `level=error` 数据。
对比采用**日均值**归一化（当前周期÷{CURR_DAYS} vs 基线周期÷{BASE_DAYS}）。

---

## 一、{APP_NAME}（{APP_DESC}）

### 总量对比

| 周期 | 总量 | 日均 | 变化 |
|------|------|------|------|
| 基线 ({BASE_START_FMT}-{BASE_END_FMT}) | {BASE_TOTAL} | {BASE_DAILY_AVG} | — |
| 当前 ({CURR_START_FMT}-{CURR_END_FMT}) | {CURR_TOTAL} | {CURR_DAILY_AVG} | **{CHANGE}%** |

{一句话概括当前表现，指出是否有异常峰值}

| 日期 | 合计 |
|------|------|
| {M/D} | {COUNT} |

### 核心指标对比

| 错误类型 | 基线总量 | 基线/天 | 当前总量 | 当前/天 | 日均变化 |
|----------|---------|---------|---------|---------|---------|
| {event_type}: {error_type} | {BASE_TOTAL} | {BASE_DAILY} | {CURR_TOTAL} | {CURR_DAILY} | **{CHANGE}%** {箭头} |

**解读**：{2-3 句话分析该应用核心变化；须点名该 app 在 priority_actions 或 issues.*.by_app 中的 TOP 具体错误}

### 本应用需优先处理（TOP 5）

> 数据来源：`priority_actions[]` 中 `app={APP_NAME}`，或各 `issues.*.by_app.{APP_NAME}` 按 impact_score 取 TOP 5

| 优先级 | 类别 | 具体错误 | 基线/天 | 当前/天 | 变化 | 建议 |
|--------|------|----------|--------|---------|------|------|
| {priority} | {category} | {display} | {base_daily} | {curr_daily} | {change_pct}% | {recommendation} |

### 1. 资源加载失败（script_error: resource_load_failed，{COUNT} 次，占应用 {PCT}%）

| 资源 | 基线/天 | 当前/天 | 变化 | 突增 | 建议 |
|------|--------|---------|------|------|------|
| {display} | {base_daily} | {curr_daily} | {change_pct}% | {spike_reason 或 —} | {recommendation} |

<!-- issues.resource_load_failed.by_app.{APP_NAME} -->

> **治理追踪**：{治理建议}

### 2. JS 运行时错误（{COUNT} 次）

- **script_error: vue_error**（{COUNT} 次，日均 {DAILY}）：较基线日均 {BASE_DAILY} {上升/下降} {CHANGE}%
- **script_error: unhandled_rejection**（{COUNT} 次，日均 {DAILY}）：...
- **script_error: js_runtime_error**（{COUNT} 次，日均 {DAILY}）：...

高频消息：{message}（{N} 次）、...

### 3. API 错误（{COUNT} 次）

| 类型 | 数量 | 占比 |
|------|------|------|
| api_error: {error_type} | {N} | {PCT}% |

高频失败 API：

| 消息 / URL | 基线/天 | 当前/天 | 变化 | 建议 |
|-----------|--------|---------|------|------|
| {display} | {base_daily} | {curr_daily} | {change_pct}% | {recommendation} |

### 4. 白屏（{COUNT} 次）

{white_screen 类型和主要消息}，{页面分布}。日均 {DAILY} 次，与基线 {BASE_DAILY} 次{对比}。

> **治理追踪**：{治理建议}

### 5. SSR 错误（{COUNT} 次）

{如有 SSR 错误则列出类型和消息}

### 6. 业务自定义错误（如适用）

custom_error: update_failed：{COUNT} 次，日均 {DAILY}，{变化描述}。

> **治理追踪**：{治理建议}

---

<!-- 本模板仅渲染由映射表解析出的一个项目；不得追加其他项目章节或跨项目汇总。 -->
