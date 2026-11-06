Understanding the Keccak hash function and its variants. Rust implementation: [`hash-functions/keccak256`](https://github.com/developeruche/cryptography-n-zk-research/tree/main/hash-functions/keccak256).

### Output Lengths

The Keccak algorithm is standardized with 4 different output lengths:

| Output $n$ | Definition | Rate $r$ | Capacity $c$ |
| --- | --- | --- | --- |
| 224 | Keccak$[r = 1152, c = 448]_{224}$ | 1152 | 448 |
| 256 | Keccak$[r = 1088, c = 512]_{256}$ | 1088 | 512 |
| 384 | Keccak$[r = 832, c = 768]_{384}$ | 832 | 768 |
| 512 | Keccak$[r = 576, c = 1024]_{512}$ | 576 | 1024 |

- **$n$:** The output length.
- **$r$:** The bitrate, which determines how much data can be absorbed per block.
- **$c$:** The capacity, the remaining part of the internal state, which input is not written into directly. It determines the security level, helping to prevent collision and preimage attacks. Each variant here sets $c = 2n$.

Keccak and SHA-3 aren't quite the same thing. NIST's SHA-3 standard changed the padding by adding domain bits, so the outputs differ. Ethereum's `keccak256` uses the original padding:

- `keccak256("")` starts with `c5d24601...`
- `SHA3-256("")` starts with `a7ffc6f8...`

### The Sponge Function

Keccak is built from a sponge:

$$\text{Keccak}[r, c] \triangleq \text{Sponge}[\text{Keccak-}f[r + c],\ \text{pad10}^*\text{1},\ r]$$

![The sponge construction: message blocks are XORed into the rate part of the state, with the permutation f between them, and output blocks are read from the rate part](assets/notes/computational-proof-systems/keccak-sponge.svg)

**1. Padding the message $M$**

- Pad the message $M$ with the pattern $10^*1$, so that the result is a multiple of the bitrate $r$.
- Divide the padded message into $m = \frac{\text{padded message length}}{r}$ blocks, $P_0, P_1, P_2, \ldots, P_{m-1}$.
- A general rule: padding is always added, so if the original message length is already a multiple of $r$, a whole block's worth of padding is added.

**2. Absorbing phase**

Start with $S = 0^b$, where $b = r + c = 1600$ is the state size. For each block $P_i$:

- Pad the block to the state size: $P_i \| 0^{b - r}$
- XOR it into the state: $S = S \oplus (P_i \| 0^{b - r})$
- Apply the permutation: $S = f(S)$

**3. Squeezing phase**

Let $Z_0 = [S]_r$, the first $r$ bits of the state.

- If $|Z_0| \geq n$: the output is $[Z_0]_n$, the first $n$ bits.
- If $|Z_0| < n$: apply $S = f(S)$, take $Z_1 = [S]_r$, and let $Z = Z_0 \| Z_1$.

Squeezing continues until the output is at least $n$ bits long. All four variants above have $r \geq n$, so for them a single squeeze is enough.

### The Permutation $f$

$f$ is the permutation function, made of $n_r$ rounds of $R$.

- The state $S[w(5y + x) + z]$ is mapped to $a[x][y][z]$, where $x = 0, \ldots, 4$, $y = 0, \ldots, 4$ and $z = 0, \ldots, 2^l - 1$.
- We set $l = 6$, so that $w = 2^l = 64$ and $1600 = 5 \times 5 \times w$, and $n_r = 12 + 2l = 24$.

Each round is:

$$R = \iota \circ \chi \circ \pi \circ \rho \circ \theta$$

where, with all arithmetic over bits (addition is XOR):

$$\theta: \quad a[x][y][z] \leftarrow a[x][y][z] + \sum_{y'=0}^{4} a[x-1][y'][z] + \sum_{y'=0}^{4} a[x+1][y'][z-1]$$

$$\rho: \quad a[x][y][z] \leftarrow a[x][y][z - (t+1)(t+2)/2]$$

with $t$ satisfying $0 \leq t < 24$ and $\begin{pmatrix} 0 & 1 \\ 2 & 3 \end{pmatrix}^t \begin{pmatrix} 1 \\ 0 \end{pmatrix} = \begin{pmatrix} x \\ y \end{pmatrix}$ in $GF(5)^{2 \times 2}$, or $t = -1$ if $x = y = 0$.

$$\pi: \quad a[x][y] \leftarrow a[x'][y'], \quad \text{with} \quad \begin{pmatrix} x \\ y \end{pmatrix} = \begin{pmatrix} 0 & 1 \\ 2 & 3 \end{pmatrix} \begin{pmatrix} x' \\ y' \end{pmatrix}$$

$$\chi: \quad a[x] \leftarrow a[x] + (a[x+1] + 1)\, a[x+2]$$

$$\iota: \quad a \leftarrow a + RC[i_r]$$

In words:

1. **Theta (parity mixing):** Each bit is mixed with the parity of two other columns, so small changes in the input diffuse across the state.
2. **Rho (bitwise rotation):** Each lane is rotated by its own offset, spreading bits within lanes.
3. **Pi (lane permutation):** Lanes are moved to new positions. This is a linear rearrangement, which spreads bits across lanes.
4. **Chi (nonlinear layer):** This AND-XOR step is the only nonlinear one, and it defeats attacks based on solving linear equations.
5. **Iota (round constant injection):** Each round gets a different constant, which breaks the symmetry between rounds and across the state.

### Why Is Keccak a One-Way Hash Function?

A one-way function means that, given an output $h = H(m)$, it is computationally infeasible to find an input $m$ that produces it (preimage resistance). It is worth being precise about where this comes from, because it isn't that the steps above are hard to reverse.

**Keccak-$f$ itself is invertible.** It's a permutation, and each of its five steps has an inverse. Given a *whole* 1600-bit state, anyone can run it backwards.

**The attacker never gets a whole state.** That is the role of the capacity. The output reveals only part of the rate, and the $c$ capacity bits stay hidden. To run the permutation backwards from an output, an attacker would have to guess all the missing bits, which is at least $2^c$ possibilities for the capacity alone. A wrong guess gives nonsense, and nothing signals when a guess is right.

**The permutation makes those guesses useless.** Its 24 rounds of mixing and nonlinearity are designed so that the output behaves like a random function of the input, leaving no shortcut better than brute force. If the permutation is ideal, the sponge has a security level of up to $c/2$ bits, and for preimages of an $n$-bit output, at most $n$ bits.

So, for Keccak-256, finding a preimage costs about $2^{256}$ work and finding a collision about $2^{128}$. Note that this is computational security. Many inputs map to each output, so inverting isn't "impossible" in principle, just infeasible.
