import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.api.main import app
from backend.utils.auth import get_current_user

client = TestClient(app, raise_server_exceptions=False)

MOCK_USER = {"id": "test_user_123", "email": "test@example.com"}


class TestHealthAPI:
    def test_health_check(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data


class TestDatasetsAPIAuth:
    def test_unauthenticated_requests_rejected(self):
        """Ensure unauthenticated access to datasets is rejected with 401"""
        # Ensure no overrides
        app.dependency_overrides.pop(get_current_user, None)
        response = client.get("/api/v1/datasets/")
        assert response.status_code == 401


class TestDatasetsAPI:
    def setup_method(self):
        app.dependency_overrides[get_current_user] = lambda: MOCK_USER

    def teardown_method(self):
        app.dependency_overrides.pop(get_current_user, None)

    @patch("backend.api.datasets.dataset_service")
    def test_list_datasets(self, mock_service):
        mock_service.list_datasets.return_value = []
        response = client.get("/api/v1/datasets/")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert data["data"] == []

    @patch("backend.api.datasets.dataset_service")
    def test_upload_dataset_success(self, mock_service):
        mock_service.upload_dataset = AsyncMock()
        mock_service.upload_dataset.return_value = type(
            "Dataset", (), {"dict": lambda self: {"id": "1", "name": "test_dataset"}}
        )()
        # Mock file upload
        files = {"file": ("test.csv", "col1,col2\n1,2\n", "text/csv")}
        data = {"name": "test_dataset", "description": "test desc"}
        response = client.post("/api/v1/datasets/upload", files=files, data=data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "dataset" in data

    @patch("backend.api.datasets.dataset_service")
    def test_upload_dataset_failure(self, mock_service):
        mock_service.upload_dataset = AsyncMock(side_effect=Exception("Upload failed"))
        files = {"file": ("test.csv", "col1,col2\n1,2\n", "text/csv")}
        data = {"name": "test_dataset"}
        response = client.post("/api/v1/datasets/upload", files=files, data=data)
        assert response.status_code == 500
        data = response.json()
        assert "error" in data or "detail" in data
