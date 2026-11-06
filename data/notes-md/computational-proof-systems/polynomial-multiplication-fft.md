Here is a brief explanation of polynomial multiplication in evaluation form using the Fast Fourier Transform (FFT).

Given two polynomials in coefficient form:

$$f(x) = a_0 + a_1x + a_2x^2 + \dots + a_nx^n$$

$$g(x) = b_0 + b_1x + b_2x^2 + \dots + b_mx^m$$

their product has degree $n + m$, so it is uniquely determined by its values at $n + m + 1$ distinct points. Let $N$ be a power of two with $N \geq n + m + 1$.

1. **Convert to evaluation form using the FFT:**
   - Evaluate $f(x)$ and $g(x)$ at the $N$-th roots of unity.
   - This converts each polynomial from coefficient form to evaluation form, where it is represented by its values at those points.
2. **Multiply in evaluation form:**
   - Multiply the corresponding values of $f(x)$ and $g(x)$ at each point.
   - This pointwise multiplication takes only $O(N)$ operations.
3. **Convert the result back to coefficient form using the inverse FFT:**
   - Apply the inverse FFT to the multiplied values to obtain the coefficients of the product.

Each transform costs $O(N \log N)$, so the whole method is $O(N \log N)$, compared with $O(nm)$ for multiplying coefficients directly. The saving grows with the degree, which is what makes this method practical for high-degree polynomials.

In zero-knowledge proofs, this runs over a finite field rather than the complex numbers, where it is also called the Number Theoretic Transform (NTT). The field must contain the needed roots of unity, meaning $N$ must divide $p - 1$ for a prime field of size $p$. This is why proof systems favour fields whose $p - 1$ is divisible by a large power of two.
