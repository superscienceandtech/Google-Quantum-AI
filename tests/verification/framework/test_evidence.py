from pathlib import Path
import json
from concurrent.futures import ThreadPoolExecutor

import pytest

from verification.framework.evidence import (
    append_evidence_record,
    ArtifactRecord,
    AuthorityClass,
    EvidenceRecord,
    hash_file,
)


def test_sha256_exact(tmp_path):
    artifact = tmp_path / "artifact.bin"
    artifact.write_bytes(b"abc")
    assert hash_file(artifact) == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"


def test_missing_file_hash_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        hash_file(tmp_path / "missing.bin")


def test_artifact_record_captures_identity(tmp_path):
    artifact = tmp_path / "record.txt"
    artifact.write_text("content", encoding="utf-8")
    record = ArtifactRecord.from_file(artifact, "text/plain")
    assert record.size_bytes == 7
    assert len(record.sha256) == 64
    assert record.media_type == "text/plain"


def test_invalid_sha256_rejected():
    with pytest.raises(ValueError):
        ArtifactRecord("bad", "x" * 64, 1)


def test_evidence_record_is_machine_readable(tmp_path):
    manifest = tmp_path / "evidence.jsonl"
    record = EvidenceRecord(
        evidence_id="EV-001",
        authority=AuthorityClass.TEAM_INTERNAL,
        status="NOT_VERIFIED",
        metadata={"reason": "official source unavailable"},
    )
    append_evidence_record(manifest, record)
    payload = manifest.read_text(encoding="utf-8")
    assert '"evidence_id":"EV-001"' in payload
    assert '"authority":"TEAM_INTERNAL"' in payload


def test_evidence_status_must_be_known():
    with pytest.raises(ValueError):
        EvidenceRecord("EV-002", AuthorityClass.UNVERIFIED, "MAYBE")


def test_pass_evidence_requires_artifacts_or_references():
    with pytest.raises(ValueError):
        EvidenceRecord(
            evidence_id="EV-003",
            authority=AuthorityClass.OFFICIAL_ECOSYSTEM,
            status="PASS",
        )


def test_evidence_references_are_normalized_and_validated():
    with pytest.raises(ValueError):
        EvidenceRecord(
            evidence_id="EV-004",
            authority=AuthorityClass.TEAM_INTERNAL,
            status="NOT_VERIFIED",
            evidence_refs=("evidence 1",),
        )

    record = EvidenceRecord(
        evidence_id="EV-005",
        authority=AuthorityClass.TEAM_INTERNAL,
        status="PASS",
        evidence_refs=(" evidence-001 ",),
    )
    assert record.evidence_refs == ("evidence-001",)


def test_artifact_symlink_rejected(tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("ok", encoding="utf-8")
    link = tmp_path / "artifact-link.txt"
    try:
        link.symlink_to(artifact)
    except OSError:
        pytest.skip("Windows symlink creation is not permitted")

    with pytest.raises(OSError):
        ArtifactRecord.from_file(link)


def test_jsonl_append_is_chained_and_locked(tmp_path):
    manifest = tmp_path / "evidence.jsonl"
    first = EvidenceRecord(
        evidence_id="EV-001",
        authority=AuthorityClass.TEAM_INTERNAL,
        status="NOT_VERIFIED",
    )
    second = EvidenceRecord(
        evidence_id="EV-002",
        authority=AuthorityClass.PUBLIC_SECONDARY,
        status="NOT_VERIFIED",
    )

    append_evidence_record(manifest, first)
    append_evidence_record(manifest, second)

    lines = manifest.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    envelopes = [json.loads(line) for line in lines]
    assert envelopes[0]["sequence"] == 1
    assert envelopes[1]["sequence"] == 2
    assert len(envelopes[0]["record_hash"]) == 64
    assert envelopes[1]["previous_hash"] == __import__("hashlib").sha256(
        (lines[0] + "\n").encode("utf-8")
    ).hexdigest()


def test_concurrent_jsonl_append_preserves_every_record(tmp_path):
    manifest = tmp_path / "evidence.jsonl"

    def append(index):
        append_evidence_record(
            manifest,
            EvidenceRecord(
                evidence_id=f"EV-{index:03d}",
                authority=AuthorityClass.TEAM_INTERNAL,
                status="NOT_VERIFIED",
            ),
        )

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(append, range(24)))

    lines = manifest.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 24
    envelopes = [json.loads(line) for line in lines]
    sequences = [envelope["sequence"] for envelope in envelopes]
    assert sorted(sequences) == list(range(1, 25))
