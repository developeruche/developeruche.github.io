A PSBT carries an unsigned Bitcoin transaction together with everything its signers need to check and sign it, and it collects their signatures until the transaction is complete. This article covers the format byte by byte, what each participant must do and verify, and what version 2 changed. Every example is a test vector from the BIPs, decoded and checked independently.

**Contents**

1. Why PSBT exists
2. Roles
3. The wire format
4. Field reference
5. What each role does and checks
6. PSBT version 2 (BIP370)
7. Taproot and MuSig2 fields
8. Implementer checklist

---

## 1. Why PSBT exists

An unsigned transaction does not contain what a signer needs. Its inputs name coins only by outpoint (a txid and an output index), so:

- **The signer can't see what it is spending.** A SegWit signature commits to the amount being spent, and a Taproot signature to the amounts and scripts of all inputs. Showing the user the fee also needs every input's value. An offline device cannot look any of this up.
- **Scripts hide behind hashes.** A P2SH or P2WSH output contains only the hash of its script, and a Taproot output only a tweaked key. The signer needs the script itself, and for Taproot the internal key, the leaf and its Merkle proof.
- **The signer doesn't know which keys are its own.** A hardware wallet stores a seed, not a list of keys. It needs the BIP32 derivation path of every key it should sign with, and of every change output it should recognise.
- **Signatures arrive one at a time.** In a multisig, each participant signs on their own device, in any order, and something has to carry the partial set until it is complete.

Before PSBT, every wallet solved this with a format of its own. BIP174, first drafted in 2017 and supported by Bitcoin Core since version 0.17, defined a common one. Later BIPs extended it for Taproot, MuSig2 and silent payments without changing its structure.

## 2. Roles

BIP174 divides the work into roles. One program often plays several (a wallet is usually Creator, Updater, Finalizer and Extractor at once), but each role has a defined job and a defined set of checks.

| Role | Job | Bitcoin Core RPC |
|---|---|---|
| Creator | Starts the PSBT: in v0 with the complete unsigned transaction, in v2 with an empty one | `createpsbt`, `walletcreatefundedpsbt` |
| Constructor (v2 only) | Adds inputs and outputs while the PSBT still allows it | |
| Updater | Adds the data signers need: UTXOs, scripts, derivation paths, sighash types | `utxoupdatepsbt`, `walletprocesspsbt` |
| Signer | Verifies that data and adds its signatures | `walletprocesspsbt`, `descriptorprocesspsbt` |
| Combiner | Merges copies of the same PSBT that different parties have worked on | `combinepsbt` |
| Input Finalizer | Turns each input's signatures and scripts into a final scriptSig and witness | `finalizepsbt` |
| Transaction Extractor | Produces the network transaction once every input is final | `finalizepsbt` |

```text
Creator ─► Constructor ─► Updater ─┬─► Signer A ─┐
           (v2 only)               └─► Signer B ─┴─► Combiner ─► Input Finalizer ─► Transaction Extractor
```

Signers can also work in sequence, each passing its output to the next, in which case no Combiner is needed. In Bitcoin Core, `decodepsbt` prints any PSBT and `analyzepsbt` reports which role it needs next.

## 3. The wire format

```text
psbt   := magic global-map input-map* output-map*
magic  := 0x70 0x73 0x62 0x74 0xff            "psbt" followed by 0xff
map    := record* 0x00
record := keylen keytype keydata valuelen value
```

