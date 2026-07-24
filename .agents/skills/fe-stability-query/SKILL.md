---
name: fe-stability-query
description: 接收已解析的项目范围与时间意图，生成包含查询参数、缓存标识及 ODPS SQL 批次的前端稳定性查询计划。
---

# 查询计划生成

## 职责边界

本 skill 接收编排器已解析的非空 `app_names`、时间意图与可选粒度配置，生成一个完整查询计划：

1. 构建 CURR / BASE 查询参数与缓存标识，并校验周期不重叠
2. 读取 [references/batch-queries.md](references/batch-queries.md) 中的 SQL 模板
3. 按分析范围生成 round1 基础 SQL 与 round4 明细 SQL；每条 SQL 同时覆盖 CURR/BASE 并返回 `period`
4. 返回可直接执行的分批查询计划

**不** 负责项目名称映射、执行 ODPS 查询、指标计算或报告生成。项目名称必须由编排器预先映射为标准 `app_name`。

---

## Step 1：构建查询计划参数

### 粒度选择（强制）

`time_granularity=auto` 或上游未指定粒度时，必须根据时间意图选择实际粒度：

- 只有明确的小时意图使用 `hour`：`last_<N>h`、过去 N 小时、最近 N 小时，例如 `last_2h`、`last_24h`。
- 所有其他自然日意图使用 `day`：`today`、`yesterday`、`last_<N>d`、今天、昨天、最近 N 天、自然周，以及不包含具体时分秒的日期范围。
- 不得根据区间恰好等于 24 小时而推断 `hour`。上游若为自然日意图传入 `hour`，必须改为 `day`，避免“昨天”被查询成滚动 24 小时。

`time_granularity=day` 时，根据用户的表述确定对比周期（**今天** = 执行 Phase 1 当日的系统日期，**禁止**沿用本会话或历史跑批中的日期）：

| 用户说法 | CURR | BASE |
|---------|------|------|
| 默认（不指定） | 今天 | 昨天 |
| `today` / 今天 | 今天 | 昨天 |
| `yesterday` / 昨天 | 昨天 | 前天 |
| **过去一周 / 最近一周 / 过去 7 天 / 最近 7 天** | 今天起向前共 7 天（含今天） | 紧邻的前 7 天 |
| **上个自然周 / 上一自然周 / 自然周 / 上个完整自然周** | 上个自然周 周一–周日 | 上上个自然周 周一–周日 |
| 上周 / 上一周 | 上个自然周 周一–周日 | 上上个自然周 周一–周日 |
| 最近 N 天 | 今天起向前共 N 天（含今天） | 紧邻的前 N 天 |
| 本周 / 本周至今 | 本周周一–今天 | 上周同跨度 |
| 指定具体日期 | 用户给定范围 | 用户给定范围 |

> **默认规则**：「过去一周」= **滚动 7 个自然日**（今天与此前 6 天），不是自然周。仅当用户**明确提到「自然周」**（或「上周/上个自然周」）时才按周一–周日计算。

**滚动范围规则**：所有“默认”“过去/最近一周”“最近 N 天”均包含今天。对于 N 天范围：`CURR_END = TODAY`，`CURR_START = TODAY - (N - 1) 天`；BASE 为紧邻 CURR 之前、等长的 N 天。

**自然周规则**：周一为第一天，周日为最后一天。

示例：今天是周二 6/16 → 上周 = 6/8（Mon）- 6/14（Sun），上上周 = 6/1（Mon）- 6/7（Sun）。

**周报标记**：用户明确说「周报 / 稳定性周报 / 上周周报」等 → `IS_WEEKLY_REPORT = true`；否则 `false`。

**指定具体日期时的 BASE 规则**：

- 用户同时给出 CURR 和 BASE → 按用户指定
- 用户只给出 CURR 范围 → BASE 取与 CURR **等长、紧邻的前一段**

天数：`DAYS = 结束日 - 起始日 + 1`（yyyyMMdd 解析为日期后计算）。
格式化：`20260610` → `6/10`。

