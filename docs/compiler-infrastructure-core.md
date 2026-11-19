# Compiler-Neutral Infrastructure Core

- **Status:** implemented proposal; not an approved compiler or competition API.
- **Date:** 2026-11-19
- **Scope:** request validation, in-process and subprocess execution seams,
  injected verification, artifact integrity, deterministic manifests, and
  structured outcomes.
- **Not covered:** quantum circuit semantics, compiler IR, benchmark adapters,
  official serialization, or competition acceptance.

## Contracts

The implementation is in `tools/compiler_infrastructure.py` and uses only the
Python standard library plus the existing
[`tools/verify_sha256.py`](../tools/verify_sha256.py).

| Contract | Fields and invariants | Serialization |
|---|---|---|
| `ArtifactReference` | Root-relative normalized POSIX path and exactly 64 hexadecimal SHA-256 characters. Absolute paths, traversal, backslashes, drive paths, and control characters are rejected. | `to_dict` / strict `from_dict`; digest is normalized lowercase. |
| `CompilationRequest` | Schema version 1, safe request ID, at most 10,000 artifact references, JSON-object options, optional non-negative seed up to 4096 bits. JSON options are validated, copied, and recursively frozen; tuples and other non-JSON values, non-finite numbers, integers over 4096 bits, strings over one million characters, nesting over 64 levels, and more than 100,000 values are rejected. | `to_dict` / strict `from_dict`; extra or missing fields and unsupported versions are rejected. |
| `CompilationResult` | `SUCCEEDED` or `FAILED`, immutable tuple of at most 10,000 output references, and bounded string diagnostics. | `to_dict`. |
| `ExecutionContext` | Existing artifact root, output directory contained beneath that root, and optional non-negative seed. | In-process interface only. |
| `SubprocessCompilerExecutor` | Configured argv, executor identity/version, explicit environment mapping, and finite wall-clock timeout. | Local JSON protocol over stdin/stdout; not an official compiler contract. |
| `VerificationRequest` | A validated request and compilation result. | In-process interface only. |
| `VerificationResult` | `PASSED`, `FAILED`, `UNAVAILABLE`, `NOT_EXECUTED`, or `ERROR`, with bounded string diagnostics. | `to_dict`. |
| `ExecutionReport` | Overall `SUCCEEDED`, `FAILED`, or `BLOCKED`, optional compilation result, verification result, manifest reference, and categorized failure. A successful report requires successful compilation, passed verification, and a manifest. | `to_dict`. |

`CompilerExecutor.compile(request, context)` and
`CompilerVerifier.verify(request, context)` are Python protocols for dependency
injection. `SubprocessCompilerExecutor` implements the executor seam for an
external configured command. These are infrastructure extension points, not
discovered or approved competition APIs. Test doubles are used only in
`tests/test_compiler_infrastructure.py`; they do not compile quantum circuits
or implement an official verifier.

## Local subprocess protocol

`SubprocessCompilerExecutor` passes a canonical JSON object to the configured
argument vector's stdin:

```json
{
  "protocol_version": 1,
  "request": {"schema_version": 1},
  "artifact_root": "/absolute/trusted/root",
  "output_dir": "/absolute/trusted/root/runs/<request-id>/outputs"
}
```

The abbreviated request above is illustrative; the actual `request` value is
the complete `CompilationRequest.to_dict()` representation. The process must
write exactly one JSON object to stdout with exactly `status`, `artifacts`, and
`diagnostics` fields matching `CompilationResult.to_dict()`. Compiler logs
belong on stderr. A nonzero exit becomes a failed compilation; malformed or
oversized successful output is rejected. Declared artifacts are subsequently
checked by `run_compilation` against the root and their SHA-256 values.

