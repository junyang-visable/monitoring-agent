# 结果缓存策略

编排器在 **Phase 1「fe-stability-query」完成后**、进入 Phase 2 前执行本检查。缓存只保存索引，绝不复制总览或项目 JSON。

## 缓存索引

唯一缓存索引文件为 `{CACHE_DIR}/index.json`；`{CACHE_DIR}` 默认是 `{git_root}/artifacts/fe-stability-analysis/.cache/`，无法识别 git 根目录时使用 `{cwd}/artifacts/fe-stability-analysis/.cache/`。环境变量 `FE_STABILITY_CACHE_DIR` 可覆盖该目录。

Phase 1 对下列字段按固定键顺序序列化后计算 SHA-256，取前 24 位作为 `cache_key`：

- `schema_version`（固定 `2.0`）、排序后的 `app_names`
- `time_granularity`、`partition_timezone`
- CURR 与 BASE 的完整日或小时半开区间
- `stability_window_days`、`stability_window_hours`

`run_id`、`output_dir`、`output_mode`、`generated_at` 不参与 `cache_key`。因此每次无需遍历 `.cache`，只读取一个索引文件并按键查找：

```text
{CACHE_DIR}/index.json → entries[{cache_key}]
```

索引结构：

```json
{
  "index_version": "1",
  "entries": {
    "<cache_key>": {
      "key_input": { "app_names": [], "time_range": {}, "time_granularity": "hour", "partition_timezone": "GMT+1" },
      "source_run_id": "20260717_160844",
      "source_output_dir": "/abs/.../artifacts/fe-stability-analysis/20260717_160844",
      "overview_path": "/abs/.../overview.json",
      "project_paths": { "search-frontend": "/abs/.../search-frontend.json" },
      "meta_fingerprint": "<sha256>",
      "created_at": "ISO8601"
    }
  }
}
```

## 何时必须重新查询（禁止读或写缓存）

满足任一条件则执行 **Phase 2 → 3**：

1. `includes_unstable_data = true` 或 `is_provisional = true`
2. 用户明确要求重新跑数、刷新或最新数据
3. `{CACHE_DIR}/index.json` 不存在、不可解析，或 `entries[cache_key]` 不存在、其 `key_input` 不一致
4. 索引未覆盖全部 `app_names`，或其 `overview_path` / 任一 `project_paths[app]` 不存在、不可读
5. 目标 JSON 的 `meta.schema_version` 不为 `"2.0"`，或 `meta_fingerprint`、范围、项目集合、粒度、分区时区、稳定窗口与本次 Phase 1 不一致

### 数据稳定窗口判定

Phase 1 计算 `includes_unstable_data` 与 `is_provisional`。覆盖稳定窗口的数据永远重查；例如默认过去 24 小时包含最近完成分区，通常不可缓存。仅完全早于稳定窗口的固定历史区间可复用。

## 缓存命中与写入

命中有效索引时：

- `analysis_only`：跳过 Phase 2–3，返回索引指向的总览和项目 JSON 绝对路径，并注明源 `run_id`。
- `report`：跳过 Phase 2–3，使用索引指向的 JSON 执行 Phase 4，在**当前** `{OUTPUT_DIR}` 写入 `report.md`；不得复制 JSON。

Phase 3 成功写完 `{OUTPUT_DIR}/overview.json` 与所有 `{app_name}.json` 后：

1. 仅当数据稳定且未要求刷新时，计算源文件 `meta_fingerprint`。
2. 对 `{CACHE_DIR}/index.json` 获取短暂独占锁，重新读取最新内容，仅更新 `entries[cache_key]` 为当前 `run_id` 的绝对路径映射。
3. 写入临时文件后原子替换 `{CACHE_DIR}/index.json`，再释放锁；临时文件完成后必须删除。
4. 不稳定或临时数据不得创建或覆盖索引条目。

清理任何 `artifacts/fe-stability-analysis/<run_id>/` 前，必须检查 `index.json` 的全部 `entries.*.source_run_id`；仍被任一条目引用的 run 不得删除。

## Phase 1「fe-stability-query」不可跳过

每次请求都必须执行 Phase 1，重新生成范围、稳定性判定、`cache_key` 与索引路径。命中缓存时不执行 SQL，但仍必须完整校验索引和源文件元数据。
