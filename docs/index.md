# finmodel documentation

A formula-driven financial modeling library. Define models as Python classes,
evaluate rows lazily per time period, resolve circular references iteratively,
and render results as styled pandas DataFrames or standalone HTML.

## Why finmodel

Spreadsheets are great for ad-hoc work but hard to version, test, and reuse.
`finmodel` lets you express the same row-by-period logic as plain Python:

- **Rows are methods.** Each line item is a method decorated with `@row` that
  receives `(self, t)` — the model instance and the zero-based period index.
- **Lazy + cached.** Cells are computed on demand and memoised, so a deeply
  nested model evaluates each `(row, period)` pair exactly once.
- **Circularity is first-class.** Enable iterative calculation to resolve
  classic circular references (interest ↔ debt, cash sweep, etc.).
- **Presentation is separate from logic.** Attach a `Format` to control how a
  row renders, and a `Style` to theme the whole table — without touching the
  formulas.

## Documentation map

| Guide | What it covers |
|---|---|
| [Getting started](getting-started.md) | Install, build your first model, display and export it. |
| [Core concepts](concepts.md) | Rows, formulas, lazy evaluation, caching, groups, row arithmetic. |
| [Formatting](formatting.md) | The `Format` object and every `PredefinedFormats` value, plus custom formatters. |
| [Styling & themes](styling.md) | The `Style` object, every `PredefinedStyles` theme, and how to build your own. |
| [Scenario analysis](scenarios.md) | Sweep inputs and collect outputs into a tidy DataFrame. |
| [Iterative calculation](iterative-calculation.md) | Circular references, convergence, damping. |
| [API reference](api-reference.md) | Every public class, method, and function signature. |

## Runnable examples

The [`examples/`](../examples) folder contains documented Jupyter notebooks you
can run end-to-end:

1. `01_quickstart.ipynb` — a minimal income statement.
2. `02_formatting_and_styles.ipynb` — a tour of every format and theme.
3. `03_scenario_analysis.ipynb` — sensitivity sweeps over inputs.
4. `04_iterative_calculation.ipynb` — a circular interest-on-debt model.
5. `05_three_statement_model.ipynb` — a linked P&L → cash → balance-sheet model.

## 60-second example

```python
from dataclasses import dataclass
from finmodel import Model, row, PredefinedFormats as F, PredefinedStyles as S

@dataclass
class Inputs:
    revenue: float
    growth_rate: float
    cost_ratio: float

class IncomeStatement(Model[Inputs]):
    @row(group="P&L", format=F.USD)
    def revenue(self, t):
        if t == 0:
            return self.inputs.revenue
        return self.revenue(t - 1) * (1 + self.inputs.growth_rate)

    @row(group="P&L", format=F.USD)
    def costs(self, t):
        return self.revenue(t) * self.inputs.cost_ratio

    @row(group="P&L", format=F.TOTAL)
    def ebitda(self, t):
        return self.revenue(t) - self.costs(t)

    @row(group="P&L", format=F.PERCENTAGE)
    def margin(self, t):
        return self.ebitda(t) / self.revenue(t)

inputs = Inputs(revenue=1_000, growth_rate=0.10, cost_ratio=0.60)
model = IncomeStatement(periods=5, inputs=inputs, style=S.CORPORATE_BLUE)
model.calculate()

model.show()                 # styled DataFrame in Jupyter
model.to_html("income.html") # standalone HTML file
```
