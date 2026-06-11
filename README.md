# finmodel

A formula-driven financial modeling library. Define models as Python classes, evaluate rows lazily per time period, and render results as styled pandas DataFrames or HTML.

## Installation

```bash
pip install pandas numpy tqdm
pip install -e .          # development install
```

## Quick start

```python
from dataclasses import dataclass
from finmodel import Model, row, PredefinedFormats

@dataclass
class Inputs:
    revenue: float
    growth_rate: float
    cost_ratio: float

class IncomeStatement(Model[Inputs]):
    @row(format=PredefinedFormats.CURRENCY)
    def revenue(self, t):
        if t == 0:
            return self.inputs.revenue
        return self.revenue(t - 1) * (1 + self.inputs.growth_rate)

    @row(format=PredefinedFormats.CURRENCY)
    def costs(self, t):
        return self.revenue(t) * self.inputs.cost_ratio

    @row(format=PredefinedFormats.CURRENCY)
    def ebitda(self, t):
        return self.revenue(t) - self.costs(t)

    @row(format=PredefinedFormats.PERCENTAGE)
    def margin(self, t):
        return self.ebitda(t) / self.revenue(t)

inputs = Inputs(revenue=1_000, growth_rate=0.10, cost_ratio=0.60)
model = IncomeStatement(periods=5, inputs=inputs)
model.calculate()

model.show()          # styled DataFrame (Jupyter)
model.to_html("out.html")
```

## Key concepts

### Rows

Rows are defined with the `@row` decorator (recommended) or as `FormulaRow` descriptors. Each formula receives `(self, t)` where `t` is the zero-based period index.

```python
@row(group="Revenue", format=PredefinedFormats.CURRENCY)
def net_revenue(self, t):
    return self.gross_revenue(t) * (1 - self.inputs.discount_rate)
```

Row arithmetic is also supported at the class level:

```python
gross_profit = revenue - cogs          # FormulaRow + FormulaRow
```

### Formatting

| Format | Renderer |
|---|---|
| `PredefinedFormats.DEFAULT` | Accounting numerics (negative in parens) |
| `PredefinedFormats.CURRENCY` | Same as DEFAULT |
| `PredefinedFormats.PERCENTAGE` | `12.3%` |
| `PredefinedFormats.BOOLEAN` | `TRUE` / `FALSE` with color fill |
| `PredefinedFormats.DATE` | `dd/mm/yyyy` |
| `PredefinedFormats.SUMMARY_HIGHLIGHT` | Bold highlighted row |

### Themes

```python
from finmodel import PredefinedStyles

model = MyModel(periods=10, inputs=inputs, style=PredefinedStyles.JETBRAINS_DARK_THEME)
```

Available: `CLASSIC_LIGHT`, `JETBRAINS_LIGHT_THEME`, `JETBRAINS_DARK_THEME`.

### Circular references (iterative calculation)

```python
model = MyModel(
    periods=10,
    inputs=inputs,
    enable_iterative_calculation=True,
    threshold=1e-6,
    max_iterations=200,
    damping=0.5,
)
```

### Scenario analysis

```python
from finmodel import Scenarios

scenarios = Scenarios(model)
scenarios.add_output("ebitda_y5", lambda m: m.get_result_data("ebitda")[-1])

inputs_list = [Inputs(revenue=1000, growth_rate=g, cost_ratio=0.6) for g in [0.05, 0.10, 0.15]]
scenarios.run_scenarios(inputs_list)

df = scenarios.get_scenarios_df()
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
