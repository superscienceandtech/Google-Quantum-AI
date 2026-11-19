"""P010-C01 exhaustive baseline register-range and truncation audit.

This module observes the unchanged fixed-point baseline. It does not propose
or apply a precision or register-width change.
"""

from __future__ import annotations

from bisect import bisect_left
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import hashlib
import json
import platform
import sys
from time import perf_counter
from pathlib import Path
from typing import Any

from ..contract import OFFICIAL_INVSQRT_SPEC
from ..fixed_point import (
    FixedPointPrecision,
    REFERENCE_SOURCE,
    REFERENCE_SOURCE_SHA256,
    fixed_point_reference,
)

CANDIDATE_ID = "P010-C01"
CANDIDATE_VERSION = "P011-range-audit-v1"
EXPERIMENT_ID = "P011-C01-E01-BASELINE-RANGE-AUDIT"


@dataclass(frozen=True)
class RangeAuditConfig:
    """Explicit, supported domain and baseline arithmetic for a C01 run."""

    minimum_input: int = OFFICIAL_INVSQRT_SPEC.minimum_input
    maximum_input: int = OFFICIAL_INVSQRT_SPEC.maximum_input
    n_p: int = OFFICIAL_INVSQRT_SPEC.np
    precision: FixedPointPrecision = field(default_factory=FixedPointPrecision)

    def __post_init__(self) -> None:
        for name, value in (
            ("minimum_input", self.minimum_input),
            ("maximum_input", self.maximum_input),
            ("n_p", self.n_p),
        ):
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
        if not (
            OFFICIAL_INVSQRT_SPEC.minimum_input
            <= self.minimum_input
            <= self.maximum_input
            <= OFFICIAL_INVSQRT_SPEC.maximum_input
        ):
            raise ValueError("Audit bounds must be an ordered subset of the benchmark domain")
        if self.n_p != OFFICIAL_INVSQRT_SPEC.np:
            raise ValueError(
                f"Only the benchmark n_p={OFFICIAL_INVSQRT_SPEC.np} is supported"
            )
        if not isinstance(self.precision, FixedPointPrecision):
            raise ValueError("precision must be a FixedPointPrecision")
        if self.precision != FixedPointPrecision():
            raise ValueError("P010-C01 supports only the validated baseline precision")


@dataclass(frozen=True)
class ValueRange:
    name: str
    minimum: int
    maximum: int
    minimum_at: int
    maximum_at: int
    observed_unsigned_bits: int
    minimum_required_unsigned_bits: int
    declared_bits: int | None
    unused_high_bits: int | None
    distance_to_exclusive_limit: int | None
    distance_to_largest_encodable_value: int | None
    width_basis: str | None


@dataclass(frozen=True)
class RowContributionRange:
    operator: str
    row_index: int
    weight: int
    exponent: int
    discarded_low_bit_count: int
    minimum: int
    maximum: int
    minimum_at: int
    maximum_at: int
    active_input_count: int
    maximum_discarded_remainder: int
    maximum_remainder_at: int | None


@dataclass(frozen=True)
class ConsistencyCheck:
    name: str
    checked_inputs: int
    mismatch_count: int
    first_mismatch_input: int | None


@dataclass(frozen=True)
class IntervalPartitionRegion:
    interval_case: int
    normalized_minimum: int
    normalized_maximum_exclusive: int
    normalized_subranges: tuple[tuple[int, int], ...]
    observed_input_minimum: int | None
    observed_input_maximum: int | None


@dataclass(frozen=True)
class PartitionTransition:
    input_value: int
    previous_interval_case: int
    next_interval_case: int


@dataclass(frozen=True)
class PartitionAuditResult:
    minimum_input: int
    maximum_input: int
    inputs_checked: int
    full_domain: bool
    regions: tuple[IntervalPartitionRegion, ...]
    transitions: tuple[PartitionTransition, ...]
    mismatch_count: int
    first_mismatch_input: int | None

    @property
    def passed(self) -> bool:
        return (
            self.inputs_checked
            == self.maximum_input - self.minimum_input + 1
            and self.mismatch_count == 0
            and len(self.regions) == 4
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "minimum_input": self.minimum_input,
            "maximum_input": self.maximum_input,
            "inputs_checked": self.inputs_checked,
            "full_domain": self.full_domain,
            "regions": [asdict(region) for region in self.regions],
            "transitions": [asdict(region) for region in self.transitions],
            "mismatch_count": self.mismatch_count,
            "first_mismatch_input": self.first_mismatch_input,
            "passed": self.passed,
        }


