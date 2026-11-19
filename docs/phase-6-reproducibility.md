# Phase 6: Reproducibility Record

**Review date:** 2026-11-19

## Local environment

**VERIFIED LOCAL FACT:**

- OS: Linux x86_64 on WSL2, kernel `6.18.33.2-microsoft-standard-WSL2`,
  glibc 2.39.
- Python: CPython 3.12.3, GCC 13.3.0 build.
- pip: 24.0.
- g++: 13.3.0.
- GNU Make: 4.3.
- uv: 0.12.19.
- Node.js: v24.22.0.
- No project Python dependency manifest, lockfile, compiler build definition,
  or supported Python-version range was found.
- Pylance's workspace interpreter is `/usr/bin/python3`; its
  `pylanceImports` query returned “No import data”. A source scan found only
  Python standard-library imports and imports from this repository's own
  `tools` package.

No dependency was installed or upgraded.

## Kickmix source and package boundary

**VERIFIED UPSTREAM:** The inspected Qualtran commit is
`f559b12af459e7e97e6c6c382434431c03b903c9`; current public `main` resolved to
that same SHA at review time. Upstream source is C++/Python and includes
Kickmix circuit construction, file I/O, and simulation.

The pinned build metadata lists a development package version and NumPy as a
requirement. Public PyPI lists `kickmix` 1.0.0 with NumPy. The PyPI release's
source-commit mapping and its relationship to the competition's Kickmix binary
are **UNKNOWN**. No package or source was installed or built.

**PARTICIPANT-MIRROR only:** QArena's README says its runner uses CPython 3.13
and points to a competition KMB binary. Since QArena explicitly disclaims
Google/Kaggle sponsorship and the binary was not inspected, this is not a
verified toolchain requirement.

## Commands and observed results

Baseline and post-documentation validation:

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
exit 0
Ran 53 tests
OK
```

Python AST parsing succeeded for all four project/test Python files. No
benchmark compiler command, Kickmix build, `.kmb` round trip, verifier command,
or official acceptance run was executed.

## Reproducibility limits

- The local 53-test result is reproducible only as local infrastructure
  evidence; it does not establish a clean-checkout benchmark build.
- There is no project lockfile or reproducible compiler setup script.
- Cross-platform KMB compatibility and binary stability were not tested.
- The competition's private salt is unavailable, so salted test vectors cannot
  be reproduced.
- The working tree includes preserved user/phase files; this task did not
  attempt a destructive cleanup or a clean checkout.
- Repo-wide `git diff --check` flags the CRLF line ending on the final bullet
  of the protected README's pre-existing working-tree delta. A targeted scan
  of Phase 6 task files found no trailing whitespace.

No claim of a reproducible competition compiler workflow is made.
