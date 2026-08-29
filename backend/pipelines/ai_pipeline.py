from ..ml.data_ingestion import DataIngestion, DataProfiler
from ..ml.data_preprocessing import DataCleaner, FeatureEngineer
from ..ml.automl import AutoML
from typing import Dict, Any
import pandas as pd

class AIPipeline:
    def __init__(self):
        self.profiler = None
        self.cleaner = None
        self.engineer = None
        self.automl = None

    def run_pipeline(self, file_path: str) -> Dict[str, Any]:
        # Load data
        df = DataIngestion.load_data(file_path)
        # Profile
        self.profiler = DataProfiler(df)
        profile = self.profiler.generate_profile()
        target_col = profile['target_variable']
        problem_type = profile['problem_type']

        # Clean
        self.cleaner = DataCleaner(df)
        df = self.cleaner.handle_missing_values('mean')
        
        # Feature engineering
        self.engineer = FeatureEngineer(df)
        df = self.engineer.encode_categorical('onehot')
        df = self.engineer.scale_numerical('standard')
        
        if problem_type == 'time_series':
            date_col = [col for col in df.columns if 'date' in col.lower() or pd.api.types.is_datetime64_any_dtype(df[col])][0] if any('date' in col.lower() for col in df.columns) else df.columns[0]
            df = self.engineer.prepare_time_series(date_col, target_col)
        
        df = self.engineer.select_features(target_col, k=10, problem_type=problem_type)
        
        # Separate features and target for AutoML fit
        X = df.drop(columns=[target_col])
        y = df[target_col]
        
        # AutoML
        self.automl = AutoML(task_type=problem_type)
        result = self.automl.fit(X, y)
        
        return {
            'profile': profile,
            'processed_data': df,
            'automl_result': result
        }