"""Research tests for fixed-width reversible polynomial register models."""

from itertools import product
from typing import Callable
import unittest

from dqi_decoder.field import FIELD_SIZE
from dqi_decoder.reversible_polynomial import (
    xor_accumulate_polynomial_add,
    xor_accumulate_polynomial_multiply,
)

_FIELD_MODULUS = 0x1053
_SMALL_FIELD_POLYNOMIALS = {2: 0b111, 3: 0b1011, 4: 0b10011}


def _call_unchecked(function: Callable[..., object], *arguments: object) -> object:
    return function(*arguments)


def _polynomial_remainder(dividend: int, divisor: int) -> int:
    remainder = dividend
    divisor_degree = divisor.bit_length() - 1
    while remainder and remainder.bit_length() - 1 >= divisor_degree:
        remainder ^= divisor << (
            remainder.bit_length() - 1 - divisor_degree
        )
    return remainder


def _is_irreducible(polynomial: int, degree: int) -> bool:
    if polynomial.bit_length() != degree + 1:
        return False
    for divisor_degree in range(1, degree // 2 + 1):
        for lower_bits in range(1 << divisor_degree):
            divisor = (1 << divisor_degree) | lower_bits
            if _polynomial_remainder(polynomial, divisor) == 0:
                return False
    return True


def _reference_field_multiply(
    left: int,
    right: int,
    modulus: int,
    degree: int,
) -> int:
    product_value = 0
    while right:
        if right & 1:
            product_value ^= left
        left <<= 1
        right >>= 1
    while product_value.bit_length() > degree:
        product_value ^= modulus << (
            product_value.bit_length() - degree - 1
        )
    return product_value


def _reference_polynomial_add(
    left: tuple[int, ...],
    right: tuple[int, ...],
) -> tuple[int, ...]:
    width = max(len(left), len(right))
    return tuple(
        (left[index] if index < len(left) else 0)
        ^ (right[index] if index < len(right) else 0)
        for index in range(width)
    )


def _reference_polynomial_multiply(
    left: tuple[int, ...],
    right: tuple[int, ...],
    modulus: int,
    degree: int,
) -> tuple[int, ...]:
    result = [0] * (len(left) + len(right) - 1)
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            result[left_index + right_index] ^= _reference_field_multiply(
                left_value,
                right_value,
                modulus,
                degree,
            )
    return tuple(result)


def _small_register_transform(
    operation: str,
    left: int,
    right: int,
    target: int,
    modulus: int,
    degree: int,
) -> tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]:
    left_register = (left,)
    right_register = (right,)
    if operation == "add":
        value = _reference_polynomial_add(left_register, right_register)[0]
    elif operation == "multiply":
        value = _reference_polynomial_multiply(
            left_register,
            right_register,
            modulus,
            degree,
        )[0]
    else:
        raise AssertionError(f"unknown operation: {operation}")
    return left_register, right_register, (target ^ value,)


