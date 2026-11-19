# Phase 6: Execution and Artifact Lifecycle

## Current implementation

**VERIFIED LOCAL FACT:** [`tools/compiler_infrastructure.py`](../tools/compiler_infrastructure.py)
defines an in-process `CompilerExecutor.compile(request, context)` protocol.
Phase 7 adds `SubprocessCompilerExecutor`, which implements that protocol using
a bounded local JSON stdin/stdout protocol. It runs only explicitly configured
commands; it is not a discovered competition compiler interface.
`run_compilation` verifies declared inputs, creates an exclusive run directory,
invokes the executor, rechecks inputs and output digests, invokes an optional
in-process verifier, rechecks artifact integrity, and writes a deterministic
manifest. Missing verification is `BLOCKED`; only an explicit
`VerificationStatus.PASSED` yields local success.

The artifact store uses a retained root descriptor and descriptor-relative
access with `O_NOFOLLOW`/`O_DIRECTORY`, rejects non-regular files, enforces
root-relative paths, and publishes manifests via a same-directory temporary
file and exclusive link. Run IDs and manifests are not silently overwritten.
These are local infrastructure guarantees under the supported POSIX
capabilities, not proof of official compiler compatibility.

## Current limitations

- In-process executor and verifier code run with the caller's permissions.
  The subprocess executor also runs with those permissions and is not a
  sandbox.
- The subprocess executor has a wall-clock timeout and bounded stdin/stdout/
  stderr handling, and kills its POSIX process group. It has no memory, CPU,
  disk, or network restriction. An executable can consume disk through
  artifacts, and output configuration is trusted.
- The configured command and environment are not stored in manifests because
  they may contain secrets; external command configuration is therefore not
  fully reproducible from the manifest alone.
- The seed is passed to the executor; this layer cannot force a plugin to use
  it.
- The manifest contains Python/platform metadata, so byte-for-byte identity
  across different runtime/platform metadata is not promised.
- Partial compiler outputs may remain in their unique failed run directory;
  they are not reported as successful artifacts.
- Artifact roots and their parent paths are trusted configuration. Filesystem
  race resistance depends on descriptor-relative POSIX operations.

## Phase 6 compiler process decision (historical)

**VERIFIED LOCAL FACT:** No external compiler executable, invocation contract,
or official timeout/resource policy was found. The paper and upstream source
identify Kickmix as a circuit-building/serialization/simulation package, but
do not establish a competition compiler process contract.

Phase 6 therefore added no subprocess backend. Phase 7 adds a generic local
process executor for infrastructure testing and future configured backends;
it does not assert that a competition compiler or process contract exists.

## Phase 7 local process protocol

**ENGINEERING PROPOSAL, IMPLEMENTED LOCALLY:** `SubprocessCompilerExecutor`
uses argv without a shell, receives canonical request JSON on stdin, runs in
the per-run output directory with only its explicit environment, and parses a
strict `CompilationResult`-shaped JSON object from stdout. Request and pipe
capture sizes are bounded; the default timeout is 300 seconds. A timeout kills
the POSIX process group. Malformed results, missing executables, timeouts, and
nonzero exit codes remain distinct in structured outcomes.

The protocol is not official. Process execution does not isolate the compiler
from caller-owned files, and no CPU/memory/disk/network quota is set.
Captured stdout/stderr are memory-bounded, but the process may emit more before
timeout, and a descendant that creates a new session can escape process-group
cleanup.
