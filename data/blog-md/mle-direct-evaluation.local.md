# Multilinear Polynomial Extension and Direct evaluation 

A multilinear polynomial is a polynomial in multiple variables where each variable appears with degree at most 1. 

Say we have a m-variate functions that maps a string of "m" boolean vectors to a field element $F$. $f: \{0, 1\}^m \to  F$.

The extension of the m-variate function mean to say rather than mapping just a string of boolean to a field element we would like to be able to map any field element to another field element. we can express this mathematically as $\hat{f}: F^m \to F$

#### Goal for this note
Document how given, an m-variate function and some oracle query points $z \in F^m$, we could compute $\hat{f}(z)$ using only;
- $2^{m+1}$ multiplication
- $2^m$ addtions 
- $O(m)$ additional operations
- The amount of space used is coresponding to $O(m)$ field elements



before going further, would drop down here a formal/complete mathematical defination of a MLE; 

### Definition

Let $F$ be a finite field and $m \in \mathbb{N}$ be an integer. For every function $f: \{0,1\}^m \to F$, there exists a **unique** multilinear polynomial $\tilde{f}: F^m \to F$ such that:

1. $\tilde{f}$ is multilinear (each variable has degree at most 1)
2. $\tilde{f}$ agrees with $f$ on the Boolean hypercube: $\tilde{f}(b) = f(b)$ for all $b \in \{0,1\}^m$

We call $\tilde{f}$ the **multilinear extension** (MLE) of $f$.



The multilinear extension $\tilde{f}$ can be expressed explicitly as:

$$
\tilde{f}(z) = \sum_{b \in \{0,1\}^m} \text{eq}(z, b) \cdot f(b)
$$

where:
- $z = (z_1, z_2, \ldots, z_m) \in F^m$ is an arbitrary point in $F^m$
- $b = (b_1, b_2, \ldots, b_m) \in \{0,1\}^m$ ranges over all vertices of the Boolean hypercube
- The **equality indicator function** is defined as:

$$
\text{eq}(z, b) = \prod_{i=1}^{m} \text{eq}_1(z_i, b_i)
$$

- The **univariate equality indicator** is:

$$
\text{eq}_1(z_i, b_i) = z_i \cdot b_i + (1 - z_i) \cdot (1 - b_i)
$$

### Interpretation

The function $\text{eq}_1(z_i, b_i)$ acts as an interpolating factor:
- When $z_i = b_i$, we have $\text{eq}_1(z_i, b_i) = 1$
- When $z_i \neq b_i$ (and both are in $\{0,1\}$), we have $\text{eq}_1(z_i, b_i) = 0$


Therefore, $\text{eq}(z, b)$ serves as a **Lagrange basis polynomial** that equals 1 when $z = b$ and equals 0 when $z$ equals any other Boolean vector. This makes the MLE a weighted combination of the function values at Boolean points, where the weights are the multilinear Lagrange basis polynomials.


### Example

Let's work through a concrete example with $f: \{0,1\}^3 \to F$. Based on the sequence in your notes, the function maps inputs to the values $1$ through $8$. We will evaluate the MLE at the point $z = (2, 3, 4)$.

| $(b_1, b_2, b_3)$ | $f(b_1, b_2, b_3)$ |
| :--- | :--- |
| $(0,0,0)$ | $1$ |
| $(0,0,1)$ | $2$ |
| $(0,1,0)$ | $3$ |
| $(0,1,1)$ | $4$ |
| $(1,0,0)$ | $5$ |
| $(1,0,1)$ | $6$ |
| $(1,1,0)$ | $7$ |
| $(1,1,1)$ | $8$ |

**Step 1: Write the MLE Formula**

$$
\tilde{f}(z_1, z_2, z_3) = \sum_{b \in \{0,1\}^3} \text{eq}(z, b) \cdot f(b)
$$

This expands to the sum of 8 terms:

$$
\begin{aligned}
\tilde{f}(z) 
&= \text{eq}(z, 000)\cdot 1 + \text{eq}(z, 001)\cdot 2 + \text{eq}(z, 010)\cdot 3 + \text{eq}(z, 011)\cdot 4 \\
&\quad + \text{eq}(z, 100)\cdot 5 + \text{eq}(z, 101)\cdot 6 + \text{eq}(z, 110)\cdot 7 + \text{eq}(z, 111)\cdot 8
\end{aligned}
$$


**Step 2: Compute Each $\text{eq}(z, b)$ Term**

We use the simplified coordinate form: if $b_i=1$, use $z_i$; if $b_i=0$, use $(1-z_i)$.
Evaluated at $z = (2, 3, 4)$:

**For $b = (0, 0, 0)$:**
$$
\text{eq}(z, 000) = (1-z_1)(1-z_2)(1-z_3) = (1-2)(1-3)(1-4) = (-1)(-2)(-3) = -6
$$

**For $b = (0, 0, 1)$:**
$$
\text{eq}(z, 001) = (1-z_1)(1-z_2)(z_3) = (1-2)(1-3)(4) = (-1)(-2)(4) = 8
$$

**For $b = (0, 1, 0)$:**
$$
\text{eq}(z, 010) = (1-z_1)(z_2)(1-z_3) = (1-2)(3)(1-4) = (-1)(3)(-3) = 9
$$

**For $b = (0, 1, 1)$:**
$$
\text{eq}(z, 011) = (1-z_1)(z_2)(z_3) = (1-2)(3)(4) = (-1)(3)(4) = -12
$$

**For $b = (1, 0, 0)$:**
$$
\text{eq}(z, 100) = (z_1)(1-z_2)(1-z_3) = (2)(1-3)(1-4) = (2)(-2)(-3) = 12
$$

