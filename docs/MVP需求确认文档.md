---
name: mvp-requirements-confirmation
description: PR Intelligence + 社媒 Intelligence 两条产品线的 MVP 范围确认文档。区分已确认事实、合理推测、未验证假设和待用户确认项。是执行前的最后一道对齐关卡。
---

# MVP 需求确认文档

> 版本：v1.1 | 日期：2026-08-12 | Q1-Q5 已全部确认  
> 状态：**✓ 用户决策已完成，进入技术方案阶段**  
> 原则：不推测用户意图，不在信息缺失时自行补全决策

---

## 一、已确认事实（无需用户确认，可直接作为设计依据）

### 1.1 PR Intelligence 已确认事实

来源：三份 PR 方案原文（PR/ 目录），有明确引用。

| 事实 | 原文依据 | 置信度 |
|------|---------|--------|
| 每周更新一次 PR Intelligence Report | 方案原文："最终希望形成一份每周更新的PR Intelligence Report" | 高 |
| 核心逻辑链：监测→洞察→机会&风险→Actions | 方案原文明确的四步链路 | 高 |
| 任何对外行动必须人工审批，AI 不得自动发布 | 方案原文 Finding 6："任何外部 pitch、记者回复...均必须由授权人员批准" | 高 |
| KleanPal 集体诉讼已在 ClassAction.org 建档 | 方案原文有具体引用编号 | 高 |
| 参议院 HELP 委员会 2026-06-17 致函，7-06 要求答复 | 方案原文 Finding 4 有具体日期和内容 | 高 |
| Momcozy M5 在 Babylist 被列为 Best Affordable | 方案原文引用[8][9] | 高 |
| Forbes Vetted 把 M5 列为 best value（非 best overall） | 方案原文引用[11] | 高 |
| Reddit 有未经证实的虚假评价指控 | 方案原文标注为"待核验社会信号" | 中（未验证） |
| 美国 FTC 2024-10 起实施消费者评价与推荐规则 | 方案原文引用[19][20] | 高 |
| Reddit 商业用途需单独协议（非默认可用） | 方案原文 Finding 7 数据源表格 E 层明确标注 | 高 |

### 1.2 社媒 Intelligence 已确认事实

来源：用户在对话中原文粘贴的社媒需求文本。

| 事实 | 原文依据 | 置信度 |
|------|---------|--------|
| 四个核心模块：用户讨论/竞品监控/热点趋势/KOL分析 | 需求原文四段结构 | 高 |
| Reddit 和 Facebook Groups 是重点监测平台 | 原文："Reddit 和 Facebook Groups 是重点监测平台" | 高 |
| 后续可补充需要重点关注的 Subreddit | 原文明确说明 | 高 |
| 需分析 BGM、热门 Hashtag、视频模板 | 原文 S3 模块明确列出 | 高 |
| 输出形式未在需求原文中明确 | 原文无具体说明 | — |
| 报告频率未在需求原文中明确 | 原文无具体说明 | — |

### 1.3 两条产品线的共同确认事实

| 事实 | 依据 |
|------|------|
| 项目当前无 CI/CD，单人维护 | 代码库实际状态 |
| DuckDB 已入仓 13 张 CSV，28MB | 实际验证（Checkpoint 2 通过）|
| 系统 Python 版本 3.9.6 | 实际验证 |
| feedparser、duckdb、httpx、yt-dlp 已安装 | 实际验证 |
| tools/regulatory/monitor.py 存在，语法正确，未在真实网络验证 | 代码审计结论 |
| 项目不是 git repo，无版本追踪 | 实际检查 |

---

## 二、架构确定项（不依赖 Q1-Q5，可先动工）

无论用户如何回答 Q1-Q5，以下架构决策已经足够确定，可以立即开始：

### 2.1 数据采集层（确定）

```
监管源采集（tools/regulatory/monitor.py）
  → 10 个 RSS 源（CPSC/FDA/FTC/Health Canada/ACCC/UK ASA 等）
  → 输出：data/processed/regulatory/YYYYMMDD.json

媒体 RSS 采集（待写：tools/pr_intel/feed_collector.py）
  → 约 30 个核心媒体 RSS（GlobeNewswire/PRNewswire/TechCrunch 等）
  → 输出：data/processed/pr_intel/YYYYMMDD.json

社媒数据（待接入）
  → TikHub API → TikTok 内容
  → YouTube Data API v3 → YouTube 内容
  → Reddit JSON API → Subreddit 帖子
  → 输出：data/processed/social/YYYYMMDD.json
```

### 2.2 存储层（确定）

```
DuckDB（已有）：voc.duckdb
  → 新增 PR Intelligence 表：pr_articles / pr_signals / pr_risk_events
  → 新增 Social 表：social_posts / competitor_content / kol_content
  → 不另建数据库，共用单文件
```

### 2.3 风险评分逻辑（确定，来自 PR 方案原文）

```
Risk = 0.25×Severity + 0.20×Velocity + 0.15×Source Authority
     + 0.15×Potential Reach + 0.10×Corroboration
     + 0.10×Brand Proximity + 0.05×Persistence

Sev0 <30  → 周度汇总
Sev1 30-49 → 1个工作日
Sev2 50-69 → 4小时，主管通知
Sev3 70-84 → 60分钟，War Room
Sev4 ≥85  → 15分钟确认，60分钟首次简报
```

### 2.4 不做的事（确定）

