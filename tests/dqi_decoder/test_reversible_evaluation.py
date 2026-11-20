"""Research tests for fixed-width reversible polynomial evaluation models."""

from itertools import product
from typing import Callable
import unittest

from dqi_decoder.field import FIELD_SIZE
from dqi_decoder.reversible_evaluation import (
    _evaluate_and_uncompute,
    xor_accumulate_polynomial_evaluation,
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


def _reference_multiply(
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


def _reference_polynomial_evaluate(
    coefficients: tuple[int, ...],
    point: int,
    modulus: int,
    degree: int,
) -> int:
    value = 0
    point_power = 1
    for coefficient in coefficients:
        value ^= _reference_multiply(
            coefficient,
            point_power,
            modulus,
            degree,
        )
        point_power = _reference_multiply(
            point_power,
            point,
            modulus,
            degree,
        )
    return value


def _small_horner_with_clean_workspace(
    coefficients: tuple[int, ...],
    point: int,
    target: int,
    modulus: int,
    degree: int,
) -> tuple[int, tuple[int, ...]]:
    scratch = [0]
    descending = tuple(reversed(coefficients))
    accumulator_indices: list[int] = []
    steps: list[tuple[int, int, int, int]] = []

    initial_index = len(scratch)
    scratch.append(descending[0])
    accumulator_indices.append(initial_index)

    for coefficient in descending[1:]:
        previous_index = accumulator_indices[-1]
        product_index = len(scratch)
        scratch.append(
            _reference_multiply(
                scratch[previous_index],
                point,
                modulus,
                degree,
            )
        )
        accumulator_index = len(scratch)
        scratch.append(scratch[product_index] ^ coefficient)
        accumulator_indices.append(accumulator_index)
        steps.append(
            (previous_index, product_index, accumulator_index, coefficient)
        )

    updated_target = target ^ scratch[accumulator_indices[-1]]
    for previous_index, product_index, accumulator_index, coefficient in reversed(
        steps
    ):
        scratch[accumulator_index] ^= (
            scratch[product_index] ^ coefficient
        )
        scratch[product_index] ^= _reference_multiply(
            scratch[previous_index],
            point,
            modulus,
            degree,
        )
    scratch[initial_index] ^= descending[0]
    return updated_target, tuple(scratch)


class ReversiblePolynomialEvaluationTests(unittest.TestCase):
    def test_small_field_moduli_are_irreducible(self):
        for degree, modulus in _SMALL_FIELD_POLYNOMIALS.items():
            with self.subTest(degree=degree, modulus=modulus):
                self.assertTrue(_is_irreducible(modulus, degree))

    def test_small_domains_exhaustively_check_bounded_evaluation_maps(self):
        state_counts = {}
        total_states = 0
        for degree, modulus in _SMALL_FIELD_POLYNOMIALS.items():
            size = 1 << degree
            seen = set()
            state_count = size**4
            for coefficient_0, coefficient_1, point, target in product(
                range(size),
                repeat=4,
            ):
                coefficients = (coefficient_0, coefficient_1)
                expected_value = _reference_polynomial_evaluate(
                    coefficients,
                    point,
                    modulus,
                    degree,
                )
                expected_target = target ^ expected_value
                updated_target, scratch = _small_horner_with_clean_workspace(
                    coefficients,
                    point,
                    target,
                    modulus,
                    degree,
                )
                output = (coefficients, point, updated_target)
                self.assertEqual(expected_target, updated_target)
                self.assertEqual(output[:2], (coefficients, point))
                self.assertEqual(
                    _small_horner_with_clean_workspace(
                        coefficients,
                        point,
                        updated_target,
                        modulus,
                        degree,
                    )[0],
                    target,
                )
                self.assertEqual(scratch, (0, 0, 0, 0))
                self.assertNotIn(output, seen)
                seen.add(output)
            self.assertEqual(len(seen), state_count)
            state_counts[degree] = state_count
            total_states += state_count

        self.assertEqual(state_counts, {2: 256, 3: 4096, 4: 65536})
        self.assertEqual(total_states, 69888)

    def test_production_cases_match_independent_power_sum_oracle(self):
        cases = (
            ("zero polynomial", (0, 0, 0), 0x123, (0xABC,)),
            ("constant", (0x789,), 0x456, (0x111,)),
            ("degree one at zero", (0x135, 0x246), 0, (0xFFF,)),
            ("degree one at one", (0x135, 0x246), 1, (0xABC,)),
            ("higher degree", (0x123, 0x456, 0x789, 0xABC), 0x053, (0,)),
            ("sparse", (0, 0, 0xFFF, 0, 0x001), 0x123, (0x800,)),
            ("dense", (0xFFF, 0xABC, 0x789, 0x456, 0x123), 0xFFF, (0x321,)),
            ("trailing zero slots", (0x321, 0x654, 0), 0x002, (0x987,)),
            ("maximum coefficients", (0xFFF, 0xFFF, 0xFFF), 0xFFF, (0xFFF,)),
            ("selected nonzero point", (0x53, 0x123, 0xABC), 0x789, (0x456,)),
        )

        for label, polynomial, point, target in cases:
            with self.subTest(case=label):
                original = (polynomial, point, target)
                result = xor_accumulate_polynomial_evaluation(*original)
                expected_value = _reference_polynomial_evaluate(
                    polynomial,
                    point,
                    _FIELD_MODULUS,
                    12,
                )
                self.assertEqual(
                    result,
                    (polynomial, point, (target[0] ^ expected_value,)),
                )
                self.assertEqual(result[:2], original[:2])
                self.assertEqual(
                    xor_accumulate_polynomial_evaluation(*result),
                    original,
                )

    def test_production_target_accumulation_preserves_inputs_and_cleans_scratch(self):
        polynomial = (0x123, 0x456, 0x789, 0xABC)
        point = 0x053
        first_target = (0x111,)
        second_target = (0x222,)
        expected_value = _reference_polynomial_evaluate(
            polynomial,
            point,
            _FIELD_MODULUS,
            12,
        )

        result, scratch = _evaluate_and_uncompute(
            polynomial,
            point,
            first_target,
        )
        self.assertEqual(result, (first_target[0] ^ expected_value,))
        self.assertEqual(scratch, (0,) * 8)
        self.assertEqual(polynomial, (0x123, 0x456, 0x789, 0xABC))
        self.assertEqual(point, 0x053)
        self.assertEqual(
            xor_accumulate_polynomial_evaluation(
                polynomial,
                point,
                second_target,
            ),
            (polynomial, point, (second_target[0] ^ expected_value,)),
        )

    def test_repeated_application_restores_target_and_is_bijective(self):
        states = (
            ((0,), 0, (0,)),
            ((0xFFF, 0x123), 0x456, (0x789,)),
            ((0x001, 0xABC, 0xFFF), 1, (0x555,)),
            ((0x321, 0, 0x654), 0xFFF, (0xAAA,)),
        )
        outputs = set()
        for state in states:
            with self.subTest(state=state):
                output = xor_accumulate_polynomial_evaluation(*state)
                self.assertEqual(output[:2], state[:2])
                self.assertEqual(
                    xor_accumulate_polynomial_evaluation(*output),
                    state,
                )
                self.assertNotIn(output, outputs)
                outputs.add(output)

    def test_invalid_register_widths_and_field_values_are_rejected(self):
        for invalid_polynomial in ((), []):
            with self.subTest(polynomial=invalid_polynomial):
                with self.assertRaises((TypeError, ValueError)):
                    _call_unchecked(
                        xor_accumulate_polynomial_evaluation,
                        invalid_polynomial,
                        0,
                        (0,),
                    )

        for invalid_target in ((), (0, 0), []):
            with self.subTest(target=invalid_target):
                with self.assertRaises((TypeError, ValueError)):
                    _call_unchecked(
                        xor_accumulate_polynomial_evaluation,
                        (1,),
                        0,
                        invalid_target,
                    )

        for invalid in (-1, FIELD_SIZE, True, 1.0, "1"):
            with self.subTest(invalid=invalid):
                with self.assertRaises((TypeError, ValueError)):
                    _call_unchecked(
                        xor_accumulate_polynomial_evaluation,
                        (invalid,),
                        0,
                        (0,),
                    )
                with self.assertRaises((TypeError, ValueError)):
                    _call_unchecked(
                        xor_accumulate_polynomial_evaluation,
                        (0,),
                        invalid,
                        (0,),
                    )
                with self.assertRaises((TypeError, ValueError)):
                    _call_unchecked(
                        xor_accumulate_polynomial_evaluation,
                        (0,),
                        0,
                        (invalid,),
                    )

        with self.assertRaises(TypeError):
            _call_unchecked(
                xor_accumulate_polynomial_evaluation,
                [1],
                0,
                (0,),
            )

    def test_no_field_value_or_target_width_is_silently_truncated(self):
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_evaluation((FIELD_SIZE,), 0, (0,))
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_evaluation((1,), FIELD_SIZE, (0,))
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_evaluation((1,), 0, (0, 0))


if __name__ == "__main__":
    unittest.main()
