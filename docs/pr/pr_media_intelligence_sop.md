---
name: pr-media-intelligence-sop
description: Momcozy PR媒体情报体系SOP。涵盖媒体资源库结构、编辑OSINT补全方法论、飞书表格同步规范、AI推荐策略生成流程。当需要理解PR媒体数据结构、执行编辑信息补全、生成Pitch建议时使用。
---

# Momcozy PR 媒体情报体系 SOP

## 一、数据资产总览

### 飞书表格主库
链接：https://momcozy-in.feishu.cn/sheets/RbPcsD7GNhAVSpt3sA3cCDownNg

| Sheet | 内容 | 数据量 | 完整度 |
|---|---|---|---|
| ① 核心媒体库 | 521条全量媒体，20字段 | 665行 | 基础字段完整，编辑信息64%缺失 |
| ② 编辑联系人库 | 11家核心媒体×48位编辑 | 50行 | LinkedIn 71%缺失 |
| ③ SEO榜单追踪 | Breast Pump + Bottle Washer品类词 | 22行 | 含Pitching进度 |
| ④ 新品营销日历 | H2产品上市甘特 | 20行 | 19款产品×7个月 |
| ⑥ Pitch策略细化 | 6类媒体角色×4维度 | 7行 | 完整 |
| ⑦ 媒体台账SOP | PR协同管理规则 | 32行 | 完整 |
| ⑧ 媒体分级标准 | 100分制评分体系 | 65行 | 完整 |
| **⑨ 编辑社交图谱** | **OSINT补全的S级编辑社交档案** | **9行(持续增加)** | **S级8位已完成** |
| **⑩ AI推荐策略** | **媒体优先级评分+Pitch时机日历+竞品对标** | **29行** | **AI生成,需PR校准** |
| **⑪ 信息来源标注** | **字段来源标注+高优先级行动项** | **39行** | **完整** |

### 本地源文件
- 原始业务输入：`PMO/业务协作_社媒团队/momcozy pr 媒体关系全年规划表.xlsx`
- 结构化版本：`PMO/业务协作_社媒团队/momcozy pr 媒体关系全年规划表_结构化.xlsx`
- 修复内容：752个合并单元格全部展开，7个Sheet数据完整性修复

---

## 二、核心数据问题与修复记录

### 2.1 原始数据问题（已修复）

| 问题 | 影响 | 修复方式 |
|---|---|---|
| 623个合并单元格（Sheet①）| 664行中292行前5列全NULL | unmerge+fill展开 |
| G列操作策略：110字长文本每行重复 | 无法筛选/分析 | 映射为4级标签(S/A/B/C) |
| 社媒链接塞在单个单元格 | 无法独立使用各平台链接 | 拆分为Twitter/Instagram/Facebook/YouTube/Pinterest独立列 |
| 分区标题行横跨14列 | 无法数据查询 | 删除标题行，加Category数据列 |
| 817字策略说明塞在A1单格 | 无法阅读和引用 | 按章节拆分为25行独立记录 |
| 表头含换行双语文本 | 显示溢出，影响可读性 | 统一为简洁中文单行表头 |

### 2.2 数据完整度现状

```
Sheet① 核心媒体库关键字段完整度：
  媒体名称:   78%  ████████░░
  评级:       67%  ███████░░░  (33%未分级)
  Editor:     36%  ████░░░░░░  (64%无编辑信息)
  Email:       5%  █░░░░░░░░░  (95%缺失)
  Pitching:    3%  ░░░░░░░░░░  (97%空白)
```

---

## 三、OSINT编辑信息补全方法论

### 3.1 工具优先级

| 优先级 | 工具/方法 | 适用场景 | 效果 |
|---|---|---|---|
| P1 | **Exa Web Search** | 搜索`"编辑名" site:linkedin.com`或`"编辑名" 媒体名 journalist` | 最快，直接返回LinkedIn/Twitter |
| P2 | **媒体官网作者页** | `媒体URL/author/编辑名` | 可获取Bio、专业背景、联系方式 |
| P3 | **LinkedIn直接搜索** | 已知姓名+媒体名 | 职位、经历、帖子内容 |
| P4 | **Sherlock** | 用户名枚举全平台 | 适合已知Twitter handle时交叉验证 |
| P5 | **SpiderFoot** | 深度OSINT，适合建立社交图谱 | 耗时较长，适合战略级媒体 |

### 3.2 邮箱格式推断规则

常见媒体邮箱格式（用于批量推断，需验证）：

