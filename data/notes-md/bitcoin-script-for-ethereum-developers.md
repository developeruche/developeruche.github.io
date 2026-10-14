I spend most of my time in Ethereum's execution layer, where a transaction is a message to a stateful machine and "multisig" usually means a smart contract. For the past few weeks I have been studying Bitcoin from the inside, using _Mastering Bitcoin_ as my guide. This article is the write-up of that study.

There is one destination: by the end you should be able to look at any Bitcoin multisig setup (a 2012-era P2SH address, a Lightning channel, a Taproot vault, a MuSig2 key) and explain exactly what is on chain, what the network checks, what it costs, and why it was designed that way. Getting there takes a staircase, and every step depends on the one below it:

1. **Foundations**: what Bitcoin is, the UTXO model, and the cryptography it relies on.
2. **The transaction**: its bytes, its identifiers, its weight, and its life from wallet to block.
3. **Script**: the stack machine that decides whether a coin may move, and the signatures it checks.
4. **The output types**, in historical order: P2PK, P2PKH, bare multisig, OP_RETURN, P2SH.
5. **SegWit**: why it was needed, how it was deployed as a soft fork, P2WPKH and P2WSH.
6. **Taproot**: Schnorr signatures, MAST, key tweaking, P2TR and Tapscript.
7. **Time**: absolute and relative timelocks.
8. **Multisig**, the main event: five generations of it, compared byte for byte.
9. **Scripts in the wild**: Lightning, HTLCs, Ark, data carriers, and covenant proposals.

All numbers in this article (addresses, hashes, transaction weights, signature checks) were reproduced with small Python programs, most of which are included.

> **Notation.** $G$ is the secp256k1 generator, lowercase letters are scalars (private keys, nonces), uppercase letters are curve points (public keys). $H_{tag}(\cdot)$ is a BIP340 tagged hash. `<x>` in a script means "push the bytes of x". Hex in scripts is shown in the byte order it appears on the wire unless stated otherwise. "vB" means virtual bytes, "WU" means weight units.

## Contents

- **Part I: Foundations** — 1. What Bitcoin is, precisely · 2. The UTXO model, for account-model brains · 3. The cryptographic toolkit
- **Part II: The Transaction** — 4. Anatomy of a transaction, byte by byte · 5. The life cycle of a transaction
- **Part III: Script, the Machine Behind Every Coin** — 6. How Script executes · 7. Signatures: what OP_CHECKSIG actually checks
- **Part IV: The Legacy Output Types** — 8. P2PK · 9. P2PKH · 10. P2MS: bare multisig · 11. OP_RETURN · 12. P2SH
- **Part V: Segregated Witness** — 13. The problems SegWit solved · 14. How SegWit was deployed as a soft fork · 15. P2WPKH, P2WSH and their nested forms · 16. Weight, the witness discount, and BIP143
- **Part VI: Taproot** — 17. Schnorr signatures (BIP340) · 18. MAST and pay-to-contract · 19. P2TR: the Taproot construction (BIP341) · 20. Tapscript (BIP342)
- **Part VII: The Output Types Side by Side, and Time** — 21. The output-type map · 22. Timelocks: programming with time
- **Part VIII: Multisig, Five Generations** — 23. The multisig design space · 24. Generations 1 to 3 · 25. Generation 4: Tapscript multisig · 26. Generation 5: MuSig2 · 27. Threshold signatures with FROST · 28. Hybrid designs · 29. One 2-of-3 policy, eight encodings · 30. Running multisig in practice
- **Part IX: Scripts in the Wild** — 31. Lightning's scripts · 32. HTLCs, Ark, data carriers and covenants
- **Part X: The Whole Picture** — 33. The evolution in one page · References · Appendix: opcode and size cheat sheet

---

## Part I: Foundations

### 1. What Bitcoin is, precisely

Every digital-money design has to answer three questions: is this money authentic, can it be spent only once, and can only its owner spend it? Before 2008 the second question was always answered by a clearing house that saw every transaction. Bitcoin's contribution was to answer it without one. _Mastering Bitcoin_ breaks the system into four parts:

1. **A peer-to-peer network** that gossips transactions and blocks between equal peers.
2. **A public journal**, the blockchain: an append-only chain of blocks, each committing to its parent by hash.
3. **Consensus rules** that every full node applies independently to every transaction and block.
4. **Proof of work**, a lottery that decides who appends the next block and makes rewriting history expensive.

The unit of account is the satoshi: 1 BTC = $10^8$ sat. New coins enter circulation only through the _block subsidy_, which starts at 50 BTC and halves every 210,000 blocks (roughly four years). Bitcoin Core computes it with a right shift:

$$ \text{subsidy}(h) = \left\lfloor \frac{50 \cdot 10^{8}}{2^{\lfloor h / 210000 \rfloor}} \right\rfloor \ \text{sat} $$

The shift drops fractions of a satoshi, so the total supply is a geometric series with floors:

$$ \sum_{i=0}^{32} 210000 \cdot \left\lfloor \frac{5 \cdot 10^{9}}{2^{i}} \right\rfloor = 2{,}099{,}999{,}997{,}690{,}000 \ \text{sat} \approx 20{,}999{,}999.9769 \ \text{BTC} $$

Only 33 halving eras pay a non-zero subsidy; after the 33rd halving it rounds down to zero, and miners are paid by fees alone.

Four roles show up throughout this article. **Full nodes** download and verify everything and are the only parties that enforce the rules. **Miners** run full nodes, choose which transactions go into blocks, and do the proof of work. **Wallets** hold keys and build transactions. **Lightweight clients** verify block headers and Merkle proofs but trust that miners followed the rules.

One distinction will come up again and again: **consensus versus policy**. Consensus rules decide whether a block is valid; break one and every full node rejects your block forever. Policy (also called _standardness_) is what a node is willing to relay and put in its own block templates by default. Many limits people quote as "Bitcoin rules" (the dust limit, OP_RETURN size, three keys for bare multisig) are policy. Policy can change in any software release; consensus changes need a soft fork. Keep the two apart and much of Bitcoin's design starts to make sense.

### 2. The UTXO model, for account-model brains

Ethereum's state is a map from addresses to accounts (nonce, balance, code, storage), and a transaction is a message that mutates it. Bitcoin's state is a **set of unspent transaction outputs (UTXOs)**. Each UTXO is identified by an _outpoint_ (the id of the transaction that created it plus an output index) and carries two things: an **amount** and a **locking script** (`scriptPubKey`) that states the conditions for spending it. Bitcoin Core also stores the creation height and whether it came from a coinbase transaction, because some rules depend on them.

A transaction consumes whole UTXOs and creates new ones. Formally, with $U$ the UTXO set, a non-coinbase transaction $T$ with inputs $I$ and outputs $O$ is valid when:

$$ \forall i \in I:\ i.\text{outpoint} \in U \ \wedge\ \text{Script}\big(i.\text{unlock},\ U[i.\text{outpoint}].\text{lock},\ T\big) = \text{true} $$

$$ \sum_{i \in I} U[i.\text{outpoint}].\text{amount} \ \ge \ \sum_{o \in O} o.\text{amount} $$

and the new state is $U' = \big(U \setminus \{i.\text{outpoint}\}_{i \in I}\big) \cup \{(\text{txid}(T), j) \mapsto O_j\}$. The difference between the two sums is the fee, and it goes to whoever mines the block. There is no fee field.

Some consequences surprise people coming from accounts:

- **Outputs are spent in full.** To pay 0.2 BTC from a 1 BTC UTXO you create two outputs: 0.2 BTC to the payee and about 0.8 BTC back to yourself (a _change output_). Forget the change output and the miner keeps the difference.
- **There are no nonces.** Replay protection is structural: an outpoint can be spent only once in a valid chain.
- **"Balance" is a wallet concept.** The protocol only knows outputs. A wallet sums the UTXOs it can unlock, and choosing which to spend (_coin selection_) is a wallet decision with fee and privacy trade-offs.
- **Validation is per input and stateless.** Each input's script is checked against the output it spends, using only the transaction and the outputs it spends. Inputs can be verified in parallel, and a script's result never depends on chain state beyond what the transaction itself commits to (heights and times enter only through timelock fields).
- **The UTXO set is the expensive resource.** Every full node keeps every UTXO in a fast database (several gigabytes today). Many design decisions, from dust policy to SegWit's discount, aim to keep that set small.

The book uses a land-registry analogy: bitcoins are not objects you hand over; they are entries in a database that thousands of nodes keep, and a transaction is the evidence that convinces them to update it. The comparison with Ethereum:

| |Ethereum|Bitcoin|
|---|---|---|
|State|Accounts (nonce, balance, code, storage)|Set of unspent outputs (amount + locking script)|
|Transaction|Message from an account, executed by the EVM|Consumes whole outputs, creates new ones|
|Replay protection|Account nonce, chain id|Each outpoint can be spent once|
|Who may spend|Signature recovers the sender; contracts for anything else|A predicate attached to each output|
|Programmability|Turing complete, persistent storage, gas metered|Not Turing complete, stateless predicates, hard limits instead of gas|
|Fee|gas used × (base fee + tip), base fee burned|Implicit: inputs minus outputs, priced per virtual byte, all to the miner|
|A failing transaction|Reverts but still pays gas|Is invalid, never confirms, pays nothing|
|Multisig|A contract (e.g. a Safe) holds the funds|Native: a script template or an aggregated key|

That last row is where we are heading. In Bitcoin, multisig is not an application; it is a property of the coin itself.

The book also gives a vocabulary table that shows how the same two ideas have been renamed as the protocol evolved. _Authorization_ is the statement of who may spend; _authentication_ is the proof that the spender is one of them:

|Era|Authorization (in the output)|Authentication (in the spend)|
|---|---|---|
|Whitepaper|Public key|Signature|
|Original Bitcoin (legacy)|Output script (`scriptPubKey`)|Input script (`scriptSig`)|
|SegWit|Witness program|Witness structure|

### 3. The cryptographic toolkit

#### Hash functions

Bitcoin uses a handful of hash constructions, and knowing which one is used where saves a lot of confusion:

|Name|Definition|Output|Used for|
|---|---|---|---|
|SHA256|SHA-256|32 B|P2WSH script commitments, Taproot sighash sub-hashes, Lightning payment hashes|
|HASH256 (SHA256d)|SHA256(SHA256(x))|32 B|txid, wtxid, block hashes, Merkle trees, base58 checksums, legacy and SegWit v0 (BIP143) sighashes|
|RIPEMD160|RIPEMD-160|20 B|Building block of HASH160|
|HASH160|RIPEMD160(SHA256(x))|20 B|P2PKH, P2SH, P2WPKH commitments|
|Tagged hash|$H_{tag}(x) = \text{SHA256}(\text{SHA256}(tag) \Vert \text{SHA256}(tag) \Vert x)$|32 B|Everything in BIP340/341/342 (Schnorr challenges, TapLeaf, TapBranch, TapTweak, TapSighash)|

Tagged hashes (introduced with Taproot) give every use of SHA256 its own domain, so a hash computed for one purpose can never be reinterpreted as a hash for another.

#### The secp256k1 curve

Bitcoin's keys live on the elliptic curve secp256k1 (from the SEC 2 standard):

$$ y^2 \equiv x^3 + 7 \pmod p, \qquad p = 2^{256} - 2^{32} - 977 $$

The points on this curve form a group of prime order

$$ n = \texttt{0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141} \approx 1.158 \times 10^{77} $$

generated by a fixed point $G$. A **private key** is a scalar $k \in [1, n-1]$ and the **public key** is the point $K = kG$. Computing $K$ from $k$ is fast (double-and-add); recovering $k$ from $K$ is the elliptic curve discrete logarithm problem, believed to be infeasible for classical computers. The whole group law fits in a few lines of Python:

```python
P = 2**256 - 2**32 - 977
N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
G = (0x79BE667EF9DCBBAC55A06295CE870B07029BFCDB2DCE28D959F2815B16F81798,
     0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8)

def point_add(p1, p2):
    if p1 is None: return p2                      # None is the point at infinity
    if p2 is None: return p1
    if p1[0] == p2[0] and p1[1] != p2[1]: return None
    if p1 == p2:   # tangent slope for doubling
        lam = 3 * p1[0] * p1[0] * pow(2 * p1[1], P - 2, P) % P
    else:          # chord slope for addition
        lam = (p2[1] - p1[1]) * pow(p2[0] - p1[0], P - 2, P) % P
    x3 = (lam * lam - p1[0] - p2[0]) % P
    return (x3, (lam * (p1[0] - x3) - p1[1]) % P)

def point_mul(p, k):                              # double-and-add
    r = None
    for i in range(256):
        if (k >> i) & 1: r = point_add(r, p)
        p = point_add(p, p)
    return r

k = 0x1E99423A4ED27608A15A2616A2B0E9E52CED330AC530EDCC32C8FFC6A526AEDD   # the book's example key
K = point_mul(G, k)
# K.x = f028892bad7ed57d2fb57bf33081d5cfcf6f9ed3d3d7f159c2e2fff579dc341a
# K.y = 07cf33da18bd734c600b96a72bbc4749d5141c90ec8ac328ae52ddfe2e505bdb
```

(This is the textbook formula, not constant-time code. Never sign real transactions with it.)

#### Three ways to write a public key

|Encoding|Bytes|Layout|Where|
|---|---|---|---|
|Uncompressed|65|`04` ‖ x ‖ y|Early Bitcoin; non-standard in SegWit|
|Compressed|33|`02` (y even) or `03` (y odd) ‖ x|Legacy and SegWit v0 scripts|
|x-only|32|x, with y implicitly even|BIP340 Schnorr, Taproot|

Compression works because for a given $x$ there are only two valid $y$ values, $y$ and $p - y$, and exactly one of them is even. The book's key has an odd $y$, so its compressed form is `03f028…341a`. x-only keys go one step further: BIP340 simply declares that every public key is the even-$y$ point with that $x$, and signers negate their secret key when needed to make that true. That saves a byte everywhere and, as we will see, simplifies aggregation.

Note the trap the book points out: the compressed and uncompressed encodings of the same key hash to _different_ values, so one private key yields two different legacy addresses.

#### Key tweaking

Because the map $k \mapsto kG$ is linear, anyone who knows a public key $K$ and a scalar $t$ can compute

$$ K' = K + tG \quad\text{and only the key owner can compute}\quad k' = k + t \pmod n, \ \text{with}\ k'G = K'. $$

$t$ is called a **tweak**. This one identity powers BIP32 non-hardened derivation (a watch-only wallet derives child public keys from an xpub), pay-to-contract (the tweak commits to a contract), Lightning's per-commitment keys, and Taproot itself. Remember it; it returns in Part VI.

#### From keys and scripts to addresses

An address is not an account. It is a human-friendly, checksummed encoding of **an output script template plus the data that fills it**. Your wallet decodes the address back into a `scriptPubKey` and puts that in the output. Two encodings exist.

**Base58Check** (legacy) is `base58(version || payload || first 4 bytes of SHA256d(version || payload))`. The base58 alphabet drops `0`, `O`, `I` and `l` to avoid misreading. The version byte determines the leading character:

|Version byte|Prefix|Meaning|
|---|---|---|
|`0x00`|`1`|P2PKH, payload = HASH160(pubkey)|
|`0x05`|`3`|P2SH, payload = HASH160(redeem script)|
|`0x6f` / `0xc4`|`m`,`n` / `2`|Testnet P2PKH / P2SH|
|`0x80`|`5`, `K`, `L`|WIF private key (not an address)|

```python
import hashlib
def sha256(b): return hashlib.sha256(b).digest()
def hash160(b): return hashlib.new("ripemd160", sha256(b)).digest()

B58 = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
def b58check(payload: bytes) -> str:
    data = payload + sha256(sha256(payload))[:4]
    n, out = int.from_bytes(data, "big"), ""
    while n:
        n, r = divmod(n, 58)
        out = B58[r] + out
    return "1" * (len(data) - len(data.lstrip(b"\0"))) + out   # leading zero bytes -> '1'

compressed = bytes.fromhex("03f028892bad7ed57d2fb57bf33081d5cfcf6f9ed3d3d7f159c2e2fff579dc341a")
print(b58check(b"\x00" + hash160(compressed)))   # 1J7mdg5rbQyUHENYdx39WVWK7fsLpEoXZy
```

The same key in uncompressed form gives `1424C2F4bC9JidNjjTUZCbUxv6Sa1Mt62x`: same private key, different address.

**Bech32 and bech32m** (BIP173, BIP350) were designed for SegWit. An address is a human-readable part (`bc` for mainnet, `tb` for testnets), the separator `1`, then 5-bit characters: the witness version (`q` = 0, `p` = 1, …), the witness program, and a 6-character BCH checksum. The alphabet is a single case, which makes addresses easier to read aloud and smaller in QR codes, and the code is guaranteed to detect any error affecting up to 4 characters. Bech32 had one flaw: if an address ends in `p`, you can insert or delete `q`s just before that final `p` without breaking the checksum. That was harmless for SegWit v0, whose programs can only be 20 or 32 bytes, but dangerous for future versions with flexible lengths, so v1+ addresses use **bech32m**, which differs only in the constant XORed into the checksum (`1` versus `0x2bc830a3`). The book key's P2WPKH address is `bc1qh0q7g23e6pdye3sh2ttfvwmld8gfhvnmmfxuck`.

|Prefix|Output type|Encoding|
|---|---|---|
|`1…`|P2PKH|Base58Check|
|`3…`|P2SH (including nested SegWit)|Base58Check|
|`bc1q…` (42 chars)|P2WPKH|bech32|
|`bc1q…` (62 chars)|P2WSH|bech32|
|`bc1p…` (62 chars)|P2TR|bech32m|
|`bc1pfeessrawgf`|P2A (pay-to-anchor)|bech32m|

---

## Part II: The Transaction

### 4. Anatomy of a transaction, byte by byte

A transaction is a short, flat byte string. Here is the full layout in the extended (SegWit, BIP144) serialization:

|Field|Size|Notes|
|---|---|---|
|`version`|4 B, little-endian|1 or 2 (2 enables BIP68 relative timelocks); 3 marks a TRUC transaction under relay policy|
|`marker`, `flag`|1 B + 1 B|`00 01`, present only if some input has witness data|
|input count|compactSize|at least 1|
|↳ outpoint|32 B txid + 4 B index|which UTXO is being spent|
|↳ `scriptSig`|compactSize length + bytes|the legacy unlocking script; empty for native SegWit|
|↳ `sequence`|4 B|replacement signalling, relative timelocks (see below)|
|output count|compactSize|at least 1|
|↳ amount|8 B, little-endian|in satoshis|
|↳ `scriptPubKey`|compactSize length + bytes|the locking script|
|witness|per input: item count, then length-prefixed items|one stack per input, no overall count|
|`locktime`|4 B|absolute timelock (height or time)|

Lengths use **compactSize**: one byte for values up to 252, otherwise a marker byte `fd`, `fe` or `ff` followed by a 2, 4 or 8 byte little-endian integer. The marker trick is neat: in the original format the byte after `version` is the input count, and a transaction cannot have zero inputs, so `00` unambiguously announces the extended format to new software while old software never sees it (nodes strip witnesses when talking to peers that do not understand them).

#### A real transaction, decoded

The book's running example is Alice's payment to Bob's store, transaction `466200308696215bbc949d5141a49a4138ecdfdfaa2a8029c1f9bcecd1f96177`. All 194 bytes:

