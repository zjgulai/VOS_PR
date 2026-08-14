---
name: youtube-p0-rights-matrix
description: YouTube P0 的数据来源、API 用例、derived metrics、保存删除、隐私、敏感属性、供应商与产品展示权利矩阵。
date: 2026-08-14
verified_at: 2026-08-14
status: 待法务、隐私与数据负责人评审
stage: 决策门 2——数据、权利与覆盖
---

# YouTube P0 Rights Matrix 法务评审稿

## 0. 评审结论入口

本文不是法律意见。它把产品用途拆成可逐项判定的权利问题，避免用「API 能调用」「供应商有 token」或「数据公开可见」替代商业和平台授权。

当前产品级状态：`BLOCKED_PENDING_REVIEW`。

解除阻断至少需要：

1. YouTube API Client、Google Cloud project、Privacy Policy、Terms 和数据删除机制的责任主体明确。
2. 以准确用例提交或确认 Analytics & Reporting / derived metrics amendment：公开评论 NLP、内容级痛点分类、跨视频聚类、Evidence → Action、内部品牌社媒团队使用、无用户画像。
3. 法务确认原始 API Data、派生结果、删除请求、来源展示和敏感属性的处理方式。
4. Apify 路径取得足以覆盖实际采集方式和 Momcozy 用途的书面权利证据，否则保持阻断。

---

## 1. 判定状态

| 状态 | 含义 | 是否可进入真实 P0 |
|---|---|---|
| `APPROVED` | 权利来源、产品用途、保存删除和责任人均有书面证据 | 是 |
| `APPROVED_WITH_CONDITIONS` | 仅在明确范围、期限或展示条件下可用 | 满足条件后可以 |
| `PENDING_REVIEW` | 官方事实已知，但 Momcozy 的实际主体、用例或申请结果未知 | 否 |
| `BLOCKED` | 当前路径与政策冲突，或供应商不能提供必要权利证据 | 否 |
| `OUT_OF_SCOPE` | 产品主动排除，不进入 P0 | 不适用 |

「公开数据」不是判定状态。每项都必须落到以上五个状态之一。

---

## 2. 权利矩阵

