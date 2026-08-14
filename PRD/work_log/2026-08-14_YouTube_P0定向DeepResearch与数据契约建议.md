---
name: youtube-p0-deep-research-and-data-contract
description: 面向 Social Intelligence P0 的 YouTube 评论级数据能力、来源路径、合规约束、数据契约、覆盖口径与 Go/No-Go 建议。
date: 2026-08-14
verified_at: 2026-08-14
status: 待业务、法务与研发评审
stage: 定向 Deep Research 与方案决策
---

# YouTube P0 定向 Deep Research 与数据契约建议

## 0. 决策结论

### 0.1 推荐方案

YouTube P0 推荐采用「官方 YouTube Data API 为主源，固定频道上传列表为稳定范围，有限关键词搜索作为发现补充，评论线程为核心分析对象」的方案。

首期链路为：

```text
已批准频道 uploads playlist ─┐
有限 keyword search.list ─────┴→ 视频候选与范围冻结
  → videos.list 补齐元数据
  → commentThreads.list 获取顶层评论与线程
  → comments.list 补齐需要完整上下文的回复
  → Coverage + Evidence
  → 内容级痛点分类与聚类
  → 人工确认高价值 Insight
  → 待审批 Action
  → 结果回填
```

当前结论是「方案方向有条件推荐」，不是「YouTube P0 已经可开发或已通过」。进入真实 P0 前仍有三类硬门槛：

1. YouTube 对 Analytics & Reporting / derived metrics 用例的接受结果，或法务对准确用例范围的书面结论。
2. 评论级官方 API 连接器、分页、回复补齐、错误状态、30 天刷新/删除机制完成验证。
3. 社媒部门签字确认首期频道、关键词、产品、市场、语言、痛点 taxonomy、好/坏洞察样本与 Action 流程。

### 0.2 当前判断强度

| 判断 | 结论 | 把握 | 依据 |
|---|---|---|---|
| 官方 API 可以读取公开评论线程和回复 | 事实 | 高 | 官方 `commentThreads.list` 与 `comments.list` 文档 |
| 本地现有采集器已满足 S1 | 否 | 高 | 只采集视频标题、描述和计数，没有评论正文、线程和回复 |
| `regionCode=US` 能证明评论者位于美国 | 否 | 高 | 官方定义仅表示视频可在该国家观看 |
| `relevanceLanguage=en` 能保证内容全为英语 | 否 | 高 | 官方明确仍可能返回其他语言的高相关结果 |
| 评论 NLP / 情绪分析无条件允许 | 否 | 高 | 额外政策要求接受 amendment，申请表由 YouTube 判断用例是否符合 |
| 「痛点聚类」一定落在已允许示例内 | 不确定 | 中 | 官方明确允许评论 NLP、情绪和内容标签，但没有逐字定义本产品的跨视频痛点聚类 |
| Apify 采集可直接替代官方 API 合规门槛 | 否 | 高 | YouTube Developer Policies 禁止 API Client 获取 scraped YouTube data；仍需核对供应商权利链和合同 |

---

## 1. 决策问题与研究边界

本轮只回答：YouTube 是否能作为 SI P0 主线，以评论为证据发现高价值用户痛点，并形成可审批 Action。

本轮不回答：

- 社媒部门最终认为哪些痛点高价值。
- 哪些频道和关键词代表完整市场。
- Momcozy 当前 Google Cloud 项目、合同、额度和法务审批状态。
- 未实测的真实评论规模、洞察准确率、成本和业务采纳率。
- Reddit 链路是否通过；Reddit 保持独立、并行、非阻塞验收。

证据分层：

| 层级 | 本轮证据 |
|---|---|
| 官方事实 | Google / YouTube 官方 API、政策、帮助中心和合规申请表，核验日期为 2026-08-14 |
| 本地事实 | 静态检查现有采集器、现有 JSON 样本和项目文档；未读取凭证、未发起真实 API 调用 |
| 产品推断 | 基于官方能力与 S1 目标提出的采集路径、数据契约和 Go/No-Go 门槛 |
| 未知 | 商业合同、合规受理结果、真实数据质量、业务口径和验收阈值 |

---