```text
01000000                                                          version = 1
00 01                                                             segwit marker, flag
01                                                                1 input
  eb3ae38f27191aa5f3850dc9cad00492b88b72404f9da135698679268041c54a  prev txid (internal byte order)
  01000000                                                        prev output index = 1
  00                                                              scriptSig length = 0
  ffffffff                                                        sequence
02                                                                2 outputs
  204e000000000000                                                20,000 sat
  22 5120 3b41daba4c9ace578369740f15e5ec880c28279ee7f51b07dca69c7061e07068
                                                                  34-byte script: OP_1 <32 bytes>  (P2TR)
  f824010000000000                                                75,000 sat
  16 0014 7752c165ea7be772b2c0acb7f4d6047ae6f4768e                22-byte script: OP_0 <20 bytes>  (P2WPKH)
01                                                                witness for input 0: 1 item
  41 cf5efe2d…c83e8171301                                         65 bytes: 64-byte Schnorr sig + 0x01
00000000                                                          locktime = 0
```

Reading it as a protocol engineer:

- The input spends output 1 of transaction `4ac54180…8fe33aeb`. The txid appears reversed because Bitcoin shows hashes in **display byte order** (big-endian, as if the digest were a number) but stores them in **internal byte order**. Every Bitcoin developer gets bitten by this exactly once.
- The `scriptSig` is empty and the witness holds a single 65-byte item. That shape (one item, 64 or 65 bytes, spending a version-1 output) is a **Taproot key-path spend**: a BIP340 Schnorr signature plus an explicit `SIGHASH_ALL` byte.
- Output 0 pays 20,000 sat to a P2TR script (Alice's change, `bc1p8dqa4wjvnt890qmfws83te0v3qxzsfu7ul63kp7u56w8qc0qwp5qv995qn`); output 1 pays 75,000 sat to a P2WPKH script (Bob's store, `bc1qwafvze0200nh9vkq4jmlf4sy0tn0ga5w0zpkpg`).
- The previous output held 100,000 sat, so the fee is $100{,}000 - 20{,}000 - 75{,}000 = 5{,}000$ sat. Nothing in the transaction says so; nodes learn the input amount from their UTXO set.

#### Two identifiers

$$ \text{txid} = \text{SHA256d}(\text{tx without marker, flag, witness}), \qquad \text{wtxid} = \text{SHA256d}(\text{full serialization}) $$

For this transaction the txid is `4662…6177` and the wtxid is `f7cdbc7cf8b910d35cc69962e791138624e4eae7901010a6da4c02e7d238cdac`. The txid deliberately excludes signatures; Part V explains why that matters so much. Outpoints and the block header's Merkle root use txids; transaction relay (BIP339) and the SegWit witness commitment use wtxids.

#### Weight and virtual size

Blocks are limited to 4,000,000 **weight units**. Bytes outside the witness weigh 4 WU each; witness bytes weigh 1 WU:

$$ \text{weight} = 4 \cdot \text{base\_size} + \text{witness\_size} = 3 \cdot \text{base\_size} + \text{total\_size}, \qquad \text{vsize} = \left\lceil \frac{\text{weight}}{4} \right\rceil $$

Alice's transaction has a 125-byte base serialization and 194 bytes in total, so $3 \cdot 125 + 194 = 569$ WU and 143 vB, exactly what `bitcoin-cli getrawtransaction … 2` reports. The fee rate is $5000 / 143 \approx 35$ sat/vB. Fee rates are always quoted per virtual byte (or per weight unit), because block space is what miners sell.

#### Fields whose meaning changed over time

- **`version`**: version 2 (BIP68, 2016) turns on consensus-enforced relative timelocks in `sequence`. Version 3 is consensus-identical to version 2 but opts into the TRUC relay policy (BIP431, Bitcoin Core 28.0), discussed below. Reserving such knobs for future use protects people who hold _presigned_ transactions: a new rule that only applies to a new version cannot invalidate an old presigned transaction.
- **`sequence`** has had four lives: Satoshi's high-frequency replacement scheme (disabled early for DoS reasons); the BIP125 opt-in RBF signal (any input with `sequence < 0xfffffffe`); a BIP68 relative timelock (version ≥ 2 and bit 31 clear); and the switch that enables `locktime` at all (if every input has `0xffffffff`, the lock time is ignored).
- **`locktime`**: 0 means no lock. A value $L$ below 500,000,000 is a block height, and the transaction may only appear in a block whose height is greater than $L$. Anything else is a Unix time that must be below the **median time past** (MTP) of the last 11 blocks (BIP113), which runs about an hour behind wall-clock time.

#### The coinbase transaction

The first transaction in each block creates the subsidy and collects the fees. It has exactly one input, whose outpoint is null (32 zero bytes, index `0xffffffff`). Its "scriptSig" is the _coinbase field_, 2 to 100 bytes, which since BIP34 must begin with the block height. Its outputs may claim at most subsidy plus fees, cannot be spent until 100 blocks later (the _maturity_ rule), and, if any transaction in the block has a witness, must include the SegWit witness commitment (Section 14).

### 5. The life cycle of a transaction

Here is the whole journey, from the moment a receiver asks to be paid to the moment the payment is buried under blocks:

```text
RECEIVER         SENDER'S WALLET                  NETWORK (full nodes)                MINERS
--------         ---------------                  --------------------                ------
derive a fresh   decode address -> scriptPubKey
key/script  ---> select coins, add change
(addr/invoice)   set version, sequence, locktime
                 estimate fee rate
                 sign every input  ---- tx ---->  validate: consensus + policy
                                                  store in mempool, gossip to peers
                                                  (fee bumping: RBF, CPFP, packages)
                                                        |
                                                        +------------------------> pick txs by fee rate
                                                                                   coinbase + witness commitment
                                                                                   Merkle root, 80-byte header
                                                                                   grind proof of work
                                                  validate block, update UTXO set <---- new block
                                                  drop confirmed/conflicting txs
                 confirmations accumulate; reorg risk shrinks exponentially
```

#### 5.1 Receiving

The receiver's wallet derives a fresh key (usually along a BIP32 path, see Section 30), wraps it in its preferred script template and hands out the address, often inside a BIP21 URI. The book's example invoice:

```text
bitcoin:bc1qk2g6u8p4qm2s2lh3gts5cpt2mrv5skcuu7u3e4?amount=0.01577764&label=Bob%27s%20Store&message=Purchase%20at%20Bob%27s%20Store
```

A principle the book stresses: **the receiver chooses the script, the sender just copies it.** A sender must never "upgrade" a receiver's address to another type (for example turning a P2PKH address into P2WPKH), because the receiver's wallet may be unable to spend it.

#### 5.2 Building

The sender's wallet:

