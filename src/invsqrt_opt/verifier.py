from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path, PureWindowsPath
import hashlib
from typing import Any, Mapping, Protocol


class ExecutionStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    EXECUTION_PENDING = "EXECUTION_PENDING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class VerificationStatus(str, Enum):
    NOT_CHECKED = "NOT_CHECKED"
    VERIFIER_UNAVAILABLE = "VERIFIER_UNAVAILABLE"
    READY = "READY"
    EXECUTION_PENDING = "EXECUTION_PENDING"
    EXECUTION_FAILED = "EXECUTION_FAILED"
    PASSED = "PASSED"
    REJECTED = "REJECTED"
    RESULT_UNKNOWN = "RESULT_UNKNOWN"


class VerificationLevel(str, Enum):
    METADATA = "METADATA"
    STRUCTURAL = "STRUCTURAL"
    OFFICIAL = "OFFICIAL"


class ArtifactStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    INACCESSIBLE = "INACCESSIBLE"
    NOT_REGULAR = "NOT_REGULAR"


@dataclass(frozen=True)
class ArtifactDiscovery:
    relative_path: str
    status: ArtifactStatus
    file_type: str
    sha256: str | None = None
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "relative_path": self.relative_path,
            "status": self.status.value,
            "file_type": self.file_type,
            "sha256": self.sha256,
            "detail": self.detail,
        }


def discover_artifacts(
    repository_root: str | Path,
    relative_paths: tuple[str, ...] = (
        "external/verifiers/invsqrt/verify_submission_invsqrt.py",
        "external/verifiers/invsqrt/nr_reference_circuit.py",
        "external/sample_submission/invsqrt.kmb",
    ),
) -> tuple[ArtifactDiscovery, ...]:
    root = Path(repository_root).resolve()
    discoveries: list[ArtifactDiscovery] = []
    for relative_path in relative_paths:
        relative = Path(relative_path)
        windows_relative = PureWindowsPath(relative_path)
        if (
            relative.is_absolute()
            or relative.drive
            or windows_relative.drive
            or windows_relative.root
            or any(part == ".." for part in relative.parts)
        ):
            discoveries.append(
                ArtifactDiscovery(
                    relative_path,
                    ArtifactStatus.INACCESSIBLE,
                    "unknown",
                    detail="Artifact path must be relative and cannot traverse upward",
                )
            )
            continue
        unresolved = root / relative
        try:
            current = root
            has_symlink_component = False
            for part in relative.parts:
                current = current / part
                if current.is_symlink():
                    has_symlink_component = True
                    break
            if has_symlink_component:
                discoveries.append(
                    ArtifactDiscovery(
                        relative_path,
                        ArtifactStatus.NOT_REGULAR,
                        "symbolic-link",
                        detail="Symbolic-link artifact paths are not trusted",
                    )
                )
                continue
            candidate = unresolved.resolve()
            candidate.relative_to(root)
        except ValueError:
            discoveries.append(
                ArtifactDiscovery(
                    relative_path,
                    ArtifactStatus.INACCESSIBLE,
                    "unknown",
                    detail="Path escapes repository root",
                )
            )
            continue
        if not candidate.exists():
            discoveries.append(
                ArtifactDiscovery(
                    relative_path,
                    ArtifactStatus.MISSING,
                    "unknown",
                )
            )
            continue
        if not candidate.is_file():
            discoveries.append(
                ArtifactDiscovery(
                    relative_path,
                    ArtifactStatus.NOT_REGULAR,
                    "not-regular-file",
                )
            )
            continue
        try:
            digest = hashlib.sha256()
            with candidate.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
            discoveries.append(
                ArtifactDiscovery(
                    relative_path,
                    ArtifactStatus.AVAILABLE,
                    candidate.suffix.lower() or "unknown",
                    sha256=digest.hexdigest(),
                )
            )
        except (OSError, PermissionError) as exc:
            discoveries.append(
                ArtifactDiscovery(
                    relative_path,
                    ArtifactStatus.INACCESSIBLE,
                    "unknown",
                    detail=type(exc).__name__,
                )
            )
    return tuple(discoveries)


@dataclass(frozen=True)
class VerifierAvailability:
    verifier_id: str
    status: ArtifactStatus
    verifier_path: str | None
    source_checksum: str | None = None
    detail: str | None = None


