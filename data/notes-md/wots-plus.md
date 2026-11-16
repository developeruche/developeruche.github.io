This note is the sequel to [Winternitz One-Time Signature](/blog/winternitz-one-time-signature/). That post built plain WOTS in Rust: hash a secret 256 times to get a public key, and sign a byte by stopping partway along the chain. This note takes the same code and works through the three changes that turn it into **WOTS+**, the one-time signature inside XMSS and SPHINCS+:

1. **A checksum.** Plain WOTS lets anyone forge a signature for some other messages. The checksum closes that hole.
2. **Randomized hash chains.** Every step of every chain is XORed with a public mask before it is hashed.
3. **A public seed.** The masks are derived from it, so both the signer and the verifier can recompute them.

The last section covers a signing-time trick, *rapid verification*, from the [Rapidly Verifiable XMSS](/notes/cryptography-zkp/rapidly-verifiable-xmss/) note. It also shows that the code's version of the trick optimizes in the wrong direction, and gives the one-line fix.

## Phase 0: Parameters

```rust
const HASH_SIZE: usize = 32; // SHA-256 output, in bytes
const L1: usize = 32;        // message chunks: one per byte of the message hash
const L2: usize = 2;         // checksum chunks
const L: usize = L1 + L2;    // 34 chains in total
const W: u16 = 256;          // w = 8 bits per chunk, so W = 2^8 values

type Fragment = [u8; HASH_SIZE];
type Seed = [u8; 32];
```

Plain WOTS had $L = 32$ chains, one per byte of the message hash. WOTS+ adds $L_2 = 2$ chains for the checksum, so $L = 34$.

| Symbol | Value | Meaning |
|---|---|---|
| $n$ | 32 bytes | hash output size (SHA-256) |
| $w$ | 8 bits | bits signed per chain |
| $W$ | $2^8 = 256$ | values one chunk can take; also the chain length |
| $L_1$ | 32 | message chains |
| $L_2$ | 2 | checksum chains |
| $L$ | 34 | total chains |

## Phase 1: The randomized hash chain

Plain WOTS walks a chain by hashing the previous value: $x_{j+1} = H(x_j)$. WOTS+ XORs a mask in first:

$$
x_{i,0} = sk_i, \qquad x_{i,j+1} = H\big(x_{i,j} \oplus r_{i,j}\big), \qquad pk_i = x_{i,W}.
$$

Here $i$ is the chain number ($0 \le i < 34$) and $j$ is the step ($0 \le j < 256$). Each mask $r_{i,j}$ is unique to its position, and anyone can recompute it from the public seed:

$$
r_{i,j} = \mathrm{SHA256}\big(\textit{pub\_seed} \,\|\, i_{\text{u32,BE}} \,\|\, j_{\text{u16,BE}}\big).
$$

```rust
/// r_{i,j} = PRF(pub_seed, chain_idx, step_idx)
fn derive_randomizer(pub_seed: &Seed, chain_idx: u32, step_idx: u16) -> Fragment {
    let mut hasher = Sha256::new();
    hasher.update(pub_seed);
    hasher.update(&chain_idx.to_be_bytes()); // i
    hasher.update(&step_idx.to_be_bytes());  // j
    hasher.finalize().into()
}

/// x_{i,j+1} = H(x_{i,j} XOR r_{i,j}), run `iterations` times from step `start_index`.
fn hash_chain(start: &Fragment, start_index: u16, iterations: u16,
              pub_seed: &Seed, chain_addr: u32) -> Fragment {
    let mut result = *start;
    for k in 0..iterations {
        let r = derive_randomizer(pub_seed, chain_addr, start_index + k);
        let mut tmp = [0u8; HASH_SIZE];
        for b in 0..HASH_SIZE {
            tmp[b] = result[b] ^ r[b];
        }
        result = Sha256::digest(&tmp).into();
    }
    result
}
```

Compared with the plain WOTS version, `hash_chain` takes two new arguments:

- **`chain_addr`** ($i$) selects which chain's masks to use.
- **`start_index`** ($j$) says which absolute step the chain starts from. Plain WOTS could start hashing from anywhere because every step was the same function. In WOTS+, step $j$ uses mask $r_{i,j}$, so a verifier who picks up a chain halfway must know exactly where it is. If the index is off by one, every mask after that point is wrong and the chain never reaches the public key.

### Why mask the chain?

In plain WOTS, every step of every chain uses the same function $H$. If an attacker sees many chain values from many keys, a preimage of *any* of them is useful, which gives the attacker many targets at once. Plain WOTS also needs $H$ to be collision resistant.