| ID | 活动/数据 | 官方或合同事实 | P0 拟用方式 | 必需证据 | 责任角色 | 当前状态 | 法务决定 |
|---|---|---|---|---|---|---|---|
| R1 | YouTube Data API Client | API Client 受 YouTube API Services Terms 与 Developer Policies 约束 | 内部 Social Intelligence 产品读取公开资源 | Google Cloud project、API Client 名称、主体、负责人、适用条款记录 | 数据负责人 + 法务 | `PENDING_REVIEW` | 待填写 |
| R2 | `search.list` 视频发现 | 官方支持 query、频道、时间、地区、语言；结果不是全量市场样本 | 有限发现 M9/M5 Smart 相关视频 | API 项目、query 范围、quota 预算、Coverage 展示 | 数据负责人 | `PENDING_REVIEW` | 待填写 |
| R3 | 频道 uploads 范围 | 官方 API 可通过频道 uploads playlist 和 `playlistItems.list` 读取公开视频列表 | approved channel ID 的稳定发现主路径 | 频道批准清单、来源核验、采集时间边界 | 社媒 + 数据 | `PENDING_REVIEW` | 待填写 |
| R4 | 公开视频元数据 | 标题、描述、频道名等属于 API Data | 选择评论范围并展示来源上下文 | 字段清单、30 天刷新/删除任务、来源归因 | 数据 + 隐私 | `PENDING_REVIEW` | 待填写 |
| R5 | 公开评论线程 | `commentThreads.list` 可读取公开视频的公开评论线程 | S1 评论级证据主对象 | API Client 用例、字段清单、评论深链/视频链接、生命周期 | 数据 + 法务 | `PENDING_REVIEW` | 待填写 |
| R6 | 公开回复 | 线程不一定包含全部回复；`comments.list(parentId)` 可补齐 | UAT 指定和高价值候选线程补齐上下文 | 回复范围规则、Coverage、原始数据生命周期 | 数据 + 法务 | `PENDING_REVIEW` | 待填写 |
| R7 | 评论 NLP | 额外政策列出 Data API 评论 NLP 和 viewer sentiment 示例，但要求接受 amendment | 内容级痛点标签、情感、场景和证据提取 | Analytics & Reporting 用例提交内容、YouTube 接受结果 | 法务 + 产品 | `PENDING_REVIEW` | 待填写 |
| R8 | 跨视频痛点聚类 | 官方没有逐字定义本产品的跨视频痛点聚类；可能属于 derived metrics/analytics | 聚合多个评论形成痛点 Insight | 在申请中准确描述聚类输入、输出、用户、展示和保存；书面结论 | 法务 + 产品 | `PENDING_REVIEW` | 待填写 |
| R9 | 自有评分与标签 | 被接受的额外政策允许特定自有分析，但必须与 YouTube API Data 区分 | `pain_category`、价值判断、模型置信度、Action 建议 | UI/报告披露文案、数据字典、评审截图 | 产品 + 法务 | `PENDING_REVIEW` | 待填写 |
| R10 | 原始标题/描述/评论文本 | 非授权 API Data 和评论文本仍需执行 30 天刷新或删除 | Evidence、人工复核和回放 | `refresh_or_delete_at`、任务日志、刷新/删除结果、失败恢复 | 数据 + 隐私 | `PENDING_REVIEW` | 待填写 |
| R11 | 派生指标长期保存 | 用例被接受后，特定 statistical/derived metrics 最长可保存 36 个月 | 保存痛点标签、聚类结果和评审结果 | 受理结果、字段级分类、保存期限表、到期任务 | 法务 + 数据 | `PENDING_REVIEW` | 待填写 |
| R12 | 用户删除请求 | API Client 必须提供删除请求方式；相关数据应尽快且在 7 个日历日内删除 | 按 author/comment/source 定位本地原始和派生数据 | Privacy Policy、请求入口、定位关系、删除日志和完成时限 | 隐私 + 数据 | `PENDING_REVIEW` | 待填写 |
| R13 | 源删除/下架同步 | 本地 API Data 应与 YouTube 当前状态保持一致 | 刷新时删除或标记 source missing | source refresh、tombstone、Evidence 失效和重新计算规则 | 数据 | `PENDING_REVIEW` | 待填写 |
| R14 | 健康/孕产等敏感属性 | 额外政策禁止根据 API Data 推断受保护属性，包括 health status | 只做评论内容级痛点，不建立用户画像 | schema、prompt、输出规则、评审 checklist、违规样本测试 | 隐私 + 产品 | `PENDING_REVIEW` | 待填写 |
| R15 | 作者标识 | 评论资源可能含公开作者信息；数据最小化原则仍适用 | 默认不展示用户画像；必要时使用作用域内伪名化引用 | 字段必要性说明、脱敏方式、访问控制和删除定位 | 隐私 + 数据 | `PENDING_REVIEW` | 待填写 |
| R16 | YouTube 来源和品牌归因 | API Client 需要适当归因，不得伪造来源或删除作者/权利标识 | Evidence 展示来源链接，并区分自有推断 | Branding Guidelines 核对、页面截图、披露文案 | 产品 + 法务 | `PENDING_REVIEW` | 待填写 |
| R17 | Privacy Policy | API Client 需公开且准确说明收集、存储、使用和分享 | 对内部或外部使用者披露 YouTube 数据处理 | 可访问 URL、YouTube 章节、Google Privacy Policy 链接、删除说明 | 隐私 + 法务 | `PENDING_REVIEW` | 待填写 |
| R18 | 产品 Terms | 合规申请表要求 Terms 文档证据 | 明确产品使用边界和来源责任 | 可访问 URL 或批准文档、页面截图 | 法务 + 产品 | `PENDING_REVIEW` | 待填写 |
| R19 | 安全控制 | API Client 需要合理的管理、组织、技术和物理控制 | secret、API Data、日志和导出受控 | secret manager、RBAC、加密、日志脱敏、事件响应 | 安全 + 数据 | `PENDING_REVIEW` | 待填写 |
| R20 | Apify YouTube actor | YouTube Developer Policies 禁止直接/间接抓取或取得 scraped YouTube data；供应商实际权利未知 | 当前本地代码用于视频发现 | 采集方式、YouTube 书面许可或其他适用权利、DPA、保存删除、审计权 | 采购 + 法务 | `BLOCKED` | 待填写 |
| R21 | TikHub YouTube | 本地文档称当前 Key 的 YouTube search 返回 0；商业权利未核验 | 不作为 v1 主源 | 合同、产品条款、字段来源、实际能力 | 采购 + 法务 + 数据 | `OUT_OF_SCOPE` | 待填写 |
| R22 | 视频/音频下载 | API/平台条款不因元数据访问自动授予复制媒体内容的权利 | P0 不下载、不缓存视频或音频 | 如未来启用，需独立权利评审 | 法务 + 产品 | `OUT_OF_SCOPE` | 不进入 P0 |
| R23 | transcript/字幕 | 当前产品未证明官方可用性和保存权利 | P0 不采集 transcript | 如未来启用，需独立 API、版权和生命周期评审 | 法务 + 数据 | `OUT_OF_SCOPE` | 不进入 P0 |
| R24 | 自动评论/回复/发布 | P0 只生成待审批 Action | 不调用任何外部写接口 | 产品和连接器均无外发能力；UAT 负向测试 | 产品 + 安全 | `OUT_OF_SCOPE` | 不进入 P0 |

