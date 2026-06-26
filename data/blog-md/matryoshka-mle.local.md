# The Matryoshka MLE Algorithm

In modern cryptography, particularly within succinct proof systems like GKR (Goldwasser–Kalai–Rothblum), the efficient evaluation of polynomials is crucial. A fundamental operation in this context is the computation of the **Multilinear Extension (MLE)** of a Boolean function.

For a given Boolean function $f: \{0,1\}^m \to \mathbb{F}$ that maps an $m$-bit input to a value in a finite field $\mathbb{F}$, its multilinear extension, denoted $\tilde{f}$, is the unique multivariate polynomial that agrees with $f$ on all corners of the Boolean hypercube $\{0,1\}^m$ and is linear in each of its variables.

The primary challenge is evaluating this extension $\tilde{f}$ at an arbitrary point $r = (r_1, \dots, r_m) \in \mathbb{F}^m$. The standard definition for this evaluation is:

$$\tilde{f}(r) = \sum_{b \in \{0,1\}^m} f(b) \cdot eq(r, b)$$

where $eq(r, b)$ is a function that equals 1 if $r=b$ (for $r, b \in \{0,1\}^m$) and smoothly extends this property to the whole field. A common form is $eq(r, b) = \prod_{i=1}^m (r_i b_i + (1-r_i)(1-b_i))$. Direct computation using this formula requires a summation over all $2^m$ points in the Boolean hypercube, which is computationally infeasible for large $m$.

The **Matryoshka MLE algorithm** provides a significant optimization for this task. Drawing its name from the recursive structure of Russian nesting dolls, the algorithm evaluates $\tilde{f}(r)$ iteratively. It peels off one variable at a time, reducing the problem's size by half at each step. This method is particularly effective in protocols like GKR, forming a core component of modern zk-SNARKs as detailed in works like *“Scalable Zero Knowledge via Cycles of Elliptic Curves”*.


### The Algorithm

The algorithm computes $\tilde{f}(r)$ by sequentially binding the variables $r_1, \dots, r_m$. We start with the original function $f$ over $m$ variables and iteratively produce new functions over fewer variables, until we are left with a single scalar value, which is the final evaluation.

1.  **Initialization**: Define $f_0 := f$. This function $f_0$ takes $m$ Boolean inputs.

2.  **Iterative Computation**: For $i = 1, \dots, m$, compute the function $f_i: \{0,1\}^{m-i} \to \mathbb{F}$ as follows:
    $$f_i(b_{i+1}, \dots, b_m) = \sum_{b_i \in \{0,1\}} eq_1(r_i, b_i) \cdot f_{i-1}(b_i, b_{i+1}, \dots, b_m)$$
    where $eq_1(r_i, b_i) = r_i b_i + (1-r_i)(1-b_i)$. Each step $i$ eliminates one variable, and the computation requires $O(2^{m-i})$ arithmetic operations.

3.  **Output**: After $m$ steps, we compute $f_m$. This is a function of zero variables—a single scalar value in the field $\mathbb{F}$. This scalar is the final result, $\tilde{f}(r)$.

#### Implementation Note

A key observation for implementation is that the summation in Step 2 can be simplified. For any set of inputs $(b_{i+1}, \dots, b_m)$, the computation becomes:
$$f_i(\dots) = eq_1(r_i, 0) \cdot f_{i-1}(0, \dots) + eq_1(r_i, 1) \cdot f_{i-1}(1, \dots)$$
Since $eq_1(r_i, 0) = 1-r_i$ and $eq_1(r_i, 1) = r_i$, this can be rewritten as:
$$f_i(\dots) = (1-r_i) \cdot f_{i-1}(0, \dots) + r_i \cdot f_{i-1}(1, \dots)$$
This can be further rearranged to:
$$f_i(\dots) = f_{i-1}(0, \dots) + r_i(f_{i-1}(1, \dots) - f_{i-1}(0, \dots))$$
This formulation is efficient as it requires only one multiplication and two additions for each output of $f_i$. Therefore, computing all $2^{m-i}$ values of $f_i$ takes exactly $2^{m-i}$ multiplications and $2 \cdot 2^{m-i}$ additions.




## Example [Using an example to explain this further]

_unforunately, I am quite lazy, we would be using a 3varible ploy for this example_

### 🎯 Goal:

Given a Boolean function $f: \{0,1\}^3 \to \{0,1\}$, and a point $r = (r_1, r_2, r_3) \in \mathbb{F}^3$, compute the **multilinear extension** $\hat{f}(r) \in \mathbb{F}$.


### 🔧 Setup:

Let’s define:

* The field: $\mathbb{F} = \mathbb{F}_7$ (integers mod 7)
* Function $f$ defined over the domain $\{0,1\}^3$, specified as a truth table:

