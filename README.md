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

## Documentation & examples

- **Guides** live in [`docs/`](docs/index.md): [getting started](docs/getting-started.md),
  [core concepts](docs/concepts.md), [formatting](docs/formatting.md),
  [styling & themes](docs/styling.md), [scenario analysis](docs/scenarios.md),
  [iterative calculation](docs/iterative-calculation.md), and the
  [API reference](docs/api-reference.md).
- **Runnable notebooks** live in [`examples/`](examples/README.md), covering a
  quickstart, a formats/themes tour, scenario sweeps, circular references, and a
  full three-statement model.

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

A `Format` controls how one row renders (its cell text plus `highlight`/`italic`
hints). Predefined values cover the common cases:

| Group | Formats |
|---|---|
| Numerics | `DEFAULT`, `CURRENCY`, `SIGNED` |
| Scaled | `THOUSANDS` (`12.5K`), `MILLIONS` (`2.5M`), `BILLIONS` (`3.2B`) |
| Currency | `USD`, `EUR`, `GBP`, `JPY` (`$1,200` / `($1,200)`) |
| Percent / ratio | `PERCENTAGE`, `PERCENTAGE_PRECISE`, `PERCENTAGE_SIGNED`, `BASIS_POINTS` (`150 bps`), `MULTIPLE` (`2.5x`) |
| Flags | `BOOLEAN` (`TRUE`/`FALSE` with colour fill) |
| Emphasis | `SUMMARY_HIGHLIGHT`, `SUBTOTAL`, `TOTAL` (bold highlighted bands) |
| Dates | `DATE` (`dd/mm/yyyy`), `DATE_LONG` (`11 Jun 2026`), `DATE_ISO` (`2026-06-11`) |

Build your own with `Format(my_formatter)` — see [docs/formatting.md](docs/formatting.md).

### Themes

```python
from finmodel import PredefinedStyles

model = MyModel(periods=10, inputs=inputs, style=PredefinedStyles.JETBRAINS_DARK_THEME)
```

Available: `CLASSIC_LIGHT`, `JETBRAINS_LIGHT_THEME`, `JETBRAINS_DARK_THEME`,
`MINIMAL`, `CORPORATE_BLUE`, `EMERALD_LIGHT`, `SLATE_DARK`, `TERMINAL`, `PRINT`.
Build your own with the `Style` class — see [docs/styling.md](docs/styling.md).

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
