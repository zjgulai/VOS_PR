CREATE TABLE IF NOT EXISTS pr_core_media.ctl_brief_review (
    review_id VARCHAR PRIMARY KEY,
    brief_id VARCHAR NOT NULL,
    command VARCHAR NOT NULL,
    from_status VARCHAR NOT NULL,
    to_status VARCHAR NOT NULL,
    reviewer_role VARCHAR NOT NULL,
    note VARCHAR,
    reviewed_at TIMESTAMP NOT NULL,
    FOREIGN KEY (brief_id) REFERENCES pr_core_media.ads_media_brief(brief_id)
);
