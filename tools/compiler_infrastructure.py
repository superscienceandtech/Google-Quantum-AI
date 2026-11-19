"""Compiler-neutral request, artifact, execution, and verification contracts.

These contracts are infrastructure proposals, not competition APIs.
"""

from __future__ import annotations

import argparse
import contextlib
import errno
import hashlib
import hmac
import json
import math
import os
import platform
import re
import secrets
import select
import signal
import stat
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path, PurePosixPath, PureWindowsPath
from types import MappingProxyType
from typing import BinaryIO, Generator, Mapping, Optional, Protocol, Sequence, Tuple

from tools.verify_sha256 import parse_sha256, sha256_stream


_REQUEST_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")
_MAX_JSON_DEPTH = 64
_MAX_JSON_NODES = 100_000
_MAX_JSON_STRING_CHARS = 1_000_000
_MAX_ARTIFACT_REFERENCES = 10_000
_MAX_DIAGNOSTICS = 1_000
_MAX_DIAGNOSTIC_CHARS = 1_000_000
_MAX_SEED_BITS = 4096
_MAX_MANIFEST_BYTES = 16 * 1024 * 1024
_MAX_SUBPROCESS_REQUEST_BYTES = 16 * 1024 * 1024
_MAX_SUBPROCESS_RESPONSE_BYTES = 16 * 1024 * 1024
_MAX_SUBPROCESS_STDERR_BYTES = 256 * 1024
_MAX_SUBPROCESS_ENVIRONMENT_ENTRIES = 256
_MAX_SUBPROCESS_ENVIRONMENT_BYTES = 1024 * 1024
_MAX_SENSITIVE_VALUES = 256
_MAX_SENSITIVE_VALUE_CHARS = 1_000_000
_SUBPROCESS_PIPE_CHUNK_SIZE = 64 * 1024
_SUBPROCESS_JOIN_TIMEOUT_SECONDS = 2.0
_SUBPROCESS_TERMINATE_GRACE_SECONDS = 0.25
_SENSITIVE_FIELD_NAME = re.compile(
    r"(?:secret|token|password|passwd|credential|private.?key|api.?key|"
    r"access.?key|authorization|cookie|session.?id)",
    re.IGNORECASE,
)


def _freeze_json(
    value: object, depth: int = 0, node_count: Optional[list[int]] = None
) -> object:
    if node_count is None:
        node_count = [0]
    node_count[0] += 1
    if node_count[0] > _MAX_JSON_NODES:
        raise ValueError("JSON value exceeds the maximum node count")
    if depth > _MAX_JSON_DEPTH:
        raise ValueError("JSON value exceeds the maximum nesting depth")
    if type(value) is int and value.bit_length() > 4096:
        raise ValueError("JSON integer exceeds the maximum bit length")
    if value is None or type(value) in (bool, int, str):
        if type(value) is str and len(value) > _MAX_JSON_STRING_CHARS:
            raise ValueError("JSON string exceeds the maximum length")
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("JSON numbers must be finite")
        return value
    if isinstance(value, list):
        return tuple(_freeze_json(item, depth + 1, node_count) for item in value)
    if isinstance(value, Mapping):
        frozen = {}
        for key, item in value.items():
            if type(key) is not str:
                raise ValueError("JSON object keys must be strings")
            if len(key) > _MAX_JSON_STRING_CHARS:
                raise ValueError("JSON object key exceeds the maximum length")
            frozen[key] = _freeze_json(item, depth + 1, node_count)
        return MappingProxyType(frozen)
    raise ValueError(f"unsupported JSON value type: {type(value).__name__}")


def _thaw_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


