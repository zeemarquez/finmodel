import pytest
from dataclasses import dataclass
from finmodel import Model, row, Scenarios, PredefinedFormats


@dataclass
class Inp:
    revenue: float
    growth: float = 0.10


class RevenueModel(Model):
    @row(format=PredefinedFormats.CURRENCY)
    def revenue(self, t):
        if t == 0:
            return self.inputs.revenue
        return self.revenue(t - 1) * (1 + self.inputs.growth)


class TestScenarios:
    def setup_method(self):
        base = Inp(revenue=1000.0)
        self.model = RevenueModel(periods=3, inputs=base)
        self.scenarios = Scenarios(self.model)
        self.scenarios.add_output("final_rev", lambda m: float(m.get_result_data("revenue")[-1]))

    def test_duplicate_output_raises(self):
        with pytest.raises(NameError):
            self.scenarios.add_output("final_rev", lambda m: 0)

    def test_run_scenarios_count(self):
        inputs_list = [Inp(revenue=r) for r in [500, 1000, 2000]]
        self.scenarios.run_scenarios(inputs_list)
        assert len(self.scenarios.results) == 3

    def test_get_scenarios_df_shape(self):
        inputs_list = [Inp(revenue=r) for r in [500, 1000, 2000]]
        self.scenarios.run_scenarios(inputs_list)
        df = self.scenarios.get_scenarios_df()
        assert len(df) == 3
        assert ("output", "final_rev") in df.columns
        assert ("input", "revenue") in df.columns

    def test_output_values(self):
        inputs_list = [Inp(revenue=1000.0, growth=0.0), Inp(revenue=2000.0, growth=0.0)]
        self.scenarios.run_scenarios(inputs_list)
        df = self.scenarios.get_scenarios_df()
        vals = df[("output", "final_rev")].tolist()
        assert vals[0] == pytest.approx(1000.0)
        assert vals[1] == pytest.approx(2000.0)
