# Getting started

## Installation

`finmodel` depends on pandas, numpy and tqdm.

```bash
pip install pandas numpy tqdm
pip install -e .          # editable/development install from the repo root
```

To render `model.show()` inline you need a notebook environment:

```bash
pip install jupyterlab
```

## Anatomy of a model

Every model has three pieces:

1. **An `Inputs` dataclass** — the assumptions that drive the model.
2. **A `Model` subclass** — line items defined as `@row` methods.
3. **A run** — instantiate, `calculate()`, then `show()` / `to_html()`.

```python
from dataclasses import dataclass
from finmodel import Model, row, PredefinedFormats as F

# 1. Inputs ----------------------------------------------------------------
@dataclass
class Inputs:
    starting_revenue: float
    growth_rate: float
    cost_ratio: float
    tax_rate: float

# 2. Model -----------------------------------------------------------------
class IncomeStatement(Model[Inputs]):
    @row(group="Revenue", format=F.USD)
    def revenue(self, t):
        if t == 0:
            return self.inputs.starting_revenue
        return self.revenue(t - 1) * (1 + self.inputs.growth_rate)

    @row(group="Costs", format=F.USD)
    def operating_costs(self, t):
        return self.revenue(t) * self.inputs.cost_ratio

    @row(group="Earnings", format=F.SUBTOTAL)
    def ebit(self, t):
        return self.revenue(t) - self.operating_costs(t)

    @row(group="Earnings", format=F.USD)
    def tax(self, t):
        return max(self.ebit(t), 0) * self.inputs.tax_rate

    @row(group="Earnings", format=F.TOTAL)
    def net_income(self, t):
        return self.ebit(t) - self.tax(t)

    @row(group="Earnings", format=F.PERCENTAGE)
    def net_margin(self, t):
        return self.net_income(t) / self.revenue(t)

# 3. Run -------------------------------------------------------------------
inputs = Inputs(
    starting_revenue=1_000,
    growth_rate=0.12,
    cost_ratio=0.55,
    tax_rate=0.25,
)
model = IncomeStatement(periods=5, inputs=inputs)
model.calculate()
```

## Key points

- **`t` is zero-based.** Period `0` is the first column. Reference the prior
  period with `self.revenue(t - 1)` — guard `t == 0` to provide a starting value.
- **Call other rows like functions.** Inside a formula, `self.other_row(t)`
  returns that row's value at period `t`. The engine caches it.
- **`self.inputs`** exposes your dataclass. Field access is fully typed because
  `Model[Inputs]` is generic over the inputs type.
- **You must call `calculate()`** before `show()`, `df()`, `to_html()`, or
  `get_result_data()`.

## Getting the results out

```python
model.df()                       # plain (unformatted) pandas DataFrame
model.show()                     # styled pandas Styler (renders in Jupyter)
model.to_html("statement.html")  # write standalone styled HTML

model.get_rows()                 # ['revenue', 'operating_costs', ...]
model.get_result_data("ebit")    # numpy array of EBIT across all periods
```

## Re-running with new inputs

Assign new inputs and call `calculate()` again — it resets the internal caches
each run:

```python
model.inputs = Inputs(starting_revenue=1_200, growth_rate=0.08,
                      cost_ratio=0.55, tax_rate=0.25)
model.calculate()
```

For sweeping many input sets, see [scenario analysis](scenarios.md).

Next: [Core concepts](concepts.md).
