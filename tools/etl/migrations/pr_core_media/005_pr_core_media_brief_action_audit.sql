ALTER TABLE pr_core_media.ads_media_brief
ADD COLUMN IF NOT EXISTS fact_items_text VARCHAR;

ALTER TABLE pr_core_media.ads_media_brief
ADD COLUMN IF NOT EXISTS inference_items_text VARCHAR;

ALTER TABLE pr_core_media.ads_media_brief
ADD COLUMN IF NOT EXISTS evidence_ids_text VARCHAR;

ALTER TABLE pr_core_media.ads_media_brief
ADD COLUMN IF NOT EXISTS registry_version VARCHAR;

ALTER TABLE pr_core_media.ads_media_brief
ADD COLUMN IF NOT EXISTS pitch_constraint_ids_text VARCHAR;

ALTER TABLE pr_core_media.ads_media_brief
ADD COLUMN IF NOT EXISTS edition_id VARCHAR;

ALTER TABLE pr_core_media.ads_media_brief
ADD COLUMN IF NOT EXISTS journalist_id VARCHAR;

ALTER TABLE pr_core_media.ads_action
ADD COLUMN IF NOT EXISTS approved_by_role VARCHAR;

ALTER TABLE pr_core_media.ads_action
ADD COLUMN IF NOT EXISTS approved_at TIMESTAMP;

ALTER TABLE pr_core_media.ads_action
ADD COLUMN IF NOT EXISTS brief_id VARCHAR;

CREATE TABLE IF NOT EXISTS pr_core_media.ctl_action_transition (
    transition_id VARCHAR PRIMARY KEY,
    action_id VARCHAR NOT NULL,
    command VARCHAR NOT NULL,
    from_approval_status VARCHAR NOT NULL,
    to_approval_status VARCHAR NOT NULL,
    from_execution_status VARCHAR NOT NULL,
    to_execution_status VARCHAR NOT NULL,
    actor_role VARCHAR NOT NULL,
    note VARCHAR,
    occurred_at TIMESTAMP NOT NULL,
    FOREIGN KEY (action_id) REFERENCES pr_core_media.ads_action(action_id)
);
