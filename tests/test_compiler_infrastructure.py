import errno
import hashlib
import json
import os
import stat
import sys
import threading
import tempfile
import time
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from tools.compiler_infrastructure import (
    ArtifactIntegrityError,
    ArtifactReference,
    ArtifactStore,
    CompilationRequest,
    CompilationResult,
    CompilationStatus,
    ExecutionContext,
    FailureCategory,
    PosixProcessGroupBackend,
    RunStatus,
    SubprocessCompilerExecutor,
    VerificationRequest,
    VerificationResult,
    VerificationStatus,
    run_compilation,
)

DIR_FD_SUPPORTED = (
    all(
        function in os.supports_dir_fd
        for function in (os.open, os.mkdir, os.link, os.unlink)
    )
    and hasattr(os, "O_NOFOLLOW")
    and hasattr(os, "O_DIRECTORY")
)


class TestDoubleExecutor:
    name = "test-double-executor"
    version = "1"

    def __init__(
        self,
        *,
        raises=False,
        malformed=False,
        artifact_digest=None,
        exception_type=RuntimeError,
        mutate_input=False,
        partial_output=False,
        output_reference_path=None,
    ):
        self.raises = raises
        self.malformed = malformed
        self.artifact_digest = artifact_digest
        self.exception_type = exception_type
        self.mutate_input = mutate_input
        self.partial_output = partial_output
        self.output_reference_path = output_reference_path

    def compile(self, request, context):
        if self.mutate_input:
            (context.artifact_root / request.inputs[0].path).write_bytes(b"mutated input")
        if self.partial_output:
            (context.output_dir / "partial.bin").write_bytes(b"partial output")
            raise RuntimeError("partial compile")
        if self.raises:
            raise self.exception_type("test-only executor failure")
        if self.malformed:
            return {"status": "succeeded"}
        output = context.output_dir / "candidate.bin"
        output.write_bytes(b"candidate artifact")
        digest = self.artifact_digest or hashlib.sha256(output.read_bytes()).hexdigest()
        reference = ArtifactReference(
            self.output_reference_path
            or f"runs/{request.request_id}/outputs/candidate.bin",
            digest,
        )
        return CompilationResult(CompilationStatus.SUCCEEDED, (reference,))


class TestDoubleVerifier:
    name = "test-double-verifier"
    version = "1"

    def __init__(
        self,
        status=VerificationStatus.PASSED,
        raises=False,
        malformed=False,
        mutate_output=False,
    ):
        self.status = status
        self.raises = raises
        self.malformed = malformed
        self.mutate_output = mutate_output

    def verify(self, request: VerificationRequest, context):
        if self.mutate_output:
            (context.output_dir / "candidate.bin").write_bytes(b"mutated output")
        if self.raises:
            raise RuntimeError("test-only verifier failure")
        if self.malformed:
            return {"status": "passed"}
        return VerificationResult(self.status)


