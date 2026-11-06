Exploring the GKR prover and verifier, and creating a SNARK from this interactive protocol, using a polynomial commitment scheme to make it succinct.

### Understanding the GKR protocol

The GKR protocol, by Goldwasser, Kalai and Rothblum, proves that a layered arithmetic circuit was evaluated correctly. It works from the output layer back to the inputs. Let $w_i$ be the multilinear extension of the values at layer $i$, and let $add_i$ and $mul_i$ be the multilinear extensions of the wiring: $add_i(z, b, c)$ is 1 when gate $z$ of layer $i$ adds gates $b$ and $c$ of layer $i+1$. Then each layer can be written as a sum over the layer below:

$$w_i(z) = \sum_{b, c \in \{0,1\}^{k}} add_i(z, b, c)\,\big(w_{i+1}(b) + w_{i+1}(c)\big) + mul_i(z, b, c)\, w_{i+1}(b)\, w_{i+1}(c)$$

That is exactly the form the [sum-check protocol](/notes/cryptography-zkp/computational-proof-systems/sum-check-protocol/) handles. Each run reduces a claim about $w_i$ to claims about $w_{i+1}$ at random points, until the claim is about the inputs alone.

Here is an article explaining the GKR protocol in depth: [GKR](https://taueflambda.dev/posts/gkr/).

### Creating a SNARK from the GKR protocol

With a multilinear polynomial commitment scheme, the verifier no longer needs the inputs, and Fiat-Shamir removes the interaction. The result is a SNARK, as described on the [next page](/notes/cryptography-zkp/computational-proof-systems/succinct-gkr-protocol/).

Rust implementation: [`iops/gkr`](https://github.com/developeruche/cryptography-n-zk-research/tree/main/iops/gkr)
