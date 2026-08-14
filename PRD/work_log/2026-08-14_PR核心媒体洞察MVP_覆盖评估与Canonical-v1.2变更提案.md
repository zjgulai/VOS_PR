---
name: pr-core-media-insight-mvp-coverage-assessment
description: 基于 PR 团队核心媒体工作簿，对 PR Canonical v1.1 的需求覆盖、数据质量、现有实现和快速 MVP 路径进行评估，并给出 Canonical v1.2 精确变更提案。
date: 2026-08-14
status: 评估完成；用户已选择方案 C，Canonical v1.2 已生成
stage: 意图澄清与 PRD 方案对比
source_workbook: /Users/lute/Project/voc-data-product/PMO/业务协作_社媒团队/momcozy pr 媒体关系全年规划表.xlsx
target_prd: PR/PRD-Momcozy-PR-Intelligence-Agent-Canonical-v1.1.md
proposed_prd: PR/PRD-Momcozy-PR-Intelligence-Agent-Canonical-v1.2.md
---

# PR 核心媒体洞察 MVP：覆盖评估与 Canonical v1.2 变更提案

> 本文只回答三个问题：当前 PRD 是否完整覆盖 PR 核心媒体洞察；现有资产能否快速跑出 MVP；如继续，应如何修改 PRD。本文不部署采集器、不自动联系媒体，也不改变正式 PRD 当前的 P0 优先级。

## 0. 决策结论

> 2026-08-14 决策更新：用户已选择方案 C，核心媒体洞察直接替换 P4 成为正式 P0。完整新版本见 `../PR/PRD-Momcozy-PR-Intelligence-Agent-Canonical-v1.2.md`。本文保留评估时的方案比较，作为决策记录；其中「推荐 A → B」不再代表当前产品方向。

### 0.1 结论

| 判断 | 结论 | 把握 | 依据 |
|---|---|---|---|
| 业务功能是否覆盖 | **较完整覆盖** | 高 | Canonical v1.1 已定义媒体/记者画像、近 180 天选题、竞品观点、机会、风险、冷却期、Media Brief 和人工审批 |
| 可执行规格是否完整 | **不完整** | 高 | 缺工作簿导入契约、媒体/编辑/触点分层、关系事件、来源状态、字段新鲜度和编辑归属验收 |
| 能否马上正式上线 | **不能** | 高 | 现有代码只有部分 RSS 和媒体级文章表；数据库没有联系人表实例数据；现场 dry-run 的来源覆盖和风险相关性均未达标 |
| 能否快速跑验证 | **可以，限人工辅助试点** | 中高 | 工作簿已给出 11 家媒体、48 位编辑、部分作者页、历史榜单记录、关系规则和分级规则 |
| 是否应替换现有 P0 | **暂不建议直接替换** | 中 | Canonical v1.1 已确认 P4 危机预警为 P0，而核心媒体洞察为 P1；缺少 PR 负责人对两者优先级的正式选择 |

推荐采用“**方案 A 验证 → 方案 B 薄切**”：

1. 先用 5 个工作日做 Concierge Validation，证明输入可用、输出有价值。
2. 通过后再做约 2 周的 Assisted MVP，自动采集和生成草稿，人工确认编辑归属、观点、机会和风险。
3. 在两轮真实评审后，再决定核心媒体洞察是否升级为正式 P0；在此之前标记为 `P0b / Pilot`，P4 保留正式 P0。

时间为规划估算，不是交付承诺。若授权媒体源、作者页访问或业务评审人不到位，周期不成立。

### 0.2 现在不应做的事

- 不把工作簿中的社媒账号直接解释为每位编辑的个人账号。
- 不自动抓取 LinkedIn，不收集私人联系方式或推断人格。
- 不把 RSS 标题中的一般性 `recall`、`lawsuit` 直接判为 Momcozy 风险。
- 不自动生成“已确认的编辑观点”；署名不确定时只能降级到媒体层。
- 不自动发 pitch、邮件、私信或声明。
- 不一次纳入 368 家大媒体池；MVP 只验证 11 家核心媒体。

---

## 1. 证据边界

### 1.1 本轮使用的材料

