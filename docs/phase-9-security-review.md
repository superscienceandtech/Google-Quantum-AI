# Phase 9 — Security Review

## Snapshot storage

`ArtifactStore` now accepts explicit optional:

- `snapshot_limit_bytes`
- `snapshot_total_limit_bytes`

No default production values are selected. Per-snapshot and active aggregate
limits are validated and tested. An omitted limit remains unlimited.

Reservation accounting is released only after a reservation succeeds. Failed
per-snapshot or aggregate reservations do not subtract bytes from a live
snapshot; temporary-file allocation and source-verification failures also
release successful reservations.

## Subprocess containment

The POSIX backend remains process-group-based. It is not a complete OS
sandbox. Descendants that create a new session can escape process-group
timeout cleanup.

## Handoff archive controls

The handoff utility rejects traversal, absolute paths, backslashes,
symlinks, hardlinks, duplicate/colliding names, special archive entries,
corrupt archives, and configured size/count limits. TAR compression-ratio
enforcement is explicitly unsupported.

It does not extract or execute payloads.
