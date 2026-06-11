# Styling & themes

A **style** (theme) controls the look of the whole table: row banding, header
colours, fonts, alignment, and the emphasis/boolean colours. It is completely
separate from [formatting](formatting.md), which controls per-row cell text.

Pass a style when constructing the model (default is `CLASSIC_LIGHT`):

```python
from finmodel import PredefinedStyles as S

model = MyModel(periods=10, inputs=inputs, style=S.CORPORATE_BLUE)
```

## Predefined themes

Import as `from finmodel import PredefinedStyles` (aliased `S`).

| Theme | Look |
|---|---|
| `S.CLASSIC_LIGHT` | White table, light-grey banding, dark slate header. The default. |
| `S.JETBRAINS_LIGHT_THEME` | Light IDE-style theme, JetBrains Mono cells. |
| `S.JETBRAINS_DARK_THEME` | Dark IDE-style theme, JetBrains Mono cells. |
| `S.MINIMAL` | No header fill; serif font with hairline rules. Great for reports/slides. |
| `S.CORPORATE_BLUE` | Navy header with light-blue banded rows. Classic finance-deck look. |
| `S.EMERALD_LIGHT` | Green header and banding — useful to distinguish a second model. |
| `S.SLATE_DARK` | Muted neutral dark theme, easier on the eyes than pure black. |
| `S.TERMINAL` | Green-on-black monospace, Bloomberg/console aesthetic. |
| `S.PRINT` | Serif, white background, thin black rules — optimised for PDF/paper. |

All themes ship with sensible `bool_true`/`bool_false` colours so
`PredefinedFormats.BOOLEAN` rows stay legible on light and dark backgrounds.

## The `Style` object

A theme is a `Style` instance. Every field:

```python
from finmodel import Style

Style(
    default,            # CSS for normal (odd) rows
    alternate,          # CSS for banded (even) rows
    highlight,          # CSS for highlighted subtotal/total rows
    bool_true,          # CSS for TRUE cells (BOOLEAN format)
    bool_false,         # CSS for FALSE cells (BOOLEAN format)
    column_header,      # CSS for the period (column) headers
    index_header_l0,    # CSS for the index header
    blank_header,       # CSS for the empty top-left corner cell
    index_align="left",     # row-label text alignment
    column_align="right",   # data column text alignment
    global_table=None,      # CSS applied to the <table> element
    global_cells=None,      # CSS applied to every th/td (fonts, padding, etc.)
    show_category_title=True,   # show the "Categoria" index header label
    show_concept_title=True,    # show the "Concepto" index header label
)
```

### CSS values are flexible

Color/typography fields accept any of three forms — they are normalised
internally:

```python
# 1. a CSS string
default="background-color: #ffffff; color: #000000;"

# 2. a list of (property, value) tuples
global_cells=[("font-family", "monospace"), ("font-size", "12px")]

# 3. a dict
column_header={"background-color": "#1e3a8a", "color": "#ffffff"}
```

### Defaults worth knowing

- `global_table` defaults to `border-collapse: collapse; border: none;`.
- `global_cells` defaults to a sans-serif 11px cell with `white-space: nowrap`
  (so rows never wrap to two lines). If you override `global_cells`, keep
  `white-space: nowrap` unless you *want* wrapping.

## Building a custom theme

Start from the fields above. Here's a warm "amber on charcoal" theme:

```python
from finmodel import Style

AMBER_DARK = Style(
    default="background-color: #1c1917; color: #fbbf24;",
    alternate="background-color: #232020; color: #fbbf24;",
    highlight="background-color: #44403c; color: #fde68a; font-weight: bold;",
    bool_true="background-color: #14532d; color: #86efac; font-weight: bold;",
    bool_false="background-color: #7f1d1d; color: #fca5a5; font-weight: bold;",
    column_header="background-color: #0c0a09; color: #fde68a; font-weight: bold;",
    index_header_l0="background-color: #0c0a09; color: #fde68a; font-weight: bold; vertical-align: top;",
    blank_header="background-color: #0c0a09;",
    index_align="left",
    column_align="right",
    global_cells=[
        ("font-family", '"JetBrains Mono", monospace'),
        ("font-size", "12px"),
        ("padding", "6px 14px"),
        ("white-space", "nowrap"),
    ],
    global_table=[("border-collapse", "collapse"), ("background-color", "#1c1917")],
    show_category_title=False,
    show_concept_title=False,
)

model = MyModel(periods=8, inputs=inputs, style=AMBER_DARK)
```

### Tweaking an existing theme

`Style` instances are plain objects — copy one and override a field:

```python
import copy
from finmodel import PredefinedStyles as S

my_theme = copy.copy(S.CORPORATE_BLUE)
my_theme.column_align = "center"
```

## Showing the category/concept index titles

By default the predefined themes hide the `Categoria`/`Concepto` index header
labels (`show_category_title=False`, `show_concept_title=False`) for a cleaner
look. Set them to `True` if you want those labels printed above the index.

Next: [Scenario analysis](scenarios.md).
