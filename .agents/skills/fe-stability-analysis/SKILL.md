---
name: fe-stability-analysis
description: 从 ODPS 查询前端稳定性数据并生成结构化分析结果；默认生成 Markdown 报告，也支持仅返回分析结果供监控编排消费。
version: 4.6.0
---

# 前端稳定性分析编排器

## 执行纪律（最高优先级）

你是**编排器**，不是通用分析 agent。收到稳定性相关请求时：

1. **按 Phase 1 → [缓存检查] → 2 → 3 → [4] 执行**；`output_mode=analysis_only` 时 Phase 4 不执行；缓存命中时跳过后续 Phase，Phase 1 每次必跑。
2. **只调用白名单子 skill**（见 [orchestration.md](references/orchestration.md)），**禁止**擅自调用其他任何 skill、MCP、子 agent。
3. **禁止绕过子 skill**：不得直接跑 `maxc`/shell SQL、不得手写报告、不得在编排器内自行算环比或写 `analysis.json`。
4. 每个 Phase 必须按对应子 skill 的定义完整执行，收到该 Phase 规定返回值后才能进入下一 Phase。

> 完整纪律与白名单见 [references/orchestration.md](references/orchestration.md) 的「编排器执行纪律」。

## 概述

本 skill 是编排入口，负责按顺序调用四个步骤：

```
fe-stability-analysis（编排器）
├── Phase 1: fe-stability-query             → 请求解析与完整查询计划
├── [缓存检查] cache-policy               → 含今天 / 无缓存 → 继续；否则返回历史结果
├── Phase 2: dataworks-dev-assistant      → 执行 SQL
├── Phase 3: fe-stability-metrics         → 分析 → analysis.json
└── Phase 4: fe-stability-report-writer   → `output_mode=report` 时渲染并审校一份 Markdown 报告
```

## 输出模式

| `output_mode` | 行为 | 适用场景 |
|---|---|---|
| `report`（默认） | 执行 Phase 1–4，输出 `analysis.json` 和唯一 Markdown 报告 | 直接请求稳定性分析或周报 |
| `analysis_only` | 执行 Phase 1–3，返回 `analysis.json` 与结构化摘要，不生成 Markdown 报告 | Monitoring Orchestrator 的 Stability SDK 信号 |

## 分析范围（必须先确定）

先读取 [references/app-mappings.md](references/app-mappings.md)，再从用户请求中解析项目：

1. 用户未提及任何项目 → 从映射表取全部“启用”项目，形成去重、排序后的 `app_names`。
2. 用户提供一个或多个名称且与映射表的 `app_name` 或别名精确匹配（英文忽略大小写）→ 形成去重、排序后的 `app_names`。单项目也必须使用单元素数组。
3. Monitoring Orchestrator 提供多个已解析的标准应用名 → 直接使用其 `app_names`。
4. 用户明显指定了项目、但未匹配映射表 → 停止并请用户提供标准 `app_name` 或先维护映射表；不得猜测项目。

将解析结果传给每个 Phase：

| 用户是否明确指定项目 | `app_names` | 查询与报告 |
|---|---|---|
| 否 | 映射表中全部启用项目 | 批量查询全部启用项目；是否生成 Markdown 仅由 `output_mode` 决定 |
| 是，且命中映射 | 指定项目的 `app_names[]` | 单项目与多项目均走同一批量查询；是否生成 Markdown 仅由 `output_mode` 决定 |

不得维护或使用代码内固定应用列表；新增项目仅更新 [references/app-mappings.md](references/app-mappings.md)。不得在同一次执行中生成总体和项目两种报告。

最终产出：

| 产物 | 说明 |
|------|------|
| `analysis-{scope_key}-{comparison_id}.json` | 结构化分析中间文件 |
| `frontend-stability-apps-{scope_key}-{comparison_id}.md` | 仅 `output_mode=report` 时生成的唯一 Markdown 分析报告 |

---

## 子 skill 调用规范

> 完整规则见 [references/orchestration.md](references/orchestration.md)

**仅允许调用以下五个子 skill**（不得增减、不得替换）：

| Phase | `{skill-name}` |
|-------|----------------|
| 1 | `fe-stability-query` |
| 2 | `dataworks-dev-assistant` |
| 3 | `fe-stability-metrics` |
| 4 | `fe-stability-report-writer` |
| 4 后处理 | `report-generator` |

调用白名单内子 skill 时：

1. 按 `{skill-name}` 直接调用对应子 skill，并按其定义执行（不得凭印象省略）
2. 子 skill 不可用或调用失败时，提示具体原因并**阻塞当前 Phase**，不得改用其他 skill 或直连 ODPS 兜底
3. **不得**在 Phase 之间插入额外 skill 调用

---

## Phase 1：fe-stability-query（请求解析与查询计划）

完成项目映射后，调用 **`fe-stability-query`**，将用户的时间范围意图、非空 `app_names` 及可选 `time_granularity`、`partition_timezone`、`stability_window_hours` 传入，一次性生成包含查询参数、缓存标识、round1 和 round4 SQL 的完整查询计划。

**强制**：每次请求必须基于**系统当天**重新生成查询计划，并输出计划摘要（含查询范围、对比周期、`comparison_id`、`includes_unstable_data`、`is_provisional`）。