| $x_1$ | $x_2$ | $x_3$ | $f(x_1, x_2, x_3)$ |
| ----- | ----- | ----- | ------------------ |
| 0     | 0     | 0     | 1                  |
| 0     | 0     | 1     | 0                  |
| 0     | 1     | 0     | 1                  |
| 0     | 1     | 1     | 1                  |
| 1     | 0     | 0     | 0                  |
| 1     | 0     | 1     | 1                  |
| 1     | 1     | 0     | 0                  |
| 1     | 1     | 1     | 1                  |

Let:

$$
r = (r_1, r_2, r_3) = (2, 3, 6) \in \mathbb{F}_7^3
$$



### 📌 Define `eq1(r, b) = (1 - r) * (1 - b) + r * b`

This is just the **linear polynomial** that evaluates to:

* `1` when $b = r$
* `0` when $b \neq r$
  Over domain $\{0,1\}$, it's:

$$
\text{eq1}(r, b) = (1 - b)(1 - r) + b \cdot r
$$

Let’s compute `eq1` for all possible `b ∈ {0,1}` and for each `r_i`:

| b | eq1(r₁ = 2, b) | eq1(r₂ = 3, b) | eq1(r₃ = 6, b) |
| - | -------------- | -------------- | -------------- |
| 0 | (1)(-1) = 6    | (1)(-2) = 5    | (1)(-5) = 2    |
| 1 | (1)(2) = 2     | (1)(3) = 3     | (1)(6) = 6     |

(Note: All values mod 7)

So:

* $\text{eq1}(2,0) = 6, \quad \text{eq1}(2,1) = 2$
* $\text{eq1}(3,0) = 5, \quad \text{eq1}(3,1) = 3$
* $\text{eq1}(6,0) = 2, \quad \text{eq1}(6,1) = 6$



### 🔄 Matryoshka MLE Evaluation Algorithm

We define:

$$
f_0(x_1,x_2,x_3) = f(x_1,x_2,x_3) \in \{0,1\}
$$

We now compute recursively:



#### 🔹 Step 1: Compute $f_1(x_2, x_3)$

$$
f_1(x_2, x_3) = \sum_{x_1 \in \{0,1\}} \text{eq1}(r_1, x_1) \cdot f_0(x_1, x_2, x_3)
$$

For all 4 combinations of $(x_2, x_3) \in \{0,1\}^2$, we compute:

| $x_2$ | $x_3$ | $f_0(0,x_2,x_3)$ | $f_0(1,x_2,x_3)$ | $f_1(x_2,x_3)$          |
| ----- | ----- | ---------------- | ---------------- | ----------------------- |
| 0     | 0     | 1                | 0                | $6·1 + 2·0 = 6$         |
| 0     | 1     | 0                | 1                | $6·0 + 2·1 = 2$         |
| 1     | 0     | 1                | 0                | $6·1 + 2·0 = 6$         |
| 1     | 1     | 1                | 1                | $6·1 + 2·1 = 6+2=8 ≡ 1$ |

(Working mod 7: 8 ≡ 1)

So:

| $x_2$ | $x_3$ | $f_1(x_2, x_3)$ |
| ----- | ----- | --------------- |
| 0     | 0     | 6               |
| 0     | 1     | 2               |
| 1     | 0     | 6               |
| 1     | 1     | 1               |



#### 🔹 Step 2: Compute $f_2(x_3)$

$$
f_2(x_3) = \sum_{x_2 \in \{0,1\}} \text{eq1}(r_2, x_2) \cdot f_1(x_2, x_3)
$$

For each $x_3$:

| $x_3$ | $f_1(0,x_3)$ | $f_1(1,x_3)$ | $f_2(x_3)$                     |
| ----- | ------------ | ------------ | ------------------------------ |
| 0     | 6            | 6            | $5·6 + 3·6 = 30 + 18 = 48 ≡ 6$ |
| 1     | 2            | 1            | $5·2 + 3·1 = 10 + 3 = 13 ≡ 6$  |


#### 🔹 Step 3: Compute final output $f_3 = \hat{f}(r)$

$$
f_3 = \sum_{x_3 \in \{0,1\}} \text{eq1}(r_3, x_3) \cdot f_2(x_3)
$$

$$
= \text{eq1}(6, 0) · 6 + \text{eq1}(6, 1) · 6 = 2·6 + 6·6 = 12 + 36 = 48 ≡ 6 \mod 7
$$



#### ✅ Final Result:

$$
\hat{f}(r_1 = 2, r_2 = 3, r_3 = 6) = \boxed{6}
$$




### 🔍 The Optimization Trick

Recall that:

$$
eq1(r_i, b_i) = 
\begin{cases}
1 - r_i & \text{if } b_i = 0 \\
r_i & \text{if } b_i = 1
\end{cases}
$$

So we compute:

$$
\sum_{b_i \in \{0,1\}} eq1(r_i, b_i) \cdot f_{i-1}(b_i, \ldots)
= (1 - r_i) \cdot f_{i-1}(0, \ldots) + r_i \cdot f_{i-1}(1, \ldots)
$$



### 🧠 But Here's the Trick:

The authors observe that you can **compute this expression** via the **identity**:

$$
eq1(r_i, b_i) \cdot f_{i-1}(b_i, \ldots) = 
f_{i-1}(0, \ldots) + r_i \cdot \left(f_{i-1}(1, \ldots) - f_{i-1}(0, \ldots)\right)
$$

This reduces the number of multiplications because:

* Instead of **computing both $f_{i-1}(0,\ldots) \cdot (1 - r_i)$** and **$f_{i-1}(1,\ldots) \cdot r_i$** (2 multiplications),
* You compute one multiplication:

  $$
  r_i \cdot \left(f_{i-1}(1,\ldots) - f_{i-1}(0,\ldots)\right)
  $$
* And one addition:

  $$
      + f_{i-1}(0,\ldots)
  $$

Which saves one multiplication per pair.


### 🔢 For Dimension $m$, This Yields:

* $2^{m-1}$ such **pairs** at level $i$,
* So $2^{m-1}$ additions and only $2^{m-1}$ **single** multiplications,
* Totaling $2^{m-1}$ multiplications at level $i$ instead of $2^m$.

This is the source of the **efficiency** in Matryoshka:
At level $i$, you do only $2^{m - i}$ multiplications, leading to the total:

$$
\sum_{i=1}^m 2^{m - i} = 2^m - 1 \quad \text{(total multiplications)}
$$

Compared to the naïve method, which uses roughly $m \cdot 2^m$ multiplications.


I think this trick is fundalmental to the performance gain.





### Playing with this trick with same example


We're given:

* **Field**: $\mathbb{F}_7$
* **Function**: $f: \{0,1\}^3 \to \{0,1\}$ with:

| $x_1$ | $x_2$ | $x_3$ | $f(x_1,x_2,x_3)$ |
| ----- | ----- | ----- | ---------------- |
| 0     | 0     | 0     | 1                |
| 0     | 0     | 1     | 0                |
| 0     | 1     | 0     | 1                |
| 0     | 1     | 1     | 1                |
| 1     | 0     | 0     | 0                |
| 1     | 0     | 1     | 1                |
| 1     | 1     | 0     | 0                |
| 1     | 1     | 1     | 1                |

* **Evaluation point**: $r = (r_1, r_2, r_3) = (2, 3, 6) \in \mathbb{F}_7^3$

### 🔹 Step 1: Eliminate $x_1$

We define:

$$
f_1(x_2,x_3) = f(0,x_2,x_3) + r_1 \cdot (f(1,x_2,x_3) - f(0,x_2,x_3)) \mod 7
$$

Using $r_1 = 2$

| $x_2$ | $x_3$ | $f(0,x_2,x_3)$ | $f(1,x_2,x_3)$ | $f_1(x_2,x_3)$                              |
| ----- | ----- | -------------- | -------------- | ------------------------------------------- |
| 0     | 0     | 1              | 0              | $1 + 2 \cdot (0 - 1) = 1 - 2 = -1 \equiv 6$ |
| 0     | 1     | 0              | 1              | $0 + 2 \cdot (1 - 0) = 2$                  |
| 1     | 0     | 1              | 0              | $1 + 2 \cdot (-1) = -1 \equiv 6$           |
| 1     | 1     | 1              | 1              | $1 + 2 \cdot (0) = 1$                       |

So:

* $f_1(0,0) = 6$
* $f_1(0,1) = 2$
* $f_1(1,0) = 6$
* $f_1(1,1) = 1$


### 🔹 Step 2: Eliminate $x_2$

Use:

$$
f_2(x_3) = f_1(0,x_3) + r_2 \cdot (f_1(1,x_3) - f_1(0,x_3)) \mod 7
$$

with $r_2 = 3$

| $x_3$ | $f_1(0,x_3)$ | $f_1(1,x_3)$ | $f_2(x_3)$                           |
| ----- | ------------ | ------------ | ------------------------------------ |
| 0     | 6            | 6            | $6 + 3(0) = 6$                       |
| 1     | 2            | 1            | $2 + 3(1 - 2) = 2 - 3 = -1 \equiv 6$ |



#### 🔹 Step 3: Eliminate $x_3$

Use:

$$
f_3 = f_2(0) + r_3 \cdot (f_2(1) - f_2(0)) \mod 7
$$

with $r_3 = 6$:

$$
f_3 = 6 + 6 \cdot (6 - 6) = 6 + 6 \cdot 0 = 6
$$

### ✅ Final Result

$$
\hat{f}(2,3,6) = 6 \in \mathbb{F}_7
$$


### 🔢 Multiplication Count

Each use of the trick requires **1 multiplication** per step for each subcase (pair of values).

* Step 1: 4 multiplications (for each of 4 $(x_2, x_3)$ pairs)
* Step 2: 2 multiplications (one per $x_3$)
* Step 3: 1 multiplication

**Total: 7 multiplications** — again, matching the optimal $2^3 - 1 = 7$ multiplications.




#### Reference
https://eccc.weizmann.ac.il/report/2025/090/ [page 9]
https://github.com/tcoratger/whir-p3/issues/215