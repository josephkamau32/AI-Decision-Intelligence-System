from alibi_detect.cd import TabularDrift
from alibi_detect.utils.saving import save_detector, load_detector
import numpy as np
import pandas as pd
import os
from typing import Dict, Any, Optional

class DataDriftDetector:
    def __init__(self, reference_data: pd.DataFrame, model_id: str):
        self.model_id = model_id
        self.reference_data = reference_data
        self.detector = None
        self.drift_history = []
        self.setup_detector()

    def setup_detector(self):
        """Initialize the drift detector with reference data."""
        try:
            # Convert to numpy array
            X_ref = self.reference_data.values

            # Initialize drift detector
            self.detector = TabularDrift(X_ref, p_val=0.05)

        except Exception as e:
            print(f"Failed to setup drift detector: {e}")
            self.detector = None

    def detect_drift(self, new_data: pd.DataFrame) -> Dict[str, Any]:
        """Detect data drift in new data."""
        if self.detector is None:
            return {"drift_detected": False, "message": "Detector not initialized"}

        try:
            X_new = new_data.values
            preds = self.detector.predict(X_new)

            drift_detected = preds['data']['is_drift'] == 1
            p_value = preds['data']['p_val']

            result = {
                "drift_detected": drift_detected,
                "p_value": float(p_value),
                "threshold": 0.05,
                "feature_drift": preds['data']['p_val_per_feature'].tolist() if 'p_val_per_feature' in preds['data'] else None
            }

            # Store in history
            self.drift_history.append({
                "timestamp": pd.Timestamp.now(),
                "drift_detected": drift_detected,
                "p_value": float(p_value),
                "data_size": len(new_data)
            })

            return result

        except Exception as e:
            return {"drift_detected": False, "error": str(e)}

    def get_drift_history(self) -> list:
        """Get drift detection history."""
        return self.drift_history

    def save_detector(self, path: str):
        """Save the detector to disk."""
        if self.detector:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            save_detector(self.detector, path)

    def load_detector(self, path: str):
        """Load detector from disk."""
        if os.path.exists(path):
            self.detector = load_detector(path)