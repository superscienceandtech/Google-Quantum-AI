from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import hashlib
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import stat
import subprocess
import tarfile
from typing import BinaryIO, Iterable, Mapping, Protocol, Sequence
import uuid
import zipfile

from .artifacts import (
    ArtifactDeclaration,
    ArtifactManifest,
    ProvenanceStatus,
    assess_adapter_readiness,
)


VERIFIED_COMPETITION_TITLE = (
    "Google Quantum AI - Verifiable Quantum Circuit Compilation"
)
VERIFIED_COMPETITION_SLUG = "google-verifiable-quantum-circuit-compilation"
VERIFIED_COMPETITION_URL = (
    "https://www.kaggle.com/competitions/"
    "google-verifiable-quantum-circuit-compilation"
)
STAGING_RELATIVE_PATH = Path("external/acquisition-staging/invsqrt")
AUTH_ENVIRONMENT_VARIABLE_NAMES = (
    "KAGGLE_USERNAME",
    "KAGGLE_KEY",
    "KAGGLE_API_TOKEN",
)
REQUIRED_ARTIFACT_ROLES = (
    "official_verifier",
    "reference_circuit",
    "sample_submission",
    "official_scoring",
)
KNOWN_ARTIFACT_ROLES = REQUIRED_ARTIFACT_ROLES + (
    "competition_metadata",
    "runtime_specification",
    "sdk_library",
)

_ARTIFACT_IDS = {
    "official_verifier": "invsqrt-official-verifier",
    "reference_circuit": "invsqrt-reference-circuit",
    "sample_submission": "invsqrt-sample-submission",
    "official_scoring": "invsqrt-official-scoring",
    "competition_metadata": "invsqrt-competition-metadata",
    "runtime_specification": "invsqrt-runtime-specification",
    "sdk_library": "invsqrt-kickmix-library",
}


class PreflightStatus(str, Enum):
    READY = "READY"
    KAGGLE_CLI_MISSING = "KAGGLE_CLI_MISSING"
    AUTHENTICATION_UNAVAILABLE = "AUTHENTICATION_UNAVAILABLE"
    AUTHENTICATION_UNVERIFIED = "AUTHENTICATION_UNVERIFIED"
    COMPETITION_IDENTITY_UNVERIFIED = "COMPETITION_IDENTITY_UNVERIFIED"
    OUTPUT_PATH_INVALID = "OUTPUT_PATH_INVALID"
    DEPENDENCY_UNAVAILABLE = "DEPENDENCY_UNAVAILABLE"
    PREFLIGHT_FAILED = "PREFLIGHT_FAILED"


class DownloadStatus(str, Enum):
    SUCCEEDED = "SUCCEEDED"
    BLOCKED = "BLOCKED"
    TIMED_OUT = "TIMED_OUT"
    FAILED = "FAILED"


class ArchiveStatus(str, Enum):
    NOT_ARCHIVE = "NOT_ARCHIVE"
    SAFE = "SAFE"
    UNSAFE = "UNSAFE"
    TOO_LARGE = "TOO_LARGE"
    UNREADABLE = "UNREADABLE"


class RoleMappingStatus(str, Enum):
    MAPPED = "MAPPED"
    MISSING = "MISSING"
    AMBIGUOUS = "AMBIGUOUS"


class AuthenticationProbe(Protocol):
    def __call__(self, executable: Path, competition_slug: str) -> bool:
        """Return true only after a separately vetted read-only auth check."""
        ...


@dataclass(frozen=True)
class AcquisitionLimits:
    timeout_seconds: float = 600
    version_timeout_seconds: float = 5
    max_file_bytes: int = 1024 * 1024 * 1024
    max_archive_members: int = 100_000
    max_archive_uncompressed_bytes: int = 2 * 1024 * 1024 * 1024

    def __post_init__(self) -> None:
        if self.timeout_seconds <= 0 or self.version_timeout_seconds <= 0:
            raise ValueError("Subprocess timeouts must be positive")
        if self.max_file_bytes <= 0:
            raise ValueError("max_file_bytes must be positive")
        if self.max_archive_members <= 0:
            raise ValueError("max_archive_members must be positive")
        if self.max_archive_uncompressed_bytes <= 0:
            raise ValueError("max_archive_uncompressed_bytes must be positive")


@dataclass(frozen=True)
class PreflightResult:
    status: PreflightStatus
    competition_slug: str
    output_directory: Path | None
    executable_path: Path | None
    cli_version: str | None
    authentication_configuration_detected: bool
    authentication_verified: bool
    authentication_hints: tuple[str, ...]
    blockers: tuple[str, ...] = ()
    diagnostic_code: str | None = None

    @property
    def ready(self) -> bool:
        return self.status == PreflightStatus.READY


@dataclass(frozen=True)
class DownloadResult:
    status: DownloadStatus
    competition_slug: str
    command: tuple[str, ...] | None
    staging_directory: Path | None
    started_utc: str
    finished_utc: str
    exit_code: int | None
    stdout_captured: bool
    stderr_captured: bool
    diagnostic_code: str | None
    preflight: PreflightResult


@dataclass(frozen=True)
class ArchiveMember:
    relative_path: str
    size_bytes: int
    kind: str


@dataclass(frozen=True)
class ArchiveInventory:
    status: ArchiveStatus
    archive_type: str | None
    members: tuple[ArchiveMember, ...] = ()
    diagnostic_code: str | None = None


