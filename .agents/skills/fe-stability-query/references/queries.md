# SQL 查询模板

本文件由 `fe-stability-query` 读取，将占位符替换为实际日期与范围后生成可执行 SQL。每条 SQL 同时覆盖 CURR 和 BASE，并在结果中返回 `period` 字段；下游不得再通过 query id 区分周期。

表名：`icbu_de.visable_fe_full_monitoring_data_v1`

## 变量

| 变量 | 说明 |
|---|---|
| `{CURR_START}` / `{CURR_END}` | 当前周期起止（yyyyMMdd） |
| `{BASE_START}` / `{BASE_END}` | 基线周期起止（yyyyMMdd） |
| `{CURR_DAYS}` / `{BASE_DAYS}` | 周期天数 |
| `{APP_FILTER}` | 总体为空；项目范围为 `AND app_name = '{APP}'` |

CURR 与 BASE 必须为不重叠区间。若用户指定了重叠区间，查询计划必须先阻塞并要求重新指定。

## 统一范围与周期标识

每条查询都使用以下逻辑：

```sql
CASE
  WHEN ds BETWEEN '{CURR_START}' AND '{CURR_END}' THEN 'CURR'
  WHEN ds BETWEEN '{BASE_START}' AND '{BASE_END}' THEN 'BASE'
END AS period
```

基础过滤条件：

```sql
WHERE (ds BETWEEN '{CURR_START}' AND '{CURR_END}'
    OR ds BETWEEN '{BASE_START}' AND '{BASE_END}')
  AND env = 'production'
  AND event_type != 'api_slow'
  AND level = 'error'
  {APP_FILTER}
```

所有合并查询都必须保留 `period`。项目范围只替换 `{APP_FILTER}`，不得展开其他项目。

## Group A：总量与日均

### A：当前/基线每日总量（1 条）

```sql
SELECT
  CASE
    WHEN ds BETWEEN '{CURR_START}' AND '{CURR_END}' THEN 'CURR'
    WHEN ds BETWEEN '{BASE_START}' AND '{BASE_END}' THEN 'BASE'
  END AS period,
  ds,
  COUNT(*) AS cnt
FROM icbu_de.visable_fe_full_monitoring_data_v1
WHERE (ds BETWEEN '{CURR_START}' AND '{CURR_END}'
    OR ds BETWEEN '{BASE_START}' AND '{BASE_END}')
  AND env = 'production'
  AND event_type != 'api_slow'
  AND level = 'error'
  {APP_FILTER}
GROUP BY period, ds
ORDER BY period, ds
```

## Group B：类型分布

### B：当前/基线 event_type + error_type 分布（1 条）

```sql
SELECT
  CASE
    WHEN ds BETWEEN '{CURR_START}' AND '{CURR_END}' THEN 'CURR'
    WHEN ds BETWEEN '{BASE_START}' AND '{BASE_END}' THEN 'BASE'
  END AS period,
  event_type,
  error_type,
  COUNT(*) AS cnt
FROM icbu_de.visable_fe_full_monitoring_data_v1
WHERE (ds BETWEEN '{CURR_START}' AND '{CURR_END}'
    OR ds BETWEEN '{BASE_START}' AND '{BASE_END}')
  AND env = 'production'
  AND event_type != 'api_slow'
  AND level = 'error'
  {APP_FILTER}
GROUP BY period, event_type, error_type
ORDER BY period, cnt DESC
```

## Group C：明细分析

以下查询均同时返回 CURR 和 BASE。所有 TOP N 必须按 `period` 分区，不能对两个周期共用一个全局 LIMIT。

### C1：资源加载失败 TOP 10

```sql
WITH grouped AS (
  SELECT
    CASE WHEN ds BETWEEN '{CURR_START}' AND '{CURR_END}' THEN 'CURR'
         WHEN ds BETWEEN '{BASE_START}' AND '{BASE_END}' THEN 'BASE' END AS period,
    resource_url,
    COUNT(*) AS cnt
  FROM icbu_de.visable_fe_full_monitoring_data_v1
  WHERE (ds BETWEEN '{CURR_START}' AND '{CURR_END}' OR ds BETWEEN '{BASE_START}' AND '{BASE_END}')
    AND env = 'production' AND event_type = 'script_error'
    AND error_type = 'resource_load_failed' AND level = 'error'
    {APP_FILTER}
  GROUP BY period, resource_url
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY period ORDER BY cnt DESC) AS rn
  FROM grouped
)
SELECT period, resource_url, cnt
FROM ranked
WHERE rn <= 10
ORDER BY period, cnt DESC
```

### C2：API 错误 TOP 15

