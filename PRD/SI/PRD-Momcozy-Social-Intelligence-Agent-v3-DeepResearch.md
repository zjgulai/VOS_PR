---
name: momcozy-social-intelligence-agent-prd-v3
description: Momcozy 社媒智能监测 AI Agent 深度研究版 PRD。严格遵循 PR Intelligence 的问题导向与证据链架构，覆盖用户洞察(S1)、竞品监控(S2)、社媒趋势(S3)、Creator分析(S4) 及 Action Engine。
---

# Momcozy Social Intelligence Agent PRD (Deep Research 版)

> 版本：v3.0 
> 文档状态：待业务评审
> 文档日期：2026-08-13
> 目标团队：Momcozy 社媒团队、内容团队、Creator 合作团队、品牌与产品团队、数据与技术团队
> 核心逻辑：Social Monitoring → Insights → Trend & Content Intelligence → Social Media Actions
> 研究口径：以问题导向为核心，英文优先检索；平台能力以官方文档与真实合规实践为准；结论需带证据链。

## AI 速读卡

- **产品一句话**：把跨平台公开社媒信号（Reddit/Meta/TikTok/YouTube）转化为可追溯的母婴用户洞察、竞品判断、趋势机会和待审批行动。
- **核心闭环**：配置监测范围 → 采集与标准化 → AI 分析与证据抽取 → 交叉比对生成 Insight → Action 审批 → 执行结果复盘。
- **四大业务支柱**：S1 用户讨论与痛点洞察、S2 竞品社媒营销监控、S3 社媒热点与内容趋势、S4 重点 Creator 动态分析。
- **目标平台**：Reddit（重点）、Facebook Groups（重点）、Instagram、Facebook Pages、YouTube、TikTok。
- **硬约束**：不绕过登录验证码等平台反爬机制；每条结论必须回溯到源数据和采集时间；AI 绝不自动对外发帖或联系 Creator。
- **差异化能力**：建立 Evidence-first Action Chain（证据优先行动链），覆盖感知情报（明确缺失数据），以及从需求到内容的机会图谱。
- **P0 验收**：分析师能跑通单平台（如 Reddit）采集，生成带来源证据的周报草稿，并将一条用户痛点洞察转化为待执行的 Social Action。
- **最容易翻车**：把抓取不到的数据当成零、把单一负面情绪放大为品牌危机、让 LLM 在没有结构化数据输入的情况下产生事实幻觉。

---

## 第一章：产品概述

### 1.1 产品定位

Momcozy Social Intelligence Agent 是一款面向跨境母婴品牌的社媒情报与行动决策产品。它的核心使命是帮助社媒与内容团队摆脱「手工搜集、主观判断、碎版整理」的低效现状，建立一套持续发现用户需求、竞品动作、内容趋势和 Creator 机会的雷达系统，并在每个结论后附带证据与不确定性声明。

系统绝不是一个简单的舆情爬虫，必须完成以下五段闭环：

```text
监测配置（品牌/竞品词典、Creator 关注池、平台能力授权）
        |
        v
采集与清洗（跨平台 CanonicalMention、指标快照、覆盖缺口标记）
        |
        v
AI 分析引擎（实体抽取、痛点聚类、情感分析、基线偏离检测）
        |
        v
多维 Insight（S1 用户讨论 / S2 竞品动作 / S3 平台趋势 / S4 Creator 动态）
        |
        v
Social Media Action（行动建议 → 审批流 → 落地执行 → 效果反哺）
```

### 1.2 业务目标与问题定义

#### 1.2.1 业务目标

| 目标 | 结果定义 | 首期衡量方式 |
|---|---|---|
| **缩短信息发现时间** | 分析师从「大海捞针」转为「审核已筛选的高优证据」 | 基线周与上线后人工监测所需工时对比 |
| **提高洞察可执行性** | 每个 Insight 都附带具体的执行建议、平台、时间窗和责任人 | Action 生成率、采纳率、闭环时间 |
| **降低误判风险** | 清晰区分客观数据、模型推断、人工判断和未知项 | 证据覆盖率、人工驳回率 |
| **沉淀品牌知识资产** | 痛点词典、高转化的竞品玩法、Creator 黑白名单库得以沉淀 | 洞察复用率、词典版本迭代数 |
| **赋能跨部门协同** | 将用户痛点流转给产品部，将社媒危机前置给 PR | 跨部门 Action 处理数与流转速度 |

#### 1.2.2 业务场景与要回答的问题

| 模块 | 业务场景 | 要回答的问题 | 产出形态 |
|---|---|---|---|
| **S1** | 用户讨论与需求洞察 | 用户最近在讨论什么？真实使用场景和痛点是什么？有何正负面反馈或潜在风险？ | Social Listening Brief & 痛点卡 |
| **S2** | 竞品社媒营销监控 | 竞品在推什么 Campaign 或新品？哪些内容/UGC表现突出？对 Momcozy 策略有何启发？ | Competitor Intelligence Cards |
| **S3** | 热点与内容趋势洞察 | TikTok/IG/YT 有哪些相关 Hashtag/BGM 在升温？品牌适合参与吗？切入角度是什么？ | Trend Opportunity Cards |
| **S4** | 重点 Creator 内容分析 | 垂类 KOL 最近关注什么？受众反馈如何？有没有提及竞品？是否存在我们的合作机会？ | Creator Intelligence Cards |
| **Action**| 洞察转化 | 哪些话题需回应？哪些趋势要跟进？哪个 Creator 值得建联？谁来负责？ | Social Action Board |

### 1.3 深度业务调研与社媒上下文（Deep Research）

要让 Agent 输出高价值洞察，必须先向其注入深度的母婴行业社媒认知基线。

#### 1.3.1 Momcozy 与母婴社媒生态特性
母婴行业的社媒链路高度依赖「信任与同理心」。
- **高信息密度讨论场（Reddit & FB Groups）**：这是 S1 模块的核心。新手妈妈在 r/breastfeeding、r/NewParents 或私密 FB 群组中讨论的不是品牌口号，而是极度真实的痛点（如「法兰尺寸不合导致堵奶」、「带泵重返职场的尴尬」）。这里的声量可能不大，但信息纯度和转化决策权重极高。
- **视觉化与情绪共鸣场（TikTok & IG）**：这是 S3 模块的核心。POV（第一人称视角）视频、Day in the life、ASMR 清洁过程等模板非常容易在这里形成爆发趋势。
**结论**：Agent 不能用同一套逻辑处理所有平台。对 Reddit 需要深度语义解析（提取痛点、槽点），对 TikTok 需要指标增速解析（提取热点 BGM、爆款视频模板）。

#### 1.3.2 竞品动作与定位矩阵
在 S2 模块中，单纯统计竞品声量毫无意义，需要按竞品所占领的「心智叙事」来分析动作偏离：
- **Elvie / Willow**：主打高端、FemTech、隐形。其内容多强调「解放女性」，合作对象多为精英职场女性或医学专家。
- **Eufy**：新晋强势竞品，打法极其极客。在 TikTok 上大量使用真实对比数据（如吸出多少 oz 奶水）、热成像展示加热功能。
- **Momcozy**：产品线已极大丰富（M5, M9, V1 Pro, KleanPal 等），但在用户心智中常被固化为「高性价比」。
**结论**：Agent 的 S2 分析必须能抓出竞品的高表现内容，并拆解其「创意形式」（是对比评测？还是温情故事？）和「传播角度」，帮助 Momcozy 寻找差异化的内容反击点。

