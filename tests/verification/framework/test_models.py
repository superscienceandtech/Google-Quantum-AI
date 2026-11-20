import pytest

from verification.framework.models import ValidationResult, VerificationStatus


def test_validation_status_values():
    assert VerificationStatus.PASS.value == "PASS"
    assert ValidationResult(
        status=VerificationStatus.NOT_VERIFIED,
        name="generic",
        authority="TEAM_INTERNAL",
    ).status == VerificationStatus.NOT_VERIFIED


def test_validation_name_and_authority_required():
    with pytest.raises(ValueError):
        ValidationResult(
            status=VerificationStatus.FAIL,
            name="",
            authority="TEAM_INTERNAL",
        )
    with pytest.raises(ValueError):
        ValidationResult(
            status=VerificationStatus.FAIL,
            name="generic",
            authority="",
        )


def test_official_pass_requires_evidence_reference():
    with pytest.raises(ValueError):
        ValidationResult(
            status=VerificationStatus.PASS,
            name="official gate",
            authority="OFFICIAL_COMPETITION_VERIFIER",
        )

    result = ValidationResult(
        status=VerificationStatus.PASS,
        name="official gate",
        authority="OFFICIAL_COMPETITION_VERIFIER",
        evidence_refs=("evidence-001",),
    )
    assert result.evidence_refs == ("evidence-001",)


def test_official_pass_rejects_empty_duplicate_and_whitespace_refs():
    with pytest.raises(ValueError):
        ValidationResult(
            status=VerificationStatus.PASS,
            name="official gate",
            authority="OFFICIAL_COMPETITION_VERIFIER",
            evidence_refs=("",),
        )
    with pytest.raises(ValueError):
        ValidationResult(
            status=VerificationStatus.PASS,
            name="official gate",
            authority="OFFICIAL_COMPETITION_VERIFIER",
            evidence_refs=("evidence 001",),
        )
    with pytest.raises(ValueError):
        ValidationResult(
            status=VerificationStatus.PASS,
            name="official gate",
            authority="OFFICIAL_COMPETITION_VERIFIER",
            evidence_refs=("evidence-001", "evidence-001"),
        )


def test_official_pass_manifest_membership():
    with pytest.raises(ValueError):
        ValidationResult(
            status=VerificationStatus.PASS,
            name="official gate",
            authority="OFFICIAL_COMPETITION_VERIFIER",
            evidence_refs=("missing-evidence",),
            evidence_manifest={"other-evidence": {}},
        )

    result = ValidationResult(
        status=VerificationStatus.PASS,
        name="official gate",
        authority="OFFICIAL_COMPETITION_VERIFIER",
        evidence_refs=("evidence-001",),
        evidence_manifest={"evidence-001": {"status": "PASS"}},
    )
    assert result.evidence_refs == ("evidence-001",)


def test_unknown_authority_rejected():
    with pytest.raises(ValueError):
        ValidationResult(
            status=VerificationStatus.FAIL,
            name="generic",
            authority="UNSUPPORTED",
        )
