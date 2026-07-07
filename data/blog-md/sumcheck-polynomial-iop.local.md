# SumCheck Polynomial Interactive Proof 
### The Sum Check Protocol 

The sum-check protocol is a fundamental sub-protocol used in various zero-knowledge proofs, particularly in the context of interactive proofs and zero-knowledge succinct non-interactive arguments of knowledge (zk-SNARKs). It was first introduced in the context of probabilistically checkable proofs (PCPs) by Lund, Fortnow, Karloff, and Nisan. The primary purpose of the sum-check protocol is to prove that a given polynomial, evaluated over a specified domain, sums to a particular value.

The sum-check protocol has served as the single most important “hammer” in the design of efficient interactive proofs. (from ProofsArgsAndZk). Suppose we are given a v-variate polynomial $g$ defined over a finite field $F$. The purpose of the sum-check protocol is for the prover to provide the verifier with the following sum:
<br/>

$$S = \sum_{x_1 \in \{0,1\}} \sum_{x_2 \in \{0,1\}} \cdots \sum_{x_n \in \{0,1\}} f(x_1, x_2, \ldots, x_n) = T$$

<br/>
Performing the sum of the evaluations of a polynomial over the boolean hypercube may seem like a very simple task and not so useful especially when the polynomial is represented in the `Evaluation` form, make no mistake, a good number of problems can be translated into this form, having polynomial so big we would have to apply this principle to take advantage of the computational efficiency it births.


#### The Sum Check Protocol.

Recall this sum check protocol is an interactive protocol that can be made non-interactive using `Fiat Shamir`, during this protocol layout we will be exploring this protocol in its interactive form but in the RUST implementation, we will be implementing the protocol as an interactive protocol.

_Here is the equation for the sum_

$$S = \sum_{x_1 \in \{0,1\}} \sum_{x_2 \in \{0,1\}} \cdots \sum_{x_n \in \{0,1\}} f(x_1, x_2, \ldots, x_n) = T$$
**Problem Setup**
	•	Prover $(P)$ and Verifier $(V)$: The two main entities in the protocol.
	•	Multivariate Polynomial  $f(x_1, x_2, \ldots, x_n)$ : The polynomial that the prover claims has a specific sum over a domain.
	•	Domain: Typically, this is  $\{0, 1\}^n$ for simplicity, meaning all variables  x_i  can take values 0 or 1, this domain is popularly referred to as the boolean hypercube.

**Protocol Steps**

Initialisation:
The prover and verifier agree on the polynomial  $f$  and the claimed sum  $T$.

Step 1: Sum Reduction

The prover breaks down the original sum into a series of simpler sums. Starting with the outermost sum, the prover expresses it in terms of intermediate sums:

$S = \sum_{x_1 \in \{0, 1\}} g_1(x_1)$

where:
$g_1(X_1) = \sum_{x_2, \ldots, x_n \in \{0, 1\}^{n-1}} f(X_1, x_2, \ldots, x_n)$

The prover then sends the polynomial  $g_1(x_1)$  to the verifier. This process to achieving this is to reduce this multilinear polynomial to a univariate polynomial by performing a partial evaluation of this polynomial the boolean hypercube of length $\{x_2 \ldots, x_n\}$ this would return a univariate polynomial that on evaluation at $0$ , $1$ and summing this evaluation, the result would be the sum of the polynomial $g_1(X_1)$.

Step 2: Verification and Recursive Check

The verifier checks that  $g_1(0) + g_1(1) = T$.

$V$ chooses a random element $r_1 ∈ F$, and sends $r_1$ to $P$.

The prover then defines:
$S_1 = g_1(r_1, x_1, x_2, \ldots, x_n)$

**Here comes the recursion**

- In the $j$ th round, for $1 < j < v$, $P$ sends to $V$ a univariate polynomial $g_j(X_j)$ claimed to equal:

$$
∑_{(x_{j+1} ,...,x_n) ∈ \{0,1\}^{n−j}} g(r_1,...,r_{j−1},X_j,x_{j+1},...,x_n)
$$
- $V$ checks that $g_{j−1}(r_{j−1}) = g_j(0)+g_j(1)$, rejecting if not
- $V$ chooses a random element $r_j ∈ F$, and sends $r_j$ to $P$.
- In Round $v$, $P$ sends to $V$ a univariate polynomial $g_v(X_v)$ claimed to be equal $g(r_1,...,r_{v−1},X_v)$. You notice that this is the first time the initial claim polynomial is needed for proof generations. $V$ checks 0. that $g_{v−1}(r_{v−1}) = g_v(0)+g_v(1)$.
- $V$ chooses a random element $r_v ∈ F$ and evaluates $g(r_1,...,r_v)$ with a single Oracle query to g. $V$ checks that $g_v(r_v) = g(r_1,...,r_v)$, rejecting if not. 
- If $V$ has not yet been rejected, $V$ halts and accepts.


The sum-check protocol is a cornerstone in the realm of zero-knowledge proofs, especially within interactive proofs and zk-SNARKs. It plays a pivotal role in efficiently verifying that a polynomial sums to a specific value over a given domain, making it an invaluable tool in cryptographic applications. By leveraging the properties of the sum-check protocol, we can translate complex problems into manageable forms, optimizing computational efficiency and ensuring robust verification.

 

Through its iterative process of reducing multivariate polynomials to univariate forms and utilizing randomness to ensure soundness, the sum-check protocol exemplifies the ingenuity of zero-knowledge proofs. It ensures that the verifier can confidently accept or reject the prover’s claims with minimal interaction and computational overhead. As we delve deeper into the implementation of this protocol, particularly using Rust, we witness its practical applications and the elegance of its design, highlighting its significance in modern cryptographic systems.


---

# SumCheck Protocol By Hand

This subsection would be focused on implementing the steps of the sum check protocol using an example, simulating the feeling of following the protocol step by step by hand. 

given a polynomial, $f(x,y,z) = 2x + xz + yz$

The sum of the polynomial $f(x,y,z)$ over the boolean hypercube is 12, this is how it was gotten. 

| Boolean Hypercube | Poly Eval  | Evaluation result |
| ----------------- | ---------- | ----------------- |
| $0,0,0$           | $f(0,0,0)$ | $0$               |
| $0,0,1$           | $f(0,0,1)$ | $0$               |
| $0,1,0$           | $f(0,1,0)$ | $0$               |
| $0,1,1$           | $f(0,1,1)$ | $1$               |
| $1,0,0$           | $f(1,0,0)$ | $2$               |
| $1,0,1$           | $f(1,0,1)$ | $3$               |
| $1,1,0$           | $f(1,1,0)$ | $2$               |
| $1,1,1$           | $f(1,1,1)$ | $4$               |

$sum = 1 + 2 + 3 + 2 + 4 = 12$

This is the computation done by the prover and sends the result (the sum) to verifier to initialise the protocol.



![sum check protocol image](assets/blogs/sumcheck-polynomial-iop/img-1.png)

### The Protocol
1. The Prover and the verifier agrees on the `Polynomial` ($f$) and `Sum`. This is done practically by sending the polynomial alongside the computed sum to the verifier.
2. Sum Reduction:
	The prover computes the polynomial $g_1(X_1)$ making use of a multilinear polynomial partial evaluation:
	<br> 
	
	$$g_1(X_1) = \sum_{x_2, \ldots, x_n \in \{0, 1\}^{n-1}} f(X_1, x_2, \ldots, x_n)$$

	<br>
	This process from $f(x,y,z)$ where $y$ and $z$ would be replaced with the boolean hypercube elements from the boolean hypercube of length $x_2$ to $x_n$. This mathematically implies;
<br>

$$f(x,0,0) + f(x,0,1) + f(x,1,0) + f(x,1,1)$$<br>
<br>

$$f_1(x) = 10x + 1$$<br>

This polynomial $f_1$ which is yielded from the partial evaluation by the prover is sent to the verifier. 

