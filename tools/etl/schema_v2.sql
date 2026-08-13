-- ============================================================================
-- VOC/PR/Social 数据仓库核心数据契约 v2.0
-- 目标：空库执行本文件即可完整重建全部表结构（修复「schema 不可复现」问题）
-- 引擎：DuckDB
-- 来源：VR/PRD-Momcozy-Social-Intelligence-Agent.md 第五章 + 现有 voc.duckdb
-- 原则：原始事实 / 派生分析 / 人工判断 三层分离；跨平台 ID 一律 VARCHAR；
--       时间同时保存 published_at + collected_at + metric_observed_at
-- ============================================================================

-- ───────────────────────── 控制层（Control）────────────────────────────

CREATE TABLE IF NOT EXISTS dim_monitor_scope (
    scope_id         VARCHAR PRIMARY KEY,
    workspace_id     VARCHAR NOT NULL,
    scope_type       VARCHAR NOT NULL,          -- brand/product/topic/competitor/creator/community
    canonical_name   VARCHAR NOT NULL,
    aliases          VARCHAR[],
    excluded_terms   VARCHAR[],
    platforms        VARCHAR[],
    regions          VARCHAR[],
    languages        VARCHAR[],
    status           VARCHAR NOT NULL DEFAULT 'active',  -- draft/active/paused/retired
    source_of_truth  VARCHAR,
    version          VARCHAR NOT NULL DEFAULT '1.0',
    created_at       TIMESTAMP NOT NULL,
    updated_at       TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_platform_account (
    platform_account_id  VARCHAR PRIMARY KEY,
    provider             VARCHAR NOT NULL,       -- reddit/tiktok/instagram/youtube/facebook
    handle               VARCHAR NOT NULL,
    account_type         VARCHAR NOT NULL,       -- competitor/creator/own_brand/media
    brand_key            VARCHAR,                -- 关联 dim_competitor.brand_key
    verification_status  VARCHAR NOT NULL DEFAULT 'unverified',  -- verified/unverified
    product_line         VARCHAR,
    priority             VARCHAR DEFAULT 'P2',
    created_at           TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS dim_creator (
    creator_id       VARCHAR PRIMARY KEY,        -- {platform}_{handle}
    platform         VARCHAR NOT NULL,
    public_handle    VARCHAR NOT NULL,
    content_niche    VARCHAR,
    region           VARCHAR,
    follower_tier    VARCHAR,
    is_active        BOOLEAN DEFAULT TRUE,
    first_seen_at    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_product_alias (
    product_id      VARCHAR PRIMARY KEY,
    standard_model  VARCHAR NOT NULL,            -- 标准型号，如 M5 Smart
    alias           VARCHAR NOT NULL,            -- 别名/BP 编码，如 BP380
    source_url      VARCHAR,
    valid_from      DATE,
    valid_until     DATE
);

CREATE TABLE IF NOT EXISTS connector_registry (
    provider          VARCHAR NOT NULL,
    strategy          VARCHAR NOT NULL,          -- official_api/licensed_provider/manual_import/tikhub/apify
    fields            VARCHAR[],
    permission_status VARCHAR NOT NULL DEFAULT 'pending',  -- authorized/pending/partial/blocked
    coverage_grade    VARCHAR NOT NULL DEFAULT 'unknown',  -- A/B/C/D/unknown
    last_tested_at    TIMESTAMP,
    PRIMARY KEY (provider, strategy)
);

-- ───────────────────────── 原始层（ODS）─────────────────────────────────

CREATE TABLE IF NOT EXISTS ods_provider_payload (
    job_id          VARCHAR,
    provider        VARCHAR NOT NULL,
    request_hash    VARCHAR NOT NULL,
    raw_object_ref  VARCHAR NOT NULL,            -- object://raw/2026/08/11/reddit/xxx.json
    received_at     TIMESTAMP NOT NULL,
    PRIMARY KEY (provider, request_hash)
);

CREATE TABLE IF NOT EXISTS ods_collection_job (
    job_id         VARCHAR PRIMARY KEY,
    scope_id       VARCHAR,
    provider       VARCHAR NOT NULL,
    cursor         VARCHAR,
    status         VARCHAR NOT NULL,             -- pending/running/success/failed/delayed
    request_count  INTEGER DEFAULT 0,
    error_code     VARCHAR,
    started_at     TIMESTAMP,
    finished_at    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ods_metric_snapshot (
    provider_item_id  VARCHAR NOT NULL,
    observed_at       TIMESTAMP NOT NULL,
    views             INTEGER,
    likes             INTEGER,
    comments          INTEGER,
    shares            INTEGER,
    followers         INTEGER,
    PRIMARY KEY (provider_item_id, observed_at)
);

-- ───────────────────────── 明细层（DWD）────────────────────────────────

CREATE TABLE IF NOT EXISTS dwd_canonical_mention (
    mention_id          VARCHAR PRIMARY KEY,     -- {provider}_{provider_item_id}
    provider            VARCHAR NOT NULL,
    provider_item_id    VARCHAR NOT NULL,
    provider_item_type  VARCHAR NOT NULL,        -- post/comment/video/reel/story/thread/article
    source_url          VARCHAR,
    author_ref          VARCHAR,                 -- 脱敏/作用域作者引用
    community_ref       VARCHAR,                 -- subreddit/group/channel
    text_excerpt        VARCHAR,
    language            VARCHAR NOT NULL,
    region              VARCHAR,
    published_at        TIMESTAMP NOT NULL,
    collected_at        TIMESTAMP NOT NULL,
    collection_strategy VARCHAR NOT NULL,        -- official_api/authorized_export/licensed_provider/manual_import/tikhub/apify
    coverage_grade      VARCHAR NOT NULL,        -- A/B/C/D/unknown
    deletion_status     VARCHAR NOT NULL DEFAULT 'active',
    content_hash        VARCHAR NOT NULL,        -- 去重与删除定位
    raw_object_ref      VARCHAR NOT NULL,
    UNIQUE (provider, provider_item_id)
);

CREATE TABLE IF NOT EXISTS dwd_annotation (
    annotation_id   VARCHAR PRIMARY KEY,
    mention_id      VARCHAR NOT NULL,
    annotation_type VARCHAR NOT NULL,            -- topic/need/pain/sentiment/entity/risk
    label           VARCHAR,
    confidence      DOUBLE,
    model_name      VARCHAR,
    model_version   VARCHAR,
    created_at      TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS dwd_evidence (
    evidence_id      VARCHAR PRIMARY KEY,
    mention_id       VARCHAR NOT NULL,
    evidence_type    VARCHAR NOT NULL,           -- quote/url/metric/coverage
    quote_text       VARCHAR,
    source_url       VARCHAR,
    observed_at      TIMESTAMP NOT NULL,
    valid_until      TIMESTAMP,
    evidence_grade   VARCHAR NOT NULL,           -- A/B/C/D
    redaction_status VARCHAR NOT NULL DEFAULT 'none',
    FOREIGN KEY (mention_id) REFERENCES dwd_canonical_mention(mention_id)
);

CREATE TABLE IF NOT EXISTS dwd_creator_content (
    content_id      VARCHAR PRIMARY KEY,
    creator_id      VARCHAR NOT NULL,
    format          VARCHAR,                     -- video/reel/post/short
    topic_key       VARCHAR,
    sponsored_signal VARCHAR,                    -- none/ad/gifted/paid_partnership
    published_at    TIMESTAMP
);

-- 现有统一内容表（social_posts），保留原始 31 列结构并补约束
CREATE TABLE IF NOT EXISTS social_posts (
    post_id              VARCHAR PRIMARY KEY,
    platform_code        VARCHAR NOT NULL,
    account_handle       VARCHAR,
    account_type         VARCHAR,
    competitor_brand     VARCHAR,
    creator_id           VARCHAR,
    content_type         VARCHAR,
    title                VARCHAR,
    body_text            VARCHAR,
    hashtags             VARCHAR[],
    bgm_title            VARCHAR,
    bgm_author           VARCHAR,
    published_at         TIMESTAMP WITH TIME ZONE,
    fetched_at           TIMESTAMP WITH TIME ZONE,
    view_count           INTEGER,
    like_count           INTEGER,
    comment_count        INTEGER,
    share_count          INTEGER,
    engagement_rate      DOUBLE,
    view_velocity_24h    INTEGER,
    is_viral_flag        BOOLEAN,
    sentiment_label      VARCHAR,
    topics               VARCHAR[],
    pain_points          VARCHAR[],
    is_paid_collab       BOOLEAN,
    brand_mentions       VARCHAR[],
    country_code         VARCHAR,
    language             VARCHAR,
    is_processed         BOOLEAN,
    content_quality_score DOUBLE,
    sev_level            VARCHAR
);

-- ───────────────────────── 汇总层（DWS）────────────────────────────────

CREATE TABLE IF NOT EXISTS dws_topic_daily (
    stat_date     DATE NOT NULL,
    platform      VARCHAR NOT NULL,
    topic_key     VARCHAR NOT NULL,
    mention_count INTEGER DEFAULT 0,
    author_count  INTEGER DEFAULT 0,
    sentiment     VARCHAR,
    momentum      DOUBLE,
    PRIMARY KEY (stat_date, platform, topic_key)
);

CREATE TABLE IF NOT EXISTS dws_competitor_content_daily (
    stat_date      DATE NOT NULL,
    competitor_id  VARCHAR NOT NULL,
    content_type   VARCHAR NOT NULL,
    content_count  INTEGER DEFAULT 0,
    outlier_count  INTEGER DEFAULT 0,
    PRIMARY KEY (stat_date, competitor_id, content_type)
);

CREATE TABLE IF NOT EXISTS dws_trend_snapshot (
    trend_key    VARCHAR NOT NULL,
    platform     VARCHAR NOT NULL,
    observed_at  TIMESTAMP NOT NULL,
    volume       INTEGER,
    creator_count INTEGER,
    momentum     DOUBLE,
    PRIMARY KEY (trend_key, platform, observed_at)
);

CREATE TABLE IF NOT EXISTS dws_creator_period (
    creator_id   VARCHAR NOT NULL,
    period_start DATE NOT NULL,
    period_end   DATE NOT NULL,
    topic_mix    VARCHAR[],
    format_mix   VARCHAR[],
    performance  DOUBLE,
    PRIMARY KEY (creator_id, period_start)
);

-- ───────────────────────── 应用层（ADS）────────────────────────────────

CREATE TABLE IF NOT EXISTS ads_insight (
    insight_id       VARCHAR PRIMARY KEY,
    insight_type     VARCHAR NOT NULL,           -- user_need/pain_point/competitor_action/trend/creator_signal
    topic_key        VARCHAR,
    title            VARCHAR NOT NULL,
    fact_text        VARCHAR NOT NULL,           -- 只写证据支持的事实
    inference_text   VARCHAR,                    -- 模型推断，单独标识
    uncertainty_text VARCHAR,                    -- 限制与未知
    sample_size      INTEGER NOT NULL,
    evidence_set_id  VARCHAR NOT NULL,
    data_coverage    VARCHAR NOT NULL,           -- complete/partial/sparse/unknown
    model_name       VARCHAR,
    model_version    VARCHAR,
    prompt_version   VARCHAR,
    review_status    VARCHAR NOT NULL DEFAULT 'pending_review',  -- pending_review/verified/rejected/expired
    created_at       TIMESTAMP NOT NULL,
    valid_until      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS ads_action (
    action_id          VARCHAR PRIMARY KEY,
    action_type        VARCHAR NOT NULL,         -- topic_response/trend_followup/content_borrow/creator_collab/risk_response/pitch/seeding
    title              VARCHAR NOT NULL,
    content_angle      VARCHAR NOT NULL,
    platforms          VARCHAR[],
    owner_role         VARCHAR NOT NULL,         -- 角色，非个人账号
    due_at             TIMESTAMP,
    evidence_set_id    VARCHAR NOT NULL,
    source_insight_ids VARCHAR[],
    approval_status    VARCHAR NOT NULL DEFAULT 'pending',   -- pending/approved/rejected/blocked/expired
    execution_status   VARCHAR NOT NULL DEFAULT 'not_started',  -- not_started/in_progress/done/cancelled
    reviewer_note      VARCHAR,
    result_note        VARCHAR,
    created_at         TIMESTAMP NOT NULL,
    updated_at         TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS ads_report (
    report_id        VARCHAR PRIMARY KEY,
    report_type      VARCHAR NOT NULL,           -- pr_weekly/social_weekly/daily
    period_start     DATE NOT NULL,
    period_end       DATE NOT NULL,
    coverage_summary VARCHAR,
    render_ref       VARCHAR,
    model_version    VARCHAR,
    created_at       TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS ads_feedback (
    feedback_id   VARCHAR PRIMARY KEY,
    object_type   VARCHAR NOT NULL,              -- insight/action/mention/annotation
    object_id     VARCHAR NOT NULL,
    label         VARCHAR,
    reason        VARCHAR,
    reviewer_role VARCHAR,
    created_at    TIMESTAMP NOT NULL
);

-- ───────────────────────── 竞品/媒体维度表 ──────────────────────────────

CREATE TABLE IF NOT EXISTS dim_competitor (
    brand_key    VARCHAR PRIMARY KEY,
    name         VARCHAR NOT NULL,
    origin       VARCHAR,
    tier         VARCHAR,                        -- T1/T2/T3
    priority     VARCHAR,                        -- P0/P1/P2
    product_line VARCHAR,                        -- pump/feeding_appliance/both
    models       VARCHAR[],
    tiktok       VARCHAR,
    instagram    VARCHAR,
    youtube      VARCHAR,
    pr_keywords  VARCHAR[],
    source       VARCHAR DEFAULT 'config/competitor_dictionary.json'
);

CREATE TABLE IF NOT EXISTS dim_media_contacts (
    contact_id     VARCHAR PRIMARY KEY,
    media_name     VARCHAR NOT NULL,
    editor_name    VARCHAR,
    beat           VARCHAR,
    platform_id    VARCHAR,                      -- 关联平台维度表
    pitch_history  JSON,
    cooldown_until DATE,
    pitch_result   VARCHAR,                      -- accepted/rejected/no_reply/in_progress
    notes          VARCHAR,
    last_updated   DATE
);

-- ───────────────────────── PR 专项表 ───────────────────────────────────

CREATE TABLE IF NOT EXISTS pr_articles (
    article_id        VARCHAR PRIMARY KEY,
    source_id         VARCHAR NOT NULL,
    source_name       VARCHAR,
    source_type       VARCHAR,                   -- pr_wire/tech/baby_media/women_media/review_media/legal
    country           VARCHAR,
    language          VARCHAR,
    title             VARCHAR,
    url               VARCHAR,
    published_at      TIMESTAMP,
    fetched_at        TIMESTAMP,
    body_snippet      VARCHAR,
    keywords_matched  VARCHAR[],
    brand_mentions    VARCHAR[],
    risk_tier         VARCHAR,                   -- P0/P1/none
    sentiment_label   VARCHAR,
    topics            VARCHAR[],
    summary_cn        VARCHAR,
    is_processed      BOOLEAN DEFAULT FALSE,
    UNIQUE (source_id, url)
);

CREATE TABLE IF NOT EXISTS pr_risk_signals (
    signal_id        VARCHAR PRIMARY KEY,
    article_id       VARCHAR,
    signal_type      VARCHAR,                    -- regulatory/legal/reputational/product_safety
    severity_score   DOUBLE,
    velocity_score   DOUBLE,
    source_authority DOUBLE,
    brand_proximity  DOUBLE,
    corroboration    DOUBLE,
    final_risk_score DOUBLE,
    sev_level        VARCHAR,
    detected_at      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pr_opportunities (
    opportunity_id  VARCHAR PRIMARY KEY,
    source_article_id VARCHAR,
    opportunity_type VARCHAR,                    -- pitch/editorial_gap/award/op_ed/seeding
    media_name      VARCHAR,
    angle           VARCHAR,
    window_start    DATE,
    window_end      DATE,
    required_assets VARCHAR[],
    status          VARCHAR DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS pr_weekly_reports (
    report_id      VARCHAR PRIMARY KEY,
    week           VARCHAR,                      -- 2026-W33
    report_path    VARCHAR,
    generated_at   TIMESTAMP,
    status         VARCHAR DEFAULT 'draft'
);

CREATE TABLE IF NOT EXISTS social_trends (
    trend_id      VARCHAR PRIMARY KEY,
    platform      VARCHAR NOT NULL,
    trend_type    VARCHAR,                       -- hashtag/bgm/template
    trend_key     VARCHAR,
    first_seen    TIMESTAMP,
    last_seen     TIMESTAMP,
    volume        INTEGER,
    momentum      DOUBLE,
    brand_relevance VARCHAR,                     -- high/medium/low
    window_end    TIMESTAMP
);

CREATE TABLE IF NOT EXISTS dim_competitor_kol_collabs (
    collab_id          VARCHAR PRIMARY KEY,
    competitor_brand   VARCHAR,
    creator_id         VARCHAR,
    platform_code      VARCHAR,
    post_id            VARCHAR,
    post_url           VARCHAR,
    post_title         VARCHAR,
    post_body          VARCHAR,
    hashtags           VARCHAR[],
    published_at       TIMESTAMP,
    fetched_at         TIMESTAMP,
    is_paid_collab     BOOLEAN,
    collab_type        VARCHAR,
    collab_evidence    VARCHAR,
    content_theme      VARCHAR,
    content_format     VARCHAR,
    product_mentioned  VARCHAR[],
    competitor_angle   VARCHAR,
    view_count         INTEGER,
    like_count         INTEGER,
    comment_count      INTEGER,
    share_count        INTEGER,
    engagement_rate    DOUBLE,
    view_velocity_7d   INTEGER,
    is_viral           BOOLEAN,
    is_repeat_collab   BOOLEAN,
    collab_sequence_num INTEGER,
    discovery_method   VARCHAR,
    search_keyword     VARCHAR,
    verified           BOOLEAN,
    notes              VARCHAR
);

CREATE TABLE IF NOT EXISTS dim_creator_profiles (
    creator_id          VARCHAR PRIMARY KEY,
    creator_name        VARCHAR,
    platform_code       VARCHAR,
    account_handle      VARCHAR,
    account_url         VARCHAR,
    follower_count      INTEGER,
    follower_tier       VARCHAR,
    primary_topics      VARCHAR[],
    content_style       VARCHAR,
    avg_view_count      INTEGER,
    avg_engagement_rate DOUBLE,
    past_brand_collabs  JSON,
    momcozy_mentioned   BOOLEAN,
    momcozy_sentiment   VARCHAR,
    competitor_collabs  VARCHAR[],
    is_paid_collab_flag BOOLEAN,
    audience_geo_top3   VARCHAR[],
    audience_age_range  VARCHAR,
    collab_potential    VARCHAR,
    recent_topics_7d    VARCHAR[],
    recent_viral_url    VARCHAR,
    topic_shift_alert   BOOLEAN,
    data_source         VARCHAR,
    first_seen_at       TIMESTAMP,
    last_updated        DATE,
    is_active           BOOLEAN
);

-- ============================================================================
-- 结束：共 30 张表，覆盖 PRD 第五章数据模型 + 现有 voc.duckdb 全部新表。
-- 验证：python3 -c "import duckdb; con=duckdb.connect(':memory:'); con.execute(open('tools/etl/schema_v2.sql').read()); print(con.execute('SELECT count(*) FROM duckdb_tables()').fetchone())"
-- ============================================================================
