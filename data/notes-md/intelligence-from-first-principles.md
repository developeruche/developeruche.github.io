*A dense reference: the conditions under which the concept is defined, the single mechanism by which it is acquired, and how a unit of it is measured.*

---

### 0. Orientation

Two theses carry the whole document.

**Thesis A — what it is.** Intelligence is not a stock, it is a *rate*. Specifically: the conversion rate from (priors + experience + compute) into competence on situations not previously encountered. Skill is the stock; intelligence is the derivative.

**Thesis B — how it is gained.** There is one primitive operation, not many. It runs at every timescale and on every substrate, and the differences between substrates are differences in three quantities only: **credit-assignment fidelity, feedback bandwidth, and prior quality.**

The primitive:

> **Commit to a prediction → collide with reality → extract the discrepancy → assign blame internally → retain the correction in reusable form.**

Everything called "learning," "evolution," "science," "expertise," or "training" is this loop with different values for the three quantities above.

#### Notation

| Symbol | Meaning |
|---|---|
| $\mu$ | environment (a distribution over observation sequences given actions) |
| $\pi$ | policy / agent |
| $o_t, a_t, s_t$ | observation, action, latent state at time $t$ |
| $z_t$ | internal representation |
| $\theta$ | system parameters (weights, synapses, genome, institutional rules) |
| $M_t$ | the system's model at time $t$ |
| $K(\cdot)$ | Kolmogorov complexity — length of the shortest program producing the argument |
| $H(\cdot), I(\cdot;\cdot)$ | Shannon entropy, mutual information |
| $\delta_t$ | prediction error / discrepancy |
| $\mathcal{D}$ | data / experience |

---

## Part I — Conditions: when the concept is even defined

### 1.1 The three constraints

Intelligence is not a property a system has in isolation. It is a **relation between a system and a world**, and it is only meaningful when three conditions hold *simultaneously*:

1. **Preference.** Some outcomes count as better than others. Formally there is a $U: \mathcal{S} \to \mathbb{R}$, or a reward, or a fitness, or a loss. Without direction, "doing well" has no referent.
2. **Uncertainty.** The environment is neither fully known nor fully controlled. $P(s_{t+1} \mid s_t, a_t)$ is not known to the system, or $s_t$ is not directly observable, or both.
3. **Bounded resources.** Finite time, energy, memory, data, compute.

### 1.2 Why each is load-bearing — the collapse arguments

Each condition earns its place by what happens when you remove it.

**Remove preference** → nothing to measure. Behaviour can be described but not scored. "Intelligent" becomes a type error.

**Remove uncertainty** → a lookup table suffices. If $P(s_{t+1}|s_t,a_t)$ is known and deterministic, the optimal policy is precomputable and storable. A thermostat in a room with fixed dynamics needs no intelligence, only a rule. Intelligence is what you deploy *because* you cannot enumerate.

**Remove bounded resources** → brute force wins everything, and brute force is not intelligence. This is the condition people skip and it is the most important one.

> **Intelligence is fundamentally a scarcity phenomenon.**

The evidence for this is that every *ideal* formulation of intelligence is uncomputable:

- **Solomonoff induction**, the optimal predictor, assigns to a sequence $x$ the probability $M(x) = \sum_{p\,:\,U(p)=x*} 2^{-|p|}$ — a sum over all programs that output $x$ as a prefix. It has a beautiful convergence guarantee: total expected squared prediction error against the true environment $\mu$ is bounded by $\approx K(\mu)\ln 2$ — a constant that does **not grow with sequence length**. It is also uncomputable, because $K$ is uncomputable.
- **AIXI** = Solomonoff induction + expectimax planning. A complete formal specification of an optimally intelligent agent. Also uncomputable.

These are not footnotes. They tell you that **everything interesting about intelligence lives in the approximation** — in what you do when you cannot afford the correct answer. An omniscient oracle is not intelligent. It is merely right.

### 1.3 The two coupled capacities

Given the three constraints, intelligence decomposes into exactly two capacities, and they are not independent.

#### Modeling ≡ compression

To act well in an environment you do not control, you need internal structure that mirrors the environment's structure. The clean operationalisation is **compression**: if you can predict a stream, you have found regularity in it; finding regularity means you can describe it more briefly than listing it.

The **Minimum Description Length** principle makes this an objective:

$$H^* = \arg\min_{H}\ \big[\,L(H) + L(\mathcal{D}\mid H)\,\big]$$

Model cost plus residual cost. Note what this buys you: **Occam's razor stops being an aesthetic preference and becomes a theorem.** Under Solomonoff's prior $2^{-K(h)}$, preferring shorter hypotheses is not taste — it is the thing that makes induction work at all.

The identity that matters operationally:

$$\underbrace{\mathbb{E}[-\log_2 p_\theta(x)]}_{\text{cross-entropy loss, bits}} = \underbrace{H(X)}_{\text{irreducible}} + \underbrace{D_{KL}(p \Vert p_\theta)}_{\text{your ignorance}}$$

Training a next-token model *is* running a compressor. The loss, converted to bits, is literally the codelength you would pay to transmit the corpus using the model as the code. This is not an analogy — arithmetic coding realises it exactly.

#### Control ≡ requisite variety

Having a model is useless unless it steers action. **Ashby's Law of Requisite Variety** puts a hard floor here:

$$H(\text{outcome}) \;\ge\; H(\text{disturbance}) - H(\text{regulator})$$

A regulator must be able to produce at least as much variety of response as the disturbance it must absorb. *Only variety can destroy variety.* You cannot control what you cannot match in expressiveness — and, downstream, you cannot learn a distinction you cannot represent.

#### The halves are welded together

**Conant & Ashby (1970): every good regulator of a system must be a model of that system.**

Control forces modeling. You do not get to pick one. Any system that regulates well is, provably, isomorphic to a model of what it regulates — whether or not anyone designed it that way, and whether or not the model is legible.

### 1.4 The critical distinction: skill is not intelligence

This is where most confusion in the field originates.

A chess engine has superhuman skill and essentially zero generality. Skill is the **output** of an intelligent process, not the process.

