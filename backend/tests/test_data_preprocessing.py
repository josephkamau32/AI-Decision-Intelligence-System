import pytest
import pandas as pd
import numpy as np
from backend.ml.data_preprocessing import DataCleaner, FeatureEngineer

class TestDataCleaner:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'num_col': [1.0, 2.0, np.nan, 4.0],
            'cat_col': ['A', 'B', None, 'C'],
            'target': [0, 1, 0, 1]
        })

    def test_handle_missing_values_drop(self, sample_df):
        cleaner = DataCleaner(sample_df)
        result = cleaner.handle_missing_values(strategy='drop')
        assert result.shape[0] == 2  # One row with nan dropped

    def test_handle_missing_values_mean(self, sample_df):
        cleaner = DataCleaner(sample_df)
        result = cleaner.handle_missing_values(strategy='mean')
        assert not result['num_col'].isnull().any()
        assert result['num_col'].iloc[2] == 2.333333333333333  # mean of 1,2,4

    def test_handle_missing_values_median(self, sample_df):
        cleaner = DataCleaner(sample_df)
        result = cleaner.handle_missing_values(strategy='median')
        assert not result['num_col'].isnull().any()
        assert result['num_col'].iloc[2] == 2.0  # median of 1,2,4

class TestFeatureEngineer:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            'num_col': [1.0, 2.0, 3.0, 4.0],
            'cat_col': ['A', 'B', 'A', 'C'],
            'target': [0, 1, 0, 1]
        })

    def test_encode_categorical_onehot(self, sample_df):
        engineer = FeatureEngineer(sample_df)
        result = engineer.encode_categorical(method='onehot')
        assert 'cat_col_A' in result.columns
        assert 'cat_col_B' in result.columns
        assert 'cat_col_C' in result.columns
        assert 'cat_col' not in result.columns

    def test_encode_categorical_label(self, sample_df):
        engineer = FeatureEngineer(sample_df)
        result = engineer.encode_categorical(method='label')
        assert result['cat_col'].dtype == int
        assert result['cat_col'].iloc[0] == result['cat_col'].iloc[2]  # A encoded same

    def test_scale_numerical_standard(self, sample_df):
        engineer = FeatureEngineer(sample_df)
        result = engineer.scale_numerical(method='standard')
        assert result['num_col'].mean() < 0.01  # approximately 0
        assert abs(result['num_col'].std() - 1) < 0.01  # approximately 1

    def test_scale_numerical_minmax(self, sample_df):
        engineer = FeatureEngineer(sample_df)
        result = engineer.scale_numerical(method='minmax')
        assert result['num_col'].min() == 0
        assert result['num_col'].max() == 1

    def test_select_features(self, sample_df):
        engineer = FeatureEngineer(sample_df)
        result = engineer.select_features(target='target', k=1, problem_type='classification')
        assert result.shape[1] == 2  # selected feature + target
        assert 'target' in result.columns

    def test_prepare_time_series(self):
        df = pd.DataFrame({
            'date': ['2020-01-01', '2020-01-02', '2020-01-03'],
            'value': [1, 2, 3],
            'target': [10, 20, 30]
        })
        engineer = FeatureEngineer(df)
        result = engineer.prepare_time_series(date_col='date', target='target')
        assert 'ds' in result.columns
        assert 'y' in result.columns
        assert result['ds'].dtype == 'datetime64[ns]'