# Claude Skills 地图

## 1. VOC 原子技能（已有）

| 目标 | 技能 |
|---|---|
| 输入边界确认 | `voc-input-scope` |
| 数据清洗 | `voc-data-cleaning` |
| 画像构建 | `voc-persona-base` |
| 媒体库构建 | `voc-media-library` |
| 行级组装 | `voc-row-assembly` |
| 国家选择/深挖 | `voc-top-country-selection` / `voc-top20-deep-dive` |
| 关键词与作业单 | `voc-country-line-keywords` / `voc-p1-search-playbook` |
| 落表与交付 | `voc-schema-design` / `voc-delivery-packaging` |
| 质量检查 | `voc-workbook-qa` |
| 总调度 | `voc-master-orchestrator` |

## 2. 采集增强技能（外部）

| 场景 | 推荐技能 |
|---|---|
| 结构化页面提取 | `firecrawl-automation` |
| 强风控代理抓取 | `brightdata-automation` |
| 电商数据增强 | `asin-data-api-automation` / `junglescout-automation` |
| 复杂链接解析 | `markdown-proxy` |

## 3. 调用策略

- 优先使用现有 VOC 原子技能完成业务链路
- 采集受限场景再调用外部增强技能
- 所有增强调用需记录输入、输出与失败原因
