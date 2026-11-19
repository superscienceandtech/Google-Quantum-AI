from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from invsqrt_opt.contract import (
    OFFICIAL_INVSQRT_SPEC,
    CircuitContract,
    CircuitValidationLevel,
    InvSqrtSpecification,
    validate_input,
    validate_inputs,
)
from invsqrt_opt.models import (
    Candidate,
    CandidateState,
    ExperimentConfig,
    ExperimentStatus,
    VerificationStatus,
)
from invsqrt_opt.verifier import (
    ArtifactStatus,
    ExecutionStatus,
    TestDoubleVerifierAdapter,
    UnavailableVerifierAdapter,
    VerificationRequest,
    VerificationResult,
    VerificationLevel,
    VerificationStatus as VerifierVerificationStatus,
    discover_artifacts,
)


def test_official_specification_values():
    spec = OFFICIAL_INVSQRT_SPEC
    assert spec.minimum_input == 1
    assert spec.maximum_input == 3_133_452
    assert spec.np == 10
    assert spec.beta == 1
    assert spec.input_width == 22
    assert spec.shots_per_input == 64
    assert spec.total_shots == 200_540_928
    assert spec.register_name == "x"


def test_specification_is_immutable_and_serializable():
    spec = OFFICIAL_INVSQRT_SPEC
    restored = InvSqrtSpecification.from_json(spec.to_json())
    assert restored == spec
    with pytest.raises(FrozenInstanceError):
        setattr(spec, "beta", 2)


def test_specification_rejects_invalid_values():
    data = OFFICIAL_INVSQRT_SPEC.to_dict()
    data["total_shots"] = 1
    with pytest.raises(ValueError):
        InvSqrtSpecification.from_dict(data)
    data = OFFICIAL_INVSQRT_SPEC.to_dict()
    data["np"] = 11
    with pytest.raises(ValueError):
        InvSqrtSpecification.from_dict(data)


@pytest.mark.parametrize(
    ("value", "valid"),
    [
        (1, True),
        (3_133_452, True),
        (2, True),
        (0, False),
        (3_133_453, False),
        (-1, False),
        (True, False),
        (1.0, False),
        ("1", False),
    ],
)
def test_input_domain_validation(value, valid):
    if valid:
        assert validate_input(value) == value
    else:
        with pytest.raises(ValueError):
            validate_input(value)


def test_collection_validation_and_duplicate_detection():
    assert validate_inputs([1, 2, 3_133_452], require_unique=True) == (
        1,
        2,
        3_133_452,
    )
    with pytest.raises(ValueError):
        validate_inputs([1, 1], require_unique=True)


def valid_circuit_contract(**overrides):
    values = {
        "candidate_id": "candidate-001",
        "circuit_artifact": "invsqrt.kmb",
        "register_names": ("x",),
        "register_widths": {"x": 22},
        "distinct_qubit_ids": {"x": tuple(range(22))},
        "total_qubit_count": 22,
        "input_register_restored": True,
        "scratch_registers_restored": True,
        "validation_level": CircuitValidationLevel.METADATA_VALIDATED,
        "evidence_references": ("metadata-review:1",),
    }
    values.update(overrides)
    return CircuitContract(**values)


def test_valid_circuit_metadata():
    contract = valid_circuit_contract()
    assert contract.validate_metadata() == []


def test_circuit_metadata_allows_accounted_scratch_qubits():
    contract = valid_circuit_contract(
        total_qubit_count=24,
        additional_qubit_ids=(22, 23),
    )
    assert contract.validate_metadata() == []


@pytest.mark.parametrize(
    "overrides",
    [
        {"register_names": ()},
        {"register_names": ("y",)},
        {"register_widths": {"x": 21}},
        {"distinct_qubit_ids": {"x": tuple(range(21))}},
        {"distinct_qubit_ids": {"x": (0,) * 22}},
        {"input_register_restored": None},
        {"scratch_registers_restored": None},
        {"total_qubit_count": 23},
    ],
)
def test_invalid_circuit_metadata(overrides):
    contract = valid_circuit_contract(**overrides)
    assert contract.validate_metadata()


def test_circuit_official_promotion_requires_verifier():
    contract = valid_circuit_contract()
    assert contract.with_validation_level(
        CircuitValidationLevel.STRUCTURALLY_VALIDATED
    ).validation_level == CircuitValidationLevel.STRUCTURALLY_VALIDATED
    with pytest.raises(ValueError):
        contract.with_validation_level(
            CircuitValidationLevel.OFFICIAL_VERIFIER_VALIDATED
        )


def verification_request(**overrides):
    values = {
        "request_id": "verify-001",
        "candidate_id": "candidate-001",
        "candidate_artifact": "invsqrt.kmb",
        "specification_version": "P003-1",
        "verifier_id": "official-invsqrt-verifier",
        "git_commit": "5391b2e7123484efacffc0588f5e761e67b5cb55",
        "environment_metadata": {"python": "3.14"},
        "requested_level": VerificationLevel.OFFICIAL,
        "creation_timestamp": "2026-11-19T18:29:23+06:00",
        "authorization_reference": "P003-approved",
    }
    values.update(overrides)
    return VerificationRequest(**values)