@unittest.skipUnless(DIR_FD_SUPPORTED, "descriptor-relative filesystem APIs are required")
class CompilerInfrastructureTests(unittest.TestCase):
    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary_directory.cleanup)
        self.root = Path(self.temporary_directory.name) / "artifacts"
        self.root.mkdir()
        input_path = self.root / "source.bin"
        input_path.write_bytes(b"immutable input")
        self.input_bytes = input_path.read_bytes()
        self.input_reference = ArtifactReference(
            "source.bin", hashlib.sha256(self.input_bytes).hexdigest()
        )
        self.request = CompilationRequest(
            "request-1",
            (self.input_reference,),
            {"mode": "test", "nested": {"values": [1, 2]}},
            seed=17,
        )
        self.store = ArtifactStore(self.root)
        self.addCleanup(self.store.close)

    @staticmethod
    def read_verified(store, reference):
        with store.open_verified(reference) as artifact:
            return artifact.read()

    @staticmethod
    def subprocess_executor(source, *, timeout_seconds=5.0, environment=None):
        return SubprocessCompilerExecutor(
            (sys.executable, "-c", source),
            "python-test-compiler",
            "test-version",
            timeout_seconds=timeout_seconds,
            environment=environment,
        )

    def test_request_validation_and_immutable_options_snapshot(self):
        options = {"nested": {"values": [1, 2]}}
        request = CompilationRequest("valid-1", options=options)
        options["nested"]["values"].append(3)

        self.assertEqual(request.to_dict()["options"]["nested"]["values"], [1, 2])
        with self.assertRaises(TypeError):
            request.options["new"] = "value"
        with self.assertRaises(TypeError):
            request.options["nested"]["new"] = "value"
        for kwargs in (
            {"request_id": "../escape"},
            {"request_id": "valid-2", "seed": True},
            {"request_id": "valid-2", "options": {"nan": float("nan")}},
            {"request_id": "valid-2", "options": {1: "not-string-key"}},
            {"request_id": "valid-2", "options": {"tuple": (1, 2)}},
            {"request_id": "valid-2", "seed": 1 << 4096},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                CompilationRequest(**kwargs)
        nested = "leaf"
        for _ in range(66):
            nested = [nested]
        with self.assertRaises(ValueError):
            CompilationRequest("deep-options", options={"nested": nested})
        with self.assertRaises(ValueError):
            CompilationRequest("long-string", options={"value": "x" * 1_000_001})
        with self.assertRaises(ValueError):
            CompilationRequest("large-integer", options={"value": 1 << 4097})
        with self.assertRaises(ValueError):
            CompilationRequest(
                "too-many-inputs", inputs=(self.input_reference,) * 10_001
            )
        with self.assertRaises(ValueError):
            CompilationRequest.from_dict(
                {
                    **CompilationRequest("many-inputs").to_dict(),
                    "inputs": [
                        self.input_reference.to_dict()
                    ]
                    * 10_001,
                }
            )
        with self.assertRaises(ValueError):
            CompilationResult(
                CompilationStatus.SUCCEEDED,
                artifacts=(self.input_reference,) * 10_001,
            )
        with self.assertRaises(ValueError):
            CompilationResult(
                CompilationStatus.SUCCEEDED, diagnostics=("x" * 1_000_001,)
            )
        with self.assertRaises(ValueError):
            CompilationResult(
                CompilationStatus.SUCCEEDED, diagnostics=("x",) * 1_001
            )
        with self.assertRaises(ValueError):
            VerificationResult(
                VerificationStatus.PASSED, diagnostics=("x" * 600_000, "y" * 600_000)
            )

    def test_unsupported_unicode_surrogate_fails_manifest_serialization(self):
        request = CompilationRequest("surrogate", options={"value": "\ud800"})
        report = run_compilation(
            request, TestDoubleExecutor(), TestDoubleVerifier(), self.store
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.SERIALIZATION_FAILURE)

    def test_rejects_unsupported_request_version_and_bad_artifact_paths(self):
        with self.assertRaises(ValueError):
            CompilationRequest("valid-1", schema_version=2)
        for path in ("../escape", "/absolute", "folder//file", "C:\\outside"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                ArtifactReference(path, "0" * 64)

    def test_request_json_round_trip_and_strict_schema(self):
        decoded = CompilationRequest.from_dict(self.request.to_dict())

        self.assertEqual(decoded, self.request)
        invalid = self.request.to_dict()
        invalid["unrecognized"] = True
        with self.assertRaises(ValueError):
            CompilationRequest.from_dict(invalid)
        with self.assertRaises(ValueError):
            ArtifactReference.from_dict({"path": 1, "sha256": "0" * 64})
        with self.assertRaises(ValueError):
            ArtifactReference.from_dict(
                {"path": "input.bin", "sha256": "0" * 64, "extra": True}
            )

    def test_valid_executor_and_verifier_complete_lifecycle(self):
        report = run_compilation(
            self.request, TestDoubleExecutor(), TestDoubleVerifier(), self.store
        )

        self.assertEqual(report.status, RunStatus.SUCCEEDED)
        self.assertEqual(report.verification.status, VerificationStatus.PASSED)
        self.assertIsNotNone(report.manifest)
        self.assertEqual(Path(report.manifest.path).name, "manifest.json")
        self.assertEqual(self.store.verify(report.manifest), report.manifest.sha256)
        self.assertEqual((self.root / "source.bin").read_bytes(), self.input_bytes)
        self.assertEqual(report.to_dict()["status"], "succeeded")

    def test_subprocess_executor_runs_an_executable_test_workflow(self):
        source = """
import hashlib
import json
import pathlib
import sys

job = json.load(sys.stdin)
output = pathlib.Path(job["output_dir"]) / "candidate.bin"
output.write_bytes(b"subprocess test artifact")
relative = output.relative_to(pathlib.Path(job["artifact_root"])).as_posix()
print(json.dumps({
    "status": "succeeded",
    "artifacts": [{
        "path": relative,
        "sha256": hashlib.sha256(output.read_bytes()).hexdigest(),
    }],
    "diagnostics": [],
}))
"""
        report = run_compilation(
            self.request,
            self.subprocess_executor(source),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.SUCCEEDED)
        self.assertEqual(report.verification.status, VerificationStatus.PASSED)
        with self.store.open_verified(report.compilation.artifacts[0]) as artifact:
            self.assertEqual(artifact.read(), b"subprocess test artifact")

    def test_subprocess_timeout_is_structured_and_manifested(self):
        source = "import time; time.sleep(10)"
        report = run_compilation(
            self.request,
            self.subprocess_executor(source, timeout_seconds=0.1),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.PROCESS_TIMEOUT)
        self.assertIn("cleanup:", report.failure.message)
        manifest = json.loads(self.read_verified(self.store, report.manifest))
        self.assertEqual(manifest["failure"]["category"], "process_timeout")
        self.assertIn("cleanup:", manifest["failure"]["message"])
        self.assertEqual(manifest["reproducibility"]["level"], 0)

    def test_subprocess_timeout_allows_graceful_termination(self):
        marker = Path(self.temporary_directory.name) / "graceful-child-marker"
        source = """
import pathlib
import signal
import sys
import time

marker = pathlib.Path(sys.argv[1])
marker.write_text("started", encoding="utf-8")
def terminate(_signum, _frame):
    marker.write_text("terminated", encoding="utf-8")
    raise SystemExit(0)
signal.signal(signal.SIGTERM, terminate)
while True:
    time.sleep(0.05)
"""
        executor = SubprocessCompilerExecutor(
            (sys.executable, "-c", source, str(marker)),
            "python-test-compiler",
            "test-version",
            timeout_seconds=0.15,
        )
        output_dir = self.store.prepare_run("graceful-timeout")[1]
        with self.assertRaises(TimeoutError) as raised:
            executor.compile(self.request, ExecutionContext(self.root, output_dir, 17))

        self.assertEqual(marker.read_text(encoding="utf-8"), "terminated")
        self.assertIn("SIGTERM sent", " ".join(raised.exception.cleanup_diagnostics))

    def test_subprocess_timeout_forces_kill_after_grace_period(self):
        marker = Path(self.temporary_directory.name) / "forced-kill-marker"
        source = """
import pathlib
import signal
import sys
import time

signal.signal(signal.SIGTERM, signal.SIG_IGN)
pathlib.Path(sys.argv[1]).write_text("started", encoding="utf-8")
while True:
    time.sleep(0.05)
"""
        executor = SubprocessCompilerExecutor(
            (sys.executable, "-c", source, str(marker)),
            "python-test-compiler",
            "test-version",
            timeout_seconds=0.15,
        )
        output_dir = self.store.prepare_run("forced-timeout")[1]
        with self.assertRaises(TimeoutError) as raised:
            executor.compile(self.request, ExecutionContext(self.root, output_dir, 17))

        self.assertEqual(marker.read_text(encoding="utf-8"), "started")
        self.assertIn("SIGKILL sent", " ".join(raised.exception.cleanup_diagnostics))

    def test_subprocess_timeout_kills_the_direct_child(self):
        marker = Path(self.temporary_directory.name) / "child-marker"
        source = """
import pathlib
import sys
import time

marker = pathlib.Path(sys.argv[1])
marker.write_text("started", encoding="utf-8")
time.sleep(0.6)
marker.write_text("survived", encoding="utf-8")
"""
        executor = SubprocessCompilerExecutor(
            (sys.executable, "-c", source, str(marker)),
            "python-test-compiler",
            "test-version",
            timeout_seconds=0.25,
        )
        output_dir = self.store.prepare_run("direct-child")[1]
        with self.assertRaises(TimeoutError):
            executor.compile(self.request, ExecutionContext(self.root, output_dir, 17))
        time.sleep(0.45)

        self.assertEqual(marker.read_text(encoding="utf-8"), "started")

    def test_subprocess_timeout_kills_attached_descendants(self):
        marker = Path(self.temporary_directory.name) / "attached-child-marker"
        child_source = """
import pathlib
import sys
import time

marker = pathlib.Path(sys.argv[1])
marker.write_text("started", encoding="utf-8")
time.sleep(0.8)
marker.write_text("survived", encoding="utf-8")
"""
        parent_source = """
import pathlib
import subprocess
import sys
import time

marker = pathlib.Path(sys.argv[1])
subprocess.Popen([sys.executable, "-c", sys.argv[2], str(marker)])
while not marker.exists():
    time.sleep(0.01)
time.sleep(10)
"""
        executor = SubprocessCompilerExecutor(
            (sys.executable, "-c", parent_source, str(marker), child_source),
            "python-test-compiler",
            "test-version",
            timeout_seconds=0.3,
        )
        output_dir = self.store.prepare_run("attached-child")[1]
        with self.assertRaises(TimeoutError):
            executor.compile(self.request, ExecutionContext(self.root, output_dir, 17))
        time.sleep(0.6)

        self.assertEqual(marker.read_text(encoding="utf-8"), "started")

    def test_subprocess_success_cleans_up_leftover_managed_descendants(self):
        marker = Path(self.temporary_directory.name) / "success-child-marker"
        child_source = """
import pathlib
import sys
import time

marker = pathlib.Path(sys.argv[1])
marker.write_text("started", encoding="utf-8")
time.sleep(0.6)
marker.write_text("survived", encoding="utf-8")
"""
        parent_source = """
import json
import pathlib
import subprocess
import sys
import time

marker = pathlib.Path(sys.argv[1])
subprocess.Popen([sys.executable, "-c", sys.argv[2], str(marker)])
while not marker.exists():
    time.sleep(0.01)
print(json.dumps({"status": "succeeded", "artifacts": [], "diagnostics": []}))
"""
        executor = SubprocessCompilerExecutor(
            (sys.executable, "-c", parent_source, str(marker), child_source),
            "python-test-compiler",
            "test-version",
            timeout_seconds=2.0,
        )
        output_dir = self.store.prepare_run("success-child-cleanup")[1]

        result = executor.compile(
            self.request, ExecutionContext(self.root, output_dir, 17)
        )
        time.sleep(0.7)

        self.assertEqual(result.status, CompilationStatus.SUCCEEDED)
        self.assertEqual(marker.read_text(encoding="utf-8"), "started")

    def test_detached_descendant_can_outlive_timeout(self):
        marker = Path(self.temporary_directory.name) / "detached-child-marker"
        child_source = """
import pathlib
import sys
import time

marker = pathlib.Path(sys.argv[1])
time.sleep(0.3)
marker.write_text("survived", encoding="utf-8")
"""
        parent_source = """
import subprocess
import sys
import time

subprocess.Popen(
    [sys.executable, "-c", sys.argv[2], sys.argv[1]],
    start_new_session=True,
)
time.sleep(10)
"""
        executor = SubprocessCompilerExecutor(
            (sys.executable, "-c", parent_source, str(marker), child_source),
            "python-test-compiler",
            "test-version",
            timeout_seconds=0.15,
        )
        output_dir = self.store.prepare_run("detached-child")[1]
        with self.assertRaises(TimeoutError):
            executor.compile(self.request, ExecutionContext(self.root, output_dir, 17))

        self.assertEqual(marker.read_text(encoding="utf-8"), "survived")

    def test_subprocess_nonzero_exit_reports_bounded_stderr(self):
        source = """
import json
import sys

job = json.load(sys.stdin)
sys.stderr.write("rejected output directory: " + job["output_dir"])
sys.exit(7)
"""
        report = run_compilation(
            self.request,
            self.subprocess_executor(source),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.EXECUTION_FAILURE)
        self.assertEqual(report.compilation.status, CompilationStatus.FAILED)
        self.assertIn("<output-dir>", report.compilation.diagnostics[1])
        self.assertNotIn(str(self.root), report.compilation.diagnostics[1])

    def test_subprocess_redacts_configured_environment_and_arguments(self):
        environment_secret = "env-secret-value-91d2"
        argument_secret = "arg-secret-value-8f34"
        source = """
import json
import os
import sys

print("compiler-log:" + os.environ["API_TOKEN"] + ":" + sys.argv[1], file=sys.stderr)
print(json.dumps({
    "status": "succeeded",
    "artifacts": [],
    "diagnostics": [os.environ["API_TOKEN"], sys.argv[1]],
}))
"""
        executor = SubprocessCompilerExecutor(
            (sys.executable, "-c", source, argument_secret),
            "python-test-compiler",
            "test-version",
            environment={"API_TOKEN": environment_secret},
            sensitive_arguments=(argument_secret,),
        )
        report = run_compilation(self.request, executor, TestDoubleVerifier(), self.store)
        report_json = json.dumps(report.to_dict(), sort_keys=True)
        manifest_text = self.read_verified(self.store, report.manifest).decode("utf-8")

        self.assertEqual(report.status, RunStatus.SUCCEEDED)
        self.assertNotIn(environment_secret, report_json)
        self.assertNotIn(argument_secret, report_json)
        self.assertNotIn(environment_secret, manifest_text)
        self.assertNotIn(argument_secret, manifest_text)
        self.assertIn("<redacted-config>", report_json)

    def test_subprocess_preserves_request_values_while_redacting_diagnostics(self):
        secret = "request-token-needed-by-compiler-43ce"
        request = CompilationRequest(
            "request-secret-input",
            self.request.inputs,
            {"api_token": secret},
        )
        source = """
import json
import sys

job = json.load(sys.stdin)
if job["request"]["options"]["api_token"] != sys.argv[1]:
    print("request option was changed", file=sys.stderr)
    sys.exit(9)
print(json.dumps({
    "status": "succeeded",
    "artifacts": [],
    "diagnostics": [job["request"]["options"]["api_token"]],
}))
"""
        executor = SubprocessCompilerExecutor(
            (sys.executable, "-c", source, secret),
            "python-test-compiler",
            "test-version",
            sensitive_arguments=(secret,),
        )
        output_dir = self.store.prepare_run(request.request_id)[1]

        result = executor.compile(
            request, ExecutionContext(self.root, output_dir, request.seed)
        )

        self.assertEqual(result.status, CompilationStatus.SUCCEEDED)
        self.assertNotIn(secret, json.dumps(result.to_dict()))

    def test_subprocess_configuration_fingerprint_is_keyed_and_reproducibility_is_honest(self):
        key = b"configuration-fingerprint-test-key-0001"
        environment = {"API_TOKEN": "private-token-one"}
        command = (
            sys.executable,
            "-c",
            "import json; print(json.dumps({'status':'succeeded','artifacts':[],'diagnostics':[]}))",
        )
        executor = SubprocessCompilerExecutor(
            command,
            "python-test-compiler",
            "test-version",
            timeout_seconds=2.0,
            environment=environment,
            configuration_fingerprint_key=key,
        )
        repeated = SubprocessCompilerExecutor(
            command,
            "python-test-compiler",
            "test-version",
            timeout_seconds=2.0,
            environment=environment,
            configuration_fingerprint_key=key,
        )
        changed = SubprocessCompilerExecutor(
            command,
            "python-test-compiler",
            "test-version",
            timeout_seconds=2.0,
            environment={"API_TOKEN": "private-token-two"},
            configuration_fingerprint_key=key,
        )

        run_request = CompilationRequest(
            "keyed-config",
            self.request.inputs,
            {"api_token": "manifest-private-token"},
            seed=17,
        )
        fingerprint = executor.reproducibility_metadata()["configuration_fingerprint"]
        self.assertEqual(
            fingerprint, repeated.reproducibility_metadata()["configuration_fingerprint"]
        )
        self.assertNotEqual(
            fingerprint, changed.reproducibility_metadata()["configuration_fingerprint"]
        )
        request_fingerprint = executor.reproducibility_metadata(run_request)[
            "canonical_request_fingerprint"
        ]
        changed_request = CompilationRequest(
            "keyed-config",
            self.request.inputs,
            {"api_token": "another-private-token"},
            seed=17,
        )
        self.assertNotEqual(
            request_fingerprint,
            executor.reproducibility_metadata(changed_request)[
                "canonical_request_fingerprint"
            ],
        )

        report = run_compilation(run_request, executor, TestDoubleVerifier(), self.store)
        manifest_text = self.read_verified(self.store, report.manifest).decode("utf-8")
        manifest = json.loads(manifest_text)
        configuration = manifest["executor"]["configuration"]
        self.assertEqual(report.status, RunStatus.SUCCEEDED)
        self.assertEqual(configuration["fingerprint_algorithm"], "HMAC-SHA256")
        self.assertEqual(configuration["configuration_fingerprint"], fingerprint)
        self.assertEqual(
            manifest["reproducibility"]["canonical_request_fingerprint"],
            request_fingerprint,
        )
        self.assertNotIn("private-token-one", manifest_text)
        self.assertNotIn("manifest-private-token", manifest_text)
        self.assertNotIn(key.hex(), manifest_text)
        self.assertEqual(manifest["reproducibility"]["level"], 0)
        self.assertFalse(manifest["reproducibility"]["configuration_complete"])

    def test_subprocess_uses_injected_isolation_backend_and_records_its_identity(self):
        delegate = PosixProcessGroupBackend()

        class RecordingBackend:
            name = "recording-test-backend"
            version = "2"
            containment_scope = "test-process-group"

            def __init__(self):
                self.events = []

            def launch(self, command, *, cwd, environment):
                self.events.append("launch")
                return delegate.launch(command, cwd=cwd, environment=environment)

            def terminate(self, process):
                self.events.append("terminate")
                return delegate.terminate(process)

        backend = RecordingBackend()
        command = (
            sys.executable,
            "-c",
            "import json; print(json.dumps({'status':'succeeded','artifacts':[],'diagnostics':[]}))",
        )
        fingerprint_key = b"process-backend-fingerprint-key-0001"
        executor = SubprocessCompilerExecutor(
            command,
            "python-test-compiler",
            "test-version",
            configuration_fingerprint_key=fingerprint_key,
            isolation_backend=backend,
        )
        default_backend_executor = SubprocessCompilerExecutor(
            command,
            "python-test-compiler",
            "test-version",
            configuration_fingerprint_key=fingerprint_key,
        )
        self.assertNotEqual(
            executor.reproducibility_metadata()["configuration_fingerprint"],
            default_backend_executor.reproducibility_metadata()[
                "configuration_fingerprint"
            ],
        )
        report = run_compilation(self.request, executor, TestDoubleVerifier(), self.store)
        manifest = json.loads(self.read_verified(self.store, report.manifest))
        configuration = manifest["executor"]["configuration"]

        self.assertEqual(report.status, RunStatus.SUCCEEDED)
        self.assertEqual(backend.events, ["launch", "terminate"])
        self.assertEqual(configuration["isolation_backend"], backend.name)
        self.assertEqual(
            configuration["isolation_backend_version"], backend.version
        )
        self.assertEqual(
            configuration["containment_scope"], backend.containment_scope
        )

    def test_request_secrets_are_redacted_from_results_and_manifests(self):
        token = "request-token-secret-6a31"
        private_key = "private-key-secret-7bf2"
        request = CompilationRequest(
            "secret-request",
            self.request.inputs,
            {
                "api_token": token,
                "nested": {"private_key": private_key},
                "public_option": "visible",
            },
        )

        class LeakyExecutor(TestDoubleExecutor):
            def compile(self, compilation_request, context):
                result = super().compile(compilation_request, context)
                return CompilationResult(
                    result.status,
                    result.artifacts,
                    (token, private_key),
                )

        class LeakyVerifier:
            name = "test-leaky-verifier"
            version = "1"

            def verify(self, _request, _context):
                return VerificationResult(
                    VerificationStatus.PASSED,
                    (token, private_key),
                )

        report = run_compilation(request, LeakyExecutor(), LeakyVerifier(), self.store)
        manifest_text = self.read_verified(self.store, report.manifest).decode("utf-8")
        serialized_report = json.dumps(report.to_dict(), sort_keys=True)
        manifest = json.loads(manifest_text)

        self.assertEqual(report.status, RunStatus.SUCCEEDED)
        self.assertNotIn(token, manifest_text)
        self.assertNotIn(private_key, manifest_text)
        self.assertNotIn(token, serialized_report)
        self.assertNotIn(private_key, serialized_report)
        self.assertEqual(manifest["request"]["options"]["api_token"], "<redacted>")
        self.assertEqual(
            manifest["request"]["options"]["nested"]["private_key"], "<redacted>"
        )
        self.assertEqual(manifest["request"]["options"]["public_option"], "visible")

    def test_subprocess_malformed_or_ambiguous_json_is_rejected(self):
        source = """
print('{"status":"succeeded","status":"failed","artifacts":[],"diagnostics":[]}')
"""
        report = run_compilation(
            self.request,
            self.subprocess_executor(source),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.INVALID_RESULT)
        self.assertEqual(report.failure.message, "compiler returned invalid protocol data")

    def test_subprocess_rejects_invalid_utf8_and_artifact_traversal(self):
        cases = (
            (
                "invalid-utf8",
                "import sys; sys.stdout.buffer.write(b'\\xff')",
                FailureCategory.INVALID_RESULT,
            ),
            (
                "artifact-traversal",
                """import json; print(json.dumps({
                    "status":"succeeded",
                    "artifacts":[{"path":"../escape","sha256":"0000000000000000000000000000000000000000000000000000000000000000"}],
                    "diagnostics":[],
                }))""",
                FailureCategory.INVALID_RESULT,
            ),
        )
        for request_id, source, expected_category in cases:
            with self.subTest(request_id=request_id):
                request = CompilationRequest(request_id, self.request.inputs)
                report = run_compilation(
                    request,
                    self.subprocess_executor(source),
                    TestDoubleVerifier(),
                    self.store,
                )
                self.assertEqual(report.status, RunStatus.FAILED)
                self.assertEqual(report.failure.category, expected_category)
                self.assertEqual(
                    report.verification.status, VerificationStatus.NOT_EXECUTED
                )

    def test_subprocess_replaces_invalid_utf8_in_stderr(self):
        source = """
import sys

sys.stderr.buffer.write(b"warning\\xff")
print('{"status":"failed","artifacts":[],"diagnostics":[]}')
"""
        report = run_compilation(
            self.request,
            self.subprocess_executor(source),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.compilation.status, CompilationStatus.FAILED)
        self.assertIn("warning\uFFFD", report.compilation.diagnostics[-1])

    def test_subprocess_stderr_output_limit_is_enforced(self):
        source = """
import json
import sys

sys.stderr.buffer.write(b"x" * (300 * 1024))
print(json.dumps({"status":"failed","artifacts":[],"diagnostics":[]}))
"""
        report = run_compilation(
            self.request,
            self.subprocess_executor(source),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.INVALID_RESULT)
        self.assertIn("stderr exceeded", report.failure.message)

    def test_subprocess_simultaneous_stdout_stderr_flood_is_bounded(self):
        source = """
import os
import threading

def flood(descriptor, byte, count):
    chunk = byte * 65536
    for _ in range(count):
        os.write(descriptor, chunk)

threads = [
    threading.Thread(target=flood, args=(1, b"x", 272)),
    threading.Thread(target=flood, args=(2, b"y", 8)),
]
for thread in threads:
    thread.start()
for thread in threads:
    thread.join()
"""
        report = run_compilation(
            self.request,
            self.subprocess_executor(source, timeout_seconds=10.0),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.INVALID_RESULT)
        self.assertIn("stdout exceeded", report.failure.message)

    def test_subprocess_symlink_output_is_rejected(self):
        source = """
import hashlib
import json
import pathlib
import sys

job = json.load(sys.stdin)
output = pathlib.Path(job["output_dir"]) / "linked.bin"
outside = pathlib.Path(job["artifact_root"]).parent / "outside.bin"
outside.write_bytes(b"outside")
output.symlink_to(outside)
relative = output.relative_to(pathlib.Path(job["artifact_root"])).as_posix()
print(json.dumps({
    "status": "succeeded",
    "artifacts": [{
        "path": relative,
        "sha256": hashlib.sha256(b"outside").hexdigest(),
    }],
    "diagnostics": [],
}))
"""
        report = run_compilation(
            self.request,
            self.subprocess_executor(source),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.compilation.status, CompilationStatus.SUCCEEDED)
        self.assertEqual(report.failure.category, FailureCategory.ENVIRONMENT_FAILURE)
        self.assertEqual(report.verification.status, VerificationStatus.NOT_EXECUTED)

    def test_subprocess_stdout_is_bounded(self):
        source = 'import sys; sys.stdout.write("x" * (17 * 1024 * 1024))'
        report = run_compilation(
            self.request,
            self.subprocess_executor(source),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.INVALID_RESULT)

    def test_subprocess_request_size_is_bounded_before_launch(self):
        oversized_request = CompilationRequest(
            "oversized-request",
            options={"values": ["x" * 1_000_000 for _ in range(17)]},
        )
        report = run_compilation(
            oversized_request,
            self.subprocess_executor("raise RuntimeError('process must not start')"),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.INVALID_REQUEST)
        self.assertIsNone(report.compilation)

    def test_subprocess_missing_executable_has_distinct_failure(self):
        missing_executable = self.root / "does-not-exist"
        executor = SubprocessCompilerExecutor(
            (str(missing_executable),),
            "missing-test-compiler",
            "test-version",
        )
        report = run_compilation(
            self.request, executor, TestDoubleVerifier(), self.store
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.MISSING_EXECUTABLE)
        self.assertEqual(
            report.failure.message, "configured compiler executable was not found"
        )

    def test_subprocess_environment_size_is_bounded(self):
        with self.assertRaises(ValueError):
            SubprocessCompilerExecutor(
                (sys.executable,),
                "oversized-environment",
                "test-version",
                environment={"OVERSIZED": "x" * (1024 * 1024 + 1)},
            )

    def test_subprocess_uses_only_explicit_environment_and_literal_arguments(self):
        source = """
import json
import os
import sys

print(json.dumps({
    "status": "failed",
    "artifacts": [],
    "diagnostics": [os.environ.get("PHASE7_PRIVATE_MARKER", "unset"), sys.argv[1]],
}))
"""
        marker = "must-not-be-inherited"
        shell_argument = f"; touch {self.root / 'shell-marker'}"
        executor = SubprocessCompilerExecutor(
            (sys.executable, "-c", source, shell_argument),
            "python-test-compiler",
            "test-version",
            environment={},
        )
        _, output_dir = self.store.prepare_run("process-boundary")
        context = ExecutionContext(self.root, output_dir, self.request.seed)
        with patch.dict(os.environ, {"PHASE7_PRIVATE_MARKER": marker}):
            result = executor.compile(self.request, context)

        self.assertEqual(result.status, CompilationStatus.FAILED)
        self.assertEqual(
            result.diagnostics,
            ("unset", "; touch <artifact-root>/shell-marker"),
        )
        self.assertFalse((self.root / "shell-marker").exists())

    def test_missing_executor_is_blocked(self):
        report = run_compilation(self.request, None, TestDoubleVerifier(), self.store)

        self.assertEqual(report.status, RunStatus.BLOCKED)
        self.assertEqual(report.failure.category, FailureCategory.MISSING_EXECUTOR)
        self.assertEqual(report.verification.status, VerificationStatus.NOT_EXECUTED)

    def test_invalid_request_object_is_rejected(self):
        report = run_compilation(
            object(), TestDoubleExecutor(), TestDoubleVerifier(), self.store
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.INVALID_REQUEST)

    def test_invalid_artifact_store_is_reported(self):
        report = run_compilation(
            self.request, TestDoubleExecutor(), TestDoubleVerifier(), object()
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.ARTIFACT_FAILURE)

    def test_missing_verifier_cannot_report_success(self):
        report = run_compilation(self.request, TestDoubleExecutor(), None, self.store)

        self.assertEqual(report.status, RunStatus.BLOCKED)
        self.assertEqual(report.verification.status, VerificationStatus.UNAVAILABLE)
        self.assertIsNotNone(report.manifest)

    def test_executor_exception_is_reported_without_leaking_message(self):
        report = run_compilation(
            self.request, TestDoubleExecutor(raises=True), TestDoubleVerifier(), self.store
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.EXECUTION_FAILURE)
        self.assertEqual(report.failure.message, "executor raised RuntimeError")

    def test_partial_output_is_preserved_with_failed_manifest(self):
        report = run_compilation(
            self.request,
            TestDoubleExecutor(partial_output=True),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertIsNotNone(report.manifest)
        manifest = json.loads(self.read_verified(self.store, report.manifest))
        self.assertEqual(manifest["run_status"], "failed")
        self.assertEqual(manifest["failure"]["category"], "execution_failure")
        partial = self.root / "runs" / self.request.request_id / "outputs" / "partial.bin"
        self.assertEqual(partial.read_bytes(), b"partial output")

    def test_executor_input_mutation_is_detected(self):
        report = run_compilation(
            self.request,
            TestDoubleExecutor(mutate_input=True),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.INTEGRITY_MISMATCH)
        self.assertEqual(report.verification.status, VerificationStatus.NOT_EXECUTED)

    def test_verifier_output_mutation_is_detected_after_handoff(self):
        report = run_compilation(
            self.request,
            TestDoubleExecutor(),
            TestDoubleVerifier(mutate_output=True),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.verification.status, VerificationStatus.ERROR)
        self.assertEqual(report.failure.category, FailureCategory.INTEGRITY_MISMATCH)
        manifest = json.loads(self.read_verified(self.store, report.manifest))
        self.assertEqual(manifest["run_status"], "failed")

    def test_verifier_receives_verified_descriptor_streams(self):
        class ReadingVerifier:
            name = "descriptor-reading-verifier"
            version = "1"

            def verify(self, request, _context):
                reference = request.compilation_result.artifacts[0]
                self.stream = request.verified_artifacts[reference]
                self.contents = self.stream.read()
                return VerificationResult(VerificationStatus.PASSED)

        verifier = ReadingVerifier()
        report = run_compilation(self.request, TestDoubleExecutor(), verifier, self.store)

        self.assertEqual(report.status, RunStatus.SUCCEEDED)
        self.assertEqual(verifier.contents, b"candidate artifact")
        self.assertTrue(verifier.stream.closed)

    def test_malformed_executor_result_is_rejected(self):
        report = run_compilation(
            self.request,
            TestDoubleExecutor(malformed=True),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.INVALID_RESULT)
        self.assertEqual(report.verification.status, VerificationStatus.NOT_EXECUTED)

    def test_artifact_digest_mismatch_prevents_verification(self):
        report = run_compilation(
            self.request,
            TestDoubleExecutor(artifact_digest="0" * 64),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.INTEGRITY_MISMATCH)
        self.assertEqual(report.verification.status, VerificationStatus.NOT_EXECUTED)

    def test_executor_cannot_declare_input_as_output_artifact(self):
        report = run_compilation(
            self.request,
            TestDoubleExecutor(
                output_reference_path="source.bin",
                artifact_digest=self.input_reference.sha256,
            ),
            TestDoubleVerifier(),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.ARTIFACT_FAILURE)

    def test_input_digest_mismatch_prevents_execution(self):
        bad_request = CompilationRequest(
            "bad-input",
            (ArtifactReference("source.bin", "0" * 64),),
        )
        report = run_compilation(
            bad_request, TestDoubleExecutor(), TestDoubleVerifier(), self.store
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.INTEGRITY_MISMATCH)

    def test_missing_input_artifact_has_distinct_failure_category(self):
        request = CompilationRequest(
            "missing-input",
            (ArtifactReference("missing.bin", "0" * 64),),
        )
        report = run_compilation(
            request, TestDoubleExecutor(), TestDoubleVerifier(), self.store
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.MISSING_ARTIFACT)

    def test_missing_dependency_and_unsupported_operation_are_classified(self):
        for error_type, category in (
            (ModuleNotFoundError, FailureCategory.MISSING_DEPENDENCY),
            (NotImplementedError, FailureCategory.UNSUPPORTED_OPERATION),
            (OSError, FailureCategory.ENVIRONMENT_FAILURE),
        ):
            with self.subTest(error=error_type.__name__):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    (root / "source.bin").write_bytes(self.input_bytes)
                    report = run_compilation(
                        self.request,
                        TestDoubleExecutor(raises=True, exception_type=error_type),
                        TestDoubleVerifier(),
                        ArtifactStore(root),
                    )
                    self.assertEqual(report.failure.category, category)

    def test_failed_or_unavailable_verification_never_succeeds(self):
        for verification_status, run_status in (
            (VerificationStatus.FAILED, RunStatus.FAILED),
            (VerificationStatus.UNAVAILABLE, RunStatus.BLOCKED),
            (VerificationStatus.NOT_EXECUTED, RunStatus.BLOCKED),
            (VerificationStatus.ERROR, RunStatus.FAILED),
        ):
            with self.subTest(status=verification_status):
                with tempfile.TemporaryDirectory() as directory:
                    store_root = Path(directory)
                    (store_root / "source.bin").write_bytes(self.input_bytes)
                    store = ArtifactStore(store_root)
                    report = run_compilation(
                        self.request,
                        TestDoubleExecutor(),
                        TestDoubleVerifier(verification_status),
                        store,
                    )
                    self.assertEqual(report.status, run_status)
                    expected_category = (
                        FailureCategory.VERIFICATION_FAILURE
                        if verification_status is VerificationStatus.FAILED
                        else FailureCategory.VERIFIER_ERROR
                        if verification_status is VerificationStatus.ERROR
                        else FailureCategory.VERIFICATION_FAILURE
                    )
                    self.assertEqual(report.failure.category, expected_category)

    def test_verifier_exception_is_explicit_failure(self):
        report = run_compilation(
            self.request,
            TestDoubleExecutor(),
            TestDoubleVerifier(raises=True),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.verification.status, VerificationStatus.ERROR)
        self.assertEqual(report.verification.diagnostics, ("verifier raised RuntimeError",))

    def test_malformed_verifier_result_is_explicit_error(self):
        report = run_compilation(
            self.request,
            TestDoubleExecutor(),
            TestDoubleVerifier(malformed=True),
            self.store,
        )

        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.verification.status, VerificationStatus.ERROR)
        self.assertEqual(report.verification.diagnostics, ("verifier raised TypeError",))

    def test_manifest_serialization_is_canonical_and_self_consistent(self):
        report = run_compilation(
            self.request, TestDoubleExecutor(), TestDoubleVerifier(), self.store
        )
        serialized = self.read_verified(self.store, report.manifest)
        manifest = json.loads(serialized)

        self.assertEqual(
            serialized,
            json.dumps(
                manifest, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            ).encode("utf-8"),
        )
        self.assertEqual(manifest["verification"]["status"], "passed")
        self.assertIn("python_version", manifest["runtime"])
        self.assertIn("platform", manifest["runtime"])
        self.assertEqual(
            hashlib.sha256(serialized).hexdigest(), report.manifest.sha256
        )

    def test_repeated_execution_produces_identical_manifest_bytes(self):
        with tempfile.TemporaryDirectory() as second_directory:
            second_root = Path(second_directory)
            (second_root / "source.bin").write_bytes(self.input_bytes)
            second_store = ArtifactStore(second_root)
            first_report = run_compilation(
                self.request, TestDoubleExecutor(), TestDoubleVerifier(), self.store
            )
            second_report = run_compilation(
                self.request, TestDoubleExecutor(), TestDoubleVerifier(), second_store
            )

            first_manifest = self.read_verified(self.store, first_report.manifest)
            second_manifest = self.read_verified(second_store, second_report.manifest)

        self.assertEqual(first_manifest, second_manifest)

    def test_artifact_store_rejects_symlink_escape(self):
        outside = Path(self.temporary_directory.name) / "outside.bin"
        outside.write_bytes(b"outside")
        link = self.root / "outside-link"
        link.symlink_to(outside)
        reference = ArtifactReference(
            "outside-link", hashlib.sha256(b"outside").hexdigest()
        )

        with self.assertRaises((ValueError, OSError)):
            self.store.verify(reference)

    def test_artifact_store_rejects_symlinked_intermediate_directory(self):
        outside = Path(self.temporary_directory.name) / "outside-dir"
        outside.mkdir()
        (outside / "artifact.bin").write_bytes(b"outside")
        (self.root / "linked-dir").symlink_to(outside, target_is_directory=True)
        reference = ArtifactReference(
            "linked-dir/artifact.bin", hashlib.sha256(b"outside").hexdigest()
        )

        with self.assertRaises(OSError):
            self.store.verify(reference)

    def test_artifact_store_rejects_symlinked_file(self):
        outside = Path(self.temporary_directory.name) / "outside-file.bin"
        outside.write_bytes(b"outside")
        (self.root / "linked-file").symlink_to(outside)
        reference = ArtifactReference(
            "linked-file", hashlib.sha256(b"outside").hexdigest()
        )

        with self.assertRaises(OSError):
            self.store.verify(reference)

    def test_artifact_store_rejects_unvalidated_reference_type(self):
        outside = Path(self.temporary_directory.name) / "outside-reference.bin"
        outside.write_bytes(b"outside reference")
        unvalidated_reference = SimpleNamespace(
            path="../outside-reference.bin",
            sha256=hashlib.sha256(b"outside reference").hexdigest(),
        )

        with self.assertRaises(TypeError):
            self.store.verify(unvalidated_reference)

    def test_artifact_descriptor_stays_anchored_if_root_path_is_replaced(self):
        moved_root = Path(self.temporary_directory.name) / "moved-artifacts"
        outside_root = Path(self.temporary_directory.name) / "replacement-root"
        outside_root.mkdir()
        (outside_root / "source.bin").write_bytes(b"attacker replacement")
        self.root.rename(moved_root)
        self.root.symlink_to(outside_root, target_is_directory=True)

        with self.store.open_verified(self.input_reference) as artifact:
            self.assertEqual(artifact.read(), self.input_bytes)
        self.assertEqual(self.store.verify(self.input_reference), self.input_reference.sha256)

    def test_open_verified_detects_mutation_during_consumer_use(self):
        with self.assertRaises(ArtifactIntegrityError):
            with self.store.open_verified(self.input_reference) as artifact:
                artifact.read()
                (self.root / "source.bin").write_bytes(b"mutated while open")

    @unittest.skipUnless(hasattr(os, "mkfifo"), "named pipes are not supported")
    def test_artifact_store_rejects_fifo_without_blocking(self):
        fifo = self.root / "artifact.fifo"
        os.mkfifo(fifo)
        reference = ArtifactReference("artifact.fifo", "0" * 64)

        with self.assertRaises(OSError):
            self.store.verify(reference)

    def test_missing_artifact_is_reported(self):
        reference = ArtifactReference("missing.bin", "0" * 64)

        with self.assertRaises(FileNotFoundError):
            self.store.verify(reference)

    def test_duplicate_run_id_cannot_overwrite_existing_run(self):
        self.store.prepare_run("unique-run")

        with self.assertRaises(FileExistsError):
            self.store.prepare_run("unique-run")

    def test_artifact_root_symlink_is_rejected(self):
        alias = Path(self.temporary_directory.name) / "root-alias"
        alias.symlink_to(self.root, target_is_directory=True)

        with self.assertRaises(OSError):
            ArtifactStore(alias)

    def test_concurrent_manifest_publication_has_single_winner(self):
        run_dir, _ = self.store.prepare_run("manifest-concurrent")
        barrier = threading.Barrier(2)

        def publish(value):
            barrier.wait()
            return self._capture(
                lambda: self.store.write_manifest(run_dir, {"value": value})
            )

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(publish, ("first", "second")))

        references = [value for value in results if isinstance(value, ArtifactReference)]
        failures = [value for value in results if isinstance(value, Exception)]
        self.assertEqual(len(references), 1)
        self.assertEqual(len(failures), 1)
        self.assertIsInstance(failures[0], FileExistsError)
        manifest_dir = run_dir
        self.assertEqual(
            sorted(path.name for path in manifest_dir.iterdir()),
            ["manifest.json", "outputs"],
        )
        self.store.verify(references[0])

    def test_directory_fsync_failure_removes_published_manifest(self):
        original_fsync = os.fsync
        failed_once = False

        def fail_first_directory_sync(descriptor):
            nonlocal failed_once
            if stat.S_ISDIR(os.fstat(descriptor).st_mode) and not failed_once:
                failed_once = True
                raise OSError(errno.EIO, "injected directory fsync failure")
            return original_fsync(descriptor)

        with patch(
            "tools.compiler_infrastructure.os.fsync",
            side_effect=fail_first_directory_sync,
        ):
            report = run_compilation(
                self.request,
                TestDoubleExecutor(),
                TestDoubleVerifier(),
                self.store,
            )

        run_dir = self.root / "runs" / self.request.request_id
        self.assertTrue(failed_once)
        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.MANIFEST_FAILURE)
        self.assertIsNone(report.manifest)
        self.assertEqual(sorted(path.name for path in run_dir.iterdir()), ["outputs"])

    def test_manifest_rollback_sync_failure_is_reported_as_uncertain(self):
        original_fsync = os.fsync

        def fail_directory_sync(descriptor):
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                raise OSError(errno.EIO, "injected directory fsync failure")
            return original_fsync(descriptor)

        with patch(
            "tools.compiler_infrastructure.os.fsync",
            side_effect=fail_directory_sync,
        ):
            report = run_compilation(
                self.request,
                TestDoubleExecutor(),
                TestDoubleVerifier(),
                self.store,
            )

        run_dir = self.root / "runs" / self.request.request_id
        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.MANIFEST_FAILURE)
        self.assertEqual(
            report.failure.message, "manifest publication state is uncertain"
        )
        self.assertIsNone(report.manifest)
        self.assertEqual(sorted(path.name for path in run_dir.iterdir()), ["outputs"])

    def test_manifest_directory_close_failure_returns_published_reference(self):
        original_close = os.close
        run_dir = self.root / "runs" / self.request.request_id
        failed_once = False

        def fail_close_after_publication(descriptor):
            nonlocal failed_once
            if (
                not failed_once
                and stat.S_ISDIR(os.fstat(descriptor).st_mode)
                and (run_dir / "manifest.json").exists()
            ):
                failed_once = True
                original_close(descriptor)
                raise OSError(errno.EIO, "injected directory close failure")
            return original_close(descriptor)

        with patch(
            "tools.compiler_infrastructure.os.close",
            side_effect=fail_close_after_publication,
        ):
            report = run_compilation(
                self.request,
                TestDoubleExecutor(),
                TestDoubleVerifier(),
                self.store,
            )

        self.assertTrue(failed_once)
        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.MANIFEST_FAILURE)
        self.assertEqual(
            report.failure.message,
            "manifest was published but its directory descriptor could not be closed",
        )
        self.assertIsNotNone(report.manifest)
        self.store.verify(report.manifest)

    def test_failure_manifest_close_failure_returns_published_reference(self):
        original_close = os.close
        run_dir = self.root / "runs" / self.request.request_id
        failed_once = False

        def fail_close_after_publication(descriptor):
            nonlocal failed_once
            if (
                not failed_once
                and stat.S_ISDIR(os.fstat(descriptor).st_mode)
                and (run_dir / "manifest.json").exists()
            ):
                failed_once = True
                original_close(descriptor)
                raise OSError(errno.EIO, "injected directory close failure")
            return original_close(descriptor)

        with patch(
            "tools.compiler_infrastructure.os.close",
            side_effect=fail_close_after_publication,
        ):
            report = run_compilation(
                self.request,
                TestDoubleExecutor(raises=True),
                TestDoubleVerifier(),
                self.store,
            )

        self.assertTrue(failed_once)
        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.EXECUTION_FAILURE)
        self.assertIn("failure manifest published", report.failure.message)
        self.assertIsNotNone(report.manifest)
        manifest = json.loads(self.read_verified(self.store, report.manifest))
        self.assertEqual(manifest["run_status"], "failed")

    def test_directory_close_failure_does_not_mask_rollback_uncertainty(self):
        original_close = os.close
        original_fsync = os.fsync
        directory_sync_failed = False
        close_failed = False

        def fail_directory_sync(descriptor):
            nonlocal directory_sync_failed
            if stat.S_ISDIR(os.fstat(descriptor).st_mode):
                directory_sync_failed = True
                raise OSError(errno.EIO, "injected directory fsync failure")
            return original_fsync(descriptor)

        def fail_close_after_sync_failure(descriptor):
            nonlocal close_failed
            if (
                directory_sync_failed
                and not close_failed
                and stat.S_ISDIR(os.fstat(descriptor).st_mode)
            ):
                close_failed = True
                original_close(descriptor)
                raise OSError(errno.EIO, "injected directory close failure")
            return original_close(descriptor)

        with patch(
            "tools.compiler_infrastructure.os.fsync",
            side_effect=fail_directory_sync,
        ):
            with patch(
                "tools.compiler_infrastructure.os.close",
                side_effect=fail_close_after_sync_failure,
            ):
                report = run_compilation(
                    self.request,
                    TestDoubleExecutor(),
                    TestDoubleVerifier(),
                    self.store,
                )

        run_dir = self.root / "runs" / self.request.request_id
        self.assertTrue(close_failed)
        self.assertEqual(report.status, RunStatus.FAILED)
        self.assertEqual(report.failure.category, FailureCategory.MANIFEST_FAILURE)
        self.assertEqual(report.failure.message, "manifest publication state is uncertain")
        self.assertIsNone(report.manifest)
        self.assertFalse((run_dir / "manifest.json").exists())

    def test_concurrent_run_creation_has_single_winner(self):
        barrier = threading.Barrier(2)

        def create_run():
            barrier.wait()
            with ArtifactStore(self.root) as store:
                return store.prepare_run("concurrent-run")

        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(lambda _: self._capture(create_run), range(2)))

        self.assertEqual(sum(not isinstance(value, Exception) for value in results), 1)
        self.assertEqual(sum(isinstance(value, FileExistsError) for value in results), 1)

    @staticmethod
    def _capture(callback):
        try:
            return callback()
        except Exception as error:
            return error

    def test_manifest_publication_is_exclusive_and_corruption_detected(self):
        run_dir, _ = self.store.prepare_run("manifest-run")
        reference = self.store.write_manifest(run_dir, {"value": "original"})
        manifest_path = self.root / reference.path
        original_bytes = self.read_verified(self.store, reference)

        with self.assertRaises(FileExistsError):
            self.store.write_manifest(run_dir, {"value": "replacement"})
        self.assertEqual(self.read_verified(self.store, reference), original_bytes)

        manifest_path.write_bytes(b"corrupted")
        with self.assertRaises(ArtifactIntegrityError):
            self.store.verify(reference)

    def test_manifest_size_limit_is_enforced(self):
        run_dir, _ = self.store.prepare_run("large-manifest")
        values = ["x" * 1_000_000 for _ in range(17)]

        with self.assertRaises(ValueError):
            self.store.write_manifest(run_dir, {"values": values})

    def test_manifest_serialization_is_independent_of_mapping_insertion_order(self):
        first_run, _ = self.store.prepare_run("ordered-first")
        second_run, _ = self.store.prepare_run("ordered-second")
        first = self.store.write_manifest(first_run, {"z": "é", "a": -0.0})
        second = self.store.write_manifest(second_run, {"a": -0.0, "z": "é"})

        self.assertEqual(
            self.read_verified(self.store, first),
            self.read_verified(self.store, second),
        )

    def test_artifact_reference_rejects_invalid_digest(self):
        with self.assertRaises(ValueError):
            ArtifactReference("file.bin", "not-a-digest")


if __name__ == "__main__":
    unittest.main()