- **Lengths and types are compact-size integers**, the variable-length encoding transactions use: one byte below `0xfd`, otherwise a `0xfd`, `0xfe` or `0xff` prefix followed by 2, 4 or 8 bytes. `keylen` covers `keytype` and `keydata` together, and `keytype` must be minimally encoded.
- **There is one input map per transaction input and one output map per output, in order.** Maps carry no index or count of their own. A v0 parser learns how many to read from the unsigned transaction, a v2 parser from `INPUT_COUNT` and `OUTPUT_COUNT`.
- **A key is `keytype ‖ keydata`, and it must be unique within its map.** A PSBT with a duplicate key is invalid. Key data is what lets one type appear several times: an input has one `PARTIAL_SIG` record per public key, each keyed by that key.
- **`0x00` ends a map**, because no real key has length zero.
- **Unknown types are passed through untouched.** This is the extension mechanism: new BIPs register new types in a registry kept next to BIP174, and old software keeps carrying them. Type `0xFC` is a proprietary namespace for internal use; its key data starts with an identifier string and a subtype.
- **The `0xff` in the magic makes PSBTs and transactions mutually unparseable.** No transaction parser accepts a PSBT, and no PSBT parser accepts a transaction.
- **`PSBT_GLOBAL_VERSION` (`0xFB`) holds the version; if it is absent, the version is 0.** A parser that sees a version it doesn't know must stop, because the PSBT may contain types it cannot safely ignore.
- **PSBT files are binary, with the extension `.psbt`.** As text, PSBTs are base64, which is why they start with `cHNidP8`.

### A fresh PSBT, byte by byte

This is the Creator's output from BIP174's test vectors: a version 0 PSBT for a transaction with two inputs and two outputs, 167 bytes in all.

```text
70 73 62 74 ff                  magic: "psbt" + 0xff
01 00                           key: length 1, type 0x00 (PSBT_GLOBAL_UNSIGNED_TX)
9a                              value: 154 bytes follow
   02000000                     transaction version 2
   02                           2 inputs
   58e87a21…b2abdd75 00000000   input 0 spends 75ddabb2…:0 (txid bytes reversed)
   00 ffffffff                  empty scriptSig, sequence
   838d0427…d07cea1d 01000000   input 1 spends 1dea7cd0…:1
   00 ffffffff                  empty scriptSig, sequence
   02                           2 outputs
   70aaf00800000000             1.49990000 BTC
   16 0014 d85c2b71…1dda124d    to a P2WPKH script
   00e1f50500000000             1.00000000 BTC
   16 0014 00aea9a2…1d87008f    to a P2WPKH script
   00000000                     lock time 0
00                              end of the global map
00 00                           input maps 0 and 1 (empty)
00 00                           output maps 0 and 1 (empty)
```

The Creator knows only the transaction, so all of it sits in the global map, and the four empty maps are slots for later roles. These are some of the records an Updater and a Signer put into them later (key, then value):

```text
input 0:
01 03 | 04 01000000                            SIGHASH_TYPE: SIGHASH_ALL
22 06 029583bf…ab96e07f                        BIP32_DERIVATION, keyed by a 33-byte public key
      | 10 d90c6a4f 00000080 00000080 00000080       master fingerprint d90c6a4f, path m/0'/0'/0'
22 02 029583bf…ab96e07f                        PARTIAL_SIG, keyed by the same public key
      | 47 30440220…3261118c 01                      71 bytes: DER signature + sighash byte
input 1:
01 01 | 20 00c2eb0b00000000 17 a914b7f5…a921e887   WITNESS_UTXO: 2.00000000 BTC, P2SH script
```

## 4. Field reference

These are the fields defined by BIP174 and BIP370. Names drop the `PSBT_GLOBAL_`, `PSBT_IN_` and `PSBT_OUT_` prefixes.

**Global map**

| Type | Name | Key data | Value | Versions |
|---|---|---|---|---|
| `0x00` | `UNSIGNED_TX` | | the transaction, with empty scriptSigs and witnesses, in legacy serialization | v0 only, required |
| `0x01` | `XPUB` | 78-byte extended public key | master fingerprint ‖ derivation path | |
| `0x02` | `TX_VERSION` | | transaction version | v2 only, required |
| `0x03` | `FALLBACK_LOCKTIME` | | lock time to use if no input requires one | v2 only |
| `0x04`, `0x05` | `INPUT_COUNT`, `OUTPUT_COUNT` | | compact-size counts | v2 only, required |
| `0x06` | `TX_MODIFIABLE` | | flags, see Section 6 | v2 only |
| `0xFB` | `VERSION` | | PSBT version | required in v2 |
| `0xFC` | `PROPRIETARY` | identifier ‖ subtype ‖ data | anything | |

**Input map**

