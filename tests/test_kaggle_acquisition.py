from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import zipfile

import pytest

from invsqrt_opt.artifacts import ProvenanceStatus, assess_adapter_readiness
from invsqrt_opt.kaggle_acquisition import (
    AcquisitionError,
    AcquisitionLimits,
    ArchiveStatus,
    DownloadStatus,
    ExtractionError,
    KaggleAcquisitionAdapter,
    PreflightStatus,
    RoleMappingStatus,
    VERIFIED_COMPETITION_SLUG,
)


def _configure_cli(monkeypatch, tmp_path, runner):
    executable = tmp_path / "kaggle.exe"
    executable.write_bytes(b"test executable placeholder")
    monkeypatch.setattr(
        "invsqrt_opt.kaggle_acquisition.shutil.which",
        lambda _: str(executable),
    )
    monkeypatch.setattr(
        "invsqrt_opt.kaggle_acquisition.subprocess.run",
        runner,
    )
    return executable


def _completed(args, *, returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args, returncode, stdout, stderr)


def _successful_runner(calls):
    def run(args, **kwargs):
        calls.append((tuple(args), kwargs))
        if args[-1] == "--version":
            return _completed(args, stdout="Kaggle API 1.6.17\n")
        return _completed(args, stdout="download complete\n")

    return run


def _successful_download(monkeypatch, tmp_path, *, output_directory=None, limits=None):
    calls = []
    _configure_cli(monkeypatch, tmp_path, _successful_runner(calls))
    adapter = KaggleAcquisitionAdapter(tmp_path, limits=limits)
    result = adapter.download(
        output_directory=output_directory,
        authentication_probe=lambda _executable, _slug: True,
    )
    return adapter, result, calls


def test_missing_cli_blocks_preflight_and_never_runs_download(tmp_path, monkeypatch):
    monkeypatch.setattr("invsqrt_opt.kaggle_acquisition.shutil.which", lambda _: None)
    monkeypatch.setattr(
        "invsqrt_opt.kaggle_acquisition._authentication_hints",
        lambda: (),
    )
    calls = []
    monkeypatch.setattr(
        "invsqrt_opt.kaggle_acquisition.subprocess.run",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    adapter = KaggleAcquisitionAdapter(tmp_path)
    preflight = adapter.preflight()
    result = adapter.download()

    assert preflight.status == PreflightStatus.KAGGLE_CLI_MISSING
    assert result.status == DownloadStatus.BLOCKED
    assert result.command is None
    assert calls == []
    assert not adapter.staging_root.exists()


def test_missing_authentication_configuration_blocks_without_cli_download(
    tmp_path, monkeypatch
):
    calls = []
    _configure_cli(monkeypatch, tmp_path, _successful_runner(calls))
    monkeypatch.setattr(
        "invsqrt_opt.kaggle_acquisition._authentication_hints",
        lambda: (),
    )

    adapter = KaggleAcquisitionAdapter(tmp_path)
    preflight = adapter.preflight()
    result = adapter.download()

    assert preflight.status == PreflightStatus.AUTHENTICATION_UNAVAILABLE
    assert result.status == DownloadStatus.BLOCKED
    assert all(call[0][1] == "--version" for call in calls)
    assert not any(call[0][1:3] == ("competitions", "download") for call in calls)
    assert not adapter.staging_root.exists()


def test_authentication_configuration_presence_is_not_authentication(
    tmp_path, monkeypatch
):
    executable = _configure_cli(
        monkeypatch, tmp_path, _successful_runner([])
    )
    monkeypatch.setattr(
        "invsqrt_opt.kaggle_acquisition._authentication_hints",
        lambda: ("KAGGLE_KEY",),
    )

    result = KaggleAcquisitionAdapter(tmp_path).preflight()

    assert result.executable_path == executable.resolve()
    assert result.cli_version == "1.6.17"
    assert result.authentication_configuration_detected
    assert not result.authentication_verified
    assert result.status == PreflightStatus.AUTHENTICATION_UNVERIFIED


def test_unverified_slug_is_rejected_before_cli_discovery(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "invsqrt_opt.kaggle_acquisition.shutil.which",
        lambda _: pytest.fail("CLI discovery should not run"),
    )

    result = KaggleAcquisitionAdapter(tmp_path).preflight(
        competition_slug="another-competition"
    )

    assert result.status == PreflightStatus.COMPETITION_IDENTITY_UNVERIFIED


@pytest.mark.parametrize(
    "path",
    (
        "src",
        "tests",
        "docs",
        "../outside",
        r"C:outside",
        r"\outside",
    ),
)
def test_output_path_must_be_inside_approved_staging(tmp_path, path):
    adapter = KaggleAcquisitionAdapter(tmp_path)

    result = adapter.preflight(output_directory=path)

    assert result.status == PreflightStatus.OUTPUT_PATH_INVALID


def test_output_path_rejects_symlink_components(tmp_path, monkeypatch):
    adapter = KaggleAcquisitionAdapter(tmp_path)
    target = tmp_path / "external"
    is_link = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda path: path == target or is_link(path),
    )

    result = adapter.preflight()

    assert result.status == PreflightStatus.OUTPUT_PATH_INVALID


