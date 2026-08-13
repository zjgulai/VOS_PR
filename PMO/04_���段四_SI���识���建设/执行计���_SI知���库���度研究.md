---
name: si-knowledge-base-execution-plan
description: kb/si 社媒 Intelligence 知识库深���研���执行计划���对标 kb/pr 完整架构���
stage: 04_阶段四_SI知识库建���
status: ready-to-execute
created: 2026-08-13
---

# SI 知���库深度研���执行计���

> **核���目标**：为���媒 Intelligence Agent 构建���构化、���调���、有���据等级的知识库���覆盖 6 ���台 × 4 业务模��� × 3 生���系统。
> **质量���准**���每条 claim ≥2 独立来���（L1），���源标注��� L2 待核���，���个 SOP 倒推核���场景+���满���需���。
> **设���决策**���优先 Agent 可调���，兼顾人类可读���SI ���有 5 维度全���盖；P0 SOP = ���点识别 + 覆盖缺口���实；P0 ���究 = TikTok 机制 + Reddit ���区 + Creator 生态���

---

## 一、设计���策���录（Grilling 结论）

| 决策 ID | ���题 | 结论 | 影��� |
|---|---|---|---|
| Q1 | 知���库首要使用��� | 两者兼顾，Agent 可调用���先 | knowledge-system/ 采��� Kb2Agent ���式（sources/claims/concepts/acceptance���，sop/ ���人���可读步骤，wiki 作入��� |
| Q2 | SI vs PR 差异���度 | 5 个���有维���全覆盖 | 研究包���须涵盖：平台算法/Creator 生态/���势���别/社区���察/竞品内容情报 |
| Q3 | SOP ���先级 | P0 = A ���点���号识别 + E 覆盖缺口诚实（倒���场景+需求） | Phase A 必须���两个 SOP���其他 4 ���（Creator 评估/���势参与/���品拆解/Action 转化）分 Phase B/C |
| Q4 | 研���包优先级 | P0 = ① TikTok 机制 + ② Reddit 社区 + ④ Creator 生态 | Phase A ���个研究���；③ FB Groups/⑤ ���品方法论/⑥ ���果测��� 延后 Phase B/C |
| Q5 | Agent 常驻原则 | A 覆���缺��� + B 单���信号不放大 + F 母婴品���特殊性 | agent_system_prompt.md 写 3 条固有原则���其他知识按需检索 |

---

## 二、目录架构（对标 kb/pr���

```
kb/si/
├���─ wiki_社媒Intelligence���识库.md          ← 人类���读入口���对标 kb/pr/wiki）
├─��� agent_system_prompt.md                 ��� 3 条常驻原则 + ���牌占位
├── knowledge-system/                      ← 结构���知识���（Kb2Agent 格式）
│   ├── sources.yml       目标 50-60 信源
│   ├── claims.yml        目标 40-50 条主张
���   ├─��� concepts.yml      ���标 30-35 个概���
│   └── acceptance.yml    SOP ���收���约
├── sop/                                   ← 可���行 SOP
���   ├���─ 01_痛���信号识别.md                  ← Phase A P0
│   ├── 02_覆盖缺���诚实表达.md              ← Phase A P0
│   ├─��� 03_Creator评���与合作���断.md         ← Phase B
│   ├─��� 04_趋势���与决策.md                  ← Phase B
│   ├── 05_竞品高表现���容拆解.md            ← Phase C
│   └���─ 06_Social_Action转化.md            ← Phase C
├���─ out_search/                            ← 原���知识库（���填充或���入）
└���─ inner_worklog/                         ← 社���团���工作日志���待业务���供）
```

---

## 三、阶段拆分与执行顺���

### Phase A：P0 研究包 + P0 SOP（立���启���）

**���究��� 1：TikTok ���法机制���趋���传播���径**
- **Why P0**：TikTok 是 S3 趋势 + S2 竞品核心平台；v3 PRD 明确点名「趋势判断」是核心���力；���有���法 claims 则 agent 全是猜���
- **研究问题**：
  1. TikTok FYP ���法的 6 大核���因子（���播���/互动���/关���关系/设���信���/账号���置/视���信息）各占权重���
  2. 趋势如何从 niche���<10K 播放）扩散到���流（>1M）？时间窗���多久？
  3. BGM 如何驱动内���传播���母婴���类 BGM 的���命周期特征？
  4. ���么信号���示趋势���温���Hashtag 增速/Creator 参���数/播放���长率）���
  5. 母婴���牌���与趋势的最佳时机���什么（niche 末期 vs 主流初期）���
- **期望输出**���
  - 10-12 个 sources（TikTok Creator Portal / Hootsuite 2026 / Influencer Marketing Hub / Social Insider）
  - 8-10 条 claims（算���因���/趋势生命周期/BGM 机制/参与时机）
  - 5-6 个 concepts（FYP / Hashtag Challenge / Sound Virality / Trend Lifecycle）

