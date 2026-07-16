# 分析指南

## 数据解析映射

| 查询 ID | 用途 |
|---------|------|
| A | 全域每日总量、峰值日识别；结果按 `period` 拆分 |
| B | 全域 event_type + error_type 分布；结果按 `period` 拆分 |
| C1–C6 | 具体 message/url、白屏 page 明细；每条结果按 `period` 拆分（**完整分析必跑**） |

> **完整分析报告**依赖 Group C。编排器 Phase 2 第四轮应默认执行 C1、C2、C3、C4、C5、C6 各 1 条合并查询，且每条结果同时包含 CURR/BASE；C6 白屏 page 分布为必选。

## 分析要点

1. **识别异常峰值**：某天数据远超其他天，在 `peak_days` 中标注并分析根因
2. **资源加载失败**：区分 CDN chunk 问题 vs 第三方脚本问题
3. **API 错误**：按 error_type 细分，从 message 提取 URL（api_name 可能为空）
4. **白屏**：区分 dom_empty vs custom_white_screen
5. **JS 错误**：识别与 CDN chunk 同源错误（如 preload CSS 失败）
6. **治理追踪**：每项问题给出 trend + P0–P2 建议
7. **具体错误**：对 E 查询结果做 message/url 级 CURR vs BASE，识别突增与新出现（见 message-analysis.md）

## 参考文档

| 文件 | 用途 |
|------|------|
| [message-analysis.md](message-analysis.md) | 突增规则、优先级、建议模板 |
| [metrics-rules.md](metrics-rules.md) | 类型级环比与 P0–P2 |

## 应用架构参考（辅助归因，写入 insight 字段）

| app | 特征 |
|-----|------|
| search-frontend | CDN chunk 为主（>90%），Nuxt SSR |
| homepage-frontend | 第三方脚本为主（HubSpot/Bing/Hotjar 等） |
| product-editor-frontend | API 错误突出，403 可能导致白屏 |

## 常见陷阱

- **resource_load_failed 约占总量 80%**，需与其他类型分开讨论
- **单日异常可能扭曲日均值**，在 `peak_days.note` 中注明
- **某天数据明显偏低**：标注「该日数据可能不完整」，不纳入日均或注明置信度
