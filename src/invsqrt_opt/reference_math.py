"""High-precision classical model of the paper's INVSQRT reference stages.

This models the paper's real-arithmetic normalization, cubic estimate, and
single Newton step. It does not emulate the reference circuit's fixed-point
registers, truncation, QROM encoding, or quantum phase gates.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, localcontext
from fractions import Fraction

from .contract import OFFICIAL_INVSQRT_SPEC, validate_input

DECIMAL_PRECISION = 50
PAPER_VERSION = "arXiv:2610.23832v2"
ALGORITHM_VERSION = "P007-paper-real-arithmetic-v1"

_A_COEFFICIENTS = tuple(
    Decimal(value)
    for value in (
        "0.99994132489119882162",
        "0.49609891915903542303",
        "0.33261112772430493331",
        "0.14876762006038398086",
    )
)
_B_COEFFICIENTS = tuple(
    Decimal(value)
    for value in (
        "0.81648515205385221995",
        "0.27136515484240234115",
        "0.12756148214815175348",
        "0.044753028579153842218",
    )
)
_NORMALIZED_SCALE_BITS = 2 * OFFICIAL_INVSQRT_SPEC.np
_NORMALIZATION_BOUNDARIES = tuple(
    1 << exponent
    for exponent in range(2, _NORMALIZED_SCALE_BITS + 1, 2)
)
_POLYNOMIAL_INTERVALS = (Decimal("1.5"), Decimal("2"), Decimal("3"))


@dataclass(frozen=True)
class ReferenceResult:
    """Observable stages of the classical real-arithmetic reference model."""

    input_value: int
    leading_zero_pairs: int
    normalized_input: Fraction
    polynomial_argument: Fraction
    polynomial_region: str
    polynomial_interval: tuple[Decimal, Decimal]
    polynomial_rescaling: Decimal
    initial_estimate: Decimal
    corrected_normalized_estimate: Decimal
    denormalized_register_estimate: Decimal
    final_estimate: Decimal
    phase_turns_unwrapped: Decimal
    phase_turns_modulo_one: Decimal


def _validate_decimal_precision(precision: int) -> None:
    if isinstance(precision, bool) or not isinstance(precision, int):
        raise ValueError("precision must be a positive integer")
    if precision < 32:
        raise ValueError("precision must be at least 32 decimal digits")


def _normalization(value: int) -> tuple[int, Fraction]:
    shift_pairs = (
        OFFICIAL_INVSQRT_SPEC.input_width - value.bit_length()
    ) // 2
    denominator_power = _NORMALIZED_SCALE_BITS - 2 * shift_pairs
    normalized = Fraction(value, 1 << denominator_power)
    return shift_pairs, normalized


def _polynomial(
    argument: Decimal, coefficients: tuple[Decimal, ...], offset: Decimal
) -> Decimal:
    a0, a1, a2, a3 = coefficients
    delta = argument - offset
    return ((-a3 * delta + a2) * delta - a1) * delta + a0


def _evaluate(value: int) -> ReferenceResult:
    shift_pairs, normalized_fraction = _normalization(value)
    normalized = (
        Decimal(normalized_fraction.numerator)
        / Decimal(normalized_fraction.denominator)
    )

    if normalized >= 2:
        argument_fraction = normalized_fraction / 2
        argument = normalized / 2
        rescaling = Decimal(1) / Decimal(2).sqrt()
    else:
        argument_fraction = normalized_fraction
        argument = normalized
        rescaling = Decimal(1)

    if argument < Decimal("1.5"):
        coefficients = _A_COEFFICIENTS
        offset = Decimal(1)
        interval = (Decimal(1), Decimal("1.5"))
        region = "A"
    else:
        coefficients = _B_COEFFICIENTS
        offset = Decimal("1.5")
        interval = (Decimal("1.5"), Decimal(2))
        region = "B"

    initial = _polynomial(argument, coefficients, offset) * rescaling
    corrected_normalized = (
        initial
        * (Decimal(3) - normalized * initial * initial)
        / Decimal(2)
    )
    denormalized_register_estimate = (
        corrected_normalized * (Decimal(2) ** shift_pairs)
    )
    final = denormalized_register_estimate / (
        Decimal(2) ** OFFICIAL_INVSQRT_SPEC.np
    )
    phase = Decimal(OFFICIAL_INVSQRT_SPEC.beta) * final
    phase_modulo_one = phase % Decimal(1)

    return ReferenceResult(
        input_value=value,
        leading_zero_pairs=shift_pairs,
        normalized_input=normalized_fraction,
        polynomial_argument=argument_fraction,
        polynomial_region=region,
        polynomial_interval=interval,
        polynomial_rescaling=rescaling,
        initial_estimate=initial,
        corrected_normalized_estimate=corrected_normalized,
        denormalized_register_estimate=denormalized_register_estimate,
        final_estimate=final,
        phase_turns_unwrapped=phase,
        phase_turns_modulo_one=phase_modulo_one,
    )


def paper_reference(value: object, *, precision: int = DECIMAL_PRECISION) -> ReferenceResult:
    """Evaluate the supported paper stages using Decimal real arithmetic."""
    integer_value = validate_input(value)
    _validate_decimal_precision(precision)
    with localcontext() as context:
        context.prec = precision
        return _evaluate(integer_value)


def inverse_sqrt_oracle(
    value: object, *, precision: int = DECIMAL_PRECISION
) -> Decimal:
    """Return an independent high-precision oracle for 1/sqrt(value)."""
    integer_value = validate_input(value)
    _validate_decimal_precision(precision)
    with localcontext() as context:
        context.prec = precision
        return Decimal(1) / Decimal(integer_value).sqrt()


def phase_turns_oracle(
    value: object, *, precision: int = DECIMAL_PRECISION
) -> Decimal:
    """Return the benchmark target phase in turns, independently of the model."""
    integer_value = validate_input(value)
    _validate_decimal_precision(precision)
    with localcontext() as context:
        context.prec = precision
        return Decimal(OFFICIAL_INVSQRT_SPEC.beta) / Decimal(integer_value).sqrt()


def boundary_inputs() -> tuple[int, ...]:
    """Return valid inputs at and immediately around normalization/polynomial edges."""
    candidates = {OFFICIAL_INVSQRT_SPEC.minimum_input, OFFICIAL_INVSQRT_SPEC.maximum_input}
    for boundary in _NORMALIZATION_BOUNDARIES:
        candidates.update((boundary - 1, boundary, boundary + 1))

    for shift_pairs in range(OFFICIAL_INVSQRT_SPEC.np + 1):
        scale = 1 << (2 * (OFFICIAL_INVSQRT_SPEC.np - shift_pairs))
        for boundary in _POLYNOMIAL_INTERVALS:
            exact = Fraction(boundary) * scale
            floor_value = exact.numerator // exact.denominator
            candidates.update((floor_value - 1, floor_value, floor_value + 1))

    return tuple(
        sorted(
            value
            for value in candidates
            if OFFICIAL_INVSQRT_SPEC.minimum_input
            <= value
            <= OFFICIAL_INVSQRT_SPEC.maximum_input
        )
    )
