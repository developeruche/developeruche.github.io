Polynomials play a central role in zero-knowledge proofs because they provide a mathematical foundation for constructing efficient and secure cryptographic systems.

A polynomial is a mathematical expression made up of variables and coefficients, combined using addition, subtraction and multiplication, where the variables are raised to non-negative integer powers. For example, $P(x) = 3x^2 + 5x + 2$ is a polynomial. In zero-knowledge proofs, these polynomials are typically defined over finite fields (a special kind of number system used in cryptography), which makes them well suited to computation and security.

This chapter is concerned with just two classes of polynomials.

### Univariate Polynomials

Univariate polynomials have just one variable, and they are a backbone of zero-knowledge proofs, especially zk-SNARKs. Many of these proofs encode a computation as a polynomial identity in one variable $x$. One method for doing this is the Quadratic Arithmetic Program (QAP). The verifier checks the identity at a random point rather than everywhere, because two different low-degree polynomials agree at a random point only with negligible probability.

### Multilinear Polynomials

Multilinear polynomials are linear in each of their variables, like $P(x, y) = x + y + xy$. They are a natural fit for computations over many variables: a multilinear polynomial in $n$ variables is uniquely determined by its $2^n$ values on the Boolean hypercube $\{0,1\}^n$, so any table of data can be treated as one. Proof systems built on the [sum-check protocol](/notes/cryptography-zkp/computational-proof-systems/sum-check-protocol/) rely on them, and a scheme called Zeromorph commits to them and proves evaluations of them in zero knowledge.

### Univariate and Multilinear Polynomials in Zero-Knowledge Proofs

Zero-knowledge proofs are cryptographic protocols that allow a prover to demonstrate the validity of a statement without revealing any additional information, a concept pivotal for privacy and scalability in applications like blockchains. Within this domain, polynomials are fundamental mathematical constructs that enable the design of efficient and secure proof systems.

**Univariate Polynomials: The Backbone of Many zk-SNARKs**

Univariate polynomials are central to many proof systems, particularly zk-SNARKs. They are instrumental in arithmetization, where a computation, often represented as a circuit, is transformed into a system of polynomial equations, using techniques such as the Quadratic Arithmetic Program (QAP).

In the QAP framework, each wire of the circuit gets polynomials for the left inputs, right inputs and outputs of the gates. Combining them with the witness gives three polynomials: $L(x)$, $R(x)$ and $O(x)$. The computation is correct exactly when $L(x) \cdot R(x) - O(x)$ is zero at every gate's evaluation point, which means it is divisible by the target polynomial $t(x)$ that vanishes on those points:

$$L(x) \cdot R(x) - O(x) = h(x) \cdot t(x)$$

The verifier checks this identity at a random point, which makes verification both simple and cheap, without revealing the inputs.

Univariate polynomials also pair well with polynomial commitment schemes such as Kate-Zaverucha-Goldberg (KZG), where the prover commits to a polynomial and later reveals its evaluation at chosen points with a short proof ([Understanding Zero-Knowledge Proofs: Part 4 — Polynomial Commitments](https://medium.com/@bhaskark2/understanding-zero-knowledge-proofs-part-4-polynomial-commitments-e6e2a6a5e5e8)). This efficiency is crucial for applications that need succinct proofs, such as privacy-preserving cryptocurrencies.

**Multilinear Polynomials: Handling Multiple Variables Efficiently**

Multilinear polynomials have degree at most one in each variable, e.g. $P(x, y) = ax + by + cxy + d$. They are particularly useful for representing functions of many variables.

Their structure allows efficient evaluation: given the $2^n$ values on the hypercube, the polynomial can be evaluated at any point in $O(2^n)$ field operations, by fixing one variable at a time. This is what lets a sum-check prover run in time linear in the size of the table.

A notable application is the paper [Zeromorph: Zero-Knowledge Multilinear-Evaluation Proofs from Homomorphic Univariate Commitments](https://eprint.iacr.org/2023/917), which introduces a scheme to commit to multilinear polynomials and prove their evaluations in zero knowledge. The construction relies on any additively homomorphic univariate commitment, plus a protocol showing that committed polynomials satisfy public degree bounds. For an $n$-linear polynomial, instantiating it with a hiding version of KZG means the prover performs only $n + 5$ extra first-group operations to achieve zero knowledge. Previous constructions required an extra multi-scalar multiplication of size $2^n$.

For contrast, the name "multivariate" also appears in a different line of work. [Zero-Knowledge for Multivariate Polynomials](https://link.springer.com/chapter/10.1007/978-3-642-33481-8_11) builds zero-knowledge arguments of knowledge of a *solution to a system of multivariate equations* of degree $d$, generalizing schemes based on the MQ problem. It uses a polarization identity to obtain a $d$-linear function, and a cut-and-choose technique. The hard problem there is solving the equations, so it is not a commitment to a multilinear polynomial in the sense used above.

**Comparative Analysis**

| **Aspect** | **Univariate Polynomials** | **Multilinear Polynomials** |
| --- | --- | --- |
| **Definition** | One variable, e.g. $P(x) = x^2 + 2x + 1$ | Linear in each variable, e.g. $P(x, y) = x + y + xy$ |
| **Primary use in ZK** | Encoding a computation as a polynomial identity (QAP, PLONK) | Representing large tables over the Boolean hypercube (sum-check based systems) |
| **Natural domain** | Roots of unity, using FFTs | The Boolean hypercube $\{0,1\}^n$ |
| **Example check** | $L(x) R(x) - O(x) = h(x) t(x)$ at a random point | A sum over the hypercube, using sum-check |
| **Commitment schemes** | KZG, FRI | Multilinear KZG, or univariate commitments via Zeromorph |

The choice between them depends on the proof system's design goals, such as proof size, verification time and prover cost. Multilinear systems avoid FFTs, which is often a large saving for the prover, while univariate systems have mature tooling and very small proofs. Both are indispensable in the construction of modern zero-knowledge proofs.

- [Univariate polynomial Rust implementation](https://github.com/developeruche/cryptography-n-zk-research/blob/main/primitives/polynomial/src/univariant.rs)
- [Multilinear polynomial Rust implementation](https://github.com/developeruche/cryptography-n-zk-research/blob/main/primitives/polynomial/src/multilinear.rs)
