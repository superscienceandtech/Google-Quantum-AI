"""Input-preserving XOR-accumulation models for polynomial division."""

from collections.abc import Callable

from .field import validate_element
from .reversible_polynomial import PolynomialRegister
from .reversible_primitives import (
    xor_accumulate_add,
    xor_accumulate_inverse,
    xor_accumulate_multiply,
)

MAX_POLYNOMIAL_REGISTER_WIDTH = 8
MAX_DIVISION_DIVIDEND_WIDTH = 71
MAX_DIVISION_DIVISOR_WIDTH = 70
DivisionTarget = tuple[int, ...]
_AddPrimitive = Callable[[int, int, int], tuple[int, int, int]]
_MultiplyPrimitive = Callable[[int, int, int], tuple[int, int, int]]
_InversePrimitive = Callable[[int, int], tuple[int, int]]


def _validate_register(
    register: object,
    name: str,
    maximum_width: int,
) -> PolynomialRegister:
    if type(register) is not tuple:
        raise TypeError(f"{name} must be a tuple of field elements")
    if not register:
        raise ValueError(f"{name} must contain at least one coefficient")
    if len(register) > maximum_width:
        raise ValueError(
            f"{name} must contain at most "
            f"{maximum_width} coefficients"
        )
    return tuple(validate_element(value) for value in register)


def _validate_target(
    target: object,
    expected_width: int,
    name: str,
) -> DivisionTarget:
    if type(target) is not tuple:
        raise TypeError(f"{name} must be a tuple of field elements")
    if len(target) != expected_width:
        raise ValueError(
            f"{name} must contain exactly {expected_width} coefficients"
        )
    return tuple(validate_element(value) for value in target)


def _polynomial_degree(polynomial: PolynomialRegister) -> int:
    for index in range(len(polynomial) - 1, -1, -1):
        if polynomial[index] != 0:
            return index
    return -1


def _allocate(scratch: list[int], width: int) -> tuple[int, ...]:
    indices = tuple(range(len(scratch), len(scratch) + width))
    scratch.extend([0] * width)
    return indices


def _copy_register(
    source: tuple[int, ...],
    target: tuple[int, ...],
    scratch: list[int],
    add_primitive: _AddPrimitive,
) -> None:
    for source_index, target_index in zip(source, target):
        _, _, scratch[target_index] = add_primitive(
            scratch[source_index],
            0,
            scratch[target_index],
        )


def _xor_field_value(
    value: int,
    target_index: int,
    scratch: list[int],
    add_primitive: _AddPrimitive,
) -> None:
    _, _, scratch[target_index] = add_primitive(
        value,
        0,
        scratch[target_index],
    )


def _compute_accumulate_uncompute(
    dividend: PolynomialRegister,
    divisor: PolynomialRegister,
    quotient_target: DivisionTarget,
    remainder_target: DivisionTarget,
    add_primitive: _AddPrimitive = xor_accumulate_add,
    multiply_primitive: _MultiplyPrimitive = xor_accumulate_multiply,
    inverse_primitive: _InversePrimitive = xor_accumulate_inverse,
) -> tuple[DivisionTarget, DivisionTarget, tuple[int, ...]]:
    """Compute fixed-width division outputs, accumulate them, and uncompute."""
    scratch: list[int] = []
    remainder_width = len(dividend)
    quotient_width = len(dividend)
    divisor_degree = _polynomial_degree(divisor)
    divisor_leading = divisor[divisor_degree]

    initial_remainder = _allocate(scratch, remainder_width)
    initial_quotient = _allocate(scratch, quotient_width)
    for coefficient, target_index in zip(dividend, initial_remainder):
        _xor_field_value(
            coefficient,
            target_index,
            scratch,
            add_primitive,
        )

    inverse_index = _allocate(scratch, 1)[0]
    _, scratch[inverse_index] = inverse_primitive(
        divisor_leading,
        scratch[inverse_index],
    )

    current_remainder = initial_remainder
    current_quotient = initial_quotient
    steps: list[
        tuple[
            tuple[int, ...],
            tuple[int, ...],
            int,
            tuple[int, ...],
            tuple[int, ...],
            int,
            int,
        ]
    ] = []

    maximum_shift = len(dividend) - 1 - divisor_degree
    for shift in range(maximum_shift, -1, -1):
        leading_remainder_index = shift + divisor_degree
        factor_index = _allocate(scratch, 1)[0]
        _, _, scratch[factor_index] = multiply_primitive(
            scratch[current_remainder[leading_remainder_index]],
            scratch[inverse_index],
            scratch[factor_index],
        )

        next_quotient = _allocate(scratch, quotient_width)
        _copy_register(
            current_quotient,
            next_quotient,
            scratch,
            add_primitive,
        )
        _xor_field_value(
            scratch[factor_index],
            next_quotient[shift],
            scratch,
            add_primitive,
        )

        next_remainder = _allocate(scratch, remainder_width)
        _copy_register(
            current_remainder,
            next_remainder,
            scratch,
            add_primitive,
        )
        for divisor_index in range(divisor_degree + 1):
            target_index = shift + divisor_index
            _, _, scratch[next_remainder[target_index]] = multiply_primitive(
                scratch[factor_index],
                divisor[divisor_index],
                scratch[next_remainder[target_index]],
            )

        steps.append(
            (
                current_remainder,
                current_quotient,
                factor_index,
                next_remainder,
                next_quotient,
                shift,
                leading_remainder_index,
            )
        )
        current_remainder = next_remainder
        current_quotient = next_quotient

    expected_remainder_width = max(1, len(divisor) - 1)
    if any(
        scratch[index] != 0
        for index in current_remainder[expected_remainder_width:]
    ):
        raise RuntimeError("polynomial division remainder exceeds target width")

    updated_quotient = list(quotient_target)
    for value, target_index in zip(
        (scratch[index] for index in current_quotient),
        range(quotient_width),
    ):
        _, _, updated_quotient[target_index] = add_primitive(
            value,
            0,
            updated_quotient[target_index],
        )

    updated_remainder = list(remainder_target)
    for target_index in range(expected_remainder_width):
        value = (
            scratch[current_remainder[target_index]]
            if target_index < remainder_width
            else 0
        )
        _, _, updated_remainder[target_index] = add_primitive(
            value,
            0,
            updated_remainder[target_index],
        )

    for (
        previous_remainder,
        previous_quotient,
        factor_index,
        next_remainder,
        next_quotient,
        shift,
        leading_remainder_index,
    ) in reversed(steps):
        for divisor_index in range(divisor_degree, -1, -1):
            target_index = shift + divisor_index
            _, _, scratch[next_remainder[target_index]] = multiply_primitive(
                scratch[factor_index],
                divisor[divisor_index],
                scratch[next_remainder[target_index]],
            )
        _copy_register(
            previous_remainder,
            next_remainder,
            scratch,
            add_primitive,
        )
        _xor_field_value(
            scratch[factor_index],
            next_quotient[shift],
            scratch,
            add_primitive,
        )
        _copy_register(
            previous_quotient,
            next_quotient,
            scratch,
            add_primitive,
        )
        _, _, scratch[factor_index] = multiply_primitive(
            scratch[previous_remainder[leading_remainder_index]],
            scratch[inverse_index],
            scratch[factor_index],
        )

    for dividend_value, target_index in zip(dividend, initial_remainder):
        _, _, scratch[target_index] = add_primitive(
            dividend_value,
            0,
            scratch[target_index],
        )
    _, scratch[inverse_index] = inverse_primitive(
        divisor_leading,
        scratch[inverse_index],
    )

    return (
        tuple(updated_quotient),
        tuple(updated_remainder),
        tuple(scratch),
    )


