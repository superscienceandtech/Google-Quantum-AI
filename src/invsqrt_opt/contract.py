from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import json
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class InputSpec:
    minimum: int = 1
    maximum: int = 3_133_452

    def validate(self) -> None:
        if isinstance(self.minimum, bool) or isinstance(self.maximum, bool):
            raise ValueError("Input bounds must be integers")
        if not isinstance(self.minimum, int) or not isinstance(self.maximum, int):
            raise ValueError("Input bounds must be integers")
        if self.minimum < 0 or self.minimum > self.maximum:
            raise ValueError("Input bounds are inconsistent")


@dataclass(frozen=True)
class InvSqrtSpecification:
    benchmark_id: str
    minimum_input: int
    maximum_input: int
    np: int
    beta: int
    input_width: int
    shots_per_input: int
    register_name: str
    total_shots: int
    precision_bits: int
    target_phase_description: str
    phase_tolerance_description: str
    restoration_requirement: str
    contract_version: str
    source_references: tuple[str, ...]

    def __post_init__(self) -> None:
        required_text = (
            "benchmark_id",
            "target_phase_description",
            "phase_tolerance_description",
            "restoration_requirement",
            "contract_version",
        )
        for name in required_text:
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        if not isinstance(self.source_references, tuple):
            object.__setattr__(
                self, "source_references", tuple(self.source_references)
            )
        if not self.source_references:
            raise ValueError("At least one source reference is required")

        for name in (
            "minimum_input",
            "maximum_input",
            "np",
            "beta",
            "input_width",
            "shots_per_input",
            "total_shots",
            "precision_bits",
        ):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
            if value < 0:
                raise ValueError(f"{name} must be non-negative")

        if self.minimum_input < 1:
            raise ValueError("minimum_input must be positive")
        if self.maximum_input < self.minimum_input:
            raise ValueError("Input domain bounds are inconsistent")
        if self.np != 10:
            raise ValueError("np must be 10")
        if self.beta != 1:
            raise ValueError("beta must be 1")
        if self.input_width != 22:
            raise ValueError("input_width must be 22")
        if self.register_name != "x":
            raise ValueError("register_name must be x")
        if self.shots_per_input != 64:
            raise ValueError("shots_per_input must be 64")
        if self.precision_bits != 24:
            raise ValueError("precision_bits must be 24")
        if self.total_shots != (
            self.maximum_input * self.shots_per_input
        ):
            raise ValueError(
                "total_shots must equal the inclusive input-domain workload "
                "(maximum_input * shots_per_input)"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "benchmark_id": self.benchmark_id,
            "minimum_input": self.minimum_input,
            "maximum_input": self.maximum_input,
            "np": self.np,
            "beta": self.beta,
            "input_width": self.input_width,
            "shots_per_input": self.shots_per_input,
            "register_name": self.register_name,
            "total_shots": self.total_shots,
            "precision_bits": self.precision_bits,
            "target_phase_description": self.target_phase_description,
            "phase_tolerance_description": self.phase_tolerance_description,
            "restoration_requirement": self.restoration_requirement,
            "contract_version": self.contract_version,
            "source_references": list(self.source_references),
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "InvSqrtSpecification":
        values = dict(data)
        if "source_references" in values:
            values["source_references"] = tuple(values["source_references"])
        return cls(**values)

    @classmethod
    def from_json(cls, text: str) -> "InvSqrtSpecification":
        return cls.from_dict(json.loads(text))


OFFICIAL_INVSQRT_SPEC = InvSqrtSpecification(
    benchmark_id="INVSQRT",
    minimum_input=1,
    maximum_input=3_133_452,
    np=10,
    beta=1,
    input_width=22,
    shots_per_input=64,
    register_name="x",
    total_shots=200_540_928,
    precision_bits=24,
    target_phase_description="exp(2*pi*i*beta/sqrt(x))",
    phase_tolerance_description=(
        "2^-24 beta/sqrt(x) turns; official verifier uses "
        "floor(2^65 beta/sqrt(x)) in 2^-64-turn uint64 units"
    ),
    restoration_requirement="x and scratch/work registers restored; k = 0",
    contract_version="P003-1",
    source_references=(
        "docs/COMPETITION_REQUIREMENTS_MATRIX.md",
        "docs/OFFICIAL_VERIFIER_API_REFERENCE.md",
        "docs/TEAM/BENCHMARKS/INVSQRT.md",
    ),
)


def validate_input(value: object) -> int:
    if isinstance(value, bool):
        raise ValueError("Boolean values are not valid INVSQRT inputs")
    if not isinstance(value, int):
        raise ValueError("INVSQRT input must be an integer")
    if value < OFFICIAL_INVSQRT_SPEC.minimum_input:
        raise ValueError(
            f"INVSQRT input must be at least "
            f"{OFFICIAL_INVSQRT_SPEC.minimum_input}"
        )
    if value > OFFICIAL_INVSQRT_SPEC.maximum_input:
        raise ValueError(
            f"INVSQRT input must be at most "
            f"{OFFICIAL_INVSQRT_SPEC.maximum_input}"
        )
    return value


def validate_inputs(
    values: Iterable[object],
    *,
    require_unique: bool = False,
) -> tuple[int, ...]:
    try:
        validated = tuple(validate_input(value) for value in values)
    except TypeError as exc:
        raise ValueError("INVSQRT inputs must be a collection") from exc
    if require_unique and len(set(validated)) != len(validated):
        raise ValueError("INVSQRT inputs must be unique")
    return validated


class CircuitValidationLevel(str, Enum):
    UNKNOWN = "UNKNOWN"
    METADATA_VALIDATED = "METADATA_VALIDATED"
    STRUCTURALLY_VALIDATED = "STRUCTURALLY_VALIDATED"
    OFFICIAL_VERIFIER_VALIDATED = "OFFICIAL_VERIFIER_VALIDATED"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class CircuitContract:
    candidate_id: str
    circuit_artifact: str
    register_names: tuple[str, ...]
    register_widths: Mapping[str, int]
    distinct_qubit_ids: Mapping[str, tuple[int, ...]]
    total_qubit_count: int
    input_register_restored: bool | None
    scratch_registers_restored: bool | None
    validation_level: CircuitValidationLevel = CircuitValidationLevel.UNKNOWN
    evidence_references: tuple[str, ...] = ()
    additional_qubit_ids: tuple[int, ...] | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.candidate_id, str) or not self.candidate_id.strip():
            raise ValueError("candidate_id is required")
        if not isinstance(self.circuit_artifact, str) or not self.circuit_artifact.strip():
            raise ValueError("circuit_artifact is required")
        if not isinstance(self.register_names, tuple):
            object.__setattr__(self, "register_names", tuple(self.register_names))
        object.__setattr__(
            self,
            "register_widths",
            dict(self.register_widths),
        )
        normalized_qubits: dict[str, tuple[int, ...]] = {}
        for name, qubits in self.distinct_qubit_ids.items():
            normalized_qubits[name] = tuple(qubits)
        object.__setattr__(
            self,
            "distinct_qubit_ids",
            normalized_qubits,
        )
        object.__setattr__(
            self,
            "validation_level",
            (
                self.validation_level
                if isinstance(self.validation_level, CircuitValidationLevel)
                else CircuitValidationLevel(self.validation_level)
            ),
        )
        object.__setattr__(
            self, "evidence_references", tuple(self.evidence_references)
        )
        if self.additional_qubit_ids is not None:
            object.__setattr__(
                self, "additional_qubit_ids", tuple(self.additional_qubit_ids)
            )
        if isinstance(self.total_qubit_count, bool) or not isinstance(
            self.total_qubit_count, int
        ):
            raise ValueError("total_qubit_count must be an integer")
        if self.total_qubit_count < 0:
            raise ValueError("total_qubit_count must be non-negative")

    def validate_metadata(self) -> list[str]:
        errors: list[str] = []
        spec = OFFICIAL_INVSQRT_SPEC
        if tuple(self.register_names) != (spec.register_name,):
            errors.append("Exactly one named register 'x' is required")
        if "x" not in self.register_widths:
            errors.append("Missing 'x' register width")
        elif self.register_widths["x"] != spec.input_width:
            errors.append("The 'x' register must have width 22")
        x_qubits = self.distinct_qubit_ids.get("x")
        if x_qubits is None:
            errors.append("Missing 'x' register qubit metadata")
        elif len(x_qubits) != spec.input_width:
            errors.append("The 'x' register must contain exactly 22 qubits")
        elif len(set(x_qubits)) != len(x_qubits):
            errors.append("The 'x' register qubits must be distinct")
        if set(self.register_widths) != {"x"}:
            errors.append("Register metadata must contain only 'x'")
        if any(
            isinstance(width, bool) or not isinstance(width, int) or width < 0
            for width in self.register_widths.values()
        ):
            errors.append("Register widths must be non-negative integers")
        all_qubits: list[int] = []
        for qubits in self.distinct_qubit_ids.values():
            all_qubits.extend(qubits)
        if any(
            isinstance(qubit, bool) or not isinstance(qubit, int) or qubit < 0
            for qubit in all_qubits
        ):
            errors.append("Qubit identifiers must be non-negative integers")
        if len(set(all_qubits)) != len(all_qubits):
            errors.append("Qubit identifiers must not be duplicated across registers")
        if self.total_qubit_count < spec.input_width:
            errors.append("Total circuit qubit count cannot be less than input width")
        if "x" in self.register_widths and x_qubits is not None:
            if len(x_qubits) != self.register_widths["x"]:
                errors.append("Register width conflicts with distinct qubit count")
        if self.additional_qubit_ids is None:
            if self.total_qubit_count != spec.input_width:
                errors.append(
                    "Additional qubit identifiers are required to reconcile "
                    "the total circuit qubit count"
                )
        else:
            all_qubits.extend(self.additional_qubit_ids)
            if any(
                isinstance(qubit, bool) or not isinstance(qubit, int) or qubit < 0
                for qubit in all_qubits
            ):
                errors.append("Qubit identifiers must be non-negative integers")
            if len(set(all_qubits)) != len(all_qubits):
                errors.append("Qubit identifiers must be distinct")
            if len(all_qubits) != self.total_qubit_count:
                errors.append(
                    "Total circuit qubit count conflicts with distinct qubit identifiers"
                )
        if self.input_register_restored is not True:
            errors.append("Input-register restoration evidence is missing")
        if self.scratch_registers_restored is not True:
            errors.append("Scratch/work-register restoration evidence is missing")
        return errors

    def with_validation_level(
        self,
        level: CircuitValidationLevel,
    ) -> "CircuitContract":
        level = (
            level
            if isinstance(level, CircuitValidationLevel)
            else CircuitValidationLevel(level)
        )
        if level in (
            CircuitValidationLevel.METADATA_VALIDATED,
            CircuitValidationLevel.STRUCTURALLY_VALIDATED,
        ) and not self.evidence_references:
            raise ValueError("Validated metadata requires evidence references")
        if level == CircuitValidationLevel.OFFICIAL_VERIFIER_VALIDATED:
            raise ValueError(
                "Only an executed official verifier result may establish "
                "OFFICIAL_VERIFIER_VALIDATED"
            )
        return CircuitContract(
            candidate_id=self.candidate_id,
            circuit_artifact=self.circuit_artifact,
            register_names=self.register_names,
            register_widths=dict(self.register_widths),
            distinct_qubit_ids=dict(self.distinct_qubit_ids),
            total_qubit_count=self.total_qubit_count,
            input_register_restored=self.input_register_restored,
            scratch_registers_restored=self.scratch_registers_restored,
            validation_level=level,
            evidence_references=self.evidence_references,
            additional_qubit_ids=self.additional_qubit_ids,
        )
