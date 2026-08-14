---
name: youtube-p0-capability-manifest
description: YouTube P0 官方 API 连接器的能力清单、字段映射、错误语义、Coverage、生命周期、验证阶段、验收证据与当前缺口。
date: 2026-08-14
status: V0 fixture-only 已通过，V1 未授权
stage: 决策门 2——数据、权利与覆盖
manifest_version: 1.0-draft
---

# YouTube P0 Capability Manifest 技术验证稿

## 0. 当前技术结论

| 项目 | 当前状态 | 证据层级 |
|---|---|---|
| 官方 YouTube Data API 文档能力 | 已核验 | 官方文档，只读研究 |
| Google Cloud / YouTube API 项目 | 未核验 | 未读取凭证或项目配置 |
| 官方视频发现连接器 | 未实现或未定位到可复用实现 | 本地代码搜索 |
| 官方评论线程连接器 | 未实现或未定位到可复用实现 | 本地代码搜索 |
| 官方回复补齐 | 未实现或未定位到可复用实现 | 本地代码搜索 |
| 当前 `youtube_collector.py` | 视频发现能力未变；V0 已移除个人 profile 读取、US/en 硬填和数据库错误吞没 | 行为测试 + 静态检查 |
| S1 评论数据 | 未验证 | 样本无评论正文、thread/reply ID |
| Coverage | V0 完成 10 类状态映射；真实分页和 CoverageReport 未实现 | 合成 fixture |
| 30 天刷新/删除 | V0 完成 3 类定位/动作 fixture；真实调度和删除未实现 | 合成 fixture |
| 产品级判断 | `NO_GO` | V0 通过不解除 G2、G3、G5–G10 |

本 Manifest 定义“需要证明什么”，不授权读取个人凭证、调用真实 API 或修改生产数据。真实只读连接测试必须在 Rights Matrix 和执行审批通过后运行。

---

## 1. 连接器身份与范围

| 字段 | v1 值 | 状态 |
|---|---|---|
| `provider` | `youtube_data_api` | 已定义 |
| `strategy` | `official_api` | 已定义 |
| `use_case` | `analytics_and_reporting_comment_pain_insight` | 待法务确认 |
| `scope_id` | `scope_youtube_p0_pumping_us_en_v1` | 待业务确认 |
| `connector_owner` | 数据/研发负责人角色 | 具体人员待指定 |
| `business_owner` | 社媒负责人角色 | 具体人员待指定 |
| `legal_owner` | 法务/隐私负责人角色 | 具体人员待指定 |
| `runtime_environment` | 公司批准环境 | 待指定 |
| `secret_source` | approved secret manager/runtime injection | 待指定 |
| `write_capability` | 禁止；P0 只读 | 硬约束 |

P0 连接器不得读取 `~/.zshrc`、用户 shell profile、仓库 `.env` 或源代码中的 token。验证报告只记录项目的脱敏引用，不记录 API Key。

---

## 2. 来源方案状态

| 方案 | 用途 | 当前状态 | 进入 P0 的条件 |
|---|---|---|---|
| YouTube Data API | 主源：频道、视频、评论线程、回复 | `RECOMMENDED_PENDING_ACCESS` | Rights Matrix 通过 + 官方项目只读连接验证 |
| Apify `streamers~youtube-scraper` | 当前实验视频发现 | `BLOCKED_FOR_P0` | 供应商权利证据与评论能力均通过；仍不替代官方 derived metrics 门 |
| TikHub YouTube | 当前 Key 的 search 曾返回 0 | `OUT_OF_SCOPE_V1` | 重新评审合同、字段来源和稳定性后另行决定 |
| 手工导入 fixture | 离线数据契约和错误测试 | `ALLOWED_NON_PRODUCTION` | 只使用已批准或合成样本，并明确非真实覆盖 |

---

## 3. 官方端点能力

