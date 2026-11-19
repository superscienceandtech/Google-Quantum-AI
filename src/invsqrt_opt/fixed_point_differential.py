"""Opt-in differential validation against a hash-pinned mirror source model."""

from __future__ import annotations

import argparse
import ast
from dataclasses import asdict, dataclass
import dataclasses
import hashlib
from importlib import import_module
import json
import math
import platform
import time
from typing import Any
from urllib.request import urlopen

from .contract import OFFICIAL_INVSQRT_SPEC
from .fixed_point import (
    ALGORITHM_VERSION,
    FixedPointPrecision,
    REFERENCE_SOURCE_SHA256,
    fixed_point_reference,
)

REFERENCE_REPOSITORY = "qarena-ai/invsqrt"
REFERENCE_COMMIT = "6ac78ec5ace6dfd5831ccac2547041408f5d8278"
REFERENCE_PATH = "verifiers/invsqrt/nr_reference_circuit.py"
VERIFIER_PATH = "verifiers/invsqrt/verify_submission_invsqrt.py"
VERIFIER_SHA256 = "ddef520dec6b68d1cf0a6f328ddd36d79eb84570b9192cf3f7acaf073f06733a"
DEFAULT_CHUNK_SIZE = 8_192


@dataclass(frozen=True)
class DifferentialValidationResult:
    local_algorithm_version: str
    reference_repository: str
    reference_commit: str
    reference_path: str
    reference_sha256: str
    verifier_path: str
    verifier_sha256: str
    source_provenance: str
    comparison_method: str
    n_p: int
    precision: tuple[tuple[str, int], ...]
    input_minimum: int
    input_maximum: int
    input_order: str
    compared_inputs: int
    mismatch_count: int
    maximum_integer_output_difference: int
    first_mismatch: tuple[int, int, int] | None
    mismatch_examples: tuple[tuple[int, int, int], ...]
    completion_status: str
    python_version: str
    numpy_version: str
    elapsed_seconds: float

    def to_dict(self) -> dict[str, object]:
        data = asdict(self)
        data["precision"] = dict(self.precision)
        return data


def _fetch_pinned_file(path: str, expected_sha256: str) -> bytes:
    url = (
        f"https://raw.githubusercontent.com/{REFERENCE_REPOSITORY}/"
        f"{REFERENCE_COMMIT}/{path}"
    )
    with urlopen(url, timeout=30) as response:
        content = response.read()
    actual_sha256 = hashlib.sha256(content).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            f"SHA-256 mismatch for {path}: expected {expected_sha256}, "
            f"received {actual_sha256}"
        )
    return content


def _load_reference_model(source: bytes, numpy: Any) -> tuple[Any, Any]:
    tree = ast.parse(source)
    selected: list[ast.stmt] = []
    found = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id in {"POLY_A", "POLY_B"}
            for target in node.targets
        ):
            selected.append(node)
            found.update(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
                and target.id in {"POLY_A", "POLY_B"}
            )
        elif isinstance(node, ast.ClassDef) and node.name == "Precision":
            selected.append(node)
            found.add(node.name)
        elif (
            isinstance(node, ast.FunctionDef)
            and node.name == "fixed_point_model"
        ):
            selected.append(node)
            found.add(node.name)
    required = {"POLY_A", "POLY_B", "Precision", "fixed_point_model"}
    if found != required:
        raise ValueError(
            "Pinned source does not contain the expected pure-model definitions"
        )
    namespace = {
        "dataclasses": dataclasses,
        "math": math,
        "np": numpy,
    }
    exec(
        compile(ast.Module(body=selected, type_ignores=[]), "<pinned-model>", "exec"),
        namespace,
    )
    return namespace["Precision"], namespace["fixed_point_model"]


