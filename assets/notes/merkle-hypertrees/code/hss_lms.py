"""
HSS/LMS hash-based signatures (RFC 8554) -- a readable reference implementation.

This is the hypertree you meet in LMS: HSS stacks L complete LMS trees.
Level 0 is the TOP tree (its root is the public key); level L-1 is the
bottom tree that signs messages. Each level's leaf signs the next level's
LMS public key.

Scope and intent
----------------
* Teaching / reference code: clear over fast. Pure Python + hashlib.
* Implements the SHA-256 / m = n = 32 parameter sets of RFC 8554
  (LMS H5..H25, LM-OTS W1..W8), pseudorandom key generation from
  Appendix A, HSS key generation (Alg. 7), signing with automatic
  regeneration of exhausted lower levels (Alg. 8), and HSS verification
  (Sec. 6.3).
* Default mode follows NIST SP 800-208 Sec. 6.1: every LMS tree gets its own
  I and SEED from the random generator, and the LM-OTS randomizer C is random.
* Optional deterministic mode (deterministic=True, NOT SP 800-208 compliant for
  HSS): lower-level trees and C are derived from the parent's SEED and leaf
  index. This derivation reproduces RFC 8554 Test Case 2 byte for byte from its
  top-level SEED and I, and makes upper-level re-signing after a state rollback
  produce identical bytes.
* Checked against RFC 8554 Appendix F test vectors (see test_hss_lms.py).
* NOT hardened: no constant-time care (hash-based signing leaks nothing
  secret through timing of chain lengths, but key loading etc. is not
  audited), no secure memory wiping, no HSM integration.

Wire formats follow RFC 8554 exactly, so signatures interoperate with other
conformant implementations (e.g. cisco/hash-sigs).
"""

from __future__ import annotations

import hashlib
import os
import struct
from dataclasses import dataclass, field
from typing import Callable, List, Optional

# --------------------------------------------------------------------------
# Encoding helpers and domain-separation constants (RFC 8554 Sec. 3, 4, 5)
# --------------------------------------------------------------------------

D_PBLC = 0x8080  # hashing an LM-OTS public key
D_MESG = 0x8181  # hashing the message
D_LEAF = 0x8282  # hashing a Merkle leaf
D_INTR = 0x8383  # hashing a Merkle interior node


def u32(x: int) -> bytes:
    return struct.pack(">I", x)


def u16(x: int) -> bytes:
    return struct.pack(">H", x)


def u8(x: int) -> bytes:
    return struct.pack(">B", x)


def H(*parts: bytes) -> bytes:
    h = hashlib.sha256()
    for p in parts:
        h.update(p)
    return h.digest()


class InvalidSignature(Exception):
    pass


class KeyExhausted(Exception):
    pass


# --------------------------------------------------------------------------
# Parameter sets (RFC 8554 Table 1 and Table 2)
# --------------------------------------------------------------------------


@dataclass(frozen=True)
class LmotsParams:
    typecode: int
    n: int   # hash length in bytes
    w: int   # bits per Winternitz digit (1, 2, 4, 8)
    p: int   # number of chains
    ls: int  # checksum left shift

    @property
    def sig_len(self) -> int:
        return 4 + self.n * (self.p + 1)


@dataclass(frozen=True)
class LmsParams:
    typecode: int
    m: int  # node length in bytes
    h: int  # tree height


LMOTS = {
    1: LmotsParams(1, 32, 1, 265, 7),
    2: LmotsParams(2, 32, 2, 133, 6),
    3: LmotsParams(3, 32, 4, 67, 4),
    4: LmotsParams(4, 32, 8, 34, 0),
}
LMOTS_BY_NAME = {"W1": LMOTS[1], "W2": LMOTS[2], "W4": LMOTS[3], "W8": LMOTS[4]}

LMS = {
    5: LmsParams(5, 32, 5),
    6: LmsParams(6, 32, 10),
    7: LmsParams(7, 32, 15),
    8: LmsParams(8, 32, 20),
    9: LmsParams(9, 32, 25),
}
LMS_BY_HEIGHT = {p.h: p for p in LMS.values()}


def lms_sig_len(lms: LmsParams, ots: LmotsParams) -> int:
    # u32(q) || lmots_sig || u32(type) || path[0..h-1]
    return 4 + ots.sig_len + 4 + lms.m * lms.h


def lms_pub_len(lms: LmsParams) -> int:
    # u32(type) || u32(otstype) || I || T[1]
    return 4 + 4 + 16 + lms.m


