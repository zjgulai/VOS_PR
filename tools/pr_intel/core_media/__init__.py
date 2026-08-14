"""PR 核心媒体洞察 P0 的领域合同与离线数据管道。"""

from .contracts import (
    BylineStatus,
    ContractViolation,
    CoverageStatus,
    PermissionStatus,
    ReviewStatus,
    RightsLabel,
    stable_id,
)
from .scope_loader import P0Scope, load_scope, validate_scope, validate_scope_dict

__all__ = [
    "BylineStatus",
    "ContractViolation",
    "CoverageStatus",
    "P0Scope",
    "PermissionStatus",
    "ReviewStatus",
    "RightsLabel",
    "load_scope",
    "stable_id",
    "validate_scope",
    "validate_scope_dict",
]
