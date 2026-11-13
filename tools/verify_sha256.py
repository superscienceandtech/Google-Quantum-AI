#!/usr/bin/env python3
"""Verify a file against an expected SHA-256 digest."""

import argparse
import hashlib
import sys
from pathlib import Path
from typing import Optional, Sequence


_CHUNK_SIZE = 1024 * 1024
_HEX_DIGITS = frozenset("0123456789abcdefABCDEF")


def parse_sha256(value: str) -> str:
    if len(value) != 64 or any(character not in _HEX_DIGITS for character in value):
        raise argparse.ArgumentTypeError(
            "expected exactly 64 hexadecimal characters for a SHA-256 digest"
        )
    return value.lower()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as artifact:
        while chunk := artifact.read(_CHUNK_SIZE):
            digest.update(chunk)
    return digest.hexdigest()


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
        print(f"ERROR: cannot read {arguments.file}: {error}", file=sys.stderr)
        return 2

    if actual_sha256 != arguments.expected_sha256:
        print(
            f"ERROR: SHA-256 mismatch for {arguments.file}: "
            f"expected {arguments.expected_sha256}, got {actual_sha256}",
            file=sys.stderr,
        )
        return 1

    print(f"OK: SHA-256 verified for {arguments.file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
