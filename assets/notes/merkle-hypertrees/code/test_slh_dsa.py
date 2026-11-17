"""
Tests for slh_dsa.py against NIST ACVP SLH-DSA sigGen vectors.

Usage: python3 -I test_slh_dsa.py prompt.json expectedResults.json [--all]

By default runs every 'f' (fast) group fully, and the first test of each 's'
(small) group, for the 'internal' and 'external/pure' interfaces, in both
deterministic and hedged (additionalRandomness) modes. --all runs everything.
"""

import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from slh_dsa import PARAMS, SLHDSA  # noqa: E402


def main(prompt_path, expected_path, run_all=False):
    with open(prompt_path) as f:
        prompt = json.load(f)
    with open(expected_path) as f:
        expected = json.load(f)
    exp = {(g["tgId"], t["tcId"]): t["signature"] for g in expected["testGroups"] for t in g["tests"]}

    passed = failed = 0
    for g in prompt["testGroups"]:
        if g.get("preHash") == "preHash":
            continue  # HashSLH-DSA (pre-hash) variant not implemented here
        ps = g["parameterSet"]
        scheme = SLHDSA(PARAMS[ps])
        tests = g["tests"] if (run_all or ps.endswith("f")) else g["tests"][:1]
        t0 = time.time()
        for t in tests:
            sk = bytes.fromhex(t["sk"])
            msg = bytes.fromhex(t["message"])
            addrnd = None if g["deterministic"] else bytes.fromhex(t["additionalRandomness"])
            if g["signatureInterface"] == "internal":
                sig = scheme.sign_internal(msg, sk, addrnd)
            else:
                sig = scheme.sign(msg, sk, bytes.fromhex(t["context"]), addrnd)
            ok = sig.hex().upper() == exp[(g["tgId"], t["tcId"])].upper()
            n = PARAMS[ps].n
            pk = sk[2 * n:]
            if g["signatureInterface"] == "internal":
                ok = ok and scheme.verify_internal(msg, sig, pk)
                ok = ok and not scheme.verify_internal(msg + b"x", sig, pk)
            else:
                ctx = bytes.fromhex(t["context"])
                wrong_ctx = ctx[:-1] if len(ctx) == 255 else ctx + b"x"
                ok = ok and scheme.verify(msg, sig, pk, ctx) and not scheme.verify(msg, sig, pk, wrong_ctx)
            passed += ok
            failed += not ok
        mode = "det" if g["deterministic"] else "hedged"
        print(f"group {g['tgId']:>2} {ps:<20} {g['signatureInterface']:<8} {mode:<6} "
              f"{len(tests)} test(s) {'ok' if failed == 0 else 'FAILURES'}  ({time.time() - t0:.1f}s)")
    print(f"\n{passed} passed, {failed} failed")
    return failed == 0


if __name__ == "__main__":
    ok = main(sys.argv[1], sys.argv[2], "--all" in sys.argv)
    sys.exit(0 if ok else 1)
