from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import sys

from .candidates.c01_range_audit import (
    audit_interval_partition,
    get_interval_partition_regions,
)
from .contract import OFFICIAL_INVSQRT_SPEC
from .fixed_point import (
    ALGORITHM_VERSION,
    FixedPointPrecision,
    fixed_point_reference,
)


@dataclass(frozen=True)
class SignedWidthEvidence:
    signed_width: int
    representable_minimum: int
    representable_maximum: int

    def verify_endpoints(self, minimum: int, maximum: int) -> bool:
        return (
            self.representable_minimum <= minimum
            and maximum <= self.representable_maximum
        )


@dataclass(frozen=True)
class FixedPointScaling:
    fractional_bits: int | None
    scale_factor: int | None
    real_number_range_available: bool


@dataclass(frozen=True)
class PartitionExtrema:
    interval_case: int
    minimum: int
    maximum: int
    minimum_at: int
    maximum_at: int


@dataclass(frozen=True)
class IntermediateWidthEntry:
    intermediate_id: str
    model_field_or_operation: str
    mathematical_definition: str
    integer_representation: str
    signedness: str
    fractional_scaling: FixedPointScaling
    minimum_observed: int
    maximum_observed: int
    minimum_at: int
    maximum_at: int
    existing_declared_width: int | None
    minimum_unsigned_width: int
    minimum_signed_width: int
    evidence_classification: str
    confidence: str
    limitations: str
    partition_extrema: tuple[PartitionExtrema, ...]
    circuit_mapping_status: str

    def to_dict(self) -> dict[str, object]:
        value = asdict(self)
        value["fractional_scaling"] = asdict(self.fractional_scaling)
        value["partition_extrema"] = [
            asdict(item) for item in self.partition_extrema
        ]
        return value


@dataclass(frozen=True)
class WidthAnalysisResult:
    model_identity: str
    minimum_input: int
    maximum_input: int
    inputs_evaluated: int
    mismatches: int
    repeated_run_identical: bool | None
    started_at_utc: str
    completed_at_utc: str
    python_version: str
    entries: tuple[IntermediateWidthEntry, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "model_identity": self.model_identity,
            "minimum_input": self.minimum_input,
            "maximum_input": self.maximum_input,
            "inputs_evaluated": self.inputs_evaluated,
            "mismatches": self.mismatches,
            "repeated_run_identical": self.repeated_run_identical,
            "started_at_utc": self.started_at_utc,
            "completed_at_utc": self.completed_at_utc,
            "python_version": self.python_version,
            "entries": [entry.to_dict() for entry in self.entries],
        }


@dataclass(frozen=True)
class WidthOpportunity:
    intermediate_id: str
    mathematical_range_is_narrower: bool
    decision: str
    rationale: str


def unsigned_representation_width(maximum: int) -> int:
    if isinstance(maximum, bool) or not isinstance(maximum, int):
        raise ValueError("maximum must be an integer")
    if maximum < 0:
        raise ValueError("unsigned representation rejects negative values")
    return max(1, maximum.bit_length())


def signed_representation_width(minimum: int, maximum: int) -> int:
    if isinstance(minimum, bool) or not isinstance(minimum, int):
        raise ValueError("minimum must be an integer")
    if isinstance(maximum, bool) or not isinstance(maximum, int):
        raise ValueError("maximum must be an integer")
    if minimum > maximum:
        raise ValueError("minimum must not exceed maximum")
    evidence = signed_width_evidence(minimum, maximum)
    return evidence.signed_width


def signed_width_evidence(minimum: int, maximum: int) -> SignedWidthEvidence:
    if isinstance(minimum, bool) or not isinstance(minimum, int):
        raise ValueError("minimum must be an integer")
    if isinstance(maximum, bool) or not isinstance(maximum, int):
        raise ValueError("maximum must be an integer")
    if minimum > maximum:
        raise ValueError("minimum must not exceed maximum")

    for width in range(1, 4097):
        representable_minimum = -(1 << (width - 1))
        representable_maximum = (1 << (width - 1)) - 1
        if representable_minimum <= minimum and maximum <= representable_maximum:
            return SignedWidthEvidence(
                signed_width=width,
                representable_minimum=representable_minimum,
                representable_maximum=representable_maximum,
            )
    raise OverflowError("Signed representation width exceeded 4096 bits")