Chollet's correction is the sharpest available: intelligence is a **conversion rate** — how efficiently a system turns priors plus experience into new skill on tasks it has not seen. A system needing ten million games to play well is doing something categorically different from one needing ten. Both may end at identical skill. Only one demonstrated intelligence.

Structurally, his measure is:

$$I \;\propto\; \underset{\text{tasks}}{\text{avg}} \left[ \frac{\text{generalization difficulty of the solution found}}{\text{priors} \;+\; \text{experience consumed}} \right]$$

with difficulty measured in algorithmic-complexity terms. The shape is what matters: **numerator = how far you generalized; denominator = what you were given and what you burned.** Any measure lacking a denominator is measuring skill, not intelligence.

### 1.5 No Free Lunch: there is no intelligence *in general*

The NFL theorems state that averaged over **all** possible environments, every algorithm performs identically. Therefore:

> **Intelligence is always relative to a distribution over environments. Priors are not a limitation to be engineered away — they are the precondition for generalizing at all.**

Human intelligence is fitted to a universe containing locality, causality, persistent objects, other agents, and approximate stationarity. Strip those regularities and human cognition has nothing to grip. The same is true of every architecture: convolution assumes translation-invariance and locality; attention assumes relevance is content-addressable rather than positional.

The practical consequence, which is easy to state and hard to internalise:

> **You cannot separate "how much a system learns" from "what it was ready to learn." Most of the difference between a good and a bad learner is decided before any data arrives.**

### 1.6 What intelligence is not

Each of these gets conflated with it, and each conflation causes specific errors:

| Not | Why | Error it causes |
|---|---|---|
| **Consciousness** | Subjective experience is orthogonal to capability | Treating capability claims as claims about moral status, and vice versa |
| **Goals or values** | Capability and objective are orthogonal axes; a system can be enormously capable and pointed anywhere | Assuming capability implies benign direction |
| **Knowledge** | Knowledge is the stored residue; intelligence is what acquires and applies it | Confusing retrieval benchmarks with reasoning benchmarks |
| **Optimality** | Optimality is easy to define and usually impossible to compute | Judging systems against an uncomputable ideal instead of against a resource budget |
| **Computation** | Computation transforms representations by rules; intelligence chooses *which* representations, rules, and actions | "More FLOPs = more intelligent" |

### 1.7 The one-line compression

> **Intelligence is the efficient conversion of limited experience into effective action in environments not previously encountered, under resource constraints, by a system that models the world it must act in.**

Every term is load-bearing:

- drop *efficient* → brute force
- drop *not previously encountered* → memorisation
- drop *resource constraints* → an uncomputable ideal
- drop *models* → reflex

---

## Part II — Mechanism: the single primitive operation

### 2.0 The constraint that forces the shape

Start information-theoretically. Intelligence is internal structure mirroring external structure, so "how does a system gain intelligence" reduces to **"how does structure about the world get into the system."**

There are exactly two sources:

1. **Inherited priors** — structure present at initialisation (genome, architecture, pretrained weights, institutional knowledge).
2. **Contact with the world** — and contact transmits information *only when the observation could have come out differently than expected.*

That second clause is the entire mechanism. If prediction and observation match perfectly, zero bits crossed the boundary. Nothing was learned because nothing was surprising.

> **Surprise is the currency of learning. Error is its unit.**

#### The negative result

Let $W$ be the world and $S_t$ the system's internal state. If $S_{t+1} = f(S_t, \text{internal noise})$ with no new observation, the **data processing inequality** gives:

$$I(W; S_{t+1}) \;\le\; I(W; S_t)$$

**No amount of internal computation creates new information about the world.** A system can think for a thousand years in a sealed room and discover nothing about what is outside it. Deduction, search, and self-play only unfold consequences already latent in priors plus held data.

#### The essential caveat: amortization

The unfolding is *not* worthless, and this is exactly where reasoning fits.

Under bounded resources, converting expensive-to-compute knowledge into cheap-to-retrieve knowledge is a **genuine capability gain**, even though it adds zero bits about the world. AlphaZero's self-play adds no information about chess beyond the rules; it *amortizes* the consequences of those rules into a fast policy. Mathematics adds no empirical bits and is obviously not useless.

The clean split:

| | increases | measured by |
|---|---|---|
| **Contact with reality** | what the system *could* know | mutual information $I(W;S)$ |
| **Internal computation** | what the system can *afford* to know | compute needed per query |

Equivalently: contact reduces **empirical uncertainty**, computation reduces **logical uncertainty**. Both are required; neither substitutes for the other. Test-time reasoning, chain-of-thought, and search are all trades of inference compute for the same bits — moving them from expensive to cheap, not creating them.

---

### 2.1 Stage 0 — Priors

Before the first observation, the system must already contain assumptions about what kinds of structure the world has. NFL guarantees this: without bias, generalization is impossible.

**Priors appear as architecture, not content.** They are a *shape* into which knowledge can be poured, and they determine which regularities the system can perceive at all.

| Substrate | Prior mechanism |
|---|---|
| Genome | body plan, reflexes, cortical wiring rules, critical periods |
| CNN | translation invariance, locality, hierarchy |
| Transformer | content-addressable relevance, permutation-equivariance modulo position encoding |
| Institution | charter, procedure, precedent |

Two systems given identical data extract wildly different amounts depending on prior fit.

### 2.2 Stage 1 — Commitment

The system must produce an expectation **before** observing. Easy to overlook, entirely load-bearing: without a commitment there is nothing to be wrong about, and therefore no error signal.

This is Popper's falsifiability criterion arrived at from mechanics rather than philosophy. A theory that predicts everything transmits nothing when reality arrives. An organism that does not anticipate can only react. A model with no forward pass has no loss.

#### Sharper commitment ⇒ more bits per observation

The information gained from observing outcome $o$ is $-\log_2 p(o)$. If your predictive distribution is near-uniform over $k$ outcomes, you gain at most $\log_2 k$ bits and your *update* is diffuse. If you commit to a sharp distribution and are wrong, the surprise — and therefore the correction — is large.

