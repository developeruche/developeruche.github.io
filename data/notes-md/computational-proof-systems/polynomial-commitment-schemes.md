In the ever-evolving world of cryptography and secure computation, polynomial commitments stand as a cornerstone of modern protocols, blending mathematical elegance with practical power. But what exactly are they? At their core, polynomial commitments let a prover publish a short commitment to a polynomial, a mathematical expression like $x^2 + 3x + 2$, and later prove what that polynomial evaluates to at chosen points, without sending the whole polynomial. The commitment is binding, so the prover cannot change the polynomial afterwards. Verifiers can check evaluations cheaply, and this makes these commitments indispensable in zero-knowledge proofs, blockchain scaling and verifiable computation. If the polynomial itself must stay secret, the scheme also has to be hiding, which not every scheme is by default.

Imagine you need to prove you know a secret recipe, but you can't share the ingredients: just a taste that confirms it's legit. Polynomial commitments do something similar: they let us "commit" to a polynomial and later reveal only what's needed, efficiently and securely. This chapter explores how they work, why they matter, and where they're pushing the boundaries of technology.

*Intro powered by Grok; I was extremely lazy :)*

In this chapter:

- [KZG Polynomial Commitment Scheme](/notes/cryptography-zkp/computational-proof-systems/kzg-polynomial-commitment/)
- [Univariate KZG](/notes/cryptography-zkp/computational-proof-systems/univariate-kzg/)
- [Multilinear KZG](/notes/cryptography-zkp/computational-proof-systems/multilinear-kzg/)
- [Batch Univariate KZG](/notes/cryptography-zkp/computational-proof-systems/batch-univariate-kzg/)
- [FRI](/notes/cryptography-zkp/computational-proof-systems/fri-polynomial-commitment/)
