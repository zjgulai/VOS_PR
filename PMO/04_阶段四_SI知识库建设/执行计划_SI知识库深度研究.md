---
name: si-knowledge-base-execution-plan
description: kb/si 社媒 Intelligence 知识库深度研究执行计划。对标 kb/pr 完整架构，覆盖 6 平台 × 4 业务模块 × 3 生态系统。Grilling Q1-Q5 设计决策全部锁定后开始执行。
---

# SI 知识库深度研究执行计划

> 版本：v1.0 | 日期：2026-08-13
> 核心目标：为社媒 Intelligence Agent 构建结构化、可调用、有证据等级的知识库，覆盖 6 平台 × 4 业务模块 × 3 生态系统。
> 质量标准：每条 claim ≥2 独立来源（L1），单一来源标注 L2 待核实，每个 SOP 倒推核心场景+未被满足的需求。

---

## 一、设计决策记录（Grilling Q1-Q5 全部锁定）

| 决策 | 结论 |
|---|---|
| Q1 使用者 | 两者兼顾，Agent 可调用优先 |
| Q2 SI 独有维度 | 5 个：平台算法 / Creator 生态 / 趋势识别 / 社区洞察 / 竞品内容情报 |
| Q3 SOP P0 | A 痛点信号识别 + E 覆盖缺口诚实（倒推核心场景 + 未满足需求） |
| Q4 研究包优先级 | P0：① TikTok 机制 + ② Reddit 社区 + ④ Creator 生态 |
| Q5 Agent 常驻原则 | A 覆盖缺口 + B 单一信号不放大 + F 母婴品类特殊性 |

---

## 二、目录架构（对标 kb/pr）

```
kb/si/
├── wiki_社媒Intelligence知识库.md          ← 人类可读入口
├── agent_system_prompt.md                 ← 3 条常驻原则 + 品牌占位
├── knowledge-system/                      ← 结构化知识层（Kb2Agent 格式）
│   ├── sources.yml     目标 50-60 个信源
│   ├── claims.yml      目标 40-50 条主张
│   ├── concepts.yml    目标 30-35 个概念
│   └── acceptance.yml  SOP 验收契约
├── sop/                                   ← 6 个可执行 SOP
│   ├── 01_痛点信号识别.md                   ← Phase A P0
│   ├── 02_覆盖缺口诚实表达.md              ← Phase A P0
│   ├── 03_Creator评估与合作判断.md         ← Phase B
│   ├── 04_趋势参与决策.md                  ← Phase B
│   ├── 05_竞品高表现内容拆解.md            ← Phase C
│   └── 06_Social_Action转化.md            ← Phase C
├── out_search/                            ← 外部知识库文章（待填充）
└── inner_worklog/                         ← 社媒团队工作日志（待业务提供）
```

---

## 三、阶段拆分与研究包

### Phase A：P0 研究包（立即启动）

**研究包 1：TikTok 算法机制与趋势传播路径**
- Why P0：TikTok 是 S3 趋势 + S2 竞品核心平台；无算法 claims 则趋势判断全是猜测
- 研究问题：
  1. FYP 算法的 6 大核心因子（完播率/互动率/关注关系/设备信号/账号设置/视频信息）各自权重？
  2. 趋势如何从 niche（<10K 播放）扩散到主流（>1M）？时间窗口多久？
  3. BGM 如何驱动内容传播？母婴类 BGM 的生命周期特征？
  4. 什么信号预示趋势升温（Hashtag 增速/Creator 参与数/播放增长率）？
  5. 母婴品牌参与趋势的最佳时机（niche 末期 vs 主流初期）？
- 目标产出：10-12 个 sources + 8-10 条 claims + 5-6 个 concepts

**研究包 2：Reddit 母婴社区行为与信号提取**
- Why P0：Reddit 是 S1 用户讨论最高质量来源，v3 PRD 明确标为重点
- 研究问题：
  1. r/breastfeeding / r/NewParents / r/beyondthebump 的社区规范（禁止商业推广/医疗建议风险/真实性要求）？
  2. 高质量信号特征（帖子长度/评论数/Upvote 比/OP 参与度）？
  3. 噪音识别标准（水军特征/品牌水军/竞品黑稿/单一负面情绪放大）？
  4. 痛点 vs 抱怨的区分框架（频次/严重性/可解决性/影响范围）？
  5. Reddit Data API 官方限制与 Apify 抓取合规边界？
