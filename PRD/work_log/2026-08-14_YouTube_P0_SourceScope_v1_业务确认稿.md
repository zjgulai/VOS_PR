---
name: youtube-p0-source-scope-v1
description: YouTube P0 首期产品、频道、查询、市场、语言、时间、评论范围、痛点分类与签字项。用于社媒部门冻结真实采集和 UAT 边界。
date: 2026-08-14
status: 方案 A 产品规划已确认，V1 preflight 已启动，待社媒部门签字
stage: 决策门 2——数据、权利与覆盖
scope_version: 1.0-draft
selected_scope: M9/BP223 + M5 Smart/BP380
---

# YouTube P0 SourceScope v1 业务确认稿

## 0. 使用方式

本文把 YouTube P0 的采集和分析范围转成可签字决策。标记规则：

| 标记 | 含义 |
|---|---|
| 已确认 | 用户已确认的产品规划，不等于社媒部门已签字 |
| 建议默认 | 产品建议，社媒部门可修改 |
| 待确认 | 缺少会影响范围或验收的业务决定 |
| 禁止 | 不能作为 P0 的数据或结论口径 |

社媒部门确认前，本文保持 `draft`，不得用于宣称 YouTube 已覆盖美国英语用户或已具备市场代表性。

---

## 1. P0 目标与范围对象

| 项目 | v1 内容 | 状态 |
|---|---|---|
| 唯一业务结果 | 从 YouTube 公开评论发现高价值用户痛点，形成有 Evidence、可人工确认、可审批、可回填的 Action | 产品规划已确认；部门待签字 |
| 产品级 Go/No-Go | YouTube 决定 SI P0 产品级结果；Reddit 独立、并行、非阻塞验收 | 产品规划已确认；部门待签字 |
| 分析对象 | 可访问的顶层评论；高价值候选和 UAT 指定线程补齐公开回复 | 建议默认 |
| 主数据源 | 官方 YouTube Data API | 定向研究推荐；授权待确认 |
| 稳定发现范围 | 已批准频道的 uploads playlist | 建议默认 |
| 补充发现范围 | 有限关键词 `search.list` | 建议默认 |
| 不进入 P0 | S2 竞品内容报告、S3 趋势、S4 Creator、周报、自动回复、自动发布 | 产品规划已确认 |
| `scope_id` | `scope_youtube_p0_pumping_us_en_v1` | 建议默认；产品范围确认后冻结 |
| `workspace_id` | `momcozy_social` | 沿用既有数据契约 |

### 1.1 范围选择

| 方案 | 产品范围 | 优点 | 风险 | 建议 |
|---|---|---|---|---|
| A. 双型号薄切 | `M9 / BP223` + `M5 Smart / BP380` | 别名已有来源，范围小，适合验证评论 → 痛点 → Action | 不能代表全部 Pumping 产品 | 产品规划已确认；部门待签字 |
| B. Pumping 全线 | M5 Smart、M9、S9 Pro、S12 Pro、V1 Pro、V2、Air 1 等 | 业务覆盖更广 | query 歧义、频道和评论量扩大，人工标注负担上升 | P0 通过后扩展 |
| C. Pumping + Feeding | 同时加入 W1、KleanPal Pro 等喂养电器 | 覆盖两个品类 | 痛点 taxonomy、竞品、Action owner 和数据分布不同 | 不建议首期合并 |

用户已于 2026-08-14 确认按方案 A 启动 V0 离线验证。该确认属于产品规划决策，不替代社媒部门对频道、关键词、时间窗口、taxonomy、Action 和 UAT 样本的签字。社媒部门如果改选 B 或 C，必须同时重审频道、关键词、排除词、taxonomy、人工样本和 UAT 容量，不能只增加产品名。

2026-08-14 用户进一步授权启动 V1 决策节点。当前授权范围为 preflight 和本地 HTTP 合同实施，不替代社媒部门对 SourceScope 的签字，也不是真实 API 调用授权。固定频道、历史窗口、query、taxonomy、Action 和 UAT 样本仍保持「待确认」。

---

## 2. 产品、别名与竞品范围

### 2.1 Momcozy 产品