| 能力 ID | 端点 | P0 用途 | 关键输入 | 关键输出 | 默认 quota | 当前状态 |
|---|---|---|---|---|---:|---|
| C1 | `channels.list` | 取得批准频道的 uploads playlist 等元数据 | `id`、`part` | channel、related playlists | 1 unit | 待连接验证 |
| C2 | `playlistItems.list` | 遍历批准频道的 uploads | `playlistId`、`pageToken`、`maxResults<=50` | video IDs、`nextPageToken` | 1 unit | 待连接验证 |
| C3 | `search.list` | 有限关键词发现视频 | `q`、`type=video`、时间、region/language、`pageToken` | 候选 video IDs、页 token | 独立 100 calls/day，每次 1 | 待连接验证 |
| C4 | `videos.list` | 补齐视频状态、频道、发布时间和统计 | video IDs、`part` / `fields` | video metadata/statistics | 1 unit | 待连接验证 |
| C5 | `commentThreads.list` | 获取视频顶层评论和线程 | `videoId`、`order=time`、`textFormat=plainText`、`pageToken`、`maxResults<=100` | thread、top-level comment、reply count、`nextPageToken` | 1 unit | 待连接验证 |
| C6 | `comments.list` | 补齐指定顶层评论的全部可访问回复 | `parentId`、`textFormat=plainText`、`pageToken`、`maxResults<=100` | replies、`nextPageToken` | 1 unit | 待连接验证 |

quota 数值依据 2026-08-14 核验的官方文档。实施前重新核验，不在 Manifest 中写死每日采集量。

---

## 4. 连接器接口验收

沿用项目 `SocialConnector` 六个方法，但为 YouTube 增加明确输入输出：

| 方法 | 必须实现的行为 | 成功证据 | 失败行为 |
|---|---|---|---|
| `validate_access` | 只读检查项目可访问的端点和 quota，不拉取大范围业务数据 | 脱敏项目引用、端点状态、quota bucket、时间 | 返回结构化授权错误，不读取个人 shell 配置 |
| `build_query` | 将批准的 SourceScope 编译为 uploads、search、video、comment 请求 | `scope_version`、query hash、时间和参数快照 | 未签字 scope 直接阻断 |
| `collect` | 按 page token 增量采集，支持断点恢复和停止原因 | 原始引用、页数、next token、错误和请求计数 | 不把错误或限速返回为空结果 |
| `normalize` | 映射 VideoSource、CanonicalMention 和线程父子关系 | ID、source URL、时间、文本、语言、raw ref | 缺失字段为 `null` / `unknown`，不伪造 `US/en` |
| `collect_metrics` | 保存带时间的官方计数快照 | `observed_at` 与源字段 | 字段不可用时为 `null` |
| `delete_or_mark` | 刷新或删除到期、源删除和用户请求数据 | 目标 ID、动作、结果、时间、关联派生对象 | 失败进入可重试/人工处理队列，不静默 |

---

## 5. 字段映射

### 5.1 VideoSource

| 目标字段 | 官方来源/生成方式 | 必填 | 当前实现 | 验证 |
|---|---|---:|---|---|
| `video_id` | API video ID | 是 | Apify 样本可见，但非官方连接 | 待官方 API 验证 |
| `channel_id` | video/channel resource | 是 | 当前采集器只保存 channel name | 阻断 |
| `source_url` | 由 `video_id` 生成官方 URL | 是 | 当前有视频 URL | 待一致性验证 |
| `discovery_method` | `channel_uploads` / `keyword_search` | 是 | 当前未保存 | 阻断 |
| `discovery_query_id` | 内部 query 版本引用 | 条件必填 | 当前未保存 | 阻断 |
| `title` / `description` | API snippet | 是 | 当前 Apify 有 | 待官方 API 验证 |
| `published_at` | API snippet | 是 | 当前有 | 待格式验证 |
| `comment_count` | video statistics 快照 | 否 | 当前有计数 | 不能代替评论覆盖 |
| `comments_access_status` | comment endpoint 结果 | 是 | 当前未保存 | 阻断 |
| `fetched_at` / `refreshed_at` | 系统时间 | 是 | 仅有 fetched | 需补齐 |
| `refresh_or_delete_at` | 生命周期规则生成 | 是 | 当前未保存 | 阻断 |

### 5.2 CanonicalMention

