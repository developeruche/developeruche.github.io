FRI lets a prover convince a verifier that a long list of committed values really comes from a low-degree polynomial, while the verifier reads only a few of those values. It needs no trusted setup and no elliptic curves, only a hash function.

FRI stands for **Fast Reed-Solomon Interactive Oracle Proof of Proximity**. The name sounds scary, but the core idea is one trick repeated: **fold the polynomial in half, again and again, until it is a constant.** By the end of this page you will have followed that trick by hand.

### The Problem FRI Solves

Say the prover has a polynomial $f$ of degree less than $d$. In most proof systems, the prover must show the verifier that some committed data is such a polynomial, because a correct computation produces a low-degree polynomial, and a cheating one generally doesn't.

[KZG](/notes/cryptography-zkp/computational-proof-systems/kzg-polynomial-commitment/) solves this with a pairing and a trusted setup: the structure of the setup forces the degree bound. FRI takes a different route.

### Step 1: Stretch the Polynomial

The prover evaluates $f$ on a domain $D$ much larger than $d$. For example, $f$ might have degree below 4 and be evaluated on 8 points. The list of values is called a **Reed-Solomon codeword**, and the ratio $\rho = d / |D|$ is the **rate**. Here $\rho = \frac{1}{2}$.

Why stretch it? Two different polynomials of degree below $d$ agree on fewer than $d$ points. So on a domain several times bigger than $d$, two low-degree polynomials must differ almost everywhere. A list of values is therefore either close to one low-degree polynomial, or it disagrees with every low-degree polynomial on many positions.

That is what makes spot checks work, because cheating can't be hidden in just one or two places. It is also why FRI speaks of *proximity*: it shows the list is close to a low-degree polynomial, not exactly equal to one.

### Step 2: Commit with a Merkle Tree

The prover hashes all the values into a [Merkle tree](/blog/merkle-tree-blockchain/), and sends the root. This single hash fixes every value. Later, the prover can reveal any position with a short path that proves it was in the tree.

The verifier could now ask for random positions. But a few random values say nothing about the degree on their own, since any handful of points fits some low-degree polynomial. Checking the degree directly would need more than $d$ values, and for large $d$ that is far too many. We need a way to make the problem smaller.

### Step 3: Fold

Here is the trick. Any polynomial can be split into its even and odd powers:

$$f(x) = f_{even}(x^2) + x \cdot f_{odd}(x^2)$$

For example:

$$1 + 2x + 3x^2 + 4x^3 = \underbrace{(1 + 3x^2)}_{f_{even}(x^2)} + x \cdot \underbrace{(2 + 4x^2)}_{f_{odd}(x^2)}$$

Both $f_{even}(y) = 1 + 3y$ and $f_{odd}(y) = 2 + 4y$ have half the degree bound of $f$.

The verifier sends a random number $\beta$, and the prover combines the two halves into one new polynomial:

$$f_1(y) = f_{even}(y) + \beta \cdot f_{odd}(y)$$

This $f_1$ has half the degree. It also needs only half the domain, because of how the domain is chosen. $D$ is built from roots of unity, so if $x$ is in $D$ then so is $-x$, and both square to the same $y = x^2$. So the squares of $D$ form a new domain, half the size. The rate stays the same.

The prover commits to $f_1$ on the new domain with a new Merkle root, and folds again. Each fold halves the degree bound, so after $\log_2 d$ folds the polynomial is a **constant**, a single number, which the prover simply sends.

Checking that a list is a constant is easy: every value in it must be that number.

### Step 4: Check the Folds with Queries

The prover could have cheated by committing to anything at each layer, so the verifier must confirm each layer is really the fold of the one before. The key fact is that one fold can be checked at a point using just two values from the previous layer:

$$f_{even}(x^2) = \frac{f(x) + f(-x)}{2} \qquad f_{odd}(x^2) = \frac{f(x) - f(-x)}{2x}$$

So:

$$f_1(x^2) = \frac{f(x) + f(-x)}{2} + \beta \cdot \frac{f(x) - f(-x)}{2x}$$

The verifier picks a random $x$, and the prover opens $f(x)$ and $f(-x)$ with Merkle paths, along with $f_1(x^2)$. The verifier checks that formula. Then it moves down a layer using $x^2$ and $-x^2$, and continues all the way to the constant.

Repeating this at several random starting points makes up the whole test.

### A Worked Example

We work in the field $\mathbb{F}_{97}$, where 64 has order 8, so the domain is its powers:

$$D = [1, 64, 22, 50, 96, 33, 75, 47]$$

Notice the pairs: each element's negative sits 4 places later. For example, $-64 \equiv 33 \pmod{97}$.

Take $f(x) = 1 + 2x + 3x^2 + 4x^3$, of degree below 4. Its codeword is:

| $x$ | 1 | 64 | 22 | 50 | 96 | 33 | 75 | 47 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| $f(x)$ | 10 | 7 | 51 | 0 | 95 | 30 | 42 | 64 |

The prover commits to this list.

**First fold.** The verifier sends $\beta = 7$. The prover computes:

