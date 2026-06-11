# Formatting

A **format** controls how a single row renders — the text of each cell plus a
couple of typographic hints. Formatting is independent from the underlying
numbers: the stored value is always the raw result of your formula.

## The `Format` object

```python
from finmodel import Format

Format(
    formatter,        # callable: value -> str
    highlight=False,  # render the whole row as a bold, highlighted band
    italic=False,     # render the row's values in italics
)
```

- `formatter` turns a cell value into its display string.
- `highlight=True` marks the row as an emphasised subtotal/total band (it uses
  the active theme's `highlight` colours).
- `italic=True` italicises the row — handy for ratios and memo lines.

Attach a format to a row via the decorator:

```python
@row(format=PredefinedFormats.PERCENTAGE)
def margin(self, t): ...
```

If you omit `format`, the row uses `PredefinedFormats.DEFAULT`.

## Predefined formats

Import as `from finmodel import PredefinedFormats` (aliased to `F` below).

### Core numerics

| Format | Example input | Renders |
|---|---|---|
| `F.DEFAULT` | `1234.5` / `-1234` | `1,234` / `(1,234)` |
| `F.CURRENCY` | same as DEFAULT | `1,234` / `(1,234)` |
| `F.SIGNED` | `1234` / `-1234` | `+1,234` / `(1,234)` |

Accounting convention: negatives are wrapped in parentheses, values below `0.01`
collapse to `-`, and sub-unit magnitudes show one decimal place.

### Scaled numerics

| Format | Example input | Renders |
|---|---|---|
| `F.THOUSANDS` | `12_500` | `12.5K` |
| `F.MILLIONS` | `2_500_000` | `2.5M` |
| `F.BILLIONS` | `3_200_000_000` | `3.2B` |

### Currency symbols

| Format | Example input | Renders |
|---|---|---|
| `F.USD` | `1200` / `-1200` | `$1,200` / `($1,200)` |
| `F.EUR` | `1200` | `€1,200` |
| `F.GBP` | `1200` | `£1,200` |
| `F.JPY` | `1200` | `¥1,200` |

### Percentages & ratios

| Format | Example input | Renders |
|---|---|---|
| `F.PERCENTAGE` | `0.123` | `12.3%` *(italic)* |
| `F.PERCENTAGE_PRECISE` | `0.1234` | `12.34%` *(italic)* |
| `F.PERCENTAGE_SIGNED` | `0.05` / `-0.02` | `+5.0%` / `-2.0%` *(italic)* |
| `F.BASIS_POINTS` | `0.015` | `150 bps` *(italic)* |
| `F.MULTIPLE` | `2.5` | `2.5x` *(italic)* |

### Flags

| Format | Example input | Renders |
|---|---|---|
| `F.BOOLEAN` | `True` / `False` | `TRUE` / `FALSE` with green/red fill |

`BOOLEAN` is special-cased by the renderer: each cell is individually coloured
using the theme's `bool_true` / `bool_false` styles.

### Emphasis (subtotal / total bands)

| Format | Notes |
|---|---|
| `F.SUMMARY_HIGHLIGHT` | Bold highlighted band (accounting numerics). |
| `F.SUBTOTAL` | Alias for a highlighted subtotal band. |
| `F.TOTAL` | Alias for a highlighted total band. |

These render numbers like `DEFAULT` but set `highlight=True`, so the whole row
picks up the active theme's emphasis colour.

### Dates

| Format | Example input | Renders |
|---|---|---|
| `F.DATE` | `datetime(2026, 6, 11)` | `11/06/2026` |
| `F.DATE_LONG` | `datetime(2026, 6, 11)` | `11 Jun 2026` |
| `F.DATE_ISO` | `datetime(2026, 6, 11)` | `2026-06-11` |

## Custom formatters

A formatter is just `Callable[[Any], str]`. Build any rendering you need:

```python
from finmodel import Format

def x_per_unit(x):
    if not isinstance(x, (int, float)):
        return str(x)
    return f"{x:,.2f} / unit"

UNIT_ECONOMICS = Format(formatter=x_per_unit, italic=True)

@row(format=UNIT_ECONOMICS)
def cost_per_unit(self, t): ...
```

### Helpers for building formatters

`finmodel.styles` exposes a couple of factories used by the predefined set,
which you can reuse:

```python
from finmodel.styles import make_currency_formatter, _scaled_numeric_formatter

CHF = Format(make_currency_formatter("CHF ", decimals=0))
HUNDREDS = Format(_scaled_numeric_formatter(100, "h", decimals=1))
```

- `make_currency_formatter(symbol, decimals=0)` → accounting formatter with a
  currency prefix and parenthesised negatives.
- `_scaled_numeric_formatter(divisor, suffix, decimals=1)` → divides by `divisor`
  and appends `suffix` (this is how `THOUSANDS`/`MILLIONS`/`BILLIONS` are built).

## Cleaning up row labels

Row method names are snake_case. When rendering, `finmodel` applies
`label_format()` to turn `net_income` into `Net income` and to expand a few
finance abbreviations (`bop → BoP`, `eop → EoP`, `tin → TIN`,
`real`/`nominal`/`inf` into parenthesised qualifiers). You can call it directly:

```python
from finmodel import label_format
label_format("ebitda_real")   # -> 'Ebitda (real)'
```

Next: [Styling & themes](styling.md).