def test_verification_request_round_trip():
    request = verification_request()
    assert VerificationRequest.from_dict(request.to_dict()) == request


def test_unavailable_verifier_is_fail_closed():
    adapter = UnavailableVerifierAdapter()
    availability = adapter.discover()
    assert availability.status == ArtifactStatus.MISSING
    result = adapter.execute(verification_request())
    assert result.verification_status == VerifierVerificationStatus.VERIFIER_UNAVAILABLE
    assert result.execution_status == ExecutionStatus.NOT_STARTED
    assert result.provenance_complete is False


def test_test_double_can_never_pass_officially():
    adapter = TestDoubleVerifierAdapter()
    result = adapter.execute(verification_request())
    assert result.verification_status == VerifierVerificationStatus.REJECTED
    assert result.verifier_source_checksum is None
    assert result.provenance_complete is False


def test_incomplete_verification_pass_is_rejected():
    with pytest.raises(ValueError):
        VerificationResult(
            request_id="verify-001",
            candidate_id="candidate-001",
            verifier_id="official-invsqrt-verifier",
            verifier_source_checksum=None,
            execution_status=ExecutionStatus.EXECUTED,
            verification_status=VerifierVerificationStatus.PASSED,
            exit_code=0,
            evidence_references=("official-output:1",),
            provenance_complete=True,
        )


def test_candidate_official_promotion_requires_real_result():
    candidate = Candidate(
        candidate_id="candidate-001",
        candidate_version="v1",
        optimization_strategy="foundation",
        configuration={},
        circuit_artifact="invsqrt.kmb",
    )
    with pytest.raises(ValueError):
        Candidate(
            candidate_id="candidate-001",
            candidate_version="v1",
            optimization_strategy="foundation",
            configuration={},
            state=CandidateState.OFFICIAL_VERIFIER_VALIDATED,
            verification_status=VerificationStatus.PASSED,
            evidence_references=("cannot-be-enough",),
        )
    result = VerificationResult(
        request_id="verify-001",
        candidate_id="candidate-001",
        verifier_id="official-invsqrt-verifier",
        verifier_source_checksum="official-source-checksum",
        execution_status=ExecutionStatus.EXECUTED,
        verification_status=VerifierVerificationStatus.PASSED,
        exit_code=0,
        evidence_references=("official-output:run-1",),
        provenance_complete=True,
    )
    promoted = candidate.promote_from_verification_result(result)
    assert promoted.state == CandidateState.OFFICIAL_VERIFIER_VALIDATED


def test_executed_result_with_unknown_status_is_rejected():
    with pytest.raises(ValueError):
        VerificationResult(
            request_id="verify-001",
            candidate_id="candidate-001",
            verifier_id="official-invsqrt-verifier",
            verifier_source_checksum="abc",
            execution_status=ExecutionStatus.EXECUTED,
            verification_status=VerifierVerificationStatus.NOT_CHECKED,
            exit_code=0,
            evidence_references=("official-output:1",),
            provenance_complete=True,
        )


def test_artifact_discovery_is_read_only(tmp_path):
    discoveries = discover_artifacts(tmp_path)
    assert len(discoveries) == 3
    assert all(
        discovery.status == ArtifactStatus.MISSING
        for discovery in discoveries
    )
    official = tmp_path / "external/verifiers/invsqrt"
    official.mkdir(parents=True)
    verifier = official / "verify_submission_invsqrt.py"
    verifier.write_text("print('fixture')\n", encoding="utf-8")
    discoveries = discover_artifacts(tmp_path)
    by_path = {item.relative_path: item for item in discoveries}
    assert by_path[
        "external/verifiers/invsqrt/verify_submission_invsqrt.py"
    ].status == ArtifactStatus.AVAILABLE
    assert by_path[
        "external/verifiers/invsqrt/verify_submission_invsqrt.py"
    ].sha256
    assert verifier.read_text(encoding="utf-8") == "print('fixture')\n"


def test_p002_candidate_and_experiment_compatibility():
    candidate = Candidate(
        candidate_id="candidate-001",
        candidate_version="v1",
        optimization_strategy="foundation",
        configuration={},
    )
    assert Candidate.from_dict(candidate.to_dict()) == candidate
    config = ExperimentConfig(
        experiment_id="exp-001",
        candidate_id="candidate-001",
        strategy_name="foundation",
        parameter_configuration={},
        random_seed=None,
        software_version="0.1",
        dependency_metadata={"python": "3.14"},
        git_commit="5391b2e7123484efacffc0588f5e761e67b5cb55",
        creation_timestamp="2026-11-19T18:29:23+06:00",
        execution_status=ExperimentStatus.CREATED,
    )
    assert ExperimentConfig.from_dict(config.to_dict()) == config
