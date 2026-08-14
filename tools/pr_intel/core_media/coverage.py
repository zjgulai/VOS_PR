"""Coverage aggregation that never converts failure or unknown into a true zero."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional, Sequence

from tools.pr_intel.core_media.connectors.base import CollectionResult
from tools.pr_intel.core_media.contracts import CoverageStatus, stable_id


@dataclass(frozen=True)
class CoverageJob:
    request_id: str
    requested_start: datetime
    requested_end: datetime
    actual_start: Optional[datetime]
    actual_end: Optional[datetime]
    result: CollectionResult
    last_success_at: Optional[str]


@dataclass(frozen=True)
class CoverageEntry:
    coverage_id: str
    source_id: str
    edition_id: str
    requested_start: str
    requested_end: str
    actual_start: Optional[str]
    actual_end: Optional[str]
    documents_seen: int
    documents_accepted: int
    status: CoverageStatus
    gap_reason: Optional[str]
    last_success_at: Optional[str]
    recovery_action: str
    display_message: str


@dataclass(frozen=True)
class CoverageReport:
    requested_start: str
    requested_end: str
    actual_start: Optional[str]
    actual_end: Optional[str]
    documents_seen: int
    documents_accepted: int
    status: CoverageStatus
    entries: tuple[CoverageEntry, ...]
    generated_at: str


_STATUS_COPY = {
    CoverageStatus.COMPLETE: (
        None,
        "按计划继续下一周期",
        "本次来源检查完成，结论仅适用于显示的实际覆盖窗口。",
    ),
    CoverageStatus.PARTIAL: (
        "partial_source_coverage",
        "查看缺失记录并运行人工 fallback",
        "本次只有部分覆盖，任何趋势或观点结论都必须显示缺口。",
    ),
    CoverageStatus.NO_MATCH: (
        "no_relevant_match_in_observed_window",
        "保留为真实零匹配并按下个周期复查",
        "本次获准且实际覆盖的范围内未匹配到相关文档；不等同于媒体未报道。",
    ),
    CoverageStatus.SOURCE_UNAVAILABLE: (
        "source_unavailable",
        "检查入口状态或切换到人工 URL fallback",
        "来源当前不可用，无法判断是否存在相关报道。",
    ),
    CoverageStatus.RATE_LIMITED: (
        "rate_limited",
        "遵守 Retry-After 后重试，不扩大并发",
        "来源触发限速，本周期覆盖不完整，不能解释为零内容。",
    ),
    CoverageStatus.SCHEMA_CHANGED: (
        "schema_changed",
        "暂停该连接器并人工核验 selector/feed 结构",
        "来源结构发生变化，解析结果不可用于业务结论。",
    ),
    CoverageStatus.PROFILE_INVALID: (
        "profile_invalid",
        "核验作者页、任职状态和替代公开入口",
        "作者入口失效或身份待核验，编辑级结论已暂停。",
    ),
    CoverageStatus.PERMISSION_PENDING: (
        "permission_pending",
        "完成权利、字段和保留期签字",
        "来源权限尚未批准，本周期没有执行真实采集。",
    ),
    CoverageStatus.UNKNOWN: (
        "unknown",
        "人工检查运行记录并明确分类",
        "覆盖状态未知，不得生成确定性结论。",
    ),
}


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("coverage_datetime_timezone_required")
    return (
        value.astimezone(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def build_coverage_report(
    jobs: Sequence[CoverageJob],
    window: tuple[datetime, datetime],
) -> CoverageReport:
    requested_start, requested_end = window
    if requested_start >= requested_end:
        raise ValueError("coverage_window_invalid")
    window_start = _iso(requested_start)
    window_end = _iso(requested_end)
    entries: list[CoverageEntry] = []
    actual_starts: list[datetime] = []
    actual_ends: list[datetime] = []

    for job in jobs:
        if job.requested_start != requested_start or job.requested_end != requested_end:
            raise ValueError("coverage_job_window_mismatch")
        if (job.actual_start is None) != (job.actual_end is None):
            raise ValueError("actual_coverage_window_incomplete")
        if job.actual_start is not None and job.actual_end is not None:
            if job.actual_start > job.actual_end:
                raise ValueError("actual_coverage_window_invalid")
            actual_starts.append(job.actual_start)
            actual_ends.append(job.actual_end)
        gap_reason, recovery, display = _STATUS_COPY[job.result.coverage_status]
        coverage_id = stable_id(
            "coverage",
            job.result.source_id,
            job.result.edition_id,
            window_start,
            window_end,
        )
        entries.append(
            CoverageEntry(
                coverage_id=coverage_id,
                source_id=job.result.source_id,
                edition_id=job.result.edition_id,
                requested_start=window_start,
                requested_end=window_end,
                actual_start=_iso(job.actual_start) if job.actual_start else None,
                actual_end=_iso(job.actual_end) if job.actual_end else None,
                documents_seen=job.result.items_seen,
                documents_accepted=job.result.items_accepted,
                status=job.result.coverage_status,
                gap_reason=gap_reason,
                last_success_at=job.last_success_at,
                recovery_action=recovery,
                display_message=display,
            )
        )

    statuses = {entry.status for entry in entries}
    if not entries:
        overall = CoverageStatus.UNKNOWN
    elif statuses <= {CoverageStatus.COMPLETE, CoverageStatus.NO_MATCH}:
        overall = CoverageStatus.COMPLETE
    elif len(statuses) == 1:
        overall = next(iter(statuses))
    else:
        overall = CoverageStatus.PARTIAL

    return CoverageReport(
        requested_start=window_start,
        requested_end=window_end,
        actual_start=_iso(min(actual_starts)) if actual_starts else None,
        actual_end=_iso(max(actual_ends)) if actual_ends else None,
        documents_seen=sum(entry.documents_seen for entry in entries),
        documents_accepted=sum(entry.documents_accepted for entry in entries),
        status=overall,
        entries=tuple(entries),
        generated_at=datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
    )
