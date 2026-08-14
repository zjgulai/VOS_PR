CREATE TABLE IF NOT EXISTS pr_core_media.ctl_deletion_audit (
    audit_id VARCHAR PRIMARY KEY,
    object_type VARCHAR NOT NULL,
    object_id VARCHAR NOT NULL,
    requested_by_role VARCHAR NOT NULL,
    reason_code VARCHAR NOT NULL,
    status VARCHAR NOT NULL,
    target_count INTEGER NOT NULL,
    unresolved_dependencies_text VARCHAR NOT NULL,
    created_at TIMESTAMP NOT NULL,
    approved_by_role VARCHAR,
    approved_at TIMESTAMP,
    completed_at TIMESTAMP,
    safe_error_message VARCHAR
);

CREATE TABLE IF NOT EXISTS pr_core_media.ctl_deletion_target (
    target_id VARCHAR PRIMARY KEY,
    audit_id VARCHAR NOT NULL,
    table_name VARCHAR NOT NULL,
    selector_json VARCHAR NOT NULL,
    target_action VARCHAR NOT NULL,
    located_count INTEGER NOT NULL,
    execution_status VARCHAR NOT NULL,
    executed_count INTEGER NOT NULL,
    error_code VARCHAR,
    created_at TIMESTAMP NOT NULL,
    executed_at TIMESTAMP,
    FOREIGN KEY (audit_id)
        REFERENCES pr_core_media.ctl_deletion_audit(audit_id)
);
