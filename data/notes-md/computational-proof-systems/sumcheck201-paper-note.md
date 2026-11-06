These are my notes from reading [Sumcheck 201](https://github.com/ingonyama-zk/papers/blob/main/sumcheck_201_chapter_1.pdf) by Ingonyama, which explores algorithmic modifications to the sum-check protocol for products of multilinear extensions, to improve parallel computation and address memory bottlenecks. I implemented both algorithms in [super-sumcheck](https://github.com/developeruche/super-sumcheck). If the [sum-check protocol](/notes/cryptography-zkp/computational-proof-systems/sum-check-protocol/) is new to you, start there.

A feeling you must get used to going further: this feels like doing sum-check in reverse.

### The Boolean Hypercube and the Lagrange Basis

Take the $n$-dimensional Boolean hypercube $\{0,1\}^n$, with $n = \log_2 N$. The Lagrange basis on it is:

$$\chi_{\vec{s}}(\vec{x}) = \prod_{i=1}^{n} (\bar{x}_i \bar{s}_i + x_i s_i)$$

where:

- $\vec{s}_n(k) = \{s_{MSB(k)}, \ldots, s_{LSB(k)}\}$ is the $n$-bit representation of an integer $k$
- $\vec{x}_n = \{x_n, x_{n-1}, \ldots, x_1\}$
- $\bar{x}_i = 1 - x_i$ and $\bar{s}_i = 1 - s_i$

A multilinear polynomial can be expressed in the Lagrange basis as:

$$f(\vec{x}) = \sum_{k=1}^{2^n} \chi_{\vec{s}_n(k-1)}(\vec{x}) \cdot f(\vec{s}_n(k-1))$$

**Sample.** The values $\{f_0, f_1, f_2, f_3\} \in \mathbb{F}^4$ are represented on $\{0,1\}^2$, each one occupying a vertex of the hypercube:

| $k$ | $\vec{s}_2(k)$, as $(x_2, x_1)$ | $f(\vec{s}_2(k))$ |
| --- | --- | --- |
| 0 | $(0, 0)$ | $f_0$ |
| 1 | $(0, 1)$ | $f_1$ |
| 2 | $(1, 0)$ | $f_2$ |
| 3 | $(1, 1)$ | $f_3$ |

So:

$$f(x_2, x_1) = \sum_{k=1}^{4} \chi_{\vec{s}_2(k-1)}(\vec{x}) \cdot f(\vec{s}_2(k-1)) = \bar{x}_2 \bar{x}_1 f_0 + \bar{x}_2 x_1 f_1 + x_2 \bar{x}_1 f_2 + x_2 x_1 f_3$$

The property everything below relies on is that a multilinear polynomial can be split on any one variable, for any input, not only 0 and 1:

$$f(x, y) = \bar{y} \cdot f(x, 0) + y \cdot f(x, 1)$$

For example, take $f(x, y) = 2xy + 2x$. Directly, $f(2, 3) = 2 \cdot 2 \cdot 3 + 2 \cdot 2 = 16$. Using the split, $f(2, 3) = (1 - 3) \cdot f(2, 0) + 3 \cdot f(2, 1) = -2 \cdot 4 + 3 \cdot 8 = 16$.

### Algorithm 1: Collapsing Arrays

The idea is to parallelize each round's computation efficiently, while collapsing the vector size by half each round. Each round depends only on the array from the previous round.

We can write the polynomial of round 1 as an indexed vector:

$$r_1(\vec{x}_{n-1}, x) = \bar{x} \cdot f(\vec{x}_{n-1}, 0) + x \cdot f(\vec{x}_{n-1}, 1)$$

and store $f$ in an array of size $2^n$, where the even element $f(\vec{x}_{n-1}, 0)$ and the odd element $f(\vec{x}_{n-1}, 1)$ are consecutive. Then we sum over $\{0,1\}^{n-1}$ to compute the first round polynomial:

$$
\begin{aligned}
r_1(x) &= \sum_{x_i \in \{0,1\}} r_1(\vec{x}_{n-1}, x) \\
&= \bar{x} \sum_{x_i \in \{0,1\}} f(\vec{x}_{n-1}, 0) + x \sum_{x_i \in \{0,1\}} f(\vec{x}_{n-1}, 1)
\end{aligned}
$$

The prover sends $r_1(x)$ to the verifier, to obtain $\alpha_1 \in \mathbb{F}$. Computing this sum can be done entirely in parallel. As a preparatory step for the next round, we compute

$$r_1(x_n, \ldots, x_2, \alpha_1) = \bar{\alpha}_1 \cdot f(x_n, \ldots, x_2, 0) + \alpha_1 \cdot f(x_n, \ldots, x_2, 1)$$

and store it in a $2^{n-1}$-element array, the intermediate representation.

In round 2:

$$
\begin{aligned}
r_2(\vec{x}_{n-2}, x, \alpha_1) = {} & \bar{x} \big( \bar{\alpha}_1 f(\vec{x}_{n-2}, 0, 0) + \alpha_1 f(\vec{x}_{n-2}, 0, 1) \big) \\
& + x \big( \bar{\alpha}_1 f(\vec{x}_{n-2}, 1, 0) + \alpha_1 f(\vec{x}_{n-2}, 1, 1) \big) \\
= {} & \bar{x} \cdot r_1(\vec{x}_{n-2}, 0, \alpha_1) + x \cdot r_1(\vec{x}_{n-2}, 1, \alpha_1)
\end{aligned}
$$

We can note that this equation can be written in terms of $r_1$, so we can discard the original $2^n$ array. In general, the array for the $p$-th round follows this recursive formula:

$$r_p(\vec{x}_{n-p}, x, \vec{\alpha}_{p-1}) = \bar{x} \cdot r_{p-1}(\vec{x}_{n-p}, 0, \vec{\alpha}_{p-1}) + x \cdot r_{p-1}(\vec{x}_{n-p}, 1, \vec{\alpha}_{p-1})$$

where the two terms are consecutive even and odd elements of the array of $2^{n-p+1}$ elements left over from the previous round. This temporary array must be stored in memory, to be used in the next round. This is how the prover computes $r_p(x)$:

$$r_p(x) = \sum_{x_i \in \{0,1\}} r_p(\vec{x}_{n-p}, x, \vec{\alpha}_{p-1})$$

### Example

Take a polynomial in 3 variables:

$$
\begin{aligned}
f(x_3, x_2, x_1) = {} & f_0 \bar{x}_3 \bar{x}_2 \bar{x}_1 + f_1 \bar{x}_3 \bar{x}_2 x_1 + f_2 \bar{x}_3 x_2 \bar{x}_1 + f_3 \bar{x}_3 x_2 x_1 \\
& + f_4 x_3 \bar{x}_2 \bar{x}_1 + f_5 x_3 \bar{x}_2 x_1 + f_6 x_3 x_2 \bar{x}_1 + f_7 x_3 x_2 x_1
\end{aligned}
$$

**Round 1.** The round polynomial is:

$$r_1(x) = \sum_{x_3, x_2 \in \{0,1\}} f(x_3, x_2, x) = \sum_{i=0}^{3} r_1^{(i)}(x) \qquad \text{where} \qquad r_1^{(i)}(x) = f_{2i} \bar{x} + f_{2i+1} x$$

That is:

$$r_1(x) = \bar{x} (f_0 + f_2 + f_4 + f_6) + x (f_1 + f_3 + f_5 + f_7)$$

with one term per pair: $r_1^{(0)}(x) = \bar{x} f_0 + x f_1$, $r_1^{(1)}(x) = \bar{x} f_2 + x f_3$, $r_1^{(2)}(x) = \bar{x} f_4 + x f_5$, and $r_1^{(3)}(x) = \bar{x} f_6 + x f_7$.

After substituting $x = \alpha_1$, we keep the values $r_1^{(i)}(\alpha_1)$ as the entries on the vertices of a 2-dimensional Boolean hypercube, or equivalently a 4-element array. We can then compute $r_2$ directly from this data.

**Round 2.**

$$r_2(x) = \sum_{x_3 \in \{0,1\}} f(x_3, x, \alpha_1) = \sum_{i=0}^{1} r_2^{(i)}(x) \qquad \text{where} \qquad r_2^{(i)}(x) = r_1^{(2i)}(\alpha_1) \bar{x} + r_1^{(2i+1)}(\alpha_1) x$$

So:

$$r_2^{(0)}(x) = [\bar{\alpha}_1 f_0 + \alpha_1 f_1] \bar{x} + [\bar{\alpha}_1 f_2 + \alpha_1 f_3] x$$

$$r_2^{(1)}(x) = [\bar{\alpha}_1 f_4 + \alpha_1 f_5] \bar{x} + [\bar{\alpha}_1 f_6 + \alpha_1 f_7] x$$

**Round 3.** Similarly, we keep $r_2^{(i)}(\alpha_2)$ as a two-element array, and compute:

$$r_3(x) = f(x, \alpha_2, \alpha_1) = r_2^{(0)}(\alpha_2) \bar{x} + r_2^{(1)}(\alpha_2) x$$

$$
\begin{aligned}
r_3(x) = {} & \big( [\bar{\alpha}_1 \bar{\alpha}_2 f_0 + \alpha_1 \bar{\alpha}_2 f_1] + [\bar{\alpha}_1 \alpha_2 f_2 + \alpha_1 \alpha_2 f_3] \big) \bar{x} \\
& + \big( [\bar{\alpha}_1 \bar{\alpha}_2 f_4 + \alpha_1 \bar{\alpha}_2 f_5] + [\bar{\alpha}_1 \alpha_2 f_6 + \alpha_1 \alpha_2 f_7] \big) x
\end{aligned}
$$

At the end, $r_3(\alpha_3) = f(\alpha_3, \alpha_2, \alpha_1)$, the single evaluation the verifier needs to check.

This example uses one polynomial, so each round polynomial is linear. For a product of $d$ multilinear polynomials, the prover keeps one array per polynomial and folds them all the same way. Each round polynomial then has degree $d$, so the prover computes it at $d + 1$ points.

### Algorithm 2: Precomputation

The round polynomial can also be written using the Lagrange basis over the variables already fixed:

$$
\begin{aligned}
r_p(x) &= \sum_{x_i \in \{0,1\}} f(\vec{x}_{n-p}, x, \vec{\alpha}_{p-1}) \\
&= \sum_{r=1}^{2^p} \left( \chi_{\vec{s}_p(r-1)}(x, \vec{\alpha}_{p-1}) \cdot \sum_{x_i \in \{0,1\}} f(\vec{x}_{n-p}, \vec{s}_p(r-1)) \right)
\end{aligned}
$$

Notice that the round polynomial in the $p$-th round is a sum of the elements of the Hadamard product of two $2^p$-element vectors, and one of them, the inner sums of $f$, can be precomputed entirely before the sum-check protocol starts. The challenges only enter through the $\chi$ vector.

### Comparing the Two

Algorithm 1 is less memory intensive, since the arrays halve each round, while Algorithm 2 stores precomputed tables to offload work up front.

Algorithm 2 is easier to understand by looking at the paper's diagram. But my [benchmark](https://github.com/developeruche/super-sumcheck/blob/main/benches/benchmark.rs) shows Algorithm 1 is far faster in this implementation: for four polynomials in 7 variables, around 270 µs against around 775 ms, measured while preparing this page. So more effort has been placed into Algorithm 1. That gap reflects this implementation and these parameters, and shouldn't be read as a general ratio between the two algorithms.