@dataclass(frozen=True)
class FileInventoryItem:
    relative_path: str
    original_filename: str
    size_bytes: int
    sha256: str
    readable: bool
    file_type: str
    archive_status: ArchiveStatus
    archive_type: str | None
    archive_members: tuple[ArchiveMember, ...]
    source_competition_slug: str
    retrieved_utc: str
    download_status: DownloadStatus
    provenance_status: ProvenanceStatus
    source_archive_path: str | None = None
    archive_member_path: str | None = None


@dataclass(frozen=True)
class ExtractedArchiveMember:
    source_archive_path: str
    archive_member_path: str
    staged_relative_path: str
    staged_path: Path


@dataclass(frozen=True)
class AcquisitionInventory:
    staging_directory: Path
    files: tuple[FileInventoryItem, ...]
    source_competition_slug: str
    retrieved_utc: str
    download_status: DownloadStatus


@dataclass(frozen=True)
class ArtifactRoleMapping:
    role: str
    status: RoleMappingStatus
    candidate_paths: tuple[str, ...]
    selected_path: str | None


@dataclass(frozen=True)
class ArtifactRoleMappingResult:
    roles: tuple[ArtifactRoleMapping, ...]

    def for_role(self, role: str) -> ArtifactRoleMapping:
        for item in self.roles:
            if item.role == role:
                return item
        raise KeyError(role)

    @property
    def complete_required_roles(self) -> bool:
        return all(
            self.for_role(role).status == RoleMappingStatus.MAPPED
            for role in REQUIRED_ARTIFACT_ROLES
        )


class AcquisitionError(ValueError):
    """Raised when an acquisition or staging path fails a security check."""


class ArchiveSafetyError(ValueError):
    """Raised when an archive contains unsafe or ambiguous members."""


class ExtractionError(ValueError):
    """Raised when an explicitly requested safe extraction cannot complete."""


