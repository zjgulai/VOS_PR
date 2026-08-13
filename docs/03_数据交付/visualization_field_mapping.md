# 可视化字段映射与清洗规范

> 本文档定义 `viz_dataset.json` 的字段结构、数据来源、清洗规则。
> 由 `tools/export_viz_json.py` 调用 `tools/cleaning/` 各模块执行清洗。

## 1. 数据来源

| CSV 文件 | 位置 | 清洗模块 | 目标 Section |
|---------|------|---------|-------------|
| dim_project_meta.csv | `data/delivery/tables/` | `clean_dim_project_meta.py` | `overview` |
| dim_country_product_persona.csv | `data/delivery/tables/` | `clean_dim_country_product_persona.py` | `personas` |
| dim_top20_country_insight.csv | `data/delivery/tables/` | `clean_dim_top20_country_insight.py` | `top20` |
| dim_cluster_strategy.csv | `data/delivery/tables/` | `clean_dim_cluster_strategy.py` | `clusters` |
| dim_country_price_sensitivity.csv | `data/delivery/tables/` | `clean_dim_country_price_sensitivity.py` | `purchasing_power` |
| dim_info_source_quality.csv | `data/delivery/tables/` | `clean_dim_info_source_quality.py` | `trust_sources` |
| cfg_top10_platform_entry.csv | `data/delivery/tables/` | `clean_cfg_top10_platform_entry.py` | `platforms` |
| cfg_top10_country_line.csv | `data/delivery/tables/` | `clean_cfg_top10_country_line.py` | `keywords` |
| cfg_p1_search_playbook.csv | `data/delivery/tables/` | `clean_cfg_p1_search_playbook.py` | `p1_search` (新增) |
| dim_country_segment_matrix.csv | `data/delivery/tables/` | `clean_dim_country_segment_matrix.py` | `segments` (新增) |
| voc_summary_flat.csv | `data/delivery/` | `export_viz_json.py` 内联 | `voc_summary` |

## 2. 输出结构 — `viz_dataset.json`

```json
{
  "meta": { ... },
  "overview": [ ... ],
  "countries": [ ... ],
  "personas": [ ... ],
  "top20": [ ... ],
  "clusters": [ ... ],
  "purchasing_power": [ ... ],
  "trust_sources": [ ... ],
  "platforms": [ ... ],
  "keywords": [ ... ],
  "p1_search": [ ... ],
  "segments": [ ... ],
  "voc_summary": [ ... ]
}
```

## 3. 各Section字段定义

### 3.1 `meta`

| 字段 | 类型 | 来源 | 清洗规则 |
|------|------|------|---------|
| generated_at | string (ISO datetime) | 脚本运行时生成 | — |
| source_files | string[] | CSV文件名列表 | — |
| total_countries | int | 去重统计 | — |
| total_product_lines | int | 去重统计 | — |

### 3.2 `overview`

来源：`dim_project_meta.csv`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| key | string | 项目 | strip 空格 |
| value | string/number | 数值 | 数字型尝试 int/float 转换 |

### 3.3 `countries` — 国家基础信息

来源：`dim_country_product_persona.csv` + 去重国家

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| code | string | （映射表派生） | ISO 3166-1 alpha-2，大写 |
| name_cn | string | 国家 | strip；统一映射（见§4.1） |
| is_top20 | bool | 是否出现在 TOP20国家深挖 | — |
| is_top10 | bool | 是否出现在 TOP10国家品线 | — |
| sales_amount | number | 销售额 | 去除逗号、¥、$符号，转float |

### 3.4 `personas` — 国家×品线画像

来源：`dim_country_product_persona.csv`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| country | string | 国家 | 统一映射（§4.1） |
| country_code | string | — | 由国家名查 §4.1 映射表 |
| product_line | string | 产品品线 | 统一映射（§4.2） |
| identity_profile | string | 身份画像 | strip；保留换行 |
| media_preference | string | 媒体偏好 | strip |
| purchase_habit | string | 购买习惯 | strip |
| brand_preference | string | 品牌偏好 | strip |
| competitor_brands | string | 核心竞争品牌（国际/本土） | strip |
| competitor_models | string | 核心竞品产品名称/型号 | strip |
| marketing_preference | string | 营销偏好 | strip |
| social_platforms | string | 社媒传播类平台 | 统一分隔符→逗号 |
| vertical_communities | string | 垂类社区平台 | 统一分隔符→逗号 |
| vertical_media | string | 垂类官方媒体平台 | 统一分隔符→逗号 |

