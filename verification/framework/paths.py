from __future__ import annotations

from pathlib import Path
from typing import Iterable


class SafePathError(ValueError):
    pass


def validate_allowed_path(
    root: str | Path,
    candidate: str | Path,
    *,
    allowed_extensions: Iterable[str] | None = None,
    require_file: bool = True,
) -> Path:
    root_path = Path(root).resolve(strict=True)
    if not root_path.is_dir():
        raise SafePathError(f"Root is not a directory: {root_path}")

    candidate_path = Path(candidate)
    if not candidate_path.is_absolute():
        candidate_path = root_path / candidate_path

    absolute_candidate = candidate_path.absolute()
    for current in (absolute_candidate, *absolute_candidate.parents):
        if current == root_path:
            break
        if current.is_symlink():
            raise SafePathError("Symbolic links are not allowed")

    try:
        resolved = candidate_path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise SafePathError(f"Path does not exist: {candidate_path}") from exc

    if resolved != root_path and root_path not in resolved.parents:
        raise SafePathError("Path escapes the allowed root")

    if require_file and not resolved.is_file():
        raise SafePathError(f"Path is not a regular file: {resolved}")

    if resolved.is_symlink():
        raise SafePathError("Symbolic links are not allowed")

    if allowed_extensions is not None:
        allowed = {item.lower() for item in allowed_extensions}
        if resolved.suffix.lower() not in allowed:
            raise SafePathError(
                f"Unexpected file extension {resolved.suffix!r}; allowed={sorted(allowed)}"
            )

    return resolved
