from typing import Callable, Union, Dict, Any, List, Tuple
from datetime import datetime, timedelta

# ==============================================================================
# 1. UTILITIES & CSS PARSING ENGINE
# ==============================================================================

def _parse_css(css: Union[str, List[Tuple[str, str]], Dict[str, str]]) -> List[Tuple[str, str]]:
    """Normalizes mixed style formats into standard list-of-tuple properties for Pandas."""
    if isinstance(css, list):
        return css
    if isinstance(css, dict):
        return list(css.items())
    props = []
    for item in css.split(';'):
        if not item.strip():
            continue
        if ':' in item:
            k, v = item.split(':', 1)
            props.append((k.strip(), v.strip()))
    return props

def label_format(label: str) -> str:
    """Formats raw python snake_case attributes into clean accounting line labels."""
    replace_map = {'bop': 'BoP', 'eop': 'EoP', 'real': '(real)', 'nominal': '(nominal)', 'inf': '(real)', 'tin': 'TIN'}
    words = [replace_map.get(w, w) for w in label.split('_')]
    words[0] = words[0].capitalize()
    return ' '.join(words)


# ==============================================================================
# 2. FLEXIBLE FORMAT ENGINE
# ==============================================================================

class Format:
    """Encapsulates data visualization rendering rules and typographic hints."""
    def __init__(self, formatter: Callable[[Any], str], highlight: bool = False, italic: bool = False):
        self.formatter = formatter
        self.highlight = highlight
        self.italic = italic

# --- Default Formatter Behaviors ---
def standard_numeric_formatter(x: Any) -> str:
    if not isinstance(x, (int, float)):
        return str(x)
    if abs(x) < 0.01:
        return "-"
    decimals = 1 if abs(x) < 1 else 0
    return f"({abs(x):,.{decimals}f})" if x < 0 else f"{x:,.{decimals}f}"

def percentage_formatter(x: Any) -> str:
    if not isinstance(x, (int, float)):
        return str(x)
    return f"{x:.1%}"

def boolean_formatter(x: Any) -> str:
    return "TRUE" if x else "FALSE"

def short_date_formatter(x:datetime) -> str:
    return x.strftime("%d/%m/%Y")

def long_date_formatter(x: datetime) -> str:
    return x.strftime("%d %b %Y")

def iso_date_formatter(x: datetime) -> str:
    return x.strftime("%Y-%m-%d")

def precise_percentage_formatter(x: Any) -> str:
    """Percentage with two decimal places, e.g. ``12.34%``."""
    if not isinstance(x, (int, float)):
        return str(x)
    return f"{x:.2%}"

def signed_percentage_formatter(x: Any) -> str:
    """Percentage that always shows an explicit sign, e.g. ``+5.0%`` / ``-2.0%``."""
    if not isinstance(x, (int, float)):
        return str(x)
    return f"{x:+.1%}"

def basis_points_formatter(x: Any) -> str:
    """Renders a fraction as basis points, e.g. ``0.015`` -> ``150 bps``."""
    if not isinstance(x, (int, float)):
        return str(x)
    return f"{x * 10_000:,.0f} bps"

def multiple_formatter(x: Any) -> str:
    """Renders a ratio as a multiple, e.g. ``2.5`` -> ``2.5x`` (used for valuation/leverage)."""
    if not isinstance(x, (int, float)):
        return str(x)
    return f"{x:,.1f}x"

def signed_numeric_formatter(x: Any) -> str:
    """Accounting numerics that always show an explicit ``+`` for positive values."""
    if not isinstance(x, (int, float)):
        return str(x)
    if abs(x) < 0.01:
        return "-"
    decimals = 1 if abs(x) < 1 else 0
    return f"({abs(x):,.{decimals}f})" if x < 0 else f"+{x:,.{decimals}f}"

def _scaled_numeric_formatter(divisor: float, suffix: str, decimals: int = 1) -> Callable[[Any], str]:
    """Builds an accounting formatter that divides by ``divisor`` and appends ``suffix`` (e.g. K, M, B)."""
    def formatter(x: Any) -> str:
        if not isinstance(x, (int, float)):
            return str(x)
        v = x / divisor
        if abs(v) < (10 ** -decimals) / 2:
            return "-"
        return f"({abs(v):,.{decimals}f}{suffix})" if v < 0 else f"{v:,.{decimals}f}{suffix}"
    return formatter

