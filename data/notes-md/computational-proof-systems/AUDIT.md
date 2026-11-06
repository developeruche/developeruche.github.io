# Audit log: Computational Proof Systems

Corrections made while importing the book from GitBook, page by page. Numbers
were recomputed with a script, and Rust code was checked against
[cryptography-n-zk-research](https://github.com/developeruche/cryptography-n-zk-research)
(`cargo test` on `sum_check`, `circuits`, `pcs`, `gkr`, `succinct_gkr_protocol` and `groth16` passes).

Fixed everywhere: spelling, grammar, GitBook markup, and broken links to the repo after its folders moved.

## Chapter One

### Overview of Computation
- **IsZero circuit was unsound.** `in * out === 0` was missing, so a prover could claim a non-zero value is zero. `inv <== ...` was also invalid (a non-quadratic expression needs `<--`), and the top-level component is now `component main`. Now matches circomlib.
- **IsZero diagram was wrong.** It computed `out = in * (1 - in * inv)`, which is always 0 for an honest witness. Redrawn.
- Said the problem is first an arithmetic circuit and then an algebraic one. They are the same thing.
- Said the book explores AIR and CCS. It doesn't, so they are now listed for completeness only.

### Arithmetic Circuits
- Wires carry field elements, not integers.

### Arithmetic Circuits in Rust
- Said the final layers run "from input to output". After `reverse()` they run from output to input.
- Text described coloured boxes and an octagon that the image doesn't have.
- Added the actual evaluation result. Removed a duplicated snippet.

### Polynomials
- `3x2` should be `3x^2`.
- **QAP check was wrong.** Said `H(x)` must "lie within the span of other polynomials". The check is divisibility by the target polynomial: `L R - O = h t`.
- Said a QAP is three polynomials. There is one per wire; three result from combining them with the witness.
- Said verification checks a polynomial "evaluates to zero at a random point". It checks an identity at a random point.
- Removed "sum-over-subsets", which isn't how multilinear evaluation is done.
- **Nachef-Patarin-Volte paper was misdescribed** as using multilinear polynomials for efficient proofs. It is about knowledge of a solution to multivariate equations (checked against the abstract).
- Zeromorph claims checked against its abstract, and the $2^n$ comparison added.

### R1CS to QAP
- **Coefficient matrix, last row:** `1/2, -3/2, 2` should be `1, -3/2, 1/2`.
- **Dimensions were wrong:** the coefficient matrix is 5x3, not 3x5, and it is multiplied as `w^T C`.
- **The example never finished.** It stopped at `C`. Added `C(x)`, `A(x)`, `B(x)`, `t(x)`, `h(x)` and a failing witness.
- "Single polynomial" corrected to one polynomial identity.
- Added that `out = 21` is a public input, since the constraints alone allow other values.
- A garbled display equation (`=====` in the matrices) was repaired, and `poly_2` simplified.

### Polynomial Multiplication Using FFT
- Said to evaluate at `2n+2m+2` points. The product needs `n+m+1`, rounded up to a power of two.
- Added complexity and the finite-field requirement.

## Chapter Two

### Interactive and Non-Interactive Proofs
- Said NIZKs "usually" need a trusted setup. They need a CRS or a random oracle; Fiat-Shamir has no trusted setup.
- **Said zk-SNARKs require a trusted setup.** Many do, but STARKs don't. Also said pairings; hash-based systems exist too.
- SNARKs and Fiat-Shamir were shown as separate methods. Many SNARKs use Fiat-Shamir.
- Added the caveats on Fiat-Shamir: the statement must be hashed, and not every interactive protocol stays sound.
- 3-coloring: catch probability is "at least" 1/|E|; added that V checks the openings, and that zero knowledge relies on hiding commitments.
- Comparison table had an empty extra column. Removed the "computational cost" row, which depends on the scheme rather than interaction.
- Public verifiability of interactive proofs: explained why not.

## Chapter Three

### Polynomial Commitment Schemes
- Said commitments work "without revealing the polynomial". Binding and evaluation proofs are the core; hiding is a separate property.

### KZG
- **`P(2) = 20` was wrong:** $2x^3 + x + 4$ at 2 is 22.
- **Pairings were misdescribed** as multiplying curve points "in a way that's hard to reverse". Defined properly.
- **The SRS and pairing check mixed the two groups.** Now uses $G_1$ and $G_2$, and includes $\alpha G_2$.
- "Evaluate symbolically" replaced by the real linear combination.
- Said KZG hides the polynomial. Plain KZG isn't hiding.
- A leaked $\alpha$ lets someone forge openings: stated precisely. Added the 1-of-n ceremony property and the lack of post-quantum security.

### Univariate KZG
- Page held only links. Added a checked worked example and a note that `generate_srs` takes `tau` for testing.

### Multilinear KZG
- Said hypercube size is "directly proportional" to the number of variables. It is $2^{\ell}$.
- SRS was described as "all powers of" the Lagrange polynomials. It is their evaluations.
- Summation limits `2l` corrected to $2^{\ell}$, and `r` to `tau`.
- **Witness polynomials are not unique** as a set, as the page claimed. Now "there exist". (For example, adding $(X_2 - z_2)$ to $w_1$ and subtracting $(X_1 - z_1)$ from $w_2$ gives another solution.)
- **Variables were wrong:** $w_i$ doesn't depend on $X_i$ or earlier variables.
- **Example opened at $x = 2$, the same value as $\tau_x$,** so the first proof element dropped out of the check and was never tested. Now opens at $(5, 1)$.
- `2xy + 4x + 3 - 23 = 0` was a false statement. Group notation mixed `+` and exponents, and an unexplained $g_3$ is now $g_T$.
- Rust signature matched to the repo (`point`).

### Batch Univariate KZG
- **Said it does "batch commitment and batch verification".** The repo opens one polynomial at many points. Page now says so, with the protocol and a checked example.

### FRI
- The source page only says "TODO", and `pcs/src/fri/mod.rs` is empty. See "Chapter Three: FRI (new)" below.

## Chapter Four: Sum-Check

- **Round 2 check was wrong.** It compared `f1(0) + f1(1)` with `f2(r1)`. It must be `g1(r1) = g2(0) + g2(1)`. The wrong version only "passed" because both sides happen to be 12. The right values are 21.
- **Final check was wrong:** `S2(6)` should be `g3(3)`, and the values 22 = 22 are now shown.
- **The diagram had the same wrong checks.** Replaced by a table.
- **Univariate sum-check section was wrong.** The `p'(X) = sum p(x)/(X-r)` construction isn't a real protocol. Replaced with the Aurora protocol, plus a checked example over F17.
- Degree checks were missing from the protocol. Added, with the soundness argument and bound.
- LFKN introduced sum-check for interactive proofs, not PCPs.
- Said the implementation is interactive; it is non-interactive.
- "Only the last round needs the polynomial" is true of the verifier, not the prover.
- Notation unified (`f`, `g_j`, `n`). Sets now render as `{0,1}`.
- `ff` crate corrected to `ark_ff`. Rust snippets replaced with the current repo code, since the repo has moved on.
- Verifier step list had the check reversed.

### Issue in the repo code, not fixed

`Verifier::verify` takes the polynomial and sum from the proof and doesn't absorb them into the transcript. A test proof claiming a false sum (999) was accepted. See "Limitations" on the page. The repo itself was not changed.

## Chapter Five: GKR

### The GKR Protocol
- Title typo `GRK`. Page held only a link and one sentence. Added the layer equation that the chapter depends on.

### Succinct GKR
- **The main claim was wrong.** It said KZG shrinks the proof from $O(d)$ to $O(\log d)$. The repo's proof still holds sum-check data and two evaluations for every layer, so it stays $O(d \log S)$. KZG only removes the input from the verifier's work, $O(n)$ to $O(\log n)$. Added a comparison table.
- **Openings aren't constant size.** A multilinear KZG opening has one group element per variable, not "typically a single group element".
- **"Instead of sending evaluations, store them"** was false: the code sends them for every layer.
- **Step 3 committed to the wrong polynomial.** $w_{n-1}$ is opened against $C_{in}$, so it is the input polynomial.
- **Example was wrong:** $w_1(r_b) = 5$ and $w_1(r_c) = 12$ are gate values, not evaluations at random points. Rewritten with checked numbers, and the 3-element input padded to a power of two.
- Added the verifier's remaining wiring cost, and that this construction isn't zero knowledge.
- "A breach compromises security" narrowed to soundness.

### Issue in the repo code, not fixed

For every layer after the first, `verify` in both `arks/snarks/succinct_gkr_protocol` and `iops/gkr` skips the sum-check's final check against `add`, `mul`, `w_b`, `w_c`. A forged succinct GKR proof claiming output 999 for a circuit whose true output is 100 was accepted (tested in a scratch copy). The forgery was only tested against the succinct verifier; `iops/gkr` has the same loop by inspection.

Also in `iops/gkr/src/utils.rs:130`, `(false, F::ZERO);` lacks a `return`, so the layer-one check of `sum` against the claim has no effect. And each sum-check uses a fresh transcript.

## Chapter Six: Groth16

- **Page stopped mid-way.** It ended partway through the linear combinations, with no proving or verifying. Added both, and the QAP step it skipped. Checked by running the setup, prover and verifier equations with random values over a prime field.
- **Index error:** the proving key listed $L_p \ldots L_{m-1}$. The $L_i$ are per variable, so it runs to $L_{n-1}$. The same slip is in the source notes it followed.
- **Degree error:** $2n - 1$ corrected to the real bound on $H Z_x$ ($2m - 2$), which is now described in words.
- `G_3` corrected to $\mathbb{G}_T$. Said the setup includes $\mathbb{G}_T$ elements; the listed keys don't.
- R1CS notation corrected: matrices are $m \times n$; vectors are in $\mathbb{F}^n$, not "$\mathbb{F}^{3n}$" per vector.
- Pairing was named but never defined. Defined. Linear combination formula mixed product and additive notation. `C_i(X).G_1` corrected to $\tau$.
- Listed logical gates under circuit structure, though Groth16 needs arithmetic circuits.
- Added the discriminant's characteristic condition, toxic waste, the role of $\gamma$ and $\delta$, proof size and malleability.
- **Rewritten in my own words:** the setup section was close to verbatim from Remco Bloemen's notes. It is still credited.

## Chapter Seven: PLONK

The GitBook chapter only linked to a separate book, [developeruche.gitbook.io/plonk](https://developeruche.gitbook.io/plonk), so its 5 pages are imported here. All prover and verifier formulas were checked by running a full PLONK round trip over a prime field, with the commitments checked in the exponent: an honest trace and one with a public input both pass, and a trace with broken wiring is rejected. `cargo test -p plonk_protocol` passes.

### Introduction and Setup
- **The SRS omitted $\mathbb{G}_2$.** It needs $(G_2, \tau G_2)$ for the pairing check. Added, with the $n + 5$ degree requirement.
- Said a commitment keeps coefficients "hidden". Plain KZG isn't hiding.
- "Linear interactive oracle protocol" corrected to interactive oracle proof, and the compile-to-SNARK step added.

### Plonkish Arithmetization
- **Selector error:** $q_L = (0, 1, 1)$ should be $(0, 1, 0)$. With the old value, gate 3 gives 6, not 0. The $Q$ matrix had the same error.
- **Padding row mismatch:** the $Q$ table had $Q_O = -1$ where the vector had 0.
- **Bad trace example was the good trace.** The text said a trace satisfied the gates but was invalid, then showed the valid one. Now shows a real invalid trace (7, 9, 63).
- **Public values:** $q_C$ must be the negative of the value, or the gate says $a = -k$.
- **Garbled identity:** `= z_{H^t}` restored to $Z_H \cdot t$, and "degree at most $N$" corrected to less than $N$.
- **False statement in equality of sets:** "equal if $f(h) = g(h)$ for all $h$" would require the same order. Removed.
- **Witness in preprocessed input:** `CommonPreprocessedInput` listed $a, b, c$, which change per execution.
- **Slides removed.** Four slide images had no credit, and one showed the running product incorrectly (a single product, not a sum of cumulative products). Replaced with text and the same numbers.
- Sets corrected to multisets, `v` to `r`, and the column header `0` to `O`. Connected $\eta$ to $k_1$, $k_2$, which the prover uses but the page never explained.

### The PLONK Prover
- **$z(X)$:** the product's upper limit was `Q`; it is $i$. Blinding factors `b` and `r` were mixed.
- **Point and polynomial shared a name.** The evaluation point `z` is now $\zeta$, as the polynomial is $z(X)$.
- **$r(X)$:** the signs were lost, shown as `•`. Restored.
- **Split degrees:** said all parts have degree below $n$; $t'_{hi}$ goes up to $n + 5$.
- Round four's purpose was described as computational cheapness. It is Schwartz-Zippel.
- **$\text{PI}$ sign:** with $q_L = 1$, $\text{PI}(X) = -\sum w_i L_i(X)$. The round trip fails with the positive sign, which is what the source had.

### The PLONK Verifier
- **Pairing check was wrong:** $u\bar{z}_\omega [W_{z\omega}]_1$ should be $u\zeta\omega [W_{\zeta\omega}]_1$. The round trip rejects honest proofs with the old version.
- **$L_1$ formula typo:** $\omega(z^{n-1})$ should be $\omega(\zeta^n - 1)$.
- **$[D]_1$ was left as "(other terms)".** Now written out in full.
- Said verification is independent of circuit size; the public input part isn't.

## Chapter Eight: PLONK Extensions

### TurboPLONK
- "Copy Constraints as Memory" was an empty heading. Filled in from the proposal.
- "Dynamic selectors" are fixed by the circuit. Heading corrected. Added the state model, $w$, and a Fibonacci transition example.

### Lookup Arguments and PlonKup
- **Said lookups hide the table.** Tables are often public. What's hidden is the looked-up values.
- The page was titled PLONKUP without mentioning it. Added, with a link.

### Plookup
- **Wrong citation.** It cited Bootle et al. Eurocrypt 2016; the abstract refers to their Asiacrypt 2018 work.
- **$Z$ formula:** $\prod_{j \leq i}(\gamma + f_j)$ should be $j < i$. Checked numerically against the recurrence.
- **$\beta, \gamma$ give soundness,** not "zero-knowledge properties".
- Sorting must follow the order of $t$, which wasn't stated. Added the idea and a checked example.
- Removed "$\mathfrak{d}(\mathscr{P}) = 5n + 4$", because the paper couldn't be opened to verify it.

### Halo2 Lookup Protocol
- **Page was a pasted AI chat.** It included "Your Concern" and "What do you think?". Rewritten as a note.
- **The claimed flaw was wrong.** It said a prover could pass with $A = [1,2,4,4]$, $S = [3,4,4,4]$, $A' = S' = [1,2,4,4]$. Step 4 catches this, as $S'$ isn't a permutation of $S$: the product ends at $21/10$, not 1. Now a section showing that.
- **Examples used invalid data,** where $A$ wasn't a subset of $S$. The computed $Z$ was for that case. New example, with $Z$ returning to 1.
- Explained why padding is safe, why $L_0(A' - S')$ is needed, and the blinding rows. "Step 2" was the first step.

### HyperPlonk
- **Wrong authors.** "The xAI team" is Chen, Bünz, Boneh and Zhang.
- $B_\mu := \{0,1\}\mu$ corrected. Added high-degree gates, the paper's second main result.
- **Page stopped mid-way,** ending at a literal `...` before reaching HyperPlonk itself. Added a section covering how each part is replaced, based on the paper's abstract and the standard construction. It should be read as an overview.

## Miscellaneous

Both were mostly photos of handwritten pages. They are now typed out, so the text and math can be searched and read on a phone.

### Sumcheck 201
All formulas were run against random polynomials: both algorithms produce the same round polynomials, and Algorithm 1 ends at the right evaluation.

- **Index slips in the handwriting:** the $k$ to $f$ table read $f_1, f_2, f_3, f_4$ where it should read $f_0 \ldots f_3$, and $r_2^{(1)}$ used $f_3$ for $f_5$.
- Round 2 summed over a variable that was also held fixed on the left side.
- **Array size:** the even and odd elements are in the $2^{n-p+1}$ array, not $2^{n-p}$.
- Diagram axes were labelled $x_0, x_1$, while the formulas use $x_1, x_2$. Replaced by a table.
- Ingonyama was misspelled, and added a link to the paper. Added how products of polynomials change the round degree, which is the paper's subject but wasn't in the example.
- **The benchmark claim changed.** The note said Algorithm 1 is 30x faster. Running your `super-sumcheck` benchmark today gave about 270 µs against 775 ms, nearer 2,800x. The page now quotes these, with a warning that it reflects this implementation. The note was also cut off mid-sentence.

### Keccak
- **The one-way explanation was wrong.** It said Keccak-$f$'s steps are "irreversible" and contribute to "non-invertibility". Keccak-$f$ is a permutation, and each step can be inverted. One-wayness comes from the hidden capacity. Rewritten.
- **"Information is lost, making inversion impossible"** is false reasoning. Losing information doesn't make a function one-way, and inversion is infeasible rather than impossible.
- **Pi was called non-linear.** Only chi is.
- Iota's purpose is breaking symmetry, rather than preventing "cycles and fixed points".
- Titled "Keccak (SHA-3)", but they differ in padding. Added this, with hash values checked against a reimplementation that matches Python's SHA3-256.
- $r$ absorbs per block, not "per round". Typed out the photos of the formula and sponge (redrawn).

## Chapter Three: FRI (new)

Your page only said "TODO", so **this page is new writing, at your request**, rather than an import. Every number in the example, including both cheating cases, was computed by script. The folding rules are standard. The query counts are approximations, so please read them as a guide.

### Could not verify

Medium links return 403 to automated requests, so they were not opened:
`@bhaskark2` (Polynomials), `@yujiangtham` (Overview), `web3studio` (Arithmetic Circuits).

Also unreachable: `research.metastate.dev/plonk-by-hand-part-1` (Plonkish Arithmetization) failed to connect. The plookup paper's PDF is behind a browser check, so only its abstract was read.