3. Verification and recursive check
	The verifier performs this check;
	<br>
 
	$$f_1(0) + f_1(1) = 12$$
	<br>

	if the check fails the prover is been malicious the verifier halts the verification process. 
	The verifier chooses a random number $r_1 ∈ F$ and sends $r_1$ to the prover.
	
	Say $r_1 = 2$;
	<br>

	 With this information, the prover define the polynomial;
	<br>

	 $$S_1 = g_1(r_1, x_1, x_2, ... x_n)$$
	<br>
 
	 This implies;
	<br>

	 $$s_1 = f(r_1,y,z) = 2z + yz + 4$$
	<br>

	Performing reduction in the polynomial, still using the boolean hypercube elements similar to what was done earlier on but this time the length of the boolean hypercube is 1 less. Mathematically this would imply;
	<br>
	<br> 
	$$ s_1(y, 0) + s_1(y, 1) = 10 + y = f_2(y) $$
	
	The prover sends $f_2$ to the verifier, then the verifier carries out this check;
	<br>
	$$f_1(0) + f_1(1) = f_2(r_1)$$
	<br>
 
	$$f_1(0) + f_1(1) = 0 + 1 + 10 + 1 = 12$$
	<br>

	$$f_2(r_1) = 10 + 2 = 12$$
	
	This check passes!
	With this, the verifier can send another random number to the prover to compute the next claim. 
	Say $r_2 = 4$, the prover would respond with a Univariate polynomial;
	<br>
	<br>
	$S_2(X_3) = f(2,4,X_3) = 6z + 4$. 
	
	The verifier performs this check. 
	<br>
	$$S_2(0) + S_2(1) = f_2(r_2)$$
	<br>
	$$S_2(0) + S_2(1) = 4 + 0 + 10 = 14$$
	<br>
	$$f_2(r_2) = 10 + 4 = 14$$	<br>
	The Verifier now performs the last check, verifier chooses another random number $r_3 = 3$;
	<br>
 	<br>
  
	Check:
	<br>
	$S_2(r_3) = f(r_1, r_2, r_3)$
	<br>
	$S_2(6) = f(2,4,3)$
	<br>
 
	If this check passes, the verifier is mathematically satisfied with the proof of the sum computation. 
	
	Where $f$ is the initial polynomial $\{2,4,3\}$ are all the random numbers sent by the verifier during the protocol interaction.
	
	This Ends the Sum Check implementation by hand.
	
	Notice it is only at the last round that the initial polynomial is needed, this can be used as a notch for making the RUST implementation more efficient. This also can be switched to using a polynomial commitment scheme for making this algorithm more memory cheap, we will be exploring this in the future.




---
# SumCheck Rust Implementation

### A step-by-step approach to building a sum check proving system.

Complete Implementation: [Github Repo](https://github.com/developeruche/cryptography-n-zk-research/tree/main/sum_check)

The design approach we would be taken is very similar to the over implementations in this book. 
1. Design the structural interface
2. Comment out the step needed for implementing this interface
3. Working on any utility function that would be need
4. Implement the complete interface
5. Write Unit test. :)

### Drawing the Interface
We would be working with two sturctures to implement the `Sum Check` protocol specifications; 
1. Prover 
2. Verifier 

**Prover Interface**
```rust
pub trait ProverInterface<F: PrimeField> {
    fn calculate_sum(&mut self);
    fn compute_round_zero_poly(&mut self);
    fn sum_check_proof(&mut self) -> SumCheckProof<F>;
}
```

Info:
- The Generic `PrimeField` is gotten from  `ff` crate
- `calculate_sum`: This function would be used to compute the sum of the polynomial.
- `compute_round_zero_poly`: This function computes the round zero polynomial during the Zeroth round of the Sum Check protocol.
- `sum_check_proof`: This is the main function of the prover, computing the `SumCheckProof` of the given polynomial.

**Verifier Interface**
```rust
pub trait VerifierInterface<F: PrimeField> {
    fn verify(&mut self, proof: &SumCheckProof<F>) -> bool;
}
```

info:
- `verify`: This function returns the validity state of of a given `Su,CheckProof`, a `True` of `False`.

**Note: This is a non-interactive implementation, using Fiat Shamir transcript**
see [Fiat Shamir]() if you haven't.


### Defining Data Structures
We have gotten the interface on how the Sum check proof system implementation would be structured. The main Data structure we would be needing are;

