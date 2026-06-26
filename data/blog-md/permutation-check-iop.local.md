# Permutation Check Polynomial IOP
The PermutationCheck PIOP is used in many zero knowledge protocol, this document would be looking into this PIOP from the light of the plonk protocol.

The permutation check in the Plonk protocol is used to ensure that a set of variables or constraints satisfies a particular permutation argument. This is essential in Plonk to enforce consistency between “wires” (the inputs and outputs of arithmetic gates) across multiple constraints without explicitly revealing intermediate values.

For example:
- Suppose you have variables  $a, b, c$  in one gate and  $x, y, z$  in another, and you want to enforce that  $a$  is equal to  $x$ ,  $b$  is equal to  $y$ , and  $c$  is equal to  $z$ .
- Instead of explicitly encoding these equalities, Plonk ensures this by proving that  $\{a, b, c\}$  is a permutation of  $\{x, y, z\}$.

**How Does the Permutation Check Work?**
1.	**Lagrange Interpolation of Wires**:
Each wire’s values over a domain (like the set of gates) are represented as polynomials  $w_1(X), w_2(X), \ldots, w_n(X)$.
2.	**Adding a Permutation Commitment**:
A permutation polynomial  $\sigma(X)$  is introduced, which encodes the intended permutation mapping. For example,  $\sigma(i)$  indicates that the value at position  $i$  in one wire corresponds to the value at position  $\sigma(i)$  in another wire.
3.	Creating Permuted Copies:
For the wires to match under the permutation, the prover commits to polynomials  $z(X)$  (the permutation accumulator) that “links” the original wire values to their permuted counterparts. This polynomial ensures consistency between the original and permuted values.
4.	Defining the Permutation Argument:
To verify that the values match under the permutation, the Plonk protocol checks a consistency equation over the domain. Specifically:

$$ z(X) \cdot \prod_{i=1}^{n}(w_i(X) + \beta \cdot s_i(X) + \gamma) = z(\omega \cdot X) \cdot \prod_{i=1}^{n}(w_i(X) + \beta \cdot X + \gamma) $$

Here:
- $z(X)$: Permutation polynomial (accumulator).
- $w_i(X)$: Wire polynomials representing the values.
- $s_i(X)$: Permutation selectors encoding  $\sigma(X)$.
- $\beta, \gamma$: Random challenges to prevent cheating.
- $\omega$: A root of unity for cycling through the domain.
5.	Zero-Knowledge Property:
By committing to the wire polynomials and using random challenges  $\beta, \gamma$, the prover ensures that the verifier cannot infer the actual values being permuted, preserving zero-knowledge.

## PermutationCheck Polynomial IOP on Multilinear Polynomials
This is relatively the most robust (computationally) PIOP in the plonk protocol, but it happens to see good use in other cryptographic proof systems (at least some form of it variants). 

> Given two MLEs $f$ and $g$, and a permutation Polynomial $\sigma_{perm}$, prove $g$ is applying $\sigma_{perm}$ over $f$.

The strategy that would be adopted it doing this would be;
- Building two polynomials;
$a(\vec{x}) := f(\vec{x}) + \beta\cdot\sigma_{id}(\vec{x}) + \gamma,$
$b(\vec{x}) := g(\vec{x}) + \beta\cdot\sigma_{perm}(\vec{x}) + \gamma$
- Invloke the `Product Check` protocol on $a(\vec{x})$ and $b(\vec{x})$. (See Lemma 5.3 in the Plonk paper for more details on this)


Next: [ProductCheck Polynomial IOP](https://hackmd.io/@0xdeveloperuche/B1GexOrGkl)





reference:
Zhenfei Zhang: https://www.youtube.com/watch?v=kAD5aBnZHvU
Plonk Paper: https://eprint.iacr.org/2019/953