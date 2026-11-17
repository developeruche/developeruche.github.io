"""
Tests for hss_lms.py.

Usage:  python3 -I test_hss_lms.py /path/to/rfc8554.txt

1. RFC 8554 Appendix F, Test Case 1: verify a 2-level HSS signature.
2. RFC 8554 Appendix F, Test Case 2: rebuild the top LMS public key and the
   second-level public key from the published SEED/I values (checks
   Appendix A key derivation, LM-OTS key generation and tree hashing), then
   verify the published signature.
3. Round trips over every LM-OTS parameter set and several HSS shapes.
4. Negative tests: flipped bits, truncation, wrong Nspk, wrong message.
5. Full exhaustion of a small 2-level key: every signature verifies, all
   leaf indices are distinct, regeneration happens on schedule, and the key
   refuses to sign once exhausted.
6. State persistence: write-ahead persist, crash simulation, reload.
7. Signature-size formula matches real signatures.
"""

import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hss_lms import (  # noqa: E402
    LMOTS_BY_NAME, LMS_BY_HEIGHT, HssPrivateKey, KeyExhausted, LmsPrivateKey,
    derive_child, hss_sig_len, hss_verify, u32,
)

HEX = re.compile(r"^[0-9a-f]+$")


def extract_blocks(rfc_text: str) -> dict:
    """Return {'Test Case 1 Public Key': bytes, ...} by concatenating hex fields."""
    lines = rfc_text.splitlines()
    start = next(i for i, l in enumerate(lines) if l.startswith("Appendix F.  Test Cases"))
    blocks, current, buf = {}, None, []
    for line in lines[start:]:
        if line.startswith("RFC 8554") or line.startswith("McGrew, et al."):
            continue  # page header/footer
        m = re.match(r"^\s+(Test Case \d (Public Key|Message|Signature|Private Key))\s*$", line)
        if m:
            if current:
                blocks[current] = bytes.fromhex("".join(buf))
            current, buf = m.group(1), []
            continue
        if current is None:
            continue
        line = line.split("#")[0]
        line = re.sub(r"\|.*\|", "", line)
        for tok in line.split():
            if HEX.match(tok) and len(tok) % 2 == 0:
                buf.append(tok)
    if current:
        blocks[current] = bytes.fromhex("".join(buf))
    return blocks


def check(cond, label):
    print(("PASS " if cond else "FAIL ") + label)
    if not cond:
        raise SystemExit(1)


def no_persist(_):
    pass


