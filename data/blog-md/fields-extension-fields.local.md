**Lecture Notes: Fields and Extension Fields in Cryptography**

**Date:** April 28, 2025
**Target Audience:** Cryptography Students

**1. Introduction: Why Fields Matter in Cryptography?**

Modern cryptography relies heavily on abstract algebra. While concepts like groups are fundamental (think Diffie-Hellman in $(\mathbb{Z}_p^*, \times)$), **fields** provide a richer structure essential for many algorithms.

* **Finite Fields (Galois Fields):** These are the cornerstone. Operations in finite fields are deterministic, efficient to compute, and possess properties that make cryptographic problems (like the Discrete Logarithm Problem) computationally hard.
* **Applications:**
    * **AES (Advanced Encryption Standard):** All byte operations (SubBytes, MixColumns) are defined over the finite field $GF(2^8)$.
    * **Elliptic Curve Cryptography (ECC):** Points on elliptic curves are defined over finite fields, typically prime fields $GF(p)$ or binary extension fields $GF(2^n)$. Curve arithmetic *is* field arithmetic.
    * **Diffie-Hellman Key Exchange:** Can be implemented over the multiplicative group of any finite field, $GF(q)^*$.
    * **Error-Correcting Codes:** While not strictly crypto, codes like Reed-Solomon are built on polynomial algebra over finite fields and have cryptographic applications (e.g., in some threshold schemes).

Understanding fields, especially finite fields and how to extend them, is crucial for analysing, implementing, and breaking cryptographic systems.

**2. Recap: Groups and Rings**

Before defining fields, let's briefly recall groups and rings.

* **Group:** A set $G$ with a binary operation $*$ ($ (G, *) $) satisfying:
    1.  Closure: $\forall a, b \in G, a * b \in G$.
    2.  Associativity: $\forall a, b, c \in G, (a * b) * c = a * (b * c)$.
    3.  Identity Element: $\exists e \in G$ such that $\forall a \in G, a * e = e * a = a$.
    4.  Inverse Element: $\forall a \in G, \exists a^{-1} \in G$ such that $a * a^{-1} = a^{-1} * a = e$.
    * *Abelian Group:* If the operation $*$ is also commutative ($a * b = b * a$).
    * *Examples:* $(\mathbb{Z}, +)$, $(\mathbb{Q}, +)$, $(\mathbb{R}, +)$, $(\mathbb{C}, +)$, $(\mathbb{Z}_n, +)$, $(\mathbb{Q}^*, \times)$, $(\mathbb{R}^*, \times)$, $(\mathbb{C}^*, \times)$, $(\mathbb{Z}_p^*, \times)$ for prime $p$.

* **Ring:** A set $R$ with two binary operations, addition ($+$) and multiplication ($\times$) ($ (R, +, \times) $), satisfying:
    1.  $(R, +)$ is an Abelian group (identity is $0$, inverse of $a$ is $-a$).
    2.  Multiplication is associative: $\forall a, b, c \in R, (a \times b) \times c = a \times (b \times c)$.
    3.  Distributive Laws: $\forall a, b, c \in R$, $a \times (b+c) = (a \times b) + (a \times c)$ and $(a+b) \times c = (a \times c) + (b \times c)$.
    * *Commutative Ring:* If multiplication is commutative ($a \times b = b \times a$).
    * *Ring with Unity:* If there exists a multiplicative identity $1 \in R$ such that $\forall a \in R, a \times 1 = 1 \times a = a$. (Note: $1 \neq 0$ is usually required).
    * *Integral Domain:* A commutative ring with unity ($1 \neq 0$) that has no zero divisors (i.e., if $a \times b = 0$, then $a=0$ or $b=0$).
    * *Examples:* $(\mathbb{Z}, +, \times)$ (Integral Domain), $(\mathbb{Q}, +, \times)$, $(\mathbb{R}, +, \times)$, $(\mathbb{C}, +, \times)$, $(\mathbb{Z}_n, +, \times)$ (Commutative ring with unity; Integral Domain only if $n$ is prime).

**3. Fields**

A field is essentially a structure where you can add, subtract, multiply, and divide (by non-zero elements).

* **Definition:** A set $F$ with two operations, addition ($+$) and multiplication ($\times$) ($ (F, +, \times) $), is a **field** if:
    1.  $(F, +, \times)$ is a commutative ring with unity $1$ (where $1 \neq 0$).
    2.  Every non-zero element has a multiplicative inverse: $\forall a \in F, a \neq 0, \exists a^{-1} \in F$ such that $a \times a^{-1} = a^{-1} \times a = 1$.

