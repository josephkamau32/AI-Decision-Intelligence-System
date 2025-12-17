import os
import uuid
from datetime import datetime
from typing import List
from fastapi import UploadFile
import aiofiles
from ..schemas.dataset import DatasetInfo, DatasetUploadRequest
from ..utils.config import settings

from ..ml.data_ingestion import DataIngestion, DataProfiler

class DatasetService:
    def __init__(self):
        self.datasets = []  # In-memory storage for demo

    async def upload_dataset(self, file: UploadFile, request: DatasetUploadRequest) -> DatasetInfo:
        """Upload a dataset file."""
        # Ensure upload directory exists
        os.makedirs(settings.upload_dir, exist_ok=True)

        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join(settings.upload_dir, unique_filename)

        # Save file asynchronously
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        # Create dataset info
        dataset = DatasetInfo(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            file_path=file_path,
            created_at=datetime.utcnow(),
            size=len(content)
        )

        # Store in memory (in real app, save to DB)
        self.datasets.append(dataset)

        return dataset

    def list_datasets(self) -> List[DatasetInfo]:
        """List all uploaded datasets."""
        return self.datasets

dataset_service = DatasetService()