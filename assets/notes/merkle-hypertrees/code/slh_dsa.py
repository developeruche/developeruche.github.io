"""
SLH-DSA (FIPS 205) -- a readable reference implementation, written to show
the hypertree clearly.

The hypertree lives in four functions, which correspond one-to-one to the
generic pseudocode in the accompanying article:

    article name          FIPS 205 name     Algorithm
    -------------------   ---------------   ---------
    tree_node             xmss_node          9
    tree_sign             xmss_sign         10
    tree_root_from_sig    xmss_pkFromSig    11
    ht_sign / ht_verify   ht_sign/verify    12 / 13

Everything else (WOTS+, FORS, the hash instantiations) is support code.

Scope: SHAKE and SHA2 instantiations, all twelve FIPS 205 parameter sets,
internal and external ("pure") interfaces, deterministic and hedged signing.
Checked against NIST ACVP SLH-DSA sigGen vectors (see test_slh_dsa.py).
Teaching code: pure Python, slow, not hardened against faults or side channels.
"""

from __future__ import annotations

import hashlib
import hmac
import os
from dataclasses import dataclass
from math import ceil, floor, log2

# --------------------------------------------------------------------------
# Parameter sets (FIPS 205, Table 2)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class Params:
    name: str
    n: int
    h: int
    d: int
    hp: int    # h' = height of each XMSS tree in the hypertree
    a: int     # FORS tree height
    k: int     # number of FORS trees
    lg_w: int
    m: int     # message-digest bytes
    sha2: bool

    @property
    def w(self) -> int:
        return 1 << self.lg_w

    @property
    def len1(self) -> int:
        return ceil(8 * self.n / self.lg_w)

    @property
    def len2(self) -> int:
        return floor(log2(self.len1 * (self.w - 1)) / self.lg_w) + 1

    @property
    def len(self) -> int:
        return self.len1 + self.len2

    @property
    def sig_bytes(self) -> int:
        return (1 + self.k * (1 + self.a) + self.h + self.d * self.len) * self.n


_TABLE2 = [
    # name-suffix  n   h   d  h'  a   k  lg_w  m
    ("128s", 16, 63, 7, 9, 12, 14, 4, 30),
    ("128f", 16, 66, 22, 3, 6, 33, 4, 34),
    ("192s", 24, 63, 7, 9, 14, 17, 4, 39),
    ("192f", 24, 66, 22, 3, 8, 33, 4, 42),
    ("256s", 32, 64, 8, 8, 14, 22, 4, 47),
    ("256f", 32, 68, 17, 4, 9, 35, 4, 49),
]
PARAMS = {}
for fam, is_sha2 in (("SHA2", True), ("SHAKE", False)):
    for suf, n, h, d, hp, a, k, lg_w, m in _TABLE2:
        name = f"SLH-DSA-{fam}-{suf}"
        PARAMS[name] = Params(name, n, h, d, hp, a, k, lg_w, m, is_sha2)


# --------------------------------------------------------------------------
# ADRS: the 32-byte address that makes every hash call unique (FIPS 205 4.2)
# --------------------------------------------------------------------------

WOTS_HASH, WOTS_PK, TREE, FORS_TREE, FORS_ROOTS, WOTS_PRF, FORS_PRF = range(7)


class ADRS:
    __slots__ = ("b",)

    def __init__(self, b: bytes = bytes(32)):
        self.b = bytearray(b)

    def copy(self) -> "ADRS":
        return ADRS(bytes(self.b))

    def _set(self, lo: int, hi: int, v: int) -> None:
        self.b[lo:hi] = v.to_bytes(hi - lo, "big")

    def set_layer(self, v): self._set(0, 4, v)
    def set_tree(self, v): self._set(4, 16, v)          # 12 bytes
    def set_type_and_clear(self, v):
        self._set(16, 20, v)
        self.b[20:32] = bytes(12)
    def set_key_pair(self, v): self._set(20, 24, v)
    def set_chain(self, v): self._set(24, 28, v)
    def set_tree_height(self, v): self._set(24, 28, v)
    def set_hash(self, v): self._set(28, 32, v)
    def set_tree_index(self, v): self._set(28, 32, v)
    def get_key_pair(self) -> int: return int.from_bytes(self.b[20:24], "big")
    def get_tree_index(self) -> int: return int.from_bytes(self.b[28:32], "big")

    def compressed(self) -> bytes:
        """ADRSc (22 bytes) used by the SHA2 instantiation (FIPS 205 11.2)."""
        b = self.b
        return bytes([b[3]]) + bytes(b[8:16]) + bytes([b[19]]) + bytes(b[20:32])


