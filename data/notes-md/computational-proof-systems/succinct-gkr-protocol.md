## Making the GKR Protocol Succinct with Multilinear KZG Commitments

In the world of verifiable computation, ensuring that a computation was performed correctly without re-executing it is a game-changer, especially for large datasets or complex circuits. The GKR protocol, named after Goldwasser, Kalai and Rothblum, is a well-known interactive proof system that achieves this goal. However, the plain protocol leaves the verifier with one job that grows with the computation: it has to read the whole input. In this article, I share my findings on integrating the multilinear KZG polynomial commitment scheme into GKR, an approach I've implemented in Rust.

### Introduction to Verifiable Computation and the GKR Protocol

Verifiable computation allows a prover to convince a verifier that a computation, say evaluating a circuit, was performed correctly, without the verifier needing to redo the work. The GKR protocol is particularly effective for this, as it verifies computations layer by layer using the sum-check protocol. It works on arithmetic circuits, where gates perform addition or multiplication over a finite field.

In the standard GKR protocol, the prover works through the circuit's layers, starting from the output and moving back to the inputs. For each layer, the prover runs a sum-check and sends two evaluations of the next layer. At the end, the verifier evaluates the multilinear extension of the *input* at two random points, to confirm the final claim. This takes time linear in the input size, and it means the verifier must hold the whole input.

A *succinct* proof system aims to keep the proof small, ideally polylogarithmic in the computation size, with efficient verification. Polynomial commitments remove the input from the verifier's work, and Fiat-Shamir removes the interaction.

### Background: Understanding the Components

**The GKR protocol**

The GKR protocol operates on an arithmetic circuit with layers of gates. Each layer's values are expressed as a multilinear polynomial, and the protocol verifies these polynomials recursively:

- **Output layer:** The prover asserts the circuit's output, represented as a multilinear extension $w_0(x)$.
- **Intermediate layers:** For each layer $i$, the prover uses the sum-check protocol to reduce a claim about $w_i(x)$ to evaluations of the next layer's polynomial $w_{i+1}(x)$.
- **Input layer:** The verifier checks the final evaluations against the circuit's input.

The sum-check protocol reduces a claimed sum over a polynomial to one evaluation at a random point, and the random points are chosen via a Fiat-Shamir transcript for non-interactivity. In each layer, the prover sends the evaluations $w_{i+1}(r_b)$ and $w_{i+1}(r_c)$.

**The multilinear KZG polynomial commitment scheme**

The KZG (Kate-Zaverucha-Goldberg) commitment scheme allows a prover to commit to a polynomial and later open it at specific points, with the verifier checking these openings efficiently. The [multilinear version](/notes/cryptography-zkp/computational-proof-systems/multilinear-kzg/) is tailored to polynomials over multiple variables, making it a natural fit for GKR, where the layer polynomials are multilinear extensions of circuit values.

In this scheme:

- **Commitment:** Given a multilinear polynomial $p(x_1, \ldots, x_n)$ and a structured reference string (SRS) from a trusted setup, the prover computes a single group element in a pairing-friendly elliptic curve group ($\mathbb{G}_1$).
- **Opening:** To prove $p(z) = v$ at the point $z$, the prover generates an opening proof with one group element per variable, so $n$ elements.
- **Verification:** The verifier uses the commitment, the point $z$, the value $v$ and the opening proof to check consistency, using $n + 1$ pairings.

### The Succinct GKR Protocol: How It Works

The idea is to replace the one thing the verifier had to hold, the input, with a commitment to it. Everything else in GKR stays the same.

**Protocol steps**

1. **Commitment to the input:**
   - The prover interpolates the circuit's input into a multilinear polynomial $w_{in}(x)$.
   - Using multilinear KZG and an SRS, the prover computes a commitment $C_{in}$.
   - This commitment is appended to the Fiat-Shamir transcript, so that the challenges depend on it.
