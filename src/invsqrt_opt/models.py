from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
import math
from typing import Any, Mapping


class CandidateState(str, Enum):
    CREATED = "CREATED"
    BUILT = "BUILT"
    STRUCTURALLY_VALIDATED = "STRUCTURALLY_VALIDATED"
    OFFICIAL_VERIFIER_VALIDATED = "OFFICIAL_VERIFIER_VALIDATED"
    REJECTED = "REJECTED"


class VerificationStatus(str, Enum):
    NOT_RUN = "NOT_RUN"
    PASSED = "PASSED"
    FAILED = "FAILED"


class MetricProvenance(str, Enum):
    OFFICIAL = "OFFICIAL"
    ESTIMATE = "ESTIMATE"
    UNAVAILABLE = "UNAVAILABLE"
    UNKNOWN = "UNKNOWN"


class MeasurementStatus(str, Enum):
    MEASURED = "MEASURED"
    ESTIMATED = "ESTIMATED"
    UNAVAILABLE = "UNAVAILABLE"


class ExperimentStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


def _finite_number(name: str, value: float | int) -> float:
    if isinstance(value, bool):
        raise ValueError(f"{name} must be a finite number")
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must be a finite number") from exc
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    if number < 0:
        raise ValueError(f"{name} must be non-negative")
    return number


def _enum_value(enum_type: type[Enum], value: Enum | str) -> Enum:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"Unsupported {enum_type.__name__}: {value}") from exc


@dataclass(frozen=True)
class ResourceMetrics:
    qubit_count: int | None
    toffoli_like_count: float | None
    base_t_count: float | None
    rotation_fallback_t_contribution: float | None
    provenance: MetricProvenance = MetricProvenance.UNAVAILABLE
    measurement_status: MeasurementStatus = MeasurementStatus.UNAVAILABLE

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "provenance", _enum_value(MetricProvenance, self.provenance)
        )
        object.__setattr__(
            self,
            "measurement_status",
            _enum_value(MeasurementStatus, self.measurement_status),
        )

        if self.qubit_count is not None:
            if isinstance(self.qubit_count, bool) or not isinstance(self.qubit_count, int):
                raise ValueError("qubit_count must be a non-negative integer")
            if self.qubit_count < 0:
                raise ValueError("qubit_count must be non-negative")

        for name in (
            "toffoli_like_count",
            "base_t_count",
            "rotation_fallback_t_contribution",
        ):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _finite_number(name, value))

        complete = (
            self.qubit_count is not None
            and self.toffoli_like_count is not None
            and self.base_t_count is not None
            and self.rotation_fallback_t_contribution is not None
        )
        if not complete and self.provenance == MetricProvenance.OFFICIAL:
            raise ValueError("Official resource metrics must include every required count")

    @property
    def total_t_equivalent_contribution(self) -> float | None:
        if self.base_t_count is None or self.rotation_fallback_t_contribution is None:
            return None
        return self.base_t_count + self.rotation_fallback_t_contribution

    @property
    def is_complete(self) -> bool:
        return (
            self.qubit_count is not None
            and self.toffoli_like_count is not None
            and self.base_t_count is not None
            and self.rotation_fallback_t_contribution is not None
        )

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["provenance"] = self.provenance.value
        data["measurement_status"] = self.measurement_status.value
        return data

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ResourceMetrics":
        allowed = {
            "qubit_count",
            "toffoli_like_count",
            "base_t_count",
            "rotation_fallback_t_contribution",
            "provenance",
            "measurement_status",
        }
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"Unknown resource metric fields: {sorted(unknown)}")
        return cls(**dict(data))


