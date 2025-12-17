"""
Enhanced data ingestion with auto-profiling and quality detection
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class DataProfiler:
    """Automatically profile and analyze datasets"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.profile = {}
    
    def detect_column_types(self) -> Dict[str, str]:
        """
        Auto-detect column types beyond pandas dtype
        
        Returns:
            Dict mapping column names to detected types
        """
        column_types = {}
        
        for col in self.df.columns:
            col_data = self.df[col]
            
            # Skip if all null
            if col_data.isna().all():
                column_types[col] = 'unknown'
                continue
            
            # Check for datetime
            if pd.api.types.is_datetime64_any_dtype(col_data):
                column_types[col] = 'datetime'
            elif pd.api.types.is_numeric_dtype(col_data):
                # Check if it's actually categorical (few unique values)
                unique_ratio = col_data.nunique() / len(col_data)
                if unique_ratio < 0.05 and col_data.nunique() < 20:
                    column_types[col] = 'categorical_numeric'
                else:
                    column_types[col] = 'numeric'
            elif pd.api.types.is_object_dtype(col_data):
                # Try to parse as datetime
                try:
                    pd.to_datetime(col_data.dropna().head(100), errors='raise')
                    column_types[col] = 'datetime_string'
                except:
                    # Check if categorical
                    if col_data.nunique() / len(col_data) < 0.1:
                        column_types[col] = 'categorical'
                    else:
                        column_types[col] = 'text'
            else:
                column_types[col] = str(col_data.dtype)
        
        return column_types
    
    def detect_target_variable(self) -> Tuple[str, str]:
        """
        Auto-detect likely target variable
        
        Returns:
            Tuple of (target_column_name, problem_type)
        """
        candidates = []
        
        for col in self.df.columns:
            col_data = self.df[col]
            
            # Skip non-numeric for now
            if not pd.api.types.is_numeric_dtype(col_data):
                continue
            
            # Check cardinality
            unique_count = col_data.nunique()
            unique_ratio = unique_count / len(col_data)
            
            # Binary classification candidate
            if unique_count == 2:
                candidates.append((col, 'classification', 100))
            # Multi-class classification candidate (2-20 unique values, low ratio)
            elif 2 < unique_count <= 20 and unique_ratio < 0.1:
                candidates.append((col, 'classification', 80))
            # Regression candidate (many unique values)
            elif unique_ratio > 0.1:
                candidates.append((col, 'regression', 50))
        
        if not candidates:
            # Default to last column
            last_col = self.df.columns[-1]
            return last_col, 'auto'
        
        # Sort by score and return best
        candidates.sort(key=lambda x: x[2], reverse=True)
        return candidates[0][0], candidates[0][1]
    
    def detect_outliers(self, column: str, method: str = 'iqr') -> np.ndarray:
        """
        Detect outliers in a column
        
        Args:
            column: Column name
            method: 'iqr' or 'zscore'
            
        Returns:
            Boolean array indicating outliers
        """
        if column not in self.df.columns:
            return np.array([False] * len(self.df))
        
        col_data = self.df[column]
        
        if not pd.api.types.is_numeric_dtype(col_data):
            return np.array([False] * len(self.df))
        
        if method == 'iqr':
            Q1 = col_data.quantile(0.25)
            Q3 = col_data.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            return (col_data < lower_bound) | (col_data > upper_bound)
        
        elif method == 'zscore':
            z_scores = np.abs((col_data - col_data.mean()) / col_data.std())
            return z_scores > 3
        
        return np.array([False] * len(self.df))
    
    def generate_profile(self) -> Dict[str, Any]:
        """
        Generate comprehensive data profile
        
        Returns:
            Dictionary with profile information
        """
        logger.info(f"Profiling dataset with shape {self.df.shape}")
        
        # Basic info
        profile = {
            'rows': len(self.df),
            'columns': len(self.df.columns),
            'memory_mb': self.df.memory_usage(deep=True).sum() / 1024**2,
            'duplicates': int(self.df.duplicated().sum()),
            'column_types': self.detect_column_types(),
            'columns': []
        }
        
        # Detect target
        target_col, problem_type = self.detect_target_variable()
        profile['suggested_target'] = target_col
        profile['suggested_problem_type'] = problem_type
        
        # Analyze each column
        for col in self.df.columns:
            col_data = self.df[col]
            
            col_profile = {
                'name': col,
                'dtype': str(col_data.dtype),
                'detected_type': profile['column_types'][col],
                'unique_values': int(col_data.nunique()),
                'missing_count': int(col_data.isna().sum()),
                'missing_percent': float(col_data.isna().sum() / len(col_data) * 100),
                'is_target_candidate': col == target_col
            }
            
            # Numeric statistics
            if pd.api.types.is_numeric_dtype(col_data):
                col_profile['statistics'] = {
                    'mean': float(col_data.mean()) if not col_data.isna().all() else None,
                    'std': float(col_data.std()) if not col_data.isna().all() else None,
                    'min': float(col_data.min()) if not col_data.isna().all() else None,
                    'max': float(col_data.max()) if not col_data.isna().all() else None,
                    'median': float(col_data.median()) if not col_data.isna().all() else None,
                    'q25': float(col_data.quantile(0.25)) if not col_data.isna().all() else None,
                    'q75': float(col_data.quantile(0.75)) if not col_data.isna().all() else None
                }
                
                # Outlier detection
                outliers = self.detect_outliers(col)
                col_profile['outliers_count'] = int(outliers.sum())
                col_profile['outliers_percent'] = float(outliers.sum() / len(col_data) * 100)
            
            # Categorical statistics
            elif profile['column_types'][col] in ['categorical', 'categorical_numeric']:
                value_counts = col_data.value_counts().head(10)
                col_profile['top_values'] = [
                    {'value': str(val), 'count': int(count)}
                    for val, count in value_counts.items()
                ]
            
            profile['columns'].append(col_profile)
        
        self.profile = profile
        logger.info(f"Profile generated. Suggested target: {target_col} ({problem_type})")
        
        return profile
    
    def get_data_quality_issues(self) -> List[Dict[str, Any]]:
        """
        Identify data quality issues
        
        Returns:
            List of issues found
        """
        issues = []
        
        # Check for high missing values
        for col_profile in self.profile.get('columns', []):
            if col_profile['missing_percent'] > 50:
                issues.append({
                    'severity': 'high',
                    'column': col_profile['name'],
                    'issue': 'high_missing_values',
                    'details': f"{col_profile['missing_percent']:.1f}% missing values"
                })
            elif col_profile['missing_percent'] > 20:
                issues.append({
                    'severity': 'medium',
                    'column': col_profile['name'],
                    'issue': 'moderate_missing_values',
                    'details': f"{col_profile['missing_percent']:.1f}% missing values"
                })
            
            # Check for high outliers
            if 'outliers_percent' in col_profile and col_profile['outliers_percent'] > 10:
                issues.append({
                    'severity': 'medium',
                    'column': col_profile['name'],
                    'issue': 'high_outliers',
                    'details': f"{col_profile['outliers_percent']:.1f}% outliers detected"
                })
            
            # Check for constant columns
            if col_profile['unique_values'] == 1:
                issues.append({
                    'severity': 'high',
                    'column': col_profile['name'],
                    'issue': 'constant_column',
                    'details': 'Column has only one unique value'
                })
        
        # Check for high duplicates
        if self.profile.get('duplicates', 0) / self.profile.get('rows', 1) > 0.1:
            issues.append({
                'severity': 'medium',
                'column': None,
                'issue': 'high_duplicates',
                'details': f"{self.profile['duplicates']} duplicate rows found"
            })
        
        return issues

def ingest_and_profile_dataset(file_path: str) -> Dict[str, Any]:
    """
    Load dataset and generate comprehensive profile
    
    Args:
        file_path: Path to dataset file
        
    Returns:
        Dictionary with dataframe and profile
    """
    logger.info(f"Ingesting dataset from {file_path}")
    
    # Load based on file extension
    file_path = Path(file_path)
    
    if file_path.suffix == '.csv':
        df = pd.read_csv(file_path)
    elif file_path.suffix in ['.xlsx', '.xls']:
        df = pd.read_excel(file_path)
    elif file_path.suffix == '.json':
        df = pd.read_json(file_path)
    elif file_path.suffix == '.parquet':
        df = pd.read_parquet(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path.suffix}")
    
    logger.info(f"Loaded dataset with shape {df.shape}")
    
    # Profile the dataset
    profiler = DataProfiler(df)
    profile = profiler.generate_profile()
    issues = profiler.get_data_quality_issues()
    
    return {
        'dataframe': df,
        'profile': profile,
        'quality_issues': issues
    }