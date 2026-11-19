from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import importlib.metadata
import importlib.util
from pathlib import Path, PureWindowsPath
import subprocess
from typing import Any, Protocol

from .backend import BackendOperation, OperationStatus, UnavailableBackend
from .configurations import CandidateConfiguration
from .search_space import SearchSpace
from .verifier import ArtifactStatus, discover_artifacts


class IntakeStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"
    INACCESSIBLE = "INACCESSIBLE"
    INVALID = "INVALID"
    CHECKSUM_MISMATCH = "CHECKSUM_MISMATCH"


class TrackingStatus(str, Enum):
    TRACKED = "TRACKED"
    UNTRACKED = "UNTRACKED"
    EXTERNAL = "EXTERNAL"
    UNKNOWN = "UNKNOWN"


class CompatibilityStatus(str, Enum):
    UNKNOWN = "UNKNOWN"
    COMPATIBLE = "COMPATIBLE"
    INCOMPATIBLE = "INCOMPATIBLE"


class ProvenanceStatus(str, Enum):
    OFFICIAL_AUTHENTICATED = "OFFICIAL_AUTHENTICATED"
    OFFICIAL_SOURCE_UNVERIFIED = "OFFICIAL_SOURCE_UNVERIFIED"
    UNAUTHENTICATED_MIRROR = "UNAUTHENTICATED_MIRROR"
    LOCAL_UNVERIFIED = "LOCAL_UNVERIFIED"
    MISSING = "MISSING"
    CORRUPTED = "CORRUPTED"
    ACQUISITION_BLOCKED = "ACQUISITION_BLOCKED"


@dataclass(frozen=True)
class ArtifactDeclaration:
    role: str
    relative_path: str
    provenance: str
    version: str | None = None
    source_commit: str | None = None
    expected_sha256: str | None = None
    artifact_id: str | None = None
    source_identity: str | None = None
    source_url: str | None = None
    authentication_evidence: str | None = None
    provenance_status: ProvenanceStatus = ProvenanceStatus.LOCAL_UNVERIFIED

    def __post_init__(self) -> None:
        for field_name in ("role", "relative_path", "provenance"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")
        if self.artifact_id is None:
            object.__setattr__(self, "artifact_id", self.role)
        elif not isinstance(self.artifact_id, str) or not self.artifact_id.strip():
            raise ValueError("artifact_id must be a non-empty string")
        for field_name in (
            "source_identity",
            "source_url",
            "authentication_evidence",
        ):
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"{field_name} must be a non-empty string when set")
        try:
            provenance_status = ProvenanceStatus(self.provenance_status)
        except (TypeError, ValueError) as exc:
            raise ValueError("Unsupported provenance_status") from exc
        object.__setattr__(self, "provenance_status", provenance_status)
        if provenance_status == ProvenanceStatus.OFFICIAL_AUTHENTICATED and (
            not self.source_identity
            or not self.source_url
            or not self.source_url.startswith("https://")
            or not self.authentication_evidence
            or self.expected_sha256 is None
        ):
            raise ValueError(
                "Authenticated official artifacts require an exact source "
                "identity, HTTPS source URL, authentication evidence, and "
                "expected SHA-256"
            )
        relative = Path(self.relative_path)
        windows_relative = PureWindowsPath(self.relative_path)
        if (
            relative.is_absolute()
            or relative.drive
            or windows_relative.drive
            or windows_relative.root
            or any(part == ".." for part in relative.parts)
        ):
            raise ValueError("Artifact paths must be relative and cannot traverse upward")
        if self.expected_sha256 is not None and (
            len(self.expected_sha256) != 64
            or any(character not in "0123456789abcdefABCDEF" for character in self.expected_sha256)
        ):
            raise ValueError("expected_sha256 must be a 64-character hexadecimal digest")


@dataclass(frozen=True)
class ArtifactRecord:
    role: str
    relative_path: str
    status: IntakeStatus
    readable: bool | None
    file_type: str
    sha256: str | None
    expected_sha256: str | None
    tracking_status: TrackingStatus
    compatibility_status: CompatibilityStatus
    provenance: str
    version: str | None = None
    source_commit: str | None = None
    detail: str | None = None
    artifact_id: str | None = None
    source_identity: str | None = None
    source_url: str | None = None
    authentication_evidence: str | None = None
    provenance_status: ProvenanceStatus = ProvenanceStatus.LOCAL_UNVERIFIED

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id or self.role,
            "role": self.role,
            "relative_path": self.relative_path,
            "status": self.status.value,
            "readable": self.readable,
            "file_type": self.file_type,
            "sha256": self.sha256,
            "expected_sha256": self.expected_sha256,
            "tracking_status": self.tracking_status.value,
            "compatibility_status": self.compatibility_status.value,
            "provenance": self.provenance,
            "version": self.version,
            "source_commit": self.source_commit,
            "detail": self.detail,
            "source_identity": self.source_identity,
            "source_url": self.source_url,
            "authentication_evidence": self.authentication_evidence,
            "provenance_status": self.provenance_status.value,
        }