**���究包 2：Reddit 母婴���区行���与信号提取**
- **Why P0**：Reddit 是 S1 用户讨���的最高���量来源（v3 PRD ���确标为重点）；没有社区行��� claims 则���点识��� SOP 无从落地
- **研���问题**���
  1. r/breastfeeding / r/NewParents / r/beyondthebump 等核心子���块的社区规范（���止商业���广/医���建���风险/真实性要���）���
  2. ���质量信号特���是���么（帖���长度/评���数/Upvote 比/OP ���动���）？
  3. ���音识���标准（���军特征/品牌���军/���品黑稿/���一���面情绪放大）？
  4. 痛点 vs 抱怨的区分框架���频次/严重性/���解决性/影���范围）？
  5. Reddit API 官���限制与 Apify ���取合规边界���
- **期���输出**：
  - 8-10 个 sources（Reddit API Docs / Apify Reddit Actor / Sprout Social / Brand24）
  - 10-12 条 claims（社区规范/高���量信号/噪音识别/痛���判断框架）
  - 6-8 ��� concepts���Subreddit Etiquette / Signal-to-Noise / Pain Point vs Complaint / Upvote Ratio）

**研究��� 3：母婴垂类 Creator 生态���度图谱**
- **Why P0**：Creator 生���是 S4 ���全部，且直接���响 Action Engine 的���作建议质量
- **研���问题**：
  1. TikTok / IG / YouTube ���婴 Creator 分���标准（Nano <10K / Micro 10K-100K / Mid 100K-500K / Macro >500K）？
  2. 各���级受���特征、���容类���、商业���作模式���异？
  3. 母��� Creator 的商业披露识别���#ad / #sponsored / #partnership / 无披露���险）？
  4. ���黑名���机制：什么信号标��� Creator 为高风险���医���误导/品类冲突/负���舆论/虚���流量���？
  5. ���作时机判断框���（Creator ���容方���变化/受众增���阶段/���品合���空窗）���
- **期望���出**：
  - 10-12 个 sources（Influencer Marketing Hub / HypeAuditor / AspireIQ / FTC Endorsement Guides）
  - 12-15 条 claims���Creator 分���/受众特征/商业���露/红黑名单/合���时机）
  - 8-10 个 concepts（Nano Influencer / Engagement Rate / Sponsored Content Disclosure / Creator Lifecycle���

**SOP 1：痛点���号识别**（���推核心场景+未满足需���）
- **核���场���**：社��� Analyst 看到 Reddit 上 1 条「Momcozy 吸奶器法���尺寸不���导致堵���」���子���agent 如何判断���是���需要上报���产品团队的真实痛���」还是「���一���音」？
- **未满足需求**：当前���法是���人工主���判断 + ���评���数���，缺乏结构化标���，容���误���（把���条负面���大为危机 or 把真���痛点���噪音）
- **SOP 输出**：5 维���断框架���频次/严重性/可解决性/影响范围/社区共鸣）+ 3 级���类（P0 痛点/P1 改进建议/P2 噪音���+ 验���契约

**SOP 2：���盖缺���诚实���达**（倒推���心���景+未满足需求）
- **���心场景**���agent 抓取��� Reddit 97 条���子、TikTok 30 条视频，但 Instagram 0 条���API ���制）、Facebook Groups 0 ���（私密���无法抓取）。agent 如���诚实表达「我���覆���了 Reddit + TikTok，IG/FB 是缺���」而���是���出「Instagram 讨���量为 0」？
- **未满足需���**：v3 PRD 点名���最容���翻车」���一���「���抓不到���数据当���零」���当���没有标准化的缺���标注���板
- **SOP 输���**：3 ���缺口（���术限制/ToS ���制/���源未配置）+ 标注模板（���台/缺口类型/影响范围/替代方���）+ 验收契约

---

### Phase B：P1 研���包 + P1 SOP

**研究包 4���Facebook Groups ���婴社���运���生态**
- 公开群 vs 私密群的数据可及��� / 群主���态 / 帖���类型分布 / Apify Groups Scraper 合���边界

**研究包 5：社媒���品内容情报方���论**
- 竞品爆款拆解框架（BGM/脚本/视���/钩子/CTA）/ 高表现内���共同���征 / 可借鉴要素���别标准

**SOP 3：Creator ���估与合作判���**
- 评估框���（受众匹配度/内���风格/商业披露���规/���史���作质量）+ 合作时机 + 红���名单���制

**SOP 4：趋势参与决���**
- ���势适合品牌���断（品类相���性/调性匹配/时间窗���/执行难度）+ 参���方式（���进 vs 改编 vs 放弃）

---

### Phase C���P2 研究包 + P2 SOP

**研���包 6：社媒效果���量与 ROI ���架**
- Social Listening KPI（覆盖率/信���密度/洞���转化率）/ 趋势参与时效测��� / Creator ���作 ROI

