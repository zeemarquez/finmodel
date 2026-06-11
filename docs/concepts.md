# Core concepts

## Rows

A **row** is a single line item evaluated across every period. The recommended
way to define one is the `@row` decorator on a method:

```python
@row(group="Revenue", format=PredefinedFormats.USD)
def revenue(self, t):
    if t == 0:
        return self.inputs.starting_revenue
    return self.revenue(t - 1) * (1 + self.inputs.growth_rate)
```

`@row` accepts two optional keyword arguments:

| Argument | Purpose |
|---|---|
| `group` | Category label used to band rows and draw section separators. |
| `format` | A [`Format`](formatting.md) controlling how the row renders. |

Under the hood the decorator wraps your function in a `FormulaRow` descriptor.
The method body becomes the row's `formula`, receiving `(self, t)`.

## Lazy evaluation and caching

Rows are **pull-based**: nothing is computed until you ask for it. When you call
`calculate()`, the model evaluates each declared row for `t = 0 … periods-1`.
Each `(row, period)` result is memoised in an internal cache, so even if twenty
rows all reference `revenue(t)`, the revenue formula for that period runs once.

```python
model.calculate()       # fills the cache
model.clear_cache()     # drop cached values (calculate() also resets them)
```

Because evaluation is recursive and cached, you can freely reference:

- **Earlier periods** — `self.revenue(t - 1)` (time recursion).
- **Other rows in the same period** — `self.costs(t)` (cross-row dependency).

If a row ends up depending on *itself* within the same period, that's a circular
reference. By default this raises a `ValueError`; enable
[iterative calculation](iterative-calculation.md) to resolve it numerically.

## Groups

The `group` argument organises rows into categories. Rows with the same group
are banded together, and a separator line is drawn whenever the group changes
between adjacent rows. Groups become the outer level of the DataFrame's index:

```python
@row(group="Revenue", format=F.USD)
def gross_revenue(self, t): ...

@row(group="Revenue", format=F.USD)
def net_revenue(self, t): ...

@row(group="Costs", format=F.USD)
def cogs(self, t): ...
```

You can also set the group after the fact with `some_row.set_group("...")`.

## Row arithmetic

`FormulaRow` objects support `+`, `-`, `*`, and `/`, so you can derive rows from
existing ones at the class level without writing a method:

```python
class Model1(Model[Inputs]):
    @row(format=F.USD)
    def revenue(self, t): ...

    @row(format=F.USD)
    def cogs(self, t): ...

    # Derived row — no method body needed:
    gross_profit = (revenue - cogs).set_group("Earnings")
```

Operators work with constants too (`revenue * 0.6`), and are commutative where it
makes sense (`100 - revenue`). Each operation returns a fresh `FormulaRow` whose
formula evaluates its operands through the model's cache.

## Constant rows: `SimpleRow`

For a value that's the same in every period, use `SimpleRow`:

```python
from finmodel import SimpleRow

class MyModel(Model[Inputs]):
    tax_rate = SimpleRow(0.25, format=F.PERCENTAGE)
```

## Initial values

A `FormulaRow` can carry an `initial` value used at `t == 0` instead of running
its formula — it short-circuits the formula in period 0 entirely. This is useful
for fixed opening balances. (For seeding iterative calculations, note the
default seed is already `0.0`; see [iterative calculation](iterative-calculation.md).)

```python
from finmodel import FormulaRow

opening_cash = FormulaRow(
    formula=lambda m, t: m.cash(t - 1) + m.net_flow(t),
    initial=500.0,        # used at t == 0
    format=F.USD,
)
```

> Note: the `@row` decorator does not take `initial`; construct a `FormulaRow`
> directly (or use `SimpleRow`) when you need a seed value.

## The evaluation lifecycle

```text
calculate()
  ├─ reset caches
  ├─ (optional) iterate to convergence for circular models
  └─ for each declared row, for each period t:
        _eval_row(row, t)  ──►  cache[(row, t)]
  └─ collect results_data[row_name] = np.array([...])

show() / df() / to_html()
  └─ build a MultiIndex DataFrame from results_data, then apply Format + Style
```

Next: [Formatting](formatting.md) and [Styling & themes](styling.md).
