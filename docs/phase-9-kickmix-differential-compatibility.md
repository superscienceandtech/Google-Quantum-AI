# Phase 9 — Kickmix Differential Compatibility

- **Pinned reference:** Qualtran/Kickmix
  `f559b12af459e7e97e6c6c382434431c03b903c9`
- **Runtime availability:** Kickmix, Qualtran, NumPy, and pytest absent.
- **Differential status:** `SOURCE_INSPECTED`

The pinned KMX format and binary-format documentation were reviewed where
available. The local parser provides bounded KMX v2 text behavior:

- local opcode validation;
- sparse register and wire parsing;
- condition syntax and stack tests;
- decimal exponent text preservation;
- quote and comment handling;
- resource ID-span summaries.

It does not implement or execute:

- upstream parser binaries;
- canonical KMB serialization;
- KMB framing or truncation checks;
- upstream KMX exception equivalence;
- official fixture round trips.

## KMB status

**NOT IMPLEMENTED**.