def _canonical_json_bytes(value: object, byte_limit: int, limit_message: str) -> bytes:
    encoder = json.JSONEncoder(
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    chunks = []
    byte_count = 0
    for text_chunk in encoder.iterencode(value):
        byte_chunk = text_chunk.encode("utf-8")
        byte_count += len(byte_chunk)
        if byte_count > byte_limit:
            raise ValueError(limit_message)
        chunks.append(byte_chunk)
    return b"".join(chunks)


def _is_utf8_string(value: str) -> bool:
    try:
        value.encode("utf-8")
    except UnicodeEncodeError:
        return False
    return True


def _collect_sensitive_values(value: object) -> Tuple[str, ...]:
    values = set()

    def collect_leaf(item: object) -> None:
        if type(item) is str and item:
            values.add(item)
        elif isinstance(item, Mapping):
            for nested in item.values():
                collect_leaf(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                collect_leaf(nested)

    def visit(item: object) -> None:
        if isinstance(item, Mapping):
            for key, nested in item.items():
                if type(key) is str and _SENSITIVE_FIELD_NAME.search(key):
                    collect_leaf(nested)
                else:
                    visit(nested)
        elif isinstance(item, (list, tuple)):
            for nested in item:
                visit(nested)

    visit(value)
    if (
        len(values) > _MAX_SENSITIVE_VALUES
        or sum(len(item) for item in values) > _MAX_SENSITIVE_VALUE_CHARS
    ):
        raise ValueError("too many sensitive request values to redact safely")
    return tuple(sorted(values, key=lambda item: (-len(item), item)))


def _redact_text_values(text: str, values: Sequence[str]) -> str:
    for value in values:
        text = text.replace(value, "<redacted-request>")
    return text


def _redact_sensitive_json(value: object) -> object:
    if isinstance(value, Mapping):
        return {
            key: (
                "<redacted>"
                if type(key) is str and _SENSITIVE_FIELD_NAME.search(key)
                else _redact_sensitive_json(item)
            )
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [_redact_sensitive_json(item) for item in value]
    return value


def _validate_diagnostics(value: object, field_name: str) -> None:
    if (
        type(value) is not tuple
        or len(value) > _MAX_DIAGNOSTICS
        or any(type(item) is not str for item in value)
        or sum(len(item) for item in value) > _MAX_DIAGNOSTIC_CHARS
    ):
        raise ValueError(f"{field_name} must be a tuple of at most {_MAX_DIAGNOSTICS} strings")
    if any(len(item) > _MAX_JSON_STRING_CHARS for item in value):
        raise ValueError(f"{field_name} must contain bounded strings")


def _validate_relative_path(value: str) -> str:
    if (
        type(value) is not str
        or not value
        or "\\" in value
        or len(value) > 4096
        or any(ord(character) < 32 or ord(character) == 127 for character in value)
    ):
        raise ValueError("artifact path must be a non-empty relative POSIX path")
    posix_path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if (
        posix_path.is_absolute()
        or windows_path.is_absolute()
        or windows_path.drive
        or not posix_path.parts
        or posix_path.as_posix() != value
        or any(part in ("", ".", "..") for part in posix_path.parts)
    ):
        raise ValueError("artifact path must be normalized and remain relative")
    return value


@dataclass(frozen=True)
class ArtifactReference:
    """A root-relative file path and its expected SHA-256 digest."""

    path: str
    sha256: str

    def __post_init__(self) -> None:
        _validate_relative_path(self.path)
        try:
            normalized_digest = parse_sha256(self.sha256)
        except (argparse.ArgumentTypeError, TypeError) as error:
            raise ValueError("artifact sha256 must be 64 hexadecimal characters") from error
        object.__setattr__(self, "sha256", normalized_digest)

    def to_dict(self) -> dict:
        return {"path": self.path, "sha256": self.sha256}

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> ArtifactReference:
        if not isinstance(value, Mapping) or set(value) != {"path", "sha256"}:
            raise ValueError("artifact reference must contain exactly path and sha256")
        path, digest = value["path"], value["sha256"]
        if type(path) is not str or type(digest) is not str:
            raise ValueError("artifact path and sha256 must be strings")
        return cls(path, digest)


@dataclass(frozen=True)
class CompilationRequest:
    """Versioned, compiler-neutral request; options are immutable JSON data."""

    request_id: str
    inputs: Tuple[ArtifactReference, ...] = ()
    options: Mapping[str, object] = field(default_factory=dict)
    seed: Optional[int] = None
    schema_version: int = 1

    def __post_init__(self) -> None:
        if type(self.request_id) is not str or not _REQUEST_ID.fullmatch(self.request_id):
            raise ValueError("request_id must be 1-128 safe ASCII identifier characters")
        if type(self.schema_version) is not int or self.schema_version != 1:
            raise ValueError("unsupported compilation request schema_version")
        if (
            type(self.inputs) is not tuple
            or len(self.inputs) > _MAX_ARTIFACT_REFERENCES
            or any(not isinstance(item, ArtifactReference) for item in self.inputs)
        ):
            raise ValueError(
                f"inputs must be a tuple of at most {_MAX_ARTIFACT_REFERENCES} "
                "ArtifactReference values"
            )
        if not isinstance(self.options, Mapping):
            raise ValueError("options must be a JSON object")
        frozen_options = _freeze_json(self.options)
        if not isinstance(frozen_options, Mapping):
            raise ValueError("options must be a JSON object")
        object.__setattr__(self, "options", frozen_options)
        if self.seed is not None and (
            type(self.seed) is not int
            or self.seed < 0
            or self.seed.bit_length() > _MAX_SEED_BITS
        ):
            raise ValueError("seed must be a bounded non-negative integer or None")

    def to_dict(self) -> dict:
        return {
            "schema_version": self.schema_version,
            "request_id": self.request_id,
            "inputs": [item.to_dict() for item in self.inputs],
            "options": _thaw_json(self.options),
            "seed": self.seed,
        }

    @classmethod
    def from_dict(cls, value: Mapping[str, object]) -> CompilationRequest:
        required = {"schema_version", "request_id", "inputs", "options", "seed"}
        if not isinstance(value, Mapping) or set(value) != required:
            raise ValueError("compilation request has missing or unexpected fields")
        inputs = value["inputs"]
        options = value["options"]
        if type(inputs) is not list:
            raise ValueError("compilation request inputs must be a JSON array")
        if len(inputs) > _MAX_ARTIFACT_REFERENCES:
            raise ValueError("compilation request contains too many input artifacts")
        if not isinstance(options, Mapping):
            raise ValueError("compilation request options must be a JSON object")
        if any(not isinstance(item, Mapping) for item in inputs):
            raise ValueError("compilation request inputs must contain artifact objects")
        request_id = value["request_id"]
        schema_version = value["schema_version"]
        seed = value["seed"]
        if type(request_id) is not str:
            raise ValueError("request_id must be a string")
        if type(schema_version) is not int:
            raise ValueError("schema_version must be an integer")
        if seed is not None and type(seed) is not int:
            raise ValueError("seed must be an integer or None")
        return cls(
            request_id=request_id,
            inputs=tuple(ArtifactReference.from_dict(item) for item in inputs),
            options=options,
            seed=seed,
            schema_version=schema_version,
        )


class CompilationStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"


@dataclass(frozen=True)
class CompilationResult:
    status: CompilationStatus
    artifacts: Tuple[ArtifactReference, ...] = ()
    diagnostics: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, CompilationStatus):
            raise ValueError("status must be a CompilationStatus")
        if (
            type(self.artifacts) is not tuple
            or len(self.artifacts) > _MAX_ARTIFACT_REFERENCES
            or any(not isinstance(item, ArtifactReference) for item in self.artifacts)
        ):
            raise ValueError(
                f"artifacts must be a tuple of at most {_MAX_ARTIFACT_REFERENCES} "
                "ArtifactReference values"
            )
        _validate_diagnostics(self.diagnostics, "diagnostics")

    def to_dict(self) -> dict:
        return {
            "status": self.status.value,
            "artifacts": [item.to_dict() for item in self.artifacts],
            "diagnostics": list(self.diagnostics),
        }


@dataclass(frozen=True)
class ExecutionContext:
    artifact_root: Path
    output_dir: Path
    seed: Optional[int]

    def __post_init__(self) -> None:
        if not isinstance(self.artifact_root, Path) or not isinstance(self.output_dir, Path):
            raise ValueError("execution paths must be pathlib.Path values")
        if self.seed is not None and (
            type(self.seed) is not int
            or self.seed < 0
            or self.seed.bit_length() > _MAX_SEED_BITS
        ):
            raise ValueError("execution seed must be a bounded non-negative integer or None")
        root = self.artifact_root.resolve(strict=True)
        output = self.output_dir.resolve(strict=True)
        if not root.is_dir() or not output.is_dir():
            raise ValueError("execution root and output paths must be directories")
        try:
            output.relative_to(root)
        except ValueError as error:
            raise ValueError("execution output directory must be beneath artifact root") from error


class CompilerExecutor(Protocol):
    name: str
    version: str

    def compile(
        self, request: CompilationRequest, context: ExecutionContext
    ) -> CompilationResult:
        """Compile request inputs and write outputs beneath context.output_dir."""


class ProcessIsolationBackend(Protocol):
    name: str
    version: str
    containment_scope: str

    def launch(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
    ) -> subprocess.Popen:
        """Launch with stdin/stdout/stderr pipes and the backend's isolation boundary."""

    def terminate(self, process: subprocess.Popen) -> Tuple[str, ...]:
        """Stop the managed process and report cleanup outcomes."""


class SubprocessRequestError(ValueError):
    """Raised when a request cannot be represented by the local process protocol."""


class InvalidSubprocessResponse(ValueError):
    """Raised when a compiler process returns an invalid local protocol response."""


class CompilerProcessTimeout(TimeoutError):
    """Raised when a compiler process exceeds its configured wall-clock timeout."""

    def __init__(self, cleanup_diagnostics: Tuple[str, ...] = ()) -> None:
        self.cleanup_diagnostics = cleanup_diagnostics
        message = "compiler process exceeded its configured timeout"
        if cleanup_diagnostics:
            message += "; cleanup: " + "; ".join(cleanup_diagnostics)
        super().__init__(message)


def _reject_duplicate_json_keys(pairs: list[Tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON object contains a duplicate key")
        result[key] = value
    return result


def _read_bounded_pipe(
    stream: BinaryIO,
    limit: int,
    state: dict,
    stop_event: threading.Event,
    output_limit_event: threading.Event,
) -> None:
    captured = bytearray()
    overflow = False
    descriptor = stream.fileno()
    try:
        while not stop_event.is_set():
            readable, _, _ = select.select([descriptor], [], [], 0.1)
            if not readable:
                continue
            try:
                chunk = os.read(descriptor, _SUBPROCESS_PIPE_CHUNK_SIZE)
            except BlockingIOError:
                continue
            if not chunk:
                break
            remaining = limit - len(captured)
            if remaining > 0:
                captured.extend(chunk[:remaining])
            if len(chunk) > remaining:
                overflow = True
                output_limit_event.set()
    except (OSError, ValueError) as error:
        state["error"] = error
    state["bytes"] = bytes(captured)
    state["overflow"] = overflow


def _write_subprocess_input(
    stream: BinaryIO,
    payload: bytes,
    state: dict,
    stop_event: threading.Event,
) -> None:
    descriptor = stream.fileno()
    offset = 0
    try:
        while offset < len(payload) and not stop_event.is_set():
            _, writable, _ = select.select([], [descriptor], [], 0.1)
            if not writable:
                continue
            try:
                written = os.write(descriptor, payload[offset:])
            except BlockingIOError:
                continue
            if written <= 0:
                raise OSError("compiler request pipe accepted no data")
            offset += written
    except (BrokenPipeError, OSError, ValueError) as error:
        state["error"] = error
    finally:
        try:
            stream.close()
        except OSError as error:
            state["error"] = state.get("error") or error
    state["complete"] = offset == len(payload)


class SubprocessCompilerExecutor:
    """Run a configured compiler using the local JSON stdin/stdout protocol.

    The process receives a JSON envelope on stdin and must return one
    CompilationResult-shaped JSON object on stdout. This is an engineering
    interface, not an official competition protocol or a security sandbox.
    Explicit environment values are redacted from diagnostics; callers must
    identify secret command arguments with ``sensitive_arguments``.
    """

    name: str
    version: str

    def __init__(
        self,
        command: Sequence[str],
        name: str,
        version: str,
        *,
        timeout_seconds: float = 300.0,
        environment: Optional[Mapping[str, str]] = None,
        sensitive_arguments: Sequence[str] = (),
        configuration_fingerprint_key: Optional[bytes] = None,
        isolation_backend: Optional[ProcessIsolationBackend] = None,
    ) -> None:
        if (
            isinstance(command, (str, bytes))
            or not isinstance(command, Sequence)
            or not command
            or len(command) > 256
            or any(
                type(argument) is not str
                or not argument
                or "\x00" in argument
                or len(argument) > 32_768
                or not _is_utf8_string(argument)
                for argument in command
            )
        ):
            raise ValueError("command must be a non-empty sequence of bounded strings")
        if not all(
            type(value) is str and value and not any(ord(ch) < 32 for ch in value)
            for value in (name, version)
        ):
            raise ValueError("executor identity must be non-empty printable strings")
        if (
            type(timeout_seconds) not in (int, float)
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
            or timeout_seconds > 86_400
        ):
            raise ValueError("timeout_seconds must be finite and between 0 and 86400")
        if environment is None:
            environment = {}
        if not isinstance(environment, Mapping):
            raise ValueError("environment must map valid strings to strings")
        if len(environment) > _MAX_SUBPROCESS_ENVIRONMENT_ENTRIES:
            raise ValueError("environment contains too many entries")
        environment_copy = {}
        environment_bytes = 0
        for key, value in environment.items():
            if (
                type(key) is not str
                or not key
                or "=" in key
                or "\x00" in key
                or type(value) is not str
                or "\x00" in value
            ):
                raise ValueError("environment must map valid strings to strings")
            try:
                environment_bytes += (
                    len(key.encode("utf-8")) + len(value.encode("utf-8")) + 2
                )
            except UnicodeEncodeError as error:
                raise ValueError("environment must contain valid Unicode strings") from error
            if environment_bytes > _MAX_SUBPROCESS_ENVIRONMENT_BYTES:
                raise ValueError("environment exceeds the maximum size")
            environment_copy[key] = value
        if (
            isinstance(sensitive_arguments, (str, bytes))
            or not isinstance(sensitive_arguments, Sequence)
            or any(
                type(value) is not str
                or not value
                or "\x00" in value
                or not any(value in argument for argument in command[1:])
                for value in sensitive_arguments
            )
        ):
            raise ValueError("sensitive_arguments must identify configured command arguments")
        if configuration_fingerprint_key is not None and (
            type(configuration_fingerprint_key) is not bytes
            or len(configuration_fingerprint_key) < 32
        ):
            raise ValueError("configuration_fingerprint_key must contain at least 32 bytes")
        if isolation_backend is None:
            isolation_backend = PosixProcessGroupBackend()
        if not all(
            type(value) is str and value and not any(ord(ch) < 32 for ch in value)
            for value in (
                getattr(isolation_backend, "name", None),
                getattr(isolation_backend, "version", None),
                getattr(isolation_backend, "containment_scope", None),
            )
        ) or not callable(getattr(isolation_backend, "launch", None)) or not callable(
            getattr(isolation_backend, "terminate", None)
        ):
            raise ValueError("isolation_backend does not implement the process isolation contract")

        self.command = tuple(command)
        self.name = name
        self.version = version
        self.timeout_seconds = float(timeout_seconds)
        self.environment = MappingProxyType(environment_copy)
        self._sensitive_arguments = tuple(sensitive_arguments)
        self._configuration_fingerprint_key = configuration_fingerprint_key
        self.isolation_backend = isolation_backend
        self._isolation_backend_metadata = {
            "name": isolation_backend.name,
            "version": isolation_backend.version,
            "containment_scope": isolation_backend.containment_scope,
        }

    def reproducibility_metadata(
        self, request: Optional[CompilationRequest] = None
    ) -> dict:
        metadata = {
            "executable_name": PureWindowsPath(self.command[0]).name,
            "executable_sha256": None,
            "executable_identity_status": "not_captured",
            "argument_count": len(self.command) - 1,
            "arguments_recorded": False,
            "timeout_seconds": self.timeout_seconds,
            "environment_keys": sorted(self.environment),
            "environment_values_recorded": False,
            "isolation_backend": self._isolation_backend_metadata["name"],
            "isolation_backend_version": self._isolation_backend_metadata["version"],
            "containment_scope": self._isolation_backend_metadata["containment_scope"],
            "configuration_fingerprint": None,
            "fingerprint_algorithm": None,
            "canonical_request_fingerprint": None,
            "request_fingerprint_algorithm": None,
            "request_schema_version": request.schema_version if request is not None else None,
        }
        if self._configuration_fingerprint_key is not None:
            configuration = _canonical_json_bytes(
                {
                    "command": list(self.command),
                    "environment": dict(self.environment),
                    "timeout_seconds": self.timeout_seconds,
                    "executor": {"name": self.name, "version": self.version},
                    "isolation_backend": self._isolation_backend_metadata,
                },
                _MAX_SUBPROCESS_REQUEST_BYTES,
                "compiler configuration exceeds the maximum fingerprint size",
            )
            metadata["configuration_fingerprint"] = hmac.new(
                self._configuration_fingerprint_key,
                configuration,
                hashlib.sha256,
            ).hexdigest()
            metadata["fingerprint_algorithm"] = "HMAC-SHA256"
            if request is not None:
                try:
                    request_bytes = _canonical_json_bytes(
                        request.to_dict(),
                        _MAX_SUBPROCESS_REQUEST_BYTES,
                        "request exceeds the maximum fingerprint size",
                    )
                except (TypeError, ValueError, UnicodeEncodeError):
                    pass
                else:
                    metadata["canonical_request_fingerprint"] = hmac.new(
                        self._configuration_fingerprint_key,
                        request_bytes,
                        hashlib.sha256,
                    ).hexdigest()
                    metadata["request_fingerprint_algorithm"] = "HMAC-SHA256"
        return metadata

    @staticmethod
    def _terminate_process_group(process: subprocess.Popen) -> Tuple[str, ...]:
        diagnostics = []
        try:
            os.killpg(process.pid, 0)
            group_exists = True
        except ProcessLookupError:
            group_exists = False
            diagnostics.append("managed process group had already exited")
        except OSError as error:
            group_exists = error.errno == errno.EPERM
            diagnostics.append(f"process-group status failed ({type(error).__name__})")

        if group_exists:
            try:
                os.killpg(process.pid, signal.SIGTERM)
                diagnostics.append("SIGTERM sent to managed process group")
            except ProcessLookupError:
                group_exists = False
            except OSError as error:
                diagnostics.append(f"SIGTERM failed ({type(error).__name__})")
        elif process.poll() is None:
            try:
                process.terminate()
                diagnostics.append("SIGTERM sent to direct child")
            except OSError as error:
                diagnostics.append(f"direct-child SIGTERM failed ({type(error).__name__})")

        deadline = time.monotonic() + _SUBPROCESS_TERMINATE_GRACE_SECONDS
        while group_exists and time.monotonic() < deadline:
            try:
                os.killpg(process.pid, 0)
                group_exists = True
            except ProcessLookupError:
                group_exists = False
                break
            except OSError as error:
                group_exists = error.errno == errno.EPERM
                diagnostics.append(f"process-group status failed ({type(error).__name__})")
            try:
                process.wait(timeout=min(0.05, max(0.0, deadline - time.monotonic())))
            except subprocess.TimeoutExpired:
                pass
            except OSError as error:
                diagnostics.append(f"direct-child wait failed ({type(error).__name__})")
                break
            time.sleep(min(0.01, max(0.0, deadline - time.monotonic())))

        if group_exists:
            try:
                os.killpg(process.pid, signal.SIGKILL)
                diagnostics.append("SIGKILL sent to remaining managed process group")
            except ProcessLookupError:
                pass
            except OSError as error:
                diagnostics.append(f"process-group SIGKILL failed ({type(error).__name__})")
                try:
                    process.kill()
                    diagnostics.append("SIGKILL sent to direct child")
                except OSError as child_error:
                    diagnostics.append(f"direct-child SIGKILL failed ({type(child_error).__name__})")

        try:
            process.wait(timeout=_SUBPROCESS_JOIN_TIMEOUT_SECONDS)
            diagnostics.append("direct child reaped")
        except subprocess.TimeoutExpired:
            try:
                process.kill()
            except OSError as error:
                diagnostics.append(f"direct-child forced kill failed ({type(error).__name__})")
            try:
                process.wait(timeout=_SUBPROCESS_JOIN_TIMEOUT_SECONDS)
                diagnostics.append("direct child reaped after forced kill")
            except (OSError, subprocess.TimeoutExpired) as error:
                diagnostics.append(f"direct child could not be reaped ({type(error).__name__})")
        except OSError as error:
            diagnostics.append(f"direct-child reap failed ({type(error).__name__})")
        return tuple(diagnostics)

    def _redact_diagnostic(
        self,
        text: str,
        context: ExecutionContext,
        request_sensitive_values: Sequence[str] = (),
    ) -> str:
        replacements = [
            (str(context.output_dir), "<output-dir>"),
            (str(context.artifact_root), "<artifact-root>"),
        ]
        replacements.extend(
            (value, "<redacted-config>") for value in self._sensitive_arguments
        )
        replacements.extend(
            (value, "<redacted-config>")
            for value in self.environment.values()
            if value
        )
        for value, replacement in sorted(
            set(replacements), key=lambda item: (-len(item[0]), item[0])
        ):
            text = text.replace(value, replacement)
        return _redact_text_values(text, request_sensitive_values)

    def _parse_result(
        self,
        response: bytes,
        stderr: bytes,
        stderr_overflow: bool,
        context: ExecutionContext,
        request_sensitive_values: Sequence[str],
    ) -> CompilationResult:
        try:
            value = json.loads(
                response.decode("utf-8"),
                object_pairs_hook=_reject_duplicate_json_keys,
            )
            if (
                type(value) is not dict
                or set(value) != {"status", "artifacts", "diagnostics"}
                or type(value["status"]) is not str
                or type(value["artifacts"]) is not list
                or type(value["diagnostics"]) is not list
                or any(type(item) is not str for item in value["diagnostics"])
            ):
                raise ValueError("response has an invalid shape")
            status = CompilationStatus(value["status"])
            artifacts = []
            for item in value["artifacts"]:
                if not isinstance(item, Mapping):
                    raise ValueError("invalid artifact reference")
                artifacts.append(ArtifactReference.from_dict(item))
            diagnostics = tuple(
                self._redact_diagnostic(item, context, request_sensitive_values)
                for item in value["diagnostics"]
            )
            if stderr:
                stderr_text = self._redact_diagnostic(
                    stderr.decode("utf-8", errors="replace"),
                    context,
                    request_sensitive_values,
                ).strip()
                if stderr_text:
                    diagnostics += (stderr_text,)
            if stderr_overflow:
                diagnostics += ("compiler stderr was truncated",)
            return CompilationResult(status, tuple(artifacts), diagnostics)
        except (UnicodeDecodeError, json.JSONDecodeError, RecursionError, TypeError, ValueError) as error:
            raise InvalidSubprocessResponse("compiler returned invalid protocol data") from error

    def compile(
        self, request: CompilationRequest, context: ExecutionContext
    ) -> CompilationResult:
        if not isinstance(request, CompilationRequest) or not isinstance(
            context, ExecutionContext
        ):
            raise TypeError("compile requires a CompilationRequest and ExecutionContext")
        serialized_request = request.to_dict()
        envelope = {
            "protocol_version": 1,
            "request": serialized_request,
            "artifact_root": str(context.artifact_root),
            "output_dir": str(context.output_dir),
        }
        try:
            request_sensitive_values = _collect_sensitive_values(serialized_request)
            payload = _canonical_json_bytes(
                envelope,
                _MAX_SUBPROCESS_REQUEST_BYTES,
                "serialized request exceeds the maximum size",
            )
        except (TypeError, ValueError, UnicodeEncodeError) as error:
            raise SubprocessRequestError("request cannot be serialized") from error

        process = self.isolation_backend.launch(
            self.command,
            cwd=context.output_dir,
            environment=self.environment,
        )
        if process.stdin is None or process.stdout is None or process.stderr is None:
            self.isolation_backend.terminate(process)
            raise OSError("compiler process pipes could not be created")

        try:
            for pipe in (process.stdin, process.stdout, process.stderr):
                os.set_blocking(pipe.fileno(), False)
        except OSError as error:
            cleanup = self.isolation_backend.terminate(process)
            close_errors = []
            for pipe in (process.stdin, process.stdout, process.stderr):
                try:
                    pipe.close()
                except OSError as close_error:
                    close_errors.append(type(close_error).__name__)
            message = "compiler process pipes could not be configured"
            if cleanup:
                message += "; cleanup: " + "; ".join(cleanup)
            if close_errors:
                message += "; pipe close failed (" + ", ".join(close_errors) + ")"
            raise OSError(message) from error

        stdout_state: dict = {}
        stderr_state: dict = {}
        stdin_state: dict = {}
        stop_event = threading.Event()
        output_limit_event = threading.Event()
        stdout_reader = threading.Thread(
            target=_read_bounded_pipe,
            args=(
                process.stdout,
                _MAX_SUBPROCESS_RESPONSE_BYTES,
                stdout_state,
                stop_event,
                output_limit_event,
            ),
            daemon=True,
        )
        stderr_reader = threading.Thread(
            target=_read_bounded_pipe,
            args=(
                process.stderr,
                _MAX_SUBPROCESS_STDERR_BYTES,
                stderr_state,
                stop_event,
                output_limit_event,
            ),
            daemon=True,
        )
        stdin_writer = threading.Thread(
            target=_write_subprocess_input,
            args=(process.stdin, payload, stdin_state, stop_event),
            daemon=True,
        )
        timed_out = False
        cleanup_diagnostics = []
        process_error = None
        termination_attempted = False
        try:
            stdout_reader.start()
            stderr_reader.start()
            stdin_writer.start()
            deadline = time.monotonic() + self.timeout_seconds
            while process.poll() is None:
                if output_limit_event.is_set():
                    termination_attempted = True
                    cleanup_diagnostics.extend(self.isolation_backend.terminate(process))
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    timed_out = True
                    termination_attempted = True
                    cleanup_diagnostics.extend(self.isolation_backend.terminate(process))
                    break
                try:
                    process.wait(timeout=min(0.05, remaining))
                except subprocess.TimeoutExpired:
                    continue
        except BaseException as error:
            process_error = error
        finally:
            if not termination_attempted:
                termination_attempted = True
                cleanup_diagnostics.extend(self.isolation_backend.terminate(process))
            workers = (stdout_reader, stderr_reader, stdin_writer)
            for worker in workers:
                if worker.ident is not None:
                    worker.join(_SUBPROCESS_JOIN_TIMEOUT_SECONDS)
            if any(worker.is_alive() for worker in workers):
                cleanup_diagnostics.extend(self.isolation_backend.terminate(process))
                stop_event.set()
                cleanup_diagnostics.append(
                    "pipe readers stopped after bounded wait; detached pipe holders may remain"
                )
                for worker in workers:
                    if worker.ident is not None:
                        worker.join(0.5)
            stop_event.set()
            for pipe in (process.stdin, process.stdout, process.stderr):
                try:
                    pipe.close()
                except OSError as error:
                    cleanup_diagnostics.append(f"process pipe close failed ({type(error).__name__})")
            workers_alive = any(worker.is_alive() for worker in workers)

        if process_error is not None:
            raise process_error
        if timed_out:
            raise CompilerProcessTimeout(tuple(cleanup_diagnostics))
        if stdout_state.get("overflow"):
            message = "compiler stdout exceeded the maximum response size"
            if cleanup_diagnostics:
                message += "; cleanup: " + "; ".join(cleanup_diagnostics)
            raise InvalidSubprocessResponse(message)
        if stderr_state.get("overflow"):
            message = "compiler stderr exceeded the maximum captured output size"
            if cleanup_diagnostics:
                message += "; cleanup: " + "; ".join(cleanup_diagnostics)
            raise InvalidSubprocessResponse(message)
        cleanup_incomplete = any(
            "failed" in item or "could not" in item or "may remain" in item
            for item in cleanup_diagnostics
        )
        if cleanup_incomplete:
            raise OSError(
                "compiler process cleanup did not complete; cleanup: "
                + "; ".join(cleanup_diagnostics)
            )
        if workers_alive:
            raise OSError(
                "compiler process pipes did not close; cleanup: "
                + "; ".join(cleanup_diagnostics)
            )
        if process.returncode != 0:
            diagnostics = [f"compiler process exited with status {process.returncode}"]
            if stderr_state.get("bytes"):
                stderr_text = self._redact_diagnostic(
                    stderr_state["bytes"].decode("utf-8", errors="replace"),
                    context,
                    request_sensitive_values,
                ).strip()
                if stderr_text:
                    diagnostics.append(stderr_text)
            if stderr_state.get("overflow"):
                diagnostics.append("compiler stderr was truncated")
            return CompilationResult(CompilationStatus.FAILED, diagnostics=tuple(diagnostics))
        if stdin_state.get("error") is not None:
            raise InvalidSubprocessResponse("compiler closed stdin before reading the request")
        if not stdin_state.get("complete", False):
            raise InvalidSubprocessResponse("compiler request was not completely delivered")
        if stdout_state.get("error") is not None or stderr_state.get("error") is not None:
            raise OSError("could not read compiler process output")
        return self._parse_result(
            stdout_state.get("bytes", b""),
            stderr_state.get("bytes", b""),
            stderr_state.get("overflow", False),
            context,
            request_sensitive_values,
        )


class PosixProcessGroupBackend:
    """Provide process-group lifecycle management, not a security sandbox."""

    name = "posix-process-group"
    version = "1"
    containment_scope = "same-session-process-group"

    def __init__(self) -> None:
        if os.name != "posix" or not hasattr(os, "killpg"):
            raise OSError(
                errno.ENOTSUP,
                "process-group timeout enforcement is unavailable on this platform",
            )

    def launch(
        self,
        command: Sequence[str],
        *,
        cwd: Path,
        environment: Mapping[str, str],
    ) -> subprocess.Popen:
        return subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
            cwd=cwd,
            env=dict(environment),
            close_fds=True,
            start_new_session=True,
        )

    def terminate(self, process: subprocess.Popen) -> Tuple[str, ...]:
        return SubprocessCompilerExecutor._terminate_process_group(process)


class VerificationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    UNAVAILABLE = "unavailable"
    NOT_EXECUTED = "not_executed"
    ERROR = "error"


@dataclass(frozen=True)
class VerificationRequest:
    compilation_request: CompilationRequest
    compilation_result: CompilationResult
    verified_artifacts: Mapping[ArtifactReference, BinaryIO] = field(
        default_factory=dict,
        compare=False,
        repr=False,
    )

    def __post_init__(self) -> None:
        if not isinstance(self.compilation_request, CompilationRequest):
            raise ValueError("compilation_request must be a CompilationRequest")
        if not isinstance(self.compilation_result, CompilationResult):
            raise ValueError("compilation_result must be a CompilationResult")
        if not isinstance(self.verified_artifacts, Mapping) or any(
            not isinstance(reference, ArtifactReference)
            or not callable(getattr(stream, "read", None))
            or not callable(getattr(stream, "seek", None))
            for reference, stream in self.verified_artifacts.items()
        ):
            raise ValueError("verified_artifacts must map artifact references to readable streams")
        object.__setattr__(
            self,
            "verified_artifacts",
            MappingProxyType(dict(self.verified_artifacts)),
        )


@dataclass(frozen=True)
class VerificationResult:
    status: VerificationStatus
    diagnostics: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.status, VerificationStatus):
            raise ValueError("status must be a VerificationStatus")
        _validate_diagnostics(self.diagnostics, "diagnostics")

    def to_dict(self) -> dict:
        return {"status": self.status.value, "diagnostics": list(self.diagnostics)}


class CompilerVerifier(Protocol):
    name: str
    version: str

    def verify(
        self, request: VerificationRequest, context: ExecutionContext
    ) -> VerificationResult:
        """Verify compiler-neutral artifacts; never implies official acceptance."""


class RunStatus(str, Enum):
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    BLOCKED = "blocked"


class FailureCategory(str, Enum):
    INVALID_REQUEST = "invalid_request"
    UNSUPPORTED_OPERATION = "unsupported_operation"
    MISSING_DEPENDENCY = "missing_dependency"
    MISSING_ARTIFACT = "missing_artifact"
    MISSING_EXECUTOR = "missing_executor"
    ENVIRONMENT_FAILURE = "environment_failure"
    EXECUTION_FAILURE = "execution_failure"
    INVALID_RESULT = "invalid_result"
    MISSING_EXECUTABLE = "missing_executable"
    PROCESS_TIMEOUT = "process_timeout"
    ARTIFACT_FAILURE = "artifact_failure"
    INTEGRITY_MISMATCH = "integrity_mismatch"
    SERIALIZATION_FAILURE = "serialization_failure"
    VERIFICATION_FAILURE = "verification_failure"
    VERIFIER_ERROR = "verifier_error"
    MANIFEST_FAILURE = "manifest_failure"


@dataclass(frozen=True)
class RunFailure:
    category: FailureCategory
    message: str

    def __post_init__(self) -> None:
        if not isinstance(self.category, FailureCategory):
            raise ValueError("category must be a FailureCategory")
        if type(self.message) is not str or not self.message:
            raise ValueError("failure message must be a non-empty string")


@dataclass(frozen=True)
class ExecutionReport:
    request_id: Optional[str]
    status: RunStatus
    compilation: Optional[CompilationResult]
    verification: VerificationResult
    manifest: Optional[ArtifactReference]
    failure: Optional[RunFailure]

    def __post_init__(self) -> None:
        if self.request_id is not None and type(self.request_id) is not str:
            raise ValueError("request_id must be a string or None")
        if not isinstance(self.status, RunStatus):
            raise ValueError("status must be a RunStatus")
        if not isinstance(self.verification, VerificationResult):
            raise ValueError("verification must be a VerificationResult")
        if self.compilation is not None and not isinstance(self.compilation, CompilationResult):
            raise ValueError("compilation must be a CompilationResult or None")
        if self.manifest is not None and not isinstance(self.manifest, ArtifactReference):
            raise ValueError("manifest must be an ArtifactReference or None")
        if self.failure is not None and not isinstance(self.failure, RunFailure):
            raise ValueError("failure must be a RunFailure or None")
        if self.status is RunStatus.SUCCEEDED and (
            self.compilation is None
            or self.compilation.status is not CompilationStatus.SUCCEEDED
            or self.verification.status is not VerificationStatus.PASSED
            or self.manifest is None
            or self.failure is not None
        ):
            raise ValueError("successful reports require compilation, verification, and a manifest")
        if self.status is not RunStatus.SUCCEEDED and self.failure is None:
            raise ValueError("failed or blocked reports require a failure")

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "status": self.status.value,
            "compilation": self.compilation.to_dict() if self.compilation else None,
            "verification": self.verification.to_dict(),
            "manifest": self.manifest.to_dict() if self.manifest else None,
            "failure": (
                {"category": self.failure.category.value, "message": self.failure.message}
                if self.failure
                else None
            ),
        }


class ArtifactIntegrityError(ValueError):
    """Raised when an artifact does not match its declared digest."""


class ManifestPublicationError(OSError):
    """Raised when manifest publication or cleanup cannot be reported complete."""

    def __init__(
        self,
        message: str,
        reference: Optional[ArtifactReference] = None,
        *,
        uncertain: bool = True,
    ) -> None:
        super().__init__(errno.EIO, message)
        self.reference = reference
        self.uncertain = uncertain


class ArtifactStore:
    """Access root-relative artifacts through a retained directory descriptor."""

    def __init__(self, root: Path) -> None:
        if not isinstance(root, Path):
            raise TypeError("artifact root must be a pathlib.Path")
        required_dir_fd_apis = (os.open, os.mkdir, os.link, os.unlink)
        if (
            any(api not in os.supports_dir_fd for api in required_dir_fd_apis)
            or not hasattr(os, "O_NOFOLLOW")
            or not hasattr(os, "O_DIRECTORY")
        ):
            raise OSError(errno.ENOTSUP, "descriptor-relative artifact access is unavailable")
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_DIRECTORY", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(root, flags)
        try:
            if not stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise ValueError("artifact root must be a directory")
        except BaseException:
            os.close(descriptor)
            raise
        self.root = Path(os.path.abspath(root))
        self._root_fd = descriptor
        self._closed = False

    def close(self) -> None:
        if not self._closed:
            os.close(self._root_fd)
            self._closed = True

    def __enter__(self) -> ArtifactStore:
        if self._closed:
            raise ValueError("artifact store is closed")
        return self

    def __exit__(self, *_exc_info: object) -> None:
        del _exc_info
        self.close()

    def __del__(self) -> None:
        try:
            self.close()
        except (AttributeError, OSError):
            pass

    @staticmethod
    def _directory_flags() -> int:
        return (
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0)
        )

    def _open_directory(self, parts: Tuple[str, ...]) -> int:
        if self._closed:
            raise ValueError("artifact store is closed")
        descriptor = os.dup(self._root_fd)
        try:
            for part in parts:
                next_descriptor = os.open(
                    part, self._directory_flags(), dir_fd=descriptor
                )
                os.close(descriptor)
                descriptor = next_descriptor
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise

    def _open_artifact(self, reference: ArtifactReference) -> int:
        if self._closed:
            raise ValueError("artifact store is closed")
        if not isinstance(reference, ArtifactReference):
            raise TypeError("reference must be an ArtifactReference")
        relative_path = _validate_relative_path(reference.path)
        parts = PurePosixPath(relative_path).parts
        parent_fd = self._open_directory(parts[:-1])
        flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0)
        flags |= getattr(os, "O_NOFOLLOW", 0)
        flags |= getattr(os, "O_NONBLOCK", 0)
        try:
            descriptor = os.open(parts[-1], flags, dir_fd=parent_fd)
        finally:
            os.close(parent_fd)
        try:
            if not stat.S_ISREG(os.fstat(descriptor).st_mode):
                raise OSError(errno.EINVAL, "not a regular file", reference.path)
        except BaseException:
            os.close(descriptor)
            raise
        return descriptor

    def _hash_descriptor(self, descriptor: int) -> str:
        before = os.fstat(descriptor)
        os.lseek(descriptor, 0, os.SEEK_SET)
        with os.fdopen(descriptor, "rb", closefd=False) as artifact:
            actual_digest = sha256_stream(artifact)
        os.lseek(descriptor, 0, os.SEEK_SET)
        after = os.fstat(descriptor)
        before_state = (
            before.st_dev,
            before.st_ino,
            before.st_size,
            before.st_mtime_ns,
            before.st_ctime_ns,
        )
        after_state = (
            after.st_dev,
            after.st_ino,
            after.st_size,
            after.st_mtime_ns,
            after.st_ctime_ns,
        )
        if before_state != after_state:
            raise OSError(errno.EBUSY, "artifact changed while hashing")
        return actual_digest

    @contextlib.contextmanager
    def open_verified(self, reference: ArtifactReference) -> Generator[BinaryIO, None, None]:
        """Yield a read-only stream and revalidate it when the consumer is done."""
        if not isinstance(reference, ArtifactReference):
            raise TypeError("reference must be an ArtifactReference")
        descriptor = self._open_artifact(reference)
        try:
            if self._hash_descriptor(descriptor) != reference.sha256:
                raise ArtifactIntegrityError(
                    f"SHA-256 mismatch for artifact {reference.path}"
                )
            with os.fdopen(descriptor, "rb", closefd=False) as artifact:
                try:
                    yield artifact
                finally:
                    if self._hash_descriptor(descriptor) != reference.sha256:
                        raise ArtifactIntegrityError(
                            f"artifact changed while in use: {reference.path}"
                        )
        finally:
            os.close(descriptor)

    def verify(self, reference: ArtifactReference) -> str:
        descriptor = self._open_artifact(reference)
        try:
            actual_digest = self._hash_descriptor(descriptor)
        finally:
            os.close(descriptor)
        if actual_digest != reference.sha256:
            raise ArtifactIntegrityError(f"SHA-256 mismatch for artifact {reference.path}")
        return actual_digest

    def reference(self, path: Path) -> ArtifactReference:
        if not isinstance(path, Path):
            raise TypeError("artifact path must be a pathlib.Path")
        try:
            relative = path.absolute().relative_to(self.root)
        except ValueError as error:
            raise ValueError("artifact path resolves outside the artifact root") from error
        reference = ArtifactReference(relative.as_posix(), "0" * 64)
        descriptor = self._open_artifact(reference)
        try:
            digest = self._hash_descriptor(descriptor)
        finally:
            os.close(descriptor)
        return ArtifactReference(relative.as_posix(), digest)

    def prepare_run(self, request_id: str) -> Tuple[Path, Path]:
        if type(request_id) is not str or not _REQUEST_ID.fullmatch(request_id):
            raise ValueError("request_id must be 1-128 safe ASCII identifier characters")
        if self._closed:
            raise ValueError("artifact store is closed")
        try:
            os.mkdir("runs", dir_fd=self._root_fd)
        except FileExistsError:
            pass
        runs_fd = os.open("runs", self._directory_flags(), dir_fd=self._root_fd)
        try:
            os.mkdir(request_id, dir_fd=runs_fd)
            run_fd = os.open(request_id, self._directory_flags(), dir_fd=runs_fd)
        finally:
            os.close(runs_fd)
        try:
            os.mkdir("outputs", dir_fd=run_fd)
        except BaseException:
            os.close(run_fd)
            raise
        os.close(run_fd)
        run_dir = self.root / "runs" / request_id
        output_dir = run_dir / "outputs"
        return run_dir, output_dir

    def write_manifest(self, run_dir: Path, manifest: Mapping[str, object]) -> ArtifactReference:
        if not isinstance(manifest, Mapping):
            raise TypeError("manifest must be a mapping")
        try:
            relative = run_dir.absolute().relative_to(self.root)
        except ValueError as error:
            raise ValueError("manifest directory resolves outside the artifact root") from error
        _validate_relative_path(relative.as_posix())
        serialized = _canonical_json_bytes(
            _thaw_json(_freeze_json(manifest)),
            _MAX_MANIFEST_BYTES,
            "manifest exceeds the maximum serialized size",
        )
        reference = ArtifactReference(
            (relative / "manifest.json").as_posix(),
            hashlib.sha256(serialized).hexdigest(),
        )

        run_fd = self._open_directory(relative.parts)
        temporary_name = f".manifest-{secrets.token_hex(16)}.tmp"
        temporary_fd = -1
        published = False
        publication_error: Optional[BaseException] = None
        publication_cause: Optional[BaseException] = None
        try:
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_CLOEXEC", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0)
            temporary_fd = os.open(temporary_name, flags, 0o600, dir_fd=run_fd)
            with os.fdopen(temporary_fd, "wb", closefd=True) as output:
                temporary_fd = -1
                output.write(serialized)
                output.flush()
                os.fsync(output.fileno())
            os.link(
                temporary_name,
                "manifest.json",
                src_dir_fd=run_fd,
                dst_dir_fd=run_fd,
                follow_symlinks=False,
            )
            published = True
            os.unlink(temporary_name, dir_fd=run_fd)
            os.fsync(run_fd)
        except BaseException as error:
            cleanup_error = None
            if temporary_fd >= 0:
                try:
                    os.close(temporary_fd)
                except OSError as close_error:
                    cleanup_error = close_error
                temporary_fd = -1
            try:
                os.unlink(temporary_name, dir_fd=run_fd)
            except FileNotFoundError:
                pass
            except OSError as unlink_error:
                cleanup_error = cleanup_error or unlink_error
            if published:
                try:
                    os.unlink("manifest.json", dir_fd=run_fd)
                except FileNotFoundError:
                    pass
                except OSError as unlink_error:
                    cleanup_error = cleanup_error or unlink_error
                try:
                    os.fsync(run_fd)
                except OSError as sync_error:
                    cleanup_error = cleanup_error or sync_error
            if cleanup_error is not None:
                publication_error = ManifestPublicationError(
                    "manifest publication/cleanup state is uncertain "
                    f"({type(cleanup_error).__name__})"
                )
                publication_cause = error
            else:
                publication_error = error
        finally:
            try:
                os.close(run_fd)
            except OSError as close_error:
                if publication_error is None:
                    if published:
                        publication_error = ManifestPublicationError(
                            "manifest was published but its directory descriptor "
                            "could not be closed",
                            reference,
                            uncertain=False,
                        )
                    else:
                        publication_error = close_error
                else:
                    previous_error = publication_error
                    publication_error = ManifestPublicationError(
                        "manifest operation and directory descriptor cleanup state "
                        "is uncertain "
                        f"({type(close_error).__name__})"
                    )
                    publication_cause = previous_error
        if publication_error is not None:
            if publication_cause is not None:
                raise publication_error from publication_cause
            raise publication_error
        return reference