def run_full_domain_validation(
    *, chunk_size: int = DEFAULT_CHUNK_SIZE
) -> DifferentialValidationResult:
    """Compare every benchmark input against the pinned source model."""
    if (
        isinstance(chunk_size, bool)
        or not isinstance(chunk_size, int)
        or chunk_size < 1
    ):
        raise ValueError("chunk_size must be a positive integer")

    np = import_module("numpy")

    started = time.perf_counter()
    reference_bytes = _fetch_pinned_file(
        REFERENCE_PATH, REFERENCE_SOURCE_SHA256
    )
    verifier_bytes = _fetch_pinned_file(VERIFIER_PATH, VERIFIER_SHA256)
    if not verifier_bytes:
        raise ValueError("Pinned verifier source is empty")
    precision_type, reference_model = _load_reference_model(
        reference_bytes, np
    )
    reference_precision = precision_type()
    precision_values = tuple(
        sorted(asdict(reference_precision).items())
    )
    expected_precision = tuple(sorted(asdict(FixedPointPrecision()).items()))
    if precision_values != expected_precision:
        raise ValueError("Pinned reference default precision changed")

    minimum = OFFICIAL_INVSQRT_SPEC.minimum_input
    maximum = OFFICIAL_INVSQRT_SPEC.maximum_input
    compared = mismatch_count = maximum_difference = 0
    first_mismatch = None
    mismatch_examples: list[tuple[int, int, int]] = []
    for start in range(minimum, maximum + 1, chunk_size):
        stop = min(start + chunk_size, maximum + 1)
        expected = reference_model(
            OFFICIAL_INVSQRT_SPEC.np,
            reference_precision,
            np.arange(start, stop, dtype=np.int64),
        )
        for offset, reference_value in enumerate(expected):
            input_value = start + offset
            actual_value = fixed_point_reference(input_value).result_register
            reference_integer = int(reference_value)
            difference = abs(actual_value - reference_integer)
            compared += 1
            if difference:
                mismatch_count += 1
                mismatch = (input_value, actual_value, reference_integer)
                if first_mismatch is None:
                    first_mismatch = mismatch
                if len(mismatch_examples) < 20:
                    mismatch_examples.append(mismatch)
            maximum_difference = max(maximum_difference, difference)

    expected_count = maximum - minimum + 1
    complete = compared == expected_count
    return DifferentialValidationResult(
        local_algorithm_version=ALGORITHM_VERSION,
        reference_repository=REFERENCE_REPOSITORY,
        reference_commit=REFERENCE_COMMIT,
        reference_path=REFERENCE_PATH,
        reference_sha256=hashlib.sha256(reference_bytes).hexdigest(),
        verifier_path=VERIFIER_PATH,
        verifier_sha256=hashlib.sha256(verifier_bytes).hexdigest(),
        source_provenance=(
            "PUBLIC_MIRROR_HASH_VERIFIED; OFFICIAL_ORIGIN_NOT_AUTHENTICATED"
        ),
        comparison_method=(
            "Pinned pure-Python fixed_point_model AST definitions executed "
            "without circuit builder; local scalar model compared input-by-input"
        ),
        n_p=OFFICIAL_INVSQRT_SPEC.np,
        precision=precision_values,
        input_minimum=minimum,
        input_maximum=maximum,
        input_order="ascending contiguous chunks",
        compared_inputs=compared,
        mismatch_count=mismatch_count,
        maximum_integer_output_difference=maximum_difference,
        first_mismatch=first_mismatch,
        mismatch_examples=tuple(mismatch_examples),
        completion_status="COMPLETED" if complete else "INCOMPLETE",
        python_version=platform.python_version(),
        numpy_version=np.__version__,
        elapsed_seconds=round(time.perf_counter() - started, 3),
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare the fixed-point emulator with the pinned mirror model."
    )
    parser.add_argument(
        "--mode",
        choices=("FULL_DOMAIN_VALIDATION",),
        default="FULL_DOMAIN_VALIDATION",
    )
    parser.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    args = parser.parse_args()
    result = run_full_domain_validation(chunk_size=args.chunk_size)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))
    if result.completion_status != "COMPLETED" or result.mismatch_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
