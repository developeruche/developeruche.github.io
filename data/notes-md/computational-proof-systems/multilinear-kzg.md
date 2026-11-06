Similar to the univariate KZG scheme, the interface of this commitment scheme entails:

1. Generate SRS
2. Commit function
3. Opening
4. Verification

Because we are dealing with multiple variables, these functions need adapting to keep the scheme secure and succinct.

KZG on multilinear polynomials is quite different from the univariate case. First, the multilinear polynomial is expressed by its evaluations over the Boolean hypercube, which has $2^{\ell}$ points for a polynomial with $\ell$ variables.

For example, given the multilinear polynomial $f(x,y) = 2xy + x + y + 4$, its evaluation form is:

| Boolean hypercube | Poly eval | Evaluation result |
| --- | --- | --- |
| $0,0$ | $f(0,0)$ | $4$ |
| $0,1$ | $f(0,1)$ | $5$ |
| $1,0$ | $f(1,0)$ | $5$ |
| $1,1$ | $f(1,1)$ | $8$ |

$$f(x,y) = [4, 5, 5, 8]$$

### Generating the Structured Reference String (SRS)

The structured reference string (SRS) consists of encodings in $\mathbb{G}_1$ of all Lagrange basis polynomials, evaluated at a randomly chosen input $\tau \in \mathbb{F}^{\ell}$. That is, if $\chi_1, \ldots, \chi_{2^{\ell}}$ denotes an enumeration of the $2^{\ell}$ Lagrange basis polynomials, the SRS contains $(g_1^{\chi_1(\tau)}, \ldots, g_1^{\chi_{2^{\ell}}(\tau)})$. The toxic waste that must be discarded, because it can be used to destroy binding, is the value $\tau$. Recall that $\ell$ is the number of variables of the multilinear polynomial.

```rust
pub struct MultiLinearSRS<P: Pairing> {
    pub g1_power_of_taus: Vec<P::G1>, // this is an expression of g1^tau^i over the boolean hypercube (every possible combination of each monomial)
    pub g2_power_of_taus: Vec<P::G2>, // this is a vector of g2^tau^i
}
```

This is the `MultiLinearSRS` structure. We have already described `g1_power_of_taus`. `g2_power_of_taus` is simpler: one element of $\mathbb{G}_2$ for each coordinate of $\tau$:

$$\texttt{g2\_power\_of\_taus} = [g_2^{\tau_1}, \ldots, g_2^{\tau_{\ell}}]$$

### Commit Function

This function commits to the polynomial, returning a group element that can be used for verification later. This is what the function interface looks like:

```rust
fn commit<F: PrimeField>(srs: &MultiLinearSRS<P>, poly: &Multilinear<F>) -> P::G1
```

It takes the `srs` and the `poly` to commit to, and returns the commitment.

This function is quite simple: it raises each element of the `srs` to the matching evaluation in `poly`, and multiplies the results together. Mathematically, if

$$q(X) = \sum_{i=1}^{2^{\ell}} c_i \chi_i(X)$$

then

$$g_1^{q(\tau)} = \prod_{i=1}^{2^{\ell}} \left(g_1^{\chi_i(\tau)}\right)^{c_i}$$

which can be computed given the values $g_1^{\chi_i(\tau)}$ for all $i$, even without knowing $\tau$.

### Opening Function

This is also known as making an evaluation and creating a proof for it. This is what the interface of `open` looks like:

```rust
fn open<F: PrimeField>(
    srs: &MultiLinearSRS<P>,
    poly: &Multilinear<F>,
    point: &[F],
) -> (F, Vec<<P as Pairing>::G1>)
```

This function takes the `srs`, the `poly`, and the `point` at which to evaluate the polynomial, and returns the evaluation along with a `Vec` of group elements, where each element is a commitment associated with one variable of the polynomial.

**Mathematically**

To open the commitment at input $z \in \mathbb{F}^{\ell}$ to some value $v$, i.e. to prove that $q(z) = v$, the committer computes a series of $\ell$ "witness polynomials" $w_1, \ldots, w_{\ell}$, defined by the following fact. For any fixed $z = (z_1, \ldots, z_{\ell}) \in \mathbb{F}^{\ell}$ and any multilinear polynomial $q$, we have $q(z) = v$ if and only if there exist multilinear polynomials $w_1, \ldots, w_{\ell}$ such that:

$$q(X) - v = \sum_{i=1}^{\ell} (X_i - z_i)\, w_i(X)$$

If $q(X) - v$ can be expressed as the right side of this equation, then clearly $q(z) - v = 0$, and hence $q(z) = v$.

On the other hand, suppose that $q(z) = v$. By dividing $q(X) - v$ by $(X_1 - z_1)$, we can identify multilinear polynomials $w_1$ and $s_1$ such that:

$$q(X) - v = (X_1 - z_1) \cdot w_1(X_2, \ldots, X_{\ell}) + s_1(X_2, \ldots, X_{\ell})$$

Since $q$ has degree one in $X_1$, neither $w_1$ nor the remainder $s_1$ depends on $X_1$. Iterating this process, we can divide $s_1$ by $(X_2 - z_2)$ to write:

$$q(X) - v = (X_1 - z_1) \cdot w_1(X_2, \ldots, X_{\ell}) + (X_2 - z_2) \cdot w_2(X_3, \ldots, X_{\ell}) + s_2(X_3, \ldots, X_{\ell})$$