def _report(
    request_id: Optional[str],
    status: RunStatus,
    compilation: Optional[CompilationResult] = None,
    verification_status: VerificationStatus = VerificationStatus.NOT_EXECUTED,
    manifest: Optional[ArtifactReference] = None,
    failure: Optional[RunFailure] = None,
    verification_diagnostics: Tuple[str, ...] = (),
) -> ExecutionReport:
    return ExecutionReport(
        request_id=request_id,
        status=status,
        compilation=compilation,
        verification=VerificationResult(verification_status, verification_diagnostics),
        manifest=manifest,
        failure=failure,
    )


def _artifact_failure_category(error: Exception) -> FailureCategory:
    if isinstance(error, ArtifactIntegrityError):
        return FailureCategory.INTEGRITY_MISMATCH
    if isinstance(error, FileNotFoundError):
        return FailureCategory.MISSING_ARTIFACT
    if isinstance(error, OSError):
        return FailureCategory.ENVIRONMENT_FAILURE
    return FailureCategory.ARTIFACT_FAILURE


def _component_failure_category(
    error: Exception, default: FailureCategory
) -> FailureCategory:
    if isinstance(error, CompilerProcessTimeout):
        return FailureCategory.PROCESS_TIMEOUT
    if isinstance(error, FileNotFoundError):
        return FailureCategory.MISSING_EXECUTABLE
    if isinstance(error, SubprocessRequestError):
        return FailureCategory.INVALID_REQUEST
    if isinstance(error, InvalidSubprocessResponse):
        return FailureCategory.INVALID_RESULT
    if isinstance(error, ImportError):
        return FailureCategory.MISSING_DEPENDENCY
    if isinstance(error, NotImplementedError):
        return FailureCategory.UNSUPPORTED_OPERATION
    if isinstance(error, OSError):
        return FailureCategory.ENVIRONMENT_FAILURE
    return default