def test_safe_download_uses_argument_array_and_unique_staging(
    tmp_path, monkeypatch
):
    calls = []
    adapter, result, calls = _successful_download(
        monkeypatch,
        tmp_path,
        output_directory="external\\acquisition-staging\\invsqrt",
    )

    assert result.status == DownloadStatus.SUCCEEDED
    assert result.command is not None
    assert result.command[1:] == (
        "competitions",
        "download",
        "-c",
        VERIFIED_COMPETITION_SLUG,
        "-p",
        str(result.staging_directory),
    )
    assert result.staging_directory is not None
    assert result.staging_directory.parent == adapter.staging_root
    assert calls[-1][1]["shell"] is False
    assert isinstance(calls[-1][0], tuple)
    assert calls[-1][1]["timeout"] == adapter.limits.timeout_seconds


def test_download_does_not_overwrite_existing_files(tmp_path, monkeypatch):
    adapter = KaggleAcquisitionAdapter(tmp_path)
    existing = adapter.staging_root / "operator-data.txt"
    existing.parent.mkdir(parents=True)
    existing.write_text("preserve", encoding="utf-8")
    _, result, _ = _successful_download(monkeypatch, tmp_path)

    assert result.status == DownloadStatus.SUCCEEDED
    assert existing.read_text(encoding="utf-8") == "preserve"
    assert result.staging_directory != adapter.staging_root
    assert result.staging_directory is not None
    assert result.staging_directory.is_dir()


def test_download_timeout_is_classified_without_returning_process_output(
    tmp_path, monkeypatch
):
    calls = []

    def run(args, **kwargs):
        calls.append((tuple(args), kwargs))
        if args[-1] == "--version":
            return _completed(args, stdout="Kaggle API 1.6.17")
        raise subprocess.TimeoutExpired(args, kwargs["timeout"], output="secret-output")

    _configure_cli(monkeypatch, tmp_path, run)
    adapter = KaggleAcquisitionAdapter(tmp_path)
    result = adapter.download(authentication_probe=lambda _exe, _slug: True)

    assert result.status == DownloadStatus.TIMED_OUT
    assert result.diagnostic_code == "KAGGLE_DOWNLOAD_TIMEOUT"
    assert result.stdout_captured
    assert "secret-output" not in repr(result)