## 2. 本地 YouTube 资产审计

### 2.1 已验证事实

| 资产 | 静态检查结果 | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| [`youtube_collector.py`](../../tools/social/youtube_collector.py) | 使用 `streamers~youtube-scraper`，目标写明为 S2/S3 视频与关键词搜索 | 已有第三方视频发现代码 | 官方 API 已接入、评论可采、S1 可用或合规已通过 |
| [`youtube_20260813_040755.json`](../../data/processed/social/youtube_20260813_040755.json) | 有 3 条视频记录，包含标题、描述、视频 URL、观看/点赞/评论计数 | 至少发生过一次视频搜索结果落盘 | 评论正文、线程、回复、分页、coverage、稳定刷新和删除机制 |
| [`00_推进计划_批次2.md`](../00_推进计划_批次2.md) | 早期状态将 YouTube 标为 `CODE_UNVERIFIED` | 项目存在历史状态差异 | 后续样本已满足评论级验收 |

现有采集器在 V0 修复前暴露四项问题：

1. 数据对象错误：`YouTubeVideo` 只有视频标题、描述和计数，没有 `comment_id`、评论正文、线程或回复。该阻断项仍未解决。
2. 范围被伪装成事实：代码曾将每条记录的 `country_code` 和 `language` 固定为 `US` 和 `en`。V0 已将无内容级证据时的默认值改为 `unknown`。
3. 凭证治理不合格：模块曾在导入时读取 `~/.zshrc` 并把匹配到的 API 值写入进程环境。V0 已移除该行为；生产凭证仍需采用经批准的 runtime secret 注入方式。
4. 错误不可观测：写入数据库时曾捕获通用异常后直接 `pass`。V0 已改为显式抛出带 video ID 的错误。

因此，现有 3 条视频样本的证据等级仍是「第三方视频发现 smoke」，不能升级为「YouTube 评论连接器已验证」或「S1 已具备真实数据」。V0 离线验证只把第 2–4 项从已知代码缺陷降为后续生产配置/实测门，没有解决评论数据对象、来源权利和真实端到端验收。

### 2.2 本轮没有执行的操作

- 没有运行本地采集器，因为其 import 路径会读取个人 shell 配置。
- 没有读取或打印 API Key、`.env`、token 或其他凭证。
- 没有调用 Apify、YouTube API 或修改外部系统。
- 没有对现有数据库和 Reddit 工作台做写入。

---

## 3. 三条数据源方案的完整对比

### 3.1 对比结果

| 维度 | A. 官方 Data API 主源 | B. 官方 API + 获批供应商补充 | C. 现有 Apify-only |
|---|---|---|---|
| S1 评论级契合度 | 高：官方支持评论线程与回复 | 可能高：取决于供应商实际字段 | 当前低：本地实现只采视频 |
| 来源可追溯 | 高：`video_id`、`commentThread.id`、`comment.id`、官方 URL | 中到高：必须保留 provider 与原始 ID | 中：现有只保留视频 URL，评论证据不存在 |
| 覆盖可解释 | 中：可分页、记录错误，但搜索结果不是全网完整样本 | 中：需要逐源披露和去重 | 低：现有实现没有评论 coverage 与分页语义 |
| 政策证据 | 最清晰，但 derived metrics 仍需接受额外条款 | 复杂：官方政策、供应商合同和实际采集方式都要审 | 高风险：官方政策明确禁止取得 scraped YouTube data |
| 存储与删除 | 可按官方 30 天刷新/删除规则实现 | 需同时满足两套或多套约束 | 当前未见相关机制 |
| 配额可规划 | 高：搜索独立 100 次/日；评论等端点共享 10,000 units/日 | 中：还受供应商额度与价格影响 | 中：受 actor、平台变化、供应商费用影响 |
| 故障可诊断 | 高：官方错误码和分页状态明确 | 中：取决于 provider manifest | 低到中：V0 已让 DB 写入失败显式抛错，但空结果、HTTP 错误、分页和 quota 还没有真实端到端验证 |
| 锁定与返工 | 低到中：围绕官方资源模型构建 | 中：需 adapter 与 provider 差异层 | 高：当前 schema 是视频对象，切 S1 要重做核心契约 |
| P0 结论 | 推荐 | 条件性备选 | 不推荐作为 P0 主线 |

