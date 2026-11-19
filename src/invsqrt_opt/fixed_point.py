"""Independent integer model of the mirrored INVSQRT reference circuit.

The arithmetic and layouts follow the reference implementation identified in
docs/research/INVSQRT_FIXED_POINT_SEMANTICS_AND_EMULATOR_READINESS.md. This
module models its classical fixed-point pipeline; it does not build or simulate
a quantum circuit.
"""

from __future__ import annotations

from dataclasses import astuple, dataclass
from functools import lru_cache
import math
from typing import Iterable

from .contract import OFFICIAL_INVSQRT_SPEC, validate_input

REFERENCE_SOURCE = (
    "qarena-ai/invsqrt@6ac78ec5ace6dfd5831ccac2547041408f5d8278:"
    "verifiers/invsqrt/nr_reference_circuit.py"
)
REFERENCE_SOURCE_SHA256 = "bb90330dcf774f7b502de471293facba67f27952cc8808fe4a9970a9b1322e23"
ALGORITHM_VERSION = "P008-independent-fixed-point-v1"

_POLYNOMIAL_A = (
    0.99994132489119882162,
    0.49609891915903542303,
    0.33261112772430493331,
    0.14876762006038398086,
)
_POLYNOMIAL_B = (
    0.81648515205385221995,
    0.27136515484240234115,
    0.12756148214815175348,
    0.044753028579153842218,
)


@lru_cache(maxsize=None)
def _coefficient_table(coef_bits: int) -> tuple[tuple[int, ...], ...]:
    cases = (
        _POLYNOMIAL_A,
        _POLYNOMIAL_B,
        tuple(
            coefficient / (2**power * math.sqrt(2))
            for power, coefficient in enumerate(_POLYNOMIAL_A)
        ),
        tuple(
            coefficient / (2**power * math.sqrt(2))
            for power, coefficient in enumerate(_POLYNOMIAL_B)
        ),
    )
    return tuple(
        tuple(round(coefficient * 2**coef_bits) for coefficient in case)
        for case in cases
    )


