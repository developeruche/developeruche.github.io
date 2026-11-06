**Introduction and context**

Polynomial commitment schemes allow a prover to commit to a polynomial and later prove specific properties of it. The plookup protocol, from the paper [plookup: A simplified polynomial protocol for lookup tables](https://eprint.iacr.org/2020/315) by Ariel Gabizon and Zachary J. Williamson (2020), addresses a specific challenge: verifying that the values of a committed polynomial $f$, at the points of a multiplicative subgroup, are contained in a lookup table $t$. This is crucial for applications in zk-SNARKs, such as batched range proofs, where we need to ensure all polynomial values fall within a specific range.

**Background: commitment schemes and polynomial commitments**

A commitment scheme allows a party to commit to a value, with two key properties:

- **Hiding property:** The commitment reveals no information about the committed value.
- **Binding property:** Once committed, the value cannot be changed.

Polynomial commitment schemes extend this to polynomials, enabling commitments to functions that encode complex data or computations. Schemes like [KZG](https://risencrypto.github.io/Kate/) allow succinct commitments and efficient verification of polynomial evaluations, which are foundational for zk-SNARKs.

**Problem statement and motivation**

The protocol verifies that, for each point in a multiplicative subgroup $H$ of size $n + 1$, the value of $f$ at that point (apart from one point left free) is in the lookup table $t$, which has $d$ elements. This is essential in scenarios like range checks, where we need to prove all values of $f$ lie within a specific set.

The closest earlier protocol, by [Bootle et al. (Asiacrypt 2018)](https://eprint.iacr.org/2018/380), requires commitments to several auxiliary polynomials of degree $d \cdot \log n$. Plookup simplifies this, requiring only *three commitments* to auxiliary polynomials of degree $n$, which can be much smaller when $d \sim n$.

**The idea**

Take the sorted list $s$ of $f$ and $t$ combined, in the same order as $t$. Every value of $f$ now sits next to an equal value. So if we look at the pairs of neighbours in $s$, we see the neighbouring pairs of $t$, plus some repeated pairs $(f_i, f_i)$. The protocol checks that as a multiset identity: a randomized expression in $\beta$ and $\gamma$ matches on the two sides. A value of $f$ that isn't in $t$ would create pairs that can't be accounted for.

**Detailed protocol steps**

The steps assume $d = n + 1$ for simplicity. If $d$ is smaller, pad $t$ by repeating its last element. Here $H = \{\mathbf{g}, \ldots, \mathbf{g}^{n+1} = 1\}$, and $f \in \mathbb{F}^n$ holds the values of the polynomial at the first $n$ points.

1. **Sorting and representation:**
   - Concatenate $f \in \mathbb{F}^n$ and $t \in \mathbb{F}^{n+1}$, and sort the result by the order of $t$ to get $s \in \mathbb{F}^{2n+1}$.
   - Represent $s$ using two polynomials $h_1, h_2$ of degree at most $n$, with $h_1(\mathbf{g}^i) = s_i$ and $h_2(\mathbf{g}^i) = s_{n+i}$ for $i \in [n+1]$. They overlap on one element, $s_{n+1}$, which ties the two halves together.
2. **Prover sends polynomials:** The prover computes and sends $h_1$ and $h_2$ to the verifier.
3. **Verifier sends random challenges:** The verifier chooses random $\beta, \gamma \in \mathbb{F}$ and sends them to the prover.
4. **Prover computes the aggregation polynomial:** The prover computes $Z$, of degree at most $n$, defined by $Z(\mathbf{g}) = 1$, $Z(\mathbf{g}^{n+1}) = 1$, and for $2 \leq i \leq n$:

$$Z(\mathbf{g}^i) = \frac{(1+\beta)^{i-1} \prod_{j < i} (\gamma + f_j) \cdot \prod_{1 \leq j < i} (\gamma(1+\beta) + t_j + \beta t_{j+1})}{\prod_{1 \leq j < i} (\gamma(1+\beta) + s_j + \beta s_{j+1}) (\gamma(1+\beta) + s_{n+j} + \beta s_{n+j+1})}$$

5. **Prover sends the aggregation polynomial:** The prover sends $Z$ to the verifier.
6. **Verifier checks identities:** The verifier checks these, for all $\mathbf{x} \in H$:

$$L_1(\mathbf{x})(Z(\mathbf{x}) - 1) = 0$$

$$
\begin{aligned}
& (\mathbf{x} - \mathbf{g}^{n+1})\, Z(\mathbf{x})\, (1+\beta)\, (\gamma + f(\mathbf{x}))\, (\gamma(1+\beta) + t(\mathbf{x}) + \beta t(\mathbf{g}\mathbf{x})) \\
& = (\mathbf{x} - \mathbf{g}^{n+1})\, Z(\mathbf{g}\mathbf{x})\, (\gamma(1+\beta) + h_1(\mathbf{x}) + \beta h_1(\mathbf{g}\mathbf{x}))\, (\gamma(1+\beta) + h_2(\mathbf{x}) + \beta h_2(\mathbf{g}\mathbf{x}))
\end{aligned}
$$

$$L_{n+1}(\mathbf{x})(h_1(\mathbf{x}) - h_2(\mathbf{g}\mathbf{x})) = 0$$

$$L_{n+1}(\mathbf{x})(Z(\mathbf{x}) - 1) = 0$$

The first and last identities fix $Z$ to 1 at both ends, the second is the running product, and the third connects the two halves of $s$. The verifier accepts if and only if all of them pass.

If the values of $f$ aren't contained in $t$, the verifier accepts with negligible probability.

**A small example**

Take $n = 3$, with $t = [1, 2, 3, 4]$ and $f = [2, 2, 4]$. Sorting gives $s = [1, 2, 2, 2, 3, 4, 4]$, so $h_1$ takes the values $[1, 2, 2, 2]$ and $h_2$ takes $[2, 3, 4, 4]$. They share the value of $s_4 = 2$. For random $\beta$ and $\gamma$, the running product $Z$ comes back to 1.

If instead $f = [2, 2, 5]$, the value 5 isn't in the table. Sorting gives $[1, 2, 2, 2, 3, 4, 5]$, where the neighbouring pair $(4, 5)$ has no counterpart, and the running product no longer comes back to 1.

**Key components**

- **Sorting mechanism:** Sorting $f$ and $t$ together transforms the membership problem into checking consistency in the sorted list, handled through $h_1$ and $h_2$.
- **Aggregation polynomial $Z$:** This polynomial, part of a grand product argument, compactly verifies the multiset identity. The random challenges $\beta$ and $\gamma$ are what make this sound.
- **Efficiency:** Plookup needs three commitments to polynomials of degree $n$ (namely $h_1$, $h_2$ and $Z$), which is especially attractive when $d \leq n$.