def xor_accumulate_polynomial_division(
    dividend: PolynomialRegister,
    divisor: PolynomialRegister,
    quotient_target: DivisionTarget,
    remainder_target: DivisionTarget,
    *,
    max_dividend_width: int = MAX_DIVISION_DIVIDEND_WIDTH,
    max_divisor_width: int = MAX_DIVISION_DIVISOR_WIDTH,
) -> tuple[
    PolynomialRegister,
    PolynomialRegister,
    DivisionTarget,
    DivisionTarget,
]:
    """Accumulate fixed-width quotient and remainder into separate targets.

    Inputs are nonempty, low-degree-first GF(2^12) tuples. Their widths must
    not exceed ``max_dividend_width`` and ``max_divisor_width``, respectively;
    those limits are bounded by ``MAX_DIVISION_DIVIDEND_WIDTH`` and
    ``MAX_DIVISION_DIVISOR_WIDTH``. The quotient target width equals the
    dividend register width. The remainder target width is
    ``max(1, len(divisor) - 1)``. A zero divisor raises ``ZeroDivisionError``.

    The default capacities (71 dividend slots and 70 divisor slots) cover
    the P014 polynomial operands ``z^70`` and ``S(z)`` of degree at most 69.
    They do not imply P008 circuit compatibility or change P013's separate
    eight-slot input contract.
    """
    if type(max_dividend_width) is not int:
        raise TypeError("max_dividend_width must be an integer")
    if not 1 <= max_dividend_width <= MAX_DIVISION_DIVIDEND_WIDTH:
        raise ValueError(
            "max_dividend_width must be in "
            f"[1, {MAX_DIVISION_DIVIDEND_WIDTH}]"
        )
    if type(max_divisor_width) is not int:
        raise TypeError("max_divisor_width must be an integer")
    if not 1 <= max_divisor_width <= MAX_DIVISION_DIVISOR_WIDTH:
        raise ValueError(
            "max_divisor_width must be in "
            f"[1, {MAX_DIVISION_DIVISOR_WIDTH}]"
        )

    dividend_register = _validate_register(
        dividend,
        "dividend",
        max_dividend_width,
    )
    divisor_register = _validate_register(
        divisor,
        "divisor",
        max_divisor_width,
    )
    quotient_width = len(dividend_register)
    remainder_width = max(1, len(divisor_register) - 1)
    quotient_register = _validate_target(
        quotient_target,
        quotient_width,
        "quotient_target",
    )
    remainder_register = _validate_target(
        remainder_target,
        remainder_width,
        "remainder_target",
    )

    if _polynomial_degree(divisor_register) < 0:
        raise ZeroDivisionError("polynomial divisor must be nonzero")

    updated_quotient, updated_remainder, scratch = (
        _compute_accumulate_uncompute(
            dividend_register,
            divisor_register,
            quotient_register,
            remainder_register,
        )
    )
    if any(scratch):
        raise RuntimeError("polynomial division left nonzero scratch")

    return (
        dividend_register,
        divisor_register,
        updated_quotient,
        updated_remainder,
    )