1. **Selects coins.** It picks UTXOs that cover amount plus fee, trading off fee (fewer, cheaper-to-spend inputs), privacy (avoid linking unrelated coins) and UTXO hygiene (consolidate when fees are low).
2. **Creates outputs.** The payment, plus change unless an exact match was found. Ideally the change uses the same script type as the payment so observers cannot tell which is which.
3. **Estimates the fee rate.** The fee is a bid in an auction for block space. Bitcoin Core's `estimatesmartfee` buckets recently confirmed transactions by fee rate and asks how long each bucket took to confirm. Since every input type has a different size, the wallet needs the scripts before it can know the fee.
4. **Sets the knobs.** Many wallets set `locktime` to the current tip height so the transaction can only be mined in the next block or later (_anti fee sniping_: a miner trying to re-mine the previous block cannot pull this transaction's fee into it), set `sequence` to signal RBF, and use version 2.

#### 5.3 Signing

Each input is signed separately. A signature commits to a digest of the transaction (the _sighash_, Section 7), and the sighash flag decides which parts are covered. Because inputs are independent, different parties can sign different inputs of the same transaction, which is how CoinJoin, payjoin and every multisig workflow operate. The interchange format for that is the **PSBT** (Partially Signed Bitcoin Transaction, BIP174 and BIP370): a container that carries the unsigned transaction plus everything a signer needs (the UTXOs being spent, scripts, derivation paths, partial signatures) between a _creator_, _updaters_, _signers_ (often hardware devices), a _combiner_, a _finalizer_ and an _extractor_. The book recommends it to anyone building wallets that sign with more than one key, and Part VIII leans on it.

#### 5.4 Broadcast, validation and policy

The wallet hands the transaction to any node. Each node validates it before relaying it, and an invalid transaction dies at the first honest node. The book's checklist, abridged:

- syntax correct, inputs and outputs non-empty, weight low enough for a block;
- every output value and the total between 0 and 21 million BTC;
- `locktime` and BIP68 sequence locks satisfied;
- signature operation count within limits;
- every spent output exists in the UTXO set (or the mempool) and is unspent; coinbase outputs are mature;
- sum of inputs ≥ sum of outputs;
- every input's scripts validate.

Those are consensus checks. On top of them Bitcoin Core applies **policy** before it accepts a transaction into its mempool. As of the current releases (28.0 to 31.0) the important defaults are:

|Policy|Default|
|---|---|
|Max standard transaction weight|400,000 WU (a tenth of a block)|
|Standard versions|1, 2 and 3|
|Output scripts|standard templates only: P2PK, P2PKH, P2SH, bare multisig up to 3 keys, OP_RETURN, P2WPKH, P2WSH, P2TR, P2A, and witness programs of future versions|
|`scriptSig`|push-only, at most 1,650 bytes|
|Dust|outputs below about 3 sat/vB × (output size + cost to spend it), e.g. 546 sat for P2PKH, 294 for P2WPKH, 330 for P2WSH/P2TR, 240 for P2A|
|Minimum relay fee|0.1 sat/vB (lowered from 1 sat/vB in 29.1)|
|OP_RETURN|multiple outputs, up to 100,000 bytes of script in total (since 30.0; previously one output with a script of at most 83 bytes, i.e. 80 bytes of data)|
|Legacy signature operations|at most 2,500 per transaction (since 29.1, in preparation for the BIP54 "consensus cleanup" proposal)|
|Mempool|300 MB, transactions expire after 2 weeks|

If a transaction spends an output the node has never seen, it waits in a small **orphan pool** until the parent arrives. Peers announce transactions by wtxid (`inv`), and the receiver fetches the ones it lacks (`getdata`).

#### 5.5 Life in the mempool: the fee market

Each node's mempool is its own view of unconfirmed transactions, sorted by how attractive they are to mine. If fees rise after you broadcast, you can **fee bump**:

- **Replace-by-fee (RBF).** Broadcast a conflicting version that spends at least one of the same inputs and pays more. Nodes accept a replacement only if miners would prefer it: traditionally a higher fee rate and a higher absolute fee, and since Core 31.0, formally, a strictly better mempool fee-rate diagram (see below). BIP125 originally required an opt-in signal; Bitcoin Core 28.0 made _full RBF_ the default (any unconfirmed transaction can be replaced) and 29.0 removed the option entirely. Only the signers can create the replacement. The book's warning: when replacing more than once, make every version conflict with every other version, or a miner holding version 0 could confirm it alongside version 2 and pay your recipient twice.
- **Child-pays-for-parent (CPFP).** Anyone who receives an output of the stuck transaction (the payee, or the sender through their change) spends it in a high-fee child. Miners evaluate parent and child as a _package_ and mine both if the combined fee rate is attractive.
- **Package relay.** A parent below the minimum mempool fee would be rejected before its child could rescue it. Since 28.0 nodes accept and relay _one-parent-one-child_ (1p1c) packages together, and the parent may even pay zero fee (TRUC parents since 28.0, any 1p1c parent since 31.0).

The adversarial version of this is **transaction pinning**: in a multiparty protocol, a counterparty uses the anti-DoS rules to make your fee bump impossible, for example by attaching a huge low-fee child so that RBF becomes prohibitively expensive, or by exhausting descendant limits. For time-sensitive contracts like Lightning, a successful pin can mean theft. Three generations of fixes have followed:

1. **CPFP carve-out** (2019): one extra small child allowed beyond the descendant limit, plus Lightning's _anchor outputs_. The book describes this state.
2. **TRUC transactions** (v3, BIP431, Core 28.0): a v3 transaction may have at most one unconfirmed parent and at most one unconfirmed child, a child of an unconfirmed v3 parent is capped at 1,000 vB, v3 transactions are capped at 10,000 vB, and a new child can evict an existing sibling. Small, predictable topologies are much harder to pin. Paired with the keyless **pay-to-anchor** output (P2A, `OP_1 <0x4e73>`) and **ephemeral dust** (Core 29.0: a zero-fee transaction may carry one dust output if a child in the same package spends it), a presigned transaction can pay zero fee and let whoever needs it confirmed attach the fee later.
3. **Cluster mempool** (Core 31.0, April 2026): the mempool is reorganised into clusters of connected transactions, limited to 64 transactions and 101 kvB each, replacing the old 25-ancestor/25-descendant limits. A replacement is accepted only if it makes the mempool's _fee-rate diagram_ strictly better, and the CPFP carve-out was removed; TRUC with sibling eviction is now the recommended tool for contracting protocols.

#### 5.6 Mining

A miner's node builds a **block template**: the most profitable set of transactions, ordered so that parents precede children, within 4 M weight units. It then adds:

- the **coinbase transaction**, paying subsidy plus fees to the miner, with the block height first in its coinbase field (BIP34);
- the **witness commitment**, an `OP_RETURN` output in the coinbase containing `aa21a9ed` and $\text{SHA256d}(\text{witness Merkle root} \Vert \text{witness reserved value})$, where the witness tree is built from wtxids (the coinbase's own wtxid counts as zero);
- the **Merkle root** of all txids, built by pairwise SHA256d hashing (an odd last element is paired with itself, a quirk behind CVE-2012-2459).

The 80-byte header holds `version` (now a BIP9 signalling bitfield), the previous block hash, the Merkle root, a timestamp, the target in compact `nBits` form, and a 32-bit nonce. Mining means finding a header whose SHA256d, read as a number, is below the target:

$$ \text{SHA256d}(\text{header}) < \text{target} = \text{coefficient} \cdot 2^{8(\text{exponent} - 3)} $$

The book's block 277,316 has `nBits = 0x1903a30c`, so the target is $\texttt{0x03a30c} \cdot 2^{8 \cdot (0x19 - 3)}$, a 256-bit number with 62 leading zero bits. Every 2,016 blocks each node recomputes the target so blocks keep arriving about every ten minutes:

$$ \text{target}_{new} = \text{target}_{old} \cdot \frac{\text{actual time of the last 2016 blocks}}{20160 \ \text{minutes}} $$

clamped to a factor of 4 in either direction (and, thanks to an off-by-one in the original code, measured over 2,015 intervals). The 32-bit nonce is exhausted in a blink, so miners also vary an _extra nonce_ in the coinbase, some version bits, and the timestamp.

#### 5.7 Propagation and validation

The winning block spreads quickly thanks to **compact block relay** (BIP152): peers already hold most transactions in their mempools, so the block travels as a header plus short transaction ids. Each full node then validates every transaction in it, applies it to the UTXO set (remove spent outputs, add created ones), and evicts from its mempool everything that was confirmed or now conflicts. Note what the block does _not_ contain: account balances, state roots or execution traces. It is just the ordered list of transactions; each node derives the state itself.

#### 5.8 Confirmations and finality

Finality is probabilistic. Nodes follow the valid chain with the most cumulative work, so a transaction with $z$ blocks on top can be reversed only by an attacker who produces a longer chain. The whitepaper models the attacker (with a fraction $q$ of hash power, honest miners $p = 1 - q$) and gets:

$$ P(\text{attacker catches up}) = 1 - \sum_{k=0}^{z} \frac{\lambda^{k} e^{-\lambda}}{k!} \left(1 - \left(\frac{q}{p}\right)^{z-k}\right), \qquad \lambda = z\,\frac{q}{p} $$

|$z$ (confirmations)|$q = 0.10$|$q = 0.30$|
|---|---|---|
|1|0.2045873|0.6277491|
|2|0.0509779|0.4457171|
|4|0.0034552|0.2391269|
|6|0.0002428|0.1321112|
|10|0.0000012|0.0416605|

This is where the folk rule of "six confirmations" comes from: against an attacker with 10% of the hash rate, the chance of reversal after six blocks is about 0.02%. Coinbase outputs have a stricter rule (100 blocks) for a different reason: a normal transaction knocked out by a reorg can simply be mined again in the new chain, but a coinbase transaction cannot, so it and everything spending it would vanish.

With the transaction's journey mapped, we can zoom into the one step this article cares most about: _every input's scripts validate_.

## Part III: Script, the Machine Behind Every Coin

### 6. How Script executes

#### Design goals

Script is a small, Forth-like stack language. Its designers made three choices that an EVM engineer should internalise before reading a single opcode:

1. **No loops, no jumps.** The only control flow is `IF`/`ELSE`/`ENDIF`. Execution time is bounded by script length, so there is no gas: limits on size and operation counts do the job.
2. **No state.** A script sees the stack it is given, the transaction being validated, and data about the outputs being spent. Nothing persists after it runs. The same script with the same transaction gives the same answer on every node, forever.
3. **It is a predicate, not a program.** A script does not _do_ anything; it answers "may this output be spent by this transaction?" with yes or no. The work of moving value is done by the transaction structure itself.

#### Data model

- The **main stack** holds byte vectors of at most 520 bytes. There is also an **alt stack**; together they may hold at most 1,000 elements.
- **Numbers** are byte vectors in little-endian, sign-magnitude form ("CScriptNum"). Arithmetic opcodes accept inputs of at most 4 bytes. Examples: 4320 is `e010`, 800,000 is `00350c`, 128 is `8000` (an extra byte keeps the sign bit clear), and −1 is `81`.
- **Booleans**: a value is false if it is empty, all zero bytes, or "negative zero" (zeros ending in `0x80`). Everything else is true. `OP_0` pushes the empty vector; comparison opcodes push `01` or empty.

#### Encoding

A script is a byte string. Each byte is an opcode, and some opcodes consume the bytes that follow:

|Bytes|Name|Effect|
|---|---|---|
|`00`|`OP_0` / `OP_FALSE`|push empty vector|
|`01`–`4b`|(direct push)|push the next 1 to 75 bytes|
|`4c`, `4d`, `4e`|`OP_PUSHDATA1/2/4`|next 1, 2 or 4 bytes give the length, then push|
|`4f`|`OP_1NEGATE`|push −1|
|`51`–`60`|`OP_1`…`OP_16`|push the number 1 to 16|
|`61`, `63`, `64`, `67`, `68`, `69`, `6a`|`NOP`, `IF`, `NOTIF`, `ELSE`, `ENDIF`, `VERIFY`, `RETURN`|flow control|
|`6b`–`7d`|`TOALTSTACK`, `DROP`, `DUP`, `SWAP`, `ROT`, `PICK`, `ROLL`, `IFDUP`…|stack manipulation|
|`82`|`OP_SIZE`|push the length of the top element|
|`87`, `88`|`EQUAL`, `EQUALVERIFY`|byte equality|
|`8b`–`a5`|`ADD`, `SUB`, `NUMEQUAL`, `LESSTHAN`, `WITHIN`, `BOOLAND`…|32-bit arithmetic and logic|
|`a6`–`aa`|`RIPEMD160`, `SHA1`, `SHA256`, `HASH160`, `HASH256`|hashing|
|`ab`|`OP_CODESEPARATOR`|changes which part of the script signatures commit to|
|`ac`–`af`|`CHECKSIG`, `CHECKSIGVERIFY`, `CHECKMULTISIG`, `CHECKMULTISIGVERIFY`|signature checks|
|`b1`, `b2`|`CHECKLOCKTIMEVERIFY`, `CHECKSEQUENCEVERIFY`|timelocks (formerly `NOP2`, `NOP3`)|
|`ba`|`OP_CHECKSIGADD`|Tapscript only (formerly invalid)|

Fifteen opcodes, including `OP_CAT`, `OP_SUBSTR`, `OP_MUL`, `OP_DIV`, `OP_LSHIFT` and the bitwise `AND`/`OR`/`XOR`, were **disabled** by Satoshi in 2010 after bugs were found. In legacy and SegWit v0 scripts their mere presence fails the script, even inside a branch that never executes. In Tapscript all fifteen fall into the `OP_SUCCESSx` range (Section 20), which is why the proposal to bring back `OP_CAT` (BIP347) can be a soft fork rather than a hard one.

Pushes have many encodings: the number 2 can be pushed as `OP_2`, as `01 02`, as `02 02 00` (non-minimal), with `OP_PUSHDATA1`, and so on. That freedom was a source of malleability (Section 13), which is why policy (and, in some contexts, consensus) insists on the **minimal** encoding.

#### Execution model

For a legacy output, validation of one input is:

1. Run the `scriptSig` on an empty stack. (It should contain only pushes; this is consensus for P2SH spends and policy otherwise.)
2. Copy the resulting stack and run the `scriptPubKey` of the output being spent on it.
3. The input is valid if nothing failed and the top stack element is true.

Originally Bitcoin concatenated the two scripts and ran them as one. In 2010 that turned out to be exploitable (the "1 `OP_RETURN`" bug: at the time, `OP_RETURN` ended execution and used the top stack item as the result, so an unlocking script could end the combined program early and succeed without ever reaching the lock). Running the scripts separately, passing only the stack between them, closed the hole. P2SH, SegWit and Taproot each add stages to this pipeline, and we will extend the picture as we meet them.

Every input is validated against **its own** previous output, independently of the other inputs. The only thing tying them together is the transaction digest that their signatures commit to.

#### Limits

|Limit|Value|Kind|
|---|---|---|
|Script size (legacy, P2SH redeem script, P2WSH witness script)|10,000 bytes|consensus|
|Stack element size|520 bytes|consensus|
|Non-push opcodes per script|201|consensus (not in Tapscript)|
|Stack + alt stack elements|1,000|consensus|
|Keys per `CHECKMULTISIG`|20|consensus|
|Signature operations per block|80,000 "sigop cost"|consensus|
|`scriptSig` size|1,650 bytes|policy|
|P2SH redeem script sigops|15|policy|
|P2WSH witness script|3,600 bytes; at most 100 stack items of at most 80 bytes|policy|
|Tapscript stack items|at most 80 bytes|policy|

#### Flow control and guard clauses

Because Script is postfix, the condition comes _before_ the `IF`:

```text
<condition> OP_IF
    <run when true>
OP_ELSE
    <run when false>
OP_ENDIF
```

The interpreter keeps a stack of booleans, one per open `IF`; an opcode executes only when all of them are true. Unexecuted branches are still parsed (and in legacy scripts still checked for disabled opcodes). Conditions are typically supplied by the spender, which lets one script offer several spending paths: the witness acts as a map through the maze. With nested `IF`s, the values are consumed top of stack first, so to select the inner `ELSE` of an outer `IF` you push `0` then `1` (the book's "Isn't that backward?" moment).

Opcodes ending in `VERIFY` are guard clauses: `OP_EQUALVERIFY` is `OP_EQUAL OP_VERIFY`, and it aborts the whole script on failure. The book's example: "Bob may spend with a signature _and_ the preimage of a hash" is

```text
OP_HASH160 <expected hash> OP_EQUALVERIFY <Bob's pubkey> OP_CHECKSIG
```

spent with `<Bob's sig> <preimage>`. Use `VERIFY` for preconditions and `IF` only when you need alternative paths.

#### A Script interpreter in under 100 lines

Reading Script is much easier once you have run it. This interpreter covers every opcode used in this article. It takes the signature check as a callback because what a signature commits to (the _sighash_) depends on the whole transaction and the script version, which is the subject of the next section.

```python
import hashlib

def hash160(b): return hashlib.new("ripemd160", hashlib.sha256(b).digest()).digest()

def num(b: bytes) -> int:                       # CScriptNum decode (little-endian, sign-magnitude)
    if not b: return 0
    n = int.from_bytes(b, "little")
    return -(n & ~(0x80 << 8 * (len(b) - 1))) if b[-1] & 0x80 else n

def enc(n: int) -> bytes:                       # CScriptNum encode (minimal)
    if n == 0: return b""
    out, a = bytearray(), abs(n)
    while a: out.append(a & 0xff); a >>= 8
    if out[-1] & 0x80: out.append(0x80 if n < 0 else 0)
    elif n < 0: out[-1] |= 0x80
    return bytes(out)

def true(b: bytes) -> bool:                     # empty, zeros and "negative zero" are false
    return any(b[:-1]) or (len(b) > 0 and b[-1] not in (0, 0x80))

def ops(script: bytes):                         # tokenizer: yields (opcode, pushed_data_or_None)
    i = 0
    while i < len(script):
        op = script[i]; i += 1
        if op <= 0x4e:                          # OP_0, direct pushes, OP_PUSHDATA1/2/4
            n = op if op < 0x4c else int.from_bytes(script[i:i + (1, 2, 4)[op - 0x4c]], "little")
            i += 0 if op < 0x4c else (1, 2, 4)[op - 0x4c]
            yield op, script[i:i + n]; i += n
        else:
            yield op, None

def run(script: bytes, stack: list, checksig, tx=None, tapscript=False) -> list:
    """Execute one script on `stack`. checksig(sig, pubkey) -> bool is supplied by the caller,
    because what a signature commits to (the sighash) depends on the transaction."""
    tx = tx or {"locktime": 0, "sequence": 0xffffffff, "version": 2}
    exec_stack = []                              # one bool per open OP_IF
    for op, data in ops(script):
        live = all(exec_stack)
        if op in (0x63, 0x64):                   # OP_IF / OP_NOTIF
            v = False
            if live:
                c = stack.pop()
                if tapscript and c not in (b"", b"\x01"): raise ValueError("MINIMALIF")
                v = true(c) if op == 0x63 else not true(c)
            exec_stack.append(v)
        elif op == 0x67: exec_stack[-1] = not exec_stack[-1]          # OP_ELSE
        elif op == 0x68: exec_stack.pop()                             # OP_ENDIF
        elif not live: continue                                       # skip unexecuted branch
        elif data is not None: stack.append(data)                     # push
        elif 0x51 <= op <= 0x60 or op == 0x4f: stack.append(enc(op - 0x50))   # OP_1..OP_16, OP_1NEGATE
        elif op == 0x69:                                              # OP_VERIFY
            if not true(stack.pop()): raise ValueError("VERIFY failed")
        elif op == 0x6a: raise ValueError("OP_RETURN")
        elif op == 0x75: stack.pop()                                  # OP_DROP
        elif op == 0x76: stack.append(stack[-1])                      # OP_DUP
        elif op == 0x73:                                              # OP_IFDUP
            if true(stack[-1]): stack.append(stack[-1])
        elif op == 0x7c: stack[-2], stack[-1] = stack[-1], stack[-2]  # OP_SWAP
        elif op == 0x82: stack.append(enc(len(stack[-1])))            # OP_SIZE
        elif op in (0x87, 0x88):                                      # OP_EQUAL[VERIFY]
            eq = stack.pop() == stack.pop()
            if op == 0x88 and not eq: raise ValueError("EQUALVERIFY failed")
            if op == 0x87: stack.append(b"\x01" if eq else b"")
        elif op in (0x93, 0x94, 0x9c):                                # OP_ADD, OP_SUB, OP_NUMEQUAL
            b, a = num(stack.pop()), num(stack.pop())
            stack.append(enc(a + b if op == 0x93 else a - b if op == 0x94 else int(a == b)))
        elif op == 0xa9: stack.append(hash160(stack.pop()))           # OP_HASH160
        elif op in (0xac, 0xad):                                      # OP_CHECKSIG[VERIFY]
            pub, sig = stack.pop(), stack.pop()
            ok = len(sig) > 0 and checksig(sig, pub)
            if tapscript and sig and not ok: raise ValueError("bad signature")
            if op == 0xad and not ok: raise ValueError("CHECKSIGVERIFY failed")
            if op == 0xac: stack.append(b"\x01" if ok else b"")
        elif op == 0xba and tapscript:                                # OP_CHECKSIGADD
            pub, n, sig = stack.pop(), num(stack.pop()), stack.pop()
            ok = len(sig) > 0 and checksig(sig, pub)
            if sig and not ok: raise ValueError("bad signature")
            stack.append(enc(n + ok))
        elif op == 0xae and not tapscript:                            # OP_CHECKMULTISIG
            k = num(stack.pop()); keys = [stack.pop() for _ in range(k)]
            t = num(stack.pop()); sigs = [stack.pop() for _ in range(t)]
            if stack.pop() != b"": raise ValueError("NULLDUMMY")      # the extra element
            i = 0                                                     # keys and sigs in the same order
            for s in sigs:
                while i < k and not checksig(s, keys[i]): i += 1
                i += 1
            stack.append(b"\x01" if i <= k else b"")
        elif op == 0xb1:                                              # OP_CHECKLOCKTIMEVERIFY
            n, lt = num(stack[-1]), tx["locktime"]
            if n < 0 or (n < 500_000_000) != (lt < 500_000_000) or n > lt or tx["sequence"] == 0xffffffff:
                raise ValueError("CLTV failed")
        elif op == 0xb2:                                              # OP_CHECKSEQUENCEVERIFY (heights only)
            n, seq = num(stack[-1]), tx["sequence"]
            if tx["version"] < 2 or seq >> 31 or (seq & 0xffff) < (n & 0xffff): raise ValueError("CSV failed")
        else: raise ValueError(f"opcode {op:#x} not in this toy")
    if exec_stack: raise ValueError("unbalanced OP_IF")
    return stack

def verify_legacy(script_sig: bytes, script_pubkey: bytes, checksig, tx=None) -> bool:
    stack = run(script_sig, [], checksig, tx)        # 1. run the unlocking script alone
    stack = run(script_pubkey, stack, checksig, tx)  # 2. run the locking script on the result
    return len(stack) > 0 and true(stack[-1])        # 3. success = a true value on top
```

Feeding it the book's first example, the lock `3 OP_ADD 5 OP_EQUAL` (`53 93 55 87`) and the key `2` (`52`), returns `True`: the scriptSig leaves `[02]`, `OP_3` pushes `03`, `OP_ADD` leaves `05`, `OP_5` pushes `05`, and `OP_EQUAL` leaves `01`. Anyone who can add can spend that output, which is the point of the example: Script checks a math problem, and only some math problems require a secret to solve. The rest of this article reuses this interpreter with real signatures plugged in. Every result quoted later (valid, invalid, and why) came from running it.

#### Malleability and the strictness flags

A third party who can change _how_ a valid unlocking script is encoded, without invalidating it, changes the transaction's txid. Bitcoin accumulated a set of rules that remove such freedom:

|Rule|Requirement|Status|
|---|---|---|
|DERSIG (BIP66)|ECDSA signatures strictly DER-encoded|consensus (2015)|
|LOW_S|ECDSA `s` in the lower half of the range|policy|
|MINIMALDATA|pushes and numbers minimally encoded|policy|
|NULLDUMMY (BIP147)|the extra `CHECKMULTISIG` element must be empty|consensus with SegWit|
|NULLFAIL|a failing signature check must be given an empty signature|policy; consensus in Tapscript|
|MINIMALIF|`IF` argument exactly empty or `01`|policy for P2WSH; consensus in Tapscript|
|CLEANSTACK|exactly one element left at the end|policy for legacy; consensus for SegWit and Tapscript|
|WITNESS_PUBKEYTYPE|compressed keys only in SegWit v0|policy|

SegWit removed most of the _motivation_ for these rules by taking signatures out of the txid, but they still matter for fee predictability and for the hygiene of presigned transactions.

#### How Script gets upgraded

A soft fork may only **tighten** the rules: anything valid under the new rules must have been valid under the old ones, so un-upgraded nodes keep following the chain. Script was designed with hooks for exactly this:

- **`OP_NOP1`–`OP_NOP10`** do nothing, so a soft fork can redefine one to "fail unless condition X holds". `OP_CHECKLOCKTIMEVERIFY` was `OP_NOP2` (BIP65) and `OP_CHECKSEQUENCEVERIFY` was `OP_NOP3` (BIP112). Because old nodes treat them as no-ops that leave the stack untouched, the new opcodes must leave their argument on the stack too, which is why they are usually followed by `OP_DROP`.
- **Template reinterpretation**: P2SH gave the pattern `OP_HASH160 <20 bytes> OP_EQUAL` an extra meaning.
- **Witness versions**: SegWit made `OP_n <2 to 40 bytes>` "anyone can spend" for old nodes and versioned for new ones (Part V).
- **Tapscript's hooks**: `OP_SUCCESSx` opcodes, leaf versions, unknown public key types and the annex (Part VI).

### 7. Signatures: what OP_CHECKSIG actually checks

`OP_CHECKSIG` pops a public key and a signature and checks that the signature was made by that key **over a digest of the spending transaction**. That digest is what makes a signature an authorization of _this_ transaction and not a free-floating proof of key ownership. In the book's notation:

$$ \text{Sig} = F_{sig}\big(F_{hash}(m),\ x\big) $$

where $x$ is the private key and $m$ is a specific selection of transaction data. Bitcoin uses two signature schemes: ECDSA for legacy and SegWit v0 scripts, and Schnorr (BIP340) for Taproot. Schnorr gets its own section in Part VI; here is ECDSA.

#### ECDSA

With private key $x$, public key $X = xG$ and message hash $z$:

- **Sign:** pick a secret nonce $k$, compute $R = kG$, $r = R_x \bmod n$, and $s = k^{-1}(z + r x) \bmod n$. The signature is $(r, s)$.
- **Verify:** compute $u_1 = z s^{-1}$ and $u_2 = r s^{-1}$, then accept if $(u_1 G + u_2 X)_x \equiv r \pmod n$.

Verification works because $u_1 G + u_2 X = s^{-1}(z + r x) G = kG = R$. Two weaknesses matter for Bitcoin. First, if $(r, s)$ is valid then so is $(r, n - s)$, a free mutation for anyone who sees the signature, which is why policy demands the "low S" form. Second, ECDSA is not linear, so signatures do not combine; multi-party ECDSA needs heavy machinery.

Signatures are serialized in DER plus a one-byte sighash flag. The book's example, split into fields:

```text
30 45                       DER sequence, 69 bytes follow
02 21 00884d142d86652a3f47ba4746ec719bbfbd040a570b1deccbb6498c75c4ae24cb    r (33 bytes: 0x00 pad because the top bit is set)
02 20 4b9f039ff08df09cbe9f6addac960298cad530a863ea8f53982c09db8f6e3813      s (32 bytes)
01                          SIGHASH_ALL
```

So an ECDSA signature costs 71 to 73 bytes on chain. Schnorr signatures are a fixed 64 bytes (65 with an explicit sighash byte).

#### Nonces are the private key's bodyguard

The nonce must be secret and never reused. If the same $k$ signs two different digests $z_1, z_2$, both signatures share $r$ and anyone can solve two linear equations for the key:

$$ s_1 - s_2 = k^{-1}(z_1 - z_2) \ \Rightarrow\ k = \frac{z_1 - z_2}{s_1 - s_2}, \qquad x = \frac{s_1 k - z_1}{r} \pmod n $$

This has cost real users real money (badly seeded random number generators in wallets). The standard defence, from RFC6979 for ECDSA and BIP340 for Schnorr, is to derive $k$ deterministically from the private key and the message, optionally mixing in fresh randomness. Remember this section when we reach MuSig2, where deterministic nonces become _dangerous_.

#### Sighash flags: choosing what to sign

The last byte of a legacy or SegWit v0 signature (or the optional 65th byte of a Schnorr signature) selects which parts of the transaction the signature covers:

|Flag|Value|Signs|Use case from the book|
|---|---|---|---|
|`ALL`|`0x01`|all inputs, all outputs|normal payments|
|`NONE`|`0x02`|all inputs, no outputs|a "blank cheque" whose destination others may fill in|
|`SINGLE`|`0x03`|all inputs, only the output with this input's index|combinable partial transactions|
|`ALL\|ANYONECANPAY`|`0x81`|this input, all outputs|crowdfunding: anyone may add inputs|
|`NONE\|ANYONECANPAY`|`0x82`|this input only|a "dust collector": donate a tiny UTXO to whoever sweeps it|
|`SINGLE\|ANYONECANPAY`|`0x83`|this input and its paired output|building blocks for swaps and fee attachment|

Taproot adds `SIGHASH_DEFAULT` (`0x00`, implied by a 64-byte signature), which behaves like `ALL`. Because the flag itself is part of the signed digest, nobody can change it after the fact. Proposals such as `SIGHASH_ANYPREVOUT` (BIP118), which would let a signature skip committing to the outpoint and enable more flexible Lightning designs, are not active.

#### The legacy digest and its quadratic cost

For legacy inputs the digest is computed by copying the transaction, blanking every `scriptSig`, putting the _script code_ (the script being executed, after the last `OP_CODESEPARATOR`) into the input being signed, adjusting inputs and outputs according to the flag, appending the 4-byte flag, and hashing with SHA256d. Two problems follow:

1. **Quadratic hashing.** Each of $n$ inputs hashes a copy of a transaction whose size grows with $n$, so validation does $O(n^2)$ hashing. A single transaction close to 1 MB mined in 2015 took tens of seconds to validate, and worst-case constructions were far worse.
2. **The amount is not signed.** A legacy signature does not commit to the value of the output being spent, so an offline signer (a hardware wallet) cannot know the fee it is approving without being fed and verifying every previous transaction in full.

Both are fixed by the new digest algorithms of SegWit (BIP143) and Taproot (BIP341). There is also a historical oddity: with `SIGHASH_SINGLE`, if the input's index has no matching output, legacy code signs the constant `1` instead of a transaction digest, so such a signature can be reused for anything that key controls. Wallets avoid that case.

---

## Part IV: The Legacy Output Types

Bitcoin's output types are best understood as a sequence of fixes. Each one solved a pain point of the one before, and each fix is still visible on chain because old outputs never expire. In this part we walk through the pre-SegWit generation in the order it appeared. For each type: the problem it solved, the exact script, how a spend is evaluated, what it costs, and what was still wrong with it.

### 8. P2PK: pay to public key

The whitepaper's model, coins sent to a public key and spent with a signature, maps directly onto the simplest possible script.

```text
scriptPubKey:  <pubkey> OP_CHECKSIG              21 <33 bytes> ac   (35 bytes; 67 with an uncompressed key)
scriptSig:     <sig>
```

The combined evaluation is two steps: push the signature, push the key, and `OP_CHECKSIG` replaces both with true or false. In Bitcoin 0.1 you could pay someone by typing their **IP address**: your node connected to theirs and asked for a fresh public key, then built exactly this script. The feature was removed long ago (the receiver had to be online and reachable, which NATs and laptops made impractical), but P2PK lives on in the early coinbase rewards, which paid miners this way. Many of those 2009 and 2010 outputs have never moved.

What was wrong with it:

- A public key is long (65 bytes back then) and has no checksum, so it is a terrible thing to read over the phone.
- The key itself is on chain from the moment the coins are received, which is relevant to long-term quantum-computing concerns. Hashed output types reveal the key only when the coins are spent, though BIP341's authors call that protection weak at best: a key is exposed while its spending transaction waits to confirm, and a large share of all coins sit in outputs whose keys are already public anyway.

### 9. P2PKH: pay to public key hash

The fix was to put a 20-byte _commitment_ to the key in the output and reveal the key only when spending.

```text
scriptPubKey:  OP_DUP OP_HASH160 <20-byte HASH160(pubkey)> OP_EQUALVERIFY OP_CHECKSIG
               76 a9 14 <20 bytes> 88 ac                                              (25 bytes)
scriptSig:     <sig> <pubkey>                                                         (~107 bytes)
```

The evaluation, with the stack's top on the right:

|Step|Operation|Stack after|
|---|---|---|
|1|push `<sig>`|`sig`|
|2|push `<pubkey>`|`sig pubkey`|
| |_scriptSig done; the stack carries over_| |
|3|`OP_DUP`|`sig pubkey pubkey`|
|4|`OP_HASH160`|`sig pubkey h(pubkey)`|
|5|push `<pkh>`|`sig pubkey h(pubkey) pkh`|
|6|`OP_EQUALVERIFY`|`sig pubkey` (aborts if the hashes differ)|
|7|`OP_CHECKSIG`|`1` (or empty if the signature is bad)|

Running it in the interpreter with a real ECDSA signature from Bob's key returns `True`; the same script with Alice's signature and Bob's key gets through `OP_EQUALVERIFY` (the key matches the hash) but `OP_CHECKSIG` pushes false, so the spend is invalid.

Satoshi never explained why the commitment uses SHA256 _followed by_ RIPEMD160, but the result, HASH160, is 20 bytes, and with a version byte and a checksum it becomes the familiar `1…` address (Section 3). P2PKH was the workhorse of Bitcoin for its first eight years.

**Cost:** a P2PKH output is 34 bytes (8 amount + 1 length + 25 script) and spending it takes a 148-byte input (36 outpoint + 1 + 107 scriptSig + 4 sequence). A typical one-input, two-output payment is 226 bytes. Keep those numbers in mind; SegWit will cut them sharply.

### 10. P2MS: bare multisig

Multisignature is as old as Bitcoin's scripting system. A _t-of-k_ multisig (the book's term for what older texts call m-of-n) lists $k$ public keys and requires signatures from at least $t$ of them:

```text
scriptPubKey:  OP_t <pubkey_1> ... <pubkey_k> OP_k OP_CHECKMULTISIG
scriptSig:     OP_0 <sig_a> <sig_b> ...                  (t signatures, in key order)
```

For 2-of-3 with compressed keys the script is `52 21<A> 21<B> 21<C> 53 ae`, 105 bytes.

#### The famous off-by-one

`OP_CHECKMULTISIG` pops $k$, the $k$ keys, $t$, the $t$ signatures, and then **one more element** that it ignores. Without that extra element the stack underflows and the script fails, so every multisig spend starts with a dummy push, by convention `OP_0`. BIP147 (deployed with SegWit) made "the dummy must be empty" a consensus rule, so the quirk is now permanent. Whether it was a bug or a reserved slot for a future "which keys signed" bitmap, only Satoshi could say; the book diplomatically calls it an _oddity_.

My interpreter reproduces all three outcomes for a 2-of-3 between Alice, Bob and Carol:

```text
OP_0 <sig_B> <sig_C>   ->  valid
     <sig_B> <sig_C>   ->  invalid: stack underflow (no dummy)
OP_0 <sig_C> <sig_B>   ->  invalid: CHECKMULTISIG pushes false (wrong order)
```

#### How the matching works, and why order matters

`OP_CHECKMULTISIG` does not search for a key for each signature. It walks the keys and the signatures with two cursors, in the same relative order. Each signature is tried against the current key; on success both cursors advance, on failure only the key cursor advances. If the remaining signatures outnumber the remaining keys, it fails. Consequences:

- Signatures must appear **in the same order as their public keys** in the script.
- A $t$-of-$k$ check can cost up to $k$ signature verifications: the book's 1-of-5 example checks the single signature against key 0, 1, 2, 3 and finally 4.
- For that reason legacy sigop counting charges a bare `CHECKMULTISIG` as **20** signature operations regardless of $k$.

#### Limits and why bare multisig faded

Consensus allows up to 20 keys per `CHECKMULTISIG`, but Bitcoin Core only relays bare multisig with at most **3** keys. Bare multisig has the same drawbacks as P2PK, multiplied: the sender must obtain the whole script and pay for its bytes, there is no address format, every byte sits in the UTXO set until spent, and the policy is visible to everyone. For 2-of-3 the output is 114 bytes and the input 188 vB.

Bare multisig survives today mostly as a data-embedding trick: protocols like Bitcoin Stamps encode arbitrary bytes as fake "public keys" in bare multisig outputs, which are expensive to the UTXO set precisely because they can never be spent. Bitcoin Core exposes `-permitbaremultisig` (default on) for node operators who want to stop relaying them.

### 11. OP_RETURN: provably unspendable data

People have always wanted to anchor data in the blockchain, from timestamping a document hash to recording the state of another protocol. Early attempts encoded data as fake addresses, creating unspendable UTXOs that every full node had to keep forever. The compromise was a dedicated template:

```text
scriptPubKey:  OP_RETURN <data>
```

Executing `OP_RETURN` fails the script immediately, so the output can never be spent. Nodes know that up front and **do not store these outputs in the UTXO set**. The data still costs block space and sits in the chain, but not in the expensive database. The amount is normally zero (OP_RETURN outputs are exempt from the dust rule) because anything assigned to it is burned.

Uses include document notarisation (the book cites the `DOCPROOF` prefix of the Proof of Existence service), aggregated timestamping schemes like OpenTimestamps, and token protocols such as Runes, whose messages are `OP_RETURN OP_13 <payload>` outputs.

The allowed size is a matter of policy, and a contested one. For most of the last decade Bitcoin Core relayed one OP_RETURN output per transaction with at most 80 bytes of data. Bitcoin Core 30.0 (October 2025) raised the default limit to 100,000 bytes and allowed several such outputs per transaction; its proponents argued that the old limit no longer stopped data from being embedded and only pushed it into more harmful places, such as fake keys that bloat the UTXO set. The consensus rules never had a limit beyond the transaction size.

### 12. P2SH: pay to script hash

By 2012 the pain of complex scripts was obvious. The book's illustration is Mohammed, an importer in Dubai whose company wants every customer payment locked in a 2-of-5 multisig (Mohammed, three partners, and their lawyer). With bare multisig, every customer would need special wallet software, would have to be sent the whole script, and would pay to put five public keys in their transaction; and the script would sit in every node's UTXO set until spent.

**BIP16** turned the problem around: the output commits to the _hash_ of the script, and the spender reveals the script (now called the **redeem script**) at spend time.

```text
redeemScript:  2 <PK1> <PK2> <PK3> <PK4> <PK5> 5 OP_CHECKMULTISIG
scriptPubKey:  OP_HASH160 <20-byte HASH160(redeemScript)> OP_EQUAL      a9 14 <20 bytes> 87   (23 bytes)
scriptSig:     OP_0 <sig1> <sig2> <serialized redeemScript>
```

For Mohammed's script the book gives the hash `54c557e07dde5bb6cb791c7a540e0a4796f5e97e`; with base58check version byte `0x05` it becomes `39RF6JqABiHdYHkfChV6USGMe6Nsr66Gzw`, which is exactly what my code produces. Customers just pay a `3…` address like any other.

#### How a P2SH spend is evaluated

1. Run the `scriptSig` (it **must** be push-only) and copy the resulting stack.
2. Run the `scriptPubKey` on it: the top element (the serialized redeem script) is hashed and compared with the commitment. This must succeed.
3. Because the `scriptPubKey` matches the exact P2SH template, take the copied stack from step 1, pop the redeem script, **deserialize it and execute it** on the remaining items. It must also succeed.

Step 3 is the soft-fork trick. A node that predates BIP16 only performs steps 1 and 2: to it, a P2SH output is spendable by anyone who knows the redeem script. Upgraded nodes add the constraint of step 3. Old nodes accept every block new nodes accept, so the chain does not split. The same pattern, "looks anyone-can-spend to old nodes, carries new rules for new nodes", is how SegWit and Taproot were deployed.

#### Why P2SH multisig tops out at 15 keys

The redeem script travels as a single stack element, and stack elements are limited to 520 bytes. A $t$-of-$k$ `CHECKMULTISIG` script with compressed keys is

$$ \text{size} = 1 + 34k + 1 + 1 = 34k + 3 \ \text{bytes} $$

so $k = 15$ gives 513 bytes and $k = 16$ gives 547, over the limit. (Policy independently caps P2SH redeem scripts at 15 signature operations.) That is the origin of the "15-of-15" ceiling the book mentions.

#### Benefits and pitfalls

The book lists the benefits: senders need no special software; the long script moves from the output (and the UTXO set) to the input (only the blockchain); its cost moves from the time of payment to the time of spending; and the fee for it moves from the sender to the receiver, who chose it. The pitfalls:

- **No recursion.** A redeem script cannot itself be P2SH.
- **Commit to a broken script and the coins are gone.** Nodes cannot validate a redeem script they have never seen, so an output committing to an invalid script is accepted and can never be spent.
- **Only 80-bit collision security.** If an attacker participates in building a multisig script (say, as one of the cosigners who submits a key last), they can grind their own key to find two scripts with the same HASH160, one of which they control alone. That is a collision search, so it costs about $2^{80}$ work rather than $2^{160}$. The book notes that Bitcoin miners collectively perform roughly $2^{80}$ hashes every hour (of a different function, so they cannot do this today), which shows such attacks are not science fiction for large multiparty setups. SegWit's P2WSH uses a 32-byte SHA256 commitment (128-bit collision security) for this reason.

**Cost:** a 2-of-3 P2SH spend needs `OP_0`, two ~72-byte signatures and the 105-byte redeem script in the `scriptSig`: 254 bytes of script, a **297-byte input**, and a typical one-input, two-output transaction of 371 bytes. Every one of those bytes counted at full weight. That is the problem SegWit's discount set out to fix.

---

## Part V: Segregated Witness

### 13. The problems SegWit solved

By 2015 Bitcoin had a list of problems that all traced back to one design decision: **signatures were part of the data hashed into the txid.**

#### Third-party malleability

The book's example: the script `2 OP_ADD 4 OP_EQUAL` can be satisfied by pushing the number 2, and 2 can be pushed as `OP_2`, `01 02`, `02 02 00`, `OP_PUSHDATA1 01 02`, and many other encodings. Each encoding yields a different, equally valid transaction with a **different txid**. ECDSA adds another free mutation: if $(r, s)$ is a valid signature, so is $(r, n - s)$. So anyone relaying Alice's payment could mutate it, and if the mutant confirmed, any transaction that spent Alice's output by the _original_ txid (say Bob's onward payment to Carol) became permanently invalid, even though nobody did anything wrong.

#### Second-party malleability

Even with every encoding rule tightened (the abandoned BIP62 tried), a _co-signer_ can always produce a fresh signature with a different nonce, and therefore a different txid. In a two-party contract that is fatal: Bob can change the txid of a transaction Alice depends on.

#### Circular dependencies

Contract protocols need to sign transactions **before** their parents are signed. The book's example: Alice and Bob want to fund a 2-of-2 output (Tx0) but first want a signed refund (Tx1) that returns their money if the other disappears. Tx1 spends Tx0, so it must reference Tx0's txid. But Tx0's txid depends on Tx0's signatures, and once those exist either party could broadcast Tx0 before signing the refund. Payment channels, and therefore Lightning, were impractical without a fix.

#### And three more

- **Quadratic signature hashing** and the unsigned input amount (Section 7).
- **Capacity**: the 1 MB block size limit was a political flashpoint.
- **Upgradability**: every new script feature needed its own clever soft-fork trick.

The fix for the first three was understood as early as 2011: compute the txid **without** the unlocking data. Doing it as a hard fork was off the table. The insight of late 2015 was how to do it as a soft fork.

### 14. How SegWit was deployed as a soft fork

SegWit (BIP141, with BIP143 for signatures and BIP144 for serialization) defines a new output template, the **witness program**:

```text
scriptPubKey:  <version: OP_0 .. OP_16> <witness program: 2 to 40 bytes>
```

To a pre-SegWit node this is just two pushes; it leaves a non-empty element on top, so it is spendable by anyone with an empty `scriptSig`. A SegWit node instead requires:

- the `scriptSig` must be **empty** (or, for nested SegWit, exactly one push of the witness program);
- the spend is authenticated by a new per-input **witness** field, which old nodes never see;
- the version byte selects the rules: v0 is defined by BIP141, v1 by BIP341 (Taproot), and v2 to v16 remain **anyone-can-spend** to everyone, reserved for future soft forks. For v0 the program must be exactly 20 or 32 bytes; any other length is invalid.

Old nodes allow an empty `scriptSig`; new nodes _require_ it. Every block valid under the new rules is valid under the old, so it is a soft fork. The witnesses are still committed to, just not in the txid: the coinbase transaction carries a Merkle root of all **wtxids** (Section 5.6), so a block's witnesses cannot be swapped without changing the coinbase, and therefore the block's Merkle root and hash.

|Problem|How SegWit fixes it|
|---|---|
|Third-party malleability|witnesses are outside the txid|
|Second-party malleability|same: re-signing changes the wtxid, not the txid|
|Circular dependencies|presign a child against a parent's txid before the parent is signed|
|Quadratic hashing|new digest algorithm with cached sub-hashes (BIP143)|
|Unsigned amounts|the digest commits to the spent amount|
|Capacity|block weight: witness bytes weigh a quarter|
|Upgrades|16 more witness versions, each a clean slate|

Note what does _not_ change: legacy inputs in a SegWit transaction are as malleable as ever. Only inputs spending witness programs get the guarantees.

SegWit activated at block 481,824 in August 2017, after one of the most contentious episodes in Bitcoin's history: BIP9 miner signalling stalled for months, a user-activated soft fork (BIP148) threatened to reject non-signalling blocks, and miners finally signalled. The book's Chapter 12 tells the story, including the discovery that some miners stood to lose a hidden efficiency advantage (covert ASICBoost) if SegWit activated.

### 15. P2WPKH, P2WSH and their nested forms

Version 0 defines two programs, distinguished purely by length.

#### P2WPKH: 20-byte program

```text
scriptPubKey:  OP_0 <20-byte HASH160(pubkey)>            00 14 <20 bytes>      (22 bytes)
scriptSig:     (empty)
witness:       <sig> <pubkey>
```

Validation: the witness must contain exactly two items, the HASH160 of the second must equal the program, and then the pair is checked exactly as if it were spending `OP_DUP OP_HASH160 <program> OP_EQUALVERIFY OP_CHECKSIG`. That reconstructed P2PKH script is also what the signature digest calls the _script code_. The book converts the P2PKH output `OP_DUP OP_HASH160 ab68025513c3dbd2f7b92a94e0581f5d50f654e7 OP_EQUALVERIFY OP_CHECKSIG` into the P2WPKH output `0 ab68025513c3dbd2f7b92a94e0581f5d50f654e7` (address `bc1q4d5qy4gnc0da9aae922wqkqlt4g0v4889q04gu`). The public key must be compressed (policy), and only the receiver should ever create such an output from their own key; the book is emphatic that a sender must not convert someone's P2PKH address into P2WPKH on their behalf.

Cost: the input is 41 non-witness bytes (164 WU) plus a 108-byte witness, **68 vB instead of 148 vB**.

#### P2WSH: 32-byte program

```text
scriptPubKey:  OP_0 <32-byte SHA256(witnessScript)>      00 20 <32 bytes>      (34 bytes)
scriptSig:     (empty)
witness:       <arg_1> ... <arg_m> <witnessScript>
```

Validation: the last witness item is the **witness script**; its single SHA256 must equal the program; it is executed with the remaining items as the initial stack; and execution must end with exactly one true element. Compared with P2SH:

- **SHA256, not HASH160**: a 32-byte commitment gives 128-bit collision resistance, closing the multiparty collision attack described in Section 12.
- **No 520-byte ceiling on the script**: the witness script is not a stack push, so consensus allows up to 10,000 bytes (policy: 3,600 bytes, at most 100 other items of at most 80 bytes). A single `CHECKMULTISIG` can now use its full 20 keys.
- MINIMALIF is policy, which helps make branch selection non-malleable.

The book's example rewrites Mohammed's P2SH output as `0 a9b7b38d972cabc7961dbfbcb841ad4508d133c47ba87457b4a0e8aae86dbb89`, spent with the witness `<SigA> <SigB> <2 PubA PubB PubC PubD PubE 5 OP_CHECKMULTISIG>` (plus the dummy) and an empty `scriptSig`.

#### Nested SegWit: P2SH-P2WPKH and P2SH-P2WSH

In 2017 most wallets could not send to a bech32 address. To get SegWit's benefits anyway, a receiver could wrap the witness program inside P2SH: the redeem script _is_ the witness program.

```text
P2SH-P2WPKH
  redeemScript:  0014<20-byte pubkey hash>                 (22 bytes)
  scriptPubKey:  OP_HASH160 <HASH160(redeemScript)> OP_EQUAL
  scriptSig:     <0014...>                                 (a single 23-byte push)
  witness:       <sig> <pubkey>

P2SH-P2WSH
  redeemScript:  0020<32-byte SHA256(witnessScript)>       (34 bytes)
  scriptSig:     <0020...>                                 (a single 35-byte push)
  witness:       <args...> <witnessScript>
```

The book's examples check out: wrapping `0 ab68…54e7` gives the script hash `3e0547268b3b19288b3adef9719ec8659f4b2b0b` and the address `37Lx99uaGn5avKBxiW26HjedQE3LrDCZru`; wrapping Mohammed's P2WSH program gives `86762607e8fe87c0c37740cddee880988b9455b2` and `3Dwz1MXhM6EfFoJChHCxh1jWHb8GQqRenG`. Nested outputs cost more than native ones (a P2SH-P2WPKH input is 91 vB versus 68), and the outer P2SH layer brings back 80-bit collision security, so they are a transition technology. You will still see them in old wallets and exchanges.

### 16. Weight, the witness discount, and BIP143

#### Why witness bytes are cheaper

The weight formula from Section 4 counts witness bytes at a quarter of the cost of everything else. Two reasons are usually given. First, witness data never enters the UTXO set: once validated it is only needed by nodes serving historical blocks, and pruned nodes can discard it. Second, it rebalances the cost of creating outputs (which burdens every node until spent) against spending them (which shrinks the UTXO set). BIP141 also explains why it is a single composite limit rather than "1 MB base plus 3 MB witness": two separate limits would turn block building and fee estimation into a two-dimensional knapsack problem.

The effect on everyday transactions (one input, two outputs, signatures of 72 bytes for ECDSA and 64 for Schnorr):

|Transaction|Size|Change vs P2PKH|
|---|---|---|
|P2PKH|226 vB|(baseline)|
|P2SH-P2WPKH|166 vB|−27%|
|P2WPKH|141 vB|−38%|
|P2TR key path|154 vB|−32%|
|P2WSH 2-of-3|201 vB| |
|P2SH 2-of-3|371 vB| |

(P2TR outputs are 12 bytes bigger than P2WPKH outputs, which is why a single-signature Taproot payment is slightly larger than a P2WPKH one even though its input is smaller. The multisig rows foreshadow Part VIII.)

#### BIP143: a signature digest that scales

For v0 witness programs the signed message is SHA256d of a fixed-layout preimage:

|#|Field|Notes|
|---|---|---|
|1|`nVersion` (4)| |
|2|`hashPrevouts` (32)|SHA256d of all outpoints; zero with `ANYONECANPAY`|
|3|`hashSequence` (32)|SHA256d of all sequences; zero with `ANYONECANPAY`, `SINGLE` or `NONE`|
|4|outpoint (36)|of the input being signed|
|5|`scriptCode`|the witness script, or for P2WPKH the reconstructed `76a914{20}88ac`|
|6|**amount** (8)|value of the output being spent (new)|
|7|`nSequence` (4)|of this input|
|8|`hashOutputs` (32)|SHA256d of all outputs; only the matching output with `SINGLE`; zero with `NONE`|
|9|`nLockTime` (4)| |
|10|sighash type (4)| |

Items 2, 3 and 8 are computed once per transaction and reused for every input, so total hashing grows **linearly** with the number of inputs. And because item 6 commits to the amount, a signer that is told the wrong amount produces a signature that is simply invalid. That made life easier for hardware wallets, though not entirely safe: a signature commits only to the amount of _its own_ input, and a malicious host can still lie about the others across two signing sessions. Taproot's digest closes that gap (Section 19).

---

## Part VI: Taproot

Taproot (BIPs 340, 341 and 342, activated in November 2021 at block 709,632) is three ideas assembled into one output type: a better signature scheme, a way to hide unused spending conditions, and a trick that lets the cooperative case look like an ordinary single-key payment. The book builds it from the ground up, and so will we.

### 17. Schnorr signatures (BIP340)

#### From an identity protocol to a signature

The book starts with Schnorr's 1989 _identification_ protocol. Alice has private key $x$ and public key $xG$, and wants to prove she knows $x$ without revealing it:

1. Alice picks a secret random **nonce** $k$ and sends $kG$.
2. Bob replies with a random **challenge** $e$.
3. Alice sends $s = k + e x$.
4. Bob accepts if $sG = kG + e\,(xG)$.

The book's toy version with plain integers makes the algebra concrete (and insecure, since integers can be divided): with $G = 5$, $x = 3$, $k = 7$, $e = 11$ we get $xG = 15$, $kG = 35$, $s = 7 + 11 \cdot 3 = 40$, and Bob checks $40 \cdot 5 = 200 = 35 + 11 \cdot 15$.

Two details carry the security. The nonce hides $x$: with $k$ unknown, $s = k + ex$ is one equation in two unknowns. And the _order_ matters: if an impostor learned $e$ before committing to $kG$, they could pick any $s$ and set $kG = sG - e\,xG$, passing the check without knowing $x$.

Bitcoin cannot have Bob in the loop, since thousands of nodes (including ones that do not exist yet) must verify the proof. The **Fiat-Shamir transform** replaces Bob's challenge with a hash: $e = H(kG \Vert m)$. Alice cannot predict the hash before choosing $kG$, so the order is enforced by mathematics, and including $m$ binds the proof to a message. BIP340 additionally hashes in the public key, $e = H(R \Vert P \Vert m)$, which prevents a signature for one key being turned into a signature for a related key (exactly the danger with BIP32's publicly tweakable keys).