class ReversiblePolynomialTests(unittest.TestCase):
    def test_small_field_polynomials_are_irreducible(self):
        for degree, modulus in _SMALL_FIELD_POLYNOMIALS.items():
            with self.subTest(degree=degree, modulus=modulus):
                self.assertTrue(_is_irreducible(modulus, degree))

    def test_small_domains_exhaustively_check_complete_one_coefficient_maps(self):
        for degree, modulus in _SMALL_FIELD_POLYNOMIALS.items():
            size = 1 << degree
            for operation in ("add", "multiply"):
                with self.subTest(degree=degree, operation=operation):
                    seen = set()
                    state_count = size**3
                    for left, right, target in product(
                        range(size),
                        repeat=3,
                    ):
                        output = _small_register_transform(
                            operation,
                            left,
                            right,
                            target,
                            modulus,
                            degree,
                        )
                        self.assertEqual(
                            output[:2],
                            ((left,), (right,)),
                        )
                        self.assertEqual(
                            _small_register_transform(
                                operation,
                                output[0][0],
                                output[1][0],
                                output[2][0],
                                modulus,
                                degree,
                            ),
                            ((left,), (right,), (target,)),
                        )
                        self.assertNotIn(output, seen)
                        seen.add(output)
                    self.assertEqual(len(seen), state_count)

    def test_small_field_oracles_cover_two_coefficient_polynomials(self):
        for degree, modulus in _SMALL_FIELD_POLYNOMIALS.items():
            size = 1 << degree
            target = (size - 1, 0)
            with self.subTest(degree=degree):
                for left_low, left_high, right_constant in product(
                    range(size),
                    repeat=3,
                ):
                    left = (left_low, left_high)
                    right = (right_constant,)
                    added = _reference_polynomial_add(left, right)
                    multiplied = _reference_polynomial_multiply(
                        left,
                        right,
                        modulus,
                        degree,
                    )
                    self.assertEqual(
                        added,
                        (left_low ^ right_constant, left_high),
                    )
                    self.assertEqual(
                        multiplied,
                        (
                            _reference_field_multiply(
                                left_low,
                                right_constant,
                                modulus,
                                degree,
                            ),
                            _reference_field_multiply(
                                left_high,
                                right_constant,
                                modulus,
                                degree,
                            ),
                        ),
                    )
                    self.assertEqual(
                        tuple(target[index] ^ value for index, value in enumerate(added)),
                        (
                            target[0] ^ left_low ^ right_constant,
                            target[1] ^ left_high,
                        ),
                    )
                    self.assertEqual(
                        tuple(
                            target[index] ^ value
                            for index, value in enumerate(multiplied)
                        ),
                        (
                            target[0]
                            ^ _reference_field_multiply(
                                left_low,
                                right_constant,
                                modulus,
                                degree,
                            ),
                            target[1]
                            ^ _reference_field_multiply(
                                left_high,
                                right_constant,
                                modulus,
                                degree,
                            ),
                        ),
                    )

    def test_production_addition_matches_independent_reference(self):
        cases = (
            ((0x123, 0xABC), (0x456, 0xFFF), (0x789, 0x012)),
            ((0, 0, 0), (0xFFF,), (0xAAA, 0xBBB, 0xCCC)),
            ((0xFFF, 0xFFF), (0xFFF,), (0, 0xFFF)),
            ((0x123,), (0x456, 0x789, 0xABC), (0xFFF, 0xFFF, 0xFFF)),
        )
        for left, right, target in cases:
            with self.subTest(left=left, right=right):
                original = (left, right, target)
                result = xor_accumulate_polynomial_add(*original)
                expected_sum = _reference_polynomial_add(left, right)
                expected_target = tuple(
                    target[index] ^ expected_sum[index]
                    for index in range(len(target))
                )
                self.assertEqual(result, (left, right, expected_target))
                self.assertEqual(result[:2], original[:2])
                self.assertEqual(len(result[2]), max(len(left), len(right)))
                self.assertEqual(
                    xor_accumulate_polynomial_add(*result),
                    original,
                )

        self.assertEqual(
            _reference_polynomial_add((0x123, 0xABC), (0x456, 0xFFF)),
            (0x575, 0x543),
        )

    def test_production_multiplication_matches_independent_reference(self):
        cases = (
            ((0x123,), (0x456,), (0x135,)),
            ((0x123, 0x456), (0x789, 0xABC), (0x111, 0x222, 0x333)),
            ((0x123, 0x456, 0x789), (0xABC, 0x053), (0, 1, 0xFFF, 0x800)),
            ((0, 0), (0xFFF, 0x123), (0xABC, 0xDEF, 0x987)),
            ((1, 0, 0), (0x456, 0x789), (0x111, 0x222, 0x333, 0x444)),
            ((0, 0xFFF), (0x123, 0), (0xAAA, 0xBBB, 0xCCC)),
            ((0xFFF, 0xFFF), (0xFFF,), (0, 0xFFF)),
        )
        for left, right, target in cases:
            with self.subTest(left=left, right=right):
                original = (left, right, target)
                result = xor_accumulate_polynomial_multiply(*original)
                expected_product = _reference_polynomial_multiply(
                    left,
                    right,
                    _FIELD_MODULUS,
                    12,
                )
                expected_target = tuple(
                    target[index] ^ expected_product[index]
                    for index in range(len(target))
                )
                self.assertEqual(result, (left, right, expected_target))
                self.assertEqual(result[:2], original[:2])
                self.assertEqual(
                    len(result[2]),
                    len(left) + len(right) - 1,
                )
                self.assertEqual(
                    xor_accumulate_polynomial_multiply(*result),
                    original,
                )

        self.assertEqual(
            _reference_polynomial_multiply(
                (0x123, 0x456),
                (0x789, 0xABC),
                _FIELD_MODULUS,
                12,
            ),
            (0xAC1, 0xC31, 0x584),
        )
        self.assertEqual(
            _reference_polynomial_multiply(
                (0x123, 0x456, 0x789),
                (0xABC, 0x053),
                _FIELD_MODULUS,
                12,
            ),
            (0x113, 0xD0E, 0xBBD, 0x5B0),
        )

    def test_invalid_register_widths_and_coefficients_are_rejected(self):
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_add((), (1,), (0,))
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_multiply((1,), (), (0,))
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_add((1, 2), (3,), (0,))
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_add((1,), (2, 3), (0,))
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_add((1,), (2,), (0, 0))
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_add((1,), (2,), ())
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_multiply((1, 2), (3,), (0,))
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_multiply((1,), (2, 3), (0, 0, 0))

        for invalid in (-1, FIELD_SIZE, True, 1.0, "1"):
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    _call_unchecked(
                        xor_accumulate_polynomial_add,
                        (invalid,),
                        (0,),
                        (0,),
                    )
                with self.assertRaises((TypeError, ValueError)):
                    _call_unchecked(
                        xor_accumulate_polynomial_add,
                        (0,),
                        (0,),
                        (invalid,),
                    )
                with self.assertRaises((TypeError, ValueError)):
                    _call_unchecked(
                        xor_accumulate_polynomial_multiply,
                        (0,),
                        (invalid,),
                        (0,),
                    )

        with self.assertRaises(TypeError):
            _call_unchecked(xor_accumulate_polynomial_add, [1], (0,), (0,))
        with self.assertRaises(TypeError):
            _call_unchecked(xor_accumulate_polynomial_multiply, (1,), (0,), [0])


if __name__ == "__main__":
    unittest.main()
