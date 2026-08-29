"""
Basic test structure for AutoML and inference
"""
import pytest
import pandas as pd
import numpy as np
from backend.ml.automl import AutoML
from backend.ml.inference import ModelInference
from backend.ml.explainability import ModelExplainer
from backend.ml.data_preprocessing import DataCleaner, FeatureEngineer

class TestAutoML:
    """Test AutoML engine"""
    
    def test_classification_training(self):
        """Test classification model training"""
        # Create synthetic classification data
        np.random.seed(42)
        X = pd.DataFrame(np.random.randn(100, 5), columns=[f'feature_{i}' for i in range(5)])
        y = pd.Series(np.random.randint(0, 2, 100), name='target')
        
        # Train AutoML
        automl = AutoML(task_type='classification', test_size=0.2)
        results = automl.fit(X, y, log_artifacts=False)
        
        # Assertions
        assert results['best_model'] is not None
        assert results['best_score'] > 0
        assert results['task_type'] == 'classification'
        assert len(results['all_results']) > 0
    
    def test_regression_training(self):
        """Test regression model training"""
        # Create synthetic regression data
        np.random.seed(42)
        X = pd.DataFrame(np.random.randn(100, 5), columns=[f'feature_{i}' for i in range(5)])
        y = pd.Series(np.random.randn(100), name='target')
        
        # Train AutoML
        automl = AutoML(task_type='regression', test_size=0.2)
        results = automl.fit(X, y, log_artifacts=False)
        
        # Assertions
        assert results['best_model'] is not None
        assert results['task_type'] == 'regression'
        assert 'r2_score' in results['all_results'][results['best_model']]
    
    def test_predict(self):
        """Test predictions"""
        # Train model
        np.random.seed(42)
        X = pd.DataFrame(np.random.randn(100, 5), columns=[f'feature_{i}' for i in range(5)])
        y = pd.Series(np.random.randint(0, 2, 100))
        
        automl = AutoML(task_type='classification')
        automl.fit(X, y, use_cv=False, log_artifacts=False)
        
        # Make prediction
        X_test = pd.DataFrame(np.random.randn(5, 5), columns=[f'feature_{i}' for i in range(5)])
        predictions = automl.predict(X_test)
        
        # Assertions
        assert len(predictions) == 5

class TestDataPreprocessing:
    """Test data preprocessing components"""
    
    def test_missing_value_handling(self):
        """Test missing value imputation"""
        df = pd.DataFrame({
            'num1': [1.0, 2.0, np.nan, 4.0, 5.0],
            'num2': [np.nan, 2.0, 3.0, 4.0, 5.0]
        })
        
        cleaner = DataCleaner(df)
        cleaned = cleaner.handle_missing_values(strategy='mean')
        
        # Check no missing values remain
        assert cleaned.isna().sum().sum() == 0
        assert cleaned['num1'].iloc[2] == 3.0  # Mean of [1, 2, 4, 5]
    
    def test_categorical_encoding(self):
        """Test categorical encoding"""
        df = pd.DataFrame({
            'cat1': ['a', 'b', 'c', 'a', 'b'],
            'num1': [1, 2, 3, 4, 5]
        })
        
        engineer = FeatureEngineer(df)
        encoded = engineer.encode_categorical(method='label')
        
        # Check that categorical column is encoded
        assert pd.api.types.is_numeric_dtype(encoded['cat1'])

class TestExplainability:
    """Test SHAP explainability"""
    
    def test_global_importance(self):
        """Test global feature importance"""
        # Train a simple model
        np.random.seed(42)
        X = pd.DataFrame(np.random.randn(100, 5), columns=[f'feature_{i}' for i in range(5)])
        y = pd.Series(np.random.randint(0, 2, 100))
        
        automl = AutoML(task_type='classification')
        automl.fit(X, y, use_cv=False, log_artifacts=False)
        
        # Create explainer
        explainer = ModelExplainer(automl.best_model, X.head(20))
        importance = explainer.get_global_importance(X.head(20), top_n=5)
        
        # Assertions
        assert 'feature_importance' in importance
        assert len(importance['feature_importance']) <= 5
    
    def test_local_explanation(self):
        """Test instance-level explanation"""
        # Train model
        np.random.seed(42)
        X = pd.DataFrame(np.random.randn(100, 5), columns=[f'feature_{i}' for i in range(5)])
        y = pd.Series(np.random.randint(0, 2, 100))
        
        automl = AutoML(task_type='classification')
        automl.fit(X, y, use_cv=False, log_artifacts=False)
        
        # Create explainer and explain one instance
        explainer = ModelExplainer(automl.best_model, X.head(20))
        explanation = explainer.explain_instance(X.iloc[0:1])
        
        # Assertions
        assert 'features' in explanation or 'explanations' in explanation

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