@dataclass(frozen=True)
class RangeAuditResult:
    experiment_id: str
    candidate_id: str
    candidate_version: str
    execution_status: str
    configuration: dict[str, Any]
    minimum_input: int
    maximum_input: int
    inputs_evaluated: int
    full_domain: bool
    critical_inputs_total: int
    critical_inputs_in_run: int
    critical_inputs_sha256: str
    baseline_source: str
    baseline_source_sha256: str
    baseline_implementation_sha256: str
    candidate_implementation_sha256: str
    baseline_output_sha256: str
    register_ranges: tuple[ValueRange, ...]
    row_contribution_ranges: tuple[RowContributionRange, ...]
    consistency_checks: tuple[ConsistencyCheck, ...]
    started_at_utc: str
    completed_at_utc: str
    runtime_seconds: float
    python_version: str
    platform: str

    @property
    def passed(self) -> bool:
        return (
            self.execution_status == "COMPLETED"
            and all(check.mismatch_count == 0 for check in self.consistency_checks)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "candidate_id": self.candidate_id,
            "candidate_version": self.candidate_version,
            "execution_status": self.execution_status,
            "passed": self.passed,
            "configuration": self.configuration,
            "input_coverage": {
                "minimum_input": self.minimum_input,
                "maximum_input": self.maximum_input,
                "inputs_evaluated": self.inputs_evaluated,
                "full_domain": self.full_domain,
                "critical_inputs_total": self.critical_inputs_total,
                "critical_inputs_in_run": self.critical_inputs_in_run,
                "critical_inputs_sha256": self.critical_inputs_sha256,
            },
            "baseline": {
                "source": self.baseline_source,
                "source_sha256": self.baseline_source_sha256,
                "implementation_sha256": self.baseline_implementation_sha256,
                "output_sha256": self.baseline_output_sha256,
            },
            "candidate_implementation_sha256": self.candidate_implementation_sha256,
            "register_ranges": [asdict(item) for item in self.register_ranges],
            "row_contribution_ranges": [
                asdict(item) for item in self.row_contribution_ranges
            ],
            "consistency_checks": [
                asdict(item) for item in self.consistency_checks
            ],
            "execution": {
                "started_at_utc": self.started_at_utc,
                "completed_at_utc": self.completed_at_utc,
                "runtime_seconds": self.runtime_seconds,
                "python_version": self.python_version,
                "platform": self.platform,
            },
        }