def fixed_point_scaling(
    fractional_bits: int | None,
    *,
    real_number_range_available: bool = False,
) -> FixedPointScaling:
    if fractional_bits is not None:
        if (
            isinstance(fractional_bits, bool)
            or not isinstance(fractional_bits, int)
            or fractional_bits < 0
        ):
            raise ValueError("fractional_bits must be a non-negative integer")
        scale_factor = 1 << fractional_bits
    else:
        scale_factor = None
    return FixedPointScaling(
        fractional_bits=fractional_bits,
        scale_factor=scale_factor,
        real_number_range_available=real_number_range_available,
    )


_INTERMEDIATE_SCALE = {
    "input": fixed_point_scaling(None),
    "shift_pairs": fixed_point_scaling(None),
    "normalized": fixed_point_scaling(0),
    "interval_case": fixed_point_scaling(None),
    "coefficient_c0": fixed_point_scaling(17),
    "coefficient_c1": fixed_point_scaling(17),
    "coefficient_c2": fixed_point_scaling(17),
    "coefficient_c3": fixed_point_scaling(17),
    "horner_r1": fixed_point_scaling(17),
    "horner_r2": fixed_point_scaling(17),
    "horner_r3": fixed_point_scaling(17),
    "square": fixed_point_scaling(28),
    "mantissa_product": fixed_point_scaling(28),
    "newton_correction": fixed_point_scaling(28),
    "newton_result_before_denormalization": fixed_point_scaling(29),
    "phase_numerator": fixed_point_scaling(40),
}


_MODEL_FIELD = {
    "input": "FixedPointResult.input_value",
    "shift_pairs": "FixedPointResult.shift_pairs",
    "normalized": "FixedPointResult.normalized_register",
    "interval_case": "FixedPointResult.interval_case",
    "coefficient_c0": "FixedPointResult.coefficient_integers[0]",
    "coefficient_c1": "FixedPointResult.coefficient_integers[1]",
    "coefficient_c2": "FixedPointResult.coefficient_integers[2]",
    "coefficient_c3": "FixedPointResult.coefficient_integers[3]",
    "horner_r1": "FixedPointResult.horner_registers[0]",
    "horner_r2": "FixedPointResult.horner_registers[1]",
    "horner_r3": "FixedPointResult.horner_registers[2]",
    "square": "FixedPointResult.square_register",
    "mantissa_product": "FixedPointResult.product_register",
    "newton_correction": "3 << product_bits - FixedPointResult.product_register",
    "newton_result_before_denormalization": "FixedPointResult.result_register >> FixedPointResult.shift_pairs",
    "phase_numerator": "FixedPointResult.result_register",
}


_DECLARED_WIDTH = {
    "input": 22,
    "shift_pairs": None,
    "normalized": 22,
    "interval_case": None,
    "coefficient_c0": 17,
    "coefficient_c1": 17,
    "coefficient_c2": 17,
    "coefficient_c3": 17,
    "horner_r1": 17,
    "horner_r2": 17,
    "horner_r3": 17,
    "square": 28,
    "mantissa_product": 30,
    "newton_correction": None,
    "newton_result_before_denormalization": 30,
    "phase_numerator": 40,
}


_DEFINITION = {
    "input": "Valid benchmark input integer.",
    "shift_pairs": "Leading-zero-pair denormalization shift count.",
    "normalized": "Input left-shifted by twice shift_pairs.",
    "interval_case": "Four-way normalized coefficient selector.",
    "coefficient_c0": "First source coefficient integer.",
    "coefficient_c1": "Second source coefficient integer.",
    "coefficient_c2": "Third source coefficient integer.",
    "coefficient_c3": "Fourth source coefficient integer.",
    "horner_r1": "First Horner accumulator.",
    "horner_r2": "Second Horner accumulator.",
    "horner_r3": "Third Horner accumulator.",
    "square": "Bitwise square construction register.",
    "mantissa_product": "Mantissa row-truncated product register.",
    "newton_correction": "3 << product_bits minus the mantissa product.",
    "newton_result_before_denormalization": "Newton result before left shift.",
    "phase_numerator": "Denormalized phase-turn numerator.",
}