@dataclass(frozen=True)
class SDKInventory:
    name: str
    import_name: str
    import_available: bool
    version: str | None
    version_status: str
    api_status: str
    evidence_reference: str
    inspection_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "import_name": self.import_name,
            "import_available": self.import_available,
            "version": self.version,
            "version_status": self.version_status,
            "api_status": self.api_status,
            "evidence_reference": self.evidence_reference,
            "inspection_error": self.inspection_error,
        }


@dataclass(frozen=True)
class ArtifactManifest:
    repository_root: Path
    artifact_root_kind: str
    artifacts: tuple[ArtifactRecord, ...]
    sdk: SDKInventory
    schema_version: str = "2"

    def __post_init__(self) -> None:
        object.__setattr__(self, "repository_root", Path(self.repository_root).resolve())
        object.__setattr__(self, "artifacts", tuple(self.artifacts))
        if self.artifact_root_kind not in {"repository", "external"}:
            raise ValueError("artifact_root_kind must be 'repository' or 'external'")
        roles = [artifact.role for artifact in self.artifacts]
        if len(roles) != len(set(roles)):
            raise ValueError("Artifact roles must be unique")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "artifact_root_kind": self.artifact_root_kind,
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "sdk": self.sdk.to_dict(),
        }

    def artifact_for_role(self, role: str) -> ArtifactRecord | None:
        return next((artifact for artifact in self.artifacts if artifact.role == role), None)

    @classmethod
    def discover(
        cls,
        repository_root: str | Path,
        *,
        artifact_root: str | Path | None = None,
        declarations: tuple[ArtifactDeclaration, ...] | None = None,
    ) -> ArtifactManifest:
        repo = Path(repository_root).resolve()
        root = Path(artifact_root).resolve() if artifact_root is not None else repo
        is_repository_root = root == repo
        specs = declarations or default_artifact_declarations()
        if len({spec.role for spec in specs}) != len(specs):
            raise ValueError("Artifact roles must be unique")
        discoveries = discover_artifacts(
            root,
            tuple(spec.relative_path for spec in specs),
        )
        records: list[ArtifactRecord] = []
        for spec, found in zip(specs, discoveries):
            status = {
                ArtifactStatus.AVAILABLE: IntakeStatus.AVAILABLE,
                ArtifactStatus.MISSING: IntakeStatus.MISSING,
                ArtifactStatus.INACCESSIBLE: IntakeStatus.INACCESSIBLE,
                ArtifactStatus.NOT_REGULAR: IntakeStatus.INVALID,
            }[found.status]
            detail = found.detail
            if (
                status == IntakeStatus.AVAILABLE
                and spec.expected_sha256 is not None
                and found.sha256 is not None
                and found.sha256.lower() != spec.expected_sha256.lower()
            ):
                status = IntakeStatus.CHECKSUM_MISMATCH
                detail = "SHA-256 does not match the declared checksum"
            provenance_status = spec.provenance_status
            if found.status == ArtifactStatus.MISSING:
                provenance_status = ProvenanceStatus.MISSING
            elif status == IntakeStatus.CHECKSUM_MISMATCH:
                provenance_status = ProvenanceStatus.CORRUPTED
            elif status in (IntakeStatus.INACCESSIBLE, IntakeStatus.INVALID):
                provenance_status = ProvenanceStatus.ACQUISITION_BLOCKED
            tracking = _tracking_status(repo, root, spec.relative_path, is_repository_root)
            records.append(
                ArtifactRecord(
                    role=spec.role,
                    relative_path=spec.relative_path,
                    status=status,
                    readable=(
                        True
                        if found.status == ArtifactStatus.AVAILABLE
                        else False
                        if found.status
                        in (ArtifactStatus.INACCESSIBLE, ArtifactStatus.NOT_REGULAR)
                        else None
                    ),
                    file_type=found.file_type,
                    sha256=found.sha256,
                    expected_sha256=spec.expected_sha256,
                    tracking_status=tracking,
                    compatibility_status=CompatibilityStatus.UNKNOWN,
                    provenance=spec.provenance,
                    version=spec.version,
                    source_commit=spec.source_commit,
                    detail=detail,
                    artifact_id=spec.artifact_id,
                    source_identity=spec.source_identity,
                    source_url=spec.source_url,
                    authentication_evidence=spec.authentication_evidence,
                    provenance_status=provenance_status,
                )
            )
        sdk = inspect_sdk()
        return cls(
            repository_root=repo,
            artifact_root_kind="repository" if is_repository_root else "external",
            artifacts=tuple(records),
            sdk=sdk,
        )