**等待返回**：完整查询计划（查询范围、日期变量、`COMPARISON_ID`、`IS_WEEKLY_REPORT`、`INCLUDES_UNSTABLE_DATA`、`IS_PROVISIONAL`、round1 与 round4 SQL 批次；每条结果含 `period=CURR|BASE`）。

---

## 缓存检查（Phase 1「fe-stability-query」之后）

按 [references/cache-policy.md](references/cache-policy.md) 与 [orchestration.md](references/orchestration.md) 解析 `{OUTPUT_DIR}` 并检查；缓存所需文件由 `output_mode` 决定：

1. 若 `includes_unstable_data = true` → **继续 Phase 2**
2. 若当前模式所需缓存文件存在，且 `meta` 与 Phase 1 日期、范围及稳定窗口一致 → **直接返回缓存结果**，流程结束，注明「命中历史缓存」
3. 否则 → **继续 Phase 2**

---

## Phase 2：执行 SQL 查询

调用 **`dataworks-dev-assistant`**，按 Phase 1 查询计划中的 SQL 批次依次执行：

1. **第一轮（并行）**：round1（A、B；2 条）
2. **第四轮（必做）**：执行查询计划中已生成的 round4（C1/C2/C3/C4/C5/C6；6 条，每条含 CURR/BASE）。具体错误信息分析依赖此轮数据。

**等待所有查询结果返回后**，继续 Phase 3。

---

## Phase 3：数据分析

按 [orchestration.md](references/orchestration.md) 解析 `{OUTPUT_DIR}`。

调用 **`fe-stability-metrics`**，传入：

- Phase 1「fe-stability-query」输出的日期/小时变量、`time_granularity`、`partition_timezone`、`IS_WEEKLY_REPORT`、`app_names`
- Phase 2 全部查询结果
- `{OUTPUT_DIR}`

**等待返回**：`analysis.json` 路径 + `comparison_id` + 摘要（含 P0 数量、突增条数、首要处理项）。

若 `output_mode=analysis_only`：到此结束，返回 `analysis.json` 路径、`comparison_id`、范围、临时结果标记和摘要；**不得调用** `fe-stability-report-writer` 或 `report-generator`。

---

## Phase 4：报告渲染

仅 `output_mode=report` 时执行。本模式未显式提供时默认为 `report`。

调用 **`fe-stability-report-writer`**，传入：

- Phase 3 的 `analysis.json` 路径 + `app_names`
- `{OUTPUT_DIR}`

`fe-stability-report-writer` 必须先按模板生成事实完整的 Markdown 草稿；若 `report-generator` 可用，再调用它做文档审校与表达优化。`report-generator` 不得重新计算指标、修改数值、删除必需章节或改变报告范围。

**等待返回**唯一 Markdown 报告的绝对路径，向用户展示最终审校后的内容摘要。

---

## 编排原则

- Phase 1 **每次必跑**；Phase 2–3 按 [cache-policy.md](references/cache-policy.md) 决定是否跳过；Phase 4 仅 `output_mode=report` 时执行
- **覆盖稳定窗口的数据必须重查**；不覆盖且缓存有效时可返回历史结果
- **仅调用白名单五个子 skill**；禁止调用 `fe-stability-generate`、`odps-skill`、`maxcompute-cli-guidance-ncs` 等任何其他 skill
- SQL 模板仅由 `fe-stability-query` 维护；编排器与 `dataworks-dev-assistant` **不得**自行编写或修改 SQL 模板
- 查询执行仅通过 `dataworks-dev-assistant`（Phase 2）；编排器 **不得** 直接执行 `maxc` 或 shell 查数
- 指标计算仅由 `fe-stability-metrics` 完成；`fe-stability-report-writer` 禁止重算
- 子 skill 调用纪律、输出目录、产物命名均遵循 [orchestration.md](references/orchestration.md)

---

## 数据过滤规范

所有 SQL 已内嵌以下过滤条件（由 `fe-stability-query` 模板保证）：

```sql
env = 'production'
AND event_type != 'api_slow'
AND level = 'error'
```

---

## 关键表信息

```
icbu_de.visable_fe_full_monitoring_data_v1
├── 分区: ds (yyyyMMdd), hh (00-23)
├── event_type: script_error | api_error | white_screen | ssr_error | custom_error | component_error | api_slow
├── error_type: resource_load_failed | vue_error | unhandled_rejection | js_runtime_error |
│              unknown | network | client | timeout | server |
│              dom_empty | dom_missing | sample_points | custom_white_screen |
│              ssr_white_screen | vue_ssr_error | update_failed | render_error | white_screen
├── level: error | warning | info
├── env: production | staging
└── app_name: 项目标准名见 references/app-mappings.md
```

---

## 文件位置

| 资源 | 说明 |
|------|------|
| [references/cache-policy.md](references/cache-policy.md) | 含今天重查 / 历史缓存命中规则 |
| [references/orchestration.md](references/orchestration.md) | 子 skill 调用纪律、输出目录、产物命名 |
| [references/app-mappings.md](references/app-mappings.md) | 项目标准名、展示名称与用户别名 |
| `fe-stability-query` | SQL 模板见 `references/batch-queries.md` |
| `fe-stability-metrics` | Schema 见 `{skill}/references/analysis-schema.md` |
| `fe-stability-report-writer` | 模板见 `{skill}/references/template-*.md` |
