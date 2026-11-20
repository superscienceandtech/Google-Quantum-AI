from __future__ import annotations

import hashlib
import json
import os
import stat
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

try:
    import fcntl
except ImportError:
    fcntl = None

try:
    import msvcrt
except ImportError:
    msvcrt = None


class AuthorityClass(str, Enum):
    OFFICIAL_COMPETITION_VERIFIER = "OFFICIAL_COMPETITION_VERIFIER"
    OFFICIAL_ECOSYSTEM = "OFFICIAL_ECOSYSTEM"
    PUBLIC_SECONDARY = "PUBLIC_SECONDARY"
    TEAM_INTERNAL = "TEAM_INTERNAL"
    UNVERIFIED = "UNVERIFIED"
    UNAVAILABLE = "UNAVAILABLE"


def hash_file(path: str | Path, chunk_size: int = 1024 * 1024) -> str:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    digest = hashlib.sha256()
    resolved = Path(path)
    if not resolved.is_file():
        raise FileNotFoundError(resolved)
    with resolved.open("rb") as stream:
        for chunk in iter(lambda: stream.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


_MANIFEST_LOCKS: dict[str, threading.RLock] = {}
_MANIFEST_LOCKS_GUARD = threading.Lock()


def _manifest_lock(manifest: Path) -> threading.RLock:
    key = str(manifest.resolve(strict=False))
    with _MANIFEST_LOCKS_GUARD:
        lock = _MANIFEST_LOCKS.get(key)
        if lock is None:
            lock = threading.RLock()
            _MANIFEST_LOCKS[key] = lock
        return lock


def _acquire_file_lock(manifest: Path):
    lock_path = manifest.with_name(manifest.name + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    if lock_path.exists() and lock_path.is_symlink():
        raise OSError(f"Evidence lock file must not be a symlink: {lock_path}")
    stream = lock_path.open("a+b")
    if stream.seek(0, os.SEEK_END) == 0:
        stream.write(b"\0")
        stream.flush()
        os.fsync(stream.fileno())
    stream.seek(0)

    if fcntl is not None:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
    elif msvcrt is not None:
        msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
    return stream


def _release_file_lock(stream) -> None:
    if fcntl is not None:
        fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
    elif msvcrt is not None:
        msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
    stream.close()


def _record_hash(sequence: int, previous_hash: str, record: Mapping[str, Any]) -> str:
    payload = {
        "previous_hash": previous_hash,
        "record": dict(record),
        "sequence": sequence,
    }
    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


@dataclass(frozen=True)
class ArtifactRecord:
    path: str
    sha256: str
    size_bytes: int
    media_type: str = "application/octet-stream"

    def __post_init__(self) -> None:
        if len(self.sha256) != 64:
            raise ValueError("SHA-256 must contain exactly 64 hexadecimal characters")
        try:
            int(self.sha256, 16)
        except ValueError as exc:
            raise ValueError("SHA-256 must be hexadecimal") from exc
        if self.size_bytes < 0:
            raise ValueError("size_bytes must not be negative")

    @classmethod
    def from_file(cls, path: str | Path, media_type: str = "application/octet-stream") -> "ArtifactRecord":
        resolved = Path(path)
        if not resolved.is_file():
            raise FileNotFoundError(resolved)
        if resolved.is_symlink():
            raise OSError(f"Evidence artifacts must not be symlinks: {resolved}")

        open_flags = os.O_RDONLY
        if hasattr(os, "O_BINARY"):
            open_flags |= os.O_BINARY
        if hasattr(os, "O_NOFOLLOW"):
            open_flags |= os.O_NOFOLLOW
        descriptor = os.open(resolved, open_flags)
        try:
            before = os.fstat(descriptor)
            if not stat.S_ISREG(before.st_mode):
                raise OSError(f"Evidence artifact is not a regular file: {resolved}")
            digest = hashlib.sha256()
            with os.fdopen(descriptor, "rb", closefd=False) as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            after = os.fstat(descriptor)
        finally:
            os.close(descriptor)

        identity_before = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
        )
        identity_after = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
        )
        if identity_before != identity_after:
            raise RuntimeError(
                f"Artifact changed while hashing: {resolved}"
            )
        path_stat = resolved.stat(follow_symlinks=False)
        identity_path = (
            path_stat.st_dev,
            path_stat.st_ino,
            path_stat.st_size,
            path_stat.st_mtime_ns,
        )
        if identity_before != identity_path:
            raise RuntimeError(
                f"Artifact changed or was replaced while hashing: {resolved}"
            )
        return cls(
            path=str(resolved.resolve()),
            sha256=digest.hexdigest(),
            size_bytes=after.st_size,
            media_type=media_type,
        )


@dataclass(frozen=True)
class EvidenceRecord:
    evidence_id: str
    authority: AuthorityClass
    status: str
    artifacts: tuple[ArtifactRecord, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.evidence_id:
            raise ValueError("evidence_id must not be empty")
        if self.status not in {
            "PASS",
            "FAIL",
            "BLOCKED",
            "NOT_RUN",
            "NOT_VERIFIED",
            "NEEDS_REVIEW",
        }:
            raise ValueError(f"Unknown evidence status: {self.status}")
        if self.status == "PASS" and not self.artifacts and not self.evidence_refs:
            raise ValueError("PASS evidence requires artifacts or evidence_refs")
        if not isinstance(self.authority, AuthorityClass):
            try:
                authority = AuthorityClass(self.authority)
                object.__setattr__(self, "authority", authority)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Unknown authority: {self.authority}") from exc

        normalized_refs = tuple(
            reference.strip()
            for reference in self.evidence_refs
            if isinstance(reference, str)
        )
        if any(
            not reference
            or len(reference) > 128
            or any(character.isspace() for character in reference)
            for reference in normalized_refs
        ):
            raise ValueError("Evidence references must be non-empty, unspaced identifiers")
        object.__setattr__(self, "evidence_refs", normalized_refs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "authority": self.authority.value,
            "status": self.status,
            "created_at": self.created_at,
            "artifacts": [
                {
                    "path": artifact.path,
                    "sha256": artifact.sha256,
                    "size_bytes": artifact.size_bytes,
                    "media_type": artifact.media_type,
                }
                for artifact in self.artifacts
            ],
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
        }


def append_evidence_record(
    manifest_path: str | Path,
    record: EvidenceRecord,
) -> None:
    manifest = Path(manifest_path)
    if manifest.exists() and manifest.is_dir():
        raise IsADirectoryError(manifest)
    manifest.parent.mkdir(parents=True, exist_ok=True)

    record_payload = record.to_dict()
    line = json.dumps(
        record_payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )

    thread_lock = _manifest_lock(manifest)
    with thread_lock:
        lock_stream = _acquire_file_lock(manifest)
        try:
            existing = manifest.read_bytes() if manifest.exists() else b""
            sequence = len(existing.splitlines()) + 1 if existing else 1
            previous_hash = hashlib.sha256(existing).hexdigest()
            record_hash = _record_hash(sequence, previous_hash, record_payload)
            envelope = {
                "sequence": sequence,
                "previous_hash": previous_hash,
                "record_hash": record_hash,
                "record": record_payload,
            }
            encoded = (
                json.dumps(
                    envelope,
                    sort_keys=True,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                + "\n"
            ).encode("utf-8")

            with manifest.open("ab") as stream:
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
        finally:
            _release_file_lock(lock_stream)
