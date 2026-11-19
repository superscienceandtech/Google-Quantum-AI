from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Any, Mapping, Protocol

from .configurations import CandidateConfiguration
from .contract import CircuitContract
from .execution import ExecutionStatus
from .models import ResourceMetrics
from .search_space import SearchSpace


class OperationStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class BackendOperation:
    status: OperationStatus
    value: Any = None
    error: str | None = None
    evidence_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, OperationStatus):
            object.__setattr__(self, "status", OperationStatus(self.status))
        object.__setattr__(
            self, "evidence_references", tuple(self.evidence_references)
        )
        if self.status == OperationStatus.FAILED and not self.error:
            raise ValueError("Failed backend operations require an error")


@dataclass(frozen=True)
class BuiltCircuit:
    artifact_reference: str
    circuit: Any = field(repr=False, compare=False)
    metadata: CircuitContract | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_reference, str) or not self.artifact_reference.strip():
            raise ValueError("artifact_reference is required")

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_reference": self.artifact_reference,
            "metadata": (
                {
                    "candidate_id": self.metadata.candidate_id,
                    "circuit_artifact": self.metadata.circuit_artifact,
                    "register_names": list(self.metadata.register_names),
                    "register_widths": dict(self.metadata.register_widths),
                    "distinct_qubit_ids": {
                        name: list(qubits)
                        for name, qubits in self.metadata.distinct_qubit_ids.items()
                    },
                    "total_qubit_count": self.metadata.total_qubit_count,
                    "input_register_restored": self.metadata.input_register_restored,
                    "scratch_registers_restored": self.metadata.scratch_registers_restored,
                    "validation_level": self.metadata.validation_level.value,
                    "evidence_references": list(self.metadata.evidence_references),
                }
                if self.metadata is not None
                else None
            ),
        }


class ExperimentBackend(Protocol):
    backend_id: str
    backend_version: str

    @property
    def available(self) -> bool:
        ...

    def validate_configuration(
        self,
        configuration: CandidateConfiguration,
        search_space: SearchSpace,
    ) -> BackendOperation:
        ...

    def construct_circuit(
        self,
        configuration: CandidateConfiguration,
    ) -> BackendOperation:
        ...

    def measure_resources(
        self,
        configuration: CandidateConfiguration,
        circuit: BuiltCircuit,
    ) -> BackendOperation:
        ...

    def compile_circuit(
        self,
        configuration: CandidateConfiguration,
        circuit: BuiltCircuit,
    ) -> BackendOperation:
        ...


class UnavailableBackend:
    backend_id = "unavailable"
    backend_version = "unknown"

    @property
    def available(self) -> bool:
        return False

    def validate_configuration(
        self,
        configuration: CandidateConfiguration,
        search_space: SearchSpace,
    ) -> BackendOperation:
        return BackendOperation(
            OperationStatus.UNAVAILABLE,
            error="No circuit backend is configured",
        )

    def construct_circuit(
        self,
        configuration: CandidateConfiguration,
    ) -> BackendOperation:
        return BackendOperation(
            OperationStatus.UNAVAILABLE,
            error="No circuit-construction backend is configured",
        )

    def measure_resources(
        self,
        configuration: CandidateConfiguration,
        circuit: BuiltCircuit,
    ) -> BackendOperation:
        return BackendOperation(
            OperationStatus.UNAVAILABLE,
            error="No resource-measurement backend is configured",
        )

    def compile_circuit(
        self,
        configuration: CandidateConfiguration,
        circuit: BuiltCircuit,
    ) -> BackendOperation:
        return BackendOperation(
            OperationStatus.UNAVAILABLE,
            error="No circuit-compilation backend is configured",
        )


@dataclass(frozen=True)
class BackendExecutionResult:
    configuration_id: str
    backend_id: str
    backend_version: str
    execution_status: ExecutionStatus
    operations: Mapping[str, BackendOperation]
    resource_metrics: ResourceMetrics | None = None
    circuit_metadata: CircuitContract | None = None
    runtime_seconds: float | None = None
    verification_result: Mapping[str, Any] | None = None
    error: str | None = None
    evidence_references: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.execution_status, ExecutionStatus):
            object.__setattr__(
                self, "execution_status", ExecutionStatus(self.execution_status)
            )
        if not isinstance(self.operations, Mapping):
            raise ValueError("operations must be a mapping")
        object.__setattr__(self, "operations", dict(self.operations))
        object.__setattr__(
            self, "evidence_references", tuple(self.evidence_references)
        )
        if self.runtime_seconds is not None:
            if (
                isinstance(self.runtime_seconds, bool)
                or not isinstance(self.runtime_seconds, (int, float))
                or not math.isfinite(self.runtime_seconds)
                or self.runtime_seconds < 0
            ):
                raise ValueError("runtime_seconds must be finite and non-negative")

    def to_dict(self) -> dict[str, Any]:
        def summarize(value: Any) -> Any:
            if isinstance(value, BuiltCircuit):
                return value.to_dict()
            if isinstance(value, ResourceMetrics):
                return value.to_dict()
            if isinstance(value, CircuitContract):
                return {
                    "candidate_id": value.candidate_id,
                    "circuit_artifact": value.circuit_artifact,
                    "validation_level": value.validation_level.value,
                    "metadata_errors": value.validate_metadata(),
                }
            if value is None or isinstance(value, (str, int, float, bool)):
                return value
            return {"type": type(value).__name__}

        return {
            "configuration_id": self.configuration_id,
            "backend_id": self.backend_id,
            "backend_version": self.backend_version,
            "execution_status": self.execution_status.value,
            "operations": {
                name: {
                    "status": operation.status.value,
                    "value": summarize(operation.value),
                    "error": operation.error,
                    "evidence_references": list(operation.evidence_references),
                }
                for name, operation in self.operations.items()
            },
            "resource_metrics": (
                self.resource_metrics.to_dict()
                if self.resource_metrics is not None
                else None
            ),
            "circuit_metadata": (
                summarize(self.circuit_metadata)
                if self.circuit_metadata is not None
                else None
            ),
            "runtime_seconds": self.runtime_seconds,
            "verification_result": (
                dict(self.verification_result)
                if self.verification_result is not None
                else None
            ),
            "error": self.error,
            "evidence_references": list(self.evidence_references),
        }
