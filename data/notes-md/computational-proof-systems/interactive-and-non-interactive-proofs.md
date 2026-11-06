### Introduction

Zero-knowledge proof systems come in two fundamental varieties: interactive and non-interactive protocols. Each has distinct characteristics and use cases that make it suitable for different applications in cryptography and secure computation.

### Interactive Zero-Knowledge Proofs

Interactive zero-knowledge proofs involve a back-and-forth dialogue between two parties:

- The **prover** (P), who possesses the secret information and wants to prove a statement
- The **verifier** (V), who challenges the prover and verifies the proof

**Key characteristics**

1. **Multiple rounds**: The proof consists of multiple rounds of communication between P and V.
2. **Challenge-response**: Each round typically involves a commitment from the prover, a challenge from the verifier, and a response from the prover.
3. **Randomness**: The verifier's challenges are randomly chosen.
4. **Completeness**: An honest prover can convince an honest verifier.
5. **Soundness**: A dishonest prover cannot convince a verifier, except with negligible probability.
6. **Zero knowledge**: The verifier learns nothing beyond the validity of the statement.

**Public-coin protocol example: graph 3-coloring**

Consider the following interactive protocol for proving that a graph G is 3-colorable without revealing the coloring:

```
Protocol steps:
1. P has a valid 3-coloring C of graph G
2. In each round:
   a. P randomly permutes the three colors (e.g., red→blue, blue→green, green→red)
   b. P commits to the color of each vertex using a cryptographic commitment scheme
   c. V randomly selects an edge (u,v) from G
   d. P opens the commitments to the colors of vertices u and v
   e. V checks that the openings are valid and that the two colors are different

Security parameters:
- If G has no valid 3-coloring, each round catches P with probability at least 1/|E|
- k rounds achieve a soundness error of at most (1-1/|E|)^k
```

This protocol exemplifies several key properties:

- It is public coin, because V's challenges are purely random and V keeps no secrets.
- It reveals nothing about the actual coloring. The verifier only ever sees two different colors, and fresh permutations stop the colors from being linked across rounds. This relies on the commitments being hiding.
- It can be repeated to reach any desired security level.

### Non-interactive Zero-Knowledge Proofs (NIZK)

Non-interactive zero-knowledge proofs eliminate the need for multiple rounds of interaction between the prover and verifier.

**Key features**

1. **Single message**: The entire proof is contained in one message from P to V.
2. **Some shared setup**: NIZKs need an assumption beyond plain interaction: either a common reference string (CRS), which may or may not need a trusted setup, or the random oracle model.
3. **Public verifiability**: Anyone with the verification key and the statement can verify the proof.
4. **Reusability**: The same proof can be verified multiple times by different parties.

**Construction methods**

1. **Fiat-Shamir transform**
   - Converts a public-coin interactive proof into a non-interactive one.
   - Replaces the verifier's challenges with the output of a cryptographic hash function, applied to everything sent so far. That includes the statement itself: leaving it out ("weak Fiat-Shamir") has led to real attacks.
   - Security is analysed in the random oracle model. Not every interactive protocol stays sound when transformed, because the prover can now try many challenges offline. Protocols with many rounds need a stronger property called round-by-round soundness.
2. **zk-SNARKs (Zero-Knowledge Succinct Non-Interactive Arguments of Knowledge)**
   - Provide succinct proofs (constant or polylogarithmic size).
   - Some require a trusted setup (Groth16, and PLONK with KZG). Others are transparent (STARKs).
   - Rest on cryptographic assumptions such as pairings or collision-resistant hash functions.
   - Many SNARKs are themselves built by applying Fiat-Shamir to an interactive protocol, so these two methods are not exclusive.

**Comparison table**

| Aspect | Interactive ZK | Non-interactive ZK |
| --- | --- | --- |
| Communication rounds | Multiple | Single |
| Setup requirements | Minimal | CRS or random oracle |
| Proof size | Depends on the protocol | Depends on the scheme; can be succinct |
| Real-time requirement | Yes | No |
| Public verifiability | No: the transcript only convinces the verifier who chose the challenges | Yes |

### Applications

1. **Interactive ZK use cases**
   - Authentication systems
   - Secure multiparty computation
   - Online zero-knowledge protocols
2. **NIZK use cases**
   - Blockchain and cryptocurrency systems
   - Digital signature schemes (Schnorr signatures are Fiat-Shamir applied to an interactive proof)
   - Anonymous credentials
   - Privacy-preserving smart contracts

### Technical Considerations

When choosing between interactive and non-interactive protocols, consider:

1. **Performance requirements**: proof generation time, verification time, communication complexity and storage requirements.
2. **Security requirements**: trusted setup assumptions, cryptographic assumptions and the required security level.
3. **System constraints**: network latency tolerance, storage limitations and real-time interaction capabilities.
