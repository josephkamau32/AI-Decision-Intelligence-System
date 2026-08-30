"""
Tests for DataIngestion and DataProfiler
"""

import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from backend.ml.data_ingestion import DataIngestion, DataProfiler


class TestDataIngestion:
    def test_load_csv(self):
        data = {"col1": [1, 2, 3], "col2": ["a", "b", "c"]}
        df = pd.DataFrame(data)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            df.to_csv(f, index=False)
            file_path = f.name
        try:
            loaded_df = DataIngestion.load_data(file_path)
            pd.testing.assert_frame_equal(loaded_df, df)
        finally:
            os.unlink(file_path)

    def test_load_json(self):
        data = {"col1": [1, 2, 3], "col2": ["a", "b", "c"]}
        df = pd.DataFrame(data)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            df.to_json(f, orient="records")
            file_path = f.name
        try:
            loaded_df = DataIngestion.load_data(file_path)
            assert loaded_df.shape == df.shape
            assert set(loaded_df.columns) == set(df.columns)
        finally:
            os.unlink(file_path)

    def test_load_unsupported_format(self):
        with pytest.raises(ValueError, match="Unsupported file format"):
            DataIngestion.load_data("test.unsupported")


class TestDataProfiler:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame(
            {
                "num_col": [1.0, 2.0, np.nan, 4.0],
                "cat_col": ["A", "B", "A", "C"],
                "date_col": ["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-04"],
                "target": [0, 1, 0, 1],
            }
        )

    def test_detect_column_types(self, sample_df):
        profiler = DataProfiler(sample_df)
        types = profiler.detect_column_types()
        assert "num_col" in types
        assert "cat_col" in types
        assert "date_col" in types

    def test_detect_missing_values(self, sample_df):
        profiler = DataProfiler(sample_df)
        missing = profiler.detect_missing_values()
        assert missing["num_col"] == 1
        assert missing["cat_col"] == 0

    def test_detect_outliers(self, sample_df):
        profiler = DataProfiler(sample_df)
        outliers = profiler.detect_outliers()
        assert isinstance(outliers, dict)
        assert "num_col" in outliers

    def test_detect_target_variable(self, sample_df):
        profiler = DataProfiler(sample_df)
        target, problem_type = profiler.detect_target_variable()
        assert target in sample_df.columns
        assert problem_type in ["classification", "regression", "time_series", "auto"]

    def test_detect_problem_type_classification(self, sample_df):
        profiler = DataProfiler(sample_df)
        problem_type = profiler.detect_problem_type("target")
        assert problem_type == "classification"

    def test_generate_profile(self, sample_df):
        profiler = DataProfiler(sample_df)
        profile = profiler.generate_profile()
        assert "column_types" in profile
        assert "missing_values" in profile
        assert "outliers" in profile
        assert "target_variable" in profile
        assert "problem_type" in profile
        assert "shape" in profile
        assert "columns" in profile
        assert "columns_info" in profile

    def test_get_data_quality_issues(self, sample_df):
        profiler = DataProfiler(sample_df)
        profiler.generate_profile()
        issues = profiler.get_data_quality_issues()
        assert isinstance(issues, list)
