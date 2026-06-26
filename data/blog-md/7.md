# The Groth16 protocol

prerequisite for this study are;
- Bilinear pairings and elliptic curves
- Quadratic arithmetic programs (QAPs)

Bilinear pairings and elliptic curves are fundamental to the Groth16 proving system and many other advanced cryptographic protocols. Elliptic curves provide a secure and efficient foundation, while bilinear pairings enable the construction of succinct, non-interactive proofs that are both powerful and practical for real-world applications.


#### Elliptic Curves

**Elliptic Curves Overview:** An elliptic curve is a set of points that satisfy a specific mathematical equation. Over a finite field $\mathbb{F}_q​$, an elliptic curve $E$ is typically defined by an equation of the form: $y^2 = x^3 + ax + b$ where $a$ and $b$ are coefficients in $\mathbb{F}_q$, and the curve is non-singular (i.e., it has no cusps or self-intersections), which requires the discriminant $4a^3 + 27b^2 \neq 0$.

### Bilinear Pairings in Groth16

In the context of the Groth16 proving system, bilinear pairings are used to construct efficient proofs that are both small in size and quick to verify. The system relies on the properties of bilinear pairings to ensure that the proof verification can be performed using simple algebraic operations, making the process efficient even for complex statements.

**Example Use in Groth16:**

- **Setup Phase:** During the setup phase, a trusted party generates public parameters that include elements in $G_1$​, $G_2$​, and $G_T$​.
- **Proving Phase:** The prover uses these parameters to create a proof that certain computations were performed correctly. This involves operations in $G1$​ and $G2$.
- **Verification Phase:** The verifier checks the proof by performing pairing operations $e$ and ensures that certain equations hold in $G_T$​. The bilinear nature of the pairing allows these checks to be performed efficiently.

### The Protocol 
The `Groth16` protocol in most cases, starts with a Circuit. A `Circuit`  in ZKP is a structured way to represent a computation. It is analogous to a digital logic circuit used in computer engineering. 

**Structure:**

- A circuit is composed of **inputs**, **gates**, and **outputs**.
- **Inputs**: These are the values that the prover knows and wants to keep private (often called witnesses) along with the public inputs.
- **Gates**: These perform basic operations (such as addition, multiplication, logical AND, OR) on the inputs.
- **Outputs**: These are the results of the computations performed by the gates.

**Types of Circuits:**

- **Arithmetic Circuits**: These circuits use arithmetic gates (addition, multiplication) over a finite field. They are often used in zk-SNARKs because they can efficiently represent the types of computations involved in many cryptographic applications.
- **Boolean Circuits**: These circuits use logical gates (AND, OR, NOT) and are more common in classical computer science but can be transformed into arithmetic circuits for use in zk-SNARKs.

The next stage of the protocol is to convert this `Circuit` to a format called `R1CS` 

A rank-1 constraint system (R1CS) with n variables and m constraints and p public inputs has a witness vector $w∈F^n$. By convention, the first p elements of w are the public input and the first public input $w_0​$ is fixed to 1. The m constraints in R1CS are a product equation between three inner products:
$$
(w⋅ai​)⋅(w⋅bi​)=w⋅ci​
$$
where vectors $(a_i​,b_i​,c_i​)∈F^3⋅^n$ specify the constraint. The constraint vectors are usually very sparse, typically only nonzero for a single or few values. These constraint vectors can be aggregated in $n×m$ matrices so that the whole constraint system can be concisely written using an element-wise product.

$$
(w⋅A)∘(w⋅B)=w⋅C
$$

After obtaining this R1CS representation, it needs to be transformed into its QAP representation to go further in this proof system.

#### Trusted Setup 
This next stage of the groth16 protocol is the trusted setup stage, in this stage, something called the `Common reference string` or `Public parameter` is obtained. This `Groth16` proof system has two phases; 

1. The **Powers of Tau**
2. **Circuit Specific Common reference string generation**

##### Powers of Tau
During this process, we would be generating $τ,α,β$ having in mind that the number of constraints in the Circuit is $m$, we would compute the following;

$(τ^0,τ^1,τ^2,…,τ^{2⋅m−2})⋅G_1​$
$(τ^0,τ^1,τ^2,…,τ^{m−1})⋅G_2​$
$α⋅(τ^0,τ^1,τ^2,…,τ^{m−1})⋅G_1​$
$β⋅(τ^0,τ^1,τ^2,…,τ^{m−1})⋅G_1​$
$β⋅G_2​$

This completes the phase one process of the trusted setup.

**Circuit Specific Common reference string generation**
This phase involves doing some operations that are circuit-specific.

Given circuit polynomials $A_i​,B_i​,C_i$​, generate random values $γ,δ$ and define the polynomials $L_i$​ by:
$$
L_i​(X)=β⋅A_i​(X)+α⋅B_i​(X)+C_i​(X)
$$

We can not compute the $L_i​(X)$ directly since we don't know $α$ and $β$, but we can still construct $L_i​(τ)⋅G_1​$ using linear combinations of the values from the previous step. This way, we compute the proving key:

$(α,β,δ)⋅G_1​$
$(τ^0,τ^1,τ^2,τ^3,…,τ^{m−1})⋅G_1​$
$δ^{−1}⋅(L_p​(τ),L_{p+1}​(τ),…,L_{m−1}​(τ))⋅G_1​,$
$δ^{−1}⋅(τ^0,τ^1,τ^2,τ3,…,τ^{m−2})⋅Z_x​(τ)⋅G_1​$
$(β,δ)⋅G_2​$
$(τ^0,τ^1,τ^2,τ^3,…,τ^{m−1})⋅G_2​$

Verification key;

$α⋅G_1​$
$γ^{−1}⋅(L_0​(τ),L_1​(τ),L_2​(τ),…,L_{p−1}​(τ))⋅G)_1​$
$(β,γ,δ)⋅G_2​$

Instead of providing $α⋅G1$​ and $β⋅G_2​$ we could also provide $α⋅β⋅G_3​$ in the verifying key, but $G_3$​elements tend to be big and weird so we avoid them.

The Phase 2 ceremony is critical for soundness. If $δ$ is known the prover can construct any $δ^{−1}⋅P(τ)⋅G_1$​ of degree $2⋅n−1$ where otherwise it is constraint to the form $δ^{−1}⋅H(τ)⋅Z_x​(τ)⋅G_1$​. The forced factorization into $H$ and $Z_x$ is critical for soundness.

**Linear combination**
if you are as smart as I am Phase two is very confusing, but before we can break this down, we need to look into linear combination; how we can construct information concerning from secret even though we have just the encrypted version of this secret ($G.secret$).

_Keep your eyes on this_
$∏_{i=0}^l​(G.{τ^i})^{ϕ_i}​=G.{ϕ(τ)}$ 

Having in mind that $G.{τ^i}$ are the elements of the powers of tau. 

To achieve this $L_i​(X).G_1 =β⋅A_i​(X).G_1 +α⋅B_i​(X).G_1+C_i​(X).G_1$, 

We would have to break this down; 
1. $β⋅A_i​(τ).G_1$
2. $α⋅B_i​(τ).G_1$
3. $C_i​(X).G_1$



reference;
[Remco Bloemen](https://2π.com/22/groth16/)
https://www.rareskills.io/post/groth16