@dataclass(frozen=True)
class VerificationRequest:
    request_id: str
    candidate_id: str
    candidate_artifact: str
    specification_version: str
    verifier_id: str
    git_commit: str
    environment_metadata: Mapping[str, str]
    requested_level: VerificationLevel
    creation_timestamp: str
    authorization_reference: str | None = None

    def __post_init__(self) -> None:
        for name in (
            "request_id",
            "candidate_id",
            "candidate_artifact",
            "specification_version",
            "verifier_id",
            "git_commit",
            "creation_timestamp",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} is required")
        try:
            datetime.fromisoformat(self.creation_timestamp)
        except ValueError as exc:
            raise ValueError("creation_timestamp must be ISO-8601") from exc
        if not isinstance(self.environment_metadata, Mapping):
            raise ValueError("environment_metadata must be a mapping")
        if not all(
            isinstance(key, str) and isinstance(value, str)
            for key, value in self.environment_metadata.items()
        ):
            raise ValueError("environment_metadata must map strings to strings")
        object.__setattr__(
            self,
            "environment_metadata",
            dict(self.environment_metadata),
        )
        object.__setattr__(
            self,
            "requested_level",
            (
                self.requested_level
                if isinstance(self.requested_level, VerificationLevel)
                else VerificationLevel(self.requested_level)
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "candidate_id": self.candidate_id,
            "candidate_artifact": self.candidate_artifact,
            "specification_version": self.specification_version,
            "verifier_id": self.verifier_id,
            "git_commit": self.git_commit,
            "environment_metadata": dict(self.environment_metadata),
            "requested_level": self.requested_level.value,
            "creation_timestamp": self.creation_timestamp,
            "authorization_reference": self.authorization_reference,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VerificationRequest":
        values = dict(data)
        values["requested_level"] = VerificationLevel(values["requested_level"])
        return cls(**values)


@dataclass(frozen=True)
class EvidenceProvenance:
    source: str
    source_checksum: str | None
    git_commit: str
    evidence_references: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("Evidence source is required")
        if not isinstance(self.git_commit, str) or not self.git_commit.strip():
            raise ValueError("Evidence git_commit is required")
        object.__setattr__(
            self, "evidence_references", tuple(self.evidence_references)
        )

    @property
    def is_complete(self) -> bool:
        return bool(self.source and self.git_commit and self.evidence_references)


@dataclass(frozen=True)
class VerificationResult:
    request_id: str
    candidate_id: str
    verifier_id: str
    verifier_source_checksum: str | None
    execution_status: ExecutionStatus
    verification_status: VerificationStatus
    exit_code: int | None
    evidence_references: tuple[str, ...]
    stdout_reference: str | None = None
    stderr_reference: str | None = None
    execution_start: str | None = None
    execution_end: str | None = None
    resource_metrics: Mapping[str, Any] | None = None
    error_details: str | None = None
    provenance_complete: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "execution_status",
            (
                self.execution_status
                if isinstance(self.execution_status, ExecutionStatus)
                else ExecutionStatus(self.execution_status)
            ),
        )
        object.__setattr__(
            self,
            "verification_status",
            (
                self.verification_status
                if isinstance(self.verification_status, VerificationStatus)
                else VerificationStatus(self.verification_status)
            ),
        )
        object.__setattr__(
            self, "evidence_references", tuple(self.evidence_references)
        )
        if self.resource_metrics is not None:
            object.__setattr__(
                self, "resource_metrics", dict(self.resource_metrics)
            )

        if self.verification_status == VerificationStatus.PASSED:
            if self.execution_status != ExecutionStatus.EXECUTED:
                raise ValueError("PASSED requires an executed verifier")
            if self.exit_code != 0:
                raise ValueError("PASSED requires exit code 0")
            if not self.evidence_references:
                raise ValueError("PASSED requires evidence references")
            if not self.verifier_source_checksum:
                raise ValueError("PASSED requires verifier source checksum")
            if not self.provenance_complete:
                raise ValueError("PASSED requires complete provenance")

        if self.execution_status == ExecutionStatus.EXECUTED:
            if self.verification_status not in (
                VerificationStatus.PASSED,
                VerificationStatus.REJECTED,
                VerificationStatus.RESULT_UNKNOWN,
            ):
                raise ValueError("Executed result has no valid verification outcome")

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "candidate_id": self.candidate_id,
            "verifier_id": self.verifier_id,
            "verifier_source_checksum": self.verifier_source_checksum,
            "execution_status": self.execution_status.value,
            "verification_status": self.verification_status.value,
            "exit_code": self.exit_code,
            "evidence_references": list(self.evidence_references),
            "stdout_reference": self.stdout_reference,
            "stderr_reference": self.stderr_reference,
            "execution_start": self.execution_start,
            "execution_end": self.execution_end,
            "resource_metrics": (
                dict(self.resource_metrics) if self.resource_metrics is not None else None
            ),
            "error_details": self.error_details,
            "provenance_complete": self.provenance_complete,
        }

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "VerificationResult":
        values = dict(data)
        values["evidence_references"] = tuple(
            values.get("evidence_references", ())
        )
        return cls(**values)