def make_currency_formatter(symbol: str = "$", decimals: int = 0) -> Callable[[Any], str]:
    """
    Builds an accounting formatter prefixed with a currency ``symbol``.

    Negatives are wrapped in parentheses (e.g. ``($1,200)``); near-zero renders as ``-``.
    """
    def formatter(x: Any) -> str:
        if not isinstance(x, (int, float)):
            return str(x)
        if abs(x) < 0.01:
            return "-"
        return (
            f"({symbol}{abs(x):,.{decimals}f})" if x < 0
            else f"{symbol}{x:,.{decimals}f}"
        )
    return formatter

# Reusable scaled formatters (thousands / millions / billions)
thousands_formatter = _scaled_numeric_formatter(1_000, "K")
millions_formatter = _scaled_numeric_formatter(1_000_000, "M")
billions_formatter = _scaled_numeric_formatter(1_000_000_000, "B")


class PredefinedFormats:
    # --- Core numerics ---
    DEFAULT = Format(formatter=standard_numeric_formatter)
    CURRENCY = Format(formatter=standard_numeric_formatter)
    SIGNED = Format(formatter=signed_numeric_formatter)

    # --- Scaled numerics ---
    THOUSANDS = Format(formatter=thousands_formatter)
    MILLIONS = Format(formatter=millions_formatter)
    BILLIONS = Format(formatter=billions_formatter)

    # --- Currency symbols ---
    USD = Format(formatter=make_currency_formatter("$"))
    EUR = Format(formatter=make_currency_formatter("€"))
    GBP = Format(formatter=make_currency_formatter("£"))
    JPY = Format(formatter=make_currency_formatter("¥"))

    # --- Percentages & ratios ---
    PERCENTAGE = Format(formatter=percentage_formatter, italic=True)
    PERCENTAGE_PRECISE = Format(formatter=precise_percentage_formatter, italic=True)
    PERCENTAGE_SIGNED = Format(formatter=signed_percentage_formatter, italic=True)
    BASIS_POINTS = Format(formatter=basis_points_formatter, italic=True)
    MULTIPLE = Format(formatter=multiple_formatter, italic=True)

    # --- Flags ---
    BOOLEAN = Format(formatter=boolean_formatter)

    # --- Emphasis (bold highlighted subtotal/total rows) ---
    SUMMARY_HIGHLIGHT = Format(formatter=standard_numeric_formatter, highlight=True)
    SUBTOTAL = Format(formatter=standard_numeric_formatter, highlight=True)
    TOTAL = Format(formatter=standard_numeric_formatter, highlight=True)

    # --- Dates ---
    DATE = Format(formatter=short_date_formatter)
    DATE_LONG = Format(formatter=long_date_formatter)
    DATE_ISO = Format(formatter=iso_date_formatter)


# ==============================================================================
# 3. INTERCHANGEABLE STYLING / THEME ENGINE
# ==============================================================================

class Style:
    """Defines structural visual layout specifications for financial matrices."""
    def __init__(
        self,
        default: str,
        alternate: str,
        highlight: str,
        bool_true: str,
        bool_false: str,
        column_header: Union[str, list],
        index_header_l0: Union[str, list],
        blank_header: Union[str, list],
        index_align: str = "left",  
        column_align: str = "right",
        global_table: Union[str, list] = None,
        global_cells: Union[str, list] = None,
        show_category_title: bool = True,
        show_concept_title: bool = True
    ):
        self.default = default
        self.alternate = alternate
        self.highlight = highlight
        self.bool_true = bool_true
        self.bool_false = bool_false
        self.index_align = index_align
        self.column_align = column_align
        self.show_category_title = show_category_title
        self.show_concept_title = show_concept_title
        
        self.column_header = _parse_css(column_header)
        self.index_header_l0 = _parse_css(index_header_l0)
        self.blank_header = _parse_css(blank_header)
        self.global_table = _parse_css(global_table or "border-collapse: collapse; border: none;")
        
        # Enforce `white-space: nowrap;` globally on table cells by default to guarantee single-line height
        self.global_cells = _parse_css(
            global_cells or "font-family: sans-serif; font-size: 11px; border: none; padding: 6px; white-space: nowrap;"
        )


