import pytest
from dataclasses import dataclass
from finmodel import Model, FormulaRow, SimpleRow, row, PredefinedFormats


@dataclass
class SimpleInputs:
    revenue: float = 1000.0
    growth: float = 0.10
    cost_ratio: float = 0.60


class SimpleModel(Model):
    @row(format=PredefinedFormats.CURRENCY)
    def revenue(self, t):
        if t == 0:
            return self.inputs.revenue
        return self.revenue(t - 1) * (1 + self.inputs.growth)

    @row(format=PredefinedFormats.CURRENCY)
    def costs(self, t):
        return self.revenue(t) * self.inputs.cost_ratio

    @row(format=PredefinedFormats.CURRENCY)
    def ebitda(self, t):
        return self.revenue(t) - self.costs(t)

    @row(format=PredefinedFormats.PERCENTAGE)
    def margin(self, t):
        return self.ebitda(t) / self.revenue(t)


class TestFormulaRow:
    def test_declared_rows_order(self):
        names = [r.name for r in SimpleModel._declared_rows]
        assert names == ["revenue", "costs", "ebitda", "margin"]

    def test_arithmetic_add(self):
        a = FormulaRow(lambda m, t: 3.0)
        b = FormulaRow(lambda m, t: 2.0)
        c = a + b

        class M(Model):
            pass

        m = M(periods=1, inputs=None)
        assert m._eval_row(c, 0) == 5.0

    def test_arithmetic_sub(self):
        a = FormulaRow(lambda m, t: 10.0)
        b = FormulaRow(lambda m, t: 4.0)
        c = a - b
        m = Model.__new__(Model)
        m.__dict__.update({"_cache": {}, "_prev_cache": {}, "_eval_stack": set(), "enable_iterative_calculation": False})
        assert m._eval_row(c, 0) == 6.0

    def test_arithmetic_scalar(self):
        a = FormulaRow(lambda m, t: 5.0)
        b = a * 3
        m = Model.__new__(Model)
        m.__dict__.update({"_cache": {}, "_prev_cache": {}, "_eval_stack": set(), "enable_iterative_calculation": False})
        assert m._eval_row(b, 0) == 15.0


class TestModel:
    def setup_method(self):
        self.inputs = SimpleInputs()
        self.model = SimpleModel(periods=5, inputs=self.inputs)
        self.model.calculate()

    def test_periods_count(self):
        data = self.model.get_result_data("revenue")
        assert len(data) == 5

    def test_revenue_growth(self):
        rev = self.model.get_result_data("revenue")
        assert rev[0] == pytest.approx(1000.0)
        assert rev[1] == pytest.approx(1100.0)
        assert rev[4] == pytest.approx(1000.0 * 1.10**4)

    def test_ebitda_equals_revenue_minus_costs(self):
        rev = self.model.get_result_data("revenue")
        costs = self.model.get_result_data("costs")
        ebitda = self.model.get_result_data("ebitda")
        for t in range(5):
            assert ebitda[t] == pytest.approx(rev[t] - costs[t])

    def test_margin_constant(self):
        margin = self.model.get_result_data("margin")
        for t in range(5):
            assert margin[t] == pytest.approx(0.40)

    def test_df_shape(self):
        df = self.model.df()
        assert df.shape == (4, 5)

    def test_get_rows(self):
        assert set(self.model.get_rows()) == {"revenue", "costs", "ebitda", "margin"}

    def test_caching(self):
        self.model.clear_cache()
        val1 = self.model._eval_row(SimpleModel.__dict__["revenue"], 0)
        val2 = self.model._eval_row(SimpleModel.__dict__["revenue"], 0)
        assert val1 == val2


class TestCircularReference:
    def test_raises_without_iterative(self):
        @dataclass
        class Inp:
            pass

        class CircularModel(Model):
            @row()
            def a(self, t):
                return self.b(t) + 1

            @row()
            def b(self, t):
                return self.a(t) - 1

        m = CircularModel(periods=2, inputs=Inp())
        with pytest.raises(ValueError, match="Circular reference"):
            m.calculate()

    def test_resolves_with_iterative(self):
        @dataclass
        class Inp:
            target: float = 100.0

        class IterModel(Model):
            @row(initial=0.0)
            def x(self, t):
                return self.y(t) * 0.5

            @row()
            def y(self, t):
                return self.inputs.target + self.x(t) * 0.1

        m = IterModel(periods=3, inputs=Inp(), enable_iterative_calculation=True, threshold=1e-8)
        m.calculate()
        x = m.get_result_data("x")
        y = m.get_result_data("y")
        # t=0 always uses the declared initial value (0.0), so only check convergence for t≥1
        for t in range(1, 3):
            assert x[t] == pytest.approx(y[t] * 0.5, rel=1e-3)


class TestSimpleRow:
    def test_constant_value(self):
        class ConstModel(Model):
            rate = SimpleRow(0.05, format=PredefinedFormats.PERCENTAGE)

        m = ConstModel(periods=3, inputs=None)
        m.calculate()
        data = m.get_result_data("rate")
        assert all(v == pytest.approx(0.05) for v in data)