WOTS+ gives every position $(i, j)$ its own function $x \mapsto H(x \oplus r_{i,j})$. A value computed at one position is useless at any other, and the security proof only needs second-preimage resistance and one-wayness, not collision resistance. Second-preimage resistance is the weaker assumption, which is why WOTS+ can use shorter hashes than plain WOTS for the same security. (The proof also assumes a keyed hash family; this code keeps the masks but uses unkeyed SHA-256. See the comparison table at the end.) The rapidly verifiable XMSS note describes the attacks this blocks: chain splicing and multi-target attacks.

## Phase 2: Key generation

```rust
pub struct WotsPrivateKey { keys: Vec<Fragment>, pub_seed: Seed }
pub struct WotsPublicKey  { keys: Vec<Fragment>, pub_seed: Seed }
pub struct WotsSignature  { keys: Vec<Fragment> }

impl WotsPrivateKey {
    pub fn new() -> Self {
        let mut rng = rand::rng();
        let mut keys = Vec::with_capacity(L);
        for _ in 0..L {
            let mut key_fragment = [0u8; HASH_SIZE];
            rng.fill_bytes(&mut key_fragment);
            keys.push(key_fragment);
        }
        let mut pub_seed = [0u8; 32];
        rng.fill_bytes(&mut pub_seed);
        WotsPrivateKey { keys, pub_seed }
    }

    pub fn to_public(&self) -> WotsPublicKey {
        let pub_keys = self.keys.iter().enumerate()
            .map(|(i, sk_i)| hash_chain(sk_i, 0, W, &self.pub_seed, i as u32))
            .collect();
        WotsPublicKey { keys: pub_keys, pub_seed: self.pub_seed }
    }
}
```

1. Draw 34 random 32-byte fragments. These are the private key.
2. Draw a random 32-byte `pub_seed`. It is public; it only fixes the masks.
3. Walk each chain from step 0 for all $W = 256$ steps. The 34 end points, together with `pub_seed`, are the public key.

`pub_seed` lives in both keys. The signature leaves it out, because the verifier already holds the public key.

**Sizes:**

- Public key: $34 \times 32 + 32 = 1{,}120$ bytes.
- Signature: $34 \times 32 = 1{,}088$ bytes.
- `WotsPublicKey::hash()` compresses the public key to one 32-byte value, $\mathrm{SHA256}(pk_0 \| \dots \| pk_{33} \| \textit{pub\_seed})$, which is the kind of value a Merkle tree leaf stores.

## Phase 3: The checksum

### The hole in plain WOTS

A signature reveals the chain value at position $W - m_i$. Anyone can hash forward, but nobody can hash backward. From a signature on $m$, an attacker can compute every position $\ge W - m_i$, which means valid signatures for **every message $m'$ with $m'_i \le m_i$ in every byte**.

Plain WOTS therefore leaks signatures for other messages. Since the attacker can't choose the hash of a message, this is a weakness rather than a direct break, but it is exactly the kind of weakness that should not exist.

### The fix

Append a counter that moves the *other* way. The code computes

$$
C = \sum_{i=0}^{31} \big(W - m_i\big) = \sum_{i=0}^{31} (256 - m_i),
$$

and signs its two big-endian bytes on chains 32 and 33, the same way it signs message bytes:

```rust
fn checksum(msg: &[u8]) -> Vec<u8> {
    let mut c: u16 = 0;
    for &byte in msg {
        c += W - (byte as u16);
    }
    vec![(c >> 8) as u8, (c & 0xFF) as u8]
}
```

This is why a forger loses:

- Making any message byte smaller (the only direction hashing forward allows) makes $C$ larger.
- A larger $C$ has, at its first differing big-endian byte, a larger value $c'_k > c_k$.
- Signing $c'_k$ needs the chain value at position $W - c'_k$, which is *earlier* than the revealed $W - c_k$. Getting there means inverting the hash.

So every tampered message breaks at least one chain.

**Range check.** Each term $256 - m_i$ lies in $[1, 256]$, so $C \in [32, 8192]$. The code's comment says the maximum is "$L_1 (W-1) \approx 8160$". That's slightly off: the true maximum is $32 \times 256 = 8192$. It still fits easily in a `u16` and in two base-256 digits (the high byte is at most $8192 \gg 8 = 32$), so the code is correct.

