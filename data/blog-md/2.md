# ZeroCheck Polynomial Interactive Oracle Proof

The ZeroCheck PIOP (Polynomial Interactive Oracle Protocol) is a subprotocol used in zero-knowledge proof systems to verify that a polynomial evaluates to zero over a specific domain. It is a critical building block in many zero-knowledge proof systems, particularly in protocols like Plonk, to check consistency or enforce certain constraints.

### Purpose of ZeroCheck PIOP

In a zero-knowledge proof, the prover often needs to demonstrate that a polynomial $f(X)$:
	•	Either evaluates to zero on certain inputs, such as all elements in a domain $D$,
	•	Or satisfies specific conditions implying that some computation is correct.

For instance:
	1. $f(X) = 0$ might encode the correctness of a relation.
	2. $f(X) = 0$ over all $X \in D$ might verify consistency with a pre-specified structure.

This ensures that the prover’s claims about the polynomial are consistent with the protocol’s constraints.

### How ZeroCheck PIOP Works

The protocol is structured in several rounds of interaction between the prover and verifier. Here’s the general approach:

1.	Input: The prover holds a polynomial $f(X)$ and claims it satisfies  $f(X) = 0$  over a domain $D$.
2.	Polynomial Reduction:
	    •	The prover reduces $f(X)$ modulo a vanishing polynomial $Z_D(X)$, which vanishes (evaluates to zero) at all points in $D$:

    $$ Z_D(X) = \prod_{x \in D} (X - x) $$

	•	The prover expresses $f(X)$ as:
    $f(X) = Z_D(X) \cdot q(X) + r(X)$,

where:
- $q(X)$  is the quotient polynomial.
- $r(X)$  is the remainder polynomial with degree  $\text{deg}(r) < \text{deg}(Z_D)$.

3.	Verifier Query:
	•	The verifier checks whether $r(X) = 0$. This involves:
	•	Sampling random challenge points  $\alpha$  from the field.
	•	Asking the prover for evaluations of  $f(X)$,  $Z_D(X)$, and  $q(X)$ at  $\alpha$.

4.	Verification:
	•	Using the prover’s responses, the verifier confirms:
$f(\alpha) = Z_D(\alpha) \cdot q(\alpha) + r(\alpha)$.
•	If $r(X) = 0$, then  $f(X)$  is divisible by  $Z_D(X)$, and the claim  $f(X) = 0$  over  $D$  holds.

_This relation works fine here and the polynomial is a Univariate polynomial, would like to establish such relationship but over a multilinear polynomial this time. How can we achieve this?_



---
## ZeroCheck: Multilinear polynomials
_This finds application in HyperPlonk (a multi-linear expression of the plonk protocol)_

Given a polynomial $w(x_1, x_2, x_3)$, prove $w$ is a zero polynomial (a poly that evaluates to `zero` for every input variables).

Making use of the `Schwartz-Zipple lemma`. prover can prove sufficently that $w$ is a zero polynomial if $w(r_1,r_2,r_3)$ = 0, where $\{r_1,r_2,r_3\}$ are random field elements.

Prover builds a polynomial $f$ and proves $f$'s is $0$ via `SumCheck`
$f(x_1,x_2,x_3) = w(r_1,r_2,r_3) \cdot eq((x_1,x_2,x_3), (r_1,r_2,r_3))$

where;
$eq(\vec{x},\vec{y}) = \prod_{i=1}^{3} (x_iy_i + (1 - x_i)(1 - y_i))$
$eq(\vec{x},\vec{y})$ is $1$ if $\vec{x}= \vec{y}$; else $0$;


Next: [Permutation Check Polynomial IOP](https://hackmd.io/@0xdeveloperuche/BkCdZ1tGJg)


reference: 
Zhenfei Zhang: https://www.youtube.com/watch?v=kAD5aBnZHvU