1. `Prover`
	```rust
	#[derive(Clone, Default, Debug)]
	pub struct Prover<F: PrimeField> {
	    pub poly: Multilinear<F>,
	    pub round_poly: Vec<Multilinear<F>>,
	    pub round_0_poly: Multilinear<F>,
	    pub sum: F,
	    pub transcript: FiatShamirTranscript,
	}
	```
	- `poly`: This is the polynomial the sum check protocol would be ran on.
	- `round_poly`: This is a vector of polynomials yielded during the protocol process
	- `round_0_poly`: this is the first polynomial yielded during this protocol.
	- `sum`: this is the prover claimed sum.
	- `transcript`: this is the Fiat Shamir transcript used to make this protocol implementation non-interactive.
	
2. `Verifier`
	```rust
	#[derive(Clone, Default, Debug)]
	pub struct Verifier<F: PrimeField> {
	    pub transcript: FiatShamirTranscript,
	    phantom: std::marker::PhantomData<F>,
	}
	```
	The `Verifer` is a very simple structure, having just the `transcript` used for making this protocol non-interactive.
	
3. `SumCheckProof`
```rust
#[derive(Clone, PartialEq, Eq, Hash, Default, Debug)]
pub struct SumCheckProof<F: PrimeField> {
    pub polynomial: Multilinear<F>,
    pub round_poly: Vec<Multilinear<F>>,
    pub round_0_poly: Multilinear<F>,
    pub sum: F,
}
```
On give a polynomial to the prover to run the sum check protocol on, the prover return this data structure and the data structure can be verified by the verifier.

- `polynomial`: this is the polynomial the sum check protocol was ran on.
- `round_poly`: this is a vector of polynomials yielded during the sum check protocol.
- `round_0_poly`: this is the first polynomial yielded during the sum check protocol.
- `sum`: this is the sum that is to be proven.

### Implementing Interfaces 

Now the interface and data structures has been laid out properly, the next task item to handle is to implement these interfaces on the corresponding data structure, we would be starting with the `Prover`.

#### Prover Interface Implementation

Before diving into the `ProverInterface` Implementation, we would be implementing some functions;

```rust
impl<F: PrimeField> Prover<F> {
    pub fn new(poly: Multilinear<F>) -> Self {
        Self {
            poly,
            round_poly: Default::default(),
            round_0_poly: Default::default(),
            sum: Default::default(),
            transcript: Default::default(),
        }
    }
    pub fn new_with_sum(poly: Multilinear<F>, sum: F) -> Self {
        Self {
            poly,
            round_poly: Default::default(),
            round_0_poly: Default::default(),
            sum,
            transcript: Default::default(),
        }
    }
    pub fn new_with_sum_and_round_zero(poly: Multilinear<F>) -> Self {
        let mut prover = Self::new(poly);
        prover.calculate_sum();
        prover.compute_round_zero_poly();
        prover
    }
}
```

Info: 
- `new`: This function creates a new prover instance.
- `new_with_sum`: This function crates a new prover instance with sum already computed.
- `new_with_sum_and_round_zero`: This function creates a new  prover instance, computes the sum and computes the round zero polynomial.

**Implementing the prover interface**

```rust
impl<F: PrimeField> ProverInterface<F> for Prover<F> {
    fn calculate_sum(&mut self) {
        self.sum = self.poly.evaluations.iter().sum();
    }
    fn compute_round_zero_poly(&mut self) {
        let number_of_round = self.poly.num_vars - 1;
        let bh = boolean_hypercube(number_of_round);
        let mut bh_partials: Multilinear<F> = Multilinear::zero(1);

        for bh_i in bh {
            let current_partial = self
                .poly
                .partial_evaluations(bh_i, vec![1; number_of_round]);
            bh_partials += current_partial;
        }

        self.transcript.append(bh_partials.to_bytes());
        self.round_0_poly = bh_partials;
    }

    fn sum_check_proof(&mut self) -> SumCheckProof<F> {
        self.compute_round_zero_poly();
        let mut all_random_reponse = Vec::new();

        for i in 1..self.poly.num_vars {
            let number_of_round = self.poly.num_vars - i - 1;
            let bh = boolean_hypercube::<F>(number_of_round);

            let mut bh_partials: Multilinear<F> = Multilinear::zero(1);
            let verifier_random_reponse_f = F::from_be_bytes_mod_order(&self.transcript.sample());
            all_random_reponse.push(verifier_random_reponse_f);

            for bh_i in bh {
                let bh_len = bh_i.len();
                let mut eval_vector = all_random_reponse.clone();
                eval_vector.extend(bh_i);
                let mut eval_index = vec![0; all_random_reponse.len()];
                let suffix_eval_index = vec![1; bh_len];
                eval_index.extend(suffix_eval_index);

                let current_partial = self.poly.partial_evaluations(eval_vector, eval_index);

                bh_partials += current_partial;
            }

            self.transcript.append(bh_partials.to_bytes());
            self.round_poly.push(bh_partials);
        }

        SumCheckProof {
            polynomial: self.poly.clone(),
            round_poly: self.round_poly.clone(),
            round_0_poly: self.round_0_poly.clone(),
            sum: self.sum,
        }
    }
}
```

