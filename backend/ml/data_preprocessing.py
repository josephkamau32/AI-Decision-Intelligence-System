import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, MinMaxScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, f_classif, f_regression
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class DataCleaner:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        logger.info(f"Initialized DataCleaner with DataFrame of shape {df.shape}")

    def handle_missing_values(self, strategy: str = 'mean') -> pd.DataFrame:
        logger.info(f"Handling missing values with strategy: {strategy}")
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        if strategy == 'drop':
            self.df = self.df.dropna()
            logger.info("Dropped rows with missing values")
        else:
            if num_cols.any():
                num_imputer = SimpleImputer(strategy=strategy if strategy in ['mean', 'median'] else 'mean')
                self.df[num_cols] = num_imputer.fit_transform(self.df[num_cols])
                logger.info(f"Imputed numerical columns: {list(num_cols)}")
            if cat_cols.any():
                cat_imputer = SimpleImputer(strategy='most_frequent')
                self.df[cat_cols] = cat_imputer.fit_transform(self.df[cat_cols])
                logger.info(f"Imputed categorical columns: {list(cat_cols)}")
        return self.df

class FeatureEngineer:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        logger.info(f"Initialized FeatureEngineer with DataFrame of shape {df.shape}")

    def encode_categorical(self, method: str = 'onehot') -> pd.DataFrame:
        logger.info(f"Encoding categorical variables with method: {method}")
        cat_cols = self.df.select_dtypes(include=['object', 'category']).columns
        if method == 'onehot':
            self.df = pd.get_dummies(self.df, columns=cat_cols, drop_first=True)
            logger.info(f"One-hot encoded columns: {list(cat_cols)}")
        elif method == 'label':
            le = LabelEncoder()
            for col in cat_cols:
                self.df[col] = le.fit_transform(self.df[col].astype(str))
            logger.info(f"Label encoded columns: {list(cat_cols)}")
        return self.df

    def scale_numerical(self, method: str = 'standard') -> pd.DataFrame:
        logger.info(f"Scaling numerical variables with method: {method}")
        num_cols = self.df.select_dtypes(include=[np.number]).columns
        if num_cols.empty:
            logger.info("No numerical columns to scale")
            return self.df
        if method == 'standard':
            scaler = StandardScaler()
        elif method == 'minmax':
            scaler = MinMaxScaler()
        self.df[num_cols] = scaler.fit_transform(self.df[num_cols])
        logger.info(f"Scaled numerical columns: {list(num_cols)}")
        return self.df

    def select_features(self, target: str, k: int = 10, problem_type: str = 'regression') -> pd.DataFrame:
        logger.info(f"Selecting top {k} features for {problem_type} problem")
        if target not in self.df.columns:
            logger.warning(f"Target column {target} not found in DataFrame")
            return self.df
        X = self.df.drop(columns=[target])
        y = self.df[target]
        if problem_type == 'classification':
            selector = SelectKBest(score_func=f_classif, k=min(k, X.shape[1]))
        else:
            selector = SelectKBest(score_func=f_regression, k=min(k, X.shape[1]))
        X_selected = selector.fit_transform(X, y)
        selected_cols = X.columns[selector.get_support()]
        self.df = pd.concat([pd.DataFrame(X_selected, columns=selected_cols, index=self.df.index), self.df[target]], axis=1)
        logger.info(f"Selected features: {list(selected_cols)}")
        return self.df

    def prepare_time_series(self, date_col: str, target: str) -> pd.DataFrame:
        logger.info(f"Preparing time series data with date column: {date_col}")
        if date_col in self.df.columns:
            self.df[date_col] = pd.to_datetime(self.df[date_col])
            self.df = self.df.sort_values(date_col)
            self.df = self.df.rename(columns={date_col: 'ds', target: 'y'})
            logger.info("Time series data prepared")
        else:
            logger.warning(f"Date column {date_col} not found")
        return self.df