def _run_register_width_analysis_once(
    minimum_input: int = OFFICIAL_INVSQRT_SPEC.minimum_input,
    maximum_input: int = OFFICIAL_INVSQRT_SPEC.maximum_input,
) -> WidthAnalysisResult:
    if (
        isinstance(minimum_input, bool)
        or not isinstance(minimum_input, int)
        or isinstance(maximum_input, bool)
        or not isinstance(maximum_input, int)
    ):
        raise ValueError("Input bounds must be integers")
    if not (
        OFFICIAL_INVSQRT_SPEC.minimum_input
        <= minimum_input
        <= maximum_input
        <= OFFICIAL_INVSQRT_SPEC.maximum_input
    ):
        raise ValueError("Bounds must be an ordered subset of the benchmark domain")

    started = datetime.now(timezone.utc)
    accumulator = {
        name: {
            "minimum": None,
            "maximum": None,
            "minimum_at": None,
            "maximum_at": None,
        }
        for name in _MODEL_FIELD
    }
    partition_accumulator = {
        name: {
            case: {
                "minimum": None,
                "maximum": None,
                "minimum_at": None,
                "maximum_at": None,
            }
            for case in range(4)
        }
        for name in _MODEL_FIELD
    }
    mismatches = 0
    evaluated = 0

    partition_regions = get_interval_partition_regions()

    for input_value in range(minimum_input, maximum_input + 1):
        result = fixed_point_reference(input_value)
        values = {
            "input": result.input_value,
            "shift_pairs": result.shift_pairs,
            "normalized": result.normalized_register,
            "interval_case": result.interval_case,
            "coefficient_c0": result.coefficient_integers[0],
            "coefficient_c1": result.coefficient_integers[1],
            "coefficient_c2": result.coefficient_integers[2],
            "coefficient_c3": result.coefficient_integers[3],
            "horner_r1": result.horner_registers[0],
            "horner_r2": result.horner_registers[1],
            "horner_r3": result.horner_registers[2],
            "square": result.square_register,
            "mantissa_product": result.product_register,
            "newton_correction": (
                (3 << FixedPointPrecision().product_bits)
                - result.product_register
            ),
            "newton_result_before_denormalization": (
                result.result_register >> result.shift_pairs
            ),
            "phase_numerator": result.result_register,
        }
        matched_case = next(
            (
                region.interval_case
                for region in partition_regions
                if any(
                    lower <= result.normalized_register < upper
                    for lower, upper in region.normalized_subranges
                )
            ),
            None,
        )
        if matched_case is None or matched_case != result.interval_case:
            mismatches += 1

        for name, value in values.items():
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                mismatches += 1
                continue
            total = accumulator[name]
            if total["minimum"] is None or value < total["minimum"]:
                total["minimum"] = value
                total["minimum_at"] = input_value
            if total["maximum"] is None or value > total["maximum"]:
                total["maximum"] = value
                total["maximum_at"] = input_value
            if matched_case is not None:
                partition = partition_accumulator[name][matched_case]
                if partition["minimum"] is None or value < partition["minimum"]:
                    partition["minimum"] = value
                    partition["minimum_at"] = input_value
                if partition["maximum"] is None or value > partition["maximum"]:
                    partition["maximum"] = value
                    partition["maximum_at"] = input_value
        evaluated += 1

    partition_audit = audit_interval_partition(
        __import__(
            "invsqrt_opt.candidates.c01_range_audit",
            fromlist=["RangeAuditConfig"],
        ).RangeAuditConfig(minimum_input, maximum_input)
    )
    mismatches += partition_audit.mismatch_count

    entries: list[IntermediateWidthEntry] = []
    for name in _MODEL_FIELD:
        total = accumulator[name]
        minimum = total["minimum"]
        maximum = total["maximum"]
        if minimum is None or maximum is None:
            raise RuntimeError(f"{name} was not observed")
        unsigned_width = unsigned_representation_width(maximum)
        signed_width = signed_width_evidence(minimum, maximum)
        if not signed_width.verify_endpoints(minimum, maximum):
            raise RuntimeError(f"{name} signed-width endpoint verification failed")

        partition_extrema = tuple(
            PartitionExtrema(
                interval_case=case,
                minimum=partition_accumulator[name][case]["minimum"],
                maximum=partition_accumulator[name][case]["maximum"],
                minimum_at=partition_accumulator[name][case]["minimum_at"],
                maximum_at=partition_accumulator[name][case]["maximum_at"],
            )
            for case in range(4)
            if partition_accumulator[name][case]["minimum"] is not None
        )

        declared_width = _DECLARED_WIDTH[name]
        narrower = (
            declared_width is not None
            and unsigned_width < declared_width
        )
        if narrower:
            opportunity = "REQUIRES_CANONICAL_CIRCUIT_MAPPING"
        elif declared_width is None:
            opportunity = "REQUIRES_CANONICAL_CIRCUIT_MAPPING"
        else:
            opportunity = "NO_WIDTH_REDUCTION_IDENTIFIED"

        entries.append(
            IntermediateWidthEntry(
                intermediate_id=name,
                model_field_or_operation=_MODEL_FIELD[name],
                mathematical_definition=_DEFINITION[name],
                integer_representation="unsigned integer",
                signedness="unsigned",
                fractional_scaling=_INTERMEDIATE_SCALE[name],
                minimum_observed=minimum,
                maximum_observed=maximum,
                minimum_at=total["minimum_at"],
                maximum_at=total["maximum_at"],
                existing_declared_width=declared_width,
                minimum_unsigned_width=unsigned_width,
                minimum_signed_width=signed_width.signed_width,
                evidence_classification="EXHAUSTIVELY_OBSERVED",
                confidence="domain-specific strong; circuit correspondence unknown",
                limitations=(
                    "Exhaustive only over the official input domain; "
                    "does not prove values outside the domain or circuit allocation"
                ),
                partition_extrema=partition_extrema,
                circuit_mapping_status=(
                    "UNMAPPED"
                    if narrower or declared_width is None
                    else "UNMAPPED"
                ),
            )
        )

    completed = datetime.now(timezone.utc)
    return WidthAnalysisResult(
        model_identity=ALGORITHM_VERSION,
        minimum_input=minimum_input,
        maximum_input=maximum_input,
        inputs_evaluated=evaluated,
        mismatches=mismatches,
        repeated_run_identical=True,
        started_at_utc=started.isoformat(),
        completed_at_utc=completed.isoformat(),
        python_version=sys.version,
        entries=tuple(entries),
    )


