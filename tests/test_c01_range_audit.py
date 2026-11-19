import hashlib

import pytest

from invsqrt_opt.candidates.c01_range_audit import (
    CANDIDATE_ID,
    CANDIDATE_VERSION,
    RangeAuditConfig,
    audit_interval_partition,
    get_interval_partition_regions,
    run_range_audit,
)
from invsqrt_opt.fixed_point import FixedPointPrecision, fixed_point_reference


def test_range_audit_reports_baseline_golden_outputs_and_stage_ranges():
    result = run_range_audit(RangeAuditConfig(1, 1))

    assert result.candidate_id == CANDIDATE_ID == "P010-C01"
    assert result.candidate_version == CANDIDATE_VERSION
    assert result.inputs_evaluated == 1
    assert result.full_domain is False
    assert result.execution_status == "COMPLETED"
    assert result.passed
    assert result.baseline_output_sha256 == hashlib.sha256(
        (1_099_511_609_344).to_bytes(5, "big")
    ).hexdigest()

    ranges = {item.name: item for item in result.register_ranges}
    assert ranges["normalized"].minimum == 1 << 20
    assert ranges["normalized"].declared_bits == 22
    assert ranges["shift_pairs"].minimum == 10
    assert ranges["interval_case"].minimum == 0
    assert ranges["coefficient_c0"].minimum == 131_064
    assert ranges["coefficient_c3"].minimum == 19_499
    assert ranges["horner_r1"].minimum == 43_596
    assert ranges["horner_r2"].minimum == 65_025
    assert ranges["horner_r3"].minimum == 131_064
    assert ranges["newton_correction"].declared_bits is None
    assert ranges["newton_correction"].minimum_required_unsigned_bits == 30

    horner_rows = [
        row for row in result.row_contribution_ranges
        if row.operator.startswith("horner_")
    ]
    assert horner_rows
    assert all(row.maximum == 0 for row in horner_rows)
    assert all(check.checked_inputs == 1 for check in result.consistency_checks)
    assert all(check.mismatch_count == 0 for check in result.consistency_checks)


def test_default_config_is_explicit_full_domain_and_serializable():
    default_config = RangeAuditConfig()
    result = run_range_audit(RangeAuditConfig(1, 1))
    payload = result.to_dict()

    assert default_config.minimum_input == 1
    assert default_config.maximum_input == 3_133_452
    assert default_config.n_p == 10
    assert result.configuration["precision"] == {
        "delta_bits": 14,
        "coef_bits": 17,
        "square_bits": 28,
        "product_bits": 28,
        "result_bits": 29,
    }
    assert payload["input_coverage"]["full_domain"] is False
    assert payload["baseline"]["source_sha256"]
    assert payload["candidate_implementation_sha256"]


def test_subrange_audit_counts_only_critical_inputs_in_its_coverage():
    result = run_range_audit(RangeAuditConfig(6, 8))

    assert result.passed
    assert result.inputs_evaluated == 3
    assert result.critical_inputs_in_run == 3
    assert result.critical_inputs_in_run < result.critical_inputs_total


def test_domain_maximum_matches_pinned_baseline_and_is_deterministic():
    maximum_input = 3_133_452
    config = RangeAuditConfig(maximum_input, maximum_input)

    first = run_range_audit(config)
    second = run_range_audit(config)

    expected_digest = hashlib.sha256(
        (621_138_295).to_bytes(5, "big")
    ).hexdigest()
    assert first.passed and second.passed
    assert first.baseline_output_sha256 == expected_digest
    assert second.baseline_output_sha256 == expected_digest
    assert first.register_ranges == second.register_ranges
    assert first.row_contribution_ranges == second.row_contribution_ranges


@pytest.mark.parametrize(
    "values",
    [
        {"minimum_input": True, "maximum_input": 2},
        {"minimum_input": 0, "maximum_input": 2},
        {"minimum_input": 3, "maximum_input": 2},
        {"maximum_input": 3_133_453},
        {"n_p": 9},
        {"precision": FixedPointPrecision(coef_bits=16)},
    ],
)
def test_range_audit_rejects_invalid_or_unsupported_configuration(values):
    with pytest.raises(ValueError):
        RangeAuditConfig(**values)


def test_range_audit_rejects_invalid_configuration_object():
    with pytest.raises(ValueError, match="RangeAuditConfig"):
        run_range_audit(object())  # type: ignore[arg-type]


def test_interval_partition_is_complete_and_non_overlapping():
    regions = get_interval_partition_regions()
    subranges = sorted(
        subrange
        for region in regions
        for subrange in region.normalized_subranges
    )

    assert tuple(region.interval_case for region in regions) == (0, 1, 2, 3)
    assert subranges == [
        (1_048_576, 1_572_864),
        (1_572_864, 2_097_152),
        (2_097_152, 3_145_728),
        (3_145_728, 4_194_304),
    ]
    assert subranges[0][0] == 1_048_576
    assert subranges[-1][1] == 4_194_304
    assert all(left[1] == right[0] for left, right in zip(subranges, subranges[1:]))


def test_interval_partition_boundary_values_match_fixed_point_cases():
    test_inputs = (
        1,
        1_048_575,
        1_048_576,
        1_310_719,
        1_310_720,
        1_572_863,
        1_572_864,
        1_835_007,
        1_835_008,
        2_097_151,
        2_097_152,
        2_621_439,
        2_621_440,
        3_133_452,
    )
    for input_value in test_inputs:
        result = audit_interval_partition(
            RangeAuditConfig(input_value, input_value)
        )
        fixed_point_result = fixed_point_reference(input_value)
        assert result.inputs_checked == 1
        assert result.mismatch_count == 0
        assert fixed_point_result.interval_case in (0, 1, 2, 3)


def test_interval_partition_rejects_domain_minimum_and_maximum_invalid():
    with pytest.raises(ValueError):
        audit_interval_partition(RangeAuditConfig(0, 1))
    with pytest.raises(ValueError):
        audit_interval_partition(RangeAuditConfig(1, 3_133_453))


def test_interval_partition_audit_is_deterministic_for_small_subrange():
    config = RangeAuditConfig(1, 4096)
    first = audit_interval_partition(config)
    second = audit_interval_partition(config)

    assert first.to_dict() == second.to_dict()
    assert first.passed
    assert first.inputs_checked == 4096
    assert first.mismatch_count == 0
