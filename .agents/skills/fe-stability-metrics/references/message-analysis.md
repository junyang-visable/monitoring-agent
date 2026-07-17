# 具体错误信息分析

在 event_type 量级分析之外，必须对 **message / resource_url 粒度** 做 CURR vs BASE 对比，识别突增、新出现错误，并给出可执行建议。

## 数据来源

Group C 查询结果，query id 格式：

```
{C_ID}
```

示例：`C1`、`C2`。每条结果必须含 `period` 和 `app_name` 列。

| E ID | 字段 key | category |
|------|----------|----------|
| C1 | resource_url | resource_load_failed |
| C2 | message | api_error |
| C3 | message | js_runtime |
| C4 | message | white_screen |
| C5 | message（+ event_type） | ssr / custom / component |
| C6 | page_id | white_screen page 分布 |

C6 为必选，用于白屏 page 分布，写入对应 `ErrorDetailItem.extra.page_breakdown`。慢请求不再进入稳定性分析查询。

## 合并规则

对同一 `app_name + category + key`（全域范围没有 `app_name` 时使用空值） ：

1. 从同一条 E 查询结果中读取 `period=CURR` 的 `count`
2. 从同一条 E 查询结果中读取 `period=BASE` 的 `count`（无则 0）
3. 计算 `base_rate` / `curr_rate` / `rate_unit` / `change_pct` / `trend`（公式同 metrics-rules）
4. 生成 `display`：URL 取 path 末段或域名；message 取前 120 字

## 突增识别（is_spike）

满足**任一**条件则 `is_spike = true`，写入 `spike_reason`：

| 类型 | 条件 |
|------|------|
| 环比突增 | `change_pct >= 100%` 且日等价值 `curr_rate × rate_unit_factor >= 10` |
| 新出现 | `base_count = 0` 且日等价值 `curr_rate × rate_unit_factor >= 5` |
| 量级突增 | 日等价值 `curr_rate × rate_unit_factor >= 100` 且 `change_pct >= 50%` |
| 绝对量大且恶化 | 日等价值 `curr_rate × rate_unit_factor >= 500` 且 `change_pct >= 20%` |

`is_new = (base_count == 0 && curr_count > 0)`

## 单条错误优先级（priority）

在 metrics-rules 类型级 P0–P2 基础上，对单条错误：

| 优先级 | 条件 |
|--------|------|
| **P0** | `is_spike` 且日等价值 >= 100；或 API 403/401/5xx 且日等价值 >= 20；或白屏 dom_empty 相关且日等价值 >= 10 |
| **P1** | `is_spike` 且日等价值 >= 10；或日等价值 >= 50 且 `change_pct >= 50%` |
| **P2** | 其余有 CURR 数据的条目 |

## 影响力排序（impact_score）

用于 `priority_actions` 排序：

```
impact_score = 日等价值 × (1 + max(change_pct, 0) / 100)
其中 `rate_unit_factor=1`（day）或 `24`（hour）；若 priority = P0 → × 3
若 priority = P1 → × 2
若 is_new → × 1.5
```

取 TOP 15 写入 `priority_actions`，每条必须含 `recommendation`。

## 建议生成（recommendation）

按 key/message 模式匹配（写入 `root_cause_hint` + `recommendation`）：

| 模式 | root_cause_hint | recommendation |
|------|-----------------|----------------|
| `*.js` / `chunk` / CloudFront CDN | CDN chunk 加载失败 | 核对部署版本与 CDN 缓存；检查 chunk 文件是否缺失；回滚或补发静态资源 |
| 第三方域名（hubspot/bing/hotjar/facebook 等） | 第三方脚本失败 | 评估是否必需；改为 async/defer；失败降级不影响主流程 |
| HTTP 403 / 401 | 权限/登录态 | 检查接口鉴权、Cookie、会话过期；排查未登录访问 |
| HTTP 405 | 方法不匹配 | 核对请求 method 与后端约定 |
| HTTP 400 / 422 | 参数/校验 | 核对入参变更、发布窗口内 API 契约 |
| timeout / network | 网络或超时 | 检查依赖服务 SLA、超时配置、重试策略 |
| dom_empty / white_screen | 渲染或关键资源失败 | 关联同 app 的 chunk/API 错误；查 SSR 日志与白屏采样点 |
| vue_error / unhandled_rejection | 运行时异常 | 定位堆栈对应组件/版本；查是否与 chunk 失败同源 |
| update_failed / PUBLISH | 业务发布失败 | 查后端 publish 接口与权限；对照产品编辑器发布链路 |

无法匹配时：`recommendation` 写「结合 message 与发布窗口排查，确认是否为新上线引入」。

## 输出字段

每条写入 `ErrorDetailItem`（见 analysis-schema.md），并汇总：

- `issues.{category}.details[]` — 该类别下全部明细（按 impact_score 降序，最多 20 条/类）
- 项目 JSON 的 `issues.{category}.details[]` — 写入对应应用的独立明细
- `priority_actions[]` — 全域 TOP 15 待处理项
- `spike_alerts[]` — 全部 `is_spike=true`（最多 30 条）

## 报告解读要求

`global.summary_insight` 必须提及：

1. 突增最严重的 1–2 条具体错误（非仅类型名）
2. `priority_actions` 中 P0 数量与首要处理项

各 `issues.*.insight` 必须引用该类别 `details` 中 TOP 3 的具体 key/message。