$$\text{expected information from an observation} = H[p(o)] \quad\text{(your predictive entropy)}$$

which is why **confidence is what makes experience expensive and therefore instructive**, and also why calibration matters: a sharp *and wrong* model learns fast; a sharp and *overconfident* model can be destabilised by outliers. This tension resurfaces in Stage 4.

### 2.3 Stage 2 — Discrepancy

Reality returns an outcome. The difference between predicted and actual is the raw learning signal.

$$\delta_t = o_t - \hat{o}_t \qquad\text{or}\qquad \delta_t = \nabla_\theta \mathcal{L}(o_t, \hat{o}_t) \qquad\text{or}\qquad \delta_t = r_t + \gamma V(s_{t+1}) - V(s_t)$$

The form varies by substrate — prediction error in cortex, loss gradient in a network, differential survival in evolution, profit and loss in a market, experimental disconfirmation in science — but the role is identical.

#### Signal quality has three axes, and they dominate learning speed

| Axis | Question | Cheap end | Expensive end |
|---|---|---|---|
| **Density** | How often does feedback arrive? | every token | once per lifetime |
| **Latency** | How long after the causal action? | immediate | generations |
| **Informativeness** | Does it say only *wrong*, or *wrong, in which direction, by how much*? | full gradient | scalar bit |

A scalar "you lost" at the end of a 100-move game is nearly worthless per unit of experience. A dense, directional, immediate signal is worth orders of magnitude more.

This is the concrete reason gradient methods dominate evolutionary ones in practice. For a $d$-dimensional parameter vector, a black-box/ES gradient estimate has variance that scales with $d$, so it needs $O(d)$ more samples than backpropagation to achieve comparable gradient accuracy. At $d = 10^{10}$ that is not a constant factor you engineer around.

### 2.4 Stage 3 — Credit assignment

**This is the hard problem. Everything else in the cycle is bookkeeping.**

The system knows it was wrong. It does not know *which of its internal components* was responsible. With millions of parameters and a long chain of intervening actions, "the outcome was bad" is nearly uninformative until decomposed.

#### Structural: which internal element caused the error?

$$\frac{\partial \mathcal{L}}{\partial \theta_i} \quad\text{for every } i$$

- **Backpropagation** solves this *exactly*, at the cost of requiring differentiability and paying a chain-rule pass. It returns a full $d$-dimensional direction.
- **Evolution** solves it terribly: the whole organism is the unit of selection, so a death carries roughly one bit and cannot say which gene was at fault. Order-of-magnitude: an asexual population absorbs ~1 bit per generation; recombination raises this to roughly $O(\sqrt{d})$ bits per generation, which is a large improvement and still nowhere near $d$. Evolution compensates with astronomical sample counts and four billion years.

#### Temporal: which of my earlier actions caused the later outcome?

- **Temporal-difference learning** bootstraps: instead of waiting for the final result, predict your own next prediction and correct locally.

$$V(s_t) \leftarrow V(s_t) + \alpha\big[\underbrace{r_t + \gamma V(s_{t+1}) - V(s_t)}_{\delta_t}\big]$$

- **Eligibility traces** mark recently active elements as blame-eligible: $e_t = \gamma\lambda e_{t-1} + \nabla_\theta V(s_t)$.
- **Biology** broadcasts a neuromodulatory reward-prediction-error signal (dopamine) for roughly the same purpose.
- **Science** implements structural credit assignment *socially*: the controlled experiment isolates a variable. Randomised trials exist precisely because correlational data makes blame ambiguous.

#### The general principle

> **The efficiency of credit assignment sets the exchange rate between experience and intelligence.**

Perfect credit assignment → learn from a handful of examples. No credit assignment → search blindly and pay exponentially.

### 2.5 Stage 4 — Update under constraint

Two constraints bind, and both are *essential rather than unfortunate*.

#### Conservatism — the stability–plasticity dilemma

The update must not destroy working structure. Push too hard on one example → catastrophic forgetting. Push too little → never move. Every learning system needs an answer: learning rates, momentum, replay buffers, regularisation, sleep-based consolidation, elastic weight penalties, institutional conservatism.

#### Bounded capacity — where generalization actually comes from

This is the more interesting constraint and the least intuitive point in the document.

If a system had unlimited capacity, the optimal response to every error would be to **memorise the specific case**. Zero training error, nothing transferable.

Under a capacity limit, the only way to accommodate many observations is to discover what they *share*. Shared structure is compression, and compression is understanding. Therefore:

> **Limited capacity is not a defect in a learner. It is the mechanism that manufactures abstraction.**

Regularization, dropout, weight decay, bottleneck layers, small training budgets, and the finite genome all do the same job from different angles: they make memorisation unaffordable and thereby make understanding the cheapest available option.

