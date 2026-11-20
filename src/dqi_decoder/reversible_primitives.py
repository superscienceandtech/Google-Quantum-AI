"""Input-preserving XOR-accumulation models for DQI field primitives.

These functions model reversible register relations; they do not construct
quantum gates or establish a circuit decomposition.
"""

from .field import FIELD_SIZE, add, inverse, multiply, validate_element


def xor_accumulate_add(left: int, right: int, target: int) -> tuple[int, int, int]:
    """Return ``(left, right, target XOR (left + right))`` over GF(2^12)."""
    validate_element(left)
    validate_element(right)
    validate_element(target)
    return left, right, target ^ add(left, right)


def xor_accumulate_multiply(
    left: int,
    right: int,
    target: int,
) -> tuple[int, int, int]:
    """Return ``(left, right, target XOR (left * right))`` over GF(2^12)."""
    validate_element(left)
    validate_element(right)
    validate_element(target)
    return left, right, target ^ multiply(left, right)


def xor_accumulate_square(value: int, target: int) -> tuple[int, int]:
    """Return ``(value, target XOR value^2)`` over GF(2^12)."""
    validate_element(value)
    validate_element(target)
    return value, target ^ multiply(value, value)


def xor_accumulate_inverse(value: int, target: int) -> tuple[int, int]:
    """Accumulate the inverse, using the total extension inverse(0)=0.

    The zero convention makes this oracle a total function; it does not assert
    that zero has a multiplicative inverse in the field.
    """
    validate_element(value)
    validate_element(target)
    inverse_value = 0 if value == 0 else inverse(value)
    return value, target ^ inverse_value


def target_width() -> int:
    """Return the width in bits of each field-element target register."""
    return FIELD_SIZE.bit_length() - 1
