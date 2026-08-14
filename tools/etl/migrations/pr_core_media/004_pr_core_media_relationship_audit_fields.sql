ALTER TABLE pr_core_media.dwd_pitch_constraint
ADD COLUMN IF NOT EXISTS topic_key VARCHAR;

ALTER TABLE pr_core_media.dwd_pitch_constraint
ADD COLUMN IF NOT EXISTS evidence_refs_text VARCHAR;

ALTER TABLE pr_core_media.dwd_pitch_constraint
ADD COLUMN IF NOT EXISTS rule_version VARCHAR;

ALTER TABLE pr_core_media.dwd_pitch_constraint
ADD COLUMN IF NOT EXISTS override_evidence_ref VARCHAR;
