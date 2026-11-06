The category of cryptographic proof system this book focuses on is the `Zero Knowledge` proof system. A zero-knowledge proof system is a cryptographic protocol that allows one party, known as the prover, to convince another party, known as the verifier, that a particular statement is true without revealing any information beyond the validity of the statement itself. This remarkable concept ensures that the verifier gains no additional knowledge about the prover's secret or the underlying data beyond the fact that the statement is correct.

Going into the protocol, the `Prover` usually has a `Problem` it claims to have a solution to, and the `Verifier` expects a `Proof` that the `Prover` has a valid `Solution` to the `Problem`.

Most zero-knowledge proof systems follow this process:

![From a problem to a SNARK: problem, computation, algebraic circuit, arithmetization, quadratic arithmetic program, SNARK](assets/notes/computational-proof-systems/problem-to-snark.png)

This chapter focuses on navigating from `Problem` → `Computation` → `Algebraic Circuit` → `Arithmetization` → `Quadratic Arithmetic Program`.

### Problem

This is the computable problem, expressible mathematically, that the `Prover` can compute the solution to. The example we will play with is the `IsZero` problem.

The `IsZero` problem, in the context of zero-knowledge proofs and circuit-based proving systems like Circom, is the challenge of checking whether a given value is zero inside an arithmetic circuit. A circuit can only add and multiply, so "is this value equal to zero?" has no direct gate. The usual solution has the prover supply the inverse of the value as an extra witness, and then uses constraints to check it.

This problem can be expressed as a Circom circuit this way:

```circom
pragma circom 2.0.0;

template IsZero() {
    signal input in;
    signal output out;
    signal inv;

    // Witness hint: the prover computes inv. `<--` adds NO constraint.
    inv <-- in != 0 ? 1 / in : 0;

    // Constraint 1: defines out
    out <== 1 - in * inv;

    // Constraint 2: without this one, the circuit is unsound
    in * out === 0;
}

component main = IsZero();
```

Both constraints matter, because `inv` is only a hint and the prover can set it to anything:

- If `in` is not zero, constraint 2 forces `out = 0`, and constraint 1 then forces `inv` to be the true inverse.
- If `in` is zero, constraint 1 gives `out = 1` whatever `inv` is.

Without constraint 2, a cheating prover could take a non-zero `in`, set `inv = 0`, and get `out = 1`, claiming that a non-zero value is zero.

Now that we've declared this problem as a Circom circuit, the next step is to represent it as an `Algebraic Circuit`.

### Algebraic Circuit

An algebraic circuit is a mathematical representation used to perform computations over a field by composing basic arithmetic operations (addition and multiplication) and constants. These circuits are integral to the design and analysis of cryptographic proof systems, especially zero-knowledge proofs. Algebraic circuits help convert computational problems into polynomial forms, which are then used to construct proofs that verify the correctness of computations without revealing the inputs.

**Components of an Algebraic Circuit**

1. **Inputs**: The variables or elements from a finite field that serve as the starting values for the circuit.
2. **Gates**: **Addition gates** sum two inputs from the field, and **multiplication gates** multiply two inputs from the field.
3. **Constants**: Fixed elements from the field used in operations.
4. **Outputs**: The results of the computations, which are also elements of the field.

**Structure of an Algebraic Circuit**

An algebraic circuit can be visualized as a directed acyclic graph (DAG), where nodes represent inputs, gates and outputs, and edges represent the flow of data from one operation to another.

Recall the `IsZero` problem we are playing with. This is how it is expressed as an `Algebraic Circuit`. Gates 0 to 2 compute `out = 1 - in * inv`, and gate 3 computes `in * out`, whose result the circuit constrains to be zero:

![The IsZero algebraic circuit: in times minus one, times inv, plus one gives out; in times out must equal zero](assets/notes/computational-proof-systems/is-zero-circuit.svg)

After obtaining the algebraic circuit, the next step is to represent it in an `Intermediate Representation` like `R1CS`, `Plonkish`, `AIR` and so on. This is done by `Arithmetization`.

### Arithmetization

Arithmetization is the process of taking a circuit description via a programming language and turning it into a system of mathematical constraints that enable fast verification. With this set of mathematical constraints, a verifier can run a small number of algebraic checks to show with high probability that the prover is not lying.

I got this definition from [this](https://medium.com/@yujiangtham/lets-dissect-a-zksnark-part-2-5f92f1d7d2e9) blog.

**Arithmetization Techniques**

These are the most common arithmetization techniques. This book works with R1CS and Plonkish; AIR and CCS are listed for completeness.

1. R1CS
2. Plonkish
3. AIR
4. CCS

In summary, the journey from a computable problem to a verifiable proof involves several crucial steps: expressing the problem as an algebraic (arithmetic) circuit, and then arithmetizing that circuit into mathematical constraints suitable for efficient verification. Breaking these steps down gives a deeper understanding of how zero-knowledge proofs ensure privacy and integrity, and sets the stage for the specific techniques explored in the rest of this book.