def test_nonzero_exit_is_classified_and_cli_output_is_withheld(
    tmp_path, monkeypatch
):
    secret = "sensitive-kaggle-token-123456789"
    calls = []

    def run(args, **kwargs):
        calls.append((tuple(args), kwargs))
        if args[-1] == "--version":
            return _completed(args, stdout="Kaggle API 1.6.17")
        return _completed(args, returncode=13, stderr=secret)

    _configure_cli(monkeypatch, tmp_path, run)
    result = KaggleAcquisitionAdapter(tmp_path).download(
        authentication_probe=lambda _exe, _slug: True
    )

    assert result.status == DownloadStatus.FAILED
    assert result.exit_code == 13
    assert result.stderr_captured
    assert secret not in repr(result)
    assert result.diagnostic_code == "KAGGLE_NONZERO_EXIT"


def test_auth_environment_variable_values_never_appear_in_results(
    tmp_path, monkeypatch
):
    secret = "never-print-this-kaggle-secret"
    monkeypatch.setenv("KAGGLE_KEY", secret)
    _configure_cli(monkeypatch, tmp_path, _successful_runner([]))

    result = KaggleAcquisitionAdapter(tmp_path).preflight()

    assert "KAGGLE_KEY" in result.authentication_hints
    assert secret not in repr(result)
    assert result.status == PreflightStatus.AUTHENTICATION_UNVERIFIED


def test_invalid_authentication_probe_blocks_download(tmp_path, monkeypatch):
    calls = []
    _configure_cli(monkeypatch, tmp_path, _successful_runner(calls))

    result = KaggleAcquisitionAdapter(tmp_path).download(
        authentication_probe=lambda _exe, _slug: False
    )

    assert result.status == DownloadStatus.BLOCKED
    assert result.preflight.status == PreflightStatus.AUTHENTICATION_UNAVAILABLE
    assert not any(call[0][1:3] == ("competitions", "download") for call in calls)


def test_inventory_hashes_files_and_does_not_execute_them(tmp_path, monkeypatch):
    adapter, result, _ = _successful_download(monkeypatch, tmp_path)
    assert result.staging_directory is not None
    payload = b"print('this file is never executed')"
    script = result.staging_directory / "possible_verifier.py"
    script.write_bytes(payload)

    inventory = adapter.inventory(result)

    assert len(inventory.files) == 1
    item = inventory.files[0]
    assert item.relative_path == "possible_verifier.py"
    assert item.original_filename == "possible_verifier.py"
    assert item.size_bytes == len(payload)
    assert item.sha256 == hashlib.sha256(payload).hexdigest()
    assert item.readable
    assert item.archive_status == ArchiveStatus.NOT_ARCHIVE
    assert item.provenance_status == ProvenanceStatus.OFFICIAL_SOURCE_UNVERIFIED
    assert script.read_bytes() == payload


def test_inventory_rejects_symlinks(tmp_path, monkeypatch):
    adapter, result, _ = _successful_download(monkeypatch, tmp_path)
    assert result.staging_directory is not None
    linked = result.staging_directory / "linked.bin"
    linked.write_bytes(b"payload")
    is_link = Path.is_symlink
    monkeypatch.setattr(
        Path,
        "is_symlink",
        lambda path: path == linked or is_link(path),
    )

    with pytest.raises(AcquisitionError, match="Symbolic links"):
        adapter.inventory(result)


def test_inventory_rejects_unexpected_filesystem_objects(tmp_path, monkeypatch):
    adapter, result, _ = _successful_download(monkeypatch, tmp_path)
    assert result.staging_directory is not None
    special = result.staging_directory / "unexpected"
    special.write_bytes(b"placeholder")
    original_lstat = Path.lstat
    monkeypatch.setattr(
        Path,
        "lstat",
        lambda path: os.stat_result(
            (stat.S_IFIFO | 0o600, 0, 0, 1, 0, 0, 0, 0, 0, 0)
        )
        if path == special
        else original_lstat(path),
    )
    monkeypatch.setattr(
        "invsqrt_opt.kaggle_acquisition._is_link_or_junction",
        lambda _path: False,
    )

    with pytest.raises(AcquisitionError, match="non-regular"):
        adapter.inventory(result)


