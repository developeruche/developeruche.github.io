PLONK (Permutations over Lagrange-bases for Oecumenical Noninteractive arguments of Knowledge) is a zero-knowledge proving system designed for scalability and efficiency in blockchain and cryptographic applications. Its modularity and simplicity make it a favored choice for developers and researchers working on zk-SNARKs (Zero-Knowledge Succinct Non-Interactive Arguments of Knowledge).

Introduced in 2019, PLONK addressed a key limitation of earlier protocols such as Groth16: the need for a new trusted setup for each circuit. PLONK uses one universal trusted setup, and builds on polynomial commitment schemes to achieve succinct, efficiently verifiable proofs.

This part takes a deep technical dive into the mechanics of the protocol, breaking down its components, theory and implementation.

Like a good number of zkSNARK protocols, its life cycle can be described as follows:

1. Computation
2. Algebraic circuit
3. Intermediate representation (for example, R1CS or Plonkish)
4. Polynomial structure (for example, QAP in the Groth16 protocol)
5. Interactive oracle proof, an information-theoretic protocol
6. SNARK, by compiling the protocol with a polynomial commitment scheme and Fiat-Shamir

### Protocol Overview

This is just a trailer of what will be explored:

- Universal trusted setup
- Expressing the computation as a circuit, and circuit compilation
- Witness generation and proof generation
- Verification

**Notation**

- $\mathbb{F}$: A finite field.
- $\omega$: A primitive $n$-th root of unity in $\mathbb{F}$, meaning $\omega^n = 1$ and $\omega^k \neq 1$ for $0 < k < n$.
- All polynomials have coefficients in $\mathbb{F}$, and the variable is usually denoted by $X$. We denote this set as $\mathbb{F}[X]$.
- We represent polynomials by single letters like $p, a, b, z$.
- $L_i$: A Lagrange basis polynomial.
- $M$: A matrix.
- $G$: A group generator.
- $[x]_1$: The element $x \cdot G_1$ of group 1.
- $[x]_2$: The element $x \cdot G_2$ of group 2.

### PLONK: Universal Trusted Setup

A trusted setup is needed because of the polynomial commitment scheme, which in this case is KZG. It needs a **one-time** universal trusted setup. It is called universal because the same setup can be used across many circuits, up to a maximum size, which reduces the amount of trust that needs to be established. Should the setup be compromised, however, invalid proofs can be generated.

> A polynomial commitment scheme is a cryptographic protocol that allows someone to commit to a polynomial, and later prove evaluations of the polynomial at specific points. It's like making a secure promise about a polynomial without sending all of it.

These are the steps involved in the [KZG scheme](/notes/cryptography-zkp/computational-proof-systems/kzg-polynomial-commitment/):

1. Setup
2. Commit to a polynomial
3. Prove an evaluation
4. Verify an evaluation proof

We only look at the `setup` stage here, which is the same setup needed in the PLONK protocol.

**Setup**

The first step is a one-time trusted setup. Once it is completed, the other steps can be repeated to commit to and reveal various polynomials.

- Let $G_1$ and $G_2$ be generators of the two groups of a pairing-friendly elliptic curve.
- Let $l$ be the maximum degree of the polynomials we want to commit to. For a PLONK circuit with $n$ gates, the blinded polynomials require $l = n + 5$.
- Pick a random field element $\tau \in \mathbb{F}_p$.
- Compute and publish $(G_1, \tau G_1, \tau^2 G_1, \ldots, \tau^l G_1)$ and $(G_2, \tau G_2)$.

> Note that $\tau$ must not be revealed. It is a secret parameter of the setup, and must be discarded after the setup ceremony so that nobody can figure out its value.

These published points are the Structured Reference String (SRS), which is used at the other stages of the commitment scheme.

This is all that is needed for the setup phase of the protocol.
