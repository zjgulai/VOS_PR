---
name: momcozy-social-intelligence-agent-prd
description: Momcozy 社媒智能监测 AI Agent 产品需求文档，涵盖用户讨论洞察、竞品社媒动作、平台趋势、Creator 分析、证据链、数据采集、数据仓库、AI 分析和 Social Media Action。当产品、数据或研发团队需要设计和实施该系统时使用。
---

# Momcozy Social Intelligence Agent PRD

> 版本：v2.0
> 文档状态：待业务评审
> 文档日期：2026-08-12
> 目标团队：Momcozy 社媒团队、内容团队、Creator 合作团队、品牌与产品团队、数据与研发团队
> 研究口径：英文优先检索；平台能力以官方文档为准；无法确认的内容标记为「未验证」或「此处未解决」

## AI 速读卡

- 产品一句话：把跨平台公开社媒信号变成可追溯的母婴用户洞察、竞品判断、趋势机会和待审批行动。
- 核心循环：配置监测范围 → 采集 → 标准化与质量检查 → AI 分析 → 证据核验 → Action 审批 → 记录结果。
- 目标平台：Reddit、Facebook Groups、Instagram、Facebook Pages、YouTube、TikTok；接入按平台能力矩阵分阶段交付。
- 硬约束：不绕过登录、权限、验证码或平台限制；每条结论必须能回溯到来源和采集时间；AI 不直接对外发帖。
- 推荐默认：先用 Reddit、YouTube 和已授权的品牌自有账号验证闭环，Meta/TikTok 的外部监听采用批准或 licensed provider 连接器。
- 发挥空间：看板视觉、报告版式、模型供应商、队列和云厂商可以替换，但不能破坏数据契约和证据链。
- P0 验收：社媒分析师能配置一个监测任务，得到带来源证据的周报，并把一条建议转为可跟踪 Action。
- 最容易翻车：把 Research API 当作商业监听 API、把抓不到的数据写成零、把模型猜测写成事实、把私密群组当作可采集对象。
- 超预期机会：证据覆盖率、需求到内容机会图谱、Creator 合作时机卡、行动结果反哺模型。

## 第一章：产品概述

### 1.1 产品定位

Momcozy Social Intelligence Agent 是一款面向跨境母婴品牌的社媒情报与行动决策产品，让社媒团队能够持续发现用户需求、竞品动作、内容趋势和 Creator 机会，并在每个结论后看到证据与不确定性，而无需手工浏览多个平台、复制数据和拼接周报。

系统不等于一个“社媒内容爬虫”，也不等于一个只会生成摘要的聊天机器人。它必须完成五段闭环：

```text
监测范围
    |
    v
平台连接器与采集任务
    |
    v
标准化 Mention / Content / Creator / Metric Snapshot
    |
    v
话题、需求、情感、趋势、竞品动作、Creator 分析
    |
    v
Evidence-backed Insight
    |
    v
Social Media Action → 人工审批 → 执行结果 → 复盘反馈
```

### 1.2 业务目标与问题定义

#### 1.2.1 业务目标

| 目标 | 结果定义 | 首期衡量方式 |
|---|---|---|
| 缩短信息发现时间 | 分析师从“浏览平台”转为“审核已筛选证据” | 基线周与上线后周的人工监测工时对比 |
| 提高洞察可执行性 | 每个重要洞察都带建议动作、负责人角色、平台、时间窗和证据 | Action 完整率、采纳率、完成率 |
| 降低误判风险 | 区分采集事实、模型推断、人工判断和未知项 | 证据覆盖率、人工驳回率、抽检错误率 |
| 形成品牌知识资产 | 关键词、产品别名、话题、Creator、竞品动作和行动结果可积累 | 词典版本、洞察复用率、行动复盘数量 |
| 支撑 Momcozy 产品与内容协同 | 将用户痛点映射到内容机会、FAQ、产品反馈和 Creator brief | 洞察被内容团队采用的数量 |

#### 1.2.2 业务问题

| 问题 | 需要回答的问题 | 产出 |
|---|---|---|
| 用户讨论分散 | 用户最近在讨论什么、为什么讨论、哪里变热 | Social Listening Brief |
| 产品需求隐藏在评论中 | 用户的真实使用场景、疑问、痛点、正负面反馈是什么 | Need / Pain / Question Cards |
| 竞品动作不可比较 | 竞品在推广什么、用什么内容形式、哪些内容明显跑出基线 | Competitor Intelligence |
| 热点难以判断是否适合品牌 | 热度是真是假、是否与目标人群相关、何时参与、怎么切入 | Trend Opportunity Cards |
| Creator 只看粉丝数 | Creator 最近关注什么、受众回应什么、是否处于合适合作窗口 | Creator Intelligence Cards |
| 洞察不能落地 | 哪些话题值得回应、哪些内容值得做、谁负责、何时完成 | Social Action Board |

### 1.3 Momcozy 业务上下文

Momcozy 官网当前公开的业务分类包括 Pregnancy、Bras and Postpartum、Pumping、Feeding、On The Go、Baby Care 等，产品覆盖可穿戴吸奶器、哺乳文胸、喂养、奶瓶清洗与加热、婴儿车、婴儿背带、婴儿监视器等。官网的产品与 Support 页面还存在标准型号和 BP 别名映射，例如 M5 Smart 对应 BP380、M9 对应 BP223、W1 对应 BP420。来源 1、来源 2、来源 3。

这会直接影响产品设计：

1. 监测词典不能只保存一个产品名称，必须支持标准型号、内部编码、用户俗称、拼写变体和历史型号。
2. 用户讨论不应只按产品型号聚类，还要按使用场景聚类，例如工作、通勤、夜间、旅行、照顾宝宝时泵奶、清洁、法兰适配、舒适度、噪音、电量、溢漏和售后。
3. 话题解释必须避免把社媒意见变成医疗结论。涉及健康、安全、泌乳或婴儿护理的内容，只能输出“用户讨论信号”和“建议转交专业团队核验”，不能替代 IBCLC、医生或官方说明。
4. 社媒监听要服务全品类扩展，但首期围绕泵奶与哺乳场景建立可验证闭环，再扩展到 Baby Care、Feeding、On The Go 等品类。

### 1.4 三类用户画像

| 角色 | 核心目标 | 对现有工具最大的不满 | 愿意切换的功能 |
|---|---|---|---|
| 社媒分析师 | 每日发现重要话题，产出周报与风险提示 | 数据散落，手工复制链接，无法判断热度是否真实 | 点击洞察即可展开原文、时间、平台、样本量、模型置信度和证据链 |
| 内容与 Creator 负责人 | 找到可执行选题、内容形式和合作对象 | 竞品和热点信息无法转成 brief，Creator 只按粉丝量排序 | 一键生成带角度、平台、时间窗、风险和素材要求的 Action/brief |
| 品牌、产品与管理者 | 判断舆情、竞品和机会是否值得投入 | 看到了结论却不知道来源、数据完整度和建议依据 | “结论—证据—决策—结果”一体化摘要，支持审批和复盘 |

### 1.5 差异化对比表

以下对比是产品定位层面的差异，不代表对具体商业软件的采购级功能审计。

| 功能 | 常见社媒监听或 BI 工具 | 本产品 | 实现方式 |
|---|---|---|---|
| 结论可信度 | 常见为指标和摘要并列展示 | 每个 Insight 绑定 evidence_set、source_capability、sample_size、freshness 和 uncertainty | 证据服务与报告渲染强制关联 |
| 平台覆盖表达 | 容易把“支持平台”理解为全量覆盖 | 用连接器能力矩阵展示可采字段、权限、延迟、覆盖缺口和数据质量 | connector registry + coverage banner |
| 母婴需求理解 | 通用情感和话题标签 | 话题、场景、需求、痛点、疑问、信任风险和产品实体分层 | Momcozy ontology + 版本化标签 |
| 洞察到行动 | 生成报告后由人再整理任务 | Action 必须含动作类型、平台、内容角度、时间窗、负责人角色、风险和验收指标 | Action Engine + 人工审批状态机 |
| Creator 分析 | 以粉丝数、互动量或名单管理为主 | 结合内容方向变化、受众评论、商业披露、竞品合作和合作时机 | Creator timeline + timing score + brand safety review |
| 知识积累 | 报告是终点 | 执行结果、人工纠错和采纳情况反哺词典、规则与模型评估集 | feedback loop + annotation set |

### 1.6 可行性边界

| 在范围内及原因 | 明确排除在外及原因 |
|---|---|
| 采集公开内容、品牌自有账号数据、获得授权的 Page/Business 数据和 licensed provider 数据 | 绕过登录、验证码、访问控制、地区限制或平台反自动化机制 |
| Reddit 公开帖子、评论、Subreddit 上下文和允许使用的指标 | 把 Reddit 历史全量 firehose 当作默认能力；历史覆盖必须以实际授权和连接器说明为准 |
| YouTube 公开视频、频道、视频统计和公开评论线程 | 把 search.list 的结果总数当作精确市场规模；官方文档明确总数可能是近似值 |
| 已完成 Meta 审核和授权的自有 Page、Instagram Business 或 approved partner 数据 | 未经确认的 Facebook Groups 全量监听，尤其是私密群组和成员画像 |
| TikTok 官方 Commercial Content API、Business/approved provider 或经法务确认的数据合作 | 把 TikTok Research Tools 作为商业监听默认入口；官方页面将 Research Tools 限定为符合条件的非商业研究者 |
| 对视频做平台允许的字幕、voice-to-text、标题、描述、评论和元数据分析 | 未获授权下载、长期保存或再发布完整视频、音频、图片和用户个人资料 |
| Markdown、JSON、CSV 报告和内部 Action/brief | AI 自动代表 Momcozy 对外回复、发帖、投放广告或联系 Creator |
| P0 采用现有 Python、DuckDB/Parquet、FastAPI 方向做试点 | 在没有真实连接器、授权和数据质量验收前承诺企业级全平台实时覆盖 |

### 1.7 约束分层

| 硬约束 | 推荐默认 | 发挥空间 |
|---|---|---|
| 所有外部数据必须有 provider、source_url 或 provider_item_id、published_at、collected_at 和数据能力标签 | 先建立 Reddit、YouTube、品牌自有 Meta 数据和可人工导入数据的闭环 | 可用 Metabase、内置看板或现有项目的 Next.js 看板呈现 |
| 不采集私密群组、未授权账号和平台明确禁止的内容；AI 生成内容不自动对外发布 | 连接器采用统一接口，平台差异放在 adapter 内 | 队列可用 Redis、SQS、Pub/Sub 或现有任务调度器 |
| 重要结论必须引用至少一条证据，趋势和风险结论需要多条独立证据或标记低置信度 | 原文存在对象存储或本地原始归档，分析层只引用 evidence_id | LLM 可用已批准的 Kimi、DeepSeek、Claude、OpenAI 或云上模型 |
| 删除、下架和合规请求必须能按 provider_item_id 定位并清理 | 原始数据与派生数据分开，保留删除审计记录 | 归档周期和跨区域部署由法务与基础设施团队决定 |
| 采用统一时间、币种、语言、平台、实体和指标语义 | 时间统一 UTC，展示层按团队时区转换 | 标签名称可以中英双语，模型可按成本策略替换 |

### 1.8 研究边界与来源等级

本 PRD 不把搜索摘要当作平台事实。来源等级如下：

