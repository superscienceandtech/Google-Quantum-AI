"""Read-only manifest and archive-inspection utilities for artifact handoff."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import stat
import sys
import tarfile
import unicodedata
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Iterable, Optional


MANIFEST_VERSION = 1
CLASSIFICATIONS = frozenset({
    "official_competition",
    "official_verifier",
    "official_runtime",
    "upstream_source",
    "paper_derived_reference",
    "user_supplied",
    "locally_generated",
    "unknown",
})


class HandoffError(ValueError):
    pass


@dataclass(frozen=True)
class ArchiveLimits:
    max_members: Optional[int] = None
    max_member_bytes: Optional[int] = None
    max_total_bytes: Optional[int] = None
    max_compression_ratio: Optional[float] = None


@dataclass(frozen=True)
class ArchiveMember:
    path: str
    kind: str
    size: int
    compressed_size: Optional[int] = None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _validate_manifest_filename(value: str) -> str:
    if type(value) is not str or not value:
        raise HandoffError("manifest original_filename must be a non-empty string")
    if "\\" in value:
        raise HandoffError("manifest original_filename must use normalized POSIX separators")
    if "\x00" in value or any(ord(char) < 32 for char in value):
        raise HandoffError("manifest original_filename contains a control character")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if (
        posix.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or posix.as_posix() != value
        or any(part in ("", ".", "..") for part in posix.parts)
    ):
        raise HandoffError(
            f"manifest original_filename must be a normalized relative POSIX path: {value}"
        )
    return posix.as_posix()


def _validate_normalized_archive_path(value: str) -> str:
    if type(value) is not str or not value:
        raise HandoffError("archive member path must be a non-empty string")
    if "\\" in value:
        raise HandoffError(f"archive member uses a backslash: {value}")
    if "\x00" in value or any(ord(char) < 32 for char in value):
        raise HandoffError(f"archive member path contains a control character: {value}")
    value = unicodedata.normalize("NFC", value)
    if value in (".", "./"):
        raise HandoffError("archive member path must name a member")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if (
        posix.is_absolute()
        or windows.is_absolute()
        or windows.drive
        or posix.as_posix() != value.rstrip("/")
        or any(part in ("", ".", "..") for part in posix.parts)
    ):
        raise HandoffError(f"unsafe archive member path: {value}")
    return posix.as_posix().rstrip("/")


def _check_member_collisions(members: Iterable[ArchiveMember]) -> None:
    names: dict[str, str] = {}
    folded: dict[str, str] = {}
    for member in members:
        normalized = _validate_normalized_archive_path(member.path)
        fold = normalized.casefold()
        if normalized in names:
            raise HandoffError(f"duplicate archive path: {normalized}")
        if fold in folded:
            raise HandoffError(
                f"case-folding archive path collision: {folded[fold]} and {normalized}"
            )
        names[normalized] = member.kind
        folded[fold] = normalized

    for path, kind in names.items():
        for prefix in PurePosixPath(path).parents:
            prefix_text = prefix.as_posix()
            if prefix_text == ".":
                continue
            if prefix_text in names and names[prefix_text] == "file":
                raise HandoffError(
                    f"file/directory collision: {prefix_text} is a file and parent of {path}"
                )
        if kind == "file":
            for other in names:
                if other.startswith(path + "/"):
                    raise HandoffError(
                        f"file/directory collision: {path} is a file and parent of {other}"
                    )


def inspect_archive(path: Path, limits: Optional[ArchiveLimits] = None) -> dict:
    limits = limits or ArchiveLimits()
    for name, value in (
        ("max_members", limits.max_members),
        ("max_member_bytes", limits.max_member_bytes),
        ("max_total_bytes", limits.max_total_bytes),
    ):
        if value is not None and (type(value) is not int or value < 0):
            raise HandoffError(f"{name} must be a non-negative integer")
    if (
        limits.max_compression_ratio is not None
        and (
            type(limits.max_compression_ratio) not in (int, float)
            or not math.isfinite(limits.max_compression_ratio)
            or limits.max_compression_ratio < 0
        )
    ):
        raise HandoffError("max_compression_ratio must be a non-negative finite number")
    if not path.is_file():
        raise HandoffError("archive path must refer to a regular file")

    members: list[ArchiveMember] = []
    nested_archives = []
    total_size = 0
    try:
        if zipfile.is_zipfile(path):
            with zipfile.ZipFile(path, "r") as archive:
                infos = archive.infolist()
                if limits.max_members is not None and len(infos) > limits.max_members:
                    raise HandoffError(
                        f"archive member count {len(infos)} exceeds limit "
                        f"{limits.max_members}"
                    )
                for info in infos:
                    mode = info.external_attr >> 16
                    unix_type = stat.S_IFMT(mode)
                    if unix_type == stat.S_IFLNK:
                        raise HandoffError(f"symbolic link archive member: {info.filename}")
                    if unix_type not in (0, stat.S_IFREG, stat.S_IFDIR):
                        raise HandoffError(f"special archive member: {info.filename}")
                    name_says_directory = info.is_dir()
                    mode_says_directory = unix_type == stat.S_IFDIR
                    if name_says_directory != mode_says_directory and unix_type != 0:
                        raise HandoffError(f"directory mode mismatch: {info.filename}")
                    kind = "directory" if name_says_directory or mode_says_directory else "file"
                    normalized = _validate_normalized_archive_path(info.filename)
                    member = ArchiveMember(
                        normalized,
                        kind,
                        int(info.file_size),
                        int(info.compress_size),
                    )
                    members.append(member)
                    if kind == "file":
                        total_size += member.size
                        if (
                            limits.max_member_bytes is not None
                            and member.size > limits.max_member_bytes
                        ):
                            raise HandoffError(
                                f"archive member {normalized} size {member.size} exceeds "
                                f"limit {limits.max_member_bytes}"
                            )
                        if _looks_nested(normalized):
                            nested_archives.append(normalized)
                        with archive.open(info, "r") as source:
                            while source.read(1024 * 1024):
                                pass
        elif tarfile.is_tarfile(path):
            if limits.max_compression_ratio is not None:
                raise HandoffError(
                    "compression-ratio limits are not supported for TAR archives"
                )
            with tarfile.open(path, "r:*") as archive:
                infos = archive.getmembers()
                if limits.max_members is not None and len(infos) > limits.max_members:
                    raise HandoffError(
                        f"archive member count {len(infos)} exceeds limit "
                        f"{limits.max_members}"
                    )
                for info in infos:
                    if info.issym():
                        raise HandoffError(f"symbolic link archive member: {info.name}")
                    if info.islnk():
                        raise HandoffError(f"hardlink archive member: {info.name}")
                    if info.isdir():
                        kind = "directory"
                    elif info.isfile():
                        kind = "file"
                    else:
                        raise HandoffError(f"special archive member: {info.name}")
                    normalized = _validate_normalized_archive_path(info.name)
                    member = ArchiveMember(normalized, kind, int(info.size), None)
                    members.append(member)
                    if kind == "file":
                        total_size += member.size
                        if (
                            limits.max_member_bytes is not None
                            and member.size > limits.max_member_bytes
                        ):
                            raise HandoffError(
                                f"archive member {normalized} size {member.size} exceeds "
                                f"limit {limits.max_member_bytes}"
                            )
                        if _looks_nested(normalized):
                            nested_archives.append(normalized)
                        source = archive.extractfile(info)
                        if source is not None:
                            with source:
                                while source.read(1024 * 1024):
                                    pass
        else:
            raise HandoffError("unsupported or invalid archive")
    except (
        zipfile.BadZipFile,
        tarfile.TarError,
        EOFError,
        OSError,
        RuntimeError,
        NotImplementedError,
    ) as error:
        raise HandoffError(f"corrupt or unreadable archive: {type(error).__name__}") from error

    _check_member_collisions(members)
    if limits.max_total_bytes is not None and total_size > limits.max_total_bytes:
        raise HandoffError(
            f"archive uncompressed file size {total_size} exceeds limit "
            f"{limits.max_total_bytes}"
        )
    if limits.max_compression_ratio is not None:
        zip_members = [member for member in members if member.compressed_size is not None]
        compressed = sum(member.compressed_size or 0 for member in zip_members)
        if compressed > 0:
            ratio = total_size / compressed
            if ratio > limits.max_compression_ratio:
                raise HandoffError(
                    f"archive compression ratio {ratio:.2f} exceeds limit "
                    f"{limits.max_compression_ratio:.2f}"
                )

    return {
        "member_count": len(members),
        "file_count": sum(member.kind == "file" for member in members),
        "directory_count": sum(member.kind == "directory" for member in members),
        "uncompressed_file_bytes": total_size,
        "nested_archive_members": sorted(nested_archives),
        "members": [
            {
                "path": member.path,
                "kind": member.kind,
                "size": member.size,
            }
            for member in members
        ],
    }


def _looks_nested(path: str) -> bool:
    lower = path.casefold()
    return lower.endswith((".zip", ".tar", ".tar.gz", ".tgz", ".tar.bz2", ".tar.xz", ".7z"))


def validate_manifest(value: object) -> dict:
    if not isinstance(value, dict):
        raise HandoffError("manifest must be a JSON object")
    if set(value) != {"schema_version", "artifacts"}:
        raise HandoffError("manifest must contain exactly schema_version and artifacts")
    if type(value["schema_version"]) is not int or value["schema_version"] != MANIFEST_VERSION:
        raise HandoffError("unsupported manifest schema version")
    if not isinstance(value["artifacts"], list):
        raise HandoffError("manifest artifacts must be a list")

    required = {
        "artifact_id",
        "benchmark",
        "original_filename",
        "artifact_type",
        "source",
        "retrieval_timestamp",
        "file_size_bytes",
        "sha256",
        "version_or_commit",
        "license_or_access_restriction",
        "classification",
        "verification_status",
        "redistribution_allowed",
        "secret_or_salt_included",
    }
    identifiers: set[str] = set()
    names: set[str] = set()
    for index, artifact in enumerate(value["artifacts"]):
        if not isinstance(artifact, dict) or set(artifact) != required:
            raise HandoffError(
                f"manifest artifact {index} must contain exactly the required fields"
            )
        for key in ("artifact_id", "benchmark", "original_filename", "artifact_type",
                    "source", "license_or_access_restriction", "classification",
                    "verification_status"):
            if type(artifact[key]) is not str:
                raise HandoffError(f"manifest artifact {index} field {key} must be a string")
        if not artifact["artifact_id"]:
            raise HandoffError(f"manifest artifact {index} has an empty artifact_id")
        if artifact["artifact_id"] in identifiers:
            raise HandoffError(f"duplicate artifact_id: {artifact['artifact_id']}")
        identifiers.add(artifact["artifact_id"])
        filename = _validate_manifest_filename(artifact["original_filename"])
        if filename in names:
            raise HandoffError(
                f"duplicate original_filename: {filename}"
            )
        names.add(filename)
        if artifact["classification"] not in CLASSIFICATIONS:
            raise HandoffError(
                f"unsupported classification: {artifact['classification']}"
            )
        if type(artifact["redistribution_allowed"]) is not bool:
            raise HandoffError(
                f"manifest artifact {index} redistribution_allowed must be boolean"
            )
        if type(artifact["secret_or_salt_included"]) is not bool:
            raise HandoffError(
                f"manifest artifact {index} secret_or_salt_included must be boolean"
            )
        for nullable in ("retrieval_timestamp", "file_size_bytes", "sha256",
                         "version_or_commit"):
            if artifact[nullable] is not None and not isinstance(artifact[nullable],
                                                                 (str if nullable != "file_size_bytes" else int)):
                raise HandoffError(
                    f"manifest artifact {index} field {nullable} has invalid type"
                )
        if artifact["file_size_bytes"] is not None:
            if type(artifact["file_size_bytes"]) is not int or artifact["file_size_bytes"] < 0:
                raise HandoffError(
                    f"manifest artifact {index} file_size_bytes must be non-negative"
                )
        if artifact["sha256"] is not None:
            digest = artifact["sha256"]
            if (
                type(digest) is not str
                or len(digest) != 64
                or any(char not in "0123456789abcdef" for char in digest)
            ):
                raise HandoffError(
                    f"manifest artifact {index} sha256 must be lowercase hexadecimal"
                )
    return value


def verify_manifest(manifest: dict, artifact_root: Path) -> dict:
    validate_manifest(manifest)
    results = []
    duplicates: dict[str, str] = {}
    root = artifact_root.resolve(strict=True)
    if not root.is_dir():
        raise HandoffError("artifact_root must be a directory")
    for artifact in manifest["artifacts"]:
        digest = None
        size = None
        filename = _validate_manifest_filename(artifact["original_filename"])
        path = root / filename
        if artifact["file_size_bytes"] is None and artifact["sha256"] is None:
            status = "PENDING"
        elif not path.exists():
            status = "MISSING"
        else:
            try:
                resolved = path.resolve(strict=True)
                if resolved != path or not resolved.is_relative_to(root):
                    raise HandoffError(
                        f"artifact path escapes or is symlinked: {filename}"
                    )
                descriptor = os.open(
                    resolved,
                    os.O_RDONLY
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                )
            except (FileNotFoundError, OSError) as error:
                if isinstance(error, FileNotFoundError):
                    status = "MISSING"
                    digest = None
                    size = None
                    results.append({
                        "artifact_id": artifact["artifact_id"],
                        "status": status,
                        "sha256": None,
                        "file_size_bytes": None,
                    })
                    continue
                raise HandoffError(f"cannot open manifest artifact: {filename}") from error
            try:
                metadata = os.fstat(descriptor)
                if not stat.S_ISREG(metadata.st_mode):
                    raise HandoffError(
                        f"manifest artifact must be a regular file: {filename}"
                    )
                if metadata.st_nlink != 1:
                    raise HandoffError(
                        f"manifest artifact must have exactly one hard link: {filename}"
                    )
                size = metadata.st_size
                digest_obj = hashlib.sha256()
                with os.fdopen(descriptor, "rb", closefd=False) as source:
                    for chunk in iter(lambda: source.read(1024 * 1024), b""):
                        digest_obj.update(chunk)
                digest = digest_obj.hexdigest()
            finally:
                os.close(descriptor)
            size_match = artifact["file_size_bytes"] is None or size == artifact["file_size_bytes"]
            digest_match = artifact["sha256"] is None or digest == artifact["sha256"]
            if digest_match and size_match:
                status = "HASH_COMPUTED — AUTHENTICITY_NOT_INDEPENDENTLY_ESTABLISHED"
            else:
                status = "INTEGRITY_MISMATCH"
                if size != artifact["file_size_bytes"] and artifact["file_size_bytes"] is not None:
                    status += ": size mismatch"
                if artifact["sha256"] is not None and digest != artifact["sha256"]:
                    status += ": sha256 mismatch"
            if digest in duplicates and duplicates[digest] != artifact["original_filename"]:
                status += ": duplicate hash"
            duplicates[digest] = artifact["original_filename"]
        results.append({
            "artifact_id": artifact["artifact_id"],
            "status": status,
            "sha256": digest if "digest" in locals() else None,
            "file_size_bytes": size if "size" in locals() else None,
        })
    return {"schema_version": MANIFEST_VERSION, "results": results}


def _parse_limits(arguments: argparse.Namespace) -> ArchiveLimits:
    return ArchiveLimits(
        max_members=arguments.max_members,
        max_member_bytes=arguments.max_member_bytes,
        max_total_bytes=arguments.max_total_bytes,
        max_compression_ratio=arguments.max_compression_ratio,
    )


def _add_limit_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--max-members", type=int)
    parser.add_argument("--max-member-bytes", type=int)
    parser.add_argument("--max-total-uncompressed-bytes", dest="max_total_bytes", type=int)
    parser.add_argument("--max-compression-ratio", type=float)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Read-only competition artifact manifest and archive inspection."
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    inspect = subcommands.add_parser("inspect-archive")
    inspect.add_argument("archive", type=Path)
    _add_limit_arguments(inspect)

    verify = subcommands.add_parser("verify-manifest")
    verify.add_argument("manifest", type=Path)
    verify.add_argument("artifact_root", type=Path)

    hash_command = subcommands.add_parser("hash")
    hash_command.add_argument("artifact", type=Path)

    arguments = parser.parse_args(argv)
    try:
        if arguments.command == "inspect-archive":
            report = inspect_archive(arguments.archive, _parse_limits(arguments))
        elif arguments.command == "verify-manifest":
            with arguments.manifest.open("r", encoding="utf-8") as source:
                manifest = json.load(source)
            report = verify_manifest(manifest, arguments.artifact_root)
        else:
            path = arguments.artifact
            if not path.is_file():
                raise HandoffError("artifact path must refer to a regular file")
            report = {
                "filename": path.name,
                "file_size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "verification_status":
                    "HASH_COMPUTED — AUTHENTICITY_NOT_INDEPENDENTLY_ESTABLISHED",
            }
        print(json.dumps(report, sort_keys=True, separators=(",", ":")))
        return 0
    except (HandoffError, json.JSONDecodeError, UnicodeDecodeError, OSError) as error:
        print(f"artifact handoff failed: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