def default_artifact_declarations() -> tuple[ArtifactDeclaration, ...]:
    reference = "P013: canonical competition source not established"
    return (
        ArtifactDeclaration(
            "official_verifier",
            "external/verifiers/invsqrt/verify_submission_invsqrt.py",
            reference,
            artifact_id="invsqrt-official-verifier",
            provenance_status=ProvenanceStatus.OFFICIAL_SOURCE_UNVERIFIED,
        ),
        ArtifactDeclaration(
            "reference_circuit",
            "external/verifiers/invsqrt/nr_reference_circuit.py",
            reference,
            artifact_id="invsqrt-reference-circuit",
            provenance_status=ProvenanceStatus.OFFICIAL_SOURCE_UNVERIFIED,
        ),
        ArtifactDeclaration(
            "sample_submission",
            "external/sample_submission/invsqrt.kmb",
            reference,
            artifact_id="invsqrt-sample-submission",
            provenance_status=ProvenanceStatus.OFFICIAL_SOURCE_UNVERIFIED,
        ),
        ArtifactDeclaration(
            "sdk_library",
            "external/kickmix/kickmix.so",
            reference,
            artifact_id="invsqrt-kickmix-library",
            provenance_status=ProvenanceStatus.OFFICIAL_SOURCE_UNVERIFIED,
        ),
    )


def inspect_sdk() -> SDKInventory:
    evidence = "origin/main:docs/DEPENDENCY_COMPATIBILITY_REPORT.md"
    try:
        module_spec = importlib.util.find_spec("kickmix")
    except (ImportError, ValueError) as exc:
        return SDKInventory(
            "Kickmix",
            "kickmix",
            False,
            None,
            "UNKNOWN",
            "UNKNOWN",
            evidence,
            type(exc).__name__,
        )
    if module_spec is None:
        return SDKInventory(
            "Kickmix",
            "kickmix",
            False,
            None,
            "UNKNOWN",
            "UNKNOWN",
            evidence,
        )
    try:
        version = importlib.metadata.version("kickmix")
    except importlib.metadata.PackageNotFoundError:
        version = None
    return SDKInventory(
        "Kickmix",
        "kickmix",
        True,
        version,
        "KNOWN" if version is not None else "UNKNOWN",
        "UNKNOWN",
        evidence,
    )


def _tracking_status(
    repository_root: Path,
    artifact_root: Path,
    relative_path: str,
    artifact_root_is_repository: bool,
) -> TrackingStatus:
    if not artifact_root_is_repository:
        try:
            (artifact_root / relative_path).resolve().relative_to(repository_root)
        except ValueError:
            return TrackingStatus.EXTERNAL
    try:
        repository_relative = (artifact_root / relative_path).resolve().relative_to(
            repository_root
        )
    except ValueError:
        return TrackingStatus.EXTERNAL
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(repository_root),
                "ls-files",
                "--error-unmatch",
                "--",
                repository_relative.as_posix(),
            ],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return TrackingStatus.UNKNOWN
    if result.returncode == 0:
        return TrackingStatus.TRACKED
    if result.returncode == 1:
        return TrackingStatus.UNTRACKED
    return TrackingStatus.UNKNOWN


@dataclass(frozen=True)
class AdapterReadiness:
    ready: bool
    status: str
    blockers: tuple[str, ...]
    production_adapter_implemented: bool
    verifier_available: bool
    reference_circuit_available: bool
    sample_submission_available: bool
    sdk_import_available: bool
    sdk_api_status: str
    artifact_provenance_statuses: Mapping[str, str] = field(default_factory=dict)
    artifact_integrity_statuses: Mapping[str, str] = field(default_factory=dict)
    required_artifacts_authenticated: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "ready": self.ready,
            "status": self.status,
            "blockers": list(self.blockers),
            "production_adapter_implemented": self.production_adapter_implemented,
            "verifier_available": self.verifier_available,
            "reference_circuit_available": self.reference_circuit_available,
            "sample_submission_available": self.sample_submission_available,
            "sdk_import_available": self.sdk_import_available,
            "sdk_api_status": self.sdk_api_status,
            "artifact_provenance_statuses": dict(
                self.artifact_provenance_statuses
            ),
            "artifact_integrity_statuses": dict(
                self.artifact_integrity_statuses
            ),
            "required_artifacts_authenticated": self.required_artifacts_authenticated,
        }