### 3.5 `top20` — TOP20国家深挖

来源：`dim_top20_country_insight.csv`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| country | string | 国家 | 统一映射 |
| country_code | string | — | 派生 |
| sales_amount | number | 销售额 | 数字清洗 |
| insight | string | 国家洞察 | strip |

### 3.6 `clusters` — 区域Cluster策略卡

来源：`dim_cluster_strategy.csv`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| cluster | string | 区域cluster | strip，统一映射（§4.3） |
| representative_countries | string | TOP20代表国家 | strip |
| top20_count | int | TOP20国家数 | int 转换 |
| common_customer_traits | string | 共性客群特征 | strip |
| common_trust_sources | string | 共性信任来源 | strip |
| common_content_angle | string | 共性内容切口 | strip |
| common_price_strategy | string | 共性价格策略 | strip |
| channel_focus | string | 渠道与平台侧重 | strip |
| country_differences | string | 国家差异点 | strip |
| recommended_actions | string | 建议优先动作 | strip |

### 3.7 `purchasing_power` — 国家购买力与价格敏感

来源：`dim_country_price_sensitivity.csv`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| country | string | 国家 | 统一映射 |
| country_code | string | — | 派生 |
| region_cluster | string | 区域cluster | 统一映射 |
| purchasing_power_tier | string | 国家购买力层级 | strip |
| product_line | string | 产品品线 | 统一映射（§4.2） |
| competitor_brands | string | 核心竞争品牌 | strip |
| competitor_models | string | 核心竞品产品名称/型号 | strip |
| priority | string | 品线优先级 | 统一映射（§4.4） |
| sample_segment | string | 样本客群 | strip |
| spending_mindset | string | 品类支出心智 | strip |
| price_sensitivity | string | 价格敏感方式 | strip |
| bundle_preference | string | 套装偏好 | strip（CSV新增） |
| gift_preference | string | 赠品偏好 | strip（CSV新增） |
| promo_sensitivity | string | 节点促销敏感度 | strip（CSV新增） |
| brand_tier_preference | string | 品牌梯度偏好 | strip（CSV新增） |
| purchase_channel_preference | string | 成交偏好渠道 | strip（CSV新增） |
| recommended_price_strategy | string | 推荐价格策略 | strip（CSV新增） |
| recommended_promo_tactic | string | 推荐促销打法 | strip（CSV新增） |
| recommended_bundle_direction | string | 推荐套装方向 | strip（CSV新增） |
| recommended_gift_direction | string | 推荐赠品方向 | strip（CSV新增） |
| risk_notes | string | 主要风险提示 | strip（CSV新增） |
| local_judgment | string | 国家本地判断 | strip（CSV新增） |

### 3.8 `trust_sources` — 信息源质量分层

来源：`dim_info_source_quality.csv`

> 字段映射变更：原xlsx的 `来源名称` / `链接` → CSV的 `代表平台` / `代表入口`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| country | string | 国家 | 统一映射 |
| country_code | string | — | 派生 |
| region_cluster | string | 区域cluster | strip |
| product_line | string | 产品品线 | 统一映射 |
| competitor_brands | string | 核心竞争品牌（国际/本土） | strip |
| competitor_models | string | 核心竞品产品名称/型号 | strip |
| priority | string | 品线优先级 | 统一映射 |
| sample_segment | string | 样本客群 | strip |
| research_question_type | string | 研究问题类型 | strip |
| source_tier | string | 来源层级 | strip |
| source_type | string | 来源类型 | strip |
| source_name | string | **代表平台** | strip（原 `来源名称`） |
| entry | string | **代表入口** | strip（替代原 `url`/`链接`） |
| target_segment | string | 适配客群 | strip（CSV新增） |
| suggested_usage | string | 建议用途 | strip（CSV新增） |
| keyword_direction | string | 关键词方向 | strip（CSV新增） |
| access_method | string | 来源获取方式 | strip（CSV新增） |
| risk_notes | string | 风险说明 | strip（CSV新增） |

### 3.9 `platforms` — TOP10平台入口