#### 1.3.3 Creator 合作的合规与时机捕捉
母婴 Creator 合作不再是简单的「看粉丝数发品」。
- **转型与受众流失**：许多 Creator 随着孩子长大，内容重心会从 Pumping 转向 Toddler 教育，此时继续推吸奶器效果极差。S4 必须检测其 30天/90天的话题分布变化。
- **合规风险 (FTC 披露)**：2024 年底起美国 FTC 严格审查虚假评价与未披露的赞助（#ad / #sponsored / #gifted）。若竞品合作了某 Creator 却未合规披露，这既是情报，也是品牌合作时的风险预警。
**结论**：S4 需要一个独立的「商业披露检测」机制，并且在输出合作 Action 时强制附带 Brand Safety 与 Compliance 检查。

### 1.4 三类用户画像

| 角色 | 核心目标 | 当前最大痛点 | 本产品带来的改变 |
|---|---|---|---|
| **社媒分析师** | 每日从海量数据发现信号，产出月/周报 | 数据平台多且散，靠人工复制链接；对热点只能凭直觉判断 | 直接审批 AI 筛选好的高优证据卡片，一键生成带有引用来源的 Markdown 报告草稿 |
| **内容 / KOL 策划** | 寻找可借势的爆款趋势、竞品痛点及合适的 KOL | KOL 名单静态，无法感知近期转型；趋势发现永远滞后 | 获得带执行指南的 Action Brief，明确知道「用什么角度、拍什么内容、跟进什么 BGM」 |
| **社媒/品牌负责人** | 审核并跟踪社媒行动的落地结果，把控品牌风险 | 洞察只停留在 PPT 里，无人执行，也无法追溯转化效果 | 统一的 Action Board 看板，洞察直接关联任务执行状态，实现「发现-执行-复盘」闭环 |

### 1.5 差异化对比（vs 传统舆情工具）

| 核心维度 | 传统监听工具 (如 Meltwater/Sprout) | 本 Agent (Social Intelligence) |
|---|---|---|
| **洞察落脚点** | 停留在一堆标签图云、声量折线图 | 直接输出 `Action Candidate`，明确指出下一步该干什么 |
| **事实关联度** | 情绪占比 60%，但难以定位是具体哪个零件的问题 | 区分 `Claim`、`Fact`、`Inference`，每个判断带 `evidence_set_id` |
| **竞品分析** | 只看 SOV (声量份额) 和粉丝数涨跌 | 抓取异常高优爆款，拆解竞品正在采用的「内容模板与叙事角度」 |
| **平台覆盖表达** | 假装全网覆盖，导致 0 数据时误以为用户没反应 | 引入 `coverage_grade`，实事求是展示数据抓取缺口，避免误判 |

### 1.6 可行性与系统边界

| 明确在范围内 (In Scope) | 明确排除在外 (Out of Scope) |
|---|---|
| 采集公开页面内容及品牌自有已授权的 Page 数据 | 绝对不绕过验证码、不抓取需人工验证的私密群组内用户敏感信息 |
| 利用 TikHub/Apify 抓取 TikTok、YT、IG 公开指标快照 | 把平台短期 API 限流视为系统永久故障，强制隐瞒爬取失败情况 |
| 分析并输出建议性质的 Social Media Action Brief | Agent **自动**在社交媒体上注册账号、**自动**私信 KOL、**自动**回复用户 |
| 使用 P0-P3 分阶段演进架构，用 DuckDB+Parquet 作为试验田 | 抛开业务可行性，强行从第一天就要求全平台 100% 毫秒级实时流式监听 |

### 1.7 约束分层

| 类型 | 约束要求 | 影响域 |
|---|---|---|
| **硬约束** | 所有派生结论必须回溯到源数据的 `provider_item_id` 和 `collected_at` | 数据库表结构不可妥协、Agent 提示词必须强制输出 evidence |
| **硬约束** | 涉及向外部输出动作的 Action，必须人工 (Human-in-the-loop) 审批 | 交互设计中必须存在审批流，不可跳过 |
| **推荐默认** | 先跑通 Reddit API 和 YouTube Data API，确保全链路畅通，再逐步磕 Meta 的合规 | 项目 P0 的连接器优先级和验收标准 |
| **发挥空间** | 具体的 Dashboard 前端 UI 排版、使用的开源 Embedding 模型、队列中间件 | 不影响核心数据流的技术选型可自由调整 |


---

## 第二章：整体布局与导航

### 2.1 产品信息架构 (Information Architecture)

```text
Momcozy Social Intelligence OS
│
├─ 0. 概览大屏 (Overview Dashboard)
│   ├─ 核心数据覆盖率横幅 (Coverage Banner)
│   ├─ 今日 Top 3 重大洞察速览
│   └─ Action Board 摘要 (待审批/执行中/严重风险)
│
├─ 1. S1: 用户需求监听 (Social Listening)
│   ├─ 痛点与需求热力图 (Topics & Needs)
│   ├─ 情感偏移追踪 (Sentiment Tracking)
│   └─ 关联原帖证据钻取 (Evidence Explorer)
│
├─ 2. S2: 竞品动作监控 (Competitor Monitoring)
│   ├─ 竞品活跃度大盘 (Campaign Volume)
│   ├─ 爆款内容清单 (Top Performing Content)
│   └─ 营销策略拆解卡片 (Strategy Decoding)
│
├─ 3. S3: 趋势与热点雷达 (Trend Radar)
│   ├─ 核心平台 Hashtag/BGM 飙升榜
│   ├─ 母婴相关度评分矩阵 (Relevance Score)
│   └─ 参与时机倒计时 (Action Window)
│
├─ 4. S4: Creator 情报局 (Creator Intelligence)
│   ├─ 重点关注池状态 (Watchlist Health)
│   ├─ 创作方向转型提醒 (Niche Shift Alerts)
│   └─ 品牌安全与合规检测卡 (Brand Safety & FTC Check)
│
├─ 5. 行动转化中心 (Action Engine)
│   ├─ Trello 式看版 (Candidate -> Review -> In Progress -> Done -> Archived)
│   └─ ROI 效果复盘记录 (Action Review Log)
│
├─ 6. 自动报告生成器 (Report Builder)
│   ├─ 每周/每月周报自动聚合
│   └─ 导出 Markdown / CSV 支持
│
└─ 7. 系统配置与治理 (Admin)
    ├─ 抓取词典与追踪黑白名单
    ├─ Connector API Keys 凭证状态
    └─ 用户权限分配
```

### 2.2 桌面端布局示意图 (ASCII)

```text
+-----------------------------------------------------------------------------------+
| 👑 Momcozy Social Intelligence OS | 🕒 Last Updated: 2h ago | 👤 Jane (Analyst) |
+-------------+---------------------------------------------------------------------+
| [导航栏]    | 🔔 【Coverage Alert】 TikTok API 限流中，S3 数据可能存在 4h 延迟        |
| 📊 Overview +---------------------------------------------------------------------+
| 👂 S1 监听   | [ S1 痛点洞察卡 ]            [ S2 竞品爆款卡 ]                    |
| ⚔️ S2 竞品   | 话题: M9 法兰尺寸偏小        Eufy 新出了产奶量测评视频           |
| 📈 S3 趋势   | 热度: 🔥 +40% (24h)          播放量偏离基线: +250%               |
| 🌟 S4 KOL    | 建议 Action: 出一期挑选指南  建议 Action: 快速复刻同款测试       |
| 🎯 Action   +---------------------------------------------------------------------+
| 📝 Reports  | 📝 【Action 待审批任务】                                          |
| ⚙️ Admin    |  - [待审批] 回应 Reddit 上关于清洗管道发霉的集中抱怨 (S1)           |
|             |  - [进行中] 趁热打铁跟进 #PumpTok 的搞笑 BGM 挑战 (S3)             |
|             |  - [待审批] 暂停与 KOL @MommyLife 的合作 (检测到 Eufy 合作) (S4)    |
+-------------+---------------------------------------------------------------------+
```

