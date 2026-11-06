TurboPLONK is an evolution of PLONK that interprets a circuit as a sequence of states, with transitions between them and copy constraints. This model keeps the benefits of zero-knowledge proofs based on polynomial commitment schemes, but allows more concise and specialized representations, resulting in better performance for constraint-heavy tasks such as bitwise operations.

See TurboPLONK as "PLONK with superpowers". It lets you define custom gates, and inject constants via selectors, which compresses operations like elliptic curve arithmetic into fewer constraints, making circuits smaller and proofs faster. The [TurboPLONK proposal](https://docs.zkproof.org/pages/standards/accepted-workshop3/proposal-turbo_plonk.pdf) by Gabizon and Williamson gives fixed-base scalar multiplication as an example: one gate for every two input bits.

This works because the verifier checks its equation directly on a random opening of the prover's polynomials, rather than "in the exponent" with a pairing, so PLONK isn't tied to R1CS-style constraints.

### Key Components of TurboPLONK

**The state.** A program is a sequence of states in $\mathbb{F}^w$, one per row of the trace, where the state size $w$ is chosen by the program designer. Proof size and prover time grow linearly with $w$, and standard choices are 3 or 4.

**Transition gate.** A transition gate is a polynomial constraint that can involve the values of both the current row and the next row. Vanilla PLONK is the special case that only uses the current row.

For example, a Fibonacci trace with columns $a$ and $b$ needs no copy constraints between rows at all, just two transition constraints:

$$a_{i+1} - b_i = 0 \qquad b_{i+1} - a_i - b_i = 0$$

Starting from $(1, 1)$, the rows are $(1, 1), (1, 2), (2, 3), (3, 5)$. On the polynomial side, the next row is reached with $a(\omega X)$.

**Selectors.** Selectors are preprocessed values fixed by the circuit, one per row. They are no longer limited to choosing between addition and multiplication. They can supply arbitrary precomputed constants (e.g. elliptic curve parameters), or switch a row between different constraint modes.

**Copy constraints as memory.** A copy constraint partitions the cells of the trace into sets that must hold equal values. The proposal notes that this can be thought of as enabling memory access, since a later value in the trace can be forced to equal an earlier one.
