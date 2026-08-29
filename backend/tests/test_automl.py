"""
Tests for AutoML engine
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from backend.ml.automl import AutoML


class TestAutoML:
    @pytest.fixture
    def classification_data(self):
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0] * 3,
            'feature2': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0] * 3
        })
        y = pd.Series([0, 1, 0, 1, 0, 1, 0, 1, 0, 1] * 3, name='target')
        return X, y

    @pytest.fixture
    def regression_data(self):
        np.random.seed(42)
        X = pd.DataFrame({
            'feature1': [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0] * 3,
            'feature2': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0] * 3
        })
        y = pd.Series([1.5, 2.5, 3.5, 4.5, 5.5, 6.5, 7.5, 8.5, 9.5, 10.5] * 3, name='target')
        return X, y

    @pytest.fixture
    def time_series_data(self):
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', periods=30, freq='D')
        values = np.linspace(10, 50, 30) + np.random.normal(0, 1, 30)
        X = pd.DataFrame({'date': dates})
        y = pd.Series(values, name='target')
        return X, y

    def test_fit_classification(self, classification_data):
        X, y = classification_data
        automl = AutoML(task_type='classification', test_size=0.2)
        result = automl.fit(X, y, experiment_name='test_automl_cls', log_artifacts=False)

        assert result['best_model'] is not None
        assert result['best_score'] > 0
        assert result['task_type'] == 'classification'
        assert isinstance(result['all_results'], dict)
        assert automl.best_model is not None

    def test_fit_regression(self, regression_data):
        X, y = regression_data
        automl = AutoML(task_type='regression', test_size=0.2)
        result = automl.fit(X, y, experiment_name='test_automl_reg', log_artifacts=False)

        assert result['best_model'] is not None
        assert result['task_type'] == 'regression'
        assert isinstance(result['all_results'], dict)
        assert automl.best_model is not None

    def test_fit_time_series(self, time_series_data):
        X, y = time_series_data
        automl = AutoML(task_type='time_series', test_size=0.2)
        result = automl.fit(X, y, experiment_name='test_automl_ts', log_artifacts=False)

        assert result['best_model'] is not None
        assert result['task_type'] == 'time_series'
        assert isinstance(result['all_results'], dict)
        assert automl.best_model is not None

    def test_predict_and_proba(self, classification_data):
        X, y = classification_data
        automl = AutoML(task_type='classification', test_size=0.2)
        automl.fit(X, y, experiment_name='test_automl_pred', use_cv=False, log_artifacts=False)

        preds = automl.predict(X.head(5))
        assert len(preds) == 5

        probs = automl.predict_proba(X.head(5))
        assert len(probs) == 5

    def test_save_and_load_model(self, classification_data):
        X, y = classification_data
        automl = AutoML(task_type='classification', test_size=0.2)
        automl.fit(X, y, experiment_name='test_automl_persist', use_cv=False, log_artifacts=False)

        with tempfile.TemporaryDirectory() as tmp_dir:
            model_file = os.path.join(tmp_dir, 'model.joblib')
            automl.save_model(model_file)
            assert os.path.exists(model_file)

            loaded_model = automl.load_model(model_file)
            assert loaded_model is not None

    @pytest.mark.slow
    def test_fit_classification_with_mlflow_packaging(self, classification_data):
        """End-to-end test with full MLflow artifact logging and model registration"""
        X, y = classification_data
        automl = AutoML(task_type='classification', test_size=0.2)
        # Uses full defaults: use_cv=True, log_artifacts=True
        result = automl.fit(X, y, experiment_name='test_automl_cls_slow')

        assert result['best_model'] is not None
        assert result['best_score'] > 0
        assert automl.best_model is not None

    @pytest.mark.slow
    def test_fit_regression_with_mlflow_packaging(self, regression_data):
        """End-to-end test with full MLflow artifact logging and model registration"""
        X, y = regression_data
        automl = AutoML(task_type='regression', test_size=0.2)
        # Uses full defaults: use_cv=True, log_artifacts=True
        result = automl.fit(X, y, experiment_name='test_automl_reg_slow')

        assert result['best_model'] is not None
        assert result['task_type'] == 'regression'
        assert automl.best_model is not None