### 3.2 选择规则

选择 A，除非真实 UAT 证明官方 API 在已经批准的 P0 范围内存在无法接受、无法合法弥补的缺口。

B 只在以下条件全部满足时启用：

1. 明确官方 API 的具体缺口，而不是笼统追求更多数据。
2. 供应商提供数据来源、采集方式、许可、保存、删除、刷新和故障语义的书面证据。
3. 法务与采购确认其权利链适用于 Momcozy 的 Analytics & Reporting 用例。
4. 产品保留 provider、coverage 和来源差异，不把多源数据伪装成同质全量样本。

C 当前只保留为待处置实验资产，不作为 S1 的验收来源。若供应商无法证明获得 YouTube 书面许可或其他适用权利，不能把该路径推进到 P0。

---

## 4. 官方 API 能力与限制

### 4.1 视频发现

| 能力 | 官方边界 | P0 设计影响 |
|---|---|---|
| `playlistItems.list` | 每页最多 50 条，使用 `nextPageToken` 翻页，成本 1 unit | 已批准频道的 uploads playlist 作为稳定范围主路径 |
| `search.list` | 默认独立额度 100 calls/day，每次调用成本 1；额外分页也消耗调用 | 只用于有限关键词发现，不作为全网全量监测承诺 |
| `search.list` + `channelId` + `type=video` | 未配合内容所有者/本人过滤时最多 500 个视频 | 不能用它替代频道 uploads playlist 的历史遍历 |
| `pageInfo.totalResults` | 近似值，上限 1,000,000；官方要求不要用它生成分页 | Coverage 使用 page token、停止原因与已取页数，不用该字段声称完整规模 |
| `regionCode` | 返回可在指定国家观看的视频 | 只能作为搜索请求参数，不能当作上传者或评论者地理位置 |
| `relevanceLanguage` | 返回对指定语言最相关的结果，仍可能包含其他语言 | 必须单独识别文本语言；未知时保留 `unknown` |

### 4.2 评论与回复

| 能力 | 官方边界 | P0 设计影响 |
|---|---|---|
| `commentThreads.list` | 可按 `videoId` 获取线程；每页 1–100；支持 `time` / `relevance`、`pageToken` 和 `plainText`；成本 1 unit | 对选中视频采集顶层评论；首轮按 `time` 保证口径清晰 |
| `commentThreads.list.searchTerms` | 只返回包含指定词的评论 | 不作为主要采集条件，否则会漏掉未使用预设词的真实痛点 |
| 线程内 replies | `commentThread` 不保证包含全部回复 | 不能把内嵌 replies 直接写成完整回复覆盖 |
| `comments.list(parentId)` | 可按顶层评论 ID 拉取回复；每页 1–100；成本 1 unit | 对高价值候选线程和 UAT 固定样本补齐全部回复，并记录覆盖 |
| `commentsDisabled` | 视频关闭评论时返回 403 错误 | 状态写为 `comments_disabled`，不得写成 `0 comments` |
| Made for Kids | YouTube 会关闭评论功能 | 记录为平台能力不可用；不能据此推断没有用户痛点 |

### 4.3 2026 年 6 月配额口径

官方当前默认分桶为：

- `search.list`：独立 100 calls/day，每次 1。
- `videos.insert`：独立 100 calls/day，与本 P0 无关。
- 其他端点合计：10,000 units/day；`commentThreads.list`、`comments.list`、`playlistItems.list`、`videos.list` 均为 1 unit。
- 无效请求至少消耗 1，额外分页请求也消耗额度。

这意味着配额的主要规划变量不是旧口径中的「一次搜索 100 units」，而是每日搜索调用次数、选中视频数量、评论页数、需补齐回复的线程数和刷新频率。P0 应根据业务冻结范围后再估算，当前不编造日调用量。

---

## 5. 推荐采集范围与执行路径

### 5.1 P0 范围原则

P0 是评论级用户痛点洞察，不是视频热度 Dashboard。范围按以下顺序冻结：

