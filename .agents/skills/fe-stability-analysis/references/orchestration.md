# 编排器公共规则

本文件定义 `fe-stability-analysis` 调用子 skill 时的统一解析逻辑。各 Phase 均引用此规则，不重复描述。

---

## 编排器执行纪律（强制）

`fe-stability-analysis` 作为**唯一编排入口**，必须遵守：

1. **按 Phase 1 → [缓存检查] → 2 → 3 → 4 顺序执行**；缓存命中时可跳过 Phase 2–4，但 Phase 1 与缓存检查不可跳过。
2. **仅调用白名单 skill**（见下表），不得擅自调用任何其他 skill、MCP、子 agent 或外部助手。
3. **不得绕过子 skill**：禁止直接执行 shell / `maxc` / DataWorks CLI、禁止手写 SQL 替代 `fe-stability-query`、禁止直接写 Markdown 报告替代 `fe-stability-report-writer`、禁止在编排器内自行计算指标替代 `fe-stability-metrics`。
4. **子 skill 必须完整执行**：按对应 skill 的定义完整执行，不得凭记忆或摘要省略步骤。
5. **等待 Phase 完成**：每一 Phase 必须收到该 Phase 规定的返回值后，方可进入下一 Phase。
6. **不得因「更高效」「更熟悉」而替换路径**：即使其他 skill 看似能完成同类任务，仍必须走本编排链路。
7. **范围与日期以本次 Phase 1「fe-stability-query」为准**：每次请求必须先解析项目范围并重算日期，不得沿用会话或旧报告中的区间。
8. **结果缓存**：见 [cache-policy.md](cache-policy.md)。**含今天必重查**；不含今天且当前范围对应的缓存文件齐全且 meta 与 `scope` / `app_name` 一致时，**允许直接返回缓存**，跳过 Phase 2–4。

### 子 skill 白名单（仅此五个）

| `{skill-name}` | 调用阶段 | 用途 |
|----------------|---------|------|
| `fe-stability-query` | Phase 1 | 生成完整查询计划（参数、缓存标识、round1 与 round4 SQL） |
| `dataworks-dev-assistant` | Phase 2 | 执行 SQL |
| `fe-stability-metrics` | Phase 3 | 指标计算 + analysis.json |
| `fe-stability-report-writer` | Phase 4 | Markdown 报告渲染 |
| `report-generator` | Phase 4 后处理 | 报告结构、表达与可读性审校 |

### 禁止调用的 skill（非 exhaustive，原则性禁止）

编排器**不得**调用白名单以外的任何 skill，尤其包括但不限于：

- `fe-stability-generate`、`fe-stability-report` 及其他历史/并行稳定性 skill
- `odps-skill`、`maxcompute-cli-guidance-ncs`、`webvital-maxcompute-sql`
- `dataworks-dev-assistant` 以外的 DataWorks / ODPS 相关 skill
- 任意 Cursor / QoderWork 通用 skill（如 `explore-repository`、`cr-frontend` 等）

若用户或上下文暗示使用上述 skill，编排器仍**只走本编排链路**。

---

## 本编排器涉及的 skill

白名单与调用阶段见上文 **子 skill 白名单** 表。

---

## 输出目录解析（Phase 1 后）

Phase 1 完成后解析 `{OUTPUT_DIR}`，用于缓存检查及后续 Phase：

| 优先级 | 条件 | 输出目录 |
|--------|------|----------|
| 1 | 用户本次对话明确指定路径 | 用户给定的绝对或相对路径 |
| 2 | 环境变量 `FE_STABILITY_OUTPUT_DIR` 已设置 | 该变量值 |
| 3 | 能识别 git 工作区根目录 | `{git_root}/outputs/fe-stability-analysis/` |
| 4 | 兜底 | `{cwd}/outputs/fe-stability-analysis/` |

> **禁止**写入 skill 安装目录（`~/.agents/skills/`、`./skills/` 下的路径）。

---

## 产物命名（comparison_id）

由 `fe-stability-metrics` 生成，规则见 `fe-stability-metrics/references/analysis-schema.md`：

| 产物 | 文件名 |
|------|--------|
| 分析中间文件 | `{OUTPUT_DIR}/analysis-{comparison_id}.json` |
| 唯一报告 | `{OUTPUT_DIR}/frontend-stability-{scope}-{comparison_id}.md` |

`scope=global` 时文件名中的 scope 为 `global`；`scope=app` 时使用明确指定的 `{app_name}`。缓存不得跨范围复用。
