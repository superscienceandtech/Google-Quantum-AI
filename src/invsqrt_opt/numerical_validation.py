"""Reproducible validation for the paper-based classical INVSQRT model."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import json
import platform
import random
import sys
from typing import Iterable, Literal

from .contract import OFFICIAL_INVSQRT_SPEC, validate_input
from .reference_math import (
    ALGORITHM_VERSION,
    DECIMAL_PRECISION,
    PAPER_VERSION,
    _evaluate,
    _validate_decimal_precision,
    boundary_inputs,
)

ValidationMode = Literal["SAMPLED_VALIDATION", "EXHAUSTIVE_VALIDATION"]
DEFAULT_SAMPLE_COUNT = 1024
DEFAULT_SAMPLE_SEED = 7_007
_PAPER_REPORTED_MAX_RELATIVE_ERROR = Decimal("2.84e-8")
_PAPER_REPORTED_MAX_ERROR_INPUT = 2_588_411

_RELATIVE_ERROR_BINS = (
    ("<=1e-12", Decimal("1e-12")),
    ("(1e-12,1e-11]", Decimal("1e-11")),
    ("(1e-11,1e-10]", Decimal("1e-10")),
    ("(1e-10,1e-9]", Decimal("1e-9")),
    ("(1e-9,1e-8]", Decimal("1e-8")),
    (">1e-8", None),
)


@dataclass(frozen=True)
class NumericalValidationResult:
    algorithm_version: str
    paper_version: str
    source_references: tuple[str, ...]
    provenance_labels: tuple[str, ...]
    validation_mode: ValidationMode
    input_minimum: int
    input_maximum: int
    evaluation_count: int
    sample_count_requested: int | None
    sample_seed: int | None
    decimal_precision: int
    maximum_absolute_error: str
    maximum_absolute_error_input: int
    maximum_relative_error: str
    maximum_relative_error_input: int
    paper_reported_relative_error: str
    paper_reported_error_input: int
    measured_relative_error_at_paper_input: str | None
    absolute_difference_from_paper_report: str | None
    mean_signed_error: str
    mean_absolute_error: str
    mean_signed_relative_error: str
    mean_absolute_relative_error: str
    relative_error_distribution: tuple[tuple[str, int], ...]
    boundary_evaluation_count: int
    maximum_boundary_relative_error: str
    maximum_boundary_relative_error_input: int
    environment: tuple[tuple[str, str], ...]
    execution_timestamp_utc: str
    quantum_verification: str

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["source_references"] = list(self.source_references)
        data["provenance_labels"] = list(self.provenance_labels)
        data["relative_error_distribution"] = dict(
            self.relative_error_distribution
        )
        data["environment"] = dict(self.environment)
        return data


def _validate_mode(mode: str) -> ValidationMode:
    if mode == "SAMPLED_VALIDATION":
        return "SAMPLED_VALIDATION"
    if mode == "EXHAUSTIVE_VALIDATION":
        return "EXHAUSTIVE_VALIDATION"
    raise ValueError(f"Unsupported validation mode: {mode}")


def run_numerical_validation(
    inputs: Iterable[int],
    *,
    validation_mode: ValidationMode,
    precision: int = DECIMAL_PRECISION,
    sample_count_requested: int | None = None,
    sample_seed: int | None = None,
) -> NumericalValidationResult:
    """Measure model error against the independent Decimal square-root oracle."""
    mode = _validate_mode(validation_mode)
    _validate_decimal_precision(precision)
    if mode == "EXHAUSTIVE_VALIDATION":
        if not isinstance(inputs, range) or inputs != range(
            OFFICIAL_INVSQRT_SPEC.minimum_input,
            OFFICIAL_INVSQRT_SPEC.maximum_input + 1,
        ):
            raise ValueError(
                "Exhaustive mode requires the complete official input-domain range"
            )
        if sample_count_requested is not None or sample_seed is not None:
            raise ValueError("Exhaustive validation does not use sample metadata")
    elif sample_count_requested is not None and (
        isinstance(sample_count_requested, bool)
        or not isinstance(sample_count_requested, int)
        or sample_count_requested < 1
    ):
        raise ValueError("sample_count_requested must be a positive integer")
    if sample_seed is not None and (
        isinstance(sample_seed, bool) or not isinstance(sample_seed, int)
    ):
        raise ValueError("sample_seed must be an integer")

    boundaries = set(boundary_inputs())
    bin_counts = {label: 0 for label, _ in _RELATIVE_ERROR_BINS}
    count = 0
    signed_error_sum = Decimal(0)
    absolute_error_sum = Decimal(0)
    signed_relative_sum = Decimal(0)
    absolute_relative_sum = Decimal(0)
    max_absolute_error = Decimal(-1)
    max_absolute_input = 0
    max_relative_error = Decimal(-1)
    max_relative_input = 0
    max_boundary_relative_error = Decimal(-1)
    max_boundary_input = 0
    boundary_count = 0
    paper_input_relative_error: Decimal | None = None

    with localcontext() as context:
        context.prec = precision
        for raw_value in inputs:
            value = validate_input(raw_value)
            result = _evaluate(value)
            oracle = Decimal(1) / Decimal(value).sqrt()
            signed_error = result.final_estimate - oracle
            absolute_error = abs(signed_error)
            signed_relative_error = signed_error / oracle
            absolute_relative_error = abs(signed_relative_error)
            count += 1
            signed_error_sum += signed_error
            absolute_error_sum += absolute_error
            signed_relative_sum += signed_relative_error
            absolute_relative_sum += absolute_relative_error

            if absolute_error > max_absolute_error:
                max_absolute_error = absolute_error
                max_absolute_input = value
            if absolute_relative_error > max_relative_error:
                max_relative_error = absolute_relative_error
                max_relative_input = value
            if value == _PAPER_REPORTED_MAX_ERROR_INPUT:
                paper_input_relative_error = absolute_relative_error
            if value in boundaries:
                boundary_count += 1
                if absolute_relative_error > max_boundary_relative_error:
                    max_boundary_relative_error = absolute_relative_error
                    max_boundary_input = value

            for label, upper_bound in _RELATIVE_ERROR_BINS:
                if upper_bound is None or absolute_relative_error <= upper_bound:
                    bin_counts[label] += 1
                    break

    if count == 0:
        raise ValueError("At least one input is required")
    if max_boundary_relative_error < 0:
        max_boundary_relative_error = Decimal(0)
    if paper_input_relative_error is None:
        paper_difference = None
    else:
        with localcontext() as context:
            context.prec = precision
            paper_difference = abs(
                paper_input_relative_error
                - _PAPER_REPORTED_MAX_RELATIVE_ERROR
            )
    if mode == "EXHAUSTIVE_VALIDATION" and count != (
        OFFICIAL_INVSQRT_SPEC.maximum_input
        - OFFICIAL_INVSQRT_SPEC.minimum_input
        + 1
    ):
        raise ValueError("Exhaustive validation did not evaluate the full domain")

    environment = (
        ("python_version", platform.python_version()),
        ("python_implementation", platform.python_implementation()),
        ("platform", platform.platform()),
        ("machine", platform.machine()),
    )
    return NumericalValidationResult(
        algorithm_version=ALGORITHM_VERSION,
        paper_version=PAPER_VERSION,
        source_references=(
            "arXiv:2610.23832v2, §III.1.2, Eqs. (14)-(31), including (17)-(24)",
            "arXiv:2610.23832v2, Appendix B.1 and B.3, Eqs. (102)-(110)",
        ),
        provenance_labels=(
            "CLASSICAL_REFERENCE",
            "PAPER_REPORTED",
            "HIGH_PRECISION_ORACLE",
            mode,
            "QUANTUM_VERIFICATION_NOT_PERFORMED",
        ),
        validation_mode=mode,
        input_minimum=OFFICIAL_INVSQRT_SPEC.minimum_input,
        input_maximum=OFFICIAL_INVSQRT_SPEC.maximum_input,
        evaluation_count=count,
        sample_count_requested=sample_count_requested,
        sample_seed=sample_seed,
        decimal_precision=precision,
        maximum_absolute_error=str(max_absolute_error),
        maximum_absolute_error_input=max_absolute_input,
        maximum_relative_error=str(max_relative_error),
        maximum_relative_error_input=max_relative_input,
        paper_reported_relative_error=str(
            _PAPER_REPORTED_MAX_RELATIVE_ERROR
        ),
        paper_reported_error_input=_PAPER_REPORTED_MAX_ERROR_INPUT,
        measured_relative_error_at_paper_input=(
            None
            if paper_input_relative_error is None
            else str(paper_input_relative_error)
        ),
        absolute_difference_from_paper_report=(
            None if paper_difference is None else str(paper_difference)
        ),
        mean_signed_error=str(signed_error_sum / count),
        mean_absolute_error=str(absolute_error_sum / count),
        mean_signed_relative_error=str(signed_relative_sum / count),
        mean_absolute_relative_error=str(absolute_relative_sum / count),
        relative_error_distribution=tuple(bin_counts.items()),
        boundary_evaluation_count=boundary_count,
        maximum_boundary_relative_error=str(max_boundary_relative_error),
        maximum_boundary_relative_error_input=max_boundary_input,
        environment=environment,
        execution_timestamp_utc=datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z"),
        quantum_verification="NOT_PERFORMED",
    )


def deterministic_sample_inputs(
    *,
    sample_count: int = DEFAULT_SAMPLE_COUNT,
    seed: int = DEFAULT_SAMPLE_SEED,
) -> tuple[int, ...]:
    """Create a reproducible uniform integer sample plus required edge cases."""
    if isinstance(sample_count, bool) or not isinstance(sample_count, int):
        raise ValueError("sample_count must be a positive integer")
    if sample_count < 1:
        raise ValueError("sample_count must be a positive integer")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    rng = random.Random(seed)
    values = set(boundary_inputs())
    values.add(2_588_411)
    for _ in range(sample_count):
        values.add(
            rng.randint(
                OFFICIAL_INVSQRT_SPEC.minimum_input,
                OFFICIAL_INVSQRT_SPEC.maximum_input,
            )
        )
    return tuple(sorted(values))


def _main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--mode",
        choices=("SAMPLED_VALIDATION", "EXHAUSTIVE_VALIDATION"),
        default="EXHAUSTIVE_VALIDATION",
    )
    parser.add_argument("--precision", type=int, default=DECIMAL_PRECISION)
    arguments = parser.parse_args()
    if arguments.mode == "EXHAUSTIVE_VALIDATION":
        inputs: Iterable[int] = range(
            OFFICIAL_INVSQRT_SPEC.minimum_input,
            OFFICIAL_INVSQRT_SPEC.maximum_input + 1,
        )
        sample_count_requested = None
        sample_seed = None
    else:
        sample_count_requested = DEFAULT_SAMPLE_COUNT
        sample_seed = DEFAULT_SAMPLE_SEED
        inputs = deterministic_sample_inputs(
            sample_count=sample_count_requested, seed=sample_seed
        )
    result = run_numerical_validation(
        inputs,
        validation_mode=arguments.mode,
        precision=arguments.precision,
        sample_count_requested=sample_count_requested,
        sample_seed=sample_seed,
    )
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(_main())