**Orientation.** This code signs with $W - v$ steps. RFC 8391 and the XMSS papers do the opposite: they sign with $v$ steps and use the checksum $\sum (w - 1 - m_i)$. The two conventions are mirror images of each other, so each checksum runs against the direction the forger can move in. Keep that in mind when comparing this code with the papers, because it matters for rapid verification below.

## Phase 4: Signing

Put the 32 message bytes and the 2 checksum bytes into one list $v = (v_0, \dots, v_{33})$, and reveal each chain at position $W - v_i$:

$$
\sigma_i = x_{i,\,W - v_i} = \mathrm{chain}_i\big(sk_i,\ \text{from step } 0,\ W - v_i \text{ steps}\big).
$$

```rust
pub fn sign(&self, message_hash: &Fragment) -> WotsSignature {
    let cs = checksum(message_hash);
    let signature_keys = self.keys.iter()
        .zip(message_hash.iter().chain(cs.iter()))   // v = m || checksum
        .enumerate()
        .map(|(i, (sk_i, &v_i))| {
            hash_chain(sk_i, 0, W - (v_i as u16), &self.pub_seed, i as u32)
        })
        .collect();
    WotsSignature { keys: signature_keys }
}
```

Two edge cases:

- Since $v_i \le 255$, the revealed position is always at least 1. The private key itself ($x_{i,0}$) is never revealed.
- When $v_i = 0$, the signature fragment *is* the public key fragment $x_{i,256}$, and the verifier does no work on that chain.

## Phase 5: Verification

Recompute $v$ from the message hash, then finish each chain. Start at position $W - v_i$ and take the remaining $v_i$ steps up to $W$:

```rust
pub fn verify(&self, message_hash: &Fragment, signature: &WotsSignature) -> bool {
    if signature.keys.len() != L {
        return false;
    }
    let cs = checksum(message_hash);
    let recovered_keys: Vec<Fragment> = signature.keys.iter()
        .zip(message_hash.iter().chain(cs.iter()))
        .enumerate()
        .map(|(i, (sig_i, &v_i))| {
            let start_index = W - (v_i as u16); // where the signer stopped
            hash_chain(sig_i, start_index, v_i as u16, &self.pub_seed, i as u32)
        })
        .collect();
    self.keys == recovered_keys
}
```

The `start_index = W - v_i` line is the WOTS+ detail that has no counterpart in plain WOTS. The verifier continues the signer's chain from the exact step where the signer stopped, using masks $r_{i,W-v_i}, \dots, r_{i,W-1}$. The length check at the top rejects a signature with too few fragments. Without it, `zip` would silently compare fewer chains.

### Cost

Signing and verifying split each 256-step chain between them, so together they always do $L \cdot W = 34 \times 256 = 8{,}704$ steps. The verifier's share is

$$
\text{verify steps} = \sum_{i=0}^{33} v_i .
$$

Each step costs **two** SHA-256 calls: one to derive $r_{i,j}$ and one for the chain hash. Key generation is therefore $8{,}704 \times 2 = 17{,}408$ SHA-256 calls. For a random message, verification averages about **4,200 steps**: the message bytes contribute about $32 \times 127.5 = 4{,}080$, and the checksum bytes contribute the rest.

## Phase 6: Rapid verification

### The idea

Verification cost depends on the message digest, and the signer can choose among many digests. Hash the message with a counter, $d_{ctr} = \mathrm{SHA256}(\text{message} \,\|\, ctr_{\text{u32,BE}})$, try $T+1$ counters, sign the cheapest $d_{ctr}$, and send $ctr$ along with the signature. Signing costs a few hundred extra hashes, once. Every later verification is cheaper. This is the idea behind the [Rapidly Verifiable XMSS](/notes/cryptography-zkp/rapidly-verifiable-xmss/) note.

The code does this in `sign_optimized`. It hashes the message once, clones the hasher state for each counter (so the extra signing cost does not grow with message length), and scores each digest:

```rust
pub fn sign_optimized(&self, message: &[u8], max_attempts: u32) -> (WotsSignature, u32) {
    let mut best_ctr = 0;
    let mut best_score = 0;
    let mut best_digest = [0u8; HASH_SIZE];

    let mut base_hasher = Sha256::new();
    base_hasher.update(message);

    for ctr in 0..=max_attempts {
        let mut hasher = base_hasher.clone();
        hasher.update(&ctr.to_be_bytes());
        let digest: Fragment = hasher.finalize().into();
        let cs = checksum(&digest);
        let score: u32 = digest.iter().chain(cs.iter()).map(|&x| x as u32).sum();
        if score > best_score {          // <-- keeps the HIGHEST score
            best_score = score;
            best_ctr = ctr;
            best_digest = digest;
        }
    }
    (self.sign(&best_digest), best_ctr)
}
```

