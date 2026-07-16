---
name: fe-stability-report-writer
description: 读取 analysis.json，按总体或指定项目范围渲染一份事实完整的 Markdown 报告，并在可用时调用 report-generator 进行结构与表达审校。
version: 1.6.0
---

# 报告渲染与输出

## 职责边界

1. 读取 `analysis-{comparison_id}.json`（schema ≥ 1.1）
2. 按范围渲染一份事实完整的 Markdown 草稿
3. 在 `report-generator` 可用时调用它审校草稿，并写入最终报告

**禁止** 重新计算指标；**禁止** 省略 `priority_actions` / `spike_alerts` / `issues.*.details` 章节。

`report-generator` 只能优化结构、表达、标题、段落和表格可读性；不得修改 `analysis.json` 中的数字、日期、项目范围、优先级或事实结论。

---

## 输入

- `analysis.json` 绝对路径
- `{OUTPUT_DIR}`
- `scope`：`global` 或 `app`；`scope=app` 时还需映射表解析出的 `app_name` 与展示名称

若 `meta.schema_version` < `"1.1"` 或缺少 `priority_actions`，提示需重新运行 `fe-stability-metrics`。

---

## Step 1：读取 analysis.json

校验 `meta.comparison_id`、`meta.schema_version`。

---

## Step 2：按范围渲染唯一报告

| 范围 | 模板 | 输出 |
|---|---|---|
| `global` | [references/template-summary.md](references/template-summary.md) | `frontend-stability-global-{comparison_id}.md`；不得渲染「按应用维度汇总」 |
| `app` | [references/template-by-app.md](references/template-by-app.md) | `frontend-stability-{app_name}-{comparison_id}.md`；仅渲染该 `app_name` 的章节，不得渲染其他应用或跨应用汇总 |

不得在同一次执行中渲染两份报告。

### `global`：总体报告

模板：[references/template-summary.md](references/template-summary.md)

**必含章节**（不可省略）：

| 章节 | json 路径 |
|------|-----------|
| 需优先处理的具体错误 | `priority_actions[]` |
| 错误突增告警 | `spike_alerts[]` |
| 各问题明细表 | `issues.*.details[]` |
| 优先治理建议 | `governance[]` + 关联 `related_errors` |

草稿：`{OUTPUT_DIR}/.draft-frontend-stability-global-{comparison_id}.md`

---

### `app`：指定项目报告

模板：[references/template-by-app.md](references/template-by-app.md)

该指定 app **必含**：

- 「本应用需优先处理（TOP 5）」— `priority_actions` 或 `issues.*.by_app.{app}`
- 资源/API/JS 等明细表 — 含基线/天、当前/天、变化、建议

草稿：`{OUTPUT_DIR}/.draft-frontend-stability-{app_name}-{comparison_id}.md`

---

## Step 4：调用 report-generator 审校

1. 解析 `report-generator`：优先 `./skills/report-generator/SKILL.md`，否则使用 `~/.agents/skills/report-generator/SKILL.md`。
2. 若路径存在，Read 该 `SKILL.md` 并按其工作流执行；若两处均不存在，记录跳过原因并将草稿提升为最终报告。
3. `report-generator` 存在时，将当前范围的 Markdown 草稿、`analysis.json` 和以下约束传入：
   - 保留所有必需章节及明细表
   - 保留所有数字、日期、项目名称、优先级和建议事实
   - 只审校当前 `scope`，不得添加其他项目或跨项目汇总
   - 输出最终 Markdown 到约定的 `frontend-stability-{scope}-{comparison_id}.md`
4. 若 `report-generator` 不存在：记录“未找到可选 report-generator，跳过审校”，将草稿提升为最终报告并继续；不得阻塞 Phase 4。
5. 若已找到 `report-generator` 但执行失败：报告错误并阻塞 Phase 4，不得把未经审校的草稿静默当作最终报告。

## Step 5：输出约定

返回唯一报告的绝对路径及其范围。
