---
name: fe-stability-report-writer
description: 读取 Stability 总览及项目独立 JSON，渲染一份事实完整的 Markdown 报告，并在可用时调用 report-generator 进行结构与表达审校。
version: 2.1.0
---

# 报告渲染与输出

## 职责边界

1. 读取由上游显式传入的 `overview.json` 及其 `project_files` 指向的项目 JSON（schema = 2.0）
2. 按范围渲染一份事实完整的 Markdown 草稿
3. 在 `report-generator` 可用时调用它审校草稿，并写入最终报告

**禁止** 重新计算指标；**禁止** 省略 `priority_actions` / `spike_alerts` / `issues.*.details` 章节。

`report-generator` 只能优化结构、表达、标题、段落和表格可读性；不得修改输入 JSON 中的数字、日期、项目范围、优先级或事实结论。

---

## 输入

- 总览 JSON 绝对路径
- 项目 JSON 路径映射（或总览 `meta.project_files` 可解析到的路径）
- `{OUTPUT_DIR}`
- `meta.app_names`：上游传入或默认解析出的项目范围。

若总览或任一项目 JSON 的 `meta.schema_version` 不等于 `"2.0"`，或缺少 `priority_actions`，提示需重新运行 `fe-stability-metrics`。

---

## Step 1：读取总览与项目 JSON

校验每个文件的 `meta.comparison_id`、`meta.schema_version` 与项目范围一致。项目章节只能读取对应项目 JSON；不得从总览中假设或重建项目明细。

缓存命中时可读取源 `run_id` 的 JSON，并仍在当前 `{OUTPUT_DIR}` 写入 `report.md`；不得复制源 JSON。

---

## Step 2：按范围渲染唯一报告

| 范围 | 模板 | 输出 |
|---|---|---|
| `app_names` | [references/template-by-apps.md](references/template-by-apps.md) | `report.md`；按 `meta.app_names` 渲染每个项目章节 |

不得在同一次执行中渲染两份报告。

### 项目范围报告

模板：[references/template-by-apps.md](references/template-by-apps.md)

每个 `meta.app_names` 中的 app **必含**：

- 「本应用需优先处理（TOP 5）」— 对应项目 JSON 的 `priority_actions`
- 资源/API/JS 等明细表 — 含基线/天、当前/天、变化、建议

草稿：`{OUTPUT_DIR}/.draft-report.md`

---

## Step 4：调用 report-generator 审校

1. 解析 `report-generator`：优先 `./skills/report-generator/SKILL.md`，否则使用 `~/.agents/skills/report-generator/SKILL.md`。
2. 若路径存在，Read 该 `SKILL.md` 并按其工作流执行；若两处均不存在，记录跳过原因并将草稿提升为最终报告。
3. `report-generator` 存在时，将当前范围的 Markdown 草稿、总览 JSON、项目 JSON 路径映射和以下约束传入：
   - 保留所有必需章节及明细表
   - 保留所有数字、日期、项目名称、优先级和建议事实
   - 仅渲染 `meta.app_names` 中的项目
   - 输出最终 Markdown 到约定的范围文件名
4. 若 `report-generator` 不存在：记录“未找到可选 report-generator，跳过审校”，将草稿提升为最终报告并继续；不得阻塞 Phase 4。
5. 若已找到 `report-generator` 但执行失败：报告错误并阻塞 Phase 4，不得把未经审校的草稿静默当作最终报告。

## Step 5：输出约定

返回唯一报告的绝对路径及其范围。
