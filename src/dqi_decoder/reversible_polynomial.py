"""Input-preserving XOR-accumulation models for fixed-width polynomials."""

from .field import validate_element
from .reversible_primitives import (
    xor_accumulate_add,
    xor_accumulate_multiply,
)

PolynomialRegister = tuple[int, ...]


def _validate_register(register: object, name: str) -> PolynomialRegister:
    if type(register) is not tuple:
        raise TypeError(f"{name} must be a tuple of field elements")
    if not register:
        raise ValueError(f"{name} must contain at least one coefficient")
    return tuple(validate_element(value) for value in register)


def _validate_target(
    target: object,
    expected_width: int,
) -> PolynomialRegister:
    target_register = _validate_register(target, "target")
    if len(target_register) != expected_width:
        raise ValueError(
            f"target must contain exactly {expected_width} coefficients"
        )
    return target_register


def xor_accumulate_polynomial_add(
    left: PolynomialRegister,
    right: PolynomialRegister,
    target: PolynomialRegister,
) -> tuple[PolynomialRegister, PolynomialRegister, PolynomialRegister]:
    """Accumulate the low-degree-first polynomial sum into ``target``.

    Registers are nonempty tuples of GF(2^12) elements. A shorter operand is
    zero-padded through the larger operand's width; the target width must be
    exactly the larger operand width. The operands are preserved.
    """
    left_register = _validate_register(left, "left")
    right_register = _validate_register(right, "right")
    result_width = max(len(left_register), len(right_register))
    target_register = _validate_target(target, result_width)

    result = []
    for index, target_value in enumerate(target_register):
        left_value = left_register[index] if index < len(left_register) else 0
        right_value = right_register[index] if index < len(right_register) else 0
        _, _, accumulated = xor_accumulate_add(
            left_value,
            right_value,
            target_value,
        )
        result.append(accumulated)

    return left_register, right_register, tuple(result)


def xor_accumulate_polynomial_multiply(
    left: PolynomialRegister,
    right: PolynomialRegister,
    target: PolynomialRegister,
) -> tuple[PolynomialRegister, PolynomialRegister, PolynomialRegister]:
    """Accumulate the full polynomial product into a fixed-width target.

    Registers are nonempty, low-degree-first tuples of GF(2^12) elements.
    For operand widths ``m`` and ``n``, the target width is exactly
    ``m + n - 1``; no product coefficient is truncated. An all-zero tuple
    represents the zero polynomial at its declared register width.
    """
    left_register = _validate_register(left, "left")
    right_register = _validate_register(right, "right")
    result_width = len(left_register) + len(right_register) - 1
    target_register = _validate_target(target, result_width)
    result = list(target_register)

    for left_index, left_value in enumerate(left_register):
        for right_index, right_value in enumerate(right_register):
            target_index = left_index + right_index
            _, _, result[target_index] = xor_accumulate_multiply(
                left_value,
                right_value,
                result[target_index],
            )

    return left_register, right_register, tuple(result)