---

## 3. Analytics & Reporting 用例说明草案

以下文字用于法务和产品准备申请，不代表已经提交或被接受：

> Momcozy 的内部 Social Intelligence API Client 面向获准的品牌社媒、产品和 PR 人员。产品使用 YouTube Data API 获取限定频道和限定关键词发现范围内的公开视频元数据、公开评论线程及必要回复。系统对评论内容执行 NLP，识别与指定 Momcozy 产品相关的使用场景、问题和痛点，将每个派生 Insight 链接回原始 YouTube 来源与 Coverage 报告，由人工确认后生成待审批业务 Action。产品不推断或建立评论者的年龄、种族、宗教、政治倾向、性取向、健康状态、怀孕或哺乳身份等用户画像；不自动评论、发布或联系用户；原始评论文本和相关 API Data 执行 30 天刷新或删除，自有派生结果的保存期限以 YouTube 接受结果为准。

法务评审时不能把「痛点聚类」缩写成笼统的「sentiment」。申请必须准确描述跨评论/跨视频聚类、业务用户、页面展示、Evidence、Action 和保存方式。

---

## 4. 数据分类与保存

| 数据类别 | 示例字段 | 建议分类 | 最长保存建议 | 决策依据 |
|---|---|---|---|---|
| 原始 API Data | 视频标题、描述、频道名、评论文本 | YouTube API Data | 30 天内刷新或删除 | 官方 Developer Policies / derived metrics policy |
| 原始标识 | `video_id`、`comment_id`、`thread_id` | API Data / 删除定位 | 与刷新删除规则一致；具体保留待法务确认 | 需要定位源和删除请求 |
| 作者引用 | `author_channel_id` 或显示名 | 用户相关数据 | 默认不保存显示名；必要标识伪名化并纳入删除 | 数据最小化 + 删除定位 |
| 源指标快照 | views、likes、comment count | API statistics | 默认 30 天；只有受理结果覆盖时才延长 | 额外条款可能允许最长 36 个月 |
| 派生标签 | pain、scenario、sentiment | 自有 derived data | 受理前不超过原始数据生命周期；受理后按批准范围 | 不能先假设获批 |
| Insight | 事实、推断、反证、不确定性 | 自有产品结果 | 与 Evidence 有效性联动 | 源失效时需重算或降级 |
| Action 与人工决定 | 批准、驳回、执行、结果 | 内部业务记录 | 按内部业务记录政策；不得保留已删除源的违规原文 | 与 API Data 分离保存 |
| Coverage / 审计日志 | 页数、错误、停止原因、任务结果 | 系统审计数据 | 按安全与审计政策 | 不保存 secret 或完整评论正文 |

保存期限最终表必须由法务、隐私和数据共同签字。不能把 36 个月作为所有数据的默认期限。

---

## 5. 产品展示与禁用规则

### 5.1 必须展示

- YouTube 来源链接或可定位来源的官方 ID。
- API Data 与 Momcozy 自有标签、评分、聚类和建议的明确区分。
- SourceScope、时间范围、平台范围、Coverage、缺失页/回复和错误状态。
- `published_at`、`collected_at`、`refreshed_at`，避免旧数据被当成当前事实。
- 原始内容失效或已删除时的 Evidence 降级状态。

