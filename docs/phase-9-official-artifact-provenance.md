# Phase 9 — Official Artifact Provenance

## Artifact acquisition

No official competition artifact was acquired in Phase 9.

Checked:

- Kaggle CLI availability;
- Kaggle environment variables;
- `~/.kaggle/kaggle.json`;
- local repository artifacts;
- Kaggle data-list endpoint.

The endpoint was not authorized and no bytes were downloaded.

## Provenance model

The repository's handoff utility computes SHA-256 and file size, validates
strict manifest fields, rejects traversal and hard links, and distinguishes:

- PENDING;
- MISSING;
- integrity mismatch;
- locally computed hash without independent authenticity.

A locally computed digest is not an official publisher digest.
