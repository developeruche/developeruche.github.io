# ProductCheck Polynomial Interactive Oracle Proof

ProductCheck PIOP (Polynomial Interactive Oracle Proof) is a subprotocol commonly used in zero-knowledge proofs to verify the product relation of polynomials or polynomial evaluations efficiently. This verification is performed without revealing sensitive information about the underlying data.

ProductCheck ensures that a claimed product relation holds between given polynomials or their evaluations. For example, suppose you have three polynomials $f(X)$, $g(X)$, and $h(X)$, and the prover claims:


$$h(X) = f(X) \cdot g(X)$$


The ProductCheck PIOP is used to verify this claim interactively with the verifier without revealing the explicit form of these polynomials.

### Definition of ProductCheck Relation

The relation  $R_{\text{Prod}}$  in a `ProductCheck PIOP` is defined as follows:


$$R_{\text{Prod}} = \{ (h, f, g) \mid h(X) = f(X) \cdot g(X) \}$$


This means $h(X)$  is the pointwise product of  $f(X)$  and  $g(X)$.

### Key Steps in ProductCheck PIOP

The protocol typically involves the following steps:
1.	**Claim Commitment**:
The prover commits to polynomials $f(X)$, $g(X)$, and $h(X)$, or their evaluations over a specific domain. These commitments may be polynomial oracles or cryptographic polynomial commitments (e.g., KZG commitments).
2.	**Verifier Challenges**:
The verifier sends a random challenge  $\alpha$  to the prover.
3.	**Pointwise Check**:
The prover evaluates $f(\alpha)$, $g(\alpha)$, and $h(\alpha)$ and sends these values back to the verifier. The verifier checks whether:
$h(\alpha) = f(\alpha) \cdot g(\alpha)$
4.**Consistency Check (Optional)**:
If commitments were used, the verifier ensures that the evaluations $f(\alpha), g(\alpha), h(\alpha)$  are consistent with the committed polynomials.

_As was explored in ZeroCheck, this sub-protocol works fine for Univariate Polynomials and we would also want to establish such relationship for the multilinear polynomial also_

---
## ProductCheck: Multilinear Polynomial

This is to an extent similar to the multilinear sumcheck, but in this case we've got two multilinear polynomials $f$ and $g$ and we want to prove that the product of eash of these polynomials over the boolean hypercube is equal. 
This can be expressed mathemeatically;

$$ \prod_{x_1, x_2, x_3 \in \{0,1\}^3} f(x_1,x_2,x_3) =  \prod_{x_1, x_2, x_3 \in \{0,1\}^3} g(x_1,x_2,x_3) $$

**Step One**: A new polynomial $p(x_0, x_1, x_2, x_3)$ with 4 variable;
- Define $p(0, x_1, x_2, x_3) = f(x_1,x_2,x_3) / g(x_1,x_2,x_3)$ 
- Define $p(1,\vec{x}) = p(\vec{x}, 0) \times p(\vec{x}, 1)$
- if $f$ and $g$ have the same product, $p(1,1,1,0) == 1$ 

Now, knowing this, how can we prove it? this is where the concept of random linear combination comes into play!

**Step Two**: Another new polynomial $q(x_1,x_2,x_3)$ with $3$ variables
- Define
    $q(x_1,x_2,x_3) = p(1,x_1,x_2,x_3) - p(x_1,x_2,x_3,0) \times p(x_1,_x2,x_3,1) + r \cdot (f(x_1,x_2,x_3) - p(0,x_1,x_2,x_3) \times  g(x_1,x_2,x_3))$
- Invoke Zero Check on $q$, and addtionally prove $q(1,1,1,0) = 1$, then we have been able to achieve proving that;
    - $p(1, \vec{x}) - p(\vec{x}, 0) \times p(\vec{x}, 1) = 0$
    - $f(\vec{x}) - p(0, \vec{x}) \times g(\vec{x}) = 0$

Next: [SumCheck Polynomial IOP](https://hackmd.io/@0xdeveloperuche/BJqcjSHz1g)


reference:
Zhenfei Zhang: https://www.youtube.com/watch?v=kAD5aBnZHvU