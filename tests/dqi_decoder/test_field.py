"""Research unit tests for the paper-specified GF(2^12) representation."""

import random
import unittest

from dqi_decoder.field import (
    FIELD_DEGREE,
    FIELD_MODULUS_POLYNOMIAL,
    FIELD_SIZE,
    add,
    inverse,
    multiply,
    power,
    validate_element,
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


class FiniteFieldTests(unittest.TestCase):
    def test_field_parameters_match_paper_polynomial_basis(self):
        self.assertEqual(FIELD_DEGREE, 12)
        self.assertEqual(FIELD_SIZE, 4096)
        self.assertEqual(FIELD_MODULUS_POLYNOMIAL, 0x1053)

    def test_additive_identity_and_characteristic_two(self):
        for value in (0, 1, 2, 0x53, 0xFFF):
            with self.subTest(value=value):
                self.assertEqual(add(value, 0), value)
                self.assertEqual(add(value, value), 0)

    def test_add_is_xor(self):
        cases = (
            (0x123, 0x456, 0x575),
            (0, 0xABC, 0xABC),
            (1, 0xABC, 0xABD),
        )
        for left, right, expected in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(add(left, right), expected)

    def test_multiplication_identities_and_commutativity(self):
        values = (0, 1, 2, 0x53, 0xABC, 0xFFF)
        for value in values:
            with self.subTest(value=value):
                self.assertEqual(multiply(value, 0), 0)
                self.assertEqual(multiply(value, 1), value)
            for other in values:
                with self.subTest(value=value, other=other):
                    self.assertEqual(
                        multiply(value, other),
                        multiply(other, value),
                    )

    def test_multiplication_reduces_by_the_paper_polynomial(self):
        # alpha^12 = alpha^6 + alpha^4 + alpha + 1 in characteristic two.
        self.assertEqual(multiply(0b10, 1 << 11), 0b000001010011)

    def test_multiplication_matches_independent_carryless_reference(self):
        rng = random.Random(0xD012)
        cases = [
            (left, right)
            for left in range(0, FIELD_SIZE, 127)
            for right in range(0, FIELD_SIZE, 193)
        ]
        cases.extend(
            (rng.randrange(FIELD_SIZE), rng.randrange(FIELD_SIZE))
            for _ in range(512)
        )
        cases.extend(((0xFFF, 0xFFF), (0x800, 0x800), (0xF52, 0xFFF)))

        for left, right in cases:
            with self.subTest(left=left, right=right):
                self.assertEqual(
                    multiply(left, right),
                    _reference_multiply(left, right),
                )

    def test_power_handles_zero_and_nonnegative_exponents(self):
        self.assertEqual(power(0, 0), 1)
        self.assertEqual(power(0, 7), 0)
        self.assertEqual(power(0b10, 12), 0b000001010011)

    def test_alpha_enumerates_all_nonzero_field_elements(self):
        self.assertEqual(power(0b10, 4095), 1)
        for prime_factor in (3, 5, 7, 13):
            with self.subTest(prime_factor=prime_factor):
                self.assertNotEqual(power(0b10, 4095 // prime_factor), 1)

    def test_every_nonzero_element_has_a_multiplicative_inverse(self):
        for value in range(1, FIELD_SIZE):
            with self.subTest(value=value):
                self.assertEqual(
                    _reference_multiply(value, inverse(value)),
                    1,
                )
                self.assertEqual(
                    inverse(value),
                    _reference_power(value, FIELD_SIZE - 2),
                )

    def test_element_range_is_validated(self):
        for value in (-1, FIELD_SIZE):
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_element(value)

    def test_field_elements_must_be_integers_not_coercible_values(self):
        for value in (True, 1.0, "1"):
            with self.subTest(value=value), self.assertRaises(TypeError):
                validate_element(value)

    def test_inverse_rejects_zero_and_power_rejects_negative_exponents(self):
        with self.assertRaisesRegex(ValueError, "zero"):
            inverse(0)
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            power(2, -1)


if __name__ == "__main__":
    unittest.main()
