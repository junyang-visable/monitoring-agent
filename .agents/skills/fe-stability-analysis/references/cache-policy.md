# 结果缓存策略

编排器在 **Phase 1「fe-stability-query」完成后**、进入 Phase 2 之前执行本检查。

## 何时必须重新查询（禁止读缓存）

满足**任一**条件则 **完整执行 Phase 2 → 3 → 4**：

1. **`includes_today = true`**：用户询问的日期范围包含「今天」（见下）
2. **缓存文件不完整**：当前范围的 `analysis.json` 或唯一 Markdown 报告缺失
3. **缓存与本次日期或范围不一致**：`analysis.json` 内 `meta` 与 Phase 1 计算的 CURR/BASE、`scope`、`app_name` 不匹配
4. **用户明确要求重新跑数 / 刷新 / 最新数据**

### includes_today 判定

Phase 1 由 `fe-stability-query` 计算（`today` = 系统当天 yyyyMMdd）：

```
includes_today =
  (CURR_START <= today <= CURR_END)
  OR (BASE_START <= today <= BASE_END)
```

典型情况：

| 场景 | includes_today | 是否可缓存 |
|------|----------------|-----------|
| 过去一周（滚动 7 天，截至昨天） | false | 可缓存 |
| 上个自然周 vs 上上个自然周 | false | 可缓存 |
| 本周（周一至昨天） | false（若 today 不在 CURR 内） | 可缓存 |
| 本周至今 / 含今天 / CURR_END=今天 | true | **必须重查** |
| 指定范围含今天 | true | **必须重查** |

## 何时允许返回缓存

**同时**满足：

1. `includes_today = false`
2. 以下当前范围对应的两文件均存在且可读：

```
{OUTPUT_DIR}/analysis-{comparison_id}.json
{OUTPUT_DIR}/frontend-stability-global-{comparison_id}.md
# 或（指定项目时）
{OUTPUT_DIR}/frontend-stability-{app_name}-{comparison_id}.md
```

3. `analysis.json` 中 `meta.comparison_id`、`meta.curr_start/end`、`meta.base_start/end`、`meta.scope`、`meta.app_name`（项目范围时）与 Phase 1 一致

→ **跳过 Phase 2、3、4**，直接 Read 缓存报告返回用户，并注明「命中历史缓存，未重新查数」。

## Phase 1「fe-stability-query」不可跳过

无论是否命中缓存，**每次请求都必须执行 Phase 1「fe-stability-query」**（解析项目范围与时间意图，基于今天生成计划参数和缓存标识）。

命中缓存时不执行查询计划中的 SQL；计划参数、`comparison_id` 与 `includes_today` 仍必须生成并校验。
