This is very similar to the standard univariate commitment scheme, but it opens one polynomial at several points at once, with a single group element as the proof.

To open $P$ at points $z_1, \ldots, z_k$, with values $y_1, \ldots, y_k$:

1. Interpolate $r(X)$, the polynomial of degree less than $k$ with $r(z_i) = y_i$.
2. Build the vanishing polynomial $Z(X) = \prod_i (X - z_i)$.
3. Compute $Q(X) = \frac{P(X) - r(X)}{Z(X)}$, which is a polynomial exactly when all the claimed values are right. The proof is $W = Q(\alpha) G_1$.

The verifier computes $r$ and $Z$ from the points and values, and checks:

$$e(C - r(\alpha) G_1,\ G_2) = e(W,\ Z(\alpha) G_2)$$

Here $r(\alpha)G_1$ and $Z(\alpha)G_2$ come from the SRS, so unlike single-point KZG, the SRS needs enough powers of $\alpha$ in $\mathbb{G}_2$ to cover $Z$, which has degree $k$. The verifier's work also grows with $k$, since it has to compute $r$ and $Z$.

**Example.** Take $P(x) = 2x^3 + x + 4$, opened at $1$ and $2$, with values $7$ and $22$. Then $r(x) = 15x - 8$, $Z(x) = x^2 - 3x + 2$, and $Q(x) = 2x + 6$. With a toy $\alpha = 5$, the check compares exponents: $259 - 67 = 192$ on the left, and $16 \cdot 12 = 192$ on the right.

Rust implementation: [`pcs/src/kzg/univariate/batch.rs`](https://github.com/developeruche/cryptography-n-zk-research/blob/main/pcs/src/kzg/univariate/batch.rs)
