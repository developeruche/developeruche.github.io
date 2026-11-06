Exploring the KZG polynomial commitment scheme over a univariate polynomial.

These are my favorite resources for understanding the univariate KZG commitment scheme:

- [KZG in Practice: Polynomial Commitment Schemes and Their Usage in Scaling Ethereum (Scroll)](https://scroll.io/blog/kzg)
- [KZG Commitment Scheme (Scroll Documentation)](https://docs.scroll.io/en/learn/zero-knowledge/kzg-commitment-scheme/)

With these resources, you should be able to attempt building the KZG commitment scheme!

### A quick worked example

Using the polynomial from the [previous page](/notes/cryptography-zkp/computational-proof-systems/kzg-polynomial-commitment/), with a toy trapdoor $\alpha = 5$ (in reality nobody knows $\alpha$, and all of this happens in a finite field):

- **Commit:** $P(x) = 2x^3 + x + 4$, so $P(5) = 259$ and $C = 259\,G_1$.
- **Open at $a = 2$:** $P(2) = 22$, and $Q(x) = \frac{2x^3 + x - 18}{x - 2} = 2x^2 + 4x + 9$. So $Q(5) = 79$ and $W = 79\,G_1$.
- **Verify:** the pairing check compares exponents: $259 - 22 = 237$ on the left, and $79 \cdot (5 - 2) = 237$ on the right.

### Rust implementation

[`pcs/src/kzg/univariate/mod.rs`](https://github.com/developeruche/cryptography-n-zk-research/blob/main/pcs/src/kzg/univariate/mod.rs). Note that its `generate_srs` takes `tau` as an argument, which is convenient for testing. A real deployment takes the SRS from a ceremony, so that nobody holds `tau`.