| 材料 | 用途 | 证据边界 |
|---|---|---|
| `momcozy pr 媒体关系全年规划表.xlsx` | 核心媒体、编辑、触点、关系规则、历史文章、媒体分级和营销日历 | 团队工作资产；不等于字段均已确认或数据授权已经完成 |
| `PRD-Momcozy-PR-Intelligence-Agent-Canonical-v1.1.md` | 当前正式产品规格 | 用于判断需求设计覆盖，不代表能力已经实现 |
| `momcozy_pr_intelligence_implementation_plan_2026-08-11.md` | 上游业务、数据和实施蓝图 | 规划材料，不代表供应商、预算或数据源已经获批 |
| `tools/pr_intel/` 与 `tools/etl/schema_v2.sql` | 当前代码和数据模型 | 用于评估可复用程度；未做任何写库或生产调用 |

### 1.2 工作簿读取说明

事实：本轮通过只读方式成功读取工作表、单元格、合并区域和超链接，未修改原工作簿。该文件在另一套 XLSX 解析器和 `unzip` 完整性检查中未能直接导入，但通过 `openpyxl` 的内存流可以读取。

推断：业务内容可用，但正式产品导入前应由 PR 团队在 Excel 中“另存为”标准 `.xlsx`，并把新文件作为导入验收样本。当前现象不足以断言原文件内容损坏。

---

## 2. 附件数据审计

### 2.1 `吸奶器核心媒体池`

工作表包含 11 家核心媒体和 48 位有姓名的编辑，另有 1 行未填写编辑。每家媒体编辑数最少 1 位、中位数 4 位、最多 8 位。

| 字段 | 有值数 / 48 | 完整率 | MVP 判断 |
|---|---:|---:|---|
| 媒体 | 48 | 100% | 可导入，但需生成稳定 `outlet_id` |
| 类型 / 区域 | 48 | 100% | 可作为范围标签；仍需拆分国家与 edition |
| 角色定位 | 48 | 100% | 可作为媒体角色标签，不应作为算法事实 |
| 媒体 Social Media | 48 | 100% | 由媒体级合并单元格继承；不是编辑个人账号 |
| Editor Name | 48 | 100% | 可生成候选 `journalist_id`，仍需核验同名与任职状态 |
| Editor Position | 33 | 68.8% | 15 位缺失，必须显示为未知 |
| LinkedIn | 14 | 29.2% | 仅作人工核验链接，不纳入自动抓取 |
| 个人简介 / 作者页 | 25 | 52.1% | 是编辑级监测最有价值的直接入口，但只覆盖约一半编辑 |
| Cooperation type | 38 | 79.2% | 可作为关系标签，不能替代真实互动历史 |
| Owner | 21 | 43.8% | 27 位缺负责人，不能默认分配 |

11 家媒体都列有 X/Twitter、Instagram、Facebook；10 家列有 YouTube，9 家列有 TikTok。它们主要是媒体官方账号，不足以回答“某位编辑近期在写什么”。编辑级判断仍需作者页、署名文章或人工确认。

范围冲突：名单中既有 USA，也有 UK/USA 媒体；Canonical v1.1 当前 P0 限定美国英语市场。MVP 必须明确监测美国版、英国版还是两者，不能只按媒体品牌名合并。

### 2.2 其他工作表的产品价值

| 工作表 | 可复用内容 | 不能直接当成什么 |
|---|---|---|
| `pitch策略细化` | 六类媒体角色、关系策略、维护方式，可转成 angle/action taxonomy | 不是采集范围或已验证的编辑偏好 |
| `资源库管理规则` | 统一媒体库、30 天冲突检查、3 个工作日更新、发布台账、月度维护和唯一事实源规则 | 不是已经结构化的关系事件数据 |
| `下半年新品营销日历` | 产品节点和潜在传播窗口 | 38 个 Launch Promo / PR Marketing 布尔位全部为否，不能据此认定“没有 PR 计划” |
| `1-3 高权重SEO GEO Listicle` | 23 条历史记录，可作为文章发现、Momcozy 是否出现、编辑联系和 pitch 状态的初始验证集 | 不是完整历史语料，也不是自动化准确率的充分样本 |
| `1-2核心媒体Core Media List` | 368 个唯一媒体名、S/A/B/C 评级、维护/开发/测试优先级、编辑和负责人，可用于 P1 扩面 | 不适合直接进入 11 家媒体 MVP；字段缺失较多 |
| `1-1媒体分级标准` | 100 分分级框架：触达、权威、受众、跨平台、内容、合作历史、接受度 | 现有媒体表只存最终等级，没有七项分数和公式，当前评级不可完全审计 |

