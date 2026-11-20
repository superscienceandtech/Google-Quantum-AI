"""Research-only decoder tests with an independent syndrome oracle."""

from collections.abc import Sequence
import inspect
from pathlib import Path
from typing import cast
import unittest
from unittest.mock import patch

import dqi_decoder
from dqi_decoder import (
    DQI_ERROR_SYMBOL_COUNT,
    DQI_MAX_CORRECTABLE_ERRORS,
    DQI_SYNDROME_COUNT,
    DecodedError,
    InvalidSyndrome,
    NoDecodingSolution,
    decode_error,
)
from dqi_decoder.decoder import (
    _find_error_positions,
    _key_equation,
    _recover_error_symbols,
)

_FIELD_MODULUS = 0x1053


def _reference_multiply(left: int, right: int) -> int:
    product = 0
    while right:
        if right & 1:
            product ^= left
        left <<= 1
        right >>= 1
    while product.bit_length() > 12:
        product ^= _FIELD_MODULUS << (product.bit_length() - 13)
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


def _reference_inverse(value: int) -> int:
    if value == 0:
        raise ZeroDivisionError
    return _reference_power(value, 4094)


def _independent_syndrome(error_symbols: tuple[int, ...]) -> tuple[int, ...]:
    result = []
    for syndrome_index in range(DQI_SYNDROME_COUNT):
        value = 0
        for position, symbol in enumerate(error_symbols):
            if symbol == 0:
                continue
            value ^= _reference_multiply(
                symbol,
                _reference_power(2, (syndrome_index + 1) * position),
            )
        result.append(value)
    return tuple(result)


def _reference_evaluate(
    polynomial: tuple[int, ...],
    point: int,
) -> int:
    value = 0
    for coefficient in reversed(polynomial):
        value = _reference_multiply(value, point) ^ coefficient
    return value


def _reference_derivative(polynomial: tuple[int, ...]) -> tuple[int, ...]:
    derivative = [0] * max(0, len(polynomial) - 1)
    for exponent in range(1, len(polynomial), 2):
        derivative[exponent - 1] = polynomial[exponent]
    while derivative and derivative[-1] == 0:
        derivative.pop()
    return tuple(derivative)


def _reference_polynomial_multiply(
    left: tuple[int, ...],
    right: tuple[int, ...],
) -> tuple[int, ...]:
    if not left or not right:
        return ()
    product = [0] * (len(left) + len(right) - 1)
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            product[left_index + right_index] ^= _reference_multiply(
                left_value,
                right_value,
            )
    while product and product[-1] == 0:
        product.pop()
    return tuple(product)


def _error_vector(
    positions: tuple[int, ...],
    magnitudes: tuple[int, ...] | None = None,
) -> tuple[int, ...]:
    if magnitudes is not None and len(magnitudes) != len(positions):
        raise ValueError("one magnitude is required per position")
    errors = [0] * DQI_ERROR_SYMBOL_COUNT
    for index, position in enumerate(positions):
        errors[position] = (
            magnitudes[index]
            if magnitudes is not None
            else ((0x127 * (index + 1)) ^ (0x35 + index)) & 0xFFF
        )
        if errors[position] == 0:
            errors[position] = 1
    return tuple(errors)


