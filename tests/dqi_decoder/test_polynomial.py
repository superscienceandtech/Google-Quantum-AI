"""Research unit tests for low-degree-first polynomial arithmetic."""

import unittest

from dqi_decoder.field import FIELD_DEGREE
from dqi_decoder.polynomial import (
    add_polynomials,
    degree,
    divide_polynomials,
    evaluate_polynomial,
    formal_derivative,
    multiply_polynomials,
    normalize,
)

_FIELD_MODULUS = 0x1053


def _reference_multiply(left: int, right: int) -> int:
    product = 0
    while right:
        if right & 1:
            product ^= left
        left <<= 1
        right >>= 1
    while product.bit_length() > FIELD_DEGREE:
        product ^= _FIELD_MODULUS << (product.bit_length() - FIELD_DEGREE - 1)
    return product


def _reference_evaluate(polynomial: tuple[int, ...], point: int) -> int:
    value = 0
    for coefficient in reversed(polynomial):
        value = _reference_multiply(value, point) ^ coefficient
    return value


def _reference_divide(
    dividend: tuple[int, ...],
    divisor: tuple[int, ...],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    remainder = list(dividend)
    while remainder and remainder[-1] == 0:
        remainder.pop()
    if not divisor:
        raise ZeroDivisionError
    quotient = [0] * max(0, len(remainder) - len(divisor) + 1)
    inverse_leading = _reference_power(divisor[-1], (1 << FIELD_DEGREE) - 2)
    while remainder and len(remainder) >= len(divisor):
        shift = len(remainder) - len(divisor)
        factor = _reference_multiply(remainder[-1], inverse_leading)
        quotient[shift] = factor
        for index, coefficient in enumerate(divisor):
            remainder[shift + index] ^= _reference_multiply(factor, coefficient)
        while remainder and remainder[-1] == 0:
            remainder.pop()
    return _trim(quotient), tuple(remainder)


def _reference_power(base: int, exponent: int) -> int:
    result = 1
    factor = base
    while exponent:
        if exponent & 1:
            result = _reference_multiply(result, factor)
        exponent >>= 1
        if exponent:
            factor = _reference_multiply(factor, factor)
    return result


def _trim(values: list[int]) -> tuple[int, ...]:
    while values and values[-1] == 0:
        values.pop()
    return tuple(values)


class PolynomialTests(unittest.TestCase):
    def test_coefficients_are_low_degree_first_and_normalized(self):
        self.assertEqual(normalize((1, 2, 0, 0)), (1, 2))
        self.assertEqual(degree((1, 2, 0)), 1)
        self.assertEqual(degree(()), -1)

    def test_add_and_multiply(self):
        self.assertEqual(add_polynomials((1, 2), (1, 3)), (0, 1))
        self.assertEqual(multiply_polynomials((1, 1), (1, 1)), (1, 0, 1))

    def test_division_reconstructs_dividend(self):
        dividend = (5, 0x17, 0x23, 0x11, 0x7)
        divisor = (3, 2, 1)
        quotient, remainder = divide_polynomials(dividend, divisor)

        expected_quotient, expected_remainder = _reference_divide(
            dividend,
            divisor,
        )
        self.assertEqual(quotient, expected_quotient)
        self.assertEqual(remainder, expected_remainder)
        self.assertLess(degree(remainder), degree(divisor))

    def test_division_preserves_nonzero_remainder_and_constant_divisors(self):
        dividend = (7, 0x12, 0x3, 0, 0)
        quotient, remainder = divide_polynomials(dividend, (1, 1))
        self.assertEqual(
            (quotient, remainder),
            _reference_divide(dividend, (1, 1)),
        )
        self.assertNotEqual(remainder, ())

        quotient, remainder = divide_polynomials(dividend, (3,))
        self.assertEqual(remainder, ())
        self.assertEqual(
            quotient,
            _reference_divide(dividend, (3,))[0],
        )

    def test_division_rejects_zero_polynomial(self):
        with self.assertRaises(ZeroDivisionError):
            divide_polynomials((1,), ())

    def test_evaluation_and_formal_derivative(self):
        polynomial = (3, 2, 5, 7)
        for point in (0, 1, 2, 0xA53, 0xFFF):
            with self.subTest(point=point):
                self.assertEqual(
                    evaluate_polynomial(polynomial, point),
                    _reference_evaluate(polynomial, point),
                )
        self.assertEqual(formal_derivative(polynomial), (2, 0, 7))

    def test_zero_and_constant_polynomials(self):
        self.assertEqual(normalize((0, 0)), ())
        self.assertEqual(evaluate_polynomial((), 0xA53), 0)
        self.assertEqual(evaluate_polynomial((0xA53,), 0xFFF), 0xA53)


if __name__ == "__main__":
    unittest.main()