Invocation uses an argv sequence, never a shell; no parent environment is
inherited unless explicitly included in the executor's environment mapping.
At most 256 environment entries and 1 MiB of UTF-8 environment data are
accepted. The working directory is the run's output directory. The request
and stdout are each capped at 16 MiB; captured stderr is capped at 256 KiB.
JSON serialization enforces the request and manifest byte limits while
encoding. The default wall-clock timeout is 300 seconds, with a maximum
configured timeout of 24 hours. On timeout, cleanup sends `SIGTERM` to the
dedicated POSIX process group, waits at most 250 ms, then sends `SIGKILL` to
remaining group members and reaps the direct child with bounded waits. Cleanup
outcomes are included in timeout diagnostics. The same group cleanup runs
after the direct child exits, to stop leftover workers in its managed group.
`ProcessIsolationBackend` is injectable so a deployment can supply a platform-
specific lifecycle/containment implementation; the default
`PosixProcessGroupBackend` fails closed when POSIX process-group support is
unavailable. The selected backend name, version, and declared containment
scope are recorded in the manifest, but the infrastructure cannot independently
prove that a custom backend enforces its declaration. Pipe readers and the
request writer use nonblocking I/O and bounded shutdown waits. Exceeding
either capture limit terminates the managed process group, bounding captured
output and limiting overrun to bytes already buffered by the pipe/read chunk.
This is not a CPU, memory, or disk quota.

Every explicitly configured environment value and every request option value
under a secret-like field name is redacted from returned compiler/verifier
diagnostics and manifest request data. The subprocess receives the original
validated request options; redaction does not change compiler input semantics,
so configured executables are trusted with those values. Secret command
values must be passed using `sensitive_arguments`; other arguments are not
assumed secret. Redaction
covers exact configured strings, not encoded or transformed values, and
field-name matching cannot detect a secret placed under an innocuous name.
Compiler-controlled text may still contain unrecognized secrets or arbitrary
paths.

The process receives absolute artifact paths and runs with the caller's OS
permissions. This is **not a sandbox**: the executable can access any file,
network, or resource available to the caller, can consume disk while writing
artifacts, and can modify inputs before integrity checks detect the change.
No CPU, memory, disk, or network quotas are applied. A descendant that creates
a new session can escape timeout process-group cleanup; do not use this
executor for untrusted programs. Raw command arguments and environment values
are not recorded in manifests. The executor record includes the executable
basename, argument count, timeout, environment key names, and whether a
keyed configuration fingerprint is available. If a caller supplies a
32-byte-or-longer `configuration_fingerprint_key`, the manifest contains an
HMAC-SHA256 fingerprint of the command, environment, timeout, executor
identity, and declared isolation-backend identity/scope; the key is never
stored. The same key also fingerprints the canonical request. Use the same
separately managed key to compare fingerprints. These fingerprints do not
reconstruct the configuration or establish the executable's content identity.

`ArtifactStore.verify(reference)` returns the verified digest, not a path that
could later be reopened against a changed pathname. Consumers that need the
bytes can use `ArtifactStore.open_verified(reference)`, which yields a
read-only stream held on the validated descriptor and rechecks the digest on
context exit. During verifier handoff, `VerificationRequest.verified_artifacts`
provides a read-only mapping from every input/output reference to its opened,
verified stream; streams remain open for the verifier call and are checked
again when it returns. Verifiers should consume these handles rather than
reopening paths. Artifact paths are revalidated at the store boundary; runtime
type annotations alone are not treated as input validation.

## Execution and artifact lifecycle

`run_compilation` performs these steps:

1. Require a validated request and configured executor.
2. Verify every input reference against the configured artifact root using
   descriptor-relative traversal.
3. Create a new `runs/<request_id>/outputs` directory without overwriting an
   existing run.
4. Pass the executor an `ExecutionContext` containing the root, output
   directory, and explicit seed.
5. Re-verify inputs after execution to detect compiler-side mutation. Reject
   malformed results; require each declared output to resolve within the run
   output directory and match its digest.
6. Invoke the configured verifier. Recheck input and output digests after
   handoff to detect mutations by the verifier. A missing verifier produces
   `UNAVAILABLE` and overall `BLOCKED`, never success.
7. Write a deterministic manifest, then return an `ExecutionReport`. Failed
   compilation leaves partial output in its unique run directory and attempts
   to write a failure manifest; partial output is not treated as successful.

Manifest JSON uses UTF-8, sorted keys, compact separators, and rejects
non-finite numbers, over-depth/over-count option values, oversized strings,
more than 1,000 diagnostics or one million diagnostic characters, and
serialized manifests larger than 16 MiB. A complete manifest is written
to a unique same-directory temporary file, fsynced, and published by an
exclusive hard link; existing manifests are never overwritten. The directory
is fsynced after publication. If that sync fails, the store attempts to remove
the published manifest and sync the rollback. If rollback or its sync also
fails, it reports an explicitly uncertain publication state and returns no
manifest reference. The reference digest is computed from the serialized
bytes before publication, so a descriptor-close error after successful sync
returns the known published reference with a manifest-failure outcome. It
records request data after redacting values under secret-like field names,
input and output digests, Python implementation/version/platform/architecture,
executor/verifier names and versions, safe subprocess configuration metadata,
and verification outcome. It intentionally omits wall-clock timestamps to
preserve deterministic manifest bytes and does not claim authenticated
provenance.

