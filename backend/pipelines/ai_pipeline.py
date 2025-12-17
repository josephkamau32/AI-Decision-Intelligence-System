from ..ml.data_ingestion import DataIngestion, DataProfiler
from ..ml.data_preprocessing import DataCleaner, FeatureEngineer
from ..ml.automl import AutoMLEngine
from typing import Dict, Any
import pandas as pd

class AIPipeline:
    def __init__(self):
        self.ingestion = DataIngestion()
        self.profiler = None
        self.cleaner = None
        self.engineer = None
        self.automl = AutoMLEngine()

    def run_pipeline(self, file_path: str) -> Dict[str, Any]:
        # Load data
        df = self.ingestion.load_data(file_path)
        # Profile
        self.profiler = DataProfiler(df)
        profile = self.profiler.profile()
        # Clean
        self.cleaner = DataCleaner(df)
        df = self.cleaner.handle_missing_values('mean')  # default
        # Feature engineering
        self.engineer = FeatureEngineer(df)
        df = self.engineer.encode_categorical('onehot')
        df = self.engineer.scale_numerical('standard')
        if profile['problem_type'] == 'time_series':
            # Assume date_col is detected, but for simplicity, assume first col or 'date'
            date_col = [col for col in df.columns if 'date' in col.lower() or pd.api.types.is_datetime64_any_dtype(df[col])][0] if any('date' in col.lower() for col in df.columns) else df.columns[0]
            df = self.engineer.prepare_time_series(date_col, profile['target_variable'])
        df = self.engineer.select_features(profile['target_variable'], k=10, problem_type=profile['problem_type'])
        # AutoML
        result = self.automl.train_and_select(df, profile['target_variable'], profile['problem_type'])
        return {
            'profile': profile,
            'processed_data': df,
            'automl_result': result
        }