@dataclass(frozen=True)
class Candidate:
    candidate_id: str
    candidate_version: str
    optimization_strategy: str
    configuration: Mapping[str, Any]
    circuit_artifact: str | None = None
    circuit_builder_reference: str | None = None
    resource_metrics: ResourceMetrics | None = None
    state: CandidateState = CandidateState.CREATED
    verification_status: VerificationStatus = VerificationStatus.NOT_RUN
    experiment_provenance: tuple[str, ...] = field(default_factory=tuple)
    evidence_references: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in ("candidate_id", "candidate_version", "optimization_strategy"):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if not isinstance(self.configuration, Mapping):
            raise ValueError("configuration must be a mapping")
        object.__setattr__(
            self, "state", _enum_value(CandidateState, self.state)
        )
        object.__setattr__(
            self,
            "verification_status",
            _enum_value(VerificationStatus, self.verification_status),
        )
        object.__setattr__(
            self, "experiment_provenance", tuple(self.experiment_provenance)
        )
        object.__setattr__(
            self, "evidence_references", tuple(self.evidence_references)
        )
        if self.state == CandidateState.OFFICIAL_VERIFIER_VALIDATED:
            raise ValueError(
                "OFFICIAL_VERIFIER_VALIDATED must be established through "
                "Candidate.promote_from_verification_result"
            )
        if self.state in (
            CandidateState.STRUCTURALLY_VALIDATED,
            CandidateState.OFFICIAL_VERIFIER_VALIDATED,
        ) and not self.evidence_references:
            raise ValueError("Validated candidates require evidence references")

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "candidate_version": self.candidate_version,
            "optimization_strategy": self.optimization_strategy,
            "configuration": dict(self.configuration),
            "circuit_artifact": self.circuit_artifact,
            "circuit_builder_reference": self.circuit_builder_reference,
            "resource_metrics": (
                self.resource_metrics.to_dict() if self.resource_metrics else None
            ),
            "state": self.state.value,
            "verification_status": self.verification_status.value,
            "experiment_provenance": list(self.experiment_provenance),
            "evidence_references": list(self.evidence_references),
        }

    def promote_from_verification_result(
        self,
        result: Any,
    ) -> "Candidate":
        from .verifier import (
            ExecutionStatus,
            VerificationStatus as VerifierVerificationStatus,
        )

        if result.candidate_id != self.candidate_id:
            raise ValueError("Verification result candidate ID does not match")
        if result.verification_status != VerifierVerificationStatus.PASSED:
            raise ValueError("Only a PASSED verification result may promote a candidate")
        if result.execution_status != ExecutionStatus.EXECUTED:
            raise ValueError("Official promotion requires executed verifier evidence")
        if result.exit_code != 0:
            raise ValueError("Official promotion requires verifier exit code 0")
        if not result.verifier_source_checksum:
            raise ValueError("Official promotion requires a verifier source checksum")
        if not result.provenance_complete:
            raise ValueError("Official promotion requires complete provenance")
        if not result.evidence_references:
            raise ValueError("Official promotion requires evidence references")

        evidence = tuple(
            dict.fromkeys(
                tuple(self.evidence_references) + tuple(result.evidence_references)
            )
        )
        promoted = object.__new__(Candidate)
        object.__setattr__(promoted, "candidate_id", self.candidate_id)
        object.__setattr__(promoted, "candidate_version", self.candidate_version)
        object.__setattr__(
            promoted, "optimization_strategy", self.optimization_strategy
        )
        object.__setattr__(promoted, "configuration", dict(self.configuration))
        object.__setattr__(promoted, "circuit_artifact", self.circuit_artifact)
        object.__setattr__(
            promoted,
            "circuit_builder_reference",
            self.circuit_builder_reference,
        )
        object.__setattr__(promoted, "resource_metrics", self.resource_metrics)
        object.__setattr__(
            promoted,
            "state",
            CandidateState.OFFICIAL_VERIFIER_VALIDATED,
        )
        object.__setattr__(
            promoted,
            "verification_status",
            VerificationStatus.PASSED,
        )
        object.__setattr__(
            promoted,
            "experiment_provenance",
            tuple(self.experiment_provenance),
        )
        object.__setattr__(promoted, "evidence_references", evidence)
        return promoted

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "Candidate":
        allowed = set(cls.__dataclass_fields__)
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"Unknown candidate fields: {sorted(unknown)}")
        values = dict(data)
        if values.get("resource_metrics") is not None:
            values["resource_metrics"] = ResourceMetrics.from_dict(
                values["resource_metrics"]
            )
        return cls(**values)


@dataclass(frozen=True)
class ExperimentConfig:
    experiment_id: str
    candidate_id: str
    strategy_name: str
    parameter_configuration: Mapping[str, Any]
    random_seed: int | None
    software_version: str
    dependency_metadata: Mapping[str, str]
    git_commit: str
    creation_timestamp: str
    execution_status: ExperimentStatus = ExperimentStatus.CREATED
    evidence_references: tuple[str, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        for name in (
            "experiment_id",
            "candidate_id",
            "strategy_name",
            "software_version",
            "git_commit",
            "creation_timestamp",
        ):
            if not isinstance(getattr(self, name), str) or not getattr(self, name).strip():
                raise ValueError(f"{name} is required")
        if not isinstance(self.parameter_configuration, Mapping):
            raise ValueError("parameter_configuration must be a mapping")
        if not isinstance(self.dependency_metadata, Mapping):
            raise ValueError("dependency_metadata must be a mapping")
        if not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in self.dependency_metadata.items()
        ):
            raise ValueError("dependency_metadata must map strings to strings")
        if self.random_seed is not None:
            if isinstance(self.random_seed, bool) or not isinstance(self.random_seed, int):
                raise ValueError("random_seed must be an integer")
        try:
            datetime.fromisoformat(self.creation_timestamp)
        except ValueError as exc:
            raise ValueError("creation_timestamp must be ISO-8601") from exc
        object.__setattr__(
            self,
            "execution_status",
            _enum_value(ExperimentStatus, self.execution_status),
        )
        object.__setattr__(
            self, "evidence_references", tuple(self.evidence_references)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "candidate_id": self.candidate_id,
            "strategy_name": self.strategy_name,
            "parameter_configuration": dict(self.parameter_configuration),
            "random_seed": self.random_seed,
            "software_version": self.software_version,
            "dependency_metadata": dict(self.dependency_metadata),
            "git_commit": self.git_commit,
            "creation_timestamp": self.creation_timestamp,
            "execution_status": self.execution_status.value,
            "evidence_references": list(self.evidence_references),
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "ExperimentConfig":
        allowed = set(cls.__dataclass_fields__)
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(f"Unknown experiment configuration fields: {sorted(unknown)}")
        return cls(**dict(data))