| 媒体 | 邮箱格式 | 示例 |
|---|---|---|
| Forbes | firstname.lastname@forbes.com | alicia.betz@forbes.com |
| Consumer Reports | f.lastname@consumer.org 或 flastname@cr.consumer.org | — |
| BabyCenter | firstname.lastname@babycenter.com | — |
| NBC News | firstname.lastname@nbcuni.com | — |
| Good Housekeeping (US) | firstname.lastname@hearst.com | — |
| Good Housekeeping (UK) | firstname.lastname@hearst.co.uk | madeleine.evans@hearst.co.uk |
| Babylist | firstname.lastname@babylist.com | **latifah.miles@babylist.com ✅已确认** |
| What to Expect | firstname.lastname@whattoexpect.com | — |
| Parents | firstname.lastname@dotdashmeredith.com | — |

### 3.3 已完成OSINT的编辑档案

| 编辑 | 媒体 | LinkedIn | Twitter | 邮箱 | 关键洞察 |
|---|---|---|---|---|---|
| Alicia Betz | Forbes | linkedin.com/in/alicia-betz | @aliciabetz | alicia.betz@forbes.com(推断) | 3孩妈妈+前教师,测试40+款婴儿推车,ABC Expo常客 |
| Blake Bakkila | BabyCenter | linkedin.com/in/blake-bakkila-42a3b796 | — | — | **⚠️已离职！现为自由撰稿** |
| Caitlin Giddings | Wirecutter | linkedin.com/in/caitlin-giddings | @caitlingiddings | — | **⚠️已离职！现在Pillar4 Media** |
| Jessica D'Argenio Waller | Consumer Reports | linkedin.com/in/jessicadwaller | — | — | MS营养学+CPST,专业背书极强 |
| Zoe Malin | NBC Select | linkedin.com/in/zoemalin | @zoemalin | — | Talking Shop专栏接受品牌推荐 |
| Latifah Miles | Babylist | linkedin.com/in/latifah-miles-mba-3b861062 | — | **latifah.miles@babylist.com ✅** | 主动在LinkedIn征集泌乳顾问资源 |
| Madeleine Evans | GH UK | uk.linkedin.com/in/madeleine-evans-a93368139 | — | madeleine.evans@hearst.co.uk(推断) | ⚠️专注Beauty/Health,非母婴主编 |
| Marguerite Williams Kypreos | Women's Health UK | — | — | — | ⚠️是助产士/IBCLC顾问,非媒体编辑! |

---

## 四、AI推荐策略框架

### 4.1 媒体优先级评分维度（100分制）

```
评分 = 流量量级(25) + DA/SEO权重(25) + TA匹配度(15) + 跨平台(10) + 内容深度(15) + 合作历史(5) + 意愿度(5)
```

### 4.2 Top 8 媒体AI评分

| 媒体 | AI评分 | 优先级 | 关键行动 |
|---|---|---|---|
| Consumer Reports | 96 | P0 | 提交W1/M8深度测评；强调安全认证 |
| Wirecutter (NYT) | 94 | P0 | ⚠️确认新编辑；争取Best Value位 |
| BabyCenter | 93 | P0 | ⚠️确认新联系人；申报Awards |
| What to Expect | 92 | P0 | 申报Best Awards；母乳喂养月专题 |
| Forbes Vetted | 91 | P1 | Prime Day/BF必报；礼品指南入选 |
| Good Housekeeping US | 89 | P1 | 申报GH Institute奖项 |
| Babylist | 88 | P1 | 直接发Pitch至latifah.miles@babylist.com |
| NBC News Select | 87 | P1 | 申请Talking Shop专栏 |

### 4.3 高价值Pitch时机（2026 H2）

| 时间 | 节点 | 优先媒体 | 产品 |
|---|---|---|---|
| 8月底 | 世界母乳喂养周余热+9月母乳喂养月 | CR/Babylist/WTE | M5/S12 Pro/Air1 |
| 9月 | Prime Day秋+开学季 | Forbes/NBC/BuzzFeed | M5/W1 |
| 10月 | 国家婴儿配方奶/母乳喂养月 | Healthline/Verywell/Babylist | Air1/M5 |
| 10月底 | 万圣节礼品指南 | BestProducts/Bustle/Country Living | W1/M5礼品装 |
| 11月 | BF/Cyber Monday | 全S级媒体 | 全线 |
| 11月 | 节日礼品指南 | GH/Real Simple/ELLE | S12 Pro/W1 |
| 1月 | CES 2027 | CNET/Wired/Engadget | M8/技术新品 |

