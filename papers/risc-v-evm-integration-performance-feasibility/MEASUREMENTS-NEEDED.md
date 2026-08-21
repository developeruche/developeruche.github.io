# Measurements needed — RISC-V EVM paper

Pass 1 classification of every empirical claim in the draft. Produced by
grepping the source for `benchmark|performance|efficien|plausible|overhead|
faster|slower|speed|latency|throughput|cost|improv|optimi[sz]|\d+×|measur|
evaluat|result` over prose (code fences excluded), then checking each hit
against the repository.

**Headline: the draft contains exactly one quantitative claim in prose — "44
environment calls" — and it is correct.** There are no timings, no comparative
numbers, and no `N×` claims anywhere in the document. The paper is a
design-and-feasibility report, and Pass 1 rewrites the abstract to say so.

---

## A. Backed — a number exists and verifies

| # | Claim | Where | Verification | Action |
|---|-------|-------|--------------|--------|
| A1 | "44 environment calls were implemented" | §5 bullet 3 | **Verified.** `RiscvEVMECalls` in `riscv_evm_core/src/e_constants.rs` has exactly 44 variants. | Keep. Move into the ecall table so the number sits in a table, not only prose. |
| A2 | Per-opcode register consumption | §5 bullet 4 (prose only) | **Verified** from the `*_REGISTER` constants in `e_constants.rs`: `LOG0`=2, `LOG1`=10, `SSTORE`=16 in, `SLOAD`=8 in/8 out, `CALL`=26 in, `CREATE`=10 in/5 out, `CREATE2`=18 in/5 out (highest register x23). `ECALL_CODE_REG`=x31. | **Promote to the Pass 2 register-pressure table.** This is the paper's only real result. |
| A3 | Certain opcodes are unimplementable in the register-only mapping | §5 bullet 4 | **Partly verified.** `LOG2`, `LOG3`, `LOG4`, `DELEGATECALL`, `STATICCALL`, `CALLCODE` have **zero** register constants — they exist as enum variants but have no calling convention. | Keep as an implementation-status fact. **But see Q1 below: the "impossible" framing does not hold for all of them.** |

### Register budget (derived, not measured)

RV32IM has x0–x31. x0 is hardwired zero and x31 is `ECALL_CODE_REG`, leaving
**30 registers** for ecall arguments. The encoding is fixed by two verified
data points — `LOG0`=2 (offset, size) and `LOG1`=10 (offset, size, one 256-bit
topic) — so a 256-bit topic costs 8 registers:

| Opcode | Registers required | Available | Verdict |
|---|---|---|---|
| LOG0 | 2 | 30 | implemented |
| LOG1 | 10 | 30 | implemented |
| LOG2 | 2 + 16 = 18 | 30 | **fits**, not implemented |
| LOG3 | 2 + 24 = 26 | 30 | **fits**, not implemented |
| LOG4 | 2 + 32 = 34 | 30 | **exceeds budget** |

This is arithmetic over a verified encoding, not a measurement. It needs the
author's confirmation before it goes in the paper (Q1).

---

## B. Measurable now — the draft can produce these; no value invented

### M1 — Static instruction count per mapped EVM opcode
- **Why:** substantiates (or kills) "simple arithmetic, logic, and stack operations mapped efficiently".
- **Workload:** each mapped EVM opcode, assembled in isolation with `riscv-assembler`.
- **Varied:** opcode.
- **Reported:** RV32IM instructions emitted per opcode; median and max across the mapped set.
- **Machine:** none needed — static count, deterministic.
- **Blocked by:** nothing.

### M2 — Runtime bytecode size, RISC-V vs EVM
- **Why:** gives the paper a real comparative number without a timing harness.
- **Workload:** the counter contract, already written in RV32IM assembly, versus a semantically equivalent Solidity counter compiled with `solc`.
- **Varied:** contract (start with the counter; add ERC-20 if one exists).
- **Reported:** runtime bytecode size in bytes for each, and the ratio.
- **Machine:** none needed — static.
- **Caveat to state in the paper:** the RISC-V contract is hand-written assembly and the Solidity one is compiler-generated, so this measures the encoding, not programmer output. Say so.

