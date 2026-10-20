> **Also on HackMD.** This note was first published on HackMD. If you would rather read it there, it is at [hackmd.io/@0xdeveloperuche/Hyls3QgP-e](https://hackmd.io/@0xdeveloperuche/Hyls3QgP-e).

## XMSS (Extended Merkle Signature Scheme)

### Hash-Based Cryptography Context

Hash-based cryptography provides a secure and reliable way of encrypting, decrypting, and verifying digital signatures, offering cryptographic solutions that can withstand attacks from quantum computers.

* **Foundation:** It relies on the cryptographic strength of hash functions and pseudo-random functions, which are well-understood and not known to be broken by quantum computers.
* **Mechanism:**
    * Establishes a mutual secret key using a key agreement protocol relying on hash functions.
    * Uses a Merkle signature scheme to sign and verify messages using the shared secret key.
    * The Merkle signature scheme uses a hash tree to generate a signature secure against both classical and quantum attacks.

### Stateful vs. Stateless

Hash-based signatures are divided into two categories:

* **Stateless:** (e.g., SPHINCS) Do not require keeping track of state but often have larger signature sizes.
* **Stateful:** (e.g., XMSS) Requires the storage of a secret-key state; the signing key changes after every signature.
    * **Crucial Constraint:** If an attacker obtains signatures of two different messages created using the same One-Time Signature (OTS) key, it becomes computationally feasible to create forgeries. Therefore, the state must be updated (index incremented) after every signature.

### Structure of XMSS

XMSS combines the Winternitz One-Time Signature (WOTS+) with a Merkle Tree structure.

* **Merkle Tree:** A binary hash tree of height $h$. The root node is the public key, and the leaves are the OTS key pairs.
* **WOTS+ (Winternitz One-Time Signature Plus):**
    * Used for the leaves of the tree to sign the actual messages.
    * Parameters:
        * $n$: Security parameter (message digest length).
        * $w$: Winternitz parameter (trade-off between speed and size).
        * $l$: The total number of blocks in a signature ($l_1$ message chains + $l_2$ checksum chains).

### Evolution: From Classical WOTS to WOTS+

Classical WOTS hash chains were deterministic and unkeyed, introducing several security issues:

1. **Chain Splicing / Multi-target Attacks:**
    * If an attacker observes multiple signatures, they may collect partial hash chains.
    * Because chains are not randomized, these partial chains can sometimes be combined.
    * This weakens security in multi-signature or adaptive settings.
2. **Unsustainability for Tree-based Schemes:**
    * When WOTS is used as a leaf signature in a Merkle tree, an attacker sees many WOTS public keys and signatures.
    * The lack of per-step domain separation becomes exploitable.

**The WOTS+ Solution:** WOTS+ fixes these problems by introducing randomness to every step of the hash chain.

* **Keyed Hashing:** Instead of hashing directly $x \to H(x)$, WOTS+ hashes using a bitwise XOR with a random value $r$ (and domain separators): $x \to H(x \oplus r)$.
* **Role of $r$:** $r$ is a public, deterministic random value unique to each chain index and step index. This ensures domain separation and mitigates multi-target attacks.

## Optimize XMSS Verification

### The Core Goal

The primary question addressed is: *"How can we maximize the verification speed of XMSS on embedded devices?"*

* **Context:** In IoT and embedded applications (e.g., vehicle-to-vehicle communication, secure boot), verification happens much more frequently than signing.
* **Resource Constraints:** Embedded devices (like ARM Cortex-M4) are constrained in memory and computing power, making verification efficiency critical.

### PZMCM / Winternitz Tuning

The optimization relies on a technique proposed by PZMCM (Perin et al.), which exploits the probabilistic nature of WOTS+ chain lengths.

* **Cost Analysis:** The cost of verifying a WOTS+ signature is largely determined by the values of the $l_1$ integers $h_1, \dots, h_{l_1}$ derived from the message digest.
    * Verification requires completing the hash chains.
    * The number of hash computations is $\sum (w - 1 - h_i)$.
    * **Key Insight:** As $h_i$ increases (the value in the signature is higher), the work remaining for the verifier *decreases*.
* **The Trade-off:**
    * We can loop over $T$ counters and append them to the message: $M_{ctr} = H_{msg}(ctr, message)$.
    * We search for the counter that maximizes the cumulative chain length (sum of $h_i$).
    * This reduces the number of steps the verification would take, **hence reducing the verification time**.
    * *Note:* There are about a factor of 10 fewer checksum chains than message chains, so optimizing message chains yields significant gains.

### Rapidly Verifiable XMSS Algorithm

To implement this efficiently without exploding the signing time, the algorithm uses an iterative approach that stores the internal state of the hash function.

**Algorithm Logic:** Instead of re-hashing the entire message for every counter attempt ($T$ times), we:

1. Compute the hash state for the static part of the message (Prefix + Message Body).
2. Store this `intermediate_state`.
3. Only process the final block (containing the counter) $T$ times.

This makes the added signing cost independent of the message length.

### Python Implementation

> *This implementation replaces the standard signing routine to include the iterative counter search. This is the core innovation presented by the paper.*

```python
import math

def XMSS_sign_iterative(M, SK, t, n=32):
    """
    Generates an XMSS signature optimized for verification speed using 
    an iterative counter search.

    Parameters:
    M (bytes): The message to be signed.
    SK (object): The XMSS private key structure.
    t (int): The exponent for the number of counters to test (Total T = 2^t).
    n (int): Security parameter (byte length of message digest, e.g., 32 for SHA-256).

    Returns:
    tuple: (Updated SK, Signature Sig, best_counter ctr)
    """

    # 1. Retrieve and update the signature index from the secret key
    idx_sig = getIdx(SK)              
    setIdx(SK, idx_sig + 1)           
    # 2. Initialize Address structure (set to zero)
    ADRS = toByte(0, 32)              

    # 3. Generate randomness 'r' using a PRF
    # Derived from part of the SK and the current index
    sk_prf = getSKPRF(SK)
    r = PRF(sk_prf, toByte(idx_sig, 32))  

    # 4. Optimization Setup: Pre-calculate Hash State
    best_length = -1
    
    # Calculate number of full 512-bit (64-byte) blocks to process once.
    # Formula: 2 (header blocks) + floor(ceil(len(M))/64)
    # Note: The '2' covers the prefix data (r, Root, idx)
    msg_len_bytes = len(M) # equivalent to ceil(log2(M)/8)
    num_blocks = 2 + math.floor(msg_len_bytes / 64) 

    # Construct the input prefix: r || Root || index || Message
    # This input is static except for the final block containing the counter
    input_stream = (
        r + 
        getRoot(SK) + 
        toByte(idx_sig, n) + 
        M
    ) 

    # Compute and store the intermediate SHA-256 state
    # This avoids re-hashing the large message body for every counter iteration
    intermediate_state = sha256_inc_blocks(input_stream, num_blocks) 

    # 5. Iterative Search for Best Counter
    # Loop through 2^t possible counters to find the one producing the fastest-to-verify hash
    best_ctr = 0
    final_h = None

    for i in range(0, 2**t): 
        # Preserve the pre-calculated state before modifying it
        temp_state = intermediate_state.copy()

        # Prepare the final input block: Last part of Message || counter i
        current_input_block = last_block(M + toByte(i, 8))

        # Finalize the hash computation using the preserved state
        # h is the candidate message digest
        h = sha256_inc_finalize(temp_state, current_input_block, 1)

        # Calculate the "length" (cost) of verifying this specific hash
        # Higher length = faster verification (less hashing required for WOTS+)
        new_length = wots_getlengths(h)

        # If this hash is faster to verify than previous best, keep it
        if new_length > best_length:
            best_length = new_length
            best_ctr = i
            final_h = h
            M_prime = h # The message digest to sign is the best hash found

    # 6. Generate the standard XMSS signature using the optimized message digest
    # treeSig generates the WOTS+ signature and authentication path
    signature_body = treeSig(M_prime, SK, idx_sig, ADRS) 

    # Construct the final signature bundle: index || randomness || signature
    Sig = toByte(idx_sig, n) + r + signature_body

    # Return updated key, signature, and the optimized counter
    return (SK, Sig, best_ctr)
```

### RFC Compatibility

* To maintain compatibility with RFC 8391, the counter `ctr` is appended to the message input rather than altering the internal hash structure.
* The modified line in the signing algorithm becomes `byte[n] M' <- Hmsg(r || getRoot(SK) || toByte(idx_sig, n), (M || ctr))`.

**Benefit:** A standard RFC-compliant verifier can verify the signature as long as they are aware the message has an appended counter (which can be handled via a wrapper function).

### Performance Analysis

**Signing Time:** By storing the hash state, the time added to signing is independent of message size. For a 100KB message, signing time drops from over 3 hours (without this optimization) to just 14 seconds.

**Verification Speed:**

* Using a modest number of counters yields a ~20% speedup.
* A larger counter search (approx. 1 minute of signing time) creates signatures that are verified 1.44 times faster than standard signatures.
* Combining this with Time-Memory Trade-Off (TMTO) optimizations on an ARM Cortex-M4 reduces verification cycles from 13.85 million to 6.56 million (over a factor of 2 reduction).

### Security

* The PZMCM technique (searching for a specific hash) might introduce bias, but formal analysis proves that as long as the hash function behaves like a random function, security does not significantly degrade.
* The parameters listed in the RFC still achieve the same level of security with this tuning applied.

**Rust Implementation:** [developeruche/cryptography-n-zk-research — digitial-signatures/xmss-sha256](https://github.com/developeruche/cryptography-n-zk-research/tree/main/digitial-signatures/xmss-sha256)