* **Equivalent Definition:** A set $F$ is a field if:
    1.  $(F, +)$ is an Abelian group (identity $0$).
    2.  $(F \setminus \{0\}, \times)$ is an Abelian group (identity $1$).
    3.  Multiplication distributes over addition.

* **Key Properties:**
    * Fields are always integral domains (no zero divisors). Proof: If $a \times b = 0$ and $a \neq 0$, then $a^{-1}$ exists. $a^{-1} \times (a \times b) = a^{-1} \times 0 \implies (a^{-1} \times a) \times b = 0 \implies 1 \times b = 0 \implies b = 0$.
* **Examples:** $(\mathbb{Q}, +, \times)$, $(\mathbb{R}, +, \times)$, $(\mathbb{C}, +, \times)$.
* **Non-Examples:** $(\mathbb{Z}, +, \times)$ (not all non-zero elements have multiplicative inverses, e.g., $2^{-1} = 1/2 \notin \mathbb{Z}$), $(\mathbb{Z}_n, +, \times)$ for composite $n$ (elements corresponding to factors of $n$ lack multiplicative inverses, and there are zero divisors).

**4. Finite Fields (Galois Fields)**

Fields with a finite number of elements are crucial in cryptography.

* **Definition:** A field with a finite number of elements is called a **finite field** or **Galois Field**.
* **Notation:** $GF(q)$ or $\mathbb{F}_q$, where $q$ is the number of elements (the **order** or **size** of the field).

* **Theorem:** A finite field $GF(q)$ exists if and only if $q$ is a prime power ($q = p^n$ for some prime $p$ and integer $n \ge 1$).
    * $p$ is the **characteristic** of the field.
    * For any prime power $q$, there is essentially only one field of order $q$ (they are all isomorphic).

**4.1. Prime Fields: $GF(p)$ or $\mathbb{F}_p$**

The simplest finite fields occur when $n=1$, so $q=p$ (a prime).

* **Construction:** The ring $(\mathbb{Z}_p, +, \times)$ (integers modulo $p$) forms a field $GF(p)$.
    * Set: $\{0, 1, 2, \dots, p-1\}$.
    * Operations: Addition and multiplication are performed modulo $p$.
* **Why is $\mathbb{Z}_p$ a field?**
    * $(\mathbb{Z}_p, +)$ is an Abelian group.
    * $(\mathbb{Z}_p, +, \times)$ is a commutative ring with unity $1$.
    * **Existence of Multiplicative Inverses:** For any $a \in \{1, 2, \dots, p-1\}$, does $a^{-1} \pmod{p}$ exist? Yes, because $p$ is prime, $\gcd(a, p) = 1$. By the Extended Euclidean Algorithm, we can find integers $x, y$ such that $ax + py = \gcd(a, p) = 1$. Taking this equation modulo $p$, we get $ax \equiv 1 \pmod{p}$. Therefore, $x \pmod{p}$ is the multiplicative inverse $a^{-1}$.
* **Example: $GF(5)$ or $\mathbb{F}_5$**
    * Elements: $\{0, 1, 2, 3, 4\}$.
    * Operations: Modulo 5.
    * Addition Table (mod 5):
        ```
        + | 0 1 2 3 4
        --|---------
        0 | 0 1 2 3 4
        1 | 1 2 3 4 0
        2 | 2 3 4 0 1
        3 | 3 4 0 1 2
        4 | 4 0 1 2 3
        ```
    * Multiplication Table (mod 5):
        ```
        x | 0 1 2 3 4
        --|---------
        0 | 0 0 0 0 0
        1 | 0 1 2 3 4
        2 | 0 2 4 1 3  (e.g., 2x3=6=1 mod 5; 2x4=8=3 mod 5)
        3 | 0 3 1 4 2  (e.g., 3x3=9=4 mod 5)
        4 | 0 4 3 2 1  (e.g., 4x4=16=1 mod 5)
        ```
    * Inverses: $1^{-1}=1, 2^{-1}=3, 3^{-1}=2, 4^{-1}=4$. Every non-zero element has an inverse.

**5. Extension Fields: $GF(p^n)$ or $\mathbb{F}_{p^n}$ for $n > 1$**

How do we construct fields with $p^n$ elements when $n > 1$? We can't just use $\mathbb{Z}_{p^n}$ because it's not a field (it has zero divisors when $n>1$). We need a different approach using polynomial rings.

* **Analogy:** Think about constructing the complex numbers $\mathbb{C}$ from the real numbers $\mathbb{R}$. $\mathbb{R}$ is a field. We want solutions to $x^2 + 1 = 0$, which has no solution in $\mathbb{R}$. We introduce a symbol $i$ such that $i^2 = -1$. Then $\mathbb{C} = \{ a + bi \mid a, b \in \mathbb{R} \}$. Operations are defined using the rule $i^2 = -1$. $x^2+1$ is *irreducible* over $\mathbb{R}$.

