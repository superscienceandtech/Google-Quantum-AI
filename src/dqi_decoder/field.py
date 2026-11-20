"""GF(2^12) arithmetic in the polynomial basis specified for DQI."""

FIELD_DEGREE = 12
FIELD_SIZE = 1 << FIELD_DEGREE

# alpha^12 + alpha^6 + alpha^4 + alpha + 1, including its degree-12 term.
FIELD_MODULUS_POLYNOMIAL = (1 << 12) | (1 << 6) | (1 << 4) | (1 << 1) | 1
_ELEMENT_MASK = FIELD_SIZE - 1


def validate_element(value: object) -> int:
    """Return a valid polynomial-basis field element, or raise a clear error.

    Bit k is the coefficient of alpha^k in the paper's little-endian
    polynomial basis (1, alpha, ..., alpha^11). This is an internal
    mathematical representation, not a circuit-wire serialization.
    """
    if type(value) is not int:
        raise TypeError("field elements must be integers")
    if not 0 <= value < FIELD_SIZE:
        raise ValueError(f"field element must be in [0, {FIELD_SIZE - 1}]")
    return value


def add(left: int, right: int) -> int:
    """Add two field elements (coefficient-wise addition modulo two)."""
    validate_element(left)
    validate_element(right)
    return left ^ right


def multiply(left: int, right: int) -> int:
    """Multiply and reduce two elements modulo the DQI field polynomial."""
    validate_element(left)
    validate_element(right)

    product = 0
    multiplicand = left
    multiplier = right
    while multiplier:
        if multiplier & 1:
            product ^= multiplicand
        multiplier >>= 1
        multiplicand <<= 1
        if multiplicand & FIELD_SIZE:
            multiplicand ^= FIELD_MODULUS_POLYNOMIAL
    return product & _ELEMENT_MASK


def power(base: int, exponent: int) -> int:
    """Raise a field element to a nonnegative integer power."""
    validate_element(base)
    if type(exponent) is not int:
        raise TypeError("exponent must be an integer")
    if exponent < 0:
        raise ValueError("exponent must be nonnegative")

    result = 1
    factor = base
    remaining = exponent
    while remaining:
        if remaining & 1:
            result = multiply(result, factor)
        remaining >>= 1
        if remaining:
            factor = multiply(factor, factor)
    return result


def inverse(value: int) -> int:
    """Return the multiplicative inverse of a nonzero field element."""
    validate_element(value)
    if value == 0:
        raise ValueError("zero has no multiplicative inverse")
    return power(value, FIELD_SIZE - 2)