| Type | Name | Key data | Value | Versions |
|---|---|---|---|---|
| `0x00` | `NON_WITNESS_UTXO` | | the full previous transaction | |
| `0x01` | `WITNESS_UTXO` | | the spent output: amount ‖ scriptPubKey, for SegWit inputs | |
| `0x02` | `PARTIAL_SIG` | public key | ECDSA signature as pushed: DER ‖ sighash byte | |
| `0x03` | `SIGHASH_TYPE` | | sighash type every signature must use | |
| `0x04` | `REDEEM_SCRIPT` | | P2SH redeem script | |
| `0x05` | `WITNESS_SCRIPT` | | P2WSH witness script | |
| `0x06` | `BIP32_DERIVATION` | public key | master fingerprint ‖ derivation path | |
| `0x07` | `FINAL_SCRIPTSIG` | | complete scriptSig | |
| `0x08` | `FINAL_SCRIPTWITNESS` | | complete witness stack | |
| `0x0a`–`0x0d` | `RIPEMD160`, `SHA256`, `HASH160`, `HASH256` | hash | preimage, for hashlocks | |
| `0x0e` | `PREVIOUS_TXID` | | txid of the coin being spent | v2 only, required |
| `0x0f` | `OUTPUT_INDEX` | | its output index | v2 only, required |
| `0x10` | `SEQUENCE` | | sequence number; `0xffffffff` if absent | v2 only |
| `0x11` | `REQUIRED_TIME_LOCKTIME` | | minimum lock time as a timestamp, ≥ 500,000,000 | v2 only |
| `0x12` | `REQUIRED_HEIGHT_LOCKTIME` | | minimum lock time as a block height, 1 to 499,999,999 | v2 only |

**Output map**

| Type | Name | Key data | Value | Versions |
|---|---|---|---|---|
| `0x00` | `REDEEM_SCRIPT` | | redeem script, so a signer can verify change | |
| `0x01` | `WITNESS_SCRIPT` | | witness script | |
| `0x02` | `BIP32_DERIVATION` | public key | master fingerprint ‖ derivation path | |
| `0x03` | `AMOUNT` | | amount in satoshis | v2 only, required |
| `0x04` | `SCRIPT` | | scriptPubKey | v2 only, required |

The type registry next to BIP174 lists the rest. Besides Taproot and MuSig2 (Section 7), it includes fields for silent payments (BIP375 and BIP376, v2 only), pay-to-contract tweaks (BIP372) and proof-of-reserves commitments (BIP127).

## 5. What each role does and checks

### Creator and Updater

The v0 Creator writes the unsigned transaction, with empty scriptSigs and witnesses, and one empty map per input and output. The Updater adds what it knows. It needs no private keys, so a watch-only wallet or a multisig coordinator can do this job:

- the coin each input spends,
- the redeem and witness scripts behind P2SH and P2WSH hashes,
- the derivation paths of every key that can sign an input or that an output pays to, and the global xpubs they come from,
- optionally, a sighash type and hash preimages.

**Which UTXO field.** `NON_WITNESS_UTXO` (the whole previous transaction) is meant for legacy inputs and `WITNESS_UTXO` (only the spent output) for SegWit inputs, and an input may carry both. The full transaction is also the safer choice for SegWit v0 inputs, because of the 2020 fee attack. A BIP143 signature commits only to its own input's amount, so a malicious coordinator can request two signatures over the same transaction, understating a different input's value each time. Each session shows a sane fee, but combining one valid signature from each produces a transaction whose real fee is far larger. Hashing the full previous transaction proves the amount, which is why many hardware wallets now require it for SegWit v0 inputs. Taproot fixes the problem in the signature itself: a BIP341 signature commits to every input's amount and scriptPubKey, so `WITNESS_UTXO` is enough, provided the signer has it for *every* input.

### Signer

BIP174's signer checklist:

1. If `NON_WITNESS_UTXO` is present, its hash must equal the txid in the input's outpoint.
2. If `WITNESS_UTXO` is present, sign only with a SegWit signature hash, never a legacy one.
3. A `REDEEM_SCRIPT` must hash to the spent scriptPubKey, and a `WITNESS_SCRIPT` must hash to the scriptPubKey or to the redeem script.
4. If `SIGHASH_TYPE` is present, sign with that type if it is acceptable and refuse otherwise. If it is absent, use `SIGHASH_ALL` (or its Taproot equivalent, `SIGHASH_DEFAULT`).
5. Use only the UTXO data in the PSBT, add data but never remove any, and store each signature as a `PARTIAL_SIG` keyed by its public key.

What to sign follows from the UTXO fields. With a `WITNESS_UTXO`, the script is the redeem script if there is one (P2SH-wrapped SegWit) and the scriptPubKey otherwise. P2WPKH then signs a BIP143 hash with the matching P2PKH script code, and P2WSH signs a BIP143 hash over the witness script. With only a `NON_WITNESS_UTXO`, the signer computes a legacy signature hash over the redeem script or the spent scriptPubKey. With neither, it cannot sign.

A good signer also shows the user what is being signed: destinations, amounts and fee. It can compute the fee because the PSBT carries every input's value.

**Change detection.** To keep its own change out of that display, a signer checks each output's `BIP32_DERIVATION`. If the fingerprint is its own and deriving the path gives the output's key, the output is change. For multisig, it reconstructs the policy of the inputs it signs (which keys, in what order, how many are required), uses the derivation paths and global xpubs to find each cosigner's xpub, and treats as change only outputs with exactly the same policy. A PSBT comes from an untrusted host, so devices usually make the user register the wallet's descriptor or policy (BIP388) once, then check every PSBT against it.

### Combiner

The Combiner takes several PSBTs for the same transaction and outputs one that contains every record from all of them, without duplicates. It needs no script knowledge. In v0, "the same transaction" means the same `UNSIGNED_TX`; Section 6 gives the v2 equivalent. If two PSBTs carry the same key with different values, the Combiner may keep either value or refuse to combine. BIP174 allows an arbitrary choice because an invalid value can only produce an invalid signature or transaction, and if both values are valid the choice doesn't matter. When participants add only distinct records, the order of combining doesn't matter: `Combine(fA(p), fB(p)) = fA(fB(p)) = fB(fA(p))`.

### Input Finalizer

For each input that has enough data to satisfy its script, the Finalizer builds the complete scriptSig and witness and stores them as `FINAL_SCRIPTSIG` and `FINAL_SCRIPTWITNESS`, leaving either one unset if it would be empty. It then deletes every other record in that input's map except the UTXO fields and fields it doesn't understand. It must refuse to finalize an input whose signatures don't match a given `SIGHASH_TYPE`. This is the role that has to understand scripts: signature order, the dummy element that `OP_CHECKMULTISIG` consumes, and the redeem-script push that wraps P2SH-SegWit.

### Transaction Extractor

If every input is final, the Extractor copies the final scriptSigs and witnesses into the transaction and serializes it; otherwise it leaves the PSBT alone. It may also validate the result, which is why the Finalizer keeps the UTXOs.

### One transaction through every role

BIP174's test vectors take the transaction from Section 3 through every role. Input 0 spends a 0.5 BTC P2SH 2-of-2 multisig output and input 1 a 2 BTC P2SH-P2WSH 2-of-2. Signer A holds one key of each multisig and Signer B the other, and they sign copies of the same PSBT in parallel:

| Step | Input 0 (P2SH 2-of-2) | Input 1 (P2SH-P2WSH 2-of-2) | Outputs | Size |
|---|---|---|---|---|
| Creator | empty | empty | empty | 167 B |
| Updater | `NON_WITNESS_UTXO`, `REDEEM_SCRIPT`, 2 × `BIP32_DERIVATION` | `WITNESS_UTXO`, `REDEEM_SCRIPT`, `WITNESS_SCRIPT`, 2 × `BIP32_DERIVATION` | `BIP32_DERIVATION` | 889 B |
| Updater | + `SIGHASH_TYPE` | + `SIGHASH_TYPE` | | 903 B |
| Signer A, Signer B | + one `PARTIAL_SIG` each | + one `PARTIAL_SIG` each | | 1,117 B, 1,118 B |
| Combiner | 2 × `PARTIAL_SIG` | 2 × `PARTIAL_SIG` | | 1,332 B |
| Input Finalizer | `NON_WITNESS_UTXO`, `FINAL_SCRIPTSIG` | `WITNESS_UTXO`, `FINAL_SCRIPTSIG`, `FINAL_SCRIPTWITNESS` | unchanged | 976 B |
| Transaction Extractor | | | | 628-byte transaction (463 vB) |

