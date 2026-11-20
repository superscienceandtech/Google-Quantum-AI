"""Research unit tests for the primary-paper DQI syndrome equation."""

import unittest

from dqi_decoder.field import add, power
from dqi_decoder.syndrome import (
    DQI_ERROR_SYMBOL_COUNT,
    DQI_SYNDROME_COUNT,
    compute_dqi_syndrome,
)


class SyndromeTests(unittest.TestCase):
    def test_zero_error_vector_has_zero_syndromes(self):
        self.assertEqual(
            compute_dqi_syndrome([0] * DQI_ERROR_SYMBOL_COUNT),
            (0,) * DQI_SYNDROME_COUNT,
        )

    def test_impulse_at_coordinate_zero_is_constant_across_syndromes(self):
        error_symbols = [0] * DQI_ERROR_SYMBOL_COUNT
        error_symbols[0] = 0xA53

        self.assertEqual(
            compute_dqi_syndrome(error_symbols),
            (0xA53,) * DQI_SYNDROME_COUNT,
        )

    def test_impulse_at_coordinate_one_uses_alpha_to_the_i_plus_one(self):
        error_symbols = [0] * DQI_ERROR_SYMBOL_COUNT
        error_symbols[1] = 1
        expected = tuple(
            power(0b10, i + 1) for i in range(DQI_SYNDROME_COUNT)
        )

        self.assertEqual(compute_dqi_syndrome(error_symbols), expected)

    def test_syndrome_evaluation_is_deterministic_and_linear(self):
        left = [0] * DQI_ERROR_SYMBOL_COUNT
        right = [0] * DQI_ERROR_SYMBOL_COUNT
        left[0], left[3] = 0x17, 0xB2
        right[1], right[3] = 0xA1, 0x23

        combined = [add(a, b) for a, b in zip(left, right)]
        left_syndromes = compute_dqi_syndrome(left)
        right_syndromes = compute_dqi_syndrome(right)
        expected = tuple(
            add(a, b) for a, b in zip(left_syndromes, right_syndromes)
        )

        self.assertEqual(compute_dqi_syndrome(combined), expected)
        self.assertEqual(compute_dqi_syndrome(combined), expected)

    def test_syndrome_input_length_and_elements_are_validated(self):
        with self.assertRaisesRegex(ValueError, "expected 4095"):
            compute_dqi_syndrome([])

        invalid = [0] * DQI_ERROR_SYMBOL_COUNT
        invalid[14] = 4096
        with self.assertRaisesRegex(ValueError, "field element"):
            compute_dqi_syndrome(invalid)


if __name__ == "__main__":
    unittest.main()