来源：`cfg_top10_platform_entry.csv`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| country | string | 国家 | 统一映射 |
| country_code | string | — | 派生 |
| country_sales | number | 国家销售额 | 数字清洗 |
| priority_line | string | 优先品线 | strip |
| competitor_brands | string | 核心竞争品牌 | strip |
| competitor_models | string | 核心竞品产品名称/型号 | strip |
| country_judgment | string | 国家判断 | strip |
| platform_type | string | 平台类型 | 统一分类（§4.5） |
| platform | string | 平台 | strip |
| entry_section | string | 入口/版块 | strip |
| access_method | string | 访问方式 | strip |
| keyword_pack | string | 关键词包 | strip |
| sampling_advice | string | 采样建议 | strip |
| source_index | string | 来源索引 | strip |

### 3.10 `keywords` — TOP10国家品线关键词数据

来源：`cfg_top10_country_line.csv`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| country | string | 国家 | 统一映射 |
| country_code | string | — | 派生 |
| product_line | string | 产品品线 | 统一映射 |
| competitor_brands | string | 核心竞争品牌 | strip |
| competitor_models | string | 核心竞品产品名称/型号 | strip |
| sales_amount | number | 销售额 | 数字清洗 |
| country_total_sales | number | 国家总销售额 | 数字清洗 |
| share_in_country | string | 国家内占比 | strip |
| line_rank | int | 品线排名 | int 转换 |
| crawl_priority | string | 抓取优先级 | 统一映射 |
| priority_note | string | 优先级说明 | strip |
| core_product_terms | string | 核心产品词 | 统一分隔符→逗号 |
| pain_point_terms | string | 痛点词 | 统一分隔符→逗号 |
| scenario_terms | string | 场景词 | 统一分隔符→逗号 |
| decision_terms | string | 决策词 | 统一分隔符→逗号 |
| topic_clusters | string | 主题簇 | strip |
| recommended_entry | string | 推荐入口 | strip |

### 3.11 `p1_search` — P1搜索作业单 (新增)

来源：`cfg_p1_search_playbook.csv`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| country | string | 国家 | 统一映射 |
| country_code | string | — | 派生 |
| product_line | string | 产品品线 | 统一映射 |
| competitor_brands | string | 核心竞争品牌 | strip |
| competitor_models | string | 核心竞品产品名称/型号 | strip |
| sales_amount | number | 销售额 | 数字清洗 |
| country_total_sales | number | 国家总销售额 | 数字清洗 |
| share_in_country | string | 国家内占比 | strip |
| line_rank | string | 品线排名 | strip |
| crawl_priority | string | 抓取优先级 | 统一映射 |
| priority_note | string | 优先级说明 | strip |
| core_product_terms | string | 核心产品词 | 统一分隔符→逗号 |
| pain_point_terms | string | 痛点词 | 统一分隔符→逗号 |
| scenario_terms | string | 场景词 | 统一分隔符→逗号 |
| decision_terms | string | 决策词 | 统一分隔符→逗号 |
| topic_clusters | string | 主题簇 | strip |
| recommended_entry | string | 推荐入口 | strip |
| site_search_query | string | 站内搜索语句 | strip |
| community_boolean_query | string | 社区布尔组合 | strip |
| decision_search_query | string | 决策搜索组合 | strip |
| local_language_variant | string | 本地语言变体 | strip |
| google_search_query | string | 推荐Google搜索 | strip |
| mixed_test_terms | string | 中英混合测试词 | strip |
| entry_1 | string | 入口1 | strip |
| entry_2 | string | 入口2 | strip |
| entry_3 | string | 入口3 | strip |

### 3.12 `segments` — 国家客群矩阵 (新增)

来源：`dim_country_segment_matrix.csv`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| country | string | 国家 | 统一映射 |
| country_code | string | — | 派生 |
| region_cluster | string | 区域cluster | strip |
| purchasing_power_initial | string | 国家购买力初判 | strip |
| product_line | string | 产品品线 | 统一映射 |
| competitor_brands | string | 核心竞争品牌 | strip |
| competitor_models | string | 核心竞品产品名称/型号 | strip |
| priority | string | 品线优先级 | 统一映射 |
| segment_code | string | 客群编码 | strip |
| segment_name | string | 客群名称 | strip |
| lifecycle | string | 生命周期 | strip |
| family_structure | string | 家庭结构 | strip |
| decision_driver | string | 决策驱动 | strip |
| core_pain_points | string | 核心痛点 | strip |
| key_purchase_motivation | string | 关键购买动机 | strip |
| main_resistance | string | 主要阻力 | strip |
| core_trust_source | string | 核心信任来源 | strip |
| priority_content_angle | string | 优先内容切口 | strip |
| price_sensitivity_initial | string | 价格敏感初判 | strip |
| local_marketing_angle | string | 本地化营销切口 | strip |
| social_platforms | string | 社媒传播类平台 | 统一分隔符→逗号 |
| community_platforms | string | 垂类社区平台 | 统一分隔符→逗号 |
| official_media_platforms | string | 垂类官方媒体平台 | 统一分隔符→逗号 |
| local_judgment | string | 国家本地判断 | strip |
| source_index | string | 来源索引 | strip |