Reproducibility levels are: **0** result recorded; **1** inputs and complete
configuration recorded; **2** toolchain and executable identity recorded;
**3** environment sufficiently pinned for controlled replay; **4** independent
replay reproduced the relevant result. Current manifests explicitly report
**LEVEL 0**. Request, input/output references, seed, runtime metadata, and
verifier result are recorded, but full command/environment values, executable
content digest, dependency lock, and independent replay are unavailable.
An HMAC fingerprint can identify matching configuration only when the same
external key is available; it does not raise the replay level. No run is
reported as LEVEL 4.

Compiler-controlled diagnostics are redacted for configured environment
values, explicitly marked command secrets, and secret-like request fields.
Unrecognized or transformed secrets can still appear in diagnostics. A
manifest hash establishes byte equality with its bytes, not publisher
identity.

Run IDs are single-use within one artifact root. Creation uses descriptor-
relative `mkdir`, so concurrent attempts for the same ID have one winner;
the other fails with an already-exists error rather than reusing or replacing
artifacts. Manifest publication is also exclusive under concurrent writers.
To compare repeated deterministic runs, use isolated roots.

## Error behavior

`RunFailure.category` distinguishes invalid requests, unsupported operations,
missing dependencies, missing artifacts, missing executors, environment and
execution failures, malformed results, artifact failures, digest mismatches,
verification failures/errors, serialization failures, and manifest failures.
Untrusted exception messages are not copied into failure messages; the
exception class is reported. Compiler diagnostics and verifier diagnostics
remain explicit structured fields.

Overall status rules:

- `SUCCEEDED`: compilation succeeded, all declared outputs passed integrity
  checks, and verification returned `PASSED`.
- `FAILED`: execution, result, artifact integrity, verification, or manifest
  processing failed.
- `BLOCKED`: no executor or no usable verification result is available.

## Security boundaries and limitations

- Artifact references are relative to an explicit root; lexical traversal,
  absolute paths, and platform-specific path forms are rejected.
- `ArtifactStore` rejects non-`ArtifactReference` values and revalidates the
  reference path before descriptor-relative access, including callers that
  bypass the request deserializer.
- Output artifacts must resolve beneath the per-run output directory.
- The artifact store uses a retained root directory descriptor and
  descriptor-relative traversal with `O_NOFOLLOW`/`O_DIRECTORY`. Files are
  opened nonblocking, checked as regular files, and hashed through that same
  descriptor using the existing SHA-256 streaming helper.
- File metadata is compared before/after hashing to detect ordinary concurrent
  changes; this does not provide an immutable snapshot against an adversary
  able to modify file contents while preserving observable metadata.
- Outputs are re-verified after verifier handoff and before manifest
  publication, but are not locked or snapshotted. A concurrent writer may
  change an output after the final hash check; the manifest records the checked
  digest but cannot ensure the file remains unchanged afterward.
- The store fails closed if the platform lacks the required `dir_fd`,
  `O_NOFOLLOW`, or `O_DIRECTORY` capabilities. The artifact root and its parent
  path are trusted configuration; executors receive a path and are not
  sandboxed from filesystem access.
- Executors and verifiers run in-process with the caller's permissions; these
  protocols do not sandbox code. A malicious or defective adapter could modify
  any file it can access, including declared inputs. Input immutability is
  demonstrated only for the test doubles and checker behavior, not enforced
  against arbitrary plugins.
- This layer does not authenticate compilers, verifiers, inputs, or manifests.
- The request seed is passed to the executor; the infrastructure does not
  control randomness inside an executor that ignores it.
- Manifest bytes are deterministic for the same normalized request, component
  metadata, results, and Python JSON implementation. Cross-Python-version or
  cross-platform byte identity is not promised.
- Verifier “passed” means only that the configured verifier returned that
  status. It does not imply official competition acceptance.

## Security and correctness review findings

These are findings from the local implementation review, not external
penetration testing.

