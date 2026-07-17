# 批量项目 SQL 查询模板

本文件是唯一 SQL 模板。`{APP_LIST}` 必须由编排器已解析、去重的标准 `app_name` 安全替换为 SQL 字符串列表。`{CURR_PARTITION_PREDICATE}` 与 `{BASE_PARTITION_PREDICATE}` 必须分别替换为完整且可分区裁剪的 `ds`/`hh` 谓词。所有查询覆盖 CURR/BASE，返回 `app_name` 和 `period`，并只过滤选中的项目。

## A：每日总量

```sql
SELECT app_name,
  CASE WHEN {CURR_PARTITION_PREDICATE} THEN 'CURR' ELSE 'BASE' END AS period,
  ds, hh, COUNT(*) AS cnt
FROM icbu_de.visable_fe_full_monitoring_data_v1
WHERE ({CURR_PARTITION_PREDICATE} OR {BASE_PARTITION_PREDICATE})
  AND env = 'production' AND event_type != 'api_slow' AND level = 'error'
  AND app_name IN ({APP_LIST})
GROUP BY app_name, period, ds, hh
ORDER BY app_name, period, ds, hh
```

## B：类型分布

```sql
SELECT app_name,
  CASE WHEN {CURR_PARTITION_PREDICATE} THEN 'CURR' ELSE 'BASE' END AS period,
  event_type, error_type, COUNT(*) AS cnt
FROM icbu_de.visable_fe_full_monitoring_data_v1
WHERE ({CURR_PARTITION_PREDICATE} OR {BASE_PARTITION_PREDICATE})
  AND env = 'production' AND event_type != 'api_slow' AND level = 'error'
  AND app_name IN ({APP_LIST})
GROUP BY app_name, period, event_type, error_type
ORDER BY app_name, period, cnt DESC
```

## C1：资源加载失败 TOP 10

```sql
WITH grouped AS (
  SELECT app_name, CASE WHEN {CURR_PARTITION_PREDICATE} THEN 'CURR' ELSE 'BASE' END AS period,
    resource_url, COUNT(*) AS cnt
  FROM icbu_de.visable_fe_full_monitoring_data_v1
  WHERE ({CURR_PARTITION_PREDICATE} OR {BASE_PARTITION_PREDICATE})
    AND env = 'production' AND event_type = 'script_error' AND error_type = 'resource_load_failed' AND level = 'error'
    AND app_name IN ({APP_LIST})
  GROUP BY app_name, period, resource_url
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY app_name, period ORDER BY cnt DESC) AS rn FROM grouped
)
SELECT app_name, period, resource_url, cnt FROM ranked WHERE rn <= 10 ORDER BY app_name, period, cnt DESC
```

## C2：API 错误 TOP 15

```sql
WITH grouped AS (
  SELECT app_name, CASE WHEN {CURR_PARTITION_PREDICATE} THEN 'CURR' ELSE 'BASE' END AS period,
    message, COUNT(*) AS cnt
  FROM icbu_de.visable_fe_full_monitoring_data_v1
  WHERE ({CURR_PARTITION_PREDICATE} OR {BASE_PARTITION_PREDICATE})
    AND env = 'production' AND event_type = 'api_error' AND level = 'error' AND app_name IN ({APP_LIST})
  GROUP BY app_name, period, message
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY app_name, period ORDER BY cnt DESC) AS rn FROM grouped
)
SELECT app_name, period, message, cnt FROM ranked WHERE rn <= 15 ORDER BY app_name, period, cnt DESC
```

## C3：脚本错误 TOP 15

```sql
WITH grouped AS (
  SELECT app_name, CASE WHEN {CURR_PARTITION_PREDICATE} THEN 'CURR' ELSE 'BASE' END AS period,
    message, COUNT(*) AS cnt
  FROM icbu_de.visable_fe_full_monitoring_data_v1
  WHERE ({CURR_PARTITION_PREDICATE} OR {BASE_PARTITION_PREDICATE})
    AND env = 'production' AND event_type = 'script_error' AND error_type != 'resource_load_failed' AND level = 'error'
    AND app_name IN ({APP_LIST})
  GROUP BY app_name, period, message
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY app_name, period ORDER BY cnt DESC) AS rn FROM grouped
)
SELECT app_name, period, message, cnt FROM ranked WHERE rn <= 15 ORDER BY app_name, period, cnt DESC
```

## C4：白屏消息 TOP 15

```sql
WITH grouped AS (
  SELECT app_name, CASE WHEN {CURR_PARTITION_PREDICATE} THEN 'CURR' ELSE 'BASE' END AS period,
    message, COUNT(*) AS cnt
  FROM icbu_de.visable_fe_full_monitoring_data_v1
  WHERE ({CURR_PARTITION_PREDICATE} OR {BASE_PARTITION_PREDICATE})
    AND env = 'production' AND event_type = 'white_screen' AND level = 'error' AND app_name IN ({APP_LIST})
  GROUP BY app_name, period, message
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY app_name, period ORDER BY cnt DESC) AS rn FROM grouped
)
SELECT app_name, period, message, cnt FROM ranked WHERE rn <= 15 ORDER BY app_name, period, cnt DESC
```

## C5：SSR / Component / Custom TOP 15

```sql
WITH grouped AS (
  SELECT app_name, CASE WHEN {CURR_PARTITION_PREDICATE} THEN 'CURR' ELSE 'BASE' END AS period,
    event_type, error_type, message, COUNT(*) AS cnt
  FROM icbu_de.visable_fe_full_monitoring_data_v1
  WHERE ({CURR_PARTITION_PREDICATE} OR {BASE_PARTITION_PREDICATE})
    AND env = 'production' AND event_type IN ('ssr_error', 'component_error', 'custom_error') AND level = 'error'
    AND app_name IN ({APP_LIST})
  GROUP BY app_name, period, event_type, error_type, message
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY app_name, period ORDER BY cnt DESC) AS rn FROM grouped
)
SELECT app_name, period, event_type, error_type, message, cnt FROM ranked WHERE rn <= 15 ORDER BY app_name, period, cnt DESC
```

## C6：白屏页面 TOP 15

```sql
WITH grouped AS (
  SELECT app_name, CASE WHEN {CURR_PARTITION_PREDICATE} THEN 'CURR' ELSE 'BASE' END AS period,
    page_id, COUNT(*) AS cnt
  FROM icbu_de.visable_fe_full_monitoring_data_v1
  WHERE ({CURR_PARTITION_PREDICATE} OR {BASE_PARTITION_PREDICATE})
    AND env = 'production' AND event_type = 'white_screen' AND level = 'error' AND app_name IN ({APP_LIST})
  GROUP BY app_name, period, page_id
), ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY app_name, period ORDER BY cnt DESC) AS rn FROM grouped
)
SELECT app_name, period, page_id, cnt FROM ranked WHERE rn <= 15 ORDER BY app_name, period, cnt DESC
```