@dataclass(frozen=True)
class FixedPointPrecision:
    """Source-defined widths; the emulator currently supports only defaults."""

    delta_bits: int = 14
    coef_bits: int = 17
    square_bits: int = 28
    product_bits: int = 28
    result_bits: int = 29

    def __post_init__(self) -> None:
        for name, value in zip(
            (
                "delta_bits",
                "coef_bits",
                "square_bits",
                "product_bits",
                "result_bits",
            ),
            astuple(self),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")

    def coefficient_table(self) -> tuple[tuple[int, ...], ...]:
        """Return source-defined nearest-integer coefficient magnitudes."""
        return _coefficient_table(self.coef_bits)

    def output_bits(self, n_p: int) -> int:
        _validate_positive_integer("n_p", n_p)
        return self.result_bits + n_p + 1


_SUPPORTED_PRECISION = FixedPointPrecision()


@dataclass(frozen=True)
class FixedPointResult:
    """Intermediate integer registers and final phase-turn representation."""

    input_value: int
    shift_pairs: int
    normalized_register: int
    interval_case: int
    coefficient_integers: tuple[int, int, int, int]
    delta_terms: tuple[tuple[int, int], ...]
    horner_registers: tuple[int, int, int]
    square_register: int
    product_register: int
    correction_register: int
    result_register: int
    phase_fraction_bits: int
    output_bits: int

    @property
    def phase_turns_numerator(self) -> int:
        return self.result_register

    @property
    def phase_turns_denominator(self) -> int:
        return 1 << self.output_bits


def _validate_positive_integer(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return value


def _bit(value: int, index: int) -> int:
    return (value >> index) & 1


def _truncated_product(
    rows: Iterable[tuple[int, int]],
    operand: int,
    output_fraction_bits: int,
    operand_fraction_bits: int,
    register_limit_bits: int,
) -> int:
    """Accumulate the source's row-wise column truncations without rounding."""
    for name, value, minimum in (
        ("output_fraction_bits", output_fraction_bits, 0),
        ("operand_fraction_bits", operand_fraction_bits, 0),
        ("register_limit_bits", register_limit_bits, 1),
    ):
        if (
            isinstance(value, bool)
            or not isinstance(value, int)
            or value < minimum
        ):
            raise ValueError(f"{name} must be an integer of at least {minimum}")
    if isinstance(operand, bool) or not isinstance(operand, int) or operand < 0:
        raise ValueError("operand must be a non-negative integer")

    accumulator = 0
    for row in rows:
        if not isinstance(row, tuple) or len(row) != 2:
            raise ValueError("each product row must be a (control, weight) tuple")
        control, weight = row
        if type(control) is not int or control not in (0, 1):
            raise ValueError("row control must be the integer 0 or 1")
        if isinstance(weight, bool) or not isinstance(weight, int):
            raise ValueError("row weight must be an integer")
        exponent = output_fraction_bits - operand_fraction_bits + weight
        accumulator += control * (
            operand << exponent if exponent >= 0 else operand >> -exponent
        )
    if accumulator >= 1 << register_limit_bits:
        raise OverflowError("Intermediate register overflow.")
    return accumulator


def fixed_point_reference(
    value: object,
    *,
    n_p: int = OFFICIAL_INVSQRT_SPEC.np,
    precision: FixedPointPrecision = FixedPointPrecision(),
) -> FixedPointResult:
    """Evaluate the sourced fixed-point model for one integer input.

    Coefficient conversion uses the source's binary64 operations followed by
    Python's round-to-nearest/ties-to-even. Every multiplier truncates each
    partial-product row to the target least-significant bit before accumulation.
    Only the benchmark's n_p=10 and default register widths are supported.
    """
    x = validate_input(value)
    n_p = _validate_positive_integer("n_p", n_p)
    if not isinstance(precision, FixedPointPrecision):
        raise ValueError("precision must be a FixedPointPrecision")
    if n_p != OFFICIAL_INVSQRT_SPEC.np:
        raise ValueError(
            f"Only the benchmark n_p={OFFICIAL_INVSQRT_SPEC.np} is supported"
        )
    if precision != _SUPPORTED_PRECISION:
        raise ValueError("Only the default fixed-point precision is supported")

    width = 2 * n_p + 2
    shift_pairs = (width - x.bit_length()) // 2
    normalized = x << (2 * shift_pairs)
    top = _bit(normalized, width - 1)
    second = _bit(normalized, width - 2)
    third = _bit(normalized, width - 3)
    interval_case = third if top == 0 else 2 + second

    coefficient_table = precision.coefficient_table()
    coefficients = tuple(coefficient_table[interval_case])
    delta = [(top & third, -1)]
    delta.extend(
        (_bit(normalized, width - 2 - fractional_position), -fractional_position)
        for fractional_position in range(
            2, min(precision.delta_bits, width - 2) + 1
        )
    )

    coefficient_width = precision.coef_bits
    current = coefficients[3]
    horner_values: list[int] = []
    for accumulator in (coefficients[2], coefficients[1], coefficients[0]):
        product = _truncated_product(
            delta,
            current,
            coefficient_width,
            coefficient_width,
            coefficient_width,
        )
        current = accumulator - product
        if current <= 0 or current >= 1 << coefficient_width:
            raise OverflowError("Horner intermediate does not fit its register.")
        horner_values.append(current)
    y0 = current

    square_width = precision.square_bits
    y_bits = {
        fractional_position: _bit(
            y0, coefficient_width - fractional_position
        )
        for fractional_position in range(1, coefficient_width + 1)
    }
    square = 0
    for fractional_position in range(1, coefficient_width + 1):
        if 2 * fractional_position <= square_width:
            square += y_bits[fractional_position] << (
                square_width - 2 * fractional_position
            )
        for other_position in range(fractional_position + 1, coefficient_width + 1):
            product_position = fractional_position + other_position - 1
            if product_position <= square_width:
                square += (
                    y_bits[fractional_position] & y_bits[other_position]
                ) << (square_width - product_position)
    if square >= 1 << square_width:
        raise OverflowError("Intermediate register overflow.")

    product_width = precision.product_bits
    normalized_rows = [
        (_bit(normalized, bit_position), bit_position - width + 2)
        for bit_position in range(width)
    ]
    product = _truncated_product(
        normalized_rows,
        square,
        product_width,
        square_width,
        product_width + 2,
    )
    correction = (3 << product_width) - product
    result_width = precision.result_bits
    result = _truncated_product(
        (
            (y_bits[fractional_position], -fractional_position)
            for fractional_position in range(1, coefficient_width + 1)
        ),
        correction,
        result_width,
        product_width,
        result_width + 1,
    )
    output = result << shift_pairs
    output_bits = precision.output_bits(n_p)
    if output >= 1 << output_bits:
        raise OverflowError("Denormalized result does not fit its register.")

    return FixedPointResult(
        input_value=x,
        shift_pairs=shift_pairs,
        normalized_register=normalized,
        interval_case=interval_case,
        coefficient_integers=(
            coefficients[0],
            coefficients[1],
            coefficients[2],
            coefficients[3],
        ),
        delta_terms=tuple(delta),
        horner_registers=(
            horner_values[0],
            horner_values[1],
            horner_values[2],
        ),
        square_register=square,
        product_register=product,
        correction_register=correction,
        result_register=output,
        phase_fraction_bits=output_bits,
        output_bits=output_bits,
    )


def fixed_point_value(
    value: object,
    *,
    n_p: int = OFFICIAL_INVSQRT_SPEC.np,
    precision: FixedPointPrecision = FixedPointPrecision(),
) -> tuple[int, int]:
    """Return `(fixed-point numerator, denominator)` for the phase in turns."""
    result = fixed_point_reference(value, n_p=n_p, precision=precision)
    return result.result_register, result.phase_turns_denominator
