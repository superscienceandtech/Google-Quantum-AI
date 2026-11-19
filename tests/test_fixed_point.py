from dataclasses import asdict
import json
from typing import cast

import pytest

from invsqrt_opt.fixed_point import (
    FixedPointPrecision,
    _truncated_product,
    fixed_point_reference,
    fixed_point_value,
)


EXPECTED_COEFFICIENT_TABLE = (
    (131064, 65025, 43596, 19499),
    (107018, 35568, 16720, 5866),
    (92676, 22990, 7707, 1724),
    (75673, 12575, 2956, 518),
)

REFERENCE_GOLDEN_OUTPUTS = {
    1: 1_099_511_609_344,
    2: 777_472_123_904,
    3: 634_803_334_144,
    4: 549_755_804_672,
    5: 491_716_544_512,
    6: 448_873_742_336,
    7: 415_576_332_288,
    8: 388_736_061_952,
    12: 317_401_667_072,
    16: 274_877_902_336,
    24: 224_436_871_168,
    32: 194_368_030_976,
    63: 138_525_444_096,
    64: 137_438_951_168,
    127: 97_565_880_064,
    128: 97_184_015_488,
    255: 68_854_088_704,
    256: 68_719_475_584,
    511: 48_639_531_072,
    512: 48_592_007_744,
    1023: 34_376_527_936,
    1024: 34_359_737_792,
    2047: 24_301_938_208,
    2048: 24_296_003_872,
    2_588_411: 683_412_976,
    3_133_452: 621_138_295,
}


def test_source_defined_coefficient_encoding_matches_integer_vectors():
    assert FixedPointPrecision().coefficient_table() == EXPECTED_COEFFICIENT_TABLE
    assert (
        FixedPointPrecision().coefficient_table()
        == FixedPointPrecision().coefficient_table()
    )
    assert all(
        0 <= value < 1 << 17
        for row in EXPECTED_COEFFICIENT_TABLE
        for value in row
    )


def test_precision_configuration_serialization_is_deterministic():
    precision = FixedPointPrecision()
    expected = (
        '{"coef_bits": 17, "delta_bits": 14, "product_bits": 28, '
        '"result_bits": 29, "square_bits": 28}'
    )
    assert json.dumps(asdict(precision), sort_keys=True) == expected


@pytest.mark.parametrize(
    ("rows", "operand", "output_bits", "operand_bits", "register_bits", "expected"),
    [
        ((), 0, 0, 0, 1, 0),
        (((1, 0),), 0, 3, 3, 4, 0),
        (((1, 0),), 1, 3, 3, 4, 1),
        (((1, 0),), 15, 3, 3, 4, 15),
        (((1, 1),), 7, 3, 3, 5, 14),
        (((1, -1),), 3, 3, 3, 4, 1),
        (((1, -1),), 5, 2, 3, 4, 1),
        (((1, -2),), 7, 2, 3, 4, 0),
        (((1, -14),), (1 << 14) - 1, 17, 17, 14, 0),
    ],
)
def test_row_multiplier_boundaries_and_exact_truncation(
    rows, operand, output_bits, operand_bits, register_bits, expected
):
    assert _truncated_product(
        rows,
        operand=operand,
        output_fraction_bits=output_bits,
        operand_fraction_bits=operand_bits,
        register_limit_bits=register_bits,
    ) == expected


@pytest.mark.parametrize(
    ("rows", "operand", "widths"),
    [
        (((1, 0),), -1, (2, 2, 4)),
        (((2, 0),), 1, (2, 2, 4)),
        (((True, 0),), 1, (2, 2, 4)),
        (((1, True),), 1, (2, 2, 4)),
        (((1, 0),), 1, (True, 2, 4)),
        (((1, 0),), 1, (-1, 2, 4)),
        (((1, 0),), 1, (2, -1, 4)),
        (((1, 0),), 1, (2, 2, 0)),
        (((1, 0, 2),), 1, (2, 2, 4)),
    ],
)
def test_row_multiplier_rejects_unsupported_operands_and_rows(rows, operand, widths):
    with pytest.raises(ValueError):
        _truncated_product(
            rows,
            operand=operand,
            output_fraction_bits=widths[0],
            operand_fraction_bits=widths[1],
            register_limit_bits=widths[2],
        )