大媒体池的关键完整度：370 行有媒体名，242 行有编辑，101 行有职位，31 行有邮箱，19 行有 pitching status。MVP 不应通过模糊匹配把这些行自动合并到 11 家核心媒体；应先建立唯一 ID 和人工复核队列。

---

## 3. 当前 PRD 覆盖矩阵

### 3.1 业务能力覆盖

| PR 要回答的问题 | Canonical v1.1 | 判断 |
|---|---|---|
| 核心媒体和编辑是谁 | 已定义 outlet and journalist registry | 已覆盖 |
| 编辑近期写什么 | 已定义近 180 天主题、内容形式和时间线 | 已覆盖 |
| 是否测评竞品 | 已定义 journalist articles and competitor views | 已覆盖 |
| 如何评价竞品、核心观点是什么 | 已定义竞品观点、证据偏好、编辑部与商业内容区分 | 已覆盖 |
| Momcozy 是否有切入点 | 已定义机会识别、目标媒体/编辑、角度、资产缺口和时机 | 已覆盖 |
| 是否有 Momcozy/竞品负面评价 | 已定义品牌、竞品和媒体信号 | 已覆盖，但媒体专属口径仍需补充 |
| 是否涉及产品安全、质量等风险 | 已定义风险识别、证据、分级和人工审批 | 已覆盖，但当前代码相关性不足 |
| 同题冷却和关系冲突 | 已定义 cooldown、关系状态和不 pitch 理由 | 已覆盖 |
| 结论是否可追溯 | 已定义 Evidence、来源、时间和不确定性 | 已覆盖 |
| 是否自动联系记者 | 明确禁止；所有对外行动人工审批 | 已覆盖 |

结论：**PRD 对业务问题的覆盖不是主要矛盾。主要矛盾是从工作簿到产品对象、从媒体文章到编辑归属、从信号到可验收 Media Brief 的执行契约没有写完整。**

### 3.2 必须补进 PRD 的缺口

| 缺口 | 后果 | v1.2 必须新增 |
|---|---|---|
| 工作簿导入契约 | 合并单元格、链接和空值可能被错误继承 | sheet/列映射、向下填充规则、空值规则、行号溯源和导入报告 |
| 媒体、edition、编辑、触点混在一个对象 | UK/USA 内容、媒体账号和编辑账号可能误归属 | `Outlet`、`OutletEdition`、`Journalist`、`Touchpoint` 分层 |
| 编辑身份和任职状态无核验字段 | 同名、离职或自由撰稿人被误画像 | `identity_status`、`affiliation_status`、`verified_by/at` |
| 文章只有 `author_text` | 无法稳定汇总到编辑 | `journalist_id` 可空、署名解析状态和人工复核队列 |
| 关系历史只有概念 | 无法执行 30 天冲突、跟进和禁联 | `RelationshipEvent` 与 `PitchConstraint` |
| 社媒触点无来源状态 | 有链接不代表可稳定采集 | 平台、URL、实体归属、权限、访问状态、最后检查时间 |
| 媒体评级只存结果 | 无法解释评级变化 | `MediaScoreSnapshot` 保存七项分数、证据和版本 |
| 输出没有专属验收 | “生成了摘要”不等于“可用于 pitch” | Media Brief 质量、署名精度、引用和建议采纳验收 |

---

## 4. 现有实现可复用性

### 4.1 已有资产

- `feed_collector.py` 已有媒体 RSS 注册表、文章标准化、品牌词和风险词。
- `schema_v2.sql` 已有 `pr_articles`、`pr_opportunities`、`pr_weekly_reports`，并预留 `dim_media_contacts` 定义。
- `opportunity_finder.py` 和 `report_generator.py` 可复用部分机会与报告结构。
- 三个相关 Python 文件通过了本轮静态编译检查。

### 4.2 现场 dry-run 结果

本轮仅对母婴、女性和测评媒体执行了只读 dry-run，没有写文件和数据库：