Finalizing shows how the two input types differ. Input 0's scriptSig becomes `OP_0 <sig> <sig> <redeem script>`. Input 1's scriptSig is only the 34-byte push of its redeem script (`0020` followed by a script hash), and its signatures move to the witness: `[<empty>, <sig>, <sig>, <witness script>]`. Before signing, either signer can compute the fee: 2.5 BTC in, 2.4999 BTC out, 10,000 sats. The vector predates the fee attack; today, many hardware wallets would refuse to sign input 1 without its full previous transaction.

## 6. PSBT version 2 (BIP370)

**The problem.** In v0 the transaction is fixed at creation. `UNSIGNED_TX` is the PSBT's identity, so adding an input or output means building a new transaction and therefore a new PSBT; Bitcoin Core's `joinpsbts` merges PSBTs exactly this way. Nothing in v0 records which changes existing signatures would survive. Protocols that build a transaction together, such as coinjoins, payjoins, dual-funded Lightning channels and swaps, need to add inputs and outputs to a PSBT that others have already seen, and sometimes already signed with `ANYONECANPAY`.

**The change.** v2 removes `UNSIGNED_TX` and stores each part of the transaction in the map it belongs to. The version, fallback lock time and counts go in the global map; the outpoint, sequence and lock-time requirements in each input map; the amount and script in each output map. As a side effect, everything about an input or output now lives in one place. `PSBT_GLOBAL_VERSION` must be 2, v0 must not contain v2 fields, and v2 must not contain `UNSIGNED_TX`, so neither version can be mistaken for the other. (There is no version 1: v0 had been informally called "v1", so the BIP skipped the number.)

The smallest valid v2 PSBT in BIP370's test vectors, 145 bytes:

```text
70 73 62 74 ff                  magic
01 02 | 04 02000000             TX_VERSION = 2
01 04 | 01 01                   INPUT_COUNT = 1
01 05 | 01 02                   OUTPUT_COUNT = 2
01 fb | 04 02000000             VERSION = 2
00
01 0e | 20 0b0ad921…84815fc8    PREVIOUS_TXID
01 0f | 04 00000000             OUTPUT_INDEX = 0
00                              (no SEQUENCE, so 0xffffffff)
01 03 | 08 0008af2f00000000     AMOUNT = 8.00000000 BTC
01 04 | 16 0014c430…9926272c    SCRIPT (P2WPKH)
00
01 03 | 08 8bbdeb0b00000000     AMOUNT = 1.99998859 BTC
01 04 | 16 00144dd1…474f8513    SCRIPT (P2WPKH)
00
```

### The Constructor and `TX_MODIFIABLE`

A v2 Creator starts with zero inputs and outputs, sets `PSBT_GLOBAL_VERSION` to 2 and the transaction version, and should set the fallback lock time. If others will add to the transaction, it must also set `TX_MODIFIABLE` and a transaction version of at least 2, so that features such as `OP_CHECKSEQUENCEVERIFY` work for every input without negotiation. Constructors then add inputs (each with `PREVIOUS_TXID`, `OUTPUT_INDEX` and any lock-time requirement) and outputs (with `AMOUNT` and `SCRIPT`), and update the counts.

`TX_MODIFIABLE` holds three flags:

| Bit | Flag | Meaning |
|---|---|---|
| 0 | Inputs Modifiable | inputs may be added or removed |
| 1 | Outputs Modifiable | outputs may be added or removed |
| 2 | Has SIGHASH_SINGLE | a signature pairs an input with the output at the same index |