| 标准型号 | 已知别名 | P0 状态 | 需要业务确认 |
|---|---|---|---|
| M9 | BP223 | 建议纳入 | 是否为首期核心 SKU；是否还有市场用名、旧名和拼写变体 |
| M5 Smart | BP380 | 建议纳入 | 是否同时包含历史 M5 内容；`M5` 单独出现时如何消歧 |
| 其他 Pumping 型号 | 见 `competitor_dictionary.json` 的 Momcozy models | 暂不纳入 | 哪些在 P0 后按优先级扩展 |
| Feeding 产品 | W1 / BP420、KleanPal Pro 等 | 暂不纳入 | 是否另建独立 `scope_id`，不与 Pumping 混合验收 |

事实来源：[`competitor_dictionary.json`](../../config/competitor_dictionary.json) 当前记录了 Momcozy 产品线、型号与部分 BP 别名。业务仍需确认这些名称是否完整、有效并适用于美国英语市场。

### 2.2 P0 竞品频道候选

竞品词典当前将 Eufy、Elvie、Willow、Spectra、Medela 标为 Pumping P0。词典没有保存已验证 YouTube channel ID，因此下表只用于发起人工核验，不能直接采集。

| 品牌 | 角色 | YouTube channel ID | 业务确认 | 证据要求 |
|---|---|---|---|---|
| Momcozy | 自有品牌 | 待人工核验 | 待确认 | 官方网站或已认证账号交叉验证 |
| Eufy | P0 竞品 | 待人工核验 | 待确认 | 品牌官网或已认证账号交叉验证 |
| Elvie | P0 竞品 | 待人工核验 | 待确认 | 同上 |
| Willow | P0 竞品 | 待人工核验 | 待确认 | 同上 |
| Spectra | P0 竞品 | 待人工核验 | 待确认 | 同上 |
| Medela | P0 竞品 | 待人工核验 | 待确认 | 同上 |

### 2.3 专业评测与 Creator 频道

不由系统自动猜测频道。社媒部门应提供现有重点 Creator/KOL 池，并为每个候选频道记录：

| 必填字段 | 说明 |
|---|---|
| `channel_id` | YouTube 官方稳定 ID，不只保存显示名或 handle |
| `channel_name` | 当前显示名 |
| `channel_role` | `own_brand`、`competitor`、`professional_review`、`creator` |
| `why_in_scope` | 与 M9/M5 Smart 用户痛点的业务关系 |
| `verification_source` | 官网、已认证账号、内部 CRM 或人工复核记录 |
| `verified_by` / `verified_at` | 核验角色和时间 |
| `status` | `approved`、`rejected`、`pending_verification` |

只有 `approved` 频道进入固定 uploads 范围。关键词发现的新频道先进入候选池，不自动扩展 P0。

---

## 3. 查询词与排除规则

### 3.1 视频发现 query 候选

query 用于发现视频，不用于通过 `commentThreads.list.searchTerms` 过滤评论。选中视频后，默认读取范围内全部可访问顶层评论，避免预设词降低痛点召回。

| query 组 | 候选词 | 状态 |
|---|---|---|
| 品牌 + 型号 | `Momcozy M9`、`Momcozy BP223`、`Momcozy M5 Smart`、`Momcozy BP380` | 建议默认 |
| 型号 + 评测 | `Momcozy M9 review`、`Momcozy M5 review` | 建议默认 |
| 型号 + 对比 | `Momcozy M9 vs`、`Momcozy M5 vs` | 建议默认 |
| 品类 + 品牌 | `Momcozy wearable breast pump`、`Momcozy hands free breast pump` | 建议默认 |
| 使用场景 | `Momcozy pump at work`、`Momcozy pump travel`、`Momcozy pump overnight` | 待业务确认 |
| 问题发现 | `Momcozy pump leaking`、`Momcozy pump suction`、`Momcozy pump flange`、`Momcozy pump cleaning` | 待业务确认 |

### 3.2 排除与消歧

| 歧义 | 规则 | 状态 |
|---|---|---|
| `M9` | 单独出现时必须与 `Momcozy`、`breast pump` 或批准频道共同满足；排除 Leica M9 等无关实体 | 建议默认 |
| `M5` | 单独出现时必须与 `Momcozy`、`breast pump` 或批准频道共同满足；排除 BMW M5 等无关实体 | 建议默认 |
| `pump` | 排除水泵、汽车泵、健身 pump 等无关语境 | 建议默认 |
| `BP223` / `BP380` | 只有经产品别名表确认后作为强实体词 | 建议默认 |
| Sponsored review | 不排除，但保留公开的 `#ad`、affiliate 或 sponsorship 信号 | 建议默认 |