### 3.13 `voc_negative` — 负面VOC萃取

来源：`dim_voc_negative_extract.csv` → `clean_dim_voc_negative_extract.py`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| country | string | 国家 | 统一映射（§4.1） |
| country_code | string | — | 由国家名查映射表 |
| cluster | string | 区域cluster | strip |
| product_line | string | 产品品线 | 统一映射（§4.2） |
| platform_type | string | 平台类型 | 统一映射（§4.5） |
| platform | string | 平台 | strip |
| segment_code | string | 画像编码 | strip |
| segment_name | string | 画像名称 | strip |
| lifecycle | string | 生命周期 | strip |
| pain_category | string | 痛点大类(功能/价格/体验/服务/安全) | 限定枚举值；默认"体验" |
| negative_theme | string | 负面主题 | strip |
| original_text | string | 负面原文摘录(本地语言) | strip |
| translated_text | string | 负面原文摘录(中文翻译) | strip；允许空值 |
| frequency | int | 频次估算 | int 转换；DTC 默认 1，社区默认 3 |
| intensity | string | 负面强度(高/中/低) | 限定枚举值；默认"中" |
| competitor_brand | string | 竞品关联品牌 | strip |
| action_suggestion | string | 对应运营建议 | strip |
| source_url | string | 来源URL | strip |
| collect_date | string | 采集日期 | strip |
| batch_code | string | 批次编码 | strip |
| priority | string | 优先级 | strip；默认 P2 |

**去重逻辑**：使用 `source_url` + `original_text` 前50字符作为组合去重键（社区帖子同一URL可能有多条不同回复）。

**垃圾行清洗**：由 `fix_dtc_garbage.py` 预处理，删除 Cloudflare 拦截、404 错误、markdown 残片、网站导航文本、无关推荐文章等非真实评论内容。

**缺失字段补全**：DTC/社区采集数据可能缺少 `画像编码`、`画像名称`、`生命周期`、`频次估算`，由 `fix_dtc_garbage.py` 按品线自动推断填充。

### 3.14 `voc_summary` — VOC采集汇总

来源：`voc_summary_flat.csv`

| 字段 | 类型 | 原始列名 | 清洗规则 |
|------|------|---------|---------|
| country_code | string | country_code | 大写 |
| country_name_cn | string | country_name_cn | strip |
| product_line | string | product_line | 统一映射 |
| total_comment_cnt | int | total_comment_cnt | int |
| valid_comment_cnt | int | valid_comment_cnt | int |
| positive_rate | float | positive_rate | float |
| negative_rate | float | negative_rate | float |
| top_themes | string | top_themes | strip |
| top_pain_points | string | top_pain_points | strip |
| platform_count | int | platform_count | int |
| platform_list | string | platform_list | strip |

## 4. 字段值标准化映射表

### 4.1 国家名称映射