1. A 级：平台官方 API、开发者文档、Terms、官方产品页面和 Momcozy 官方页面。
2. B 级：云厂商官方参考架构、官方开源仓库和官方合规指南。
3. C 级：第三方工具或行业文章，只用于补充实现模式，不用于确认平台权限和法律结论。
4. D 级：搜索结果、论坛、未验证账号、推测性行业信息，只能作为待核验线索。

本轮已核查的关键来源：

| 编号 | 来源 | 用途 | 研究结论 |
|---|---|---|---|
| 来源 1 | https://momcozy.com/ | 品牌官网产品和业务分类 | 确认 Momcozy 多品类产品结构与自有社区、Support、IBCLC 等入口 |
| 来源 2 | https://momcozy.com/collections/wearable-breast-pump | 可穿戴吸奶器产品和使用场景 | 确认工作、出行、舒适度、噪音、电量、清洁、法兰等比较维度 |
| 来源 3 | https://support.momcozy.com/article/54801143113369 | 产品别名映射 | 确认标准型号与 BP 编码需要进入词典 |
| 来源 4 | https://www.reddit.com/dev/api/ | Reddit API 资源、搜索、Listing、评论 | 可作为连接器设计参考；实际商业使用还需检查当前 Data API 规则与授权 |
| 来源 5 | https://developers.google.com/youtube/v3/getting-started | YouTube API 认证、资源和配额 | 可采视频、频道、评论等公共资源；配额和字段需运行时监控 |
| 来源 6 | https://developers.google.com/youtube/v3/docs/search/list | YouTube 搜索参数 | 支持关键词、频道、时间、地区、语言和排序，但结果是搜索结果而非全量市场样本 |
| 来源 7 | https://developers.google.com/youtube/v3/docs/commentThreads/list | YouTube 评论线程 | 可以按视频或频道读取公开评论线程，并按时间或相关性排序 |
| 来源 8 | https://developers.tiktok.com/products/research-api | TikTok Research Tools 资格与数据范围 | 官方定位为符合条件的研究者，不能当作 Momcozy 商业监听默认入口 |
| 来源 9 | https://developers.tiktok.com/doc/research-api-faq | TikTok Research API FAQ | Research API 的资格、数据时效和统计滞后需要在产品中展示，不可假设实时 |
| 来源 10 | https://developers.tiktok.com/doc/research-api-specs-query-videos | TikTok 视频字段和查询条件 | 可参考字段模型；商用需采用符合资格的 Commercial Content API 或 licensed source |
| 来源 11 | https://www.ftc.gov/business-guidance/resources/disclosures-101-social-media-influencers | Creator 商业披露 | Creator 合作建议必须包含披露检查，不把赠品或付费关系当成无关信息 |
| 来源 12 | https://aws.amazon.com/solutions/guidance/social-media-data-pipeline-on-aws/ | 社媒数据管道架构 | 事件驱动、队列缓冲、统一格式、原始存储和节流处理是可复用模式 |
| 来源 13 | https://docs.langchain.com/oss/python/langgraph/persistence | Agent 持久化 | Checkpointer 适合任务状态、人工介入、恢复和审计 |
| 来源 14 | https://docs.langchain.com/oss/python/langgraph/interrupts | Agent 审批 | interrupt/resume 适合 Action 审批，不应直接让模型执行外部动作 |
| 来源 15 | https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/aggregations | 检索与聚合 | 关键词检索、语义检索和聚合可组合，适合证据探索 |
| 来源 16 | https://docs.getdbt.com/docs/build/incremental-models | 增量数仓 | unique_key、增量模型和 schema change 策略适合汇总层维护 |
| 来源 17 | https://docs.getdbt.com/docs/build/data-tests | 数据质量 | unique、not_null、accepted_values、relationships 和自定义 SQL 测试可作为验收基础 |

研究限制：Meta 官方文档在当前抓取环境返回 400，TikTok 部分商用接口页需要实际开发者账号权限，Reddit Data API 规则页返回 403。因此本 PRD 对 Meta、TikTok、Reddit 的权限结论采用“官方公开能力已知 + 目标账号和应用需现场复核”的表达，不把未能现场确认的端点写成已承诺能力。

## 第二章：整体布局与导航

### 2.1 产品信息架构

```text
Momcozy Social Intelligence
|
+-- 首页 Overview
|   +-- 今日重要信号
|   +-- 用户话题变化
|   +-- 竞品动作
|   +-- 趋势机会
|   +-- 待处理 Action
|
+-- 用户洞察 Social Listening
|   +-- 话题
|   +-- 需求与痛点
|   +-- 情感与风险
|   +-- 证据探索
|
+-- 竞品监控 Competitors
|   +-- 竞品账号
|   +-- 内容与 Campaign
|   +-- 高表现内容
|   +-- 差异化机会
|
+-- 趋势 Trend Radar
|   +-- Hashtag
|   +-- Audio / BGM
|   +-- 视频模板
|   +-- 母婴垂类趋势
|   +-- 可迁移创意
|
+-- Creator Intelligence
|   +-- 关注池
|   +-- 内容方向变化
|   +-- 受众反馈
|   +-- 合作机会
|
+-- Action Board
|   +-- 待审核
|   +-- 进行中
|   +-- 已完成
|   +-- 复盘
|
+-- Reports
|   +-- 日报
|   +-- 周报
|   +-- 月报
|   +-- 导出
|
+-- Admin
    +-- 监测范围
    +-- 连接器与授权
    +-- 词典与标签
    +-- 告警规则
    +-- 用户与权限
    +-- 数据质量
```

### 2.2 桌面端布局

```text
+--------------------------------------------------------------------------------+
| 顶栏 12%：Momcozy Social Intelligence | 数据日期 | 覆盖状态 | 通知 | 账号菜单 |
+-------------+------------------------------------------------------------------+
| 左侧导航    | 主内容区 78%                                                     |
| 20%         |                                                                  |
|             |  页面标题 + 时间范围 + 平台筛选 + 来源能力提示                  |
| Overview    |  +----------------+----------------+---------------------------+ |
| 用户洞察    |  | 重要信号        | 用户话题变化    | 竞品和趋势摘要          | |
| 竞品监控    |  +----------------+----------------+---------------------------+ |
| 趋势雷达    |  | 证据卡片列表：来源、发布时间、互动、标签、置信度、打开原文      | |
| Creator     |  +--------------------------------------------------------------+ |
| Action      |  | 主图表：话题量 / 情感 / 话题动量 / Creator 内容表现             | |
| Reports     |  +--------------------------------------------------------------+ |
| Admin       |  | 右侧抽屉：Insight 详情、证据链、生成 Action、人工反馈            | |
|             |                                                                  |
+-------------+------------------------------------------------------------------+
| 底部状态栏 10%：最近采集时间 | 成功率 | 缺口平台 | 当前报告生成状态                     |
+--------------------------------------------------------------------------------+
```

布局理由：社媒分析工作首先是判断优先级，而不是浏览所有内容。因此主界面先展示“重要信号”和数据覆盖状态，再进入证据卡片和原文；配置、报告和 Action 使用固定导航，避免把任务状态藏在聊天窗口里。

### 2.3 首次使用流程

```text
进入系统
  |
  +-- 已有监测范围 --> 进入 Overview，显示最近一次运行和覆盖状态
  |
  +-- 没有监测范围 --> 配置向导
                         |
                         +-- 选择 Momcozy 品类与产品词典
                         +-- 选择平台和数据源能力
                         +-- 添加竞品账号和 Creator 账号
                         +-- 选择 Subreddit / Group 监测范围
                         +-- 设置语言、地区、频率和告警
                         +-- 运行连接测试
                         +-- 创建首个分析任务
```

### 2.4 角色权限

| 角色 | 查看洞察 | 配置监测 | 审批 Action | 管理凭证 | 导出原文 |
|---|---:|---:|---:|---:|---:|
| Analyst | 是 | 是 | 是 | 否 | 受限 |
| Content Lead | 是 | 可编辑内容标签 | 是 | 否 | 受限 |
| Brand/Product | 是 | 否 | 可审批品牌风险 | 否 | 受限 |
| Admin | 是 | 是 | 是 | 是 | 按合规策略 |
| Viewer | 是 | 否 | 否 | 否 | 否 |

权限设计原则：凭证只保存 secret_ref，不在浏览器、报告或 LLM prompt 中显示；原文导出权限与普通洞察查看权限分离。

## 第三章：核心模块详细设计

### 第 3.1 节 监测范围与连接器管理

#### a) ASCII 图

```text
+----------------------------------------------------------------------------+
| 监测范围                                                                    |
| Momcozy 品牌词  已启用  |  Reddit 连接  已验证  |  YouTube 连接  部分成功    |
+------------------------+---------------------------------------------------+
| 监测对象              | 连接器能力卡                                      |
| 当前已配置：Momcozy、M5、M9、BP223                                          |
| 品牌：Momcozy          | Reddit：帖子、评论、Subreddit、互动指标            |
| 产品：M5, M9, BP223    | YouTube：视频、频道、评论线程、统计快照            |
| 话题：pumping at work  | Meta：自有账号已授权；外部监听待权限确认           |
| 竞品：待团队确认       | TikTok：Research 资格不适用于商业默认入口          |
| Creator：待团队导入    | 状态：可用 / 部分可用 / 待授权 / 已暂停             |
+------------------------+---------------------------------------------------+
| 操作：新增监测对象 | 测试连接 | 查看覆盖缺口 | 保存版本 | 停用          |
+----------------------------------------------------------------------------+
```

界面实现时，不能把“待团队确认”当成真实账号或占位数据；未配置项应显示为空状态和明确 CTA。

#### b) 交互流程

正常流程：

```text
管理员选择新增监测对象
  --> 选择对象类型：品牌 / 产品 / 话题 / 竞品 / Creator / 社区
  --> 输入标准名称、别名、语言、国家、排除词
  --> 系统预览匹配规则和可能误匹配
  --> 选择连接器和采集频率
  --> 测试连接
  --> 保存配置版本
  --> 调度器在下一周期使用新版本
```

失败流程一：连接凭证过期。

```text
测试连接
  --> provider 返回认证失败
  --> 状态变为待授权，隐藏原 token
  --> 展示重新授权入口和影响范围
  --> 不删除历史数据，不继续重试无效请求
```

失败流程二：平台能访问但字段不完整。

```text
测试连接
  --> 返回内容但缺少评论或互动字段
  --> 创建 coverage_gap 记录
  --> 连接器标记为部分可用
  --> 报告显示字段缺口，禁止把缺失值当作 0
```

失败流程三：监测词命中大量噪声。

```text
预览匹配
  --> 噪声样本比例超过配置阈值
  --> 提示添加上下文词或排除词
  --> 允许保存为观察任务，但默认不进入 Action 生成
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 草稿 | 新配置未保存 | 灰色 Draft | 保存或放弃 |
| 已启用 | 配置保存且连接测试通过 | 绿色 Enabled | 停用、授权失效或质量失败 |
| 部分可用 | 只能获取部分字段或覆盖有限 | 黄色 Partial | 字段恢复或人工确认继续使用 |
| 待授权 | 凭证缺失、过期或平台审核未通过 | 橙色 Action needed | 完成授权并测试通过 |
| 已暂停 | 管理员暂停或平台风险触发熔断 | 蓝色 Paused | 管理员恢复 |
| 质量异常 | 连续运行无数据、重复率异常或 schema 变化 | 红色 Quality issue | 修��连接器并通过回归样本 |

#### d) 依赖关系

```text
监测配置
  --> connector_registry
  --> keyword_dictionary
  --> collection_job
  --> provider_cursor
  --> coverage_report
