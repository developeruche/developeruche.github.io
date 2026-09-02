**Idea: adaptation is intelligence.** Survival of the fittest, turned into an optimisation procedure.

The big question is how to use that idea for optimisation. Given a function

$$f(x) = x_1^2 + \log(x_2) + \frac{\sin(x_3)}{1 - x_4}$$

suppose we want to find the maximum value of $f(x)$ subject to some constraints. Optimisation only makes sense when there are constraints.

## Population and chromosomes

> "Population means the gene pool of a species."

> "The gene pool of a species is a collection of many chromosomes that over time have created the characteristics and attributes of that species."

> "Chromosomes are information updated over time by evolution."

> "It is important to note, evolution is a very slow algorithm. Evolution does not happen immediately."

## How evolution happens

Evolution happens by the selection of chromosomes, which happens during mating and reproduction, where a **crossover** happens.

Crossover simply means some traits (chromosomes) come from one parent and some other traits from the other parent, making the child a composition of traits from both parents.

That makes sense, but a fair question follows: if this is true, how do new items come into the population? The answer is **mutation**.

The mutation of genetic material brings about a gigantic possibility for evolution to create new things.

**Note.** Mutation is a very risky business, so you must be careful with it.

After crossover and mutation, the child can be sent into the population, and after a while the parent.

## Applying the idea to a real-value optimisation problem

How can this abstract idea be applied to a real-value optimisation problem?

For the function

$$f(x) = x_1^2 + \log(x_2) + \frac{\sin(x_3)}{1 - x_4}$$

each part of the function is mapped to a binary array:

| Term | Binary encoding |
|---|---|
| $x_1^2$ | `1 1 0 1 0` |
| $\log(x_2)$ | `1 0 0 1 1` |
| $\sin(x_3)$ | `0 0 1 0 1` |
| $1 - x_4$ | `0 0 1 1 0` |

Concatenating them gives the chromosome array:

`[1 1 0 1 0 | 1 0 0 1 1 | 1 1 1 0 1 | 0 0 1 1 0]`

Using this data structure we can create a population.

## Simple genetic algorithm

1. Initialise the population.
2. Calculate the fitness of the population.
3. While the stopping criterion is not satisfied:
   - Select parents.
   - Perform crossover, producing offspring.
   - Apply mutation.
   - Calculate fitness.

## Driving forces

Each family of methods is pulled forward by a different signal.

| Approach | Driving force |
|---|---|
| Neural networks | error |
| Reinforcement learning | reward and punishment |
| Evolutionary algorithms | fitness |

## Why use a GA

- Easy to code.
- They provide many solutions, which can help avoid local extrema.
- They can be parallelised.

## Shortcomings of GAs

- They are extremely slow.
- The fitness function may not be easily designed; it comes from the nature of the problem.

## Population size

How many chromosomes there are in one generation.

1. **Too many** — the GA becomes extremely sluggish.
2. **Too few** — not many possibilities for mating, and only a part of the search space gets sampled.

## Crossover frequency

1. **All the time** — all offspring are made via a crossover.
2. **Never (0%)** — copy the parents.

## Mutation frequency

1. **Never (0%)** — no change in copies or in offspring, so it takes extremely longer.
2. **Too often (50%)** — huge variability, preventing convergence.
3. **Rarely (0.1%)** — additional diversity, contributing to good solutions.

## How to select parents

> "This is very important because the first step of every generation is to select parents, apply crossover, and in some cases mutation."

1. **When fitness values are very different** — rank selection: rank all chromosomes based on their fitness values.
2. **When fitness values are not very different** — roulette wheel selection.

## Other GA models

- Island models.

## How to initialise the population

1. Generally random.
2. Domain knowledge can be embedded to seed the population.
3. It has to be a uniform mixture of possible values.

## When to stop the evolution

1. Maximum number of generations.
2. Minimum level of diversity.
3. Some level of fitness.
4. A certain number of generations during which no significant fitness change occurs.