**SOP 5：���品高表���内容拆解**
- 系统化拆���框架（what made it viral）+ 可借鉴要素提取 + ���容方向���出

**SOP 6：Social Action ���化**
- 洞察 → Action 标准流程���提���/审���/执���/复盘）+ Action 完整要素���平台/时间窗/责任���/成功标准）

---

## 四、执行 TODO（Phase A 优先）

**立即启动���Phase A）**：

- [ ] **TODO-A1**：创建���录结��� `kb/si/{wiki,agent_system_prompt.md,knowledge-system/{sources,claims,concepts,acceptance}.yml,sop/,out_search/,inner_worklog/}`
- [ ] **TODO-A2**���运行 3 组并��� web 搜索（TikTok 算法 / Reddit 社��� / Creator 生态），���组 2-3 个���询，共 6-9 ���搜索
- [ ] **TODO-A3**：交���审计验证搜���结果，筛选 L1 信���（≥2 独立来���确认的结���），标��� L2（单���待核���）
- [ ] **TODO-A4**：写入 `kb/si/knowledge-system/sources.yml`���28-32 个信源，Phase A 目标）
- [ ] **TODO-A5**���写入 `kb/si/knowledge-system/claims.yml`（28-32 条主张，Phase A 目标）
- [ ] **TODO-A6**���写��� `kb/si/knowledge-system/concepts.yml`（19-24 个概念，Phase A 目标）
- [ ] **TODO-A7**：���入 `kb/si/sop/01_痛���信号识别.md`（5 维框架 + 3 级分类 + 验收契约）
- [ ] **TODO-A8**���写入 `kb/si/sop/02_覆盖缺口诚实���达.md`（3 类缺口 + ���注模板 + 验收契约）
- [ ] **TODO-A9**���写入 `kb/si/knowledge-system/acceptance.yml`（2 ��� SOP 的验���契约）
- [ ] **TODO-A10**���写入 `kb/si/agent_system_prompt.md`（3 条常驻原则：���盖缺���/单���信号不���大/母婴品类特殊��� + ���牌占���）
- [ ] **TODO-A11**：写��� `kb/si/wiki_社媒Intelligence知识库.md`（���类可读入口，索引所有 SOP + 知识���）
- [ ] **TODO-A12**���业务协���（更新 `PMO/业务协作_社媒团队/` Excel 表格���添加 Creator 红���名单/趋势监测配���/缺���标注规范等 sheet���
- [ ] **TODO-A13**：提交 Phase A（commit + push，commit message: "Phase A complete: SI knowledge base foundation — TikTok/Reddit/Creator + 2 P0 SOPs"）

**Phase B & C ���后**���
- Phase B TODO 在 Phase A 完成���再拆���
- Phase C TODO 在 Phase B 完���后再拆解

---

## 五、质���标准与���收契约

| ���度 | 标准 | 验收方��� |
|---|---|---|
| ���源质量 | 每条 claim ���2 独���来源（L1）；单���标注 L2 待���实 | sources.yml 中每个 sourceId 带 authority / asOf / url；claims.yml 中 evidenceGrade 字��� |
| SOP 可执行性 | 每��� SOP 倒推���心���景+未满���需求，���出结���化框���+验���契��� | acceptance.yml 中每个 SOP 有 verifiable gates（输入/输出/���断标准） |
| Agent ���调用性 | knowledge-system/ 采用 Kb2Agent 格式���claims 有 claimType / risk / verification 字段 | 写一个简单��� Python loader 能���析 sources/claims/concepts 并返回结构化对��� |
| 人类可读��� | wiki 作入口���SOP 有「为���么需���这个���+ 步骤 + 案��� | ���媒 Analyst 能在 5 分���内找到���标 SOP ���理解其使用场��� |
| 交���审��� | 每��� claim 在 crossAuditNote 字���注明多���确认���单���待核��� | claims.yml 中 crossAuditNote 非空且注明信源数��� |

---

## ���、���险与���赖

| 风险 | 影响 | ���解措��� |
|---|---|---|
| TikTok 算法官���文���有限 | 研究包 1 可能���能拿到二手分析报��� | 补充 Hootsuite / Influencer Marketing Hub 等���业报告���标注为 L2 待���实 |
| Reddit 社区规范分散在各���版块 | 研究��� 2 需要逐个子���块查���规则 | 优先���盖 r/breastfeeding / r/NewParents / r/beyondthebump 三个核心版块 |
| Creator 生���变���快 | ���究��� 3 ��� claims 可��� 6 ���月后过��� | 每条 claim 带 asOf 字段，标���有效���；设计���可更新架构 |
| ���务团队未提供 inner_worklog | 缺���第一���工作���志���为 context | Phase A 先用公���知识���建，Phase B 再���业务索取工作日志补充 |

---

## 七、下���步

**立即���动**：启��� TODO-A1���创建目录结构），���后并���启动 TODO-A2���3 组 web ���索）。

