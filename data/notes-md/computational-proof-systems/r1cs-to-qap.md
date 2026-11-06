This section dives into how a problem represented in `R1CS` can be transformed into a `QAP`.

Explore these chapters of the RareSkills book:

1. [R1CS](https://www.rareskills.io/post/rank-1-constraint-system)
2. [QAP](https://www.rareskills.io/post/quadratic-arithmetic-program)
3. [R1CS to QAP](https://rareskills.io/post/r1cs-to-qap)

Let's play with a quick example of transforming R1CS to QAP.

The rank-one constraint system is a very flexible way to represent an arithmetic circuit, and for many proving systems, R1CS is the data structure in which the computation is presented to the proving system.

### The example

We will go from this equation, with the solution $x = 2$, to a QAP:

$$x^3 \cdot x + 5 = 21$$

*Reducing this equation to a form that fits R1CS, where each line has one multiplication:*

$$a = x \cdot x$$

$$b = a \cdot x$$

$$out - 5 = b \cdot x$$

*This is what the witness looks like:*

$$w = [1, x, a, b, out] = [1, 2, 4, 8, 21]$$

### R1CS

Recall the R1CS format, where $\circ$ is element-wise multiplication:

$$Cw = Aw \circ Bw$$

Each constraint is one row. $C$ encodes the left-hand sides $[a,\ b,\ out - 5]$, $A$ encodes the first factors $[x,\ a,\ b]$, and $B$ encodes the second factors $[x,\ x,\ x]$:

$$
C =
\begin{pmatrix}
0 & 0 & 1 & 0 & 0 \\
0 & 0 & 0 & 1 & 0 \\
-5 & 0 & 0 & 0 & 1
\end{pmatrix}
\quad
A =
\begin{pmatrix}
0 & 1 & 0 & 0 & 0 \\
0 & 0 & 1 & 0 & 0 \\
0 & 0 & 0 & 1 & 0
\end{pmatrix}
\quad
B =
\begin{pmatrix}
0 & 1 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 & 0 \\
0 & 1 & 0 & 0 & 0
\end{pmatrix}
$$

Multiplying each matrix by $w$ gives $Cw = [4, 8, 16]$, $Aw = [2, 4, 8]$ and $Bw = [2, 2, 2]$, and indeed $4 = 2 \cdot 2$, $8 = 4 \cdot 2$ and $16 = 8 \cdot 2$.

Note that $out = 21$ is a *public input*. These three constraints hold for any $x$ with $out = x^4 + 5$ (for example $x = 3$, $out = 86$). What pins the statement to 21 is that the verifier supplies that value itself.

### From R1CS to QAP

In a QAP, we represent the R1CS structure using polynomials that implement exactly the same logic.

The number of polynomials and their degree depend on the length of the witness and the number of constraints. The witness has 5 elements, so each matrix gives 5 polynomials, one per column. Each constraint contributes 1 point to each polynomial. We have 3 constraints, so we get 3 points per polynomial, which define a polynomial of degree at most 2. We choose the evaluation points $x = 1, 2, 3$, one per constraint.

Starting with $C$, we interpolate each column:

For the 1st column of $C$, $y = [0, 0, -5]$ at $x = [1, 2, 3]$:

$$c_0(x) = -\frac{5}{2}(x-1)(x-2) = -\frac{5}{2}x^2 + \frac{15}{2}x - 5$$

For the 2nd column, all values are zero, so $c_1(x) = 0$.

For the 3rd column, $y = [1, 0, 0]$:

$$c_2(x) = \frac{1}{2}(x-2)(x-3) = \frac{1}{2}x^2 - \frac{5}{2}x + 3$$

For the 4th column, $y = [0, 1, 0]$:

$$c_3(x) = -(x-1)(x-3) = -x^2 + 4x - 3$$

For the 5th column, $y = [0, 0, 1]$:

$$c_4(x) = \frac{1}{2}(x-1)(x-2) = \frac{1}{2}x^2 - \frac{3}{2}x + 1$$

Writing the coefficients as a matrix, one row per polynomial, with columns for $1$, $x$ and $x^2$:

$$
C_{\text{poly}} =
\begin{pmatrix}
-5 & \frac{15}{2} & -\frac{5}{2} \\
0 & 0 & 0 \\
3 & -\frac{5}{2} & \frac{1}{2} \\
-3 & 4 & -1 \\
1 & -\frac{3}{2} & \frac{1}{2}
\end{pmatrix}
$$

There is one more step: combining these polynomials with the witness. $w^T$ has dimension $1 \times 5$ and $C_{\text{poly}}$ has dimension $5 \times 3$, so $w^T C_{\text{poly}}$ has dimension $1 \times 3$. That row holds the coefficients of a single polynomial, $C(x) = \sum_i w_i\, c_i(x)$:

$$C(x) = 1 \cdot c_0(x) + 2 \cdot c_1(x) + 4 \cdot c_2(x) + 8 \cdot c_3(x) + 21 \cdot c_4(x) = 2x^2 - 2x + 4$$

As a check, this passes through the entries of $Cw$: $C(1) = 4$, $C(2) = 8$, $C(3) = 16$.

Doing the same for the other two matrices gives:

$$A(x) = x^2 - x + 2 \qquad B(x) = 2$$

Again, $A(1), A(2), A(3) = 2, 4, 8$ and $B$ is $2$ everywhere, matching $Aw$ and $Bw$.

### The QAP check

All three constraints hold exactly when $A(x)B(x) - C(x)$ is zero at $x = 1, 2, 3$, which means it is divisible by the target polynomial $t(x) = (x-1)(x-2)(x-3)$. So the whole R1CS collapses into one polynomial identity:

$$A(x)B(x) - C(x) = h(x)\,t(x)$$

In this example $A(x)B(x) = 2x^2 - 2x + 4 = C(x)$, so the left side is exactly zero and $h(x) = 0$. That is special to this small example: $B(x)$ happens to be a constant, so the product stays at degree 2. In general the left side is a non-zero polynomial and $h(x)$ is non-zero.

A wrong witness breaks the identity. Take $out = 22$ with everything else unchanged, so $w = [1, 2, 4, 8, 22]$. Then $C(x)$ becomes $\frac{5}{2}x^2 - \frac{7}{2}x + 5$, and $A(x)B(x) - C(x)$ equals $-1$ at $x = 3$. It does not vanish at all three points, so no $h(x)$ exists.

It is truly epic seeing these huge matrices reduced to a single polynomial identity!

In a real proof system all of this happens over a finite field, so a fraction like $\frac{5}{2}$ means $5$ times the field inverse of $2$.