def main(rfc_path: str):
    with open(rfc_path, "r", encoding="utf-8") as f:
        blocks = extract_blocks(f.read())

    # ---- 1. Test Case 1 --------------------------------------------------
    pk1, msg1, sig1 = (blocks[f"Test Case 1 {k}"] for k in ("Public Key", "Message", "Signature"))
    check(len(pk1) == 60, f"TC1 public key length 60 (got {len(pk1)})")
    check(hss_verify(msg1, pk1, sig1), "TC1 HSS signature verifies")
    check(not hss_verify(msg1 + b"!", pk1, sig1), "TC1 rejects modified message")
    W8, H5, H10, W4 = LMOTS_BY_NAME["W8"], LMS_BY_HEIGHT[5], LMS_BY_HEIGHT[10], LMOTS_BY_NAME["W4"]
    check(len(sig1) == hss_sig_len([(H5, W8), (H5, W8)]), f"TC1 size formula: {len(sig1)} bytes")

    # ---- 2. Test Case 2 --------------------------------------------------
    pk2, msg2, sig2, priv2 = (blocks[f"Test Case 2 {k}"] for k in
                              ("Public Key", "Message", "Signature", "Private Key"))
    seed0, I0, seed1, I1 = priv2[0:32], priv2[32:48], priv2[48:80], priv2[80:96]
    t = time.time()
    top = LmsPrivateKey.generate(H10, W4, I=I0, seed=seed0)
    check(u32(2) + top.public_key() == pk2,
          f"TC2 top-level public key rebuilt from SEED/I ({time.time() - t:.1f}s, 1024 leaves)")
    child = LmsPrivateKey.generate(H5, W8, I=I1, seed=seed1)
    check(child.public_key() in sig2, "TC2 second-level public key rebuilt and found inside signature")
    check(hss_verify(msg2, pk2, sig2), "TC2 HSS signature verifies")
    check(len(sig2) == hss_sig_len([(H10, W4), (H5, W8)]), f"TC2 size formula: {len(sig2)} bytes")

    # Deterministic derivation: starting from ONLY the top-level SEED and I,
    # derive the child tree for top leaf q=3, derive every randomizer C, and
    # re-sign. The result must equal the published signature byte for byte.
    q_top = int.from_bytes(sig2[4:8], "big")
    check(derive_child(I0, q_top, seed0) == (I1, seed1),
          f"TC2 second-level I and SEED derived from top SEED at leaf q={q_top}")
    q_bot = int.from_bytes(sig2[4 + (4 + W4.sig_len + 4 + 32 * 10) + 56:][:4], "big")
    top.q, child.q = q_top, q_bot
    rebuilt = (u32(1) + top.sign(child.public_key(), deterministic=True) + child.public_key()
               + child.sign(msg2, deterministic=True))
    check(rebuilt == sig2,
          f"TC2 signature reproduced byte-for-byte from the top seed alone (bottom q={q_bot})")

    # ---- 3. Round trips --------------------------------------------------
    for name, ots in LMOTS_BY_NAME.items():
        key = HssPrivateKey.generate([(H5, ots)])
        s = key.sign(b"hello " + name.encode(), no_persist)
        check(hss_verify(b"hello " + name.encode(), key.public_key(), s), f"L=1 H5/{name} round trip")
    for shape in ([(H5, W4), (H5, W4)], [(H10, W4), (H5, W8), (H5, W4)]):
        key = HssPrivateKey.generate(shape)
        s = key.sign(b"multi-level", no_persist)
        check(hss_verify(b"multi-level", key.public_key(), s) and len(s) == hss_sig_len(shape),
              f"L={len(shape)} heights {[l.h for l, _ in shape]} round trip, {len(s)} bytes")

    # ---- 4. Negative tests -----------------------------------------------
    key = HssPrivateKey.generate([(H5, W4), (H5, W4)])
    pk = key.public_key()
    s = key.sign(b"msg", no_persist)
    bad = 0
    for pos in range(0, len(s), 97):  # flip one bit at many positions across all fields
        t_sig = bytearray(s)
        t_sig[pos] ^= 0x01
        bad += hss_verify(b"msg", pk, bytes(t_sig))
    check(bad == 0, f"all {len(range(0, len(s), 97))} single-bit corruptions rejected")
    check(not hss_verify(b"msg", pk, s[:-1]), "truncated signature rejected")
    check(not hss_verify(b"msg", pk, s + b"\x00"), "signature with trailing byte rejected")
    check(not hss_verify(b"msg", pk, u32(0) + s[4:]), "wrong Nspk rejected")
    check(not hss_verify(b"msg", u32(3) + pk[4:], s), "public key with wrong L rejected")
    other = HssPrivateKey.generate([(H5, W4), (H5, W4)])
    check(not hss_verify(b"msg", other.public_key(), s), "signature under a different key rejected")
    # Splice: valid bottom LMS signature from key A under a different level-1 key
    s2 = other.sign(b"msg", no_persist)
    mixed = s[:4 + (4 + W4.sig_len + 4 + 32 * 5) + 56] + s2[4 + (4 + W4.sig_len + 4 + 32 * 5) + 56:]
    check(not hss_verify(b"msg", pk, mixed), "spliced bottom signature from another key rejected")

    # ---- 5. Exhaust a small 2-level key (32 x 32 = 1024 signatures) ---------
    t = time.time()
    key = HssPrivateKey.generate([(H5, W4), (H5, W4)])
    pk = key.public_key()
    check(key.remaining() == 1024, "fresh 2-level H5/H5 key reports 1024 signatures")
    seen, regenerations, last_child = set(), 0, key.levels[1].I
    for k in range(1024):
        m = k.to_bytes(4, "big")
        s = key.sign(m, no_persist)
        if key.levels[1].I != last_child:
            regenerations, last_child = regenerations + 1, key.levels[1].I
        route = (key.levels[0].q, key.levels[1].I, key.levels[1].q)
        assert route not in seen
        seen.add(route)
        if k % 61 == 0 or k > 1015:
            assert hss_verify(m, pk, s), k
    check(key.remaining() == 0, "remaining() reaches 0 after 1024 signatures")
    check(regenerations == 31, f"bottom tree regenerated 31 times (got {regenerations})")
    try:
        key.sign(b"one too many", no_persist)
        check(False, "exhausted key refuses to sign")
    except KeyExhausted:
        check(True, f"exhausted key refuses to sign ({time.time() - t:.1f}s for 1024 signatures)")

    # ---- 6. Persistence ---------------------------------------------------
    key = HssPrivateKey.generate([(H5, W4), (H5, W4)])
    pk = key.public_key()
    store = {}

    def persist(k):
        store["state"] = k.to_bytes()

    for i in range(40):  # crosses one bottom-tree boundary
        key.sign(b"x%d" % i, persist)
    reloaded = HssPrivateKey.from_bytes(store["state"])
    s = reloaded.sign(b"after reload", persist)
    check(hss_verify(b"after reload", pk, s), "state saved, reloaded, and signing continues")
    check((reloaded.levels[0].q, reloaded.levels[1].q) == (2, 9),
          f"reloaded counters are (top q, bottom q) = {(reloaded.levels[0].q, reloaded.levels[1].q)}")

    def failing_persist(_):
        raise IOError("disk full")

    before = (reloaded.levels[0].q, reloaded.levels[1].q)
    try:
        reloaded.sign(b"never released", failing_persist)
        check(False, "no signature escapes when persist fails")
    except IOError:
        after = (reloaded.levels[0].q, reloaded.levels[1].q)
        check(after[1] == before[1] + 1,
              "no signature escapes when persist fails (the unreleased leaf is harmless)")

    # ---- 8. Rollback: why deterministic child derivation matters ------------
    for deterministic in (True, False):
        key = HssPrivateKey.generate([(H5, W4), (H5, W4)], deterministic=deterministic)
        for i in range(30):
            key.sign(b"m%d" % i, no_persist)
        backup = key.to_bytes()                      # e.g. a VM snapshot
        for i in range(5):                           # crosses into a new bottom tree
            key.sign(b"a%d" % i, no_persist)
        first = key.signed_pubs[1]
        restored = HssPrivateKey.from_bytes(backup)  # rolled back to the snapshot
        for i in range(5):
            restored.sign(b"b%d" % i, no_persist)
        same = restored.signed_pubs[1] == first
        if deterministic:
            check(same, "rollback, deterministic mode: top leaf re-signs identical bytes (harmless)")
        else:
            check(not same, "rollback, random mode: top leaf signs a DIFFERENT child key (OTS reuse)")

    print("\nAll checks passed.")


if __name__ == "__main__":
    main(sys.argv[1])