query 和排除规则必须版本化。UAT 后新增的规则进入 `scope_version` 变更记录，不能覆盖原运行口径。

---

## 4. 市场、语言与时间范围

| 维度 | v1 建议 | 数据语义 | 待确认项 |
|---|---|---|---|
| 业务市场 | 美国 | 描述产品目标市场 | 社媒部门是否接受 |
| `regionCode` | `US` | 只表示搜索结果中的视频可在美国观看 | 禁止写成评论者位于美国 |
| 业务语言 | 英语 | P0 主要评审语言 | 是否接受少量其他语言进入 coverage |
| `relevanceLanguage` | `en` | 只表示搜索相关性偏好 | 禁止写成结果全部为英语 |
| 评论语言 | 内容级识别；无法判断写 `unknown` | 真实文本属性 | 非英语评论是否保留、翻译或排除 |
| 历史窗口 | 最近 90 天 | 产品建议值，不代表行业标准 | 社媒部门可选 30/90/180 天或固定日期 |
| 增量刷新 | 频率由真实量级和 quota 估算后决定 | 当前未知 | 业务时效要求和技术预算 |

推荐使用最近 90 天作为首次受控样本，因为它在时效与场景多样性之间提供一个可讨论的起点；该数字没有内部 baseline 支持，业务签字前不能作为正式 SLA。

---

## 5. 评论与回复范围

| 对象 | v1 规则 | Coverage 要求 |
|---|---|---|
| 顶层评论 | 对入选视频读取全部可访问顶层评论，按 `time` 分页 | 记录页数、评论数、`nextPageToken` 和停止原因 |
| 评论搜索词 | 不使用 `searchTerms` 作为主采集过滤 | 避免只看到预设痛点词 |
| 回复 | 对 UAT 指定线程和高价值候选线程调用 `comments.list(parentId)` 补齐 | 记录 `replies_expected`、`replies_fetched` 和缺口 |
| 评论关闭 | 状态为 `comments_disabled` | 不得写成零评论或零痛点 |
| Made for Kids | 状态为 `made_for_kids_no_comments` | 作为覆盖缺口披露 |
| 删除或不可用 | 刷新时更新 `deletion_status` | 不保留失效原文作为当前证据 |

高价值候选在回复补齐前只能标为 `candidate`。如果回复 coverage 不完整，Insight 必须披露上下文缺口。

---

## 6. 痛点 taxonomy v0.1

taxonomy 只分类评论内容，不推断评论者的健康、孕产、年龄或其他敏感属性。

| `pain_category` | 要回答的问题 | 示例表达仅用于标注培训 |
|---|---|---|
| `fit_and_flange` | 尺寸、法兰、贴合是否造成使用困难 | fit、flange size、seal |
| `comfort_and_pain` | 使用时是否不适或疼痛 | uncomfortable、painful |
| `suction_and_output` | 吸力、模式或产出体验是否不符合预期 | weak suction、output drop |
| `leakage_and_spill` | 是否漏奶、溢出或装配后密封异常 | leaking、spilling |
| `noise_and_privacy` | 工作或公共场景是否存在噪音和隐蔽性问题 | loud、not discreet |
| `cleaning_and_assembly` | 清洗、消毒、拆装是否负担过高 | hard to clean、too many parts |
| `battery_and_charging` | 续航、充电或移动使用是否受限 | battery、charging |
| `portability_and_workflow` | 工作、通勤、旅行、夜间等流程是否被打断 | work、commute、travel |
| `app_and_connectivity` | App、连接或控制是否造成问题 | pairing、sync、app |
| `support_and_replacement` | 售后、退换、耗材或更换件是否影响体验 | support、replacement |
| `trust_and_safety_signal` | 评论内容是否提出需要 PR/合规复核的安全或信任信号 | 只生成跨产品移交，不由 SI 定级 |
| `other_or_unknown` | 证据不足或不属于当前 taxonomy | 保留原文和人工备注 |

### 6.1 高价值判断

一个痛点只有同时满足以下条件，才能由人工确认成高价值 Insight：