class OfficialVerifierAdapter(Protocol):
    def discover(self) -> VerifierAvailability:
        ...

    def validate_request(
        self,
        request: VerificationRequest,
    ) -> tuple[str, ...]:
        ...

    def execute(
        self,
        request: VerificationRequest,
    ) -> VerificationResult:
        ...


class UnavailableVerifierAdapter:
    """Fail-closed adapter used when no official verifier is available."""

    def discover(self) -> VerifierAvailability:
        return VerifierAvailability(
            verifier_id="official-invsqrt-verifier",
            status=ArtifactStatus.MISSING,
            verifier_path=None,
            detail="Official verifier artifact was not discovered",
        )

    def validate_request(
        self,
        request: VerificationRequest,
    ) -> tuple[str, ...]:
        availability = self.discover()
        if availability.status != ArtifactStatus.AVAILABLE:
            return ("Official verifier is unavailable",)
        if not request.authorization_reference:
            return ("Verifier execution requires authorization",)
        return ()

    def execute(
        self,
        request: VerificationRequest,
    ) -> VerificationResult:
        errors = self.validate_request(request)
        return VerificationResult(
            request_id=request.request_id,
            candidate_id=request.candidate_id,
            verifier_id=request.verifier_id,
            verifier_source_checksum=None,
            execution_status=ExecutionStatus.NOT_STARTED,
            verification_status=(
                VerificationStatus.VERIFIER_UNAVAILABLE
                if "Official verifier is unavailable" in errors
                else VerificationStatus.RESULT_UNKNOWN
            ),
            exit_code=None,
            evidence_references=(),
            error_details="; ".join(errors),
            provenance_complete=False,
        )


class TestDoubleVerifierAdapter:
    """Explicit test-only adapter; it can never return an official pass."""

    __test__ = False

    def __init__(self, unavailable: bool = False) -> None:
        self.unavailable = unavailable

    def discover(self) -> VerifierAvailability:
        if self.unavailable:
            return VerifierAvailability(
                verifier_id="TEST_DOUBLE_OFFICIAL_INVSQRT_VERIFIER",
                status=ArtifactStatus.MISSING,
                verifier_path=None,
                detail="Explicit test double",
            )
        return VerifierAvailability(
            verifier_id="TEST_DOUBLE_OFFICIAL_INVSQRT_VERIFIER",
            status=ArtifactStatus.AVAILABLE,
            verifier_path="<test-double>",
            source_checksum="test-double-not-an-official-checksum",
            detail="Explicit test double; cannot establish official pass",
        )

    def validate_request(
        self,
        request: VerificationRequest,
    ) -> tuple[str, ...]:
        if self.unavailable:
            return ("Test-double verifier unavailable",)
        if not request.candidate_artifact:
            return ("Candidate artifact is missing",)
        return ()

    def execute(
        self,
        request: VerificationRequest,
    ) -> VerificationResult:
        errors = self.validate_request(request)
        if errors:
            return VerificationResult(
                request_id=request.request_id,
                candidate_id=request.candidate_id,
                verifier_id=request.verifier_id,
                verifier_source_checksum=None,
                execution_status=ExecutionStatus.NOT_STARTED,
                verification_status=VerificationStatus.RESULT_UNKNOWN,
                exit_code=None,
                evidence_references=("test-double",),
                error_details="; ".join(errors),
                provenance_complete=False,
            )
        return VerificationResult(
            request_id=request.request_id,
            candidate_id=request.candidate_id,
            verifier_id=request.verifier_id,
            verifier_source_checksum=None,
            execution_status=ExecutionStatus.EXECUTED,
            verification_status=VerificationStatus.REJECTED,
            exit_code=0,
            evidence_references=("test-double:rejected",),
            error_details="Test double never represents an official pass",
            provenance_complete=False,
        )
