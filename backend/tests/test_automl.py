import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
from backend.ml.automl import AutoMLEngine

class TestAutoMLEngine:
    @pytest.fixture
    def sample_classification_df(self):
        return pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5, 6],
            'feature2': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'target': [0, 1, 0, 1, 0, 1]
        })

    @pytest.fixture
    def sample_regression_df(self):
        return pd.DataFrame({
            'feature1': [1, 2, 3, 4, 5, 6],
            'feature2': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6],
            'target': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        })

    @pytest.fixture
    def sample_time_series_df(self):
        dates = pd.date_range('2020-01-01', periods=20, freq='D')
        values = np.random.randn(20).cumsum()
        return pd.DataFrame({'ds': dates, 'y': values})

    @patch('backend.ml.automl.mlflow')
    def test_train_and_select_classification(self, mock_mlflow, sample_classification_df):
        mock_mlflow.start_run.return_value.__enter__.return_value = None
        mock_mlflow.active_run.info.run_id = 'test_run_id'
        engine = AutoMLEngine()
        result = engine.train_and_select(sample_classification_df, 'target', 'classification')
        assert 'best_model' in result
        assert 'best_score' in result
        assert 'trained_model' in result
        assert 'all_results' in result
        assert 'run_id' in result

    @patch('backend.ml.automl.mlflow')
    def test_train_and_select_regression(self, mock_mlflow, sample_regression_df):
        mock_mlflow.start_run.return_value.__enter__.return_value = None
        mock_mlflow.active_run.info.run_id = 'test_run_id'
        engine = AutoMLEngine()
        result = engine.train_and_select(sample_regression_df, 'target', 'regression')
        assert 'best_model' in result
        assert 'best_score' in result
        assert 'trained_model' in result
        assert 'all_results' in result
        assert 'run_id' in result

    @patch('backend.ml.automl.mlflow')
    def test_train_and_select_time_series(self, mock_mlflow, sample_time_series_df):
        mock_mlflow.start_run.return_value.__enter__.return_value = None
        mock_mlflow.active_run.info.run_id = 'test_run_id'
        engine = AutoMLEngine()
        result = engine.train_and_select(sample_time_series_df, 'y', 'time_series')
        assert 'best_model' in result
        assert 'best_score' in result
        assert 'trained_model' in result
        assert 'all_results' in result
        assert 'run_id' in result