class KaggleAcquisitionAdapter:
    """Fail-closed Kaggle CLI adapter for staging competition downloads."""

    def __init__(
        self,
        repository_root: str | Path,
        *,
        limits: AcquisitionLimits | None = None,
    ) -> None:
        self.repository_root = Path(repository_root).resolve()
        if not self.repository_root.is_dir():
            raise ValueError("repository_root must be an existing directory")
        self.staging_root = self.repository_root / STAGING_RELATIVE_PATH
        self.limits = limits or AcquisitionLimits()

    def preflight(
        self,
        *,
        competition_slug: str = VERIFIED_COMPETITION_SLUG,
        output_directory: str | Path | None = None,
        authentication_probe: AuthenticationProbe | None = None,
    ) -> PreflightResult:
        if competition_slug != VERIFIED_COMPETITION_SLUG:
            return self._preflight_result(
                PreflightStatus.COMPETITION_IDENTITY_UNVERIFIED,
                competition_slug,
                None,
                blockers=("Competition slug is not the P014-verified identity",),
                diagnostic_code="UNVERIFIED_COMPETITION_SLUG",
            )

        try:
            output_path = self._validate_output_directory(output_directory)
        except AcquisitionError:
            return self._preflight_result(
                PreflightStatus.OUTPUT_PATH_INVALID,
                competition_slug,
                None,
                blockers=("Output path must remain inside the approved staging area",),
                diagnostic_code="INVALID_OUTPUT_PATH",
            )

        discovered = shutil.which("kaggle")
        if discovered is None:
            return self._preflight_result(
                PreflightStatus.KAGGLE_CLI_MISSING,
                competition_slug,
                output_path,
                blockers=("Kaggle CLI executable was not found",),
                diagnostic_code="KAGGLE_CLI_NOT_FOUND",
            )
        executable = Path(discovered).resolve()
        if not executable.is_file():
            return self._preflight_result(
                PreflightStatus.PREFLIGHT_FAILED,
                competition_slug,
                output_path,
                executable_path=executable,
                blockers=("Discovered Kaggle CLI is not a regular file",),
                diagnostic_code="INVALID_KAGGLE_EXECUTABLE",
            )

        version, version_error = self._read_cli_version(executable)
        if version_error is not None:
            return self._preflight_result(
                PreflightStatus.PREFLIGHT_FAILED,
                competition_slug,
                output_path,
                executable_path=executable,
                blockers=("Kaggle CLI version could not be established",),
                diagnostic_code=version_error,
            )

        hints = _authentication_hints()
        if authentication_probe is None:
            if not hints:
                return self._preflight_result(
                    PreflightStatus.AUTHENTICATION_UNAVAILABLE,
                    competition_slug,
                    output_path,
                    executable_path=executable,
                    cli_version=version,
                    authentication_hints=hints,
                    blockers=("No Kaggle authentication configuration was detected",),
                    diagnostic_code="AUTHENTICATION_CONFIGURATION_MISSING",
                )
            return self._preflight_result(
                PreflightStatus.AUTHENTICATION_UNVERIFIED,
                competition_slug,
                output_path,
                executable_path=executable,
                cli_version=version,
                authentication_hints=hints,
                blockers=(
                    "Authentication configuration presence does not establish access",
                    "No vetted read-only authentication check was supplied",
                ),
                diagnostic_code="AUTHENTICATION_NOT_VERIFIED",
            )

        if not authentication_probe(executable, competition_slug):
            return self._preflight_result(
                PreflightStatus.AUTHENTICATION_UNAVAILABLE,
                competition_slug,
                output_path,
                executable_path=executable,
                cli_version=version,
                authentication_hints=hints,
                blockers=("The supplied authentication check did not confirm access",),
                diagnostic_code="AUTHENTICATION_CHECK_FAILED",
            )

        return self._preflight_result(
            PreflightStatus.READY,
            competition_slug,
            output_path,
            executable_path=executable,
            cli_version=version,
            authentication_hints=hints,
            authentication_verified=True,
        )

    def build_download_command(
        self,
        executable: str | Path,
        staging_directory: str | Path,
        *,
        competition_slug: str = VERIFIED_COMPETITION_SLUG,
    ) -> tuple[str, ...]:
        if competition_slug != VERIFIED_COMPETITION_SLUG:
            raise AcquisitionError("Competition slug is not P014-verified")
        executable_path = Path(executable).resolve()
        discovered = shutil.which("kaggle")
        if discovered is None or executable_path != Path(discovered).resolve():
            raise AcquisitionError("Executable is not the discovered Kaggle CLI")
        if not executable_path.is_file():
            raise AcquisitionError("Kaggle CLI executable is not a regular file")
        staging_path = self._validate_output_directory(staging_directory)
        if not staging_path.is_dir():
            raise AcquisitionError("Staging directory must exist before command construction")
        return (
            str(executable_path),
            "competitions",
            "download",
            "-c",
            VERIFIED_COMPETITION_SLUG,
            "-p",
            str(staging_path),
        )

    def download(
        self,
        *,
        competition_slug: str = VERIFIED_COMPETITION_SLUG,
        output_directory: str | Path | None = None,
        authentication_probe: AuthenticationProbe | None = None,
    ) -> DownloadResult:
        started = _utc_now()
        preflight = self.preflight(
            competition_slug=competition_slug,
            output_directory=output_directory,
            authentication_probe=authentication_probe,
        )
        if not preflight.ready or preflight.executable_path is None:
            return DownloadResult(
                status=DownloadStatus.BLOCKED,
                competition_slug=competition_slug,
                command=None,
                staging_directory=None,
                started_utc=started,
                finished_utc=_utc_now(),
                exit_code=None,
                stdout_captured=False,
                stderr_captured=False,
                diagnostic_code=preflight.diagnostic_code or "PREFLIGHT_BLOCKED",
                preflight=preflight,
            )

        if preflight.output_directory is None:
            return DownloadResult(
                status=DownloadStatus.BLOCKED,
                competition_slug=competition_slug,
                command=None,
                staging_directory=None,
                started_utc=started,
                finished_utc=_utc_now(),
                exit_code=None,
                stdout_captured=False,
                stderr_captured=False,
                diagnostic_code="PREFLIGHT_OUTPUT_PATH_MISSING",
                preflight=preflight,
            )
        run_directory = self._create_run_directory(preflight.output_directory)
        command = self.build_download_command(
            preflight.executable_path,
            run_directory,
            competition_slug=competition_slug,
        )
        try:
            completed = subprocess.run(
                command,
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.limits.timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            return DownloadResult(
                status=DownloadStatus.TIMED_OUT,
                competition_slug=competition_slug,
                command=command,
                staging_directory=run_directory,
                started_utc=started,
                finished_utc=_utc_now(),
                exit_code=None,
                stdout_captured=exc.stdout is not None,
                stderr_captured=exc.stderr is not None,
                diagnostic_code="KAGGLE_DOWNLOAD_TIMEOUT",
                preflight=preflight,
            )
        except OSError as exc:
            return DownloadResult(
                status=DownloadStatus.FAILED,
                competition_slug=competition_slug,
                command=command,
                staging_directory=run_directory,
                started_utc=started,
                finished_utc=_utc_now(),
                exit_code=None,
                stdout_captured=False,
                stderr_captured=False,
                diagnostic_code=f"KAGGLE_PROCESS_{type(exc).__name__.upper()}",
                preflight=preflight,
            )

        return DownloadResult(
            status=(
                DownloadStatus.SUCCEEDED
                if completed.returncode == 0
                else DownloadStatus.FAILED
            ),
            competition_slug=competition_slug,
            command=command,
            staging_directory=run_directory,
            started_utc=started,
            finished_utc=_utc_now(),
            exit_code=completed.returncode,
            stdout_captured=bool(completed.stdout),
            stderr_captured=bool(completed.stderr),
            diagnostic_code=(
                None if completed.returncode == 0 else "KAGGLE_NONZERO_EXIT"
            ),
            preflight=preflight,
        )

    def inventory(
        self,
        download: DownloadResult,
        *,
        extracted_members: Sequence[ExtractedArchiveMember] = (),
    ) -> AcquisitionInventory:
        if download.status != DownloadStatus.SUCCEEDED:
            raise AcquisitionError("Only a successful download can be inventoried")
        if download.competition_slug != VERIFIED_COMPETITION_SLUG:
            raise AcquisitionError("Download competition identity is not verified")
        if download.staging_directory is None:
            raise AcquisitionError("Download result has no staging directory")
        staging = _validate_staging_path(
            self.repository_root,
            self.staging_root,
            download.staging_directory,
        )
        files = _inventory_tree(staging, self.limits)
        retrieved = download.finished_utc
        files_by_path = {row[0].casefold(): row for row in files}
        extraction_by_path = {
            _normalize_archive_path(item.staged_relative_path).casefold(): item
            for item in extracted_members
        }
        if len(extraction_by_path) != len(extracted_members):
            raise AcquisitionError("Extraction evidence contains duplicate staged paths")
        for item in extracted_members:
            archive_path = _normalize_archive_path(item.source_archive_path)
            member_path = _normalize_archive_path(item.archive_member_path)
            staged_path = _normalize_archive_path(item.staged_relative_path)
            archive_row = files_by_path.get(archive_path.casefold())
            staged_row = files_by_path.get(staged_path.casefold())
            if (
                archive_row is None
                or archive_row[4].status != ArchiveStatus.SAFE
                or staged_row is None
                or not any(
                    member.relative_path.casefold() == member_path.casefold()
                    and member.kind == "file"
                    for member in archive_row[4].members
                )
                or item.staged_path.resolve(strict=False)
                != staging.joinpath(*PurePosixPath(staged_path).parts).resolve(
                    strict=False
                )
            ):
                raise AcquisitionError("Extraction evidence does not match staged inventory")
        return AcquisitionInventory(
            staging_directory=staging,
            files=tuple(
                FileInventoryItem(
                    relative_path=path,
                    original_filename=PurePosixPath(path).name,
                    size_bytes=size,
                    sha256=digest,
                    readable=True,
                    file_type=file_type,
                    archive_status=archive.status,
                    archive_type=archive.archive_type,
                    archive_members=archive.members,
                    source_competition_slug=download.competition_slug,
                    retrieved_utc=retrieved,
                    download_status=download.status,
                    provenance_status=ProvenanceStatus.OFFICIAL_SOURCE_UNVERIFIED,
                    source_archive_path=(
                        extraction_by_path[path.casefold()].source_archive_path
                        if path.casefold() in extraction_by_path
                        else None
                    ),
                    archive_member_path=(
                        extraction_by_path[path.casefold()].archive_member_path
                        if path.casefold() in extraction_by_path
                        else None
                    ),
                )
                for path, size, digest, file_type, archive in files
            ),
            source_competition_slug=download.competition_slug,
            retrieved_utc=retrieved,
            download_status=download.status,
        )

    def extract_archive_members(
        self,
        download: DownloadResult,
        archive_relative_path: str,
        member_paths: Sequence[str],
        *,
        destination_directory: str | Path,
    ) -> tuple[ExtractedArchiveMember, ...]:
        """Explicitly extract selected safe regular members; never called by download()."""
        if download.status != DownloadStatus.SUCCEEDED or download.staging_directory is None:
            raise ExtractionError("A successful staged download is required")
        staging = _validate_staging_path(
            self.repository_root,
            self.staging_root,
            download.staging_directory,
        )
        archive_path = _resolve_existing_file(staging, archive_relative_path)
        archive_inventory = _inspect_archive(archive_path, self.limits)
        if archive_inventory.status != ArchiveStatus.SAFE:
            raise ExtractionError("Archive is not safe for selected-member extraction")

        try:
            normalized_members = tuple(
                _normalize_archive_path(path) for path in member_paths
            )
        except ArchiveSafetyError as exc:
            raise ExtractionError("Selected member path is unsafe") from exc
        if len(set(path.casefold() for path in normalized_members)) != len(normalized_members):
            raise ExtractionError("Selected archive members contain duplicates")
        available = {
            member.relative_path.casefold(): member
            for member in archive_inventory.members
            if member.kind == "file"
        }
        if any(path.casefold() not in available for path in normalized_members):
            raise ExtractionError("Selected path is not a regular archive member")

        try:
            destination = _validate_staging_path(
                self.repository_root,
                self.staging_root,
                destination_directory,
            )
        except AcquisitionError as exc:
            raise ExtractionError("Extraction destination is outside approved staging") from exc
        if destination.exists():
            raise ExtractionError("Extraction destination already exists")
        _create_directory_chain(self.repository_root, destination)
        extracted: list[ExtractedArchiveMember] = []
        for member_path in normalized_members:
            member = available[member_path.casefold()]
            target = destination.joinpath(*PurePosixPath(member.relative_path).parts)
            _create_directory_chain(destination, target.parent)
            if target.exists() or _is_link_or_junction(target):
                raise ExtractionError("Extraction would overwrite an existing path")
            try:
                with _open_archive_member(archive_path, archive_inventory, member_path) as source:
                    _copy_member_exclusive(
                        source,
                        target,
                        expected_size=member.size_bytes,
                        max_bytes=self.limits.max_file_bytes,
                    )
            except (OSError, tarfile.TarError, zipfile.BadZipFile) as exc:
                raise ExtractionError(
                    f"Archive member extraction failed ({type(exc).__name__})"
                ) from exc
            extracted.append(
                ExtractedArchiveMember(
                    source_archive_path=archive_path.relative_to(staging).as_posix(),
                    archive_member_path=member.relative_path,
                    staged_relative_path=target.relative_to(staging).as_posix(),
                    staged_path=target,
                )
            )
        return tuple(extracted)

    def map_artifact_roles(
        self,
        observed_paths: Iterable[str],
        evidence_mapping: Mapping[str, Sequence[str]],
    ) -> ArtifactRoleMappingResult:
        observed = {_normalize_archive_path(path).casefold() for path in observed_paths}
        unknown_roles = set(evidence_mapping).difference(KNOWN_ARTIFACT_ROLES)
        if unknown_roles:
            raise ValueError(f"Unknown artifact roles: {', '.join(sorted(unknown_roles))}")

        results: list[ArtifactRoleMapping] = []
        for role in KNOWN_ARTIFACT_ROLES:
            candidates = tuple(
                _normalize_archive_path(path)
                for path in evidence_mapping.get(role, ())
            )
            matches = tuple(
                path for path in candidates if path.casefold() in observed
            )
            if len(matches) == 1:
                status = RoleMappingStatus.MAPPED
                selected = matches[0]
            elif len(matches) > 1:
                status = RoleMappingStatus.AMBIGUOUS
                selected = None
            else:
                status = RoleMappingStatus.MISSING
                selected = None
            results.append(
                ArtifactRoleMapping(
                    role=role,
                    status=status,
                    candidate_paths=candidates,
                    selected_path=selected,
                )
            )

        selected_paths: dict[str, list[int]] = {}
        for index, item in enumerate(results):
            if item.selected_path is not None:
                selected_paths.setdefault(item.selected_path.casefold(), []).append(index)
        for indexes in selected_paths.values():
            if len(indexes) > 1:
                for index in indexes:
                    item = results[index]
                    results[index] = ArtifactRoleMapping(
                        role=item.role,
                        status=RoleMappingStatus.AMBIGUOUS,
                        candidate_paths=item.candidate_paths,
                        selected_path=None,
                    )
        return ArtifactRoleMappingResult(tuple(results))

    def handoff_to_p005(
        self,
        download: DownloadResult,
        inventory: AcquisitionInventory,
        role_mapping: ArtifactRoleMappingResult,
    ) -> ArtifactManifest:
        if download.status != DownloadStatus.SUCCEEDED:
            raise AcquisitionError("A successful download is required for P005 handoff")
        if inventory.staging_directory != download.staging_directory:
            raise AcquisitionError("Inventory and download staging paths do not match")
        if inventory.download_status != DownloadStatus.SUCCEEDED:
            raise AcquisitionError("Inventory does not record a successful download")
        if inventory.source_competition_slug != VERIFIED_COMPETITION_SLUG:
            raise AcquisitionError("Inventory source identity is not verified")
        _validate_staging_path(
            self.repository_root,
            self.staging_root,
            inventory.staging_directory,
        )
        mapped_roles = [item.role for item in role_mapping.roles]
        if len(mapped_roles) != len(set(mapped_roles)):
            raise AcquisitionError("Role mapping contains duplicate roles")
        if any(role not in KNOWN_ARTIFACT_ROLES for role in mapped_roles):
            raise AcquisitionError("Role mapping contains an unknown artifact role")
        available_files = {
            item.relative_path.casefold()
            for item in inventory.files
            if item.archive_status == ArchiveStatus.NOT_ARCHIVE
            and item.readable
        }
        declarations: list[ArtifactDeclaration] = []
        for item in role_mapping.roles:
            if item.status != RoleMappingStatus.MAPPED or item.selected_path is None:
                continue
            if item.selected_path.casefold() not in available_files:
                raise AcquisitionError("Mapped artifact is not an inventoried staged file")
            declarations.append(
                ArtifactDeclaration(
                    role=item.role,
                    relative_path=item.selected_path,
                    provenance=(
                        f"P015 Kaggle CLI download; source slug "
                        f"{VERIFIED_COMPETITION_SLUG}; retrieved {inventory.retrieved_utc}; "
                        f"archive={_archive_provenance(item.selected_path, inventory)}; "
                        "artifact role identity remains unverified"
                    ),
                    version=download.preflight.cli_version,
                    artifact_id=_ARTIFACT_IDS[item.role],
                    source_identity=VERIFIED_COMPETITION_SLUG,
                    source_url=VERIFIED_COMPETITION_URL,
                    authentication_evidence=None,
                    provenance_status=ProvenanceStatus.OFFICIAL_SOURCE_UNVERIFIED,
                )
            )
        if not declarations:
            raise AcquisitionError(
                "P005 handoff requires at least one explicitly mapped artifact"
            )
        return ArtifactManifest.discover(
            self.repository_root,
            artifact_root=inventory.staging_directory,
            declarations=tuple(declarations),
        )

    def assess_p005_readiness(self, manifest: ArtifactManifest):
        return assess_adapter_readiness(manifest)

    def _read_cli_version(self, executable: Path) -> tuple[str | None, str | None]:
        try:
            completed = subprocess.run(
                (str(executable), "--version"),
                shell=False,
                check=False,
                capture_output=True,
                text=True,
                timeout=self.limits.version_timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return None, "KAGGLE_VERSION_TIMEOUT"
        except OSError as exc:
            return None, f"KAGGLE_VERSION_{type(exc).__name__.upper()}"
        if completed.returncode != 0:
            return None, "KAGGLE_VERSION_NONZERO_EXIT"
        output = "\n".join(
            value for value in (completed.stdout, completed.stderr) if value
        )
        version_patterns = (
            r"\s*Kaggle(?: API)?\s+(\d+\.\d+(?:\.\d+){0,2}(?:[-+][A-Za-z0-9.]+)?)\s*",
            r"\s*kaggle,\s+version\s+(\d+\.\d+(?:\.\d+){0,2}(?:[-+][A-Za-z0-9.]+)?)\s*",
        )
        for line in output.splitlines():
            for pattern in version_patterns:
                match = re.fullmatch(pattern, line, flags=re.IGNORECASE)
                if match is not None:
                    return match.group(1), None
        return None, None

    def _validate_output_directory(
        self,
        output_directory: str | Path | None,
    ) -> Path:
        requested = (
            self.staging_root
            if output_directory is None
            else Path(output_directory)
        )
        if not requested.is_absolute():
            requested = self.repository_root / requested
        if ".." in requested.parts:
            raise AcquisitionError("Output path cannot contain parent traversal")
        resolved = requested.resolve(strict=False)
        approved = self.staging_root.resolve(strict=False)
        try:
            relative = resolved.relative_to(approved)
        except ValueError as exc:
            raise AcquisitionError("Output path is outside approved staging") from exc
        if not relative.parts and resolved != approved:
            raise AcquisitionError("Invalid staging root")
        _reject_link_components(self.repository_root, requested)
        if resolved.exists() and not resolved.is_dir():
            raise AcquisitionError("Output path exists and is not a directory")
        return resolved

    def _create_run_directory(self, output_directory: Path) -> Path:
        base = self._validate_output_directory(output_directory)
        _create_directory_chain(self.repository_root, base)
        run_directory = base / uuid.uuid4().hex
        run_directory.mkdir()
        _reject_link_components(self.repository_root, run_directory)
        return run_directory

    def _preflight_result(
        self,
        status: PreflightStatus,
        competition_slug: str,
        output_directory: Path | None,
        *,
        executable_path: Path | None = None,
        cli_version: str | None = None,
        authentication_hints: tuple[str, ...] = (),
        authentication_verified: bool = False,
        blockers: tuple[str, ...] = (),
        diagnostic_code: str | None = None,
    ) -> PreflightResult:
        return PreflightResult(
            status=status,
            competition_slug=competition_slug,
            output_directory=output_directory,
            executable_path=executable_path,
            cli_version=cli_version,
            authentication_configuration_detected=bool(authentication_hints),
            authentication_verified=authentication_verified,
            authentication_hints=authentication_hints,
            blockers=blockers,
            diagnostic_code=diagnostic_code,
        )


def _authentication_hints() -> tuple[str, ...]:
    present_names = tuple(
        name for name in AUTH_ENVIRONMENT_VARIABLE_NAMES if name in os.environ
    )
    hints = list(present_names)
    if (Path.home() / ".kaggle" / "kaggle.json").is_file():
        hints.append("standard_kaggle_config_file_present")
    return tuple(hints)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_link_or_junction(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    return bool(is_junction()) if callable(is_junction) else False


def _reject_link_components(root: Path, candidate: Path) -> None:
    root = root.resolve()
    candidate = Path(candidate).absolute()
    try:
        relative = candidate.relative_to(root)
    except ValueError as exc:
        raise AcquisitionError("Path escapes repository root") from exc
    current = root
    if _is_link_or_junction(current):
        raise AcquisitionError("Repository root cannot be a symbolic link or junction")
    for part in relative.parts:
        current = current / part
        if _is_link_or_junction(current):
            raise AcquisitionError("Symbolic links and junctions are not allowed")


def _validate_staging_path(
    repository_root: Path,
    staging_root: Path,
    path: str | Path,
) -> Path:
    requested = Path(path)
    if not requested.is_absolute():
        requested = repository_root / requested
    if ".." in requested.parts:
        raise AcquisitionError("Staging path cannot contain parent traversal")
    _reject_link_components(repository_root, requested)
    resolved = requested.resolve(strict=False)
    try:
        resolved.relative_to(staging_root.resolve(strict=False))
    except ValueError as exc:
        raise AcquisitionError("Path is outside the approved acquisition area") from exc
    _reject_link_components(repository_root, resolved)
    return resolved


def _create_directory_chain(root: Path, directory: Path) -> None:
    root = root.resolve()
    directory = Path(directory).absolute()
    try:
        relative = directory.relative_to(root)
    except ValueError as exc:
        raise AcquisitionError("Directory is outside its approved root") from exc
    current = root
    if _is_link_or_junction(current) or not current.is_dir():
        raise AcquisitionError("Approved root is not a regular directory")
    for part in relative.parts:
        current = current / part
        try:
            current.mkdir()
        except FileExistsError:
            pass
        if _is_link_or_junction(current) or not current.is_dir():
            raise AcquisitionError("Directory chain contains a link or non-directory")


def _normalize_archive_path(path: str) -> str:
    if (
        not isinstance(path, str)
        or not path
        or any(ord(character) < 32 or ord(character) == 127 for character in path)
    ):
        raise ArchiveSafetyError("Archive member path is empty or invalid")
    normalized = path.replace("\\", "/")
    windows_path = PureWindowsPath(path)
    if (
        normalized.startswith("/")
        or windows_path.drive
        or windows_path.root
        or any(part in {"..", ""} for part in normalized.split("/"))
        or any(":" in part for part in normalized.split("/"))
    ):
        raise ArchiveSafetyError("Archive member path is absolute or traverses")
    pure = PurePosixPath(normalized)
    if not pure.parts or any(part == ".." for part in pure.parts):
        raise ArchiveSafetyError("Archive member path is invalid")
    return pure.as_posix()


def _inventory_tree(
    staging: Path,
    limits: AcquisitionLimits,
) -> list[tuple[str, int, str, str, ArchiveInventory]]:
    if _is_link_or_junction(staging) or not staging.is_dir():
        raise AcquisitionError("Staging directory is missing or unsafe")
    results: list[tuple[str, int, str, str, ArchiveInventory]] = []
    pending = [staging]
    while pending:
        directory = pending.pop()
        _reject_link_components(staging, directory)
        for child in sorted(directory.iterdir(), key=lambda item: item.name.casefold()):
            _reject_link_components(staging, child)
            if _is_link_or_junction(child):
                raise AcquisitionError("Staging inventory rejected a symbolic link")
            metadata = child.lstat()
            if stat.S_ISDIR(metadata.st_mode):
                pending.append(child)
                continue
            if not stat.S_ISREG(metadata.st_mode):
                raise AcquisitionError("Staging inventory rejected a non-regular object")
            if metadata.st_size > limits.max_file_bytes:
                raise AcquisitionError("Staged file exceeds the configured size limit")
            digest = hashlib.sha256()
            try:
                with _open_regular_file(child) as handle:
                    for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                        digest.update(chunk)
            except OSError as exc:
                raise AcquisitionError(
                    f"Staged file is unreadable ({type(exc).__name__})"
                ) from exc
            archive = _inspect_archive(child, limits)
            if archive.status == ArchiveStatus.UNSAFE:
                file_type = f"unsafe-archive:{archive.archive_type or 'unknown'}"
            elif archive.status == ArchiveStatus.SAFE:
                file_type = f"archive:{archive.archive_type}"
            else:
                file_type = child.suffix.lower().lstrip(".") or "unknown"
            relative = child.relative_to(staging).as_posix()
            results.append(
                (
                    relative,
                    metadata.st_size,
                    digest.hexdigest(),
                    file_type,
                    archive,
                )
            )
    return sorted(results, key=lambda row: row[0].casefold())


def _inspect_archive(path: Path, limits: AcquisitionLimits) -> ArchiveInventory:
    try:
        with _open_regular_file(path) as source:
            try:
                with zipfile.ZipFile(source) as archive:
                    return _inspect_zip(archive, limits)
            except zipfile.BadZipFile:
                source.seek(0)
            try:
                with tarfile.open(fileobj=source, mode="r:*") as archive:
                    return _inspect_tar(archive, limits)
            except (tarfile.TarError, EOFError, OSError):
                if path.name.lower().endswith(
                    (".zip", ".tar", ".tgz", ".tar.gz", ".tar.bz2", ".tar.xz")
                ):
                    return ArchiveInventory(
                        ArchiveStatus.UNREADABLE,
                        None,
                        diagnostic_code="INVALID_ARCHIVE_FORMAT",
                    )
                return ArchiveInventory(ArchiveStatus.NOT_ARCHIVE, None)
    except AcquisitionError:
        return ArchiveInventory(
            ArchiveStatus.UNSAFE, None, diagnostic_code="UNSAFE_ARCHIVE_PATH"
        )
    except (OSError, zipfile.BadZipFile, tarfile.TarError):
        return ArchiveInventory(
            ArchiveStatus.UNREADABLE,
            None,
            diagnostic_code="ARCHIVE_READ_FAILED",
        )


def _inspect_zip(archive: zipfile.ZipFile, limits: AcquisitionLimits) -> ArchiveInventory:
    try:
        members: list[ArchiveMember] = []
        seen: set[str] = set()
        total_size = 0
        for index, info in enumerate(archive.infolist()):
            if index >= limits.max_archive_members:
                return ArchiveInventory(
                    ArchiveStatus.TOO_LARGE, "zip", diagnostic_code="ARCHIVE_MEMBER_LIMIT"
                )
            name = info.filename.rstrip("/")
            try:
                member_path = _normalize_archive_path(name)
            except ArchiveSafetyError:
                return ArchiveInventory(
                    ArchiveStatus.UNSAFE, "zip", diagnostic_code="UNSAFE_ARCHIVE_MEMBER_PATH"
                )
            key = member_path.casefold()
            if key in seen:
                return ArchiveInventory(
                    ArchiveStatus.UNSAFE, "zip", diagnostic_code="DUPLICATE_ARCHIVE_MEMBER"
                )
            seen.add(key)
            mode = info.external_attr >> 16
            kind_bits = stat.S_IFMT(mode)
            if stat.S_ISLNK(mode) or kind_bits not in (0, stat.S_IFREG, stat.S_IFDIR):
                return ArchiveInventory(
                    ArchiveStatus.UNSAFE, "zip", diagnostic_code="UNSAFE_ARCHIVE_MEMBER_TYPE"
                )
            is_directory = info.is_dir() or stat.S_ISDIR(mode)
            if not is_directory and kind_bits not in (0, stat.S_IFREG):
                return ArchiveInventory(
                    ArchiveStatus.UNSAFE, "zip", diagnostic_code="UNSAFE_ARCHIVE_MEMBER_TYPE"
                )
            size = 0 if is_directory else info.file_size
            if size > limits.max_file_bytes:
                return ArchiveInventory(
                    ArchiveStatus.TOO_LARGE, "zip", diagnostic_code="ARCHIVE_FILE_LIMIT"
                )
            total_size += size
            if total_size > limits.max_archive_uncompressed_bytes:
                return ArchiveInventory(
                    ArchiveStatus.TOO_LARGE, "zip", diagnostic_code="ARCHIVE_TOTAL_LIMIT"
                )
            members.append(
                ArchiveMember(
                    relative_path=member_path,
                    size_bytes=size,
                    kind="directory" if is_directory else "file",
                )
            )
        return ArchiveInventory(ArchiveStatus.SAFE, "zip", tuple(members))
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return ArchiveInventory(
            ArchiveStatus.UNREADABLE, "zip", diagnostic_code="ARCHIVE_READ_FAILED"
        )


def _inspect_tar(archive: tarfile.TarFile, limits: AcquisitionLimits) -> ArchiveInventory:
    try:
        members: list[ArchiveMember] = []
        seen: set[str] = set()
        total_size = 0
        for index, info in enumerate(archive):
            if index >= limits.max_archive_members:
                return ArchiveInventory(
                    ArchiveStatus.TOO_LARGE, "tar", diagnostic_code="ARCHIVE_MEMBER_LIMIT"
                )
            try:
                member_path = _normalize_archive_path(info.name.rstrip("/"))
            except ArchiveSafetyError:
                return ArchiveInventory(
                    ArchiveStatus.UNSAFE, "tar", diagnostic_code="UNSAFE_ARCHIVE_MEMBER_PATH"
                )
            key = member_path.casefold()
            if key in seen:
                return ArchiveInventory(
                    ArchiveStatus.UNSAFE, "tar", diagnostic_code="DUPLICATE_ARCHIVE_MEMBER"
                )
            seen.add(key)
            if info.isdir():
                kind = "directory"
                size = 0
            elif info.isfile():
                kind = "file"
                size = info.size
            else:
                return ArchiveInventory(
                    ArchiveStatus.UNSAFE, "tar", diagnostic_code="UNSAFE_ARCHIVE_MEMBER_TYPE"
                )
            if size > limits.max_file_bytes:
                return ArchiveInventory(
                    ArchiveStatus.TOO_LARGE, "tar", diagnostic_code="ARCHIVE_FILE_LIMIT"
                )
            total_size += size
            if total_size > limits.max_archive_uncompressed_bytes:
                return ArchiveInventory(
                    ArchiveStatus.TOO_LARGE, "tar", diagnostic_code="ARCHIVE_TOTAL_LIMIT"
                )
            members.append(ArchiveMember(member_path, size, kind))
        return ArchiveInventory(ArchiveStatus.SAFE, "tar", tuple(members))
    except (OSError, tarfile.TarError, EOFError):
        return ArchiveInventory(
            ArchiveStatus.UNREADABLE, "tar", diagnostic_code="ARCHIVE_READ_FAILED"
        )


def _resolve_existing_file(root: Path, relative_path: str) -> Path:
    normalized = _normalize_archive_path(relative_path)
    candidate = root.joinpath(*PurePosixPath(normalized).parts)
    _reject_link_components(root, candidate)
    if _is_link_or_junction(candidate):
        raise AcquisitionError("File path cannot be a symbolic link")
    resolved = candidate.resolve(strict=False)
    try:
        resolved.relative_to(root.resolve())
    except ValueError as exc:
        raise AcquisitionError("File path escapes the staging directory") from exc
    if not resolved.is_file():
        raise AcquisitionError("File path is not a regular file")
    return resolved


@contextmanager
def _open_archive_member(
    archive_path: Path,
    inventory: ArchiveInventory,
    member_path: str,
) -> Iterator[BinaryIO]:
    normalized = _normalize_archive_path(member_path)
    if inventory.archive_type == "zip":
        with _open_regular_file(archive_path) as archive_file:
            with zipfile.ZipFile(archive_file) as archive:
                with archive.open(normalized, "r") as member:
                    yield member
        return
    if inventory.archive_type == "tar":
        with _open_regular_file(archive_path) as archive_file:
            with tarfile.open(fileobj=archive_file, mode="r:*") as archive:
                member = archive.extractfile(normalized)
                if member is None:
                    raise ExtractionError("Archive member is not a regular file")
                with member:
                    yield member
        return
    raise ExtractionError("Unsupported archive type")


def _copy_member_exclusive(
    source: BinaryIO,
    destination: Path,
    *,
    expected_size: int,
    max_bytes: int,
) -> None:
    written = 0
    with destination.open("xb") as target:
        while True:
            chunk = source.read(min(1024 * 1024, max_bytes - written + 1))
            if not chunk:
                break
            written += len(chunk)
            if written > max_bytes or written > expected_size:
                raise ExtractionError("Archive member exceeds its declared size")
            target.write(chunk)
    if written != expected_size:
        raise ExtractionError("Extracted size does not match archive metadata")


def _archive_provenance(
    selected_path: str,
    inventory: AcquisitionInventory,
) -> str:
    selected = next(
        (
            item
            for item in inventory.files
            if item.relative_path.casefold() == selected_path.casefold()
        ),
        None,
    )
    if selected is None or selected.source_archive_path is None:
        return "source archive/member not recorded"
    return (
        f"{selected.source_archive_path}#"
        f"{selected.archive_member_path or 'member-unavailable'}"
    )


@contextmanager
def _open_regular_file(path: Path) -> Iterator[BinaryIO]:
    if _is_link_or_junction(path):
        raise AcquisitionError("File cannot be a symbolic link or junction")
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode):
        raise AcquisitionError("File is not a regular filesystem object")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        opened = os.fstat(descriptor)
        if (
            not stat.S_ISREG(opened.st_mode)
            or before.st_dev != opened.st_dev
            or before.st_ino != opened.st_ino
        ):
            raise AcquisitionError("File changed while it was being opened")
        handle = os.fdopen(descriptor, "rb")
        descriptor = -1
        with handle:
            yield handle
    finally:
        if descriptor >= 0:
            os.close(descriptor)