and so forth, until we have written:

$$q(X) - v = \sum_{i=1}^{\ell} (X_i - z_i) \cdot w_i(X_{i+1}, \ldots, X_{\ell}) + s_{\ell}$$

where $s_{\ell}$ depends on no variables, i.e. it is simply a field element. Setting $X = z$ makes every other term vanish, and since $q(z) - v = 0$, it must hold that $s_{\ell} = 0$, completing the proof.

To open the commitment at $z$ to the value $v$, the prover computes $w_1, \ldots, w_{\ell}$ and sends the verifier values $y_1, \ldots, y_{\ell}$ claimed to equal $g_1^{w_i(\tau)}$. Since each $w_i$ is multilinear, $g_1^{w_i(\tau)}$ can be computed from the SRS, even though the prover does not know $\tau$.

### Verification

The verification stage is less trouble than opening. The major operations are computing some elliptic curve pairings, multiplying them, and comparing the results.

Mathematically, with commitment $c$:

$$e(c \cdot g_1^{-v},\ g_2) = \prod_{i=1}^{\ell} e\left(y_i,\ g_2^{\tau_i} \cdot g_2^{-z_i}\right)$$

This looks complete. Yes, it is, but still confusing...

### Example

Given the polynomial

$$f(x,y) = 2xy + 4x + 3$$

this is its representation in evaluation form over the Boolean hypercube:

| Boolean hypercube | Poly eval | Evaluation result |
| --- | --- | --- |
| $0,0$ | $f(0,0)$ | $3$ |
| $0,1$ | $f(0,1)$ | $3$ |
| $1,0$ | $f(1,0)$ | $7$ |
| $1,1$ | $f(1,1)$ | $9$ |

$$f(x,y) = [3, 3, 7, 9]$$

We use small integers so the arithmetic is easy to follow. In reality, all exponents live in a large finite field.

**Trusted setup**

1. Generate a vector of $\tau$ values, with one per variable of the polynomial:

$$\tau_x = 2, \quad \tau_y = 4$$

2. Perform the SRS generation step, evaluating each Lagrange basis polynomial at $\tau$:

| Boolean hypercube | Basis polynomial | Operation | Result |
| --- | --- | --- | --- |
| $0,0$ | $(1-x)(1-y)$ | $(1-2)(1-4)$ | $3$ |
| $0,1$ | $(1-x)y$ | $(1-2) \cdot 4$ | $-4$ |
| $1,0$ | $x(1-y)$ | $2(1-4)$ | $-6$ |
| $1,1$ | $xy$ | $2 \cdot 4$ | $8$ |

So the SRS in $\mathbb{G}_1$ is $[g_1^{3}, g_1^{-4}, g_1^{-6}, g_1^{8}]$, and in $\mathbb{G}_2$ it is $[g_2^{2}, g_2^{4}]$.

**Commitment**

Raise each SRS element to the matching evaluation of $f$, and multiply:

$$c = (g_1^{3})^{3} \cdot (g_1^{-4})^{3} \cdot (g_1^{-6})^{7} \cdot (g_1^{8})^{9} = g_1^{9 - 12 - 42 + 72} = g_1^{27}$$

As a check, this is $f(\tau_x, \tau_y) = f(2, 4) = 16 + 8 + 3 = 27$.

**Opening**

Open at $x = 5$, $y = 1$. The evaluation is:

$$v = f(5, 1) = 2 \cdot 5 \cdot 1 + 4 \cdot 5 + 3 = 33$$

Subtract the value, then divide by $(x - 5)$ and $(y - 1)$ in turn:

$$f(x,y) - 33 = 2xy + 4x - 30$$

$$2xy + 4x - 30 = (x - 5)(2y + 4) + (10y - 10)$$

$$10y - 10 = (y - 1) \cdot 10$$

So $w_x = 2y + 4$ and $w_y = 10$. Evaluating them at $\tau$ using the SRS gives the two proof elements:

$$y_x = g_1^{2 \cdot 4 + 4} = g_1^{12}, \qquad y_y = g_1^{10}$$

**Verification**

The verifier checks:

$$e(c \cdot g_1^{-33},\ g_2) = e(y_x,\ g_2^{\tau_x} \cdot g_2^{-5}) \cdot e(y_y,\ g_2^{\tau_y} \cdot g_2^{-1})$$

Substituting the values:

$$e(g_1^{27 - 33},\ g_2) = e(g_1^{12},\ g_2^{2 - 5}) \cdot e(g_1^{10},\ g_2^{4 - 1})$$

With $g_T = e(g_1, g_2)$, the exponents multiply across each pairing:

$$g_T^{-6} = g_T^{12 \cdot (-3)} \cdot g_T^{10 \cdot 3} = g_T^{-36 + 30} = g_T^{-6}$$

The check passes.

Special credit to:

- [Proofs, Arguments, and Zero-Knowledge](https://people.cs.georgetown.edu/jthaler/ProofsArgsAndZK.html) by [Justin Thaler](https://x.com/SuccinctJT)
- [Mike Francis](https://x.com/only1franchesco)

Rust implementation: [`pcs/src/kzg/multilinear/mod.rs`](https://github.com/developeruche/cryptography-n-zk-research/blob/main/pcs/src/kzg/multilinear/mod.rs)
