# R1CS to QAP

The Rank one constraint system is a very flexible way to represent an arithmetic circuit and to most proving systems, R1CS is the data structure in which the compute is presented to to the proving system. 

In this write-up, I will be exploring how to go from an arithmetic circuit (in polynomial form) to QAP.

Example;

$x^3 * x + 5 = 21$

_reducing this equation to a format that can be reduced to R1CS_

$a = x * x$
$b = a * x$
$out - 5 = b * x$

_this is what the witness would look like, recall the witness consists of the_

$w = [1, x, a, b, out]$
$w = [1,2,4,8,21]$

recall the R1CS format is as follows; 
$Cw=Aw⋅Bw$ 


to represent this in this format;

$C$ would be influenced by $[a,b,out-5]$ 
$A$ would be influenced by $[x,a,b]$
$B$ would be influenced by $[x]$

$$
C = 
\begin{pmatrix}
	0 & 0 & 1 & 0 & 0 \\
	0 & 0 & 0 & 1 & 0 \\
	-5 & 0 & 0 & 0 & 1 \\
\end{pmatrix}
$$
$$
A = 
\begin{pmatrix}
	0 & 1 & 0 & 0 & 0 \\
	0 & 0 & 1 & 0 & 0 \\
	0 & 0 & 0 & 1 & 0 \\
\end{pmatrix}
$$
$$
B = 
\begin{pmatrix}
	0 & 1 & 0 & 0 & 0 \\
	0 & 1 & 0 & 0 & 0 \\
	0 & 1 & 0 & 0 & 0 \\
\end{pmatrix}
$$

The R1CS representation of this would be given as;

$$\begin{pmatrix}
	0 & 0 & 1 & 0 & 0 \\
	0 & 0 & 0 & 1 & 0 \\
	-5 & 0 & 0 & 0 & 1 \\
\end{pmatrix}[1,2,4,8,21] = 
\begin{pmatrix}
	0 & 1 & 0 & 0 & 0 \\
	0 & 0 & 1 & 0 & 0 \\
	0 & 0 & 0 & 1 & 0 \\
\end{pmatrix}
[1,2,4,8,21]
∘
\begin{pmatrix}
	0 & 1 & 0 & 0 & 0 \\
	0 & 1 & 0 & 0 & 0 \\
	0 & 1 & 0 & 0 & 0 \\
\end{pmatrix}
[1,2,4,8,21]
$$

Now transforming this R1CS to its QAP representation.

In QAP we would be representing the R1CS structure using polynomials, but these polynomials completely implement the same logic done by the R1CS. 

In the construction used, the number of polynomials & their degree would depend on the length of the solution vector & the number of gates. The solution vector contains 5 elements, so we can construct 5 polynomials. Each gate contributes 1 point to each polynomial. We have 3 gates here, we get 3 points per polynomial. 3 points allows us to define a polynomial of maximum degree 2. So we can construct 5 polynomials each with a maximum degree of 2. So we can transform our matrices collectively into 5 polynomials, each of degree 2.

for the first column of C; 
$y = [0, 0, -5]$
$x=[1,2,3]$

$$
	poly_0 =  -\frac{5}{2} (x-2) (x-1) \\ = \\ -\frac{5 x^2}{2}+\frac{15 x}{2}-5 
$$

for the second column, there is no need to do this, because this would result in a Zero polynomial. 

for the 3rd column of C;
$y = [1, 0, 0]$
$x = [1, 2, 3]$

$$ poly_2 =  \left(\frac{x-2}{2}-1\right) (x-1)+1 \\ = \\ \frac{x^2}{2}-\frac{5 x}{2}+3  $$
for the 4th column of C; 
$y = [0,1,0]$
$x=[1,2,3]$

$$poly_3 =  (3-x) (x-1) \\ = \\ -x^2+4 x-3 $$

for the 5th column of C;
$y = [0,0,1]$
$x=[1,2,3]$

$$  poly_4 = \frac{1}{2} (x-2) (x-1) \\ = \\ \frac{x^2}{2}-\frac{3 x}{2}+1 $$

This construct the QAP representation of C, we would be making use of the co-efficient of these vectors;

$$
C = 
\begin{pmatrix}
	-5 & \frac{15}{2} & \frac{-5}{2}\\
	0 & 0 & 0\\
	3 & \frac{-5}{2} & \frac{1}{2}\\
	-3 & 4 & -1\\
	\frac{1}{2} & \frac{-3}{2} & \frac{1}{2}\\
\end{pmatrix}
$$
This is how `C` would be represented in QAP form;

But we are not done yet, there is just one more step, 

We have to multiply $C$ and $w$, $C$ is of the dimension of $3X5$  and $w$ is of the dimension of $5X1$ this would result in a matrix of dimension $3x1$, take this array as the co-efficient of a polynomial, that Polynomial is the QAP representation of $C$. 

It is truly epic seeing these huge matrices reduced to a single polynomial!