| ID / severity | Finding and evidence | Fix and regression test |
|---|---|---|
| CINF-01 / MEDIUM | The earlier artifact flow resolved a path and reopened it, leaving a pathname replacement window. | Retained root descriptor, `openat`-style `dir_fd` traversal and descriptor-backed verification. Covered by `test_artifact_descriptor_stays_anchored_if_root_path_is_replaced`, `test_artifact_store_rejects_symlinked_file`, and `test_artifact_store_rejects_symlinked_intermediate_directory`. |
| CINF-02 / MEDIUM | Inputs were not rechecked after execution, and outputs could change after their initial digest check or during verifier handoff. | Reverify inputs after executor and verifier; reverify outputs after verifier. Covered by `test_executor_input_mutation_is_detected`, `test_verifier_output_mutation_is_detected_after_handoff`, and `test_open_verified_detects_mutation_during_consumer_use`. |
| CINF-03 / LOW | Writing the final manifest directly could leave a partial file after interruption. | Write/fsync a unique temporary file, publish with an exclusive hard link, fsync directory. Covered by `test_manifest_publication_is_exclusive_and_corruption_detected` and `test_concurrent_manifest_publication_has_single_winner`. |
| CINF-04 / LOW | Existing run-directory setup checked the path after creation without anchoring operations to the artifact root. | Descriptor-relative directory creation; ID collisions remain exclusive and are not overwritten. Covered by `test_duplicate_run_id_cannot_overwrite_existing_run` and `test_concurrent_run_creation_has_single_winner`. |
| CINF-05 / LOW | The SHA-256 CLI included the supplied path in success and mismatch output and full `OSError` text in failures, potentially exposing local path details. | Report status/digests or the error reason without echoing paths. Covered by `test_file_error_does_not_disclose_full_path` and `test_fails_for_digest_mismatch`. |
| CINF-06 / MEDIUM | Request option nesting and serialized size, reference counts, diagnostic payloads, and seed magnitude lacked consistent bounds, permitting excessive work or serialization failure from caller-owned data. | Limit nesting to 64, option values to 100,000, strings to 1,000,000 characters, references to 10,000, seed integers to 4096 bits, diagnostics to 1,000 entries/1,000,000 characters, and manifests to 16 MiB. Covered by `test_request_validation_and_immutable_options_snapshot` and `test_manifest_size_limit_is_enforced`. |
| CINF-07 / MEDIUM | `ArtifactStore.verify` relied on its type annotation; a custom object with `path="../outside"` reached descriptor-relative traversal and could read a file outside the root. This was reproduced before correction. | `_open_artifact` now requires an `ArtifactReference` and revalidates its path before opening. Covered by `test_artifact_store_rejects_unvalidated_reference_type`. |
| CINF-08 / MEDIUM | A directory `fsync` failure after publishing `manifest.json` raised an error while leaving the file visible, so the caller reported no reference and a retry could not publish. A directory-descriptor close error after publication had the same missing-reference problem and could mask an earlier failure. | The store attempts to unlink and sync a failed publication; reports uncertain state if rollback fails; computes the reference before publication and includes it if descriptor close fails after successful sync. Covered by `test_directory_fsync_failure_removes_published_manifest`, `test_manifest_rollback_sync_failure_is_reported_as_uncertain`, `test_manifest_directory_close_failure_returns_published_reference`, `test_failure_manifest_close_failure_returns_published_reference`, and `test_directory_close_failure_does_not_mask_rollback_uncertainty`. |

The existing tests do not establish resistance to a malicious in-process
executor/verifier, filesystem content changes that evade available metadata
checks, storage-device failure, permission-denied behavior under every
privilege model, or every POSIX filesystem's hard-link/fsync guarantees.

## Reproducible validation

From the repository root, with Python 3.8 or newer on the supported POSIX
filesystem described above:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 -B -c 'import ast, pathlib; paths=("tools/verify_sha256.py", "tests/test_verify_sha256.py", "tools/compiler_infrastructure.py", "tests/test_compiler_infrastructure.py"); [ast.parse(pathlib.Path(path).read_text(), filename=path) for path in paths]; print("Syntax OK:", ", ".join(paths))'
```

Both commands use the standard library. There is still no project-wide
compiler build system or dependency manifest; this validation applies to the
utility and compiler-neutral infrastructure only.
