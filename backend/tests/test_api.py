import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
from backend.api.main import app

client = TestClient(app)

class TestHealthAPI:
    def test_health_check(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

class TestDatasetsAPI:
    @patch('backend.api.datasets.dataset_service')
    def test_list_datasets(self, mock_service):
        mock_service.list_datasets.return_value = []
        response = client.get("/api/v1/datasets/")
        assert response.status_code == 200
        data = response.json()
        assert "datasets" in data
        assert data["datasets"] == []

    @patch('backend.api.datasets.dataset_service')
    def test_upload_dataset_success(self, mock_service):
        mock_service.upload_dataset = AsyncMock()
        mock_service.upload_dataset.return_value = type('Dataset', (), {'dict': lambda: {'id': 1, 'name': 'test'}})()
        # Mock file upload
        files = {'file': ('test.csv', 'col1,col2\n1,2\n', 'text/csv')}
        data = {'name': 'test_dataset', 'description': 'test desc'}
        response = client.post("/api/v1/datasets/upload", files=files, data=data)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "dataset" in data

    @patch('backend.api.datasets.dataset_service')
    def test_upload_dataset_failure(self, mock_service):
        mock_service.upload_dataset = AsyncMock(side_effect=Exception("Upload failed"))
        files = {'file': ('test.csv', 'col1,col2\n1,2\n', 'text/csv')}
        data = {'name': 'test_dataset'}
        response = client.post("/api/v1/datasets/upload", files=files, data=data)
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data