```

读取：品牌实体、产品别名、排除词、平台账号、授权引用。写入：配置版本、连接测试、覆盖缺口、调度任务。该模块不直接写 Insight 和 Action。

#### e) 待决问题

1. Momcozy 生产环境是否已有可合法使用的 Meta、TikTok、Reddit 商业数据授权或 licensed provider 合同。
2. 首期是只服务美国英文市场，还是同时支持加拿大、英国、澳大利亚等英语市场。
3. 社媒团队是否允许 Analyst 手工导入 CSV、视频链接或平台导出文件作为补充数据源。

### 第 3.2 节 用户讨论与需求洞察 Social Listening

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| 用户洞察 过去 7 天 | Reddit 重点 | Facebook Groups 重点 | 其他平台辅助            |
+-------------------+----------------+-------------------+-------------------------+
| 讨论量              | 1,284           | 覆盖 6 个已授权范围   | 数据覆盖率 72%           |
| 上升话题            | 法兰适配、清洁、返工泵奶                                   |
| 负面风险            | 需人工核验的产品/服务话题 3 条                              |
+-------------------+----------------+-------------------+-------------------------+
| 话题卡：返工后如何维持泵奶节奏 ↑ 41%                                      |
| 需求：需要低打扰、易清洁、可在工作场景使用的解决方案                     |
| 证据：Reddit 帖子 8 条，YouTube 评论 12 条，跨平台独立作者 15 人           |
| 置信度：中 | 数据新鲜度：11 小时 | 打开证据 | 生成回应 Action              |
+--------------------------------------------------------------------------------+
| 左：话题树 | 中：情感与需求矩阵 | 右：证据抽屉、原文链接、人工标注         |
+--------------------------------------------------------------------------------+
```

#### b) 交互流程

正常流程：

```text
用户选择时间范围、平台、品牌或产品
  --> 系统读取 DWD mentions 和 metric snapshots
  --> 过滤低质量、重复和不具备证据的记录
  --> 话题聚类与需求标签分类
  --> 计算声量、作者数、互动、情感、变化率和数据覆盖
  --> 生成 Insight 卡片
  --> 分析师打开证据并确认、修改或驳回标签
  --> 确认后的 Insight 可生成回应或内容 Action
```

失败流程一：平台数据缺口。

```text
查询跨平台讨论
  --> Facebook Groups 或 TikTok 连接器无有效数据
  --> 页面显示覆盖缺口和影响范围
  --> 仍展示可用平台，但禁止显示“全平台总量”
  --> Insight 标记为部分覆盖
```

失败流程二：情感模型低置信度。

```text
模型分析
  --> 讽刺、缩写、图片文字或混合语言导致置信度低
  --> 该条内容进入人工复核队列
  --> 汇总指标使用“未判定”类别，不强行归为正面或负面
```

失败流程三：话题聚类不稳定。

```text
每日聚类
  --> 新旧聚类无法稳定匹配
  --> 保留 cluster lineage 和版本
  --> 报告说明“本周话题与上周不可直接比较”
  --> 分析师可合并、拆分或重命名话题
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 数据准备中 | 采集任务仍在运行 | 蓝色进度条 | 数据达到最低样本或任务结束 |
| 部分覆盖 | 至少一个重点连接器不可用 | 黄色 Coverage gap | 连接器恢复或人工确认报告 |
| 已聚类 | 话题与样本已生成 | 蓝色 Topic ready | 重新运行或人工修订 |
| 待核验 | 关键结论缺证据或低置信度 | 橙色 Review | 分析师确认或驳回 |
| 已确认 | 证据和标签通过人工审核 | 绿色 Verified | 进入报告或生成 Action |
| 已驳回 | 误匹配、重复、无关或证据不足 | 灰色 Rejected | 重新采集或加入排除规则 |
| 风险升级 | 负面传播速度、影响范围或安全词满足规则 | 红色 Escalated | 品牌负责人确认并创建处理任务 |

#### d) 依赖关系

```text
ODS raw items
  --> DWD canonical mentions
  --> NLP annotations
  --> topic clusters + need cards + risk signals
  --> evidence sets
  --> social listening insights
  --> action engine
```

读取：mention、comment、thread、metric snapshot、产品词典、历史基线。写入：topic cluster、need card、pain point、sentiment summary、risk signal、evidence set、人工标注。

#### e) 待决问题

1. 用户引语是否允许在内部报告中保存原文，还是只能保存短摘录和原文链接。
2. 社媒团队是否需要按国家、语言和产品线分别生成分析，或首期只做英语美国市场。
3. 风险话题是否需要与客服、质量或法务系统联动，还是只在 Action Board 中跟踪。

### 第 3.3 节 竞品社媒营销动作监控

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| 竞品监控 | 时间 30 天 | 平台 TikTok / Instagram / YouTube / Facebook | 对比视图 |
+--------------------------------------------------------------------------------+
| 竞品实体：eufy / Elvie / Willow / Spectra / Haakaa / BabyBuddha / 自定义       |
| 内容类型：新品 | Campaign | Creator | UGC | 教育 | 对比 | 促销 | 社区互动       |
+--------------------------------------------------------------------------------+
| 竞品内容流                                                                     |
| 08-08 竞品 A 公开视频   主题：工作场景   表现：相对账号基线 2.4x   查看证据      |
| 08-07 竞品 B Creator 合作 主题：舒适度     商业披露：已检测     查看关系图        |
| 08-05 竞品 C 新品内容     主题：清洁效率   数据：部分字段缺失   查看覆盖提示      |
+--------------------------------------------------------------------------------+
| 右侧：竞品传播重点矩阵 | 主题占比 | 内容形式 | 表现偏离 | Momcozy 可借鉴角度     |
+--------------------------------------------------------------------------------+
```

系统不能预置未经团队确认的竞品账号 handle。竞品名称、官方账号、地区账号和账号类型必须来自 Admin 配置，并保存来源和确认人。

#### b) 交互流程

正常流程：

```text
管理员配置竞品官方账号
  --> 连接器采集新内容和指标快照
  --> 抽取标题、描述、字幕、标签、音频 ID、内容类型和合作信号
  --> 计算账号内基线与同类内容基线
  --> 标记异常高表现内容
  --> 聚合竞品近期传播重点
  --> 生成“事实、可能原因、Momcozy 可借鉴点”三段式卡片
```

失败流程一：竞品账号不是真实官方账号。

```text
账号验证
  --> 账号名称相似但无法确认所有权
  --> 标记 source_identity_unverified
  --> 不纳入官方竞品表现比较
  --> 允许分析师手动确认或删除
```

失败流程二：账号互动指标不支持历史快照。

```text
指标刷新
  --> 只能获得当前累计值
  --> 不生成虚假的 24 小时增速
  --> 展示“仅有累计快照”
  --> 以两次真实采集快照计算后续变化
```

失败流程三：视频可见但字幕不可用。

```text
视频分析
  --> 没有公开字幕或平台不提供 transcript
  --> 只分析标题、描述、标签、评论和可用元数据
  --> 内容主题置信度下降
  --> 不声称已分析视频全部语义
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 已确认账号 | 官方身份由 Analyst 或 Admin 确认 | 绿色 Verified | 账号变更或人工撤销 |
| 待确认账号 | 新增但缺少身份证据 | 黄色 Unverified | 人工确认或移除 |
| 新内容 | 首次采集到的内容 | 蓝色 New | 完成分析 |
| 高表现候选 | 指标超过账号或内容类型基线 | 橙色 Outlier | 证据核验后成为高表现或误报 |
| 高表现已确认 | 指标快照满足规则且时间有效 | 绿色 Confirmed | 进入竞品报告 |
| 指标不可比 | 缺少粉丝、观看或历史快照 | 灰色 Incomparable | 采集到足够快照 |
| Campaign 候选 | 内容与其他内容在时间、标签、主题上形成集合 | 紫色 Campaign | 人工命名或拆分 |

#### d) 依赖关系

```text
competitor accounts
  --> content items + metric snapshots
  --> content taxonomy + campaign candidates
  --> outlier detection
  --> competitor focus summary
  --> differentiation opportunity
```

读取：竞品账号、内容、评论、指标快照、产品和主题词典。写入：内容分类、Campaign、Creator relationship、表现基线、对比机会。

#### e) 待决问题

1. 首期竞品池由社媒团队提供多少个品牌和多少个官方账号，是否包含地区账号。
2. “高表现”采用账号内基线、同类内容基线，还是外部行业基准；推荐默认采用前两者，外部基准作为后续补充。
3. 是否允许保存竞品视频缩略图或只保存平台链接、元数据和分析摘要。

### 第 3.4 节 社媒热点与内容趋势 Trend Radar

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| Trend Radar 过去 14 天 | TikTok | Instagram | YouTube | 母婴垂类 | 可迁移创意      |
+--------------------------------------------------------------------------------+
| 趋势名称：Pumping at Work                                                     |
| 热度：上升 | 讨论变化：+0.63 | 创作者广度：中 | 数据完整度：部分 | 窗口：7-14 天     |
| 代表内容：3 条 | 常见玩法：POV、day-in-the-life、问答 | 品牌相关度：高                |
| 建议：参与，但先做真实场景教育内容；风险：不得暗示所有人适用同一泵奶方案         |
| 证据：平台快照、公开视频、评论主题、历史基线 | 生成 Trend Action | 忽略该趋势       |
+--------------------------------------------------------------------------------+
| 左侧：趋势动量图 | 中部：内容模板卡 | 右侧：品牌适配评分与时间窗                 |
+--------------------------------------------------------------------------------+
```

趋势必须区分“平台热度事实”和“品牌是否适合参与”的判断。热度高不等于品牌相关度高，也不等于适合 Momcozy 复制。

#### b) 交互流程

正常流程：

```text
系统采集 Hashtag、Audio、视频、标签和时间快照
  --> 计算声量、参与作者数、互动率、跨平台出现次数和增速
  --> 聚类为趋势实体并与母婴 ontology 匹配
  --> 抽取常见内容结构和代表证据
  --> 评估品牌相关度、创作可行性、风险和参与窗口
  --> 生成 Trend Opportunity Card
  --> 用户选择跟进，转为 Trend Action
```

失败流程一：趋势数据只有单个平台一次快照。

```text
趋势识别
  --> 没有历史快照或平台统计延迟未知
  --> 只标记为“候选趋势”
  --> 不输出增长率和峰值预测
  --> 等待后续快照或人工补充证据
```

失败流程二：热门音频可见但品牌不能使用。

```text
Audio 分析
  --> 发现音频但商业使用权或地区适用性未知
  --> Action 禁止直接写“使用该 BGM”
  --> 改写为“参考剪辑节奏或内容结构”
  --> 由内容团队确认授权后再使用
```

失败流程三：跨行业趋势迁移会造成母婴语境不适。