2. **Layer-by-layer reduction:**
   - Start with the output layer's polynomial $w_0(x)$, evaluated at a random point $n_r$ from the transcript.
   - For each layer $i$, use the sum-check protocol to reduce the claim about $w_i$ to the evaluations of $w_{i+1}$ at $r_b$ and $r_c$, which the prover sends.
   - Combine those two evaluations into one claim for the next layer, using random $\alpha$ and $\beta$ from the transcript.
3. **Openings at the input layer:**
   - For the final points $r_b$ and $r_c$, the prover computes $w_{in}(r_b)$ and $w_{in}(r_c)$, with a KZG opening proof for each.
   - These openings and proofs are part of the final proof.
4. **Verification at the input layer:**
   - The verifier uses KZG to check both openings against $C_{in}$.
   - It computes the expected claim $\alpha \cdot w_{in}(r_b) + \beta \cdot w_{in}(r_c)$, and checks that it equals the final claim.

**What this does and doesn't make succinct**

Compare the two versions, for a circuit of depth $d$ and at most $S$ gates per layer, with $n$ inputs:

| | Standard GKR | With multilinear KZG |
| --- | --- | --- |
| Sum-check data per layer | $O(\log S)$ field elements | $O(\log S)$ field elements |
| Total proof, sum-check part | $O(d \log S)$ | $O(d \log S)$ |
| Input | Verifier holds all $n$ values | One commitment |
| Input check | $O(n)$ field operations | Two openings: $O(\log n)$ group elements and pairings |

So the proof stays linear in the depth. What improves is the input check, from linear to logarithmic. The whole proof is polylogarithmic in the circuit's size as long as the depth is small compared to that size, which is the setting GKR targets.

One cost remains. The verifier still needs $add_i$ and $mul_i$ at random points. For a circuit with regular structure this can be fast, but in general, including in this implementation, the verifier builds those polynomials from the circuit, which takes time proportional to the circuit's size. Making verification fully succinct for arbitrary circuits would also need commitments to the wiring.

### Implementation in Rust

I've implemented this in Rust, extending the standard GKR protocol: [`arks/snarks/succinct_gkr_protocol`](https://github.com/developeruche/cryptography-n-zk-research/tree/main/arks/snarks/succinct_gkr_protocol). Here's a look at the key differences:

**Standard GKR (snippet)**

```rust
// In prove:
w_i_b.push(eval_w_i_b);
w_i_c.push(eval_w_i_c);
// In verify:
let w_in_b = w_in.evaluate(&last_rand_b).unwrap();
let w_in_c = w_in.evaluate(&last_rand_c).unwrap();
let expected_claim = last_alpha * w_in_b + last_beta * w_in_c;
```

The verifier recomputes the input evaluations from the input itself.

**Succinct GKR (snippet)**

```rust
// In prove (last layer):
let (point_evaluation_w_last_b, proof_w_last_b) =
    MultilinearKZG::open(&srs, &w_i_mle, &last_rand_b);
let (point_evaluation_w_last_c, proof_w_last_c) =
    MultilinearKZG::open(&srs, &w_i_mle, &last_rand_c);
proof_b = SuccinctGKRMultilinearKZGOPenningProof {
    opening: point_evaluation_w_last_b,
    opening_proof: proof_w_last_b,
};
proof_c = SuccinctGKRMultilinearKZGOPenningProof {
    opening: point_evaluation_w_last_c,
    opening_proof: proof_w_last_c,
};

// In verify:
let w_in_b_opening_verification = MultilinearKZG::verify(
    &srs,
    &input_poly_commitment,
    &last_rand_b,
    &proof.w_i_b_last_proof.opening,
    &proof.w_i_b_last_proof.opening_proof,
);
let w_in_c_opening_verification = MultilinearKZG::verify(
    &srs,
    &input_poly_commitment,
    &last_rand_c,
    &proof.w_i_c_last_proof.opening,
    &proof.w_i_c_last_proof.opening_proof,
);
let expected_claim = last_alpha * proof.w_i_b_last_proof.opening
    + last_beta * proof.w_i_c_last_proof.opening;
```