### 2.3 首次使用流程

1. **Auth & Setup**: Admin 在设置页输入 TikHub、Apify 等第三方服务的 API Keys。
2. **Dictionary Builder**: 配置品牌词（Momcozy, M5, M9, V1 Pro 等及其变体）、竞品白名单、要重点监控的 Subreddit 列表及 Creator 初始白名单。
3. **Dry Run**: 触发一次全量连接测试，生成一份 `coverage_report`，确认各个平台的抓取连通性、配额消耗速率及字段缺失情况。
4. **Data Ingestion**: 启动第一次定时抓取任务，累积历史快照基线（Baseline）。
5. **Insights Gen**: Agent 根据首批数据运行 Pipeline，生成 S1-S4 的初始洞察和候选 Action，进入日常操作流。

### 2.4 角色权限表

| 角色 | 查看 S1-S4 洞察 | 配置爬虫词典/凭证 | 审批 Action 建议 | 导出原始用户数据 (PII) |
|---|:---:|:---:|:---:|:---:|
| **Admin** | ✅ | ✅ | ✅ | ✅ (受法务审核约束) |
| **社媒分析师 (Analyst)** | ✅ | ✅ | ❌ | ❌ |
| **内容负责人 / 策划** | ✅ | ❌ | ✅ | ❌ |
| **品牌合规专员** | ✅ | ❌ | ✅ (拥有最高一票否决权) | ❌ |

---

## 第三章：核心模块详细设计

### 第 3.1 节 监测范围与连接器管理

#### a) 架构示意图 (ASCII)

```text
[ 监测范围池 ] 
  ├─ 品牌词: [Momcozy, M5...] 
  ├─ 竞品: [Elvie, Eufy...]
  ├─ KOL: [@mommy_jane, ...]
  └─ 社区: [r/breastfeeding...]
         ↓ 映射给
[ 连接器 (Connectors) ]
  ├─ Reddit (TikHub) --> [状态: ✅ 健康]
  ├─ YouTube (Apify) --> [状态: ✅ 健康]
  └─ TikTok (TikHub) --> [状态: ⚠️ 限流重试中]
```

#### b) 交互流程

- **正常流程**：Analyst 添加一个竞品账号 `@eufy_baby` -> 系统校验平台有效性 -> 选择监控频率 (如 12h 一次) -> 绑定到 TikHub/Apify 任务队列 -> 任务成功，数据进入 ODS 归档。
- **失败流程 1 (账号不存在)**：Analyst 输错账号名 -> 校验接口返回 404 -> UI 抛出错误提示，阻止配置保存，避免脏数据跑入定时任务。
- **失败流程 2 (抓取限流)**：定时任务触发 -> TikHub 报 429 Too Many Requests -> 连接器进入 Exponential Backoff 退避状态 -> UI 顶部显示黄色预警横幅。
- **失败流程 3 (凭证失效)**：Apify 余额耗尽 -> API 报 401/402 -> 连接器标记为 `broken` -> ODS 停止写入，转入 DLQ -> 发送邮件告警给 Admin。

#### c) 状态清单

| 状态 | 触发条件 | 视觉颜色 | 后续逻辑 |
|---|---|---|---|
| `Healthy` | 连接器正常返回 200 及预期 JSON Schema | 🟢 绿 | 继续下一次定时轮询 |
| `Partial` | 抓取到了帖子但缺少评论/互动等字段 | 🟡 黄 | 数据入库，但字段置空，影响部分分析权重 |
| `Rate_Limited` | 触发平台反爬 429 | 🟠 橙 | 进入冷却退避队列 |
| `Broken` | 认证失败或 Schema 大改无法解析 | 🔴 红 | 熔断停止，等待人工修复 Adapter |

#### d) 依赖关系
- 依赖上游：外部第三方数据服务商 (Apify / TikHub API)。
- 依赖下游：数据存储层 (ODS / DuckDB)。

#### e) 待决问题
1. Momcozy 公司当前可用于这套 Agent 的 Apify 月度预算上限是多少？是否需要配置熔断阈值？
2. 针对 FB 私密群组，是否存在法务认可的「人工导出版」方案以替代 API 自动化抓取？


---

### 第 3.2 节 用户讨论与需求洞察（S1 Social Listening）

#### a) 架构示意图 (ASCII)

```text
[ DWD 层清洗数据 ] (Reddit/FB/YT评论)
        ↓
[ NLP Engine ] (语义聚类 / 痛点提取 / 情感打分)
        ↓
+-------------------------------------------------+
| S1 洞察结果卡片                                 |
| 主题: [漏奶/密封不严]   | 情感: 😠负面 85%      |
| 趋势: +120% 声量激增    | 场景: [开车时], [平躺]  |
| 代表证据:                                       |
| - r/NewParents: "M9 稍微弯腰就洒了..." (链接)    |
| - YT Comment: "开车戴这个搞得衣服全湿了" (链接)  |
+-------------------------------------------------+
        ↓
[ 转化建议 ] --> Action: 输出图文辟谣/科普「正确佩戴姿势」
```

#### b) 交互流程

- **正常流程**：数据到位 -> LLM / Embedding 聚类出 `topic_key` -> 提取典型引语 (Quotes) -> 形成 S1 Insight 卡片 -> Analyst 点击审批并转化为 Action 候选。
- **失败流程 1 (样本太少)**：某个话题下只有 2 条吐槽 -> 达不到置信度阈值 (设定为 10 条) -> 该 Insight 标记为 `Low Confidence`，进入观察池，不强制推给 Analyst。
- **失败流程 2 (情绪误判)**：用户发帖 "This pump is sick af!" (表达极好) -> 基础 NLP 误判为负面 -> Analyst 在卡片上右键点击 "修正情感标签" -> 该样本被加入微调校准集。
- **失败流程 3 (数据源倾斜)**：本周 API 故障导致 TikTok 评论未能抓取 -> S1 面板显示「数据覆盖警告：当前结论仅基于 Reddit 样本生成，可能不具备普适性」。

#### c) 状态清单

| 状态 | 触发条件 | 视觉颜色 | 后续逻辑 |
|---|---|---|---|
| `New Topic` | 聚类算法新发现的此前未见话题 | 🔵 蓝 | 突出展示在顶部 |
| `Trending` | 同比上周话题声量暴增 50% 以上 | 🔥 火焰 | 触发邮件/飞书告警 |
| `Confirmed` | Analyst 审阅过并同意该痛点真实存在 | 🟢 绿 | 允许生成 Action |
| `Rejected` | Analyst 认为这是垃圾信息或误匹配 | ⚪ 灰 | 从统计大盘剔除 |

#### d) 依赖关系
- 依赖上游：3.1 提供的高质量干净文本数据。
- 依赖下游：Action Engine（3.6）用于将确定的痛点变成动作。

#### e) 待决问题
1. 当 S1 模块检测到严重的产品质量安全问题时（如机器过热），除了在 UI 告警，是否需要 Webhook 直接打通内部的质量追踪系统 (Jira)？

---

### 第 3.3 节 竞品社媒营销动作监控（S2）

#### a) 架构示意图 (ASCII)