@pytest.mark.parametrize(
    "unsafe_member",
    ("../outside.py", "C:/outside.py", "C:outside.py", "/rooted.py", "a/../b.py"),
)
def test_archive_inventory_detects_unsafe_paths(
    tmp_path, monkeypatch, unsafe_member
):
    adapter, result, _ = _successful_download(monkeypatch, tmp_path)
    assert result.staging_directory is not None
    archive_path = result.staging_directory / "bundle.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(unsafe_member, b"unsafe")

    inventory = adapter.inventory(result)

    archive_item = inventory.files[0]
    assert archive_item.archive_status == ArchiveStatus.UNSAFE
    assert archive_item.archive_members == ()


def test_inventory_rejects_oversized_staged_file(tmp_path, monkeypatch):
    adapter, result, _ = _successful_download(
        monkeypatch,
        tmp_path,
        limits=AcquisitionLimits(max_file_bytes=4),
    )
    assert result.staging_directory is not None
    (result.staging_directory / "too-large.bin").write_bytes(b"12345")

    with pytest.raises(AcquisitionError, match="size limit"):
        adapter.inventory(result)


def test_archive_inventory_detects_duplicate_member_paths(tmp_path, monkeypatch):
    adapter, result, _ = _successful_download(monkeypatch, tmp_path)
    assert result.staging_directory is not None
    archive_path = result.staging_directory / "bundle.zip"
    with pytest.warns(UserWarning):
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("a/file.bin", b"first")
            archive.writestr("a/file.bin", b"second")

    item = adapter.inventory(result).files[0]

    assert item.archive_status == ArchiveStatus.UNSAFE
    assert item.archive_members == ()


def test_archive_inventory_rejects_symlink_members(tmp_path, monkeypatch):
    adapter, result, _ = _successful_download(monkeypatch, tmp_path)
    assert result.staging_directory is not None
    archive_path = result.staging_directory / "bundle.zip"
    link = zipfile.ZipInfo("link.py")
    link.create_system = 3
    link.external_attr = (stat.S_IFLNK | 0o777) << 16
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr(link, "target.py")

    item = adapter.inventory(result).files[0]

    assert item.archive_status == ArchiveStatus.UNSAFE


def test_archive_inventory_enforces_size_and_member_limits(tmp_path, monkeypatch):
    adapter, result, _ = _successful_download(
        monkeypatch,
        tmp_path,
        limits=AcquisitionLimits(
            max_file_bytes=1024,
            max_archive_members=1,
            max_archive_uncompressed_bytes=128,
        ),
    )
    assert result.staging_directory is not None
    archive_path = result.staging_directory / "bundle.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("one.txt", b"1")
        archive.writestr("two.txt", b"2")

    item = adapter.inventory(result).files[0]

    assert item.archive_status == ArchiveStatus.TOO_LARGE


def test_explicit_member_extraction_is_confined_and_not_automatic(
    tmp_path, monkeypatch
):
    adapter, result, _ = _successful_download(monkeypatch, tmp_path)
    assert result.staging_directory is not None
    archive_path = result.staging_directory / "bundle.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("verifiers/check.py", b"pass")
        archive.writestr("ignored.txt", b"not selected")

    assert adapter.inventory(result).files[0].archive_status == ArchiveStatus.SAFE
    destination = result.staging_directory / "selected"
    extracted = adapter.extract_archive_members(
        result,
        "bundle.zip",
        ("verifiers/check.py",),
        destination_directory=destination,
    )

    assert len(extracted) == 1
    assert extracted[0].staged_path.read_bytes() == b"pass"
    assert extracted[0].source_archive_path == "bundle.zip"
    assert extracted[0].archive_member_path == "verifiers/check.py"
    assert not (destination / "ignored.txt").exists()
    assert not (tmp_path / "outside.py").exists()


