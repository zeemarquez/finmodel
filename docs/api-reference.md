# API reference

Everything below is importable directly from `finmodel`.

```python
from finmodel import (
    Model, FormulaRow, BoundRow, SimpleRow, row,
    Format, Style, PredefinedFormats, PredefinedStyles, label_format,
    Scenarios,
)
```

---

## `Model[I]`

Base class for models. Subclass it and declare rows with `@row`. The generic
parameter `I` is your `Inputs` dataclass type, which types `self.inputs`.

### Constructor

```python
Model(
    periods: int,
    inputs: I,
    style: Style = None,                       # default: PredefinedStyles.CLASSIC_LIGHT
    enable_iterative_calculation: bool = False,
    threshold: float = 1e-4,
    max_iterations: int = 100,
    damping: float = 0.5,
)
```

| Argument | Description |
|---|---|
| `periods` | Number of time periods (columns), evaluated as `t = 0 … periods-1`. |
| `inputs` | Your inputs dataclass instance, exposed as `self.inputs`. |
| `style` | A `Style`/`PredefinedStyles` theme for rendering. |
| `enable_iterative_calculation` | Resolve circular references numerically. See [iterative calculation](iterative-calculation.md). |
| `threshold` | Convergence tolerance for iterative calculation. |
| `max_iterations` | Iteration cap for iterative calculation. |
| `damping` | Relaxation factor (`0 < d < 1`) for iterative calculation. |

### Methods

| Method | Returns | Description |
|---|---|---|
| `calculate()` | `None` | Evaluate every row over every period and cache results. Call before any output. |
| `clear_cache()` | `None` | Drop internal caches (also done at the start of `calculate()`). |
| `get_rows()` | `list[str]` | Names of all computed rows. |
| `get_result_data(row_name)` | `np.ndarray` | Values of a row across all periods. |
| `df()` | `pd.DataFrame` | Unformatted DataFrame, MultiIndexed by `(Categoria, Concepto)`. |
| `show()` | `pd.io.formats.style.Styler` | Styled table that renders in Jupyter. |
| `to_html(filepath)` | `str` | Write the styled table to an HTML file and return the HTML. |

> `df()`, `show()`, `to_html()` and `get_result_data()` raise if called before
> `calculate()` has populated results.

---

## `row(group=None, format=None)`

Decorator that turns an instance method `func(self, t)` into a `FormulaRow`.

```python
@row(group="Revenue", format=PredefinedFormats.USD)
def revenue(self, t):
    ...
```

| Argument | Description |
|---|---|
| `group` | Category label (outer index level, used for banding/separators). |
| `format` | A `Format` controlling cell rendering. Defaults to `PredefinedFormats.DEFAULT`. |

The decorator does **not** accept `initial` — construct a `FormulaRow` directly
when you need a seed value.

---

## `FormulaRow`

The descriptor that backs every row. You rarely construct it directly (use
`@row`), but it's needed for `initial` values and explicit lambdas.

```python
FormulaRow(
    formula: Callable[[Model, int], Any] = None,  # (model, t) -> value
    initial: Any = None,                          # value used at t == 0
    group: str = None,
    format: Format = None,
)
```

### Methods & operators

| Member | Description |
|---|---|
| `set_group(group)` | Set the group label; returns `self` for chaining. |
| `link()` | Return a new `FormulaRow` that evaluates this one through the model cache. |
| `+ - * /` | Combine with another `FormulaRow` or a constant to derive a new row. |

Reverse operators (`__radd__`, `__rsub__`, `__rmul__`) make `100 - revenue` and
`0.6 * revenue` work.

---

## `SimpleRow(value, **kwargs)`

A `FormulaRow` whose value is constant across all periods.

```python
tax_rate = SimpleRow(0.25, format=PredefinedFormats.PERCENTAGE)
```

`**kwargs` are forwarded to `FormulaRow` (e.g. `group`, `format`).

---

## `BoundRow`

What you get when you access a row on a model instance (`self.revenue`). Calling
it, `self.revenue(t)`, evaluates the row at period `t` through the model's cache.
You don't construct these yourself.

---

## `Format`

```python
Format(
    formatter: Callable[[Any], str],
    highlight: bool = False,
    italic: bool = False,
)
```

See [formatting](formatting.md) for the full catalogue and custom formatters.

### `PredefinedFormats`

Numerics: `DEFAULT`, `CURRENCY`, `SIGNED` ·
Scaled: `THOUSANDS`, `MILLIONS`, `BILLIONS` ·
Currency: `USD`, `EUR`, `GBP`, `JPY` ·
Percent/ratio: `PERCENTAGE`, `PERCENTAGE_PRECISE`, `PERCENTAGE_SIGNED`,
`BASIS_POINTS`, `MULTIPLE` ·
Flags: `BOOLEAN` ·
Emphasis: `SUMMARY_HIGHLIGHT`, `SUBTOTAL`, `TOTAL` ·
Dates: `DATE`, `DATE_LONG`, `DATE_ISO`.

### Formatter helpers (in `finmodel.styles`)

| Helper | Description |
|---|---|
| `make_currency_formatter(symbol="$", decimals=0)` | Currency-prefixed accounting formatter. |
| `standard_numeric_formatter`, `percentage_formatter`, `boolean_formatter`, `short_date_formatter` | The base building blocks. |
| `thousands_formatter`, `millions_formatter`, `billions_formatter`, `multiple_formatter`, `basis_points_formatter` | Ready-made formatters. |

---

## `Style`

```python
Style(
    default, alternate, highlight, bool_true, bool_false,
    column_header, index_header_l0, blank_header,
    index_align="left", column_align="right",
    global_table=None, global_cells=None,
    show_category_title=True, show_concept_title=True,
)
```

Color/CSS fields accept a CSS string, a list of `(prop, value)` tuples, or a
dict. See [styling](styling.md) for field-by-field details.

### `PredefinedStyles`

`CLASSIC_LIGHT`, `JETBRAINS_LIGHT_THEME`, `JETBRAINS_DARK_THEME`, `MINIMAL`,
`CORPORATE_BLUE`, `EMERALD_LIGHT`, `SLATE_DARK`, `TERMINAL`, `PRINT`.

---

## `label_format(label)`

Turn a snake_case row name into a display label, expanding finance
abbreviations (`bop→BoP`, `eop→EoP`, `tin→TIN`, `real`/`nominal`/`inf` into
parenthesised qualifiers).

```python
label_format("net_income")    # 'Net income'
label_format("ebitda_real")   # 'Ebitda (real)'
```

---

## `Scenarios`

```python
Scenarios(model)
  .add_output(name: str, extractor: Callable[[Model], Any]) -> None
  .run_scenarios(inputs_list: list) -> None
  .get_scenarios_df() -> pd.DataFrame
```

See [scenario analysis](scenarios.md).
