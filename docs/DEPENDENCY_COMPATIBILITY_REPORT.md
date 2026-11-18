# Dependency Compatibility Report

## Actual verifier imports

INVSQRT, DQI:

- Python standard library
- NumPy
- kickmix

DFTHC-SOS:

- NumPy
- NumPy typing
- kickmix
- no direct PySCF or OpenFermion dependency

No Cirq, Qualtran, or external DFTHC package is imported by the verifiers.

## Current tested environment

- Python: 3.13.15 in `/home/yousuf/.venvs/gqai/bin/python`
- NumPy: 2.5.5
- SciPy: 1.18.1
- kickmix: loaded as `external/kickmix/kickmix.so`
- System: Ubuntu 26.04.1 LTS on Linux 6.18 WSL2
- Memory: 8,035,968 KB total
- Disk: 92 GB free in the workspace view

The shared library is ELF 64-bit and dynamically links `libstdc++.so.6`, `libm.so.6`, `libgcc_s.so.6`, and `libc.so.6`.

## Compatibility findings

- All three verifier `--help` commands and all bounded structural loads work in Python 3.13.15 with NumPy 2.5.5 and the packaged kickmix shared library.
- Python 3.14.7 and NumPy 2.5.3 are available system-wide, but the authoritative observed evidence used Python 3.13.15.
- Kickmix is not an installed package; it is an official shared library supplied under `external/kickmix/`.
- `pyscf`, `openfermion`, `cirq`, and `qualtran` are not required by the observed verifier source and are not installed.
- No pinned dependency manifest is present; a manifest should be created only after test evidence establishes all official versions.

## Memory and disk evidence

- INVSQRT full sample: max RSS 523,844 KB.
- DFTHC-SOS full sample: max RSS 1,112,216 KB.
- DQI 256-shot: max RSS 3,482,040 KB.
- DQI 1024-shot: max RSS 3,496,640 KB.
- Host memory is approximately 8 GB, so DQI should use one worker for full execution.
- No 102,400-shot DQI run was executed.