def test_explicit_extraction_rejects_traversal_and_existing_destination(
    tmp_path, monkeypatch
):
    adapter, result, _ = _successful_download(monkeypatch, tmp_path)
    assert result.staging_directory is not None
    archive_path = result.staging_directory / "bundle.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("safe.txt", b"safe")

    with pytest.raises(ExtractionError, match="outside"):
        adapter.extract_archive_members(
            result,
            "bundle.zip",
            ("safe.txt",),
            destination_directory=tmp_path / "outside",
        )
    existing = result.staging_directory / "existing"
    existing.mkdir()
    with pytest.raises(ExtractionError, match="already exists"):
        adapter.extract_archive_members(
            result,
            "bundle.zip",
            ("safe.txt",),
            destination_directory=existing,
        )


def test_explicit_extraction_rejects_unsafe_archive_members(tmp_path, monkeypatch):
    adapter, result, _ = _successful_download(monkeypatch, tmp_path)
    assert result.staging_directory is not None
    archive_path = result.staging_directory / "bundle.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("../escape.py", b"pass")

    with pytest.raises(ExtractionError, match="not safe"):
        adapter.extract_archive_members(
            result,
            "bundle.zip",
            ("../escape.py",),
            destination_directory=result.staging_directory / "selected",
        )


def test_role_mapping_reports_missing_and_ambiguous_candidates(tmp_path):
    adapter = KaggleAcquisitionAdapter(tmp_path)
    mapping = adapter.map_artifact_roles(
        ("a.py", "b.py"),
        {
            "official_verifier": ("a.py", "b.py"),
            "reference_circuit": ("missing.py",),
        },
    )

    assert mapping.for_role("official_verifier").status == RoleMappingStatus.AMBIGUOUS
    assert mapping.for_role("reference_circuit").status == RoleMappingStatus.MISSING
    assert mapping.for_role("sample_submission").status == RoleMappingStatus.MISSING
    assert not mapping.complete_required_roles


def test_role_mapping_does_not_allow_one_file_to_fill_two_roles(tmp_path):
    mapping = KaggleAcquisitionAdapter(tmp_path).map_artifact_roles(
        ("same.bin",),
        {
            "official_verifier": ("same.bin",),
            "reference_circuit": ("same.bin",),
        },
    )

    assert mapping.for_role("official_verifier").status == RoleMappingStatus.AMBIGUOUS
    assert mapping.for_role("reference_circuit").status == RoleMappingStatus.AMBIGUOUS


def test_role_mapping_rejects_unverified_paths_and_unknown_roles(tmp_path):
    adapter = KaggleAcquisitionAdapter(tmp_path)
    with pytest.raises(ValueError, match="Unknown artifact roles"):
        adapter.map_artifact_roles((), {"untrusted": ("x",)})
    with pytest.raises(ValueError):
        adapter.map_artifact_roles((), {"official_verifier": ("../escape.py",)})


def test_download_command_rejects_arbitrary_executable(tmp_path, monkeypatch):
    executable = tmp_path / "other.exe"
    executable.write_bytes(b"not the kaggle CLI")
    adapter = KaggleAcquisitionAdapter(tmp_path)
    staging = adapter.staging_root
    staging.mkdir(parents=True)
    monkeypatch.setattr(
        "invsqrt_opt.kaggle_acquisition.shutil.which",
        lambda _: str(tmp_path / "different.exe"),
    )

    with pytest.raises(AcquisitionError, match="discovered Kaggle CLI"):
        adapter.build_download_command(executable, staging)


