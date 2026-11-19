from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ExecutionStatus(str, Enum):
    CONFIGURATION_PENDING = "CONFIGURATION_PENDING"
    CONFIGURATION_INVALID = "CONFIGURATION_INVALID"
    CONFIGURATION_VALID = "CONFIGURATION_VALID"
    DUPLICATE_CONFIGURATION = "DUPLICATE_CONFIGURATION"
    BACKEND_UNAVAILABLE = "BACKEND_UNAVAILABLE"
    EXECUTION_PENDING = "EXECUTION_PENDING"
    EXECUTION_RUNNING = "EXECUTION_RUNNING"
    EXECUTION_SUCCEEDED = "EXECUTION_SUCCEEDED"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    RESOURCE_METRICS_UNAVAILABLE = "RESOURCE_METRICS_UNAVAILABLE"
    CIRCUIT_METADATA_UNAVAILABLE = "CIRCUIT_METADATA_UNAVAILABLE"
    COMPILATION_UNAVAILABLE = "COMPILATION_UNAVAILABLE"
    VERIFICATION_PENDING = "VERIFICATION_PENDING"
    VERIFICATION_UNAVAILABLE = "VERIFICATION_UNAVAILABLE"
    OFFICIAL_VERIFICATION_PASSED = "OFFICIAL_VERIFICATION_PASSED"
    OFFICIAL_VERIFICATION_REJECTED = "OFFICIAL_VERIFICATION_REJECTED"
    RESULT_UNKNOWN = "RESULT_UNKNOWN"


_TRANSITIONS: dict[ExecutionStatus, frozenset[ExecutionStatus]] = {
    ExecutionStatus.CONFIGURATION_PENDING: frozenset(
        {
            ExecutionStatus.CONFIGURATION_INVALID,
            ExecutionStatus.CONFIGURATION_VALID,
        }
    ),
    ExecutionStatus.CONFIGURATION_INVALID: frozenset(),
    ExecutionStatus.CONFIGURATION_VALID: frozenset(
        {
            ExecutionStatus.DUPLICATE_CONFIGURATION,
            ExecutionStatus.BACKEND_UNAVAILABLE,
            ExecutionStatus.EXECUTION_PENDING,
        }
    ),
    ExecutionStatus.BACKEND_UNAVAILABLE: frozenset(),
    ExecutionStatus.DUPLICATE_CONFIGURATION: frozenset(),
    ExecutionStatus.EXECUTION_PENDING: frozenset(
        {ExecutionStatus.EXECUTION_RUNNING, ExecutionStatus.EXECUTION_FAILED}
    ),
    ExecutionStatus.EXECUTION_RUNNING: frozenset(
        {
            ExecutionStatus.EXECUTION_SUCCEEDED,
            ExecutionStatus.EXECUTION_FAILED,
            ExecutionStatus.RESOURCE_METRICS_UNAVAILABLE,
            ExecutionStatus.CIRCUIT_METADATA_UNAVAILABLE,
            ExecutionStatus.COMPILATION_UNAVAILABLE,
            ExecutionStatus.VERIFICATION_PENDING,
            ExecutionStatus.VERIFICATION_UNAVAILABLE,
            ExecutionStatus.OFFICIAL_VERIFICATION_PASSED,
            ExecutionStatus.OFFICIAL_VERIFICATION_REJECTED,
            ExecutionStatus.RESULT_UNKNOWN,
        }
    ),
    ExecutionStatus.VERIFICATION_PENDING: frozenset(
        {
            ExecutionStatus.VERIFICATION_UNAVAILABLE,
            ExecutionStatus.RESOURCE_METRICS_UNAVAILABLE,
            ExecutionStatus.CIRCUIT_METADATA_UNAVAILABLE,
            ExecutionStatus.COMPILATION_UNAVAILABLE,
            ExecutionStatus.OFFICIAL_VERIFICATION_PASSED,
            ExecutionStatus.OFFICIAL_VERIFICATION_REJECTED,
            ExecutionStatus.RESULT_UNKNOWN,
            ExecutionStatus.EXECUTION_FAILED,
        }
    ),
}


@dataclass
class ExecutionLifecycle:
    current: ExecutionStatus = ExecutionStatus.CONFIGURATION_PENDING
    history: list[ExecutionStatus] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.history:
            self.history.append(self.current)

    def transition(self, status: ExecutionStatus) -> None:
        if not isinstance(status, ExecutionStatus):
            status = ExecutionStatus(status)
        allowed = _TRANSITIONS.get(self.current, frozenset())
        if status not in allowed:
            raise ValueError(
                f"Invalid execution transition: {self.current.value} -> {status.value}"
            )
        self.current = status
        self.history.append(status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "current": self.current.value,
            "history": [status.value for status in self.history],
        }
