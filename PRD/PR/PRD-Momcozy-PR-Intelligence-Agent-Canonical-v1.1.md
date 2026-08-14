---
name: momcozy-pr-intelligence-agent-canonical-v1-1
description: Momcozy PR Intelligence Agent 整合版产品需求文档。以 P4 危机预警为 P0，保留品牌、竞品、媒体、机会与战略模块的后续规划，并统一证据、治理、Action 和验收规则。
---

# Momcozy PR Intelligence Agent PRD（Canonical v1.1）

> 版本：v1.1
> 文档状态：产品整合完成，待 PR、法务、产品安全和数据团队评审
> 文档日期：2026-08-14
> 目标团队：Momcozy PR、品牌传播、法务合规、产品安全、数据与研发团队
> 核心逻辑：Media and Industry Monitoring → Insights → Opportunities and Risks → PR Actions
> 研究口径：英文优先检索；媒体、法律与监管事实优先引用项目内已有 deep research 与官方来源；无法确认的内容标记为「未验证」或「此处未解决」

## 0. 整合决策与文档边界

本文件是 PR Intelligence 的唯一产品主规格。整合规则如下：

| 来源 | 吸收内容 | 处理结果 |
|---|---|---|
| `momcozy_pr_intelligence_implementation_plan_2026-08-11.md` | 业务问题、证据与反证、组织治理、RACI、Definition of Done 和阶段路线 | 作为业务与治理依据吸收 |
| 本文件原 v1.0 | 产品结构、状态、数据契约、错误、输出和验收 | 保留为主骨架 |
| `momcozy-pr-intelligence-ai-agent-plan.pplx.md` | 带来源的媒体、竞品、监管和采购研究 | 仅作带时间戳研究附录；外部事实使用前复核 |
| `momcozy-pr-intelligence-ai-agent-plan.ds.md` | 三问表达和报告展示思路 | 归档为概念稿，不作为需求或事实依据 |

已确认的产品规划：P0 只验证 P4 危机预警，范围限定为美国市场、英语、pumping/feeding 品类；首期覆盖产品安全/召回/监管、隐私与数据、误导性宣传与评价真实性、快速升级的负面舆情四类风险。风险采用 `Sev0–Sev4`，由单一事件负责人组织法务、产品安全、隐私或 PR 领域共同确认，主指标为「风险确认与分级总时长」。

待部门确认：具体 SKU 与别名、数据源与合同、分级阈值、SLA、事件负责人、领域审批人、历史样本、baseline 和 Go/No-Go 条件。未完成确认前，文中的相关数字只作为候选验收参数，不代表部门承诺。

## AI 速读卡

- 产品一句话：把全球媒体、行业、竞品和核心媒体信号变成可追溯的 PR 洞察、机会、风险与待审批行动。
- 核心循环：配置监测范围与数据源 → 采集 → 实体与话题分类 → 证据抽取 → 风险/机会评分 → 人工审批 → PR Action → 复盘。
- 目标范围：P0 聚焦美国英语 pumping/feeding 的 P4 危机预警；品牌健康、竞品、核心媒体、机会和战略分析按 P1–P3 扩展。
- 硬约束：每条结论必须能回溯到来源和采集时间；区分事实、主张、推断与未知；AI 不自动联系记者、不自动发布声明。
- 推荐默认：先用获准媒体源、官方监管源和允许使用的内部一方数据验证 P4；不以未经授权的社区采集补齐覆盖。
- 发挥空间：看板视觉、报告版式、模型供应商、队列和云厂商可替换，但不能破坏证据链、风险分级和人工审批。
- P0 验收：PR Analyst 能把一条获准真实风险信号转为 Evidence Card，经人工确认完成 `Sev0–Sev4` 分级、责任人指派、风险 Action 和结果回填；覆盖缺口全程可见。
- 最容易翻车：把新闻条数当 Share of Voice、把单条匿名帖子当事实、把品牌自述当独立验证、让 Agent 自动对外沟通。
- 超预期机会：Claim-Evidence-Counterevidence 卡、Trust Debt 指标、编辑选题冷却期、行动结果反哺模型评估集。

## 第一章：产品概述

### 1.1 产品定位

Momcozy PR Intelligence Agent 是一款面向跨境母婴品牌的媒体情报与 PR 决策产品，让 PR 团队能够持续发现媒体与行业变化、核心媒体选题、竞品动作和风险信号，并在每条结论后看到证据、来源权威度和不确定性，而无需手工浏览新闻、复制链接和拼接周报。

系统不是新闻搜索器，也不是自动写稿机。它必须完成五段闭环：

```text
监测范围与数据源
    |
    v
采集与标准化
    |
    v
实体、话题、主张与证据抽取
    |
    v
风险 / 机会 / 媒体匹配 / 叙事分析
    |
    v
PR Action → 人工审批 → 执行 → 复盘反馈
```

### 1.2 业务目标与问题定义

#### 1.2.1 业务目标

| 目标 | 结果定义 | 首期衡量方式 |
|---|---|---|
| 缩短信息发现时间 | PR 从浏览新闻转为审核已筛选证据 | 基线周与上线后周的人工监测工时对比 |
| 提高行动可执行性 | 每个洞察带建议动作、负责人角色、媒体、角度、时间窗和证据 | Action 完整率、采纳率、闭环时间 |
| 降低误判风险 | 区分采集事实、模型推断、人工判断和未知项 | 证据覆盖率、人工驳回率、抽检错误率 |
| 建立品牌知识资产 | 关键词、竞品、媒体、记者、主张和行动结果可积累 | 词典版本、洞察复用率、复盘数量 |
| 支撑跨部门协同 | 将风险信号映射到法务、安全、客服、产品和传播动作 | 风险升级正确率、事实确认时间 |

#### 1.2.2 业务问题

| 问题 | 需要回答的问题 | 产出 |
|---|---|---|
| 媒体关注什么 | 媒体和行业现在关注哪些品牌内容、产品和议题 | Media and Industry Brief |
| 哪些话题在升温 | 哪些行业趋势和话题值得进入、窗口期如何 | Topic and Trend Cards |
| 竞品在传播什么 | 竞品获得哪些报道、什么角度、哪些评测维度赢输 | Competitor Position Cards |
| 核心媒体在想什么 | 编辑近期写什么、如何评价竞品、有没有切入点 | Media and Journalist Briefs |
| 风险有多严重 | 负面、争议、安全、隐私信号的等级、影响范围和紧迫度 | Risk Signals and Alerts |
| 接下来做什么 | 哪些话题进入、哪些媒体 pitch、什么角度、是否 seeding | PR Action Board |

### 1.3 Momcozy 业务上下文

项目内已有 deep research 对 Momcozy 的品牌、媒体位置、竞品和风险做了系统梳理，以下事实基线直接沿用，投产前需按最新时点重新核验。

#### 1.3.1 品牌与产品

Momcozy 是可穿戴吸奶器起家的跨境母婴 DTC 品牌，官网产品覆盖 Pregnancy、Bras and Postpartum、Pumping、Feeding、On The Go、Baby Care 等分类，产品包括可穿戴吸奶器（M5、M9、S9 Pro、S12 Pro、V1、V2、Air 1、W1 暖按摩吸奶器）、婴儿监视器、奶瓶清洗消毒器（KleanPal Pro）、婴儿背带、哺乳文胸等。标准型号存在 BP 别名映射，例如 M5 Smart 对应 BP380、M9 对应 BP223。来源：Momcozy 官网与 Support 页面，以及项目内 PR 调研方案。

产品含义：

1. 监测词典必须支持标准型号、BP 编码、用户俗称和拼写变体。
2. 品牌已从单一吸奶器扩展到多品类，PR 风险面从单品性能扩展到医疗器械合规、数字隐私、婴儿安全、专家伦理、心理健康和多国监管。
3. 品牌叙事存在「价值/舒适」与「性能领导者」的张力，PR 系统需要按 SKU 和评测维度分析，而不是按品牌名平均。

#### 1.3.2 媒体位置（来自项目内 PR 调研，投产前核验）

| 维度 | 已知事实 | 含义 |
|---|---|---|
| 权威背书 | Babylist 将 M5 Smart 列为 affordable，The Bump 将 V1 Pro 列为最佳整体免提、Air 1 为最隐形之一，Forbes Vetted 将 M5 列为 best value，Consumer Reports 将四款 Momcozy 吸奶器入测 | 价值、舒适、便携和特定形态有可赢维度 |
| 媒体缺口 | What to Expect、Good Housekeeping 美国版、Reviewed（USA TODAY）当前榜单未见 Momcozy，BabyCenter 评测页停留在 2024 年 | 存在明确的 pitch 和送测缺口 |
| 叙事张力 | Wirecutter 对 S9 Pro 使用「largest and least discreet」「clunky」等措辞，Modern Retail 将 Momcozy 置于「dupe/跟随者」框架 | 需要主动纠正或补齐证据，而非只压制负面 |

#### 1.3.3 风险基线（来自项目内 PR 调研，投产前核验）

| 风险 | 类型 | 已知事实 |
|---|---|---|
| KleanPal Pro 集体诉讼 | 产品安全 + 法律 | 2026-05 在 E.D.N.Y. 提起，指控高温消毒下塑料件脱落释放微塑料，ClassAction.org、TINA.org、Law360 已索引 |
| CPSC 公开 incident 报告 | 产品安全 | SaferProducts 上有 BS03 相关公开报告 |
| 美国参议院隐私问询 | 隐私 + 监管 | 2026-06 参议院 HELP 委员会致函关注 App 和联网产品数据处理 |
| 加拿大历史召回 | 监管 | Health Canada RA-72662，因缺少医疗器械许可召回，后于 2023-05 补发许可 |
| 评价真实性质疑 | 信任 + 合规 | Reddit 社区存在隐性营销/虚假评价指控，属未证实但需审计的信号 |

这些风险不能靠「正面内容压制」处理，必须由法务、隐私、产品安全、客服和 PR 共同形成事实包、响应门禁和审计记录。美国 FTC 自 2024-10 实施消费者评价与推荐规则，评价真实性和赞助披露同时是法律与声誉议题。

#### 1.3.4 竞品与赛道

竞品必须按赛道管理，而不是一张品牌名单：

| 赛道 | 主要竞品 |
|---|---|
| 可穿戴/免手持吸奶器 | Willow、Elvie（被 Willow 收购）、Eufy、Medela、Lansinoh、Spectra、BabyBuddha、Bellababy |
| 清洗/喂养电器 | Baby Brezza、Grownsy、Papablic |
| 婴儿监视器 | Nanit、Owlet、Infant Optics、VTech、Eufy |
| 背带 | Ergobaby、BabyBjörn、Tula |
| 产后/护理 | Frida、Haakaa |

系统应为每个竞品维护 Narrative Position Card：主张、证据、媒体接受度、反证和时间线。

### 1.4 三类用户画像

| 角色 | 核心目标 | 对现有工具最大的不满 | 愿意切换的能力 |
|---|---|---|---|
| PR Analyst | 每日发现重要媒体信号，产出周报与风险提示 | 数据散落，手工复制链接，无法判断话题是否真实升温 | 点击洞察即可展开原文、时间、来源权威度、样本量和证据链 |
| PR 与 Media Relations 负责人 | 找到可 pitch 媒体、角度和送测时机 | 编辑画像和竞品观点无法转成可执行 brief | 一键生成带媒体、角度、窗口、资产和风险的 pitch/seeding 建议 |
| 品牌、法务与管理者 | 判断风险、机会和投入是否值得 | 看到结论却不知道来源、权威度和建议依据 | 结论、证据、决策、结果一体化摘要，支持审批和复盘 |

### 1.5 差异化对比表

以下对比是产品定位层面的差异，不代表对具体商业软件的采购级功能审计。

