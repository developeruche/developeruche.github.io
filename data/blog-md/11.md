# How ZK-Rollups Work After EIP-4844: From `calldata` to Blobs

The Ethereum Dencun upgrade, powered by **EIP-4844 (Proto-Danksharding)**, marks a fundamental shift in how Layer 2 rollups achieve scalability. This update introduces a new, cost-effective way to post data on-chain, moving away from the expensive `calldata` method to a new system: **"blobs."**

For ZK-Rollups, this isn't just a simple swap. It requires a new cryptographic architecture to prove that the data processed off-chain is the same data posted in these new blobs. This article breaks down the problem, the EIP-4844 solution, and the clever cryptographic trick ZK-rollups now use.



### The Old Bottleneck: Data Availability via `calldata`

To maintain security and allow anyone to reconstruct the L2 state (a property called **data availability** or DA), rollups must post all their transaction data to the L1 (Ethereum).

* **Before EIP-4844:** The only place to do this was in a transaction's `calldata`.
* **The Problem:** This was extremely expensive. `calldata` is processed by all Ethereum nodes and competes for the same block space as L1 transactions. For many rollups, this DA cost accounted for over 80% of their total user transaction fees.

### The EIP-4844 Solution: Blob-Carrying Transactions

EIP-4844 introduces **blob-carrying transactions**. A blob is a large (~128 KB) packet of data designed specifically for rollup DA.

Here's what makes blobs a game-changer:
* **Cheap:** Blobs have a separate fee market (blob gas), so they don't compete with regular L1 transactions.
* **Temporary:** Blob data is pruned from L1 nodes after a few weeks (e.g., ~18 days). This is long enough for DA, but it avoids permanently bloating the Ethereum state.
* **Opaque to the EVM:** This is the most crucial part. The EVM **cannot read the data inside a blob**. Instead, the execution layer only has access to a cryptographic commitment to the blob.

This commitment is not a simple hash. EIP-4844 uses **KZG (Kate-Zarankiewicz-Goldwasser) commitments**. The L1 contract sees a `versioned_hash` (derived from the blob's KZG commitment) and can get this hash using the new `blobhash` opcode.


### The New Challenge for ZK-Rollups: The "Consistency Check"

This "opaque" nature of blobs creates a new challenge for ZK-Rollups.

* **The Old Way (with `calldata`):**
    1.  A ZK-Rollup posted its transactions to `calldata`.
    2.  The L1 verifier contract would **hash** this `calldata` (e.g., using `keccak256`).
    3.  This hash was passed into the ZK-circuit as a **public input**.
    4.  The circuit would prove: "I correctly processed a batch of transactions that *also* hash to this exact public input." This linked the off-chain proof to the on-chain data.

* **The New Problem (with blobs):**
    1.  The rollup posts a blob.
    2.  The L1 contract only has the `versioned_hash` (a KZG commitment).
    3.  The ZK-circuit has the raw blob data.

How can the circuit prove that its raw data is the *exact same data* represented by the `versioned_hash` on L1? This is the **blob consistency check**, also known as a **proof of equivalence**.


### The Solution: Polynomials and Precompiles

The solution is a clever cryptographic protocol that uses the fact that KZG commitments are based on **polynomials**.

The data in a blob is interpreted as a polynomial, let's call it `p(x)`. The KZG commitment is a commitment to this polynomial. To prove that the blob data used in the ZK-circuit is the same as the one committed to on L1, we use the **Schwartz-Zippel Lemma**. This lemma states that if two polynomials are different, they will only evaluate to the same value at a random point `z` with a very low probability.

So, the new process becomes a two-step verification:

#### Step 1: Verify the L1 Commitment (Point Evaluation Precompile)

EIP-4844 introduces a new precompile at address `0x0A` called the **`point_evaluation_precompile`**.

This precompile's job is to verify a KZG proof. The ZK-Rollup's L1 contract calls this precompile and essentially asks it: "For the blob represented by this `versioned_hash`, does its polynomial `p(x)` equal `y` when evaluated at point `z`?"

`precompile.verify(versioned_hash, z, y, kzg_proof)`

If the precompile returns `true`, the L1 contract now trusts that `(z, y)` is a valid evaluation of the blob's polynomial.

#### Step 2: Verify the ZK-Circuit's Data (In-Circuit Evaluation)

Now, the ZK-circuit (off-chain) must prove it's working with the same data.
1.  The circuit takes the **raw blob data** as a private input (witness).
2.  It also takes `z` and `y` (from Step 1) as **public inputs**.
3.  **Inside the circuit**, it reconstructs the *exact same* polynomial `p(x)` from the raw blob data.
4.  It then evaluates this polynomial at the point `z`.
5.  Finally, it asserts that its result **equals** `y`.

If `p_circuit(z) == y`, and the L1 precompile has already confirmed that `p_blob(z) == y`, we have cryptographically proven that the circuit's polynomial and the blob's polynomial are identical. The consistency check is complete!


### The Final Hurdle: Non-Native Field Arithmetic

There's one last, highly technical complication. Cryptography runs on specific elliptic curves, and these curves operate over different mathematical "fields."

* EIP-4844 (Blobs/KZG) uses the **BLS12-381** curve.
* Most ZK-Rollups (and Ethereum's existing precompiles) use the **BN254** curve.

This means the ZK-circuit (running on BN254) must perform polynomial math for the blob (which is defined over BLS12-381). This is called **non-native field arithmetic**, and it is computationally very expensive.

Rollup teams must implement complex circuits (e.g., using a barycentric formula) to perform this BLS12-381 math inside their BN254 ZK-proof. This is a significant engineering feat, but it's the final piece of the puzzle that makes the entire EIP-4844 system compatible with existing ZK-EVMs.


EIP-4844 is more than just "cheaper data." It fundamentally re-architects the data layer of Ethereum. For ZK-Rollups, this required moving away from simple hashing to a more complex system of polynomial equivalence.

By combining blob transactions, KZG commitments, the new `point_evaluation_precompile`, and advanced in-circuit non-native field arithmetic, ZK-Rollups can securely and verifiably use this new, ultra-cheap data source, paving the way for the next wave of L2 scalability.