| 目标字段 | 官方来源/生成方式 | 必填 | 当前实现 | 验证 |
|---|---|---:|---|---|
| `mention_id` | provider + comment ID 派生 | 是 | 无评论对象 | 阻断 |
| `provider_item_id` / `comment_id` | comment resource ID | 是 | 无 | 阻断 |
| `comment_thread_id` | commentThread ID | 是 | 无 | 阻断 |
| `parent_comment_id` | reply parent ID | 回复必填 | 无 | 阻断 |
| `is_top_level` | 由 thread/reply 类型生成 | 是 | 无 | 阻断 |
| `video_id` / `channel_id` | thread/video 资源 | 是 | 无评论映射 | 阻断 |
| `source_url` | 官方来源 URL + ID | 是 | 无评论深链 | 阻断 |
| `text_original` | comment text `plainText` | 是 | 无 | 阻断 |
| `published_at` / `updated_at` | comment snippet | 是/否 | 无 | 阻断 |
| `collected_at` / `refreshed_at` | 系统时间 | 是 | 无 | 阻断 |
| `detected_language` | 内容级识别，允许 `unknown` | 是 | 当前视频对象硬填 `en` | 阻断 |
| `region` | 默认 `unknown`，只在有合法直接证据时填写 | 否 | 当前视频对象硬填 `US` | 阻断 |
| `author_reference` | 最小化、作用域伪名化引用 | 否 | 无 | 待隐私设计 |
| `raw_object_ref` / `etag` | 原始载荷引用/官方 etag | 是/否 | 无评论原始载荷 | 阻断 |
| `refresh_or_delete_at` | 生命周期规则生成 | 是 | 无 | 阻断 |
| `deletion_status` | `active` 等状态 | 是 | 无评论对象 | 阻断 |

### 5.3 CoverageReport

| 字段 | 含义 | 当前状态 |
|---|---|---|
| `scope_id` / `scope_version` / `run_id` | 运行与签字范围绑定 | 未实现 |
| `videos_discovered` / `videos_hydrated` | 发现与补齐分离 | 未实现 |
| `comments_enabled` / `comments_disabled` | 能力与关闭分离 | 未实现 |
| `thread_pages_fetched` / `threads_fetched` | 顶层评论覆盖 | 未实现 |
| `replies_expected` / `replies_fetched` | 回复覆盖 | 未实现 |
| `next_page_token_present` | 是否主动提前停止 | 未实现 |
| `stop_reason` | 完成、page cap、quota、权限、错误等 | 未实现 |
| `error_code` / `error_count` | 官方错误与重试情况 | 未实现 |
| `coverage_status` | 第 6 节枚举 | 未实现 |

现有 `schema_v2.sql` 提供 `dim_monitor_scope`、`connector_registry`、`ods_collection_job`、`dwd_canonical_mention` 和 `dwd_evidence` 基础，但缺少 YouTube 线程/父子回复、明确 CoverageReport、`refreshed_at` 和 `refresh_or_delete_at` 等 v1 硬字段。进入实现计划前必须先决定扩展表还是新增关系表，本文不直接修改 schema。

---

## 6. Coverage 与错误状态

### 6.1 Coverage 枚举

| 状态 | 触发条件 | 报告语义 |
|---|---|---|
| `complete_for_defined_scope` | 定义范围内无下一页，预定回复均处理 | 只写「定义范围内完成」 |
| `partial_page_cap` | 达到批准的页数/评论上限且仍有下一页 | 部分覆盖 |
| `comments_disabled` | API 返回 `commentsDisabled` | 评论不可用，不是零评论 |
| `made_for_kids_no_comments` | Made for Kids 导致评论不可用 | 覆盖缺口 |
| `video_unavailable` | 视频删除、私密或不可访问 | 覆盖缺口 |
| `permission_denied` | 403/授权不足且不是评论关闭 | 权限失败 |
| `quota_exhausted` | 搜索或共享 quota 达限 | 部分覆盖，等待恢复 |
| `transient_error` | 网络/服务暂时错误 | 可重试失败 |
| `schema_mismatch` | 官方/供应商字段变化破坏解析 | 质量失败，进入人工处理 |
| `zero_comments_confirmed` | 评论功能可用、分页结束、返回零条 | 定义范围内零评论 |

