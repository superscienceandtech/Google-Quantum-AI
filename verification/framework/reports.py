from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from collections.abc import Mapping
from typing import Any


def write_immutable_json(path: str | Path, data: Mapping[str, Any]) -> Path:
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        raise FileExistsError(
            f"Refusing to overwrite existing verification report: {destination}"
        )

    payload = json.dumps(
        dict(data),
        sort_keys=True,
        indent=2,
        allow_nan=False,
    ) + "\n"

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{destination.name}.",
        suffix=".tmp",
        dir=destination.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())

        try:
            os.link(temporary, destination)
        except FileExistsError:
            raise FileExistsError(
                f"Refusing to overwrite existing verification report: {destination}"
            )
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return destination
