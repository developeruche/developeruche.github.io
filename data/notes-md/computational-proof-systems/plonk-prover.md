At the heart of the PLONK protocol lies one of its most fascinating components: the prover. After the universal trusted setup and the arithmetization of our computation, the prover constructs a zero-knowledge proof that convinces the verifier without revealing any sensitive information.

Unlike Groth16, PLONK's prover works from a universal setup, and it still produces proofs that are compact, while maintaining the critical property of zero knowledge.

The PLONK prover is broken down into rounds. As the protocol progresses, we create polynomials, establish mathematical relationships between them, and seal them with polynomial commitments, all of which form the `Proof`.

Recall `CommonPreprocessedInput` $\{ S_{\sigma_1}, S_{\sigma_2}, S_{\sigma_3}, q_L, q_R, q_O, q_M, q_C \}$, obtained when Plonkish arithmetization was applied to the circuit. The prover also holds the execution trace $T$ for its witness.

This page uses the numbering of the PLONK paper: $H = \{\omega, \omega^2, \ldots, \omega^n\}$, with $L_1(\omega) = 1$. So the running product $z$ starts at $\omega$ rather than at 1.

### Round One

**Objective.** Create the polynomials $a, b, c$ and commit to them. These polynomials express the circuit's execution trace for this witness.

**Procedure**

- Initialize the `Transcript` with values that bind the circuit, such as the commitments in `CommonPreprocessedInput` and the public inputs. This is needed for the protocol's soundness. The transcript could be Merlin, a Fiat-Shamir hash, and so on.
- Generate random field elements for the blinding factors: $b_1, \ldots, b_6$.
- Create the polynomials $a', b', c'$ by interpolating the columns of the $T$ matrix on the domain $H$.
- Create $a, b, c$ by blinding $a', b', c'$ with the factors above. This is what makes the protocol zero knowledge. Learn more about blinding polynomials [here](https://hackmd.io/@0xdeveloperuche/rkSR2_Vz1l).
- Commit to $a, b, c$, and append the commitments to the transcript.

Mathematically:

$$a(X) = (b_1 X + b_2) Z_H(X) + a'(X)$$

$$b(X) = (b_3 X + b_4) Z_H(X) + b'(X)$$

$$c(X) = (b_5 X + b_6) Z_H(X) + c'(X)$$

Because $Z_H$ vanishes on $H$, the blinding doesn't change any value on the domain. The commitments are $[a]_1, [b]_1, [c]_1$.

### Round Two

**Objective.** Enforce consistency across shared wires in the circuit, using a permutation argument.

**Procedure**

- Compute the permutation challenges $\beta$ and $\gamma$ from the transcript.
- Compute $z(X)$, a polynomial encoding the wiring of the circuit.
- Blind $z(X)$, following the same idea as round one.
- Commit to $z(X)$ to obtain $[z]_1$, and append it to the transcript.

Mathematically, with blinding factors $b_7, b_8, b_9 \in \mathbb{F}$, wire values $w_1, \ldots, w_{3n}$ (the columns of $T$, stacked), and $\sigma^*$ the permutation written on the field elements that label the positions:

$$z(X) = (b_7 X^2 + b_8 X + b_9) Z_H(X) + L_1(X) + \sum_{i=1}^{n-1} L_{i+1}(X) \prod_{j=1}^{i} \frac{N_j}{D_j}$$

where each row contributes:

$$N_j = (w_j + \beta \omega^j + \gamma)(w_{n+j} + \beta k_1 \omega^j + \gamma)(w_{2n+j} + \beta k_2 \omega^j + \gamma)$$

$$D_j = (w_j + \beta \sigma^*(j) + \gamma)(w_{n+j} + \beta \sigma^*(n+j) + \gamma)(w_{2n+j} + \beta \sigma^*(2n+j) + \gamma)$$

Each $L_{i+1}$ term sets the value of $z$ at $\omega^{i+1}$ to the running product of the first $i$ rows.

### Round Three

**Objective.** This is the most computationally intense round. The goal is to create a polynomial $t$, the quotient that captures all the constraints of the circuit and the witness, and to commit to it. It isn't as straightforward as the earlier rounds, because the degree of this polynomial is $3n + 5$, where $n$ is the number of gates, while the trusted setup only covers degree $n + 5$. The clever solution is to split the polynomial in 3 before committing.

**Procedure**

- Sample $\alpha$ from the transcript.
- Compute $t(X)$.
- Commit to $t_{lo}(X)$, $t_{mid}(X)$ and $t_{hi}(X)$, and append the commitments to the transcript.

Mathematically, $t(X)$ is the sum of these four parts, where the public input polynomial $\text{PI}(X)$ carries the public values:

$$\frac{a(X) b(X) q_M(X) + a(X) q_L(X) + b(X) q_R(X) + c(X) q_O(X) + \text{PI}(X) + q_C(X)}{Z_H(X)}$$

$$+ \frac{\alpha\, (a(X) + \beta X + \gamma)(b(X) + \beta k_1 X + \gamma)(c(X) + \beta k_2 X + \gamma)\, z(X)}{Z_H(X)}$$

$$- \frac{\alpha\, (a(X) + \beta S_{\sigma_1}(X) + \gamma)(b(X) + \beta S_{\sigma_2}(X) + \gamma)(c(X) + \beta S_{\sigma_3}(X) + \gamma)\, z(X\omega)}{Z_H(X)}$$

$$+ \frac{\alpha^2\, (z(X) - 1) L_1(X)}{Z_H(X)}$$

Each numerator vanishes on $H$ if the witness is correct, so the division is exact. If it isn't correct, no such polynomial $t$ exists. The parts check the gates, the wiring, and the start of the running product.