1. 产品/SKU 与使用场景：待业务确认。
2. 市场：业务目标可设为美国，但数据层不能把观看可用地区等同于评论者所在地。
3. 语言：业务目标可设为英语，但采集结果需要文本级语言识别并允许 `unknown`。
4. 固定频道：品牌、竞品、专业评测、母婴创作者的批准清单。
5. 关键词发现：产品名、品类词、场景词、问题词和排除词的版本化清单。
6. 时间范围：用明确的 `publishedAfter` / 频道上传时间边界，不承诺历史全量。
7. 评论范围：选中视频的全部可访问顶层评论；高价值候选与 UAT 样本补齐回复。

P0 不采集或保存视频、音频，不默认抓取 transcript。若后续需要字幕或媒体内容，必须单独验证官方能力、版权和保存边界。

### 5.2 发现与刷新流程

| 阶段 | 输入 | 输出 | 停止条件 |
|---|---|---|---|
| 频道发现 | approved channel IDs | uploads playlist 与新视频 ID | 到达批准时间边界或没有 `nextPageToken` |
| 关键词发现 | 版本化 query、时间范围、region/language 请求参数 | bounded video candidates | 达到搜索调用预算、页数上限或没有 `nextPageToken` |
| 视频补齐 | video IDs | 状态、发布时间、频道、标题、评论计数等 | 所有候选已处理或错误有记录 |
| 顶层评论 | 可访问 video IDs | comment threads、顶层评论、reply count | 没有 `nextPageToken` 或明确停止原因 |
| 回复补齐 | 选定 top-level comment IDs | 完整可访问回复 | 没有 `nextPageToken` 或明确停止原因 |
| 刷新/删除 | 到期记录和删除请求 | 更新、删除或 tombstone | 每条到期数据均有处理结果 |

---

## 6. YouTube P0 最小数据契约

### 6.1 `SourceScope`

| 字段 | 类型/示例 | 规则 |
|---|---|---|
| `scope_id` | string | 一次批准范围的稳定 ID |
| `scope_version` | string | 频道、关键词、时间、市场或语言变化必须升级 |
| `provider` | `youtube_data_api` | 不用笼统的 `youtube` 掩盖来源方式 |
| `provider_mode` | `official_api` / `third_party_pending_approval` | 第三方未获批前不能进入生产范围 |
| `channel_ids` | string[] | 业务签字后的固定频道清单 |
| `queries` | object[] | 含 query、排除词和版本 |
| `published_after` / `published_before` | timestamp | 明确时间边界 |
| `region_code_request` | `US` | 只描述请求参数，不写入评论者地理事实 |
| `relevance_language_request` | `en` | 只描述相关性偏好 |
| `approved_by` / `approved_at` | string / timestamp | 记录业务、数据、法务批准证据 |

### 6.2 `VideoSource`

| 字段 | 规则 |
|---|---|
| `video_id`、`channel_id`、`source_url` | 官方稳定标识和可回看来源 |
| `discovery_method` | `channel_uploads` 或 `keyword_search` |
| `discovery_query_id` | 仅搜索发现时填写 |
| `title`、`description`、`published_at` | 原始 API Data；进入 30 天刷新/删除机制 |
| `comment_count` | 官方快照，保留 `fetched_at`；不能代替实际评论覆盖 |
| `made_for_kids_status` | 可得则记录；未知不推断 |
| `comments_access_status` | `enabled`、`disabled`、`unavailable`、`unknown` |
| `fetched_at`、`refreshed_at`、`refresh_or_delete_at` | 强制保存生命周期时间 |

### 6.3 `CanonicalMention`：评论级核心对象