def test_p005_handoff_preserves_unverified_provenance_and_blocks_readiness(
    tmp_path, monkeypatch
):
    adapter, download, _ = _successful_download(monkeypatch, tmp_path)
    assert download.staging_directory is not None
    archive_path = download.staging_directory / "observed-bundle.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("observed/sample.bin", b"sample bytes")
    extracted = adapter.extract_archive_members(
        download,
        "observed-bundle.zip",
        ("observed/sample.bin",),
        destination_directory=download.staging_directory / "extracted",
    )
    inventory = adapter.inventory(download, extracted_members=extracted)
    mapping = adapter.map_artifact_roles(
        tuple(item.relative_path for item in inventory.files),
        {"sample_submission": ("extracted/observed/sample.bin",)},
    )

    manifest = adapter.handoff_to_p005(download, inventory, mapping)
    record = manifest.artifact_for_role("sample_submission")
    readiness = adapter.assess_p005_readiness(manifest)

    assert manifest.schema_version == "2"
    assert record is not None
    assert record.sha256 == hashlib.sha256(b"sample bytes").hexdigest()
    assert record.expected_sha256 is None
    assert record.provenance_status == ProvenanceStatus.OFFICIAL_SOURCE_UNVERIFIED
    assert record.authentication_evidence is None
    assert "observed-bundle.zip#observed/sample.bin" in record.provenance
    assert not readiness.ready
    assert not readiness.required_artifacts_authenticated
    assert any("not authenticated as official" in blocker for blocker in readiness.blockers)


def test_handoff_rejects_noncanonical_identity_and_non_download_results(
    tmp_path, monkeypatch
):
    adapter, download, _ = _successful_download(monkeypatch, tmp_path)
    assert download.staging_directory is not None
    inventory = adapter.inventory(download)
    missing_roles = adapter.map_artifact_roles((), {})

    blocked = download.__class__(
        status=DownloadStatus.BLOCKED,
        competition_slug=download.competition_slug,
        command=None,
        staging_directory=None,
        started_utc=download.started_utc,
        finished_utc=download.finished_utc,
        exit_code=None,
        stdout_captured=False,
        stderr_captured=False,
        diagnostic_code="test-only",
        preflight=download.preflight,
    )
    with pytest.raises(AcquisitionError, match="successful download"):
        adapter.handoff_to_p005(blocked, inventory, missing_roles)

    forged_inventory = inventory.__class__(
        staging_directory=inventory.staging_directory,
        files=inventory.files,
        source_competition_slug="another-competition",
        retrieved_utc=inventory.retrieved_utc,
        download_status=inventory.download_status,
    )
    with pytest.raises(AcquisitionError, match="source identity"):
        adapter.handoff_to_p005(download, forged_inventory, missing_roles)


def test_inventory_rejects_failed_download_results(tmp_path):
    adapter = KaggleAcquisitionAdapter(tmp_path)
    failed = type("Failed", (), {"status": DownloadStatus.FAILED})()

    with pytest.raises(AcquisitionError, match="Only a successful"):
        adapter.inventory(failed)


def test_cli_failure_does_not_trigger_automatic_retry(tmp_path, monkeypatch):
    calls = []

    def run(args, **kwargs):
        calls.append(tuple(args))
        if args[-1] == "--version":
            return _completed(args, stdout="Kaggle API 1.6.17")
        return _completed(args, returncode=7, stderr="failure")

    _configure_cli(monkeypatch, tmp_path, run)
    result = KaggleAcquisitionAdapter(tmp_path).download(
        authentication_probe=lambda _exe, _slug: True
    )

    assert result.status == DownloadStatus.FAILED
    assert sum(args[1:3] == ("competitions", "download") for args in calls) == 1


def test_download_output_directory_is_created_only_after_ready_preflight(
    tmp_path, monkeypatch
):
    calls = []
    _configure_cli(monkeypatch, tmp_path, _successful_runner(calls))
    adapter = KaggleAcquisitionAdapter(tmp_path)

    result = adapter.download()

    assert result.status == DownloadStatus.BLOCKED
    assert not adapter.staging_root.exists()
    assert all(args[0][1] == "--version" for args in calls)


def test_verified_identity_constants_and_timestamp_format():
    assert VERIFIED_COMPETITION_SLUG == (
        "google-verifiable-quantum-circuit-compilation"
    )
    timestamp = datetime.now(timezone.utc).isoformat()
    assert datetime.fromisoformat(timestamp).tzinfo is not None