$$f_1(y) = (1 + 3y) + 7(2 + 4y) = 15 + 31y$$

on the domain of squares, $[1, 22, 96, 75]$, and commits to:

| $y$ | 1 | 22 | 96 | 75 |
| --- | --- | --- | --- | --- |
| $f_1(y)$ | 46 | 18 | 81 | 12 |

**Second fold.** The verifier sends $\beta = 11$. Now $f_1$ splits into $f_{even} = 15$ and $f_{odd} = 31$, so:

$$f_2 = 15 + 11 \cdot 31 = 356 \equiv 65 \pmod{97}$$

That is a constant, so the prover just sends 65.

![Folding: eight values fold into four, and then into a constant, 65](assets/notes/computational-proof-systems/fri-folding.svg)

**A query.** The verifier picks $x = 64$, so $-x = 33$ and $x^2 = 22$. The prover opens $f(64) = 7$ and $f(33) = 30$. The verifier computes, modulo 97:

$$\frac{7 + 30}{2} = 67 \qquad \frac{7 - 30}{2 \cdot 64} = 90 \qquad f_1(22) \stackrel{?}{=} 67 + 7 \cdot 90 \equiv 18$$

The opened value is $f_1(22) = 18$, so the check passes.

Next layer: $y = 22$, so $-y = 75$. The prover opens $f_1(22) = 18$ and $f_1(75) = 12$:

$$\frac{18 + 12}{2} = 15 \qquad \frac{18 - 12}{2 \cdot 22} = 31 \qquad 15 + 11 \cdot 31 \equiv 65$$

That matches the constant, so this query passes.

**Catching a cheater.** Suppose the prover changes one value, committing $f(50) = 1$ instead of 0. Now there are two options:

- **Fold it honestly.** The value at $y = 75$ in the next layer becomes 31 rather than 12. The last layer becomes $[65, 94]$, which isn't constant. The query above would catch this: it computes 94 from the opened values $18$ and $31$, instead of 65.
- **Hide it by keeping $f_1$ as it was.** A query at $x = 50$ now computes 31 from the first layer, but finds 12 opened in the second, so it fails.

Not every query lands on the problem, though. A query starting at $x = 1$ only touches the unchanged values, and passes either way. That is why the verifier makes many queries.

### How Much Checking Is Enough?

If the committed list is far from any low-degree polynomial, then each query catches the prover with a decent probability, and independent queries multiply. The number of queries for a target security level depends on the rate and on which security analysis is used. As a rough guide, for 100 bits at rate $\frac{1}{2}$:

- **Commonly used conjecture:** about 100 queries
- **A conservative simple bound** (catching with probability $\frac{1 - \rho}{2}$ per query): about 240 queries

Lower rates need fewer queries, at the cost of a larger codeword and slower proving. Real systems also fold by more than 2 at a time, and evaluate on a shifted domain (a coset) so that the codeword doesn't overlap the points where the computation is defined.

### The Non-Interactive Version

As usual, [Fiat-Shamir](/notes/cryptography-zkp/computational-proof-systems/interactive-and-non-interactive-proofs/) removes the conversation. Each $\beta$ is the hash of the transcript so far, including the Merkle roots, and so are the query positions. The order matters: the prover must commit to each layer before it can learn the next $\beta$.

### From a Low-Degree Test to a Commitment Scheme

FRI as described tests the degree. To use it as a polynomial commitment, the prover also needs to show an evaluation, $f(z) = v$. The same trick as KZG applies. If $f(z) = v$, then this is a polynomial, of degree one less:

$$q(x) = \frac{f(x) - v}{x - z}$$

If the claim is false, the division doesn't come out clean, and $q$ isn't close to a low-degree polynomial. So the prover runs FRI on $q$, and the verifier computes each value of $q$ it needs from the opened values of $f$.

### FRI Compared with KZG

| | KZG | FRI |
| --- | --- | --- |
| Trusted setup | Yes | No |
| Relies on | Elliptic curve pairings | Hash functions |
| Post-quantum | No | Believed to be, if the hash is |
| Proof size | Very small and constant | Larger, growing with $\log^2 d$ (often tens of kilobytes or more) |
| Verifier | A few pairings | Many hashes and small field operations |

Neither is simply better. FRI is the commitment behind STARKs and many fast modern provers, while KZG wins where tiny proofs matter most, such as verification on a blockchain.

### Summary

1. **Stretch** the polynomial onto a large domain, so cheating must be widespread.
2. **Commit** with a Merkle tree.
3. **Fold** with random challenges until only a constant is left.
4. **Query** random positions, to check each fold was done honestly.

### Further Reading

- [Fast Reed-Solomon Interactive Oracle Proofs of Proximity](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ICALP.2018.14), the original paper by Ben-Sasson, Bentov, Horesh and Riabzev
- [STARKs, Part II: Thank Goodness It's FRI-day](https://vitalik.eth.limo/general/2017/11/22/starks_part_2.html) by Vitalik Buterin
- [A summary on the FRI low degree test](https://eprint.iacr.org/2022/1216) by Ulrich Haböck, for the security analysis