### 6.2 错误处理

| 错误类别 | 行为 | 禁止行为 |
|---|---|---|
| 400 参数错误 | 记录 request hash、错误码和 scope version，停止该请求 | 自动删掉过滤条件后扩大范围 |
| 403 `commentsDisabled` | 写专用 coverage 状态 | 写成 `0 comments` |
| 403 权限错误 | 阻断并通知 owner | 静默降级到抓取器 |
| 404 video/comment not found | 标记源不可用，触发生命周期处理 | 永久保留为当前 Evidence |
| 429/quota | 保存 cursor 和 next token，按批准策略恢复 | 从头重跑制造重复 |
| 5xx/网络错误 | 有界重试，失败进入 DLQ/人工队列 | `except Exception: pass` |
| schema mismatch | 停止标准化，保留脱敏错误样本 | 缺失字段补零或硬编码 |

---

## 7. Secret、安全与可观测性

### 7.1 硬约束

- API Key 只由批准的 secret manager 或运行时注入。
- 不读取 `.env`、`~/.zshrc`、shell history 或个人配置获得凭证。
- 日志不得记录 key、OAuth token、完整授权 header 或合规申请凭证。
- API Client 默认为只读，不配置评论、回复、上传或其他写权限。
- 原始评论访问按角色控制，导出和删除操作留审计记录。

### 7.2 运行指标

| 指标 | 用途 | 验收 |
|---|---|---|
| 请求数与 quota bucket | 预算和限额 | 每次运行可追踪，不含 key |
| 端点成功/失败/重试 | 稳定性 | 按端点和错误码可分解 |
| 页数、next token、stop reason | Coverage | 能解释为何停止 |
| 字段缺失率 | schema 质量 | `null` 与零分开 |
| source refresh/delete 成功率 | 生命周期 | 到期记录均有结果 |
| DLQ/人工队列积压 | 失败恢复 | 不能静默丢失 |

---

## 8. 技术验证阶段

### V0：离线与静态门

不使用真实凭证和外部调用。

| 验证 | 通过证据 | 当前状态 |
|---|---|---|
| SourceScope schema 可解析 | 固定 v1 fixture | `PASS`：无 schema 错误 |
| comment/thread/reply fixture 标准化 | 父子关系与幂等断言 | `PASS`：3 条记录、3 个唯一 mention |
| Coverage 状态映射 | 每个错误/停止状态至少一个 fixture | `PASS`：10 个 case，无 mismatch |
| secret 扫描 | 无硬编码或个人 profile 读取 | `PASS`：现有 collector 无 finding |
| 静默异常扫描 | 关键路径无通用 `pass` | `PASS`：现有 collector 无 finding |
| 生命周期 fixture | 30 天刷新/删除和源删除可定位 | `PASS`：refresh/source missing/delete request 均可定位 |

V0 于 2026-08-14 以合成 fixture 通过。该结果只证明离线契约、状态映射和已检查的代码安全行为，不证明官方 API 权限、真实字段、quota、稳定性、保存删除任务或业务价值。V1 仍受 Rights Matrix 和执行授权阻断。

### V1：官方 API 最小只读连接

前置：Rights Matrix 的 R1、R4–R6、R17–R19 至少达到 `APPROVED_WITH_CONDITIONS`，且有批准的项目和运行环境。

| 验证 | 受控输入 | 通过证据 |
|---|---|---|
| `validate_access` | 一个批准的 channel/video | 脱敏项目引用、端点状态、quota 时间戳 |
| 视频补齐 | 一个批准 video ID | `video_id`、`channel_id`、状态、时间 |
| 顶层评论 | 同一 video ID | 至少一个真实 thread；若评论关闭则验证正确状态 |
| 回复补齐 | 一个有回复的批准 top-level comment | `replies_expected` 与分页结果 |
| 失败语义 | 一个 comments disabled 或 fixture | 不写零评论 |