| 字段 | 规则 |
|---|---|
| `mention_id` | 内部稳定 ID，建议由 provider + comment ID 派生 |
| `provider` | `youtube_data_api` |
| `video_id`、`comment_thread_id`、`comment_id` | 保留官方标识 |
| `parent_comment_id` | 顶层为空，回复指向顶层评论 |
| `is_top_level` | boolean |
| `source_url` | 能回到对应视频/评论的 URL；无法深链时至少回到视频并保留官方 ID |
| `text_original` | 原始评论文本；受 30 天刷新/删除约束 |
| `published_at`、`updated_at`、`fetched_at` | 区分源时间与采集时间 |
| `like_count`、`reply_count` | 源快照，含 `fetched_at` |
| `detected_language` | 内容级识别结果，允许 `unknown`；不得由请求参数硬填 |
| `author_reference` | 默认最小化；仅在确有去重需求时保存伪名化标识，不建立用户画像 |
| `raw_reference` / `etag` | 用于回放、刷新和变更检测，不保存密钥 |
| `refresh_or_delete_at` | 生命周期硬字段 |
| `deletion_status` | `active`、`refresh_due`、`deleted`、`source_missing` |

### 6.4 `CoverageReport`

| 字段 | 规则 |
|---|---|
| `coverage_report_id`、`scope_id`、`run_id` | 关联批准范围与采集运行 |
| `videos_discovered` / `videos_hydrated` | 区分发现与成功补齐 |
| `videos_comments_enabled` / `comments_disabled` | 单独统计，不能合并为零评论 |
| `thread_pages_fetched` / `threads_fetched` | 顶层评论覆盖 |
| `replies_expected` / `replies_fetched` | 回复覆盖；未知时不能写 100% |
| `next_page_token_present` | 停止时是否仍有下一页 |
| `stop_reason` | `scope_complete`、`page_cap`、`quota_exhausted`、`policy_blocked` 等 |
| `error_code` / `error_count` | 保留官方错误语义和次数 |
| `coverage_status` | 使用第 7 节枚举 |
| `started_at` / `ended_at` | 运行时间边界 |

### 6.5 `Evidence`、`Insight` 与 `Action`

| 对象 | 最小字段 | 约束 |
|---|---|---|
| `Evidence` | `evidence_set_id`、`mention_ids`、`source_urls`、`coverage_report_id`、支持/反证、生成时间 | 每条结论可回到评论与覆盖报告 |
| `Insight` | `insight_id`、`pain_taxonomy_version`、`pain_category`、场景、后果、证据、反证、不确定性、人工状态 | 明确标为产品自有推断，不冒充 YouTube 官方指标 |
| `Action` | `action_id`、`insight_id`、`evidence_set_id`、类型、owner、预期结果、审批、有效期、回填 | P0 只生成待审批 Action，不自动对外发布或回复 |

痛点分类只能针对评论内容和场景，不得推断或聚合评论者的健康状态、怀孕/哺乳身份、年龄、种族、宗教、政治倾向、性取向等受保护属性。

---

## 7. Coverage 与错误语义

### 7.1 必须使用的状态

| `coverage_status` | 含义 | 是否可写成完成 |
|---|---|---|
| `complete_for_defined_scope` | 在已定义范围内没有下一页，且预定回复范围已处理 | 是，但只能说「定义范围内完成」 |
| `partial_page_cap` | 到达产品设置的页数或评论数上限 | 否 |
| `comments_disabled` | API 返回评论关闭 | 否；也不能写成零痛点 |
| `made_for_kids_no_comments` | 视频/频道因 Made for Kids 不提供评论 | 否 |
| `video_unavailable` | 视频删除、私密、地区或其他原因不可访问 | 否 |
| `permission_denied` | 授权或权限不足 | 否 |
| `quota_exhausted` | 搜索桶或共享 quota 耗尽 | 否 |
| `transient_error` | 网络、服务或可重试错误 | 否 |
| `deleted_or_refreshed` | 生命周期任务已按规则处理 | 不适用于采集完整度 |
| `zero_comments_confirmed` | 评论功能可用、分页结束且实际返回零条 | 只表示该定义范围内零评论 |

### 7.2 禁止表述

- 禁止「YouTube 全网用户都在讨论……」。
- 禁止把 `pageInfo.totalResults` 当成精确总量。
- 禁止把 `regionCode=US` 写成「美国用户」。
- 禁止把 `relevanceLanguage=en` 写成「全部英语」。
- 禁止把评论关闭、视频不可用、quota 用尽、抓取失败写成零提及。
- 禁止直接比较 YouTube 与 Reddit 的绝对提及量而不披露各自范围和 coverage。

---

## 8. 合规、保存与隐私门槛

### 8.1 官方政策事实