def _executor_manifest_data(
    name: Optional[str],
    version: Optional[str],
    configuration: Optional[Mapping[str, object]],
) -> dict:
    record: dict[str, object] = {"name": name, "version": version}
    if configuration is not None:
        record["configuration"] = dict(configuration)
    return record


def _reproducibility_metadata(
    executor_configuration: Optional[Mapping[str, object]] = None,
) -> dict:
    metadata = {
        "level": 0,
        "level_name": "result_recorded",
        "configuration_complete": False,
        "executable_identity_complete": False,
        "independent_replay": False,
        "canonical_request_fingerprint": None,
        "request_fingerprint_algorithm": None,
    }
    if executor_configuration is not None:
        metadata["canonical_request_fingerprint"] = executor_configuration.get(
            "canonical_request_fingerprint"
        )
        metadata["request_fingerprint_algorithm"] = executor_configuration.get(
            "request_fingerprint_algorithm"
        )
    return metadata


def _failure_manifest(
    artifact_store: ArtifactStore,
    run_dir: Path,
    request: CompilationRequest,
    executor_name: Optional[str],
    executor_version: Optional[str],
    category: FailureCategory,
    message: str,
    compilation: Optional[CompilationResult] = None,
    executor_configuration: Optional[Mapping[str, object]] = None,
) -> Tuple[Optional[ArtifactReference], Optional[str]]:
    manifest = {
        "schema_version": 1,
        "run_status": RunStatus.FAILED.value,
        "runtime": {
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform": sys.platform,
            "architecture": platform.machine(),
        },
        "reproducibility": _reproducibility_metadata(executor_configuration),
        "request": request.to_dict(),
        "executor": _executor_manifest_data(
            executor_name, executor_version, executor_configuration
        ),
        "compilation": compilation.to_dict() if compilation is not None else None,
        "verification": {
            "status": VerificationStatus.NOT_EXECUTED.value,
            "diagnostics": [],
        },
        "failure": {"category": category.value, "message": message},
    }
    try:
        return artifact_store.write_manifest(run_dir, manifest), None
    except ManifestPublicationError as error:
        if error.uncertain:
            return None, "publication state is uncertain"
        return error.reference, "published but directory descriptor close failed"
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        return None, f"unavailable ({type(error).__name__})"