| 能力 | 常见媒体监测或舆情工具 | 本产品 | 实现方式 |
|---|---|---|---|
| 结论可信度 | 常见为指标和摘要并列展示 | 每条 Insight 绑定 evidence_set、source_authority、sample_size 和 uncertainty | 证据服务与报告渲染强制关联 |
| 事实与判断分离 | 情绪分数容易掩盖主张来源 | 区分 claim、evidence、counterevidence、fact、inference、opinion | Claim-Evidence 数据对象 |
| 竞品分析 | 以品牌级声量为主 | 按赛道、SKU、评测维度和 Narrative Position Card 分析 | 分赛道 taxonomy + 版本化竞品卡 |
| 核心媒体运营 | 以名单群发为主 | 按编辑近期选题、竞品观点、证据偏好、冷却期和关系史运营 | journalist brief + 冷却期状态机 |
| 风险分级 | 以负面情绪为主 | 权威度、严重度、扩散速度、多源印证分开评分，并配 SLA | Risk Signal 模型 + War Room |
| 洞察到行动 | 报告后由人再整理任务 | Action 必须含类型、目标媒体、角度、资产、风险和验收指标 | PR Action Engine + 人工审批 |
| 效果衡量 | 以曝光量和声量为主 | 按 AMEC 区分 outputs、out-takes、outcomes、impact | 分层指标 + 贡献说明 |

### 1.6 可行性边界

| 在范围内及原因 | 明确排除在外及原因 |
|---|---|
| 采集授权新闻、官方监管、公开网页、已授权媒体库和内部一方数据 | 绕过版权、登录、验证码、访问控制或平台反自动化机制 |
| 对媒体报道做实体、话题、主张、立场、风险和机会分析 | 把媒体情绪等同于品牌声誉，把互动量等同于影响，把搜索条数等同于 Share of Voice |
| 构建记者画像、竞品观点、冷却期和 pitch 建议 | 保存记者私人联系方式、敏感个人信息或推断性人格标签 |
| 对风险做分级、SLA、事实包和响应门禁 | 自动对外发布声明、纠错、召回通知或直接联系记者 |
| 采购合规媒体数据源，用官方监管源和开放发现源补充 | 未经授权抓取 Reddit 或 TikTok 用于商业监测 |
| P0 采用现有 Python、DuckDB/Parquet、FastAPI 方向做试点 | 在没有真实数据源、授权和验收前承诺全球全平台实时覆盖 |

### 1.7 约束分层

| 硬约束 | 推荐默认 | 发挥空间 |
|---|---|---|
| 所有外部数据必须有 source、source_url 或 document_id、published_at、fetched_at 和权利标签 | 先采购一个合规媒体数据源，再用监管和开放发现源补充 | 可用 Metabase、内置看板或现有 Next.js 看板呈现 |
| 重要结论必须引用至少一条证据，风险和机会结论需要证据等级或标记低置信度 | 先聚焦美国英语市场、pumping/feeding 赛道、8-12 个竞品 | 队列可用 Redis、SQS、Pub/Sub 或现有调度器 |
| AI 生成内容不自动对外发布；任何 pitch、回复、声明、纠错都需人工审批 | 实体解析、话题、风险、机会评分先规则后模型 | LLM 可用已批准的 Kimi、DeepSeek、Claude、OpenAI 或云模型 |
| 删除、下架和合规请求必须能按 document_id 定位并清理 | 原始证据与派生分析分库，保存删除审计记录 | 归档周期和跨区域部署由法务与基础设施团队决定 |
| 时间统一 UTC，展示层按团队时区转换；指标语义统一 | 风险分与置信度分离，不合并成一个数 | 标签可中英双语，模型可按成本策略替换 |

### 1.8 研究范围与来源等级

研究范围（本次 PRD 的覆盖边界）：

1. 品牌报道、行业趋势和分赛道竞品媒体分析。
2. 核心媒体画像、编辑选题、竞品评价和潜在切入点。
3. 负面、争议、产品安全、隐私和监管风险信号。
4. 洞察到 PR Action 的转化，包括话题进入、媒体 pitch、产品 seeding、专家 engagement 和风险升级。
5. 每周 PR Intelligence Report 的生成、审核和复盘闭环。

来源等级：

1. A 级：监管与官方事实，例如 FDA、FTC、Health Canada、法院、政府、公司政策与备案。
2. B 级：核心媒体与授权媒体库，例如 Babylist、The Bump、Forbes Vetted、Consumer Reports、Marie Claire。
3. C 级：开放新闻发现，例如 GDELT、Media Cloud、Google News 线索。
4. D 级：社交、视频与搜索信号，例如 X、YouTube、Google Trends。
5. E 级：受限社区，例如 Reddit、TikTok、Meta 社区，需独立商业授权。
6. F 级：内部一方数据，例如 PR 台账、CRM、客服、退货、质保、产品安全、销售与搜索。

本轮直接核验的官方来源与用途：

| 编号 | 来源 | 用途 |
|---|---|---|
| 来源 1 | https://momcozy.com/ | 品牌产品与业务分类 |
| 来源 2 | https://momcozy.com/collections/wearable-breast-pump | 吸奶器产品与使用场景 |
| 来源 3 | https://support.momcozy.com/article/54801143113369 | 标准型号与 BP 别名映射 |
| 来源 4 | https://developers.google.com/youtube/v3/getting-started | YouTube API 资源与配额 |
| 来源 5 | https://developers.google.com/youtube/v3/docs/search/list | YouTube 搜索能力与限制 |
| 来源 6 | https://developers.tiktok.com/products/research-api | TikTok Research Tools 资格边界 |
| 来源 7 | https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers | Creator 与赠品披露要求 |
| 来源 8 | https://docs.langchain.com/oss/python/langgraph/persistence | Agent 持久化与恢复 |
| 来源 9 | https://docs.langchain.com/oss/python/langgraph/interrupts | Agent 人工审批 |
| 来源 10 | https://docs.getdbt.com/docs/build/data-tests | 数据质量断言 |
| 来源 11 | https://aws.amazon.com/solutions/guidance/social-media-data-pipeline-on-aws/ | 多源数据管道模式 |

项目内已有 deep research 是事实基线的主要来源：

| 编号 | 文件 | 用途 |
|---|---|---|
| 基线 1 | PR/momcozy_pr_intelligence_implementation_plan_2026-08-11.md | 品牌、竞品、媒体、风险、数据架构、评分模型、路线图 |
| 基线 2 | PR/momcozy-pr-intelligence-ai-agent-plan.pplx.md | 竞品矩阵、核心媒体画像、行业趋势与来源链接 |

研究限制：本 PRD 不对媒体榜单、诉讼进展、监管问询答复和竞品声量做重新测量，这些事实以项目内 deep research 为基线，投产前必须按最新时点重新核验并建立基线。

## 第二章：整体布局与导航

### 2.1 产品信息架构

```text
Momcozy PR Intelligence
|
+-- 首页 Overview
|   +-- 今日重要媒体信号
|   +-- 话题与竞品变化
|   +-- 风险与机会
|   +-- 待处理 Action
|
+-- 媒体与行业监测 Media Radar
|   +-- 品牌报道
|   +-- 行业趋势
|   +-- 竞品矩阵
|   +-- 叙事与反叙事
|
+-- 核心媒体 Media Workbench
|   +-- 媒体与记者画像
|   +-- 选题与竞品观点
|   +-- pitch 与冷却期
|
+-- 风险 Risk War Room
|   +-- 风险信号
|   +-- 分级与 SLA
|   +-- 事实包与时间线
|
+-- 机会 Opportunity Planner
|   +-- 机会排序
|   +-- 媒体匹配
|   +-- 资产缺口
|
+-- PR Action Center
|   +-- 待审核
|   +-- 进行中
|   +-- 已完成
|   +-- 复盘
|
+-- 周报 Weekly Report
|   +-- 生成
|   +-- 审核
|   +-- 历史与导出
|
+-- 治理 Governance
    +-- 监测范围与词典
    +-- 数据源与授权
    +-- 评分规则与阈值
    +-- 用户与权限
    +-- 数据质量与成本
```

### 2.2 桌面端布局

```text
+--------------------------------------------------------------------------------+
| 顶栏 12%：Momcozy PR Intelligence | 数据日期 | 覆盖状态 | 通知 | 账号菜单     |
+-------------+------------------------------------------------------------------+
| 左侧导航    | 主内容区 78%                                                     |
| 20%         |                                                                  |
|             |  页面标题 + 时间范围 + 市场/赛道/来源筛选 + 来源能力提示           |
| Overview    |  +----------------+----------------+---------------------------+ |
| 媒体雷达    |  | 重要媒体信号    | 话题变化        | 风险与机会摘要           | |
| 核心媒体    |  +----------------+----------------+---------------------------+ |
| 风险        |  | 报道/证据卡片：来源、发布时间、权威度、实体、标签、打开原文        | |
| 机会        |  +--------------------------------------------------------------+ |
| Action      |  | 主图表：声量 / 话题动量 / 竞品占位 / 媒体覆盖                     | |
| 周报        |  +--------------------------------------------------------------+ |
| 治理        |  | 右侧抽屉：Insight 详情、证据链、生成 Action、人工反馈            | |
|             |                                                                  |
+-------------+------------------------------------------------------------------+
| 底部状态栏 10%：最近采集时间 | 成功率 | 缺口来源 | 当前报告生成状态                   |
+--------------------------------------------------------------------------------+
```

布局理由：PR 工作首先是判断优先级和可信度，而不是浏览所有报道。主界面先展示「重要信号」和数据覆盖状态，再进入证据卡片和原文；风险、机会、Action 使用固定导航，避免把任务状态藏在聊天窗口里。

### 2.3 首次使用流程

```text
进入系统
  |
  +-- 已有监测范围 --> 进入 Overview，显示最近一次运行和覆盖状态
  |
  +-- 没有监测范围 --> 配置向导
                         |
                         +-- 选择 Momcozy 品牌、产品、竞品和赛道
                         +-- 选择市场和语言
                         +-- 选择数据源与授权状态
                         +-- 添加核心媒体和记者
                         +-- 设置风险等级、SLA 和告警
                         +-- 运行连接测试
                         +-- 创建首个监测任务
```

### 2.4 角色权限

| 角色 | 查看洞察 | 配置监测 | 审批 Action | 管理凭证 | 导出原文 |
|---|---:|---:|---:|---:|---:|
| PR Analyst | 是 | 是 | 是 | 否 | 受限 |
| PR / Media Relations | 是 | 可编辑媒体关系 | 是 | 否 | 受限 |
| Brand / Legal / Safety | 是 | 否 | 可审批对应风险 | 否 | 受限 |
| Admin | 是 | 是 | 是 | 是 | 按合规策略 |
| Viewer | 是 | 否 | 否 | 否 | 否 |

权限原则：凭证只保存 secret_ref；记者关系、危机材料和内部一方数据不能因语义搜索默认向所有 PR 用户开放。

## 第三章：核心模块详细设计

### 第 3.1 节 监测范围与数据源管理

#### a) ASCII 图

```text
+----------------------------------------------------------------------------+
| 监测范围                                                                    |
| 品牌 Momcozy | 赛道 pumping | 市场 US | 语言 en | 数据源 3/5 已授权           |
+------------------------+---------------------------------------------------+
| 监测对象              | 数据源能力卡                                      |
| 品牌：Momcozy          | 媒体库：已授权，覆盖美英加，含全文与权利标签        |
| 产品：M5 M9 Air 1 W1   | 监管源：FDA、FTC、Health Canada、CPSC，每日         |
| 竞品：Willow Eufy 等   | 开放发现：GDELT 或 Google News 线索，用于回链        |
| 媒体：Babylist 等      | 社交信号：X 近 7 天、YouTube 按配额、Trends 待批准   |
| 记者：待团队导入       | 受限社区：Reddit/TikTok 待商业授权                   |
+------------------------+---------------------------------------------------+
| 操作：新增监测对象 | 测试连接 | 查看覆盖缺口 | 保存版本 | 停用          |
+----------------------------------------------------------------------------+
```

界面实现时，未配置项显示为空状态和明确 CTA，不预置未确认的账号或数据源。

#### b) 交互流程

正常流程：

