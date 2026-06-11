# Scenario analysis

`Scenarios` runs a model repeatedly over a list of input sets and collects
named outputs into a tidy DataFrame — ideal for sensitivity tables and
tornado-style comparisons.

## Workflow

```python
from dataclasses import dataclass
from finmodel import Model, row, Scenarios, PredefinedFormats as F

@dataclass
class Inputs:
    revenue: float
    growth_rate: float
    cost_ratio: float

class IncomeStatement(Model[Inputs]):
    @row(format=F.USD)
    def revenue(self, t):
        return self.inputs.revenue if t == 0 else self.revenue(t - 1) * (1 + self.inputs.growth_rate)

    @row(format=F.USD)
    def ebitda(self, t):
        return self.revenue(t) * (1 - self.inputs.cost_ratio)

# 1. Build a model instance (its inputs will be swapped per scenario).
model = IncomeStatement(periods=5, inputs=Inputs(1_000, 0.10, 0.60))

# 2. Wrap it in Scenarios and register the outputs you care about.
scenarios = Scenarios(model)
scenarios.add_output("ebitda_y5", lambda m: m.get_result_data("ebitda")[-1])
scenarios.add_output("revenue_y5", lambda m: m.get_result_data("revenue")[-1])

# 3. Provide the list of input sets to sweep.
grid = [
    Inputs(revenue=1_000, growth_rate=g, cost_ratio=c)
    for g in (0.05, 0.10, 0.15)
    for c in (0.55, 0.60)
]
scenarios.run_scenarios(grid)

# 4. Collect everything into one DataFrame.
df = scenarios.get_scenarios_df()
```

## The result DataFrame

`get_scenarios_df()` returns one row per scenario, with a two-level column
index that separates assumptions from results:

| `('input', ...)` columns | `('output', ...)` columns |
|---|---|
| every field of your `Inputs` dataclass | every output you registered |

```text
        input                       output
      revenue growth_rate cost_ratio  ebitda_y5  revenue_y5
0        1000        0.05       0.55   ...        ...
1        1000        0.05       0.60   ...        ...
...
```

Because it's a plain pandas DataFrame you can pivot it into a sensitivity grid:

```python
df.columns = ["_".join(c) for c in df.columns]   # flatten the MultiIndex
pivot = df.pivot(index="input_growth_rate",
                 columns="input_cost_ratio",
                 values="output_ebitda_y5")
```

## API summary

| Method | Description |
|---|---|
| `Scenarios(model)` | Wrap a model instance. |
| `add_output(name, extractor)` | Register an output; `extractor` is `Model -> value`. Raises `NameError` on a duplicate name. |
| `run_scenarios(inputs_list)` | Run the model once per input set (shows a `tqdm` progress bar). |
| `get_scenarios_df()` | Return the combined inputs/outputs DataFrame. |

### Extractor functions

An extractor receives the freshly-`calculate()`d model and returns any value:

```python
scenarios.add_output("peak_margin",
                     lambda m: max(m.get_result_data("ebitda") / m.get_result_data("revenue")))
scenarios.add_output("y3_revenue",
                     lambda m: m.get_result_data("revenue")[2])
```

> Your `Inputs` must be a `@dataclass` — `Scenarios` uses `dataclasses.asdict`
> to record each scenario's assumptions.

Next: [Iterative calculation](iterative-calculation.md).
