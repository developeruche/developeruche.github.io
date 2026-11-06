Understanding PLONK when expressed over multilinear polynomials. See this as a study companion while reading the HyperPlonk paper.

Proof systems have long been a fascinating cornerstone of cryptography and theoretical computer science, offering ways to verify complex computations without redoing the heavy lifting. In recent years, **SNARKs** (Succinct Non-Interactive Arguments of Knowledge) have captured the spotlight. They allow someone to prove they've correctly solved a problem, with a proof that's tiny and quick to check. Zero-knowledge SNARKs can also keep the solution secret. This has sparked a wave of real-world applications, from scaling blockchains to securing sensitive data.

Among the SNARK family, **Plonk** has risen as a fan favorite. Its proofs are compact (just a few hundred bytes) and can be verified quickly. Plonk's flexibility shines through its support for custom gates. But there's a hitch: when circuits get massive, with millions or billions of gates, the prover starts to sweat. The culprit is **fast Fourier transforms (FFTs)**, which Plonk relies on to handle its univariate polynomials. These scale quasi-linearly with circuit size, at $O(s \log s)$, turning proof generation into a bottleneck for large-scale tasks.

The FFT algorithm is quite fascinating, but it introduces significant overhead in the PLONK PIOP when building the polynomials representing the circuit trace. The goal of HyperPlonk is to eliminate the FFT from this flow.

In [HyperPlonk: Plonk with Linear-Time Prover and High-Degree Custom Gates](https://eprint.iacr.org/2022/1355), Binyi Chen, Benedikt Bünz, Dan Boneh and Zhenfei Zhang introduce an adaptation of the Plonk Interactive Oracle Proof (IOP). Unlike Plonk, HyperPlonk operates over the **Boolean hypercube**, denoted $B_\mu := \{0,1\}^\mu$, the space of binary strings of length $\mu$. This redefines it as a **multilinear IOP**, which can be compiled with a suitable multilinear commitment scheme. The result is a SNARK (or a zkSNARK) with a highly efficient prover.

HyperPlonk inherits Plonk's flexibility, but it brings some serious upgrades:

- It removes the need for FFTs during proof generation, relying on the classic [sum-check protocol](/notes/cryptography-zkp/computational-proof-systems/sum-check-protocol/) instead. This takes the prover's runtime from $O_\lambda(s \log s)$ to $O_\lambda(s)$.
- It supports custom gates of much higher degree without harming the prover's running time.

### Technical Overview

To express PLONK over the Boolean hypercube, we break PLONK down into its elementary sub-protocols, make each of them work on multilinear polynomials, and then trust the compounding effect.

### Recap on PLONK

If you don't know how PLONK works, you shouldn't be here!! Start with [this part of the book](/notes/cryptography-zkp/computational-proof-systems/plonk-protocol/).

**1. What's a circuit?**

- A **circuit** is a math flowchart with steps called **gates**.
- Each gate takes two inputs and does one operation: add, multiply, or something custom.
- It has **n public inputs** (starting numbers) and **s gates** (steps).

**2. Turning the circuit into a table**

- Plonk builds a table **M** with three columns: **Left (L)**, **Right (R)** and **Output (O)**.
- The table has **n + s + 1 rows**:
  - **First n rows:** Public inputs.
  - **Next s rows:** Gate inputs and outputs.
  - **Last row:** A check, set to zero, to confirm the final output.

**3. Encoding the table into a polynomial**

- This formulation uses a **cyclic subgroup Ω** with $3(n + s + 1)$ elements.
- It creates a polynomial $M(X)$ that encodes the table: $M(\omega^0) = L_0$, $M(\omega^1) = R_0$, $M(\omega^2) = O_0$, and so on for each row.

**4. Committing to the polynomial**

- The prover "locks" $M(X)$ in a commitment, like a sealed envelope.
- The verifier can ask questions about it without seeing the polynomial.

**5. Proving it's correct**

- The prover shows:
  - Each gate's output fits its operation (e.g., $O = L \cdot R$ for multiplication).
  - Inputs and outputs connect properly between gates.
  - The final row confirms the output is correct (zero).
- This is done in a short proof through a back-and-forth process.

### From Roots of Unity to the Hypercube

HyperPlonk keeps these same three checks, but replaces each tool that requires an FFT:

| Plonk | HyperPlonk |
| --- | --- |
| Table encoded over a subgroup of roots of unity | Table encoded as a multilinear polynomial over $B_\mu$ |
| Gates checked by dividing by $Z_H$ | Gates checked by a **zero check** |
| Wiring checked by a running product $z(X)$, shifted with $\omega X$ | Wiring checked by a **permutation check**, built on a **product check** |
| Univariate commitment, such as KZG | Multilinear commitment |

**Gates: the zero check.** The gate identity must hold at every point of the hypercube. Over the hypercube there's no $Z_H$ to divide by, so the check is turned into a sum. The verifier picks a random $r$, and the prover runs sum-check on:

$$\sum_{x \in B_\mu} eq(r, x) \cdot g(x) = 0$$

where $g$ is the gate identity, and $eq(r, x)$ is the multilinear polynomial that is 1 when $r = x$ on the hypercube and 0 at other hypercube points. A non-zero value of $g$ anywhere makes this sum non-zero, except with negligible probability over $r$.

**Wiring: the permutation check.** As in Plonk, wire values are combined with their positions using random $\beta$ and $\gamma$, and the check becomes the claim that two products are equal. HyperPlonk proves that claim with a product check, built from sum-check rather than from $\omega$-shifts. The zero check and these checks all reduce to evaluations of multilinear polynomials at random points.

**Why higher-degree gates get cheap.** With sum-check, the prover works over the hypercube, whose size doesn't grow with the gate's degree. Plonk's FFTs need a larger evaluation domain as the degree increases. This makes high-degree custom gates practical in HyperPlonk.

**Finishing.** Those evaluation claims are then opened using a multilinear polynomial commitment scheme, such as [multilinear KZG](/notes/cryptography-zkp/computational-proof-systems/multilinear-kzg/), and Fiat-Shamir makes the whole protocol non-interactive.

For the details of each sub-protocol, read the paper alongside this page.
