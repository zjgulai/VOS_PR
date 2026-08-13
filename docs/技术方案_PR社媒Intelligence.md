---
name: pr-social-intelligence-technical-plan
description: PR Intelligence + 社媒 Intelligence 完整技术方案。基于 Q1-Q5 用户决策，每一项标注事实/合理推测/未验证假设/风险。是执行阶段的权威参考文档。
---

# PR + 社媒 Intelligence 技术方案

> 版本：v1.0 | 日期：2026-08-12  
> 范围：完整版（Q5=C，3-4 周），PR 周报 + 社媒周报双线并行  
> 约束来自用户决策（Q1-Q5）：

| 决策点 | 答案 | 技术含义 |
|--------|------|---------|
| Q1 输出形式 | D → 先做 Markdown | 近期不做飞书 API，脚本直接写 `.md` 文件 |
| Q2 审核角色 | A → 专职 Analyst | 草稿需结构化，Analyst 可直接编辑后发布 |
| Q3 LLM | Kimi + DeepSeek | 用这两个 API 做洞察摘要和周报生成 |
| Q4 ToS 风险 | A → 接受 | 可用 Apify/browser-use 采集 Facebook Groups |
| Q5 范围 | C → 完整版 | 两套周报全量交付，预估 3-4 周 |

---

## 一、已确认事实 vs 未验证假设

在开始执行前，以下每一项都需要清楚标注其可信度：

### 1.1 已确认事实（可直接使用）

| 事实 | 验证方式 |
|------|---------|
| DuckDB 6张 PR/Social 表已建立（18-29列各表）| 实际查询验证 |
| monitor.py 13个监管源已配置（含 ClassAction.org）| 代码审计 + 语法验证 |
| feed_collector.py 26个媒体 RSS 源已配置 | 代码审计 + 语法验证 |
| feedparser、duckdb、httpx 已安装（Python 3.9）| 实际导入验证 |
| 本机网络对外部 URL 大量 Connection reset | 实际测试 |
| ClassAction.org v4 Shopee 端点返回 403（API 存在）| 实际测试 |

### 1.2 合理推测（需在部署环境确认）

| 推测 | 依据 | 验证方法 |
|------|------|---------|
| 部署服务器网络可访问 CPSC/FDA/FTC RSS | 本机限制不等于服务器限制 | 在服务器运行 `python3 tools/regulatory/monitor.py --dry-run` |
| Kimi API 兼容 OpenAI SDK 格式 | Kimi 官方文档标注兼容 | 用 `openai` 库测试 Kimi endpoint |
| DeepSeek API 同上 | DeepSeek 官方文档 | 同上 |
| Facebook Groups 第三方爬取可持续使用 | Apify 现阶段可用 | 首次运行后监控封号情况 |

### 1.3 未验证假设（风险项，见第五章）

| 假设 | 风险等级 | 如果错了的后果 |
|------|---------|--------------|
| Shopee 内部 API 带 cookie 可返回评论 | 中 | Shopee VOC 仍为空白，需转向 Apify |
| Kimi/DeepSeek 生成的中文周报质量够用 | 中 | 需要 Analyst 大量重写，价值降低 |
| 1人可以在 3-4 周内完成全量系统 | 高 | **最大风险**，详见第五章 |
| 媒体 RSS 源的 URL 都是有效且稳定的 | 低-中 | 部分 RSS URL 可能 404 或无内容 |

---

## 二、系统架构（基于 Q1-Q5 确定版）

### 2.1 整体数据流

