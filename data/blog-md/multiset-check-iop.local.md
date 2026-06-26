# The multiset check IOP

The multiset check IOP (Interactive Oracle Proof) is a cryptographic technique often used in zero-knowledge proof systems to verify that two collections (multisets) are identical, without directly revealing their contents. This approach is particularly valuable in protocols like PLONK, where the prover and verifier need to ensure consistency between certain sets of values derived during the computation.

### Multiset Basics

A multiset is a collection of elements where repetition is allowed. For instance:
	•	 $A = \{a, b, a, c\}$
	•	 $B = \{c, a, b, a\}$

The multisets A and B are equal if they contain the same elements with the same multiplicities, regardless of the order.

Use Case in Cryptography

In proof systems like PLONK, multisets often represent:
	1.	Wires of a circuit: Ensuring input and output wires match the expected values.
	2.	Permutations: Verifying that the values in one column are a valid permutation of another (e.g., proving consistency across gates).

The multiset check is used to verify these properties efficiently, without requiring the verifier to directly inspect large data sets.

### Steps in a Multiset Check

1.	Encoding the Multisets:
The prover encodes each multiset into a polynomial using a technique like Lagrange interpolation. For a multiset  $A = \{a_1, a_2, …, a_n\}$ , the encoding polynomial is typically:
$f_A(X) = (X - a_1)(X - a_2)\cdots(X - a_n)$
This is often computed in an optimized way using evaluations over a domain, especially in FFT-based systems.
2.	Equality Test via a Ratio:
    To check that A and B are equal, their encoded polynomials $f_A(X$ and $f_B(X)$ should satisfy:

    $\frac{f_A(X)}{f_B(X)} = 1$

    This equality is tested at a random challenge point to ensure soundness.
3.	Reducing to a Single Polynomial Check:
In protocols like PLONK, the multiset check is reduced to verifying a single consistency polynomial $Z(X)$, known as the permutation polynomial. This polynomial encodes how one multiset can be transformed into another via a permutation.

### Advantages of Multiset Check IOP

1.	Efficiency: Instead of directly comparing two sets element by element, the polynomial-based approach reduces the problem to evaluating a small number of polynomial identities.
2.	Soundness: A dishonest prover cannot construct fake polynomials without risking detection by the verifier’s random checks.
3.	Zero-Knowledge: The verifier learns nothing about the specific contents of the sets, only that they are equal.

### Application in PLONK

In PLONK, the multiset check is used to ensure:
	•	Correct wiring of gates: Inputs and outputs of logical/arithmetic gates align correctly.
	•	Permutation arguments: Columns of the proving table (representing wires or values) are consistent under a specified permutation.

This is achieved using the permutation polynomial  $Z(X)$  and constraints of the form:

$Z(\omega X) = Z(X) \cdot \frac{f_A(X)}{f_B(X)}$

where $\omega$ is a root of unity and $f_A(X)$, $f_B(X)$ are polynomials representing the original and permuted multisets.

The multiset check IOP is a cornerstone of many advanced proving systems, providing a robust, efficient way to handle consistency checks in a cryptographic system.