```text
迁移评估
  --> 生活方式趋势与母婴产品关系弱或可能引发反感
  --> 品牌相关度降级
  --> 建议只观察，不生成内容 Action
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 候选趋势 | 单次或低覆盖信号出现 | 灰色 Candidate | 获得历史快照或被驳回 |
| 上升趋势 | 变化率和样本量达到阈值 | 绿色 Rising | 进入稳定、下降或数据失效 |
| 窗口临近 | 趋势仍上升且估计时间窗较短 | 橙色 Window closing | 生成 Action、过期或人工关闭 |
| 品牌适配高 | 受众、场景和内容形式匹配 | 紫色 Relevant | 审批、降级或过期 |
| 不建议参与 | 风险高、相关度低或商业权利未知 | 红色 Avoid | 重新评估或归档 |
| 已过期 | 趋势下降或时间窗结束 | 灰色 Expired | 保留历史用于复盘 |

#### d) 依赖关系

```text
platform trend snapshots
  --> trend entities
  --> momentum metrics
  --> content template extraction
  --> Momcozy relevance and safety assessment
  --> trend opportunity
  --> action board
```

#### e) 待决问题

1. TikTok、Instagram 的趋势数据是采购 licensed feed、使用平台商业产品，还是由团队定期导入 Creative Center 导出结果。
2. 是否需要把音频授权状态纳入内容审批系统；推荐默认必须纳入，否则 Action 不得直接建议复用音频。
3. 趋势窗口预测是仅输出规则化时间段，还是允许模型给出日期；推荐默认输出区间和依据，不输出无证据的精确峰值日期。

### 第 3.5 节 重点 Creator 内容分析

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| Creator Intelligence | 关注池 38 | 近期发布 124 | 方向变化 6 | 合作候选 9          |
+--------------------------------------------------------------------------------+
| Creator：由团队配置的账号名 | 平台 | 地区 | 内容定位 | 数据能力 | 最后采集时间       |
| 近期主题：泵奶场景 42% | 新手妈妈教育 26% | 工作与生活 18% | 其他 14%             |
| 高表现内容：标题/形式/表现相对个人基线/评论关注点/商业披露                         |
| 方向变化：从产品评测转向产后生活；证据：30 天与 90 天主题分布比较               |
| 合作时机：7.4/10 | 竞品合作：已检测但关系强度待人工确认 | 品牌安全：需复核             |
| 操作：查看时间线 | 标注定位 | 生成 Creator Brief | 加入 Action | 忽略               |
+--------------------------------------------------------------------------------+
```

Creator 画像不能把个人敏感信息、推测性身份或未公开受众数据写入系统。只分析公开的内容、商业披露、互动和账号元数据。

#### b) 交互流程

正常流程：

```text
管理员添加 Creator 公开账号
  --> 验证账号身份和平台
  --> 定期采集视频、标题、描述、字幕或公开转写、评论和指标快照
  --> 聚合 30 天、90 天内容主题与形式
  --> 检测高表现内容和方向变化
  --> 识别品牌、竞品、合作和商业披露信号
  --> 生成合作时机卡
  --> Analyst 审核后生成 Creator Brief 或 Action
```

失败流程一：内容只能拿到标题和指标。

```text
Creator 内容采集
  --> 没有字幕、评论或完整描述
  --> 画像明确标注分析范围
  --> 主题结论降置信度
  --> 不把“没有提及某品牌”解释为“没有合作”
```

失败流程二：商业披露不明确。

```text
商业信号检测
  --> 没有 #ad 或平台 disclosure，但出现产品赠送或品牌标签线索
  --> 标记“商业关系待确认”
  --> 合作建议必须交给人工和法务/品牌流程确认
```

失败流程三：Creator 方向变化来自发布频率变化而非真实转型。

```text
方向变化检测
  --> 近 30 天样本不足或发布频率异常
  --> 不输出“定位已改变”
  --> 输出“观察到主题占比变化，样本不足以确认转型”
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 待验证账号 | handle 已输入但身份未确认 | 黄色 Unverified | 人工确认或删除 |
| 已跟踪 | 账号身份和采集范围确认 | 绿色 Tracked | 暂停或失效 |
| 内容不足 | 时间窗内低于最低样本量 | 灰色 Sparse | 获得新内容或扩大窗口 |
| 方向变化候选 | 主题分布偏离历史基线 | 橙色 Shift candidate | 人工确认或降级 |
| 合作候选 | 匹配度、受众、时机达到阈值 | 紫色 Opportunity | 生成 brief、拒绝或过期 |
| 品牌安全复核 | 负面、争议或披露不明 | 红色 Review | 品牌负责人确认 |

#### d) 依赖关系

```text
creator registry
  --> creator posts + comments + metric snapshots
  --> topic and format timeline
  --> audience feedback
  --> brand and competitor relationship signals
  --> timing score + safety review
  --> creator brief / action
```

#### e) 待决问题

1. Creator 关注池由谁维护，是否需要 CRM、Affiliate 或 Creator 合同数据合并。
2. “合作空窗期”是否可使用内部合作记录；若不能，系统只能显示公开商业披露信号。
3. 是否需要按 Creator 地区、语言、内容垂类和受众生命周期建立人工标签。

### 第 3.6 节 Social Action Engine 与 Action Board

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| Social Action Board | 待审核 12 | 进行中 8 | 已完成 26 | 待复盘 5                  |
+--------------------------------------------------------------------------------+
| P1 话题回应 | 法兰尺寸选择内容 | Reddit + Blog | 截止 08-18 | 证据 14 条 | 审核 |
| P1 趋势跟进 | 工作场景泵奶 POV  | TikTok + IG   | 截止 08-20 | 证据 9 条  | 审核 |
| P2 内容借鉴 | 竞品清洁对比形式  | Shorts        | 截止 08-25 | 证据 6 条  | 审核 |
| P2 Creator  | 公开账号合作评估  | TikTok        | 截止 08-30 | 证据 11 条 | 审核 |
+--------------------------------------------------------------------------------+
| Action 详情                                                                      |
| 为什么现在做 | 依据哪些证据 | 具体做什么 | 谁负责 | 需要什么素材 | 风险与禁用说法     |
| 成功指标 | 执行状态 | 复盘结果 | 关联洞察 | 关联竞品/趋势/Creator                         |
+--------------------------------------------------------------------------------+
```

#### b) 交互流程

正常流程：

```text
四类分析模块产生 Insight
  --> Action Engine 根据规则和模板生成候选 Action
  --> 计算优先级、紧迫性、品牌相关度、证据完整度和风险
  --> Analyst 编辑标题、角度、平台、负责人和验收指标
  --> 品牌负责人审批
  --> 状态变为进行中
  --> 执行者补充内容链接、发布时间、结果指标
  --> 复盘并标记采纳、部分有效、无效或无法执行
```

失败流程一：证据不足。

```text
Action Engine
  --> 结论只有单条低置信度证据
  --> 生成“观察任务”而非“立即行动”
  --> Action 不能进入已审批状态
```

失败流程二：建议涉及健康、安全或法律风险。

```text
Action Engine
  --> 命中安全、医疗、婴儿护理或广告披露规则
  --> 自动加品牌/专业团队复核
  --> 禁止自动生成对外承诺和疗效性表述
```

失败流程三：行动时间窗已经过期。

```text
用户打开 Action
  --> trend_window_end 已过去
  --> Action 标记为过期
  --> 保留为历史洞察，不允许直接标记为已执行
  --> 用户可从历史证据创建新的常青内容 Action
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 候选 | 模型生成但未人工编辑 | 灰色 Candidate | 编辑、忽略或删除 |
| 待审核 | 信息完整且等待 Analyst/品牌负责人 | 橙色 Review | 批准或驳回 |
| 已批准 | 审核通过，允许执行 | 绿色 Approved | 开始执行、过期或取消 |
| 进行中 | 已创建内容或合作任务 | 蓝色 In progress | 补充结果或标记阻塞 |
| 已阻塞 | 缺素材、权限、预算或合作条件 | 红色 Blocked | 解决阻塞、取消或重规划 |
| 已完成 | 执行者提交结果 | 深绿色 Done | 进入复盘 |
| 已复盘 | 结果、偏差和学习已记录 | 紫色 Learned | 归档 |
| 已驳回 | 人工认为不适合或证据不足 | 灰色 Rejected | 新证据触发重建 |

#### d) 依赖关系

```text
social listening / competitor / trend / creator insights
  --> action_candidate
  --> human review
  --> action_execution
  --> action_result
  --> feedback and evaluation set
```

#### e) 待决问题

1. Action 是否需要同步到现有任务系统、飞书或 Slack；P0 先保存在系统并支持 Markdown 导出。
2. 内容执行结果由谁填写，是否能回接 TikTok、Instagram、YouTube 的自有账号数据。
3. 是否允许品牌负责人直接审批，还是必须经过 Analyst 先确认证据。

### 第 3.7 节 AI Agent 工作台与证据问答

#### a) ASCII 图

```text
+--------------------------------------------------------------------------------+
| Ask Momcozy Intelligence                                                       |
| 问：过去 14 天用户对 M9 在工作场景最常提到什么？                              |
+--------------------------------------------------------------------------------+
| Agent 回答区                                                                   |
| 结论 1：工作场景讨论集中在隐蔽性、噪音、充电和清洁。                         |
| 证据覆盖：Reddit 23 条、YouTube 评论 8 条；Meta 外部数据不可比。               |
| 不确定性：没有足够样本判断美国以外用户是否有同样需求。                         |
| 相关来源：source item 19、source item 31、topic cluster 2026-08-12-04           |
+--------------------------------------------------------------------------------+
| 可执行操作：展开证据 | 对比上周 | 生成用户回应 Action | 导出 Markdown | 反馈正确性 |
+--------------------------------------------------------------------------------+
```

#### b) 交互流程

```text
用户提出问题
  --> Agent 识别时间、平台、实体、分析任务和输出格式
  --> 调用检索、指标、证据、报告和 Action 工具
  --> 若范围不明确，展示解析后的查询条件
  --> 先返回事实和证据，再返回解释与建议
  --> 用户可继续追问、改时间范围或生成 Action
```

失败流程一：问题超出数据覆盖。

```text
用户问“全平台用户怎么看”
  --> Agent 检查 coverage_report
  --> 发现仅有 Reddit、YouTube 和自有账号数据
  --> 明确回答可覆盖范围，不伪造全平台结论
```

失败流程二：Agent 无法找到证据。

```text
用户问具体品牌危机
  --> 检索结果为空或全部低质量
  --> 返回“没有找到可验证证据”
  --> 提供扩大时间、平台或关键词的选项
```

失败流程三：用户要求 Agent 直接发帖。

```text
用户要求“马上去 Reddit 回复”
  --> Agent 拒绝自动对外执行
  --> 提供内部审核稿、依据和风险提示
  --> 用户必须在外部平台按现有审批流程执行
```

#### c) 状态清单

| 状态名称 | 触发条件 | 视觉标识 | 退出条件 |
|---|---|---|---|
| 解析中 | 正在识别查询范围 | 蓝色 | 形成 Query Plan |
| 需要确认范围 | 时间、平台或实体含义不明确 | 黄色 | 用户确认或系统采用默认范围 |
| 检索中 | 正在调用工具 | 蓝色进度 | 工具返回或超时 |
| 有证据回答 | 找到足够来源 | 绿色 | 用户继续追问或结束 |
| 部分证据 | 数据覆盖不完整 | 橙色 | 用户接受范围或调整查询 |
| 无证据 | 没有可验证结果 | 灰色 | 扩大查询或结束 |
| 需要人工复核 | 涉及风险或外部行动 | 红色 | 进入审批流程 |

#### d) 依赖关系

```text
user query
  --> query planner
  --> search tool / metric tool / evidence tool / action tool
  --> answer with citations and uncertainty
  --> optional action draft