def test_row_multiplier_truncates_negative_shift_toward_floor():
    assert _truncated_product(
        ((1, 0),), operand=0b101, output_fraction_bits=2,
        operand_fraction_bits=3, register_limit_bits=4,
    ) == 0b10


def test_row_multiplier_accumulates_columns_and_checks_register_overflow():
    assert _truncated_product(
        ((1, 0), (1, 1)), operand=3, output_fraction_bits=2,
        operand_fraction_bits=2, register_limit_bits=4,
    ) == 9
    with pytest.raises(OverflowError, match="register overflow"):
        _truncated_product(
            ((1, 0), (1, 0)), operand=8, output_fraction_bits=3,
            operand_fraction_bits=3, register_limit_bits=4,
        )


@pytest.mark.parametrize(
    ("value", "expected_shift", "expected_case", "expected_intermediates", "expected_output"),
    [
        (1, 10, 0, (131_064, 65_025, 43_596, 19_499), 1_099_511_609_344),
        (6, 9, 1, (107_018, 35_568, 16_720, 5_866), 448_873_742_336),
        (8, 9, 2, (92_676, 22_990, 7_707, 1_724), 388_736_061_952),
        (12, 9, 3, (75_673, 12_575, 2_956, 518), 317_401_667_072),
    ],
)
def test_stage_vectors_for_all_four_interval_cases(
    value, expected_shift, expected_case, expected_intermediates, expected_output
):
    result = fixed_point_reference(value)
    assert result.shift_pairs == expected_shift
    assert result.interval_case == expected_case
    assert result.coefficient_integers == expected_intermediates
    assert result.result_register == expected_output


@pytest.mark.parametrize("value, expected", REFERENCE_GOLDEN_OUTPUTS.items())
def test_golden_output_matches_source_reference_model(value, expected):
    result = fixed_point_reference(value)
    assert result.result_register == expected
    numerator, denominator = fixed_point_value(value)
    assert numerator == expected
    assert denominator == 1 << 40


def test_result_is_deterministic_and_preserves_input():
    first = fixed_point_reference(2_588_411)
    second = fixed_point_reference(2_588_411)
    assert first == second
    assert first.input_value == 2_588_411
    assert first.phase_turns_numerator == first.result_register
    assert first.phase_turns_denominator == 1 << first.phase_fraction_bits


@pytest.mark.parametrize("value", [0, -1, 3_133_453, True, 1.0, "1"])
def test_model_rejects_invalid_benchmark_inputs(value):
    with pytest.raises(ValueError):
        fixed_point_reference(value)


@pytest.mark.parametrize(
    "values",
    [
        {"delta_bits": 0},
        {"coef_bits": -1},
        {"square_bits": True},
        {"product_bits": 0},
        {"result_bits": 1.5},
    ],
)
def test_precision_rejects_invalid_widths(values):
    with pytest.raises(ValueError):
        FixedPointPrecision(**values)


def test_model_rejects_unsupported_precision_object_and_invalid_np():
    with pytest.raises(ValueError, match="FixedPointPrecision"):
        fixed_point_reference(1, precision=cast(FixedPointPrecision, object()))
    with pytest.raises(ValueError, match="n_p"):
        fixed_point_reference(1, n_p=True)
    with pytest.raises(ValueError, match="Only the benchmark n_p=10"):
        fixed_point_reference(1, n_p=9)


@pytest.mark.parametrize(
    "values",
    [
        {"delta_bits": 13},
        {"coef_bits": 16},
        {"square_bits": 27},
        {"product_bits": 27},
        {"result_bits": 28},
    ],
)
def test_model_rejects_unsupported_precision_configurations(values):
    with pytest.raises(ValueError, match="default fixed-point precision"):
        fixed_point_reference(1, precision=FixedPointPrecision(**values))


def test_input_api_rejects_decimal_and_float_without_coercion():
    from decimal import Decimal

    for value in (Decimal(1), 1.0, True):
        with pytest.raises(ValueError):
            fixed_point_reference(value)
