import unittest

from dqi_decoder.reversible_division import (
    MAX_DIVISION_DIVIDEND_WIDTH,
    MAX_DIVISION_DIVISOR_WIDTH,
    MAX_POLYNOMIAL_REGISTER_WIDTH,
    _compute_accumulate_uncompute,
    xor_accumulate_polynomial_division,
)


_SMALL_MODULI = {2: 0b111, 3: 0b1011, 4: 0b10011}
_GF12_MODULUS = 0x1053


def _reference_multiply(left: int, right: int, degree: int, modulus: int) -> int:
    mask = (1 << degree) - 1
    result = 0
    while right:
        if right & 1:
            result ^= left
        right >>= 1
        left <<= 1
        if left & (1 << degree):
            left ^= modulus
    return result & mask


def _reference_inverse(value: int, degree: int, modulus: int) -> int:
    if value == 0:
        raise ZeroDivisionError("zero has no multiplicative inverse")
    result = 1
    base = value
    exponent = (1 << degree) - 2
    while exponent:
        if exponent & 1:
            result = _reference_multiply(result, base, degree, modulus)
        base = _reference_multiply(base, base, degree, modulus)
        exponent >>= 1
    return result


def _reference_polynomial_degree(polynomial: tuple[int, ...]) -> int:
    for index in range(len(polynomial) - 1, -1, -1):
        if polynomial[index]:
            return index
    return -1