# --------------------------------------------------------------------------
# Hash instantiations (FIPS 205 Section 11)
# --------------------------------------------------------------------------


def _mgf1(hash_name: str, seed: bytes, length: int) -> bytes:
    out, c = b"", 0
    while len(out) < length:
        out += hashlib.new(hash_name, seed + c.to_bytes(4, "big")).digest()
        c += 1
    return out[:length]


class Hashes:
    def __init__(self, p: Params):
        self.p = p

    # -- tweakable hash family: F (one block), H (two blocks), T_l (l blocks)
    def F(self, pk_seed: bytes, adrs: ADRS, m1: bytes) -> bytes:
        p = self.p
        if not p.sha2:
            return hashlib.shake_256(pk_seed + bytes(adrs.b) + m1).digest(p.n)
        return hashlib.sha256(pk_seed + bytes(64 - p.n) + adrs.compressed() + m1).digest()[:p.n]

    def H(self, pk_seed: bytes, adrs: ADRS, m2: bytes) -> bytes:
        return self.T(pk_seed, adrs, m2)

    def T(self, pk_seed: bytes, adrs: ADRS, ml: bytes) -> bytes:
        p = self.p
        if not p.sha2:
            return hashlib.shake_256(pk_seed + bytes(adrs.b) + ml).digest(p.n)
        if p.n == 16:
            return hashlib.sha256(pk_seed + bytes(64 - p.n) + adrs.compressed() + ml).digest()[:p.n]
        return hashlib.sha512(pk_seed + bytes(128 - p.n) + adrs.compressed() + ml).digest()[:p.n]

    def PRF(self, pk_seed: bytes, sk_seed: bytes, adrs: ADRS) -> bytes:
        p = self.p
        if not p.sha2:
            return hashlib.shake_256(pk_seed + bytes(adrs.b) + sk_seed).digest(p.n)
        return hashlib.sha256(pk_seed + bytes(64 - p.n) + adrs.compressed() + sk_seed).digest()[:p.n]

    def PRF_msg(self, sk_prf: bytes, opt_rand: bytes, msg: bytes) -> bytes:
        p = self.p
        if not p.sha2:
            return hashlib.shake_256(sk_prf + opt_rand + msg).digest(p.n)
        alg = "sha256" if p.n == 16 else "sha512"
        return hmac.new(sk_prf, opt_rand + msg, alg).digest()[:p.n]

    def H_msg(self, R: bytes, pk_seed: bytes, pk_root: bytes, msg: bytes) -> bytes:
        p = self.p
        if not p.sha2:
            return hashlib.shake_256(R + pk_seed + pk_root + msg).digest(p.m)
        alg = "sha256" if p.n == 16 else "sha512"
        inner = hashlib.new(alg, R + pk_seed + pk_root + msg).digest()
        return _mgf1(alg, R + pk_seed + inner, p.m)


# --------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------


def base_2b(X: bytes, b: int, out_len: int):
    """Algorithm 4: read out_len b-bit digits from X, most significant first."""
    i, bits, total, out = 0, 0, 0, []
    for _ in range(out_len):
        while bits < b:
            total = (total << 8) + X[i]
            i += 1
            bits += 8
        bits -= b
        out.append((total >> bits) % (1 << b))
    return out