1. 问题强度和重复性：具体困难或后果可说明，并存在重复或强单例证据。
2. 业务相关性：与 v1 产品、市场、语言和当前目标直接相关。
3. 证据可信度：原文、来源、时间、上下文、反证和 Coverage 足以支撑。
4. 可行动性：能形成明确 Action 类型、owner、预期结果和决策时限。

具体阈值不在模型输出后倒推。社媒部门需要先提供好/坏洞察样本，再冻结验收口径。

---

## 7. Action 范围

| 候选 Action | 是否进入 v1 | 必须确认的 owner | 说明 |
|---|---|---|---|
| 内容选题/教育内容 | 建议进入 | 社媒内容负责人 | 由 Evidence 支撑，不能写医疗或绝对化承诺 |
| FAQ/使用指南更新 | 建议进入 | Support / 内容负责人 | 需要批准的产品事实 |
| 产品反馈 | 建议进入 | 产品/VOC 负责人 | 只提交证据，不替代产品决策 |
| PR 风险升级 | 建议进入 | PR 事件负责人 | SI 只移交信号，不复制 PR War Room |
| Creator 合作 | 暂不进入 | Creator 负责人 | 属 S4，P0 后评估 |
| 自动回复/自动发布 | 禁止 | 不适用 | 所有外部动作保持人工审批 |

社媒部门需要在签字时至少选择一种 v1 Action，并指定审批角色、执行角色和结果回填字段。

---

## 8. 人工标注与 UAT 输入

| 输入 | 要求 | 当前状态 |
|---|---|---|
| 好洞察样本 | 5 条真实历史样例，说明为何有价值、采取了什么行动 | 待社媒部门提供 |
| 无用洞察样本 | 5 条真实历史样例，说明为何不可用 | 待社媒部门提供 |
| 痛点标注样本 | 覆盖 v0.1 taxonomy 的真实评论；数量由业务和数据共同确定 | 待确认 |
| 边界样本 | 反讽、广告、重复、无关型号、非英语、上下文不足 | 待确认 |
| Action 样本 | 至少覆盖一个批准、一个驳回和一个结果回填案例 | 待确认 |

固定样本必须在模型评分前冻结。验收人盲评时不展示模型置信度和推荐结果。

---

## 9. 签字表

| 决策 | 推荐值 | 业务决定 | 决策人 | 日期 | 变更原因 |
|---|---|---|---|---|---|
| P0 产品范围 | M9/BP223 + M5 Smart/BP380 | 产品规划已确认；社媒部门待签字 | 社媒负责人 | 待填写 | 待填写 |
| 市场 | US | 待确认 | 社媒负责人 | 待填写 | 待填写 |
| 语言 | English，其他语言保留 coverage 状态 | 待确认 | 社媒负责人 | 待填写 | 待填写 |
| 历史窗口 | 最近 90 天 | 待确认 | 社媒 + 数据 | 待填写 | 待填写 |
| 固定频道清单 | 仅 `approved` channel ID | 待提供 | 社媒负责人 | 待填写 | 待填写 |
| query / 排除词 | 第 3 节 v1 候选 | 待确认 | 社媒 + 产品 | 待填写 | 待填写 |
| taxonomy | 第 6 节 v0.1 | 待确认 | 社媒 + 产品/VOC | 待填写 | 待填写 |
| 首期 Action | 内容/FAQ/产品反馈/PR 移交中至少一种 | 待确认 | 社媒负责人 | 待填写 | 待填写 |
| 好/坏洞察样本 | 各 5 条 | 待提供 | 社媒分析师 | 待填写 | 待填写 |

签字完成标准：产品、市场、语言、历史窗口、固定频道、query、taxonomy、Action 和标注样本均有明确值；不能用「后续再说」进入真实 UAT。

---

## 10. 变更与依赖

- 权利与保存边界由 [`YouTube P0 Rights Matrix`](2026-08-14_YouTube_P0_Rights_Matrix_法务评审稿.md) 管理。
- 技术能力、端点、错误和验证证据由 [`YouTube P0 Capability Manifest`](2026-08-14_YouTube_P0_Capability_Manifest_技术验证稿.md) 管理。
- 官方来源和研究结论见 [`YouTube P0 定向 Deep Research 与数据契约建议`](2026-08-14_YouTube_P0定向DeepResearch与数据契约建议.md)。
- 任何范围变更必须升级 `scope_version`，保留旧版本和对应 Coverage/UAT 结果。
