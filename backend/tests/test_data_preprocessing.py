import pytest
import pandas as pd
import numpy as np
from backend.ml.data_preprocessing import DataCleaner, FeatureEngineer


class TestDataCleaner:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame(
            {
                "num_col": [1.0, 2.0, np.nan, 4.0],
                "cat_col": ["A", "B", None, "C"],
                "target": [0, 1, 0, 1],
            }
        )

    def test_handle_missing_values_drop(self, sample_df):
        cleaner = DataCleaner(sample_df)
        result = cleaner.handle_missing_values(strategy="drop")
        assert result.shape[0] == 3  # One row with nan/None dropped (row 2)

    def test_handle_missing_values_mean(self, sample_df):
        cleaner = DataCleaner(sample_df)
        result = cleaner.handle_missing_values(strategy="mean")
        assert not result["num_col"].isnull().any()
        assert result["num_col"].iloc[2] == pytest.approx(7.0 / 3.0)  # mean of 1, 2, 4

    def test_handle_missing_values_median(self, sample_df):
        cleaner = DataCleaner(sample_df)
        result = cleaner.handle_missing_values(strategy="median")
        assert not result["num_col"].isnull().any()
        assert result["num_col"].iloc[2] == 2.0  # median of 1, 2, 4


class TestFeatureEngineer:
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame(
            {
                "num_col": [1.0, 2.0, 3.0, 4.0],
                "cat_col": ["A", "B", "A", "C"],
                "target": [0, 1, 0, 1],
            }
        )

    def test_encode_categorical_onehot_default(self, sample_df):
        """Default drop_first=True drops first category dummy."""
        engineer = FeatureEngineer(sample_df)
        result = engineer.encode_categorical(method="onehot", drop_first=True)
        assert "cat_col_B" in result.columns
        assert "cat_col_C" in result.columns
        assert "cat_col_A" not in result.columns
        assert "cat_col" not in result.columns

    def test_encode_categorical_onehot_no_drop(self, sample_df):
        """Configured drop_first=False preserves all category dummy columns."""
        engineer = FeatureEngineer(sample_df)
        result = engineer.encode_categorical(method="onehot", drop_first=False)
        assert "cat_col_A" in result.columns
        assert "cat_col_B" in result.columns
        assert "cat_col_C" in result.columns
        assert "cat_col" not in result.columns

    def test_encode_categorical_label(self, sample_df):
        engineer = FeatureEngineer(sample_df)
        result = engineer.encode_categorical(method="label")
        assert np.issubdtype(result["cat_col"].dtype, np.integer)
        assert result["cat_col"].iloc[0] == result["cat_col"].iloc[2]  # A encoded same

    def test_encode_categorical_label_multiple_columns_persistence(self):
        """Regression test: verify per-column LabelEncoder instances are stored in self.encoders and invert independently."""
        df = pd.DataFrame(
            {
                "color": ["red", "blue", "green", "red"],
                "size": ["S", "M", "L", "XL"],
                "target": [0, 1, 0, 1],
            }
        )
        engineer = FeatureEngineer(df)
        encoded_df = engineer.encode_categorical(method="label")

        # Verify distinct encoders are registered
        assert "color" in engineer.encoders
        assert "size" in engineer.encoders
        assert engineer.encoders["color"] is not engineer.encoders["size"]

        # Verify each encoder retained its specific classes independently
        assert set(engineer.encoders["color"].classes_) == {"red", "blue", "green"}
        assert set(engineer.encoders["size"].classes_) == {"S", "M", "L", "XL"}

        # Verify inverse transforms work correctly per column
        recovered_colors = engineer.encoders["color"].inverse_transform(
            encoded_df["color"]
        )
        recovered_sizes = engineer.encoders["size"].inverse_transform(
            encoded_df["size"]
        )
        assert list(recovered_colors) == ["red", "blue", "green", "red"]
        assert list(recovered_sizes) == ["S", "M", "L", "XL"]

    def test_scale_numerical_standard(self, sample_df):
        engineer = FeatureEngineer(sample_df)
        result = engineer.scale_numerical(method="standard")
        assert abs(result["num_col"].mean()) < 0.01  # approximately 0
        assert abs(np.std(result["num_col"]) - 1.0) < 0.01  # population std is 1.0

    def test_scale_numerical_minmax(self, sample_df):
        engineer = FeatureEngineer(sample_df)
        result = engineer.scale_numerical(method="minmax")
        assert result["num_col"].min() == 0
        assert result["num_col"].max() == 1

    def test_select_features(self, sample_df):
        engineer = FeatureEngineer(sample_df)
        result = engineer.select_features(
            target="target", k=1, problem_type="classification"
        )
        assert "target" in result.columns
        assert "num_col" in result.columns

    def test_select_features_missing_target_raises_value_error(self, sample_df):
        """Verify select_features raises ValueError when target column is missing."""
        engineer = FeatureEngineer(sample_df)
        with pytest.raises(
            ValueError, match="Target column 'missing_target' not found"
        ):
            engineer.select_features(
                target="missing_target", k=1, problem_type="classification"
            )

    def test_prepare_time_series(self):
        df = pd.DataFrame(
            {
                "date": ["2020-01-01", "2020-01-02", "2020-01-03"],
                "value": [1, 2, 3],
                "target": [10, 20, 30],
            }
        )
        engineer = FeatureEngineer(df)
        result = engineer.prepare_time_series(date_col="date", target="target")
        assert "ds" in result.columns
        assert "y" in result.columns
        assert result["ds"].dtype == "datetime64[ns]"