1. Developer Policies 原则上禁止 API Client 使用 API Data 创建新的 derived data 或 metrics；2026-06-01 生效的额外政策为接受 amendment 的 Analytics & Reporting 用例开放特定例外。
2. 额外政策明确列出内容分类、标签和 viewer sentiment，并允许对 Data API 评论执行 NLP；但具体产品仍需在申请表中准确描述，由 YouTube 判断是否符合。
3. 被接受的 derived metrics 最长可保存 36 个月；视频标题、创作者名称、描述和评论文本仍必须执行 30 天刷新或删除。
4. 用户要求删除相关数据时，应尽快处理并在 7 个日历日内完成。
5. API Client 需要公开且准确的隐私政策、适当安全控制、来源标识和 YouTube 归因。
6. Developer Policies 禁止直接或间接抓取 YouTube Applications，也禁止获得 scraped YouTube data；公共搜索引擎例外不适用于本产品的默认假设。

### 8.2 对 P0 的直接要求

| 要求 | P0 证据 |
|---|---|
| 用例批准 | 合规申请/审计结果，准确写明「内部品牌社媒团队、公开评论 NLP、内容级痛点分类、跨视频聚类、Evidence → Action、无用户画像」 |
| 隐私与条款 | 可访问的 Privacy Policy、产品 Terms、删除说明和 Google Privacy Policy 链接 |
| 产品截图 | 合规申请需要的首页、YouTube branding、Dashboard/feature 截图；无生产凭证时使用批准的 review 环境 |
| 数据生命周期 | 原始标题/描述/评论的 `refresh_or_delete_at`、任务日志、删除请求定位与证据 |
| 敏感属性 | 数据模型、prompt、评审规则和输出检查均禁止用户健康/孕产等属性推断 |
| 自有指标披露 | 痛点类别、价值评分、聚类和建议明确标为 Momcozy 产品推断，不是 YouTube 指标 |
| 供应商 | 逐项核验来源方式、许可和合同；Apify token 或技术成功不等于商业/平台授权 |

法务与 YouTube 尚未对本产品具体用例给出结论，因此本文不能把「痛点聚类已获允许」写成事实。这一项是产品级硬门槛，不是上线后的补充文档。

---

## 9. YouTube P0 Go/No-Go

### 9.1 硬门槛

| 门槛 | Go 证据 | 当前状态 | 未满足时影响 |
|---|---|---|---|
| G1 业务范围 | 产品/SKU、频道、关键词、排除词、时间、市场、语言、taxonomy 获业务签字 | 未知 | No-Go |
| G2 来源与合规 | 官方 API 项目、Privacy/Terms、Analytics & Reporting amendment/审核结果或等效书面结论 | 未知 | No-Go |
| G3 评论级连接 | 官方 `commentThreads.list` 可读取真实评论；`comments.list` 可按既定规则补回复 | 未验证 | No-Go |
| G4 凭证与错误 | approved secret 注入；不读个人 shell；无静默异常；quota/错误可见 | 部分满足：V0 源码/行为检查通过，runtime secret 和真实错误码未验证 | No-Go |
| G5 数据契约 | 评论 ID、父子关系、来源 URL、时间、原始引用、幂等、刷新/删除字段齐全 | 未实现 | No-Go |
| G6 Coverage | 分页、reply coverage、停止原因和错误状态可区分；无地理/语言硬填 | 未实现 | No-Go |
| G7 生命周期 | 30 天刷新/删除和 7 日删除请求具备可验证日志 | 未实现 | No-Go |
| G8 洞察安全 | 内容级痛点、Evidence、反证、不确定性、人工确认；不做敏感用户画像 | 待设计验证 | No-Go |
| G9 Action 闭环 | 人工确认 → 待审批 Action → 批准/驳回 → 结果回填可追踪 | 待业务确认 | No-Go |
| G10 UAT | 固定真实范围和人工标注集通过；阈值由业务先签字再执行 | 未定义 | No-Go |

只要任一硬门槛未通过，YouTube 主线就是 SI P0 产品级 No-Go。Reddit 通过不能替代；Reddit 自身失败也不自动证明 YouTube 失败。