```
采集层（每日/每周自动运行）
├── 监管源 RSS × 13       → tools/regulatory/monitor.py
├── 媒体 RSS × 26         → tools/pr_intel/feed_collector.py
├── TikHub API            → tools/social/tiktok_collector.py  [待写]
├── YouTube Data API v3   → tools/social/youtube_collector.py [待写]
├── Reddit JSON API       → tools/social/reddit_collector.py  [待写]
└── Facebook Groups/Apify → tools/social/fb_groups_collector.py [待写]
        ↓
存储层（DuckDB voc.duckdb）
├── pr_articles           → 原始文章/信号
├── pr_risk_signals       → 风险评分结果
├── pr_opportunities      → 机会点
├── pr_weekly_reports     → 周报记录
├── social_posts          → 社媒内容
└── social_trends         → 趋势数据
        ↓
分析层（每周一次，LLM 处理）
├── 风险评分器             → tools/pr_intel/risk_scorer.py  [待写]
├── 机会识别器             → tools/pr_intel/opportunity_finder.py [待写]
└── 周报生成器             → tools/pr_intel/report_generator.py [待写]
        ↓
交付层（Q1=D：Markdown 文件）
├── reports/pr_intel/YYYY-WW_PR_Intelligence.md   → PR Analyst 审核
└── reports/social_intel/YYYY-WW_Social_Intel.md  → 社媒 Analyst 审核
```

### 2.2 LLM 调用层设计（Q3=Kimi+DeepSeek）

```python
# tools/llm/client.py — 待写
# 策略：Kimi 做长文本摘要（支持 128k context），DeepSeek 做分析推理

LLM_ROUTING = {
    "summarize_article": "kimi",      # 文章摘要，长文本
    "score_risk": "deepseek",         # 风险推理，逻辑性强
    "generate_report": "kimi",        # 周报生成，结构化输出
    "identify_opportunity": "deepseek" # 机会判断，分析推理
}
```

**未验证假设**：Kimi API endpoint 和认证方式需要在实际环境确认。

### 2.3 调度配置（Q5=C 完整版需要两套调度）

```bash
# crontab 配置（待写入部署服务器）
# 每日 08:00 采集监管源和媒体 RSS
0 8 * * * cd /path/to/voc-data-product && python3 tools/regulatory/monitor.py --write-db
0 8 * * * cd /path/to/voc-data-product && python3 tools/pr_intel/feed_collector.py --write-db

# 每日 09:00 采集社媒数据
0 9 * * * cd /path/to/voc-data-product && python3 tools/social/tiktok_collector.py

# 每周一 10:00 生成周报草稿
0 10 * * 1 cd /path/to/voc-data-product && python3 tools/pr_intel/report_generator.py

# 每日 P0 预警检查（高频）
*/30 * * * * cd /path/to/voc-data-product && python3 tools/pr_intel/alert_checker.py
```

**合理推测**：cron 在 macOS 本地开发机上可用，生产部署可能需要换成 launchd 或 systemd。

---

## 三、执行 Checklist（3-4 周完整版）

### 第 1 周：采集层全部打通

| # | 任务 | 文件 | 验收标准 | 已确认/待验证 |
|---|------|------|---------|-------------|
| 1.1 | 在部署服务器验证监管 RSS 可访问 | `tools/regulatory/monitor.py` | 至少 3 个 RSS 源返回真实条目 | **待验证** |
| 1.2 | 验证媒体 RSS 源可访问性 | `tools/pr_intel/feed_collector.py` | 至少 15/26 个源有效 | **待验证** |
| 1.3 | 配置 Kimi API Key，验证调用 | `tools/llm/client.py`（新建） | `client.complete("test")` 返回正常 | **待验证** |
| 1.4 | 配置 DeepSeek API Key，验证调用 | 同上 | 同上 | **待验证** |
| 1.5 | 写 TikHub API 采集器 | `tools/social/tiktok_collector.py` | 1 个竞品账号返回 ≥5 条内容 | 待写 |
| 1.6 | 写 YouTube Data API 采集器 | `tools/social/youtube_collector.py` | 1 个频道返回 ≥5 条视频 | 待写 |
| 1.7 | 写 Reddit JSON API 采集器 | `tools/social/reddit_collector.py` | r/breastfeeding 返回 ≥10 条帖子 | 待写 |
| 1.8 | 写 Facebook Groups 采集器（Apify）| `tools/social/fb_groups_collector.py` | 1 个群组返回 ≥10 条帖子 | 待写 |

### 第 2 周：分析层 + 风险评分

