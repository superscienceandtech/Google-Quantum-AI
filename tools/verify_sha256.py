#!/usr/bin/env python3
"""Verify a file against an expected SHA-256 digest."""

import argparse
import errno
import hashlib
import os
import stat
import sys
from pathlib import Path
from typing import BinaryIO, Optional, Sequence


_CHUNK_SIZE = 1024 * 1024
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def parse_sha256(value: str) -> str:
    if len(value) != 64 or any(character not in _HEX_DIGITS for character in value):
        raise argparse.ArgumentTypeError(
            "expected exactly 64 hexadecimal characters for a SHA-256 digest"
        )
    return value.lower()


def sha256_stream(artifact: BinaryIO) -> str:
    """Hash bytes from the current position of an already-open binary stream."""
    digest = hashlib.sha256()
    while chunk := artifact.read(_CHUNK_SIZE):
        digest.update(chunk)
    return digest.hexdigest()


def sha256_file(path: Path) -> str:
    flags = os.O_RDONLY
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    flags |= getattr(os, "O_NONBLOCK", 0)

    descriptor = os.open(path, flags)
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise OSError(errno.EINVAL, "not a regular file", path)

        with os.fdopen(descriptor, "rb", closefd=True) as artifact:
            descriptor = -1
            digest = sha256_stream(artifact)
    finally:
        if descriptor >= 0:
            os.close(descriptor)

    return digest


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verify a file against an expected SHA-256 digest."
    )
    parser.add_argument("file", type=Path, help="file whose contents will be hashed")
    parser.add_argument(
        "expected_sha256", type=parse_sha256, help="expected SHA-256 digest"
    )
    arguments = parser.parse_args(argv)

    try:
        actual_sha256 = sha256_file(arguments.file)
    except OSError as error:
        print(
            f"ERROR: cannot read input: {error.strerror or type(error).__name__}",
            file=sys.stderr,
        )
        return 2

    if actual_sha256 != arguments.expected_sha256:
        print(
            "ERROR: SHA-256 mismatch: "
            f"expected {arguments.expected_sha256}, got {actual_sha256}",
            file=sys.stderr,
        )
        return 1

    print("OK: SHA-256 verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