* **General Construction using Polynomials:**
    1.  **Base Field:** Start with a prime field $GF(p) = \mathbb{F}_p$.
    2.  **Polynomial Ring:** Consider the ring of polynomials with coefficients from $GF(p)$, denoted $GF(p)[x]$ or $\mathbb{F}_p[x]$.
        * Example elements for $\mathbb{F}_2[x]$: $0, 1, x, x+1, x^2, x^2+1, x^2+x, x^2+x+1, \dots$
    3.  **Irreducible Polynomial:** Find a polynomial $m(x) \in GF(p)[x]$ of degree $n$ that is **irreducible** over $GF(p)$.
        * *Irreducible:* $m(x)$ cannot be factored into a product of two polynomials in $GF(p)[x]$ both having degree less than $n$ (and greater than 0). It's the polynomial analog of a prime number.
        * *Existence:* Irreducible polynomials of every degree $n \ge 1$ exist over any finite field $GF(p)$. Finding them can be computationally intensive for large $n$.
    4.  **Construct the Field:** The extension field $GF(p^n)$ is constructed as the set of polynomials in $GF(p)[x]$ modulo the irreducible polynomial $m(x)$.
        * $GF(p^n) \cong GF(p)[x] / \langle m(x) \rangle$
        * The elements of this field can be represented as polynomials of degree strictly less than $n$:
            $F = \{ a_{n-1}x^{n-1} + a_{n-2}x^{n-2} + \dots + a_1x + a_0 \mid a_i \in GF(p) \}$
        * There are $p$ choices for each of the $n$ coefficients ($a_0, \dots, a_{n-1}$), giving $p^n$ distinct elements in total.
    5.  **Operations in $GF(p^n)$:**
        * **Addition:** Polynomial addition, where coefficients are added modulo $p$. The degree of the result is always $< n$.
            * Example: In $GF(2^3)$ (using some $m(x)$ of degree 3), $(x^2+1) + (x^2+x) = (1+1)x^2 + x + 1 = 0x^2 + x + 1 = x+1$. (Coeffs mod 2)
        * **Multiplication:** Polynomial multiplication, followed by taking the remainder when divided by the irreducible polynomial $m(x)$. The coefficients are handled modulo $p$.
            * Let $a(x), b(x) \in GF(p^n)$. Compute $c(x) = a(x) \times b(x)$ using standard polynomial multiplication (with coefficients mod $p$).
            * The result is $a(x) \times b(x) \pmod{m(x)}$. This is the remainder $r(x)$ when $c(x)$ is divided by $m(x)$, so $c(x) = q(x)m(x) + r(x)$ where $\deg(r(x)) < \deg(m(x)) = n$.
        * **Multiplicative Inverse:** For a non-zero element $a(x)$, its inverse $a(x)^{-1}$ can be found using the **Extended Euclidean Algorithm for Polynomials** over $GF(p)$, finding $s(x), t(x)$ such that $a(x)s(x) + m(x)t(x) = \gcd(a(x), m(x))$. Since $m(x)$ is irreducible and $a(x) \neq 0$ (and $\deg(a(x)) < n$), $\gcd(a(x), m(x)) = 1$ (or a non-zero constant in $GF(p)$, which has an inverse). Then $a(x)s(x) \equiv \gcd \pmod{m(x)}$, and $s(x) \times (\gcd^{-1})$ is the inverse of $a(x)$ modulo $m(x)$.