```text
管理员选择新增数据源
  --> 选择类型：媒体库 / 监管源 / 开放发现 / 社交信号 / 受限社区 / 内部数据
  --> 输入凭证引用、市场、语言和权利说明
  --> 系统预览可采字段和覆盖范围
  --> 测试连接
  --> 保存配置版本
  --> 调度器在下一周期使用新版本
```

失败流程一：凭证过期或额度不足。

```text
测试连接
  --> 返回认证失败或额度耗尽
  --> 状态变为待授权，隐藏原凭证
  --> 展示重新授权入口和影响范围
  --> 不删除历史数据，不继续重试无效请求
```

失败流程二：数据源可访问但全文或权利受限。

```text
测试连接
  --> 返回元数据但缺少全文或转发权利
  --> 创建 coverage_gap 记录
  --> 数据源标记为部分可用
  --> 报告显示字段缺口，不把缺失值当作 0
```

失败流程三：监管源 schema 变化。

```text
每日采集
  --> 监管源返回字段结构变化
  --> 连接器进入质量保护，保存字段差异
  --> 相关监管风险报告暂缓生成
  --> 更新 adapter 并回放样本
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 草稿 | 新数据源未保存 | 灰色 Draft | 保存或放弃 |
| 已启用 | 配置保存且连接测试通过 | 绿色 Enabled | 停用、授权失效或质量失败 |
| 部分可用 | 只能获取部分字段或覆盖有限 | 黄色 Partial | 字段恢复或人工确认继续使用 |
| 待授权 | 凭证缺失、过期或额度不足 | 橙色 Action needed | 完成授权并测试通过 |
| 已暂停 | 管理员暂停或数据源风险触发熔断 | 蓝色 Paused | 管理员恢复 |
| 质量异常 | 连续运行无数据、重复率异常或 schema 变化 | 红色 Quality issue | 修复连接器并通过回归样本 |

#### d) 依赖关系

```text
监测配置
  --> source_registry
  --> keyword_and_competitor_dictionary
  --> collection_job
  --> source_cursor
  --> coverage_report
```

读取：品牌实体、产品别名、竞品、媒体、数据源权利和授权引用。写入：配置版本、连接测试、覆盖缺口、调度任务。该模块不直接写 Insight 和 Action。

#### e) 待决问题

1. Momcozy 生产环境是否已有 Meltwater、Cision、Muck Rack、Factiva 或 LexisNexis 等媒体数据订阅，现有权利和出口限制是什么。
2. 美国英语市场内的目标媒体、监管来源、销售渠道和地域判定规则分别是什么。
3. 内部一方数据（PR 台账、客服、退货、质保、产品安全）是否允许接入，以及以何种聚合粒度接入。

### 第 3.2 节 品牌与行业竞品分析 Media and Industry Monitoring

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| 媒体与行业监测 过去 7 天 | 市场 US | 赛道 pumping/feeding | 覆盖 72%             |
+-------------------+----------------+-------------------+-------------------------+
| 品牌报道量          | 42 条去重        | 权威来源 6 家        | 转载已聚类                |
| 升温话题            | 工作母亲支持、清洁便利、隐私透明度                                |
| 竞品动作            | 竞品新品、保险渠道、评测排名变化                                  |
+-------------------+----------------+-------------------+-------------------------+
| 报道卡：The Bump 将 V1 Pro 列为最佳整体免提                                  |
| 事实：媒体认可外置动力免提形态；推断：存在定向评测机会；未知：榜单更新节奏      |
| 证据：报道链接、发布时间、采集时间、权威度、立场标签                          |
| 操作：打开原文 | 对比上一周期 | 生成机会 Action | 标注误报                          |
+--------------------------------------------------------------------------------+
| 左：品牌/竞品声量 | 中：话题动量与占位 | 右：证据抽屉与反证                         |
+--------------------------------------------------------------------------------+
```

#### b) 交互流程

正常流程：

```text
用户选择时间范围、市场、赛道和实体
  --> 系统读取标准化文档和提及
  --> 过滤转载、促销和低相关记录
  --> 实体解析与话题分类
  --> 计算声量、来源权威度、立场、变化率和覆盖
  --> 生成媒体与竞品 Insight 卡片
  --> 分析师打开证据并确认、修改或驳回标签
  --> 确认后的 Insight 可生成机会或风险 Action
```

失败流程一：转载导致声量虚高。

```text
声量统计
  --> 检测到同一报道被多次转载
  --> 按首发聚类，保留传播节点
  --> 报告展示去重声量和转载范围
  --> 不把转载量当作独立媒体报道
```

失败流程二：竞品品牌歧义。

```text
竞品提及解析
  --> 品牌名与产品、人名或机构重名
  --> 实体消歧置信度低
  --> 该条进入人工复核
  --> 不进入竞品声量比较
```

失败流程三：话题聚类不稳定。

```text
每日聚类
  --> 新旧聚类无法稳定匹配
  --> 保留 cluster lineage 和版本
  --> 报告说明本周与上周不可直接比较
  --> 分析师可合并、拆分或重命名话题
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 数据准备中 | 采集任务仍在运行 | 蓝色进度条 | 数据达到最低样本或任务结束 |
| 部分覆盖 | 至少一个重点数据源不可用 | 黄色 Coverage gap | 数据源恢复或人工确认报告 |
| 已聚类 | 话题与样本已生成 | 蓝色 Topic ready | 重新运行或人工修订 |
| 待核验 | 关键结论缺证据或低置信度 | 橙色 Review | 分析师确认或驳回 |
| 已确认 | 证据和标签通过人工审核 | 绿色 Verified | 进入报告或生成 Action |
| 已驳回 | 误匹配、转载、无关或证据不足 | 灰色 Rejected | 重新采集或加入排除规则 |
| 风险升级 | 安全、隐私、监管或传播速度满足规则 | 红色 Escalated | 进入 Risk War Room |

#### d) 依赖关系

```text
ODS documents
  --> DWD mentions and claims
  --> entity and taxonomy classification
  --> topic clusters and competitor position cards
  --> evidence sets
  --> media and industry insights
  --> opportunity / risk / action engine
```

读取：文档、提及、主张、竞品词典、产品词典、历史基线。写入：话题簇、竞品卡、叙事、证据集、人工标注。

#### e) 待决问题

1. Share of Relevant Voice 的合格媒体池、目标话题和权威度权重如何定义；首期先建立基线，不把搜索条数当 SOV。
2. 竞品池是 8-12 个还是按赛道扩展，是否包含地区账号和收购后合并品牌。
3. 是否需要对叙事反叙事（例如 Marie Claire 对哺乳产品化的批评）单独建模。

### 第 3.3 节 核心媒体洞察 Media Workbench

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| 核心媒体 | 时间 180 天 | 分层：评测/消费/商业/监管 | 记者 24 人已画像              |
+--------------------------------------------------------------------------------+
| 媒体：Consumer Reports | 主题：可穿戴泵、婴儿监视器安全 | 立场：独立、安全优先          |
| 记者：由团队配置的署名 | 近期选题 | 证据偏好：测试方法、安全、隐私 | 冷却期：无              |
| 竞品观点：公开评测维度与排名 | 与 Momcozy 关系：已入测，需补具体型号证据                    |
| 潜在切入：non-WiFi 监视器隐私、具体型号的实测维度                                |
| 操作：查看时间线 | 标注画像 | 生成 pitch 草稿 | 加入 Action | 设置冷却期                    |
+--------------------------------------------------------------------------------+
| 左：媒体/记者画像 | 中：近 180 天选题与竞品观点 | 右：pitch 角度与资产缺口           |
+--------------------------------------------------------------------------------+
```

记者画像不保存敏感私人信息或推断性人格标签，只保存公开署名、近期选题、报道形式、证据偏好、竞品观点、地域、受众和关系史。

#### b) 交互流程

正常流程：

```text
管理员添加核心媒体和记者公开署名
  --> 定期采集其近期文章、榜单和观点
  --> 聚合 180 天主题、形式、证据偏好和竞品评价
  --> 检测编辑变动和选题变化
  --> 生成 Media Brief
  --> Analyst 审核后生成 pitch 或 seeding 建议
```

失败流程一：记者署名无法可靠归属。

```text
文章采集
  --> 署名缺失或存在同名
  --> 标记 source_identity_unverified
  --> 不纳入记者画像比较
  --> 允许分析师手动确认或删除
```

失败流程二：竞品观点来源是赞助内容。

```text
观点抽取
  --> 检测到 affiliate 或赞助披露
  --> 观点标记商业机制，降低独立验证权重
  --> 报告区分编辑部观点与商业内容
```

失败流程三：编辑刚完成同题报道。

```text
pitch 建议
  --> 检测到编辑近期已写同题
  --> 触发冷却期
  --> 系统输出不 pitch 理由
  --> 等待冷却期结束或编辑转向新题
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 待验证署名 | 记者已输入但身份未确认 | 黄色 Unverified | 人工确认或删除 |
| 已画像 | 记者身份和采集范围确认 | 绿色 Profiled | 暂停或失效 |
| 选题变化候选 | 近 180 天主题偏离历史 | 橙色 Shift candidate | 人工确认或降级 |
| 冷却期 | 近期同题、禁联或关系风险 | 蓝色 Cooldown | 冷却期结束或人工解除 |
| pitch 就绪 | 选题契合、证据充分、无冲突 | 紫色 Ready | 生成 brief、拒绝或过期 |
| 关系复核 | 负面、争议或披露不明 | 红色 Review | 品牌负责人确认 |

#### d) 依赖关系

```text
outlet and journalist registry
  --> journalist articles and competitor views
  --> beat and evidence preference timeline
  --> cooldown and relation status
  --> pitch readiness
  --> media brief / action
```

#### e) 待决问题

1. 核心媒体清单由 PR 团队确认还是按分层方法先候选后确认；推荐默认先候选 20-40 家再确认。
2. 是否接入 Muck Rack 或类似记者数据库补齐署名、联系方式和机构关系。
3. 冷却期规则由谁维护，是否区分禁联、刚同题、利益冲突和关系恶化。

### 第 3.4 节 风险识别与预警 Risk War Room

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| Risk War Room | 待核验 4 | 升级 2 | 已结案 11 | SLA 未超时                        |
+--------------------------------------------------------------------------------+
| 风险：产品安全信号 | 等级 Sev2 | 置信度 中 | 影响范围：单 SKU/市场 | 责任人：安全负责人 |
| 事实：公开 incident 报告存在 | 未知：内部事故率未接入 | 禁止表述：断言无风险             |
| 时间线：首次信号 → 核验 → 事实包 → 升级 → 结案                                      |
| 操作：查看证据 | 生成事实包 | 升级 | 记录口径 | 结案                          |
+--------------------------------------------------------------------------------+
| 左：风险队列 | 中：分级与 SLA | 右：事实包、时间线、stakeholder map           |
+--------------------------------------------------------------------------------+
```

#### b) 交互流程

正常流程：

```text
系统检测负面、安全、隐私、监管或真实性信号
  --> 证据核验与多源印证
  --> 计算风险分和置信度
  --> 生成分级和 SLA
  --> 通知责任人
  --> 生成事实包：已知、未知、待核验、禁止表述
  --> 人工确认后升级或结案
```

失败流程一：信号严重但证据不足。

```text
风险检测
  --> 高严重度但低置信度
  --> 不因证据不足沉底
  --> 快速进入人工核验
  --> 显示置信度而非隐藏信号
```

失败流程二：把许可问题误读为安全缺陷。

```text
监管信号解析
  --> 识别召回原因和纠正状态
  --> 保存完整时间线和纠正记录
  --> 禁止标题式误读
  --> 由监管团队复核口径
```

失败流程三：人工未及时响应。

