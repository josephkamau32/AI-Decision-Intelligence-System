import pandas as pd
import numpy as np
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class DataIngestion:
    @staticmethod
    def load_data(file_path: str) -> pd.DataFrame:
        logger.info(f"Loading data from {file_path}")
        # Support csv, json, etc. For now csv
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            logger.info(f"Loaded CSV data with shape {df.shape}")
            return df
        elif file_path.endswith('.json'):
            df = pd.read_json(file_path)
            logger.info(f"Loaded JSON data with shape {df.shape}")
            return df
        else:
            logger.error(f"Unsupported file format for {file_path}")
            raise ValueError("Unsupported file format")

class DataProfiler:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        logger.info(f"Initialized DataProfiler with DataFrame of shape {df.shape}")

    def detect_data_types(self) -> Dict[str, str]:
        data_types = {col: str(dtype) for col, dtype in self.df.dtypes.items()}
        logger.info(f"Detected data types: {data_types}")
        return data_types

    def detect_missing_values(self) -> Dict[str, int]:
        missing = self.df.isnull().sum().to_dict()
        logger.info(f"Detected missing values: {missing}")
        return missing

    def detect_outliers(self) -> Dict[str, List[int]]:
        outliers = {}
        for col in self.df.select_dtypes(include=[np.number]).columns:
            Q1 = self.df[col].quantile(0.25)
            Q3 = self.df[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            outlier_indices = self.df[(self.df[col] < lower_bound) | (self.df[col] > upper_bound)].index.tolist()
            outliers[col] = outlier_indices
        logger.info(f"Detected outliers in columns: {list(outliers.keys())}")
        return outliers

    def detect_target_variable(self) -> str:
        # Simple heuristic: last column
        target = self.df.columns[-1]
        logger.info(f"Detected target variable: {target}")
        return target

    def detect_problem_type(self, target: str) -> str:
        unique_vals = self.df[target].nunique()
        if self.df[target].dtype == 'object' or (isinstance(self.df[target].dtype, pd.CategoricalDtype)) or unique_vals < min(10, len(self.df) * 0.1):
            problem_type = 'classification'
        # Check for potential time-series: if any column looks like date
        date_cols = []
        for col in self.df.columns:
            if 'date' in col.lower() or 'time' in col.lower():
                date_cols.append(col)
            try:
                pd.to_datetime(self.df[col].head())
                date_cols.append(col)
            except:
                pass
        if date_cols:
            problem_type = 'time_series'
        else:
            problem_type = 'regression'
        logger.info(f"Detected problem type: {problem_type}")
        return problem_type

    def profile(self) -> Dict[str, Any]:
        logger.info("Starting data profiling")
        target = self.detect_target_variable()
        profile_result = {
            'data_types': self.detect_data_types(),
            'missing_values': self.detect_missing_values(),
            'outliers': self.detect_outliers(),
            'target_variable': target,
            'problem_type': self.detect_problem_type(target),
            'shape': self.df.shape,
            'columns': list(self.df.columns)
        }
        logger.info(f"Data profiling completed: shape {self.df.shape}, problem type {profile_result['problem_type']}")
        return profile_result