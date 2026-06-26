# A Deep Dive into EIP-7928 and Block-Level Access Lists

Ethereum’s scaling roadmap has long been defined by a tension between state growth and execution throughput. While we often discuss modularity and L2s, the L1 execution layer remains bound by a fundamental constraint: **sequential processing dictated by unknown state dependencies.**

In this article, we dive into **EIP-7928: Block-Level Access Lists (BALs)**. This is not just a metadata optimization; it is a structural shift in how we decouple state access from execution, enabling parallel disk I/O, parallel EVM execution, and paving the way for efficient ZK-proving of L1 blocks.

### The IO Bottleneck and The "Unknown" State

To understand why BALs are necessary, we have to look at the lifecycle of a block verification today. When a validator receives a block, it is effectively flying blind.

1. **Sequential Dependency:** The validator cannot know which storage slots Transaction  will touch until Transaction  has finished executing.
2. **The IO penalty:** Every `SLOAD` is a potential cache miss, triggering a disk seek into the Merkle Patricia Trie (MPT).
3. **The Result:** We are forced to execute essentially single-threaded, interleaving IO waits with CPU bursts.

This model makes "state" a blocker for "compute." EIP-7928 proposes inverting this relationship by enforcing a **Block-Level Access List (BAL)**.

### EIP-7928 Specification

A BAL is a deterministic record of *every* account and storage slot accessed during the execution of a block, including the resulting state diffs.

Crucially, this is not a "hint"—it is a validity condition. If the BAL does not perfectly match the execution trace, the block is invalid.

#### The Data Structure (RLP)

Unlike the Consensus Layer’s shift to SSZ, EIP-7928 currently utilizes RLP (Recursive Length Prefix) encoding for the `ExecutionPayload` to maintain compatibility with existing EL infrastructure (like Geth/Reth).

The core unit is the `AccountChanges` list. A simplified view of the schema looks like this:

```python
AccountChanges = [
    Address,                    # 20 bytes
    List[SlotChanges],          # Storage writes/changes
    List[StorageKey],           # Read-only storage keys
    List[BalanceChange],        # Post-tx balances
    List[NonceChange],          # Post-tx nonces
    List[CodeChange]            # Deployed bytecode
]

```

The BAL introduces the concept of a `BlockAccessIndex`. This is a `uint16` that maps a state change to a specific point in the block lifecycle:

* **0:** Pre-execution (System contracts, e.g., EIP-2935 block hash history).
* **1..N:** The specific transaction index causing the change.
* **N+1:** Post-execution (Withdrawals, consolidations).

#### Handling The "Diffs"

The spec requires recording **post-transaction values**. This is a critical design choice.

* **Writes:** We record the `value_after`.
* **Reads:** We record the slot key.
* **Balances:** We record the *exact* post-transaction balance.

By including the `value_after` for every write, the BAL essentially functions as a stream of **state diffs**. This allows a node to update its state representation without necessarily re-executing the EVM, which is massive for "healing" or fast-syncing nodes.

### The Mechanism: From Sequential to Parallel

With a valid BAL in the block body, the execution pipeline transforms from `Sequential (IO + EVM)` to `Parallel IO + Parallel EVM`.

#### Phase 1: Parallel Prefetching

Before the EVM is even instantiated, the client parses the BAL. It collects every `Address` and `StorageKey` listed.

* **Action:** Fire off asynchronous disk reads for all keys simultaneously.
* **Result:** The "hot" state is loaded into memory. The cache is warm before execution starts.

#### Phase 2: Dependency Graph & Conflict Detection

Because the BAL maps accesses to specific Transaction Indices, we can construct a **conflict graph**.

* If  reads Slot  and  writes to Slot , and , they are disjoint.
* Disjoint transactions can be executed on separate cores.
* **Performance:** Historical analysis suggests 60-80% of transactions in a block have no state overlap. This allows for massive parallelization.

### The ZK & Low-Level Perspective

For those of us working on ZK-rollups or zkEVMs, EIP-7928 is particularly interesting.

**1. Accelerating Witness Generation:** 
In a ZK context (using zkVMs like SP1 or RISC Zero), the latency bottleneck is often the serial execution required to generate the witness (execution trace). Due to the sequential nature of the EVM, a prover currently must execute every transaction in a block, one by one, to determine which state slots are accessed even though ~80% of transactions are statistically disjoint. The current State Transition Function offers no guide to enforce or identify this independence upfront. BALs solve this by providing a deterministic dependency graph before execution begins. This allows zkVM guest programs to safely parallelize execution and even shard proof generation across independent transaction clusters, a safe, clean architectural shift that was previously impossible.

**2. Stateless Clients & Verkle:**
While not fully stateless (we aren't including the full Merkle proofs *in* the BAL to save bandwidth), this is a stepping stone. The `StorageChange` tuples act as the "leaves" that would be updated in a Verkle tree or a binary state tree.

**3. State Healing:**
The inclusion of `value_after` allows for "Executionless State Updates." A light client or a lagging node can apply the state transitions (balance updates, storage writes) purely by trusting the consensus verification of the BAL, without spinning up a heavy EVM stack.

### Engineering Challenges & Edge Cases

The specification is strict, and implementing this in Rust, Go or other languages requires handling nuanced edge cases:

* **Gas Checks vs. Access:** If a `CALL` fails due to an out-of-gas exception *before* accessing state, the target address must **not** be in the BAL. This implies the BAL generation must be tightly coupled with the EVM interpreter loop.
* **The "No-Op" Write:** If an SSTORE writes the same value that already exists, it is functionally a read. However, the EIP mandates that if it was an `SSTORE` opcode, it must be recorded, but implementations must be smart enough to distinguish actual state root changes.
* **Co-processor Overhead:** While we save on IO, we add overhead in hashing and verifying the BAL RLP. However, given an average BAL size of ~70KB (compressed), the bandwidth trade-off is negligible compared to the execution speedup.



EIP-7928 is a necessary modernization of the Ethereum block structure. By making state access explicit and deterministic, we move away from the single-threaded constraints of 2015 and toward a parallel, high-performance execution layer.

For client developers and ZK engineers, this reduces the "magic" required to execute a block. We no longer guess; we verify.

### References

* [EIP-7928 Specification](https://eips.ethereum.org/EIPS/eip-7928)
* [Block-level Access Lists - EthResearch](https://ethresear.ch/t/block-level-access-lists-bals/22331)
* [Block Accesss Lists - Website](https://blockaccesslist.xyz/)