```

#### e) 待决问题

1. 是否需要保留跨会话记忆；推荐默认只保留工作区偏好和已确认词典，不保留个人用户信息。
2. 是否允许用户通过自然语言修改监测配置；推荐默认自然语言只生成配置草稿，保存需人工确认。

## 第四章：超越竞品的差异化功能：

### 第 4.1 节 Evidence-first Action Chain

#### 1. 竞品为何未必具备这一能力

这是基于公开产品形态的推断，不是对具体厂商内部实现的事实判断。传统监听平台通常以数据搜索、指标和报告为主；任务系统通常以执行为主。两者由不同数据模型和团队维护，导致“为什么做这个 Action”常常需要人工复制链接。本产品将证据对象设计成 Insight 和 Action 的共同依赖，产品边界从“报告结束”延伸到“行动复盘”。

#### 2. 本产品如何实现

每条 Insight 必须包含 evidence_set_id。每个 Action 必须引用一个或多个 Insight。报告渲染器在没有 evidence_set 的情况下只能输出观察性提示，不能输出强行动语言。证据集包含原始来源、采集时间、平台、数据能力、内容摘录、指标快照、模型版本和人工审核记录。

推荐默认：先用关系表实现引用完整性，OpenSearch 只负责检索，不作为唯一事实存储。

#### 3. 交互流程

```text
原始内容
  --> 证据记录
  --> 话题 / 竞品 / 趋势 / Creator Insight
  --> Action 候选
  --> 人工审核
  --> 执行结果
  --> 复盘反馈
```

#### 4. 风险与应对

风险：来源内容被删除或链接失效。应对：保存允许保留的最小摘录、provider_item_id、采集时间和删除标记；不承诺永久复现原文。

### 第 4.2 节 Coverage-aware Intelligence

#### 1. 竞品为何未必具备此功能

这是基于公开行业架构的推断。平台连接权限、字段、时效和数据供应商经常不同，普通看板更容易把缺失值隐藏在聚合结果中。��产品把覆盖状态作为一级业务数据，避免把某个平台没有数据误解为用户没有讨论。

#### 2. 本产品如何实现

每次报告带 coverage_report：平台、连接器、数据类型、时间范围、成功率、缺失字段、是否可比较、最后成功采集时间和限制原因。指标查询必须返回 coverage_scope。汇总函数禁止将 null 转换为 0，除非字段契约明确说明零值有业务含义。

#### 3. 交互流程

```text
用户查看跨平台总览
  --> 系统先显示覆盖横幅
  --> 用户展开平台贡献和缺口
  --> 指标卡显示“可比范围”
  --> 生成报告时自动写入限制说明
```

#### 4. 风险与应对

风险：覆盖提示过多导致用户忽略。应对：只在结论受缺口影响时显示高优先级提示，普通技术日志进入数据质量页。

### 第 4.3 节 Demand-to-Content Opportunity Graph

#### 1. 竞品为何未必具备此功能

用户需求、内容资产、产品页面、客服 FAQ 和 Creator brief 通常分属不同系统，社媒工具不拥有内容生产闭环，内容工具也不保留社媒证据。这里的差异不是“模型更聪明”，而是数据对象之间的关系被显式建模。

#### 2. 本产品如何实现

建立如下关系：

```text
用户话题
  --> 需求 / 痛点 / 疑问
  --> 使用场景
  --> 可回答问题
  --> 内容角度
  --> 平台形式
  --> Creator 类型
  --> 产品页 / FAQ / 内容资产
  --> Action 结果
```

分析师可以从“法兰适配”跳转到证据、现有 FAQ、待创作内容和相关 Creator，而不是重新搜索。

#### 3. 交互流程

```text
确认用户需求卡
  --> 系统显示可回答问题和已有资产
  --> 用户选择内容平台与目标人群
  --> Agent 生成 brief 草稿
  --> 人工补充禁用表述和品牌要求
  --> 转为 Action
```

#### 4. 风险与应对

风险：模型把相关性误判成因果关系。应对：关系类型区分“证据支持”“模型推测”“人工确认”，报告不使用因果性语言，除非有业务验证。

### 第 4.4 节 Creator Timing and Brand Safety Card

#### 1. 竞品为何未必具备这一能力

Creator 发现工具往往优化搜索、粉丝和互动等静态筛选；品牌安全和合作时机则涉及近期内容方向、商业披露、竞品关系与品牌禁区，依赖时间序列和人工判断，不是单一排序分数能够覆盖。

#### 2. 本产品如何实现

合作时机分数只作为排序辅助，不作为自动选人。评分拆成内容匹配、受众场景、近期表现趋势、公开商业空窗、品牌安全、数据完整度六项，并展示每项证据和缺失项。Creator 合作建议必须经过人工审批。FTC 来源 11 要求对有金钱、赠品或其他物质关系的推荐进行清晰披露，产品将 disclosure_check 作为合作卡必填字段。

#### 3. 交互流程

```text
Creator 近期内容
  --> 主题与形式时间线
  --> 受众评论关注点
  --> 商业披露与品牌关系
  --> 时机与安全卡
  --> 人工确认
  --> Creator Brief
```

#### 4. 风险与应对

风险：公开信息不足造成误判。应对：显示数据完整度，允许输出“无法判断合作空窗”，不把缺失解释为没有合作。

## 第五章：数据模型

### 5.1 数据模型原则

1. 原始事实、派生分析和人工判断分开保存。
2. 所有跨平台 ID 作为字符串保存，不把平台雪花 ID强制转换成整数。
3. 时间字段同时保存 published_at、collected_at、metric_observed_at 和 valid_until，避免把当前累计指标误当成历史表现。
4. 每个派生结论保存 model_name、model_version、prompt_version、created_at 和 evidence_set_id。
5. 列表型关系使用子表或关系表实现；下面 JSON5 示例只展示单条记录，实际数据库不依赖一个超大 JSON 文档。

### 5.2 MonitorScope 数据契约

```json
{
  "version": "1.0", // 必填，契约版本
  "scope_id": "scope_momcozy_pumping_us", // 必填，工作区内唯一标识
  "workspace_id": "momcozy_social", // 必填，数据隔离边界
  "scope_type": "brand_product_topic", // 必填，brand、product、topic、competitor、creator 或 community
  "canonical_name": "Momcozy M9", // 必填，标准名称
  "aliases_text": "M9, BP223, Mobile Flow, Momcozy wearable pump", // 默认值为空字符串，逗号分隔别名
  "excluded_terms_text": "car seat, unrelated M9 model", // 默认值为空字符串，排除词
  "platforms_text": "reddit, youtube, instagram, facebook, tiktok", // 必填，目标平台
  "regions_text": "US", // 默认值为工作区地区，ISO 国家代码文本
  "languages_text": "en", // 默认值为 en，语言代码文本
  "status": "active", // 必填，draft、active、paused 或 retired
  "source_of_truth": "momcozy_support_article_54801143113369", // 必填，词典来源
  "created_at": "2026-08-12T00:00:00Z", // 必填，UTC 创建时间
  "updated_at": "2026-08-12T00:00:00Z" // 必填，UTC 更新时间
}
```

### 5.3 CanonicalMention 数据契约

```json
{
  "version": "1.0", // 必填，契约版本
  "mention_id": "reddit_t3_abc123", // 必填，平台与原始 ID 组成的稳定标识
  "provider": "reddit", // 必填，数据提供方
  "provider_item_id": "t3_abc123", // 必填，平台原始内容 ID
  "provider_item_type": "post", // 必填，post、comment、video、reel、story 或 thread
  "source_url": "https://www.reddit.com/r/example/comments/abc123", // 必填，原文地址
  "author_ref": "provider_scoped_author_hash", // 必填，脱敏或平台作用域作者引用
  "author_display_name": "masked_or_public_name", // 默认值为空字符串，按合规策略保存
  "community_ref": "r_example", // 默认值为空字符串，Subreddit、Group 或频道引用
  "text_excerpt": "short permitted excerpt", // 默认值为空字符串，允许保存的短摘录
  "media_ref": "provider_media_reference", // 默认值为空字符串，不代表本地保存完整媒体
  "language": "en", // 默认值为 und，ISO 语言代码
  "region": "US", // 默认值为 unknown，来源可验证的地区
  "published_at": "2026-08-11T15:00:00Z", // 必填，内容发布时间
  "collected_at": "2026-08-11T17:00:00Z", // 必填，采集时间
  "metrics_snapshot_ref": "metric_20260811_170000", // 默认值为空字符串，最近一次指标快照
  "content_hash": "sha256_normalized_text", // 必填，用于去重和删除定位
  "collection_strategy": "official_api", // 必填，official_api、authorized_export、licensed_provider 或 manual_import
  "coverage_grade": "A", // 必填，A、B、C、D 或 unknown
  "deletion_status": "active", // 必填，active、deleted、provider_unavailable 或 pending_delete
  "raw_object_ref": "object://raw/2026/08/11/reddit/abc123.json", // 必填，原始载荷引用
  "created_at": "2026-08-11T17:01:00Z", // 必填，系统入库时间
  "updated_at": "2026-08-11T17:01:00Z" // 必填，系统更新时间
}
```

### 5.4 Insight 数据契约

```json
{
  "version": "1.0", // 必填，契约版本
  "insight_id": "insight_2026_08_12_topic_004", // 必填，洞察唯一标识
  "insight_type": "user_need", // 必填，user_need、pain_point、competitor_action、trend 或 creator_signal
  "title": "工作场景中的低打扰泵奶需求", // 必填，面向业务用户的标题
  "summary": "公开讨论显示用户同时关注低打扰、充电和清洁，但跨平台覆盖不完整。", // 必填，事实优先摘要
  "fact_text": "用户在若干公开讨论中提及工作场景和低打扰需求。", // 默认值为空字符串，只写证据支持的事实
  "inference_text": "可能存在将隐蔽性与日常维护一起考虑的内容机会。", // 默认值为空字符串，模型推断必须单独标识
  "uncertainty_text": "Meta 外部公开数据未纳入本次比较。", // 默认值为空字符串，限制与未知
  "topic_key": "workday_pumping", // 必填，稳定主题键
  "entities_text": "Momcozy M9, wearable pump", // 默认值为空字符串，实体文本
  "sentiment_label": "mixed", // 必填，positive、negative、neutral、mixed 或 unknown
  "momentum_score": "0.63", // 默认值为 null，规则化趋势分数，不代表绝对热度
  "sample_size": "31", // 必填，参与该结论的内容数量
  "evidence_set_id": "evidence_set_2026_08_12_004", // 必填，证据集引用
  "data_coverage": "partial", // 必填，complete、partial、sparse 或 unknown
  "model_name": "approved_llm_provider", // 必填，模型供应商或本地模型名
  "model_version": "runtime_version", // 必填，模型版本
  "prompt_version": "insight_prompt_v3", // 必填，Prompt 版本
  "review_status": "pending_review", // 必填，pending_review、verified、rejected 或 expired
  "created_at": "2026-08-12T09:00:00Z", // 必填，生成时间
  "valid_until": "2026-08-19T09:00:00Z" // 默认值为空字符串，趋势类洞察有效期
}
```

### 5.5 SocialAction 数据契约

```json
{
  "version": "1.0", // 必填，契约版本
  "action_id": "action_2026_08_12_007", // 必填，Action 唯一标识
  "action_type": "topic_response", // 必填，topic_response、trend_followup、content_borrow、creator_collab 或 risk_response
  "title": "制作工作场景泵奶的真实使用指南", // 必填，动作标题
  "why_now": "相关讨论正在增加，且已有证据显示用户需要场景化答案。", // 必填，行动时机
  "platforms_text": "Instagram Reels, YouTube Shorts, Reddit response", // 必填，建议平台
  "audience_text": "returning_to_work_pumping_moms", // 必填，目标人群标签
  "content_angle": "用真实工作日场景解释如何规划设备、充电、清洁和隐私", // 必填，内容角度
  "required_assets_text": "approved product facts, fit guide, cleaning guide", // 默认值为空字符串，所需素材
  "owner_role": "social_content_lead", // 必填，负责角色而非个人账号
  "due_at": "2026-08-20T17:00:00Z", // 默认值为空字符串，截止时间
  "success_metric": "发布后 7 天保存率、评论中的问题解决率和有效点击", // 必填，验收指标
  "risk_text": "不得承诺统一效果，不得用医疗或绝对化表述。", // 必填，风险与禁用表述
  "source_insight_ids_text": "insight_2026_08_12_topic_004", // 必填，来源洞察
  "evidence_set_id": "evidence_set_2026_08_12_004", // 必填，证据集
  "approval_status": "pending", // 必填，pending、approved、rejected、blocked 或 expired
  "execution_status": "not_started", // 必填，not_started、in_progress、done 或 cancelled
  "reviewer_note": "", // 默认值为空字符串，人工审核记录
  "result_note": "", // 默认值为空字符串，执行复盘记录
  "created_at": "2026-08-12T09:10:00Z", // 必填，创建时间
  "updated_at": "2026-08-12T09:10:00Z" // 必填，更新时间
}
```

### 5.6 关系型数仓分层

#### 控制层

| 表 | 粒度 | 关键字段 |
|---|---|---|
| dim_monitor_scope | 一个监测对象版本 | scope_id、canonical_name、aliases、status、version |
| dim_platform_account | 一个平台账号 | platform_account_id、provider、handle、account_type、verification_status |
| dim_creator | 一个 Creator 规范实体 | creator_id、platform、public_handle、content_niche、region |
| dim_product_alias | 一个产品别名 | product_id、standard_model、alias、source_url、valid_from、valid_until |
| connector_registry | 一个连接器能力版本 | provider、strategy、fields_text、permission_status、last_tested_at |

#### 原始层 ODS

| 表 | 粒度 | 关键字段 |
|---|---|---|
| ods_provider_payload | 一次 provider 返回载荷 | job_id、provider、request_hash、raw_object_ref、received_at |
| ods_collection_job | 一次采集任务 | job_id、scope_id、cursor、status、request_count、error_code |
| ods_metric_snapshot | 一个内容在一个时间点的指标 | provider_item_id、observed_at、views、likes、comments、shares、followers |

#### 明细层 DWD

| 表 | 粒度 | 关键字段 |
|---|---|---|
| dwd_canonical_mention | 一条帖子、评论或视频内容 | mention_id、provider_item_id、text_excerpt、published_at、coverage_grade |
| dwd_annotation | 一个模型对一条内容的一组标注 | mention_id、annotation_type、label、confidence、model_version |
| dwd_evidence | 一个可引用证据 | evidence_id、mention_id、quote_text、source_url、observed_at、validity |
| dwd_creator_content | 一个 Creator 内容 | content_id、creator_id、format、topic_key、sponsored_signal |

#### 汇总层 DWS

| 表 | 粒度 | 关键字段 |
|---|---|---|
| dws_topic_daily | 日期、平台、话题 | stat_date、platform、topic_key、mention_count、author_count、sentiment |
| dws_competitor_content_daily | 日期、竞品、内容类型 | stat_date、competitor_id、content_type、content_count、outlier_count |
| dws_trend_snapshot | 趋势与时间快照 | trend_key、platform、observed_at、volume、creator_count、momentum |
| dws_creator_period | Creator 与分析周期 | creator_id、period_start、period_end、topic_mix、format_mix、performance |

#### 应用层 ADS

| 表 | 粒度 | 关键字段 |
|---|---|---|
| ads_insight | 一个业务洞察 | insight_id、insight_type、fact_text、inference_text、evidence_set_id |
| ads_action | 一个 Action | action_id、action_type、approval_status、execution_status、source_insight_ids |
| ads_report | 一份报告 | report_id、report_type、period、coverage_summary、render_ref |
| ads_feedback | 一条人工反馈 | feedback_id、object_type、object_id、label、reason、reviewer_role |

### 5.7 核心表 SQL 草案

以下是逻辑 DDL，实际数据库类型可以按项目现有 DuckDB 或生产仓库调整。

```sql
CREATE TABLE dwd_canonical_mention (
    mention_id VARCHAR PRIMARY KEY,
    provider VARCHAR NOT NULL,
    provider_item_id VARCHAR NOT NULL,
    provider_item_type VARCHAR NOT NULL,
    source_url VARCHAR,
    author_ref VARCHAR,
    community_ref VARCHAR,
    text_excerpt VARCHAR,
    language VARCHAR NOT NULL,
    region VARCHAR,
    published_at TIMESTAMP NOT NULL,
    collected_at TIMESTAMP NOT NULL,
    collection_strategy VARCHAR NOT NULL,
    coverage_grade VARCHAR NOT NULL,
    deletion_status VARCHAR NOT NULL,
    content_hash VARCHAR NOT NULL,
    raw_object_ref VARCHAR NOT NULL,
    UNIQUE(provider, provider_item_id)
);

