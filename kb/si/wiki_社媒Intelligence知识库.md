---
name: si-wiki-social-intelligence
description: 社媒 Intelligence 知识库人类可读入口。综合 Phase A 深度研究成果（TikTok 算法/Reddit 社区/Creator 生态），是社媒 Analyst 和 SI Agent 的主要查阅入口。
---

# 社媒 Intelligence LLM 知识库

> 版本：v1.0 (Phase A) | 日期：2026-08-13
> 来源：Phase A 深度研究（9 路并行搜索 + 交叉审计验证），交叉验证
> 用途：Agent 按需检索 + 社媒 Analyst 方法论查阅

---

## 一、Agent 常驻原则（3 条，不可变）

1. **覆盖缺口诚实** — 抓不到 ≠ 没有，必须标注缺口类型和影响范围
2. **单一信号不放大** — 每条「用户普遍需求」结论须 N≥3 且跨 ≥2 来源
3. **母婴品类特殊** — 禁用疗效表述，FTC 披露必须，健康声明须 RCT 证据

→ 完整定义：`agent_system_prompt.md`

---

## 二、知识库索引

### 平台算法层（TikTok）

| 要回答的问题 | 查阅位置 |
|---|---|
| TikTok 算法最看重什么信号？ | claims.yml CLM-SI-TT-001 |
| 一个趋势还有没有参与价值？ | claims.yml CLM-SI-TT-002/003 + concepts.yml CONCEPT-TREND-LIFECYCLE |
| BGM/声音如何影响分发？ | claims.yml CLM-SI-TT-004 + concepts.yml CONCEPT-SOUND-VIRALITY |
| 内容如何做 TikTok 搜索优化？ | claims.yml CLM-SI-TT-005 + concepts.yml CONCEPT-SEARCH-VALUE-TIKTOK |
| 如何通过声量播种制造趋势？ | claims.yml CLM-SI-TT-006 |

**核心记忆点**：
- 完播率 + saves/shares 最强，likes 是弱信号
- 2025 末起：先测试自己 follower 池 → 再广泛推
- 趋势 5,000-20,000 视频数 = 最高杠杆窗口
- 商业账号只能用 CML，不能用普通音乐

---

### 社区洞察层（Reddit）

| 要回答的问题 | 查阅位置 |
|---|---|
| 如何区分真实痛点和噪音？ | sop/01_痛点信号识别.md + CLM-SI-RD-001 |
| 如何系统提取 Reddit 用户痛点？ | sop/01_痛点信号识别.md + CLM-SI-RD-002 |
| Reddit 能提前多久预警品牌风险？ | claims.yml CLM-SI-RD-003 |
| 如何在不被封号的情况下参与 Reddit？ | claims.yml CLM-SI-RD-004 |
| 哪类帖子信号最强？ | claims.yml CLM-SI-RD-005 |

**核心记忆点**：
- 40 条跨 3 子版块 = 信号；1 条 = 噪音
- 5 类帖子推荐请求最强
- 母婴社区反营销文化强，倾听为主
- Reddit 可提前数周预警品牌风险

---

### Creator 生态层

| 要回答的问题 | 查阅位置 |
|---|---|
| 各层 Creator 多少钱？互动率多少？ | CLM-SI-CR-001/002 |
| 如何判断 Creator 是否适合 Momcozy？ | CLM-SI-CR-003 + sop/03（Phase B，待写）|
| 如何识别假粉和 engagement pod？ | CLM-SI-CR-004 + concepts.yml CONCEPT-BRAND-SAFETY |
| FTC 披露要求是什么？ | CLM-SI-CR-005 + concepts.yml CONCEPT-FTC-DISCLOSURE |
| Nano 和 Micro Creator 有多高效？ | CLM-SI-CR-001 + CLM-SI-TT-006 |

**核心记忆点**：
- 母婴 Nano（1-10K）互动率最高（TikTok 5.5%），reach-efficiency 54.9x
- 孩子年龄匹配 > follower 数
- Bot>60% / pod>80% = 危险，不合作
- FTC：只 tag 品牌不算足够披露

---

### SOP 索引

| SOP | 适用场景 | 状态 |
|---|---|---|
| sop/01_痛点信号识别.md | S1 分析：从 Reddit 帖提取真实痛点 | ✅ Phase A |
| sop/02_覆盖缺口诚实表达.md | 所有模块：数据不完整时的表达规范 | ✅ Phase A |
| sop/03_Creator评估与合作判断.md | S4：评估 Creator 是否值得建联 | ⏳ Phase B |
| sop/04_趋势参与决策.md | S3：判断品牌是否应跟进趋势 | ⏳ Phase B |
| sop/05_竞品高表现内容拆解.md | S2：系统拆解竞品爆款 | ⏳ Phase C |
| sop/06_Social_Action转化.md | 所有模块：洞察转 Action 标准流程 | ⏳ Phase C |

---

## 三、知识库状态（Phase A 完成后）

| 层 | Phase A 完成 | Phase B/C 目标 |
|---|---|---|
| sources.yml | 28 个信源 | 50-60 |
| claims.yml | 15 条主张 | 40-50 |
| concepts.yml | 15 个概念 | 30-35 |
| sop/ | 2 个（P0） | 6 个 |