@dataclass
class _ValueRangeAccumulator:
    name: str
    declared_bits: int | None
    width_basis: str | None
    minimum: int | None = None
    maximum: int | None = None
    minimum_at: int | None = None
    maximum_at: int | None = None

    def observe(self, input_value: int, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RuntimeError(f"{self.name} is not a non-negative integer")
        if self.minimum is None or value < self.minimum:
            self.minimum = value
            self.minimum_at = input_value
        if self.maximum is None or value > self.maximum:
            self.maximum = value
            self.maximum_at = input_value

    def finish(self) -> ValueRange:
        if (
            self.minimum is None
            or self.maximum is None
            or self.minimum_at is None
            or self.maximum_at is None
        ):
            raise RuntimeError(f"{self.name} was not observed")
        observed_bits = self.maximum.bit_length()
        required_bits = max(1, observed_bits)
        if self.declared_bits is None:
            unused_high_bits = None
            distance_to_exclusive_limit = None
            distance_to_largest_encodable_value = None
        else:
            exclusive_limit = 1 << self.declared_bits
            if self.maximum >= exclusive_limit:
                raise RuntimeError(f"{self.name} exceeded its declared width")
            unused_high_bits = self.declared_bits - required_bits
            distance_to_exclusive_limit = exclusive_limit - self.maximum
            distance_to_largest_encodable_value = exclusive_limit - 1 - self.maximum
        return ValueRange(
            name=self.name,
            minimum=self.minimum,
            maximum=self.maximum,
            minimum_at=self.minimum_at,
            maximum_at=self.maximum_at,
            observed_unsigned_bits=observed_bits,
            minimum_required_unsigned_bits=required_bits,
            declared_bits=self.declared_bits,
            unused_high_bits=unused_high_bits,
            distance_to_exclusive_limit=distance_to_exclusive_limit,
            distance_to_largest_encodable_value=distance_to_largest_encodable_value,
            width_basis=self.width_basis,
        )


@dataclass
class _RowRangeAccumulator:
    operator: str
    row_index: int
    weight: int
    exponent: int
    minimum: int | None = None
    maximum: int | None = None
    minimum_at: int | None = None
    maximum_at: int | None = None
    active_input_count: int = 0
    maximum_discarded_remainder: int = 0
    maximum_remainder_at: int | None = None

    def observe(
        self,
        input_value: int,
        control: int,
        operand: int,
        contribution: int,
    ) -> None:
        if self.minimum is None or contribution < self.minimum:
            self.minimum = contribution
            self.minimum_at = input_value
        if self.maximum is None or contribution > self.maximum:
            self.maximum = contribution
            self.maximum_at = input_value
        if control == 1:
            self.active_input_count += 1
            if self.exponent < 0:
                remainder = operand & ((1 << -self.exponent) - 1)
                if remainder > self.maximum_discarded_remainder:
                    self.maximum_discarded_remainder = remainder
                    self.maximum_remainder_at = input_value

    def finish(self) -> RowContributionRange:
        if (
            self.minimum is None
            or self.maximum is None
            or self.minimum_at is None
            or self.maximum_at is None
        ):
            raise RuntimeError(f"{self.operator} row {self.row_index} was not observed")
        return RowContributionRange(
            operator=self.operator,
            row_index=self.row_index,
            weight=self.weight,
            exponent=self.exponent,
            discarded_low_bit_count=max(0, -self.exponent),
            minimum=self.minimum,
            maximum=self.maximum,
            minimum_at=self.minimum_at,
            maximum_at=self.maximum_at,
            active_input_count=self.active_input_count,
            maximum_discarded_remainder=self.maximum_discarded_remainder,
            maximum_remainder_at=self.maximum_remainder_at,
        )


@dataclass
class _CheckAccumulator:
    name: str
    checked_inputs: int = 0
    mismatch_count: int = 0
    first_mismatch_input: int | None = None

    def observe(self, input_value: int, matched: bool) -> None:
        self.checked_inputs += 1
        if not matched:
            self.mismatch_count += 1
            if self.first_mismatch_input is None:
                self.first_mismatch_input = input_value

    def finish(self) -> ConsistencyCheck:
        return ConsistencyCheck(
            name=self.name,
            checked_inputs=self.checked_inputs,
            mismatch_count=self.mismatch_count,
            first_mismatch_input=self.first_mismatch_input,
        )


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _critical_boundary_inputs(n_p: int) -> tuple[int, ...]:
    candidates = {
        OFFICIAL_INVSQRT_SPEC.minimum_input,
        OFFICIAL_INVSQRT_SPEC.maximum_input,
    }
    for exponent in range(2, 2 * n_p + 1, 2):
        boundary = 1 << exponent
        candidates.update((boundary - 1, boundary, boundary + 1))

    for shift_pairs in range(n_p + 1):
        scale = 1 << (2 * (n_p - shift_pairs))
        for numerator, denominator in ((3, 2), (2, 1), (3, 1)):
            boundary_numerator = numerator * scale
            floor_value = boundary_numerator // denominator
            ceil_value = (
                boundary_numerator + denominator - 1
            ) // denominator
            for boundary in (floor_value, ceil_value):
                candidates.update((boundary - 1, boundary, boundary + 1))

    return tuple(
        sorted(
            value
            for value in candidates
            if OFFICIAL_INVSQRT_SPEC.minimum_input
            <= value
            <= OFFICIAL_INVSQRT_SPEC.maximum_input
        )
    )


def _contribution(control: int, operand: int, exponent: int) -> int:
    shifted = operand << exponent if exponent >= 0 else operand >> -exponent
    return control * shifted


def get_interval_partition_regions(
    n_p: int = OFFICIAL_INVSQRT_SPEC.np,
) -> tuple[IntervalPartitionRegion, ...]:
    """Describe the four baseline normalized-input intervals exactly.

    These bounds are in the 22-bit normalized register used by the P008
    fixed-point emulator. They are not a claim about physical circuit wires.
    """
    if isinstance(n_p, bool) or not isinstance(n_p, int):
        raise ValueError("n_p must be an integer")
    if n_p != OFFICIAL_INVSQRT_SPEC.np:
        raise ValueError(f"Only the benchmark n_p={OFFICIAL_INVSQRT_SPEC.np} is supported")
    normalized_width = 2 * n_p + 2
    base = 1 << (normalized_width - 2)
    subranges = (
        ((base, base * 3 // 2),),
        ((base * 3 // 2, base * 2),),
        ((base * 2, base * 3),),
        ((base * 3, base * 4),),
    )
    return tuple(
        IntervalPartitionRegion(
            interval_case=case,
            normalized_minimum=min(subrange[0] for subrange in subranges[case]),
            normalized_maximum_exclusive=max(subrange[1] for subrange in subranges[case]),
            normalized_subranges=subranges[case],
            observed_input_minimum=None,
            observed_input_maximum=None,
        )
        for case in range(4)
    )


def audit_interval_partition(
    config: RangeAuditConfig | None = None,
) -> PartitionAuditResult:
    """Exhaustively classify an inclusive input range by the baseline partition.

    Expected interval cases are derived from normalized integer boundaries.
    The fixed-point emulator supplies the actual normalized register and case,
    while no circuit or width equivalence is inferred.
    """
    if config is None:
        config = RangeAuditConfig()
    if not isinstance(config, RangeAuditConfig):
        raise ValueError("config must be a RangeAuditConfig")

    regions = get_interval_partition_regions(config.n_p)
    observed_minimum = [None] * 4
    observed_maximum = [None] * 4
    transitions: list[PartitionTransition] = []
    previous_case: int | None = None
    mismatch_count = 0
    first_mismatch: int | None = None
    inputs_checked = 0

    for input_value in range(config.minimum_input, config.maximum_input + 1):
        result = fixed_point_reference(
            input_value,
            n_p=config.n_p,
            precision=config.precision,
        )
        normalized = result.normalized_register
        expected_case = next(
            (
                region.interval_case
                for region in regions
                if any(
                    subrange_minimum
                    <= normalized
                    < subrange_maximum_exclusive
                    for subrange_minimum, subrange_maximum_exclusive
                    in region.normalized_subranges
                )
            ),
            None,
        )
        if expected_case is None:
            mismatch_count += 1
            if first_mismatch is None:
                first_mismatch = input_value
        elif result.interval_case != expected_case:
            mismatch_count += 1
            if first_mismatch is None:
                first_mismatch = input_value

        case = result.interval_case
        if not 0 <= case < 4:
            mismatch_count += 1
            if first_mismatch is None:
                first_mismatch = input_value
        else:
            if observed_minimum[case] is None:
                observed_minimum[case] = input_value
            observed_maximum[case] = input_value
            if previous_case is not None and previous_case != case:
                transitions.append(
                    PartitionTransition(
                        input_value=input_value,
                        previous_interval_case=previous_case,
                        next_interval_case=case,
                    )
                )
            previous_case = case
        inputs_checked += 1

    finalized_regions = tuple(
        IntervalPartitionRegion(
            interval_case=region.interval_case,
            normalized_minimum=region.normalized_minimum,
            normalized_maximum_exclusive=region.normalized_maximum_exclusive,
            normalized_subranges=region.normalized_subranges,
            observed_input_minimum=observed_minimum[region.interval_case],
            observed_input_maximum=observed_maximum[region.interval_case],
        )
        for region in regions
    )
    normalized_minimum = 1 << (2 * config.n_p)
    normalized_maximum_exclusive = 1 << (2 * config.n_p + 2)
    subranges = sorted(
        subrange
        for region in regions
        for subrange in region.normalized_subranges
    )
    covered = (
        len(subranges) == 4
        and subranges[0][0] == normalized_minimum
        and subranges[-1][1] == normalized_maximum_exclusive
        and all(left[1] == right[0] for left, right in zip(subranges, subranges[1:]))
        and all(left[1] <= right[0] for left, right in zip(subranges, subranges[1:]))
    )
    if not covered:
        mismatch_count += 1
        if first_mismatch is None:
            first_mismatch = config.minimum_input
    if (
        config.minimum_input == OFFICIAL_INVSQRT_SPEC.minimum_input
        and config.maximum_input == OFFICIAL_INVSQRT_SPEC.maximum_input
        and any(minimum is None for minimum in observed_minimum)
    ):
        mismatch_count += 1
        if first_mismatch is None:
            first_mismatch = config.minimum_input

    return PartitionAuditResult(
        minimum_input=config.minimum_input,
        maximum_input=config.maximum_input,
        inputs_checked=inputs_checked,
        full_domain=(
            config.minimum_input == OFFICIAL_INVSQRT_SPEC.minimum_input
            and config.maximum_input == OFFICIAL_INVSQRT_SPEC.maximum_input
        ),
        regions=finalized_regions,
        transitions=tuple(transitions),
        mismatch_count=mismatch_count,
        first_mismatch_input=first_mismatch,
    )


def run_range_audit(
    config: RangeAuditConfig | None = None,
) -> RangeAuditResult:
    """Scan an inclusive domain using only the validated default baseline."""
    if config is None:
        config = RangeAuditConfig()
    if not isinstance(config, RangeAuditConfig):
        raise ValueError("config must be a RangeAuditConfig")

    precision = config.precision
    output_bits = precision.output_bits(config.n_p)
    declared_registers = (
        ("input", config.n_p * 2 + 2, "benchmark input register width"),
        ("normalized", config.n_p * 2 + 2, "baseline fixed-point model width"),
        ("coefficient_c0", precision.coef_bits, "baseline coefficient width"),
        ("coefficient_c1", precision.coef_bits, "baseline coefficient width"),
        ("coefficient_c2", precision.coef_bits, "baseline coefficient width"),
        ("coefficient_c3", precision.coef_bits, "baseline coefficient width"),
        ("horner_r1", precision.coef_bits, "baseline Horner register width"),
        ("horner_r2", precision.coef_bits, "baseline Horner register width"),
        ("horner_r3", precision.coef_bits, "baseline Horner register width"),
        ("square", precision.square_bits, "baseline square register width"),
        ("mantissa_product", precision.product_bits + 2, "baseline product register limit"),
        ("newton_correction", None, None),
        ("newton_result_before_denormalization", precision.result_bits + 1, "baseline result product register limit"),
        ("phase_numerator", output_bits, "baseline output register width"),
    )
    ranges = {
        name: _ValueRangeAccumulator(name, width, basis)
        for name, width, basis in declared_registers
    }
    ranges["shift_pairs"] = _ValueRangeAccumulator(
        "shift_pairs", None, None
    )
    ranges["interval_case"] = _ValueRangeAccumulator(
        "interval_case", None, None
    )

    row_ranges: dict[str, list[_RowRangeAccumulator]] = {}
    checks = {
        name: _CheckAccumulator(name)
        for name in (
            "horner_r1",
            "horner_r2",
            "horner_r3",
            "mantissa_product",
            "newton_result_before_denormalization",
            "denormalized_phase_numerator",
        )
    }
    output_digest = hashlib.sha256()
    critical_inputs = _critical_boundary_inputs(config.n_p)
    critical_digest = hashlib.sha256()
    for boundary in critical_inputs:
        critical_digest.update(boundary.to_bytes(4, "big"))
    critical_inputs_in_run = sum(
        config.minimum_input <= value <= config.maximum_input
        for value in critical_inputs
    )
    critical_input_index = bisect_left(critical_inputs, config.minimum_input)
    critical_inputs_seen = 0

    module_path = Path(__file__).resolve()
    baseline_path = module_path.parents[1] / "fixed_point.py"
    candidate_implementation_sha256 = _sha256(module_path)
    baseline_implementation_sha256 = _sha256(baseline_path)
    started_at = datetime.now(timezone.utc)
    start_clock = perf_counter()
    inputs_evaluated = 0
    for input_value in range(config.minimum_input, config.maximum_input + 1):
        if (
            critical_input_index < len(critical_inputs)
            and input_value == critical_inputs[critical_input_index]
        ):
            critical_input_index += 1
            critical_inputs_seen += 1
        result = fixed_point_reference(
            input_value, n_p=config.n_p, precision=precision
        )
        inputs_evaluated += 1

        unscaled_result = result.result_register >> result.shift_pairs
        values = (
            ("input", result.input_value),
            ("normalized", result.normalized_register),
            ("shift_pairs", result.shift_pairs),
            ("interval_case", result.interval_case),
            ("coefficient_c0", result.coefficient_integers[0]),
            ("coefficient_c1", result.coefficient_integers[1]),
            ("coefficient_c2", result.coefficient_integers[2]),
            ("coefficient_c3", result.coefficient_integers[3]),
            ("horner_r1", result.horner_registers[0]),
            ("horner_r2", result.horner_registers[1]),
            ("horner_r3", result.horner_registers[2]),
            ("square", result.square_register),
            ("mantissa_product", result.product_register),
            ("newton_correction", result.correction_register),
            ("newton_result_before_denormalization", unscaled_result),
            ("phase_numerator", result.result_register),
        )
        for name, value in values:
            ranges[name].observe(input_value, value)
        output_digest.update(result.result_register.to_bytes((output_bits + 7) // 8, "big"))

        coefficients = result.coefficient_integers
        horner_operands = (
            coefficients[3],
            result.horner_registers[0],
            result.horner_registers[1],
        )
        horner_accumulators = (
            coefficients[2],
            coefficients[1],
            coefficients[0],
        )
        for stage_name, operand, accumulator, expected in (
            zip(
                ("horner_r1", "horner_r2", "horner_r3"),
                horner_operands,
                horner_accumulators,
                result.horner_registers,
            )
        ):
            stage_rows = row_ranges.get(stage_name)
            if stage_rows is None:
                stage_rows = [
                    _RowRangeAccumulator(
                        operator=stage_name,
                        row_index=row_index,
                        weight=weight,
                        exponent=weight,
                    )
                    for row_index, (_, weight) in enumerate(result.delta_terms)
                ]
                row_ranges[stage_name] = stage_rows
            row_total = 0
            for row_index, (control, weight) in enumerate(result.delta_terms):
                contribution = _contribution(control, operand, weight)
                stage_rows[row_index].observe(
                    input_value, control, operand, contribution
                )
                row_total += contribution
            checks[stage_name].observe(
                input_value, accumulator - row_total == expected
            )

        normalized_width = config.n_p * 2 + 2
        normalized_rows = (
            (
                (result.normalized_register >> bit_position) & 1,
                bit_position - normalized_width + 2,
            )
            for bit_position in range(normalized_width)
        )
        product_rows = row_ranges.get("mantissa_product")
        if product_rows is None:
            product_rows = [
                _RowRangeAccumulator(
                    operator="mantissa_product",
                    row_index=row_index,
                    weight=weight,
                    exponent=weight,
                )
                for row_index, (_, weight) in enumerate(
                    (
                        (
                            0,
                            bit_position - normalized_width + 2,
                        )
                        for bit_position in range(normalized_width)
                    )
                )
            ]
            row_ranges["mantissa_product"] = product_rows
        product_total = 0
        for row_index, (control, weight) in enumerate(normalized_rows):
            contribution = _contribution(
                control, result.square_register, weight
            )
            product_rows[row_index].observe(
                input_value,
                control,
                result.square_register,
                contribution,
            )
            product_total += contribution
        checks["mantissa_product"].observe(
            input_value, product_total == result.product_register
        )

        result_rows = row_ranges.get("newton_result_before_denormalization")
        y_bits = tuple(
            (result.horner_registers[2] >> (precision.coef_bits - position)) & 1
            for position in range(1, precision.coef_bits + 1)
        )
        result_weights = tuple(-position for position in range(1, precision.coef_bits + 1))
        if result_rows is None:
            result_rows = [
                _RowRangeAccumulator(
                    operator="newton_result_before_denormalization",
                    row_index=row_index,
                    weight=weight,
                    exponent=precision.result_bits - precision.product_bits + weight,
                )
                for row_index, weight in enumerate(result_weights)
            ]
            row_ranges["newton_result_before_denormalization"] = result_rows
        result_total = 0
        for row_index, (control, weight) in enumerate(zip(y_bits, result_weights)):
            exponent = precision.result_bits - precision.product_bits + weight
            contribution = _contribution(
                control, result.correction_register, exponent
            )
            result_rows[row_index].observe(
                input_value,
                control,
                result.correction_register,
                contribution,
            )
            result_total += contribution
        checks["newton_result_before_denormalization"].observe(
            input_value, result_total == unscaled_result
        )
        checks["denormalized_phase_numerator"].observe(
            input_value,
            unscaled_result << result.shift_pairs == result.result_register,
        )

    completed_at = datetime.now(timezone.utc)
    elapsed = perf_counter() - start_clock
    final_ranges = tuple(ranges[name].finish() for name, _, _ in declared_registers) + (
        ranges["shift_pairs"].finish(),
        ranges["interval_case"].finish(),
    )
    final_rows = tuple(
        row_ranges[operator][row_index].finish()
        for operator in (
            "horner_r1",
            "horner_r2",
            "horner_r3",
            "mantissa_product",
            "newton_result_before_denormalization",
        )
        for row_index in range(len(row_ranges[operator]))
    )
    final_checks = tuple(check.finish() for check in checks.values())
    expected_count = config.maximum_input - config.minimum_input + 1
    all_checks_passed = (
        inputs_evaluated == expected_count
        and critical_inputs_seen == critical_inputs_in_run
        and all(check.mismatch_count == 0 for check in final_checks)
        and all(check.checked_inputs == inputs_evaluated for check in final_checks)
    )

    return RangeAuditResult(
        experiment_id=EXPERIMENT_ID,
        candidate_id=CANDIDATE_ID,
        candidate_version=CANDIDATE_VERSION,
        execution_status="COMPLETED" if all_checks_passed else "FAILED",
        configuration={
            "minimum_input": config.minimum_input,
            "maximum_input": config.maximum_input,
            "n_p": config.n_p,
            "precision": asdict(precision),
            "input_order": "ascending_inclusive",
            "mode": "baseline_observation_only",
        },
        minimum_input=config.minimum_input,
        maximum_input=config.maximum_input,
        inputs_evaluated=inputs_evaluated,
        full_domain=(
            config.minimum_input == OFFICIAL_INVSQRT_SPEC.minimum_input
            and config.maximum_input == OFFICIAL_INVSQRT_SPEC.maximum_input
        ),
        critical_inputs_total=len(critical_inputs),
        critical_inputs_in_run=critical_inputs_seen,
        critical_inputs_sha256=critical_digest.hexdigest(),
        baseline_source=REFERENCE_SOURCE,
        baseline_source_sha256=REFERENCE_SOURCE_SHA256,
        baseline_implementation_sha256=baseline_implementation_sha256,
        candidate_implementation_sha256=candidate_implementation_sha256,
        baseline_output_sha256=output_digest.hexdigest(),
        register_ranges=final_ranges,
        row_contribution_ranges=final_rows,
        consistency_checks=final_checks,
        started_at_utc=started_at.isoformat(),
        completed_at_utc=completed_at.isoformat(),
        runtime_seconds=elapsed,
        python_version=sys.version,
        platform=platform.platform(),
    )


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--minimum-input",
        type=int,
        default=OFFICIAL_INVSQRT_SPEC.minimum_input,
    )
    parser.add_argument(
        "--maximum-input",
        type=int,
        default=OFFICIAL_INVSQRT_SPEC.maximum_input,
    )
    args = parser.parse_args()
    result = run_range_audit(
        RangeAuditConfig(
            minimum_input=args.minimum_input,
            maximum_input=args.maximum_input,
        )
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
