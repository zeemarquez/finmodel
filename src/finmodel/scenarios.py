from finmodel.model import Model
from typing import Callable, Any
from tqdm import tqdm 
from dataclasses import dataclass, field, replace, asdict
import pandas as pd


class Scenarios():
    def __init__(self, model:Model):
        self.model = model
        self.output_extractors:dict[str, Callable[[Model], Any]] = {}
        self.results = {}

    def add_output(self, name:str, extractor_function:Callable[[Model], Any]):
        if name in self.output_extractors:
            raise NameError(f"Output <{name}> is already defined. Choose another name")
        self.output_extractors[name] = extractor_function

    def __process_outputs(self)->dict[str, Any]:
        outputs = {}
        for name, func in self.output_extractors.items():
            outputs[name] = func(self.model)

        return outputs
    
    def run_scenarios(self, scenarios_inputs:list):
        i = 0
        for inputs in tqdm(scenarios_inputs, desc="Calculating scenarios"):
            self.model.inputs = inputs
            self.model.calculate()
            results = {
                'outputs':self.__process_outputs(),
                'inputs':asdict(inputs)
            }

            self.results[i] = results
            i += 1

    def get_scenarios_df(self)->pd.DataFrame:
        df_data = {}
        for i, scenario in self.results.items():
            for input, value in scenario['inputs'].items():
                key = ('input', input)
                if key in df_data:
                    df_data[key].append(value)
                else:
                    df_data[key] = [value]


            for output, value in scenario['outputs'].items():
                key = ('output', output)
                if key in df_data:
                    df_data[key].append(value)
                else:
                    df_data[key] = [value]

        return pd.DataFrame(df_data)

        





        



    