class PredefinedStyles:
    CLASSIC_LIGHT = Style(
        default="background-color: #ffffff; color: #000000;",
        alternate="background-color: #f9fafb; color: #000000;",
        highlight="background-color: #e5e7eb; font-weight: bold; color: #000000;",
        bool_true="background-color: #d1fae5; color: #065f46; font-weight: bold;",
        bool_false="background-color: #fee2e2; color: #991b1b; font-weight: bold;",
        column_header="background-color: #1f2937; color: #f3f4f6; font-weight: bold; padding: 10px;",
        index_header_l0="background-color: #1f2937; color: #f3f4f6; font-weight: bold; padding: 10px; vertical-align: top;",
        blank_header="background-color: #1f2937;",
        index_align="left",
        column_align="right",
        show_category_title=False,
        show_concept_title=False
    )

    JETBRAINS_LIGHT_THEME = Style(
        default="background-color: #ffffff; color: #1e1e24;",
        alternate="background-color: #f7f7f9; color: #1e1e24;",
        highlight="background-color: #e4e4e7; font-weight: bold; color: #000000;",
        bool_true="background-color: #d1fae5; color: #065f46; font-weight: bold;",
        bool_false="background-color: #fee2e2; color: #991b1b; font-weight: bold;",
        column_header="background-color: #f1f1f4; color: #1e1e24; font-weight: bold;",
        index_header_l0="background-color: #f1f1f4; color: #1e1e24; font-weight: bold; vertical-align: top;",
        blank_header="background-color: #f1f1f4;",
        index_align="left",
        column_align="right",
        global_cells=[
            ('font-family', '"JetBrains Mono", Consolas, monospace'),
            ('font-size', '12px'),
            ('border', 'none'),
            ('padding', '6px 14px'),
            ('text-align', 'right'),
            ('white-space', 'nowrap')  # Enforce single line layout on body cells
        ],
        global_table=[
            ('border-collapse', 'collapse'),
            ('border', 'none'),
            ('background-color', '#ffffff')
        ],
        show_category_title=False,
        show_concept_title=False
    )

    JETBRAINS_DARK_THEME = Style(
        default="background-color: #18181a; color: #e4e4e7;",
        alternate="background-color: #18181a; color: #e4e4e7;",
        highlight="background-color: #2d2d31; font-weight: bold; color: #ffffff;",
        bool_true="background-color: #064e3b; color: #34d399; font-weight: bold;",
        bool_false="background-color: #4c0519; color: #f87171; font-weight: bold;",
        column_header="background-color: #0f0f11; color: #ffffff; font-weight: bold;",
        index_header_l0="background-color: #0f0f11; color: #ffffff; font-weight: bold; vertical-align: top;",
        blank_header="background-color: #0f0f11;",
        index_align="left",  
        column_align="right",
        global_cells=[
            ('font-family', '"JetBrains Mono", Consolas, monospace'),
            ('font-size', '12px'),
            ('border', 'none'),
            ('padding', '6px 14px'),
            ('text-align', 'right'),
            ('white-space', 'nowrap')  # Enforce single line layout on body cells
        ],
        global_table=[
            ('border-collapse', 'collapse'),
            ('border', 'none'),
            ('background-color', '#18181a')
        ],
        show_category_title=False,
        show_concept_title=False
    )

    # Minimal: no header fill, hairline rules — clean look for reports and slides.
    MINIMAL = Style(
        default="background-color: #ffffff; color: #111827;",
        alternate="background-color: #ffffff; color: #111827;",
        highlight="background-color: #ffffff; font-weight: bold; color: #111827; border-top: 1px solid #111827; border-bottom: 1px solid #111827;",
        bool_true="background-color: #ffffff; color: #047857; font-weight: bold;",
        bool_false="background-color: #ffffff; color: #b91c1c; font-weight: bold;",
        column_header="background-color: #ffffff; color: #111827; font-weight: bold; border-bottom: 2px solid #111827;",
        index_header_l0="background-color: #ffffff; color: #111827; font-weight: bold; border-bottom: 2px solid #111827; vertical-align: top;",
        blank_header="background-color: #ffffff; border-bottom: 2px solid #111827;",
        index_align="left",
        column_align="right",
        global_cells=[
            ('font-family', 'Georgia, "Times New Roman", serif'),
            ('font-size', '12px'),
            ('border', 'none'),
            ('padding', '6px 16px'),
            ('white-space', 'nowrap'),
        ],
        global_table=[('border-collapse', 'collapse'), ('border', 'none'), ('background-color', '#ffffff')],
        show_category_title=False,
        show_concept_title=False,
    )

    # Corporate blue: banded rows with a navy header — classic finance deck look.
    CORPORATE_BLUE = Style(
        default="background-color: #ffffff; color: #0f172a;",
        alternate="background-color: #eff6ff; color: #0f172a;",
        highlight="background-color: #1e3a8a; font-weight: bold; color: #ffffff;",
        bool_true="background-color: #dbeafe; color: #1e40af; font-weight: bold;",
        bool_false="background-color: #fee2e2; color: #991b1b; font-weight: bold;",
        column_header="background-color: #1e3a8a; color: #ffffff; font-weight: bold; padding: 10px;",
        index_header_l0="background-color: #1e3a8a; color: #ffffff; font-weight: bold; padding: 10px; vertical-align: top;",
        blank_header="background-color: #1e3a8a;",
        index_align="left",
        column_align="right",
        show_category_title=False,
        show_concept_title=False,
    )

    # Emerald: green banded theme, useful to distinguish a second model side-by-side.
    EMERALD_LIGHT = Style(
        default="background-color: #ffffff; color: #064e3b;",
        alternate="background-color: #ecfdf5; color: #064e3b;",
        highlight="background-color: #047857; font-weight: bold; color: #ffffff;",
        bool_true="background-color: #d1fae5; color: #065f46; font-weight: bold;",
        bool_false="background-color: #fee2e2; color: #991b1b; font-weight: bold;",
        column_header="background-color: #065f46; color: #ecfdf5; font-weight: bold; padding: 10px;",
        index_header_l0="background-color: #065f46; color: #ecfdf5; font-weight: bold; padding: 10px; vertical-align: top;",
        blank_header="background-color: #065f46;",
        index_align="left",
        column_align="right",
        show_category_title=False,
        show_concept_title=False,
    )

    # Slate dark: muted neutral dark theme that is easier on the eyes than pure black.
    SLATE_DARK = Style(
        default="background-color: #1e293b; color: #e2e8f0;",
        alternate="background-color: #243044; color: #e2e8f0;",
        highlight="background-color: #334155; font-weight: bold; color: #ffffff;",
        bool_true="background-color: #064e3b; color: #34d399; font-weight: bold;",
        bool_false="background-color: #4c0519; color: #f87171; font-weight: bold;",
        column_header="background-color: #0f172a; color: #f8fafc; font-weight: bold; padding: 10px;",
        index_header_l0="background-color: #0f172a; color: #f8fafc; font-weight: bold; padding: 10px; vertical-align: top;",
        blank_header="background-color: #0f172a;",
        index_align="left",
        column_align="right",
        global_cells=[
            ('font-family', 'sans-serif'),
            ('font-size', '12px'),
            ('border', 'none'),
            ('padding', '6px 14px'),
            ('white-space', 'nowrap'),
        ],
        global_table=[('border-collapse', 'collapse'), ('border', 'none'), ('background-color', '#1e293b')],
        show_category_title=False,
        show_concept_title=False,
    )

    # Terminal: green-on-black monospace, evokes a Bloomberg/console aesthetic.
    TERMINAL = Style(
        default="background-color: #000000; color: #33ff66;",
        alternate="background-color: #050805; color: #33ff66;",
        highlight="background-color: #0a1a0a; font-weight: bold; color: #adffba;",
        bool_true="background-color: #002200; color: #33ff66; font-weight: bold;",
        bool_false="background-color: #220000; color: #ff5555; font-weight: bold;",
        column_header="background-color: #001a00; color: #adffba; font-weight: bold;",
        index_header_l0="background-color: #001a00; color: #adffba; font-weight: bold; vertical-align: top;",
        blank_header="background-color: #001a00;",
        index_align="left",
        column_align="right",
        global_cells=[
            ('font-family', '"JetBrains Mono", Consolas, monospace'),
            ('font-size', '12px'),
            ('border', 'none'),
            ('padding', '5px 14px'),
            ('text-align', 'right'),
            ('white-space', 'nowrap'),
        ],
        global_table=[('border-collapse', 'collapse'), ('border', 'none'), ('background-color', '#000000')],
        show_category_title=False,
        show_concept_title=False,
    )

    # Print: serif, white background, thin black rules — optimised for PDF / paper export.
    PRINT = Style(
        default="background-color: #ffffff; color: #000000;",
        alternate="background-color: #ffffff; color: #000000;",
        highlight="background-color: #ffffff; font-weight: bold; color: #000000; border-top: 1px solid #000000;",
        bool_true="background-color: #ffffff; color: #000000; font-weight: bold;",
        bool_false="background-color: #ffffff; color: #000000;",
        column_header="background-color: #ffffff; color: #000000; font-weight: bold; border-bottom: 1.5px solid #000000;",
        index_header_l0="background-color: #ffffff; color: #000000; font-weight: bold; border-bottom: 1.5px solid #000000; vertical-align: top;",
        blank_header="background-color: #ffffff; border-bottom: 1.5px solid #000000;",
        index_align="left",
        column_align="right",
        global_cells=[
            ('font-family', '"Times New Roman", Georgia, serif'),
            ('font-size', '11px'),
            ('border', 'none'),
            ('padding', '4px 14px'),
            ('white-space', 'nowrap'),
        ],
        global_table=[('border-collapse', 'collapse'), ('border', 'none'), ('background-color', '#ffffff')],
        show_category_title=False,
        show_concept_title=False,
    )