```
原始值 → 标准值 (code)
美国 → 美国 (US)
英国 → 英国 (GB)
德国 → 德国 (DE)
法国 → 法国 (FR)
日本 → 日本 (JP)
澳大利亚 → 澳大利亚 (AU)
加拿大 → 加拿大 (CA)
意大利 → 意大利 (IT)
西班牙 → 西班牙 (ES)
荷兰 → 荷兰 (NL)
比利时 → 比利时 (BE)
瑞士 → 瑞士 (CH)
奥地利 → 奥地利 (AT)
瑞典 → 瑞典 (SE)
挪威 → 挪威 (NO)
丹麦 → 丹麦 (DK)
芬兰 → 芬兰 (FI)
爱尔兰 → 爱尔兰 (IE)
波兰 → 波兰 (PL)
捷克 → 捷克 (CZ)
葡萄牙 → 葡萄牙 (PT)
希腊 → 希腊 (GR)
韩国 → 韩国 (KR)
新加坡 → 新加坡 (SG)
马来西亚 → 马来西亚 (MY)
泰国 → 泰国 (TH)
印度尼西亚 → 印度尼西亚 (ID)
菲律宾 → 菲律宾 (PH)
越南 → 越南 (VN)
印度 → 印度 (IN)
巴西 → 巴西 (BR)
墨西哥 → 墨西哥 (MX)
阿根廷 → 阿根廷 (AR)
智利 → 智利 (CL)
哥伦比亚 → 哥伦比亚 (CO)
秘鲁 → 秘鲁 (PE)
南非 → 南非 (ZA)
阿联酋 → 阿联酋 (AE)
沙特阿拉伯 → 沙特阿拉伯 (SA)
以色列 → 以色列 (IL)
土耳其 → 土耳其 (TR)
埃及 → 埃及 (EG)
俄罗斯 → 俄罗斯 (RU)
乌克兰 → 乌克兰 (UA)
罗马尼亚 → 罗马尼亚 (RO)
匈牙利 → 匈牙利 (HU)
新西兰 → 新西兰 (NZ)
中国台湾 → 中国台湾 (TW)
中国香港 → 中国香港 (HK)
柬埔寨 → 柬埔寨 (KH)
尼日利亚 → 尼日利亚 (NG)
肯尼亚 → 肯尼亚 (KE)
巴基斯坦 → 巴基斯坦 (PK)
孟加拉国 → 孟加拉国 (BD)
```

> 注：国家名称如有简写或别名（如"UK"→"英国"），在脚本中处理。
> `GLOBAL` 行在 `voc_summary` 中保留，`country_code = "GLOBAL"`。

### 4.2 品线名称标准化

```
吸奶器 → 吸奶器
消毒柜 / 消毒锅 → 消毒柜
暖奶器 → 暖奶器
辅食机 → 辅食机
智能监控 → 智能监控
喂养电器 → 喂养电器
家居出行 → 家居出行
unknown → unknown
（空值） → unknown
```

### 4.3 区域Cluster标准化

```
Strip 空格和换行；保留原始 cluster 名称。
预期值：北美, 西欧, 北欧, 南欧, 东欧, 东亚, 东南亚, 南亚, 中东, 拉美, 非洲, 大洋洲
```

### 4.4 优先级标准化

```
P1 → P1
P2 → P2
P3 → P3
（空值/其他） → P3
```

### 4.5 平台类型标准化

```
社媒传播类 → social_media
垂类社区类 → vertical_community
垂类官方媒体类 → vertical_official
电商平台 → ecommerce
搜索引擎 → search_engine
竞品官方电商 → competitor_dtc
第三方评测类 → third_party_review
（其他） → other
```

## 5. 通用清洗规则

1. **空白处理**：所有字符串字段 `strip()` 前后空白、替换 `\u00a0`（不间断空格）为普通空格
2. **多值分隔符**：统一使用英文逗号 `,` 分隔（原始可能有 `、`、`/`、`；`、`\n`）
3. **数字清洗**：去除千位逗号、货币符号，`None`/空值 → `null`
4. **HTML实体**：去除 `&nbsp;`、`&amp;` 等 HTML 残留
5. **空行跳过**：国家字段为空的行直接跳过
6. **UTF-8 BOM**：CSV 读取使用 `utf-8-sig` 编码

## 6. 清洗模块架构

```
tools/cleaning/
├── __init__.py
├── _common.py                           # 共享工具函数和映射表
├── clean_dim_project_meta.py            # → overview
├── clean_dim_country_product_persona.py # → personas
├── clean_dim_top20_country_insight.py   # → top20
├── clean_dim_cluster_strategy.py        # → clusters
├── clean_dim_country_price_sensitivity.py # → purchasing_power
├── clean_dim_info_source_quality.py     # → trust_sources
├── clean_cfg_top10_platform_entry.py    # → platforms
├── clean_cfg_top10_country_line.py      # → keywords
├── clean_cfg_p1_search_playbook.py      # → p1_search
├── clean_dim_country_segment_matrix.py  # → segments
├── clean_dim_voc_negative_extract.py    # → voc_negative
└── fix_dtc_garbage.py                   # 一次性 DTC 垃圾清洗与字段补全
```

每个模块导出 `build() -> list[dict]`，可独立运行调试（`python -m tools.cleaning.clean_xxx`）。