### 5.2 禁止展示或生成

- 「美国妈妈认为……」：除非有独立合法证据确认评论者位置和身份。
- 「哺乳期用户」「产后用户」等由评论推断的个人健康/孕产身份。
- 「YouTube 全网」「全部英语评论」「完整市场份额」等超出 Coverage 的结论。
- 将痛点分、情感分或价值分展示为 YouTube 官方指标。
- 已删除评论的长期原文副本。
- 未经人工批准的外部回复、发布或用户联系。

---

## 6. Apify 供应商证据清单

在 R20 从 `BLOCKED` 变更前，采购和法务至少需要获得：

1. actor 实际数据取得方式，不接受只有字段列表和营销页面。
2. 数据取得符合 YouTube 条款的书面依据，包括 YouTube 许可或其他适用权利。
3. Momcozy 商业 Analytics & Reporting 用途是否在授权范围内。
4. 原始内容、作者信息、派生分析、保存期限和删除请求的合同条款。
5. 数据处理地点、分包方、访问控制、事故通知和 DPA。
6. provider schema 变化、限流、缺失和删除同步的服务承诺。
7. 审计证据和合同终止后的数据删除方式。

技术调用成功、actor `LIVE`、HTTP 200/201 或已有 3 条视频样本均不能替代以上证据。

---

## 7. 法务签字表

| 决策项 | 推荐决定 | 最终决定 | 证据链接/编号 | Owner | 日期 |
|---|---|---|---|---|---|
| Data API API Client 主体与项目 | 只使用批准的公司项目 | 待填写 | 待填写 | 数据 + 法务 | 待填写 |
| Analytics & Reporting 用例 | 按第 3 节准确提交 | 待填写 | 待填写 | 产品 + 法务 | 待填写 |
| 评论 NLP | 受理后按条件启用 | 待填写 | 待填写 | 法务 | 待填写 |
| 跨视频痛点聚类 | 在申请中单独描述并取得明确结论 | 待填写 | 待填写 | 法务 | 待填写 |
| 原始 API Data | 30 天刷新或删除 | 待填写 | 待填写 | 隐私 + 数据 | 待填写 |
| 派生结果 | 只按获批范围和期限保存 | 待填写 | 待填写 | 法务 + 数据 | 待填写 |
| 用户删除请求 | 尽快且不超过 7 个日历日 | 待填写 | 待填写 | 隐私 | 待填写 |
| 敏感属性 | 禁止推断和画像 | 待填写 | 待填写 | 隐私 + 产品 | 待填写 |
| Apify | 证据不足前保持 `BLOCKED` | 待填写 | 待填写 | 采购 + 法务 | 待填写 |
| 视频/音频/transcript | `OUT_OF_SCOPE` | 待填写 | 待填写 | 产品 + 法务 | 待填写 |

签字完成标准：R1–R19 每项有明确状态和证据；R20 保持阻断或取得足以解除阻断的书面证据；R22–R24 明确不进入 P0。

---

## 8. 来源与关联材料

官方来源：

- [YouTube API Services Developer Policies](https://developers.google.com/youtube/terms/developer-policies)
- [Additional policies for derived metrics and data storage](https://developers.google.com/youtube/terms/derived-metrics-policy)
- [YouTube API Services Terms of Service](https://developers.google.com/youtube/terms/api-services-terms-of-service)
- [YouTube API audit and quota extension form](https://support.google.com/youtube/contact/yt_api_form?hl=en-GB)
- [YouTube Data API `commentThreads.list`](https://developers.google.com/youtube/v3/docs/commentThreads/list)
- [YouTube Data API `comments.list`](https://developers.google.com/youtube/v3/docs/comments/list)

关联材料：

- [`YouTube P0 SourceScope v1`](2026-08-14_YouTube_P0_SourceScope_v1_业务确认稿.md)
- [`YouTube P0 Capability Manifest`](2026-08-14_YouTube_P0_Capability_Manifest_技术验证稿.md)
- [`YouTube P0 定向 Deep Research 与数据契约建议`](2026-08-14_YouTube_P0定向DeepResearch与数据契约建议.md)

官方事实核验日期为 2026-08-14。实际项目、合同、申请和法务状态均未核验，必须以签字证据更新本文。
