# DQI-P008 — Reversible Decoder Specification and Computational Contract

**Project:** Google Quantum AI — Verifiable Quantum Circuit Compilation
**Workstream:** DQI Decoder
**Phase:** 01 — P008
**Branch:** `feat/dqi-decoder`
**Repository:** `D:\PROJECT\Quantum_AI\Google-Quantum-AI`
**HEAD:** `5391b2e7123484efacffc0588f5e761e67b5cb55`
**Assessment date:** 2026-11-20
**Disposition:** **PARTIALLY SPECIFIED — not implementation-ready for a verifier-compatible reversible circuit**

## 1. Executive summary

This report specifies the research-level reversible DQI operation supported
by Rubin et al., arXiv:2610.23832v2, §§III.2.1–III.2.2, Eqs. (36)–(40), and
maps it to the existing P005–P007 classical prototype. It separates the
paper’s defined mathematical behavior from proposed reversible programming
contracts and from missing executable verifier details.

On the promised domain, the paper establishes a unique error vector `e` of
weight at most `ell=35` for a syndrome `s=B^T e`. Equation (38) specifies
that, for a fixed classical record `c`, the circuit preserves `s`, applies
phase `(-1)^(c·bin(e))`, and returns workspace to zero. Equation (36)
expresses erasure of the error register while retaining the syndrome.
The paper’s reference construction describes synchronized EEA, Chien search,
Forney recovery, per-symbol phase correction, clearing temporary symbol
workspace, and EEA uncomputation.

The paper supports an architectural reversible algorithm, and some
reversible-arithmetic facts, but this repository has no DQI circuit source,
quantum framework dependency, official verifier, official sample/fixtures,
or executable register serialization. The classical Python decoder is not
reversible. Exact field-to-wire encoding, total behavior outside the promise,
precise circuit-level EEA state transitions, a complete garbage-cleanup
proof for a new implementation, and official resource interpretation remain
unresolved.

**Implementation readiness:**

- Reversible field arithmetic: **PARTIALLY SPECIFIED**.
- Reversible polynomial arithmetic and EEA: **PARTIALLY SPECIFIED**.
- Complete reversible decoder under the paper’s logical contract:
  **PARTIALLY SPECIFIED**.
- Official verifier integration: **BLOCKED**.
- Benchmark execution: **BLOCKED / separately gated**.

No circuit, gates, ancilla estimates, benchmark, verifier, or DQI tests were
created or run in P008. No P001–P007 document or source/test file was
modified. P008 does not start P009.

## 2. Repository and source baseline

### Repository state

- Root: `D:\PROJECT\Quantum_AI\Google-Quantum-AI`
- Branch: `feat/dqi-decoder`
- HEAD before and after: `5391b2e7123484efacffc0588f5e761e67b5cb55`
- Initial staged changes: none.
- Initial tracked unstaged changes: none.
- All 48 initial untracked paths were preserved: the P001–P007 reports,
  existing DQI source/tests, the P005 gap-closure report, and unrelated
  INVSQRT `.pyc` cache files.
- The P008 target did not exist initially.
- `README.md` is the only tracked file at this HEAD. No dependency manifest
  (`pyproject.toml`, `setup.py`, requirements file, lock file, or equivalent)
  or quantum-framework imports were found. No dependency was installed.
- A pre-existing root `.pytest_cache` directory was visible; it was not
  read, altered, or removed.

### Prior documents and code inspected

P001–P007 and the full DQI package/test inventory were inspected for
continuity. P002/P003/P004 record unresolved executable register and bit
serialization, and P003/P004 report the official verifier/scorer,
reference/sample circuit, fixtures, and expected outputs absent in their
inspected refs. P005–P007 provide classical field, syndrome, polynomial,
decoder, and independent correctness-test evidence only.

### Primary source inspected