| # | 任务 | 文件 | 验收标准 | 已确认/待验证 |
|---|------|------|---------|-------------|
| 2.1 | 写风险评分器（实现 PR 方案原文公式）| `tools/pr_intel/risk_scorer.py` | 给10篇文章评分，P0 分数 ≥80 的能触发 | 待写 |
| 2.2 | 写机会识别器 | `tools/pr_intel/opportunity_finder.py` | 每周至少识别 3 个机会点 | 待写 |
| 2.3 | 写 P0 实时预警检查器 | `tools/pr_intel/alert_checker.py` | 发现 P0 信号后写入 pr_risk_signals | 待写 |
| 2.4 | 写社媒竞品内容分析 | `tools/social/competitor_analyzer.py` | 识别高互动内容（>均值 3 倍）打 is_viral_flag | 待写 |
| 2.5 | 写趋势聚合器 | `tools/social/trend_aggregator.py` | 每周输出 Top10 Hashtag/BGM | 待写 |

### 第 3 周：周报生成层

| # | 任务 | 文件 | 验收标准 | 已确认/待验证 |
|---|------|------|---------|-------------|
| 3.1 | 写 PR 周报生成器（LLM + 模板）| `tools/pr_intel/report_generator.py` | 生成可读的 .md 草稿，结构符合 PR Intelligence Report 格式 | 待写 |
| 3.2 | 写社媒周报生成器 | `tools/social/report_generator.py` | 生成包含四个模块（S1-S4）的 .md 草稿 | 待写 |
| 3.3 | 写报告输出管理器（文件命名/归档）| `tools/report_manager.py` | `reports/pr_intel/2026-W33_PR_Intelligence.md` 格式正确 | 待写 |
| 3.4 | 配置 cron job（每周一 10:00）| 服务器 crontab | 每周一自动生成草稿，文件存在于 reports/ | 合理推测 |

### 第 4 周：验收 + 第一轮真实周报

| # | 任务 | 验收标准 |
|---|------|---------|
| 4.1 | PR Analyst 完成第一轮审核 | Analyst 反馈草稿质量，记录修改内容 |
| 4.2 | P0 预警真实触发测试 | 手动注入一条 ClassAction.org 数据，验证预警链路 |
| 4.3 | 社媒周报第一版完成 | 社媒团队确认四个模块内容有效 |
| 4.4 | 输出已知问题清单 | 记录哪些平台数据质量不足，哪些功能需要调整 |

---

## 四、周报结构模板（草稿格式，供 Analyst 使用）

### 4.1 PR Intelligence Report（每周一生成）

```markdown
# PR Intelligence Report — Week of YYYY-MM-DD

## 执行摘要（4句话）
- 媒体和行业发生了什么：[LLM 填充]
- 对 Momcozy 意味着什么：[LLM 填充]
- 本周最重要的机会：[LLM 填充]
- 本周最需要关注的风险：[LLM 填充]

## P0/P1 风险预警
| 风险 | 来源 | Sev等级 | 风险分 | 建议行动 |
|...   |...   |...      |...     |...      |

## 媒体与竞品动态
- 本周竞品重大事件（GlobeNewswire/TechCrunch）
- 榜单变化（Babylist/The Bump/Consumer Reports）
- 值得关注的编辑选题

## 机会清单
| 机会 | 媒体 | 角度 | 窗口期 | 所需资产 |
|...   |...   |...   |...     |...      |

## PR Actions（本周建议）
| 行动 | 负责人 | 截止 | 所需 |
|...   |...     |...   |...   |

## 上周跟进
[上周 Actions 的执行状态]

---
*草稿由 AI 生成，所有引用来源可追溯，对外行动须 Analyst 审批后执行*
```

### 4.2 Social Media Intelligence Report（每周一生成）

```markdown
# Social Media Intelligence Report — Week of YYYY-MM-DD

## 执行摘要

## S1 用户讨论洞察
- 本周热点话题（Reddit/Facebook Groups）
- 高频痛点：[...]
- 新增需求信号：[...]
- 潜在风险：[...]

## S2 竞品社媒动态
| 品牌 | 平台 | 内容重点 | 最高互动内容 | 观察 |
|...   |...   |...       |...           |...   |

## S3 热点趋势
- TikTok 热门 Hashtag Top5
- 热门 BGM（含使用视频数和增速）
- 本周值得跟进的趋势（含时间窗口建议）

## S4 KOL 动态
- 重点 KOL 本周内容方向
- 是否出现品牌/竞品合作内容
- 潜在合作机会

## Social Media Actions（本周建议）
| 行动类型 | 具体建议 | 优先级 |
|...       |...       |...     |

---
*草稿由 AI 生成，需团队 review 后使用*
```

