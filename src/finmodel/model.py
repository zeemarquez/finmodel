from typing import Generic, Callable, Union, Dict, Any, List, Tuple, Set, Type, overload, TypeVar
import pandas as pd
from finmodel.styles import *
import numpy as np

# Define type variables to assist static analysis engines (Pylance/IntelliSense)
M = TypeVar('M', bound='Model')
I = TypeVar('I')

class FormulaRow:
    """Descriptor pattern class managing lazy evaluation and structural arithmetic operators."""
    _counter = 0

    def __init__(
        self, 
        formula: Callable[[Any, int], Any] = None, 
        initial: Any = None, 
        group: str = None, 
        format: Format = None
    ):
        self.formula = formula
        self.initial = initial
        self.group = group
        self.format = format or PredefinedFormats.DEFAULT
        self.name = None
        self._order = FormulaRow._counter
        FormulaRow._counter += 1

    def set_group(self, group:str):
        self.group = group
        return self

    # Overloads to guide IDEs on descriptor return types
    @overload
    def __get__(self, instance: None, owner: Type[M]) -> 'FormulaRow': ...

    @overload
    def __get__(self, instance: M, owner: Type[M]) -> 'BoundRow': ...

    def __get__(self, instance: Any, owner: Any) -> Any:
        if instance is None:
            return self
        # Memoize the BoundRow per (descriptor, instance) to avoid ~50k allocations/sim.
        cache = instance.__dict__.get('_bound_cache')
        if cache is None:
            cache = {}
            instance.__dict__['_bound_cache'] = cache
        bound = cache.get(self)
        if bound is None:
            bound = BoundRow(self, instance)
            cache[self] = bound
        return bound

    def __add__(self, other: Union['FormulaRow', int, float]) -> 'FormulaRow':
        return FormulaRow(lambda m, t: m._eval_row(self, t) + (m._eval_row(other, t) if isinstance(other, FormulaRow) else other))

    def __sub__(self, other: Union['FormulaRow', int, float]) -> 'FormulaRow':
        return FormulaRow(lambda m, t: m._eval_row(self, t) - (m._eval_row(other, t) if isinstance(other, FormulaRow) else other))

    def __mul__(self, other: Union['FormulaRow', int, float]) -> 'FormulaRow':
        return FormulaRow(lambda m, t: m._eval_row(self, t) * (m._eval_row(other, t) if isinstance(other, FormulaRow) else other))

    def __truediv__(self, other: Union['FormulaRow', int, float]) -> 'FormulaRow':
        return FormulaRow(lambda m, t: m._eval_row(self, t) / (m._eval_row(other, t) if isinstance(other, FormulaRow) else other))

    def __radd__(self, other): return self.__add__(other)
    def __rmul__(self, other): return self.__mul__(other)
    def __rsub__(self, other): return FormulaRow(lambda m, t: other - m._eval_row(self, t))

    def link(self) -> 'FormulaRow':
        return FormulaRow(lambda m, t: m._eval_row(self, t))

class SimpleRow(FormulaRow):
    def __init__(self, value: Any, **kwargs):
        super().__init__(formula=lambda m, t: value, initial=value, **kwargs)

class BoundRow:
    """Represents a FormulaRow bound to a specific Model instance."""
    def __init__(self, row: FormulaRow, model: 'Model'):
        self._row = row
        self._model = model

    def __call__(self, t: int) -> Any:
        return self._model._eval_row(self._row, t)

def row(group: str = None, format: Format = None) -> Callable[[Callable[[Any, int], Any]], FormulaRow]:
    """
    Decorator to define a FormulaRow using a standard instance method.
    Provides 100% native IDE autocomplete (Pylance/IntelliSense) for class attributes.
    """
    def decorator(func: Callable[[Any, int], Any]) -> FormulaRow:
        # Wrap the function directly inside a FormulaRow object
        return FormulaRow(formula=func, group=group, format=format)
    return decorator


