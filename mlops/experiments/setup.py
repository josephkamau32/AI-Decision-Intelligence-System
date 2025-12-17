import mlflow
import os

def setup_mlflow_experiment():
    """Set up MLflow experiment for tracking."""
    tracking_uri = "file:./mlops/experiments"
    experiment_name = "AI Decision Intelligence"
    mlflow.set_tracking_uri(tracking_uri)
    experiment = mlflow.get_experiment_by_name(experiment_name)
    if experiment is None:
        mlflow.create_experiment(experiment_name)
    mlflow.set_experiment(experiment_name)

if __name__ == "__main__":
    setup_mlflow_experiment()
    print("MLflow experiment set up successfully.")