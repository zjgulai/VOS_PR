CREATE SCHEMA IF NOT EXISTS pr_core_media;

CREATE TABLE IF NOT EXISTS pr_core_media.schema_migrations (
    migration_id VARCHAR PRIMARY KEY,
    checksum VARCHAR NOT NULL,
    applied_at TIMESTAMP NOT NULL DEFAULT current_timestamp
);

CREATE TABLE IF NOT EXISTS pr_core_media.ctl_import_batch (
    import_version VARCHAR PRIMARY KEY,
    source_file_ref VARCHAR NOT NULL,
    source_file_sha256 VARCHAR NOT NULL,
    source_sheet VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    outlet_count INTEGER NOT NULL,
    journalist_count INTEGER NOT NULL,
    preview_ref VARCHAR NOT NULL,
    approved_by_role VARCHAR,
    approved_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS pr_core_media.ctl_import_record (
    import_record_id VARCHAR PRIMARY KEY,
    import_version VARCHAR NOT NULL,
    source_file_ref VARCHAR NOT NULL,
    source_sheet VARCHAR NOT NULL,
    source_row_ref VARCHAR NOT NULL,
    raw_hash VARCHAR NOT NULL,
    entity_type VARCHAR NOT NULL,
    entity_id VARCHAR,
    raw_record_json VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (import_version)
        REFERENCES pr_core_media.ctl_import_batch(import_version)
);

CREATE TABLE IF NOT EXISTS pr_core_media.ctl_source_capability (
    source_id VARCHAR PRIMARY KEY,
    version VARCHAR NOT NULL,
    edition_id VARCHAR NOT NULL,
    source_type VARCHAR NOT NULL,
    collection_method VARCHAR NOT NULL,
    entrypoint VARCHAR,
    permission_status VARCHAR NOT NULL,
    permission_evidence_ref VARCHAR NOT NULL,
    rights_label VARCHAR NOT NULL,
    allowed_fields_text VARCHAR NOT NULL,
    retention_days INTEGER,
    collection_frequency VARCHAR NOT NULL,
    historical_window_days INTEGER NOT NULL,
    credential_ref VARCHAR,
    access_status VARCHAR NOT NULL,
    last_tested_at TIMESTAMP,
    last_success_at TIMESTAMP,
    fallback_method VARCHAR NOT NULL,
    fallback_source_id VARCHAR,
    owner_role VARCHAR NOT NULL,
    reviewer_role VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS pr_core_media.ctl_collection_job (
    job_id VARCHAR PRIMARY KEY,
    run_id VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    edition_id VARCHAR NOT NULL,
    requested_start TIMESTAMP NOT NULL,
    requested_end TIMESTAMP NOT NULL,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    status VARCHAR NOT NULL,
    items_seen INTEGER NOT NULL,
    items_accepted INTEGER NOT NULL,
    next_cursor VARCHAR,
    error_code VARCHAR,
    safe_error_message VARCHAR,
    recovery_action VARCHAR,
    started_at TIMESTAMP NOT NULL,
    finished_at TIMESTAMP,
    UNIQUE (run_id, source_id, requested_start, requested_end)
);

CREATE TABLE IF NOT EXISTS pr_core_media.dim_outlet (
    outlet_id VARCHAR PRIMARY KEY,
    canonical_name VARCHAR NOT NULL,
    media_type VARCHAR,
    role_tags_text VARCHAR,
    status VARCHAR NOT NULL,
    source_file_ref VARCHAR NOT NULL,
    source_sheet VARCHAR NOT NULL,
    source_row_ref VARCHAR NOT NULL,
    import_version VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS pr_core_media.dim_outlet_edition (
    edition_id VARCHAR PRIMARY KEY,
    outlet_id VARCHAR NOT NULL,
    country VARCHAR NOT NULL,
    language VARCHAR NOT NULL,
    canonical_domain VARCHAR,
    owner_role VARCHAR,
    status VARCHAR NOT NULL,
    verified_at TIMESTAMP,
    verification_evidence_ref VARCHAR,
    source_file_ref VARCHAR NOT NULL,
    source_sheet VARCHAR NOT NULL,
    source_row_ref VARCHAR NOT NULL,
    import_version VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (outlet_id) REFERENCES pr_core_media.dim_outlet(outlet_id),
    UNIQUE (outlet_id, country, language, canonical_domain)
);

CREATE TABLE IF NOT EXISTS pr_core_media.dim_journalist (
    journalist_id VARCHAR PRIMARY KEY,
    public_name VARCHAR NOT NULL,
    public_title VARCHAR,
    identity_status VARCHAR NOT NULL,
    verified_at TIMESTAMP,
    verification_evidence_ref VARCHAR,
    source_file_ref VARCHAR NOT NULL,
    source_sheet VARCHAR NOT NULL,
    source_row_ref VARCHAR NOT NULL,
    import_version VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS pr_core_media.bridge_journalist_affiliation (
    affiliation_id VARCHAR PRIMARY KEY,
    journalist_id VARCHAR NOT NULL,
    edition_id VARCHAR NOT NULL,
    role VARCHAR,
    affiliation_status VARCHAR NOT NULL,
    source_url VARCHAR,
    valid_from TIMESTAMP,
    valid_until TIMESTAMP,
    verified_at TIMESTAMP,
    source_file_ref VARCHAR NOT NULL,
    source_sheet VARCHAR NOT NULL,
    source_row_ref VARCHAR NOT NULL,
    import_version VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (journalist_id)
        REFERENCES pr_core_media.dim_journalist(journalist_id),
    FOREIGN KEY (edition_id)
        REFERENCES pr_core_media.dim_outlet_edition(edition_id)
);

CREATE TABLE IF NOT EXISTS pr_core_media.dim_touchpoint (
    touchpoint_id VARCHAR PRIMARY KEY,
    entity_type VARCHAR NOT NULL,
    entity_id VARCHAR NOT NULL,
    platform VARCHAR NOT NULL,
    public_url VARCHAR NOT NULL,
    ownership_type VARCHAR NOT NULL,
    collection_policy VARCHAR NOT NULL,
    access_status VARCHAR NOT NULL,
    last_checked_at TIMESTAMP,
    source_file_ref VARCHAR NOT NULL,
    source_sheet VARCHAR NOT NULL,
    source_row_ref VARCHAR NOT NULL,
    import_version VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    UNIQUE (entity_type, entity_id, platform, public_url)
);

CREATE TABLE IF NOT EXISTS pr_core_media.ods_raw_envelope (
    envelope_id VARCHAR PRIMARY KEY,
    run_id VARCHAR NOT NULL,
    source_id VARCHAR NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    payload_sha256 VARCHAR NOT NULL,
    raw_object_ref VARCHAR NOT NULL,
    rights_label VARCHAR NOT NULL,
    allowed_fields_text VARCHAR NOT NULL,
    retention_expires_at TIMESTAMP,
    record_count INTEGER NOT NULL,
    deletion_status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    UNIQUE (source_id, payload_sha256)
);

CREATE TABLE IF NOT EXISTS pr_core_media.dwd_document (
    document_id VARCHAR PRIMARY KEY,
    source_id VARCHAR NOT NULL,
    edition_id VARCHAR NOT NULL,
    journalist_id VARCHAR,
    canonical_url VARCHAR NOT NULL,
    published_at TIMESTAMP NOT NULL,
    fetched_at TIMESTAMP NOT NULL,
    title VARCHAR,
    author_text VARCHAR,
    byline_status VARCHAR NOT NULL,
    content_type VARCHAR NOT NULL,
    sponsorship_status VARCHAR NOT NULL,
    text_hash VARCHAR NOT NULL,
    rights_label VARCHAR NOT NULL,
    is_syndicated BOOLEAN NOT NULL,
    canonical_document_id VARCHAR,
    deletion_status VARCHAR NOT NULL,
    raw_object_ref VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (edition_id)
        REFERENCES pr_core_media.dim_outlet_edition(edition_id),
    FOREIGN KEY (journalist_id)
        REFERENCES pr_core_media.dim_journalist(journalist_id),
    UNIQUE (source_id, text_hash)
);

CREATE TABLE IF NOT EXISTS pr_core_media.bridge_document_byline (
    byline_id VARCHAR PRIMARY KEY,
    document_id VARCHAR NOT NULL,
    author_ordinal INTEGER NOT NULL,
    author_text VARCHAR NOT NULL,
    journalist_id VARCHAR,
    byline_status VARCHAR NOT NULL,
    evidence_ref VARCHAR,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (document_id)
        REFERENCES pr_core_media.dwd_document(document_id),
    FOREIGN KEY (journalist_id)
        REFERENCES pr_core_media.dim_journalist(journalist_id),
    UNIQUE (document_id, author_ordinal)
);

CREATE TABLE IF NOT EXISTS pr_core_media.dwd_editorial_signal (
    signal_id VARCHAR PRIMARY KEY,
    document_id VARCHAR NOT NULL,
    edition_id VARCHAR NOT NULL,
    journalist_id VARCHAR,
    signal_type VARCHAR NOT NULL,
    subject_entity VARCHAR,
    topic_key VARCHAR,
    stance VARCHAR NOT NULL,
    claim_text VARCHAR NOT NULL,
    evidence_span VARCHAR,
    sponsorship_status VARCHAR NOT NULL,
    confidence DOUBLE NOT NULL,
    review_status VARCHAR NOT NULL,
    evidence_set_id VARCHAR NOT NULL,
    rule_version VARCHAR NOT NULL,
    model_name VARCHAR,
    model_version VARCHAR,
    prompt_version VARCHAR,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (document_id)
        REFERENCES pr_core_media.dwd_document(document_id),
    FOREIGN KEY (edition_id)
        REFERENCES pr_core_media.dim_outlet_edition(edition_id),
    FOREIGN KEY (journalist_id)
        REFERENCES pr_core_media.dim_journalist(journalist_id)
);

CREATE TABLE IF NOT EXISTS pr_core_media.dwd_claim (
    claim_id VARCHAR PRIMARY KEY,
    claim_text VARCHAR NOT NULL,
    claimant_text VARCHAR NOT NULL,
    subject VARCHAR NOT NULL,
    predicate VARCHAR NOT NULL,
    time_scope VARCHAR,
    verification_status VARCHAR NOT NULL,
    confidence DOUBLE NOT NULL,
    markets_text VARCHAR NOT NULL,
    entities_text VARCHAR,
    model_name VARCHAR,
    model_version VARCHAR NOT NULL,
    prompt_version VARCHAR,
    review_status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    valid_until TIMESTAMP
);

CREATE TABLE IF NOT EXISTS pr_core_media.dwd_evidence (
    evidence_id VARCHAR PRIMARY KEY,
    claim_id VARCHAR NOT NULL,
    document_id VARCHAR NOT NULL,
    quote_span VARCHAR,
    supports_or_refutes VARCHAR NOT NULL,
    evidence_grade VARCHAR NOT NULL,
    observed_at TIMESTAMP NOT NULL,
    valid_until TIMESTAMP,
    redaction_status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (claim_id) REFERENCES pr_core_media.dwd_claim(claim_id),
    FOREIGN KEY (document_id)
        REFERENCES pr_core_media.dwd_document(document_id)
);

CREATE TABLE IF NOT EXISTS pr_core_media.bridge_evidence_set_item (
    evidence_set_id VARCHAR NOT NULL,
    evidence_id VARCHAR NOT NULL,
    ordinal INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL,
    PRIMARY KEY (evidence_set_id, evidence_id),
    FOREIGN KEY (evidence_id)
        REFERENCES pr_core_media.dwd_evidence(evidence_id)
);

CREATE TABLE IF NOT EXISTS pr_core_media.dwd_relationship_event (
    event_id VARCHAR PRIMARY KEY,
    journalist_id VARCHAR,
    edition_id VARCHAR NOT NULL,
    event_type VARCHAR NOT NULL,
    occurred_at TIMESTAMP,
    outcome VARCHAR,
    owner_role VARCHAR,
    source_type VARCHAR NOT NULL,
    source_row_ref VARCHAR,
    next_follow_up_at TIMESTAMP,
    review_status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (journalist_id)
        REFERENCES pr_core_media.dim_journalist(journalist_id),
    FOREIGN KEY (edition_id)
        REFERENCES pr_core_media.dim_outlet_edition(edition_id)
);

CREATE TABLE IF NOT EXISTS pr_core_media.dwd_pitch_constraint (
    constraint_id VARCHAR PRIMARY KEY,
    journalist_id VARCHAR,
    edition_id VARCHAR,
    reason_code VARCHAR NOT NULL,
    starts_at TIMESTAMP,
    ends_at TIMESTAMP,
    status VARCHAR NOT NULL,
    evidence_ref VARCHAR,
    approved_by_role VARCHAR,
    approved_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (journalist_id)
        REFERENCES pr_core_media.dim_journalist(journalist_id),
    FOREIGN KEY (edition_id)
        REFERENCES pr_core_media.dim_outlet_edition(edition_id)
);

CREATE TABLE IF NOT EXISTS pr_core_media.dws_source_coverage (
    coverage_id VARCHAR PRIMARY KEY,
    source_id VARCHAR NOT NULL,
    edition_id VARCHAR NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    actual_coverage_start TIMESTAMP,
    actual_coverage_end TIMESTAMP,
    status VARCHAR NOT NULL,
    documents_seen INTEGER NOT NULL,
    documents_accepted INTEGER NOT NULL,
    last_success_at TIMESTAMP,
    gap_reason VARCHAR,
    recovery_action VARCHAR,
    generated_at TIMESTAMP NOT NULL,
    UNIQUE (source_id, edition_id, period_start, period_end)
);

CREATE TABLE IF NOT EXISTS pr_core_media.dws_edition_period (
    edition_id VARCHAR NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    topic_mix_text VARCHAR NOT NULL,
    stance_mix_text VARCHAR NOT NULL,
    document_count INTEGER NOT NULL,
    coverage_status VARCHAR NOT NULL,
    generated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (edition_id, period_start, period_end)
);

CREATE TABLE IF NOT EXISTS pr_core_media.dws_journalist_period (
    journalist_id VARCHAR NOT NULL,
    period_start TIMESTAMP NOT NULL,
    period_end TIMESTAMP NOT NULL,
    topic_mix_text VARCHAR NOT NULL,
    competitor_view_mix_text VARCHAR NOT NULL,
    document_count INTEGER NOT NULL,
    coverage_status VARCHAR NOT NULL,
    generated_at TIMESTAMP NOT NULL,
    PRIMARY KEY (journalist_id, period_start, period_end)
);

CREATE TABLE IF NOT EXISTS pr_core_media.ads_media_brief (
    brief_id VARCHAR PRIMARY KEY,
    scope_type VARCHAR NOT NULL,
    scope_id VARCHAR NOT NULL,
    window_start TIMESTAMP NOT NULL,
    window_end TIMESTAMP NOT NULL,
    baseline_start TIMESTAMP,
    baseline_end TIMESTAMP,
    actual_coverage_start TIMESTAMP,
    actual_coverage_end TIMESTAMP,
    document_count INTEGER NOT NULL,
    recent_focus_text VARCHAR NOT NULL,
    competitor_view_ids_text VARCHAR,
    momcozy_presence_status VARCHAR NOT NULL,
    opportunity_ids_text VARCHAR,
    media_risk_ids_text VARCHAR,
    pitch_readiness VARCHAR NOT NULL,
    no_pitch_reason_codes_text VARCHAR,
    coverage_status VARCHAR NOT NULL,
    uncertainty_text VARCHAR NOT NULL,
    evidence_set_id VARCHAR NOT NULL,
    rule_version VARCHAR NOT NULL,
    model_name VARCHAR,
    model_version VARCHAR,
    prompt_version VARCHAR,
    review_status VARCHAR NOT NULL,
    generated_at TIMESTAMP NOT NULL,
    reviewed_at TIMESTAMP,
    UNIQUE (
        scope_type,
        scope_id,
        window_start,
        window_end,
        rule_version,
        model_version
    )
);

CREATE TABLE IF NOT EXISTS pr_core_media.ads_opportunity (
    opportunity_id VARCHAR PRIMARY KEY,
    edition_id VARCHAR NOT NULL,
    journalist_id VARCHAR,
    topic_fit DOUBLE,
    timing DOUBLE,
    competitor_gap DOUBLE,
    evidence_strength DOUBLE,
    asset_gap VARCHAR,
    relationship_penalty DOUBLE,
    risk_penalty DOUBLE,
    rank_group VARCHAR NOT NULL,
    angle VARCHAR NOT NULL,
    why_now VARCHAR NOT NULL,
    evidence_set_id VARCHAR NOT NULL,
    review_status VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS pr_core_media.ads_media_risk (
    media_risk_id VARCHAR PRIMARY KEY,
    document_id VARCHAR NOT NULL,
    edition_id VARCHAR NOT NULL,
    journalist_id VARCHAR,
    risk_type VARCHAR NOT NULL,
    brand_relevance VARCHAR NOT NULL,
    product_relevance VARCHAR NOT NULL,
    category_relevance VARCHAR NOT NULL,
    evidence_span VARCHAR NOT NULL,
    sponsorship_status VARCHAR NOT NULL,
    priority VARCHAR NOT NULL,
    review_status VARCHAR NOT NULL,
    escalation_result VARCHAR,
    evidence_set_id VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    FOREIGN KEY (document_id)
        REFERENCES pr_core_media.dwd_document(document_id)
);

CREATE TABLE IF NOT EXISTS pr_core_media.ads_action (
    action_id VARCHAR PRIMARY KEY,
    action_type VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    why_now VARCHAR NOT NULL,
    edition_id VARCHAR NOT NULL,
    journalist_id VARCHAR,
    target_outlet_text VARCHAR NOT NULL,
    target_journalist_text VARCHAR,
    content_angle VARCHAR NOT NULL,
    required_assets_text VARCHAR,
    owner_role VARCHAR NOT NULL,
    due_at TIMESTAMP,
    success_metric VARCHAR NOT NULL,
    risk_text VARCHAR NOT NULL,
    pitch_constraint_ids_text VARCHAR,
    source_insight_ids_text VARCHAR NOT NULL,
    evidence_set_id VARCHAR NOT NULL,
    approval_status VARCHAR NOT NULL,
    execution_status VARCHAR NOT NULL,
    reviewer_note VARCHAR,
    result_note VARCHAR,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE TABLE IF NOT EXISTS pr_core_media.ads_feedback (
    feedback_id VARCHAR PRIMARY KEY,
    object_type VARCHAR NOT NULL,
    object_id VARCHAR NOT NULL,
    label VARCHAR NOT NULL,
    reason VARCHAR NOT NULL,
    reviewer_role VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL
);