class Model(Generic[I]):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._declared_rows: List[FormulaRow] = []
        for name, attr in cls.__dict__.items():
            if isinstance(attr, FormulaRow):
                attr.name = name
                cls._declared_rows.append(attr)
        cls._declared_rows.sort(key=lambda r: r._order)

    def __init__(
        self, 
        periods:int,
        inputs:I,
        style: Style = None,
        enable_iterative_calculation: bool = False,
        threshold: float = 1e-4,
        max_iterations: int = 100,
        damping: float = 0.5,
    ):
        self.periods = periods
        self.inputs:I = inputs
        self.initial_period = 0
        self.style = style or PredefinedStyles.CLASSIC_LIGHT
        self.enable_iterative_calculation = enable_iterative_calculation
        self.threshold = threshold
        self.max_iterations = max_iterations
        self.damping = damping
        self.results_data = {}
        
        self._cache: Dict[Tuple[FormulaRow, int], Any] = {}
        self._prev_cache: Dict[Tuple[FormulaRow, int], Any] = {}
        # Set instead of list so the `in` check inside _eval_row is O(1) instead of O(depth).
        self._eval_stack: Set[Tuple[FormulaRow, int]] = set()

    def clear_cache(self):
        self._cache.clear()
        self._prev_cache.clear()
        self._eval_stack.clear()

    def _eval_row(self, row: FormulaRow, t: int) -> Any:
        # Local-bind hot attributes to avoid repeated attribute lookups in the inner loop.
        cache = self._cache
        cache_key = (row, t)

        if cache_key in cache:
            return cache[cache_key]

        stack = self._eval_stack
        if cache_key in stack:
            if self.enable_iterative_calculation:
                prev = self._prev_cache.get(cache_key)
                if prev is not None:
                    return prev
                if row.initial is not None:
                    return row.initial
                return 0.0
            raise ValueError(
                f"Circular reference detected: '{row.name}' depends on itself in period {t}. "
                f"Enable 'enable_iterative_calculation=True' to resolve."
            )

        stack.add(cache_key)
        try:
            if row.initial is not None and t == 0:
                val = row.initial
            elif row.formula is not None:
                val = row.formula(self, t)
            else:
                val = 0.0
        finally:
            stack.discard(cache_key)

        cache[cache_key] = val
        return val

    def _converged(self) -> Tuple[bool, float]:
        max_delta = 0.0
        for k, v in self._cache.items():
            if not isinstance(v, (int, float)) or isinstance(v, bool):
                continue
            pv = self._prev_cache.get(k, 0.0)
            if not isinstance(pv, (int, float)) or isinstance(pv, bool):
                pv = 0.0
            d = abs(v - pv)
            if d > max_delta:
                max_delta = d
        return max_delta < self.threshold, max_delta

    def calculate(self):
        self._cache = {}
        self._prev_cache = {}
        self._eval_stack = set()

        if self.enable_iterative_calculation:
            max_delta = float("inf")
            alpha = self.damping
            apply_damping = 0.0 < alpha < 1.0
            for iteration in range(self.max_iterations):
                self._prev_cache = self._cache
                self._cache = {}
                self._eval_stack = set()
                for row in self._declared_rows:
                    for t in range(self.periods):
                        self._eval_row(row, t)
                if iteration > 0:
                    if apply_damping:
                        # Only blend numeric values; bools/dates pass through unchanged.
                        # list() avoids any risk of "dict changed size during iteration" if a
                        # subclass mutates the cache; this branch is skipped when damping=1.0.
                        prev = self._prev_cache
                        for k, v in list(self._cache.items()):
                            if isinstance(v, (int, float)) and not isinstance(v, bool):
                                pv = prev.get(k, 0.0)
                                if isinstance(pv, (int, float)) and not isinstance(pv, bool):
                                    self._cache[k] = alpha * v + (1 - alpha) * pv
                    ok, max_delta = self._converged()
                    if ok:
                        break

        results_data = {}
        for row in self._declared_rows:
            periods_data = []
            for t in range(self.periods):
                periods_data.append(self._eval_row(row, t))
            
            periods_data = np.array(periods_data)
            results_data[row.name] = periods_data

        self.results_data = results_data

    def get_rows(self):
        return list(self.results_data.keys())

    def get_result_data(self, row_name:str) -> np.ndarray:
        return self.results_data[row_name]

    def df(self) -> pd.DataFrame:
        if len(self.results_data.keys()) == 0:
            raise ValueError("Model results are empty. Make sure to run calculate")
 
        df_data = []
        for row in self._declared_rows:
            category = row.group if row.group is not None else ""
            display_name = row.name if row.name else "Unnamed"
            row_dict = {"Concepto": display_name, "Categoria": category}
            for t in range(self.periods):
                row_dict[str(t + self.initial_period)] = self.results_data[row.name][t]
            df_data.append(row_dict)

        df = pd.DataFrame(df_data).set_index(["Categoria", "Concepto"])
        df.columns = df.columns.astype(int)
        return df

    def show(self) -> Any:
        df = self.df()
        df.index.names = [
            "Categoria" if self.style.show_category_title else None,
            "Concepto" if self.style.show_concept_title else None
        ]
        
        df_style = df.style
        for row_item in self._declared_rows:
            category = row_item.group if row_item.group is not None else ""
            df_style = df_style.format(row_item.format.formatter, subset=pd.IndexSlice[(category, row_item.name), :])

        def apply_dynamic_styles(row_data: pd.Series):
            idx = df.index.get_loc(row_data.name)
            row_obj = next((r for r in self._declared_rows if r.name == row_data.name[1]), None)
            
            if row_obj and row_obj.format == PredefinedFormats.BOOLEAN:
                border = " border-top: 2px solid #3f3f46;" if idx > 0 and row_data.name[0] != df.index[idx-1][0] else ""
                return [self.style.bool_true + border if val else self.style.bool_false + border for val in row_data.values]

            style = self.style.highlight if (row_obj and row_obj.format.highlight) else (self.style.alternate if idx % 2 == 0 else self.style.default)
            if row_obj and row_obj.format.italic:
                style += " font-style: italic;"
            if idx > 0 and row_data.name[0] != df.index[idx-1][0]:
                style += " border-top: 2px solid #3f3f46;"
            return [style] * len(row_data)

        def apply_index_styles(index_data):
            styles = []
            for i, label in enumerate(index_data):
                row_obj = next((r for r in self._declared_rows if r.name == df.index[i][1]), None)
                style = self.style.highlight if (row_obj and row_obj.format.highlight) else (self.style.alternate if i % 2 == 0 else self.style.default)
                if i > 0 and df.index[i][0] != df.index[i-1][0]:
                    style += " border-top: 2px solid #3f3f46;"
                styles.append(style + f" text-align: {self.style.index_align} !important;")
            return styles

        custom_index_headers = self.style.index_header_l0 + [('text-align', f"{self.style.index_align} !important")]
        custom_column_headers = self.style.column_header + [('text-align', f"{self.style.column_align} !important")]

        table_styles = [
            {"selector": "th, td", "props": self.style.global_cells},
            {"selector": "", "props": self.style.global_table},
            {"selector": "th.row_heading", "props": [("text-align", f"{self.style.index_align} !important")]},
            {"selector": "th.row_heading.level0", "props": [("white-space", "normal !important")]},
            {"selector": "th.level0", "props": custom_index_headers},
            {"selector": "th.col_heading", "props": custom_column_headers},
            {"selector": "th.index_name", "props": custom_index_headers},
            {"selector": ".blank", "props": self.style.blank_header},
        ]

        if not self.style.show_category_title:
            table_styles.append({"selector": "th.index_name.level0", "props": [("display", "none")]})
        if not self.style.show_concept_title:
            table_styles.append({"selector": "th.index_name.level1", "props": [("display", "none")]})

        return (df_style
            .apply(apply_dynamic_styles, axis=1)
            .apply_index(apply_index_styles, axis=0, level=1)
            .set_table_styles(table_styles)
            .format_index(label_format, axis=0, level=1)
        )

    def to_html(self, filepath: str) -> str:
        styled = self.show()
        return styled.to_html(filepath)