```text
风险触发
  --> SLA 超时
  --> 自动升级到更高责任人
  --> 记录升级轨迹
  --> 更新 stakeholder map 和通知
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 待核验 | 信号出现但未验证 | 灰色 Unverified | 核验完成 |
| 已确认 | 事实核验通过 | 绿色 Confirmed | 分级或结案 |
| 升级中 | 满足分级和 SLA 条件 | 橙色 Escalated | 责任人确认 |
| War Room | Sev3/Sev4 事件 | 红色 Active | 事件降级或结案 |
| 已结案 | 事实闭环、口径确定、行动完成 | 深绿色 Closed | 归档 |
| 误报 | 核验后确认无关或错误 | 灰色 False positive | 加入排除规则 |

#### d) 依赖关系

```text
risk signals
  --> claim and evidence verification
  --> risk scoring and confidence
  --> severity and SLA
  --> fact pack and timeline
  --> incident workflow and closure
```

#### e) 待决问题

1. 风险分公式的权重是否需要按产品安全、隐私、真实性等类型分别配置。
2. 严重风险是否需要与客服、质保、产品安全和法务系统联动，还是只在 War Room 内跟踪。
3. 内部事故数据（客服、退货、质保、事件报告）以何种权限和粒度接入。

### 第 3.5 节 机会识别 Opportunity Planner

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| Opportunity Planner 过去 7 天 | 候选 8 | 已批准 3 | 已忽略 2                          |
+--------------------------------------------------------------------------------+
| 机会：工作母亲实用支持 | 评分 74 | 话题动量 中 | 媒体契合 高 | 资产缺口：法律审核、双语 toolkit |
| 目标媒体：女性职场、HR、家庭政策媒体 | 角度：PUMP Act 权益 + 泵奶空间 checklist            |
| 证据：政策来源、行业趋势、媒体兴趣 | 风险：不得暗示购买设备就能克服系统问题                    |
| 操作：查看证据 | 生成 pitch 草稿 | 标记资产缺口 | 加入 Action | 忽略                        |
+--------------------------------------------------------------------------------+
| 左：机会排序卡 | 中：媒体匹配与角度 | 右：资产缺口与风险                    |
+--------------------------------------------------------------------------------+
```

#### b) 交互流程

正常流程：

```text
系统从话题、竞品、媒体和品牌证据中识别机会
  --> 计算机会分和风险惩罚
  --> 匹配目标媒体、编辑和角度
  --> 识别资产缺口
  --> 生成 Opportunity Card
  --> Analyst 审核后生成 pitch 或 seeding Action
```

失败流程一：证据不足但话题很热。

```text
机会识别
  --> 热度高但缺少可验证证据
  --> 机会降级为观察任务
  --> 不生成对外 pitch
  --> 等待证据补齐
```

失败流程二：机会涉及医疗或健康宣称。

```text
机会评估
  --> 命中健康、安全或疗效相关规则
  --> 加专业团队复核
  --> 禁止生成绝对化和疗效性表述
```

失败流程三：机会窗口已过期。

```text
用户打开机会
  --> 时间窗已过去
  --> 标记为过期
  --> 保留为历史洞察
  --> 可从历史证据创建常青内容机会
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 候选 | 评分后未人工审核 | 灰色 Candidate | 编辑、忽略或删除 |
| 待审核 | 信息完整等待 Analyst | 橙色 Review | 批准或驳回 |
| 已批准 | 审核通过可执行 | 绿色 Approved | 转 Action、过期或取消 |
| 资产缺口 | 缺证据、素材或专家 | 黄色 Asset gap | 补齐资产或降级 |
| 已过期 | 时间窗结束 | 灰色 Expired | 保留历史复盘 |
| 已驳回 | 人工认为不适合或证据不足 | 灰色 Rejected | 新证据触发重建 |

#### d) 依赖关系

```text
topic / competitor / media / brand evidence
  --> opportunity scoring
  --> media match
  --> angle and asset gap
  --> opportunity card
  --> action engine
```

#### e) 待决问题

1. 机会分公式的权重和风险惩罚系数由谁确认，是否按产品赛道分别配置。
2. 是否把内部样机库存、专家可用性和预算纳入资产缺口判断。
3. 是否需要区分「品牌机会」和「商业促销」，避免把折扣当品牌 PR 机会。

### 第 3.6 节 PR Action Engine 与 Action Center

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| PR Action Center | 待审核 9 | 进行中 6 | 已完成 18 | 待复盘 4                        |
+--------------------------------------------------------------------------------+
| P1 媒体 pitch | 向 Consumer Reports 补充 V1 Pro 实测维度 | 截止 08-18 | 证据 12 条 | 审核 |
| P1 风险应对 | 准备 KleanPal Pro 事实包 | 责任人：法务+PR | 截止 08-15 | 证据 8 条 | 审核    |
| P2 产品 seeding | 向 The Bump 送测 Air 1 | 截止 08-25 | 证据 6 条 | 审核                         |
| P2 专家 engagement | 匹配 IBCLC 支持工作母亲议题 | 截止 08-30 | 证据 9 条 | 审核              |
+--------------------------------------------------------------------------------+
| Action 详情                                                                      |
| 为什么现在做 | 依据哪些证据 | 具体做什么 | 谁负责 | 需要什么资产 | 风险与禁用表述     |
| 成功指标 | 执行状态 | 复盘结果 | 关联洞察 | 关联媒体/竞品/风险                              |
+--------------------------------------------------------------------------------+
```

#### b) 交互流程

正常流程：

```text
媒体、竞品、机会和风险模块产生 Insight
  --> Action Engine 根据规则和模板生成候选 Action
  --> 计算优先级、紧迫性、证据完整度和风险
  --> Analyst 编辑角度、媒体、负责人和验收指标
  --> 品牌或法务负责人审批
  --> 状态变为进行中
  --> 执行者补充外联、发布或结案结果
  --> 复盘并标记采纳、部分有效、无效或无法执行
```

失败流程一：证据不足。

```text
Action Engine
  --> 结论只有单条低置信度证据
  --> 生成观察任务而非立即行动
  --> Action 不能进入已审批状态
```

失败流程二：涉及对外沟通。

```text
Action Engine
  --> 命中 pitch、回复、声明、纠错或召回规则
  --> 必须人工审批
  --> 禁止自动联系记者或自动发布
```

失败流程三：时间窗已过期。

```text
用户打开 Action
  --> 时间窗已过去
  --> Action 标记为过期
  --> 保留为历史，不标记为已执行
  --> 可从历史证据创建常青 Action
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 候选 | 模型生成但未人工编辑 | 灰色 Candidate | 编辑、忽略或删除 |
| 待审核 | 信息完整等待 Analyst/品牌负责人 | 橙色 Review | 批准或驳回 |
| 已批准 | 审核通过可执行 | 绿色 Approved | 开始执行、过期或取消 |
| 进行中 | 已发起外联或任务 | 蓝色 In progress | 补充结果或标记阻塞 |
| 已阻塞 | 缺资产、权限、预算或事实 | 红色 Blocked | 解决阻塞、取消或重规划 |
| 已完成 | 执行者提交结果 | 深绿色 Done | 进入复盘 |
| 已复盘 | 结果、偏差和学习已记录 | 紫色 Learned | 归档 |
| 已驳回 | 人工认为不适合或证据不足 | 灰色 Rejected | 新证据触发重建 |

#### d) 依赖关系

```text
media / competitor / opportunity / risk insights
  --> action_candidate
  --> human review
  --> action_execution
  --> action_result
  --> feedback and evaluation set
```

#### e) 待决问题

1. Action 是否需要同步到飞书、Slack、Jira、Asana 或现有内容日历。
2. 执行结果由谁填写，是否能回接媒体覆盖、回复率、榜单位次和传播结果。
3. 是否允许品牌或法务负责人直接审批，还是必须 Analyst 先确认证据。

### 第 3.7 节 每周 PR Intelligence Report 生成

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| Weekly Report Builder | 周期 2026-W33 | 状态 待审核 | 数据冻结 08-09 24:00           |
+--------------------------------------------------------------------------------+
| 报告结构                                                                        |
| 执行摘要 → 媒体与行业 → 竞品 → 核心媒体 → 机会与风险 → PR Actions → 来源附录      |
| 覆盖与限制：数据源 3/5 可用，受限社区未纳入，声量为去重后相关报道                 |
| 引用检查：重大结论 12/12 有 evidence_set_id，抽检通过                            |
| 操作：预览 | 编辑 | 发送审核 | 导出 Markdown/JSON/PDF | 版本历史                  |
+--------------------------------------------------------------------------------+
| 左：报告章节 | 中：引用与覆盖检查 | 右：审核与导出                              |
+--------------------------------------------------------------------------------+
```

#### b) 交互流程

正常流程：

```text
周期结束冻结数据
  --> 系统聚合已核验洞察、机会、风险和 Action
  --> 生成带引用和覆盖说明的草稿
  --> 检查引用覆盖、样本量、时间窗和模型版本
  --> Analyst 编辑并发送审核
  --> 品牌负责人批准后发布
  --> 回写接受/拒绝原因和行动状态
```

失败流程一：数据覆盖不完整。

```text
报告生成
  --> 检测到数据源缺口
  --> 标题使用已覆盖范围，不写全平台
  --> 显示缺口和影响范围
  --> 禁止把缺失当作零或无事发生
```

失败流程二：出现无来源结论。

```text
报告生成
  --> 检测到结论无 evidence_set_id
  --> 该结论降级为观察提示
  --> 报告不通过发布门槛
  --> 补充证据后重跑
```

失败流程三：模型版本变更导致结果不可比。

```text
报告生成
  --> 检测到模型或词典版本变化
  --> 报告标注版本和可比性说明
  --> 保留旧版本报告
  --> 不覆盖历史数字
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 数据冻结 | 周期结束锁定数据 | 蓝色 Frozen | 报告生成 |
| 生成中 | 正在聚合和渲染 | 蓝色进度 | 草稿完成或失败 |
| 待审核 | 草稿等待 Analyst/品牌负责人 | 橙色 Review | 批准或驳回 |
| 已批准 | 审核通过可发布 | 绿色 Approved | 发布 |
| 已驳回 | 需要修改 | 灰色 Rejected | 修改后重新审核 |
| 已发布 | 报告对外或对内分发 | 深绿色 Published | 归档 |
| 生成失败 | 数据、模型或渲染错误 | 红色 Failed | 修复后重跑 |

#### d) 依赖关系

```text
verified insights + opportunities + risks + actions
  --> report aggregation
  --> citation and coverage check
  --> report draft
  --> human approval
  --> published report + feedback
```

#### e) 待决问题

1. 周报的接收人、分发渠道和审批链由谁定义。
2. 周报是否必须包含法务、产品安全和客服等跨部门附录。
3. 周报发布后是否自动生成下周的跟进任务。

## 第四章：超越竞品的差异化功能

### 第 4.1 节 Evidence-first PR Action Chain

#### 1. 竞品为何未必具备这一能力

这是基于公开产品形态的推断，不是对具体厂商内部实现的事实判断。传统媒体监测平台以搜索、指标和报告为主，任务系统以执行为主，两者由不同数据模型和团队维护，导致「为什么做这个动作」常需人工复制链接。本产品把证据对象设计成 Insight 和 Action 的共同依赖，产品边界从报告结束延伸到行动复盘。

#### 2. 本产品如何实现

每条 Insight 必须包含 evidence_set_id。每个 Action 必须引用一个或多个 Insight。报告渲染器在无 evidence_set 时只能输出观察性提示，不能输出强行动语言。证据集包含来源、采集时间、权威度、内容摘录、立场标签、模型版本和人工审核记录。推荐默认用关系表实现引用完整性，搜索引擎只负责检索，不作为唯一事实存储。

#### 3. 交互流程

```text
原始文档
  --> 证据记录
  --> 媒体/竞品/机会/风险 Insight
  --> Action 候选
  --> 人工审核
  --> 执行结果
  --> 复盘反馈
