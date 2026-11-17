# Merkle hypertree reference code

Two readable, pure-Python implementations that accompany the article
"Merkle Hypertrees: A Guide for Cryptographers and Implementers".
They are teaching and reference code: correct against official test vectors,
but slow and not hardened (no fault countermeasures, no secure memory, no HSM).

| File | What it is |
| --- | --- |
| `hss_lms.py` | LM-OTS, LMS and HSS (RFC 8554): key generation, stateful signing with regeneration of exhausted lower levels (Algorithm 8), write-ahead persistence hook, state (de)serialization, verification. |
| `test_hss_lms.py` | 32 checks: RFC 8554 Appendix F test cases 1 and 2, round trips for every LM-OTS set, corruption and splicing tests, full exhaustion of a 2-level key, persistence and rollback behaviour. |
| `slh_dsa.py` | SLH-DSA (FIPS 205), all 12 parameter sets, SHA2 and SHAKE, internal and pure external interfaces, deterministic and hedged signing. The hypertree is `tree_node`, `tree_sign`, `tree_root_from_sig`, `ht_sign`, `ht_verify` (FIPS 205 Algorithms 9 to 13). |
| `test_slh_dsa.py` | Runs NIST ACVP SLH-DSA sigGen vectors (signature equality plus verify and reject checks). |

## Running

```sh
# HSS/LMS: needs the RFC text for its test vectors
curl -O https://www.rfc-editor.org/rfc/rfc8554.txt
python3 test_hss_lms.py rfc8554.txt

# SLH-DSA: needs NIST ACVP JSON files
BASE=https://raw.githubusercontent.com/usnistgov/ACVP-Server/master/gen-val/json-files/SLH-DSA-sigGen-FIPS205
curl -o prompt.json $BASE/prompt.json
curl -o expectedResults.json $BASE/expectedResults.json
python3 test_slh_dsa.py prompt.json expectedResults.json          # every f test, first test of each s group
python3 test_slh_dsa.py prompt.json expectedResults.json --all    # everything (about 15 minutes)
```

Only the Python standard library is used.

## Results at time of writing

* HSS/LMS: all 32 checks pass in about 3 seconds. Test Case 2 is reproduced
  byte for byte from its top-level SEED and I alone (see below).
* SLH-DSA: with --all, 336 of 336 ACVP sigGen tests pass: all 12 parameter
  sets, pure and internal interfaces, deterministic and hedged signing
  (pre-hash HashSLH-DSA groups are skipped; not implemented).

## The derivation behind RFC 8554 Test Case 2

The RFC gives only the private seeds, not how the second-level key or the
randomizers C were produced. They follow Appendix A's format with special
index values in the chain-number position:

```
C          = H(I || u32(q) || u16(0xFFFD) || u8(0xFF) || SEED)
child SEED = H(I || u32(q) || u16(0xFFFE) || u8(0xFF) || SEED)
child I    = H(I || u32(q) || u16(0xFFFF) || u8(0xFF) || SEED)[:16]
```

where (I, SEED) belong to the parent tree and q is the parent leaf that
certifies the child. `hss_lms.py` offers this derivation as an option
(`deterministic=True`). Besides reproducing the test vector, it makes a signer
that is restored from an old backup re-create the same child keys, so an upper
leaf re-signs identical bytes rather than a different key. Bottom-leaf reuse
after a rollback is still fatal; state must never roll back.

The default is `deterministic=False`, because NIST SP 800-208 Section 6.1
requires a separate I and SEED from an approved random bit generator for every
LMS instance in an HSS key. Use the deterministic mode only outside that
compliance regime, and only with a reason.

## Porting notes (Rust)

* Model ADRS as `[u8; 32]` with typed setters; make "set type" clear the trailing words.
* Generate leaves in parallel (e.g. rayon); every leaf is independent.
* Keep seeds in `Zeroizing` buffers; persist counters with fsync (or an HSM
  monotonic counter) before a signature leaves the signer.
* Test against the same vectors: RFC 8554 Appendix F and NIST ACVP JSON.