```sql
WITH grouped AS (
  SELECT
    CASE WHEN ds BETWEEN '{CURR_START}' AND '{CURR_END}' THEN 'CURR'
         WHEN ds BETWEEN '{BASE_START}' AND '{BASE_END}' THEN 'BASE' END AS period,
    message,
    COUNT(*) AS cnt
  FROM icbu_de.visable_fe_full_monitoring_data_v1
  WHERE (ds BETWEEN '{CURR_START}' AND '{CURR_END}' OR ds BETWEEN '{BASE_START}' AND '{BASE_END}')
    AND env = 'production' AND event_type = 'api_error' AND level = 'error'
    {APP_FILTER}
  GROUP BY period, message
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY period ORDER BY cnt DESC) AS rn
  FROM grouped
)
SELECT period, message, cnt
FROM ranked
WHERE rn <= 15
ORDER BY period, cnt DESC
```

### C3：脚本错误消息 TOP 15

```sql
WITH grouped AS (
  SELECT
    CASE WHEN ds BETWEEN '{CURR_START}' AND '{CURR_END}' THEN 'CURR'
         WHEN ds BETWEEN '{BASE_START}' AND '{BASE_END}' THEN 'BASE' END AS period,
    message,
    COUNT(*) AS cnt
  FROM icbu_de.visable_fe_full_monitoring_data_v1
  WHERE (ds BETWEEN '{CURR_START}' AND '{CURR_END}' OR ds BETWEEN '{BASE_START}' AND '{BASE_END}')
    AND env = 'production' AND event_type = 'script_error'
    AND error_type != 'resource_load_failed' AND level = 'error'
    {APP_FILTER}
  GROUP BY period, message
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY period ORDER BY cnt DESC) AS rn
  FROM grouped
)
SELECT period, message, cnt
FROM ranked
WHERE rn <= 15
ORDER BY period, cnt DESC
```

### C4：白屏消息

```sql
SELECT
  CASE WHEN ds BETWEEN '{CURR_START}' AND '{CURR_END}' THEN 'CURR'
       WHEN ds BETWEEN '{BASE_START}' AND '{BASE_END}' THEN 'BASE' END AS period,
  message,
  COUNT(*) AS cnt
FROM icbu_de.visable_fe_full_monitoring_data_v1
WHERE (ds BETWEEN '{CURR_START}' AND '{CURR_END}' OR ds BETWEEN '{BASE_START}' AND '{BASE_END}')
  AND env = 'production' AND event_type = 'white_screen' AND level = 'error'
  {APP_FILTER}
GROUP BY period, message
ORDER BY period, cnt DESC
```

### C6：白屏 page 分布（必选）

```sql
SELECT
  CASE WHEN ds BETWEEN '{CURR_START}' AND '{CURR_END}' THEN 'CURR'
       WHEN ds BETWEEN '{BASE_START}' AND '{BASE_END}' THEN 'BASE' END AS period,
  page_id,
  ds,
  COUNT(*) AS cnt
FROM icbu_de.visable_fe_full_monitoring_data_v1
WHERE (ds BETWEEN '{CURR_START}' AND '{CURR_END}' OR ds BETWEEN '{BASE_START}' AND '{BASE_END}')
  AND env = 'production' AND event_type = 'white_screen' AND level = 'error'
  {APP_FILTER}
GROUP BY period, page_id, ds
ORDER BY period, cnt DESC
```

### C5：SSR / Component / Custom 错误

```sql
SELECT
  CASE WHEN ds BETWEEN '{CURR_START}' AND '{CURR_END}' THEN 'CURR'
       WHEN ds BETWEEN '{BASE_START}' AND '{BASE_END}' THEN 'BASE' END AS period,
  event_type,
  error_type,
  message,
  COUNT(*) AS cnt
FROM icbu_de.visable_fe_full_monitoring_data_v1
WHERE (ds BETWEEN '{CURR_START}' AND '{CURR_END}' OR ds BETWEEN '{BASE_START}' AND '{BASE_END}')
  AND env = 'production'
  AND event_type IN ('ssr_error', 'component_error', 'custom_error')
  AND level = 'error'
  {APP_FILTER}
GROUP BY period, event_type, error_type, message
ORDER BY period, cnt DESC
```

## 查询批次

| 批次 | 查询 ID | 说明 |
|---|---|---|
| 第一轮（并行） | A, B | 同时返回 CURR/BASE 的总量与类型分布（2 条） |
| 第四轮（必做，并行） | C1–C6 | 同时返回 CURR/BASE 的具体 message/url 与白屏 page 明细（6 条） |

总计：标准报告 8 条 SQL（A、B、C1–C6）。不再查询慢请求。结果必须带 `period`，不得通过拆分 query id 表示周期。
