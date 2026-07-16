# 项目映射表

本表是前端稳定性分析的项目名称单一来源。新增项目或别名时，只修改本文件；不要修改 SQL 模板、固定应用列表或编排逻辑。

## 维护规则

1. `app_name` 必须与监控表 `app_name` 字段完全一致，且使用小写连字符格式。
2. 每行至少保留一个便于用户表达的中文名称或英文别名；多个别名以 `、` 分隔。
3. 用户请求中的项目名称必须与 `app_name` 或别名**精确匹配**（忽略英文大小写）；不做模糊猜测。
4. 新增项目：新增一行；停用项目：保留该行并在状态列标为“停用”，避免历史报告无法解析。

| app_name | 展示名称 | 别名 | 状态 |
|---|---|---|---|
| `search-frontend` | 搜索前端 | 搜索、search frontend | 启用 |
| `unified-search-frontend` | 统一搜索前端 | 统一搜索、unified search、unified-search、PDP、CPP | 启用 |
| `homepage-frontend` | 首页前端 | 首页、homepage、homepage frontend | 启用 |
| `product-editor-frontend` | 商品编辑器前端 | 商品编辑器、product editor、product-editor | 启用 |