### The bug: it maximizes verification cost

The comment above the score says verification cost is proportional to $\sum (W - 1 - v_i)$, so the largest $\sum v_i$ is the cheapest. That is true for the **RFC orientation**, where the signer walks $v_i$ steps and the verifier walks the rest. This code uses the mirror image (Phase 3): the verifier walks $v_i$ steps. Its cost **is** the score:

$$
\text{verify steps} = \sum_{i=0}^{33} v_i = \text{score}.
$$

Keeping the highest score therefore picks the digest that is **most expensive** to verify. I ported the code to Python step for step and measured it on 300 random messages with `max_attempts = 255` (256 counters):

| Counter choice | Mean verify steps | vs. `ctr = 0` |
|---|---|---|
| `ctr = 0` (no search) | 4,209 | — |
| code as written (`score > best`) | 5,397 | **28% slower** |
| fixed (`score < best`) | 3,036 | **28% faster, 1.39×** |

The fixed result agrees with the roughly 1.44× speed-up reported in the rapidly verifiable XMSS note. The test suite missed the bug because `test_optimization_gain` checks that the score went *up*. It never measures the verifier's work.

### The fix

Keep the lowest score:

```rust
let mut best_score = u32::MAX;
// ...
if score < best_score {
```

Alternatively, flip the whole scheme to the RFC orientation: sign with $v_i$ steps, verify with $W - v_i$, and use the checksum $\sum (W - 1 - m_i)$. Then keeping the highest score is correct. Either way, the score and the verifier must agree on which direction is cheap.

Two more points on using `sign_optimized`:

- **The counter travels with the signature.** The verifier recomputes $\mathrm{SHA256}(\text{message} \| ctr)$ and calls the ordinary `verify`. `test_sign_optimized` does exactly this.
- **Grinding does not weaken security.** The signer is only choosing among hash outputs that it computes honestly. The key is still used once, on one digest.

## Why "one-time" still holds

Sign two different digests with the same key, and for each chain the attacker learns the earlier of the two revealed positions. They can now sign any value up to $\max(v_i, v'_i)$ on every chain, *including the checksum chains*. The checksum argument from Phase 3 no longer applies: an attacker can mix high bytes from one signature with high checksum digits from the other. Every WOTS+ key must sign exactly one digest. XMSS enforces this with a state counter; SPHINCS+ does it by picking keys from a huge tree at random.

## This code vs. RFC 8391

This implementation is a faithful *teaching* version of WOTS+. These are the differences from the standardized version used in XMSS:

| | This code | RFC 8391 (XMSS) |
|---|---|---|
| Winternitz parameter | $w = 256$ ($\log w = 8$) | $w = 16$ ($\log w = 4$): 64 + 3 chains for $n = 32$ |
| Chain step | $H(x \oplus r_{i,j})$ | $F(\textit{key}_{i,j},\ x \oplus \textit{bm}_{i,j})$: a mask **and** a per-step key, both from PRF(seed, address) |
| Mask address | chain $i$, step $j$ | layer, tree, key pair (OTS index), chain, step |
| Private key | 34 random fragments | derived from one secret seed via PRF |
| Orientation | sign $W - v_i$ steps, verify $v_i$ | sign $v_i$ steps, verify $w - 1 - v_i$ |
| Public key compression | `hash()`: one SHA-256 over all fragments | L-tree (a binary hash tree) |

The address row matters once keys are placed in a tree. Here the masks depend only on $(i, j)$, so two key pairs that share a `pub_seed` would share all their masks. XMSS adds the key-pair index to the address so every leaf gets its own masks. A single key, as used here and in the tests, is unaffected.

## Summary

- **WOTS+ = WOTS + checksum + masked chains.** The checksum stops forward-hashing forgeries. The masks give every chain position its own hash function, which defeats multi-target attacks and reduces security to second-preimage resistance.
- **`start_index` is the key implementation detail.** The verifier continues the chain from the exact step where the signer stopped, because each step uses a different mask.
- **Costs at these parameters:**
  - Public key: 1,120 bytes. Signature: 1,088 bytes.
  - Key generation: 17,408 SHA-256 calls.
  - Signing plus verifying: 8,704 chain steps in total, about 4,200 of them for the verifier.
- **Rapid verification works, once it points the right way.** Searching 256 counters makes verification about 1.39× faster, but only after `sign_optimized` keeps the *lowest* $\sum v_i$. As written, it makes verification 28% slower.