---

## 五、风险清单（不可忽略）

### 5.1 最大风险：3-4 周 1 人全量完成

**已确认事实**：单人维护，无 CI/CD，无测试框架。

**风险评估**：Q5=C（完整版）包含约 15 个待写模块。1 人 3-4 周内完成全部的假设**过于乐观**。

**建议的应对策略**：

```
第 1 周优先：采集层（1.1-1.8）
  → 这是一切的基础，没有数据一切为零

第 2 周次优先：P0 预警（2.1 + 2.3）
  → 这是最紧迫的业务价值（KleanPal/参议院盲区）

第 3 周按需：周报生成
  → 如果时间压缩，先做模板 + 人工填充，LLM 生成可以后期加

降级方案：
  如果 3-4 周内完不成全量，优先交付：
  - 监管 P0 预警（每天自动）
  - 竞品媒体 RSS 采集（每天自动）
  - 手动 + 模板生成周报（Analyst 用模板人工撰写）
```

### 5.2 Kimi/DeepSeek API 集成

**未验证**：具体 endpoint URL、认证方式、rate limit、价格。

**需要立即确认**：
- Kimi API: `api.moonshot.cn`，模型名 `moonshot-v1-128k` 或 `moonshot-v1-32k`
- DeepSeek API: `api.deepseek.com`，模型名 `deepseek-chat` 或 `deepseek-reasoner`
- 两者均兼容 OpenAI SDK（`openai.OpenAI(base_url=..., api_key=...)` 方式调用）

**验证方法（立即可运行）**：
```bash
python3 -c "
import openai
client = openai.OpenAI(
    base_url='https://api.moonshot.cn/v1',
    api_key='YOUR_KIMI_KEY'
)
r = client.chat.completions.create(
    model='moonshot-v1-8k',
    messages=[{'role':'user','content':'hello'}]
)
print(r.choices[0].message.content)
"
```

### 5.3 Facebook Groups 采集合规风险（Q4=A）

**已确认**：Meta ToS 明确禁止自动化采集。用户接受风险。

**风险缓解措施**：
- 使用 Apify（风险转移，有封号保护）
- 只采集公开群组（不尝试私密群组）
- 频率控制：每个群组每天最多采集 1 次
- 保留操作日志，出问题可追溯

**不做的事**：不爬取私人群组，不关联群组成员真实身份。

### 5.4 LLM 生成内容的准确性

**风险**：LLM 可能幻构品牌声明、引用不存在的文章、生成不准确的风险评估。

**缓解方案**（来自 PR 方案原文原则）：
- 所有 LLM 生成的摘要必须包含原始来源 URL
- `evidence_grade` 字段标注置信度
- Analyst 审核时重点验证任何具体数字和引用
- 绝不允许 LLM 生成的内容直接对外发布

---

## 六、下一步行动（优先级排序）

**本周内（不等任何人）**：

| 行动 | 原因 | 预计时间 |
|------|------|---------|
| 1. 在部署服务器跑 `monitor.py --dry-run` | 验证网络可达性，这是所有后续的前提 | 10分钟 |
| 2. 确认 Kimi + DeepSeek API Key 有效 | 验证 LLM 层可用，影响整个分析链路 | 20分钟 |
| 3. 写 `tools/llm/client.py` | LLM 统一入口，后续所有模块都依赖 | 2小时 |
| 4. 写 `tools/social/tiktok_collector.py` | TikHub API 已有 SDK，最快可以出数据的平台 | 3小时 |

**本周内需要你提供**：

| 信息 | 为什么需要 |
|------|----------|
| Kimi API Key | 无法测试 LLM 层 |
| DeepSeek API Key | 同上 |
| 部署服务器的访问方式（SSH/本机）| 验证网络和 Python 版本 |
| Apify API Key（如果已有）| Facebook Groups 采集 |
| 竞品 TikTok/Instagram 账号列表（确认版）| 采集器需要确切的账号 handle |
