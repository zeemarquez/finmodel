import pytest
from finmodel.styles import (
    label_format,
    Format,
    PredefinedFormats,
    PredefinedStyles,
    Style,
    standard_numeric_formatter,
    percentage_formatter,
    boolean_formatter,
)


class TestLabelFormat:
    def test_snake_case(self):
        assert label_format("net_revenue") == "Net revenue"

    def test_bop_replacement(self):
        # label_format capitalizes the first word via str.capitalize(), so BoP → Bop
        assert label_format("bop_real") == "Bop (real)"

    def test_eop_replacement(self):
        assert label_format("eop_nominal") == "Eop (nominal)"

    def test_single_word(self):
        assert label_format("revenue") == "Revenue"


class TestFormatters:
    def test_standard_near_zero(self):
        assert standard_numeric_formatter(0.001) == "-"

    def test_standard_negative(self):
        result = standard_numeric_formatter(-1500)
        assert result == "(1,500)"

    def test_standard_positive(self):
        assert standard_numeric_formatter(1000) == "1,000"

    def test_standard_non_numeric(self):
        assert standard_numeric_formatter("n/a") == "n/a"

    def test_percentage(self):
        assert percentage_formatter(0.123) == "12.3%"

    def test_boolean_true(self):
        assert boolean_formatter(True) == "TRUE"

    def test_boolean_false(self):
        assert boolean_formatter(False) == "FALSE"


class TestPredefinedFormats:
    def test_default_exists(self):
        assert isinstance(PredefinedFormats.DEFAULT, Format)

    def test_summary_highlight_flag(self):
        assert PredefinedFormats.SUMMARY_HIGHLIGHT.highlight is True

    def test_percentage_italic_flag(self):
        assert PredefinedFormats.PERCENTAGE.italic is True


class TestPredefinedStyles:
    def test_classic_light_is_style(self):
        assert isinstance(PredefinedStyles.CLASSIC_LIGHT, Style)

    def test_dark_theme_background(self):
        assert "#18181a" in PredefinedStyles.JETBRAINS_DARK_THEME.default

    def test_global_cells_parsed_to_list(self):
        style = PredefinedStyles.CLASSIC_LIGHT
        assert isinstance(style.global_cells, list)
        assert all(isinstance(item, tuple) for item in style.global_cells)