```text
[ 目标: @EufyBaby, @WillowPump 等官方账号内容 ]
        ↓
[ 基线偏离引擎 ] (当前视频播放量 vs 该账号近30天平均播放量)
        ↓
+-------------------------------------------------+
| S2 竞品爆款解构卡                               |
| 竞品: Eufy           | 发布时间: 12h 前       |
| 动作类型: 新品推广    | 互动偏离度: +350% 💥    |
| 内容形式: 测评对比    | 核心主张: 加热+产奶快   |
| 拆解: [开头1秒放大痛点] + [真实奶瓶刻度展示]      |
+-------------------------------------------------+
        ↓
[ 转化建议 ] --> Action: 借鉴其直观的数据展示形式，应用于 M9 的下一次 Campaign
```

#### b) 交互流程

- **正常流程**：抓取竞品新发视频 -> 对比其自身基线 (Baseline) 发现是爆款 -> LLM 分析其视觉元素和脚本逻辑 -> 生成 S2 Insight 卡片 -> Analyst 同意后归档为竞品参考库。
- **失败流程 1 (基线不可靠)**：某竞品账号刚建号，历史视频不足 5 条 -> 无法算出合理的统计学基线 -> 标记该内容为 `Baseline Unstable`，仅做流水记录，不标为爆款。
- **失败流程 2 (刷量噪声)**：竞品某视频点赞极高但评论极少/水军多 -> 触发异常比例检测 -> LLM 标记为 `Suspected Bot Traffic`，提醒 Analyst 不要盲目借鉴。
- **失败流程 3 (内容删除)**：抓取到竞品视频，随后竞品删帖 -> 系统周期核查返回 404 -> 保留文字快照，标记 `Deleted by Author`，供内部分析删帖原因。

#### c) 状态清单

