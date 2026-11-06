Rust implementation: [`arks/snarks/groth16`](https://github.com/developeruche/cryptography-n-zk-research/tree/main/arks/snarks/groth16)

The prerequisites for this study are:

- Bilinear pairings and elliptic curves
- [Quadratic arithmetic programs (QAPs)](/notes/cryptography-zkp/computational-proof-systems/r1cs-to-qap/)

Bilinear pairings and elliptic curves are fundamental to the Groth16 proving system and many other advanced cryptographic protocols. Elliptic curves provide a secure and efficient foundation, while bilinear pairings enable the construction of succinct, non-interactive proofs that are both powerful and practical.

### Elliptic Curves

An elliptic curve is a set of points that satisfy a specific mathematical equation. Over a finite field $\mathbb{F}_q$ (of characteristic other than 2 or 3), an elliptic curve $E$ is typically defined by an equation of the form $y^2 = x^3 + ax + b$, where $a$ and $b$ are coefficients in $\mathbb{F}_q$. The curve must be non-singular (it has no cusps or self-intersections), which requires $4a^3 + 27b^2 \neq 0$.

### Bilinear Pairings in Groth16

A bilinear pairing is a map $e: \mathbb{G}_1 \times \mathbb{G}_2 \to \mathbb{G}_T$ with the property that $e(aG_1, bG_2) = e(G_1, G_2)^{ab}$. It lets the verifier check a multiplication between values it can only see as curve points. Groth16 uses this so that proofs are small and quick to verify:

- **Setup phase:** Public parameters are generated, with elements in $\mathbb{G}_1$ and $\mathbb{G}_2$.
- **Proving phase:** The prover uses these parameters to create a proof that the computation was performed correctly. This involves operations in $\mathbb{G}_1$ and $\mathbb{G}_2$.
- **Verification phase:** The verifier computes pairings and checks that one equation holds in $\mathbb{G}_T$.

### The Protocol

The `Groth16` protocol, in most cases, starts with a circuit. A `Circuit` in ZKP is a structured way to represent a computation, analogous to a digital logic circuit in computer engineering.

**Structure:**

- **Inputs**: The public inputs, along with the values the prover knows and wants to keep private (the private witness).
- **Gates**: Basic operations performed on the inputs.
- **Outputs**: The results of the computations performed by the gates.

**Types of circuits:**

- **Arithmetic circuits** use addition and multiplication gates over a finite field. zk-SNARKs like Groth16 work with these.
- **Boolean circuits** use logical gates (AND, OR, NOT). They are more common in classical computer science, and can be transformed into arithmetic circuits.

### R1CS

The next stage is to convert the circuit to a format called `R1CS`.

A rank-1 constraint system with $n$ variables, $m$ constraints and $p$ public inputs has a witness vector $w \in \mathbb{F}^n$. By convention, the first $p$ elements of $w$ are the public inputs, and $w_0$ is fixed to 1. Each of the $m$ constraints is a product equation between three inner products:

$$(a_j \cdot w)(b_j \cdot w) = c_j \cdot w$$

where the vectors $a_j, b_j, c_j \in \mathbb{F}^n$ specify constraint $j$. These vectors are usually very sparse. Stacking them into $m \times n$ matrices, the whole system is written with an element-wise product:

$$Aw \circ Bw = Cw$$

### QAP

Next, the R1CS is [transformed into a QAP](/notes/cryptography-zkp/computational-proof-systems/r1cs-to-qap/). For each variable $i$, interpolate polynomials $A_i(X), B_i(X), C_i(X)$ through column $i$ of each matrix, over $m$ fixed points. Then define $A(X) = \sum_{i=0}^{n-1} w_i A_i(X)$, and similarly $B(X)$ and $C(X)$. The constraints hold exactly when there is a polynomial $H(X)$ of degree at most $m - 2$ such that

$$A(X)B(X) - C(X) = H(X) Z_x(X)$$

where $Z_x(X)$ is the polynomial that vanishes on the $m$ points.

### Trusted Setup

The next stage is the trusted setup, where the `common reference string` is generated. Groth16's setup has two phases:

1. **Powers of tau**, which is generic and can be reused by many circuits
2. **Circuit-specific generation**

**Powers of tau**

Generate random $\tau, \alpha, \beta$. For a circuit with at most $m$ constraints, compute:

$$(\tau^0, \tau^1, \ldots, \tau^{2m-2}) \cdot G_1$$

$$(\tau^0, \tau^1, \ldots, \tau^{m-1}) \cdot G_2$$

$$\alpha \cdot (\tau^0, \tau^1, \ldots, \tau^{m-1}) \cdot G_1$$

$$\beta \cdot (\tau^0, \tau^1, \ldots, \tau^{m-1}) \cdot G_1$$

$$\beta \cdot G_2$$

This completes phase one.

**Circuit-specific generation**

Given the circuit polynomials $A_i, B_i, C_i$, generate random $\gamma, \delta$, and define for each variable $i$ the polynomial:

$$L_i(X) = \beta A_i(X) + \alpha B_i(X) + C_i(X)$$

We cannot compute $L_i(X)$ directly, since nobody knows $\alpha$ and $\beta$, but we can still construct $L_i(\tau) \cdot G_1$ using linear combinations of the values from phase one. (More on this below.) This gives the **proving key**:

$$(\alpha, \beta, \delta) \cdot G_1$$

$$(\tau^0, \tau^1, \ldots, \tau^{m-1}) \cdot G_1$$

$$\delta^{-1} \cdot (L_p(\tau), L_{p+1}(\tau), \ldots, L_{n-1}(\tau)) \cdot G_1$$

$$\delta^{-1} \cdot (\tau^0, \tau^1, \ldots, \tau^{m-2}) \cdot Z_x(\tau) \cdot G_1$$

$$(\beta, \delta) \cdot G_2$$

$$(\tau^0, \tau^1, \ldots, \tau^{m-1}) \cdot G_2$$

and the **verification key**:

$$\alpha \cdot G_1$$

$$\gamma^{-1} \cdot (L_0(\tau), L_1(\tau), \ldots, L_{p-1}(\tau)) \cdot G_1$$

$$(\beta, \gamma, \delta) \cdot G_2$$

The private variables ($i \geq p$) are divided by $\delta$ and the public ones ($i < p$) by $\gamma$. This separation stops a prover from using public terms in place of private ones.

Instead of $\alpha \cdot G_1$ and $\beta \cdot G_2$, the verification key could hold their pairing $e(\alpha G_1, \beta G_2)$, since that is the only way the verifier uses them. Many implementations do this to save one pairing.

The values $\tau, \alpha, \beta, \gamma, \delta$ are toxic waste and must be destroyed. Phase two is critical for soundness: $\delta^{-1}$ forces the $H$ part of the proof into the form $\delta^{-1} H(\tau) Z_x(\tau) \cdot G_1$. Anyone who knows $\delta$ escapes that form and can forge a proof of a false statement. In practice both phases are run as multi-party ceremonies, so the setup is safe as long as one participant in each phase is honest.

**Linear combinations**

If you are as smart as I am, phase two is very confusing. Before we can break it down, we need to look at linear combinations: how we can compute with a secret, even though we only have the "encrypted" version of it ($\text{secret} \cdot G$).

*Keep your eyes on this:*

$$\sum_{i=0}^{l} \phi_i \cdot (\tau^i G) = \phi(\tau) \cdot G$$

Here the $\tau^i G$ are the elements of the powers of tau, and the $\phi_i$ are the public coefficients of a polynomial $\phi$. So anyone can evaluate a known polynomial at the secret $\tau$, inside the group.

To obtain $L_i(\tau) \cdot G_1 = \beta A_i(\tau) \cdot G_1 + \alpha B_i(\tau) \cdot G_1 + C_i(\tau) \cdot G_1$, we break it down term by term:

1. $\beta A_i(\tau) \cdot G_1$: a linear combination of $\beta \cdot \tau^j \cdot G_1$, using the coefficients of $A_i$.
2. $\alpha B_i(\tau) \cdot G_1$: a linear combination of $\alpha \cdot \tau^j \cdot G_1$, using the coefficients of $B_i$.
3. $C_i(\tau) \cdot G_1$: a linear combination of $\tau^j \cdot G_1$, using the coefficients of $C_i$.

All three lists were published in phase one, which is why they are there.

### Proving

Given a witness $w$ that satisfies the constraints, compute $A(X), B(X), C(X)$ and $H(X)$ as above. Generate two random values $r, s$, which provide the zero knowledge, and compute:

$$\mathbf{A} = \big(\alpha + A(\tau) + r\delta\big) \cdot G_1$$

$$\mathbf{B} = \big(\beta + B(\tau) + s\delta\big) \cdot G_2$$

$$
\begin{aligned}
\mathbf{C} = \Big(\ & \delta^{-1}\big(\textstyle\sum_{i=p}^{n-1} w_i L_i(\tau) + H(\tau) Z_x(\tau)\big) \\
& + s\big(\alpha + A(\tau) + r\delta\big) \\
& + r\big(\beta + B(\tau) + s\delta\big) - rs\delta\ \Big) \cdot G_1
\end{aligned}
$$

Each of these can be computed from the proving key, without knowing the secrets. The proof is the triplet $(\mathbf{A}, \mathbf{B}, \mathbf{C})$: two elements of $\mathbb{G}_1$ and one of $\mathbb{G}_2$, whatever the size of the circuit.

### Verifying

Given a proof and the public inputs $w_0, \ldots, w_{p-1}$, the verifier aggregates the public inputs:

$$\mathbf{L} = \sum_{i=0}^{p-1} w_i \cdot \left(\gamma^{-1} L_i(\tau) \cdot G_1\right)$$

and checks one equation:

$$e(\mathbf{A}, \mathbf{B}) = e(\alpha G_1, \beta G_2) \cdot e(\mathbf{L}, \gamma G_2) \cdot e(\mathbf{C}, \delta G_2)$$

Expanding both sides in the exponent, the terms with $r$ and $s$ cancel, and what remains is the QAP identity $A(\tau)B(\tau) - C(\tau) = H(\tau)Z_x(\tau)$, evaluated at the secret point $\tau$.

Note that Groth16 proofs are malleable: given a valid proof, anyone can produce a different valid proof of the same statement, without knowing the witness. Applications that use a proof as a unique identifier must account for this.

Reference:

- [Groth16 notes](https://2π.com/22/groth16/) by Remco Bloemen, which this page's setup section follows closely
- [Groth16](https://www.rareskills.io/post/groth16) by RareSkills
- [On the Size of Pairing-based Non-interactive Arguments](https://eprint.iacr.org/2016/260) by Jens Groth
