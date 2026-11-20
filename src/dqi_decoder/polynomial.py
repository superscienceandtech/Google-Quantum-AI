"""Low-degree-first polynomial arithmetic over the DQI finite field."""

from collections.abc import Sequence

from .field import add, inverse, multiply, validate_element

Polynomial = tuple[int, ...]


def normalize(polynomial: Sequence[int]) -> Polynomial:
    """Validate coefficients and remove trailing high-degree zeroes."""
    coefficients = [validate_element(value) for value in polynomial]
    while coefficients and coefficients[-1] == 0:
        coefficients.pop()
    return tuple(coefficients)


def degree(polynomial: Sequence[int]) -> int:
    """Return polynomial degree, or -1 for the zero polynomial."""
    return len(normalize(polynomial)) - 1


def add_polynomials(
    left: Sequence[int], right: Sequence[int]
) -> Polynomial:
    """Add polynomials coefficient-wise over characteristic two."""
    left_coefficients = normalize(left)
    right_coefficients = normalize(right)
    result = []
    for index in range(max(len(left_coefficients), len(right_coefficients))):
        left_value = left_coefficients[index] if index < len(left_coefficients) else 0
        right_value = (
            right_coefficients[index] if index < len(right_coefficients) else 0
        )
        result.append(add(left_value, right_value))
    return normalize(result)


def scale_polynomial(
    polynomial: Sequence[int], scalar: int
) -> Polynomial:
    """Multiply every coefficient by a field scalar."""
    coefficients = normalize(polynomial)
    validate_element(scalar)
    return normalize([multiply(value, scalar) for value in coefficients])


def multiply_polynomials(
    left: Sequence[int], right: Sequence[int]
) -> Polynomial:
    """Multiply polynomials using the DQI field operations."""
    left_coefficients = normalize(left)
    right_coefficients = normalize(right)
    if not left_coefficients or not right_coefficients:
        return ()

    product = [0] * (len(left_coefficients) + len(right_coefficients) - 1)
    for left_index, left_value in enumerate(left_coefficients):
        for right_index, right_value in enumerate(right_coefficients):
            product[left_index + right_index] = add(
                product[left_index + right_index],
                multiply(left_value, right_value),
            )
    return normalize(product)


def divide_polynomials(
    dividend: Sequence[int], divisor: Sequence[int]
) -> tuple[Polynomial, Polynomial]:
    """Return quotient and remainder over the DQI finite field."""
    remainder = list(normalize(dividend))
    divisor_coefficients = normalize(divisor)
    if not divisor_coefficients:
        raise ZeroDivisionError("polynomial divisor must be nonzero")

    quotient = [0] * max(0, len(remainder) - len(divisor_coefficients) + 1)
    leading_inverse = inverse(divisor_coefficients[-1])
    while remainder and len(remainder) >= len(divisor_coefficients):
        shift = len(remainder) - len(divisor_coefficients)
        factor = multiply(remainder[-1], leading_inverse)
        quotient[shift] = factor
        for index, coefficient in enumerate(divisor_coefficients):
            target = shift + index
            remainder[target] = add(
                remainder[target],
                multiply(factor, coefficient),
            )
        while remainder and remainder[-1] == 0:
            remainder.pop()
    return normalize(quotient), normalize(remainder)


def evaluate_polynomial(polynomial: Sequence[int], point: int) -> int:
    """Evaluate a polynomial by Horner's method."""
    coefficients = normalize(polynomial)
    validate_element(point)
    value = 0
    for coefficient in reversed(coefficients):
        value = add(multiply(value, point), coefficient)
    return value


def formal_derivative(polynomial: Sequence[int]) -> Polynomial:
    """Return the formal derivative in characteristic two."""
    coefficients = normalize(polynomial)
    derivative = [0] * max(0, len(coefficients) - 1)
    for exponent in range(1, len(coefficients), 2):
        derivative[exponent - 1] = coefficients[exponent]
    return normalize(derivative)
