from pathlib import Path

import pytest

from verification.framework.paths import SafePathError, validate_allowed_path


def test_relative_path_resolves_inside_root(tmp_path):
    artifact = tmp_path / "artifact.txt"
    artifact.write_text("ok", encoding="utf-8")
    assert validate_allowed_path(tmp_path, "artifact.txt") == artifact.resolve()


def test_path_traversal_rejected(tmp_path):
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("bad", encoding="utf-8")
    with pytest.raises(SafePathError):
        validate_allowed_path(tmp_path, "../outside.txt")


def test_missing_file_rejected(tmp_path):
    with pytest.raises(SafePathError):
        validate_allowed_path(tmp_path, "missing.txt")


def test_extension_allowlist(tmp_path):
    artifact = tmp_path / "artifact.exe"
    artifact.write_bytes(b"\0")
    with pytest.raises(SafePathError):
        validate_allowed_path(tmp_path, artifact, allowed_extensions={".json", ".txt"})


def test_directory_rejected_when_file_required(tmp_path):
    with pytest.raises(SafePathError):
        validate_allowed_path(tmp_path, ".", require_file=True)


def test_directory_allowed_when_file_not_required(tmp_path):
    assert validate_allowed_path(tmp_path, ".", require_file=False) == tmp_path.resolve()