- ❌ AI 自动发送任何对外联系（记者、社区、媒体）
- ❌ 直接复制个人健康数据进 PR 系统
- ❌ 把匿名账号与真实个人强行关联
- ❌ Reddit 商业化采集（在取得商业协议前）
- ❌ 自动执行任何有法律/声誉影响的动作

---

## 三、待用户确认项（Q1-Q5）

**以下 5 个问题决定系统的交付形态和实现路径，在得到明确答案前无法推进 C4。**

### Q1 — 输出形式 【阻塞 C4】

PR 周报和社媒报告的最终交付形式？

```
选项 A：飞书文档（发到指定群或文档库）
选项 B：Markdown 文件（存到本地，手动分发）
选项 C：飞书群消息（直接 @ 相关人，纯文本）
选项 D：还没想好，先做出来再说

影响：
  A → 需要飞书 API 集成（feishu-lark-agent skill，约 0.5 天额外工作）
  B → 最简单，0 额外工作
  C → 需要飞书 API，但比文档简单
  D → 先做 B，后期迁移
```

**用户答案：D — 先做 B（本地 Markdown），后期按需迁移到飞书**

---

### Q2 — 人工审核角色 【阻塞 C4 工作流设计】

生成周报草稿后谁来审核发布？

```
选项 A：有专职 PR Analyst，每周审核 30-60 分钟后发布
选项 B：PR/社媒负责人直接看草稿，改完就发，无专职角色
选项 C：现阶段工程师跑脚本验证，确认可用后交业务团队
选项 D：其他

影响：
  A → 需要做 Action Center 工作台（约 1 周前端工作）
  B → 只需飞书草稿文档，人工 review 后手动发布
  C → 脚本输出到终端或本地文件即可，最小实现
```

**用户答案：A — 有专职 PR Analyst，每周审核后发布**

---

### Q3 — LLM API 访问 【阻塞洞察生成层】

可以直接调用哪个 LLM？

```
选项 A：OpenAI（GPT-4o / GPT-4.1）
选项 B：Anthropic（Claude Sonnet/Opus）
选项 C：其他（Gemini / Kimi / 通义等）
选项 D：还没有，需要申请

影响：
  有 API Key → 可做洞察摘要、风险评分、周报草稿生成
  没有 → 只能做规则过滤、关键词匹配、人工撰写，系统价值大幅降低
```

**用户答案：Kimi + DeepSeek（已有 API Key）**

---

### Q4 — Reddit/Facebook 合规边界 【阻塞社媒采集设计】

是否接受用第三方工具（Apify 等）采集 Facebook Groups，了解这可能违反 Meta ToS？

```
选项 A：接受，用第三方工具，风险自担
选项 B：不接受，只用合规 API（意味着 Facebook Groups 基本采集不到）
选项 C：暂时跳过这两个平台，先做 TikTok/YouTube/TikHub

注：PR 方案原文已明确"Reddit 商业用途需单独协议"
注：Facebook Groups 无官方 API 支持第三方批量采集
影响：
  A → Apify Facebook Scraper，$50/月，有封号风险
  B → 社媒 S1 的"重点平台"两个都不能覆盖
  C → S1 先用 TikTok+YouTube 替代，Reddit/FB Groups 推后
```

**用户答案：A — 接受，用第三方工具，风险自担**

---

### Q5 — MVP 范围边界 【核心决策，直接决定工作量】

第一个可交付的版本最小是什么？

```
选项 A（最小，约 2 天）：
  监管 RSS 自动采集 + P0 风险信号飞书推送
  → 立即解决 KleanPal/参议院盲区问题
  → 输出：每天一条飞书消息，列出当天 P0 信号

选项 B（中等，约 5-7 天）：
  A + 核心媒体 RSS 采集（30个源）
    + LLM 生成周报草稿（需 Q3 确认）
    + 飞书推送
  → 输出：每周一份飞书文档草稿

选项 C（完整，约 3-4 周）：
  B + 竞品账号监控（TikHub API）
    + KOL 内容追踪
    + 社媒趋势（TikTok Creative Center）
    + Reddit 采集（如 Q4=A）
  → 输出：PR 周报 + 社媒周报，两份独立文档
```

**用户答案：C — 完整版（PR 周报 + 社媒周报，3-4 周）**

---

## 四、Q1-Q5 回答后立即输出的内容（C4）

用户回答 Q1-Q5 后，将基于上述确定事实 + 用户决策，输出：

1. **技术方案**：具体文件列表、接口定义、调度配置
2. **执行 Checklist**：每个任务 → 验收标准 → 负责人 → 预期工时
3. **风险清单**：每个待验证假设的验证方法和 fallback 方案
4. **不做的事**：明确排除在 MVP 范围之外的功能

---

## 五、可以立即执行的工作（不等 Q1-Q5）

以下工作与 Q1-Q5 无关，现在可以开始：

| 任务 | 文件 | 预计工时 | 验收标准 |
|------|------|---------|---------|
| 在 DuckDB 创建 PR 数据表结构 | `tools/etl/init_pr_tables.py` | 2小时 | SQL 建表成功，schema 可查 |
| 编写媒体 RSS 采集器（30个源） | `tools/pr_intel/feed_collector.py` | 4小时 | 至少 3 个 RSS 源返回真实条目 |
| 把 ClassAction.org 加入监管监测 | `tools/regulatory/monitor.py` | 1小时 | 关键词过滤逻辑加入 |
| 确认生产服务器 Python 版本 | 在服务器运行 `python3 --version` | 10分钟 | 得到实际版本号 |
