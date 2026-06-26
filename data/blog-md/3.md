# Jagged Multilinear Extension (Stacked MLE)



In the quest to make Zero-Knowledge Virtual Machines (zkVMs) performant enough for real-time applications like proving Ethereum blocks within the 12-second slot time (`real time proving`) memory efficiency is paramount. A major bottleneck in modern proof systems is the "Rectangular Constraint": the mathematical requirement that execution traces be perfect rectangles with power-of-two dimensions, but real computation traces are inherently irregular. When proving the execution of a complex program, different computational units operate at vastly different scales. The CPU might execute millions of operations while the hash function runs only thousands of times. Traditional approaches force us to pad these irregular traces into perfect rectangles, wasting massive amounts of memory and computation time.

Jagged Multilinear Extensions offer an elegant solution. By maintaining a dense, packed representation of actual data while preserving the mathematical fiction of a 2D table, we achieve both computational efficiency and cryptographic soundness. This article explores the theory, implementation, and practical impact of this technique.

This article was inspired by the paper [Jagged Polynomial Commitments (or: How to Stack Multilinears)](https://eprint.iacr.org/2025/917.pdf) by Succinct labs. After understanding the concepts presented here, the paper is an excellent next step. It rigorously formalizes how to transform any MLE-based polynomial commitment scheme into its jagged counterpart, providing security proofs and analysis that complement the practical focus of this article.




## Multilinear Extensions: Foundation of Modern ZK Systems

Before understanding the jagged optimization, we must first grasp what multilinear extensions are and why they matter in zero-knowledge cryptography.

### What is a Multilinear Polynomial?

A multilinear polynomial is a polynomial in multiple variables where each variable appears with degree at most 1. For example, $f(x, y, z) = 3xy + 2xz + yz$ is multilinear, while $g(x, y) = x^2y + xy$ is not (due to the $x^2$ term).

### From Boolean Functions to Field Extensions

Consider a function that maps Boolean inputs to field elements: $f: \{0, 1\}^m \to \mathbb{F}$. This function is defined only at $2^m$ discrete points corresponding to the Boolean hypercube. The multilinear extension $\tilde{f}$ extends this function to the entire field: $\tilde{f}: \mathbb{F}^m \to \mathbb{F}$.

**Formal Definition**

For every function $f: \{0,1\}^m \to \mathbb{F}$, there exists a unique multilinear polynomial $\tilde{f}: \mathbb{F}^m \to \mathbb{F}$ such that:

1. $\tilde{f}$ is multilinear (each variable has degree at most 1)
2. $\tilde{f}$ agrees with $f$ on the Boolean hypercube: $\tilde{f}(b) = f(b)$ for all $b \in \{0,1\}^m$

The multilinear extension can be expressed explicitly as:

$$\tilde{f}(z) = \sum_{b \in \{0,1\}^m} \text{eq}(z, b) \cdot f(b)$$

where $z = (z_1, z_2, \ldots, z_m) \in \mathbb{F}^m$ is an arbitrary point and $\text{eq}(z, b)$ is the equality indicator function.

### The Equality Polynomial

The equality indicator function is defined as:

$$\text{eq}(z, b) = \prod_{i=1}^{m} \text{eq}_1(z_i, b_i)$$

where the univariate equality indicator is:

$$\text{eq}_1(z_i, b_i) = z_i \cdot b_i + (1 - z_i) \cdot (1 - b_i)$$

This function acts as an interpolating factor. When $z_i = b_i$, we have $\text{eq}_1(z_i, b_i) = 1$. When $z_i \neq b_i$ (and both are Boolean), we have $\text{eq}_1(z_i, b_i) = 0$. Therefore, $\text{eq}(z, b)$ serves as a Lagrange basis polynomial that equals 1 when $z = b$ and equals 0 when $z$ equals any other Boolean vector.

### Why MLEs Matter in Zero-Knowledge

Multilinear extensions are crucial for modern ZK systems for several reasons:

**Succinct representation**: Instead of committing to exponentially many evaluations, we commit to a single polynomial that encodes all the data.

**Efficient evaluation**: Using techniques like the sumcheck protocol, we can evaluate MLEs at random points with only polynomial overhead, enabling succinct proofs.

**Compositional properties**: MLEs preserve arithmetic structure, making them ideal for expressing computational constraints.

**Direct evaluation efficiency**: Given an m-variate function and query point $z \in \mathbb{F}^m$, we can compute $\tilde{f}(z)$ using only $2^{m+1}$ multiplications, $2^m$ additions, and $O(m)$ space.

In systems like PLONK, STARKs, and modern zkVMs, execution traces are encoded as MLEs, constraints are expressed as multilinear polynomials, and the sumcheck protocol verifies these relationships efficiently.

[learn more](https://hackmd.io/@0xdeveloperuche/BJ-hB-Lb-e)


## The Jagged Structure of zkVM Traces

Real-world zkVMs don't produce neat rectangular tables. Understanding this mismatch between mathematical requirements and computational reality is key to appreciating the jagged optimization.

### Anatomy of a zkVM Execution

Consider proving the execution of a program that:

- Performs 1,000,000 basic CPU operations (ADD, MUL, SUB, etc.)
- Makes 500 bitwise operations (AND, XOR, shifts)
- Computes 20,000 Keccak hash operations
- Accesses memory 50,000 times

In a typical zkVM architecture like RISC Zero, SP1, or Nexus, each operation type gets its own "chip" or column in the execution trace:


| CPU Chip (1M rows) | Bitwise (500) | Keccak Chip (20K rows) | Memory Chip (50K rows) |
|-------------------|--------------|------------------------|------------------------|
| ADD 5,7 → 12      | XOR …         | STATE[0] …             | LOAD 0x100             |
| MUL 3,4 → 12      | AND …         | STATE[1] …             | STORE 0x200            |
| SUB 9,2 → 7       | SHL …         | ABSORB …               | LOAD 0x104             |
| …                 | …             | …                      | …                      |
| (1M ops)          | (500)         | (20K)                  | (50K)                  |


### The Rectangular Constraint Problem

Traditional MLE-based proof systems require tables to be rectangular with power-of-two dimensions. To use standard techniques, every column must be padded to match the longest:


Required shape: 2^20 × 4 = 1,048,576 rows × 4 columns

Actual data:
- CPU:     1,000,000 rows (95% of max)
- Bitwise:       500 rows (0.05% of max)  ← 99.95% waste!
- Keccak:     20,000 rows (2% of max)     ← 98% waste!
- Memory:     50,000 rows (5% of max)     ← 95% waste!

Total elements: 4,194,304
Non-zero elements: 1,070,500
Wasted space: 3,123,804 (74.5% waste!)


This padding has devastating consequences:

- **Memory**: The prover must allocate 3× more RAM than needed
- **Commitment time**: Polynomial commitments scale with table size
- **Proving time**: Many operations iterate over all rows

For a zkVM proving Ethereum block execution, this could mean 32 GB RAM instead of 10 GB, and 45-second proving time instead of 15 seconds the difference between real-time proving and impractical delays.

## One Giant MLE for All Traces

The ideal scenario would be to represent all execution traces as a single, unified multilinear extension and perform a single polynomial commitment on it. This would give us:

**Unified proof structure**: One commitment for the entire execution trace
**Batch verification**: Verify all chips together in a single protocol
**Reduced overhead**: Eliminate redundant cryptographic operations per chip

However, the rectangular padding problem stands in the way. Let's see this with a concrete example.

### A Minimal Example

Consider a tiny trace table with 3 columns:

- **Col 0 (CPU)**: Used heavily (4 rows): $[A, B, C, D]$
- **Col 1 (Memory)**: Used moderately (2 rows): $[E, F]$
- **Col 2 (Keccak)**: Used barely (1 row): $[G]$

#### The Padded (Wasteful) Form

In a standard system padded to the maximum length of 4:

| Row | Col 0 | Col 1 | Col 2 |
|-----|-------|-------|-------|
| 0   | $A$   | $E$   | $G$   |
| 1   | $B$   | $F$   | 0 (pad) |
| 2   | $C$   | 0 (pad) | 0 (pad) |
| 3   | $D$   | 0 (pad) | 0 (pad) |

- **Total committed size**: 12 elements
- **Wasted space**: 5 zeros (≈41%)

As the number of chips increases and the disparity in their usage grows, this waste becomes untenable. We need a way to commit to just the actual data while maintaining the mathematical properties required for efficient proving.

## Jagged/Stacked MLE: The Solution
The "Jagged" approach allows the prover to compress these varying columns into a single, dense 1D vector (List), while mathematically pretending they are still in a 2D table.

#### The Mechanics
1.  **Dense Representation ($q$):** Instead of padding columns with zeros, you take the columns as they are (variable lengths) and stack them on top of each other into one long vector.
2.  **The Metadata Vector ($t$):** You create a small helper vector $t$ that records the cumulative length of the columns. This tells you where one column ends and the next begins.
3.  **The Virtual Mapping:** You define functions (`row` and `col`) that allow the Verifier to translate an index from the 1D stack back to its original 2D coordinate.

The core insight of Jagged MLEs is deceptively simple: store data densely in a 1D vector, but maintain metadata that allows us to reason about it as if it were still a 2D table.

### The Dense Representation

Instead of padding columns with zeros, we stack them head-to-tail in a single dense vector:

```rust
// Traditional (padded):
let padded_table: Vec<Vec<F>> = vec![
    vec![a, b, c, d],    // CPU column (4 elements)
    vec![e, f, 0, 0],    // Memory (2 + 2 padding)
    vec![g, 0, 0, 0],    // Keccak (1 + 3 padding)
];
// Total: 12 elements (5 wasted)

// Jagged (dense):
let q: Vec<F> = vec![a, b, c, d, e, f, g];
// Total: 7 elements (0 wasted)
```

### The Metadata Vector

To reconstruct the 2D view, we track where each column ends using cumulative positions:

```rust
let column_lengths = vec![4, 2, 1];  // Actual data per column

// Compute cumulative positions
let mut metadata = Vec::new();
let mut offset = 0;
for &len in &column_lengths {
    offset += len;
    metadata.push(offset);
}
// metadata = [4, 6, 7]
```

This metadata vector $t$ serves as boundary markers:

- Indices 0–3 belong to column 0
- Indices 4–5 belong to column 1
- Index 6 belongs to column 2

### The Mapping Functions

Given an index $i$ in the dense vector $q$, we need functions to determine its original 2D coordinates.

**Column Finder**: $\text{col}(i) = \min_k \{ t_k > i \}$

Find the first boundary that exceeds our index:

```rust
pub fn col(&self, index: usize) -> Option<usize> {
    self.metadata.iter()
        .position(|&boundary| index < boundary)
}
```

**Row Finder**: $\text{row}(i) = i - t_{k-1}$ where $k = \text{col}(i)$

Subtract the previous column's endpoint:

```rust
pub fn row(&self, index: usize) -> usize {
    let col_index = self.col(index).unwrap();
    if col_index == 0 {
        index  // First column starts at 0
    } else {
        index - self.metadata[col_index - 1]
    }
}
```

## Jagged MLE by Example

Let's trace through a complete example to see how the mapping works in practice.

### Setup

Using our 3-column example:

```
Columns: [A,B,C,D], [E,F], [G]
Dense q: [A, B, C, D, E, F, G]
         0  1  2  3  4  5  6
Metadata t: [4, 6, 7]
```

### Tracing Index 5

Suppose we want to find the original (row, column) position of index 5 in the dense vector.

**Step 1: Find the Column**

- Is $5 < 4$? No
- Is $5 < 6$? **Yes!**
- Therefore, $\text{col}(5) = 1$

**Step 2: Find the Row**

- Current index: $i = 5$
- Previous boundary: $t_0 = 4$
- Row = $5 - 4 = 1$

**Result**: Index 5 maps to (row=1, col=1), which is element **F** ✓

### Complete Mapping Table

| Dense Index | Column | Row | Element |
|-------------|--------|-----|---------|
| 0 | 0 | 0 | A |
| 1 | 0 | 1 | B |
| 2 | 0 | 2 | C |
| 3 | 0 | 3 | D |
| 4 | 1 | 0 | E |
| 5 | 1 | 1 | F |
| 6 | 2 | 0 | G |

### The Mathematical Core: MLE Evaluation

The crucial innovation is how we evaluate the MLE using only the dense representation.

**Traditional MLE evaluation** (rectangular):

$$\hat{p}(z_r, z_c) = \sum_{r \in \{0,1\}^n} \sum_{c \in \{0,1\}^k} p[r][c] \cdot \text{eq}(r, z_r) \cdot \text{eq}(c, z_c)$$

This requires iterating over the entire rectangular grid, including all those zeros.

**Jagged MLE evaluation** (dense):

$$\hat{p}(z_r, z_c) = \sum_{i \in \{0,1\}^m} q[i] \cdot \text{eq}(\text{row}(i), z_r) \cdot \text{eq}(\text{col}(i), z_c)$$

The key insight: zeros contribute nothing to the sum ($0 \times \text{anything} = 0$). We can iterate only over the dense vector, computing the logical (row, col) coordinates on the fly.

**The Benefit**: For our example, we do 7 operations instead of 12. In real zkVMs with millions of rows and 74% waste, we might do 1 million operations instead of 4 million a 4× speedup!

## Rust Implementation

Let's build a production-ready Jagged MLE implementation.

### Core Data Structure

```rust
use ark_ff::Field;

pub struct StackedMle<F: Field> {
    /// The is a dense representation of the columns
    pub q: Vec<F>,
    /// Represent the start points for each columns
    pub metadata: Vec<usize>,
}

```

### Construction from Jagged Columns

```rust
impl<F: Field> StackedMle<F> {
    pub fn new(columns: &[Vec<F>]) -> Self {
        let sum_of_len = columns.iter().map(|col| col.len()).sum::<usize>();
        let padded_len = sum_of_len.next_power_of_two();

        let mut q = columns.iter().flatten().copied().collect::<Vec<_>>();
        let mut metadata = Vec::new();
        let mut offset = 0;
        for col in columns.iter() {
            offset += col.len();
            metadata.push(offset);
        }

        if q.len() < padded_len {
            q.resize(padded_len, F::zero());
        }

        let m_len = metadata.len();
        metadata[m_len - 1] = padded_len;

        Self { q, metadata }
    }
}
```

### The Mapping Functions

```rust
impl<F: Field> StackedMle<F> {
    pub fn col(&self, index: usize) -> Option<usize> {
        let mut col = None;

        for (i, &val) in self.metadata.iter().enumerate() {
            if index < val {
                col = Some(i);
                break;
            }
        }

        col
    }

    pub fn row(&self, index: usize) -> usize {
        let col_index = self.col(index).unwrap();
        let rol_index = if col_index == 0 {
            index
        } else {
            index - self.metadata[col_index - 1]
        };

        rol_index
    }
}
```

### The Evaluation Function

```rust
impl<F: Field> StackedMle<F> {
    /// Evaluate the MLE at point (z_r, z_c)
    pub fn eval(&self, z_c: &[F], z_r: &[F]) -> F {
        let row_eq = eq_funcs(z_r);
        let col_eq = eq_funcs(z_c);

        let mut res = F::ZERO;
        for (i, &coeff) in self.q.iter().enumerate() {
            res += coeff * row_eq[self.row(i)] * col_eq[self.col(i).unwrap()];
        }

        res
    }
}
```

### Helper Functions

```rust
pub fn eq_1_func<F: Field>(z_i: F, b_i: F) -> F {
    z_i * b_i + (F::one() - z_i) * (F::one() - b_i)
}

pub fn eq_funcs<F: Field>(points: &[F]) -> Vec<F> {
    let bh = generate_hypercube_vec(points.len());
    let mut evals = Vec::with_capacity(bh.len());

    // Iterate over every point 'b' in the hypercube {0,1}^m
    for b in bh {
        let mut product_term = F::one();

        for (i, &bit) in b.iter().enumerate() {
            // If b_i = 1, term is z_i
            // If b_i = 0, term is (1 - z_i)
            let term = if bit == 1 {
                points[i]
            } else {
                F::one() - points[i]
            };

            product_term *= term;
        }
        evals.push(product_term);
    }

    evals
}

pub fn generate_hypercube_vec(m: usize) -> Vec<Vec<u8>> {
    if m >= 63 {
        panic!("m is too large for a vector-based hypercube");
    }
    let num_rows = 1 << m;
    let mut result = Vec::with_capacity(num_rows);

    for i in 0..num_rows {
        let mut row = Vec::with_capacity(m);
        for bit_index in (0..m).rev() {
            row.push(((i >> bit_index) & 1) as u8);
        }

        result.push(row);
    }

    result
}
```

[complete RUST code](https://github.com/developeruche/cryptography-n-zk-research/blob/main/primitives/polynomial/src/stacked_mle.rs)



### Concrete Impact

For our zkVM example with 74% waste:

**Traditional approach**:
- Table size: 4,194,304 elements (padded)
- Sumcheck rounds: 22 rounds (log 4M)
- Prover time: $22 \cdot 4M$ operations

**Jagged approach**:
- Dense vector size: 1,070,500 elements (actual data padded to next power of 2 ≈ 1,048,576)
- Sumcheck rounds: 20 rounds (log 1M)
- Prover time: $20 \cdot 1M$ operations

**Savings**: ~4× reduction in prover computation, 2 fewer rounds, 75% less memory.

Jagged Multilinear Extensions elegantly solve a fundamental inefficiency in modern zkVMs: the mismatch between rectangular cryptographic primitives and the irregular structure of real computation traces.

### Key Insights

**Separation of concerns**: Store data densely in a 1D vector, but reason about it logically as a 2D table. The metadata vector bridges these two views.

**Practical impact**: In production zkVMs, Jagged MLEs translate to 40-70% reduction in memory usage, 30-50% faster proving times, and enabling real-time proving for applications like Ethereum block execution.


Jagged MLEs are part of a wave of optimizations making SNARKs practical for complex computations. Combined with techniques like Lasso (lookup arguments), GKR (layered circuits), and folding schemes (Nova, ProtoStar), we're approaching the goal of provable general-purpose computation with minimal overhead.

For zkVM engineers, the message is clear: structure your data for the math, but don't let the math force wasteful structures. Jagged MLEs demonstrate that with careful engineering, **we can achieve both mathematical elegance and computational efficiency**.


## References

* **[Jagged Polynomial Commitments (or: How to Stack Multilinears)](https://eprint.iacr.org/2025/917.pdf)** – *Succinct Labs (2025)*
* **[Proofs, Arguments, and Zero-Knowledge](https://people.cs.georgetown.edu/jthaler/ProofsArgsAndZK.pdf)** – *Justin Thaler*
* **[Arkworks Rust Ecosystem](https://github.com/arkworks-rs/)** – *Arkworks Contributors*
* **[Complete Jagged MLE Implementation](https://github.com/developeruche/cryptography-n-zk-research/blob/main/primitives/polynomial/src/stacked_mle.rs)** – *Source Code*