```

#### 4. 风险与应对

风险：来源内容被删除或链接失效。应对：保存允许保留的最小摘录、document_id、采集时间和删除标记；不承诺永久复现原文。

### 第 4.2 节 Claim-Evidence-Counterevidence Card

#### 1. 竞品为何未必具备这一能力

普通情感和话题标签容易把主张当事实，也容易忽略反证。PR 的核心判断往往依赖「主张、支持证据、反证、证据等级」四者，而不是单一情绪分数。这里的差异不是模型更聪明，而是把主张和证据作为一级对象显式建模。

#### 2. 本产品如何实现

建立 claim、evidence、counterevidence 三类对象，并维护 supports_or_refutes 关系。证据状态区分 verified_primary、verified_multiple_independent、credible_single_source、unverified_allegation、brand_claim、opinion、contradicted、resolved。每张卡显示事实窗口、市场、实体、支持证据、反证和未知项。

#### 3. 交互流程

```text
文档
  --> 主张抽取
  --> 支持证据与反证匹配
  --> 证据等级判定
  --> 人工审核
  --> 决策依据
```

#### 4. 风险与应对

风险：模型把相关性误判为因果或把转载当独立印证。应对：关系类型区分证据支持、模型推测、人工确认，报告不使用因果性语言，除非有业务验证。

### 第 4.3 节 核心媒体决策机制

#### 1. 竞品为何未必具备这一能力

媒体监测工具通常提供记者名单和提及，但未必把「编辑近期选题、竞品观点、证据偏好、冷却期、关系史」连成可执行的 pitch 决策。名单群发与按决策机制运营的差距来自数据对象之间的显式关系。

#### 2. 本产品如何实现

为每位核心记者维护可审计的 Media Brief：近 180 天主题、报道形式、常用证据、竞品评价、关注的风险、地域与受众、已知利益冲突、最近接触和跟进日期。pitch 建议必须输出不 pitch 的理由，例如证据不足、编辑刚完成同题、品牌没有独立数据、潜在利益冲突或风险未闭环。

#### 3. 交互流程

```text
记者文章
  --> 主题、形式和证据偏好时间线
  --> 竞品观点与关系史
  --> 冷却期与冲突检测
  --> pitch 就绪判断
  --> 人工确认后外联
```

#### 4. 风险与应对

风险：公开信息不足造成误判。应对：显示数据完整度，允许输出无法判断，不把缺失解释为没有关系。

### 第 4.4 节 Trust Debt 信任债务指标

#### 1. 竞品为何未必具备这一能力

品牌对外的承诺若快于证据、合规、服务或问答准备，会累积信任风险。传统工具倾向于报告曝光和声量，缺少把未闭环高风险项、缺失证据的高频主张、逾期媒体承诺、未披露 seeding 和政策差异统一起来的内部优先级指标。

#### 2. 本产品如何实现

Trust Debt 不是对外发布的单一分数，而是内部优先级工具，用未闭环高风险项、缺失证据的高频主张、逾期媒体承诺、未披露 seeding、政策与实际数据流差异、重复客服问题等代理指标衡量。债务高的赛道先补事实和流程，不加大发声。

#### 3. 交互流程

```text
未闭环风险 + 缺失证据主张 + 逾期承诺 + 未披露关系
  --> Trust Debt 计算
  --> 按赛道排序
  --> 触发事实补齐或降级建议
  --> 纳入治理看板
```

#### 4. 风险与应对

风险：指标被当作对外声誉分数。应对：产品明确标注为内部优先级工具，不导出、不对外、不进入公开报告。

## 第五章：数据模型

### 5.1 数据模型原则

1. 原始事实、派生分析和人工判断分开保存。
2. 所有跨平台 ID 作为字符串保存。
3. 时间字段同时保存 published_at、fetched_at、metric_observed_at 和 valid_until。
4. 每个派生结论保存 model_name、model_version、prompt_version、created_at 和 evidence_set_id。
5. 列表型关系使用子表或关系表实现；下面 JSON 示例只展示单条记录，实际数据库不依赖一个超大 JSON 文档。

### 5.2 Source 数据契约

```json
{
  "version": "1.0", // 必填，契约版本
  "source_id": "source_babylist", // 必填，来源唯一标识
  "publisher": "Babylist", // 必填，发布者名称
  "source_type": "commerce_editorial", // 必填，regulatory、commerce_editorial、news、social、community 或 internal
  "country": "US", // 默认值为 unknown，来源国家
  "language": "en", // 默认值为 und，语言代码
  "authority_level": "B", // 必填，A、B、C、D、E 或 F，权威等级不等于立场
  "licence_policy": "authorized_media_library", // 必填，权利与使用策略
  "retention_days": "90", // 默认值为 null，保留期限
  "created_at": "2026-08-12T00:00:00Z", // 必填，创建时间
  "updated_at": "2026-08-12T00:00:00Z" // 必填，更新时间
}
```

### 5.3 Document 数据契约

```json
{
  "version": "1.0", // 必填，契约版本
  "document_id": "doc_2026_08_10_000123", // 必填，文档唯一标识
  "source_id": "source_babylist", // 必填，来源引用
  "canonical_url": "https://example.com/article", // 必填，规范链接
  "published_at": "2026-08-10T15:00:00Z", // 必填，发布时间
  "fetched_at": "2026-08-10T16:00:00Z", // 必填，采集时间
  "title": "文章标题", // 默认值为空字符串，标题
  "author_text": "署名作者", // 默认值为空字符串，作者
  "text_hash": "sha256_normalized_text", // 必填，用于去重和删除定位
  "rights_label": "full_text_allowed", // 必填，full_text_allowed、metadata_only 或 excerpt_only
  "is_syndicated": "false", // 必填，是否转载
  "canonical_document_id": "", // 默认值为空字符串，首发文档引用
  "deletion_status": "active", // 必填，active、deleted、provider_unavailable 或 pending_delete
  "raw_object_ref": "object://raw/2026/08/10/babylist/000123.json", // 必填，原始载荷引用
  "created_at": "2026-08-10T16:01:00Z", // 必填，入库时间
  "updated_at": "2026-08-10T16:01:00Z" // 必填，更新时间
}
```

### 5.4 Claim 与 Evidence 数据契约

```json
{
  "version": "1.0", // 必填，契约版本
  "claim_id": "claim_2026_08_10_005", // 必填，主张唯一标识
  "claim_text": "某型号在特定评测维度表现优于竞品", // 必填，可证伪的主张
  "claimant_text": "来源媒体或品牌", // 必填，主张者
  "subject": "Momcozy V1 Pro", // 必填，主张主体
  "predicate": "rating_dimension", // 必填，关系谓词
  "time_scope": "2026-08-03/2026-08-09", // 必填，事实窗口
  "verification_status": "credible_single_source", // 必填，证据状态枚举
  "evidence_ids_text": "evidence_0001, evidence_0002", // 必填，支持证据
  "counterevidence_ids_text": "evidence_0003", // 默认值为空字符串，反证
  "confidence": "0.78", // 必填，置信度
  "markets_text": "US", // 必填，市场
  "entities_text": "Momcozy, V1 Pro", // 必填，实体
  "model_version": "claim_pipeline_v2", // 必填，模型版本
  "review_status": "pending_review", // 必填，pending_review、verified、rejected 或 expired
  "created_at": "2026-08-10T18:00:00Z", // 必填，创建时间
  "valid_until": "2026-08-17T18:00:00Z" // 默认值为空字符串，有效期
}
```

### 5.5 Risk Signal 与 Opportunity 数据契约

```json
{
  "version": "1.0", // 必填，契约版本
  "risk_signal_id": "risk_2026_08_10_011", // 必填，风险信号唯一标识
  "risk_type": "product_safety", // 必填，product_safety、regulatory、privacy、authenticity、quality、legal 或 cultural
  "severity": "68", // 必填，严重度 0-100
  "velocity": "52", // 必填，扩散速度 0-100
  "source_authority": "80", // 必填，来源权威度 0-100
  "potential_reach": "60", // 必填，潜在影响范围 0-100
  "corroboration": "40", // 必填，多源印证 0-100
  "brand_proximity": "85", // 必填，品牌接近度 0-100
  "persistence": "30", // 必填，持续性 0-100
  "risk_score": "0.0", // 必填，加权分，由规则计算，不与置信度合并
  "confidence": "0.46", // 必填，置信度，与分数分离
  "severity_level": "Sev2", // 必填，Sev0、Sev1、Sev2、Sev3 或 Sev4
  "owner_role": "product_safety_lead", // 必填，负责角色
  "status": "pending_verification", // 必填，pending_verification、confirmed、escalated、active 或 closed
  "fact_pack_ref": "factpack_2026_08_10_011", // 默认值为空字符串，事实包引用
  "created_at": "2026-08-10T19:00:00Z", // 必填，创建时间
  "updated_at": "2026-08-10T19:00:00Z" // 必填，更新时间
}
```

### 5.6 PR Action 数据契约

```json
{
  "version": "1.0", // 必填，契约版本
  "action_id": "action_2026_08_10_021", // 必填，Action 唯一标识
  "action_type": "media_pitch", // 必填，media_pitch、product_seeding、expert_engagement、topic_entry 或 risk_response
  "title": "向 Consumer Reports 补充 V1 Pro 实测维度", // 必填，动作标题
  "why_now": "该媒体已入测四款 Momcozy 产品，但缺少特定型号维度证据。", // 必填，行动时机
  "target_outlet_text": "Consumer Reports", // 必填，目标媒体
  "target_journalist_text": "", // 默认值为空字符串，目标记者
  "content_angle": "外置动力免手持形态的实测维度与适配资料", // 必填，内容角度
  "required_assets_text": "标准化性能方法、法兰资料、可自由评价样机", // 默认值为空字符串，所需资产
  "owner_role": "media_relations_lead", // 必填，负责角色
  "due_at": "2026-08-18T17:00:00Z", // 默认值为空字符串，截止时间
  "success_metric": "媒体回应率、送测到评测转化、榜单位次变化", // 必填，验收指标
  "risk_text": "不得要求预审结论或限定正面评价。", // 必填，风险与禁用表述
  "source_insight_ids_text": "insight_2026_08_10_media_007", // 必填，来源洞察
  "evidence_set_id": "evidence_set_2026_08_10_007", // 必填，证据集
  "approval_status": "pending", // 必填，pending、approved、rejected、blocked 或 expired
  "execution_status": "not_started", // 必填，not_started、in_progress、done 或 cancelled
  "reviewer_note": "", // 默认值为空字符串，人工审核记录
  "result_note": "", // 默认值为空字符串，执行复盘记录
  "created_at": "2026-08-10T20:00:00Z", // 必填，创建时间
  "updated_at": "2026-08-10T20:00:00Z" // 必填，更新时间
}
```

### 5.7 关系型数仓分层

#### 控制层

| 表 | 粒度 | 关键字段 |
|---|---|---|
| dim_brand_alias | 一个品牌或产品别名 | entity_id、standard_name、alias、source_url、valid_from、valid_until |
| dim_competitor | 一个竞品实体 | competitor_id、canonical_name、track、region、ownership |
| dim_outlet_journalist | 一个媒体或记者实体 | outlet_id、journalist_id、beats、region、retention_until |
| source_registry | 一个数据源能力版本 | provider、source_type、fields_text、permission_status、last_tested_at |

#### 原始层 ODS

| 表 | 粒度 | 关键字段 |
|---|---|---|
| ods_provider_payload | 一次 provider 返回载荷 | job_id、provider、request_hash、raw_object_ref、received_at |
| ods_collection_job | 一次采集任务 | job_id、source_id、cursor、status、request_count、error_code |

#### 明细层 DWD

| 表 | 粒度 | 关键字段 |
|---|---|---|
| dwd_document | 一篇文档 | document_id、canonical_url、published_at、fetched_at、rights_label、deletion_status |
| dwd_mention | 一个文档内的一次实体提及 | mention_id、document_id、entity_id、span、relevance、market |
| dwd_claim | 一条主张 | claim_id、claim_text、subject、predicate、verification_status、confidence |
| dwd_evidence | 一个可引用证据 | evidence_id、claim_id、document_id、quote_span、supports_or_refutes |
| dwd_risk_signal | 一条风险信号 | risk_signal_id、risk_type、severity、confidence、status、owner_role |

#### 汇总层 DWS

| 表 | 粒度 | 关键字段 |
|---|---|---|
| dws_entity_daily | 日期、实体、市场 | stat_date、entity_id、market、document_count、authority_weighted_count |
| dws_topic_daily | 日期、话题 | stat_date、topic_key、mention_count、outlet_count、stance_summary |
| dws_competitor_daily | 日期、竞品、赛道 | stat_date、competitor_id、track、position_delta、outlier_count |
| dws_outlet_period | 媒体与周期 | outlet_id、period_start、period_end、topic_mix、stance_mix |

#### 应用层 ADS

| 表 | 粒度 | 关键字段 |
|---|---|---|
| ads_insight | 一个业务洞察 | insight_id、insight_type、fact_text、inference_text、evidence_set_id |
| ads_opportunity | 一个机会 | opportunity_id、score、target_outlet、angle、asset_gap、risk_penalty |
| ads_action | 一个 Action | action_id、action_type、approval_status、execution_status、source_insight_ids |
| ads_report | 一份报告 | report_id、report_type、period、coverage_summary、render_ref |
| ads_feedback | 一条人工反馈 | feedback_id、object_type、object_id、label、reason、reviewer_role |

### 5.8 核心表 SQL 草案

```sql
CREATE TABLE dwd_document (
    document_id VARCHAR PRIMARY KEY,
    source_id VARCHAR NOT NULL,
    canonical_url VARCHAR,
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    title VARCHAR,
    author_text VARCHAR,
    text_hash VARCHAR NOT NULL,
    rights_label VARCHAR NOT NULL,
    is_syndicated BOOLEAN NOT NULL,
    canonical_document_id VARCHAR,
    deletion_status VARCHAR NOT NULL,
    raw_object_ref VARCHAR NOT NULL,
    UNIQUE(text_hash, source_id)
);