class SLHDSA:
    def __init__(self, params: Params):
        self.p = params
        self.hs = Hashes(params)

    # ---------------------------------------------------------------- WOTS+
    def chain(self, X, i, s, pk_seed, adrs):
        tmp = X
        for j in range(i, i + s):
            adrs.set_hash(j)
            tmp = self.hs.F(pk_seed, adrs, tmp)
        return tmp

    def _wots_digits(self, M: bytes):
        p = self.p
        msg = base_2b(M, p.lg_w, p.len1)
        csum = sum(p.w - 1 - v for v in msg)
        csum <<= (8 - ((p.len2 * p.lg_w) % 8)) % 8
        msg += base_2b(csum.to_bytes(ceil(p.len2 * p.lg_w / 8), "big"), p.lg_w, p.len2)
        return msg

    def _wots_sk_adrs(self, adrs):
        sk_adrs = adrs.copy()
        sk_adrs.set_type_and_clear(WOTS_PRF)
        sk_adrs.set_key_pair(adrs.get_key_pair())
        return sk_adrs

    def _wots_pk_compress(self, tmp, pk_seed, adrs):
        pk_adrs = adrs.copy()
        pk_adrs.set_type_and_clear(WOTS_PK)
        pk_adrs.set_key_pair(adrs.get_key_pair())
        return self.hs.T(pk_seed, pk_adrs, b"".join(tmp))

    def wots_pk_gen(self, sk_seed, pk_seed, adrs):                    # Algorithm 6
        sk_adrs, tmp = self._wots_sk_adrs(adrs), []
        for i in range(self.p.len):
            sk_adrs.set_chain(i)
            sk = self.hs.PRF(pk_seed, sk_seed, sk_adrs)
            adrs.set_chain(i)
            tmp.append(self.chain(sk, 0, self.p.w - 1, pk_seed, adrs))
        return self._wots_pk_compress(tmp, pk_seed, adrs)

    def wots_sign(self, M, sk_seed, pk_seed, adrs):                    # Algorithm 7
        sk_adrs, sig = self._wots_sk_adrs(adrs), []
        for i, digit in enumerate(self._wots_digits(M)):
            sk_adrs.set_chain(i)
            sk = self.hs.PRF(pk_seed, sk_seed, sk_adrs)
            adrs.set_chain(i)
            sig.append(self.chain(sk, 0, digit, pk_seed, adrs))
        return b"".join(sig)

    def wots_pk_from_sig(self, sig, M, pk_seed, adrs):                 # Algorithm 8
        n, tmp = self.p.n, []
        for i, digit in enumerate(self._wots_digits(M)):
            adrs.set_chain(i)
            tmp.append(self.chain(sig[i * n:(i + 1) * n], digit, self.p.w - 1 - digit, pk_seed, adrs))
        return self._wots_pk_compress(tmp, pk_seed, adrs)

    # ------------------------------------------------- one XMSS tree (a layer)
    def tree_node(self, sk_seed, i, z, pk_seed, adrs):                 # xmss_node, Alg. 9
        if z == 0:
            adrs.set_type_and_clear(WOTS_HASH)
            adrs.set_key_pair(i)
            return self.wots_pk_gen(sk_seed, pk_seed, adrs)
        lnode = self.tree_node(sk_seed, 2 * i, z - 1, pk_seed, adrs)
        rnode = self.tree_node(sk_seed, 2 * i + 1, z - 1, pk_seed, adrs)
        adrs.set_type_and_clear(TREE)
        adrs.set_tree_height(z)
        adrs.set_tree_index(i)
        return self.hs.H(pk_seed, adrs, lnode + rnode)

    def tree_sign(self, M, sk_seed, idx, pk_seed, adrs):               # xmss_sign, Alg. 10
        auth = [self.tree_node(sk_seed, (idx >> j) ^ 1, j, pk_seed, adrs) for j in range(self.p.hp)]
        adrs.set_type_and_clear(WOTS_HASH)
        adrs.set_key_pair(idx)
        return self.wots_sign(M, sk_seed, pk_seed, adrs) + b"".join(auth)

    def tree_root_from_sig(self, idx, sig_xmss, M, pk_seed, adrs):     # xmss_pkFromSig, Alg. 11
        n, L = self.p.n, self.p.len
        adrs.set_type_and_clear(WOTS_HASH)
        adrs.set_key_pair(idx)
        node = self.wots_pk_from_sig(sig_xmss[:L * n], M, pk_seed, adrs)
        auth = sig_xmss[L * n:]
        adrs.set_type_and_clear(TREE)
        adrs.set_tree_index(idx)
        for k in range(self.p.hp):
            adrs.set_tree_height(k + 1)
            a_k = auth[k * n:(k + 1) * n]
            if (idx >> k) % 2 == 0:
                adrs.set_tree_index(adrs.get_tree_index() // 2)
                node = self.hs.H(pk_seed, adrs, node + a_k)
            else:
                adrs.set_tree_index((adrs.get_tree_index() - 1) // 2)
                node = self.hs.H(pk_seed, adrs, a_k + node)
        return node

    # ------------------------------------------------------------ hypertree
    def ht_sign(self, M, sk_seed, pk_seed, idx_tree, idx_leaf):        # Algorithm 12
        p = self.p
        adrs = ADRS()
        adrs.set_tree(idx_tree)
        sig_tmp = self.tree_sign(M, sk_seed, idx_leaf, pk_seed, adrs)
        sig_ht = sig_tmp
        root = self.tree_root_from_sig(idx_leaf, sig_tmp, M, pk_seed, adrs)
        for j in range(1, p.d):
            idx_leaf = idx_tree % (1 << p.hp)   # h' least significant bits
            idx_tree = idx_tree >> p.hp         # remove them
            adrs.set_layer(j)
            adrs.set_tree(idx_tree)
            sig_tmp = self.tree_sign(root, sk_seed, idx_leaf, pk_seed, adrs)
            sig_ht += sig_tmp
            if j < p.d - 1:
                root = self.tree_root_from_sig(idx_leaf, sig_tmp, root, pk_seed, adrs)
        return sig_ht

    def ht_verify(self, M, sig_ht, pk_seed, idx_tree, idx_leaf, pk_root):  # Algorithm 13
        p = self.p
        step = (p.hp + p.len) * p.n
        adrs = ADRS()
        adrs.set_tree(idx_tree)
        node = self.tree_root_from_sig(idx_leaf, sig_ht[:step], M, pk_seed, adrs)
        for j in range(1, p.d):
            idx_leaf = idx_tree % (1 << p.hp)
            idx_tree = idx_tree >> p.hp
            adrs.set_layer(j)
            adrs.set_tree(idx_tree)
            node = self.tree_root_from_sig(idx_leaf, sig_ht[j * step:(j + 1) * step], node, pk_seed, adrs)
        return node == pk_root

    # ----------------------------------------------------------------- FORS
    def fors_sk_gen(self, sk_seed, pk_seed, adrs, idx):
        sk_adrs = adrs.copy()
        sk_adrs.set_type_and_clear(FORS_PRF)
        sk_adrs.set_key_pair(adrs.get_key_pair())
        sk_adrs.set_tree_index(idx)
        return self.hs.PRF(pk_seed, sk_seed, sk_adrs)

    def fors_node(self, sk_seed, i, z, pk_seed, adrs):
        if z == 0:
            sk = self.fors_sk_gen(sk_seed, pk_seed, adrs, i)
            adrs.set_tree_height(0)
            adrs.set_tree_index(i)
            return self.hs.F(pk_seed, adrs, sk)
        lnode = self.fors_node(sk_seed, 2 * i, z - 1, pk_seed, adrs)
        rnode = self.fors_node(sk_seed, 2 * i + 1, z - 1, pk_seed, adrs)
        adrs.set_tree_height(z)
        adrs.set_tree_index(i)
        return self.hs.H(pk_seed, adrs, lnode + rnode)

    def fors_sign(self, md, sk_seed, pk_seed, adrs):
        p, out = self.p, b""
        for i, idx in enumerate(base_2b(md, p.a, p.k)):
            out += self.fors_sk_gen(sk_seed, pk_seed, adrs, (i << p.a) + idx)
            for j in range(p.a):
                s = (idx >> j) ^ 1
                out += self.fors_node(sk_seed, (i << (p.a - j)) + s, j, pk_seed, adrs)
        return out

    def fors_pk_from_sig(self, sig_fors, md, pk_seed, adrs):
        p, n, roots = self.p, self.p.n, []
        for i, idx in enumerate(base_2b(md, p.a, p.k)):
            base = i * (p.a + 1) * n
            sk = sig_fors[base:base + n]
            adrs.set_tree_height(0)
            adrs.set_tree_index((i << p.a) + idx)
            node = self.hs.F(pk_seed, adrs, sk)
            for j in range(p.a):
                a_j = sig_fors[base + (j + 1) * n:base + (j + 2) * n]
                adrs.set_tree_height(j + 1)
                if (idx >> j) % 2 == 0:
                    adrs.set_tree_index(adrs.get_tree_index() // 2)
                    node = self.hs.H(pk_seed, adrs, node + a_j)
                else:
                    adrs.set_tree_index((adrs.get_tree_index() - 1) // 2)
                    node = self.hs.H(pk_seed, adrs, a_j + node)
            roots.append(node)
        pk_adrs = adrs.copy()
        pk_adrs.set_type_and_clear(FORS_ROOTS)
        pk_adrs.set_key_pair(adrs.get_key_pair())
        return self.hs.T(pk_seed, pk_adrs, b"".join(roots))

    # ------------------------------------------------------- top-level API
    def keygen_internal(self, sk_seed, sk_prf, pk_seed):               # Algorithm 18
        adrs = ADRS()
        adrs.set_layer(self.p.d - 1)
        pk_root = self.tree_node(sk_seed, 0, self.p.hp, pk_seed, adrs)  # only the top tree
        return sk_seed + sk_prf + pk_seed + pk_root, pk_seed + pk_root

    def keygen(self):
        n = self.p.n
        return self.keygen_internal(os.urandom(n), os.urandom(n), os.urandom(n))

    def _split_digest(self, digest):
        p = self.p
        ka = ceil(p.k * p.a / 8)
        t = ceil((p.h - p.hp) / 8)
        l = ceil(p.hp / 8)
        md = digest[:ka]
        idx_tree = int.from_bytes(digest[ka:ka + t], "big") % (1 << (p.h - p.hp))
        idx_leaf = int.from_bytes(digest[ka + t:ka + t + l], "big") % (1 << p.hp)
        return md, idx_tree, idx_leaf

    def sign_internal(self, M, sk, addrnd=None):                       # Algorithm 19
        n = self.p.n
        sk_seed, sk_prf, pk_seed, pk_root = (sk[i * n:(i + 1) * n] for i in range(4))
        opt_rand = addrnd if addrnd is not None else pk_seed           # None = deterministic
        R = self.hs.PRF_msg(sk_prf, opt_rand, M)
        md, idx_tree, idx_leaf = self._split_digest(self.hs.H_msg(R, pk_seed, pk_root, M))
        adrs = ADRS()
        adrs.set_tree(idx_tree)
        adrs.set_type_and_clear(FORS_TREE)
        adrs.set_key_pair(idx_leaf)
        sig_fors = self.fors_sign(md, sk_seed, pk_seed, adrs)
        pk_fors = self.fors_pk_from_sig(sig_fors, md, pk_seed, adrs)
        return R + sig_fors + self.ht_sign(pk_fors, sk_seed, pk_seed, idx_tree, idx_leaf)

    def verify_internal(self, M, sig, pk):                             # Algorithm 20
        p, n = self.p, self.p.n
        if len(sig) != p.sig_bytes or len(pk) != 2 * n:
            return False
        pk_seed, pk_root = pk[:n], pk[n:]
        R = sig[:n]
        fors_len = p.k * (1 + p.a) * n
        sig_fors, sig_ht = sig[n:n + fors_len], sig[n + fors_len:]
        md, idx_tree, idx_leaf = self._split_digest(self.hs.H_msg(R, pk_seed, pk_root, M))
        adrs = ADRS()
        adrs.set_tree(idx_tree)
        adrs.set_type_and_clear(FORS_TREE)
        adrs.set_key_pair(idx_leaf)
        pk_fors = self.fors_pk_from_sig(sig_fors, md, pk_seed, adrs)
        return self.ht_verify(pk_fors, sig_ht, pk_seed, idx_tree, idx_leaf, pk_root)

    # "Pure" external interface (Algorithms 22 and 24): domain-separate the context.
    @staticmethod
    def _pure_message(M, ctx):
        if len(ctx) > 255:
            raise ValueError("context too long")
        return bytes([0, len(ctx)]) + ctx + M

    def sign(self, M, sk, ctx=b"", addrnd=None):
        return self.sign_internal(self._pure_message(M, ctx), sk, addrnd)

    def verify(self, M, sig, pk, ctx=b""):
        return self.verify_internal(self._pure_message(M, ctx), sig, pk)
