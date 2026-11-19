from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from invsqrt_opt.artifacts import (
    ArtifactDeclaration,
    ArtifactManifest,
    CompatibilityStatus,
    IntakeStatus,
    ProvenanceStatus,
    TrackingStatus,
    UnavailableCircuitArtifactAdapter,
    UnavailableKickmixBackend,
    assess_adapter_readiness,
    default_artifact_declarations,
    inspect_sdk,
)
from invsqrt_opt.backend import BuiltCircuit, OperationStatus
from invsqrt_opt.configurations import CandidateConfiguration
from invsqrt_opt.search_space import ParameterDefinition, ParameterKind, SearchSpace
from invsqrt_opt.verifier import ArtifactStatus, discover_artifacts


def test_manifest_discovers_artifacts_without_copying_or_executing_them(tmp_path):
    artifact = tmp_path / "circuit.kmb"
    artifact.write_bytes(b"opaque circuit bytes")
    declaration = ArtifactDeclaration(
        role="sample_submission",
        relative_path="circuit.kmb",
        provenance="test fixture",
    )

    manifest = ArtifactManifest.discover(
        tmp_path,
        declarations=(declaration,),
    )

    record = manifest.artifacts[0]
    assert manifest.schema_version == "2"
    assert record.status == IntakeStatus.AVAILABLE
    assert record.readable is True
    assert record.sha256 == hashlib.sha256(b"opaque circuit bytes").hexdigest()
    assert record.tracking_status == TrackingStatus.UNKNOWN
    assert record.compatibility_status == CompatibilityStatus.UNKNOWN
    assert record.artifact_id == "sample_submission"
    assert record.provenance_status == ProvenanceStatus.LOCAL_UNVERIFIED
    assert not manifest.to_dict().get("repository_root")
    json.dumps(manifest.to_dict())


def test_manifest_records_missing_artifact_and_unknown_sdk_api(tmp_path):
    manifest = ArtifactManifest.discover(tmp_path)

    assert all(record.status == IntakeStatus.MISSING for record in manifest.artifacts)
    assert all(
        record.provenance_status == ProvenanceStatus.MISSING
        for record in manifest.artifacts
    )
    assert manifest.sdk.name == "Kickmix"
    assert manifest.sdk.api_status == "UNKNOWN"
    readiness = assess_adapter_readiness(manifest)
    assert not readiness.ready
    assert readiness.status == "BLOCKED"
    assert readiness.artifact_provenance_statuses == {
        "official_verifier": ProvenanceStatus.MISSING.value,
        "reference_circuit": ProvenanceStatus.MISSING.value,
        "sample_submission": ProvenanceStatus.MISSING.value,
    }
    assert not readiness.required_artifacts_authenticated
    assert not readiness.verifier_available
    assert not readiness.reference_circuit_available
    assert not readiness.sample_submission_available
    assert not readiness.production_adapter_implemented


def test_unavailable_adapters_do_not_construct_circuits_or_report_metrics(tmp_path):
    artifact = tmp_path / "circuit.kmb"
    artifact.write_bytes(b"opaque circuit bytes")
    record = ArtifactManifest.discover(
        tmp_path,
        declarations=(
            ArtifactDeclaration("sample_submission", "circuit.kmb", "test fixture"),
        ),
    ).artifacts[0]
    operation = UnavailableCircuitArtifactAdapter().load(record)
    readiness = assess_adapter_readiness(ArtifactManifest.discover(tmp_path))
    backend = UnavailableKickmixBackend(readiness)
    search_space = SearchSpace(
        (
            ParameterDefinition(
                name="x",
                kind=ParameterKind.INTEGER,
                minimum=1,
                maximum=1,
                step=1,
            ),
        )
    )
    configuration = CandidateConfiguration.create(
        {"x": 1},
        search_space,
        strategy_id="test",
    )
    construction = backend.construct_circuit(configuration)
    measurement = backend.measure_resources(
        configuration,
        BuiltCircuit("untrusted-reference", object()),
    )

    assert not backend.available
    assert operation.status == OperationStatus.UNAVAILABLE
    assert construction.status == OperationStatus.UNAVAILABLE
    assert measurement.status == OperationStatus.UNAVAILABLE
    assert construction.value is None
    assert measurement.value is None


def test_manifest_marks_checksum_mismatch(tmp_path):
    (tmp_path / "artifact.bin").write_bytes(b"actual")
    declaration = ArtifactDeclaration(
        role="sample_submission",
        relative_path="artifact.bin",
        provenance="test fixture",
        expected_sha256=hashlib.sha256(b"expected").hexdigest(),
    )

    record = ArtifactManifest.discover(
        tmp_path,
        declarations=(declaration,),
    ).artifacts[0]

    assert record.status == IntakeStatus.CHECKSUM_MISMATCH
    assert record.sha256 == hashlib.sha256(b"actual").hexdigest()
    assert record.provenance_status == ProvenanceStatus.CORRUPTED