def run_register_width_analysis(
    minimum_input: int = OFFICIAL_INVSQRT_SPEC.minimum_input,
    maximum_input: int = OFFICIAL_INVSQRT_SPEC.maximum_input,
) -> WidthAnalysisResult:
    result = _run_register_width_analysis_once(minimum_input, maximum_input)
    return WidthAnalysisResult(
        model_identity=result.model_identity,
        minimum_input=result.minimum_input,
        maximum_input=result.maximum_input,
        inputs_evaluated=result.inputs_evaluated,
        mismatches=result.mismatches,
        repeated_run_identical=None,
        started_at_utc=result.started_at_utc,
        completed_at_utc=result.completed_at_utc,
        python_version=result.python_version,
        entries=result.entries,
    )


def assess_width_opportunities(
    analysis: WidthAnalysisResult,
) -> tuple[WidthOpportunity, ...]:
    if not isinstance(analysis, WidthAnalysisResult):
        raise ValueError("analysis must be a WidthAnalysisResult")
    opportunities: list[WidthOpportunity] = []
    for entry in analysis.entries:
        narrower = (
            entry.existing_declared_width is not None
            and entry.minimum_unsigned_width
            < entry.existing_declared_width
        )
        if narrower:
            decision = "REQUIRES_CANONICAL_CIRCUIT_MAPPING"
            rationale = (
                "The model range is narrower than the declared model width, "
                "but no canonical circuit register mapping establishes "
                "representation, control, or overflow correspondence."
            )
        elif entry.existing_declared_width is None:
            decision = "REQUIRES_CANONICAL_CIRCUIT_MAPPING"
            rationale = (
                "A scalar range exists, but no authoritative circuit or "
                "model width is declared for this intermediate."
            )
        else:
            decision = "NO_WIDTH_REDUCTION_IDENTIFIED"
            rationale = (
                "The observed unsigned minimum width is not narrower than "
                "the declared model width."
            )
        opportunities.append(
            WidthOpportunity(
                intermediate_id=entry.intermediate_id,
                mathematical_range_is_narrower=narrower,
                decision=decision,
                rationale=rationale,
            )
        )
    return tuple(opportunities)