| 变量 | 格式 | 说明 |
|------|------|------|
| `{CURR_START}` / `{CURR_END}` | yyyyMMdd | 当前周期起止 |
| `{BASE_START}` / `{BASE_END}` | yyyyMMdd | 基线周期起止 |
| `{CURR_DAYS}` / `{BASE_DAYS}` | 整数 | 周期天数 |
| `{CURR_START_FMT}` 等 | M/D | 人类可读日期 |
| `{IS_WEEKLY_REPORT}` | boolean | 是否周报 |
| `{TODAY}` | yyyyMMdd | 系统当天 |
| `{COMPARISON_ID}` | string | 按 schema 规则预计算 |
| `{STABILITY_WINDOW_DAYS}` | integer | 最近仍可能回补的数据日数量，默认 `1` |
| `{STABLE_THROUGH}` | yyyyMMdd | 已进入稳定窗口的数据截止日 |
| `{INCLUDES_UNSTABLE_DATA}` | boolean | CURR 或 BASE 是否覆盖稳定窗口内的数据 |
| `{IS_PROVISIONAL}` | boolean | 是否应标记为临时结果 |
| `{DATA_AS_OF}` | ISO8601 | 本次查询计划生成时间 |

数据稳定窗口规则：

- `STABILITY_WINDOW_DAYS = 1`；最近一个已完成自然日仍可能有迟到或回补数据。
- `UNSTABLE_START = TODAY - STABILITY_WINDOW_DAYS`。
- `STABLE_THROUGH = UNSTABLE_START - 1 day`。
- `INCLUDES_UNSTABLE_DATA`：CURR 或 BASE 的任一日期大于等于 `UNSTABLE_START`。
- `IS_PROVISIONAL = INCLUDES_UNSTABLE_DATA`。
- 查询范围覆盖不稳定窗口时必须重新查数，且不得命中缓存。

### 小时粒度

只有明确的小时意图（例如 `last_2h`、`last_24h`、过去 N 小时）可以进入小时模式。`time_granularity=hour` 时必须同时传入 `partition_timezone` 和 `time_range`。`time_range` 表达公共时间意图；本 skill 独立生成 SDK 的整点边界，不得要求 Datadog 或 Sentry同步取整。将 UTC 时间范围转换为分区时区后处理：

1. 将 `CURR_END_AT` 向下取整到整点；当前未完成小时永不查询。
2. `last_<N>h` 的 `CURR_START_AT = CURR_END_AT - N 小时`；BASE 是紧邻且等长的前 N 小时。
3. 两个周期均为半开区间 `[start, end)`；跨日通过 `ds` 与零填充的 `hh` 共同过滤。
4. `stability_window_hours`（默认 1）内的已完成小时仍视为不稳定；任一周期覆盖它则 `includes_unstable_data=true`。
5. 小时模式必须输出 `CURR_START_AT`、`CURR_END_AT`、`BASE_START_AT`、`BASE_END_AT`（ISO8601）、`CURR_HOURS`、`BASE_HOURS`、`partition_timezone` 和 `time_granularity=hour`。`comparison_id` 使用这四个整点时间戳，不能只使用日期。

---

## 查询计划参数纪律（强制）

1. **每次 Phase 1 必须重新计算**，不得引用会话记忆、不得假设「与上次相同」。
2. **今天**取系统当前日期（非用户消息时间戳、非上次跑批日期）。
3. 参数构建完成后输出计划摘要。日模式格式：
   > 本次分析：今天 {TODAY}；CURR {CURR_START}–{CURR_END}（{CURR_DAYS} 天）vs BASE {BASE_START}–{BASE_END}（{BASE_DAYS} 天）；comparison_id=`{COMPARISON_ID}`；includes_unstable_data={INCLUDES_UNSTABLE_DATA}；is_provisional={IS_PROVISIONAL}
   小时模式格式：
   > 本次分析：分区时区 {PARTITION_TIMEZONE}；CURR [{CURR_START_AT}, {CURR_END_AT})（{CURR_HOURS} 小时）vs BASE [{BASE_START_AT}, {BASE_END_AT})（{BASE_HOURS} 小时）；comparison_id=`{COMPARISON_ID}`；includes_unstable_data={INCLUDES_UNSTABLE_DATA}；is_provisional={IS_PROVISIONAL}
4. 将 `COMPARISON_ID`、CURR/BASE 完整区间、排序后的 `app_names`、`INCLUDES_UNSTABLE_DATA`、`IS_PROVISIONAL`、粒度及稳定窗口参数、`DATA_AS_OF` 一并交给编排器，供 [cache-policy.md](../fe-stability-analysis/references/cache-policy.md) 计算 `cache_key`。
5. `comparison_id` 规则见 [fe-stability-metrics/references/analysis-schema.md](../fe-stability-metrics/references/analysis-schema.md)。

---

## Step 2：生成合并基础查询 SQL

使用编排器传入的去重、排序后的标准 `app_names`。用户未指定项目时，由上游从 `app-mappings.md` 解析全部“启用”项目后再传入；本 skill 不猜测或补全项目列表。`app_names` 缺失或为空时阻塞返回。

