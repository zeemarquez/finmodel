# Iterative calculation (circular references)

Some financial models are inherently circular. The classic case: interest
expense depends on the debt balance, the debt balance depends on free cash flow
(after interest), and free cash flow depends on interest. A spreadsheet resolves
this by toggling "iterative calculation"; `finmodel` does the same.

## The problem

By default the engine detects when a row depends on itself within a single
period and raises:

```text
ValueError: Circular reference detected: 'interest' depends on itself in period 3.
Enable 'enable_iterative_calculation=True' to resolve.
```

## Enabling iterative calculation

```python
model = LeveredModel(
    periods=10,
    inputs=inputs,
    enable_iterative_calculation=True,
    threshold=1e-6,      # convergence tolerance (max cell-to-cell delta)
    max_iterations=200,  # safety cap on iterations
    damping=0.5,         # blend factor between iterations (0 < d < 1)
)
model.calculate()
```

### What happens during `calculate()`

When iteration is enabled, `calculate()` repeatedly evaluates **all** rows for
**all** periods:

1. The previous pass's cache becomes the "previous" values.
2. Every `(row, period)` is recomputed; when a circular dependency is hit
   mid-pass, the engine substitutes the previous pass's value (or the row's
   `initial`, or `0.0` on the first pass) instead of recursing forever.
3. After the first pass, numeric cells are blended with the previous pass using
   the **damping** factor: `new = damping * new + (1 - damping) * prev`.
4. Convergence is checked: if the largest change across all numeric cells is
   below `threshold`, iteration stops; otherwise it continues up to
   `max_iterations`.

## Parameters

| Parameter | Default | Meaning |
|---|---|---|
| `enable_iterative_calculation` | `False` | Turn the solver on. |
| `threshold` | `1e-4` | Stop once the max absolute change per cell is below this. |
| `max_iterations` | `100` | Hard cap on passes (prevents infinite loops). |
| `damping` | `0.5` | Relaxation factor. Lower = more stable, slower; `1.0` = no damping. |

### Choosing `damping`

- Models that oscillate or diverge usually converge with **more** damping
  (a smaller value, e.g. `0.3`).
- Well-behaved models converge fastest near `1.0`.
- `damping=1.0` (or values outside `0 < d < 1`) disables blending entirely.

## Circular rows are just ordinary rows

You do **not** need anything special to mark a row as circular — define it with
`@row` like any other. When the solver hits the cycle mid-iteration it
substitutes the previous pass's value (seeded at `0.0` on the first pass):

```python
from finmodel import PredefinedFormats as F

class LeveredModel(Model[Inputs]):
    @row(format=F.USD)
    def ebitda(self, t):
        return self.inputs.ebitda

    # Circular: interest ← debt ← cash flow ← interest
    @row(format=F.USD)
    def interest(self, t):
        return self.debt(t) * self.inputs.rate

    @row(format=F.USD)
    def debt(self, t):
        if t == 0:
            return self.inputs.opening_debt
        # repay with cash flow after interest
        return max(self.debt(t - 1) - (self.ebitda(t) - self.interest(t)), 0)
```

### When to provide an `initial`

A circular row's first-pass seed is `0.0` by default, or the row's `initial` if
one is set. Beware: `initial` is also used as the row's **permanent** value at
`t == 0` (it short-circuits the formula in period 0). Only set it when the row's
period-0 value genuinely *is* that constant — otherwise period 0 will be frozen
to the seed instead of being solved. For most circular rows, leaving it unset
(seed `0.0`) is correct, as in the `interest` row above where `interest(0)`
solves to `debt(0) * rate`.

> The `@row` decorator does not accept `initial`; build a `FormulaRow` directly
> when you genuinely need a fixed period-0 value (see [concepts](concepts.md)).

## Verifying convergence

If a model still looks wrong after solving, it may not have converged within
`max_iterations`. Increase the cap, lower the `threshold` expectation, or add
damping. You can inspect the solved values with `get_result_data`:

```python
model.calculate()
print(model.get_result_data("interest"))
print(model.get_result_data("debt"))
```

See `examples/04_iterative_calculation.ipynb` for a complete, runnable
cash-sweep model.

Next: [API reference](api-reference.md).
