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


class PredefinedFormats:
    DEFAULT = Format(formatter=standard_numeric_formatter)
    CURRENCY = Format(formatter=standard_numeric_formatter)
    PERCENTAGE = Format(formatter=percentage_formatter, italic=True)
    BOOLEAN = Format(formatter=boolean_formatter)
    SUMMARY_HIGHLIGHT = Format(formatter=standard_numeric_formatter, highlight=True)
    DATE = Format(formatter=short_date_formatter)


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