def run_compilation(
    request: CompilationRequest,
    executor: Optional[CompilerExecutor],
    verifier: Optional[CompilerVerifier],
    artifact_store: ArtifactStore,
) -> ExecutionReport:
    """Run one compile/verify lifecycle; success requires verification to pass."""

    if not isinstance(request, CompilationRequest):
        return _report(
            None,
            RunStatus.FAILED,
            failure=RunFailure(FailureCategory.INVALID_REQUEST, "request has an invalid type"),
        )
    try:
        request_sensitive_values = _collect_sensitive_values(request.to_dict())
    except ValueError:
        return _report(
            request.request_id,
            RunStatus.FAILED,
            failure=RunFailure(
                FailureCategory.INVALID_REQUEST,
                "request contains too many sensitive values to redact safely",
            ),
        )
    if not isinstance(artifact_store, ArtifactStore):
        return _report(
            request.request_id,
            RunStatus.FAILED,
            failure=RunFailure(
                FailureCategory.ARTIFACT_FAILURE,
                "artifact store has an invalid type",
            ),
        )
    if executor is None:
        return _report(
            request.request_id,
            RunStatus.BLOCKED,
            failure=RunFailure(FailureCategory.MISSING_EXECUTOR, "no compiler executor configured"),
        )

    try:
        for input_reference in request.inputs:
            artifact_store.verify(input_reference)
        run_dir, output_dir = artifact_store.prepare_run(request.request_id)
    except (OSError, RuntimeError, ValueError, TypeError) as error:
        return _report(
            request.request_id,
            RunStatus.FAILED,
            failure=RunFailure(_artifact_failure_category(error), type(error).__name__),
        )

    executor_name = None
    executor_version = None
    executor_configuration = None
    try:
        context = ExecutionContext(artifact_store.root, output_dir, request.seed)
        executor_name = executor.name
        executor_version = executor.version
        if not all(
            type(value) is str and value and not any(ord(ch) < 32 for ch in value)
            for value in (executor_name, executor_version)
        ):
            raise ValueError("executor identity must be non-empty printable strings")
        if isinstance(executor, SubprocessCompilerExecutor):
            executor_configuration = executor.reproducibility_metadata(request)
        compilation = executor.compile(request, context)
    except Exception as error:
        category = _component_failure_category(error, FailureCategory.EXECUTION_FAILURE)
        if isinstance(error, CompilerProcessTimeout):
            message = str(error)
        elif isinstance(error, FileNotFoundError):
            message = "configured compiler executable was not found"
        elif isinstance(error, SubprocessRequestError):
            message = "subprocess request could not be serialized"
        elif isinstance(error, InvalidSubprocessResponse):
            message = str(error)
        else:
            message = f"executor raised {type(error).__name__}"
        failure = RunFailure(category, message)
        failure_manifest, manifest_error = _failure_manifest(
            artifact_store,
            run_dir,
            request,
            executor_name,
            executor_version,
            category,
            failure.message,
            executor_configuration=executor_configuration,
        )
        if manifest_error is not None:
            failure = RunFailure(
                category,
                f"{failure.message}; failure manifest {manifest_error}",
            )
        return _report(
            request.request_id,
            RunStatus.FAILED,
            manifest=failure_manifest,
            failure=failure,
        )

    if not isinstance(compilation, CompilationResult):
        failure = RunFailure(FailureCategory.INVALID_RESULT, "executor returned an invalid result")
        failure_manifest, manifest_error = _failure_manifest(
            artifact_store,
            run_dir,
            request,
            executor_name,
            executor_version,
            failure.category,
            failure.message,
            executor_configuration=executor_configuration,
        )
        if manifest_error is not None:
            failure = RunFailure(
                failure.category,
                f"{failure.message}; failure manifest {manifest_error}",
            )
        return _report(
            request.request_id,
            RunStatus.FAILED,
            manifest=failure_manifest,
            failure=failure,
        )
    compilation = CompilationResult(
        compilation.status,
        compilation.artifacts,
        tuple(
            _redact_text_values(item, request_sensitive_values)
            for item in compilation.diagnostics
        ),
    )
    if compilation.status is CompilationStatus.FAILED:
        failure = RunFailure(FailureCategory.EXECUTION_FAILURE, "compilation reported failure")
        failure_manifest, manifest_error = _failure_manifest(
            artifact_store,
            run_dir,
            request,
            executor_name,
            executor_version,
            failure.category,
            failure.message,
            compilation,
            executor_configuration,
        )
        if manifest_error is not None:
            failure = RunFailure(
                failure.category,
                f"{failure.message}; failure manifest {manifest_error}",
            )
        return _report(
            request.request_id,
            RunStatus.FAILED,
            compilation,
            manifest=failure_manifest,
            failure=failure,
        )

    try:
        for input_reference in request.inputs:
            artifact_store.verify(input_reference)
        output_prefix = (
            output_dir.relative_to(artifact_store.root).as_posix() + "/"
        )
        for output_reference in compilation.artifacts:
            if not output_reference.path.startswith(output_prefix):
                raise ValueError("compiler output must remain beneath its output directory")
            artifact_store.verify(output_reference)
    except (OSError, RuntimeError, ValueError, TypeError) as error:
        category = _artifact_failure_category(error)
        failure = RunFailure(category, type(error).__name__)
        failure_manifest, manifest_error = _failure_manifest(
            artifact_store,
            run_dir,
            request,
            executor_name,
            executor_version,
            category,
            failure.message,
            compilation,
            executor_configuration,
        )
        if manifest_error is not None:
            failure = RunFailure(
                category,
                f"{failure.message}; failure manifest {manifest_error}",
            )
        return _report(
            request.request_id,
            RunStatus.FAILED,
            compilation,
            manifest=failure_manifest,
            failure=failure,
        )

    verification = VerificationResult(VerificationStatus.UNAVAILABLE)
    verifier_failure_category = FailureCategory.VERIFIER_ERROR
    verifier_name = None
    verifier_version = None
    integrity_failure = None
    if verifier is not None:
        try:
            verifier_name = verifier.name
            verifier_version = verifier.version
            if not all(
                type(value) is str and value and not any(ord(ch) < 32 for ch in value)
                for value in (verifier_name, verifier_version)
            ):
                raise ValueError("verifier identity must be non-empty printable strings")
            with contextlib.ExitStack() as stack:
                verified_artifacts = {}
                artifact_access_error = None
                references = dict.fromkeys((*request.inputs, *compilation.artifacts))
                for reference in references:
                    try:
                        verified_artifacts[reference] = stack.enter_context(
                            artifact_store.open_verified(reference)
                        )
                    except (OSError, RuntimeError, TypeError, ValueError) as error:
                        artifact_access_error = error
                        break
                if artifact_access_error is None:
                    verification = verifier.verify(
                        VerificationRequest(request, compilation, verified_artifacts),
                        context,
                    )
                    if not isinstance(verification, VerificationResult):
                        raise TypeError("verifier returned an invalid result")
            if artifact_access_error is not None:
                integrity_failure = RunFailure(
                    _artifact_failure_category(artifact_access_error),
                    type(artifact_access_error).__name__,
                )
                verification = VerificationResult(
                    VerificationStatus.ERROR,
                    ("verified artifact access failed during verifier handoff",),
                )
        except ArtifactIntegrityError as error:
            integrity_failure = RunFailure(
                FailureCategory.INTEGRITY_MISMATCH,
                type(error).__name__,
            )
            verification = VerificationResult(
                VerificationStatus.ERROR,
                ("verified artifact changed during verifier handoff",),
            )
        except Exception as error:
            verifier_failure_category = _component_failure_category(
                error, FailureCategory.VERIFIER_ERROR
            )
            verification = VerificationResult(
                VerificationStatus.ERROR,
                (f"verifier raised {type(error).__name__}",),
            )
    verification = VerificationResult(
        verification.status,
        tuple(
            _redact_text_values(item, request_sensitive_values)
            for item in verification.diagnostics
        ),
    )

    if integrity_failure is None:
        try:
            for input_reference in request.inputs:
                artifact_store.verify(input_reference)
            for output_reference in compilation.artifacts:
                artifact_store.verify(output_reference)
        except (OSError, RuntimeError, ValueError, TypeError) as error:
            integrity_failure = RunFailure(
                _artifact_failure_category(error), type(error).__name__
            )

    if integrity_failure is not None:
        run_status = RunStatus.FAILED
    elif verification.status is VerificationStatus.PASSED:
        run_status = RunStatus.SUCCEEDED
    elif verification.status in (
        VerificationStatus.UNAVAILABLE,
        VerificationStatus.NOT_EXECUTED,
    ):
        run_status = RunStatus.BLOCKED
    else:
        run_status = RunStatus.FAILED

    manifest_data = {
        "schema_version": 1,
        "run_status": run_status.value,
        "runtime": {
            "python_implementation": platform.python_implementation(),
            "python_version": platform.python_version(),
            "platform": sys.platform,
            "architecture": platform.machine(),
        },
        "reproducibility": _reproducibility_metadata(executor_configuration),
        "request": _redact_sensitive_json(request.to_dict()),
        "executor": _executor_manifest_data(
            executor_name, executor_version, executor_configuration
        ),
        "compilation": {
            "status": compilation.status.value,
            "artifacts": [item.to_dict() for item in compilation.artifacts],
        },
        "verifier": (
            {"name": verifier_name, "version": verifier_version}
            if verifier_name is not None
            else None
        ),
        "verification": {
            "status": verification.status.value,
            "diagnostics": list(verification.diagnostics),
        },
        "failure": (
            {"category": integrity_failure.category.value, "message": integrity_failure.message}
            if integrity_failure is not None
            else None
        ),
    }
    try:
        manifest_reference = artifact_store.write_manifest(run_dir, manifest_data)
    except ManifestPublicationError as error:
        return _report(
            request.request_id,
            RunStatus.FAILED,
            compilation,
            verification.status,
            manifest=error.reference,
            failure=RunFailure(
                FailureCategory.MANIFEST_FAILURE,
                "manifest publication state is uncertain"
                if error.uncertain
                else "manifest was published but its directory descriptor could not be closed",
            ),
            verification_diagnostics=verification.diagnostics,
        )
    except (TypeError, ValueError) as error:
        return _report(
            request.request_id,
            RunStatus.FAILED,
            compilation,
            verification.status,
            failure=RunFailure(FailureCategory.SERIALIZATION_FAILURE, type(error).__name__),
            verification_diagnostics=verification.diagnostics,
        )
    except (OSError, RuntimeError) as error:
        return _report(
            request.request_id,
            RunStatus.FAILED,
            compilation,
            verification.status,
            failure=RunFailure(FailureCategory.MANIFEST_FAILURE, type(error).__name__),
            verification_diagnostics=verification.diagnostics,
        )

    if integrity_failure is not None:
        return _report(
            request.request_id,
            RunStatus.FAILED,
            compilation,
            verification.status,
            manifest_reference,
            integrity_failure,
            verification.diagnostics,
        )
    if verification.status is VerificationStatus.PASSED:
        return _report(
            request.request_id,
            RunStatus.SUCCEEDED,
            compilation,
            verification.status,
            manifest_reference,
            verification_diagnostics=verification.diagnostics,
        )
    if verification.status in (
        VerificationStatus.UNAVAILABLE,
        VerificationStatus.NOT_EXECUTED,
    ):
        return _report(
            request.request_id,
            RunStatus.BLOCKED,
            compilation,
            verification.status,
            manifest_reference,
            RunFailure(FailureCategory.VERIFICATION_FAILURE, "verification did not pass"),
            verification.diagnostics,
        )
    failure_category = (
        FailureCategory.VERIFICATION_FAILURE
        if verification.status is VerificationStatus.FAILED
        else verifier_failure_category
    )
    return _report(
        request.request_id,
        RunStatus.FAILED,
        compilation,
        verification.status,
        manifest_reference,
        RunFailure(failure_category, "verification did not pass"),
        verification.diagnostics,
    )
