# Examples

Documented, runnable Jupyter notebooks for `finmodel`. Each notebook is
self-contained — open it and run all cells.

| Notebook | What it teaches |
|---|---|
| [`01_quickstart.ipynb`](01_quickstart.ipynb) | Build and display a five-year income statement from scratch. |
| [`02_formatting_and_styles.ipynb`](02_formatting_and_styles.ipynb) | Every `PredefinedFormats` value, every built-in theme, and how to build custom ones. |
| [`03_scenario_analysis.ipynb`](03_scenario_analysis.ipynb) | Sweep inputs with `Scenarios` and pivot into a sensitivity table. |
| [`04_iterative_calculation.ipynb`](04_iterative_calculation.ipynb) | Resolve a circular interest ↔ debt cash-sweep model. |
| [`05_three_statement_model.ipynb`](05_three_statement_model.ipynb) | A linked P&L → cash flow → balance sheet with a balance check. |

## Running them

```bash
pip install -e .      # from the repo root
pip install jupyterlab
jupyter lab           # then open examples/
```

The notebooks call `model.show()`, which renders a styled table inline in
Jupyter. Outside a notebook, use `model.to_html("out.html")` to write a
standalone file, or `model.df()` for a plain DataFrame.

For conceptual background see the [`docs/`](../docs) folder.
