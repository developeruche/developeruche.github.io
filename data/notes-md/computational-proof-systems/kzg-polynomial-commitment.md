Let's dive into the KZG polynomial commitment scheme, a standout in the world of cryptography for its efficiency and elegance. Named after its creators (Kate, Zaverucha and Goldberg), KZG has become a go-to in areas like zero-knowledge proofs and blockchains.

The KZG scheme lets someone commit to a polynomial, say $P(x) = 2x^3 + x + 4$, in a way that's compact and verifiable. A single small commitment (think of it as a cryptographic fingerprint) locks in your polynomial without sending it. Later, you can open specific evaluations, like proving $P(2) = 22$, and anyone can check that quickly without seeing the whole polynomial.

**How does it work?** It relies on a bilinear pairing: a map $e: \mathbb{G}_1 \times \mathbb{G}_2 \to \mathbb{G}_T$ between elliptic curve groups, with the property that $e(aG_1, bG_2) = e(G_1, G_2)^{ab}$. This lets the verifier check one multiplication between hidden values, which ordinary curve operations can't do.

The setup starts with a trusted ceremony that generates a structured reference string (SRS), a list of precomputed points:

$$[G_1,\ \alpha G_1,\ \alpha^2 G_1,\ \ldots,\ \alpha^d G_1] \quad \text{and} \quad [G_2,\ \alpha G_2]$$

Here $G_1$ and $G_2$ are base points of the two groups, $\alpha$ is a secret number (called the trapdoor), and $d$ is the maximum degree of the polynomials you can commit to. This string is public, but $\alpha$ must stay unknown. Anyone who learns it can open a commitment to false values, so the setup has to be secure.

**Commit.** To commit to $P(x) = \sum_i p_i x^i$, you compute $C = P(\alpha) G_1$. Nobody knows $\alpha$, but this can still be computed from the SRS as a linear combination:

$$C = \sum_i p_i \cdot (\alpha^i G_1)$$

This single point $C$ is your commitment: constant-sized, no matter how big your polynomial is.

**Open.** To prove $P(a) = b$, you create the quotient polynomial

$$Q(x) = \frac{P(x) - b}{x - a}$$

which works because $P(a) = b$ means $x - a$ divides $P(x) - b$ cleanly. The proof is a commitment to the quotient: $W = Q(\alpha) G_1$.

**Verify.** The verifier uses the pairing to check $P(\alpha) - b = Q(\alpha)(\alpha - a)$ without knowing $\alpha$:

$$e(C - bG_1,\ G_2) = e(W,\ \alpha G_2 - aG_2)$$

If it holds, the claim is legit, and the check takes constant time regardless of the polynomial's size.

**Why is KZG cool?** It's very efficient: commitments and proofs are one group element each, and verification is a fixed number of pairings. This is why it's widely used in zk-SNARKs and in Ethereum's blobs ([EIP-4844](https://eips.ethereum.org/EIPS/eip-4844)).

**The catch.** That trusted setup: if the secret $\alpha$ leaks, the prover can forge openings. Multi-party ceremonies mitigate this, since $\alpha$ stays secret as long as a single participant is honest. Also, plain KZG isn't hiding. The commitment is deterministic, and every opening reveals an evaluation, so applications that need secrecy add random blinding. Finally, it relies on elliptic curve assumptions, so it isn't post-quantum secure. Alternatives like [FRI](/notes/cryptography-zkp/computational-proof-systems/fri-polynomial-commitment/) avoid both the trusted setup and the curves, at the cost of larger proofs.

In short, KZG is a sleek, pairing-based way to commit to polynomials, balancing compactness with provability. We will look at 3 flavors of this scheme:

- [Univariate KZG](/notes/cryptography-zkp/computational-proof-systems/univariate-kzg/)
- [Multilinear KZG](/notes/cryptography-zkp/computational-proof-systems/multilinear-kzg/)
- [Batch Univariate KZG](/notes/cryptography-zkp/computational-proof-systems/batch-univariate-kzg/)