- 目标产出：8-10 个 sources + 10-12 条 claims + 6-8 个 concepts

**研究包 3：母婴垂类 Creator 生态深度图谱**
- Why P0：Creator 生态是 S4 的全部，且直接影响 Action Engine 的合作建议质量
- 研究问题：
  1. TikTok/IG/YouTube 母婴 Creator 分层标准（Nano/Micro/Mid/Macro）？
  2. 各层级受众特征、内容类型、商业合作模式差异？
  3. 母婴 Creator 的商业披露识别（#ad/#sponsored/#partnership/无披露风险）？
  4. 红黑名单机制：什么信号标记 Creator 为高风险？
  5. 合作时机判断框架（Content 方向变化/受众增长阶段/竞品合作空窗）？
- 目标产出：10-12 个 sources + 12-15 条 claims + 8-10 个 concepts

### Phase B：P1 研究包

**研究包 4：Facebook Groups 母婴社群运营生态**
- 公开群 vs 私密群数据可及性 / 群主生态 / Apify Groups 合规边界

**研究包 5：社媒竞品内容情报方法论**
- 竞品爆款拆解框架（BGM/脚本/视觉/钩子/CTA）/ 高表现内容共同特征

**研究包 6：社媒效果测量与 ROI 框架**
- Social Listening KPI / 趋势参与时效测量 / Creator 合作 ROI / 覆盖率标准

### Phase C：P2 SOP 补充

- SOP 05：竞品高表现内容拆解
- SOP 06：Social Action 转化

---

## 四、Phase A 执行 TODO

| # | 任务 | 输入 | 输出 | 状态 |
|---|------|------|------|------|
| A1 | 创建 kb/si 目录结构 | — | kb/si/{knowledge-system,sop,out_search,inner_worklog} | ✅ 已完成 |
| A2 | 并行搜索（3 研究包 × 2-3 查询） | 6-9 个搜索查询 | 搜索结果 | 待执行 |
| A3 | 交叉审计（≥2 独立来源=L1，单一=L2） | 搜索结果 | 验证后的信源清单 | 待执行 |
| A4 | 写 sources.yml（28-32 个信源） | 验证信源 | kb/si/knowledge-system/sources.yml | 待执行 |
| A5 | 写 claims.yml（28-32 条主张） | 验证信源 | kb/si/knowledge-system/claims.yml | 待执行 |
| A6 | 写 concepts.yml（19-24 个概念） | 验证信源 | kb/si/knowledge-system/concepts.yml | 待执行 |
| A7 | 写 SOP 01：痛点信号识别 | 研究结果 + 场景倒推 | kb/si/sop/01_痛点信号识别.md | 待执行 |
| A8 | 写 SOP 02：覆盖缺口诚实表达 | 研究结果 + 场景倒推 | kb/si/sop/02_覆盖缺口诚实表达.md | 待执行 |
| A9 | 写 acceptance.yml（2 条 SOP 验收契约） | SOP 01+02 | kb/si/knowledge-system/acceptance.yml | 待执行 |
| A10 | 写 agent_system_prompt.md（3 条常驻原则） | Q5 决策 | kb/si/agent_system_prompt.md | 待执行 |
| A11 | 写 wiki_社媒Intelligence知识库.md | 全部 Phase A 产出 | kb/si/wiki_社媒Intelligence知识库.md | 待执行 |
| A12 | 更新 PMO 社媒团队 Excel | 新增 Creator 红黑名单/缺口标注等配置 sheet | PMO/业务协作_社媒团队/社媒团队协作表.xlsx | 待执行 |
| A13 | commit + push Phase A | 全部 A1-A12 | git commit | 待执行 |

---

## 五、完成目标（Phase A 后）

| 层 | Phase A 目标 |
|---|---|
| sources.yml | 28-32 个（TikTok/Reddit/Creator 专项） |
| claims.yml | 28-32 条（含交叉审计标注） |
| concepts.yml | 19-24 个（含 5 个 SI 独有核心概念） |
| sop/ | 2 个 P0 SOP |
| acceptance.yml | 2 条 SOP 验收契约 |

---

*Phase B + C 的详细 TODO 在 Phase A 完成后再拆解。*