### M3 — Interpreter throughput on the counter contract
- **Why:** replaces "plausible execution times", which is currently backed by nothing.
- **Workload:** deploy the counter, then N × `increment()` through `process_ecall`/`Vm`.
- **Varied:** N ∈ {1, 10², 10³, 10⁴, 10⁵}.
- **Reported:** wall-clock per call (median and p95 over ≥10 runs), RV32IM instructions retired per call, ns/instruction.
- **Machine:** must be stated — CPU model, core count, clock, RAM, OS, `rustc` version, release profile with `lto` setting.
- **Blocked by:** nothing. This is the cheapest real number available.
- **Note:** this is a *self*-measurement only. It supports no claim about the EVM until M4 lands.

### M4 — RISC-V EVM vs REVM on identical contract logic
- **Why:** the only experiment that supports any "parity / overhead / faster / slower" sentence. Every such sentence in the draft is currently unbacked and is deleted in Pass 1.
- **Workload:** same counter semantics executed through (a) stock REVM interpreter on solc bytecode and (b) the RISC-V interpreter on assembled RV32IM, both inside the same REVM `Context`/`Database`.
- **Varied:** call count, as M3.
- **Reported:** wall-clock per call for both, ratio, with the machine spec.
- **BLOCKED:** Phase Two is incomplete — the draft says "This phase is to be completed on the final research result." Until the REVM `Interpreter` trait implementation is finished this cannot run.

### M5 — Gas-cost comparison
- **BLOCKED:** gas metering is not implemented (listed as future work item 1). No economic-cost claim is possible until it is.

---

## C. Unbacked — deleted or restated in Pass 1

| # | Text | Where | Disposition |
|---|------|-------|-------------|
| U1 | "Through experimental implementation and benchmarking, we evaluate…" | Abstract | **Deleted.** No benchmarking exists. This is the defect that makes the paper read as generated. |
| U2 | "…including multi-language smart contract development, execution efficiency, and architectural compatibility" | Abstract | **Deleted** "execution efficiency" — never evaluated. |
| U3 | "provides empirical insights into the future architectural directions" | Abstract | **Deleted.** No empirics. |
| U4 | "What are the performance implications of this architectural shift?" (RQ2) | §1 | **Deleted.** Never answered. (Pass 2 removes the whole RQ list.) |
| U5 | "showing plausible execution times within the interpreter framework" | §5 | **Deleted.** No timing was taken. Superseded by M3. |
| U6 | "The overhead observed, particularly for complex opcodes…" | §6.1 | **Deleted.** Nothing was observed; no measurement exists. The word "observed" is false. |
| U7 | "may not yield significant performance gains without substantial optimization" | §6.1 | **Deleted.** Speculation with performance content. |
| U8 | "can lead to architectural friction and potential performance overhead" (Option A) | §6.3 | Restated as a design observation; performance content removed. |
| U9 | "While potentially much more performant and cleaner architecturally" (Option B) | §6.3 | Restated; performance content removed. |
| U10 | "suggesting potential performance overheads in a direct emulation approach" | §7 | **Deleted.** |
| U11 | "maintaining EVM compatibility with potential inherent inefficiencies" | §7 | **Deleted.** |
| U12 | "*Computational results will be available in the final draft.*" | §5 | **Deleted.** Replaced by an explicit scope statement in the abstract and §1. |

---

## Open questions for the author

**Q1 — the "impossible" claim.** §5 says `LOG3` and `LOG4` are impossible with
registers as temporary storage. By the verified encoding, `LOG3` needs 26
registers against 30 available — exactly what `CALL` already uses successfully.
Only `LOG4` (34) exceeds the budget. `LOG2` (18) and `LOG3` (26) both fit and
are simply unimplemented. Is the intended claim (a) LOG4 alone is impossible
and LOG2/LOG3 are merely unimplemented, or (b) there is an additional
constraint — scratch/temporary registers reserved by the handler — that makes
26 argument registers unusable in practice? If (b), what is the reserved set?
This changes the table and the abstract.

**Q2 — DELEGATECALL, STATICCALL, CALLCODE.** These have no register constants.
I can state that as fact, but to give a *required* register count I need the
decomposition of `CALL`'s 26 inputs (gas / address / value / argsOffset /
argsSize / retOffset / retSize). I can read it out of the ecall handler in
Pass 2, or you can tell me. I will not guess it.

**Q3 — M2 (bytecode size).** Cheap, static, and would give the paper its first
comparative number. Worth running before the next draft?
