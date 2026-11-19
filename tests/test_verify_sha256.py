import argparse
import hashlib
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from tools.verify_sha256 import parse_sha256, sha256_file


SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "verify_sha256.py"


class Sha256FileTests(unittest.TestCase):
    def test_hashes_empty_and_known_sha256_vectors(self) -> None:
        vectors = (
            (b"", "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
            (b"abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            for contents, expected_digest in vectors:
                with self.subTest(contents=contents):
                    path.write_bytes(contents)
                    self.assertEqual(sha256_file(path), expected_digest)

    def test_hashes_file_contents_in_chunks(self) -> None:
        contents = bytes(range(256)) * 5000
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            path.write_bytes(contents)

            self.assertEqual(sha256_file(path), hashlib.sha256(contents).hexdigest())

    def test_accepts_uppercase_digest_and_normalizes_it(self) -> None:
        digest = hashlib.sha256(b"artifact").hexdigest().upper()

        self.assertEqual(parse_sha256(digest), digest.lower())

    def test_rejects_malformed_digest(self) -> None:
        for digest in ("", "g" * 64, "a" * 63, "a" * 65):
            with self.subTest(digest=digest):
                with self.assertRaises(argparse.ArgumentTypeError):
                    parse_sha256(digest)


class Sha256CliTests(unittest.TestCase):
    def run_cli(
        self, path: Path, expected_digest: str
    ) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(SCRIPT), str(path), expected_digest],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )

    def test_succeeds_for_matching_digest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            path.write_bytes(b"known artifact")
            digest = hashlib.sha256(b"known artifact").hexdigest()

            result = self.run_cli(path, digest)

        self.assertEqual(result.returncode, 0)
        self.assertIn("SHA-256 verified", result.stdout)
        self.assertNotIn(str(path), result.stdout)
        self.assertEqual(result.stderr, "")

    def test_fails_for_digest_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private-artifact-name.bin"
            path.write_bytes(b"known artifact")

            result = self.run_cli(path, "0" * 64)

        self.assertEqual(result.returncode, 1)
        self.assertIn("SHA-256 mismatch", result.stderr)
        self.assertNotIn(str(path), result.stderr)

    def test_reports_unreadable_or_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "missing.bin"

            result = self.run_cli(path, "0" * 64)

        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read", result.stderr)

    def test_file_error_does_not_disclose_full_path(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "private-artifact-name.bin"

            result = self.run_cli(path, "0" * 64)

        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read", result.stderr)
        self.assertNotIn(str(path), result.stderr)

    def test_reports_directory_as_read_error(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            result = self.run_cli(Path(directory), "0" * 64)

        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read", result.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are not supported")
    def test_rejects_named_pipe_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.fifo"
            os.mkfifo(path)

            result = self.run_cli(path, "0" * 64)

        self.assertEqual(result.returncode, 2)
        self.assertIn("not a regular file", result.stderr)

    @unittest.skipUnless(
        hasattr(os, "O_NOFOLLOW") and hasattr(os, "symlink"),
        "symbolic-link blocking is not supported",
    )
    def test_rejects_symbolic_link_without_following(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "target.bin"
            target.write_bytes(b"target contents")
            link = Path(directory) / "artifact.bin"
            os.symlink(target, link)

            result = self.run_cli(link, hashlib.sha256(b"target contents").hexdigest())

        self.assertEqual(result.returncode, 2)
        self.assertIn("cannot read", result.stderr)

    def test_repeated_invocations_are_deterministic_and_read_only(self) -> None:
        contents = b"immutable artifact bytes"
        expected_digest = hashlib.sha256(contents).hexdigest()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "artifact.bin"
            path.write_bytes(contents)

            first = self.run_cli(path, expected_digest)
            second = self.run_cli(path, expected_digest)

            self.assertEqual(path.read_bytes(), contents)

        self.assertEqual(first.returncode, 0)
        self.assertEqual(
            (first.returncode, first.stdout, first.stderr),
            (second.returncode, second.stdout, second.stderr),
        )

    def test_rejects_malformed_digest_before_reading_file(self) -> None:
        result = self.run_cli(Path("does-not-exist"), "bad")

        self.assertEqual(result.returncode, 2)
        self.assertIn("64 hexadecimal characters", result.stderr)
        self.assertNotIn("cannot read", result.stderr)


if __name__ == "__main__":
    unittest.main()