#### BIP340 precisely

BIP340 uses 32-byte **x-only** public keys and nonces: every point is implicitly the one with even $y$. To sign message $m$ with secret key $d_0$:

1. $P = d_0 G$; if $P$ has odd $y$, use $d = n - d_0$ (so that $dG$ has even $y$), else $d = d_0$.
2. Derive the nonce deterministically from the key, the message and optional randomness: $k_0 = H_{\text{BIP0340/nonce}}\big((d \oplus H_{\text{BIP0340/aux}}(a)) \Vert P_x \Vert m\big)$; $R = k_0 G$; flip $k$ to $n - k_0$ if $R$ has odd $y$.
3. $e = H_{\text{BIP0340/challenge}}(R_x \Vert P_x \Vert m) \bmod n$.
4. $s = k + e\,d \bmod n$. The signature is $R_x \Vert s$: exactly **64 bytes**.

Verification recomputes $e$ and checks that $R' = sG - eP$ has even $y$ and $x$-coordinate $R_x$. In code (reusing `point_add`, `point_mul`, `G`, `N`, `P` from Section 3):

```python
def tagged_hash(tag, msg):
    t = hashlib.sha256(tag.encode()).digest()
    return hashlib.sha256(t + t + msg).digest()

def lift_x(x):                                    # the even-y point with this x, if any
    y_sq = (pow(x, 3, P) + 7) % P
    y = pow(y_sq, (P + 1) // 4, P)
    if pow(y, 2, P) != y_sq: return None
    return (x, y if y % 2 == 0 else P - y)

def xonly(pt): return pt[0].to_bytes(32, "big")
def i(b): return int.from_bytes(b, "big")

def schnorr_sign(msg, d0, aux=b"\0" * 32):
    Pk = point_mul(G, d0); d = d0 if Pk[1] % 2 == 0 else N - d0
    t = (d ^ i(tagged_hash("BIP0340/aux", aux))).to_bytes(32, "big")
    k0 = i(tagged_hash("BIP0340/nonce", t + xonly(Pk) + msg)) % N
    R = point_mul(G, k0); k = k0 if R[1] % 2 == 0 else N - k0
    e = i(tagged_hash("BIP0340/challenge", xonly(R) + xonly(Pk) + msg)) % N
    return xonly(R) + ((k + e * d) % N).to_bytes(32, "big")

def schnorr_verify(msg, pubkey32, sig):
    Pk, r, s = lift_x(i(pubkey32)), i(sig[:32]), i(sig[32:])
    if Pk is None or r >= P or s >= N: return False
    e = i(tagged_hash("BIP0340/challenge", sig[:32] + pubkey32 + msg)) % N
    R = point_add(point_mul(G, s), point_mul((Pk[0], P - Pk[1]), e))   # sG - eP
    return R is not None and R[1] % 2 == 0 and R[0] == r
```