Nicholas C. Rubin et al., *Leveraging verifiable structure in quantum
circuits to find more efficient compilations with agentic AI*,
[arXiv:2610.23832v2](https://arxiv.org/abs/2610.23832v2), version dated
2026-10-21; versioned HTML:
[https://arxiv.org/html/2610.23832v2](https://arxiv.org/html/2610.23832v2).
The directly inspected DQI text was §§III.2.1–III.2.3:

- Eqs. (36)–(38): error-register erasure, phase correction, input/output
  basis-state operation.
- Eq. (39) and surrounding text: code parameters, field basis, syndrome
  equation, and correctable radius.
- Eq. (40) and surrounding text: EEA/key equation, locator, Chien/Forney
  recovery, EEA uncomputation, polynomial register sharing and degree
  pointers, field-operation construction notes.
- §III.2.3, Eqs. (41)–(43): verifier sampling/score claims at paper level.

The public versioned HTML was inspected; no local immutable paper copy or
raw-byte hash was created. It is primary research evidence, not the
competition-owner verifier release or a circuit artifact.

## 3. Mathematical reversible input/output contract

### 3.1 Paper-established mathematical domain

Let `m=4095`, `n=70`, `b=12`, and `ell=35`. Let
`e=(e_0,...,e_(m-1))` be a vector over `GF(2^12)` and let
`s=B^T e` be its syndrome, equivalently represented in §III.2.2 by

```text
s_i = sum_(j=0)^(m-1) e_j alpha^((i+1)j),   i=0,...,n-1.
```

The code has minimum distance `n+1=71`. The paper states that when
`2ell <= n`, two errors of weight at most `ell` cannot have the same
syndrome; thus each promised syndrome determines a unique correctable
error vector. Here `2ell=n=70`.

Define the promised syndrome set

```text
D = { B^T e : e in GF(2^12)^m and wt(e) <= 35 }.
```

On `s in D`, write the unique vector as `e(s)`. The field and basis
mathematics are in the paper. Field-element wire order, register order,
and serialized bits are not established by that mathematical definition.

### 3.2 Required operation

For a fixed classical record `c` of `m*b` bits, Eq. (38) specifies the
following action on its stated domain:

```text
U_c |s>|0>_W
  = (-1)^(c · bin(e(s))) |s>|0>_W,
  s in D.
```

Here `W` is workspace; the phase dot product is binary parity. The syndrome
is preserved, the error is not an output register of Eq. (38), and all
workspace must be returned to zero. The record `c` is classical in the
paper’s verifier input description; this equation does not establish a
quantum record register. The exact implemented record-to-wire order and
field-symbol bit serialization remain **UNRESOLVED**.

Equation (36) also states the coherent error-erasure behavior on the promised
superposition:

```text
sum_(wt(e)<=ell) a_e |e>|B^T e>
  -> |0> sum_(wt(e)<=ell) a_e |B^T e>.
```

This is possible on that subspace because the syndrome uniquely labels each
promised error. It is not a specification for every basis state outside that
subspace.

### 3.3 Preserved data, intermediate values, and invalid cases

| Item | Contract status |
|---|---|
| Syndrome `s` | Must be preserved exactly on promised inputs. |
| Classical record `c` | Supplied as fixed classical phase-control data in the paper; not transformed by the logical operation. Exact executable interface is unavailable. |
| Error locations and magnitudes | Computed as intermediate information to form the phase; Eq. (38) does not require returning them. |
| Error vector `e(s)` | Unique on the promised domain; temporary in the reference procedure, not a final output of Eq. (38). |
| Workspace `W` | Must finish in the all-zero state for the promised input. |
| Outside `D` | Behavior is not specified by Eq. (38). A physical circuit still has a total operation, but the paper-level promise does not provide its required phase/output semantics. |
| No decoding solution | A circuit cannot raise a Python exception. The benchmark’s behavior outside its promised input distribution is not established here; a circuit implementation still needs a defined total gate sequence. |
| `bin(e)` and ordering | Paper identifies the chosen field basis and binary-parity intent, but verifier wire serialization and record ordering are not available. |

### 3.4 In-place permutation versus reversible embedding

An ordinary classical map `s -> e(s)` discards `s` if its output replaces
the input; it is not generally an invertible in-place map. By contrast,
the mathematical embedding

```text
|s>|0>_E -> |s>|e(s)>_E
```

retains `s`, so it is one-to-one on the promised set. It may be used as an
engineering model for computing an answer into a separate register, provided
its internal workspace is also handled reversibly. It is not the final
benchmark operation because Eq. (38) requires workspace zero.

The paper’s Eq. (36) maps `|e>|B^T e>` to `|0>|B^T e>` on the promised
subspace. Uniqueness makes this map injective there. Neither fact specifies
the extension to all possible register states. A circuit made from reversible
classical gates must act as a permutation on its full computational basis;
the complete off-promise extension and the verifier’s treatment of those
inputs remain **UNRESOLVED**.

## 4. Classical-to-reversible stage mapping

The “reversible relation” column below is an engineering contract shape,
not a proposed gate decomposition. “Paper support” distinguishes the
published baseline from an unverified new implementation.

| Stage | Existing classical implementation | Required reversible relation / retained information | Workspace and garbage | Uncompute possibility and evidence | Status / unresolved decisions |
|---|---|---|---|---|---|
| Field addition | `field.add` | For field registers, target-XOR form `|a>|z> -> |a>|z+a>` retains `a`; an in-place add would need both operands or a reversible permutation | Output target; temporary wires only if a chosen decomposition needs them | Addition is XOR in characteristic two. Paper §III.2.2 says field addition is linear and compiles to CNOTs. XOR update is self-inverse | Mathematical operation **SPECIFIED**; concrete wire order and interface **PARTIAL** |
| Field multiplication / squaring / constant multiplication | `field.multiply`, `field.power` | Multiplication must retain operands or retain enough information to invert a chosen mapping; target-XOR form is a generic contract candidate. Squaring and fixed nonzero `alpha^k` multiplication are field-linear maps | Product target and possible arithmetic scratch | Paper says addition, squaring, and fixed powers of `alpha` are F2-linear and compile to CNOTs; paper describes a Karatsuba register multiplier. Exact candidate decomposition/cleanup is not present locally | **PARTIALLY SPECIFIED** |
| Syndrome processing | P005 `compute_dqi_syndrome` evaluates error vector to syndrome; P006 consumes syndrome | Decoder consumes the 70-symbol syndrome while preserving it; any polynomial view or copied coefficients must either be retained and later reversed or uncomputed | Syndrome storage plus polynomial/work registers | Paper specifies `S(z)` coefficients from syndrome and requires syndrome restoration after EEA cleanup | Mathematical indexing **SPECIFIED**; quantum register mapping **UNRESOLVED** |
| Locator/evaluator via EEA | P006 `_key_equation` | Reversible state must include enough remainder, Bézout coefficient, pointer, quotient/history data to reverse each update; paper explicitly describes synchronized EEA and temporary quotient storage | Remainder and Bézout arrays, degree pointers, temporary quotient values | Paper says optimized synchronized EEA shares shrinking remainder/growing Bézout registers and stores quotients; its outputs expose Bézout coefficients. Step 3 uncomputes Step 1 | Algorithm family **SPECIFIED**; exact local reversible transition schedule/circuit unavailable |
| Polynomial division and EEA updates | P006 uses classical `divide_polynomials`, EEA loop | Quotient/remainder update must be injective over retained state; discarded coefficients or control decisions must be recorded or reconstructed by a valid inverse | Quotient and degree/control state; shifted coefficient slices | Paper describes pointer-driven synchronized steps and available-space quotient storage; it does not make the P006 classical division loop reversible by itself | **PARTIALLY SPECIFIED** |
| Chien root evaluation | P006 `_find_error_positions` scans `j=0..4094` at `alpha^-j` | Position index and evaluation result/control must be available per position; retain only required phase/control data or uncompute evaluation state | Temporary field evaluation and root bit | Paper specifies Chien search at inverse locations and per-position processing | Mathematical search **SPECIFIED**; reversible evaluation circuit and control lifecycle **PARTIAL** |
| Error evaluator and derivative | P006 `_key_equation`, `formal_derivative` | Values of `Omega`, `sigma`, and `sigma'` must remain available until magnitude/phase use; derived values must be uncomputed afterward | Polynomial registers and per-position evaluation scratch | Paper identifies `Omega`, formal derivative, and updates `sigma`, `sigma'`, `Omega` in place | Functional roles **SPECIFIED**; exact transformations and overlap constraints **PARTIAL** |
| Forney magnitude | P006 `_recover_error_symbols` | Recover `e_i` into temporary symbol workspace while retaining enough operands for reversal; paper uses `Omega` and `sigma'` | Temporary `b`-qubit symbol register and inversion scaffold as required by the chosen circuit | Paper describes per-position Itoh–Tsujii inversion and clearing the temporary symbol workspace before next position. P007 identifies formula as a derivation tested independently, not official executable behavior | Mathematical ingredients **SPECIFIED**; exact complete reversible ratio circuit **PARTIAL** |
| Phase correction | No P005–P006 circuit code | Apply the parity `c·bin(e)` as phase while symbol bits and corresponding classical record bits are available | Temporary error-symbol bits; any MBUC measurement record is distinct from DQI input record `c` | Eq. (37) explains the phase induced by measurement records; Eq. (38) states the corrective phase; paper says apply Z gates selected by `c_i` | Logical phase **SPECIFIED**; executable bit map and verifier register names **UNRESOLVED** |
| Error-symbol scratch clearing | No quantum implementation | Restore the temporary symbol register to zero without leaving entanglement or an uncorrected phase | One position’s symbol workspace and any measurement outcome | Paper says clear the temporary symbol workspace before proceeding and describes measurement-based uncomputation for suitable field products | Cleanup must be proved per subroutine; reset/discard alone is insufficient |
| EEA/syndrome cleanup | No quantum implementation | Reverse the Step 1 computation after phase use, restoring original syndrome and zeroing all EEA auxiliaries | All EEA arrays, pointers, quotients, evaluation scratch | Paper’s Step 3 explicitly uncomputes EEA, restores syndrome, and returns auxiliary registers to zero | Required behavior **SPECIFIED**; complete implementation proof absent |
| Final corrected output | P006 returns a classical error vector | Eq. (38) has no decoded-vector output: required externally visible result is phase plus preserved syndrome and zero workspace | No error-output register required by the stated paper target | Error data are temporary and cleanup is required | Corrected received word is **NOT APPLICABLE** to Eq. (38); official schema still unavailable |

## 5. Reversible EEA specification

### 5.1 Paper-described construction

The paper’s §III.2.2 reference algorithm:

1. Forms `S(z)=sum_(i=0)^(n-1) s_i z^i` and solves
   `sigma(z)S(z) = Omega(z) mod z^(2ell)` using EEA on `z^(2ell)` and
   `S(z)`, stopping when the remainder degree is below `ell`.
2. Uses a synchronized EEA variant. The paper states that it shares
   registers between shrinking remainders and growing Bézout coefficients,
   stores temporary quotients in available register space, and provides
   Bézout coefficients needed by the next stage.
3. Stores polynomials in two arrays of `n+3` registers of `b` qubits each
   and reuses the `n` input syndrome registers in the first array. Five
   `O(log n)` degree pointers track active remainders, Bézout polynomials,
   and temporary quotients. It reports `3(n+1)+9=222` synchronized EEA
   steps for the stated `n=70`, using unary iteration over the pointers.
4. Recovers symbols and phases, then uncomputes the EEA, restoring the
   syndrome and returning auxiliary registers to zero.

These are source-established features of the paper’s reference design. They
are not implemented in the repository’s classical `_key_equation` loop and
must not be treated as a copied or independently validated local circuit.

### 5.2 Reversible-state obligations

For every synchronized update, an implementation must define the full
register state (active polynomial coefficients, degree pointers, quotient
and Bézout state, control information) and prove that the transition is
invertible on its declared domain. If a quotient, shifted coefficient,
degree decision, or previous remainder is overwritten, the circuit must
either:

- retain the overwritten information in a register that is later uncomputed;
- reconstruct it through a proven inverse transition; or
- use a source-supported reversible transformation whose injectivity is
  established.

The classical quotient/remainder identity alone does not prove that the
implemented in-place update is one-to-one. The paper’s quotient storage and
synchronized update strategy are relevant evidence, but no local gate-level
transition specification, register alias map, complete inverse trace, or
off-promise extension exists in this repository.

### 5.3 Termination and cleanup

The mathematical EEA terminates at the stated degree threshold. A reversible
implementation must encode and preserve degree/control state sufficiently to
perform the correct bounded sequence and reverse it. It must not depend on
classical early-exit logic that erases which branch or number of steps was
taken unless that information is retained or coherently uncomputed.

The required clean-up boundary is explicit: after phase correction, reverse
the EEA computation, restore the original syndrome, and return all its
auxiliary registers to zero. The paper provides this architectural claim;
the repository contains no circuit demonstrating it. No ancilla count or
gate cost is inferred for a new implementation.

## 6. Reversible finite-field arithmetic specification

`|x>` below denotes a 12-qubit field word. The table gives logical relations,
not gate decompositions or ancilla estimates.

| Operation | Mathematical function | Candidate reversible relation | Retained operands / zero handling | Cleanup and correctness condition |
|---|---|---|---|---|
| Addition | `a+b` in characteristic two, equal to bitwise XOR | `|a>|z> -> |a>|z XOR a>`; with two operands, `|a>|b>|z> -> |a>|b>|z XOR (a+b)>` | Preserve any operand needed later; XOR-target form is reversible for every input | Applying the same XOR update twice restores `z`; verify output equals field sum |
| Multiplication | `a*b mod p(alpha)` | Candidate `|a>|b>|z> -> |a>|b>|z XOR (a*b)>` | Preserve both multiplicands unless a separate proven in-place permutation is used; target initialization is explicit | Reverse by applying same target update; intermediate multiplication scratch must be uncomputed. Paper describes a 63-Toffoli Karatsuba baseline, not a cost claim for this repository |
| Squaring | `a -> a^2` in GF(2^12) | In-place `|a> -> |a^2>` is a field automorphism/permutation; alternatively XOR into a target | No operand loss if in-place bijection is used | Paper says squaring is F2-linear and compiles to CNOTs; verify all field outputs and reverse map |
| Fixed constant multiplication | `a -> k*a`, especially `k=alpha^t` | In-place permutation for nonzero `k`; XOR-target relation also possible | Retain `a` if using target accumulation; zero constant is not an invertible in-place map | Paper says powers of alpha are F2-linear and compile to CNOTs; verify chosen map and inverse |
| Inversion | `a -> a^-1` for `a != 0` | In-place inverse is bijective only after behavior for zero is defined; a valid-domain nonzero precondition alone does not specify the whole circuit | P005 `inverse(0)` raises, which is not a quantum operation. Paper’s Forney use requires nonzero `sigma'` at actual error roots; behavior for other intermediate inputs must be total | Paper describes Itoh–Tsujii inversion and its reference-resource data. A complete implementation must specify zero behavior or a reversible total extension, prove the circuit, and clear inversion scratch |
| Polynomial add/scale/multiply/divide | Operations over coefficients in GF(2^12) | Apply field relations to fixed-width coefficient registers while retaining operands and degree/control information | Fixed array bounds, degree encoding, coefficient order, and quotient storage must be explicit | Normalize/trim is classical information loss unless represented by reversible control/state; EEA’s quotient and polynomial history must be preserved/uncomputed |

The paper states that addition, squaring, and fixed powers of `alpha` are
linear over F2 and compile to CNOT gates. It reports a register multiplier
and Itoh–Tsujii inverse within its reference construction. These source facts
do not establish a locally available quantum library, accepted circuit
serialization, or the costs of a new implementation.

## 7. Ancilla and garbage lifecycle

| Register category | Purpose | Required lifecycle |
|---|---|---|
| Syndrome input | Holds the 70 field symbols `s`; mathematically 840 bits/qubits | Preserve on Eq. (38) promised inputs; restore any portions reused as EEA storage |
| Classical phase record | Holds/control-selects the `m*b` measurement-record bits `c` according to the paper | Read-only control input. It is classical data, not a quantum ancilla. Exact verifier serialization is unresolved |
| Polynomial state | Holds EEA remainders, Bézout coefficients, locator/evaluator state | May share storage only under the paper’s schedule and a proven reversible state transition; restore/clear at the cleanup boundary |
| Degree/control pointers | Track active polynomial degrees and temporary quotient positions | Retain enough state to reverse pointer-driven updates; uncompute to zero |
| Temporary quotient/history | Records data overwritten or needed for the synchronized EEA inverse | Must persist until all dependent computation and reverse EEA complete; then uncompute |
| Evaluation/magnitude scratch | Computes `sigma`, `sigma'`, `Omega`, inverses, and a temporary symbol at each position | Reuse only after each position’s scratch is proven zero or correctly measurement-uncomputed |
| Measurement outcomes for MBUC | Classically control phase correction when a temporary value is measured | Keep separate from DQI input record `c`; apply required phase fixup and account for classical record lifecycle |
| Garbage | Any intermediate correlated with input or output that is not part of the specified result | Cannot be ignored, discarded, or called clean. Must be reversibly uncomputed or removed by a source-justified measurement-based protocol with correct phase handling |

Terminology and required distinction:

- **Reuse** means allocating a register again only after proving it contains
  zero and is unentangled with live state.
- **Clearing** is the result “register equals zero”; it does not identify how
  that state was obtained.
- **Reversible uncomputation** applies an inverse computation (or another
  proven reversible cleanup) while preserving the intended phase and
  correlations.
- **Measurement/reset** is a non-unitary instrument/channel in the quantum
  model. It may be used in the paper’s MBUC model only with the prescribed
  branch-dependent phase correction and outcome handling.
- **Discarding garbage** traces out or loses information and is not equivalent
  to coherent uncomputation or to a valid MBUC protocol.

No zero-garbage or zero-ancilla claim is made for a future circuit. The paper
describes MBUC for temporary error symbols and field products, but every
application must satisfy its preconditions and phase-correction obligations.

## 8. Uncomputation requirements

The paper-supported high-level cleanup sequence is:

1. Compute the key-equation/EEA state from the syndrome, retaining the data
   needed for symbol recovery and its inverse.
2. For each of the `m` positions, use the inverse-location test and
   `Omega`/`sigma'` data to recover the temporary error symbol.
3. Apply the phase contribution selected by the corresponding slice of
   classical record `c`.
4. Clear the temporary symbol workspace before advancing to the next
   position. If MBUC is used, preserve the measurement outcome and compensate
   its phase exactly; otherwise demonstrate an inverse computation.
5. Uncompute the EEA state, restore the syndrome, and return all auxiliary
   registers to zero.

The phase must survive cleanup; restoring data registers alone is not enough.
The proof obligation is that each promised computational-basis input
`(s,0_W,c)` has final syndrome `s`, final workspace zero, and phase exactly
`(-1)^(c·bin(e(s)))`. Linearity then establishes the corresponding action on
superpositions over the promised domain, provided the actual circuit model
and all measurement branches satisfy the required phase semantics.

Paper §III.2.1–III.2.2 supplies the high-level sequence and endpoint. It does
not make the classical P006 function reversible and does not provide the
missing repository’s full circuit artifact or verifier behavior. Any new
implementation must separately prove local register-level inverses,
measurement-branch correction, and complete workspace restoration.

## 9. Correctness and verification obligations

### Testable with current classical code and independent oracles

- Field multiplication, inverse on nonzero elements, polynomial evaluation
  and division against independent mathematical reference functions.
- Syndrome equation and mapping between positions/magnitudes and all 70
  syndrome symbols.
- Classical locator, evaluator, root positions, Forney magnitudes, and
  exact recovery on selected vectors through weight 35.
- Classical decoder determinism, strict input validation, and explicit
  no-solution handling for selected inputs.

These tests establish only classical mathematical behavior; they do not
establish a reversible transformation.

### Requires a reversible circuit implementation

- Every primitive and composite state update is a valid permutation or a
  defined measurement-assisted operation on the full declared circuit state.
- Input syndrome is preserved on the promised domain.
- The final phase is exactly the required parity phase.
- The output workspace and all designated ancillas are zero and unentangled
  on promised inputs.
- Every measurement branch has a correct phase fixup and declared classical
  control lifecycle.
- EEA intermediate transformations have valid inverses and cleanup.
- A basis-state simulator compares output data and phase with an independent
  classical reference, while a superposition-level argument follows from
  the model’s allowed structure.
- Off-promise behavior is total for the constructed circuit, even though its
  benchmark acceptance semantics are not stated in Eq. (38).

### Requires official verifier and artifacts

- Exact circuit parser, register names/order, field-bit mapping, record
  binding, instruction allowlist, result schema, validation/rejection
  behavior, statistical computation, and scoring/resource accounting.
- Acceptance against official sample circuits/fixtures and expected outputs.
- Official benchmark result and compliance claims.

P003/P004 report these executable materials unavailable in the inspected
refs. No verifier invocation or schema is inferred here.

## 10. Resource-accounting contract

Measure resources only for a named, complete circuit artifact and state
whether counts include phase handling, measurement-based cleanup, inverse
EEA, reset/measurement instructions, classical controls, and wrapper logic.
Report raw tool/version and circuit digest when those exist.

| Metric | Future measurement boundary | Evidence/status |
|---|---|---|
| Logical qubits / circuit width `Q` | Peak simultaneously allocated quantum wires, including 840 syndrome qubits and all workspace; report persistent and peak temporary counts separately | Paper Eq. (43) defines `Q` as total qubits, syndrome plus workspace. Exact official parser confirmation remains unavailable |
| Ancilla count and peak workspace | Maximum live scratch qubits; include inversion scaffolding and temporary symbol/evaluation state; distinguish allocated capacity from peak live wires | Required for accounting; no candidate count is established |
| Garbage/cleanup overhead | Count the full cleanup circuit and any MBUC instructions, feed-forward, and phase correction needed to return to the specified result | Paper includes workspace cleanup in its single-run Toffoli count `T`; exact official executable counting remains unverified |
| Gate counts | Counts by actual supported gate/instruction type, including compute and uncompute | Collect from final serialized circuit and report exact counting rules; no local circuit exists |
| Toffoli count `T` | Single-run count including cleanup under the paper’s Eq. (43) definition | Paper score uses `Q^2 T`; P002 records repository-summary wording conflicts, so verifier accounting still requires source confirmation |
| Gate depth / circuit depth | Critical-path depth under a specified scheduler and instruction model; report whether measurement/feed-forward latency is included | Not established as the paper’s DQI score input or official requirement; report only as separately measured metric |
| Two-qubit gates | Count according to explicit gate decomposition/instruction categories | No DQI executable allowlist or official counting semantics available |
| T-count / T-depth | Count only after a gate decomposition and fault-tolerant cost model are specified; distinguish exact from approximate synthesis | Not established by the DQI paper score; no values inferred |
| Simulator observations | Runtime, memory, tested shots, failure cases and phase behavior for a particular simulator/version | Diagnostic observation only; not a resource count or official score |
| Official benchmark measurement | Verifier-generated Q/T/score and statistical bound for the authorized full workload | BLOCKED: verifier/artifacts absent and baseline remains separately gated in P003/P004 |

The paper’s §III.2.2 reports a reference implementation resource result
(including its cleanup); these are literature values for that reference, not
measurements of this repository or a new candidate. They are not used as
estimated or achieved resources for P008.

### Evidence classes

- **Mathematical lower bound:** theorem-based minimum or bound, with proof
  and scope stated. None is claimed for implementation resources here.
- **Symbolic estimate:** algebraic expression and assumptions, not measured.
- **Measured circuit resources:** instrumented count from a specific complete
  circuit artifact and tool version.
- **Simulator observation:** behavior/runtime on simulator inputs; not a
  hardware or official resource result.
- **Official benchmark measurement:** verifier result under its exact
  official version, schema, seeds, and approved workload.

These classes must not be conflated.

## 11. Source-to-requirement traceability

| Source | Established statement | P002 / P005–P007 connection | Reversible contract requirement | Evidence status / remaining uncertainty |
|---|---|---|---|---|
| Paper §III.2.1, Eq. (36) | On weight-`<=ell` errors, the error register can be erased while syndrome labels the state | P002 §§2, 5 records syndrome preservation and clean workspace; P006 is classical only; P007 §16 explicitly excludes reversibility | Keep syndrome, erase `e`, prove uniqueness on domain and zero all other workspace | **PRIMARY SOURCE VERIFIED** on promised subspace; full-register extension unresolved |
| Paper §III.2.1, Eqs. (37)–(38) | Measurement record induces a known parity phase; circuit applies correcting phase while preserving `s` and cleaning `W` | P002 output/phase contract; P005–P007 do not implement it | Correct phase for each promised `(s,c)` and preserve syndrome | Mathematical phase contract verified; register/wire serialization and verifier input mapping unavailable |
| Paper §III.2.2, Eq. (39) | `(m,n,b,r)=(4095,70,12,2016)`, field modulus/basis and syndrome equation | P005 implements field and logical syndrome; P007 independently checks classical mapping | Quantum arithmetic must implement same abstract field operations | **PRIMARY SOURCE VERIFIED** mathematically; official executable bit order unverified |
| Paper §III.2.2, Eq. (40) | EEA key equation modulo `z^(2ell)`, stop below degree `ell`, locator factors | P006 `_key_equation`; P007 independently checks key equation and root convention | Reversible EEA must expose `sigma`, `Omega` and retain enough history to reverse | Mathematical algorithm specified; local circuit transitions not supplied |
| Paper §III.2.2, reference prose | Synchronized EEA shares remainder/Bézout storage, stores temporary quotients, uses degree pointers; EEA is uncomputed after phase | P006 is ordinary classical EEA; P007 guards termination but not reversibility | Define reversible register state, quotient/history, pointer updates, inverse and cleanup | **PARTIALLY SPECIFIED**: architecture described, complete source circuit unavailable |
| Paper §III.2.2, reference prose | Chien search uses inverse evaluation points; Forney uses `Omega` and `sigma'`; symbols are recovered position by position | P006 implements classical stages; P007 independent tests | Preserve needed polynomial state through each position, apply phase, clear symbol/evaluation scratch | Mathematical roles specified; complete gate decomposition and official formula behavior unverified |
| Paper §III.2.2, arithmetic discussion | Addition, squaring, fixed `alpha` powers are linear/CNOT; register multiplication and Itoh–Tsujii inverse described | P005 field operations are classical; no quantum framework/source in repo | Use reversible maps preserving operands or prove in-place permutation; explicitly handle inverse domain and cleanup | **PARTIALLY SPECIFIED**: paper’s reference method exists, no local reusable circuit or full primitive contract |
| Paper §III.2.2, resource paragraph and Eq. (43) | `Q` includes syndrome/workspace; `T` is single-run and includes cleanup; score uses `Q^2 T` with repetition factor | P002 §§8–9 records repository summary conflicts; P003/P004 say scorer absent | Count complete circuit including cleanup and report tool/artifact | Paper-level definition verified; official scorer implementation and other metric semantics unavailable |
| P002 §§3–9 | Repository-level register, verifier, score and authorization gaps | P003/P004 retain verifier/fixture absence | Do not infer wire schema, allowlist, result schema, or authorization from summary | **SECONDARY SUMMARY**; conflicting/incomplete items remain unresolved |
| P005 §§4–8 | Classical field and syndrome implementation, no quantum circuit | Source/test audit confirms classical-only functions | Treat as mathematical oracle/component, never as reversible proof | **WORKTREE IMPLEMENTATION VERIFIED**; not quantum evidence |
| P006 §§7–17 | Classical EEA/Chien/Forney and syndrome recheck; no quantum circuit or verifier | P007 audits mathematical convention and failure behavior | Differentially validate any future circuit against a classical reference | **WORKTREE IMPLEMENTATION VERIFIED**; no reversible state tracking |
| P007 §§5–10, 14–18 | Independent classical tests pass; no reversibility, verifier, or benchmark claim | P008 uses these findings as classical evidence only | Circuit correctness and cleanup must be proven separately | **AUDIT REPORT**; does not establish circuit behavior |
| P003/P004 artifact inventories | Official verifier/scorer, sample/reference circuit and fixtures unavailable in inspected refs | P002’s secondary API claims remain unverified | Obtain primary executable artifacts before verifier integration or official claims | **BLOCKED** pending authorized immutable sources |

## 12. Implementation-readiness matrix

Status definitions: **SPECIFIED** means the relevant source-supported
mathematical contract is sufficiently explicit for that limited item;
**PARTIALLY SPECIFIED** means architectural or mathematical evidence exists
but important implementation requirements remain; **UNRESOLVED** means
required behavior is not established; **BLOCKED** means a necessary source or
artifact is unavailable.

| Component / activity | Status | Basis and gate |
|---|---|---|
| Logical input and output phase relation on promised domain | **SPECIFIED** | Paper Eq. (38); does not specify verifier serialization or off-promise behavior |
| Valid error domain and uniqueness | **SPECIFIED** | Paper §III.2.1 and §III.2.2: `wt(e)<=35`, `2ell<=n`, unique syndrome |
| Field and syndrome mathematics | **SPECIFIED** | Paper Eq. (39); classical implementation exists, but circuit bit layout does not |
| Reversible finite-field primitive implementation | **PARTIALLY SPECIFIED** | Paper identifies linear operations, multiplication and inversion approach; zero behavior, full register contracts, local source/decomposition and cleanup remain |
| Reversible polynomial primitive implementation | **PARTIALLY SPECIFIED** | Coefficient math defined; reversible normalization, degree/pointer encoding, quotient preservation and inverse transitions unresolved |
| Reversible EEA implementation | **PARTIALLY SPECIFIED** | Synchronized EEA architecture, quotient storage, pointer scheme, outputs and cleanup are described; no local complete gate-level state transition artifact |
| Chien/Forney reversible per-symbol processing | **PARTIALLY SPECIFIED** | Mathematical sequence established; complete reversible computation, denominator domain, symbol scratch and phase/wire mapping are not |
| Complete reversible decoder for research-level logical contract | **PARTIALLY SPECIFIED** | End-to-end paper architecture exists; exact total extension and a local circuit/proof are missing |
| Official verifier integration | **BLOCKED** | P003/P004 report actual verifier, schema and fixtures unavailable; summaries do not substitute |
| Official resource scoring | **BLOCKED** | Paper gives score-level definitions, but executable scorer/counting implementation is unavailable |
| Benchmark execution | **BLOCKED / separately gated** | Official artifacts unavailable; P004 records full baseline PENDING and diagnostics NOT AUTHORIZED. This task does not authorize either |

The repository is **not ready for a verifier-compatible reversible
implementation review**. A separate bounded research circuit could only be
proposed after its total operation outside the promised domain, gate model,
and cleanup proof obligations are made explicit; it must not be represented
as official-compatible.

### Dependency-ordered prerequisites

1. Obtain immutable, authorized official verifier/scorer, reference/sample
   circuit, fixtures, schemas, and expected outputs; verify provenance and
   hashes.
2. Resolve field-symbol, syndrome-register, classical-record, bit/wire order,
   and valid-input serialization against those artifacts.
3. Write a fixed-width reversible register/state-transition specification
   for field operations, degree pointers, quotient storage, and all EEA steps,
   including total off-promise behavior.
4. Select and document a quantum circuit framework and allowed gate model
   based on project requirements; the current repository has no such
   dependency or convention.
5. Prove reversible correctness of primitives and each EEA update, including
   input retention, phase, inverse, and ancilla lifecycle.
6. Implement a small research circuit only under a separate phase prompt;
   compare its basis-state data/phase with independent classical oracles and
   prove workspace cleanup on its declared domain.
7. Integrate and validate against official fixtures only when available.
8. Keep diagnostic, baseline, and optimization authorization gates separate;
   run no verifier or benchmark until its exact approval and prerequisites
   are recorded.

## 13. Unresolved assumptions and blockers

1. **Executable I/O mapping:** Exact bit order, wire ordering, field
   serialization, register names, and classical `c` binding are not supplied
   by an inspected verifier or fixture.
2. **Off-promise semantics:** Eq. (38) is scoped to correctable syndromes.
   The required full-register reversible extension and behavior for
   unsupported syndromes are not stated.
3. **Zero inversion:** P005 classical inverse raises on zero. A circuit cannot
   raise; the full circuit behavior for zero and unpromised `sigma'` inputs
   needs an explicit total definition or a proven guard.
4. **Exact reversible EEA state:** Paper-level synchronized EEA architecture
   is described, but no local gate-level implementation or complete inverse
   trace exists. Quotient/pointer encoding, register overlap, and each
   reversible update need explicit proof.
5. **Measurement-based uncomputation:** Exact measurement outcome storage and
   branch phase correction must be specified per use. DQI input record `c`
   must not be conflated with internal measurement outcomes.
6. **Framework and gate conventions:** No project dependency manifest or
   DQI quantum-framework import was found. Gate-set and serialization
   requirements cannot be inferred from the classical Python modules.
7. **Verifier and resource accounting:** Official verifier, scorer, reference
   circuit, and fixtures remain unavailable per P003/P004. Repository
   summaries are not executable evidence.
8. **Authorization:** P003/P004 report diagnostic execution NOT AUTHORIZED,
   baseline execution PENDING, optimization NOT AUTHORIZED, and independent
   review NOT VERIFIED. P008 does not change those statuses.

## 14. Recommended P009 scope

Recommend **P009 — Reversible Primitive Contract and Small-Domain Proof
Plan**, not a full decoder implementation:

1. First obtain or explicitly record the disposition of missing official
   register/bit serialization and circuit-file requirements. If still
   unavailable, bound P009 to a clearly non-official mathematical model.
2. Specify fixed-width reversible input/output relations for field addition,
   multiplication, squaring, constant multiplication, and inversion,
   including all-input behavior, aliasing rules, and scratch cleanup.
3. Formalize a small polynomial/EEA state transition with explicit old/new
   state and a mechanically checkable inverse before choosing a framework.
4. Prepare an independent basis-state correctness oracle and workspace-zero
   checks for a small test domain. Do not claim these prove the full DQI
   circuit or official compatibility.
5. Do not implement the complete EEA, decoder circuit, verifier adapter,
   optimize resources, or execute diagnostics/benchmarks in P009 unless a
   separate prompt authorizes each and the necessary artifacts are available.

## 15. Execution and integrity report

### Actions performed

- Verified repository root, exact branch and expected HEAD before inspection.
- Inspected P001–P007, the complete current DQI Python package and tests,
  current worktree status, tracked files, dependencies/manifests, and
  quantum-framework references.
- Read the public arXiv v2 HTML DQI sections and equations cited in §2.
- Created only this P008 research document.
- Did not modify P001–P007, DQI source/tests, INVSQRT artifacts, dependency
  files, or any other existing file.
- Did not install dependencies, execute DQI code/tests, run a simulator,
  invoke a verifier, execute a benchmark, or start P009.
- Did not change branches, stage, commit, push, merge, cherry-pick, reset,
  clean, or delete files.

### Preserved baseline hashes

The following P001–P007 report bytes match the initial P008 baseline:

| Report | SHA-256 |
|---|---|
| `docs/research/DQI_P001_DEVELOPMENT_FOUNDATION.md` | `dc44f79bd38e7bd38566fc11e3234b0ece5c8adca52b66ece9823e13634eb0f8` |
| `docs/research/DQI_P002_TECHNICAL_CONTRACT.md` | `48e8772d49425cc50c0694ff7b133a7f58af1f218452a2a6ddece8bcb1eec516` |
| `docs/research/DQI_P003_EVIDENCE_READINESS_REPORT.md` | `0f47d0f4c59cdd040a569e7fc55c7a4127e69147f7a530ef2a16741dc4415163` |
| `docs/research/DQI_P004_AUTHORIZED_VERIFIER_FIXTURE_INTAKE.md` | `5496f8817f6835d2eeaa28a6e9f08f84579588eef1ddaac8d2510f6f96131167` |
| `docs/research/DQI_P005_CORE_IMPLEMENTATION_REPORT.md` | `fa937c40436c41751962b86cbc60bdd99b12024240694648f707f5846a763d97` |
| `docs/research/DQI_P005_EVIDENCE_AUTHORIZATION_GAP_CLOSURE_PLAN.md` | `a91d056176782675788c920c2b8e715c28606d538ede4515c911448214c7f4ff` |
| `docs/research/DQI_P006_CLASSICAL_DECODER_IMPLEMENTATION_REPORT.md` | `9d179e6328fa889a83a76fae7d21e8d051e0d96948a80297fd588939c5c42084` |
| `docs/research/DQI_P007_INDEPENDENT_CORRECTNESS_AUDIT.md` | `8e2fd36e3896a1f6482cb8a720ea76df6460422c4238a44a8a09215787c8d6a7` |

All 48 initial untracked paths remain present; this report adds one new
untracked file. No unrelated file was modified or deleted.

### Validation

- Strict UTF-8 decoding: **PASS**.
- Final newline: **PASS**.
- Trailing whitespace check: **PASS**.
- `git diff --check`: **PASS**.
- Branch and HEAD unchanged: **PASS**.
- P001–P007 preservation hashes: **PASS**.
- Existing untracked work preserved; no unrelated modifications/deletions:
  **PASS**.
- Final worktree: P001–P008 and the prior DQI/INVSQRT assets remain
  untracked; no staged or tracked changes were introduced.

## Final status

**PARTIALLY SPECIFIED.** The primary paper establishes the promised-domain
phase operation, uniqueness, decoder stages, synchronized EEA architecture,
high-level workspace reuse, phase correction, and cleanup endpoint. It does
not provide this repository’s official executable interface, and no
repository circuit proves the complete reversible state transitions and
workspace cleanup.

P008 is complete as a source-traceable specification and readiness assessment.
No reversible circuit has been implemented. Official verifier compatibility,
benchmark readiness, resource measurements for a local circuit, and
permission to run any benchmark remain unestablished. P008 stops here; P009
has not started.
