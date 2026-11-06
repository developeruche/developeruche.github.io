It is impossible to talk about arithmetic circuits without talking about `Polynomials`.

**Polynomials:** These are mathematical expressions that combine numbers (constants like 1, 2, 3) with variables (like x, y, z) using addition, multiplication and exponents (x², y³). Think of them as building-block towers, where the blocks are numbers and variables raised to powers.

**Arithmetic Circuit**: This is a model of how you compute these polynomials. It's like a set of instructions with wires and gates. The wires carry the numbers and variables, and the gates perform addition and multiplication to build the final polynomial expression. Just as real circuits perform calculations with electronic signals, arithmetic circuits perform computations on these mathematical elements.

Like Boolean circuits, arithmetic circuits rely on networks of wires and gates to perform computations. However, unlike Boolean circuits, which use logical operations (AND, OR), arithmetic circuits use arithmetic operations (addition, multiplication).

Wires carry data to be processed by the gates. In Boolean circuits, wires carry *bits*, while in arithmetic circuits they carry *elements of a field* (in zero-knowledge proofs, a finite field, so all arithmetic wraps around a modulus). Wires going into a gate contain the data to be processed by the gate. Wires directed out of a gate contain the result of the operation.

If a gate has no input wires, it is considered an input gate. An input gate contains the data to be processed by the circuit, which can be either a variable or a number. ([source](https://medium.com/web3studio/simple-explanations-of-arithmetic-circuits-and-zero-knowledge-proofs-806e59a79785))

A very detailed chapter on arithmetic circuits has been written by RareSkills: [Arithmetic Circuits for ZK](https://www.rareskills.io/post/arithmetic-circuit). Finish it before going on to the next page :)