| 状态 | 触发条件 | 视觉颜色 | 后续逻辑 |
|---|---|---|---|
| `Routine` | 表现平平的常规发布 | ⚪ 灰 | 仅留存数据，不重点展示 |
| `Outlier` | 数据远超基线，确认是爆款 | 🔴 红 | 置顶分析，建议借鉴 |
| `Campaign`| 检测到特定的话题标签 (如 #MothersDay) 被密集使用 | 🟣 紫 | 将多个散装帖子合并为事件分析 |

#### d) 依赖关系
- 依赖上游：TikTok / IG 连接器对特定 Handle 账号的准时抓取及指标 (Metrics) 每日更新。

#### e) 待决问题
1. 对视频创意形式的拆解，目前只能通过抓取 Caption 和 Transcript (转录文本) 来实现。如果平台不支持导出 Transcript，是否接受纯靠文字描述推断？

---

### 第 3.4 节 社媒热点与内容趋势（S3 Trend Radar）

#### a) 架构示意图 (ASCII)

```text
[ 平台趋势大盘 TikTok/IG/YT ]
        ↓
[ 过滤引擎 ] (母婴相关度 > 70% OR 形式可迁移性高)
        ↓
+-------------------------------------------------+
| S3 趋势机会卡                                   |
| 趋势类型: BGM 挑战    | 平台: TikTok            |
| 趋势名: "Just a mom trying to survive" 搞笑配音   |
| 上升斜率: 极快 🚀     | 生命周期预估: 还剩 5 天   |
| 品牌适配度: 高 (适合展现吸奶时的真实狼狈状态)       |
+-------------------------------------------------+
        ↓
[ 转化建议 ] --> Action: 通知内容团队 48h 内翻拍该 BGM
```

#### b) 交互流程

- **正常流程**：TikHub Trending 榜单抓取 -> LLM 过滤掉纯政治/游戏无关热点 -> 对相关趋势进行生命周期评分 -> 输出参与建议 -> 内容负责人审批立项。
- **失败流程 1 (热点已凉)**：抓取延迟，分析出结果时该 Hashtag 增速已连续 3 天下降 -> 系统预判生命周期已结束 -> 标记为 `Too Late to Jump In`，阻止生成执行 Action。
- **失败流程 2 (版权侵权风险)**：热点是一首版权音乐，品牌不可商用 -> 过滤引擎识别到商业风险 -> Action 建议被改写为「不可直接用原音，但可模仿其卡点节奏」。
- **失败流程 3 (品牌调性不符)**：热点是一个涉及擦边/危险动作的挑战 -> LLM 的 Brand Safety Prompt 将其拦截 -> 标记为 `Brand Safety Risk`，禁止推送。

#### c) 状态清单

| 状态 | 触发条件 | 视觉颜色 | 后续逻辑 |
|---|---|---|---|
| `Rising` | 趋势处于早期上升阶段 | 🟢 绿 | 强烈建议介入 |
| `Peaking`| 趋势达到顶峰 | 🟡 黄 | 谨慎介入，随时可能衰退 |
| `Declining`| 热度下降 | 🔴 红 | 放弃跟进 |
| `Toxic` | 存在舆论、版权、安全风险 | ⚫ 黑 | 永久拉黑 |

#### d) 依赖关系
- 依赖上游：必须使用 TikTok/IG 官方或第三方的 Trending/Explore 发现接口，而不能靠穷举。
- 依赖下游：内容制作团队的极速响应能力（趋势不等人）。

#### e) 待决问题
1. 品牌方关于 Brand Safety (危险、政治、敏感议题) 的具体定义和黑名单词库需要业务方提前提供，否则拦截引擎无法工作。

---

### 第 3.5 节 重点 Creator 内容分析（S4）

#### a) 架构示意图 (ASCII)

```text
[ Creator 白名单池: @MommyJane, @DrSmith... ]
        ↓
[ 定向监控引擎 ] (历史发文 + 粉丝画像 + FTC披露检测)
        ↓
+-------------------------------------------------+
| S4 Creator 情报卡                               |
| KOL: @MommyJane     | 平台: YT (200k 粉丝)    |
| 近30天内容偏移: ⚠️ 从 [产后恢复] 转向 [辅食添加]    |
| 竞品合作: 检测到 #ad 标签并提及 @EufyBaby         |
| 合作建议: 暂停/延缓 (受众焦点已转移 + 竞品锁定期)   |
+-------------------------------------------------+
```

#### b) 交互流程

- **正常流程**：抓取 Creator 白名单内容 -> 统计近 30 天词频分布对比 90 天前 -> 检测到无内容偏移且无竞品合作 -> 打出高「合作适宜度」评分 -> 建议 KOL 团队建联。
- **失败流程 1 (账号转型)**：如架构图所示，KOL 的孩子长大，内容不再是 Pumping -> 系统检测到 Semantic Shift -> 建议库将该 KOL 标为 `Not Suitable Currently`。
- **失败流程 2 (隐性赞助未披露)**：KOL 狂夸竞品但未带 #ad 标签 -> 系统根据语气模型判定「疑似未披露赞助」 -> 弹出警告，要求人工进行风险尽调。
- **失败流程 3 (舆论翻车)**：白名单 KOL 涉及种族歧视/虐童等社会争议 -> 其评论区负面激增 -> 触发熔断告警 -> 建议品牌立即切割。

#### c) 状态清单

| 状态 | 触发条件 | 视觉颜色 | 后续逻辑 |
|---|---|---|---|
| `Prime Window` | 处于最佳合作空窗期，内容高度匹配 | 🟢 绿 | 推送建联建议 |
| `Topic Shift`| 内容赛道发生转移 | 🟡 黄 | 重新评估合作价值 |
| `Sponsored`| 检测到与竞品的商业合作 | 🟠 橙 | 进入冷却观察期 |
| `Cancelled`| 创作者出现重大个人丑闻 | 🔴 红 | 拉黑并停止监控 |

#### d) 依赖关系
- 依赖上游：KOL 关注名单必须由业务方提供（Agent 自动海选 KOL 成本太高且准确率低，应作为未来拓展）。
- 依赖外部法规：FTC Guidelines 规则集更新。

#### e) 待决问题
1. 系统是否需要直连品牌方的 CRM/KOL 管理工具？还是 S4 分析仅停留在报告阶段，靠人工复制给 KOL 团队？

---

### 第 3.6 节 Social Action Engine 与 Action Board

这是本系统超越传统舆情软件的「最后一步」，负责将 S1-S4 的 Insight 收敛为具体行动。

#### a) 架构示意图 (ASCII)

```text
( S1 痛点 ) + ( S2 竞品解法 ) + ( S3 热点 BGM )
        ↘       ↓        ↙
  [ Action Engine 组装打分 ]
        ↓
+-------------------------------------------------------------+
| 🎯 Action Ticket: 制作「低噪音办公泵奶」TikTok 短片             |
| 来源依据: Insight-S1-009, Insight-S3-042                       |
| 推荐执行人: @内容团队   |  截止期: 3天内                        |
| 约束条件: 不可宣扬「绝对静音」以免合规纠纷                       |
| 状态: [ Approve ]  [ Reject ]  [ Modify ]                      |
+-------------------------------------------------------------+
```

#### b) 交互流程

- **正常流程**：Insight 满足确凿性阈值 -> Action 引擎合成 Ticket -> 品牌负责人点击 `Approve` -> 状态变更为 `In Progress` -> 负责人落地执行后填入结果链接 -> 变为 `Done`。
- **失败流程 1 (证据薄弱)**：Insight 虽有，但只有 1 条来源帖子 -> Action 引擎判定 Confidence 极低 -> 不生成 Ticket，仅保留在「待观察池」。
- **失败流程 2 (人工否决)**：引擎生成了 Action，但品牌负责人认为本月预算不足 -> 点击 `Reject` -> 要求输入 Reject 原因 (如: 预算限制) -> 优化未来 AI 推荐权重。
- **失败流程 3 (执行过期)**：获批跟进某热点，但执行人 7 天没动静 -> 引擎判定窗口期已过 -> 状态自动变更为 `Expired`，停止无效投入。

#### c) 状态清单

| 状态 | 触发条件 | 视觉颜色 |
|---|---|---|
| `Candidate` | AI 自动生成，等待人工审批 | ⚪ 灰 |
| `Approved` | 负责人审核通过，分配给执行人 | 🟡 黄 |
| `In Progress` | 执行人接单，正在制作内容或建联 | 🔵 蓝 |
| `Done` | 执行完毕，附带落地链接 | 🟢 绿 |
| `Rejected` / `Expired` | 审批驳回 / 超出黄金时间窗 | 🔴 红 / 🟤 褐 |

#### d) 依赖关系
- 必须基于有坚实 `evidence_set_id` 的 Insight 生成，禁止虚空创造 Action。

#### e) 待决问题
1. 这个看板是否需要双向同步到飞书任务 / Jira，以便融入团队现有的工作流？


---

### 第 3.7 节 AI Agent 工作台与证据问答

#### a) 架构示意图 (ASCII)

```text
[ 搜索框: "用户为什么觉得 M9 清洗麻烦？" ]
        ↓
[ Agent Router ] -> 查 DB / 查 Vector Index / 查 业务状态
        ↓
Agent: "根据近 2 周 45 条 Reddit 数据，主要原因是法兰死角难刷。"
🔗 证据 1: r/Mommit (2026-08-10) "The edges of M9 are hell to clean..."
🔗 证据 2: YT Comment (2026-08-12) "Milk gets stuck..."
> ⚠️ 数据限制: 目前未接入 FB Groups，可能有结论偏差。
```

#### b) 交互流程

- **正常流程**：用户提问 -> Agent 将意图转化为 SQL/Vector Search -> 返回总结并**强制附带 3-5 条真实原文和出处链接**。
- **失败流程 1 (幻觉阻断)**：用户提问的内容完全未被抓取过 -> Agent 检索返回空 -> 必须直接回答「系统暂无相关数据支撑」，**绝对禁止**靠大模型预训练知识去瞎编。
- **失败流程 2 (操作越权)**：用户要求 "去给那条黑我们的帖子留言反驳" -> Agent 识别到非法 `write` 操作 -> 拒绝执行，提示「请在外部平台通过官方账号手动处理，我只能为您起草回复文本」。
- **失败流程 3 (超出时间窗)**：用户询问 3 年前的数据 -> 数据仓库中已归档清理 -> 提示超出查询服务范围。

#### c) 状态清单 (Agent 会话状态)

| 状态 | 触发条件 | 视觉表现 |
|---|---|---|
| `Thinking` | 解析意图，生成查询计划 | 脑图 Loading 动效 |
| `Retrieving` | 正在数据库或向量库捞取证据 | 显示检索进度条 |
| `Synthesizing`| 组合证据写出连贯回答 | 打字机效果输出 |
| `Grounded` | 回答完毕，附带可用证据引用 | 链接变蓝，可悬浮预览 |

#### d) 依赖关系
- 强依赖 RAG (Retrieval-Augmented Generation) 架构的准确性，以及底层数仓 `dwd_canonical_mention` 宽表的健全。

#### e) 待决问题
1. 查询是否需要保存 Session 记忆，以支持连续多轮对话的上下文追问？

---

## 第四章：超越竞品的差异化功能

传统舆情软件通常是「词云展示机」，而此系统的差异化在于深度的逻辑闭环和业务理解。

### 4.1 Evidence-first Social Action Chain
1. **竞品为何不具备**：传统舆情软件生成的报告和任务管理系统是割裂的。出了一份舆情 PDF，执行人拿到手还得自己去想该怎么做，并且经常忘了当时是基于哪条数据做的决策。
2. **本产品如何实现**：所有派生出的 Insight 都绑定了底层明细数据的 `evidence_set_id`；基于 Insight 派生的 Action 同样继承这个溯源链条。
3. **交互流程**：查看 Action -> 点击 "查看依据" -> 展开看到 Insight 卡片 -> 点击 "查看原帖" -> 直接跳到 Reddit 吐槽详情。
4. **风险与应对**：帖子被平台删除导致链条断裂。应对：数据入库时保留去隐私的 `text_excerpt` 快照。

### 4.2 Coverage-aware Intelligence
1. **竞品为何不具备**：很多 SAAS 工具不管抓没抓全，直接在图表上画 0。如果 TikTok API 挂了三天，图表上就显示这三天品牌声量为零，极易引发业务误判。
2. **本产品如何实现**：引入 `coverage_grade` 和 `system_health`。在产出任何聚合指标时，强制判断该时间窗口内爬虫的健康度。
3. **交互流程**：大盘声量下跌 50% -> 旁边直接亮起红色提示 "⚠️ 并非真实下跌，昨日 YouTube 接口抓取失败，数据缺损"。
4. **风险与应对**：过度报警让用户麻木。应对：非核心边缘平台（如一个小论坛）抓取失败静默处理，只在 S/A 级数据源出险时强提示。

### 4.3 Demand-to-Content Opportunity Graph (需求到内容机会图谱)
1. **竞品为何不具备**：倾听用户的抱怨，和怎么拍好一条短视频，中间隔着内容创意的鸿沟。
2. **本产品如何实现**：将 S1（用户痛点）、S2（竞品高转化创意）、S3（当红 BGM/模板）在生成 Action 时做交叉合并（Cross-reference）。
3. **交互流程**：发现痛点 A -> Agent 去 S2 找竞品是怎么解的，去 S3 找最近用什么形式表达最好 -> 最终合成一个三维的 Content Brief。
4. **风险与应对**：组合出的创意四不像（生搬硬套）。应对：依赖专业的内容策划最终把关 `Approve`。

### 4.4 Creator Timing and Brand Safety Card
1. **竞品为何不具备**：网红库筛选主要看互动率 (Engagement Rate)，但网红最近是否接了大量竞品商单、是否刚刚陷入过争议，传统工具难以自动判定。
2. **本产品如何实现**：引入 FTC Compliance Prompt 和 Brand Safety Prompt，专属审查其近 30 天内容的文本。
3. **交互流程**：KOL 虽然数据好，但被检测到 "Sponsored by [Competitor]" 出现频次过高 -> Agent 将合作评级打为 C 级 (冷静期)。
4. **风险与应对**：FTC 标签五花八门，可能漏判隐性软文。应对：增加对特定感谢词 ("Thanks to X for sending me...") 的语义识别，不局限于 `#ad`。


---

## 第五章：数据模型

### 5.1 数据模型原则

1. **事实推断严格分离**：客观抓取数字存一起，LLM 生成的结论（带不可靠性）存另一张表。
2. **唯一身份追溯**：用 `provider + provider_item_id` 联合做主键，保证多级抓取不重入。
3. **时态分离**：必须保留 `published_at`（帖子发布时间）和 `collected_at`（抓取系统记录时间）。
4. **软删除策略**：合规要求删除时，标记 `deletion_status='deleted'`，不清空主键历史，避免二次爬取又入库。
5. **JSON/Parquet 兜底**：关系数据库只存提炼结构，全量乱七八糟的平台私有 Payload 原样扔对象存储。
6. **血缘强制挂载**：Insight 表必须挂 `evidence_set_id`，Action 表必须挂 `source_insight_id`。
7. **数据孤岛防御**：字段找不到不要写 0，写 `null`，以便覆盖率计算引擎能识别缺口。

### 5.2 MonitorScope 数据契约

```json
{
  "version": "1.0",
  "scope_id": "scope_brand_momcozy_m9",
  "target_type": "product",
  "keywords": ["Momcozy M9", "M9 pump", "BP223"],
  "exclude_keywords": ["giveaway", "promo code"],
  "target_platforms": ["reddit", "youtube"],
  "status": "active",
  "updated_at": "2026-08-13T10:00:00Z"
}
```

### 5.3 CanonicalMention 数据契约

```json
{
  "version": "1.0",
  "mention_id": "reddit_t3_abc123",
  "provider": "reddit",
  "provider_item_id": "t3_abc123",
  "source_url": "https://reddit.com/...",
  "author_ref": "hash_xyz",
  "text_excerpt": "The flange size is confusing...",
  "metrics": { "upvotes": 45, "comments": 12 },
  "published_at": "2026-08-12T15:00:00Z",
  "collected_at": "2026-08-13T02:00:00Z",
  "deletion_status": "active"
}
```

### 5.4 Insight 数据契约

```json
{
  "insight_id": "insight_S1_001",
  "type": "pain_point",
  "fact_text": "Reddit 上有 45 条帖子集中讨论 M9 的法兰选码困难。",
  "inference_text": "建议在官网/社媒出更直观的尺码测量尺教程。",
  "evidence_set_id": "es_001",
  "confidence_score": 0.85,
  "model_version": "gpt-4o-2024-05-13",
  "created_at": "2026-08-13T03:00:00Z"
}
```

### 5.5 SocialAction 数据契约

```json
{
  "action_id": "act_001",
  "source_insight_id": "insight_S1_001",
  "action_type": "content_creation",
  "title": "制作 M9 法兰测量 TikTok 教程",
  "assignee_role": "content_team",
  "status": "pending_approval",
  "due_date": "2026-08-20T00:00:00Z",
  "constraints": "不要建议用户购买非官方配件以避免漏奶纠纷"
}
```

### 5.6 关系型数仓分层 (Data Warehouse)

| 层级 | 职责 | 核心表 |
|---|---|---|
| **控制层 (DIM)** | 元数据与配置 | `dim_monitor_scope`, `dim_creator_watchlist`, `dim_competitor_dic` |
| **原始层 (ODS)** | 纯净落地数据 | `ods_raw_payload` (存放 JSON 链接), `ods_metric_snapshot` |
| **明细层 (DWD)** | 结构化去重数据 | `dwd_canonical_mention` (核心明细表), `dwd_nlp_annotation` |
| **汇总层 (DWS)** | 主题/时间聚合 | `dws_topic_daily`, `dws_trend_momentum`, `dws_competitor_volume` |
| **应用层 (ADS)** | 最终产出提供给端 | `ads_insight`, `ads_action`, `ads_coverage_health` |

### 5.7 核心表 SQL 草案 (PostgreSQL 示例)

```sql
CREATE TABLE dwd_canonical_mention (
    mention_id VARCHAR(128) PRIMARY KEY,
    provider VARCHAR(32) NOT NULL,
    provider_item_id VARCHAR(128) NOT NULL,
    source_url TEXT,
    text_excerpt TEXT,
    published_at TIMESTAMPTZ NOT NULL,
    collected_at TIMESTAMPTZ NOT NULL,
    metrics_json JSONB,
    deletion_status VARCHAR(16) DEFAULT 'active',
    UNIQUE (provider, provider_item_id)
);

CREATE TABLE ads_action (
    action_id VARCHAR(128) PRIMARY KEY,
    source_insight_id VARCHAR(128) NOT NULL,
    action_type VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(32) DEFAULT 'candidate',
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

### 5.8 数据质量规则 (Data Quality Rules)

1. **唯一性测试**: `provider + provider_item_id` 不可重复，重复必须触发 Upsert/Merge。
2. **完整性测试**: `collected_at` 绝对不可为空，否则丢弃（脏数据）。
3. **时序测试**: `published_at` 绝不能晚于 `collected_at` (防止解析错时区穿越)。
4. **孤儿检查**: `ads_insight` 里引用的 `evidence_set_id` 在底表中查不到，告警数据断链。

### 5.9 数据保留与删除

- 原始爬虫报文 (Payload): S3 对象存储保留 30 天后转入低频存储。
- 清洗后的 DWD 文本: 滚动保存 24 个月。
- 指标快照 (DWS): 永久保存，用于看长周期品牌力变化。
- 合规清理: 当触发 GDPR/CCPA / 平台下架请求时，根据 `provider_item_id` 抹除 DWD 文本，但聚合数字允许以脱敏形式保留。


---

## 第六章：技术架构

### 6.1 分层架构示意图 (ASCII)

```text
[ 用户体验层 (Next.js) ] -> 看板, 审批流, 报告导出
         ↕
[ API 层 (FastAPI) ] -> 鉴权, CRUD, 触发 Agent Run
         ↕
[ Agent 编排层 (LangGraph) ] -> Query Plan, 工具调用, State Checkpoint, 审批拦截
         ↕
[ AI/NLP 引擎层 ] -> GPT-4o / Claude (推理), SentenceTransformer (聚类)
         ↕
[ 数据基座层 ] -> PostgreSQL (控制), DuckDB/Parquet (分析), OpenSearch (检索)
         ↕
[ 爬虫处理层 (Python Workers) ] -> Rate Limit, Retries, Cursor Pagination
         ↕
[ 外部 API (Apify / TikHub) ] -> Reddit, TikTok, YouTube...
```

### 6.2 推荐部署路线

- **P0 (MVP 试点)**: Python 单体脚手架调度 + DuckDB + SQLite (存状态)。核心跑通 `Apify/Reddit` 链路，跑通 Prompt。证明该工具能产生有价值的 S1 洞察卡片。
- **P1 (生产增强)**: LangGraph 入驻云端集群，改用 PostgreSQL 存 Checkpoint；上云版 Elasticsearch 做文本检索，引入 Celery / Kafka 做分布式爬虫队列调度。

### 6.3 Agent 工作流 (Workflow Pipeline)

1. `Schedule_Trigger`: 定时任务唤醒 Agent。
2. `Check_Coverage`: 看看各个爬虫接回来的数据是否达标。
3. `Run_Clustering`: 聚类相似的讨论。
4. `LLM_Evaluate`: 将聚类结果喂给大模型提取 Insight。
5. `Evidence_Gate`: (关键防御) 检查提取的 Insight 是否有真实链接对应，如果没有，回退。
6. `Generate_Action`: 输出候选动作。
7. `Wait_for_Human`: (Interrupt) 挂起，直到 Analyst 点击确认。

### 6.4 连接器接口 (Connector Interface)

```python
class BaseSocialConnector:
    def check_health(self) -> HealthStatus:
        """检查 API Key 与限流状态"""
        pass
        
    def fetch_data(self, scope: ScopeConfig, cursor: str) -> FetchResult:
        """根据词典和游标抓取数据"""
        pass
        
    def normalize_to_dwd(self, raw_data: dict) -> CanonicalMention:
        """洗平为 DWD 标准宽表结构"""
        pass
```

### 6.5 平台能力矩阵

| 平台 | 采集策略 | 可采集核心对象 | 限制与覆盖盲区 | 承诺级别 |
|---|---|---|---|---|
| **Reddit** | TikHub API | 帖子, 评论, Upvotes | 历史老帖可能搜不全 | P0 (首发重点) |
| **YouTube** | Apify YouTube Scraper | 视频, Shorts, 评论区 | 评论盖楼太深可能截断 | P0 (主攻 S2/S4) |
| **TikTok** | TikHub API / SDK | 视频, Hashtag 榜单 | 商业接口极其严格，只能尝试公开抓取 | P1 |
| **Instagram** | Apify IG Scraper | Reels, Posts | 封控极严，容易死号断流 | P1 |
| **FB Groups** | 暂无法自动化 | 无法直接抓私密群 | 法务红线风险极高 | P2 (暂挂起，靠人工录入) |

### 6.6 技术依赖表

- **语言**: Python 3.11+
- **框架**: FastAPI (Web), LangGraph (Agent State)
- **数据**: DuckDB (Analytical), PostgreSQL (Transactional)
- **调度**: Celery or RQ
- **模型**: 优先调用公司认可的基础模型 API (OpenAI/Anthropic)

### 6.7 最大架构风险

- **平台风控封锁 API**：最致命风险。某天 Apify/TikHub 突然瘫痪，导致系统"断粮"。
  - *应对方案*：UI 设计必须强依赖 Coverage Banner，大大方方承认数据断流，而非给假数据。
- **Agent 死循环/发散**：面对巨大文本，LLM 可能会归纳出幻觉，乱指控竞品。
  - *应对方案*：强化 `Evidence_Gate` 代码逻辑（非 LLM），强校验 JSON 中的 ID 存不存在库里。

---

## 第七章：交互细节

### 7.1 键盘快捷键

| 快捷键 | 功能 |
|---|---|
| `Cmd + K` / `Ctrl + K` | 唤起全局搜索命令台 (Command Palette) |
| `g` then `1` | 快速跳转至 S1 (Social Listening) |
| `g` then `a` | 快速跳转至 Action Board |
| `Esc` | 关闭当前全屏或侧边栏抽屉 |
| `Enter` (在审批页) | 一键 Approve 当前选中的 Action |

### 7.2 右键菜单与上下文菜单

- **Insight 卡片右键**: 
  - [查看溯源树]
  - [转交为 Action]
  - [标记为无用 (调教模型)]
- **Action Ticket 右键**: 
  - [修改指派人]
  - [强制归档]

### 7.3 空状态 (Empty States)

- **无抓取数据时**: "Oops, 爬虫们正在努力搬砖中... 预估 2 小时后产出第一批报告，请先去喝杯咖啡☕️。"
- **无 Action 候选时**: "和平的一天！当前没有需要紧急处理的舆情或趋势机会。"

### 7.4 错误状态 (Error States)

- **API 429 报错**: 显示橙色警告条："TikTok 抓取限流中，当前 S3 数据可能为昨天的快照。"
- **断网/后端宕机**: "无法连接到大本营，请检查网络或摇人 (Slack @DevTeam)。"

### 7.5 加载状态 (Loading States)

- 用骨架屏 (Skeleton) 代替转圈圈，避免画面跳跃。
- 如果大模型正在生成周报 (耗时可能 > 30秒)，显示步骤动画: `清洗数据...` -> `提取观点...` -> `生成 Markdown...`，安抚等待情绪。


---

## 第八章：导出与输出系统

### 8.1 支持的输出格式

- **Markdown (.md)**：主打汇报格式，天然兼容 Notion/飞书/GitHub。
- **CSV / Excel**：供高阶分析师做二次透视表（如下钻看所有负面评论明细）。
- **JSON**：供上下游系统 (如现有的工单系统) 抓取。

### 8.2 输出文件结构 (ASCII)

```text
/exports
 ├─ /weekly_reports
 │   ├─ SI_Weekly_2026_W33.md
 │   └─ SI_Weekly_2026_W33_sources.csv (附带全部证据链)
 ├─ /action_briefs
 │   └─ Action_Brief_Tiktok_Challenge.pdf
```

### 8.3 Markdown 报告结构

必须包含以下固定章节：
1. **Executive Summary** (红黑榜、核心趋势)
2. **Data Coverage Warning** (必须老实交代本周哪些平台挂了，样本覆盖率)
3. **S1 - Voice of Customer** (按产品线分发用户痛点聚类)
4. **S2 & S3 - Competitive & Trends** (竞品大动作与可跟进的 Hashtag)
5. **S4 - Creator Watch** (避雷警告与合作推荐)
6. **Action Items** (本周需执行的任务清单)

### 8.4 批量处理流程
采用每周日晚凌晨 2:00 自动触发 Batch Job，将前 7 天的 DWS 汇总跑入报告生成 Pipeline。周一早 9:00 前推送到社媒负责人的飞书。

---

## 第九章：开发优先级

| 阶段 | 范围 | 交付标准 (Done Criteria) |
|---|---|---|
| **P0** (MVP) | Reddit 爬虫接入 + S1 痛点洞察链路 + 基础 Action 审批板 | Analyst 能在看板上看到真实的 Reddit 槽点，并审批出一个 Action |
| **P1** | YouTube/TikTok/IG 爬虫接入 + S2/S3/S4 全链路贯通 + 自动周报 | 社媒团队能扔掉 Excel，直接看 Markdown 周报，Action 板开始流转工作 |
| **P2** | 深度打磨「需求到机会图谱」，加入高阶 Semantic 搜索功能 | 用户可以在框里自然语言提问 "上周谁夸了我们的 M9"，Agent 能带引用回答 |
| **P3** | 自定义 BI 大屏，外部系统 Webhook 联动 | 与公司 Jira、Slack、现有 CRM 无缝打通 |

---

## 第十章：性能指标 (Performance Metrics)

| # | 指标名称 | 目标值 (SLA) | 测量方法 | 劣化阈值 (报警线) |
|:---|---|---|---|---|
| 1 | Reddit 采集延迟 | < 4 小时 | `collected_at` - 爬虫触发时 | > 12 小时 |
| 2 | YouTube 采集延迟 | < 12 小时 | `collected_at` - 爬虫触发时 | > 24 小时 |
| 3 | Connector 成功率 | > 95% | HTTP 200 次数 / 总请求数 | < 80% (触发严重告警) |
| 4 | 冗余/重复入库率 | < 0.1% | DWD 表中主键冲突检查 | > 1% (代码有 Bug) |
| 5 | 数据追溯率 (Evidence链) | 100% | `evidence_set_id` 存在性检验 | < 100% (阻断报告生成) |
| 6 | 话题聚类一致性 | > 85% | 同批数据重跑聚类比较 | < 70% |
| 7 | 情感分类准确率 (人工抽检)| > 80% | 分析师盲测 100 条数据的标签 | < 65% |
| 8 | S3 趋势发现时效性 | < 72 小时 | 热点爆发到出卡片的时间差 | > 5 天 (热点凉了) |
| 9 | 竞品数据覆盖率 | > 85% | 与竞品官方页面发帖数对比 | < 70% |
| 10 | 报告生成耗时 | < 15 分钟 | Trigger 发起到 .md 落盘 | > 30 分钟 |
| 11 | API 响应时间 (95线) | < 1.5 秒 | Gateway 监控日志 | > 3 秒 |
| 12 | 向量检索响应时间 | < 3 秒 | DB 查询耗时 | > 8 秒 |
| 13 | LLM 交互成功率 | > 98% | OpenAI/Anthropic API 监控 | < 90% |
| 14 | Action 采纳率 (业务指标) | > 50% | `Approved` / 总 `Candidate` | < 20% (AI 变成人工智障) |
| 15 | 合规审查响应时长 | < 24 小时 | Takedown Request 处理闭环 | > 48 小时 (合规红线) |

---

## 第十一章：开发者交接说明

### 11.1 实现顺序建议

1. **库表搭建**: 先搞定 PostgreSQL 的 DIM 配置表和 DWD 宽表建表，定死 JSON 结构。
2. **基建打通**: 跑通第一个 Reddit (TikHub) 的 Connector 代码，确保数据能进库且无重复。
3. **模型链路**: 写 Prompt，走 LangChain/LangGraph 逻辑，吃死 DWD 数据，吐出格式化的 JSON (Insight)。
4. **状态机**: 实现 Action Board 的 CRUD 及 Approval Flow 接口。
5. **视图层**: 开发 Next.js 前端，联调 API。
6. **扩容**: 接入 TikTok、YouTube 等其他 Connector。
7. **周报**: 编写最后的汇总及 Markdown 拼装脚本。

### 11.2 最可能导致返工的三个决策

1. **爬虫供应商依赖**：千万不要把自己当成专业的爬虫团队。直接用 Apify/TikHub。如果花 2 周写了个 TikTok 爬虫，第 3 周规则改了全挂，会被业务方骂死。**必须容忍并处理 API 的 404/429 报错**。
2. **盲目迷信大模型**：直接把几万条文本塞给 LLM 叫它总结，一定会出现幻觉并且算力破产。必须先走 `SentenceTransformer` 等小模型做聚类 (Clustering) 或传统的 TF-IDF，把骨架抽出来，只把代表性句子丢给 LLM。
3. **忽略时区与重复写入**：社媒没有完美的 ID。帖子会被更新，评论会被删除。`provider + provider_item_id` 是唯一的抓手，必须用 Upsert/Merge 处理数据落地，否则数据量会虚高。

### 11.3 哪里要严格，哪里可以灵活

| 严格 (严禁魔改) | 灵活 (自行发挥) |
|---|---|
| **证据链 (`evidence_set_id`) 不能断**，每一句 Action 都得找到原帖。 | **前端界面样式**可以自己调整，用 Tailwind/Shadcn 怎么好看怎么来。 |
| **状态机流转**必须闭环，不能跳过 Review 直接把 Action 变成 Done。 | **队列引擎**用 Celery, RQ 还是 AWS SQS 都可以。 |
| **覆盖率警告 (`Coverage`)** 必须在最显眼处展示。 | **底层的向量库**用 pgvector, Chroma 还是 Milvus 皆可。 |

### 11.4 已知的未知项 (Unknowns)

1. Momcozy 社媒团队手头到底有没有官方开绿灯的 TikTok Commercial Content API 权限？如果没有，拿不到核心历史指标。
2. Facebook Groups 的法务合规底线到底是什么？（抓别人私密群里的抱怨，会不会在欧美引来集体诉讼？）
3. 内容团队执行一条 Action 的平均周期是几天？（这决定了 `Trend` 机会窗的超时阈值设为 3 天还是 7 天）。
4. 预算池深浅：每个月花在 OpenAI API Token 和 Apify Actor 上的美金预算是多少？
5. 翻译策略：抓取到的西班牙语/德语评论，是在 ETL 层统一翻译成英文入库，还是留给 LLM 在查询时动态应对？
6. 历史数据回溯：第一次启动系统时，要不要爬取过去一年的老数据做基线？（强烈建议只爬过去 30 天，历史太长没意义且费钱）。
7. KOL 数据库：公司现有的 CRM 里有没有网红黑名单？如果有，如何映射对齐（把 CRM 的邮箱映射为社媒的 @Handle）？

### 11.5 验收剧本 (Acceptance Scenarios)

1. **【日常抓取跑通】**: 启动调度器，查看 DuckDB 里是否新增了近 24 小时的 Reddit 提及，且主键没有重复。
2. **【虚空打靶阻断】**: 断网或强行停掉爬虫，强迫 Agent 生成周报，必须看到 Agent 在报告里大字标红警告 "本周数据抓取失败，无法出具结论"，而不是编造一套假话。
3. **【痛点转化为 Action】**: 在前端挑一个 Insight (比如 "M9 法兰尺寸偏小") -> 点击生成 Action -> 走完 Approve 流程 -> 状态落盘。
4. **【FTC 披露告警】**: 手工注入一条带 `#sponsored` 却夸赞 `Eufy` 的 @网红 视频数据 -> 系统必须在 S4 面板弹出红色告警 "检测到商业合作偏移"。
5. **【证据回溯】**: 打开系统生成的 Markdown 报告，点击任何一条结论旁边的 `[证据 1]`，必须能展示出对应的原帖链接或文本。
6. **【热点追踪衰退】**: 造一段虚拟数据，某 TikTok 标签前两日飙升，第三日降为 0 -> 系统必须判定其为 `Declining` 或 `Expired`，阻止跟进。
7. **【删除合规测试】**: 在系统后台发起请求 `Delete provider_item_id = X` -> 该数据在 DWD 中标记为 deleted，相关视图刷新后不再引用该数据。

### 11.6 研发自检命令

```bash
# 1. 检查 DWD 表的重复数据率 (应该为 0)
python check_duplicate_mentions.py

# 2. 检查大模型的 JSON 输出格式是否符合 Pydantic 约束
pytest tests/test_llm_json_parser.py

# 3. 运行端到端的 Agent Mock 测流
python run_agent_workflow.py --mock-data tests/fixtures/s1_mock.json
```

### 11.7 交付判断

以下清单**全部打钩**，P0 阶段方可验收上线：
- [ ] 爬虫脚本可以在无人干预下挂机跑 3 天，不崩溃，遇到 429 会自己睡觉重试。
- [ ] S1 到 S4 的洞察卡片都有且只有基于真实文本的归纳，没有 AI 的脑补。
- [ ] Action 看板的审批按钮能用，能存数据库。
- [ ] 每周周报模板 Markdown 格式生成正常。
- [ ] 所有代码经过了法务对 PII（个人身份信息）抓取的审核确认。

