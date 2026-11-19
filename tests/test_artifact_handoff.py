import io
import json
import os
import tarfile
import tempfile
import unittest
import zipfile
import stat
from pathlib import Path

from tools.artifact_handoff import (
    ArchiveLimits,
    HandoffError,
    inspect_archive,
    sha256_file,
    validate_manifest,
    verify_manifest,
)


class ArtifactHandoffTests(unittest.TestCase):
    def test_hash_is_deterministic_and_reads_only(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            path.write_bytes(b"artifact")
            before = path.read_bytes()
            digest = sha256_file(path)
            self.assertEqual(digest, sha256_file(path))
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(len(digest), 64)

    def test_empty_archive_is_inspected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "empty.zip"
            with zipfile.ZipFile(path, "w"):
                pass
            report = inspect_archive(path)
            self.assertEqual(report["member_count"], 0)
            self.assertEqual(report["uncompressed_file_bytes"], 0)

    def test_invalid_archive_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.zip"
            path.write_bytes(b"not an archive")
            with self.assertRaises(HandoffError):
                inspect_archive(path)

    def test_zip_traversal_absolute_duplicate_and_collisions_are_rejected(self):
        unsafe_names = (
            "../escape",
            "/absolute",
            "C:/drive",
            "folder\\\\file",
            "duplicate",
        )
        for name in unsafe_names:
            with self.subTest(name=name), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "unsafe.zip"
                with zipfile.ZipFile(path, "w") as archive:
                    archive.writestr(name, b"x")
                if name == "duplicate":
                    with zipfile.ZipFile(path, "a") as archive:
                        archive.writestr(name, b"y")
                with self.assertRaises(HandoffError):
                    inspect_archive(path)

    def test_zip_symlink_hardlink_and_special_entries_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "symlink.zip"
            with zipfile.ZipFile(path, "w") as archive:
                info = zipfile.ZipInfo("link")
                info.external_attr = (0o120777 & 0xFFFF) << 16
                archive.writestr(info, "../target")
            with self.assertRaisesRegex(HandoffError, "symbolic link"):
                inspect_archive(path)

    def test_zip_file_directory_collision_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "collision.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("node", b"x")
                archive.writestr("node/child", b"y")
            with self.assertRaises(HandoffError):
                inspect_archive(path)

    def test_casefolding_collision_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "case.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("File", b"x")
                archive.writestr("file", b"y")
            with self.assertRaises(HandoffError):
                inspect_archive(path)

    def test_member_count_and_size_limits_are_enforced(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "limited.zip"
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("one", b"x" * 1024)
                archive.writestr("two", b"y")
            with self.assertRaises(HandoffError):
                inspect_archive(path, ArchiveLimits(max_members=1))
            with self.assertRaises(HandoffError):
                inspect_archive(path, ArchiveLimits(max_member_bytes=512))
            with self.assertRaises(HandoffError):
                inspect_archive(path, ArchiveLimits(max_total_bytes=1024))

    def test_corrupt_compressed_content_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corrupt.zip"
            with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("payload", b"x" * 100)
            data = bytearray(path.read_bytes())
            data[len(data) // 2] ^= 0xFF
            path.write_bytes(data)
            with self.assertRaises(HandoffError):
                inspect_archive(path)

    def test_tar_traversal_symlink_and_hardlink_are_rejected(self):
        for kind in ("traversal", "symlink", "hardlink"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / f"{kind}.tar"
                with tarfile.open(path, "w") as archive:
                    info = tarfile.TarInfo(
                        "../escape" if kind == "traversal" else "link"
                    )
                    if kind == "symlink":
                        info.type = tarfile.SYMTYPE
                        info.linkname = "../target"
                        archive.addfile(info)
                    elif kind == "hardlink":
                        info.type = tarfile.LNKTYPE
                        info.linkname = "target"
                        archive.addfile(info)
                    else:
                        info.size = 1
                        archive.addfile(info, io.BytesIO(b"x"))
                with self.assertRaises(HandoffError):
                    inspect_archive(path)

    def test_tar_compression_ratio_option_is_explicitly_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plain.tar"
            with tarfile.open(path, "w") as archive:
                info = tarfile.TarInfo("payload")
                info.size = 1
                archive.addfile(info, io.BytesIO(b"x"))
            with self.assertRaisesRegex(
                HandoffError, "not supported for TAR archives"
            ):
                inspect_archive(path, ArchiveLimits(max_compression_ratio=10))

    def test_manifest_validation_and_pending_hash_semantics(self):
        manifest = {
            "schema_version": 1,
            "artifacts": [{
                "artifact_id": "pending-1",
                "benchmark": "shared",
                "original_filename": "missing.bin",
                "artifact_type": "official_competition",
                "source": "authorized participant",
                "retrieval_timestamp": None,
                "file_size_bytes": None,
                "sha256": None,
                "version_or_commit": None,
                "license_or_access_restriction": "unknown",
                "classification": "official_competition",
                "verification_status": "PENDING",
                "redistribution_allowed": False,
                "secret_or_salt_included": False,
            }],
        }
        self.assertEqual(validate_manifest(manifest), manifest)
        with tempfile.TemporaryDirectory() as directory:
            report = verify_manifest(manifest, Path(directory))
            self.assertEqual(report["results"][0]["status"], "PENDING")

    def test_manifest_hash_and_size_mismatch_are_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            artifact = root / "artifact.bin"
            artifact.write_bytes(b"actual")
            manifest = {
                "schema_version": 1,
                "artifacts": [{
                    "artifact_id": "artifact-1",
                    "benchmark": "invsqrt",
                    "original_filename": "artifact.bin",
                    "artifact_type": "official_verifier",
                    "source": "authorized participant",
                    "retrieval_timestamp": "2026-11-20T00:00:00Z",
                    "file_size_bytes": 999,
                    "sha256": "0" * 64,
                    "version_or_commit": "v1",
                    "license_or_access_restriction": "unknown",
                    "classification": "official_verifier",
                    "verification_status": "UNKNOWN",
                    "redistribution_allowed": False,
                    "secret_or_salt_included": False,
                }],
            }
            report = verify_manifest(manifest, root)
            status = report["results"][0]["status"]
            self.assertIn("INTEGRITY_MISMATCH", status)
            self.assertIn("size mismatch", status)
            self.assertIn("sha256 mismatch", status)

    def test_malformed_manifest_fields_are_rejected(self):
        for mutate in (
            lambda value: value.update(schema_version=2),
            lambda value: value.update(extra=True),
        ):
            manifest = {"schema_version": 1, "artifacts": []}
            mutate(manifest)
            with self.assertRaises(HandoffError):
                validate_manifest(manifest)

    def test_manifest_filename_cannot_escape_artifact_root(self):
        manifest = {
            "schema_version": 1,
            "artifacts": [{
                "artifact_id": "escape",
                "benchmark": "shared",
                "original_filename": "../outside.bin",
                "artifact_type": "official_competition",
                "source": "authorized participant",
                "retrieval_timestamp": None,
                "file_size_bytes": None,
                "sha256": None,
                "version_or_commit": None,
                "license_or_access_restriction": "unknown",
                "classification": "official_competition",
                "verification_status": "PENDING",
                "redistribution_allowed": False,
                "secret_or_salt_included": False,
            }],
        }
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(HandoffError):
                verify_manifest(manifest, Path(directory))

    def test_manifest_rejects_hardlinked_artifact(self):
        manifest = {
            "schema_version": 1,
            "artifacts": [{
                "artifact_id": "hardlink",
                "benchmark": "shared",
                "original_filename": "artifact.bin",
                "artifact_type": "official_competition",
                "source": "authorized participant",
                "retrieval_timestamp": None,
                "file_size_bytes": 8,
                "sha256": "c7c5c1d70c5dec4416ab6158afd0b223ef40c29b1dc1f97ed9428b94d4cadb1c",
                "version_or_commit": None,
                "license_or_access_restriction": "unknown",
                "classification": "official_competition",
                "verification_status": "PENDING",
                "redistribution_allowed": False,
                "secret_or_salt_included": False,
            }],
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.bin"
            source.write_bytes(b"artifact")
            os.link(source, root / "artifact.bin")
            with self.assertRaisesRegex(HandoffError, "exactly one hard link"):
                verify_manifest(manifest, root)

    def test_boolean_manifest_schema_version_is_rejected(self):
        manifest = {"schema_version": True, "artifacts": []}
        with self.assertRaises(HandoffError):
            validate_manifest(manifest)

    def test_zip_socket_and_directory_mode_mismatches_are_rejected(self):
        for unix_type in (stat.S_IFSOCK, stat.S_IFDIR):
            with self.subTest(unix_type=unix_type), tempfile.TemporaryDirectory() as directory:
                path = Path(directory) / "special.zip"
                with zipfile.ZipFile(path, "w") as archive:
                    info = zipfile.ZipInfo("member")
                    info.external_attr = (unix_type | 0o755) << 16
                    archive.writestr(info, b"x")
                with self.assertRaises(HandoffError):
                    inspect_archive(path)


if __name__ == "__main__":
    unittest.main()
