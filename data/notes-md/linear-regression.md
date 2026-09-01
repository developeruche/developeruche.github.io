## 1. What It Is

Linear regression is a statistical technique for finding the relationship between variables.

In a machine learning context, it finds the relationship between a **feature** (input) and a **label** (the thing being predicted). The model assumes this relationship can be described by a straight line.

---

## 2. The Linear Regression Equation

### From algebra to machine learning

In algebra, a line is written as:

$$y = mx + b$$

Machine learning expresses the same idea with different notation:

$$y' = b + w_1x_1$$

### What each term means

| Term | Name | Algebraic equivalent | Notes |
|---|---|---|---|
| $y'$ | Predicted output | $y$ | The model's prediction, not the true value |
| $b$ | Bias | y-intercept | A **parameter** learned during training |
| $w_1$ | Weight | slope $m$ | A **parameter** learned during training |
| $x_1$ | Feature | $x$ | The input; supplied by the data, not learned |

The key distinction: $b$ and $w_1$ are what the model *figures out*. $x_1$ is what you *give* it.

### Models with multiple features

Real problems rarely depend on a single input. A model with five features looks like:

$$y' = b + w_1x_1 + w_2x_2 + w_3x_3 + w_4x_4 + w_5x_5$$

Each feature gets its own weight. There is still only one bias term. Generalized to $n$ features:

$$y' = b + \sum_{i=1}^{n} w_ix_i$$

---

## 3. Loss

**Loss** is a numerical metric describing how wrong a model's predictions are. It is measured as the distance between the model's predictions and the actual labels.

Lower loss means a better model. Loss is what training tries to minimize.

### Types of loss

| # | Loss type | Formula | What it does |
|---|---|---|---|
| 1 | **L1 loss** | $\sum \lvert \text{actual} - \text{predicted} \rvert$ | Sum of absolute differences |
| 2 | **Mean absolute error (MAE)** | $\frac{1}{n} \sum \lvert \text{actual} - \text{predicted} \rvert$ | L1 loss averaged over $n$ examples |
| 3 | **L2 loss** | $\sum (\text{actual} - \text{predicted})^2$ | Sum of squared differences |
| 4 | **Mean squared error (MSE)** | $\frac{1}{n} \sum (\text{actual} - \text{predicted})^2$ | L2 loss averaged over $n$ examples |
| 5 | **Root mean squared error (RMSE)** | $\sqrt{\frac{1}{n} \sum (\text{actual} - \text{predicted})^2}$ | Square root of MSE |

### How they relate

- MAE is just **L1 divided by $n$**; MSE is just **L2 divided by $n$**. Averaging makes the number comparable across datasets of different sizes.
- RMSE is the square root of MSE, which returns the value to the **same units as the label**. This makes it easier to interpret than MSE.

### Choosing between L1 and L2

Squaring penalizes large errors much more heavily than small ones.

- **L2 / MSE** is more sensitive to outliers. A single badly-wrong prediction dominates the loss, so the model works hard to fix it.
- **L1 / MAE** treats all errors proportionally, so it is more robust when the dataset contains outliers you don't want the model chasing.

---

## 4. Gradient Descent

Gradient descent is a mathematical technique that iteratively finds the weights and bias producing the model with the lowest loss.

### The algorithm

1. Calculate the loss using the current weights and bias.
2. Determine which direction to move the weights and bias to reduce the loss.
3. Move the weights and bias a small amount in that direction.
4. Return to step 1 and repeat until the model can't reduce the loss any further.

### Convergence

A model has **converged** when additional iterations stop meaningfully reducing the loss. At that point the model has settled at (or very near) the minimum of the loss curve.

---

## 5. Hyperparameters

> Hyperparameters are variables that control different aspects of training.

Note the contrast with parameters:

- **Parameters** ($w$ and $b$) are calculated *by* the model during training.
- **Hyperparameters** are set *by you* before training begins.

The three main hyperparameters:

### Learning rate

A floating-point number that influences how quickly a model converges. It controls the size of the step taken in step 3 of gradient descent.

- **Too low** — the model takes too long to converge.
- **Too high** — the model never converges. It bounces around the weight and bias values that minimize the loss, overshooting them repeatedly.
- **Goal** — pick a value that is neither too high nor too low, so the model converges quickly.

### Batch size

The number of examples the model processes before updating its weights and bias.

When a dataset is very large, updating the weights and bias after every single entry is impractical, so examples are grouped into **batches** instead.

### Epochs

One epoch means the model has processed **every example in the training set once**.

Training typically runs for many epochs, since a single pass through the data is rarely enough to converge.

---

## 6. Summary

| Concept | One-line definition |
|---|---|
| Linear regression | Fits a straight line describing the relationship between features and a label |
| Bias ($b$) | Learned y-intercept |
| Weight ($w$) | Learned slope, one per feature |
| Loss | How wrong the predictions are |
| Gradient descent | Iterative method for finding the $w$ and $b$ with the lowest loss |
| Learning rate | How big each gradient descent step is |
| Batch size | How many examples before each update |
| Epoch | One full pass over the training set |
