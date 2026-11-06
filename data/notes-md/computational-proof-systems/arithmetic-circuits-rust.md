Arithmetic circuits come to us from a field of research called computational complexity theory, and are the standard model for computing polynomials. An arithmetic circuit is an abstract concept, but it operates like a logic circuit: it takes variables and numbers as inputs, which go through arithmetic gates such as "add" or "multiply", as in the image below, where the boxes are inputs and the circles are gates. ([source](https://anoma.net/blog/a-vamp-irs-guide-to-arithmetic-circuits-and-perfectly-boiled-eggs))

![An arithmetic circuit: four inputs feed a multiplication gate and an addition gate, whose outputs feed a final addition gate](assets/notes/computational-proof-systems/arithmetic-circuit.png)

The design approach here is very similar to the other implementations in this book:

1. Design the structural interface and data structures
2. Comment out the steps needed to implement this interface
3. Implement the complete interface
4. Write unit tests :)

You can find the complete code implementation [here](https://github.com/developeruche/cryptography-n-zk-research/tree/main/primitives/circuits).

### Interface and Data Structures

This circuit needs just one method, responsible for evaluating the circuit on some given input.

```rust
pub trait CircuitInterface {
    fn evaluate<F>(&self, input: &[F]) -> CircuitEvaluation<F>
    where
        F: Add<Output = F> + Mul<Output = F> + Copy;
}
```

**Data structures**

```rust
#[derive(Clone, PartialEq, Eq, Hash, Default, Debug)]
pub struct Circuit {
    pub layers: Vec<CircuitLayer>,
}

#[derive(Clone, PartialEq, Eq, Hash, Default, Debug)]
pub struct CircuitLayer {
    pub layer: Vec<Gate>,
}

#[derive(Clone, PartialEq, Eq, Hash, Debug)]
pub struct Gate {
    pub g_type: GateType,
    pub inputs: [usize; 2],
}

#[derive(Clone, PartialEq, Eq, Hash, Debug)]
pub enum GateType {
    Add,
    Mul,
}
```

- `Circuit`: The entire arithmetic circuit. It contains multiple layers of gates. Layer 0 is the output layer, and the last layer is the one closest to the inputs.
- `CircuitLayer`: A single layer within the circuit, containing multiple gates. This organizes gates into layers, which helps with implementing and understanding the flow of computation.
- `Gate`: An individual gate within a layer. `g_type` indicates the operation the gate performs (`Add` or `Mul`). `inputs` holds two indices, which refer to outputs of the layer below it or, for the last layer, to the input values.
- `GateType`: An enum defining the operations a gate can perform.

Here is how this circuit is constructed:

```rust
// sample circuit evaluation
//        100(*)        - layer 0
//       /      \
//   5(+)_0    20(*)_1  - layer 1
//   /  \      /  \
//  2    3    4    5
let layer_0 = CircuitLayer::new(vec![Gate::new(GateType::Mul, [0, 1])]);
let layer_1 = CircuitLayer::new(vec![
    Gate::new(GateType::Add, [0, 1]),
    Gate::new(GateType::Mul, [2, 3]),
]);
let circuit = Circuit::new(vec![layer_0, layer_1]);
```

### Interface Implementation

This implementation evaluates the circuit on given input values, computing the output of each gate layer by layer, starting from the inputs.

The `evaluate` method takes a slice of inputs and returns a `CircuitEvaluation<F>`, where `F` is any type that supports addition and multiplication. The `CircuitEvaluation` struct holds the result: a vector of layers, where each layer is a vector of gate outputs.

```rust
impl CircuitInterface for Circuit {
    fn evaluate<F>(&self, input: &[F]) -> CircuitEvaluation<F>
    where
        F: Add<Output = F> + Mul<Output = F> + Copy,
    {
        let mut layers = vec![];
        let mut current_input = input;
        layers.push(input.to_vec());

        for layer in self.layers.iter().rev() {
            let temp_layer: Vec<_> = layer
                .layer
                .iter()
                .map(|e| match e.g_type {
                    GateType::Add => current_input[e.inputs[0]] + current_input[e.inputs[1]],
                    GateType::Mul => current_input[e.inputs[0]] * current_input[e.inputs[1]],
                })
                .collect();
            layers.push(temp_layer);
            current_input = &layers[layers.len() - 1];
        }

        layers.reverse();
        CircuitEvaluation { layers }
    }
}
```

**How it works**

1. **Initialization**: `layers` is created to hold the results of each layer, `current_input` is set to the input, and the input is pushed as the first entry of `layers`.
2. **Layer processing**: The method iterates over the circuit layers in reverse with `self.layers.iter().rev()`, because the last layer is the one that reads the inputs. Each gate is evaluated according to its type (`GateType::Add` or `GateType::Mul`), the results are collected into `temp_layer` and pushed onto `layers`, and `current_input` then points at this new layer.
3. **Finalization**: `layers` is reversed, so the result runs from output to input: `layers[0]` is the circuit output and the last entry is the original input. This matches the layer numbering of the circuit.

Here is sample code for building and executing a `Circuit` on some `input`. The result is `[[100], [5, 20], [2, 3, 4, 5]]`.

```rust
let layer_0 = CircuitLayer::new(vec![Gate::new(GateType::Mul, [0, 1])]);
let layer_1 = CircuitLayer::new(vec![
    Gate::new(GateType::Add, [0, 1]),
    Gate::new(GateType::Mul, [2, 3]),
]);
let circuit = Circuit::new(vec![layer_0, layer_1]);
let input = [
    Fr::from(2u32),
    Fr::from(3u32),
    Fr::from(4u32),
    Fr::from(5u32),
];
let evaluation = circuit.evaluate(&input);
```
