"""Measure before/after serialize_bundle blob sizes."""
import io
import sys
import time

sys.path.insert(0, ".")

import joblib
import numpy as np
import pandas as pd

# Create realistic dataset
np.random.seed(42)
data = {}
for i in range(10):
    if i % 3 == 0:
        data["feature_%d" % i] = np.random.choice(["A", "B", "C", "D"], 500)
    else:
        data["feature_%d" % i] = np.random.randn(500)
data["target"] = np.random.choice([0, 1], 500)
df = pd.DataFrame(data)
X = df.drop(columns=["target"])
y = df["target"]
print("Dataset: %d rows x %d features" % (X.shape[0], X.shape[1]))

from backend.ml.automl import AutoML

automl = AutoML(task_type="auto", test_size=0.2)

t0 = time.time()
results = automl.fit(X, y, experiment_name="BlobTest", log_artifacts=False)
train_time = time.time() - t0
print("Training time: %.2fs" % train_time)
best = results["best_model"]
score = results["best_score"]
print("Best model: %s (score: %.4f)" % (best, score))

# OLD blob (full object)
buf_old = io.BytesIO()
joblib.dump(automl, buf_old, compress=3)
old_bytes = buf_old.getvalue()
old_kb = len(old_bytes) / 1024.0
print("OLD blob: %.1f KB (%.3f MB)" % (old_kb, old_kb / 1024.0))

# NEW blob (lean)
t2 = time.time()
new_bytes = automl.serialize_bundle()
ser_time = time.time() - t2
new_kb = len(new_bytes) / 1024.0
print("NEW blob: %.1f KB (%.3f MB)" % (new_kb, new_kb / 1024.0))
print("Serialize time: %.3fs" % ser_time)

reduction = (1 - len(new_bytes) / float(len(old_bytes))) * 100
print("Reduction: %.1f%%" % reduction)
print("End-to-end (train+serialize): %.2fs" % (train_time + ser_time))

loaded = AutoML.load_bundle(new_bytes)
preds = loaded.predict(X.head(3))
print("Deserialized predictions: %s" % preds.tolist())
print("Deserialization: OK")