*(Caveat worth flagging honestly: the modern overparameterised regime complicates the naive version of this — networks with capacity to memorise often generalize anyway. The resolution is that the effective capacity is set by the optimiser's implicit bias, not the parameter count. The principle survives; "capacity" just has to be read as effective, not nominal.)*

### 2.6 Stage 5 — Consolidation

The final stage, and the one separating *learning things* from *becoming more intelligent*.

Accumulated corrections get compiled into reusable units — chunks, skills, concepts, abstractions, subroutines, named entities. What was a hard-won multi-step computation becomes a single retrievable primitive.

| Substrate | Consolidation mechanism |
|---|---|
| Brain | hippocampal → cortical transfer during sleep; episodic specifics distilled into semantic structure |
| Network | weight updates; distillation of a search procedure into a policy |
| Culture | result → paper → textbook chapter → tool → infrastructure nobody thinks about |
| Genome | developmental programs |

The consolidated unit has a property the raw experiences lacked: **it is composable.** That is what makes the whole thing compound.

### 2.7 Why the loop compounds — the abstraction ladder

Run the cycle once, get a slightly better model. Run it *with consolidation* and something qualitatively different happens: the next round of prediction and search operates over the **new primitives** rather than raw states. The search space does not shrink linearly — it collapses combinatorially.

Chase & Simon's chunking result is the cleanest empirical demonstration: chess masters reconstruct *real* board positions far better than novices, and **random** positions no better at all. The advantage is entirely in the learned vocabulary, not the machinery. A master does not search more positions per second; each unit they search over is worth thousands of raw board states.

Three consequences:

**1. Intelligence gain is path-dependent.** Which abstractions you form determines what you can efficiently learn next. Two systems with identical capacity and identical *total* experience can end up far apart based purely on the **order** in which experience arrived. This is why curriculum matters, why scaffolding works, and why some fields advance for decades while others stall — a bad early abstraction forecloses a region of the space.

**2. Returns are superlinear until they are not.** Each abstraction layer makes the next cheaper to acquire. This is the engine behind both individual expertise and civilisational acceleration. It saturates when (a) the environment stops offering new structure at the level you are searching, or (b) your priors cannot represent the next regularity up.

**3. Abstraction is lossy and can be wrong.** A consolidated chunk discards detail deemed irrelevant. If that judgement was wrong, the error is baked into the **vocabulary itself** and is far harder to correct than a surface mistake — you must unlearn the *language you think in*, not just a belief. Paradigm shifts are expensive for exactly this reason, and so is technical debt in a codebase: a bad early type is a bad early abstraction.

### 2.8 The active loop — choosing your own data

Everything above treats the system as a passive recipient. Real intelligence gain requires closing one more loop:

> **The system's actions determine its future data distribution.**

The question stops being "how do I learn from what arrives" and becomes "what should I expose myself to, given what I currently do not know?"

The optimal policy is roughly: **act to maximise expected information gain.**

$$\text{EIG}(e) \;=\; H[p(h)] \;-\; \mathbb{E}_{o \sim p(o \mid e)}\big[H[p(h \mid o, e)]\big] \;=\; I(H; O \mid e)$$

Seek states where uncertainty is highest **and** where the outcome most sharply discriminates between live hypotheses. Both terms matter — high-entropy outcomes that fail to separate hypotheses are noise, not information.

This shows up as curiosity in animals, exploration bonuses in RL, experimental design in science, A/B tests in industry. A well-chosen observation can be worth orders of magnitude more than a randomly sampled one, because it targets the region where your model is most wrong.

Two failure modes bracket it:

- **Pure exploitation** → the system only visits states it already predicts well → surprise goes to zero → learning stops. **Competence becomes a trap.**
- **Pure exploration** → never converges on anything usable.

Every intelligent system needs a schedule between them. Biology's answer is developmental: play in youth, when the cost of error is subsidised by caregivers; exploitation later.

The deep point: **an active system sits inside its own feedback loop.** Current model → actions → next data → next model. This is why intelligence gain is unstable in *both* directions. Good abstractions steer you toward informative experience; bad ones steer you into regions that confirm them.

---

## Part III — Preconditions and failure modes

### 3.1 What must be true of the system

| Requirement | Why | Failure signature |
|---|---|---|
| **Requisite variety** | You cannot learn a distinction you cannot represent (Ashby) | Persistent irreducible error; the model plateaus above the noise floor |
| **A generator of candidate structures** | Mutation, gradient direction, hypothesis proposal — something must propose | No movement despite abundant feedback |
| **Retention across cycles** | Without memory every correction is discarded | Relearns the same thing forever |
| **Capacity pressure** | Forces compression rather than storage | Memorises; perfect on seen data, useless on new |

### 3.2 What must be true of the environment

These are usually invisible because our universe supplies them for free. They are not free.

| Requirement | Statement | What breaks without it |
|---|---|---|
| **Structure** | Learnable regularity must exist | In pure noise the correct model is "it's noise." No intelligence is achievable *or needed* |
| **Approximate stationarity** | Regularities persist longer than it takes to learn them | Learned structure is stale on arrival; the loop never closes |
| **Decomposability** | The world is roughly modular — near-independent parts learnable separately and composable | If every variable interacts with every other at full strength, no local model is ever valid, and the world is unlearnable by **any** bounded system |
| **Graded feedback** | Errors discriminable in degree, not just pass/fail | All-or-nothing feedback destroys the gradient information that makes credit assignment tractable |

Decomposability deserves emphasis: **our universe's locality, hierarchy, and near-independence are arguably the deepest precondition for intelligence existing at all.** They are what make bounded models of an unbounded world possible.

### 3.3 Failure table — each mode maps to a stage

Use this as a diagnostic checklist. When a learning system is not improving, one of these is true.

| Broken stage | Failure | Signature | Fix direction |
|---|---|---|---|
| Commitment | Unfalsifiable predictions | Confident, never wrong, never improving | Force sharp, scored, pre-registered predictions |
| Discrepancy | Feedback absent, delayed, or noise-dominated | Effort without progress | Shorten the loop; add intermediate signal |
| Credit assignment | Blame misattributed | Learns superstitions; fixes the wrong thing | Isolate variables; ablate; add differentiability or traces |
| Update — too aggressive | Catastrophic forgetting | Chases the last example | Lower LR; replay; regularise |
| Update — too conservative | Rigidity | Correct in a world that has moved | Detect distribution shift; raise plasticity |
| Capacity — unbounded | Memorisation | Perfect on train, useless on test | Constrain effective capacity |
| Consolidation | Wrong abstraction locked in | Fluent reasoning in a bad vocabulary | Expensive: re-derive from raw data |
| Exploration | Competence trap | Reward flat at a local optimum; no surprise left | Inject EIG-driven exploration |
| **Objective** | Optimising a proxy | **Goodhart** — metric rises, purpose does not | Nothing internal to the loop can fix this |

That last row deserves its own note.

### 3.4 The loop has no opinion about what it is pointed at

A perfectly functioning learning loop aimed at a slightly wrong target produces a **highly capable system confidently going somewhere you did not want.** Capability and objective are orthogonal (§1.6), which means no amount of improvement to Stages 0–5 corrects an objective error — improvement makes it worse, faster.

Formally, if $\tilde{U}$ is the proxy and $U$ the true objective, optimisation pressure exploits exactly the region where $\tilde U$ and $U$ diverge, and the divergence grows with optimisation strength. This is why alignment is not a subproblem of capability; it is a property of the *specification*, which sits outside the loop entirely.

---

## Part IV — The unit, and how to measure it

### 4.1 Defining the unit

> **A unit of intelligence gained is: a retained, reusable structural change, produced by resolving a discrepancy between prediction and reality, that improves expected performance across a class of situations strictly broader than the one that produced it.**

Each clause excludes something real:

| Clause | Excludes |
|---|---|
| *Retained* | A transient correction — that is a reaction, not learning |
| *Reusable* | A fix applicable to one case only — that is a patch, not a concept |
| *Produced by resolving a discrepancy* | Structure that did not come from contact with reality — decoration, however elegant |
| ***Broader than the case that produced it*** | **Memorisation. This clause is the entire distinction between storing a fact and understanding.** |

The surplus — what the correction buys on cases never seen — is the thing being measured.

#### The measurable form

$$\text{unit} \;=\; \frac{\Delta\,\mathbb{E}_{\tau \sim \mathcal{T}}[\,\text{performance}\,]}{\text{experience consumed} \;\times\; \text{compute consumed}}$$

where $\mathcal{T}$ is a task distribution **strictly containing** the situations that generated the correction. This is Chollet's conversion rate, now expressed mechanistically rather than definitionally.

**The denominator is what makes it a measure of intelligence rather than of skill.** Any benchmark reporting only a numerator is a skill benchmark.

### 4.2 Six operationalizations

No single number captures it. These are six real measures, each valid in a different regime, each blind in a different way.

---

#### (1) Description length — *how much structure did you find?*

**Measure:** bits saved relative to a baseline code.

$$\text{bits saved} = \big(\mathcal{L}_{\text{baseline}} - \mathcal{L}_{\text{model}}\big) \times N \quad \text{[in bits]}$$

Normalised across tokenizers as **bits per byte**:

$$\text{bpb} = \frac{\mathcal{L}_{\text{nats/token}}}{\ln 2} \cdot \frac{N_{\text{tokens}}}{N_{\text{bytes}}}$$

**Valid when:** you have a probabilistic model and a held-out stream.
**Blind to:** whether the structure is *usable for control*. A perfect compressor of a stream you cannot act on has found structure but gained no leverage.
**Honest version:** charge yourself for the model too — MDL total cost $= L(H) + L(\mathcal{D}\mid H)$. Otherwise a 400B-parameter model "compressing" 1GB is cheating. This is the discipline the Hutter Prize enforces.

---

#### (2) Sample efficiency — *how much experience did it cost?*

Fit the learning curve. Empirically error falls as a power law in dataset size:

$$\varepsilon(N) \;=\; \varepsilon_\infty + c\,N^{-\alpha}$$

- $\varepsilon_\infty$ — the **irreducible floor**: aleatoric noise plus representational limits. Not your fault, and not improvable by more data.
- $\alpha$ — **the exponent is the intelligence-relevant quantity.** It is the conversion rate from data into competence, and it is set by prior fit and credit-assignment quality.
- $c$ — offset; how much you knew at $N=1$.

Two systems with equal final accuracy and different $\alpha$ are not equally intelligent. The one with higher $\alpha$ found better structure per sample.

**Valid when:** you can vary $N$ and measure held-out error.
**Blind to:** transfer. A high $\alpha$ within one distribution says nothing about a new one.

---

#### (3) Scaling-law exponents — *the conversion rate, industrialised*

$$L(N_{\text{params}}, D_{\text{tokens}}) \;=\; \underbrace{E}_{\text{entropy floor}} \;+\; \frac{A}{N^{\alpha}} \;+\; \frac{B}{D^{\beta}}$$

With Chinchilla-regime fits roughly $\alpha \approx 0.34$, $\beta \approx 0.28$, $E \approx 1.7$ nats.

This is the same object as (2), measured at industrial scale, and it is worth seeing clearly: **$E$ is the entropy of the data — the point where the world stops being predictable and no amount of anything helps. $\alpha$ and $\beta$ are conversion rates. Architecture research is, in this frame, entirely an attempt to move $\alpha$, $\beta$, and the constants — not to move $E$.**

**Valid when:** you can afford a scaling study.
**Blind to:** everything about generalization outside the training distribution, which is where §1.4's whole argument lives.

---

#### (4) Generalization difficulty — *how far did you reach?*

The measure that most directly implements §4.1. Numerator is the **algorithmic distance** between what you were given and what you produced:

$$\text{GD} \;\approx\; \frac{K(\text{solution} \mid \text{priors} + \text{experience})}{K(\text{solution})}$$

How much of the solution was *not* already implied by what you had. ARC-AGI is the concrete instantiation: tasks constructed so that the priors are explicitly enumerated (objectness, counting, symmetry, basic topology) and the experience is 2–4 examples, so the denominator is pinned and the numerator is what varies.

**Valid when:** you can bound priors and experience. This is *hard* and is precisely why benchmark contamination is fatal — contamination silently moves the item from the numerator to the denominator.
**Blind to:** nothing in principle; limited in practice by $K$ being uncomputable, so all instantiations use proxies.

---

#### (5) Regret — *the decision-theoretic measure*

$$R(T) = \sum_{t=1}^{T} \big[\,r^*_t - r_t\,\big]$$

Total shortfall against the best achievable policy in hindsight. The **rate** is what matters: $R(T) = O(\sqrt{T})$ means the per-step gap vanishes; $R(T) = O(T)$ means you never learned.

This is the only measure on the list that scores **exploration** correctly, because it charges you for the information-gathering actions you take. Measures (1)–(4) treat data as exogenous. Regret does not.

**Valid when:** the setting is sequential decision-making with a definable optimum.
**Blind to:** open-ended settings where $r^*$ is undefined.

---

#### (6) Empowerment — *the control-theoretic measure, objective-free*

$$\mathfrak{E}(s) \;=\; \max_{p(a^k)} \; I\big(A^k_t \,;\, S_{t+k} \mid s_t = s\big)$$

The channel capacity from your action sequence to your future state: **how many bits of your future you can write.** Measured in bits.

The remarkable property is that it needs **no reward function**. It measures §1.3's control half directly and is the closest thing available to an objective-free capability metric. In a 4-state line world, an agent that can reach 3 distinct states in 2 steps has $\log_2 3 \approx 1.58$ bits of empowerment; an agent in an absorbing state has exactly 0, regardless of how good its world model is.

**Valid when:** you have a transition model and a modest state/action space.
**Blind to:** whether the reachable states are *worth* reaching. Empowerment is capability with the preference condition (§1.1) deliberately removed — which is exactly why it is a clean instrument, and exactly why it is not sufficient on its own.

---

#### (7) Amortization gain — *the reasoning-specific measure*

Because §2.0 established that computation adds no bits but does add affordability, it needs its own metric:

$$\mathfrak{A} \;=\; \log_2 \frac{\text{compute to answer before consolidation}}{\text{compute to answer after}}$$

This is what self-play, distillation, chunking, and building a tool all produce. A search that took $10^9$ node expansions and now takes $10^3$ has yielded $\approx 20$ bits of amortization. **It is the only measure here that correctly scores a system that learned nothing new about the world and nonetheless got substantially more capable.**

---

### 4.3 The measures at a glance

| # | Measure | Units | Scores | Misses |
|---|---|---|---|---|
| 1 | Description length | bits | modeling | control, usability |
| 2 | Sample-efficiency exponent $\alpha$ | dimensionless | conversion rate, in-distribution | transfer |
| 3 | Scaling exponents | dimensionless | conversion rate at scale | OOD generalization |
| 4 | Generalization difficulty | dimensionless | the actual definition | uncomputable; proxy-dependent |
| 5 | Regret rate | reward·time | decision quality **and exploration** | needs a definable optimum |
| 6 | Empowerment | bits | control, objective-free | value of reachable states |
| 7 | Amortization gain | bits | reasoning / consolidation | anything requiring new data |

**Use them in combination.** A system that improves on (1) but not (6) has become a better observer without becoming a better actor. One that improves on (7) but not (1) has become faster without becoming wiser. One that improves on skill but not on (2) or (4) has not become more intelligent at all — it has been given more training data, which is a different achievement.

---

### 4.4 A minimal measurement toolkit

All of this runs as written; outputs shown are actual.

```python
"""Minimal instruments for the measures in §4.2. numpy only."""
import numpy as np
from itertools import product


# ── (1) Description length ────────────────────────────────────────────────
def bits_saved(nats_model, nats_baseline, n_tokens):
    """Bits saved vs a baseline code. Baseline for a uniform unigram
    over V tokens is log(V) nats."""
    return (nats_baseline - nats_model) / np.log(2) * n_tokens


def bits_per_byte(nats_per_token, n_tokens, n_bytes):
    """Tokenizer-invariant compression rate. The honest cross-model metric."""
    return (nats_per_token / np.log(2)) * (n_tokens / n_bytes)


# ── (2) Sample efficiency ─────────────────────────────────────────────────
def fit_power_law(n, err, floor=0.0):
    """Fit err = floor + c * n**(-alpha). Returns (c, alpha).
    alpha is the conversion rate from data into competence."""
    n, err = np.asarray(n, float), np.asarray(err, float) - floor
    m = err > 0
    A = np.vstack([np.ones(m.sum()), np.log(n[m])]).T
    coef, *_ = np.linalg.lstsq(A, np.log(err[m]), rcond=None)
    return np.exp(coef[0]), -coef[1]


def samples_for_error(c, alpha, target, floor=0.0):
    """Data required to hit a target error. Diverges as target -> floor,
    which is the point: the floor is not purchasable."""
    if target <= floor:
        return np.inf
    return (c / (target - floor)) ** (1.0 / alpha)


# ── (6) plus active learning: entropy and expected information gain ───────
def entropy(p):
    p = np.asarray(p, float); p = p[p > 0]
    return -np.sum(p * np.log2(p))


def expected_information_gain(prior, likelihood):
    """EIG of an experiment.  prior: (H,).  likelihood: (H, O), rows sum to 1.
    Returns I(H; O) in bits -- §2.8's objective for choosing what to look at."""
    prior = np.asarray(prior, float)
    likelihood = np.asarray(likelihood, float)
    marginal = prior @ likelihood
    joint = prior[:, None] * likelihood
    post = joint / np.clip(marginal, 1e-30, None)
    exp_post_H = sum(marginal[o] * entropy(post[:, o])
                     for o in range(likelihood.shape[1]))
    return entropy(prior) - exp_post_H


# ── (6) Empowerment ───────────────────────────────────────────────────────
def empowerment(T, s0, horizon=2, iters=300):
    """Channel capacity from action sequences to future state, in bits.
    T: (S, A, S) transition probabilities. Blahut-Arimoto."""
    S, A, _ = T.shape
    seqs = list(product(range(A), repeat=horizon))
    chan = np.zeros((len(seqs), S))
    for i, seq in enumerate(seqs):
        d = np.zeros(S); d[s0] = 1.0
        for a in seq:
            d = d @ T[:, a, :]
        chan[i] = d

    def kl_rows(p):
        marg = p @ chan
        with np.errstate(divide='ignore', invalid='ignore'):
            return np.nansum(chan * (np.log2(np.clip(chan, 1e-30, None))
                                     - np.log2(np.clip(marg, 1e-30, None))), axis=1)

    p = np.ones(len(seqs)) / len(seqs)
    for _ in range(iters):
        p = p * np.exp2(kl_rows(p))
        p /= p.sum()
    return float(p @ kl_rows(p))


# ── (7) Amortization ──────────────────────────────────────────────────────
def amortization_gain(cost_before, cost_after):
    """Bits of compute saved by consolidation. Adds zero world-knowledge."""
    return np.log2(cost_before / cost_after)
```

#### Worked outputs

```python
# (1) A model at 2.1 nats/token vs a uniform-50k-vocab baseline, 1M tokens:
bits_saved(2.1, np.log(50_000), 1e6)          # 1.258e7  bits  (~1.57 MB saved)
bits_per_byte(2.1, 1e6, 4.3e6)                # 0.705    bits/byte

# (2) Recover a known conversion rate from a learning curve:
ns   = np.array([1e1, 1e2, 1e3, 1e4, 1e5])
errs = 0.4 + 5.0 * ns ** -0.35                # floor 0.4, alpha 0.35
fit_power_law(ns, errs, floor=0.4)            # (5.0, 0.35)   exact
samples_for_error(5.0, 0.35, 0.5, floor=0.4)  # 71_483 samples
samples_for_error(5.0, 0.35, 0.4, floor=0.4)  # inf  <- the floor is not for sale

# (2.8) Which experiment to run, given 3 live hypotheses:
prior  = np.array([1/3, 1/3, 1/3])
test_A = np.array([[.9, .1], [.9, .1], [.1, .9]])   # separates h3 from h1,h2
test_B = np.array([[.5, .5], [.5, .5], [.5, .5]])   # separates nothing
expected_information_gain(prior, test_A)      # 0.479 bits
expected_information_gain(prior, test_B)      # 0.000 bits

# (6) Empowerment in a 4-state line world, deterministic left/right:
S, A = 4, 2
T = np.zeros((S, A, S))
for s in range(S):
    T[s, 0, max(s-1, 0)]   = 1.0
    T[s, 1, min(s+1, S-1)] = 1.0
empowerment(T, s0=1, horizon=2)               # 1.585 bits = log2(3) reachable

T_trapped = T.copy(); T_trapped[1] = 0; T_trapped[1, :, 1] = 1.0
empowerment(T_trapped, s0=1, horizon=2)       # 0.000 bits

# (7) A search compiled from 1e9 node expansions down to 1e3:
amortization_gain(1e9, 1e3)                   # 19.93 bits
```

Note what the trapped-agent case demonstrates: **empowerment is zero regardless of how good the agent's world model is.** Modeling without control scores nothing on measure (6) — the two halves of §1.3 really are separate, and a metric suite needs both.

### 4.5 A measurement protocol

When you want to claim a system got more intelligent rather than merely more skilled:

1. **Pin the denominator.** State the priors (architecture, pretraining corpus, hand-coded knowledge) and the experience (sample count, compute) *before* measuring. Unpinned denominators are how skill gets mistaken for intelligence.
2. **Define the broader class $\mathcal{T}$ explicitly**, and verify it is not contaminated by the training set. Contamination silently converts numerator into denominator and inflates the result without bound.
3. **Measure at several points on the experience axis**, not one. A single accuracy number cannot distinguish $\alpha = 0.5$ from $\alpha = 0.05$.
4. **Report a floor estimate.** Without $\varepsilon_\infty$ you cannot tell "the model is bad" from "the task is noisy."
5. **Pair a modeling measure with a control measure** — e.g. (1) or (2) alongside (5) or (6).
6. **Score the exploration separately** if the system chose its own data. Otherwise you are crediting it with information it was handed.

---

## Part V — Substrate comparison

The same loop, at radically different speeds and efficiencies. Read the last three columns: **the differences are entirely credit-assignment fidelity, feedback bandwidth, and prior quality. Nothing else.**

| Substrate | Timescale | Signal per event | Structural credit | Consolidation medium | Distinguishing property |
|---|---|---|---|---|---|
| **Evolution** | generations | ~1 bit (survive / not) | none — organism is the unit of selection | genome, developmental programs | Catastrophic sample inefficiency, compensated by 4×10⁹ years and enormous populations |
| **Nervous systems** | ms – years | dense, directional, local | decent, via neuromodulation + local plasticity | synaptic weights; sleep replay | ~12 orders of magnitude more efficient per event than evolution |
| **Culture** | years – centuries | argument, experiment, disconfirmation | via controlled experiment and institutional ablation | language, writing, institutions | **Corrections survive the death of the individual who made them.** This single property is why civilisation's capability diverged from the individual brain's |
| **Gradient-trained models** | ms | full $d$-dimensional gradient | near-exact (backprop) | weights | Fastest per step; sample-hungry relative to humans because priors are far weaker |

Two observations follow.

**On civilisation.** Individual human brains are not meaningfully more capable than fifty thousand years ago; civilisational capability has risen by orders of magnitude. So the intelligence that shapes history is not in a single skull — it is a stack, each layer running the same loop:

$$\text{evolution} \to \text{brains} \to \text{language} \to \text{writing} \to \text{institutions} \to \text{science \& markets}$$

Language is lossy compression of experience into transmissible form — the moment one organism's learning stops dying with it. Science and markets are distributed error-correction: mechanisms for generating models and killing the wrong ones *without killing the modeler*. Hayek's argument about the price system is exactly this — a market is a distributed computation over information no single participant holds. Civilisation satisfies all three conditions of §1.1: it has preferences, faces an uncertain world, and is resource-bounded.

**On thermodynamics.** Living systems maintain local order against entropy by importing free energy. Intelligence refines the trick: instead of merely dissipating, you *model*, and modeling lets you **anticipate** rather than react. Friston's free energy principle formalises this as minimising an upper bound on surprise:

$$F = \underbrace{D_{KL}\big(q(s) \,\Vert\, p(s \mid o)\big)}_{\ge 0} \;-\; \log p(o) \;\;\ge\;\; -\log p(o)$$

An intelligent system is one that keeps itself in the small set of states compatible with its own continued existence. The loop of §2 is how it does so.

---

## Part VI — Where current AI sits in this frame

Mapping the machinery you actually work with onto Part II, because the mapping is unusually clean and the gaps are the interesting part.

| Stage | Pretraining | RLHF / RLVR | In-context learning | Test-time compute |
|---|---|---|---|---|
| **0 Priors** | architecture: content-addressable relevance, depth, residual stream | inherits pretrained weights as prior | inherits weights as prior | inherits weights as prior |
| **1 Commitment** | next-token distribution — a maximally sharp, maximally dense commitment | full response | next-token, conditioned on context | intermediate tokens |
| **2 Discrepancy** | cross-entropy per token — **the highest-bandwidth error signal in the table** | scalar preference or binary verifier — **the lowest** | none (no weight update) | verifier or self-consistency |
| **3 Credit** | exact, backprop | exact structurally, poor temporally across a long response | n/a | n/a |
| **4 Update** | SGD under effective-capacity constraint | KL-penalised — explicit conservatism | activations only, discarded at end of context | none |
| **5 Consolidation** | into weights | into weights | **not consolidated** — this is the gap | not consolidated unless distilled |

Six things fall out of this table:

1. **Pretraining is a compression engine, precisely.** §1.3's identity is not metaphorical here: cross-entropy in bits *is* the codelength. Measure (1) applies directly, and scaling laws (measure 3) are the conversion-rate measurement of that engine. This is also why loss curves are the honest instrument and downstream benchmarks are the noisy proxy.

2. **The bandwidth asymmetry between pretraining and RL post-training is enormous** — every token gives a full-vocabulary distribution over what should have come next, versus one scalar for an entire trajectory. By §2.3 this predicts exactly what is observed: post-training changes behaviour with comparatively tiny data, but does not install much new structure. It is steering, not modeling.

3. **In-context learning is a second, faster loop running inside the first** — the outer loop consolidates into weights over months; the inner loop adapts within a context window and then **discards everything**. It is Stages 0–4 with Stage 5 deleted. Most of the current agenda around memory, continual learning, and long-horizon agents is an attempt to reattach Stage 5 to the inner loop. §2.7 says why this matters more than it might appear: without consolidation there is no composability, and without composability the loop does not compound.

4. **Reasoning and test-time compute are §2.0's amortization run in reverse.** Chain-of-thought spends inference compute to reach conclusions latent in the weights — it adds no bits about the world (measure 1 and 7 diverge here, which is the point). Distilling those traces back into weights runs the amortization forward and converts logical uncertainty into cheap retrieval. This also explains cleanly why self-play works in Go and not in open-ended domains: chess and Go have complete, cheap, exact verifiers, so the "collision with reality" in Stage 2 can be simulated. Where the verifier is expensive or absent, self-play has nothing to collide with.

5. **Sample-efficiency is the honest gap, and it is a priors gap.** Human children reach linguistic competence on ~10⁷–10⁸ words; frontier models use ~10¹³. By §2.4 the credit assignment is *better* in the model than in the brain — backprop is exact where biology is approximate. So the deficit is not in Stage 3. It is Stage 0: weaker, less well-fitted priors (no embodiment, no grounded causal interaction, no evolved perceptual scaffolding). This localises the research question rather than restating the mystery.

6. **The active loop (§2.8) is barely present.** Models are overwhelmingly passive recipients of a fixed corpus. They do not choose experiments to maximise EIG. Agentic systems that select their own tools, queries, and environments are the first meaningful step toward closing it — and by §2.8 that also means they inherit both instabilities: good abstractions steering toward informative data, and bad ones steering toward confirmation.

---

## Part VII — Compressions worth memorising

The document, reduced:

1. Intelligence requires **preference, uncertainty, and scarcity**. Remove any one and the concept collapses.
2. Every ideal formulation is **uncomputable**. Intelligence lives entirely in the approximation.
3. **Modeling ≡ compression. Control ≡ requisite variety.** A good regulator is necessarily a model.
4. **Skill is the stock; intelligence is the rate.** Any measure without a denominator is a skill measure.
5. NFL ⇒ **no intelligence in general** — only relative to an environment distribution. Priors are the precondition, not the defect.
6. Structure enters from exactly **two sources**: priors and contact with reality. Computation creates none, but converts expensive knowledge into cheap knowledge, which is a real gain.
7. **Surprise is the currency; error is the unit.** A matched prediction transmits zero bits.
8. **Credit assignment is the hard problem.** Its fidelity sets the exchange rate between experience and intelligence.
9. **Bounded capacity manufactures abstraction.** Unlimited capacity would memorise.
10. **Consolidation makes corrections composable**, and composability is what makes the loop compound rather than merely accumulate.
11. Compounding is **path-dependent** — the order of experience matters as much as its quantity — and **saturating**, and **lossy at the vocabulary level**, where errors are most expensive to fix.
12. **The loop has no opinion about its target.** Improving it cannot correct an objective error; it accelerates one.

#### One line

> **Intelligence is the rate at which a bounded system converts surprise into reusable structure that generalises past the case that produced it.**

---

### Source map

Ordered by how much of the above each carries.

**Definition & measure**
- Legg & Hutter, *Universal Intelligence: A Definition of Machine Intelligence* (2007) — the formalisation, and the uncomputability
- Chollet, *On the Measure of Intelligence* (2019) — the skill/intelligence correction; §1.4, §4.2(4)
- Hutter, *Universal Artificial Intelligence* (2005) — AIXI

**Modeling & compression**
- Solomonoff (1964); Rissanen, MDL — §1.3
- MacKay, *Information Theory, Inference and Learning Algorithms* — the information-theoretic bounds throughout, including evolution's bit rate
- Li & Vitányi, *An Introduction to Kolmogorov Complexity* — the reference for $K$

**Control**
- Ashby, *An Introduction to Cybernetics* (1956) — requisite variety
- Conant & Ashby (1970), *Every good regulator of a system must be a model of that system*
- Klyubin, Polani & Nehaniv (2005) — empowerment; §4.2(6)

**Mechanism**
- Sutton & Barto, *Reinforcement Learning* — the clearest treatment of temporal credit assignment; §2.4
- Rumelhart, Hinton & Williams (1986) — structural credit assignment
- Campbell (1960), *Blind Variation and Selective Retention* — the substrate-independent statement of the whole cycle, decades before any of the modern machinery
- Chase & Simon (1973) — chunking; §2.7
- Friston — free energy principle; Part V

**Epistemics**
- Popper — falsifiability, arrived at in §2.2 from mechanics rather than philosophy
- Hayek, *The Use of Knowledge in Society* (1945) — distributed computation; Part V
- Wolpert & Macready — No Free Lunch; §1.5

These disagree productively with each other, which is more useful than any one being right.