CREATE TABLE dwd_claim (
    claim_id VARCHAR PRIMARY KEY,
    claim_text VARCHAR NOT NULL,
    claimant_text VARCHAR NOT NULL,
    subject VARCHAR NOT NULL,
    predicate VARCHAR NOT NULL,
    time_scope VARCHAR,
    verification_status VARCHAR NOT NULL,
    confidence REAL NOT NULL,
    markets_text VARCHAR NOT NULL,
    model_version VARCHAR NOT NULL,
    review_status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE dwd_evidence (
    evidence_id VARCHAR PRIMARY KEY,
    claim_id VARCHAR NOT NULL,
    document_id VARCHAR NOT NULL,
    quote_span VARCHAR,
    supports_or_refutes VARCHAR NOT NULL,
    evidence_grade VARCHAR NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    valid_until TIMESTAMP,
    redaction_status VARCHAR NOT NULL,
    FOREIGN KEY (claim_id) REFERENCES dwd_claim(claim_id),
    FOREIGN KEY (document_id) REFERENCES dwd_document(document_id)
);

CREATE TABLE ads_action (
    action_id VARCHAR PRIMARY KEY,
    action_type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    content_angle VARCHAR NOT NULL,
    target_outlet_text VARCHAR NOT NULL,
    owner_role VARCHAR NOT NULL,
    due_at TIMESTAMP,
    evidence_set_id VARCHAR NOT NULL,
    approval_status VARCHAR NOT NULL,
    execution_status VARCHAR NOT NULL,
    result_note VARCHAR,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### 5.9 数据质量规则

| 规则 | 检查 | 失败处理 |
|---|---|---|
| 文档去重 | text_hash 与 source_id 唯一 | 报错并进入转载聚类 |
| 发布时间存在 | published_at 不为空且可解析 | 记录 invalid_timestamp，不进入趋势计算 |
| 采集时间存在 | fetched_at 不为空 | 采集任务失败 |
| 转载归属 | is_syndicated 有 canonical_document_id | 声量统计按首发聚类 |
| 来源可追溯 | source_url、document_id 或授权导入引用至少一个存在 | 禁止进入已验证 Insight |
| 主张有证据 | 高影响 claim 至少一条 evidence | 降级为未验证主张 |
| 证据等级 | evidence_grade 来自枚举 | 缺失进入待标注 |
| 删除同步 | document 标记删除时派生对象可定位 | 触发删除或重新生成摘要 |
| 模型版本 | claim、insight、risk 带版本 | 版本缺失不允许发布报告 |
| 增量主键 | 汇总模型有 unique key | dbt 或等价测试失败时阻止发布 |

### 5.10 数据保留与删除

| 数据 | 推荐默认 | 备注 |
|---|---|---|
| 原始 provider payload | 按合同和平台规则确定，初始 90 天 | 只为重放和审计服务 |
| 标准化文档元数据与摘录 | 180 天滚动 | 保存最小必要信息和来源链接 |
| 汇总指标与话题趋势 | 24 个月 | 删除原文后仍需检查派生统计 |
| Action 与复盘 | 36 个月 | 作为内部决策记录 |
| 记者画像与关系 | 按最小必要和合同，初始 12 个月 | 不保存敏感私人信息 |
| 凭证与 token | 由 Secret Manager 管理 | 不写入数据库和报告正文 |

## 第六章：技术架构

### 6.1 分层架构

```text
+--------------------------------------------------------------------------------+
| 体验层：Next.js / 现有 Dashboard / Markdown 报告 / 飞书或 Slack 通知           |
| 负责筛选、证据展开、Action 审批、导出和反馈                                  |
+--------------------------------------------------------------------------------+
| 应用层：FastAPI / Query API / Report API / Action API / Admin API              |
| 负责权限、查询编排、状态机、报告版本和审计                                     |
+--------------------------------------------------------------------------------+
| Agent 层：LangGraph workflow                                                  |
| 负责规划、检索、聚合、分析、证据检查、生成草稿、人工 interrupt 和恢复          |
+--------------------------------------------------------------------------------+
| 分析层：规则指标 + embeddings + topic clustering + LLM structured output      |
| 负责实体、话题、主张、立场、风险、机会、媒体匹配和 Action 候选                 |
+--------------------------------------------------------------------------------+
| 处理层：connector workers + queue + retry + DLQ + schema validation           |
| 负责节流、游标、幂等、原始归档、标准化和失败重试                               |
+--------------------------------------------------------------------------------+
| 数据层：对象存储 Parquet + DuckDB/warehouse + PostgreSQL control plane         |
| 负责原始、明细、汇总、应用、配置、审计和删除定位                               |
+--------------------------------------------------------------------------------+
| 外部层：授权媒体库 / 监管源 / 开放发现 / 社交信号 / 受限社区 / 内部数据         |
| 通过数据源能力矩阵暴露权限、字段、延迟、成本和覆盖缺口                         |
+--------------------------------------------------------------------------------+
```

### 6.2 数据源组合与合法获取

| 层级 | 来源 | 主要用途 | 获取策略与边界 |
|---|---|---|---|
| A 权威事实 | FDA、FTC、Health Canada、CPSC、政府、法院、公司政策与备案 | 监管、安全、隐私、企业事件 | 官方 API、RSS、网页变更；原文快照与版本差异 |
| B 核心媒体 | Babylist、The Bump、Forbes Vetted、Consumer Reports、Marie Claire | 编辑方向、竞品评价、传播机会 | 优先采购有版权和全文权利的媒体库；公开页仅保存许可范围内元数据与片段 |
| C 开放发现 | GDELT、Media Cloud、Google News 线索 | 全球多语种发现、趋势对照 | 用于发现并回链原站，不替代授权全文 |
| D 社交与搜索 | X、YouTube、Google Trends | 早期信号、创作者内容、需求变化 | X 近 7 天，完整历史需相应权限；YouTube 按配额；Trends 需获批 |
| E 受限社区 | Reddit、TikTok、Meta 社区 | 体验、争议与文化语境 | Reddit 商业用途需单独协议；TikTok Research Tools 面向符合条件的非商业研究者 |
| F 内部数据 | PR 台账、CRM、客服、退货、质保、产品安全、销售与搜索 | 验证真实影响和闭环 | 最小权限、目的限制、聚合去标识；不把个人健康数据复制进 PR 向量库 |

### 6.3 推荐部署路线

#### P0 试点

- 采集执行：Python connector worker，沿用现有 tools 目录风格。
- 原始数据：本地或云对象存储中的按日期分区 JSON/Parquet。
- 分析存储：DuckDB 与现有 data/warehouse 方向兼容。
- API：沿用 FastAPI，提供配置、报告、证据和 Action 接口。
- Agent：LangGraph，使用持久化 checkpointer；开发环境 SQLite，生产使用 PostgreSQL saver。
- 输出：Markdown、JSON、CSV。

#### 生产增强

- 控制面：PostgreSQL。
- 原始与分析明细：S3/GCS/Azure Blob + Parquet。
- 变换：dbt 或项目现有等价 SQL/Python pipeline，使用增量模型、unique key 和数据测试。
- 检索：OpenSearch，支持关键词、语义检索、过滤、聚合和证据 drill-down。
- 任务：SQS/Pub/Sub/Redis Streams 任选其一，必须有 DLQ、游标、节流和重试。
- 可观测性：结构化日志、采集成功率、字段缺失率、队列积压、LLM 成本、报告失败率。

### 6.4 Agent 工作流

```text
START
  --> parse_request
  --> build_query_plan
  --> load_coverage
  --> collect_and_deduplicate
  --> classify_entity_and_taxonomy
  --> extract_claim_and_evidence
  --> detect_trend_and_anomaly
  --> score_risk_and_opportunity
  --> evidence_gate
  --> human_review_if_needed
  --> render_report_or_action
  --> persist_feedback
  --> END
```

关键实现要求：

1. 采集、去重、实体分类、证据抽取、趋势异常、评分等节点使用工具返回结构化数据，不让 LLM 自由决定结果。
2. 合成节点必须输出结构化字段，不接收无法定位来源的自由文本。
3. evidence_gate 在样本量、覆盖、时间窗、证据等级、模型置信度或安全规则不满足时降级结论。
4. 风险、机会和 Action 审批使用 LangGraph interrupt/resume 或等价状态机。官方文档显示 checkpointer 和 interrupt 可支撑恢复、人工介入和故障容错。
5. 每次运行保存 run_id、query_plan、tool_calls、model_version、prompt_version、evidence_ids 和最终状态，支持回放和审计。

### 6.5 分析框架

#### 风险评分

风险总分是排序工具，不是事实结论：

```text
Risk = 0.25 x Severity + 0.20 x Velocity + 0.15 x Source Authority
     + 0.15 x Potential Reach + 0.10 x Corroboration
     + 0.10 x Brand Proximity + 0.05 x Persistence
```

各项 0-100，另设独立 Confidence。低置信高严重信号仍需快速核验，不能因证据不足沉底。

| 等级 | 分数或典型条件 | 系统动作 | 人工 SLA | 责任人 |
|---|---|---|---|---|
| Sev0 观察 | 低于 30、低权威单点 | 周度汇总 | 周报前 | Analyst |
| Sev1 关注 | 30-49、重复抱怨或核心媒体负评 | 工作队列 | 1 个工作日 | Regional PR |
| Sev2 升级 | 50-69、安全/隐私/真实性信号或明显增速 | 证据卡 + 主管通知 | 4 小时 | PR Lead + SME |
| Sev3 严重 | 70-84、权威媒体/监管/多源扩散 | War Room、暂停相关外发建议 | 60 分钟 | PR Director + Legal |
| Sev4 危急 | 85 及以上、生命安全/召回/执法/重大泄露 | 即时电话/多渠道升级 | 15 分钟确认、60 分钟首次事实简报 | Executive Crisis Team |

#### 机会评分

```text
Opportunity = 0.20 x Strategic Fit + 0.15 x Momentum + 0.15 x Media Receptivity
            + 0.20 x Evidence Readiness + 0.10 x Differentiation
            + 0.10 x Timing + 0.10 x Execution Feasibility - Risk Penalty
```

#### 证据状态

| 状态 | 含义 |
|---|---|
| verified_primary | 原始一手来源验证 |
| verified_multiple_independent | 多个独立来源印证 |
| credible_single_source | 单一可信来源 |
| unverified_allegation | 未经证实的指控 |
| brand_claim | 品牌自述，非独立验证 |
| opinion | 观点而非事实 |
| contradicted | 存在反证 |
| resolved | 已解决 |

#### 效果衡量

按 AMEC 区分 outputs、out-takes、outcomes、impact，不把曝光和内容数量等同于理解、信任、偏好或业务结果。业务结果用风险提前量、洞察转行动率、行动闭环时间和证据可追溯率衡量。

### 6.6 技术依赖表

| 库名或服务 | 用途 | 为何优于替代方案 | 大致包体积 |
|---|---|---|---|
| Python | 连接器、数据处理、Agent 服务 | 现有项目已使用，适合数据和 API 编排 | 未知 |
| DuckDB | P0 本地分析与 Parquet 查询 | 适合低运维试点和现有 VOC 项目 | 未知 |
| Parquet | 原始与明细分区存储 | 列式存储，便于重放、压缩和批量分析 | 不适用 |
| FastAPI | 配置、查询、报告和 Action API | 现有项目已有 FastAPI 方向，类型和异步生态成熟 | 未知 |
| LangGraph | 有状态 Agent、恢复和人工审批 | 图结构适合多步骤分析和 interrupt/resume | 未知 |
| PostgreSQL | 控制面、权限、配置、审计和生产 checkpointer | 事务、约束、JSON 和生态成熟 | 未知 |
| OpenSearch | 证据全文检索、语义检索、过滤和聚合 | 同时支持文本检索、向量检索和聚合 | 未知 |
| dbt | 汇总层增量变换和数据测试 | unique key、增量模型和质量断言可审计 | 未知 |
| sentence-transformers 或等价 embedding 服务 | 语义聚类和相似证据 | 比纯关键词更能处理表达差异 | 未知 |
| Hugging Face Transformers 或云 NLP 服务 | 语言、实体、立场和分类 | 可替换模型，便于离线评估和成本分层 | 未知 |
| Secret Manager | 数据源 token 和 provider key | 避免凭证进入代码和数据库 | 不适用 |

### 6.7 最大架构风险

最大风险不是 LLM 选型，而是数据权利与证据可信度。工程可以写出采集器，但不能通过代码创造版权授权或可靠事实。缓解顺序：

1. 为每个数据源建立 capability manifest，并在真实账号上运行连接测试。
2. 以授权媒体库、监管源、开放发现和自有数据建立可交付闭环。
3. 受限社区（Reddit、TikTok）只在商业授权明确可用时启用。
4. 把数据源失败作为产品状态而非系统崩溃，报告中显示覆盖缺口。
5. 预留替换连接器，不让业务层依赖某个供应商的私有结构。

### 6.8 可替换技术原则

推荐默认使用现有 Python、FastAPI、DuckDB/Parquet 和 PostgreSQL 控制面；如果项目已有 BigQuery、Snowflake、ClickHouse、Airflow、Dagster 或其他队列，可以替换。LangGraph 可替换为等价的有状态工作流引擎。OpenSearch 可替换为已有搜索引擎。

不可替换的是：Document 与 Claim 字段语义、数据源 capability、幂等键、cursor、raw reference、evidence_set、coverage_report、风险分级与 SLA、Action 审批状态机、删除定位和模型版本记录。

## 第七章：交互细节

### 7.1 键盘快捷键

| 操作 | 快捷键 | 备注 |
|---|---|---|
| 打开全局搜索 | `/` | 聚焦报道、话题、媒体、记者和 Action 搜索框 |
| 返回首页 | `g` 后 `d` | 两键组合，避免覆盖输入 |
| 打开媒体雷达 | `g` 后 `m` | Media Radar |
| 打开风险 | `g` 后 `r` | Risk War Room |
| 打开 Action | `g` 后 `a` | Action Center |
| 打开当前证据 | `o` | 在选中洞察卡片时生效 |
| 标记待复核 | `r` | 不改变原始数据 |
| 导出当前视图 | `e` | 按当前筛选生成导出任务 |
| 关闭抽屉 | `Esc` | 返回列表 |

### 7.2 右键菜单与上下文菜单

洞察卡片菜单：

```text
洞察卡片右键
+-- 打开证据链
+-- 查看原文
+-- 对比上一周期
+-- 标记为重要
+-- 修正标签
+-- 生成 Action 草稿
+-- 驳回并说明原因
```

媒体/记者卡片菜单：

```text
媒体/记者右键
+-- 查看近 180 天选题
+-- 查看竞品观点
+-- 设置冷却期
+-- 记录关系状态
+-- 生成 pitch 草稿
+-- 查看接触历史
```

风险卡片菜单：

```text
风险右键
+-- 生成事实包
+-- 升级
+-- 记录口径
+-- 结案
+-- 标记误报
```

### 7.3 空状态

| 页面 | 用户看到什么 | CTA |
|---|---|---|
| Overview 无运行 | 还没有有效采集运行，先连接一个允许使用的数据源 | 创建监测范围 |
| 媒体雷达无结果 | 当前范围内没有达到最低样本的报道，可能是关键词过窄或数据为空 | 调整关键词或时间范围 |
| 核心媒体无画像 | 尚未添加并确认核心媒体和记者署名 | 导入媒体清单 |
| 风险无信号 | 当前没有达到分级门槛的风险信号 | 查看低置信度观察 |
| 机会无候选 | 当前没有通过证据门槛的机会 | 查看资产缺口 |
| Action 无候选 | 当前没有通过证据门槛的行动建议 | 查看历史洞察 |
| 周报生成中 | 显示运行阶段、已处理样本、失败来源 | 查看运行详情 |

### 7.4 错误状态

| 触发条件 | 用户可见提示信息 | 恢复操作 |
|---|---|---|
| 数据源凭证过期 | 连接已失效，历史数据保留；请重新授权后恢复采集 | 重新授权并测试连接 |
| 触发限速 | 数据源暂时限制请求，系统已暂停该连接器，不会继续增加请求 | 等待 reset 时间或调整频率 |
| schema 变化 | 返回字段发生变化，当前任务已进入质量保护；部分报告暂缓生成 | 查看字段差异、更新 adapter、回放样本 |
| LLM 失败 | 分析模型未完成，已保留结构化指标；可稍后重跑摘要 | 切换已批准模型或重试分析阶段 |
| 原文删除 | 来源内容已不可访问，保留 document_id 与删除记录 | 查看删除审计或移除证据 |

### 7.5 加载状态

| 操作 | 指示器 | 低于该延迟不显示 | 超过劣化阈值 |
|---|---|---:|---:|
| 列表筛选 | 轻量 skeleton | 200ms | 2s 仍无结果时显示加载详情 |
| 打开证据抽屉 | 局部 spinner | 150ms | 1.5s 显示来源查询状态 |
| 生成 Insight | 阶段进度条 | 不隐藏 | 30s 无进度显示重试和失败阶段 |
| 生成周报 | 后台任务卡 | 不隐藏 | 10min 未完成触发任务告警 |
| 导出 CSV/JSON | 后台任务卡 | 不隐藏 | 2min 未完成显示导出日志 |
| 连接测试 | 按钮内 spinner | 不隐藏 | 15s 超时，标记 connection_timeout |

## 第八章：导出与输出系统

### 8.1 支持的输出格式

| 格式 | 使用场景 | 质量选项 | 备注 |
|---|---|---|---|
| Markdown | 周报、评审、内部分享 | 带来源、覆盖说明、生成版本 | P1 周报格式；P0 仅用于 Evidence Card 和风险 Action brief |
| JSON | API、二次分析、自动化消费 | schema version、evidence IDs、coverage | 机器可读，保留 null 语义 |
| CSV | 报道、媒体、竞品、风险、Action 列表 | 按当前筛选导出 | 不默认导出完整原文和个人信息 |
| HTML | 浏览器预览与邮件附件 | 内嵌图表和来源 | P1，可由 Markdown 渲染 |
| PDF | 管理层归档 | 版式固定、带研究限制 | P2，不作为首期依赖 |
| Action brief | PR 与媒体团队执行 | 一条 Action 一个 brief | 可复制到任务系统 |

### 8.2 输出文件结构

```text
reports/
+-- pr_intelligence/
|   +-- 2026-08-12_daily.md
|   +-- 2026-W33_weekly.md
|   +-- 2026-W33_weekly.json
|   +-- evidence_manifest.csv
|   +-- coverage_report.csv
|   +-- actions/
|       +-- action_2026_08_10_021.md
|       +-- action_2026_08_10_021.json
|
+-- run_logs/
    +-- run_20260810_200000.json
    +-- run_20260810_200000_errors.json
    +-- run_20260810_200000_metrics.json
```

### 8.3 每周 PR Intelligence Report 结构

```text
标题与周期
执行摘要
数据覆盖与限制
一、媒体与行业发生了什么
二、竞品媒体动态与占位
三、核心媒体洞察
四、机会与风险
五、PR Actions
风险与待人工确认事项
来源清单
模型与规则版本
```

报告写作规则：

1. 先写事实，再写判断，最后写建议。
2. 任何数字后面都写统计窗口、样本量、来源范围和采集时间。
3. 如果数据覆盖不完整，标题使用已覆盖范围，不写全平台或全媒体。
4. 每条重大结论显示 evidence_set_id 或可点击的来源链接。
5. 不引用真实用户姓名、联系方式或非必要个人信息。
6. 涉及监管、产品安全、隐私、医疗和心理健康的结论必须专业复核。

### 8.4 批量处理流程

```text
采集任务集合
  |
  +--> 媒体库 connector --------+
  +--> 监管源 connector --------+
  +--> 开放发现 connector -------+--> 并行写入 raw archive
  +--> 社交信号 connector -------+
  +--> 内部数据 connector -------+
                                  |
                                  v
                         标准化与去重、转载聚类
                                  |
                     +------------+-------------+
                     |                          |
             可并行：语言、实体、话题、      必须顺序：主张与证据抽取
             立场、规则分类                    --> 风险与机会评分
                     |                          |
                     +------------+-------------+
                                  v
                              evidence gate
                                  |
                     +------------+-------------+
                     |                          |
                  生成周报                  生成 Action 候选
                     |                          |
                     +------------+-------------+
                                  v
                         人工审核与持久化
```

## 第九章：开发优先级

按对用户行为的影响排序，而不是按工程难度排序。

| 等级 | 范围 | 交付标准 |
|---|---|---|
| P0 | 美国英语 pumping/feeding 范围配置；获准媒体源、官方监管源和允许使用的内部一方数据；Document/Claim/Evidence；四类风险识别；`Sev0–Sev4` 人工确认；单一事件负责人；风险 Action 与结果回填 | 一条真实获准风险信号可完整经过「证据—风险候选—人工确认—分级—指派—Action—结果回填」；覆盖缺口可见，AI 不自动对外响应 |
| P1 | 品牌健康度、竞品矩阵、核心媒体洞察、机会识别、媒体匹配、冷却期、周报和 Action Board | 团队能在 P4 之外持续使用品牌、竞品、媒体和机会模块，并对数据质量与行动状态进行管理 |
| P2 | 议题设定、跨来源主张图谱、语义证据检索、消息通知、模型离线评估和跨部门效果复盘 | PR 机会、风险和议题能在统一工作流内发现、审核、执行和复盘 |
| P3 | 战略决策支持、反馈评估集、预算与资源约束优化、跨市场多语言和受控 API 输出 | 系统能基于历史行动结果支持跨市场和资源配置判断 |

## 第十章：性能指标

下表是按完整产品规划保留的候选指标。P0 只启用来源可追溯、风险识别、确认分级时长、覆盖与 Action 回填相关指标；其余指标在对应模块进入 P1–P3 后启用。所有无内部 baseline 的数值均须由业务负责人签字后生效。

| 指标名称 | 目标值 | 测量方法 | 劣化阈值 |
|---|---:|---|---:|
| 采集任务成功率 | 最近 24 小时成功任务占比不低于 95% | collection_job 按 source、市场、时间窗口统计 | 低于 85% 连续 2 个周期 |
| 品牌/竞品相关性 | 英文样本 F1 不低于 0.90 | 分层 gold set 评估实体和相关性分类 | 低于 0.85 |
| 关键风险召回率 | Sev3/Sev4 召回率不低于 0.95 | 历史风险 case 回放 | 低于 0.90，且漏报做 root-cause review |
| 转载聚类准确率 | 不低于 0.90 | 人工标注转载样本回放 | 低于 0.80 |
| 高影响结论可追溯率 | 100% 有 evidence_set_id 和原文引用 | ADS 与 DWD 关联检查 | 低于 100% |
| 周报事实性抽检 | 不低于 95%，无来源的监管/安全/人物归因为 0 | 每周人工抽检样本 | 低于 90% |
| 风险首次信号到人工确认时间 | Sev2 不超过 4 小时，Sev3 不超过 60 分钟 | incident 时间戳差 | Sev3 超过 2 小时 |
| 单周报告人工编辑时间 | 相对基线下降不低于 50% | 前后工时对比 | 未下降且核验质量受损 |
| 证据搜索响应 | P95 不超过 2 秒，返回首屏 20 条 | API 端到端日志 | P95 超过 5 秒 |
| 周报生成时间 | 5 万条已清洗文档的周聚合不超过 20 分钟 | workflow started_at 到 completed_at | 超过 40 分钟 |
| 报告导出 | 1 万条明细 CSV 不超过 2 分钟 | export job 日志 | 超过 5 分钟 |
| 队列积压 | 正常窗口未完成消息少于 1,000 条 | queue depth 每 5 分钟采集 | 超过 5,000 条持续 15 分钟 |
| LLM 单条 Insight 成本 | 通过批处理和缓存控制在预算阈值内，初始阈值由财务确认 | token usage 与成本表按报告统计 | 超过预算 150% |
| Action 人工驳回率 | 首月不高于 50%，持续下降 | review_status 统计并按原因分组 | 连续两周高于 70% |
| 数据删除响应 | 收到合法删除请求后 24 小时内完成标记和派生对象定位 | deletion audit log | 超过 48 小时 |

## 第十一章：开发者交接说明

### 11.1 实现顺序建议

你必须先通过业务共识门，再安排实现。推荐顺序：

1. 由 PR、法务、产品安全、隐私和数据负责人确认 P0 的四类风险、SKU、来源、责任人、分级规则、SLA、baseline 和停止条件。
2. 用历史事件和正常样本形成固定评审集，逐条标注事实、证据、风险类别、严重度和正确升级路径。
3. 定义最小 Source & Rights、Document、Claim、Evidence、Coverage、Incident 和 Risk Action 契约，确保缺失、零值、失败和范围外信号可区分。
4. 只接一条获准媒体或监管链路与一条允许使用的内部链路，验证风险候选、反证和 Evidence Card；不先扩展到未经授权的平台。
5. 实现人工确认、`Sev0–Sev4` 分级、单一事件负责人、领域共同确认、升级和结果回填，不实现自动对外响应。
6. 用固定样本和真实试点执行 P0 验收；只有达到已签字的 Go/No-Go 条件，才进入品牌健康、竞品、核心媒体、机会和周报模块。
7. P1–P3 模块仍沿用本文件的数据、证据、审批和错误边界，不另建一套相互冲突的流程。

### 11.2 最可能导致返工的三个决策

#### 决策一：媒体数据源的权利与覆盖

- 决策是什么：采用哪一个或哪几个授权媒体库，覆盖哪些市场、语言、历史深度和出口权利。
- 安全默认选择：P0 只承诺已授权媒体库、监管源、开放发现和内部数据；受限社区通过 capability manifest 开关。
- 需要改变方向的信号：合同或授权确认了可用字段、市场、历史范围、刷新频率、保存期限和费用。

#### 决策二：数据仓库是沿用 DuckDB 还是直接上云数仓

- 决策是什么：试点和生产是否使用同一存储方案。
- 安全默认选择：P0 用 DuckDB/Parquet 保持与现有 VOC 项目兼容，控制面和审计预留 PostgreSQL；生产数据量或多人并发达到指标后迁移汇总层。
- 需要改变方向的信号：单日文档量、并发查询、保留期限或权限要求超过本地方案的验收阈值。

#### 决策三：AI 生成内容的自动化边界

- 决策是什么：Agent 能否直接联系记者、发送 pitch、发布声明、纠错或召回信息。
- 安全默认选择：Agent 只生成内部 Insight、Opportunity、Risk 和 Action，所有外部行为必须由人和现有业务系统执行。
- 需要改变方向的信号：品牌、法务、数据授权和审计流程明确允许某一类自动动作，并且通过沙盒、限额和回滚验证。

### 11.3 哪里要严格，哪里可以灵活

| 章节 | 标记 | 你必须如何处理 |
|---|---|---|
| 产品概述 | 约束 | 保持从媒体信号到 PR Action 的闭环，不做只读剪报工具 |
| 数据源能力 | 约束 | 不绕过版权和权限；缺失字段使用 null 和 coverage gap |
| 核心模块 | 约束 | 媒体、竞品、核心媒体、风险、机会和 Action 需要证据、时间窗、状态和人工反馈 |
| 数据模型 | 约束 | document_id、claim、evidence、版本、时间和删除定位不能删 |
| Agent 工作流 | 约束 | 工具取数，模型解释；风险和外部动作必须 human-in-the-loop |
| 风险与机会评分 | 约束 | 分数与置信度分离，不合并成一个数 |
| 存储技术 | 建议 | 可以沿用现有 DuckDB，也可迁移 PostgreSQL、BigQuery、Snowflake 或其他仓库 |
| 搜索技术 | 建议 | OpenSearch 是推荐默认，已有搜索引擎可替换 |
| 前端布局 | 发挥空间 | 可以根据现有 Next.js 看板调整组件、颜色、图表和响应式布局 |
| 报告版式 | 发挥空间 | 可以优化视觉层级，但不可隐藏来源、范围、样本和不确定性 |
| 模型供应商 | 建议 | 使用已经过内部批准的模型，模型版本和 Prompt 版本必须记录 |

### 11.4 已知的未知项

1. 此处未解决：Momcozy 当前拥有哪些媒体数据库、记者数据库和数据供应商订阅，以及对应的权利和出口限制。
2. 此处未解决：核心媒体清单、记者名单、竞品池和产品赛道由 PR 团队最终确认的范围。
3. 此处未解决：美国英语 P0 的具体渠道范围、业务时区、通知对象和审批链。
4. 此处未解决：内部一方数据（PR 台账、客服、退货、质保、产品安全）以何种权限和聚合粒度接入。
5. 此处未解决：Action 是否需要接入飞书、Slack、Jira、Asana 或现有内容日历。
6. 此处未解决：媒体数据供应商的收费、服务等级、历史回填范围和删除同步能力。
7. 此处未解决：风险分和机会分的权重是否需要按产品赛道、市场或风险类型分别配置。

在这些信息确认前，你应使用本 PRD 的安全默认，不要以假授权、假数据源或假媒体关系继续开发。

### 11.5 验收剧本

验收剧本 1：在本地开发环境运行离线 fixture，加载 20 条媒体报道、10 条监管记录和 5 条内部导入记录，系统应生成唯一的 Document、Mention、Claim 和 Evidence，并用 SQL 检查 text_hash 与 source_id 没有重复。

验收剧本 2：在已配置有效授权的环境运行媒体库监测任务，选择一个市场、赛道和品牌别名，任务应保存 raw payload、cursor、采集日志和标准化文档；断开网络后重启任务，应从上次 cursor 恢复或清晰记录失败原因。

验收剧本 3：打开一条竞品主张 Insight，依次查看事实、模型推断、证据等级、反证、样本量和覆盖范围；点击生成 Action，Action 应继承 insight_id 和 evidence_set_id，并默认处于待审核，不能直接变为已批准。

验收剧本 4：创建一条涉及对外 pitch 的 Action，系统应显示目标媒体、冷却期、利益冲突、资产缺口和负责人；未完成审批时不能生成已执行状态，也不能调用任何对外发信或发布接口。

验收剧本 5：模拟一个连接器连续返回 401、429、字段变化和零数据四种错误，系统应分别记录授权失效、限速暂停、schema 质量异常和空结果状态，并在报告中展示对应覆盖缺口。

验收剧本 6：用同一份 fixture 和同一模型版本重复生成周报，事实、数字、evidence_id 和 Action 来源应一致；更换模型版本后，系统应生成新的 run_id 和模型版本记录，不覆盖旧报告。

验收剧本 7：向系统注入一条高严重但低置信度的风险信号，系统应进入快速核验并显示置信度，而不是因证据不足沉底；核验后应能生成事实包并进入结案或升级流程。

### 11.6 研发自检命令

```bash
# 1. 文档结构检查
python3 /Users/lute/.agents/skills/qiaomu-ai-prd/scripts/lint_prd.py \
  /Users/lute/Project/voc-data-product/PRD/PR/PRD-Momcozy-PR-Intelligence-Agent-Canonical-v1.1.md

# 2. 搜索产品文档中的待确认项和未验证边界
rg -n "此处未解决|未验证|待授权|coverage|evidence|删除|Action|风险|机会" \
  /Users/lute/Project/voc-data-product/PRD/PR/PRD-Momcozy-PR-Intelligence-Agent-Canonical-v1.1.md

# 3. 若实现了 Python 连接器，运行项目已有测试与类型检查
python3 -m compileall tools app

# 4. 对 fixture 运行唯一键、来源、时间和缺失值检查
python3 tools/validate_voc_dataset.py
```

### 11.7 交付判断

当且仅当以下条件全部满足，才可以把产品标记为首期完成：

- PR、法务、产品安全、隐私和数据负责人已签字确认四类风险、SKU、来源、`Sev0–Sev4` 规则、SLA、owner、baseline 和停止条件。
- 至少一条真实获准媒体或监管链路，以及一条允许使用的内部数据链路，通过同一套 Document/Claim/Evidence/Coverage 规则。
- 一条真实 P4 信号能完成风险候选、证据与反证检查、人工确认、分级、单一事件负责人指派、领域共同确认、Risk Action 和结果回填。
- 数据源缺口、字段缺失、限速、删除、模型失败、范围外内容和真实零值都有可见且互不混淆的状态。
- P0 的风险确认与分级总时长按统一时间戳可计算，并达到已签字的 Go/No-Go 条件。
- 不存在自动联系记者、自动发布声明、自动纠错或自动召回通知。
- 运行 `lint_prd.py` 通过，P0 验收剧本有评审记录、日志、导出文件或截图证据。

### 11.8 研究交付说明

本次 PRD 的事实基线来自项目内已有 deep research（PR/momcozy_pr_intelligence_implementation_plan_2026-08-11.md 与 PR/momcozy-pr-intelligence-ai-agent-plan.pplx.md），以及本轮核验的 Momcozy 官方站点、YouTube Data API、TikTok for Developers、FTC 官方披露指南、AWS 官方社媒数据管道指导、LangGraph 官方文档和 dbt 官方文档。媒体榜单、诉讼进展、监管问询答复、竞品声量和品牌规模数据未经本轮重新测量，投产前必须按最新时点重新核验并建立基线。搜索工具 opencli 在当前工作环境不可用，因此没有把任何本地 OpenCLI 适配器或第三方爬虫能力写成已验证事实。

### 11.9 复盘后的下一步

下一步不是立刻开发六个数据源抓取器，而是由 PR、法务、数据、产品安全和研发共同完成一页「数据源与授权确认表」：每个数据源列出授权类型、可采字段、历史范围、刷新频率、保存期限、删除机制、供应商费用和责任人。确认表通过后，从授权媒体库和监管源的真实数据样本开始 P0 验收；未通过的数据源保持待授权状态，不影响已验证链路交付。
