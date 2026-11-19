# Phase 9 — Runtime Reproducibility

## Observed environment

- CPython 3.12.3
- Linux x86_64
- `/usr/bin/python3`

Unavailable:

- Kaggle runtime image/digest
- Kickmix/Qualtran versions
- NumPy/pandas/pytest
- verifier dependencies
- official native libraries
- compiler/linker/toolchain versions

No package or environment was installed or changed.

## Validation commands

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 -B -c 'import ast,pathlib; paths=sorted(pathlib.Path("tools").glob("*.py"))+sorted(pathlib.Path("tests").glob("*.py")); [ast.parse(path.read_text(encoding="utf-8"), filename=str(path)) for path in paths]; print(f"AST syntax OK: {len(paths)} Python files")'
git diff --check
```
