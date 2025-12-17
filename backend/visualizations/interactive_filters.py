import pandas as pd
from typing import Dict, Any, List

class InteractiveFilters:
    def __init__(self, df: pd.DataFrame):
        self.df = df

    def generate_filters(self) -> Dict[str, Any]:
        filters = {}
        for col in self.df.columns:
            if self.df[col].dtype == 'object' or pd.api.types.is_categorical_dtype(self.df[col]):
                unique_vals = self.df[col].unique().tolist()
                filters[col] = {
                    'type': 'dropdown',
                    'options': unique_vals
                }
            elif pd.api.types.is_numeric_dtype(self.df[col]):
                min_val = float(self.df[col].min())
                max_val = float(self.df[col].max())
                filters[col] = {
                    'type': 'range',
                    'min': min_val,
                    'max': max_val
                }
            elif pd.api.types.is_datetime64_any_dtype(self.df[col]):
                min_date = self.df[col].min().isoformat()
                max_date = self.df[col].max().isoformat()
                filters[col] = {
                    'type': 'date_range',
                    'min': min_date,
                    'max': max_date
                }
        return filters