| 项目 | 结果 |
|---|---|
| 11 家核心媒体中已有 RSS 配置 | 8 家 |
| 未配置 | Forbes Personal Shopper、Consumer Reports、MomJunction |
| 已配置且本次返回内容 | Women’s Health、Good Housekeeping、Made for Mums，共 3 家 |
| 已配置但本次返回 0 | Babylist、The Bump、Parents、BabyCenter、What to Expect，共 5 家 |
| 本次采集条目 | 150 |
| 有品牌提及 | 0 |
| 被现有规则标为 P0 风险 | 10 |

风险判断：150 条中没有品牌提及，却有 10 条被标为 P0，原因是当前代码只要标题或摘要命中一般风险词就升级。它可以用作线索发现，不能直接作为 Momcozy/竞品风险判断。

### 4.3 数据库与测试状态

| 检查 | 结果 |
|---|---|
| `pr_articles` | 表存在，0 行 |
| `pr_opportunities` | 表存在，0 行 |
| `pr_weekly_reports` | 表存在，0 行 |
| `dim_media_contacts` | schema 文件有定义，当前数据库中不存在 |
| PR media/journalist 专项测试 | 未发现 |

可复用结论：**现有实现只能作为有限骨架，不能直接部署为该产品。** 可复用的是 RSS 适配器、文章基本字段、报告框架；需要新增的是工作簿导入、来源可用性台账、作者解析、关系事件、编辑信号、Media Brief、相关性门禁和专项测试。

---

## 5. 三条完整路径

### 5.1 方案 A：Concierge Validation

目标：先验证“PR 团队会不会用、判断是否可信”，不验证全自动化。

| 项目 | 设计 |
|---|---|
| 周期估算 | 5 个工作日 |
| 范围 | 11 家媒体；优先选有作者页的编辑；不扩 368 家媒体池 |
| 输入 | 工作簿、人工确认的作者页/文章 URL、23 条 listicle 历史记录、竞品词典 |
| 处理 | 系统辅助整理；人工确认署名、赞助属性、竞品观点和风险相关性 |
| 输出 | 11 份媒体级 Brief；选 10–15 位编辑生成编辑级 Brief |
| 验证 | PR 团队盲评事实错误、引用、机会价值、风险价值和编辑时间 |
| 优点 | 最快暴露“输出有没有用”，不受 RSS 全覆盖阻塞 |
| 缺点 | 不能证明持续采集、自动更新和规模化成本 |
| 退出条件 | 输出无价值、主要来源无权使用、编辑归属无法达到验收门槛 |

适用：需求仍需核对、希望一周内看真实样例。

### 5.2 方案 B：Assisted MVP（推荐）

目标：验证“持续发现 → 编辑归属 → 洞察 → 人工确认 → Action”的最短产品闭环。

| 项目 | 设计 |
|---|---|
| 周期估算 | 约 2 周，前提是方案 A 通过且来源可用 |
| 范围 | 11 家核心媒体、48 位候选编辑；US edition 为默认建议，UK edition 待确认 |
| 增量窗口 | 近 30 天持续信号 |
| 历史基线 | 最多 180 天，按可获得且获准的作者页/文章补齐，不承诺全文覆盖 |
| 来源优先级 | 作者页/署名文章 → 有效 RSS → 人工 URL 导入 → 媒体社媒发现线索 |
| 自动化 | 文章发现、去重、候选署名、主题/竞品/风险候选、Brief 草稿 |
| 人工门 | 身份归属、竞品观点、风险、机会和对外 Action 全部人工确认 |
| 输出 | 每周 Media Brief、Opportunity Card、Risk Card、覆盖报告、待核验队列 |
| 优点 | 同时验证业务价值和关键技术链路；可保留 P4 正式 P0 |
| 缺点 | 仍需维护来源适配器；不能把 48 位编辑都承诺为自动覆盖 |

适用：希望把核心媒体洞察作为并行 `P0b / Pilot`，不推翻现有 P4 决策。

### 5.3 方案 C：替换正式 P0

目标：把核心媒体洞察升级为 PR 产品唯一首期闭环，P4 后移。

| 项目 | 设计 |
|---|---|
| 产品范围 | 以 11 家核心媒体和 48 位编辑为正式 P0；P4 改为 P1 |
| 必须重做 | PRD 第 0、1、3、5、9、10、11 章；P0 指标、验收剧本、实施顺序和资源计划 |
| 优点 | 与当前 PR 团队已提供的名单和媒介关系日常工作直接结合 |
| 风险 | 推翻此前 P4 决策；来源可用性仍未通过；可能把高价值需求误当成高可实施性 |
| 决策前提 | PR 负责人确认媒体关系比危机预警更高频、更高损失且有明确 owner；技术确认来源门槛；法务确认内容使用边界 |