The flags track what existing signatures still allow. After signing, a Signer must clear bit 0 if its signature doesn't use `ANYONECANPAY`, clear bit 1 unless it used `SIGHASH_NONE`, and set bit 2 if it used `SIGHASH_SINGLE`. A Constructor must check the flags before adding anything. It must refuse an input whose lock-time type is incompatible with the existing inputs, or one that would change the lock time once signatures exist. When bit 2 is set, it must keep each `SIGHASH_SINGLE` input at the same index as its output, so anything inserted before such an input needs a matching output inserted before its output. A Constructor closes the transaction by clearing the flags or removing the field.

### Lock time

In v2, inputs state requirements instead of the transaction carrying a single lock time. `REQUIRED_HEIGHT_LOCKTIME` and `REQUIRED_TIME_LOCKTIME` give the minimum block height or timestamp an input needs; an input that works with either can set both. The transaction's lock time is then derived:

```python
def determine_locktime(fallback, inputs):
    """inputs: one (required_time, required_height) pair per input, None where absent."""
    constrained = [i for i in inputs if i != (None, None)]
    if not constrained:
        return fallback or 0
    if all(h is not None for t, h in constrained):    # height wins a tie
        return max(h for t, h in constrained)
    if all(t is not None for t, h in constrained):
        return max(t for t, h in constrained)
    return None                                        # no common type: invalid
```

This function gives the expected result for all ten lock-time test vectors in BIP370. Heights are preferred when both types are possible because every signer must agree on one value: their signatures commit to the lock time.

### Identity, finalizing and compatibility

- **Identity.** A v2 PSBT is identified by the txid of the transaction its fields describe, with every sequence number set to 0 (Updaters and Combiners may change sequences) and the lock time computed as above. It plays the role `UNSIGNED_TX` played in v0.
- **Finalizing.** When the Input Finalizer clears an input, it must keep `PREVIOUS_TXID`, `OUTPUT_INDEX`, `SEQUENCE` and the lock-time fields, because the Extractor builds the transaction from them.
- **Compatibility.** v0 and v2 share the framing, so a v0 parser only needs the new fields to read v2. Converting is mechanical in both directions: build the unsigned transaction from v2's fields, or split v0's unsigned transaction into them.

**Adoption.** Ledger's Bitcoin app has used v2 since version 2.0.0 (2021), because a device can then read individual fields without parsing the whole transaction. Core Lightning uses v2 internally. Sending silent payments with PSBTs (BIP375) requires v2, because a silent-payment output's script cannot be computed until the inputs are known. Bitcoin Core merged v2 support in 2026. In version 32.0, which is in release candidates as of October 2026, `createpsbt`, `walletcreatefundedpsbt`, `converttopsbt` and `psbtbumpfee` produce v2 by default, and a new `psbt_version` argument asks for v0.

## 7. Taproot and MuSig2 fields

BIP371 adds the fields that Taproot signing needs. All of them are allowed in both v0 and v2.

| Name | Type | Key data | Value |
|---|---|---|---|
| `IN_TAP_KEY_SIG` | input `0x13` | | key-path signature, 64 or 65 bytes |
| `IN_TAP_SCRIPT_SIG` | input `0x14` | x-only key ‖ leaf hash | script-path signature |
| `IN_TAP_LEAF_SCRIPT` | input `0x15` | control block | script ‖ leaf version |
| `IN_TAP_BIP32_DERIVATION`, `OUT_TAP_BIP32_DERIVATION` | input `0x16`, output `0x07` | x-only key | hashes of the leaves the key appears in ‖ fingerprint ‖ path |
| `IN_TAP_INTERNAL_KEY`, `OUT_TAP_INTERNAL_KEY` | input `0x17`, output `0x05` | | x-only internal key |
| `IN_TAP_MERKLE_ROOT` | input `0x18` | | Merkle root of the script tree |
| `OUT_TAP_TREE` | output `0x06` | | every leaf as depth ‖ leaf version ‖ script |

What changes for each role:

- **UTXOs.** `WITNESS_UTXO` is enough for Taproot inputs, but to compute any Taproot signature hash (other than with `ANYONECANPAY`) the signer needs the UTXO of every input in the transaction, Taproot or not.
- **Key path.** The signer tweaks its key with the internal key and, if the output has a script tree, the Merkle root. It should check that the two reproduce the output key before signing.
- **Script path.** A Tapscript signature commits to its leaf, so script-path signatures are keyed by key and leaf hash, and derivation records list the leaves each key appears in. The Finalizer builds the witness from the signatures, the leaf script and its control block.
- **Outputs.** An internal key, tree and derivation paths on an output let a signer verify Taproot change the same way as before.

MuSig2 (BIP373) adds `MUSIG2_PARTICIPANT_PUBKEYS` (input `0x1a`, output `0x08`, listing an aggregate key's participants), `MUSIG2_PUB_NONCE` (input `0x1b`) and `MUSIG2_PARTIAL_SIG` (input `0x1c`). The last two are keyed by participant key ‖ aggregate key, plus a leaf hash for script-path spends. Signing takes two passes over the PSBT: every signer first adds a 66-byte public nonce, then, once all nonces are present, a 32-byte partial signature. Whoever holds all the partial signatures aggregates them into an ordinary `TAP_KEY_SIG` or `TAP_SCRIPT_SIG`. Secret nonces never enter the PSBT; they stay in the signer and must never be reused.

## 8. Implementer checklist

- **Treat every field as an untrusted claim and recompute it**: the txid of a `NON_WITNESS_UTXO`, the hashes of redeem and witness scripts, the Taproot output key from the internal key and Merkle root, every control block.
- **Require the full previous transaction for SegWit v0 inputs**, and the UTXOs of all inputs whenever one input is Taproot.
- **Show destinations, amounts and fee**, and treat an output as change only if you can derive its key and it matches the registered wallet policy.
- **Refuse unexpected sighash types**, and make anything other than `ALL` or `DEFAULT` visible to the user.
- **Pass unknown and proprietary records through unchanged**, and stop on an unknown `PSBT_GLOBAL_VERSION`.
- **Support v2**, since Bitcoin Core switches to it by default in version 32.0.
- **Strip private data before a PSBT leaves your wallet.** Xpubs, derivation paths and full previous transactions reveal your wallet's structure to coinjoin and payjoin counterparties.

---

### References

- [BIP174: Partially Signed Bitcoin Transaction Format](https://github.com/bitcoin/bips/blob/master/bip-0174.mediawiki) and the [PSBT type registry](https://github.com/bitcoin/bips/blob/master/bip-0174/type-registry.mediawiki)
- [BIP370: PSBT Version 2](https://github.com/bitcoin/bips/blob/master/bip-0370.mediawiki)
- [BIP371: Taproot Fields for PSBT](https://github.com/bitcoin/bips/blob/master/bip-0371.mediawiki), [BIP373: MuSig2 PSBT Fields](https://github.com/bitcoin/bips/blob/master/bip-0373.mediawiki)
- [BIP375: Sending Silent Payments with PSBTs](https://github.com/bitcoin/bips/blob/master/bip-0375.mediawiki), [BIP376: Spending Silent Payment outputs with PSBTs](https://github.com/bitcoin/bips/blob/master/bip-0376.mediawiki)
- [BIP143](https://github.com/bitcoin/bips/blob/master/bip-0143.mediawiki) and [BIP341](https://github.com/bitcoin/bips/blob/master/bip-0341.mediawiki) (signature hashes), [BIP388: Wallet Policies](https://github.com/bitcoin/bips/blob/master/bip-0388.mediawiki)
- Bitcoin Optech, [PSBT topic page](https://bitcoinops.org/en/topics/psbt/) and [newsletter of 8 May 2026](https://bitcoinops.org/en/newsletters/2026/05/08/) (Bitcoin Core #21283, PSBTv2)
- [Bitcoin Core 32.0 release notes draft](https://github.com/bitcoin-core/bitcoin-devwiki/wiki/32.0-Release-Notes-Draft)
- bitcoindev, ["Who uses or wants to use PSBTv2 (BIP370)"](https://groups.google.com/g/bitcoindev/c/OPx9qvmr5Nc/m/yKW8NfnNBQAJ), January 2025
