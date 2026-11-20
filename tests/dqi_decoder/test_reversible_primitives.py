"""Research tests for XOR-accumulating reversible field relations."""

from itertools import product
from typing import Callable
import unittest

from dqi_decoder.field import FIELD_SIZE, inverse
from dqi_decoder.reversible_primitives import (
    target_width,
    xor_accumulate_add,
    xor_accumulate_inverse,
    xor_accumulate_multiply,
    xor_accumulate_square,
)

_FIELD_MODULUS = 0x1053
_SMALL_FIELD_POLYNOMIALS = {2: 0b111, 3: 0b1011, 4: 0b10011}


def _invoke_unchecked(function: Callable[..., object], *arguments: object) -> object:
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
    if polynomial.bit_length() != degree + 1 or polynomial & (1 << degree) == 0:
        return False
    for divisor_degree in range(1, degree // 2 + 1):
        for lower_bits in range(1 << divisor_degree):
            divisor = (1 << divisor_degree) | lower_bits
            if _polynomial_remainder(polynomial, divisor) == 0:
                return False
    return True


def _reference_multiply(left: int, right: int, modulus: int, degree: int) -> int:
    product = 0
    while right:
        if right & 1:
            product ^= left
        left <<= 1
        right >>= 1
    while product.bit_length() > degree:
        product ^= modulus << (product.bit_length() - degree - 1)
    return product


def _reference_inverse(value: int, modulus: int, degree: int) -> int:
    if value == 0:
        return 0
    field_size = 1 << degree
    for candidate in range(1, field_size):
        if _reference_multiply(value, candidate, modulus, degree) == 1:
            return candidate
    raise AssertionError("nonzero field element has no inverse")


def _small_domain_map(
    operation: str,
    values: tuple[int, ...],
    target: int,
    modulus: int,
    degree: int,
) -> tuple[int, ...]:
    size = 1 << degree
    if operation == "add":
        left, right = values
        result = left ^ right
        return left, right, target ^ result
    if operation == "multiply":
        left, right = values
        result = _reference_multiply(left, right, modulus, degree)
        return left, right, target ^ result
    (value,) = values
    if operation == "square":
        result = _reference_multiply(value, value, modulus, degree)
    elif operation == "inverse":
        result = _reference_inverse(value, modulus, degree)
    else:
        raise AssertionError(f"unknown operation: {operation}")
    if not 0 <= target < size:
        raise AssertionError("target outside small-field width")
    return value, target ^ result


class ReversiblePrimitiveTests(unittest.TestCase):
    def test_target_width_and_production_known_vectors(self):
        self.assertEqual(target_width(), 12)

        add_cases = (
            (0x123, 0x456, 0x789, 0x123, 0x456, 0x2FC),
            (0, 0xABC, 0xFFF, 0, 0xABC, 0x543),
        )
        for left, right, target, out_left, out_right, out_target in add_cases:
            with self.subTest(operation="add", left=left, right=right):
                self.assertEqual(
                    xor_accumulate_add(left, right, target),
                    (out_left, out_right, out_target),
                )

        multiply_cases = (
            (0x123, 0x456, 0x135, 0x123, 0x456, 0x61B),
            (0xFFF, 0xFFF, 0x800, 0xFFF, 0xFFF, 0x78A),
            (0, 0xABC, 0xFFF, 0, 0xABC, 0xFFF),
        )
        for left, right, target, out_left, out_right, out_target in multiply_cases:
            with self.subTest(operation="multiply", left=left, right=right):
                self.assertEqual(
                    xor_accumulate_multiply(left, right, target),
                    (out_left, out_right, out_target),
                )

        square_cases = ((0, 0xABC, 0, 0xABC), (0x123, 0xFFF, 0x123, 0xECA))
        for value, target, out_value, out_target in square_cases:
            with self.subTest(operation="square", value=value):
                self.assertEqual(
                    xor_accumulate_square(value, target),
                    (out_value, out_target),
                )

        inverse_cases = (
            (0, 0xABC, 0, 0xABC),
            (1, 0xFFF, 1, 0xFFE),
            (0x123, 0x456, 0x123, 0xD1C),
        )
        for value, target, out_value, out_target in inverse_cases:
            with self.subTest(operation="inverse", value=value):
                self.assertEqual(
                    xor_accumulate_inverse(value, target),
                    (out_value, out_target),
                )

    def test_production_results_match_independent_gf12_oracle(self):
        rng_values = (0, 1, 2, 0x53, 0x123, 0xABC, 0xFFF)
        for left in rng_values:
            for right in rng_values:
                product = _reference_multiply(
                    left, right, _FIELD_MODULUS, 12
                )
                target = (left * 17 + right * 29) & (FIELD_SIZE - 1)
                self.assertEqual(
                    xor_accumulate_multiply(left, right, target),
                    (left, right, target ^ product),
                )
                self.assertEqual(
                    xor_accumulate_add(left, right, target),
                    (left, right, target ^ (left ^ right)),
                )
            square = _reference_multiply(left, left, _FIELD_MODULUS, 12)
            target = (left * 31 + 7) & (FIELD_SIZE - 1)
            self.assertEqual(
                xor_accumulate_square(left, target),
                (left, target ^ square),
            )
            expected_inverse = _reference_inverse(left, _FIELD_MODULUS, 12)
            self.assertEqual(
                xor_accumulate_inverse(left, target),
                (left, target ^ expected_inverse),
            )
            if left:
                self.assertEqual(
                    _reference_multiply(
                        left,
                        inverse(left),
                        _FIELD_MODULUS,
                        12,
                    ),
                    1,
                )

        self.assertEqual(
            _reference_multiply(0x123, 0x456, _FIELD_MODULUS, 12),
            0x72E,
        )
        self.assertEqual(
            _reference_multiply(0x123, 0x123, _FIELD_MODULUS, 12),
            0x135,
        )
        self.assertEqual(
            _reference_inverse(0x123, _FIELD_MODULUS, 12),
            0x94A,
        )

    def test_production_transformations_preserve_inputs_and_are_involutions(self):
        samples = (0, 1, 0x53, 0x123, 0xABC, 0xFFF)
        for left in samples:
            for right in samples:
                target = (left ^ (right << 1)) & (FIELD_SIZE - 1)
                once = xor_accumulate_add(left, right, target)
                self.assertEqual(once[:2], (left, right))
                self.assertEqual(
                    xor_accumulate_add(*once),
                    (left, right, target),
                )
                once = xor_accumulate_multiply(left, right, target)
                self.assertEqual(once[:2], (left, right))
                self.assertEqual(
                    xor_accumulate_multiply(*once),
                    (left, right, target),
                )

            target = left ^ 0xA53
            for transform in (xor_accumulate_square, xor_accumulate_inverse):
                once = transform(left, target)
                self.assertEqual(once[0], left)
                self.assertEqual(transform(*once), (left, target))

    def test_small_fields_use_verified_irreducible_polynomials(self):
        for degree, modulus in _SMALL_FIELD_POLYNOMIALS.items():
            with self.subTest(degree=degree, modulus=modulus):
                self.assertTrue(_is_irreducible(modulus, degree))

    def test_small_domains_exhaustively_prove_xor_accumulation_bijections(self):
        operation_arities = {
            "add": 2,
            "multiply": 2,
            "square": 1,
            "inverse": 1,
        }
        for degree, modulus in _SMALL_FIELD_POLYNOMIALS.items():
            size = 1 << degree
            elements = range(size)
            for operation, arity in operation_arities.items():
                with self.subTest(
                    degree=degree,
                    operation=operation,
                ):
                    seen = set()
                    state_count = size ** (arity + 1)
                    for inputs in product(elements, repeat=arity):
                        for target in elements:
                            output = _small_domain_map(
                                operation,
                                inputs,
                                target,
                                modulus,
                                degree,
                            )
                            self.assertEqual(output[:arity], inputs)
                            self.assertEqual(len(output), arity + 1)
                            self.assertEqual(
                                _small_domain_map(
                                    operation,
                                    output[:arity],
                                    output[-1],
                                    modulus,
                                    degree,
                                ),
                                (*inputs, target),
                            )
                            self.assertNotIn(output, seen)
                            seen.add(output)
                    self.assertEqual(len(seen), state_count)

    def test_small_domain_zero_and_boundary_cases(self):
        for degree, modulus in _SMALL_FIELD_POLYNOMIALS.items():
            size = 1 << degree
            with self.subTest(degree=degree):
                self.assertEqual(
                    _small_domain_map(
                        "add", (0, size - 1), 0, modulus, degree
                    ),
                    (0, size - 1, size - 1),
                )
                self.assertEqual(
                    _small_domain_map(
                        "multiply", (size - 1, size - 1), 0, modulus, degree
                    )[:2],
                    (size - 1, size - 1),
                )
                self.assertEqual(
                    _small_domain_map(
                        "multiply", (0, size - 1), size - 1, modulus, degree
                    ),
                    (0, size - 1, size - 1),
                )
                self.assertEqual(
                    _small_domain_map(
                        "square", (0,), size - 1, modulus, degree
                    ),
                    (0, size - 1),
                )
                self.assertEqual(
                    _small_domain_map(
                        "inverse", (0,), size - 1, modulus, degree
                    ),
                    (0, size - 1),
                )
                self.assertEqual(
                    _small_domain_map(
                        "inverse", (size - 1,), 0, modulus, degree
                    )[0],
                    size - 1,
                )

    def test_invalid_operands_and_targets_are_rejected(self):
        for invalid in (-1, FIELD_SIZE, True, 1.0, "1"):
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    _invoke_unchecked(xor_accumulate_add, invalid, 0, 0)
                with self.assertRaises((TypeError, ValueError)):
                    _invoke_unchecked(xor_accumulate_add, 0, 0, invalid)
                with self.assertRaises((TypeError, ValueError)):
                    _invoke_unchecked(xor_accumulate_multiply, 0, invalid, 0)
                with self.assertRaises((TypeError, ValueError)):
                    _invoke_unchecked(xor_accumulate_square, invalid, 0)
                with self.assertRaises((TypeError, ValueError)):
                    _invoke_unchecked(xor_accumulate_inverse, 0, invalid)

    def test_malformed_call_shapes_are_rejected(self):
        with self.assertRaises(TypeError):
            _invoke_unchecked(xor_accumulate_add, 1, 2)
        with self.assertRaises(TypeError):
            _invoke_unchecked(xor_accumulate_multiply, 1, 2, 3, 4)
        with self.assertRaises(TypeError):
            _invoke_unchecked(xor_accumulate_square, 1)
        with self.assertRaises(TypeError):
            _invoke_unchecked(xor_accumulate_inverse, 1, 2, 3)

    def test_caller_inputs_are_immutable_tuples(self):
        original = (0x123, 0x456, 0x789)
        snapshot = original
        result = xor_accumulate_multiply(*original)
        self.assertEqual(original, snapshot)
        self.assertIsInstance(result, tuple)
        self.assertEqual(result[:2], original[:2])


if __name__ == "__main__":
    unittest.main()