def hss_sig_len(levels: List[tuple]) -> int:
    """levels = [(LmsParams, LmotsParams), ...] from top (level 0) to bottom."""
    total = 4  # Nspk
    for i, (lms, ots) in enumerate(levels):
        total += lms_sig_len(lms, ots)
        if i > 0:
            total += lms_pub_len(lms)  # pub[i] travels inside the signature
    return total


# --------------------------------------------------------------------------
# LM-OTS (RFC 8554 Sec. 4)
# --------------------------------------------------------------------------


def coef(S: bytes, i: int, w: int) -> int:
    """The i-th w-bit digit of S, most significant first (Sec. 3.1.3)."""
    byte = S[(i * w) // 8]
    shift = 8 - (w * (i % (8 // w)) + w)
    return ((1 << w) - 1) & (byte >> shift)


def checksum(Q: bytes, ots: LmotsParams) -> int:
    total = 0
    for i in range(ots.n * 8 // ots.w):
        total += (1 << ots.w) - 1 - coef(Q, i, ots.w)
    return (total << ots.ls) & 0xFFFF


def lmots_digits(Q: bytes, ots: LmotsParams) -> List[int]:
    Qc = Q + u16(checksum(Q, ots))
    return [coef(Qc, i, ots.w) for i in range(ots.p)]


def lmots_private_element(I: bytes, q: int, i: int, seed: bytes) -> bytes:
    """Appendix A: x_q[i] = H(I || u32str(q) || u16str(i) || u8str(0xff) || SEED)."""
    return H(I, u32(q), u16(i), u8(0xFF), seed)


# Deterministic derivations used for RFC 8554 Test Case 2. Running the TC2 seeds
# through these reproduces its randomizers C and its second-level SEED and I
# exactly (checked in test_hss_lms.py). The 0xFFFD/0xFFFE/0xFFFF values sit where
# Appendix A puts the chain number i (always < 265), so they cannot collide with it.
D_C, D_CHILD_SEED, D_CHILD_I = 0xFFFD, 0xFFFE, 0xFFFF


def derive_C(I: bytes, q: int, seed: bytes) -> bytes:
    return H(I, u32(q), u16(D_C), u8(0xFF), seed)


def derive_child(I: bytes, q: int, seed: bytes):
    """(I, SEED) for the child tree certified by leaf q of the tree (I, seed)."""
    return (H(I, u32(q), u16(D_CHILD_I), u8(0xFF), seed)[:16],
            H(I, u32(q), u16(D_CHILD_SEED), u8(0xFF), seed))


def _chain(I: bytes, q: int, i: int, value: bytes, start: int, stop: int) -> bytes:
    """Apply the chain function for steps j = start .. stop-1."""
    prefix = I + u32(q) + u16(i)
    for j in range(start, stop):
        value = H(prefix, u8(j), value)
    return value


def lmots_public_key(ots: LmotsParams, I: bytes, q: int, seed: bytes) -> bytes:
    """Algorithm 1: returns K, the n-byte LM-OTS public key value."""
    top = (1 << ots.w) - 1
    ys = [_chain(I, q, i, lmots_private_element(I, q, i, seed), 0, top) for i in range(ots.p)]
    return H(I, u32(q), u16(D_PBLC), *ys)


def lmots_sign(ots: LmotsParams, I: bytes, q: int, seed: bytes, message: bytes,
               C: Optional[bytes] = None) -> bytes:
    """Algorithm 3. C is the per-signature randomizer (fresh random by default)."""
    if C is None:
        C = os.urandom(ots.n)
    Q = H(I, u32(q), u16(D_MESG), C, message)
    ys = [
        _chain(I, q, i, lmots_private_element(I, q, i, seed), 0, a)
        for i, a in enumerate(lmots_digits(Q, ots))
    ]
    return u32(ots.typecode) + C + b"".join(ys)


def lmots_pk_from_sig(sig: bytes, message: bytes, I: bytes, q: int, expected_type: int) -> bytes:
    """Algorithm 4b: recompute the candidate public key Kc from a signature."""
    if len(sig) < 4:
        raise InvalidSignature("LM-OTS signature too short")
    sigtype = struct.unpack(">I", sig[:4])[0]
    if sigtype != expected_type or sigtype not in LMOTS:
        raise InvalidSignature("LM-OTS type mismatch")
    ots = LMOTS[sigtype]
    if len(sig) != ots.sig_len:
        raise InvalidSignature("LM-OTS signature has wrong length")
    C = sig[4:4 + ots.n]
    ys = [sig[4 + ots.n * (k + 1): 4 + ots.n * (k + 2)] for k in range(ots.p)]
    Q = H(I, u32(q), u16(D_MESG), C, message)
    top = (1 << ots.w) - 1
    zs = [_chain(I, q, i, ys[i], a, top) for i, a in enumerate(lmots_digits(Q, ots))]
    return H(I, u32(q), u16(D_PBLC), *zs)


# --------------------------------------------------------------------------
# LMS: one Merkle tree of LM-OTS keys (RFC 8554 Sec. 5)
# --------------------------------------------------------------------------


@dataclass
class LmsPrivateKey:
    lms: LmsParams
    ots: LmotsParams
    I: bytes
    seed: bytes
    q: int = 0
    # Full node array T[1 .. 2^(h+1)-1]; index 0 unused. Kept in RAM so that
    # authentication paths are table lookups (RFC 8554 Appendix D).
    T: List[bytes] = field(default_factory=list, repr=False)

    @classmethod
    def generate(cls, lms: LmsParams, ots: LmotsParams, I: Optional[bytes] = None,
                 seed: Optional[bytes] = None) -> "LmsPrivateKey":
        key = cls(lms, ots, I or os.urandom(16), seed or os.urandom(lms.m))
        key._build_tree()
        return key

    def _build_tree(self) -> None:
        h = self.lms.h
        T: List[bytes] = [b""] * (1 << (h + 1))
        for q in range(1 << h):  # leaves: node r = 2^h + q
            K = lmots_public_key(self.ots, self.I, q, self.seed)
            r = (1 << h) + q
            T[r] = H(self.I, u32(r), u16(D_LEAF), K)
        for r in range((1 << h) - 1, 0, -1):  # interior nodes, bottom-up
            T[r] = H(self.I, u32(r), u16(D_INTR), T[2 * r], T[2 * r + 1])
        self.T = T

    @property
    def remaining(self) -> int:
        return (1 << self.lms.h) - self.q

    def public_key(self) -> bytes:
        return u32(self.lms.typecode) + u32(self.ots.typecode) + self.I + self.T[1]

    def sign(self, message: bytes, C: Optional[bytes] = None, deterministic: bool = False) -> bytes:
        """Sign with leaf q, then advance q. Caller is responsible for persisting
        the new q BEFORE releasing the signature (see HssPrivateKey.sign).
        With deterministic=True the randomizer C is derived from (I, q, SEED), so
        re-signing the same value at the same leaf yields identical bytes."""
        if self.q >= (1 << self.lms.h):
            raise KeyExhausted("LMS tree exhausted")
        q = self.q
        self.q += 1
        if C is None and deterministic:
            C = derive_C(self.I, q, self.seed)
        ots_sig = lmots_sign(self.ots, self.I, q, self.seed, message, C)
        r = (1 << self.lms.h) + q
        path = [self.T[(r >> i) ^ 1] for i in range(self.lms.h)]
        return u32(q) + ots_sig + u32(self.lms.typecode) + b"".join(path)


def parse_lms_public_key(buf: bytes, off: int = 0):
    """Returns ((LmsParams, LmotsParams, I, T1), new_offset)."""
    if len(buf) - off < 8:
        raise InvalidSignature("truncated LMS public key")
    lms_type, ots_type = struct.unpack(">II", buf[off:off + 8])
    if lms_type not in LMS or ots_type not in LMOTS:
        raise InvalidSignature("unknown LMS/LM-OTS type in public key")
    lms = LMS[lms_type]
    end = off + lms_pub_len(lms)
    if len(buf) < end:
        raise InvalidSignature("truncated LMS public key")
    I = buf[off + 8:off + 24]
    T1 = buf[off + 24:end]
    return (lms, LMOTS[ots_type], I, T1), end


def lms_signature_length_at(buf: bytes, off: int) -> int:
    """Length of the LMS signature starting at buf[off] (needed to split HSS sigs)."""
    if len(buf) - off < 8:
        raise InvalidSignature("truncated LMS signature")
    ots_type = struct.unpack(">I", buf[off + 4:off + 8])[0]
    if ots_type not in LMOTS:
        raise InvalidSignature("unknown LM-OTS type in signature")
    ots = LMOTS[ots_type]
    t_off = off + 4 + ots.sig_len
    if len(buf) < t_off + 4:
        raise InvalidSignature("truncated LMS signature")
    lms_type = struct.unpack(">I", buf[t_off:t_off + 4])[0]
    if lms_type not in LMS:
        raise InvalidSignature("unknown LMS type in signature")
    return 4 + ots.sig_len + 4 + LMS[lms_type].m * LMS[lms_type].h


def lms_verify(message: bytes, public_key: bytes, sig: bytes) -> bool:
    """Algorithm 6 / 6a. Returns True or False; never raises on bad input."""
    try:
        (lms, ots, I, T1), end = parse_lms_public_key(public_key)
        if end != len(public_key):
            return False
        if len(sig) < 8:
            return False
        q = struct.unpack(">I", sig[:4])[0]
        ots_sig_len = LMOTS[ots.typecode].sig_len
        ots_sig = sig[4:4 + ots_sig_len]
        t_off = 4 + ots_sig_len
        if len(sig) < t_off + 4:
            return False
        if struct.unpack(">I", sig[t_off:t_off + 4])[0] != lms.typecode:
            return False
        if q >= (1 << lms.h):
            return False
        if len(sig) != t_off + 4 + lms.m * lms.h:
            return False
        path = [sig[t_off + 4 + lms.m * i: t_off + 4 + lms.m * (i + 1)] for i in range(lms.h)]

        Kc = lmots_pk_from_sig(ots_sig, message, I, q, ots.typecode)
        node_num = (1 << lms.h) + q
        tmp = H(I, u32(node_num), u16(D_LEAF), Kc)
        for i in range(lms.h):
            parent = node_num // 2
            if node_num % 2 == 1:  # we are a right child
                tmp = H(I, u32(parent), u16(D_INTR), path[i], tmp)
            else:                   # we are a left child
                tmp = H(I, u32(parent), u16(D_INTR), tmp, path[i])
            node_num = parent
        return tmp == T1
    except InvalidSignature:
        return False


# --------------------------------------------------------------------------
# HSS: the hypertree (RFC 8554 Sec. 6)
# --------------------------------------------------------------------------


class HssPrivateKey:
    """Stateful HSS signer.

    levels[0] is the top tree; levels[-1] signs messages.
    signed_pubs[i] (for i >= 1) caches sig[i-1] || pub[i]: the parent's LMS
    signature on level i's public key, computed ONCE when level i is created
    and then copied into every signature that passes through level i.
    """

    def __init__(self, levels: List[LmsPrivateKey], signed_pubs: List[bytes],
                 rng: Callable[[int], bytes] = os.urandom, deterministic: bool = False):
        self.levels = levels
        self.signed_pubs = signed_pubs
        self.rng = rng
        # deterministic=False (default): each new tree gets I and SEED from rng,
        # as SP 800-208 Sec. 6.1 requires for HSS.
        # deterministic=True: lower trees and randomizers are derived from the
        # parent's secret and leaf index (the RFC 8554 Test Case 2 derivation).
        # A signer restored from an old backup then re-creates the SAME child
        # keys, so an upper leaf re-signs identical bytes instead of signing a
        # different child key. Not SP 800-208 compliant; never a substitute for
        # correct state handling (bottom-leaf reuse after rollback is fatal).
        self.deterministic = deterministic

    @property
    def L(self) -> int:
        return len(self.levels)

    def _new_child(self, parent: LmsPrivateKey, lms: LmsParams, ots: LmotsParams):
        """Create the child tree that parent's next leaf (parent.q) will certify."""
        if self.deterministic:
            I, seed = derive_child(parent.I, parent.q, parent.seed)
        else:
            I, seed = self.rng(16), self.rng(lms.m)
        child = LmsPrivateKey.generate(lms, ots, I, seed)
        pub = child.public_key()
        signed_pub = parent.sign(pub, deterministic=self.deterministic) + pub
        return child, signed_pub

    @classmethod
    def generate(cls, params: List[tuple], rng: Callable[[int], bytes] = os.urandom,
                 top_I: Optional[bytes] = None, top_seed: Optional[bytes] = None,
                 deterministic: bool = False) -> "HssPrivateKey":
        """Algorithm 7. params = [(LmsParams, LmotsParams), ...], top to bottom.
        Each level is its own LMS key pair with its own I and SEED."""
        if not 1 <= len(params) <= 8:
            raise ValueError("HSS supports 1 to 8 levels")
        if len({ots.n for _, ots in params} | {lms.m for lms, _ in params}) != 1:
            raise ValueError("all levels must use the same hash output length")
        lms0, ots0 = params[0]
        top = LmsPrivateKey.generate(lms0, ots0, top_I or rng(16), top_seed or rng(lms0.m))
        key = cls([top], [b""], rng, deterministic)
        for lms, ots in params[1:]:
            child, signed_pub = key._new_child(key.levels[-1], lms, ots)
            key.levels.append(child)
            key.signed_pubs.append(signed_pub)
        return key

    def public_key(self) -> bytes:
        return u32(self.L) + self.levels[0].public_key()

    def remaining(self) -> int:
        """Signatures left, counting the trees that regeneration can still create.

        Mixed-radix odometer: the bottom level's unused leaves, plus for each
        higher level its unused leaves times the capacity of everything below
        (each unused leaf can still certify one fresh subtree)."""
        caps = [1 << lvl.lms.h for lvl in self.levels]
        total = self.levels[-1].remaining
        below = caps[-1]
        for i in range(self.L - 2, -1, -1):
            total += self.levels[i].remaining * below
            below *= caps[i]
        return total

    def _refresh_exhausted_levels(self) -> None:
        """Algorithm 8: regenerate exhausted lower levels before signing."""
        if self.levels[-1].remaining > 0:
            return
        d = self.L - 1
        while d > 0 and self.levels[d].remaining == 0:
            d -= 1
        # levels d+1 .. L-1 are exhausted; level d must still have a leaf.
        if self.levels[d].remaining == 0:  # only possible when d == 0
            raise KeyExhausted("HSS key exhausted")
        for i in range(d + 1, self.L):
            old = self.levels[i]
            self.levels[i], self.signed_pubs[i] = self._new_child(self.levels[i - 1], old.lms, old.ots)

    def sign(self, message: bytes, persist: Callable[["HssPrivateKey"], None],
             C: Optional[bytes] = None) -> bytes:
        """Sign `message`. `persist(self)` is called after the state has advanced
        and BEFORE the signature is returned: if persist raises, no signature
        escapes, so a crash can waste a leaf but never reuse one."""
        self._refresh_exhausted_levels()
        bottom_sig = self.levels[-1].sign(message, C, deterministic=self.deterministic)
        persist(self)  # write-ahead: durable state first, signature second
        return u32(self.L - 1) + b"".join(self.signed_pubs[1:]) + bottom_sig

    # -- (de)serialization of the private state, for persist() callbacks ----
    def to_bytes(self) -> bytes:
        """Compact private state: per level (lms type, ots type, I, SEED, q) plus
        cached signed public keys. Trees are rebuilt from seeds on load."""
        out = [u32(self.L), u8(1 if self.deterministic else 0)]
        for lvl in self.levels:
            out += [u32(lvl.lms.typecode), u32(lvl.ots.typecode), lvl.I, lvl.seed, u32(lvl.q)]
        for sp in self.signed_pubs[1:]:
            out += [u32(len(sp)), sp]
        return b"".join(out)

    @classmethod
    def from_bytes(cls, buf: bytes, rng: Callable[[int], bytes] = os.urandom) -> "HssPrivateKey":
        L = struct.unpack(">I", buf[:4])[0]
        deterministic = bool(buf[4])
        off, levels = 5, []
        for _ in range(L):
            lt, ot = struct.unpack(">II", buf[off:off + 8])
            lms, ots = LMS[lt], LMOTS[ot]
            I = buf[off + 8:off + 24]
            seed = buf[off + 24:off + 24 + lms.m]
            q = struct.unpack(">I", buf[off + 24 + lms.m:off + 28 + lms.m])[0]
            off += 28 + lms.m
            lvl = LmsPrivateKey(lms, ots, I, seed, q)
            lvl._build_tree()
            levels.append(lvl)
        signed_pubs = [b""]
        for _ in range(L - 1):
            ln = struct.unpack(">I", buf[off:off + 4])[0]
            signed_pubs.append(buf[off + 4:off + 4 + ln])
            off += 4 + ln
        return cls(levels, signed_pubs, rng, deterministic)


def hss_verify(message: bytes, public_key: bytes, signature: bytes) -> bool:
    """RFC 8554 Sec. 6.3. Stateless; returns True/False."""
    try:
        if len(public_key) < 4 or len(signature) < 4:
            return False
        L = struct.unpack(">I", public_key[:4])[0]
        key = public_key[4:]
        Nspk = struct.unpack(">I", signature[:4])[0]
        if Nspk + 1 != L or not 1 <= L <= 8:
            return False
        off = 4
        for _ in range(Nspk):
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
        if off + sig_len != len(signature):  # no trailing or missing bytes
            return False
        return lms_verify(message, key, signature[off:])
    except (InvalidSignature, struct.error):
        return False