def assess_adapter_readiness(manifest: ArtifactManifest) -> AdapterReadiness:
    roles = {artifact.role: artifact for artifact in manifest.artifacts}
    verifier = roles.get("official_verifier")
    reference = roles.get("reference_circuit")
    sample = roles.get("sample_submission")
    verifier_available = verifier is not None and verifier.status == IntakeStatus.AVAILABLE
    reference_available = reference is not None and reference.status == IntakeStatus.AVAILABLE
    sample_available = sample is not None and sample.status == IntakeStatus.AVAILABLE
    blockers: list[str] = []
    provenance_statuses: dict[str, str] = {}
    integrity_statuses: dict[str, str] = {}
    required_artifacts_authenticated = True
    for role, record in (
        ("official verifier", verifier),
        ("reference circuit", reference),
        ("sample submission", sample),
    ):
        if record is None or record.status != IntakeStatus.AVAILABLE:
            blockers.append(f"{role} artifact is not available")
        provenance_status = (
            record.provenance_status
            if record is not None
            else ProvenanceStatus.MISSING
        )
        provenance_statuses[role.replace(" ", "_")] = provenance_status.value
        if provenance_status != ProvenanceStatus.OFFICIAL_AUTHENTICATED:
            blockers.append(f"{role} source is not authenticated as official")
        integrity_status = _integrity_status(record)
        integrity_statuses[role.replace(" ", "_")] = integrity_status
        if integrity_status != "VERIFIED":
            blockers.append(f"{role} SHA-256 integrity is not verified")
        if (
            record is None
            or record.status != IntakeStatus.AVAILABLE
            or provenance_status != ProvenanceStatus.OFFICIAL_AUTHENTICATED
            or integrity_status != "VERIFIED"
        ):
            required_artifacts_authenticated = False
    if not manifest.sdk.import_available:
        blockers.append("Kickmix runtime is not importable in this Python environment")
    if manifest.sdk.api_status != "CONFIRMED":
        blockers.append("Kickmix circuit-loading and resource APIs are not confirmed")
    blockers.append("Production Kickmix circuit/resource adapter is not implemented")
    return AdapterReadiness(
        ready=not blockers,
        status="READY" if not blockers else "BLOCKED",
        blockers=tuple(blockers),
        production_adapter_implemented=False,
        verifier_available=verifier_available,
        reference_circuit_available=reference_available,
        sample_submission_available=sample_available,
        sdk_import_available=manifest.sdk.import_available,
        sdk_api_status=manifest.sdk.api_status,
        artifact_provenance_statuses=provenance_statuses,
        artifact_integrity_statuses=integrity_statuses,
        required_artifacts_authenticated=required_artifacts_authenticated,
    )


def _integrity_status(record: ArtifactRecord | None) -> str:
    if record is None or record.status == IntakeStatus.MISSING:
        return "MISSING"
    if (
        record.status == IntakeStatus.CHECKSUM_MISMATCH
        or record.provenance_status == ProvenanceStatus.CORRUPTED
    ):
        return "CORRUPTED"
    if record.expected_sha256 is None or record.sha256 is None:
        return "UNVERIFIED"
    if record.sha256.lower() == record.expected_sha256.lower():
        return "VERIFIED"
    return "CORRUPTED"


class CircuitArtifactAdapter(Protocol):
    def load(self, artifact: ArtifactRecord) -> BackendOperation:
        ...


class UnavailableCircuitArtifactAdapter:
    def load(self, artifact: ArtifactRecord) -> BackendOperation:
        return BackendOperation(
            status=OperationStatus.UNAVAILABLE,
            error="Circuit loading is unavailable until the official artifact and Kickmix API are confirmed",
            evidence_references=(artifact.provenance,),
        )


class UnavailableKickmixBackend(UnavailableBackend):
    backend_id = "kickmix-invsqrt-unavailable"

    def __init__(self, readiness: AdapterReadiness) -> None:
        self.readiness = readiness
        self.backend_version = "unknown"

    def validate_configuration(
        self,
        configuration: CandidateConfiguration,
        search_space: SearchSpace,
    ) -> BackendOperation:
        return self._unavailable(
            f"configuration_id={configuration.configuration_id}; "
            f"search_space_id={search_space.search_space_id}"
        )

    def construct_circuit(self, configuration: CandidateConfiguration) -> BackendOperation:
        return self._unavailable(f"configuration_id={configuration.configuration_id}")

    def measure_resources(
        self,
        configuration: CandidateConfiguration,
        circuit: Any,
    ) -> BackendOperation:
        return self._unavailable(
            f"configuration_id={configuration.configuration_id}; "
            f"artifact_reference={circuit.artifact_reference}"
        )

    def compile_circuit(
        self,
        configuration: CandidateConfiguration,
        circuit: Any,
    ) -> BackendOperation:
        return self._unavailable(
            f"configuration_id={configuration.configuration_id}; "
            f"artifact_reference={circuit.artifact_reference}"
        )

    def _unavailable(self, operation_context: str) -> BackendOperation:
        detail = "; ".join(self.readiness.blockers) or "Kickmix adapter is not implemented"
        return BackendOperation(
            status=OperationStatus.UNAVAILABLE,
            error=f"{detail} ({operation_context})",
        )