* **Example: Constructing $GF(2^3) = \mathbb{F}_8$**
    1.  Base Field: $GF(2) = \mathbb{F}_2 = \{0, 1\}$. (Addition is XOR, Multiplication is AND).
    2.  Polynomial Ring: $\mathbb{F}_2[x]$.
    3.  Irreducible Polynomial: We need a degree 3 irreducible polynomial. Let's test $m(x) = x^3 + x + 1$.
        * Does it have roots in $\mathbb{F}_2$? $m(0) = 0^3+0+1 = 1 \neq 0$. $m(1) = 1^3+1+1 = 1 \neq 0$. Since it's degree 3 and has no roots, it must be irreducible over $\mathbb{F}_2$. (If a polynomial of degree 2 or 3 is reducible, it must have a linear factor, hence a root).
    4.  Construct the Field: $GF(2^3) \cong \mathbb{F}_2[x] / \langle x^3 + x + 1 \rangle$.
    5.  Elements: Polynomials of degree < 3 with coefficients in $\mathbb{F}_2$.
        $\{0, 1, x, x+1, x^2, x^2+1, x^2+x, x^2+x+1\}$. There are $2^3 = 8$ elements.
        *Often represented by coefficient vectors: 000, 001, 010, 011, 100, 101, 110, 111.*
    6.  Operations: Modulo $x^3+x+1$, coefficients modulo 2.
        * **Addition:** $(x^2+1) + (x^2+x) = (1+1)x^2 + x + 1 = x+1$. (Same as XORing coefficient vectors: $101 \oplus 110 = 011$).
        * **Multiplication:** Let's compute $(x+1) \times (x^2+1)$.
            * $(x+1)(x^2+1) = x(x^2+1) + 1(x^2+1) = x^3+x+x^2+1 = x^3+x^2+x+1$.
            * Now reduce modulo $m(x) = x^3+x+1$. We use the relation $x^3+x+1 \equiv 0 \implies x^3 \equiv -x-1 \equiv x+1 \pmod{2}$.
            * Substitute $x^3$: $(x+1) + x^2 + x + 1 = x^2 + (1+1)x + (1+1) = x^2$.
            * Alternatively, use polynomial long division: $(x^3+x^2+x+1) \div (x^3+x+1)$. Quotient is 1, remainder is $x^2$.
            * So, $(x+1) \times (x^2+1) = x^2$ in $GF(2^3)$.
        * **Inverse:** Find the inverse of $x$. Using Extended Euclidean Algorithm for $x$ and $m(x)=x^3+x+1$ over $\mathbb{F}_2$.
            $x^3+x+1 = (x^2+1) \cdot x + 1$.
            Rearranging: $1 = (x^3+x+1) - (x^2+1)x$.
            Taking modulo $m(x)$: $1 \equiv -(x^2+1)x \pmod{m(x)}$.
            Since $-1 \equiv 1 \pmod 2$, we have $1 \equiv (x^2+1)x \pmod{m(x)}$.
            Thus, $x^{-1} = x^2+1$. Let's check: $x \times (x^2+1) = x^3+x$. Since $x^3 \equiv x+1 \pmod{m(x)}$, this is $(x+1)+x = (1+1)x + 1 = 1$. Correct.

**6. Cryptographic Relevance Revisited**

* **AES ($GF(2^8)$):** Uses the field $\mathbb{F}_{2^8}$ constructed using the irreducible polynomial $m(x) = x^8 + x^4 + x^3 + x + 1$.
    * Bytes are treated as elements of this field (polynomials of degree < 8).
    * **SubBytes:** Applies a mapping $y = b^{-1} + c$ (where $b=0$ maps to $c$), which involves finding multiplicative inverses in $GF(2^8)$.
    * **MixColumns:** Involves matrix multiplication where the entries are elements of $GF(2^8)$, requiring field addition and multiplication.
* **ECC ($GF(p)$ or $GF(2^n)$):** Elliptic curve $y^2 = x^3 + ax + b$ (or similar forms).
    * The coordinates $(x, y)$ of points on the curve, and the coefficients $a, b$, are elements of a finite field $GF(q)$.
    * The point addition formulas involve field addition, subtraction, multiplication, and division (inverse). The security relies on the difficulty of the Elliptic Curve Discrete Logarithm Problem (ECDLP) in the group of points over the finite field.
* **Finite Field DLP:** The difficulty of finding $k$ given $g$ and $y=g^k$ in $GF(q)^*$ underlies the security of Diffie-Hellman, DSA, and ElGamal when implemented over finite fields. Larger fields make the DLP harder. Extension fields $GF(p^n)$ offer flexibility in size and structure.

**7. Summary**

* Fields provide algebraic structures with addition, subtraction, multiplication, and division (by non-zero elements).
* Finite fields (Galois Fields) $GF(q)$ exist only when $q = p^n$ (prime power).
* Prime fields $GF(p)$ are constructed using integers modulo $p$. Operations are modular arithmetic. Finding inverses uses the Extended Euclidean Algorithm.
* Extension fields $GF(p^n)$ for $n>1$ are constructed using polynomials over $GF(p)$ modulo an irreducible polynomial $m(x)$ of degree $n$.
    * Elements are polynomials of degree $< n$.
    * Operations involve polynomial arithmetic (coefficients mod $p$) followed by reduction modulo $m(x)$. Finding inverses uses the Extended Euclidean Algorithm for polynomials.
* Finite fields, especially $GF(p)$ and $GF(2^n)$, are fundamental building blocks for symmetric ciphers (AES), asymmetric ciphers (ECC), and key exchange protocols (Diffie-Hellman). Their properties enable both efficient computation and cryptographic hardness.

**Further Topics:** Finding irreducible polynomials, polynomial factorization over finite fields, primitive elements (generators of the multiplicative group $GF(q)^*$), specific arithmetic optimizations in $GF(2^n)$.
