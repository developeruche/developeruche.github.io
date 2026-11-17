## The short version

A Merkle hypertree is a tree whose nodes are themselves Merkle trees. It has d layers of trees, every tree has height h′, so the whole structure has total height h = d·h′ and 2^h one-time keys at the bottom.

Every leaf of every tree is a one-time signature (OTS) key. A leaf on a higher layer signs the root of exactly one tree on the layer below. A leaf on the bottom layer signs the message (in SLH-DSA, it signs a few-time FORS key, which signs the message). The public key is only the root of the single top tree.

Why bother: a single Merkle tree of height h must compute all 2^h OTS public keys at key generation. A hypertree computes only the top tree (2^h′ leaves) at key generation and builds each lower tree the first time it is needed. You get 2^h signatures for roughly the setup cost of 2^h′.

The price is size: a signature carries d OTS signatures and d authentication paths instead of one of each. With n-byte hashes:

$$
|\sigma_{HT}| \approx d\cdot|\sigma_{OTS}| + h\cdot n \qquad\qquad \text{signing work without caching} \approx d\cdot 2^{h/d}\ \text{OTS key generations}
$$

The same construction appears under three names:

| Standard | Name for the hypertree | Layers | Leaf choice |
| --- | --- | --- | --- |
| [RFC 8554](https://www.rfc-editor.org/rfc/rfc8554.html) (LMS) | HSS, Hierarchical Signature System | L = 1 to 8 levels, numbered from the top | Counter per level (stateful) |
| [RFC 8391](https://www.rfc-editor.org/rfc/rfc8391.html) (XMSS) | XMSS^MT, multi-tree XMSS | d layers of XMSS trees, numbered from the bottom | Global counter (stateful) |
| [FIPS 205](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf) (SLH-DSA, ex-SPHINCS+) | Hypertree | d = 7 to 22 layers, numbered from the bottom | Pseudorandom from the message (stateless) |

The [NHIMG glossary entry](https://nhimg.org/glossary/hypertree/) on hypertrees describes the stateful use. Hypertrees are not inherently stateful, though: SLH-DSA picks the leaf pseudorandomly from a hypertree so tall (h = 63 to 68) that a repeated leaf is rare and survivable. Sections below cover both uses.

## Building blocks: one-time signatures and Merkle trees

A hypertree is wiring between two parts: a one-time signature (OTS) scheme and a Merkle tree. Once these two are clear, the hypertree adds no new cryptography.

### The hash function

Everything is built from one hash function with an n-byte output (n = 16, 24 or 32). The schemes rely on preimage and second-preimage resistance; XMSS and SLH-DSA are designed not to need collision resistance. Against quantum attackers, Grover's algorithm only square-roots preimage search, so FIPS 205 maps n = 16 to NIST security category 1, n = 24 to category 3 and n = 32 to category 5 ([FIPS 205, Table 2](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf)).

### Lamport: the simplest one-time signature

The secret key is 2 × 256 random values; the public key is their hashes. To sign a 256-bit digest, reveal one of the two secrets for each bit. Verification hashes the revealed values and compares.

Sign two different digests and, at every bit where they differ, both secrets are now public. A forger can mix them to sign new digests. That is the meaning of "one-time", and it is the property every hypertree must protect.

### Winternitz chains (WOTS, WOTS+, LM-OTS)

Winternitz shrinks Lamport by signing several bits per hash chain:

1. Split the n-byte digest into len₁ digits of w bits each, then append len₂ checksum digits.
2. The secret key is one random start value per digit. The public key is the end of each chain after 2^w − 1 hash steps, all hashed together into one n-byte value.
3. To sign digit a, reveal the chain value after a steps.
4. To verify, hash each revealed value forward the remaining 2^w − 1 − a steps, then hash the chain ends together and compare with the public key.

The checksum is the sum of (2^w − 1 − a) over the message digits. Raising any message digit lowers the checksum, which would mean walking a checksum chain backwards, i.e. inverting the hash.

The property that makes trees possible: step 4 recomputes the OTS public key from the signature. The signer never has to send the OTS public key, because the Merkle tree authenticates whatever the verifier recomputes.

Two naming traps between the specs:

- In LMS, w is the number of bits per digit (1, 2, 4 or 8). In XMSS and SLH-DSA, w is the base (16), and FIPS 205 writes lg\_w = 4 for the bits.
- LMS calls the number of chains p; XMSS and SLH-DSA call it len. For XMSS, len₁ = ⌈8n / lg w⌉, len₂ = ⌊lg(len₁·(w − 1)) / lg w⌋ + 1, which gives len = 67 for n = 32, w = 16 ([RFC 8391 §3.1](https://www.rfc-editor.org/rfc/rfc8391.html)). SLH-DSA always has len = 2n + 3.

The LM-OTS parameter sets show the size/speed dial. Each chain costs up to 2^w − 1 hashes; larger w means fewer chains but longer ones ([RFC 8554, Table 1](https://www.rfc-editor.org/rfc/rfc8554.html)):

| LM-OTS set (SHA-256, n = 32) | Bits per digit w | Chains p | Hashes per chain | Signature bytes |
| --- | --- | --- | --- | --- |
| LMOTS\_SHA256\_N32\_W1 | 1 | 265 | 1 | 8,516 |
| LMOTS\_SHA256\_N32\_W2 | 2 | 133 | 3 | 4,292 |
| LMOTS\_SHA256\_N32\_W4 | 4 | 67 | 15 | 2,180 |
| LMOTS\_SHA256\_N32\_W8 | 8 | 34 | 255 | 1,124 |

The variants differ in how they keep every hash call distinct. WOTS+ (XMSS, SLH-DSA) feeds a per-call address into a keyed or tweaked hash. LM-OTS prefixes every call with I ‖ q ‖ i ‖ j: the 16-byte key identifier, the leaf number, the chain number and the step. The SPHINCS family also uses a few-time scheme (HORST, later FORS) at the very bottom; it is covered under stateless hypertrees below.

### Merkle tree and authentication path

Put 2^h OTS public keys at the leaves (leaf q = hash of OTS public key q), hash pairs upward, and publish the root. To prove that OTS key q belongs to the root, give the h sibling nodes on the way up: the authentication path.

LMS numbers nodes like a binary heap: the root is node 1, node r has children 2r and 2r + 1, and leaf q is node 2^h + q ([RFC 8554 §5](https://www.rfc-editor.org/rfc/rfc8554.html)). The path is then path[i] = T[(r >> i) xor 1], with r = 2^h + q.

A Merkle signature is (q, OTS signature, path). Verifying it is the loop every hypertree repeats once per layer:

```python
def merkle_verify(root, msg, q, ots_sig, path, h):
    node = leaf_hash(q, ots_pk_from_sig(ots_sig, msg, q))  # recompute the leaf
    for i in range(h):
        if (q >> i) & 1 == 0:          # we are a left child at height i
            node = node_hash(node, path[i])
        else:                           # we are a right child
            node = node_hash(path[i], node)
    return node == root
```

In every real scheme, leaf\_hash and node\_hash also take the node's position (and a key identifier or address) so no two hash calls in the structure ever share an input format. The security section below explains why.

## Why one tree is not enough, and where hypertrees came from

A single Merkle tree needs every OTS public key before it can publish its root. Key generation therefore costs 2^h OTS key generations, and that wall is what the hypertree removes.

The arithmetic, using LM-OTS with w = 8 (34 chains × 255 steps, plus key derivation and leaf hashing, about 8,700 hash calls per leaf):

| Structure for about 2^40 signatures | Key generation work (hash calls) |
| --- | --- |
| One LMS tree of height 40 | about 9.6 × 10^15 (not feasible; also not a defined parameter set) |
| HSS, 2 levels of height 20 | about 1.8 × 10^10 (top tree + first bottom tree) |
| HSS, 4 levels of height 10 | about 3.6 × 10^7 (four small trees) |

These counts are my own, from the RFC 8554 parameters; the trade is paid back in signature size, quantified in the parameters section.

### The idea: a certificate chain made of Merkle trees

If you know X.509, you already know the hypertree. A root CA signs an intermediate CA's key; the intermediate signs the leaf key; the leaf key signs the document. The verifier trusts only the root and walks the chain.

In a hypertree, every "CA" is a Merkle tree, every "certificate" is one OTS signature on the root of the tree below, and the trust anchor is the root of the top tree. Because each lower tree's root is only certified when it is first needed, the lower trees do not have to exist at key generation.

### History

| Year | Work | What it added |
| --- | --- | --- |
| 2026 | [NIST SP 800-230 (draft)](https://csrc.nist.gov/pubs/sp/800/230/ipd) | SLH-DSA sets capped at 2^24 signatures; they collapse the hypertree to d = 1 |
| 2025 | [RFC 9802](https://www.rfc-editor.org/rfc/rfc9802) | HSS, XMSS and XMSS^MT public keys in X.509 certificates |
| 2025 | [Drake, Khovratovich, Kudinov, Wagner (ePrint 2025/055)](https://eprint.iacr.org/2025/055) | XMSS-style signatures for Ethereum consensus (leanSig) |
| 2024 | [FIPS 205](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf) | SLH-DSA: the standardized stateless hypertree |
| 2020 | [NIST SP 800-208](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-208.pdf) | Approves HSS and XMSS^MT; splits one key's bottom trees across hardware modules |
| 2019 | [RFC 8554](https://www.rfc-editor.org/rfc/rfc8554.html) | LMS and its hypertree, HSS |
| 2019 | [SPHINCS+](https://sphincs.org/data/sphincs+-r3.1-specification.pdf) | Tweakable hashes, FORS, pseudorandom leaf choice |
| 2018 | [RFC 8391](https://www.rfc-editor.org/rfc/rfc8391.html) | XMSS and XMSS^MT |
| 2018 | [Grafting Trees (ePrint 2018/102)](https://eprint.iacr.org/2018/102) | First fault attack on hypertrees |
| 2015 | [SPHINCS](https://sphincs-cr-yp-to.viacache.net/sphincs-20141001.pdf) | First practical stateless hypertree: h = 60, d = 12, 41 KB signatures |
| 2007 | [GMSS](https://link.springer.com/content/pdf/10.1007/978-3-540-72738-5_3.pdf) | Many layers with different heights and Winternitz parameters; spreads work for the next tree over many signatures |
| 2006 | CMSS | Two layers of equal height |
| 1986 | Goldreich | Stateless tree of OTS keys with a random leaf per signature |
| 1979 | Merkle | Tree authentication of many OTS keys under one root |

Two lessons from this line of work matter for implementers. First, the SPHINCS authors note that Goldreich's stateless construction worked but its signatures stayed above 1 MB, with size cubic in the security parameter ([SPHINCS](https://sphincs-cr-yp-to.viacache.net/sphincs-20141001.pdf)). The practical hypertree came from shrinking the tree with a few-time signature at the bottom and choosing d carefully. Second, GMSS showed that per-layer parameters pay off: its 2^80-signature example uses four layers of height 20, with signatures of 3,620 bytes ([GMSS](https://link.springer.com/content/pdf/10.1007/978-3-540-72738-5_3.pdf)). HSS inherited that per-level flexibility; XMSS^MT and SLH-DSA did not.

## Anatomy of a hypertree

A hypertree with d layers of height-h′ trees has 1 tree on the top layer, 2^h′ trees on the next, and 2^((d−1)·h′) trees on the bottom layer. A signature is one route from a bottom leaf to the public root: d pairs of (OTS signature, authentication path).

### Layers and what each leaf signs

- The top layer (numbered d − 1 in XMSS^MT and SLH-DSA) holds one tree. Its root is the public key.
- Layer j holds 2^((d−1−j)·h′) trees. Leaf ℓ of tree t on layer j certifies tree t·2^h′ + ℓ on layer j − 1 by signing its root.
- The bottom layer (0) holds 2^h leaves in total. That is the signing capacity of a stateful hypertree, or the index space of a stateless one.

Each OTS key above the bottom layer signs exactly one value, ever: the root of its child tree. The signer may send that same OTS signature thousands of times, inside every signature that passes through the child tree, but it never signs a second value. HSS stores the certificate once; SLH-DSA recomputes it deterministically and gets the same bytes. Breaking this rule (for example, by a fault that changes a recomputed root) breaks the scheme.

### Index arithmetic

The whole route is determined by one integer, the global leaf index idx in [0, 2^h). Cut idx into d chunks of h′ bits. The lowest chunk is the leaf on layer 0; each higher chunk is the leaf one layer up. The bits above a layer's chunk name the tree on that layer:

$$
\ell_j = \left\lfloor \mathrm{idx} / 2^{\,j h'} \right\rfloor \bmod 2^{h'} \qquad\qquad t_j = \left\lfloor \mathrm{idx} / 2^{\,(j+1) h'} \right\rfloor
$$

In code this is the loop FIPS 205 uses in ht\_sign: start with idx\_leaf = idx mod 2^h′ and idx\_tree = idx >> h′, then for each layer above set idx\_leaf = idx\_tree mod 2^h′ and idx\_tree = idx\_tree >> h′ ([FIPS 205 §7](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf)).

Worked example with h = 6, d = 3, h′ = 2 and idx = 45 = 0b10·11·01:

| Layer | Tree t\_j | Leaf ℓ\_j | That leaf signs |
| --- | --- | --- | --- |
| 2 (top) | 0 | 2 | Root of tree 2 on layer 1 |
| 1 | 2 | 3 | Root of tree 11 on layer 0 |
| 0 (bottom) | 11 | 1 | The message (or FORS key) |

Check: tree 2 × 4 + leaf 3 = tree 11, and tree 0 × 4 + leaf 2 = tree 2. The diagram below draws exactly this route.

![Hypertree route for idx = 45 with d = 3 and h′ = 2: leaf 2 of the top tree signs the root of tree 2 on layer 1, leaf 3 of that tree signs the root of tree 11 on layer 0, and leaf 1 of tree 11 signs the message](assets/notes/merkle-hypertrees/hypertree-route-idx45.svg)

The signature for index 45 contains three (OTS signature, authentication path) pairs, one per drawn tree. The verifier rebuilds each tree's root from its pair and feeds it to the next layer up; the dashed trees never appear in this signature, and a stateful signer has not even built them yet.

HSS has no single global index in its wire format. Each level keeps its own counter q and its own tree height, so the "index" is a mixed-radix number with one digit per level, and the signer advances it like an odometer: the bottom digit increments every signature, and a level rolls over only when the level below it is exhausted.

### The same parts under different names

| Concept | HSS ([RFC 8554](https://www.rfc-editor.org/rfc/rfc8554.html)) | XMSS^MT ([RFC 8391](https://www.rfc-editor.org/rfc/rfc8391.html)) | SLH-DSA ([FIPS 205](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf)) |
| --- | --- | --- | --- |
| Layer count | L = 1 to 8 | d; SP 800-208 allows up to 12 | d = 7, 8, 17 or 22 |
| Layer numbering | Level 0 is the top | Layer 0 is the bottom | Layer 0 is the bottom |
| Tree height | Chosen per level: 5, 10, 15, 20 or 25 | h/d, equal for all layers | h′, equal for all layers |
| One-time scheme | LM-OTS | WOTS+, compressed with an L-tree | WOTS+ |
| Bottom leaf signs | The message | The randomized message hash | A FORS public key |
| Leaf selection | Counter q per level | Global counter idx\_MT | Derived from the message hash |
| Key material | A separate I and SEED per LMS tree, from an approved RNG (SP 800-208 §6.1) | One SEED and SK\_PRF; every tree derived | PK.seed, SK.seed, SK.prf; every tree derived |
| Domain separation | Prefix I ‖ u32(r or q) ‖ u16(type or chain) | 32-byte ADRS, plus bitmasks | 32-byte ADRS (22-byte ADRSc with SHA-2) |
| Public key | u32(L) ‖ top LMS public key | OID ‖ root ‖ SEED | PK.seed ‖ PK.root (2n bytes) |

The numbering inversion between HSS and the other two is the most common source of off-by-one bugs when porting code between them. The layer limits for HSS and XMSS^MT come from [SP 800-208](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-208.pdf), footnote 3.

## The algorithms, step by step

Key generation builds only the top tree; signing walks up the layers, each layer signing the root computed by the layer below; verification recomputes the same roots from the signature and compares the last one with the public key. The generic version below follows FIPS 205's xmss\_node, xmss\_sign, xmss\_pkFromSig, ht\_sign and ht\_verify (Algorithms 9 to 13), renamed to be scheme-neutral. HSS and XMSS^MT differ only in the wrappers that follow.

### Generic hypertree core

Parameters: d layers, tree height hp (h′), h = d·hp, n-byte hashes. addr(...) stands for whatever makes each hash call's input unique (ADRS in XMSS and SLH-DSA, the I ‖ q ‖ … prefix in LMS).

```python
def tree_node(sk_seed, pk_seed, i, z, layer, tree):
    """Node at height z, position i, in tree `tree` on `layer`. z = hp gives the root."""
    if z == 0:  # a leaf: the compressed OTS public key of key pair i
        return ots_pk_gen(sk_seed, pk_seed, addr(layer, tree, keypair=i))
    left  = tree_node(sk_seed, pk_seed, 2 * i,     z - 1, layer, tree)
    right = tree_node(sk_seed, pk_seed, 2 * i + 1, z - 1, layer, tree)
    return H(pk_seed, addr(layer, tree, height=z, index=i), left + right)

def tree_sign(msg, sk_seed, pk_seed, leaf, layer, tree):
    auth = [tree_node(sk_seed, pk_seed, (leaf >> j) ^ 1, j, layer, tree) for j in range(hp)]
    sig = ots_sign(msg, sk_seed, pk_seed, addr(layer, tree, keypair=leaf))
    return sig, auth

def tree_root_from_sig(leaf, sig, auth, msg, pk_seed, layer, tree):
    node = ots_pk_from_sig(sig, msg, pk_seed, addr(layer, tree, keypair=leaf))
    for j in range(hp):
        a = addr(layer, tree, height=j + 1, index=leaf >> (j + 1))
        if (leaf >> j) & 1 == 0:
            node = H(pk_seed, a, node + auth[j])
        else:
            node = H(pk_seed, a, auth[j] + node)
    return node

def ht_keygen(sk_seed, pk_seed):
    return tree_node(sk_seed, pk_seed, 0, hp, layer=d - 1, tree=0)   # only the top tree

def ht_sign(msg, sk_seed, pk_seed, idx_tree, idx_leaf):
    sigs, value = [], msg
    for layer in range(d):
        sig, auth = tree_sign(value, sk_seed, pk_seed, idx_leaf, layer, idx_tree)
        sigs.append((sig, auth))
        if layer < d - 1:  # the root of this tree is what the next layer up signs
            value = tree_root_from_sig(idx_leaf, sig, auth, value, pk_seed, layer, idx_tree)
            idx_leaf, idx_tree = idx_tree % 2**hp, idx_tree >> hp
    return sigs

def ht_verify(msg, sigs, pk_seed, idx_tree, idx_leaf, pk_root):
    node = msg
    for layer in range(d):
        sig, auth = sigs[layer]
        node = tree_root_from_sig(idx_leaf, sig, auth, node, pk_seed, layer, idx_tree)
        idx_leaf, idx_tree = idx_tree % 2**hp, idx_tree >> hp
    return node == pk_root
```

Three details that are easy to get wrong:

- The signer gets each tree's root from tree\_root\_from\_sig, not from a second full tree computation. It is cheaper, and it is exactly what the verifier will compute.
- The address of a node at height j + 1 uses index leaf >> (j + 1), the parent's position, not the child's. Signer and verifier must agree bit for bit.
- tree\_node is written recursively for clarity. Real code uses the stack-based treehash (RFC 8554 Appendix C) or keeps the whole tree in memory, and computes the leaves in parallel.

### Stateful wrapper: XMSS^MT

XMSS^MT keeps one counter idx\_MT in the private key. Signing reads it, increments it, then signs with idx\_tree = the top h − h/d bits and idx\_leaf = the low h/d bits ([RFC 8391 §4.2](https://www.rfc-editor.org/rfc/rfc8391.html)):

```python
def xmssmt_sign(sk, msg):
    idx = sk.idx
    if idx >= 2**h:
        raise KeyExhausted
    sk.idx = idx + 1
    persist(sk)                                  # durable BEFORE the signature leaves
    r = PRF(sk.sk_prf, to_bytes(idx, 32))         # per-signature randomizer
    digest = H_msg(r + sk.root + to_bytes(idx, n), msg)
    return to_bytes(idx, ceil(h / 8)) + r + flatten(ht_sign(digest, ..., idx >> hp, idx % 2**hp))
```

Signature size is ⌈h/8⌉ + n + (h + d·len)·n bytes.

### Stateful wrapper: HSS

HSS stacks complete LMS key pairs instead of sharing one seed. Each level i has its own LMS private key (identifier I, SEED, counter q); the private state also caches, for each level below the top, that level's public key and the parent's signature on it ([RFC 8554 §6](https://www.rfc-editor.org/rfc/rfc8554.html)).

1. Key generation: generate level 0 and publish u32(L) ‖ pub[0]. For i = 1 to L − 1, generate level i and store sig[i−1] = lms\_sign(pub[i], priv[i−1]). This step can be deferred to the first signature.
2. Signing: if the bottom level is exhausted, find the smallest d such that levels d to L − 1 are all exhausted. If d = 0, the whole HSS key is exhausted. Otherwise regenerate levels d to L − 1, signing each new public key with the level above (Algorithm 8). Then output u32(L − 1) ‖ (sig[0] ‖ pub[1]) ‖ … ‖ (sig[L−2] ‖ pub[L−1]) ‖ lms\_sign(msg, priv[L−1]).
3. Verification: read Nspk and reject unless Nspk + 1 = L. Set key = pub[0]. For each signed public key, verify sig[i] on pub[i+1] under key, then set key = pub[i+1]. Finally verify the message under key.

The pub[i+1] values travel inside the signature, which is why HSS signatures are slightly larger than XMSS^MT's, and why each level can use a different LMS and LM-OTS parameter set.

### Stateless wrapper: SLH-DSA

SLH-DSA removes the counter. The message itself chooses the route ([FIPS 205, Algorithm 19](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf)):

```python
def slh_sign(sk, msg, opt_rand):          # opt_rand = PK.seed for the deterministic variant
    R = PRF_msg(sk.prf, opt_rand, msg)
    digest = H_msg(R, sk.pk_seed, sk.pk_root, msg)          # m bytes
    md, rest = split(digest, ceil(k * a / 8))
    idx_tree = int(rest[: ceil((h - hp) / 8)]) % 2**(h - hp)
    idx_leaf = int(rest[ceil((h - hp) / 8):][: ceil(hp / 8)]) % 2**hp
    sig_fors = fors_sign(md, sk, idx_tree, idx_leaf)          # few-time key under that leaf
    pk_fors = fors_pk_from_sig(sig_fors, md, sk.pk_seed, idx_tree, idx_leaf)
    return R + sig_fors + flatten(ht_sign(pk_fors, sk.seed, sk.pk_seed, idx_tree, idx_leaf))
```

The verifier recomputes digest from R and the message, so it learns idx\_tree and idx\_leaf without them being sent. Total size is (1 + k(1 + a) + h + d·len)·n bytes.

### Cost per operation

| Operation | Work, in OTS key generations unless noted |
| --- | --- |
| Key generation | 2^hp for the top tree (HSS: one tree per level, Σ 2^h\_i, unless lower levels are deferred) |
| Sign, recomputing every tree (SLH-DSA) | d·2^hp, plus d OTS signatures |
| Sign, stateful with cached current trees | 1 OTS signature plus about 1 amortized OTS key generation; a spike of 2^hp when a new subtree is needed, unless that work is spread over earlier signatures as GMSS does |
| Verify | d OTS public-key recomputations plus h node hashes; no tree building |

The SPHINCS+ authors put it plainly: essentially all hypertree signing time goes into computing WOTS+ public keys ([SPHINCS+ spec §7.1.1](https://sphincs.org/data/sphincs+-r3.1-specification.pdf)).

## HSS, XMSS^MT and SLH-DSA side by side

All three standards use the same hypertree; they differ in leaf selection, key derivation and hash-call separation. HSS is the simplest and the most flexible stateful design, XMSS^MT shares one seed across all trees and has no per-layer choice, and SLH-DSA drops the state at the cost of signatures 2 to 14 times larger than a 2^40-signature HSS key.

| Property | HSS | XMSS^MT | SLH-DSA |
| --- | --- | --- | --- |
| State | Counter q per level | One counter idx\_MT | None |
| Different parameters per layer | Yes, if every level uses the same hash ([SP 800-208 §4](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-208.pdf)) | No: one h and d | No |
| Trees derived from | A separate random I and SEED per LMS tree | One shared SEED | One shared PK.seed and SK.seed |
| Max layers | 8 | 12 | 22 in the FIPS 205 sets |
| Public key | 60 bytes (u32(L) + 56-byte LMS key) | OID + root + SEED | 2n: 32, 48 or 64 bytes |
| Extra hashing | None beyond chains and tree | L-tree to compress each WOTS+ key ([wolfSSL comparison](https://www.wolfssl.com/lms-versus-xmss-versus-slh-dsa/)) | FORS layer under the hypertree |
| Approval | SP 800-208; CNSA 2.0 for software and firmware signing | SP 800-208; CNSA 2.0 for software and firmware signing | FIPS 205; not part of CNSA 2.0 ([CNSA 2.0 summary](https://www.encryptionconsulting.com/comparing-slh-dsa-lms-and-xmss/)) |
| Certificates | [RFC 9802](https://www.rfc-editor.org/rfc/rfc9802) | [RFC 9802](https://www.rfc-editor.org/rfc/rfc9802) | Separate specs |

### Stateful signature sizes

Sizes for SHA-256 with n = 32. HSS rows use LM-OTS W8 unless marked; they come from my implementation's size formula, which matches both RFC 8554 test-vector signatures exactly (2,644 and 3,860 bytes). XMSS^MT rows use the RFC 8391 formula ⌈h/8⌉ + n + (h + d·len)·n with len = 67 (w = 16).

| Configuration | Signatures | Signature bytes |
| --- | --- | --- |
| HSS L=1, H20 | 2^20 | 1,776 |
| HSS L=2, H10/H10 | 2^20 | 2,964 |
| XMSSMT-SHA2\_20/2\_256 | 2^20 | 4,963 |
| HSS L=2, H20/H10 | 2^30 | 3,284 |
| HSS L=2, H20/H20 | 2^40 | 3,604 |
| HSS L=2, H20/H20, W4 | 2^40 | 5,716 |
| XMSSMT-SHA2\_40/2\_256 | 2^40 | 5,605 |
| XMSSMT-SHA2\_40/8\_256 | 2^40 | 18,469 |
| HSS L=3, H20/H20/H20 | 2^60 | 5,432 |
| XMSSMT-SHA2\_60/3\_256 | 2^60 | 8,392 |
| XMSSMT-SHA2\_60/12\_256 | 2^60 | 27,688 |

Compare like with like: XMSS^MT's w = 16 matches LM-OTS W4 (67 chains), and at that width HSS 20/20 (5,716 bytes) and XMSS^MT 40/2 (5,605 bytes) are within 2%. HSS's W8 rows are smaller because each chain is 255 steps instead of 15, so one OTS key costs about 8,700 hash calls instead of about 1,000 (34 × 255 versus 67 × 15).

### SLH-DSA parameter sets

From [FIPS 205, Table 2](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf). Each set comes in SHA2 and SHAKE versions with identical sizes, and each key is rated for at most 2^64 signatures.

| Set | n | h | d | h′ | FORS a, k | Signature bytes |
| --- | --- | --- | --- | --- | --- | --- |
| 128s | 16 | 63 | 7 | 9 | 12, 14 | 7,856 |
| 128f | 16 | 66 | 22 | 3 | 6, 33 | 17,088 |
| 192s | 24 | 63 | 7 | 9 | 14, 17 | 16,224 |
| 192f | 24 | 66 | 22 | 3 | 8, 33 | 35,664 |
| 256s | 32 | 64 | 8 | 8 | 14, 22 | 29,792 |
| 256f | 32 | 68 | 17 | 4 | 9, 35 | 49,856 |

The s (small) and f (fast) sets are the hypertree trade-off made concrete: 128s uses 7 layers of height 9, so signing builds 7 × 512 WOTS+ keys; 128f uses 22 layers of height 3, so signing builds only 22 × 8, but carries 22 WOTS+ signatures.

## Stateful versus stateless hypertrees

The hypertree has no state of its own; state comes from how the leaf index is chosen. A counter gives compact signatures but forbids ever reusing an index (HSS, XMSS^MT). Deriving the index from the message removes the counter, but then the tree must be tall enough, and the bottom scheme tolerant enough, that a repeated index does no harm (SLH-DSA).

### What the state is, and why reuse is fatal

In XMSS^MT the state is one integer. In HSS it is a counter q per level, plus the cached lower trees and the signed public keys that ride inside every signature.

If one bottom leaf signs two different messages, the attacker holds two Winternitz signatures from one key. Wherever one signature is further along a chain than the other, the attacker can hash forward and sign any digit at or above the smaller value. Enough such positions make a forgery. RFC 8554 is blunt: if a secret key state is used twice, no cryptographic security guarantees remain ([RFC 8554 §1.1](https://www.rfc-editor.org/rfc/rfc8554.html)).

The hypertree adds a second rule: an upper-layer leaf must sign only one subtree root, ever. HSS gets this for free, because it stores the parent's signature on each child public key once and copies it into later signatures.

### Operational rules for stateful keys

1. Advance and persist the counter before the signature leaves the signer. SP 800-208 requires the module to store the updated index in nonvolatile memory before exporting a signature or accepting another request (§8.1).
2. Make "persisted" mean persisted. SP 800-208 warns that operating-system write caching can lose an update on power loss or crash, and suggests hardware monotonic counters (§9.1).
3. Never copy a private key. SP 800-208 rules out copies because they create a risk of OTS key reuse (§7). Backups, VM snapshots and container images are copies.
4. Keep keys in hardware. SP 800-208 requires key and signature generation in a cryptographic module that does not allow export of private keying material, at FIPS 140 Level 3 or higher (§1, §8.1).
5. Reserve indices in blocks if fsync per signature is too slow: persist idx + N, then sign up to N times from memory. A crash burns at most N leaves and never reuses one. This is a common engineering pattern, not a spec requirement.
6. Know what a rollback does to the upper layers. SP 800-208 requires a separate I and SEED from an approved random bit generator for every LMS tree in an HSS key (§6.1). My own analysis, not a spec statement: a signer rolled back to an old state generates a different random child tree, so the parent leaf signs a second public key, an upper-layer reuse on top of the bottom-layer one. Deriving child keys and LM-OTS's randomizer C from the parent makes the re-signed bytes identical instead, and RFC 8554 Test Case 2 was built that way (see the reference implementation section), but that is not SP 800-208 compliant. The reference code tests both cases. Either way, bottom-leaf reuse after a rollback is fatal, so the real fix is state that cannot roll back.

### Splitting one key across devices

The hypertree is also how SP 800-208 spreads one public key over several hardware modules, since copying is forbidden. In a two-level HSS or XMSS^MT key, the top tree lives in one module and only signs roots of bottom trees held by other modules ([SP 800-208 §7](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-208.pdf)). The top module is a single point of failure, so the bottom keys should be generated up front. For XMSS^MT, every module must use the same SEED; for HSS, an external device assembles the signature pieces.

### Stateless: how SLH-DSA survives without a counter

Goldreich's stateless scheme picked a random leaf from a tree so large that collisions never happen; its signatures stayed above 1 MB. SPHINCS put a few-time signature under each bottom leaf, so a collision only means a few-time key signs twice. That cut the total height for SPHINCS-256 from 256 to 60 at 2^128 quantum security ([SPHINCS](https://sphincs-cr-yp-to.viacache.net/sphincs-20141001.pdf)).

In SLH-DSA the route is idx = bits of H\_msg(R, PK.seed, PK.root, M), so the signer cannot steer it. Everything above the bottom is deterministic: the same leaf always signs the same subtree root with the same bytes, so upper-layer OTS keys stay one-time even though they appear in many signatures.

Collisions at the bottom are expected, not exceptional. After q signatures, each FORS key has been used about q / 2^h times on average:

$$
\mathbb{E}[\text{uses per FORS key}] \approx \frac{q}{2^{h}} \qquad \text{e.g. } q = 2^{64},\ h = 63 \ \Rightarrow\ 2
$$

That is why FORS is designed for a small number of signatures per key, on the order of ten in the SPHINCS+ parameter sets ([SPHINCS+ spec](https://sphincs.org/data/sphincs+-r3.1-specification.pdf)), and why FIPS 205 rates its sets for at most 2^64 signatures per key ([FIPS 205 §11](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf)).

The [SP 800-230 draft, published in April 2026,](https://csrc.nist.gov/pubs/sp/800/230/ipd) takes this to the other extreme. Its six sets cap a key at 2^24 signatures and use a single XMSS layer (d = 1, h = 21 or 22), giving 3,856-byte signatures at category 1 ([SP 800-230 ipd, Table 1](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-230.ipd.pdf)). With so few signatures there is no need for many layers. The draft says the security depends entirely on adhering to the limit; it aims the sets at software, firmware and certificate signing and does not approve them for general-purpose use.

## Security: what the hypertree adds and what can go wrong

A hypertree is as strong as its weakest link: the one-time (or few-time) scheme, the tree hash, the key-derivation PRF, and the guarantee that every OTS key signs one value. Three concerns are specific to hypertrees: the sheer number of hash calls an attacker can target, the address bookkeeping that keeps those calls separate, and faults that make an upper-layer key sign twice.

### Why the composition is secure

A hypertree signature is a chain of d Merkle signatures. To forge, an attacker must break at least one link: forge an OTS (or FORS) signature, find a second preimage somewhere in some tree, or distinguish the key-derivation PRF from random. Proofs bound the forgery probability by summing these chances over every key and every node in the structure.

For LMS/HSS, RFC 8554 cites a bound from Fluhrer's analysis: with up to 2^64 keys, 2^120 hash compressions and a signing oracle, the forgery probability stays below 2^−129 ([RFC 8554 §9](https://www.rfc-editor.org/rfc/rfc8554.html)).

### Multi-target attacks, and why addresses are security-critical

A hypertree with h ≈ 64 contains an astronomical number of hash evaluations. If they all used the same untweaked function, an attacker trying to invert any one of T outputs would succeed T times more often, losing log₂ T bits of security. The fix in every standard is to make each call a different function, using a per-key public value plus the call's position:

- LMS prefixes every hash with I ‖ q ‖ i ‖ j (16 random bytes per tree, leaf, chain, step) or I ‖ r ‖ D for tree nodes.
- XMSS keys each call and XORs in bitmasks, both derived from SEED and the 32-byte ADRS ([RFC 8391 §2.5](https://www.rfc-editor.org/rfc/rfc8391.html)).
- SPHINCS+ introduced tweakable hash functions; FIPS 205 standardizes the "simple" form, e.g. F = SHAKE256(PK.seed ‖ ADRS ‖ M₁). The SPHINCS+ authors note that the simple form's security argument relies entirely on the random-oracle model ([SPHINCS+ spec](https://sphincs.org/data/sphincs+-r3.1-specification.pdf)).

The implementer's consequence: every address field is part of the security argument. A bug that leaves two hash calls with the same address (a forgotten layer number, a tree address truncated to 8 bytes, a type not cleared) still produces signatures that verify against your own verifier. Round-trip tests cannot catch it; only known-answer tests can.

### Fault attacks: grafting trees

Castelnovi, Martinelli and Prest showed a fault attack on the whole SPHINCS family, SLH-DSA's ancestor included ([ePrint 2018/102](https://eprint.iacr.org/2018/102)):

1. The attacker gets a normal signature, so an upper-layer WOTS key has signed the correct subtree root δ.
2. On a later signature through the same subtree, a single random fault corrupts the root computation, so the same WOTS key signs δ\* ≠ δ. The faulty signature is still valid, because the faulty authentication path is included.
3. Two signatures from one WOTS key leak chain values. The attacker searches for a subtree of its own whose root it can sign with those values, grafts it under the compromised leaf, and can then sign any message.

The paper reports that a check of the signature before release does not help, because the faulted signature verifies, and the authors found no specific countermeasure. Later work studies redundancy and caching defenses for SPHINCS+ ([Genêt, TCHES 2023](https://bmt.ub.rub.de/index.php/TCHES/article/download/10278/9726/9149)). Practical defenses: compute each subtree root twice and compare before signing it, or sign each subtree root once and cache that signature.

For stateful hypertrees, my own reading (the paper does not analyze them): an HSS signer that stores sig[i] once and copies it never re-signs a root, so this attack has nothing to fault during routine signing. An XMSS^MT signer that follows RFC 8391 Algorithm 16 literally recomputes and re-signs every layer's root on every signature, and is exposed in the same way as SPHINCS unless it caches.

### Quantum security and hash output length

Grover's algorithm square-roots preimage search, so the output length sets the quantum margin. FIPS 205 uses n = 16, 24 and 32 for categories 1, 3 and 5. SP 800-208 also approves truncated SHA-256/192 and SHAKE256/192 for LMS and XMSS ([SP 800-208 §4, §5](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-208.pdf)), and CNSA 2.0 guidance lists LMS with SHA-256/192 as the preferred choice for software and firmware signing ([summary](https://www.encryptionconsulting.com/comparing-slh-dsa-lms-and-xmss/)). Smaller n shrinks every part of the signature proportionally.

### Side channels

The chain positions in a Winternitz signature depend only on the public message digits, so signing time leaks nothing the signature does not already show. The secrets are the seeds fed into the PRF; on embedded devices that PRF call is the realistic power-analysis target, as with any keyed hash.

## Choosing h and d: sizes and costs

For a fixed capacity 2^h, every extra layer adds one OTS signature to every signature, while every layer removed doubles-and-more the work to build each tree. For h = 60 and n = 32 the useful range is narrow: below about 3 layers trees get too expensive to build, above about 12 the signatures grow past 25 KB.

With n-byte hashes and an OTS of len chains, a bare hypertree signature (no FORS, no index) costs:

$$
|\sigma_{HT}| = (h + d\cdot \mathrm{len})\cdot n \qquad \text{keygen} = 2^{h/d} \qquad \text{sign (no cache)} = d\cdot 2^{h/d} \qquad \text{verify} \approx d\cdot \mathrm{len}\cdot \tfrac{w-1}{2} + h
$$

Keygen and signing are counted in OTS key generations; verification in hash calls (half the chain on average). The SPHINCS authors summarize the shape: signing time grows exponentially as layers are removed; for h = 60, going from d = 60 to d = 12 raises d·2^(h/d) only from 120 to 384 ([SPHINCS](https://sphincs-cr-yp-to.viacache.net/sphincs-20141001.pdf)).

Worked trade-off for h = 60, n = 32, WOTS+ with w = 16 (len = 67), computed from the formulas above:

| Layers d | Tree height h′ | Hypertree signature bytes | Keygen (OTS keys) | Sign, no cache (OTS keys) | Verify (hash calls) |
| --- | --- | --- | --- | --- | --- |
| 2 | 30 | 6,208 | 1.1 × 10^9 | 2.1 × 10^9 | about 1,070 |
| 3 | 20 | 8,352 | 1.0 × 10^6 | 3.1 × 10^6 | about 1,570 |
| 4 | 15 | 10,496 | 32,768 | 131,072 | about 2,070 |
| 5 | 12 | 12,640 | 4,096 | 20,480 | about 2,580 |
| 6 | 10 | 14,784 | 1,024 | 6,144 | about 3,080 |
| 10 | 6 | 23,360 | 64 | 640 | about 5,100 |
| 12 | 5 | 27,648 | 32 | 384 | about 6,100 |
| 20 | 3 | 44,800 | 8 | 160 | about 10,100 |

Two things change the picture for stateful signers. Caching the current tree on each layer makes the per-signature cost close to one OTS signature, so a stateful key can afford fewer, taller layers than the "sign, no cache" column suggests. The cost becomes memory instead: about 2^(h′+1)·n bytes per cached tree (64 KB for h′ = 10, n = 32), plus a spike of 2^h′ key generations whenever a new subtree is needed, unless that work is spread over earlier signatures.

### Per-layer choices (HSS only)

Because HSS lets each level choose its own LMS height and LM-OTS width, the upper levels can trade differently from the bottom one:

- The top tree is built once, at key generation. Make it as tall as your key-generation budget allows; it sets how many bottom trees you can ever create.
- Lower trees are rebuilt every time they run out. Keep them small enough that a rebuild fits your worst-case signing latency, or rebuild them in the background ahead of time.
- Every level's OTS signature is verified on every signature, so a larger w at any level shrinks signatures but adds verification work for every verifier. Choose w for the verifier you care about, typically a constrained device in firmware signing.

### Starting points by use case

| Use case | Starting point | Why |
| --- | --- | --- |
| Firmware or boot images, up to about 2^20 signatures | HSS with L = 1 or 2 (e.g. H20, or H10/H10) | 1.8 to 3 KB signatures, cheap verification on the device |
| Signing service spread over several HSMs | Two-level HSS or XMSS^MT, top tree in one module | The layout SP 800-208 §7 describes for distributed keys |
| Signer that cannot keep state, unknown volume | SLH-DSA 128s (smallest) or 128f (fastest signing) | No counter to lose; 7.9 or 17.1 KB signatures |
| Signer that cannot keep state, at most 2^24 signatures | SP 800-230 sets, once final | 3,856-byte signatures, but only if the cap is guaranteed |
| One signature per time slot (validators, epochs) | Index derived from the clock, as leanSig does | The clock is the state; no counter to persist |

## Implementation guide

Build bottom-up and pin each layer with known-answer tests before moving up: addresses and encodings, then the OTS, then one tree, then the hypertree loop, then the wrapper and its state. Hypertree bugs rarely break round trips; they silently weaken domain separation, so only test vectors catch them.

### Build order

1. **Encodings and addresses.** All integers are big-endian. LMS uses u32/u16/u8 prefixes. XMSS and SLH-DSA use a 32-byte ADRS, but the tree-address field is 8 bytes in RFC 8391 and 12 bytes in FIPS 205. Setting a new type must clear the words after it. SLH-DSA's SHA-2 variants hash a compressed 22-byte ADRSc instead.
2. **OTS.** Digit extraction (coef in LMS, base\_2b in FIPS 205), the checksum and its left shift, the chain function. Test key generation from a seed against vectors, then sign/recover round trips.
3. **One tree.** Treehash, authentication path, root-from-signature. Test by rebuilding a published public key from its seed.
4. **The hypertree loop.** Index split and per-layer addresses. Test against full signature vectors.
5. **The wrapper.** Message randomization, wire format, strict parsing.
6. **State.** Persistence, reservation, exhaustion, regeneration of lower trees.

### What a stateful signer keeps

| Item | Size | Notes |
| --- | --- | --- |
| Seeds and key identifiers | n bytes each; per level in HSS | The only true secrets; everything else can be recomputed |
| Counters | 4 to 8 bytes | q per level (HSS) or one idx (XMSS^MT); must survive crashes |
| Current tree per layer | 2^(h′+1)·n bytes (64 KB for h′ = 10) | Makes authentication paths a lookup; or use a traversal algorithm |
| Signed child public keys or upper signatures | One OTS signature + path per layer | Computed once per subtree; also the cheapest fault defense |
| Next-tree buffer (optional) | Same as one tree | Built incrementally so a tree switch causes no latency spike |

For tall single trees, traversal algorithms keep O(h) nodes instead of the whole tree: Szydlo's algorithm (used by GMSS) and BDS (Buchmann, Dahmen and Schneider, PQCrypto 2008).

### Performance

- Hash calls are the whole cost. Leaves are independent, so parallelize leaf generation across cores and use multi-buffer SHA-256 or Keccak (4 or 8 lanes) where available.
- In SLH-DSA's SHA-2 functions, PK.seed is padded to one full hash block before ADRSc: 64 bytes for SHA-256, 128 for SHA-512 ([FIPS 205 §11.2](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf)). Compute the hash state after that first block once per key and resume from it on every call; it removes one compression function per hash.
- A stateless signer can still cache. The top tree of SLH-DSA never changes, so caching its nodes saves 2^h′ WOTS+ key generations per signature (one seventh of the hypertree work for 128s).

### Verifier checklist

- Parse by typecode and length; reject unknown types, wrong lengths, missing bytes and trailing bytes.
- HSS: reject unless Nspk + 1 = L, and check every level's types against what it signs. RFC 8554 requires a verifier to check each typecode and return INVALID on unknown or mismatched types ([RFC 8554 §9](https://www.rfc-editor.org/rfc/rfc8554.html)).
- Reject leaf indices ≥ 2^h.
- Verify every layer every time, including the signed public keys that look "cached".
- Verification needs no state, no secret and little memory; a streaming verifier can process one layer at a time.

### Testing

- **Known answers:** RFC 8554 Appendix F has two HSS test cases, one with the private seeds, so you can test key generation and signing, not just verification. NIST's ACVP repository publishes key generation, signing and verification vectors as JSON for both SLH-DSA and LMS ([usnistgov/ACVP-Server](https://github.com/usnistgov/ACVP-Server)).
- **Boundaries:** signatures at leaf 2^h′ − 1 and 2^h′ of each layer, the first signature after a lower tree is regenerated, the last signature before exhaustion, and the refusal after it.
- **Corruption:** flip bits in every field, truncate, append, and splice layers from two different keys.
- **Interop:** sign with yours, verify with another implementation, and the reverse.
- **Faults (for exposed devices):** inject a flipped bit into a subtree root computation and confirm the countermeasure refuses to sign.

### Libraries to compare against

| Scheme | Library | Language | Note |
| --- | --- | --- | --- |
| HSS/LMS | [cisco/hash-sigs](https://github.com/cisco/hash-sigs) | C | The example implementation RFC 8554 points to (Appendix E) |
| HSS/LMS | [hbs-lms](https://docs.rs/crate/hbs-lms/latest) (Fraunhofer AISEC) | Rust | no\_std capable; states binary compatibility with hash-sigs |
| XMSS, XMSS^MT | [xmss-reference](https://github.com/joostrijneveld/xmss-reference) | C | The reference implementation of RFC 8391 |
| SLH-DSA | [slh-dsa](https://docs.rs/slh-dsa) (RustCrypto) | Rust | Carries a warning that it has never been independently audited |
| SLH-DSA | [fips205](https://docs.rs/crate/fips205/0.5.0) | Rust | All twelve parameter sets |
| XMSS-style, Ethereum | [leanSig](https://github.com/leanEthereum/leanSig) | Rust | Generalized XMSS for Ethereum consensus |

### Bugs that pass round-trip tests

- Numbering HSS levels from the bottom, or XMSS^MT layers from the top.
- Setting an ADRS type without clearing the words after it, or writing the tree address into the wrong width.
- Using the child's index instead of the parent's (leaf >> (j + 1)) in a node address.
- A wrong checksum shift (ls in LMS; the csum shift in FIPS 205 Algorithm 7).
- Incrementing the counter after the signature leaves, or persisting it through a write cache.
- In a distributed XMSS^MT key, modules that do not share the same SEED.

## Reference implementations, tested against official vectors

Two pure-Python implementations accompany this note ([download them here](/assets/notes/merkle-hypertrees/code/README.md)): HSS/LMS per RFC 8554, and SLH-DSA per FIPS 205, written so its hypertree functions match the generic pseudocode above line for line. Both reproduce official test vectors byte for byte. They use only the Python standard library and are teaching code: slow, and without fault or side-channel hardening.

| File | Implements | Checked against | Result |
| --- | --- | --- | --- |
| [hss\_lms.py](/assets/notes/merkle-hypertrees/code/hss_lms.py) | LM-OTS, LMS, HSS key generation, stateful signing with Algorithm 8 regeneration, persistence hook, verification | RFC 8554 Appendix F, test cases 1 and 2 | Both verify; Test Case 2's public key and full signature rebuilt from its top-level SEED and I alone |
| [test\_hss\_lms.py](/assets/notes/merkle-hypertrees/code/test_hss_lms.py) | 32 checks | Also: every LM-OTS set, 50 bit-flips, truncation, splicing, a full 1,024-signature exhaustion with 31 regenerations, crash and rollback behaviour | All pass in about 3 seconds |
| [slh\_dsa.py](/assets/notes/merkle-hypertrees/code/slh_dsa.py) | All 12 FIPS 205 sets, SHA2 and SHAKE, internal and pure interfaces, deterministic and hedged | NIST ACVP SLH-DSA sigGen vectors | 336 of 336 pass: every test for all 12 sets, both interfaces, deterministic and hedged (the pre-hash HashSLH-DSA groups are not implemented) |

One result is worth knowing even if you never run the code. RFC 8554 publishes Test Case 2's private seeds but not how its second-level key and randomizers were made. They follow Appendix A's format with special values in the chain-number slot: C = H(I ‖ u32(q) ‖ u16(0xFFFD) ‖ u8(0xFF) ‖ SEED), child SEED uses 0xFFFE, and child I is the first 16 bytes with 0xFFFF, where q is the parent leaf. hss\_lms.py offers it as an option (deterministic=True). The default follows SP 800-208 §6.1 and draws every tree's I and SEED from the random generator.

### The HSS hypertree logic

This is the part of hss\_lms.py that is specific to the hypertree; everything else is one LMS tree.

```python
def _new_child(self, parent, lms, ots):
    """Create the child tree that parent's next leaf (parent.q) will certify."""
    if self.deterministic:
        I, seed = derive_child(parent.I, parent.q, parent.seed)
    else:
        I, seed = self.rng(16), self.rng(lms.m)
    child = LmsPrivateKey.generate(lms, ots, I, seed)
    pub = child.public_key()
    signed_pub = parent.sign(pub, deterministic=self.deterministic) + pub
    return child, signed_pub

def _refresh_exhausted_levels(self):
    """RFC 8554 Algorithm 8: regenerate exhausted lower levels before signing."""
    if self.levels[-1].remaining > 0:
        return
    d = self.L - 1
    while d > 0 and self.levels[d].remaining == 0:
        d -= 1
    if self.levels[d].remaining == 0:      # only possible when d == 0
        raise KeyExhausted("HSS key exhausted")
    for i in range(d + 1, self.L):
        old = self.levels[i]
        self.levels[i], self.signed_pubs[i] = self._new_child(self.levels[i - 1], old.lms, old.ots)

def sign(self, message, persist, C=None):
    self._refresh_exhausted_levels()
    bottom_sig = self.levels[-1].sign(message, C, deterministic=self.deterministic)
    persist(self)                          # durable state first, signature second
    return u32(self.L - 1) + b"".join(self.signed_pubs[1:]) + bottom_sig

def hss_verify(message, public_key, signature):
    L = int.from_bytes(public_key[:4], "big")
    key = public_key[4:]
    Nspk = int.from_bytes(signature[:4], "big")
    if Nspk + 1 != L or not 1 <= L <= 8:
        return False
    off = 4
    for _ in range(Nspk):                  # walk down: each level certifies the next
        sig_len = lms_signature_length_at(signature, off)
        lms_sig = signature[off:off + sig_len]
        off += sig_len
        _, pub_end = parse_lms_public_key(signature, off)
        child_pub = signature[off:pub_end]
        off = pub_end
        if not lms_verify(child_pub, key, lms_sig):
            return False
        key = child_pub
    sig_len = lms_signature_length_at(signature, off)
    if off + sig_len != len(signature):    # no trailing or missing bytes
        return False
    return lms_verify(message, key, signature[off:])
```

The excerpt drops the try/except that turns parse errors into False; the file has it.

### Running the tests

```text
python3 test_hss_lms.py rfc8554.txt
python3 test_slh_dsa.py prompt.json expectedResults.json [--all]
```

The [README](/assets/notes/merkle-hypertrees/code/README.md) has the download commands for the RFC text and the ACVP JSON files, plus porting notes for Rust.

## Where the design is moving

Recent work is shrinking the hypertree when the signature count is bounded: NIST's limited-use SLH-DSA sets drop to one layer, and Ethereum's leanSig keeps a two-level split for key management but removes the OTS signatures between levels.

### Bounded-use SLH-DSA

NIST decided in March 2025 to add SLH-DSA variants with a smaller maximum number of signatures, pointing to Fluhrer and Dang's parameter study (ePrint 2024/018) and suggesting a target near 2^24 ([pqc-forum](https://groups.google.com/a/list.nist.gov/g/pqc-forum/c/vtMTuE_3u-0)). NIST also said it favours sets whose security degrades slowly under moderate overuse. The result is the SP 800-230 draft with d = 1, covered in the stateful-versus-stateless section. The lesson for designers: layers exist to make 2^64 signatures affordable, and with 2^24 they are dead weight.

### leanSig: a split tree without the hypertree's certificates

The Ethereum Foundation's leanSig targets the consensus layer, where each validator signs once per slot ([ePrint 2025/055](https://eprint.iacr.org/2025/055)). Aggregation is meant to come from hash-based succinct arguments rather than from the signature scheme itself, and later notes refine the encoding ([ePrint 2025/1332](https://eprint.iacr.org/2025/1332), [ePrint 2025/889](https://eprint.iacr.org/2025/889)).

Its key structure is instructive next to a hypertree. Per the library source ([generalized\_xmss.rs](https://raw.githubusercontent.com/leanEthereum/leanSig/main/src/signature/generalized_xmss.rs)):

- The lifetime tree of depth LOG\_LIFETIME (32 in the current parameter sets, per [these parameter notes](https://notes.ethereum.org/@b-wagn/r1kf3JEbGx)) is split at the midpoint into one top tree and sqrt(LIFETIME) bottom trees.
- The top tree's leaves are the bottom trees' roots directly. There is no OTS signature between levels, so a signature carries a single combined authentication path.
- Key generation computes only the bottom trees inside the requested activation interval, keeps their roots, and builds a possibly sparse top tree from them.
- The secret key always holds the full top tree and two consecutive bottom trees; advance\_preparation computes the next bottom tree and drops the oldest.

Compared with a hypertree, this trades lazy generation for a smaller and simpler signature. A hypertree can create a subtree years later because a certificate (an OTS signature) binds it to the root at that time. A plain split tree needs every bottom root in the active range before the public key exists, which is why leanSig works with activation intervals. My own observation, not the authors': for SNARK aggregation, each hypertree layer would add another Winternitz verification to the circuit for every signature, so a single path is the cheaper statement to prove.

The state problem also looks different: the index is the slot number, so the clock is the counter. The library still requires that each pair of secret key and epoch never be used twice to sign ([leanSig README](https://github.com/leanEthereum/leanSig)).

## Sources and further reading

If you read only three: RFC 8554 Section 6 for the simplest stateful hypertree, FIPS 205 Sections 6 and 7 for the cleanest pseudocode, and SP 800-208 Sections 7 to 9 for what running a stateful key in production really involves.

**Standards**

- [RFC 8554: Leighton-Micali Hash-Based Signatures](https://www.rfc-editor.org/rfc/rfc8554.html) (LMS, LM-OTS, HSS; Appendix F test vectors)
- [RFC 8391: XMSS](https://www.rfc-editor.org/rfc/rfc8391.html) (WOTS+, XMSS, XMSS^MT)
- [FIPS 205: Stateless Hash-Based Digital Signature Standard](https://nvlpubs.nist.gov/nistpubs/FIPS/NIST.FIPS.205.pdf) (SLH-DSA)
- [NIST SP 800-208: Recommendation for Stateful Hash-Based Signature Schemes](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-208.pdf)
- [NIST SP 800-230 (initial public draft)](https://csrc.nist.gov/pubs/sp/800/230/ipd), limited-use SLH-DSA parameter sets ([PDF](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-230.ipd.pdf))
- [RFC 9802](https://www.rfc-editor.org/rfc/rfc9802): HSS, XMSS and XMSS^MT in X.509

**Papers**

- [SPHINCS: practical stateless hash-based signatures](https://sphincs-cr-yp-to.viacache.net/sphincs-20141001.pdf) (Bernstein et al., Eurocrypt 2015): the hyper-tree, Goldreich comparison, h/d trade-off
- [SPHINCS+ specification, round 3.1](https://sphincs.org/data/sphincs+-r3.1-specification.pdf) and [The SPHINCS+ signature framework (ePrint 2019/1086)](https://eprint.iacr.org/2019/1086): tweakable hashes, FORS
- [GMSS: Merkle signatures with virtually unlimited signature capacity](https://link.springer.com/content/pdf/10.1007/978-3-540-72738-5_3.pdf) (Buchmann, Dahmen, Klintsevich, Okeya, Vuillaume, ACNS 2007)
- [Grafting Trees: a fault attack against the SPHINCS framework (ePrint 2018/102)](https://eprint.iacr.org/2018/102)
- [Genêt, fault countermeasures for SPHINCS+ (TCHES 2023)](https://bmt.ub.rub.de/index.php/TCHES/article/download/10278/9726/9149)
- [Hash-based multi-signatures for post-quantum Ethereum (ePrint 2025/055)](https://eprint.iacr.org/2025/055), with follow-ups [ePrint 2025/889](https://eprint.iacr.org/2025/889) and [ePrint 2025/1332](https://eprint.iacr.org/2025/1332)

**Discussion and comparisons**

- [NIST pqc-forum: plan for SLH-DSA with fewer signatures](https://groups.google.com/a/list.nist.gov/g/pqc-forum/c/vtMTuE_3u-0)
- [wolfSSL: LMS versus XMSS versus SLH-DSA](https://www.wolfssl.com/lms-versus-xmss-versus-slh-dsa/)
- [Encryption Consulting: comparing SLH-DSA, LMS and XMSS](https://www.encryptionconsulting.com/comparing-slh-dsa-lms-and-xmss/) (CNSA 2.0 context)
- [leanSig parameter notes](https://notes.ethereum.org/@b-wagn/r1kf3JEbGx)
- [NHIMG glossary: Hypertree](https://nhimg.org/glossary/hypertree/), the entry that started this note

**Code and test vectors**

- [cisco/hash-sigs](https://github.com/cisco/hash-sigs) (C, HSS/LMS)
- [hbs-lms](https://docs.rs/crate/hbs-lms/latest) (Rust, HSS/LMS)
- [xmss-reference](https://github.com/joostrijneveld/xmss-reference) (C, XMSS and XMSS^MT)
- [RustCrypto slh-dsa](https://docs.rs/slh-dsa) and [fips205](https://docs.rs/crate/fips205/0.5.0) (Rust, SLH-DSA)
- [leanSig](https://github.com/leanEthereum/leanSig) and its [generalized\_xmss.rs](https://raw.githubusercontent.com/leanEthereum/leanSig/main/src/signature/generalized_xmss.rs) (Rust)
- [NIST ACVP-Server JSON vectors](https://github.com/usnistgov/ACVP-Server) (SLH-DSA and LMS keyGen, sigGen, sigVer)