CREATE TABLE dwd_evidence (
    evidence_id VARCHAR PRIMARY KEY,
    mention_id VARCHAR NOT NULL,
    evidence_type VARCHAR NOT NULL,
    quote_text VARCHAR,
    source_url VARCHAR,
    observed_at TIMESTAMP NOT NULL,
    valid_until TIMESTAMP,
    evidence_grade VARCHAR NOT NULL,
    redaction_status VARCHAR NOT NULL,
    FOREIGN KEY (mention_id) REFERENCES dwd_canonical_mention(mention_id)
);

CREATE TABLE ads_insight (
    insight_id VARCHAR PRIMARY KEY,
    insight_type VARCHAR NOT NULL,
    topic_key VARCHAR,
    title VARCHAR NOT NULL,
    fact_text VARCHAR NOT NULL,
    inference_text VARCHAR,
    uncertainty_text VARCHAR,
    sample_size INTEGER NOT NULL,
    evidence_set_id VARCHAR NOT NULL,
    data_coverage VARCHAR NOT NULL,
    model_version VARCHAR NOT NULL,
    review_status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE ads_action (
    action_id VARCHAR PRIMARY KEY,
    action_type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    content_angle VARCHAR NOT NULL,
    platforms_text VARCHAR NOT NULL,
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

### 5.8 数据质量规则

| 规则 | 检查 | 失败处理 |
|---|---|---|
| 主键唯一 | provider + provider_item_id 不重复 | 报错并进入去重队列 |
| 发布时间存在 | published_at 不为空且可解析 | 记录 invalid_timestamp，不进入趋势计算 |
| 采集时间存在 | collected_at 不为空 | 采集任务失败 |
| 指标语义 | 缺失指标为 null，不转为 0 | 报告显示 unavailable |
| 来源可追溯 | 原文链接、provider ID 或人工导入文件引用至少一个存在 | 禁止进入已验证 Insight |
| 词典可解释 | 话题、产品、竞品标签存在词典版本 | 进入待标注状态 |
| 数据新鲜度 | 当前报告范围内至少一个有效采集时间 | 显示数据过期横幅 |
| 删除同步 | provider item 被标记删除时，派生对象可定位 | 触发删除或重新生成摘要 |
| 模型版本 | annotation 和 insight 带版本 | 版本缺失不允许发布报告 |
| 增量主键 | 汇总模型有 unique key | dbt 或等价测试失败时阻止发布 |

### 5.9 数据保留与删除

| 数据 | 推荐默认 | 备注 |
|---|---|---|
| 原始 provider payload | 按合同和平台规则确定，初始 90 天 | 只为重放和审计服务，不展示给普通用户 |
| 标准化内容摘录与元数据 | 180 天滚动 | 保存最小必要信息和来源链接 |
| 汇总指标与主题趋势 | 24 个月 | 删除原文后仍需检查是否可保留派生统计 |
| Action 与复盘 | 36 个月 | 作为内部决策记录 |
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
| 负责话题、需求、情感、竞品、趋势、Creator、风险和 Action 候选                 |
+--------------------------------------------------------------------------------+
| 处理层：connector workers + queue + retry + DLQ + schema validation           |
| 负责节流、游标、幂等、原始归档、标准化和失败重试                               |
+--------------------------------------------------------------------------------+
| 数据层：对象存储 Parquet + DuckDB/warehouse + PostgreSQL control plane         |
| 负责原始、明细、汇总、应用、配置、审计和删除定位                               |
+--------------------------------------------------------------------------------+
| 外部层：Reddit / Meta / YouTube / TikTok / licensed provider / manual import  |
| 通过能力矩阵暴露权限、字段、延迟、成本和覆盖缺口                             |
+--------------------------------------------------------------------------------+
```

### 6.2 推荐部署路线

#### P0 试点

- 采集执行：Python connector worker，使用现有 `tools` 目录风格。
- 原始数据：本地或云对象存储中的按日期分区 JSON/Parquet。
- 分析存储：DuckDB 与现有 `data/warehouse` 方向兼容。
- API：沿用 FastAPI，提供配置、报告、证据和 Action 接口。
- Agent：LangGraph，使用持久化 checkpointer；开发环境可 SQLite，生产使用 PostgreSQL saver。
- 输出：Markdown、JSON、CSV。

#### 生产增强

- 控制面：PostgreSQL。
- 原始与分析明细：S3/GCS/Azure Blob + Parquet。
- 变换：dbt 或项目现有等价 SQL/Python pipeline，使用增量模型、unique key 和数据测试。
- 检索：OpenSearch，支持关键词、语义检索、过滤、聚合和 evidence drill-down。
- 任务：SQS/Pub/Sub/Redis Streams 任选其一，必须有 DLQ、游标、节流和重试。
- 可观测性：结构化日志、采集成功率、字段缺失率、队列积压、LLM 成本、报告失败率。

### 6.3 Agent 工作流

```text
START
  --> parse_request
  --> build_query_plan
  --> load_coverage
  --> retrieve_evidence
  --> validate_sample_and_freshness
  --> run_deterministic_metrics
  --> run_domain_classifiers
  --> synthesize_fact_and_inference
  --> evidence_gate
  --> human_review_if_needed
  --> render_report_or_action
  --> persist_feedback
  --> END
```

关键实现要求：

1. `retrieve_evidence`、`run_deterministic_metrics` 和 `evidence_gate` 不交给 LLM 自由决定结果，使用工具返回结构化数据。
2. `synthesize_fact_and_inference` 必须输出结构化字段，不接收无法定位来源的自由文本。
3. `evidence_gate` 在样本量、覆盖、时间窗、模型置信度或安全规则不满足时降级结论。
4. Action 审批使用 LangGraph interrupt/resume 或等价状态机。官方文档来源 13、来源 14显示 checkpointer 和 interrupt 可支撑恢复、人工介入和故障容错。
5. 每次运行保存 run_id、query_plan、tool_calls、model_version、prompt_version、evidence_ids 和最终状态，支持回放和审计。

### 6.4 连接器接口

```python
class SocialConnector:
    provider: str
    strategy: str

    def validate_access(self, config: dict) -> dict:
        """返回权限、字段、地区和错误信息，不写业务数据。"""

    def build_query(self, scope: dict, window: dict) -> dict:
        """把统一监测范围编译为平台查询。"""

    def collect(self, query: dict, cursor: str | None) -> dict:
        """返回原始载荷、下一游标、限流信息和覆盖信息。"""

    def normalize(self, raw_item: dict) -> dict:
        """返回 CanonicalMention，不执行模型推理。"""

    def collect_metrics(self, item_ids: str) -> dict:
        """返回时间点指标快照；不支持的字段返回 null。"""

    def delete_or_mark(self, provider_item_id: str) -> dict:
        """按平台规则删除或标记不可用。"""
```

连接器不可变约束：幂等、游标可恢复、原始载荷可审计、缺失字段不伪造、异常进入 DLQ、平台权限状态可见。

### 6.5 平台能力矩阵

| 平台 | 首期推荐策略 | 可采集对象 | 关键限制 | 业务承诺 |
|---|---|---|---|---|
| Reddit | 官方 API 与已批准账号 | Subreddit 帖子、评论、标题、作者作用域引用、互动指标 | 当前 Data API 规则、商业用途和限速需以账号实际条款为准 | P0 可验证 Reddit 重点社区，但不承诺历史全量 |
| YouTube | 官方 Data API v3 | 频道、视频、标题、描述、统计、公开评论线程、搜索结果 | search.list 有单独配额；搜索结果不是全量市场；字幕未必可得 | P0 可做竞品、Creator 和评论分析 |
| Instagram | 自有 Business/Creator 授权或 approved provider | 自有媒体、账号指标，外部公开内容取决于权限/供应商 | 外部 Hashtag、竞品和评论覆盖必须现场验证 | P1，能力逐字段展示 |
| Facebook Pages | 自有 Page 授权或 approved provider | 自有 Page 内容和指标；外部 Page 视权限 | Meta 权限、App Review 和字段变化 | P1，先接自有账号 |
| Facebook Groups | 只接合法授权、公开且明确允许的数据源 | Group 内容取决于权限与供应商 | 私密群组不采；官方 Graph 能力需现场验证 | P1/P2，重点是覆盖状态和人工导入降级 |
| TikTok | Commercial Content API、Business approved access 或 licensed provider | 商业内容、广告或 provider 允许的公开内容 | Research Tools 官方面向符合条件的非商业研究者；数据可能有延迟 | P1/P2，未经批准不承诺 organic 全量 |

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
| sentence-transformers 或等价 embedding 服务 | 语义聚类和相似证据 | 比纯关键词更能处理用户表达差异 | 未知 |
| Hugging Face Transformers 或云 NLP 服务 | 语言、情感、实体和分类 | 可替换模型，便于离线评估和成本分层 | 未知 |
| Secret Manager | 平台 token 和 provider key | 避免凭证进入代码和数据库 | 不适用 |

### 6.7 最大架构风险

最大风险不是 LLM 选型，而是外部平台数据权限与数据稳定性。工程可以写出连接器，但不能通过代码创造平台授权。缓解顺序：

1. 为每个平台建立 capability manifest，并在真实账号上运行连接测试。
2. 以 Reddit、YouTube、自有账号和人工导入建立可交付闭环。
3. Meta/TikTok 外部监听只在合同、官方批准或 licensed provider 明确可用时启用。
4. 把 provider 失败作为产品状态而非系统崩溃，报告中显示覆盖缺口。
5. 预留替换连接器，不让业务层依赖某个爬虫字段或供应商的私有结构。

### 6.8 可替换技术原则

推荐默认使用现有 Python、FastAPI、DuckDB/Parquet 和 PostgreSQL 控制面；如果项目已有 BigQuery、Snowflake、ClickHouse、Airflow、Dagster 或其他队列，可以替换。LangGraph 可替换为等价的有状态工作流引擎。OpenSearch 可替换为已有搜索引擎。

不可替换的是：CanonicalMention 字段语义、provider capability、幂等键、cursor、raw reference、evidence_set、coverage_report、Action 审批状态机、删除定位和模型版本记录。

## 第七章：交互细节

### 7.1 键盘快捷键

| 操作 | 快捷键 | 备注 |
|---|---|---|
| 打开全局搜索 | `/` | 聚焦证据、话题、Creator 和 Action 搜索框 |
| 返回首页 | `g` 后 `d` | 两键组合，避免覆盖输入 |
| 打开用户洞察 | `g` 后 `s` | Social Listening |
| 打开 Action Board | `g` 后 `a` | Action |
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

Action 卡片菜单：

```text
Action 右键
+-- 编辑行动角度
+-- 发送审核
+-- 标记阻塞
+-- 复制为新 Action
+-- 查看来源洞察
+-- 记录执行结果
+-- 归档
```

来源证据菜单：

```text
证据右键
+-- 打开平台原文
+-- 复制短摘录
+-- 隐藏个人显示名
+-- 标记错误匹配
+-- 请求删除核验
```

### 7.3 空状态

| 页面 | 用户看到什么 | CTA |
|---|---|---|
| Overview 无运行 | “还没有有效采集运行，先连接一个允许使用的数据源” | 创建监测范围 |
| Social Listening 无结果 | “当前范围内没有达到最低样本的讨论，可能是数据为空或关键词过窄” | 调整关键词或时间范围 |
| 竞品无账号 | “尚未配置并确认竞品官方账号” | 导入竞品账号 |
| Trend Radar 无趋势 | “没有足够历史快照判断增长，不输出趋势结论” | 查看采集状态 |
| Creator 无关注池 | “先添加公开 Creator 账号，不从模型自动猜测账号” | 添加 Creator |
| Action 无候选 | “当前没有通过证据门槛的行动建议” | 查看低置信度观察 |
| 报告生成中 | 显示运行阶段、已处理样本、失败平台 | 查看运行详情 |

### 7.4 错误状态

| 触发条件 | 用户可见提示信息 | 恢复操作 |
|---|---|---|
| 凭证过期 | “连接已失效，历史数据保留；请重新授权后恢复采集。” | 重新授权并测试连接 |
| 触发限速 | “平台暂时限制请求，系统已暂停该连接器，不会继续增加请求。” | 等待 reset 时间或调整频率 |
| schema 变化 | “返回字段发生变化，当前任务已进入质量保护；部分报告暂缓生成。” | 查看字段差异、更新 adapter、回放样本 |
| LLM 失败 | “分析模型未完成，已保留结构化指标；可稍后重跑摘要。” | 切换已批准模型或重试分析阶段 |
| 原文删除 | “平台内容已不可访问，保留来源 ID 与删除记录，不再显示原文。” | 查看删除审计或移除证据 |

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
| Markdown | 日报、周报、评审、内部分享 | 带来源、覆盖说明、生成版本 | P0 主交付格式 |
| JSON | API、二次分析、自动化消费 | schema version、evidence IDs、coverage | 机器可读，保留 null 语义 |
| CSV | 话题、内容、指标、Creator 列表 | 按当前筛选导出 | 不默认导出完整原文个人信息 |
| HTML | 浏览器预览与邮件附件 | 内嵌图表和来源 | P1，可由 Markdown 渲染 |
| PDF | 管理层归档 | 版式固定、带研究限制 | P2，不作为首期依赖 |
| Action brief | 内容与 Creator 团队执行 | 一条 Action 一个 brief | 可复制到任务系统 |

### 8.2 输出文件结构

```text
reports/
+-- social_intelligence/
|   +-- 2026-08-12_daily.md
|   +-- 2026-08-12_daily.json
|   +-- 2026-W33_weekly.md
|   +-- 2026-W33_weekly.json
|   +-- evidence_manifest.csv
|   +-- coverage_report.csv
|   +-- actions/
|       +-- action_2026_08_12_007.md
|       +-- action_2026_08_12_007.json
|
+-- run_logs/
    +-- run_20260812_090000.json
    +-- run_20260812_090000_errors.json
    +-- run_20260812_090000_metrics.json
```

### 8.3 Markdown 报告结构

```text
标题与周期
执行摘要
数据覆盖与限制
一、用户讨论与需求
二、竞品社媒动作
三、趋势与内容机会
四、Creator 动态
五、Social Media Actions
风险与待人工确认事项
来源清单
模型与规则版本
```

报告写作规则：

1. 先写“事实”，再写“判断”，最后写“建议”。
2. 任何数字后面都写统计窗口、样本量、平台范围和指标快照时间。
3. 如果数据覆盖不完整，标题使用“已覆盖范围内”，不写“全平台”。
4. 每条重大结论显示 evidence_set_id 或可点击的来源链接。
5. 不能引用真实用户姓名、联系方式或非必要个人信息。

### 8.4 批量处理流程

```text
采集任务集合
  |
  +--> Reddit connector --------+
  +--> YouTube connector -------+
  +--> Meta connector -----------+--> 并行写入 raw archive
  +--> TikTok/provider ----------+
  +--> manual import ------------+
                                  |
                                  v
                         标准化与幂等去重
                                  |
                     +------------+-------------+
                     |                          |
             可并行：语言、实��、情感、      必须顺序：视频字幕可用性
             规则分类、指标聚合               --> 内容主题与证据摘要
                     |                          |
                     +------------+-------------+
                                  v
                              evidence gate
                                  |
                     +------------+-------------+
                     |                          |
                  生成报告                  生成 Action 候选
                     |                          |
                     +------------+-------------+
                                  v
                         人工审核与持久化
```

## 第九章：开发优先级

按对用户行为的影响排序，而不是按工程难度排序。

| 等级 | 范围 | 交付标准 |
|---|---|---|
| P0 | 监测范围配置、连接器注册、Reddit 与 YouTube 基础采集、CanonicalMention、原始归档、基础话题/情感/证据、Markdown 周报、Action 草稿和人工审核 | 分析师可以完成一次真实采集、查看证据、生成周报并把一条建议转为待审核 Action；数据缺口可见 |
| P1 | Meta 自有账号授权、Facebook Groups 合法数据源接入、竞品内容基线、Creator 时间线、趋势快照、质量监控、Action Board 状态流 | 团队能够稳定使用周报、竞品和 Creator 页面，并对数据质量和行动状态进行管理 |
| P2 | TikTok 商业授权或 licensed provider、OpenSearch 语义证据检索、跨平台需求图谱、飞书/Slack 通知、HTML/PDF、模型离线评估 | 热点窗口、Creator 合作和用户需求可以在统一工作流内发现、审核、执行和复盘 |
| P3 | 反馈闭环训练集、内容 brief 模板库、预算/资源约束优化、实验对照、内容结果回流、跨市场多语言、API 供其他系统消费 | 系统能基于历史 Action 结果调整推荐，并支持品牌规模化运营决策 |

## 第十章：性能指标

| 指标名称 | 目标值 | 测量方法 | 劣化阈值 |
|---|---:|---|---:|
| 采集任务成功率 | 最近 24 小时成功任务占比不低于 95% | collection_job 按 provider、scope、时间窗口统计 | 低于 85% 连续 2 个周期 |
| Reddit 重点范围新内容延迟 | P95 不超过 4 小时 | published_at 到 collected_at 的差值 | P95 超过 8 小时 |
| YouTube 账号内容发现延迟 | P95 不超过 12 小时 | 频道发布时间与采集时间对比 | P95 超过 24 小时 |
| CanonicalMention 幂等率 | 重复写入占比低于 0.5% | provider + provider_item_id 唯一键冲突统计 | 超过 2% |
| 原始数据可追溯率 | 100% 记录有 raw_object_ref 或授权导入引用 | SQL 检查非空率 | 低于 99.5% |
| 已验证 Insight 证据覆盖率 | 100% 重大 Insight 有 evidence_set_id | ADS 与 DWD 关联检查 | 低于 100% |
| 话题聚类可复现性 | 同一输入和模型版本重复运行，主题映射一致率不低于 90% | 固定样本回放比较 cluster lineage | 低于 80% |
| 情感模型人工抽检准确率 | 英文样本不低于 80%，中文或混合语料单独统计 | 每周人工标注 200 条，计算 macro F1 | 任一主要类别低于 70% |
| 报告生成时间 | 10 万条已清洗内容的日汇总不超过 20 分钟 | 记录 workflow started_at 与 completed_at | 超过 40 分钟 |
| 单次证据搜索响应 | P95 不超过 2 秒，返回首屏 20 条 | API 端到端日志 | P95 超过 5 秒 |
| Action 草稿生成 | P95 不超过 30 秒 | Agent run 日志 | P95 超过 90 秒 |
| 报告导出 | 1 万条明细 CSV 不超过 2 分钟 | export job 日志 | 超过 5 分钟 |
| 队列积压 | 正常窗口未完成消息少于 1,000 条 | queue depth 每 5 分钟采集 | 超过 5,000 条持续 15 分钟 |
| LLM 单条 Insight 成本 | 通过批处理和缓存控制在预算阈值内，初始阈值由财务确认 | token usage 与成本表按报告统计 | 超过预算 150% |
| Action 人工驳回率 | 首月不高于 50%，持续下降 | review_status 统计并按原因分组 | 连续两周高于 70% |
| 数据删除响应 | 收到合法删除请求后 24 小时内完成标记和派生对象定位 | deletion audit log | 超过 48 小时 |

## 第十一章：开发者交接说明

### 11.1 实现顺序建议

你应先实现数据契约和一个可回放的离线样本闭环，再接真实平台。推荐顺序：

1. 建立 `dim_monitor_scope`、`dwd_canonical_mention`、`dwd_evidence`、`ads_insight` 和 `ads_action` 的 schema，以及固定 JSON/CSV fixture。
2. 实现 connector interface、幂等键、游标、raw archive、coverage report 和失败日志。
3. 先接 Reddit 和 YouTube，完成真实连接测试；不要先做未经批准的 Facebook Groups 或 TikTok 抓取。
4. 实现规则指标、基础分类、话题聚类和 evidence gate。先确保事实可回溯，再接 LLM 摘要。
5. 实现 Markdown 周报和证据抽屉，再实现 Action 草稿、审批和复盘。
6. 接入自有 Meta 账号后，增加竞品、Creator 和趋势模块；外部 Meta/TikTok 数据必须等待授权或 licensed provider 验证。
7. 最后再引入 OpenSearch 语义检索、跨平台图谱和结果反馈闭环。

### 11.2 最可能导致返工的三个决策

#### 决策一：外部平台数据源是否能合法稳定使用

- 决策是什么：Meta/TikTok/Facebook Groups 采用哪一种官方、approved partner、licensed provider 或人工导入路径。
- 安全默认选择：P0 只承诺 Reddit、YouTube、自有账号和人工导入；所有外部连接器通过 capability manifest 开关。
- 需要改变方向的信号：合同或平台审核确认了可用字段、地区、历史范围、刷新频率、保存期限和费用。

#### 决策二：数据仓库是沿用 DuckDB 还是直接上云数仓

- 决策是什么：试点和生产是否使用同一存储方案。
- 安全默认选择：P0 用 DuckDB/Parquet 保持与现有 VOC 项目兼容，控制面和审计预留 PostgreSQL；生产数据量或多人并发达到指标后迁移汇总层。
- 需要改变方向的信号：单日内容量、并发查询、保留期限或权限要求超过本地方案的验收阈值。

#### 决策三：AI 生成内容的自动化边界

- 决策是什么：Agent 能否直接回复用户、发布内容、联系 Creator 或发送 Campaign。
- 安全默认选择：Agent 只生成内部 Insight、Action 和 brief，所有外部行为必须由人和现有业务系统执行。
- 需要改变方向的信号：品牌、法务、平台授权和审计流程明确允许某一类自动动作，并且通过沙盒、限额和回滚验证。

### 11.3 哪里要严格，哪里可以灵活

| 章节 | 标记 | 你必须如何处理 |
|---|---|---|
| 产品概述 | 约束 | 保持从社媒信号到 Action 的闭环，不做只读数据墙 |
| 平台能力 | 约束 | 不绕过权限；缺失字段使用 null 和 coverage gap |
| 核心模块 | 约束 | 四类洞察和 Action 需要证据、时间窗、状态和人工反馈 |
| 数据模型 | 约束 | provider ID、时间、版本、evidence 和删除定位不能删 |
| Agent 工作流 | 约束 | 工具取数，模型解释；风险和外部动作必须 human-in-the-loop |
| 存储技术 | 建议 | 可以沿用现有 DuckDB，也可迁移 PostgreSQL、BigQuery、Snowflake 或其他仓库 |
| 搜索技术 | 建议 | OpenSearch 是推荐默认，已有搜索引擎可替换 |
| 前端布局 | 发挥空间 | 可以根据现有 Next.js 看板调整组件、颜色、图表和响应式布局 |
| 报告版式 | 发挥空间 | 可以优化视觉层级，但不可隐藏来源、范围、样本和不确定性 |
| 模型供应商 | 建议 | 使用已经过内部批准的模型，模型版本和 Prompt 版本必须记录 |

### 11.4 已知的未知项

1. 此处未解决：Momcozy 当前对 Reddit、Meta、TikTok 和数据供应商分别拥有哪些商业授权、合同和可用凭证。
2. 此处未解决：Facebook Groups 重点清单、是否为公开群组、是否允许数据导出，以及法务对保存内容摘录的要求。
3. 此处未解决：首期市场范围、语言范围、时区和周报接收人。
4. 此处未解决：竞品官方账号、Creator 关注池和内部 Creator 合作记录是否能提供。
5. 此处未解决：Action 是否需要接入飞书、Slack、Jira、Asana 或现有内容日历。
6. 此处未解决：平台数据供应商的收费、服务等级、历史回填范围和删除同步能力。
7. 此处未解决：社媒团队对“趋势适合参与”的业务评分标准，以及品牌禁用表述清单。

在这些信息确认前，你应使用本 PRD 的安全默认，不要以假账号、假授权或假数据继续开发。

### 11.5 验收剧本

验收剧本 1：在本地开发环境运行离线 fixture，加载 20 条 Reddit 帖子、10 条 YouTube 评论和 5 条人工导入记录，系统应生成唯一的 CanonicalMention、Evidence 和 coverage_report，并用 SQL 检查 provider 与 provider_item_id 没有重复。

验收剧本 2：在已配置有效授权的环境运行 Reddit 监测任务，选择一个已确认 Subreddit 和一个产品别名，任务应保存 raw payload、cursor、采集日志和标准化内容；断开网络后重启任务，应从上次 cursor 恢复或清晰记录失败原因。

验收剧本 3：在 YouTube 连接测试中查询一个已确认频道和时间范围，系统应显示视频、统计快照和公开评论线程；当评论关闭或字段不可用时，页面应显示 unavailable，而不是 0 或空白结论。

验收剧本 4：打开一条用户需求 Insight，依次查看事实、模型推断、不确定性、样本量、覆盖范围和至少两条来源证据；点击生成 Action，Action 应继承 insight_id 和 evidence_set_id，并默认处于待审核，不能直接变为已批准。

验收剧本 5：创建一条涉及 Creator 赠品或付费合作的 Action，系统应显示商业披露复核项、品牌安全复核项和负责人；未完成审批时不能生成“已执行”状态，也不能调用任何对外发帖或私信接口。

验收剧本 6：模拟一个连接器连续返回 401、429、字段变化和零数据四种错误，系统应分别记录授权失效、限速暂停、schema 质量异常和空结果状态，并在报告中展示对应覆盖缺口。

验收剧本 7：用同一份 fixture 和同一模型版本重复生成周报，事实、数字、evidence_id 和 Action 来源应一致；更换模型版本后，系统应生成新的 run_id 和模型版本记录，不覆盖旧报告。

### 11.6 研发自检命令

```bash
# 1. 文档结构检查
python3 /Users/lute/.agents/skills/qiaomu-ai-prd/scripts/lint_prd.py \
  /Users/lute/Project/voc-data-product/VR/PRD-Momcozy-Social-Intelligence-Agent.md

# 2. 搜索产品文档中的待确认项和未验证边界
rg -n "此处未解决|未验证|待授权|coverage|evidence|删除|Action" \
  /Users/lute/Project/voc-data-product/VR/PRD-Momcozy-Social-Intelligence-Agent.md

# 3. 若实现了 Python 连接器，运行项目已有测试与类型检查
python3 -m compileall tools app

# 4. 对 fixture 运行唯一键、来源、时间和缺失值检查
python3 tools/validate_voc_dataset.py
```

### 11.7 交付判断

当且仅当以下条件全部满足，才可以把产品标记为首期完成：

- 至少一个真实获准连接器和一个离线 fixture 连接器通过同一套 CanonicalMention 测试。
- 所有报告的数字都能追溯到 DWS 查询和 evidence_set。
- 平台缺口、字段缺失、限速、删除和模型失败都有可见状态。
- Action 有人工审核、执行状态和复盘字段。
- 不存在自动绕过平台权限、自动对外发帖或未经确认的 Creator 联系流程。
- 运行 `lint_prd.py` 通过，研发验收剧本有日志、导出文件或截图证据。

### 11.8 研究交付说明

本次深度研究使用了 Momcozy 官方站点、Momcozy Support、Reddit API 文档、YouTube Data API 官方文档、TikTok for Developers、FTC 官方 Creator 披露指南、AWS 官方社媒数据管道指导、LangGraph 官方文档、OpenSearch 官方文档和 dbt 官方文档。搜索工具 `opencli` 在当前工作环境不可用，因此没有把任何本地 OpenCLI 适配器或第三方爬虫能力写成已验证事实。Meta 官方文档在当前抓取环境不可直接读取，相关结论已保留为授权和现场复核条件。

### 11.9 复盘后的下一步

下一步不是立刻开发六个平台的抓取器，而是由社媒、法务、数据和研发共同完成一页“平台接入确认表”：每个平台列出授权类型、可采字段、历史范围、刷新频率、保存期限、删除机制、供应商费用和责任人。确认表通过后，从 Reddit 与 YouTube 的真实数据样本开始 P0 验收；未通过的平台保持待授权状态，不影响已验证链路交付。
