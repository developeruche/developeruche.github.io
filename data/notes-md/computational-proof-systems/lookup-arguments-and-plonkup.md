A lookup argument is a protocol that efficiently proves that a value, or a set of values, used in a computation exists within a predefined table. It's a way to say, "I used a valid value from this list."

For example:

- **Table:** $\{1, 4, 9, 16\}$ (the squares of 1 to 4).
- **Claim:** "My computation used a value that is in this table."
- **Goal:** Prove this without revealing which value was used, and without encoding the whole check in gates.

The table itself is often public, and known to the verifier. The privacy concerns the values being looked up. What a lookup argument adds is efficiency. Expressing a check like this directly as arithmetic constraints gets unwieldy for large tables or for operations like bitwise logic and range checks, and a lookup can replace many gates with one membership check.

*Going further into this section, it's assumed the reader has a good understanding of the PLONK protocol. If that assumption is wrong, please do something about it [here](/notes/cryptography-zkp/computational-proof-systems/plonk-protocol/).*

We will look at two lookup argument protocols used hand in hand with PLONK:

- [Plookup](/notes/cryptography-zkp/computational-proof-systems/plookup/)
- [Halo2 lookup](/notes/cryptography-zkp/computational-proof-systems/halo2-lookup-protocol/)

Integrating plookup into PLONK itself gives [PlonKup](https://eprint.iacr.org/2022/086).
