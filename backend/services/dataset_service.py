import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile
import aiofiles
import pandas as pd
from ..schemas.dataset import DatasetInfo, DatasetUploadRequest
from ..utils.config import settings
import logging

logger = logging.getLogger(__name__)

class DatasetService:
    def __init__(self):
        self.datasets = []  # In-memory storage for demo

    async def upload_dataset(self, file: UploadFile, request: DatasetUploadRequest) -> DatasetInfo:
        """Upload a dataset file and extract metadata."""
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

        # Read file to get row and column counts
        rows = 0
        columns = 0
        try:
            if file_extension == '.csv':
                df = pd.read_csv(file_path)
            elif file_extension in ['.xlsx', '.xls']:
                df = pd.read_excel(file_path)
            elif file_extension == '.json':
                df = pd.read_json(file_path)
            elif file_extension == '.parquet':
                df = pd.read_parquet(file_path)
            else:
                df = None
            
            if df is not None:
                rows = len(df)
                columns = len(df.columns)
                logger.info(f"Dataset has {rows} rows and {columns} columns")
        except Exception as e:
            logger.error(f"Failed to read dataset for metadata: {e}")

        # Create dataset info with row and column counts
        dataset = DatasetInfo(
            id=str(uuid.uuid4()),
            name=request.name,
            description=request.description,
            file_path=file_path,
            created_at=datetime.utcnow(),
            size=len(content),
            rows=rows,
            columns=columns
        )

        # Store in memory (in real app, save to DB)
        self.datasets.append(dataset)

        logger.info(f"Dataset {request.name} uploaded: {rows} rows, {columns} columns")
        return dataset

    def list_datasets(self) -> List[DatasetInfo]:
        """List all uploaded datasets."""
        return self.datasets
    
    def get_dataset_by_id(self, dataset_id: str) -> Optional[DatasetInfo]:
        """Get dataset by ID."""
        for dataset in self.datasets:
            if dataset.id == dataset_id:
                return dataset
        return None
    
    def load_dataset_file(self, dataset_id: str) -> pd.DataFrame:
        """Load dataset file as DataFrame."""
        dataset = self.get_dataset_by_id(dataset_id)
        if dataset is None:
            raise ValueError(f"Dataset {dataset_id} not found")
        
        file_extension = os.path.splitext(dataset.file_path)[1]
        
        if file_extension == '.csv':
            return pd.read_csv(dataset.file_path)
        elif file_extension in ['.xlsx', '.xls']:
            return pd.read_excel(dataset.file_path)
        elif file_extension == '.json':
            return pd.read_json(dataset.file_path)
        elif file_extension == '.parquet':
            return pd.read_parquet(dataset.file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

dataset_service = DatasetService()