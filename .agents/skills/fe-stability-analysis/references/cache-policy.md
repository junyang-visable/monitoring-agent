# 结果缓存策略

编排器在 **Phase 1「fe-stability-query」完成后**、进入 Phase 2 之前执行本检查。

## 何时必须重新查询（禁止读缓存）

满足**任一**条件则 **完整执行 Phase 2 → 3 → 4**：

1. **`includes_unstable_data = true`**：范围覆盖最近仍可能回补的数据日
2. **缓存文件不完整**：`output_mode=analysis_only` 时缺少 `analysis.json`；`output_mode=report` 时缺少 `analysis.json` 或唯一 Markdown 报告
3. **缓存与本次日期或范围不一致**：`analysis.json` 内 `meta` 与 Phase 1 计算的 CURR/BASE、`scope_key`、`app_names` 不匹配
4. **用户明确要求重新跑数 / 刷新 / 最新数据**

### 数据稳定窗口判定

Phase 1 由 `fe-stability-query` 计算最近仍可能回补的数据日。默认 `stability_window_days=1`，因此今天和昨天都属于不稳定范围。

| 场景 | includes_unstable_data | 是否可缓存 |
|------|------------------------|-----------|
| 过去一周（滚动 7 天，含今天） | true | **必须重查** |
| 上个自然周 vs 上上个自然周 | false | 可缓存 |
| 本周（周一至今天） | true | **必须重查** |
| 含稳定窗口内的数据 | true | **必须重查** |
| 早于稳定窗口的数据 | false | 可按缓存完整性和 meta 命中缓存 |

## 何时允许返回缓存

**同时**满足：

1. `includes_unstable_data = false`
2. 当前模式要求的缓存文件存在且可读：

```
# output_mode=analysis_only
{OUTPUT_DIR}/analysis-{scope_key}-{comparison_id}.json

# output_mode=report
{OUTPUT_DIR}/analysis-{scope_key}-{comparison_id}.json
{OUTPUT_DIR}/frontend-stability-apps-{scope_key}-{comparison_id}.md
```

3. `analysis.json` 中 `meta.schema_version=\"1.4\"`，且 `meta.comparison_id`、日期或小时范围、`meta.time_granularity`、`meta.partition_timezone`、`meta.scope_key`、`meta.app_names`、稳定窗口参数与 Phase 1 一致

→ **跳过后续 Phase**，直接返回缓存结果，并注明「命中历史缓存，未重新查数」。

## Phase 1「fe-stability-query」不可跳过

无论是否命中缓存，**每次请求都必须执行 Phase 1「fe-stability-query」**（解析项目范围与时间意图，基于今天生成计划参数和缓存标识）。

命中缓存时不执行查询计划中的 SQL；计划参数、`comparison_id`、`includes_unstable_data` 与稳定窗口参数仍必须生成并校验。