适用：PR 负责人明确要求重新排序，并愿意为媒体来源、人工审核和数据维护负责。

### 5.4 对比与推荐

| 维度 | A Concierge | B Assisted MVP | C 替换正式 P0 |
|---|---:|---:|---:|
| 需求学习速度 | 高 | 中高 | 低 |
| 自动化验证 | 低 | 高 | 高 |
| 首轮落地成功率 | 高 | 中高 | 中低 |
| 与现有 P0 冲突 | 无 | 低 | 高 |
| 来源依赖 | 低 | 中 | 高 |
| 适合当前证据阶段 | 是 | **是，A 通过后推荐** | 否，除非重新签字 |

推荐：**A → B**。A 是 B 的业务验真阶段，不是长期方案；C 保留为两轮试点后的战略选择。

---

## 6. 推荐 MVP 产品规格

### 6.1 唯一业务结果

PR 用户在 15 分钟内回答并确认：

1. 核心媒体/编辑最近在关注什么，较其历史基线有什么变化？
2. 他们如何评价哪些竞品，依据是什么，是否属于编辑内容或商业内容？
3. Momcozy 有什么可执行的传播机会，或需要升级的负面、安全和质量风险？

“15 分钟”为候选验收目标，需先记录当前人工 baseline 后由 PR 负责人签字。

### 6.2 MVP 范围

| 维度 | 纳入 | 不纳入 |
|---|---|---|
| 媒体 | 工作簿 11 家核心媒体 | 368 家大媒体池扩面 |
| 编辑 | 48 位候选；有作者页者优先 | 未确认身份的自动画像 |
| 市场 | 建议先 US/English | UK/USA 混合汇总 |
| 内容 | 公开作者页、署名文章、获准摘要/元数据、人工 URL | 绕过登录墙、未经许可保存全文 |
| 社媒 | 媒体官方账号用于线索发现 | LinkedIn 自动抓取、个人社媒全面监控 |
| 时间 | 30 天增量 + 最多 180 天基线 | 不受控的全历史抓取 |
| 动作 | 人工确认的 Opportunity/Risk/Brief | 自动 pitch、邮件、私信或发布 |

### 6.3 处理流程

```text
工作簿导入
  → 媒体、edition、编辑、触点拆分
  → 来源可用性与权利检查
  → 文章/帖子发现与去重
  → 署名解析；不确定则进入人工队列
  → 主题、竞品观点、Momcozy 提及、风险候选抽取
  → 证据与反证绑定
  → Media Brief 草稿
  → PR Analyst 审核
  → Opportunity / Risk / No-pitch Action
  → 结果和关系事件回填
```

### 6.4 Media Brief 最小输出

每份 Brief 必须包含：

1. `Scope`：媒体、edition、编辑、时间窗口、已覆盖/未覆盖来源。
2. `Recent Focus`：近期主题及变化，至少绑定原文链接、发布日期和署名状态。
3. `Competitor View`：竞品、产品、正/负/混合观点、核心依据、内容属性。
4. `Momcozy Gap`：已出现、未出现或无法判断；不得把未采到写成未报道。
5. `Opportunity`：角度、时机、所需证据/资产、为什么适合、为什么不适合。
6. `Risk`：负面、安全、质量、隐私或评价真实性候选；必须有人审和升级理由。
7. `Relationship`：最近联系、结果、负责人、30 天冲突、冷却期和禁联理由。
8. `Uncertainty`：署名、来源、样本和权利限制。

---

## 7. 最小数据契约

### 7.1 核心对象