**For $b = (1, 0, 1)$:**
$$
\text{eq}(z, 101) = (z_1)(1-z_2)(z_3) = (2)(1-3)(4) = (2)(-2)(4) = -16
$$

**For $b = (1, 1, 0)$:**
$$
\text{eq}(z, 110) = (z_1)(z_2)(1-z_3) = (2)(3)(1-4) = (2)(3)(-3) = -18
$$

**For $b = (1, 1, 1)$:**
$$
\text{eq}(z, 111) = (z_1)(z_2)(z_3) = (2)(3)(4) = 24
$$

**Step 3: Substitute and Solve**

Now we multiply the computed weights (Lagrange basis) by the function values $f(b)$ and sum them up:

$$
\begin{aligned}
\tilde{f}(2, 3, 4) &= (-6 \cdot 1) + (8 \cdot 2) + (9 \cdot 3) + (-12 \cdot 4) \\
&\quad + (12 \cdot 5) + (-16 \cdot 6) + (-18 \cdot 7) + (24 \cdot 8) \\
\\
&= -6 + 16 + 27 - 48 + 60 - 96 - 126 + 192 \\
\\
&= 19
\end{aligned}
$$

**Step 4: Verification**

We can verify this result by observing that the input values $1, 2, \dots, 8$ follow a linear pattern. The polynomial form for this specific function is:
$$f(z) = 4z_1 + 2z_2 + z_3 + 1$$

Testing this simpler polynomial against our evaluation point $z=(2,3,4)$:
$$
4(2) + 2(3) + 4 + 1 = 8 + 6 + 4 + 1 = 19
$$

The results match, confirming the Direct Evaluation method.



## Rust Implementation: Direct Evaluation

To make this concept concrete, we implement the algorithm using Rust. We utilize the `ark_ff` library, which provides the generic `Field` traits used across the standard Zero-Knowledge Proof ecosystem (Groth16, Plonk, etc.).

The implementation follows the **Direct Evaluation** strategy, literally translating the summation formula:
$$\tilde{f}(z) = \sum_{b \in \{0,1\}^m} \text{eq}(z, b) \cdot f(b)$$

### 1\. Generating the Hypercube

The domain of our function $f$ is the boolean hypercube $\{0,1\}^m$. We represent these inputs as vectors of bits.

The function `generate_hypercube_vec` iterates from $0$ to $2^m - 1$. We use bitwise shifting `(i >> bit_index) & 1` to extract the boolean path for every possible input $b$.

```rust
pub fn generate_hypercube_vec(m: usize) -> Vec<Vec<u8>> {
    // ... allocates and populates the boolean hypercube ...
}
```

*Note: We pre-allocate memory using `Vec::with_capacity` to prevent expensive reallocations as the hypercube grows exponentially with $m$.*

### 2\. Computing Lagrange Basis Polynomials (`eq_funcs`)

This is the core of the MLE. We need to compute the weight (the `eq` term) for every point in the hypercube.

This function implements the product form of the indicator function:
$$\text{eq}(z, b) = \prod_{i=1}^{m} (z_i \cdot b_i + (1 - z_i)(1 - b_i))$$

In the code, we simplify this conditional logic:

  * If the hypercube bit $b_i$ is **1**, the term is $z_i$.
  * If the hypercube bit $b_i$ is **0**, the term is $(1 - z_i)$.



```rust
// Iterate over every point 'b' in the hypercube
for b in bh {
    let mut product_term = F::one();
    for (i, &bit) in b.iter().enumerate() {
        // Select z_i or (1 - z_i) based on the current bit
        let term = if bit == 1 {
            points[i] 
        } else {
            F::one() - points[i]
        };
        product_term *= term;
    }
    evals.push(product_term);
}
```

### 3\. The Dot Product (`mle_eval_direct`)

Finally, to get the value $\tilde{f}(z)$, we compute the weighted sum of all evaluations. This is effectively a dot product between:

1.  The vector of Lagrange basis evaluations ($\text{eq}(z, b)$).
2.  The vector of original function evaluations ($f(b)$).

<!-- end list -->

```rust
pub fn mle_eval_direct<F: Field>(points: &[F], evals: &[F]) -> F {
    let eq_s = eq_funcs(points); // Get weights
    let mut res = F::zero();

    // Sum_{b} ( f(b) * eq(z, b) )
    for (i, eval) in evals.iter().enumerate() {
        res += *eval * eq_s[i];
    }
    res
}
```

### Complexity Note

This direct implementation allows us to clearly see the math in action.

  * **Space Complexity:** $O(m \cdot 2^m)$ to store the hypercube explicitly.
  * **Time Complexity:** $O(m \cdot 2^m)$ multiplications, as we re-compute the product chain for every row in the hypercube.

In production ZK systems (like Spartan or HyperPlonk), we typically optimize this using Dynamic Programming (memoization) to achieve $O(2^m)$ time complexity, allowing us to evaluate the MLE in linear time relative to the size of the evaluation vector. But this would cause a strain on memory increasing the amount of memory needed for proof gen in these protocols, in large protocols like zkVM, this would not cut it, we would need obtain this speed-up without claiming the memory cost, Ron proposed an approach to get this done, [here](https://eprint.iacr.org/2024/1103.pdf). This next article would be exploring his ideas and prototype a RUST implementation also providing some benchmark report.

[Part 2: Ron's Optimization for Multilinear Extension Evaluation](https://hackmd.io/@0xdeveloperuche/SkWiQX8--l)

**References:**
1.  *Rothblum*, [A Note on Efficient Computation of the Multilinear Extension](https://eprint.iacr.org/2024/1103.pdf)
2.  *Developeruche*, [Rust Impl](https://github.com/developeruche/cryptography-n-zk-research/blob/main/exps/eff-mle/src/direct.rs)