$\text{PI}(X)$ has a sign that depends on the gate convention. With a public row that uses $q_L = 1$, as in $a - w_i = 0$, it is $\text{PI}(X) = -\sum_i w_i L_i(X)$.

The polynomial $t(X)$ is split into three smaller polynomials:

$$t(X) = t'_{lo}(X) + X^n t'_{mid}(X) + X^{2n} t'_{hi}(X)$$

where $t'_{lo}$ and $t'_{mid}$ have degree less than $n$, and $t'_{hi}$ has degree at most $n + 5$.

Random scalars $b_{10}, b_{11} \in \mathbb{F}$ add randomness to the split polynomials:

$$t_{lo}(X) := t'_{lo}(X) + b_{10} X^n$$

$$t_{mid}(X) := t'_{mid}(X) - b_{10} + b_{11} X^n$$

$$t_{hi}(X) := t'_{hi}(X) - b_{11}$$

These cancel out when the parts are recombined, so that still:

$$t(X) = t_{lo}(X) + X^n t_{mid}(X) + X^{2n} t_{hi}(X)$$

The prover commits to the split polynomials, obtaining $[t_{lo}]_1, [t_{mid}]_1, [t_{hi}]_1$.

### Round Four

**Objective.** By now the prover has committed to all the polynomials. To check the identities without handling whole polynomials, the protocol checks them at one random point, using field elements rather than polynomials. By the Schwartz-Zippel lemma, a false identity is very unlikely to hold there.

**Procedure.** Obtain the evaluation challenge $\zeta$ from the `Transcript`. The prover computes the evaluations of these polynomials at $\zeta$ and at $\zeta\omega$:

1. **Wire polynomials:** $\bar{a} = a(\zeta)$, $\bar{b} = b(\zeta)$, $\bar{c} = c(\zeta)$
2. **Permutation polynomials:** $\bar{s}_{\sigma_1} = S_{\sigma_1}(\zeta)$, $\bar{s}_{\sigma_2} = S_{\sigma_2}(\zeta)$
3. **Shifted running product:** $\bar{z}_\omega = z(\zeta\omega)$

The prover outputs $(\bar{a}, \bar{b}, \bar{c}, \bar{s}_{\sigma_1}, \bar{s}_{\sigma_2}, \bar{z}_\omega)$, and appends them to the transcript.

### Round Five

**Objective.** This is the last stage of proof generation. Here the prover creates 2 opening proof polynomials that combine all the others, using the evaluations from round 4.

**Procedure.** Obtain the opening challenge $v$ from the transcript.

The linearisation polynomial $r(X)$ combines all the constraints. It substitutes known evaluations wherever it can, so that the rest of the polynomial is linear in the committed polynomials:

$$
\begin{aligned}
r(X) = {} & \bar{a}\bar{b}\, q_M(X) + \bar{a}\, q_L(X) + \bar{b}\, q_R(X) + \bar{c}\, q_O(X) + \text{PI}(\zeta) + q_C(X) \\
& + \alpha \big[ (\bar{a} + \beta\zeta + \gamma)(\bar{b} + \beta k_1 \zeta + \gamma)(\bar{c} + \beta k_2 \zeta + \gamma)\, z(X) \\
& \qquad - (\bar{a} + \beta \bar{s}_{\sigma_1} + \gamma)(\bar{b} + \beta \bar{s}_{\sigma_2} + \gamma)(\bar{c} + \beta S_{\sigma_3}(X) + \gamma)\, \bar{z}_\omega \big] \\
& + \alpha^2 \big[ (z(X) - 1) L_1(\zeta) \big] \\
& - Z_H(\zeta) \big[ t_{lo}(X) + \zeta^n t_{mid}(X) + \zeta^{2n} t_{hi}(X) \big]
\end{aligned}
$$

By construction, $r(\zeta) = 0$ for an honest prover. To prove consistency between the committed polynomials and their evaluations, the prover computes two opening proof polynomials:

$$
\begin{aligned}
W_\zeta(X) = \frac{1}{X - \zeta} \Big( & r(X) + v (a(X) - \bar{a}) + v^2 (b(X) - \bar{b}) + v^3 (c(X) - \bar{c}) \\
& + v^4 (S_{\sigma_1}(X) - \bar{s}_{\sigma_1}) + v^5 (S_{\sigma_2}(X) - \bar{s}_{\sigma_2}) \Big)
\end{aligned}
$$

$$W_{\zeta\omega}(X) = \frac{z(X) - \bar{z}_\omega}{X - \zeta\omega}$$

The prover commits to these, obtaining $[W_\zeta]_1$ and $[W_{\zeta\omega}]_1$.

The final proof is:

$$
\begin{aligned}
\pi_{\text{SNARK}} = \big( & [a]_1, [b]_1, [c]_1, [z]_1, [t_{lo}]_1, [t_{mid}]_1, [t_{hi}]_1, [W_\zeta]_1, [W_{\zeta\omega}]_1, \\
& \bar{a}, \bar{b}, \bar{c}, \bar{s}_{\sigma_1}, \bar{s}_{\sigma_2}, \bar{z}_\omega \big)
\end{aligned}
$$

That is 9 group elements and 6 field elements, whatever the size of the circuit.

The multipoint evaluation challenge $u$ is then derived from the transcript for verification, which ties the evaluations to the transcript.

Through these structured rounds, the prover creates a succinct proof that captures the circuit's correctness without revealing sensitive details. From initializing the transcript to generating the final proof, each stage contributes to the protocol's goal of efficiency and universality.