只读取 [references/batch-queries.md](references/batch-queries.md)，用 Step 1 的分区谓词替换模板中的占位符。每个逻辑查询只生成一条 SQL，同时查询 CURR/BASE。

**替换规则**：

- 所有查询：替换 `{CURR_PARTITION_PREDICATE}` 与 `{BASE_PARTITION_PREDICATE}`。
  - 日模式：`ds BETWEEN '{START_DS}' AND '{END_DS}'`
  - 小时模式：`((ds > '{START_DS}' OR (ds = '{START_DS}' AND hh >= '{START_HH}')) AND (ds < '{END_DS}' OR (ds = '{END_DS}' AND hh < '{END_HH}')))`
- 所有查询结果：必须包含 `period`，值只能为 `CURR` 或 `BASE`

- 将按字典序去重后的标准应用名安全替换到 `{APP_LIST}`。结果必须含 `app_name`，不得在本 skill 外再拼接项目维度。

**第一轮（2 条，可并行）**：

| ID | 说明 |
|----|------|
| A | 当前/基线总量；日模式按 `period, ds`，小时模式按 `period, ds, hh` 分组 |
| B | 当前/基线 event_type 分布，按 `period, event_type, error_type` 分组 |

## Step 3：生成合并明细查询 SQL

每次生成以下 round4（6 类，各 1 条，同时返回 CURR/BASE），范围与 Step 2 保持一致：

| C ID | 类别 |
|------|------|
| C1 | resource_load_failed |
| C2 | api_error |
| C3 | js_runtime |
| C4 | white_screen message |
| C5 | ssr / component / custom |
| C6 | white_screen page 分布 |

对每个类别生成 1 条 SQL，**query id 命名**：

```
{C_ID}
```

示例：`C1`、`C2`。项目范围统一通过 `{APP_LIST}` 限定目标应用，并以 `app_name, period` 为聚合和 Top N 分区维度。

PERIOD：`CURR` 用 `{CURR_PARTITION_PREDICATE}`，`BASE` 用 `{BASE_PARTITION_PREDICATE}`。

round1 与 round4 必须在本次调用中一起写入查询计划；每条查询的 CURR/BASE 结果通过 `period` 区分。

---

## Step 4：输出约定

向编排器返回一个完整查询计划：

1. **计划摘要**：查询范围 + `当前 6/10–6/10（1 天）vs 基线 6/9–6/9（1 天）` + `period=CURR|BASE`
2. **计划参数**：`app_names`、全部日期变量、`IS_WEEKLY_REPORT`、`COMPARISON_ID`、`INCLUDES_UNSTABLE_DATA`、`IS_PROVISIONAL`
3. **SQL 批次列表**，每条包含：
   - `id`：如 `A`、`C1`
   - `round`：1 或 4；每个 id 只出现一次
   - `sql`：替换后的完整 SQL 字符串

示例结构：

```yaml
app_names: ["search-frontend", "product-editor-frontend"]
date_vars:
  time_granularity: hour
  partition_timezone: "GMT+1"
  CURR_START_AT: "2026-06-10T08:00:00+01:00"
  CURR_END_AT: "2026-06-11T08:00:00+01:00"
  BASE_START_AT: "2026-06-09T08:00:00+01:00"
  BASE_END_AT: "2026-06-10T08:00:00+01:00"
  CURR_HOURS: 24
  BASE_HOURS: 24
  # ...
is_weekly_report: false
comparison_id: "20260610_vs_20260609"
stability_window_days: 1
stable_through: "20260608"
includes_unstable_data: true
is_provisional: true
data_as_of: "2026-06-10T09:30:00Z"
queries:
  round1:
    - id: A
      sql: "SELECT ds, COUNT(*) ..."
    - id: B
      sql: "SELECT period, event_type, error_type, COUNT(*) ..."
  round4:
    - id: C1
      sql: "SELECT period, resource_url, COUNT(*) ..."
```

**本 skill 执行完毕，返回控制权给编排器。**

## 批量项目模式

无论 `app_names` 包含一个、多个或全部启用项目，均固定生成 A、B、C1–C6 共 8 条 SQL。A/B 按 `app_name` 聚合；C1–C6 按 `app_name, period` 计算各项目独立 Top N。

---

## 常见陷阱

- **自然周边界**：「上周」指完整自然周，不是最近 7 天
- **跨月天数**：必须用日期对象相减，不能字符串相减
- **Group C 分区**：每条 C 模板同时使用 CURR 与 BASE 分区谓词，不得生成单周期 SQL
- **MissingPartitionSpec**：生成的 SQL 必须包含 `ds` 分区条件；小时模式还必须包含 `hh` 边界