**Let's dive in!**

Here is something you need to know before going further, the `Polynomial` structure used in the implementation, is a multilinear polynomial expressed as a `Vec` of evaluations over the `Boolean Hypercube`. Trust me, if you don't understand the boolean hypercube or how a polynomial structure can be expressed over the boolean hypercube, now would be the best time. [resource]()

**calculate_sum**: This is simple the sum of the polynomials evaluation array.

**compute_round_zero_poly**: This is a very important function in the sum check protocol implementation, it computes the first polynomial yielded by the sum check protocol. This is achieved by iteratively performing a partial evaluation on the main polynomial over the boolean hypercube. After obtaining this polynomial, we need to update the `transcript`, the `transcript` accepts only bytes as input, the `Polynomial` structure provided a utility function for getting the bytes representation of the polynomial structure using this method, `to_bytes()`.

**sum_check_proof**: This is the main function for this `Prover` implementation as it computes the `SumCheckProof`. Starting off the proof generation process is, computing the round zero polynomial using the method, `compute_round_zero_poly()`. Next, we would need a `Vec` to hold all the `samples` gotten from the transcript, recall this `transcript` is emulating a random response from the `Verifier`. The the next process is the iteration stage, a lot of compute happens here;
- sample pseudo random responses from the `transcript` and also saving this in memory as we would be making use of this later on.
- Performing recursive partial evaluations on the main polynomial.
- After every recursive partial evaluation, we would be appending the resulting multi-linear polynomial to the `transcipt` and push this polynomial to the `round_poly` `Vec`, this woud be using to create a instance of the `SumCheckProof`.
- Using these data, create the `SumCheckProof` instance.


#### The Verifier Interface

This verifier interface houses just one function `verify` which on providing a `SumCheckProof`, it asserts if valid by returning a `True` or `False`.

```rust
impl<F: PrimeField> VerifierInterface<F> for Verifier<F> {
    fn verify(&mut self, proof: &SumCheckProof<F>) -> bool {
        let mut all_rands = Vec::new();
        let untrusted_sum = proof.round_0_poly.evaluate(&vec![F::one()]).unwrap()
            + proof.round_0_poly.evaluate(&vec![F::zero()]).unwrap();
        if untrusted_sum != proof.sum {
            println!(
                "untrusted_sum != proof.sum --> {} - {}",
                untrusted_sum, proof.sum
            );
            return false;
        }
        self.transcript.append(proof.round_0_poly.to_bytes());
        let sample_1 = F::from_be_bytes_mod_order(&self.transcript.sample());
        all_rands.push(sample_1);
        let eval_poly_0_at_rand = proof.round_0_poly.evaluate(&vec![sample_1]).unwrap();
        let eval_poly_1_at_0_plus_1 = proof.round_poly[0].evaluate(&vec![F::one()]).unwrap()
            + proof.round_poly[0].evaluate(&vec![F::zero()]).unwrap();
        if eval_poly_0_at_rand != eval_poly_1_at_0_plus_1 {
            println!(
                "eval_poly_0_at_rand != eval_poly_1_at_0_plus_1 --> {} - {}",
                eval_poly_0_at_rand, eval_poly_1_at_0_plus_1
            );
            return false;
        }
        self.transcript.append(proof.round_poly[0].to_bytes());
        for i in 1..proof.round_poly.len() {
            let sample_i = F::from_be_bytes_mod_order(&self.transcript.sample());
            all_rands.push(sample_i);
            let eval_poly_i_at_rand = proof.round_poly[i - 1].evaluate(&vec![sample_i]).unwrap();
            let eval_poly_i_plus_1_at_0_plus_1 =
                proof.round_poly[i].evaluate(&vec![F::one()]).unwrap()
                    + proof.round_poly[i].evaluate(&vec![F::zero()]).unwrap();

            if eval_poly_i_at_rand != eval_poly_i_plus_1_at_0_plus_1 {
                println!(
                    "eval_poly_i_at_rand != eval_poly_i_plus_1_at_0_plus_1 --> {} - {}",
                    eval_poly_i_at_rand, eval_poly_i_plus_1_at_0_plus_1
                );
                return false;
            }

            self.transcript.append(proof.round_poly[i].to_bytes());
        }
        let last_round_rand = F::from_be_bytes_mod_order(&self.transcript.sample());
        all_rands.push(last_round_rand);
        let eval_last_poly_at_rand = proof.round_poly[proof.round_poly.len() - 1]
            .evaluate(&vec![all_rands[all_rands.len() - 1]])
            .unwrap();
        let eval_main_poly_at_all_rands = proof.polynomial.evaluate(&all_rands).unwrap();

        if eval_last_poly_at_rand != eval_main_poly_at_all_rands {
            println!(
                "eval_last_poly_at_rand != eval_main_poly_at_all_rands --> {} - {}",
                eval_last_poly_at_rand, eval_main_poly_at_all_rands
            );
            return false;
        }

        true
    }
}
```