| 对象 | 最小字段 |
|---|---|
| `outlet` | `outlet_id, canonical_name, media_type, role_tags, status, source_row_ref` |
| `outlet_edition` | `edition_id, outlet_id, country, language, canonical_domain, priority, owner, verified_at` |
| `journalist` | `journalist_id, public_name, public_title, identity_status, verified_by, verified_at` |
| `journalist_affiliation` | `journalist_id, edition_id, role, start_at, end_at, affiliation_status, source_url` |
| `touchpoint` | `touchpoint_id, entity_type, entity_id, platform, public_url, ownership_type, permission_status, access_status, last_checked_at` |
| `editorial_item` | `document_id, edition_id, journalist_id_nullable, author_text, canonical_url, title, published_at, fetched_at, content_type, sponsorship_status, rights_status, text_hash` |
| `editorial_signal` | `signal_id, document_id, signal_type, entity_key, stance, claim_text, evidence_span, confidence, review_status` |
| `relationship_event` | `event_id, journalist_id, event_type, occurred_at, outcome, owner, source_row_ref, next_follow_up_at` |
| `pitch_constraint` | `constraint_id, journalist_id_or_edition_id, reason, starts_at, ends_at, status, approved_by` |
| `media_brief` | `brief_id, scope_id, window_start, window_end, evidence_set_id, coverage_status, generated_at, review_status, reviewer` |
| `media_score_snapshot` | `score_id, edition_id, score_version, seven_component_scores, total_score, grade, evidence, scored_at` |

### 7.2 工作簿映射

| 工作簿字段 | 产品对象 | 规则 |
|---|---|---|
| 媒体、类型/区域、角色定位 | `outlet` / `outlet_edition` | 合并单元格只在原媒体分组内向下填充；国家和 edition 拆分 |
| Social Media | `touchpoint` | 一格多链接拆成多行；归属默认为 `outlet`，不是 `journalist` |
| Editor Name、Position、LinkedIn、个人简介 | `journalist` / `journalist_affiliation` / `touchpoint` | LinkedIn 只存公开核验链接；作者页与个人简介链接分型 |
| Cooperation type、Owner | 关系标签 / owner | 空值保持未知，不继承其他编辑 |
| Editor 联系历史、Pitching Status、Update | `relationship_event` | 原文本保留，人工结构化日期和结果 |
| 评级、优先级、分级标准 | `media_score_snapshot` | 评级不得只保存 S/A/B/C，需保存七项组件和版本 |
| 行号与 sheet 名 | `source_row_ref` | 每个导入对象必须能回溯到原工作表和行 |

---

## 8. 验收与 Go/No-Go

以下阈值为产品建议，必须由 PR 负责人和技术负责人签字后才是正式门槛。

### 8.1 数据门槛

| 门槛 | 建议标准 |
|---|---|
| 导入完整性 | 11 家媒体、48 位编辑均生成稳定 ID；所有空值和冲突进入导入报告 |
| edition 明确 | USA 与 UK/USA 媒体不得无 edition 地混合聚合 |
| 来源状态 | 11 家媒体均有 `approved / pending / blocked / manual_only` 状态和原因 |
| 权利 | 每类来源记录可保存范围、保留期和删除方式 |
| 署名 | 无法可靠归属的文章保留 `author_text`，不得自动进入编辑画像 |

### 8.2 洞察门槛

| 门槛 | 建议标准 |
|---|---|
| 引用可追溯 | 100% 事实性结论绑定原 URL、发布日期、采集时间和证据片段 |
| 无依据风险 | 0 条；风险必须同时满足品牌/产品相关性和人工确认 |
| 编辑归属 | 在人工标注样本上 precision 不低于 90%；不确定项召回可以牺牲，但不能误归属 |
| 内容属性 | 编辑内容、赞助/affiliate、转载和未知必须区分 |
| 缺失表达 | 抓取失败、无匹配和真实零值三种状态不得混写 |

### 8.3 业务门槛

| 门槛 | 建议标准 |
|---|---|
| 评审周期 | 连续完成 2 轮周度评审 |
| Brief 可用率 | 不低于 70% 被评为“无需重大事实修正即可支持判断” |
| Action 采纳率 | Opportunity/Risk/No-pitch 建议不低于 50% 被接受或进入进一步验证 |
| 时间节省 | 相对第 0 周人工 baseline 下降不低于 30% |
| 外部动作 | 0 次未审批的自动联系、发布或风险响应 |

### 8.4 No-Go 条件

出现任一条件即停止自动化扩面：

1. 关键媒体缺少合法、可持续的文章入口，且人工 URL 也无法支撑两轮评审。
2. 署名误归属导致编辑观点被错误归因。
3. 风险卡出现无品牌相关性的严重误报。
4. PR 团队认为 Brief 只是摘要，没有改变 pitch、seeding、资产准备或风险处理决策。
5. 维护工作簿和修正来源的人工成本高于现有流程。