This code reproduces all 19 official BIP340 test vectors (signing and verification).

#### Why Bitcoin wanted Schnorr

- **Provable security** from the discrete log assumption in the random oracle model, which ECDSA has never had.
- **Fixed 64-byte encoding**, versus 71 to 73 bytes of DER.
- **Linearity.** Signatures and keys add: if $s_1 = k_1 + e x_1$ and $s_2 = k_2 + e x_2$ share the same $e$ (computed from the summed nonce and key), then $s_1 + s_2$ is a valid signature for the key $X_1 + X_2$ with nonce $R_1 + R_2$. This is the foundation of MuSig2, FROST and adaptor signatures (Part VIII).
- **Batch verification.** With random weights $a_i$, the $u$ checks $s_i G = R_i + e_i P_i$ collapse into one multi-scalar multiplication, $\left(\sum a_i s_i\right) G = \sum a_i R_i + \sum (a_i e_i) P_i$, which the book estimates at about half the cost of individual verification for a block's worth of signatures. Taproot's rules were shaped so that nodes _can_ do this; that constraint is why Tapscript dropped `OP_CHECKMULTISIG` (Section 20).

### 18. MAST and pay-to-contract, the two ingredients

#### MAST: only reveal the branch you use

Section 6's `IF`/`ELSE` trees work, but the book lists three costs: every branch adds bytes that every spender pays for, scripts have size limits that cap the number of branches, and **every branch is revealed** on every spend. If Mohammed's company spends with the 2-of-3 partners path, the whole world (including their lawyer) sees the lawyer's recovery clauses and can track their funds.

A Merkle tree fixes all three. Hash each alternative script into a leaf, hash leaves pairwise up to a root, commit to the root, and at spend time reveal only the script being used plus the sibling hashes on its path. A path costs one 32-byte hash per level, so the cost grows with $\log_2$ of the number of alternatives: a path of 15 hashes (480 bytes) selects one script out of 32,768. Placement matters too: putting the most likely script near the root (a Huffman tree, weighted by probability) minimises the expected cost. Unused branches stay private, and so does their _number_: a tree could hold one condition or a trillion.

The name has a history the book enjoys: the original idea was _Merklized Abstract Syntax Trees_, which Merklize every sub-expression; what Bitcoin adopted is a set of complete alternative scripts, so Anthony Towns coined the backronym _Merklized Alternative Script Trees_.

#### Pay-to-contract: commit inside a public key

Recall key tweaking from Section 3. Bob wants proof of what he paid Alice for. They hash a description of the deal into a scalar $t = H(\text{contract})$, Bob pays to $A' = A + tG$, and Alice spends with $a' = a + t$. Later Bob can reveal $A$ and the contract to prove the payment; Alice's spend proves she knew the contract. To everyone else, $A'$ is just another key.

#### Putting them together