### 9.2 UAT 最小剧本

1. 业务冻结一个受控真实范围：频道、查询、时间、产品和语言规则。
2. 数据/研发用官方 API 跑完整链路，保留请求类别、页数、错误、quota、停止原因和刷新时间；不在报告中记录密钥。
3. 对所有选中视频区分：评论可用且抓取完成、评论关闭、视频不可用、部分抓取、错误。
4. 对 UAT 指定线程使用 `comments.list` 补齐回复，人工核对父子关系和 reply coverage。
5. 社媒部门在不知道模型评分的情况下评审预先提供的「好洞察/无用洞察」与真实输出。
6. 每条合格 Insight 必须有直接证据、反证、Coverage、不确定性与内容级痛点标签。
7. 只有人工确认的 Insight 才能生成待审批 Action；记录批准、驳回、执行和结果。
8. 使用业务预先签字的验收阈值判定，不在实测后倒推一个容易通过的阈值。

当前不建议写死评论数、precision、recall、周期或成本阈值；这些数字必须由真实范围、baseline、漏报/误报偏好和业务样本共同确定。

---

## 10. 下一决策节点

下一节点是「决策门 2：YouTube 数据、权利与覆盖确认」，不是立即开发完整 Agent。

执行状态：已于 2026-08-14 启动并形成三份预填评审稿：

- [`SourceScope v1 业务确认稿`](2026-08-14_YouTube_P0_SourceScope_v1_业务确认稿.md)
- [`Rights Matrix 法务评审稿`](2026-08-14_YouTube_P0_Rights_Matrix_法务评审稿.md)
- [`Capability Manifest 技术验证稿`](2026-08-14_YouTube_P0_Capability_Manifest_技术验证稿.md)

三份材料已将已知事实、建议默认和待确认项分开。当前只完成评审材料准备，不代表业务、法务或技术门已经通过。

需要四方完成一张签字表：

| 参与方 | 必须回答的问题 | 产出 |
|---|---|---|
| 社媒部门 | 首期产品、频道、关键词、排除词、市场、语言、好/坏洞察、Action 类型 | `SourceScope v1` + 标注样本 |
| 数据/研发 | 官方 API 项目、评论/回复能力、分页、quota、错误、secret、刷新/删除实现方式 | capability manifest + 技术验证计划 |
| 法务/隐私 | 评论 NLP、跨视频痛点聚类、内部 Analytics & Reporting、供应商来源、敏感属性禁区 | rights matrix + 书面结论/申请记录 |
| 产品 | 唯一 P0、Coverage 状态、Evidence Gate、Go/No-Go、Reddit 非阻塞关系 | canonical PRD 变更单 |

该节点的停止条件：G1–G2 有明确结果，G3–G7 有可执行验证方案和 owner。未满足时不进入完整 S1 → Action 开发。

---

## 11. 官方来源索引

- [YouTube Data API — `commentThreads.list`](https://developers.google.com/youtube/v3/docs/commentThreads/list)
- [YouTube Data API — `commentThreads` resource 与回复限制](https://developers.google.com/youtube/v3/docs/commentThreads)
- [YouTube Data API — `comments.list`](https://developers.google.com/youtube/v3/docs/comments/list)
- [YouTube Data API — `search.list`](https://developers.google.com/youtube/v3/docs/search/list)
- [YouTube Data API — `playlistItems.list`](https://developers.google.com/youtube/v3/docs/playlistItems/list)
- [YouTube Data API — Quota Calculator](https://developers.google.com/youtube/v3/determine_quota_cost)
- [YouTube API Services — Developer Policies](https://developers.google.com/youtube/terms/developer-policies)
- [YouTube API Services — Additional policies for derived metrics and data storage](https://developers.google.com/youtube/terms/derived-metrics-policy)
- [YouTube API Services — Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service)
- [YouTube API Services — Audit and quota extension form](https://support.google.com/youtube/contact/yt_api_form?hl=en-GB)
- [YouTube Help — Made for Kids 的功能限制](https://support.google.com/youtube/answer/9610989?hl=en)

以上外部事实核验日期均为 2026-08-14。平台政策和配额可能变化，进入实现和上线评审时必须重新核验。
