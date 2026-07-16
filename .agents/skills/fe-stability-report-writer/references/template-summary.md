# 全域维度报告模板

> 数据来源：`analysis.json`。占位符映射见 `fe-stability-report-writer/SKILL.md` Step 2。

## 前端稳定性报告 — 全域维度（{CURR_START_FMT} - {CURR_END_FMT} vs {BASE_START_FMT} - {BASE_END_FMT}）

数据来源：`icbu_de.visable_fe_full_monitoring_data_v1`，仅统计 **production** 环境，已排除 `api_slow`，仅统计 `level=error` 数据。
对比采用**日均值**归一化（当前周期÷{CURR_DAYS} vs 基线周期÷{BASE_DAYS}）。

---

### 总量概览

| 周期 | 天数 | 总量 | 日均 | 变化 |
|------|------|------|------|------|
| 基线 ({BASE_START_FMT}-{BASE_END_FMT}) | {BASE_DAYS} | {BASE_TOTAL} | {BASE_DAILY_AVG} | — |
| 当前 ({CURR_START_FMT}-{CURR_END_FMT}) | {CURR_DAYS} | {CURR_TOTAL} | {CURR_DAILY_AVG} | **{TOTAL_CHANGE}%** |

{一段话总结整体趋势，指出最大驱动因素和异常事件}

基线每日明细：{逐日数据，格式: M/D NNN,NNN → ...，标注峰值日加粗}
当前每日明细：{逐日数据，格式同上}

---

### 核心指标对比（日均值）

| 指标 | 基线/天 | 当前/天 | 变化 | 趋势 |
|------|--------|---------|------|------|
| **{event_type}: {error_type}** | {BASE_DAILY} | {CURR_DAILY} | **{CHANGE}%** | {趋势箭头} |
| ... | ... | ... | ... | ... |

<!-- 按当前日均值从高到低排列所有 event_type: error_type 组合 -->
<!-- 加粗变化 ≥50% 或 ≤-50% 的行 -->

**解读**：{2-3 句话分析核心变化：最大恶化项、最大改善项、需要关注的指标}

---

### 需优先处理的具体错误（TOP 15）

> 数据来源：`priority_actions[]`

| # | 优先级 | 应用 | 类别 | 具体错误 | 基线/天 | 当前/天 | 变化 | 突增 | 建议 |
|---|--------|------|------|----------|--------|---------|------|------|------|
| {rank} | **{priority}** | {app} | {category} | {display} | {base_daily} | {curr_daily} | **{change_pct}%** {trend} | {spike_reason 或 —} | {recommendation} |
| ... | ... | ... | ... | ... | ... | ... | ... | ... | ... |

**首要处理**：{priority_actions[0].display} — {priority_actions[0].recommendation}

---

### 错误突增告警

> 数据来源：`spike_alerts[]`（`is_spike=true`）

| 应用 | 类别 | 具体错误 | 基线/天 | 当前/天 | 变化 | 原因 | 建议 |
|------|------|----------|--------|---------|------|------|------|
| {app} | {category} | {display} | {base_daily} | {curr_daily} | {change_pct}% | {spike_reason} | {recommendation} |

---

### 问题一：资源加载失败 — {标题后缀}

script_error: resource_load_failed 当前 {CURR_COUNT} 次（日均 {CURR_DAILY}），基线 {BASE_COUNT} 次（日均 {BASE_DAILY}），**日均{上升/下降} {CHANGE}%**。{描述分布特征和主要来源}

主要失败资源（含环比与建议）：

| 资源 | 基线/天 | 当前/天 | 变化 | 优先级 | 建议 |
|------|--------|---------|------|--------|------|
| {display} | {base_daily} | {curr_daily} | {change_pct}% {trend} | {priority} | {recommendation} |
| ... | ... | ... | ... | ... | ... |

<!-- 数据来源：issues.resource_load_failed.details[]，按 impact_score 降序 -->

> **治理追踪**：{治理建议和后续关注点}

**建议**：{具体修复建议}

---

### 问题二：API 错误 — {标题后缀}

API 错误（不含 api_slow）日均约 {N} 次，较基线 {N} 次{上升/下降}：

| 错误类型 | 基线/天 | 当前/天 | 变化 |
|----------|--------|---------|------|
| api_error: unknown | {BASE_DAILY} | {CURR_DAILY} | {CHANGE}% {箭头} |
| api_error: network | ... | ... | ... |
| api_error: client | ... | ... | ... |
| api_error: timeout | ... | ... | ... |
| api_error: server | ... | ... | ... |

高频失败 API（含环比与建议）：

| API / 消息 | 基线/天 | 当前/天 | 变化 | 优先级 | 建议 |
|-----------|--------|---------|------|--------|------|
| {display} | {base_daily} | {curr_daily} | {change_pct}% {trend} | {priority} | {recommendation} |

<!-- 数据来源：issues.api_errors.details[] -->

> **治理追踪**：{治理建议}

---

### 问题三：白屏 — {标题后缀}

white_screen: dom_empty 日均从基线 {BASE_DAILY} {微升/下降}至当前 {CURR_DAILY}（{CHANGE}%），{趋势描述}。{描述主要页面和错误消息}

> **治理追踪**：{治理建议}

---

### 问题四：JS 运行时错误 — {标题后缀}

| 类型 | 基线/天 | 当前/天 | 变化 |
|------|--------|---------|------|
| script_error: vue_error | {BASE_DAILY} | {CURR_DAILY} | {CHANGE}% {箭头} |
| script_error: unhandled_rejection | ... | ... | ... |
| script_error: js_runtime_error | ... | ... | ... |

高频 JS 错误（含环比与建议）：

| 消息 | 基线/天 | 当前/天 | 变化 | 优先级 | 建议 |
|------|--------|---------|------|--------|------|
| {display} | {base_daily} | {curr_daily} | {change_pct}% | {priority} | {recommendation} |

<!-- 数据来源：issues.js_runtime.details[] -->

> **治理追踪**：{治理建议}

---

### 问题五：SSR 错误 — {标题后缀}

| 类型 | 基线/天 | 当前/天 | 变化 |
|------|--------|---------|------|
| ssr_error: ssr_white_screen | {BASE_DAILY} | {CURR_DAILY} | {CHANGE}% {箭头} |
| ssr_error: vue_ssr_error | ... | ... | ... |

{量级评估和关注建议}

---

### 问题六：业务自定义错误

custom_error: update_failed (PUBLISH)：当前 {CURR_COUNT} 次（日均 {CURR_DAILY}），基线 {BASE_COUNT} 次（日均 {BASE_DAILY}），日均**{上升/下降} {CHANGE}%**。{影响说明}

---

### 按应用维度汇总

| 应用 | 基线总量 | 基线/天 | 当前总量 | 当前/天 | 日均变化 |
|------|---------|---------|---------|---------|---------|
| search-frontend | {BASE_TOTAL} | {BASE_DAILY} | {CURR_TOTAL} | {CURR_DAILY} | **{CHANGE}%** {箭头} |
| homepage-frontend | ... | ... | ... | ... | ... |
| product-editor-frontend | ... | ... | ... | ... | ... |

{一句话总结各应用变化}

---

### 优先治理建议

> 类型级见 `governance[]`；具体错误见上文「需优先处理的具体错误」表。

1. **{治理项}**（{P0/P1/P2}）：{指标名} 日均 {CHANGE}%，{具体行动建议}；关联错误：{related_errors 摘要}
2. ...