V1 是只读 smoke，不证明业务覆盖、稳定性或洞察价值。

### V2：冻结范围 Coverage 验证

前置：SourceScope v1 已签字，V1 通过。

1. 固定批准频道、query、时间窗口和 scope version。
2. 分别跑 uploads 与 search 发现，不合并丢失来源方式。
3. 补齐视频状态，逐视频记录评论可用性。
4. 分页获取范围内顶层评论。
5. 对 UAT 指定线程补齐回复。
6. 输出 CoverageReport、错误、quota 和停止原因。
7. 人工抽查源链接、文本、父子关系、语言和重复。

通过条件：没有未解释的空结果；所有提前停止有原因；`comments_disabled`、quota、权限、404、零评论互相可区分。

### V3：生命周期与 S1 → Action UAT

前置：Rights Matrix 中 R7–R19 达到允许状态，V2 通过。

| 验证 | 通过证据 |
|---|---|
| 原始 API Data 刷新/删除 | 到期任务日志、结果、失败队列 |
| 用户删除请求 | 从请求到原始/派生定位和完成的审计记录 |
| 内容级痛点分类 | 不产生敏感用户画像；每条 Insight 有 Evidence 和反证 |
| 好/坏洞察盲评 | 使用冻结样本和预先签字阈值 |
| Action | 只有人工确认 Insight 生成待审批 Action |
| 回填 | 批准、驳回、执行状态和结果可追踪 |

V3 通过后，才能重新评估 YouTube 产品级 Go/No-Go。

---

## 9. 验收证据包

每次技术验证输出一个不含凭证的 evidence package：

| 文件/记录 | 内容 |
|---|---|
| `run_manifest` | run ID、scope ID/version、代码版本、环境、开始/结束时间 |
| `capability_result` | 端点、字段、权限、quota、成功/失败 |
| `coverage_report` | 视频、评论、回复、页数、错误、停止原因 |
| `field_profile` | null、unknown、字段缺失和 schema mismatch |
| `idempotency_result` | provider + item ID 重复检查 |
| `lifecycle_result` | 刷新、删除、源失效和请求处理 |
| `uat_sample_refs` | 批准样本引用；不在公开报告复制完整敏感内容 |
| `approval_record` | 数据、法务、业务、产品的结论和条件 |

证据等级必须区分：fixture、静态检查、只读 smoke、冻结真实范围、生命周期实测和业务 UAT。低等级证据不能冒充高等级完成。

---

## 10. 技术签字表

| 决策项 | 推荐值 | 最终决定 | Owner | 证据 | 状态 |
|---|---|---|---|---|---|
| 官方 API 项目 | 公司批准的独立项目 | 待填写 | 数据负责人 | 待填写 | 未核验 |
| 运行环境 | 公司批准环境 | 待填写 | 研发负责人 | 待填写 | 未核验 |
| secret | secret manager/runtime injection | 待填写 | 安全/研发 | 待填写 | 未核验 |
| connector strategy | `official_api` | 待填写 | 数据负责人 | 待填写 | 建议默认 |
| comments order | `time` | 待填写 | 数据 + 社媒 | 待填写 | 建议默认 |
| replies policy | UAT + 高价值候选补齐 | 待填写 | 数据 + 产品 | 待填写 | 建议默认 |
| Coverage schema | 第 6 节状态 | 待填写 | 数据负责人 | 待填写 | 待实现 |
| 生命周期 | 30 天刷新/删除 + 删除请求 | 待填写 | 数据 + 隐私 | 待填写 | 待实现 |
| V0 owner/date | 离线与静态门 | 2026-08-14 本轮自动化验证 | 研发待复核 | 15 tests + V0 JSON report | `PASS fixture-only` |
| V1 owner/date | 官方只读 smoke | 待填写 | 数据/研发 | 待填写 | 权利门阻断 |
| V2 owner/date | 冻结范围 Coverage | 待填写 | 数据 + 社媒 | 待填写 | 依赖 V1 |
| V3 owner/date | 生命周期 + S1 UAT | 待填写 | 四方 | 待填写 | 依赖 V2 |