---

## 五、社交网络图谱基础数据

### 5.1 编辑圈层关系（已识别）

```
Forbes Baby & Kids 圈层：
  Alicia Betz → Esther Carlstone(编辑) → ABC Kids Expo行业网络

Consumer Reports 母婴圈：
  Jessica D'Argenio Waller → 前雇主Motherly团队 → Verywell Health医学审查圈

NBC Select 圈层：
  Zoe Malin → NBC商务内容团队 → ABC/CBS编辑圈(跨媒体)

Babylist 商务编辑圈：
  Latifah Miles → 前New York Magazine/Vox Media圈 → Dotdash Meredith网络

Wirecutter 已变动：
  原: Caitlin Giddings → Pillar4 Media (已离职)
  新: 待确认新责任编辑
```

### 5.2 专家资源网络（非媒体编辑，可用于专家背书）

| 专家 | 专业 | 媒体关联 | 应用价值 |
|---|---|---|---|
| Marguerite Williams Kypreos | 助产士/IBCLC/舌系带 | Women's Health UK撰稿 | 产品专业背书+NHS医疗系统渗透 |
| Jessica D'Argenio Waller | MS营养学+CPST | Consumer Reports主编 | 双重身份：媒体+专家 |

---

## 六、数据更新SOP

### 6.1 月度更新规则（与⑦台账SOP一致）

- 每月1日前：更新上月Pitching结果到Sheet①的Pitching Status列
- 每季度：用Exa Web Search重新核查S/A级编辑是否仍在职
- 每半年：运行OSINT补全一次，更新⑨编辑社交图谱

### 6.2 编辑离职预警机制

发现以下信号时，立即标记并通知PR团队：
- LinkedIn显示"Freelance/自由撰稿"或新公司
- 媒体官网作者页无法访问
- Pitch邮件退信(hard bounce)

当前已知离职编辑（需立即补充新联系人）：
- **Blake Bakkila** → BabyCenter (已离职，现自由撰稿)
- **Caitlin Giddings** → Wirecutter (已离职，现Pillar4 Media)

### 6.3 飞书表格写入规范

```python
# 写入新编辑信息时，必须标注信息来源
{
  "editor": "编辑名",
  "source": "Web Search / LinkedIn / 官网Bio / PR反馈",
  "verified_date": "YYYY-MM-DD",
  "verified_by": "Eden/Chloe/Anna/AI"
}
```

---

## 七、工具链配置

### 7.1 OSINT工具

```bash
# Sherlock (社交账号枚举)
# 安装
python3.11 -m venv /tmp/sherlock_env
/tmp/sherlock_env/bin/pip install sherlock-project

# 使用（搜索编辑用户名）
/tmp/sherlock_env/bin/sherlock --print-found --timeout 8 "username"
```

### 7.2 飞书API写入

```python
# 飞书表格ID: RbPcsD7GNhAVSpt3sA3cCDownNg
# Sheet IDs:
SHEET_IDS = {
    '① 核心媒体库': '3gZBba',
    '② 编辑联系人库': '3hdgis',
    '③ SEO榜单追踪': '3hrJuM',
    '④ 新品营销日历': '3hG5eE',
    '⑥ Pitch策略细化': '1YUf3G',
    '⑦ 媒体台账SOP': '1ZHCp2',
    '⑧ 媒体分级标准': '20Cdhu',
    '⑨ 编辑社交图谱': '2aTyo0',
    '⑩ AI推荐策略': '2b5je8',
    '⑪ 信息来源标注': '2bgO5i',
}
```

---

## 八、与PR团队对齐清单（需本周确认）

- [ ] **P0** BabyCenter：Blake Bakkila已离职，新编辑联系人是谁？
- [ ] **P0** Wirecutter：Caitlin Giddings已离职，新吸奶器责任编辑是谁？
- [ ] **P0** 确认W1已寄送给NBC Select Zoe Malin（"waiting shipping info"状态）
- [ ] **P1** 向Latifah Miles(Babylist)发正式Pitch：`latifah.miles@babylist.com`
- [ ] **P1** 申请NBC Select "Talking Shop"专栏（Zoe Malin明确接受品牌推荐）
- [ ] **P1** 确认GH Institute Baby Gear奖项申报截止日期
- [ ] **P2** 确认Sheet①中422位无编辑信息的媒体是否有对应联系人
- [ ] **P2** 用Semrush/Ahrefs批量补全缺失的DA/流量数据（33%空白）
