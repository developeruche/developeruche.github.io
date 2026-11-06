### The Sum-Check Protocol

The sum-check protocol is a fundamental sub-protocol used in many zero-knowledge proofs, in the context of both interactive proofs and zk-SNARKs. It was introduced by Lund, Fortnow, Karloff and Nisan in [Algebraic Methods for Interactive Proof Systems](https://dl.acm.org/doi/10.1145/146585.146605). Its purpose is to prove that a given polynomial, evaluated over a specified domain, sums to a particular value.

The sum-check protocol has served as the single most important "hammer" in the design of efficient interactive proofs (from [Proofs, Arguments, and Zero-Knowledge](https://people.cs.georgetown.edu/jthaler/ProofsArgsAndZK.html)). Suppose we are given an $n$-variate polynomial $f$ defined over a finite field $\mathbb{F}$. The prover wants to convince the verifier of the value of this sum:

$$T = \sum_{x_1 \in \{0,1\}} \sum_{x_2 \in \{0,1\}} \cdots \sum_{x_n \in \{0,1\}} f(x_1, x_2, \ldots, x_n)$$

Summing the evaluations of a polynomial over the Boolean hypercube may seem like a simple and not very useful task. Make no mistake: a good number of problems can be translated into this form, and the sum has $2^n$ terms, so the verifier gains a lot by not computing it directly.

### The Protocol

Sum-check is an interactive protocol that can be made non-interactive using `Fiat-Shamir`. This section explores it in its interactive form, while the Rust implementation below is non-interactive.

**Problem setup**

- Prover $P$ and verifier $V$: the two main entities in the protocol.
- Multivariate polynomial $f(x_1, x_2, \ldots, x_n)$: the polynomial that the prover claims has a specific sum over a domain.
- Domain: this is $\{0, 1\}^n$, meaning every variable $x_i$ takes the value 0 or 1. This domain is popularly known as the Boolean hypercube.

**Protocol steps**

Initialization: the prover and verifier agree on the polynomial $f$ and the claimed sum $T$.

**Round 1.** The prover sends a univariate polynomial, obtained by summing out every variable except the first:

$$g_1(X_1) = \sum_{(x_2, \ldots, x_n) \in \{0, 1\}^{n-1}} f(X_1, x_2, \ldots, x_n)$$

The verifier checks that $g_1(0) + g_1(1) = T$, and that the degree of $g_1$ is at most the degree of $f$ in $x_1$, rejecting if not. It then chooses a random element $r_1 \in \mathbb{F}$ and sends it to the prover. The claim is now about $g_1(r_1)$, a sum over one fewer variable.

**Round $j$, for $1 < j < n$.** The prover sends a univariate polynomial $g_j(X_j)$, claimed to equal:

$$g_j(X_j) = \sum_{(x_{j+1}, \ldots, x_n) \in \{0,1\}^{n-j}} f(r_1, \ldots, r_{j-1}, X_j, x_{j+1}, \ldots, x_n)$$

- The verifier checks that $g_{j-1}(r_{j-1}) = g_j(0) + g_j(1)$, and checks the degree of $g_j$, rejecting if not.
- The verifier chooses a random element $r_j \in \mathbb{F}$ and sends it to the prover.

**Round $n$.** The prover sends $g_n(X_n)$, claimed to equal $f(r_1, \ldots, r_{n-1}, X_n)$.

- The verifier checks that $g_{n-1}(r_{n-1}) = g_n(0) + g_n(1)$, and checks the degree of $g_n$.
- The verifier chooses a random element $r_n \in \mathbb{F}$ and evaluates $f(r_1, \ldots, r_n)$ with a single oracle query to $f$. This is the only time the verifier needs $f$ itself.
- The verifier checks that $g_n(r_n) = f(r_1, \ldots, r_n)$, rejecting if not. If nothing has been rejected, the verifier accepts.

**Why this is sound.** Suppose the claimed $T$ is wrong. To pass round 1, the prover must send some $g_1$ that differs from the true polynomial. Two different univariate polynomials of degree at most $d$ agree on at most $d$ points, so at the random $r_1$ the prover is, with high probability, left making a false claim again in the next round. This repeats until the final check, which compares against $f$ directly. By a union bound, a false claim passes with probability at most $nd/|\mathbb{F}|$, where $d$ is the maximum degree of $f$ in any variable. This argument needs the degree bound, which is why the degree checks above are part of the protocol.

Through this iterative process of reducing a multivariate sum to univariate polynomials, and using randomness to ensure soundness, the verifier can confidently accept or reject the prover's claim while doing only $O(nd)$ work plus one evaluation of $f$.

---

## Sum-Check by Hand

This section walks through the steps of the protocol using an example, to get the feeling of following it by hand. We use small integers so the arithmetic is easy to follow. A real run happens over a large finite field, with random challenges.

Given the polynomial

$$f(x,y,z) = 2x + xz + yz$$

its sum over the Boolean hypercube is 12:

| Boolean hypercube | Poly eval | Evaluation result |
| --- | --- | --- |
| $0,0,0$ | $f(0,0,0)$ | $0$ |
| $0,0,1$ | $f(0,0,1)$ | $0$ |
| $0,1,0$ | $f(0,1,0)$ | $0$ |
| $0,1,1$ | $f(0,1,1)$ | $1$ |
| $1,0,0$ | $f(1,0,0)$ | $2$ |
| $1,0,1$ | $f(1,0,1)$ | $3$ |
| $1,1,0$ | $f(1,1,0)$ | $2$ |
| $1,1,1$ | $f(1,1,1)$ | $4$ |

$$T = 1 + 2 + 3 + 2 + 4 = 12$$

The prover computes this and sends the result to the verifier to start the protocol. The prover and verifier also agree on the polynomial $f$.

**Round 1.** The prover keeps $x$ free and sums over the hypercube of the remaining variables $y$ and $z$:

$$
\begin{aligned}
g_1(x) &= f(x,0,0) + f(x,0,1) + f(x,1,0) + f(x,1,1) \\
&= 2x + 3x + 2x + (3x + 1) = 10x + 1
\end{aligned}
$$

The prover sends $g_1$. The verifier checks it against the claimed sum:

$$g_1(0) + g_1(1) = 1 + 11 = 12 = T$$

If this check fails, the prover has been malicious and the verifier halts. Otherwise, the verifier chooses a random number and sends it to the prover. Say $r_1 = 2$.

**Round 2.** The prover fixes $x = r_1 = 2$:

$$f(2,y,z) = 4 + 2z + yz$$

It then keeps $y$ free and sums over the remaining variable $z$:

$$g_2(y) = f(2,y,0) + f(2,y,1) = 4 + (6 + y) = 10 + y$$

The prover sends $g_2$. The verifier now compares it with the *previous polynomial at the challenge*:

$$g_2(0) + g_2(1) = 10 + 11 = 21 = g_1(2) = 10 \cdot 2 + 1$$

This check passes. The verifier sends another random number. Say $r_2 = 4$.

**Round 3.** The prover fixes $y = r_2 = 4$. This is the last variable, so nothing is left to sum over:

$$g_3(z) = f(2,4,z) = 4 + 2z + 4z = 6z + 4$$

The prover sends $g_3$, and the verifier checks:

$$g_3(0) + g_3(1) = 4 + 10 = 14 = g_2(4) = 10 + 4$$

**Final check.** The verifier chooses one last random number, say $r_3 = 3$, and evaluates the original polynomial at the three challenges:

$$g_3(3) = 6 \cdot 3 + 4 = 22$$

$$f(2,4,3) = 2 \cdot 2 + 2 \cdot 3 + 4 \cdot 3 = 4 + 6 + 12 = 22$$

They match, so the verifier accepts that the sum is 12. Here is the whole run on one screen:

| Round | Prover sends | Verifier checks | Verifier replies |
| --- | --- | --- | --- |
| Start | $T = 12$ | | |
| 1 | $g_1(x) = 10x + 1$ | $g_1(0) + g_1(1) = 12 = T$ | $r_1 = 2$ |
| 2 | $g_2(y) = 10 + y$ | $g_2(0) + g_2(1) = 21 = g_1(2)$ | $r_2 = 4$ |
| 3 | $g_3(z) = 6z + 4$ | $g_3(0) + g_3(1) = 14 = g_2(4)$ | $r_3 = 3$ |
| Final | | $g_3(3) = 22 = f(2,4,3)$ | Accept |

Notice that the verifier needs the original polynomial only in the final check. The prover needs it throughout. This is the opening for making things cheaper: instead of holding all of $f$, the verifier can hold a polynomial commitment to it, and ask for just that one evaluation with a proof.

---

## Sum-Check Rust Implementation

### A step-by-step approach to building a sum-check proving system

Complete implementation: [GitHub repo](https://github.com/developeruche/cryptography-n-zk-research/tree/main/iops/sum_check)

The design approach is very similar to the other implementations in this book:

1. Design the structural interface
2. Comment out the steps needed to implement this interface
3. Work on any utility functions needed
4. Implement the complete interface
5. Write unit tests :)

### Drawing the Interface

We work with two structures to implement the `Sum Check` protocol specification:

1. Prover
2. Verifier

**Prover interface**

```rust
pub trait ProverInterface<F: PrimeField> {
    fn calculate_sum(poly: &Multilinear<F>) -> F;
    fn compute_round_zero_poly<P: MultilinearPolynomialInterface<F>>(
        poly: &P,
        transcript: &mut FiatShamirTranscript,
    ) -> P;
    fn sum_check_proof<P: MultilinearPolynomialInterface<F> + Clone>(
        poly: &P,
        transcript: &mut FiatShamirTranscript,
        sum: &F,
    ) -> SumCheckProof<F, P>;
}
```

Info:

- The generic `PrimeField` comes from the `ark_ff` crate.
- `calculate_sum`: computes the sum of the polynomial over the Boolean hypercube.
- `compute_round_zero_poly`: computes the polynomial of the first round, $g_1$ in the walkthrough above. The code numbers rounds from zero.
- `sum_check_proof`: the main function of the prover, computing the `SumCheckProof` of the given polynomial.

**Verifier interface**

```rust
pub trait VerifierInterface<F: PrimeField> {
    fn verify<P: MultilinearPolynomialInterface<F> + Clone>(proof: &SumCheckProof<F, P>) -> bool;
}
```

Info:

- `verify`: returns the validity of a given `SumCheckProof`, as `true` or `false`.

**Note: this is a non-interactive implementation, using a Fiat-Shamir transcript.** See [the chapter on interactive and non-interactive proofs](/notes/cryptography-zkp/computational-proof-systems/interactive-and-non-interactive-proofs/) if you haven't.

### Defining Data Structures

`Prover` and `Verifier` are empty structs that the interfaces hang off. The main data structure is the proof itself:

```rust
#[derive(Clone, PartialEq, Eq, Hash, Default, Debug)]
pub struct SumCheckProof<F: PrimeField, P: MultilinearPolynomialInterface<F>> {
    pub polynomial: P,
    pub round_poly: Vec<P>,
    pub round_0_poly: P,
    pub sum: F,
}
```

Given a polynomial, the prover returns this data structure, and the verifier can check it.

- `polynomial`: the polynomial the sum-check protocol was run on.
- `round_poly`: the polynomials from every round after the first.
- `round_0_poly`: the polynomial from the first round.
- `sum`: the sum to be proven.

### Implementing the Interfaces

Now that the interfaces and data structures are laid out, we implement these interfaces, starting with the `Prover`.

**Prover implementation**

```rust
#[derive(Clone, Default, Debug)]
pub struct Prover;

impl<F: PrimeField> ProverInterface<F> for Prover {
    fn calculate_sum(poly: &Multilinear<F>) -> F {
        poly.evaluations.iter().sum()
    }

    fn compute_round_zero_poly<P: MultilinearPolynomialInterface<F>>(
        poly: &P,
        transcript: &mut FiatShamirTranscript,
    ) -> P {
        let number_of_round = poly.num_vars() - 1;
        let bh = boolean_hypercube(number_of_round);
        let mut bh_partials = P::zero(1); // this is an accumulator

        for bh_i in bh {
            let current_partial = poly.partial_evaluations(bh_i, vec![1; number_of_round]);
            bh_partials.internal_add_assign(&current_partial);
        }

        transcript.append(bh_partials.to_bytes());
        bh_partials
    }

    fn sum_check_proof<P: MultilinearPolynomialInterface<F> + Clone>(
        poly: &P,
        transcript: &mut FiatShamirTranscript,
        sum: &F,
    ) -> SumCheckProof<F, P> {
        let round_0_poly = Self::compute_round_zero_poly(poly, transcript);
        let mut all_random_reponse = Vec::new();
        let mut round_poly = Vec::new();

        for i in 1..poly.num_vars() {
            let number_of_round = poly.num_vars() - i - 1;
            let bh = boolean_hypercube::<F>(number_of_round);
            let mut bh_partials = P::zero(1);

            let verifier_random_reponse_f = F::from_be_bytes_mod_order(&transcript.sample());
            all_random_reponse.push(verifier_random_reponse_f);

            for bh_i in bh {
                let bh_len = bh_i.len();
                let mut eval_vector = all_random_reponse.clone();
                eval_vector.extend(bh_i);
                let mut eval_index = vec![0; all_random_reponse.len()];
                let suffix_eval_index = vec![1; bh_len];
                eval_index.extend(suffix_eval_index);

                let current_partial = poly.partial_evaluations(eval_vector, eval_index);
                bh_partials.internal_add_assign(&current_partial);
            }

            transcript.append(bh_partials.to_bytes());
            round_poly.push(bh_partials);
        }

        SumCheckProof {
            polynomial: poly.clone(),
            round_poly: round_poly.clone(),
            round_0_poly: round_0_poly.clone(),
            sum: sum.clone(),
        }
    }
}
```

**Let's dive in!**

Something you need to know before going further: the `Multilinear` polynomial structure is expressed as a `Vec` of evaluations over the Boolean hypercube. If you don't yet understand how a polynomial can be expressed over the Boolean hypercube, now is the best time to [learn](/notes/cryptography-zkp/computational-proof-systems/polynomials/).

**calculate\_sum**: This is simply the sum of the polynomial's evaluation array.

**compute\_round\_zero\_poly**: This computes the first polynomial of the protocol, by iterating over the Boolean hypercube of all variables but the first and adding up the partial evaluations of the main polynomial. The result is then appended to the `transcript`. The transcript only accepts bytes, and the polynomial structure provides `to_bytes()` to get them.

**sum\_check\_proof**: This is the main function, as it computes the `SumCheckProof`. It starts by computing the round zero polynomial. It then needs a `Vec` to hold all the samples from the transcript, since the transcript emulates a random response from the `Verifier`. Next is the iteration stage, where most of the computation happens:

- Sample a pseudo-random response from the `transcript`, and save it, as it is needed in later rounds.
- Perform partial evaluations of the main polynomial, with the sampled values fixed and the remaining variables running over the hypercube.
- Append the resulting polynomial to the `transcript`, and push it to `round_poly`.
- Finally, use all of this data to create the `SumCheckProof`.

**Verifier implementation**

The verifier has just one function, `verify`, which returns `true` or `false` for a given `SumCheckProof`.

```rust
impl<F: PrimeField> VerifierInterface<F> for Verifier {
    fn verify<P: MultilinearPolynomialInterface<F>>(proof: &SumCheckProof<F, P>) -> bool {
        // steps
        // 1. eval poly_0 at 0 and 1 and check if the sum is equal to the sum in the proof [done]
        // 2. append poly_0 to the transcript
        // 3. eval poly_1 at rand_0 from transcript and check if the eval of poly_0 at 0 and 1 is equal to poly_1 at rand_0
        // 4. append poly_1 to the transcript
        // 5. repeat step 3 and 4 until the last round
        // 6. check if the eval of the last poly at rand(last) is equal to the eval of the main poly at all rands()
        let mut transcript = FiatShamirTranscript::default();
        let mut all_rands = Vec::new();

        // step 1
        let untrusted_sum = proof.round_0_poly.evaluate(&vec![F::one()]).unwrap()
            + proof.round_0_poly.evaluate(&vec![F::zero()]).unwrap();

        if untrusted_sum != proof.sum {
            println!(
                "untrusted_sum != proof.sum --> {} - {}",
                untrusted_sum, proof.sum
            );
            return false;
        }

        // step 2
        transcript.append(proof.round_0_poly.to_bytes());

        // step 3 and 4
        let sample_1 = F::from_be_bytes_mod_order(&transcript.sample());
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

        transcript.append(proof.round_poly[0].to_bytes());

        // step 5
        for i in 1..proof.round_poly.len() {
            let sample_i = F::from_be_bytes_mod_order(&transcript.sample());
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

            transcript.append(proof.round_poly[i].to_bytes());
        }

        // step 6
        let last_round_rand = F::from_be_bytes_mod_order(&transcript.sample());
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

**verify** takes the following steps:

- Evaluate `round_0_poly` at `0` and `1`, and check that the result equals the sum stated in the proof. If this passes, continue; otherwise return `false`.
- Append `round_0_poly` to the `transcript`. This repeats what the prover did during proving, so the verifier obtains the same samples.
- Evaluate the previous polynomial at the sample, and check that it equals the next polynomial evaluated at `0` plus at `1`, so `poly_0(rand_0) == poly_1(0) + poly_1(1)`.
- Append the next polynomial to the `transcript`, and repeat the last two steps until the last round.
- At the last round, check that the last polynomial at the last sample equals the main polynomial at all the samples:

```
poly_last(rand_last) == poly(rand_0, rand_1, ... rand_last)
```

- Return `true` if none of these checks failed.

### Limitations of This Implementation

This code is written for learning, and two things separate it from a production verifier:

- **It isn't succinct.** The proof carries the whole polynomial, so the verifier does work linear in its size. A real system replaces this with a polynomial commitment and one opening proof.
- **The transcript doesn't bind the statement.** Only the round polynomials are appended to the transcript, not `polynomial` or `sum`, and `verify` takes both from the proof. A cheating prover can therefore claim any sum: pick round polynomials that fit it, derive the samples, and only then choose a polynomial that passes the final check. I confirmed this with a forged proof for a false sum, which `verify` accepted. In a real system, the verifier must take the polynomial (or its commitment) from a trusted source, not from the proof, and the transcript must absorb the polynomial and the claimed sum before the first sample is drawn. This omission is known as "weak Fiat-Shamir".

---

## Sum-Check Over a Univariate Polynomial

The most efficient uses of sum-check are on multilinear polynomials, but there is also a univariate version, introduced in [Aurora](https://eprint.iacr.org/2018/828). It works very differently from the multilinear protocol: it has no rounds, and relies on the structure of the domain instead.

$$\text{Claim:} \quad \sum_{a \in H} p(a) = T$$

Here:

- $p(X)$ is a univariate polynomial.
- $H$ is a multiplicative subgroup of the field (the roots of unity of some order), with vanishing polynomial $Z_H(X) = \prod_{a \in H}(X - a)$.
- $T$ is the claimed sum.

**The key fact.** Summing $a^k$ over a multiplicative subgroup $H$ gives $0$ unless $|H|$ divides $k$. So for any polynomial of degree less than $|H|$, the sum over $H$ depends only on the constant term, and equals $|H|$ times that constant term.

Now divide $p(X)$ by $Z_H(X)$. The quotient term vanishes on $H$, and the key fact applies to the remainder. So the claim is true exactly when $p(X)$ can be written as:

$$p(X) = q(X) \cdot Z_H(X) + X \cdot r(X) + \frac{T}{|H|}, \qquad \deg r < |H| - 1$$

**Steps of the protocol:**

1. **Prover's claim:** The prover claims the sum is $T$, and commits to $p(X)$.
2. **Prover's decomposition:** The prover computes $q(X)$ and $r(X)$ as above, and commits to both.
3. **Verifier's challenge:** The verifier sends a random point $z$.
4. **Verifier's check:** The prover opens $p$, $q$ and $r$ at $z$, and the verifier checks the equation above at $X = z$. It also checks the degree bound on $r$, using the commitment scheme. The bound is essential: without it, any $T$ could be made to fit.

**A small example.** Over $\mathbb{F}_{17}$, take $H = \{1, 4, 16, 13\}$, so $Z_H(X) = X^4 - 1$, and let $p(X) = 3 + X + 4X^2 + X^3 + 5X^4 + 9X^5 + 2X^6$. Evaluating directly gives a sum of $T = 15$. Dividing by $Z_H$ gives $q(X) = 5 + 9X + 2X^2$ and the remainder $8 + 10X + 6X^2 + X^3$. The constant term of the remainder is $8$, and $|H| \cdot 8 = 32 \equiv 15 \pmod{17}$, which matches $T$.

References: [Proofs, Arguments, and Zero-Knowledge](https://people.cs.georgetown.edu/jthaler/ProofsArgsAndZK.html) by Justin Thaler, and [Aurora: Transparent Succinct Arguments for R1CS](https://eprint.iacr.org/2018/828) by Ben-Sasson et al.