---

## 11. Go/No-Go 映射

| Deep Research 门槛 | 本 Manifest 证据 | 当前结果 |
|---|---|---|
| G3 评论级连接 | V1 | No-Go：未验证 |
| G4 凭证与错误 | V0 + 第 7 节 | 部分通过：离线安全行为通过；官方 runtime/secret 未验证 |
| G5 数据契约 | 第 5 节 + fixture | No-Go：fixture 通过，生产 schema 未扩展 |
| G6 Coverage | 第 6 节 + V2 | No-Go：10 类映射通过，真实分页未验证 |
| G7 生命周期 | V3 + lifecycle result | No-Go：定位 fixture 通过，真实任务未实现 |
| G8 洞察安全 | V3 + 盲评 | No-Go：待 Rights 与业务样本 |
| G9 Action 闭环 | V3 | No-Go：待业务流程 |
| G10 UAT | V3 + approval record | No-Go：未定义阈值 |

---

## 12. 关联材料

- [`YouTube P0 SourceScope v1`](2026-08-14_YouTube_P0_SourceScope_v1_业务确认稿.md)
- [`YouTube P0 Rights Matrix`](2026-08-14_YouTube_P0_Rights_Matrix_法务评审稿.md)
- [`YouTube P0 定向 Deep Research 与数据契约建议`](2026-08-14_YouTube_P0定向DeepResearch与数据契约建议.md)
- [`schema_v2.sql`](../../tools/etl/schema_v2.sql)
- [`youtube_collector.py`](../../tools/social/youtube_collector.py)

本 Manifest 的官方能力和配额核验日期为 2026-08-14。真实连接、权限、字段质量、稳定性、成本和生命周期仍未验证。

---

## 13. V0 实测证据

### 13.1 新增或修改的离线资产

| 资产 | 作用 |
|---|---|
| [`v0_fixture.json`](../../tests/fixtures/youtube_p0/v0_fixture.json) | 合成 SourceScope、commentThread、完整回复、10 类 Coverage 和 3 类生命周期记录 |
| [`youtube_p0_contract.py`](../../tools/social/youtube_p0_contract.py) | 纯离线 scope 校验、评论标准化、Coverage 映射、生命周期定位和静态安全审计 |
| [`validate_youtube_p0_v0.py`](../../tools/validate_youtube_p0_v0.py) | 输出机器可读 V0 报告；任一门失败时退出码为 1 |
| [`test_youtube_p0_contract.py`](../../tests/test_youtube_p0_contract.py) | 契约、幂等、父子关系、Coverage、生命周期和审计测试 |
| [`test_youtube_collector_safety.py`](../../tests/test_youtube_collector_safety.py) | import 不读取个人 profile、默认范围为 unknown、DB 错误不静默测试 |
| [`test_validate_youtube_p0_v0_cli.py`](../../tests/test_validate_youtube_p0_v0_cli.py) | CLI 正向 PASS 与不安全 collector 负向 NO_GO 测试 |

### 13.2 TDD 证据

1. 正确 RED：9 个测试失败。6 个失败来自 contract 模块缺失；3 个失败分别证明现有 collector 会读取 `.zshrc`、硬填 `US/en`、吞掉数据库错误。
2. 第一轮 GREEN：11 个测试通过。
3. CLI RED：2 个测试因验证器缺失而失败。
4. 最终 GREEN：15 个测试全部通过；还验证了空记录、空 Coverage case 和非 fixture 标记不会被误判为通过。

最终测试命令：

```bash
python3 -m unittest -v \
  tests.test_youtube_p0_contract \
  tests.test_youtube_collector_safety \
  tests.test_validate_youtube_p0_v0_cli
```

最终 V0 命令：

```bash
python3 tools/validate_youtube_p0_v0.py
```

实测结果：退出码 `0`，`overall_status=PASS`；6 个检查全部 `PASS`；标准化 3 条合成评论；Coverage 10 个 case 无 mismatch；3 条生命周期记录分别得到 `refresh_due`、`mark_source_missing` 和 `delete_due_to_request`。证据等级为 `fixture_only`。