def _reference_division(
    dividend: tuple[int, ...],
    divisor: tuple[int, ...],
    degree: int = 12,
    modulus: int = _GF12_MODULUS,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Independent normalized-list long-division oracle."""
    remainder = list(dividend)
    while remainder and remainder[-1] == 0:
        remainder.pop()
    denominator = list(divisor)
    while denominator and denominator[-1] == 0:
        denominator.pop()
    if not denominator:
        raise ZeroDivisionError

    quotient = [0] * max(0, len(remainder) - len(denominator) + 1)
    reciprocal = _reference_inverse(denominator[-1], degree, modulus)
    while remainder and len(remainder) >= len(denominator):
        shift = len(remainder) - len(denominator)
        factor = _reference_multiply(
            remainder[-1],
            reciprocal,
            degree,
            modulus,
        )
        quotient[shift] ^= factor
        for index, coefficient in enumerate(denominator):
            remainder[shift + index] ^= _reference_multiply(
                factor,
                coefficient,
                degree,
                modulus,
            )
        while remainder and remainder[-1] == 0:
            remainder.pop()

    while quotient and quotient[-1] == 0:
        quotient.pop()
    return tuple(quotient), tuple(remainder)


def _reference_polynomial_multiply(
    left: tuple[int, ...],
    right: tuple[int, ...],
    degree: int = 12,
    modulus: int = _GF12_MODULUS,
) -> tuple[int, ...]:
    result = [0] * max(0, len(left) + len(right) - 1)
    for left_index, left_value in enumerate(left):
        for right_index, right_value in enumerate(right):
            result[left_index + right_index] ^= _reference_multiply(
                left_value,
                right_value,
                degree,
                modulus,
            )
    while result and result[-1] == 0:
        result.pop()
    return tuple(result)


def _pad(polynomial: tuple[int, ...], width: int) -> tuple[int, ...]:
    return polynomial + (0,) * (width - len(polynomial))


def _small_add(left: int, right: int, target: int) -> tuple[int, int, int]:
    return left, right, target ^ left ^ right


def _small_multiply(
    left: int,
    right: int,
    target: int,
    degree: int,
    modulus: int,
) -> tuple[int, int, int]:
    return (
        left,
        right,
        target ^ _reference_multiply(left, right, degree, modulus),
    )


def _small_inverse(
    value: int,
    target: int,
    degree: int,
    modulus: int,
) -> tuple[int, int]:
    return value, target ^ _reference_inverse(value, degree, modulus)


class ReversibleDivisionTests(unittest.TestCase):
    def assert_division_case(
        self,
        dividend: tuple[int, ...],
        divisor: tuple[int, ...],
        quotient_target: tuple[int, ...],
        remainder_target: tuple[int, ...],
    ) -> None:
        expected_quotient, expected_remainder = _reference_division(
            dividend,
            divisor,
        )
        result = xor_accumulate_polynomial_division(
            dividend,
            divisor,
            quotient_target,
            remainder_target,
        )
        self.assertEqual(result[0], dividend)
        self.assertEqual(result[1], divisor)
        self.assertEqual(
            result[2],
            tuple(
                target ^ coefficient
                for target, coefficient in zip(
                    quotient_target,
                    _pad(expected_quotient, len(quotient_target)),
                )
            ),
        )
        self.assertEqual(
            result[3],
            tuple(
                target ^ coefficient
                for target, coefficient in zip(
                    remainder_target,
                    _pad(expected_remainder, len(remainder_target)),
                )
            ),
        )
        self.assertFalse(
            any(
                _reference_division_identity_remainder(
                    dividend,
                    divisor,
                    expected_quotient,
                    expected_remainder,
                )
            ),
        )
        if expected_remainder:
            self.assertLess(
                _reference_polynomial_degree(expected_remainder),
                _reference_polynomial_degree(divisor),
            )
        repeated = xor_accumulate_polynomial_division(
            result[0],
            result[1],
            result[2],
            result[3],
        )
        self.assertEqual(repeated[2], quotient_target)
        self.assertEqual(repeated[3], remainder_target)


def _reference_division_identity_remainder(
    dividend: tuple[int, ...],
    divisor: tuple[int, ...],
    quotient: tuple[int, ...],
    remainder: tuple[int, ...],
    degree: int = 12,
    modulus: int = _GF12_MODULUS,
) -> tuple[int, ...]:
    product = _reference_polynomial_multiply(
        divisor,
        quotient,
        degree,
        modulus,
    )
    width = max(len(dividend), len(product), len(remainder))
    return tuple(
        (dividend[index] if index < len(dividend) else 0)
        ^ (product[index] if index < len(product) else 0)
        ^ (remainder[index] if index < len(remainder) else 0)
        for index in range(width)
    )


class ReversibleDivisionProductionTests(ReversibleDivisionTests):
    def test_zero_constant_and_degree_cases(self) -> None:
        cases = [
            ((0, 0, 0, 0), (0x003, 0, 0), (0x111, 0x222, 0x333, 0x444), (0x555, 0x666)),
            ((0xABC,), (0x003,), (0x111,), (0x555,)),
            ((0x123, 0x456), (0, 0, 0x789), (0x111, 0x222), (0x555, 0x666)),
            ((0x234, 0, 0, 0), (0x011, 0x007), (0x111, 0x222, 0x333, 0x444), (0x555,)),
            ((0xFFF, 0xFFE, 0xFFD), (0xFFF, 0xFFE, 0xFFD), (0x111, 0x222, 0x333), (0x555, 0x666)),
        ]
        for dividend, divisor, quotient_target, remainder_target in cases:
            with self.subTest(dividend=dividend, divisor=divisor):
                self.assert_division_case(
                    dividend,
                    divisor,
                    quotient_target,
                    remainder_target,
                )

    def test_nonmonic_dense_and_sparse_division(self) -> None:
        divisor = (0, 0x002, 0x03A)
        quotient = (0x005, 0x007, 0x002)
        remainder = (0x009, 0x004)
        product = _reference_polynomial_multiply(divisor, quotient)
        dividend = tuple(
            (product[index] if index < len(product) else 0)
            ^ (remainder[index] if index < len(remainder) else 0)
            for index in range(max(len(product), len(remainder)))
        )
        dividend = _pad(dividend, 6)
        self.assert_division_case(
            dividend,
            divisor,
            (0x123, 0x456, 0x789, 0xABC, 0xDEF, 0x111),
            (0x222, 0x333),
        )

    def test_maximum_supported_register_widths(self) -> None:
        width = MAX_POLYNOMIAL_REGISTER_WIDTH
        dividend = (0xFFF, 0x001, 0xABC, 0x000, 0x321, 0x777, 0x003, 0x801)
        divisor = (0x002, 0x000, 0x1AA, 0x000, 0x00F, 0x040, 0x000, 0xFFF)
        self.assertEqual(len(dividend), width)
        self.assertEqual(len(divisor), width)
        self.assert_division_case(
            dividend,
            divisor,
            (0x101,) * width,
            (0x202,) * (width - 1),
        )
        constant_divisor = (0xFFF,)
        self.assert_division_case(
            dividend,
            constant_divisor,
            (0x303,) * width,
            (0x404,),
        )

    def test_capacity_generalized_maximum_widths(self) -> None:
        dividend = (0,) * 70 + (1,)
        divisor = tuple(
            ((index * 0x31) ^ 0xA57) & 0xFFF
            for index in range(MAX_DIVISION_DIVISOR_WIDTH - 1)
        ) + (0x123,)
        self.assertEqual(len(dividend), MAX_DIVISION_DIVIDEND_WIDTH)
        self.assertEqual(len(divisor), MAX_DIVISION_DIVISOR_WIDTH)
        self.assert_division_case(
            dividend,
            divisor,
            (0x321,) * MAX_DIVISION_DIVIDEND_WIDTH,
            (0x456,) * (MAX_DIVISION_DIVISOR_WIDTH - 1),
        )

        constant_divisor = (0x123,)
        quotient_target = (0x789,) * MAX_DIVISION_DIVIDEND_WIDTH
        remainder_target = (0xABC,)
        expected_quotient, expected_remainder = _reference_division(
            dividend,
            constant_divisor,
        )
        quotient, remainder, scratch = _compute_accumulate_uncompute(
            dividend,
            constant_divisor,
            quotient_target,
            remainder_target,
        )
        self.assertEqual(
            quotient,
            tuple(
                target ^ coefficient
                for target, coefficient in zip(
                    quotient_target,
                    _pad(expected_quotient, len(quotient_target)),
                )
            ),
        )
        self.assertEqual(remainder, remainder_target)
        self.assertFalse(any(scratch))
        self.assert_division_case(
            dividend,
            constant_divisor,
            quotient_target,
            remainder_target,
        )

    def test_capacity_overrides_and_overflow_rejection(self) -> None:
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_division(
                (1, 2),
                (1,),
                (0, 0),
                (0,),
                max_dividend_width=1,
            )
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_division(
                (1,),
                (1, 2),
                (0,),
                (0,),
                max_divisor_width=1,
            )
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_division(
                (1,) * (MAX_DIVISION_DIVIDEND_WIDTH + 1),
                (1,),
                (0,) * (MAX_DIVISION_DIVIDEND_WIDTH + 1),
                (0,),
            )
        with self.assertRaises(ValueError):
            xor_accumulate_polynomial_division(
                (1,),
                (1,) * (MAX_DIVISION_DIVISOR_WIDTH + 1),
                (0,),
                (0,) * MAX_DIVISION_DIVISOR_WIDTH,
            )
        for invalid_width in (0, MAX_DIVISION_DIVIDEND_WIDTH + 1, True):
            with self.subTest(max_dividend_width=invalid_width):
                with self.assertRaises((TypeError, ValueError)):
                    xor_accumulate_polynomial_division(
                        (1,),
                        (1,),
                        (0,),
                        (0,),
                        max_dividend_width=invalid_width,
                    )

    def test_zero_divisor_and_invalid_registers(self) -> None:
        with self.assertRaises(ZeroDivisionError):
            xor_accumulate_polynomial_division((1, 2), (0, 0), (3, 4), (5,))
        invalid_calls = (
            ((), (1,), (), ()),
            ((1,), (), (0,), (0,)),
            ((1,), (1,), (), (0,)),
            ((1,), (1,), (0,), ()),
            ((1,), (1,), (0, 0), (0,)),
            ((1,), (1,), (0,), (0, 0)),
            (
                (1,) * (MAX_DIVISION_DIVIDEND_WIDTH + 1),
                (1,),
                (0,) * (MAX_DIVISION_DIVIDEND_WIDTH + 1),
                (0,),
            ),
            (
                (1,),
                (1,) * (MAX_DIVISION_DIVISOR_WIDTH + 1),
                (0,),
                (0,) * MAX_DIVISION_DIVISOR_WIDTH,
            ),
            ((1, True), (1,), (0, 0), (0,)),
            ((1,), (1,), (0, -1), (0,)),
            ((1,), (1,), (0,), (4096,)),
            ([1], (1,), (0,), (0,)),
        )
        for arguments in invalid_calls:
            with self.subTest(arguments=arguments):
                with self.assertRaises((TypeError, ValueError)):
                    xor_accumulate_polynomial_division(*arguments)

    def test_zero_divisor_rejection_preserves_targets(self) -> None:
        quotient_target = (0x123, 0x456)
        remainder_target = (0x789,)
        with self.assertRaises(ZeroDivisionError):
            xor_accumulate_polynomial_division(
                (0xABC, 0xDEF),
                (0, 0),
                quotient_target,
                remainder_target,
            )
        self.assertEqual(quotient_target, (0x123, 0x456))
        self.assertEqual(remainder_target, (0x789,))

    def test_public_api_preserves_register_inputs_and_accumulates(self) -> None:
        dividend = (0x123, 0x456, 0x789, 0xABC)
        divisor = (0x00F, 0x101)
        quotient_target = (0x222, 0x333, 0x444, 0x555)
        remainder_target = (0x666,)
        original = (dividend, divisor, quotient_target, remainder_target)
        first = xor_accumulate_polynomial_division(*original)
        second = xor_accumulate_polynomial_division(
            first[0],
            first[1],
            first[2],
            first[3],
        )
        self.assertEqual(first[:2], original[:2])
        self.assertEqual(second[2:], original[2:])


class ReversibleDivisionSmallFieldTests(unittest.TestCase):
    def test_exhaustive_single_coefficient_full_register_states(self) -> None:
        state_counts: dict[int, int] = {}
        for degree, modulus in _SMALL_MODULI.items():
            field_size = 1 << degree
            seen_outputs: set[tuple[tuple[int, ...], ...]] = set()
            states = 0
            for dividend_value in range(field_size):
                for divisor_value in range(1, field_size):
                    expected_quotient, expected_remainder = _reference_division(
                        (dividend_value,),
                        (divisor_value,),
                        degree,
                        modulus,
                    )
                    expected_quotient = _pad(expected_quotient, 1)
                    expected_remainder = _pad(expected_remainder, 1)
                    for quotient_initial in range(field_size):
                        for remainder_initial in range(field_size):
                            add_primitive = _small_add

                            def multiply_primitive(
                                left: int,
                                right: int,
                                target: int,
                                *,
                                _degree: int = degree,
                                _modulus: int = modulus,
                            ) -> tuple[int, int, int]:
                                return _small_multiply(
                                    left,
                                    right,
                                    target,
                                    _degree,
                                    _modulus,
                                )

                            def inverse_primitive(
                                value: int,
                                target: int,
                                *,
                                _degree: int = degree,
                                _modulus: int = modulus,
                            ) -> tuple[int, int]:
                                return _small_inverse(
                                    value,
                                    target,
                                    _degree,
                                    _modulus,
                                )

                            quotient_out, remainder_out, scratch = (
                                _compute_accumulate_uncompute(
                                    (dividend_value,),
                                    (divisor_value,),
                                    (quotient_initial,),
                                    (remainder_initial,),
                                    add_primitive,
                                    multiply_primitive,
                                    inverse_primitive,
                                )
                            )
                            self.assertEqual(
                                quotient_out,
                                (quotient_initial ^ expected_quotient[0],),
                            )
                            self.assertEqual(
                                remainder_out,
                                (remainder_initial ^ expected_remainder[0],),
                            )
                            self.assertFalse(any(scratch))
                            state = (
                                (dividend_value,),
                                (divisor_value,),
                                quotient_out,
                                remainder_out,
                            )
                            self.assertNotIn(state, seen_outputs)
                            seen_outputs.add(state)
                            states += 1

            expected_states = field_size**3 * (field_size - 1)
            self.assertEqual(states, expected_states)
            self.assertEqual(len(seen_outputs), expected_states)
            state_counts[degree] = states

        self.assertEqual(state_counts, {2: 192, 3: 3584, 4: 61440})

    def test_bounded_exhaustive_small_field_register_domains(self) -> None:
        state_counts: dict[int, int] = {}
        operation_counts: dict[int, int] = {}
        for degree, modulus in _SMALL_MODULI.items():
            field_size = 1 << degree
            width = 2
            remainder_width = 1
            seen_outputs: set[tuple[tuple[int, ...], ...]] = set()
            states = 0
            operations = 0
            for dividend_value in range(field_size**width):
                dividend = (
                    dividend_value % field_size,
                    dividend_value // field_size,
                )
                for divisor_value in range(1, field_size**width):
                    divisor = (
                        divisor_value % field_size,
                        divisor_value // field_size,
                    )
                    expected_quotient, expected_remainder = _reference_division(
                        dividend,
                        divisor,
                        degree,
                        modulus,
                    )
                    expected_quotient = _pad(expected_quotient, width)
                    expected_remainder = _pad(expected_remainder, remainder_width)
                    self.assertFalse(
                        any(
                            _reference_division_identity_remainder(
                                dividend,
                                divisor,
                                expected_quotient,
                                expected_remainder,
                                degree,
                                modulus,
                            )
                        )
                    )
                    if any(expected_remainder):
                        self.assertLess(
                            _reference_polynomial_degree(expected_remainder),
                            _reference_polynomial_degree(divisor),
                        )

                    for target_case in range(2):
                        quotient_target = (
                            dividend[0] ^ divisor[0] ^ target_case,
                            dividend[1] ^ divisor[1] ^ target_case,
                        )
                        remainder_target = (
                            dividend[0] ^ divisor[1] ^ target_case,
                        )

                        add_primitive = _small_add

                        def multiply_primitive(
                            left: int,
                            right: int,
                            target: int,
                            *,
                            _degree: int = degree,
                            _modulus: int = modulus,
                        ) -> tuple[int, int, int]:
                            return _small_multiply(
                                left,
                                right,
                                target,
                                _degree,
                                _modulus,
                            )

                        def inverse_primitive(
                            value: int,
                            target: int,
                            *,
                            _degree: int = degree,
                            _modulus: int = modulus,
                        ) -> tuple[int, int]:
                            return _small_inverse(
                                value,
                                target,
                                _degree,
                                _modulus,
                            )

                        q_out, r_out, scratch = _compute_accumulate_uncompute(
                            dividend,
                            divisor,
                            quotient_target,
                            remainder_target,
                            add_primitive,
                            multiply_primitive,
                            inverse_primitive,
                        )
                        self.assertEqual(
                            q_out,
                            tuple(
                                target ^ value
                                for target, value in zip(
                                    quotient_target,
                                    expected_quotient,
                                )
                            ),
                        )
                        self.assertEqual(
                            r_out,
                            tuple(
                                target ^ value
                                for target, value in zip(
                                    remainder_target,
                                    expected_remainder,
                                )
                            ),
                        )
                        self.assertEqual(
                            dividend,
                            (dividend_value % field_size, dividend_value // field_size),
                        )
                        self.assertEqual(
                            divisor,
                            (divisor_value % field_size, divisor_value // field_size),
                        )
                        self.assertFalse(any(scratch))

                        q_twice, r_twice, scratch_twice = (
                            _compute_accumulate_uncompute(
                                dividend,
                                divisor,
                                q_out,
                                r_out,
                                add_primitive,
                                multiply_primitive,
                                inverse_primitive,
                            )
                        )
                        self.assertEqual(q_twice, quotient_target)
                        self.assertEqual(r_twice, remainder_target)
                        self.assertFalse(any(scratch_twice))

                        output_state = (dividend, divisor, q_out, r_out)
                        self.assertNotIn(output_state, seen_outputs)
                        seen_outputs.add(output_state)
                        states += 1
                        operations += 2

            expected_pairs = field_size**width * (field_size**width - 1)
            self.assertEqual(states, expected_pairs * 2)
            self.assertEqual(len(seen_outputs), states)
            state_counts[degree] = states
            operation_counts[degree] = operations

        self.assertEqual(state_counts, {2: 480, 3: 8064, 4: 130560})
        self.assertEqual(operation_counts, {2: 960, 3: 16128, 4: 261120})


if __name__ == "__main__":
    unittest.main()