The prover sends KZG openings, and the verifier checks them against the commitment, without holding the input.

**Limitations of this implementation**

This code is for learning, and it has a soundness gap to fix before relying on it. For every layer after the first, the verifier runs the sum-check's round checks, but it never performs the sum-check's final check. That is the step connecting the sum to the circuit, where it should confirm that

$$
\begin{aligned}
\text{claimed sum} = {} & \big(\alpha\, add_i(r_b, b^*, c^*) + \beta\, add_i(r_c, b^*, c^*)\big)(w_b + w_c) \\
& + \big(\alpha\, mul_i(r_b, b^*, c^*) + \beta\, mul_i(r_c, b^*, c^*)\big)\, w_b\, w_c
\end{aligned}
$$

where $b^*$ and $c^*$ are that sum-check's random challenges, and $w_b$ and $w_c$ are the values the prover sent for the next layer. Without it, those layers aren't tied to the circuit at all. I confirmed this with a forged proof: for a circuit whose true output is 100, a proof claiming 999 was accepted. The standard GKR verifier in this repo has the same loop. Separately, each sum-check samples its challenges from its own fresh transcript rather than the shared one, and in a production system every challenge should depend on everything before it.

### A Simple Example

Consider a circuit with two layers of gates:

- **Input layer:** $x_1 = 2,\ x_2 = 3,\ x_3 = 4$. An input layer needs a power-of-two size, so it is padded with a zero: $[2, 3, 4, 0]$.
- **Layer 1:** $g_1 = x_1 + x_2 = 5$ and $g_2 = x_2 \cdot x_3 = 12$.
- **Output layer:** $o = g_1 \cdot g_2 = 60$.

**Layer polynomials.** Layer 1 has two values, so its multilinear extension has one variable: $w_1(x) = 5 + 7x$, which gives $w_1(0) = 5$ and $w_1(1) = 12$. The input layer is a polynomial in two variables, $w_{in}$, with values $[2, 3, 4, 0]$ on the hypercube.

**First reduction.** The output gate multiplies gates 0 and 1 of layer 1, so $mul_0(b, c) = (1-b)c$, and the sum over the hypercube is $w_1(0) \cdot w_1(1) = 60$. The sum-check ends at random points. Say $r_b = 2$ and $r_c = 3$. The prover then sends $w_1(2) = 19$ and $w_1(3) = 26$. Note that these are evaluations at *random* points, not the gate values 5 and 12.

**Second reduction.** The verifier picks random $\alpha, \beta$, and the new claim is $\alpha \cdot 19 + \beta \cdot 26$. A second sum-check reduces it to evaluations of the input polynomial, at two new random points.

**The difference at the end.**

- **Standard GKR:** The verifier computes both evaluations of $w_{in}$ from the input $[2, 3, 4, 0]$.
- **Succinct GKR:** The verifier holds only the commitment $C_{in}$. The prover sends both evaluations, with two KZG openings of two group elements each (one per variable).

The proof size in both cases is dominated by the two sum-checks and the layer evaluations.

### Benefits and Trade-offs

**Benefits**

- **The input stays out of the verifier's work:** It needs one commitment rather than all $n$ values.
- **Non-interactive:** With Fiat-Shamir, the proof is a single message.

**Trade-offs**

- **Trusted setup:** KZG requires an SRS, typically from a trusted setup. A breach compromises soundness.
- **Prover overhead:** Generating KZG commitments and openings adds prover work.
- **No zero knowledge:** GKR's messages and the openings reveal information about the values, so this is a succinct argument, not yet a zero-knowledge one.

Using a transparent multilinear commitment scheme, such as one built on hash functions, would remove the trusted setup, at the cost of larger proofs.

By integrating the multilinear KZG commitment scheme into the GKR protocol, the verifier checks the input through a commitment instead of reading it. Future work could fix the gap above, optimize the implementation, explore zero-knowledge variants, or replace the trusted setup with more flexible alternatives.