**verify**: This function verifies the sum check proof by taking the following steps.
- evaluate the `round_0_poly` at `0` and `1` and check if the result is same as the stated sum in the `SumCheckProof`. if this passes, we can process with the protocol else return `False`.
- append the `round_0_poly` to the `transcript`, we are emulating the input the prover sent in to the `transcript` during proving, doing this we would obtain the same `samples` during verification. 
- evaluate `poly_1` at `rand_0` from `transcript` and check if the evaluation of `poly_0` at `0` and `1` is equal to `poly_1` at `rand_0`.
- append `poly_1` to the `transcript`
- repeat step 3 and 4 until the last round
- at the last round, check if the evaluation of the last poly at rand(last) is equal to the evaluation of the main poly at all rands. This implies;
```
poly_last(rand_last) == poly(rand_0, rand_1, ... rand_last)
```
- Return `True` if non of these checks fails.


# SumCheck Protocol Over a Univariate Polynomial
Most if the most efficent use of the sum-check protocol is expressed when polynomails are in multilinear form, but the sum-check protocol is also useful on polynomails expressed as univariate polynomial. This section would be exploring how sum-check can come into play here. It is important to note that sum-check on univariate polynomail is relatively much more simplier.

> the SumCheck PIOP verifies whether a univariate polynomial  p(X)  satisfies certain constraints over a set of evaluation points. For example, it can check whether the polynomial sums to a particular value over a domain  $D$


$$ \text{Claim:} \quad \sum_{x \in D} p(x) = T $$

Here:
	•	 $p(X)$  is a univariate polynomial.
	•	 $D$  is a structured evaluation domain, often a coset of the roots of unity.
	•	 $T$  is the claimed sum.

Steps in SumCheck PIOP (Univariate Case)

1.	Prover’s Initial Claim:
The prover claims: $\sum_{x \in D} p(x) = T$ and commits to $p(X)$.
2.	Verifier’s Random Challenge:
The verifier sends a random challenge $r$ to the prover.
3.	Prover’s Transformation:
The prover reduces the claim to a new polynomial $p{\prime}(X)$ defined by:
$p{\prime}(X) = \sum_{x \in D} \frac{p(x)}{X - r}$ This reduction leverages the fact that summing over the domain can be encoded as evaluations of  p(X)  divided by a shifted  X - r  term.
4.	Verifier’s Query:
The verifier queries the value of  $p{\prime}(r)$, ensuring consistency with  $p(X)$  and the claimed sum  $T$.



Next: [ZeroCheck Polynomial IOP](https://hackmd.io/@0xdeveloperuche/B1ptaSSf1x)


references:
[Proofs, Arguments, and Zero-Knowledge](https://people.cs.georgetown.edu/jthaler/ProofsArgsAndZK.html) by Justin Thaler