---

## 9. Canonical v1.2 精确变更提案

方案 C 已获用户确认。正式新版本已生成：`PRD-Momcozy-PR-Intelligence-Agent-Canonical-v1.2.md`；v1.1 保留为历史版本，不被覆盖。

| PRD 章节 | 建议变更 |
|---|---|
| 第 0 章 | 新增决策记录：核心媒体洞察是 `P0b / Pilot`，还是替换 P4 成为正式 P0 |
| 第 1.2 节 | 将附件提出的三个业务答案设为媒体洞察唯一结果，并补 baseline |
| 第 2 章 | 新增 `OutletEdition`，明确媒体、edition、编辑和触点四层导航/权限 |
| 第 3.3 节 | 加入工作簿导入、来源状态、署名人工队列、30 天增量 + 180 天基线、赞助识别和失败路径 |
| 第 4.3 节 | 将资源库规则转成 30 天冲突、3 个工作日回填、月度更新和 no-pitch 逻辑 |
| 第 5 章 | 用第 7 节对象替换过薄的 `dim_outlet_journalist`；`Document` 增加可空 `journalist_id` 和署名状态 |
| 第 6 章 | 增加作者页、RSS、人工 URL、媒体社媒发现四类适配器及 `approved/pending/blocked/manual_only` 降级 |
| 第 8 章 | 固化 Media Brief、Opportunity Card、Risk Card 和 Coverage Report 输出契约 |
| 第 9 章 | 若选方案 B，新增 `P0b / Pilot`，不改 P4；若选 C，整体重排 P0/P1 和实施顺序 |
| 第 10 章 | 新增引用、署名、Brief 可用率、Action 采纳率、人工时间和误报指标 |
| 第 11 章 | 新增工作簿导入、编辑归属、竞品观点、风险相关性、冷却期和来源降级验收剧本 |
| 附录 | 增加 7 张工作表到数据对象的映射、未知项和部门签字表 |

### 9.1 文件命名

| 文件 | 定位 |
|---|---|
| `PRD-Momcozy-PR-Intelligence-Agent-Canonical-v1.1.md` | 当前正式 PRD，保持不变 |
| `2026-08-14_PR核心媒体洞察MVP_覆盖评估与Canonical-v1.2变更提案.md` | 本轮评估和变更提案，不是正式 PRD |
| `PRD-Momcozy-PR-Intelligence-Agent-Canonical-v1.2.md` | 业务确认后生成的下一版正式 PRD |

---

## 10. 必须与 PR 团队确认的共识

### 决策级

1. 核心媒体洞察是并行 `P0b / Pilot`，还是替换 P4 成为正式 P0。
2. MVP 只监测 US edition，还是同时含 UK；同名媒体如何拆 edition。
3. 11 家媒体是否为正式封闭范围；48 位编辑中哪些为首轮 10–15 位。
4. 谁是业务 owner、每周评审人和风险升级人。

### 数据级

5. 哪些作者页、媒体页面、内部订阅和历史全文获准使用；允许保存全文、摘要还是仅元数据。
6. 工作簿中媒体官方社媒账号是否只作发现；是否另有编辑个人 X/Instagram/TikTok 名单。
7. 竞品范围和产品型号词典以哪个版本为准。
8. `Cooperation type`、`Editor 联系历史`、`Pitching Status` 的枚举、日期和更新责任人。

### 验收级

9. 当前完成一份媒体/编辑洞察的人工时间 baseline。
10. 什么样的 Brief 算“可用”，什么样的机会算“采纳”，什么情况必须 no-pitch。
11. 安全、质量、隐私和一般负面分别由谁确认，SLA 是多少。

---

## 11. 下一决策节点

建议选择：

- **A → B（推荐）**：先做 5 日 Concierge Validation，通过后转约 2 周 Assisted MVP；P4 保留正式 P0，媒体洞察标记 `P0b / Pilot`。
- **C**：核心媒体洞察替换 P4 成为正式 P0；需要先重签业务优先级和数据责任。

当前选择为方案 C，`Canonical-v1.2` 已生成。下一门槛是 PR、法务、数据与研发团队完成 P0 业务范围、来源权利、责任人和验收阈值签字。
