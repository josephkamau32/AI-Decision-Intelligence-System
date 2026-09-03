"""
End-to-end smoke test for AutoML preprocessing + training pipeline.
Tests that datasets with categorical strings, missing values, and datetime columns
can be trained without crashing.
"""
import sys
import os

# Ensure project root is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import pandas as pd
import numpy as np

# Suppress MLflow warnings for test
os.environ["MLFLOW_TRACKING_URI"] = "sqlite:///mlruns_test.db"

from backend.ml.automl import AutoML

np.random.seed(42)
n = 120

df = pd.DataFrame({
    'order_id': [f'ORD_{i:04d}' for i in range(n)],
    'created_at': pd.date_range('2024-01-01', periods=n, freq='D').astype(str),
    'city': np.random.choice(['Nairobi', 'Mombasa', 'Kisumu', 'Nakuru', None], size=n),
    'payment_method': np.random.choice(['Mpesa', 'Card', 'Airtel Money', 'Cash'], size=n),
    'product_price': np.random.uniform(500, 25000, size=n),
    'delivery_distance_km': np.random.uniform(1.5, 45.0, size=n),
    'rider_rating': np.random.choice([4.5, 4.8, 3.9, np.nan, 5.0], size=n),
    'status': np.random.choice(['Delivered', 'Cancelled', 'Pending'], size=n, p=[0.7, 0.2, 0.1]),
})

print("=" * 60)
print("TEST 1: Classification (predicting 'status')")
print("=" * 60)
X_clf = df.drop(columns=['status'])
y_clf = df['status']

automl_clf = AutoML(task_type="auto", test_size=0.2)
clf_res = automl_clf.fit(X_clf, y_clf, experiment_name="Test_Clf")
print(f"  Task type: {clf_res['task_type']}")
print(f"  Best model: {clf_res['best_model']}")
print(f"  Best score: {clf_res['best_score']:.4f}")
print(f"  All results: {list(clf_res['all_results'].keys())}")

# Test prediction on unseen row
test_row = df.iloc[[0]].drop(columns=['status'])
pred = automl_clf.predict(test_row)
print(f"  Prediction for row 0: {pred[0]} (true: {df.iloc[0]['status']})")
assert pred[0] in ['Delivered', 'Cancelled', 'Pending'], f"Unexpected prediction: {pred[0]}"
print("  [PASS] Classification test PASSED")

print()
print("=" * 60)
print("TEST 2: Regression (predicting 'product_price')")
print("=" * 60)
X_reg = df.drop(columns=['product_price'])
y_reg = df['product_price']

automl_reg = AutoML(task_type="regression", test_size=0.2)
reg_res = automl_reg.fit(X_reg, y_reg, experiment_name="Test_Reg")
print(f"  Task type: {reg_res['task_type']}")
print(f"  Best model: {reg_res['best_model']}")
print(f"  Best score (R2): {reg_res['best_score']:.4f}")

reg_pred = automl_reg.predict(df.iloc[[0]].drop(columns=['product_price']))
print(f"  Prediction for row 0: {reg_pred[0]:.2f} (true: {df.iloc[0]['product_price']:.2f})")
print("  [PASS] Regression test PASSED")

print()
print("=" * 60)
print("TEST 3: Edge case - all-string features")
print("=" * 60)
df_str = pd.DataFrame({
    'color': np.random.choice(['red', 'blue', 'green'], size=60),
    'shape': np.random.choice(['circle', 'square'], size=60),
    'size': np.random.choice(['small', 'medium', 'large'], size=60),
    'target': np.random.choice([0, 1], size=60),
})

automl_str = AutoML(task_type="auto", test_size=0.2)
str_res = automl_str.fit(df_str.drop(columns=['target']), df_str['target'], experiment_name="Test_Str")
print(f"  Task type: {str_res['task_type']}")
print(f"  Best model: {str_res['best_model']}")
print(f"  Best score: {str_res['best_score']:.4f}")
print("  [PASS] All-string features test PASSED")

print()
print("=" * 60)
print("ALL 3 TESTS PASSED SUCCESSFULLY!")
print("=" * 60)