class DecoderTests(unittest.TestCase):
    def assert_decodes(self, positions: tuple[int, ...]) -> None:
        expected_errors = _error_vector(positions)
        syndrome = _independent_syndrome(expected_errors)

        decoded = decode_error(syndrome)

        self.assertIsInstance(decoded, DecodedError)
        self.assertEqual(decoded.error_positions, positions)
        self.assertEqual(decoded.error_symbols, expected_errors)
        self.assertEqual(len(decoded.error_symbols), DQI_ERROR_SYMBOL_COUNT)
        self.assertEqual(decoded.weight, len(positions))
        expected_locator = (1,)
        for position in positions:
            expected_locator = _reference_polynomial_multiply(
                expected_locator,
                (1, _reference_power(2, position)),
            )
        self.assertEqual(decoded.locator_polynomial, expected_locator)

        key_equation_product = list(
            _reference_polynomial_multiply(
                decoded.locator_polynomial,
                syndrome,
            )[:DQI_SYNDROME_COUNT]
        )
        while key_equation_product and key_equation_product[-1] == 0:
            key_equation_product.pop()
        self.assertEqual(decoded.evaluator_polynomial, tuple(key_equation_product))
        self.assertEqual(
            _independent_syndrome(decoded.error_symbols),
            syndrome,
        )
        derivative = _reference_derivative(decoded.locator_polynomial)
        for position in positions:
            root = _reference_inverse(_reference_power(2, position))
            self.assertEqual(
                _reference_evaluate(decoded.locator_polynomial, root),
                0,
            )
            magnitude = _reference_multiply(
                _reference_evaluate(decoded.evaluator_polynomial, root),
                _reference_inverse(_reference_evaluate(derivative, root)),
            )
            self.assertEqual(decoded.error_symbols[position], magnitude)

    def test_zero_syndrome_decodes_to_zero_error(self):
        decoded = decode_error((0,) * DQI_SYNDROME_COUNT)

        self.assertEqual(decoded.error_positions, ())
        self.assertEqual(decoded.weight, 0)
        self.assertEqual(decoded.error_symbols, (0,) * DQI_ERROR_SYMBOL_COUNT)
        self.assertEqual(decoded.locator_polynomial, (1,))
        self.assertEqual(decoded.evaluator_polynomial, ())
        self.assertEqual(_independent_syndrome(decoded.error_symbols), (0,) * DQI_SYNDROME_COUNT)

    def test_package_initializer_and_public_signature(self):
        self.assertIsNotNone(dqi_decoder.__file__)
        package_file = Path(dqi_decoder.__file__)
        self.assertEqual(package_file.name, "__init__.py")
        self.assertFalse(package_file.with_name("init.py").exists())
        signature = inspect.signature(decode_error)
        self.assertEqual(tuple(signature.parameters), ("syndromes",))
        self.assertEqual(
            signature.parameters["syndromes"].annotation,
            Sequence[int],
        )
        self.assertIs(signature.return_annotation, DecodedError)

    def test_single_errors_recover_distinct_magnitudes_at_boundary_positions(self):
        cases = ((0, 0x001), (1, 0xABC), (4094, 0xFFF))
        for position, magnitude in cases:
            with self.subTest(position=position, magnitude=magnitude):
                expected_errors = _error_vector((position,), (magnitude,))
                decoded = decode_error(_independent_syndrome(expected_errors))
                self.assertEqual(decoded.error_positions, (position,))
                self.assertEqual(decoded.error_symbols, expected_errors)

    def test_single_errors_at_first_interior_and_last_positions(self):
        for position in (0, 137, DQI_ERROR_SYMBOL_COUNT - 1):
            with self.subTest(position=position):
                self.assert_decodes((position,))

    def test_multiple_errors_within_radius(self):
        positions = (0, 3, 70, 4094)
        self.assert_decodes(positions)

    def test_multiple_errors_include_repeated_magnitudes_and_both_boundaries(self):
        positions = (0, 11, 2047, 4094)
        self.assert_decodes(positions)
        errors = _error_vector(positions, (0x53, 0x53, 0xA17, 0x53))
        decoded = decode_error(_independent_syndrome(errors))
        self.assertEqual(decoded.error_positions, positions)
        self.assertEqual(decoded.error_symbols, errors)

    def test_exact_recovery_at_weights_34_and_35(self):
        for weight in (34, DQI_MAX_CORRECTABLE_ERRORS):
            positions = tuple(sorted((0, 4094, *range(13, 13 + weight - 2))))
            with self.subTest(weight=weight):
                self.assertEqual(len(positions), weight)
                self.assert_decodes(positions)

    def test_input_vector_shape_and_field_values_are_validated(self):
        with self.assertRaises(InvalidSyndrome):
            decode_error((0,) * (DQI_SYNDROME_COUNT - 1))

        malformed = [0] * DQI_SYNDROME_COUNT
        malformed[12] = 4096
        with self.assertRaises(InvalidSyndrome):
            decode_error(malformed)
        for invalid in (None, "0" * DQI_SYNDROME_COUNT, (False,) + (0,) * (DQI_SYNDROME_COUNT - 1)):
            with self.subTest(invalid_type=type(invalid).__name__):
                with self.assertRaises(InvalidSyndrome):
                    decode_error(cast(Sequence[int], invalid))

    def test_zero_constant_and_repeated_root_locators_are_handled(self):
        with self.assertRaises(NoDecodingSolution):
            _find_error_positions(())
        self.assertEqual(_find_error_positions((1,)), ())
        with self.assertRaises(NoDecodingSolution):
            _find_error_positions((1, 0, 1))

    def test_key_equation_rejects_a_non_decreasing_remainder(self):
        with patch(
            "dqi_decoder.decoder.divide_polynomials",
            return_value=((1,), (1,) * DQI_SYNDROME_COUNT),
        ):
            with self.assertRaisesRegex(NoDecodingSolution, "failed to reduce"):
                _key_equation((1,) * DQI_SYNDROME_COUNT)

    def test_forney_recovery_rejects_zero_denominator_and_zero_magnitude(self):
        with self.assertRaisesRegex(NoDecodingSolution, "derivative is zero"):
            _recover_error_symbols((1, 0, 1), (1,), (0,))
        with self.assertRaisesRegex(NoDecodingSolution, "zero error magnitude"):
            _recover_error_symbols((1, 1), (), (0,))

    def test_beyond_radius_never_returns_an_unverified_overweight_error(self):
        patterns = (
            tuple(index * 109 for index in range(DQI_MAX_CORRECTABLE_ERRORS + 1)),
            tuple(sorted((0, 4094, *range(20, 20 + DQI_MAX_CORRECTABLE_ERRORS - 1)))),
        )
        for positions in patterns:
            expected_errors = _error_vector(positions)
            syndrome = _independent_syndrome(expected_errors)
            try:
                decoded = decode_error(syndrome)
            except NoDecodingSolution:
                continue
            self.assertLessEqual(decoded.weight, DQI_MAX_CORRECTABLE_ERRORS)
            self.assertEqual(
                tuple(index for index, symbol in enumerate(decoded.error_symbols) if symbol),
                decoded.error_positions,
            )
            self.assertEqual(
                _independent_syndrome(decoded.error_symbols),
                syndrome,
            )

    def test_unmatched_syndrome_is_reported_as_no_solution(self):
        syndrome = (1,) + (0,) * (DQI_SYNDROME_COUNT - 1)
        with self.assertRaises(NoDecodingSolution):
            decode_error(syndrome)


if __name__ == "__main__":
    unittest.main()