In 2018 developers realised these combine. Most contracts end with everyone happy, and a contract that ends happily needs no enforcement, only a signature from all parties. So: make the "everyone agrees" case a **public key** (possibly an aggregate of many parties' keys), and use pay-to-contract to tweak that key with the **Merkle root** of the fallback scripts. If everyone cooperates, spend with one signature for the tweaked key; the scripts are never revealed, and the spend looks exactly like any single-key payment. If not, reveal one script and prove it was committed to.

### 19. P2TR: the Taproot construction (BIP341)

#### Building an output

Given an **internal key** $P$ (x-only) and a tree of scripts:

$$ h_{leaf} = H_{\text{TapLeaf}}\big(v \ \Vert\ \text{compact\_size}(|s|) \ \Vert\ s\big), \qquad v = \texttt{0xc0} \ \text{for Tapscript} $$

$$ h_{branch} = H_{\text{TapBranch}}\big(\min(a, b) \ \Vert\ \max(a, b)\big) $$

$$ t = H_{\text{TapTweak}}\big(P_x \ \Vert\ \text{root}\big), \qquad Q = P + tG $$

The output is `OP_1 <Q_x>`: 34 bytes, `51 20 <32 bytes>`, displayed as a `bc1p…` bech32m address. Children of a branch are sorted before hashing, so Merkle proofs do not need left/right flags. With no script tree at all, BIP341 still recommends tweaking with $t = H_{\text{TapTweak}}(P_x)$, which provably commits to "no scripts" and stops a malicious co-signer from hiding a script path in an aggregate key.

#### Two ways to spend

**Key path.** The witness is a single item: a 64-byte signature (65 with an explicit sighash byte) that verifies against $Q$. Whoever controls $P$'s secret $d$ signs with $d + t$ (adjusting signs for even $y$). That is what Alice's transaction in Section 4 did.

**Script path.** The witness is `<inputs to the script ...> <script> <control block>`. The control block is

$$ \underbrace{(v \,|\, \text{parity}(Q))}_{1 \text{ byte}} \ \Vert\ \underbrace{P_x}_{32} \ \Vert\ \underbrace{e_1 \Vert e_2 \Vert \dots \Vert e_m}_{32m \text{ bytes, } m \le 128} $$

and a node verifies it like this:

1. If there are at least two witness items and the last starts with `0x50`, remove it: it is the **annex**, reserved for future soft forks and covered by signatures. Do not use it.
2. If one item remains, it is a key-path signature: verify it against $Q$. Otherwise take the last item as the control block $c$ and the one before it as the script $s$.
3. Compute $k_0 = h_{leaf}(v, s)$ and fold in the path: $k_{j+1} = H_{\text{TapBranch}}(\text{sorted}(k_j, e_{j+1}))$.
4. Compute $t = H_{\text{TapTweak}}(P_x \Vert k_m)$ and check that $P + tG$ has $x$-coordinate $Q_x$ and the parity bit from $c$.
5. Execute $s$ under the rules of leaf version $v$ (Tapscript for `0xc0`; unknown leaf versions succeed, reserved for future soft forks) with the remaining items as the initial stack.

#### When there should be no key path

Sometimes no single key (or aggregate) should be able to spend. BIP341 suggests a "nothing up my sleeve" (NUMS) internal key whose discrete log nobody knows:

$$ H = \text{lift\_x}\big(\text{SHA256}(\text{uncompressed encoding of } G)\big) = \texttt{50929b74c1a04954b78b4b6035e97a5e078a5a0f28ec96d547bfee9ace803ac0} $$

Using $H$ directly marks your output as "script path only" to anyone who checks; using $H + rG$ for a random $r$ hides that, and revealing $r$ later proves it.

#### A worked example

Here is a complete 2-of-3 output for Alice, Bob and Carol that we will analyse further in Part VIII. The internal key is a MuSig2 aggregate of Alice and Bob (the pair expected to sign day to day, Section 26), and the tree holds two fallback leaves for Alice with Carol and Bob with Carol:

```python
def ser_compact_size(n):           # enough for scripts under 253 bytes
    return bytes([n])

def tapleaf_hash(script, v=0xC0):
    return tagged_hash("TapLeaf", bytes([v]) + ser_compact_size(len(script)) + script)

def tapbranch_hash(a, b):
    return tagged_hash("TapBranch", min(a, b) + max(a, b))

def taproot_output_key(internal_x: bytes, merkle_root: bytes):
    t = i(tagged_hash("TapTweak", internal_x + merkle_root))
    Q = point_add(lift_x(i(internal_x)), point_mul(G, t))
    return Q                       # scriptPubKey = OP_1 <xonly(Q)>; parity bit = Q[1] & 1

# 32-byte x-only keys of the three signers (derived from toy secrets "alice", "bob", "carol")
A = bytes.fromhex("9997a497d964fc1a62885b05a51166a65a90df00492c8d7cf61d6accf54803be")
B = bytes.fromhex("4edfcf9dfe6c0b5c83d1ab3f78d1b39a46ebac6798e08e19761f5ed89ec83c10")
C = bytes.fromhex("9094567ba7245794198952f68e5723ac5866ad2f67dd97223db40e14c15b092e")

leaf_AC = b"\x20" + A + b"\xad" + b"\x20" + C + b"\xac"     # <A> CHECKSIGVERIFY <C> CHECKSIG
leaf_BC = b"\x20" + B + b"\xad" + b"\x20" + C + b"\xac"     # <B> CHECKSIGVERIFY <C> CHECKSIG
root = tapbranch_hash(tapleaf_hash(leaf_AC), tapleaf_hash(leaf_BC))
internal = bytes.fromhex("b2137077e857a79ca67f28ed8195ebeeb85668af309d228fb9cc65eae718fb02")  # MuSig2(A, B)
Q = taproot_output_key(internal, root)
```

The intermediate values:

```text
TapLeaf(A&C)  293d8517a70f99003525bff3a26c665ab5b68a493d645b184e22400fe9b53fb7
TapLeaf(B&C)  73ffe226e095a49b5d4b6ba7ab7826c9eb6c155947e57b7dd5e175e847087a1a
Merkle root   f2a73554974065bd1c4b9c8aab45cbc31f672468757ab3ab497315f69c224a83
tweak t       479b0cde09d7b166b2c2fa1205330318e6951c4087c498dc231eb3e49da10c09
output key Q  32a0bd1162ca433c64fa1e1a2f5bb7452e159d26e6c18dd192fc7e04a49fcaa3  (odd y)
address       bc1px2st6ytzefpnce86rcdz7kahg5hpt8fxumqcm5vjl3lqffyle23srmmuas
```

To spend through the Alice-and-Carol leaf, the control block is `c1` (leaf version `c0` plus parity bit 1) ‖ the internal key ‖ the sibling hash `TapLeaf(B&C)`: 65 bytes. The same code reproduces the official BIP341 wallet test vectors, and an independent descriptor library (`embit`) derives the same address from `tr(b213…fb02,{and_v(v:pk(A),pk(C)),and_v(v:pk(B),pk(C))})`.

#### The Taproot signature digest

BIP341 replaces BIP143's digest for v1 outputs. The message is $H_{\text{TapSighash}}(\texttt{0x00} \Vert \text{SigMsg})$, a single SHA256 of a tagged hash (no double hashing), where `SigMsg` contains, in order: the hash type, version, lock time, and (unless `ANYONECANPAY`) SHA256s of all prevouts, **all spent amounts**, **all spent scriptPubKeys** and all sequences; then (unless `NONE` or `SINGLE`) a hash of all outputs; then a `spend_type` byte (key path or script path, annex or not), this input's position or details, the annex hash if present, the matching output for `SINGLE`; and for script-path spends the **TapLeaf hash** being executed, a key version, and the position of the last executed `OP_CODESEPARATOR`.

Three changes stand out:

- **Every input's amount and scriptPubKey are signed.** If the host lies about any input's value, or about which inputs belong to the wallet, every signature it obtains is invalid. A hardware wallet can therefore trust the amounts it is shown when it computes the fee, closing the cross-session lie described at the end of Part V.
- **Script-path signatures commit to the leaf.** A signature made for one leaf cannot be replayed in another leaf that contains the same key.
- **`SIGHASH_DEFAULT` (0x00)**: a 64-byte signature means "everything", saving the sighash byte.

#### What Taproot buys, and what it costs

When the key path is used, an input is 57.5 vB regardless of how many people stand behind the key or how many fallback scripts exist, and it is indistinguishable from any other single-signature Taproot spend. Script-path spends reveal only the branch used. The costs, which the book is honest about: an output that never wants a key path still pays 33 bytes for the internal key in every script-path spend; Taproot outputs commit to a public key directly (the tweaked $Q$) rather than to a hash; and the output is 43 bytes, a little more than P2WPKH's 31.

### 20. Tapscript (BIP342)

Leaf version `0xc0` runs **Tapscript**, a revision of Script with the following differences:

|Aspect|Legacy and SegWit v0|Tapscript|
|---|---|---|
|Signature scheme|ECDSA, DER, 71 to 73 bytes|BIP340 Schnorr, 64 or 65 bytes|
|Public keys|33-byte compressed (65 legacy)|32-byte x-only; empty key fails; any other length is an "unknown key type" that always validates (reserved for soft forks)|
|Multisig opcodes|`CHECKMULTISIG(VERIFY)`|**disabled**; use `OP_CHECKSIGADD`|
|Failed signature checks|push false (NULLFAIL is policy)|the signature must be empty; a non-empty invalid signature fails the whole script|
|`IF` arguments|MINIMALIF is policy (P2WSH)|exactly empty or `01`, by consensus|
|Script size|10,000 bytes|no limit beyond block weight|
|Non-push opcodes|at most 201|no limit|
|Signature operations|counted against the block's sigop limit|per-input budget: 50 + the input's witness size in bytes; each executed check with a non-empty signature costs 50|
|Stack|1,000 elements, 520 bytes each|same, now also checked on the initial stack|
|Upgrade hooks|`OP_NOPx`|`OP_SUCCESSx`, leaf versions, unknown key types, annex|

#### OP_CHECKSIGADD

`OP_CHECKSIGADD` (`0xba`) pops a public key, a number $n$ and a signature, and pushes $n + 1$ if the signature is valid or $n$ if it is empty. It is equivalent to `OP_ROT OP_SWAP OP_CHECKSIG OP_ADD` in one byte. A $t$-of-$k$ threshold becomes a running count:

```text
<pk_1> OP_CHECKSIG <pk_2> OP_CHECKSIGADD ... <pk_k> OP_CHECKSIGADD <t> OP_NUMEQUAL
```

Why replace `CHECKMULTISIG`? Because it tries each signature against keys until one matches, so some checks are _expected_ to fail, and you cannot batch-verify a set of checks some of which are supposed to fail. In Tapscript every non-empty signature must be valid, so a node could validate all of a block's signatures in one batch and reject the block if the batch fails. Part VIII shows `OP_CHECKSIGADD` in action.

#### OP_SUCCESSx

Opcodes 80, 98, 126 to 129, 131 to 134, 137 to 138, 141 to 142, 149 to 153 and 187 to 254 are renamed `OP_SUCCESSx`. If one appears _anywhere_ in a tapscript, even in an unexecuted branch, the script succeeds immediately; the check happens before execution. That sounds alarming, but only the output's owner chose the script, so nobody can inject one into your coins. Its purpose is upgrades: a soft fork can turn any `OP_SUCCESSx` into a real opcode with arbitrary semantics (even ones that push to the stack, which redefined `OP_NOP`s could never do), because making a "succeed" opcode sometimes fail only tightens the rules. The flip side: using one today makes your output anyone-can-spend. `OP_CAT` (126) and the disabled arithmetic opcodes all live in this range, which is why covenant proposals target Tapscript.

---

## Part VII: The Output Types Side by Side, and Time

### 21. The output-type map

Every standard output type in one table. Input sizes assume compressed keys, 72-byte ECDSA signatures (including the sighash byte) and 64-byte Schnorr signatures; multisig rows are 2-of-3.

|Type|Since|`scriptPubKey`|Spent with|Output|Input|Address|Output commits to|
|---|---|---|---|---|---|---|---|
|P2PK|2009|`<pk> OP_CHECKSIG`|scriptSig `<sig>`|44 B|114 vB|none|the raw key|
|P2PKH|2009|`OP_DUP OP_HASH160 <20> OP_EQUALVERIFY OP_CHECKSIG`|scriptSig `<sig> <pk>`|34 B|148 vB|`1…`|HASH160 of the key|
|P2MS (bare)|2009|`OP_2 <pk> <pk> <pk> OP_3 OP_CHECKMULTISIG`|scriptSig `OP_0 <sig> <sig>`|114 B|188 vB|none|the raw script|
|OP_RETURN|2014 (policy)|`OP_RETURN <data>`|unspendable|9 B + script|n/a|none|nothing (data)|
|P2SH|2012, BIP16|`OP_HASH160 <20> OP_EQUAL`|scriptSig `… <redeemScript>`|32 B|297 vB (2-of-3)|`3…`|HASH160 of the script (80-bit collision security)|
|P2SH-P2WPKH|2017|P2SH|scriptSig `<0014…>` + witness `<sig> <pk>`|32 B|91 vB|`3…`|HASH160 of a v0 program|
|P2SH-P2WSH|2017|P2SH|scriptSig `<0020…>` + witness `… <script>`|32 B|139.5 vB (2-of-3)|`3…`|HASH160 of a v0 program (80-bit)|
|P2WPKH|2017, BIP141|`OP_0 <20>`|witness `<sig> <pk>`|31 B|68 vB|`bc1q…` (42)|HASH160 of the key|
|P2WSH|2017, BIP141|`OP_0 <32>`|witness `… <witnessScript>`|43 B|104.5 vB (2-of-3)|`bc1q…` (62)|SHA256 of the script (128-bit)|
|P2TR|2021, BIP341|`OP_1 <32>`|key path `<sig>`; script path `… <script> <control>`|43 B|57.5 vB (key path)|`bc1p…`|tweaked key (128-bit)|
|P2A|2024 (policy), BIP433|`OP_1 <4e73>`|empty witness|13 B|41 vB|`bc1pfeessrawgf`|nothing (keyless)|
|Future SegWit|reserved|`OP_2`…`OP_16` `<2–40 B>`|not standard to spend yet|≤ 51 B|n/a|`bc1z…` …|to be defined|

Two patterns jump out. First, each generation moved bytes from the output (paid by the sender, stored in the UTXO set) into the spend (paid by the receiver, discounted in the witness). Second, the commitment got stronger: from nothing (P2PK, bare multisig) to 160-bit hashes, to 256-bit hashes or keys.

Policy also sets a **dust threshold** per type: an output is dust if its value is below the cost of the output plus the input that would later spend it, priced at 3 sat/vB. The resulting numbers, which Lightning's specification lists explicitly:

|Type|Dust threshold|Calculation (bytes × 3 sat/vB)|
|---|---|---|
|P2PKH|546 sat|(34 output + 148 input) × 3|
|P2SH|540 sat|(32 + 148) × 3|
|P2WPKH|294 sat|(31 + 67) × 3, the input's witness discounted|
|P2WSH, P2TR|330 sat|(43 + 67) × 3|
|P2A|240 sat|(13 + 67) × 3|
|Unknown SegWit versions|354 sat|(51 + 67) × 3|
|OP_RETURN|never dust|unspendable, not in the UTXO set|

### 22. Timelocks: programming with time

Bitcoin has four timelock mechanisms, forming a 2×2 grid:

| |Transaction field|Script opcode|
|---|---|---|
|**Absolute** ("not before height/time X")|`nLockTime`|`OP_CHECKLOCKTIMEVERIFY` (BIP65, 2015)|
|**Relative** ("not before N blocks/seconds after the spent output confirmed")|`nSequence` (BIP68, 2016)|`OP_CHECKSEQUENCEVERIFY` (BIP112, 2016)|

The **field** restricts when a _transaction_ can be mined. The **opcode** restricts which transactions can spend an _output_, by forcing the spending transaction to set the field. The difference matters. The book's example: Alice signs a transaction to Bob with `nLockTime` three months ahead and hands it to him. Bob cannot broadcast it early, but nothing stops Alice from spending the same coins elsewhere tomorrow. To guarantee Bob the money, the condition must live in the _output_.

#### Absolute: OP_CHECKLOCKTIMEVERIFY

```text
<Bob's pubkey> OP_CHECKSIGVERIFY <now + 12960 blocks> OP_CHECKLOCKTIMEVERIFY
```

12,960 blocks is about 90 days. `OP_CHECKLOCKTIMEVERIFY` (CLTV) fails unless all of these hold:

- the stack is non-empty and the top item, read as a number, is non-negative;
- it is the same _kind_ of lock as the transaction's `nLockTime` (both heights below 500,000,000, or both timestamps);
- it is less than or equal to the transaction's `nLockTime`;
- the input's `nSequence` is not `0xffffffff` (otherwise `nLockTime` would be ignored).

Since the transaction can only be mined after its `nLockTime`, the output can only be spent after the script's time. Like every redefined `NOP`, CLTV leaves its argument on the stack, so it is usually followed by `OP_DROP` (above it simply serves as the final true value).

Two gotchas from the book. All time-based locks are measured against **median time past**, about an hour behind the clock. And since a transaction has one `nLockTime`, a script that requires both a height-based and a time-based CLTV can never be satisfied, nor can a transaction spend two inputs whose CLTVs use different kinds. Miniscript (Section 30) detects such mistakes.

#### Relative: nSequence and OP_CHECKSEQUENCEVERIFY

BIP68 gives the input's `nSequence` a second meaning when the transaction version is at least 2:

```text
 bit 31           bit 22                              bits 15..0
+---------------+-----------------------------------+------------------------------+
| disable flag  | type: 0 = blocks, 1 = 512-s units | lock value (16 bits)         |
+---------------+-----------------------------------+------------------------------+
```

If bit 31 is clear, the input cannot be mined until the output it spends is at least that old: up to 65,535 blocks (about 455 days) or $65{,}535 \times 512$ s (about 388 days). Examples: `0x00000090` means 144 blocks (about a day); `0x004000a8` means $168 \times 512 = 86{,}016$ seconds. Any relative lock also signals RBF, since such a sequence is below `0xfffffffe`.

`OP_CHECKSEQUENCEVERIFY` (CSV) is to `nSequence` what CLTV is to `nLockTime`:

```text
<1000> OP_CHECKSEQUENCEVERIFY OP_DROP <pubkey> OP_CHECKSIG
```

It requires transaction version ≥ 2, the disable bit clear, the same type flag, and a value at least as large as the script's. BIP68 then enforces the actual age. Because the clock starts when the output confirms, relative locks are the natural tool for chains of presigned transactions: "the other party has N blocks to respond after you publish". Lightning's penalty mechanism is built on exactly this (Section 31).

#### The book's grand finale: a company account with time-based fallbacks

Here is the book's Example 7-1 in full. Mohammed's company account is controlled by three partners (Mohammed, Saeed and Zaira) and their lawyer:

- normally, any 2 of the 3 partners can spend;
- after 30 days of inactivity, the lawyer plus any 1 partner can spend;
- after 90 days, the lawyer alone can spend.

```text
01  OP_IF
02    OP_IF
03      2
04    OP_ELSE
05      <30 days> OP_CHECKSEQUENCEVERIFY OP_DROP
06      <Lawyer's Pubkey> OP_CHECKSIGVERIFY
07      1
08    OP_ENDIF
09    <Mohammed's Pubkey> <Saeed's Pubkey> <Zaira's Pubkey> 3 OP_CHECKMULTISIG
10  OP_ELSE
11    <90 days> OP_CHECKSEQUENCEVERIFY OP_DROP
12    <Lawyer's Pubkey> OP_CHECKSIG
13  OP_ENDIF
```

The clever bit is lines 3 and 7: both branches of the inner `IF` just push the _threshold_ for the shared `CHECKMULTISIG` on line 9, 2 normally or 1 when the lawyer has already signed. The spender picks a path with the values on top of the stack (consumed top first):

|Path|Unlocking data (top of stack last)|`nSequence` needed|
|---|---|---|
|2 of 3 partners|`OP_0 <Mohammed's sig> <Zaira's sig> OP_TRUE OP_TRUE`|any|
|lawyer + 1 partner|`OP_0 <Saeed's sig> <Lawyer's sig> OP_FALSE OP_TRUE`|≥ 4,320 blocks|
|lawyer alone|`<Lawyer's sig> OP_FALSE`|≥ 12,960 blocks|

With compressed keys the script is 192 bytes. Running it through the interpreter with real signatures and 30 days as 4,320 blocks and 90 days as 12,960: path 1 is valid; path 2 is valid with `nSequence = 4320` and fails with "CSV failed" at `nSequence = 100`; path 3 is valid at 12,960 and fails at 4,320.

This script is a fine piece of engineering and also a perfect illustration of what Taproot fixed: every spend reveals all four keys, both timelocks and the company's governance structure, and every spend pays for the bytes of all three paths. We will rebuild it as a Taproot output in Section 28.

---

## Part VIII: Multisig, Five Generations

Everything so far was preparation for this part. "Multisig" in Bitcoin is not one technique but a family that grew with each protocol upgrade. We now have all the pieces to compare them precisely.

### 23. The multisig design space

Two distinctions organise everything:

- **$k$-of-$k$ versus $t$-of-$k$.** Either everyone must sign (a _multisignature_ in the narrow sense) or any $t$ of them may (a _threshold_ policy).
- **Scripted versus scriptless.** In a _scripted_ multisig, the keys and the individual signatures go on chain and Script checks them. In a _scriptless_ one, the parties combine keys and signatures off chain with cryptography, and the chain sees one key and one signature.

Choosing between constructions means trading along these axes:

|Axis|Scripted (CHECKMULTISIG, CHECKSIGADD)|Scriptless (MuSig2, FROST)|
|---|---|---|
|On-chain size|grows with the number of keys and signatures|constant: one key, one signature|
|Privacy|the policy and the signers are public on spend|indistinguishable from a single-key spend|
|Accountability|anyone can see which keys signed|nobody can prove who did or did not sign|
|Signing interaction|each signer signs independently, in any order, once|at least two rounds; signers keep secret nonce state between them|
|Key setup|just collect public keys|MuSig2: non-interactive aggregation; FROST: an interactive DKG (or a trusted dealer)|
|Expressiveness|any mix of keys, timelocks, hashlocks|just a key (but can be combined with Taproot leaves)|
|Tooling|universal in wallets and hardware signers|standardised (MuSig2) or still being standardised (FROST)|

The book's example of the interaction cost is memorable: if one of your hardware signers lives in a bank safe deposit box, a scripted multisig needs one visit to sign, a scriptless one may need two or three.

The five generations, which the rest of this part walks through:

|Generation|Construction|Since|
|---|---|---|
|1|bare `CHECKMULTISIG` (P2MS)|2009|
|2|`CHECKMULTISIG` inside P2SH|2012|
|3|`CHECKMULTISIG` inside P2WSH (and P2SH-P2WSH)|2017|
|4|Tapscript: `CHECKSIGADD`, `CHECKSIGVERIFY` chains, one leaf per signing set|2021|
|5|scriptless: MuSig2 ($k$-of-$k$) and FROST ($t$-of-$k$) in the Taproot key path|2021 onwards (BIP327 from 2022, FROST drafts 2024–26)|

### 24. Generations 1 to 3: CHECKMULTISIG in bare, P2SH and P2WSH outputs

The first three generations run the same script, `OP_t <pk_1> … <pk_k> OP_k OP_CHECKMULTISIG`, and differ only in where it lives:

| |Bare (P2MS)|P2SH|P2SH-P2WSH|P2WSH|
|---|---|---|---|---|
|Script lives in|the output|the `scriptSig`|the witness|the witness|
|Output commits with|nothing (the script itself)|HASH160 (20 B)|HASH160 of a SHA256 program|SHA256 (32 B)|
|Max keys|3 (policy)|15 (520-byte push)|20 per `CHECKMULTISIG`|20 per `CHECKMULTISIG`|
|Unlocking data|`OP_0 <sigs>` in `scriptSig`|`OP_0 <sigs> <redeemScript>` in `scriptSig`|`scriptSig` = `<0020…>`; witness = `"" <sigs> <script>`|witness = `"" <sigs> <script>`|
|2-of-3 input|188 vB|297 vB|139.5 vB|104.5 vB|

For signature-operation accounting, `CHECKMULTISIG` inside a P2SH redeem script or P2WSH witness script is counted "accurately" as $k$ sigops (read from the preceding `OP_k`, for $k \le 16$), versus a flat 20 in a bare output.

#### Where you meet generation 3 today

P2WSH `CHECKMULTISIG` remains the most widely supported multisig format: it is what most multisig coordinators and hardware signers default to, from personal cold storage to collaborative custody. It is also inside every Lightning channel opened without Taproot. BOLT 3 defines the funding output as a P2WSH of

```text
2 <pubkey1> <pubkey2> 2 OP_CHECKMULTISIG
```

where `pubkey1` is the lexicographically lesser of the two funding keys, and every commitment transaction spends it with the witness `0 <signature_for_pubkey1> <signature_for_pubkey2>` (the `0` being our old friend, the dummy).

#### Alternatives inside the same generation

`CHECKMULTISIG` is not the only way to write a policy in P2WSH:

- A $k$-of-$k$ can be a chain: `<A> OP_CHECKSIGVERIFY <B> OP_CHECKSIG`. For 2-of-2 that is 70 bytes versus 71, and it needs no dummy element.
- A threshold can be a counter: `<A> OP_CHECKSIG OP_SWAP <B> OP_CHECKSIG OP_ADD OP_SWAP <C> OP_CHECKSIG OP_ADD 2 OP_EQUAL`, with an empty signature for each non-signer. Miniscript compiles its `thresh()` fragment into exactly this kind of pattern, which mixes freely with timelocks and hashlocks.

#### Key order matters

`CHECKMULTISIG` is order-sensitive, and the script hash depends on the order of keys. If three cosigners each build "the" multisig from the same three keys in a different order, they get three different addresses. **BIP67** fixes a canonical order (sort compressed keys lexicographically), and descriptors expose it as `sortedmulti()`. For the toy keys of Alice, Bob and Carol used throughout this part:

```text
wsh(multi(2,A,B,C))           bc1qgckaltpvatqeds5czpe4cex7egywc7uh6gezcxqeaagnjdnxy93q6cvsfz
wsh(sortedmulti(2,A,B,C))     bc1qr4uvawnp3nz7az3y0f0dchkd6ujqwznms7fd6ey24q7d9yqnu37qst7lx9
sh(wsh(sortedmulti(2,A,B,C))) 38Hj7kSWxBLvhojqqVjujs6ZNMJFqgZG5q
sh(sortedmulti(2,A,B,C))      32JCHnM8YukpZMZYNnyhVTosZjLvmjuSp8
```

Same keys, same policy, four different addresses, all computed by my code and cross-checked against an independent descriptor implementation.

**Strengths of generations 1–3:** universal support, signers who never talk to each other (a PSBT can be passed from one hardware device to the next), and full accountability: given the public keys, anyone can tell which keys produced the signatures. **Weaknesses:** every spend publishes all $k$ keys and the threshold, fingerprinting the wallet; cost grows linearly in $k$ and $t$; 20 keys per opcode.

### 25. Generation 4: Tapscript multisig

Tapscript removed `CHECKMULTISIG` and gave us three replacements, which can be mixed inside one Taproot tree.

#### 25.1 One leaf, a running count: `multi_a`

```text
<A> OP_CHECKSIG <B> OP_CHECKSIGADD <C> OP_CHECKSIGADD OP_2 OP_NUMEQUAL
```

That is 104 bytes for three keys (each push is 33 bytes: `0x20` plus an x-only key). The witness provides one slot per key **in reverse order**, a valid signature or an empty vector, followed by the script and the control block. For Alice and Carol signing, the witness is `<sig_C> <> <sig_A> <script> <control block>`. The interpreter's trace (stack top on the right):

```text
initial                    sig_C  []  sig_A
<A> OP_CHECKSIG            sig_C  []  1          Alice's signature checks out
<B> OP_CHECKSIGADD         sig_C  1              empty signature: count unchanged
<C> OP_CHECKSIGADD         2                     Carol's signature: count + 1
OP_2 OP_NUMEQUAL           1                     2 == 2
```

Two consequences of BIP342's rules: a non-signer _must_ contribute an empty vector, and if any slot holds a non-empty but invalid signature, the **whole script fails** (the interpreter reports "bad signature" when Alice's signature is placed in Bob's slot). Descriptors call this `multi_a(t, …)` and `sortedmulti_a(t, …)` (BIP387, up to 999 keys, bounded by the 1,000-element stack limit). With the NUMS point as internal key, `tr(H, multi_a(2,A,B,C))` gives `bc1p0xj4cx4w9mf2sfsyusf3dezlrgyna0ayfdrwrs76k99qtv43pl0sfklkhx`. (A real wallet should use $H + rG$ rather than bare $H$, as Section 19 explained.)

A surprise in the numbers: this input is **108.75 vB, slightly larger than the 104.5 vB of P2WSH `CHECKMULTISIG`**. Schnorr signatures save 16 WU and x-only keys save 3, but the control block adds 34 and the two extra counting opcodes add 2. `multi_a` is not about size; it is about everything around it: batch-verifiable signatures, sitting in a tree with other branches that stay hidden, and coexisting with a key path.

#### 25.2 Everyone signs: `CHECKSIGVERIFY` chains

For $k$-of-$k$ in a leaf: `<A> OP_CHECKSIGVERIFY <B> OP_CHECKSIGVERIFY <C> OP_CHECKSIG`. No counting, no empty slots, and the smallest scripted form.

#### 25.3 One leaf per signing set

Rather than one leaf that accepts any $t$ of $k$ signatures, build one leaf for each possible set of $t$ signers, each a $t$-of-$t$ chain. A spend reveals only the keys that actually signed (and one 32-byte hash per tree level), and the other keys stay private. The number of leaves is $\binom{k}{t}$ and the proof length $\lceil \log_2 \binom{k}{t} \rceil$:

|Policy|Leaves $\binom{k}{t}$|Max path length (balanced tree)|
|---|---|---|
|2-of-3|3|2|
|3-of-5|10|4|
|4-of-7|35|6|
|6-of-10|210|8|
|10-of-15|3,003|12|
|15-of-20|15,504|14|

The tree grows combinatorially, but that cost is paid off chain when building the tree; on chain the cost grows only logarithmically. A 2-of-2 leaf at depth 1 costs 107.5 vB to spend, at depth 2 115.5 vB.

#### 25.4 One aggregated key per signing set

Replace each $t$-of-$t$ chain with a single key that is the MuSig2 aggregate of that set: the leaf is just `<agg> OP_CHECKSIG` (34 bytes). BIP342 itself suggests this as the most efficient scripted threshold. A spend is one Schnorr signature: **82.75 vB** at depth 1, 90.75 vB at depth 2, and observers learn only which _aggregate_ signed. The price is that the signers in that set must run the interactive MuSig2 protocol, which brings us to generation 5.

### 26. Generation 5: scriptless multisig with MuSig2

The goal: $k$ parties, one 32-byte public key, one 64-byte signature, and nothing on chain to say there was more than one signer. Schnorr's linearity makes it _almost_ trivial; the "almost" is where the attacks live.

#### The naive scheme and the key-cancellation attack

Let each party $i$ have $x_i$, $X_i = x_i G$. Naively, the joint key is $X = \sum X_i$; each party picks a nonce $r_i$, the joint nonce is $R = \sum r_i G$, the challenge is $e = H(R \Vert X \Vert m)$, each party returns $s_i = r_i + e x_i$, and $s = \sum s_i$ satisfies $sG = R + eX$.

The book shows why this breaks: Bob waits for Alice's key $X_A$ and announces $X_B = zG - X_A$. The joint key is $X_A + X_B = zG$, which Bob alone controls. Commit-then-reveal of keys helps but is easy to get wrong. MuSig instead **weights each key by a hash of the whole key set**:

$$ L = H_{\text{KeyAgg list}}(X_1 \Vert X_2 \Vert \dots \Vert X_k), \qquad a_i = H_{\text{KeyAgg coefficient}}(L \Vert X_i), \qquad \tilde{X} = \sum_i a_i X_i $$

Now Bob cannot choose $X_B$ to cancel Alice's term, because changing $X_B$ changes every coefficient. (BIP327 sets the coefficient of the second distinct key to 1, a harmless optimisation.) Aggregation needs no interaction: anyone with the public keys can compute $\tilde{X}$.

#### Why two nonces

The nonces are the subtle part. A two-round protocol with _one_ nonce per signer turns out to be insecure when an attacker can open many signing sessions concurrently (Wagner's generalised-birthday algorithm, and later the ROS attack, let them combine sessions into a forgery). The first MuSig added a third round in which everyone commits to their nonce before revealing it. **MuSig2** gets back to two rounds by having each signer contribute _two_ nonces and binding them with a hash:

1. **Round 1 (nonces).** Each signer $i$ samples $r_{i,1}, r_{i,2}$ and publishes $R_{i,1} = r_{i,1}G$ and $R_{i,2} = r_{i,2}G$. Aggregates: $R_1 = \sum_i R_{i,1}$, $R_2 = \sum_i R_{i,2}$. This round does not depend on the message, so it can be done in advance.
2. **Round 2 (signatures).** Everyone computes $b = H_{\text{MuSig/noncecoef}}(R_1 \Vert R_2 \Vert \tilde{X} \Vert m)$, $R = R_1 + bR_2$ and $e = H_{\text{BIP0340/challenge}}(R \Vert \tilde{X} \Vert m)$, and each signer returns $s_i = r_{i,1} + b\,r_{i,2} + e\,a_i x_i$. The signature is $(R, s = \sum_i s_i)$.

Verification is **plain BIP340**, because

$$ sG = \sum_i (r_{i,1} + b\,r_{i,2})G + e \sum_i a_i x_i G = R_1 + bR_2 + e\tilde{X} = R + e\tilde{X}. $$

The real BIP327 algorithm also handles the even-$y$ conventions of x-only keys (negating nonces or keys where needed) and supports **tweaking** the aggregate key, which is exactly what you need to use $\tilde{X}$ as a Taproot internal key and spend through the key path.

#### MuSig2 in 40 lines

This toy reuses the helpers from Sections 3 and 17. Its key aggregation and partial signatures reproduce the official BIP327 test vectors, and the final signature passes the `schnorr_verify` from Section 17 unchanged.

```python
import os
def sec(pt): return bytes([2 + (pt[1] & 1)]) + xonly(pt)            # 33-byte compressed key
def parse_sec(b):
    pt = lift_x(i(b[1:]))
    return pt if (pt[1] & 1) == (b[0] & 1) else (pt[0], P - pt[1])

def key_agg(pubkeys):                                                # BIP327 KeyAgg (no tweaks)
    L = tagged_hash("KeyAgg list", b"".join(pubkeys))
    second = next((pk for pk in pubkeys[1:] if pk != pubkeys[0]), None)
    coeff = lambda pk: 1 if pk == second else i(tagged_hash("KeyAgg coefficient", L + pk)) % N
    Q = None
    for pk in pubkeys:
        Q = point_add(Q, point_mul(parse_sec(pk), coeff(pk)))
    return Q, coeff

def nonce_agg(pubnonces):                                            # each pubnonce = R1 || R2
    agg = b""
    for j in (0, 1):
        R = None
        for pn in pubnonces:
            R = point_add(R, parse_sec(pn[33 * j:33 * (j + 1)]))
        agg += sec(R)
    return agg

def session(aggnonce, Q, msg):
    b = i(tagged_hash("MuSig/noncecoef", aggnonce + xonly(Q) + msg)) % N
    R = point_add(parse_sec(aggnonce[:33]), point_mul(parse_sec(aggnonce[33:]), b))
    e = i(tagged_hash("BIP0340/challenge", xonly(R) + xonly(Q) + msg)) % N
    return b, R, e

def partial_sign(k1, k2, sk, pubkeys, aggnonce, msg):
    Q, coeff = key_agg(pubkeys)
    b, R, e = session(aggnonce, Q, msg)
    if R[1] % 2: k1, k2 = N - k1, N - k2                             # BIP340 needs even-y R
    d = sk if Q[1] % 2 == 0 else N - sk                              # ...and an even-y key
    return (k1 + b * k2 + e * coeff(sec(point_mul(G, sk))) * d) % N

# three signers, one key, one signature
sks = [i(os.urandom(32)) % N for _ in range(3)]
pks = [sec(point_mul(G, sk)) for sk in sks]
X_agg, _ = key_agg(pks)
msg = tagged_hash("demo", b"spend the 3-of-3")
nonces = [(i(os.urandom(32)) % N, i(os.urandom(32)) % N) for _ in sks]          # round 1
aggnonce = nonce_agg([sec(point_mul(G, k1)) + sec(point_mul(G, k2)) for k1, k2 in nonces])
partials = [partial_sign(k1, k2, sk, pks, aggnonce, msg) for (k1, k2), sk in zip(nonces, sks)]  # round 2
_, R, _ = session(aggnonce, X_agg, msg)
sig = xonly(R) + (sum(partials) % N).to_bytes(32, "big")
assert schnorr_verify(msg, xonly(X_agg), sig)                        # an ordinary BIP340 signature
```

#### The rules that keep MuSig2 safe

- **Never reuse a secret nonce.** If a signer answers two sessions with the same $(r_{i,1}, r_{i,2})$ but a different $b$ or $e$, the two partial signatures are two linear equations in $x_i$. BIP327 tells implementations to erase the secret nonce once used.
- **Do not derive nonces deterministically from (key, message).** This is the counter-intuitive one. RFC6979-style determinism is the _safe_ choice for single-signer ECDSA and Schnorr, but in MuSig2 a malicious co-signer can rerun a session for the same message with different nonces of their own. Your deterministic nonce stays the same while $b$ and $e$ change, and your key leaks. BIP327 allows deterministic signing only for the _last_ signer, who already knows everyone else's nonces.
- **Signers are stateful between rounds.** The secret nonce must survive from round 1 to round 2 and then be destroyed, which is awkward for hardware signers designed to be stateless.

#### Where MuSig2 is used

MuSig2 is standardised in BIP327 (marked Deployed), with companion specifications for deriving child keys from an aggregate (BIP328), PSBT fields for nonces and partial signatures (BIP373) and a `musig()` descriptor expression (BIP390, still a draft). It secures the shared outputs of protocols where the parties are online anyway: Lightning's simple Taproot channels (deployed experimentally in LND) use a MuSig2 2-of-2 for the funding output, and Ark's batch outputs are an $n$-of-$n$ MuSig2 between all participants and the operator (Section 32).

### 27. Threshold signatures with FROST

MuSig2 is $k$-of-$k$. For a $t$-of-$k$ policy that still produces one key and one signature you need a **threshold signature** scheme, and in the Schnorr world the leading one is FROST (Flexible Round-Optimized Schnorr Threshold signatures).

#### The algebra: secret sharing in the exponent

Shamir's secret sharing hides a secret $x$ in a random polynomial of degree $t - 1$:

$$ f(z) = x + a_1 z + a_2 z^2 + \dots + a_{t-1} z^{t-1}, \qquad \text{share}_j = f(j) $$

Any $t$ shares determine the polynomial, and so $x = f(0)$, by Lagrange interpolation; fewer than $t$ reveal nothing:

$$ x = \sum_{j \in S} \lambda_j \, f(j), \qquad \lambda_j = \prod_{m \in S,\ m \ne j} \frac{m}{m - j} \pmod n $$

For signers $S = \{1, 3\}$ of a 2-of-3, $\lambda_1 = 3/2$ and $\lambda_3 = -1/2$ (as field elements mod $n$). The trick is that nobody ever reconstructs $x$. Each signer multiplies their share by their Lagrange coefficient _inside_ a Schnorr signature, and the sum of those partial signatures is a signature for $X = xG$.

In a real deployment the polynomial is not chosen by a dealer who knows $x$: each participant deals a polynomial of their own and the group key is the sum, using commitments (Feldman or Pedersen verifiable secret sharing) so everyone can check that the shares they received are consistent. That is a **distributed key generation (DKG)**; ChillDKG is the Bitcoin-specific proposal. The book describes the simplest variant, where each participant splits their MuSig key share among the others so that any $t$ can reconstruct a missing participant, and points out the two inherent caveats: **no accountability** (a threshold signature cannot reveal who signed) and **manipulation attacks** (a participant can tell different cosigners different stories to collect enough shares to sign alone, unless all communication is broadcast).

#### Signing in two rounds

1. Each signer $j$ in the signing set $S$ publishes two nonce commitments $D_j = d_j G$, $E_j = e_j G$.
2. Everyone computes a **binding factor** per signer, $\rho_j = H(j, m, B)$ where $B$ is the list of all commitments, the group nonce $R = \sum_{j \in S} (D_j + \rho_j E_j)$, and the BIP340 challenge $c = H(R \Vert X \Vert m)$. Each signer returns $z_j = d_j + \rho_j e_j + \lambda_j \cdot \text{share}_j \cdot c$, and $z = \sum z_j$ satisfies $zG = R + cX$: an ordinary BIP340 signature.

The binding factors play the role of MuSig2's $b$: they stop an attacker from adapting their nonce to everyone else's. A toy 2-of-3 with a trusted dealer, again verified with the plain `schnorr_verify`:

```python
rand = lambda: i(os.urandom(32)) % N
x, a1 = rand(), rand()                                   # dealer's secret polynomial f(z) = x + a1*z
if point_mul(G, x)[1] % 2: x = N - x                     # x-only group key: force even y
X = point_mul(G, x)
share = {j: (x + a1 * j) % N for j in (1, 2, 3)}

def lagrange(j, S):
    num = den = 1
    for m in S:
        if m != j: num, den = num * m % N, den * (m - j) % N
    return num * pow(den, N - 2, N) % N

S, msg = (1, 3), tagged_hash("demo", b"2-of-3 spend")    # Alice (1) and Carol (3) sign
nonce = {j: (rand(), rand()) for j in S}                 # round 1: d_j, e_j and their commitments
comm = {j: (point_mul(G, d), point_mul(G, e)) for j, (d, e) in nonce.items()}
commit_list = b"".join(bytes([j]) + sec(D) + sec(E) for j, (D, E) in sorted(comm.items()))
rho = {j: i(tagged_hash("toy/rho", bytes([j]) + msg + commit_list)) % N for j in S}
R = None
for j in S:
    R = point_add(R, point_add(comm[j][0], point_mul(comm[j][1], rho[j])))
flip = R[1] % 2 == 1                                     # BIP340 needs an even-y R
if flip: R = (R[0], P - R[1])
c = i(tagged_hash("BIP0340/challenge", xonly(R) + xonly(X) + msg)) % N
z = 0
for j in S:                                              # round 2: partial signatures
    d, e = nonce[j]
    if flip: d, e = N - d, N - e
    z += d + rho[j] * e + lagrange(j, S) * share[j] * c
assert schnorr_verify(msg, xonly(X), xonly(R) + (z % N).to_bytes(32, "big"))
```

#### Where FROST stands

When _Mastering Bitcoin_ went to press, no scriptless threshold scheme had a BIP. As of 2026 there are drafts: ChillDKG for key generation and a "FROST Signing Protocol for BIP340 Signatures" draft opened in January 2026 that adapts RFC 9591 to x-only keys and Taproot tweaks, closely following BIP327's structure. They are still under review, so production FROST today means carefully chosen libraries and custom integration. The attraction is obvious: a 2-of-3, a 7-of-10 or a 67-of-100 all cost the same 57.5 vB to spend and look exactly like a single-signature wallet.

### 28. Hybrid designs: keys on top, scripts underneath

BIP341's own advice for using Taproot is a design method:

1. Put the **most likely** spending condition in the key path. If it involves several parties, aggregate their keys (MuSig2, or FROST for thresholds).
2. Put the less likely conditions in leaves, more likely ones nearer the root.
3. If no single key or aggregate should ever be able to spend, use a NUMS internal key.

#### Example 1: everyday 2-of-3

This is the output built in Section 19. Alice and Bob are the usual signers, Carol holds a backup key:

```text
                     output key  Q = P + t*G          (on chain: OP_1 <Q>)
                                   |
                 +-----------------+------------------+
                 |                                    |
       internal key P = MuSig2(A, B)            Merkle root
       (key path: one signature)                      |
                                        +-------------+-------------+
                                        |                           |
                                <A> CHECKSIGVERIFY          <B> CHECKSIGVERIFY
                                <C> CHECKSIG                <C> CHECKSIG
```

|Who signs|Path|Input size|What observers learn|
|---|---|---|---|
|Alice + Bob|key path, MuSig2|57.5 vB|nothing: looks like a single-key spend|
|Alice + Carol|leaf 1 (depth 1)|107.5 vB|two keys signed under a script; one hidden sibling|
|Bob + Carol|leaf 2 (depth 1)|107.5 vB|likewise|

Replacing each leaf's chain with a MuSig2 aggregate of the pair would cut the fallback spends to 82.75 vB, at the cost of an interactive signing round for those pairs.

#### Example 2: a multisig that decays into a recovery key

Inheritance and key-loss recovery are where scripts earn their keep. Normal operation is 2-of-3; if the coins sit untouched for about six months (26,280 blocks), a recovery key $R$ held by a lawyer or heir can sweep them:

```text
tr(H, { multi_a(2,A,B,C), and_v(v:pk(R),older(26280)) })
```

The second leaf compiles to `<R> OP_CHECKSIGVERIFY <26280> OP_CHECKSEQUENCEVERIFY`, and with the toy keys (and the bare NUMS key $H$) the address is `bc1p02lmc4ef6g3kjv4qfcdzejjmjhdhflxvypjxzxsp6e3qexfu6lkqpep3fz`; my Taproot code and the independent descriptor library agree. Because the timelock is _relative_, the clock restarts whenever the coins move, so the owners keep the recovery path dormant simply by spending to themselves now and then. That "dead man's switch" pattern is the basis of several inheritance-oriented wallets.

#### Example 3: Mohammed's company account, rebuilt

Section 22's 192-byte script translates into a Taproot tree like this:

- **key path:** MuSig2 of Mohammed, Saeed and Zaira (or a FROST 2-of-3 key once that tooling is mature);
- **leaf 1 (depth 1):** `multi_a(2, M, S, Z)`, any two partners;
- **leaf 2 (depth 2):** `<L> OP_CHECKSIGVERIFY <4320> OP_CHECKSEQUENCEVERIFY OP_DROP <M> OP_CHECKSIG <S> OP_CHECKSIGADD <Z> OP_CHECKSIGADD OP_1 OP_NUMEQUAL`, the lawyer plus one partner after 30 days;
- **leaf 3 (depth 2):** `<L> OP_CHECKSIGVERIFY <12960> OP_CHECKSEQUENCEVERIFY`, the lawyer alone after 90 days.

|Spending path|P2WSH (the book's script)|Taproot tree|
|---|---|---|
|all three partners|127.25 vB (via the 2-of-3 path)|**57.5 vB** (key path)|
|two partners|127.25 vB|116.75 vB|
|lawyer + one partner, after 30 days|127.0 vB|134.75 vB|
|lawyer alone, after 90 days|108.0 vB|91.75 vB|
|revealed on chain|everything, every time|only the path used; nothing on the key path|

Taproot is not uniformly smaller: the second path re-lists the partners' keys and pays for a control block, so it costs a little more than the monolithic script. But the common case collapses to the cheapest possible spend, and the existence of a lawyer, the timelocks and the company's governance stay private until someone actually needs them.

### 29. The numbers: one 2-of-3 policy, eight encodings

Here is one policy, "any two of Alice, Bob and Carol", written every way this article has covered. Sizes are for one input with 72-byte ECDSA and 64-byte Schnorr signatures, computed by serialising real transactions:

|#|Encoding|Input|Output|Revealed when spent|Who-signed visible?|Signing rounds|
|---|---|---|---|---|---|---|
|1|Bare multisig (P2MS)|188 vB|114 B|3 keys, threshold|yes|1|
|2|P2SH|297 vB|32 B|3 keys, threshold|yes|1|
|3|P2SH-P2WSH|139.5 vB|32 B|3 keys, threshold|yes|1|
|4|P2WSH|104.5 vB|43 B|3 keys, threshold|yes|1|
|5|P2TR, `multi_a` leaf, NUMS key|108.75 vB|43 B|3 keys, threshold|yes|1|
|6|P2TR, 2-of-2 leaf at depth 1|107.5 vB|43 B|2 keys, one hash|yes|1|
|7|P2TR, MuSig2-pair leaf at depth 1|82.75 vB|43 B|1 aggregate key, one hash|which pair|2|
|8|P2TR key path, MuSig2 pair or FROST 2-of-3|57.5 vB|43 B|nothing|no|2|

From row 2 to row 8 the cost of spending falls by more than a factor of five, and the information leaked falls to zero. In between sits a spectrum of trade-offs, which is why newer multisig designs increasingly combine constructions: a key path for the common case, scripted leaves for recovery and accountability.

### 30. Running multisig in practice

Cryptography is the easy part of multisig. Many real-world failures come from operations instead: lost configuration, mismatched keys, and signing devices that were tricked.

#### Descriptors are the wallet

A seed phrase alone cannot recover a multisig wallet. The book makes the point with Alice, Bob and Carol: although Alice needs only one other signature to spend, she needs **all three public keys** (and the script template) just to _find_ the coins on chain, because the outputs commit to all of them. The standard way to record that information is an **output script descriptor** (BIPs 380 to 390):

```text
wsh(sortedmulti(2,
    [a1b2c3d4/48h/0h/0h/2h]xpub6E.../<0;1>/*,
    [e5f6a7b8/48h/0h/0h/2h]xpub6F.../<0;1>/*,
    [c9d0e1f2/48h/0h/0h/2h]xpub6G.../<0;1>/*))
```

Each key carries its origin (master key fingerprint and derivation path, here the BIP48 convention `m/48'/0'/0'/2'` for P2WSH multisig), the `<0;1>` multipath expression (BIP389) covers receive and change addresses, and `/*` ranges over indexes. The Taproot equivalents are `tr(KEY, sortedmulti_a(2, …))` for the scripted form and `tr(musig(A,B), {...})` for MuSig2 (BIP390). **Back up the descriptor alongside every seed.** It is not secret in the same way (it cannot spend), but it reveals your entire transaction history.

#### PSBT, round by round

A typical 2-of-3 P2WSH spend with hardware signers:

1. The **coordinator** (a desktop wallet that knows the descriptor) creates a PSBT: the unsigned transaction, plus for each input the UTXO being spent, the witness script and every key's derivation path.
2. Signer 1 checks the PSBT, verifies the change output belongs to the same descriptor, signs, and adds a partial signature.
3. Signer 2 does the same, in any order and without talking to signer 1.
4. The **finalizer** assembles the witness (`""`, the signatures in key order, the witness script) and extracts a network transaction.

Taproot adds PSBT fields for key-path and script-path signatures, leaf scripts and control blocks (BIP371); MuSig2 adds fields for public nonces and partial signatures (BIP373), which turns the flow into two passes around the signers.

Step 2's change check is where hardware wallets earn their money. A malicious coordinator can otherwise replace the change output with an address that _looks_ like a multisig of yours but contains the attacker's keys. To check, the device must know the full policy, so modern devices ask you to **register** the descriptor (or "wallet policy", BIP388) once and verify its fingerprint on screen.

#### Miniscript

Hand-written scripts like Mohammed's are error-prone: a mixed height/time timelock, a malleable branch, or a path that can never be satisfied are easy to write and hard to spot. **Miniscript** (BIP379) is a structured subset of Script with a type system that can prove a script correct, non-malleable and within resource limits, compute worst-case witness sizes, and let any compliant wallet produce a witness for any policy. It composes:

```text
and_v(v:pk(R),older(26280))      ->  <R> OP_CHECKSIGVERIFY <26280> OP_CHECKSEQUENCEVERIFY
multi_a(2,A,B,C)                 ->  <A> OP_CHECKSIG <B> OP_CHECKSIGADD <C> OP_CHECKSIGADD OP_2 OP_NUMEQUAL
```

and it is what lets descriptors like `tr(H, {multi_a(…), and_v(…)})` exist at all.

#### Choosing a construction

|If you need…|Prefer|
|---|---|
|maximum compatibility with today's hardware signers and coordinators|P2WSH `sortedmulti`|
|to prove which keys signed (audit, corporate governance)|scripted multisig: P2WSH or Tapscript `multi_a`|
|privacy and minimum fees, parties online together (channels, Ark, joint accounts)|MuSig2 in the Taproot key path|
|recovery paths, inheritance, decaying thresholds|Taproot: key path for normal use, timelocked leaves for recovery|
|large $t$-of-$k$ with constant cost|FROST in the key path (maturing), or one MuSig2 leaf per signing set|
|signers that cannot keep state between rounds|scripted multisig|

---

## Part IX: Scripts in the Wild

Abstract templates are one thing; scripts that guard billions of dollars every day are another. This part reads a few of them line by line.

### 31. Lightning's scripts

Lightning (specified in the BOLTs) is one of the most heavily used contract systems on Bitcoin, and BOLT 3 is a masterclass in Script. Every channel is built from a handful of templates.

#### The funding output and the commitment transactions

We met the funding output in Section 24: a P2WSH 2-of-2 `CHECKMULTISIG`. Each party then holds its own version of a **commitment transaction** that spends it. The versions are _asymmetric_, as in the book's Hitesh-and-Irene example: in my copy, the other party's money is paid to them immediately, while my own money is locked behind a delay and a revocation escape hatch. Publishing my commitment is always allowed, but it costs me a wait.

#### `to_local`: delayed, revocable

```text
OP_IF
    # Penalty transaction
    <revocationpubkey>
OP_ELSE
    `to_self_delay`
    OP_CHECKSEQUENCEVERIFY
    OP_DROP
    <local_delayedpubkey>
OP_ENDIF
OP_CHECKSIG
```

The owner spends it with `<local_delayedsig> <>` (an empty vector selects the `ELSE` branch, which MINIMALIF requires to be exactly empty) after `to_self_delay` blocks, enforced by CSV. If the owner ever publishes an **old** commitment, the counterparty spends it immediately with `<revocation_sig> 1` and takes everything.

The revocation key is a nice application of key tweaking (Section 3). Each commitment has a fresh `per_commitment_point` chosen by its owner, and the other party has a `revocation_basepoint`:

$$ \text{revocationpubkey} = B_{rev} \cdot H(B_{rev} \Vert C) + C \cdot H(C \Vert B_{rev}) $$

where $B_{rev}$ is the revocation basepoint and $C$ the per-commitment point. Its private key is $b_{rev} \cdot H(B_{rev} \Vert C) + c \cdot H(C \Vert B_{rev})$, which needs _both_ secrets. When a channel moves to a new state, the owner of the old commitment hands over the old per-commitment secret $c$, and from then on the counterparty can compute the revocation key for that old state. The hash coefficients play the same role as MuSig's: neither side can pick a point that cancels the other's. The book notes that LN indexes states with a 48-bit counter, so a channel can go through about $2.8 \times 10^{14}$ updates.

#### Anchor outputs: fee bumping with two lines of Script

Commitment transactions are signed long before they are broadcast, so their fee is a guess. Anchor outputs let either party bump the fee later with CPFP:

```text
<local_funding_pubkey/remote_funding_pubkey> OP_CHECKSIG OP_IFDUP
OP_NOTIF
    OP_16 OP_CHECKSEQUENCEVERIFY
OP_ENDIF
```

Trace both ways through it:

- **Owner, with a signature:** `OP_CHECKSIG` leaves `1`; `OP_IFDUP` duplicates it because it is true; `OP_NOTIF` consumes one copy and skips the body; the remaining `1` makes the spend valid. The owner can attach a fee-paying child at once.
- **Anyone, with an empty witness:** `OP_CHECKSIG` leaves false; `OP_IFDUP` does not duplicate false; `OP_NOTIF` consumes it and runs `OP_16 OP_CHECKSEQUENCEVERIFY`, which passes only if the input is 16 blocks old, and leaves `16` (true) on the stack.

The second path exists so that unused 330-sat anchors do not pollute the UTXO set forever: once the commitment is 16 blocks deep, anyone can sweep them. My interpreter agrees: the owner path leaves `01`, the anyone path leaves `10` (16) with `nSequence = 16`, and fails with "CSV failed" at `nSequence = 5`.

With anchors, every _other_ commitment output gets at least a one-block CSV, including `to_remote`:

```text
<remotepubkey> OP_CHECKSIGVERIFY 1 OP_CHECKSEQUENCEVERIFY
```

That stops a counterparty from using their own unconfirmed output to attach children and pin the commitment transaction; the only CPFP hooks are the anchors.

The newest variant goes further. With `zero_fee_commitments`, the commitment is a **version 3 (TRUC)** transaction that normally pays no fee of its own and carries a single `shared_anchor`:

```text
OP_1 <0x4e73>
```

That is P2A, spent with an empty witness by whichever party needs the transaction confirmed, with a value of at most 240 sat (below dust is allowed under the ephemeral-dust rule). This is the TRUC, package relay, P2A and ephemeral dust machinery of Section 5.5 working together.

#### The offered HTLC: branching on the size of a witness item

An in-flight payment is an HTLC output on the commitment. For an HTLC _I_ offered, the script is:

```text
# To remote node with revocation key
OP_DUP OP_HASH160 <RIPEMD160(SHA256(revocationpubkey))> OP_EQUAL
OP_IF
    OP_CHECKSIG
OP_ELSE
    <remote_htlcpubkey> OP_SWAP OP_SIZE 32 OP_EQUAL
    OP_NOTIF
        # To local node via HTLC-timeout transaction (timelocked).
        OP_DROP 2 OP_SWAP <local_htlcpubkey> 2 OP_CHECKMULTISIG
    OP_ELSE
        # To remote node with preimage.
        OP_HASH160 <RIPEMD160(payment_hash)> OP_EQUALVERIFY
        OP_CHECKSIG
    OP_ENDIF
OP_ENDIF
```

Three spending paths, chosen by inspecting the witness itself:

1. **Revocation**, witness `<revocation_sig> <revocationpubkey>`: the top item hashes to the committed value, `OP_EQUAL` is true, and a plain `OP_CHECKSIG` follows. Storing only a hash of the revocation key saves bytes in the common case.
2. **Payment preimage**, witness `<remotehtlcsig> <payment_preimage>`: the hash test fails, so we enter `ELSE`. The remote key is pushed and swapped under the preimage, and `OP_SIZE 32 OP_EQUAL` asks _"is the top item 32 bytes long?"_ A preimage is exactly 32 bytes and a signature never is, so this one test tells the two remaining paths apart. Then `OP_HASH160` of the preimage is compared with `RIPEMD160(payment_hash)`. Since Lightning's `payment_hash` is SHA256 of the preimage, $\text{HASH160}(\text{preimage}) = \text{RIPEMD160}(\text{payment\_hash})$, a neat way to reuse the cheaper 20-byte comparison.
3. **Timeout**, witness `0 <remotehtlcsig> <localhtlcsig> <>`: the empty item has size 0, so the `NOTIF` branch drops it and performs a 2-of-2 `CHECKMULTISIG` with both HTLC keys. The remote signature exists only on a presigned _HTLC-timeout_ transaction whose `nLockTime` is the HTLC's expiry, so this path cannot be used early.

I ran all three paths through the interpreter with real keys and signatures: all valid, and a wrong preimage fails at `OP_EQUALVERIFY`. With anchors, a `1 OP_CHECKSEQUENCEVERIFY OP_DROP` is added before the final `OP_ENDIF`, for the same anti-pinning reason as above.

### 32. HTLCs, Ark, data carriers and covenants

#### Hash time-locked contracts and atomic swaps

Stripped of Lightning's revocation machinery, the book's HTLC is:

```text
OP_IF
    OP_HASH160 <H> OP_EQUALVERIFY <Receiver's pubkey> OP_CHECKSIG     # claim with the secret
OP_ELSE
    <lock time> OP_CHECKLOCKTIMEVERIFY OP_DROP <Payer's pubkey> OP_CHECKSIG   # refund after timeout
OP_ENDIF
```

With $H$ = HASH160 of a secret $R$ and a lock time of block 800,000, the interpreter accepts `<receiver sig> <R> 1`, rejects a wrong secret at `OP_EQUALVERIFY`, accepts the refund `<payer sig> 0` in a transaction with `nLockTime = 800001`, and rejects it with `nLockTime = 799999`.

The book's routing example shows why HTLCs compose. Eric invoices Alice with $H$; Alice offers Bob an HTLC for 1.003 BTC expiring in 10 blocks; Bob offers Carol 1.002 BTC for 9 blocks; Carol offers Diana 1.001 for 8; Diana offers Eric 1.000 for 7. When Eric claims with $R$, the secret flows back down the chain and every hop claims its incoming HTLC. Decreasing timeouts guarantee that each intermediary learns $R$ before their own refund deadline arrives. The same hash lock, with the same SHA256 secret, works on any chain that can check a hash, which is how BTC can be swapped atomically against coins on another chain (Ethereum included) or against a Lightning payment (a "submarine swap"). Schnorr signatures also allow replacing the hash with a point (_adaptor signatures_ and PTLCs), so the hops of a payment no longer share one recognisable hash.

#### Ark's virtual UTXOs

Ark protocols such as Arkade let many users share one on-chain output while each holds a _virtual_ UTXO (VTXO) they can exit on chain unilaterally. Arkade's documentation describes the VTXO as a Taproot output with an unspendable internal key and two leaves:

- **collaborative path** (the default): `checkSig(userPK) && checkSig(operatorPK)`, used for off-chain transfers;
- **unilateral exit path**: `checkSig(userPK) && relativeTimelock(exitDelay)`, the user's guaranteed way out, where the CSV delay prevents double-spending races.

In Tapscript, one natural encoding is `<user> OP_CHECKSIGVERIFY <operator> OP_CHECKSIG` and `<exitDelay> OP_CHECKSEQUENCEVERIFY OP_DROP <user> OP_CHECKSIG`. Batches of VTXOs hang from a tree of presigned transactions rooted at a **batch output** locked to an $n$-of-$n$ **MuSig2** key of all the VTXO owners and the operator, with an operator sweep path after the batch expires; thanks to MuSig2, each node of that tree appears on chain as a single signature if users ever have to exit. Look closely and you see the patterns of this article combined: Taproot leaves, a 2-of-2, a CSV escape hatch (Lightning's `to_local` idea), and scriptless multisig for the shared outputs.

#### Data in Script: OP_RETURN, envelopes and fake keys

Three techniques carry non-financial data today, and each sits at a different point of the cost/UTXO trade-off:

- **`OP_RETURN` outputs** (Section 11): pruned from the UTXO set, full weight, and since Core 30.0 relayed up to 100 kB by default. Runes use `OP_RETURN OP_13 <payload>`.
- **Witness envelopes** in Tapscript leaves. Ordinals inscriptions place data in a branch that never executes (example below). The envelope is added to an ordinary `<pubkey> OP_CHECKSIG` leaf, so only the key holder can reveal it. It is committed by a Taproot output and revealed in the witness of the spend (a commit-reveal pair of transactions). It works because Tapscript removed the 10,000-byte script limit; each push is still capped at 520 bytes, so large files are split into many pushes. The data pays the witness discount and never touches the UTXO set.
- **Fake public keys** in bare multisig (Section 10): the most expensive option for node operators, since the outputs can never be spent.

An inscription envelope:

```text
OP_FALSE OP_IF
    OP_PUSH "ord"
    OP_PUSH 1  OP_PUSH "text/plain;charset=utf-8"
    OP_PUSH 0  OP_PUSH "Hello, world!"
OP_ENDIF
```

Whether this is a legitimate use of block space is one of Bitcoin's long-running arguments. Technically it is a clean demonstration of how flexible "commit now, reveal later" becomes once Taproot is available.

#### Covenants: what Script still cannot do

Everything in this article constrains _who_ may spend and _when_. Script cannot constrain _where the coins go next_: apart from what a signature commits to, it has no way to inspect the spending transaction's outputs. That is why vaults today rely on presigned transactions and deleted keys, and why Ark needs an operator to cosign. Several soft-fork proposals would add such **covenants**: `OP_CHECKTEMPLATEVERIFY` (BIP119) to commit to the exact shape of the spending transaction, `OP_CHECKSIGFROMSTACK` (BIP348) to verify signatures over arbitrary data, `OP_CAT` (BIP347) to re-enable concatenation inside Tapscript, `SIGHASH_ANYPREVOUT` (BIP118) for rebindable signatures, `OP_VAULT` (BIP345) for vaults, and combinations such as LNHANCE. As of this writing none of them has activated, and how (or whether) to activate them is an open debate. Meanwhile, BitVM-style designs push today's rules to their limit, using enormous Taproot trees and presigned transaction graphs to verify arbitrary computation optimistically, without any soft fork.

---

## Part X: The Whole Picture

### 33. The evolution in one page

Read in order, the output types tell a single story:

|Step|What the output commits to|What moved, and why|
|---|---|---|
|P2PK|a public key|the whitepaper's model, made scriptable|
|P2PKH|a hash of a key|shorter outputs, checksummed addresses; the key appears only when spending|
|P2MS|a full script|multiple keys, but the sender pays and the UTXO set stores it|
|P2SH|a hash of a script|the script's cost and complexity move to the receiver and to spend time|
|P2WPKH / P2WSH|a versioned witness program|unlocking data leaves the txid (no malleability), gets cheaper, and becomes upgradable|
|P2TR|a tweaked public key that hides a script tree|the common case collapses into one signature; unused branches stay private|

Five principles recur through that history:

1. **Commit, then reveal only what is needed.** Hashes of keys, hashes of scripts, Merkle trees of scripts, and finally keys that commit to trees.
2. **Push cost away from the UTXO set.** From output to input, from the base transaction to the discounted witness.
3. **Upgrade by tightening.** Every improvement used space reserved earlier: `OP_NOP`s, anyone-can-spend templates, witness versions, leaf versions, `OP_SUCCESSx`, the annex.
4. **Multisig migrated from Script into cryptography**, but Script stays in charge of the unhappy paths: timeouts, recovery keys, revocation and accountability.
5. **Bitcoin's "smart contracts" are transaction graphs.** Lightning, Ark and vaults are not code with storage; they are carefully ordered sets of presigned transactions whose outputs carry keys, hashes and timelocks. Coming from Ethereum, that was the biggest shift in thinking for me: the protocol is the graph, and Script is the set of locks on its edges.

The story continues. Cluster mempool and TRUC transactions are making fee bumping for presigned transactions reliable. The covenant debate goes on. A proposal for a script-path-only output type without the Taproot key path (P2MR, BIP360, still a draft) shows how the same commit-and-reveal ideas may be reused to prepare for quantum computers. Whatever comes next, it will be built from the pieces in this article.

### References

**The book**

- Andreas M. Antonopoulos and David A. Harding, _Mastering Bitcoin: Programming the Open Blockchain_, 3rd edition, O'Reilly, 2023. Especially chapters 4 (Keys and Addresses), 6 (Transactions), 7 (Authorization and Authentication), 8 (Digital Signatures), 9 (Transaction Fees), 12 (Mining and Consensus) and 14 (Second-Layer Applications).
- Satoshi Nakamoto, _Bitcoin: A Peer-to-Peer Electronic Cash System_, 2008 (Appendix A of the book).

**Specifications** (all at [github.com/bitcoin/bips](https://github.com/bitcoin/bips))

- Script and transactions: BIP16 (P2SH), BIP65 (CLTV), BIP66 (strict DER), BIP68 (relative lock time), BIP112 (CSV), BIP113 (median time past), BIP125 (opt-in RBF), BIP147 (NULLDUMMY)
- SegWit: BIP141 (consensus), BIP143 (signature digest), BIP144 (serialization), BIP173 (bech32)
- Taproot: BIP340 (Schnorr), BIP341 (Taproot), BIP342 (Tapscript), BIP350 (bech32m)
- Multisig and wallets: BIP32 (HD keys), BIP48 (multisig derivation paths), BIP67 (sorted multisig keys), BIP174 and BIP370 (PSBT), BIP371 (Taproot PSBT fields), BIP327 (MuSig2), BIP328 (MuSig2 derivation), BIP373 (MuSig2 PSBT fields), BIP379 (Miniscript), BIPs 380–387 and 389–390 (descriptors, including `multi_a` and `musig()`), BIP388 (wallet policies)
- Policy and proposals: BIP431 (TRUC), BIP433 (P2A), BIP54 (consensus cleanup), BIP118, BIP119, BIP345, BIP347, BIP348 (covenant proposals), BIP360 (P2MR)

**Other sources**

- Lightning BOLT 3, _Bitcoin Transaction and Script Formats_: [github.com/lightning/bolts/blob/master/03-transactions.md](https://github.com/lightning/bolts/blob/master/03-transactions.md)
- Bitcoin Core release notes for [28.0](https://bitcoincore.org/en/releases/28.0/), [29.0](https://bitcoincore.org/en/releases/29.0/), [29.1](https://bitcoincore.org/en/releases/29.1/), [30.0](https://bitcoincore.org/en/releases/30.0/) and [31.0](https://bitcoincore.org/en/releases/31.0/)
- Arkade documentation on VTXOs: [docs.arkadeos.com](https://docs.arkadeos.com/learn/pillars/vtxos)
- Draft BIP, _FROST Signing Protocol for BIP340 Signatures_: [bitcoin/bips pull request 2070](https://github.com/bitcoin/bips/pull/2070)

### Appendix: opcode and size cheat sheet

**Opcodes used in this article**

|Hex|Opcode|Effect|
|---|---|---|
|`00`|`OP_0` / `OP_FALSE`|push empty vector|
|`01`–`4b`|push _n_|push the next _n_ bytes|
|`51`–`60`|`OP_1`–`OP_16`|push 1 to 16|
|`63` / `64` / `67` / `68`|`IF` / `NOTIF` / `ELSE` / `ENDIF`|conditional execution|
|`69`|`VERIFY`|fail unless the top is true|
|`6a`|`RETURN`|fail immediately (marks data outputs)|
|`73`|`IFDUP`|duplicate the top if it is true|
|`75` / `76` / `7c`|`DROP` / `DUP` / `SWAP`|stack manipulation|
|`82`|`SIZE`|push the length of the top item|
|`87` / `88`|`EQUAL` / `EQUALVERIFY`|byte equality|
|`93` / `94` / `9c`|`ADD` / `SUB` / `NUMEQUAL`|arithmetic|
|`a9`|`HASH160`|RIPEMD160(SHA256(x))|
|`ac` / `ad`|`CHECKSIG` / `CHECKSIGVERIFY`|signature check|
|`ae`|`CHECKMULTISIG`|$t$-of-$k$ check (legacy, SegWit v0)|
|`b1`|`CHECKLOCKTIMEVERIFY`|absolute timelock (was `NOP2`)|
|`b2`|`CHECKSEQUENCEVERIFY`|relative timelock (was `NOP3`)|
|`ba`|`CHECKSIGADD`|counting signature check (Tapscript)|

**Sizes**

|Item|Size|
|---|---|
|ECDSA signature (DER + sighash byte)|71–73 B|
|Schnorr signature|64 B (65 with an explicit sighash byte)|
|Public key|65 B uncompressed, 33 B compressed, 32 B x-only|
|Taproot control block|33 + 32·depth B|
|Outputs|P2PKH 34, P2SH 32, P2WPKH 31, P2WSH 43, P2TR 43, P2A 13 B|
|Inputs (single signature)|P2PKH 148, P2SH-P2WPKH 91, P2WPKH 68, P2TR key path 57.5 vB|
|Transaction overhead|10 B, plus 0.5 vB for the SegWit marker and flag|
|Block|4,000,000 WU; 80-byte header|