def test_hash_integrity_does_not_authenticate_artifact_source(tmp_path):
    contents = {
        "official_verifier": b"verifier fixture",
        "reference_circuit": b"circuit fixture",
        "sample_submission": b"submission fixture",
    }
    declarations = []
    for role, content in contents.items():
        relative_path = f"{role}.bin"
        (tmp_path / relative_path).write_bytes(content)
        declarations.append(
            ArtifactDeclaration(
                role=role,
                relative_path=relative_path,
                provenance="test fixture",
                expected_sha256=hashlib.sha256(content).hexdigest(),
                artifact_id=f"invsqrt-{role}",
                provenance_status=ProvenanceStatus.OFFICIAL_SOURCE_UNVERIFIED,
            )
        )

    manifest = ArtifactManifest.discover(
        tmp_path,
        declarations=tuple(declarations),
    )
    readiness = assess_adapter_readiness(manifest)

    assert all(
        status == "VERIFIED"
        for status in readiness.artifact_integrity_statuses.values()
    )
    assert all(
        status == ProvenanceStatus.OFFICIAL_SOURCE_UNVERIFIED.value
        for status in readiness.artifact_provenance_statuses.values()
    )
    assert not readiness.required_artifacts_authenticated
    assert any("not authenticated as official" in blocker for blocker in readiness.blockers)


def test_authenticated_source_requires_identity_and_evidence():
    with pytest.raises(ValueError, match="exact source identity"):
        ArtifactDeclaration(
            role="reference_circuit",
            relative_path="reference.py",
            provenance="test declaration",
            provenance_status=ProvenanceStatus.OFFICIAL_AUTHENTICATED,
        )


def test_authenticated_source_with_matching_hash_is_reported_separately(tmp_path):
    content = b"official test fixture"
    (tmp_path / "artifact.bin").write_bytes(content)
    declarations = tuple(
        ArtifactDeclaration(
            role=role,
            relative_path="artifact.bin",
            provenance="test fixture",
            expected_sha256=hashlib.sha256(content).hexdigest(),
            source_identity="test-only authenticated source",
            source_url="https://official.example/artifact.bin",
            authentication_evidence="test-only authentication fixture",
            provenance_status=ProvenanceStatus.OFFICIAL_AUTHENTICATED,
        )
        for role in ("official_verifier", "reference_circuit", "sample_submission")
    )

    manifest = ArtifactManifest.discover(tmp_path, declarations=declarations)
    readiness = assess_adapter_readiness(manifest)

    assert readiness.required_artifacts_authenticated
    assert set(readiness.artifact_integrity_statuses.values()) == {"VERIFIED"}
    assert set(readiness.artifact_provenance_statuses.values()) == {
        ProvenanceStatus.OFFICIAL_AUTHENTICATED.value
    }
    assert not readiness.ready
    assert any(
        "Production Kickmix circuit/resource adapter is not implemented" == blocker
        for blocker in readiness.blockers
    )


def test_artifact_declaration_rejects_traversal_and_absolute_paths(tmp_path):
    with pytest.raises(ValueError):
        ArtifactDeclaration("sample", "../outside.kmb", "test")
    with pytest.raises(ValueError):
        ArtifactDeclaration("sample", str(tmp_path / "outside.kmb"), "test")
    with pytest.raises(ValueError):
        ArtifactDeclaration("sample", r"C:outside.kmb", "test")
    with pytest.raises(ValueError):
        ArtifactDeclaration("sample", r"\outside.kmb", "test")


def test_legacy_discovery_rejects_windows_drive_relative_paths(tmp_path):
    results = discover_artifacts(
        tmp_path,
        (r"C:outside.kmb", r"\outside.kmb", "../outside.kmb"),
    )

    assert all(result.status == ArtifactStatus.INACCESSIBLE for result in results)


def test_manifest_rejects_symlink_artifact_paths(tmp_path, monkeypatch):
    link = tmp_path / "linked.kmb"
    is_symlink = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda path: path == link or is_symlink(path),
    )
    declaration = ArtifactDeclaration(
        role="sample_submission",
        relative_path="linked.kmb",
        provenance="test fixture",
    )

    record = ArtifactManifest.discover(
        tmp_path,
        declarations=(declaration,),
    ).artifacts[0]

    assert record.status == IntakeStatus.INVALID
    assert record.sha256 is None


def test_sdk_inventory_does_not_claim_api_readiness(monkeypatch):
    monkeypatch.setattr("invsqrt_opt.artifacts.importlib.util.find_spec", lambda _: None)

    sdk = inspect_sdk()

    assert sdk.import_available is False
    assert sdk.version is None
    assert sdk.api_status == "UNKNOWN"


def test_default_manifest_paths_are_confined_to_expected_artifact_tree():
    paths = [Path(spec.relative_path) for spec in default_artifact_declarations()]

    assert all(not path.is_absolute() for path in paths)
    assert all(".." not in path.parts for path in paths)
    assert {spec.role for spec in default_artifact_declarations()} == {
        "official_verifier",
        "reference_circuit",
        "sample_submission",
        "sdk_library",
    }
