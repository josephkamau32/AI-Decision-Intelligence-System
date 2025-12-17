import mlflow

def setup_mlflow_registry():
    """Set up MLflow model registry."""
    tracking_uri = "file:./mlops/experiments"
    mlflow.set_tracking_uri(tracking_uri)
    # Model registry is automatically available with the tracking server
    print("MLflow model registry is ready.")

def register_model(run_id, model_name, model_path):
    """Register a model in MLflow registry."""
    tracking_uri = "file:./mlops/experiments"
    mlflow.set_tracking_uri(tracking_uri)
    model_uri = f"runs:/{run_id}/{model_path}"
    mlflow.register_model(model_uri, model_name)
    print(f"Model {model_name} registered successfully.")

if __name__ == "__main__":
    setup_mlflow_registry()