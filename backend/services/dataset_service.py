import io
import os
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import UploadFile
import aiofiles
import pandas as pd
from ..schemas.dataset import DatasetInfo, DatasetUploadRequest
from ..utils.config import settings
from ..utils.storage import datasets_storage
import logging

logger = logging.getLogger(__name__)


class DatasetService:
    def __init__(self, storage=None):
        self.storage = storage or datasets_storage

    @property
    def datasets(self) -> List[DatasetInfo]:
        """Backwards compatibility property for any code inspecting dataset_service.datasets."""
        return self.list_datasets()

    async def upload_dataset(
        self,
        file: UploadFile,
        request: DatasetUploadRequest,
        user_id: Optional[str] = None,
    ) -> DatasetInfo:
        """Upload a dataset file, extract metadata, and persist to SQL database."""
        content = await file.read()
        file_extension = os.path.splitext(file.filename or "")[1].lower() or ".csv"
        dataset_id = str(uuid.uuid4())

        # Extract row count, column count, and column names directly from bytes
        rows = 0
        columns = 0
        column_names = []
        try:
            buf = io.BytesIO(content)
            if file_extension == ".csv":
                df = pd.read_csv(buf)
            elif file_extension in [".xlsx", ".xls"]:
                df = pd.read_excel(buf)
            elif file_extension == ".json":
                df = pd.read_json(buf)
            elif file_extension == ".parquet":
                df = pd.read_parquet(buf)
            else:
                try:
                    df = pd.read_csv(buf)
                except Exception:
                    df = None

            if df is not None:
                rows = len(df)
                columns = len(df.columns)
                column_names = [str(c) for c in df.columns.tolist()]
                logger.info(
                    f"Dataset {request.name} parsed: {rows} rows, {columns} columns"
                )
        except Exception as e:
            logger.error(f"Failed to inspect dataset {request.name}: {e}")

        # Persist to database & local cache
        saved_dict = self.storage.save_dataset(
            dataset_id=dataset_id,
            name=request.name,
            filename=file.filename or f"{dataset_id}{file_extension}",
            file_type=file_extension,
            file_content=content,
            description=request.description,
            user_id=user_id,
            row_count=rows,
            column_count=columns,
            column_names=column_names,
        )

        dataset = DatasetInfo(
            id=saved_dict["id"],
            name=saved_dict["name"],
            description=saved_dict.get("description"),
            file_path=saved_dict.get(
                "file_path", f"storage/datasets/{dataset_id}_{file.filename}"
            ),
            created_at=saved_dict["created_at"],
            size=saved_dict["size"],
            rows=saved_dict["rows"],
            columns=saved_dict["columns"],
            column_names=saved_dict["column_names"],
        )

        logger.info(
            f"Dataset {request.name} ({dataset_id}) saved to SQL storage for user {user_id}"
        )
        return dataset

    def list_datasets(self, user_id: Optional[str] = None) -> List[DatasetInfo]:
        """List all datasets from SQL storage, optionally scoped to a user."""
        records = self.storage.list_datasets(user_id=user_id)
        result = []
        for r in records:
            created_at = r.get("created_at")
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at)
                except Exception:
                    created_at = datetime.utcnow()
            elif not isinstance(created_at, datetime):
                created_at = datetime.utcnow()

            result.append(
                DatasetInfo(
                    id=r["id"],
                    name=r["name"],
                    description=r.get("description"),
                    file_path=r.get(
                        "file_path", f"storage/datasets/{r['id']}_{r['filename']}"
                    ),
                    created_at=created_at,
                    size=r.get("size", 0),
                    rows=r.get("rows", 0),
                    columns=r.get("columns", 0),
                    column_names=r.get("column_names", []),
                )
            )
        return result

    def get_dataset_by_id(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> Optional[DatasetInfo]:
        """Get dataset metadata by ID."""
        r = self.storage.get_dataset(dataset_id, user_id=user_id)
        if not r:
            return None
        created_at = r.get("created_at")
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except Exception:
                created_at = datetime.utcnow()
        elif not isinstance(created_at, datetime):
            created_at = datetime.utcnow()

        return DatasetInfo(
            id=r["id"],
            name=r["name"],
            description=r.get("description"),
            file_path=r.get("file_path", f"storage/datasets/{r['id']}_{r['filename']}"),
            created_at=created_at,
            size=r.get("size", 0),
            rows=r.get("rows", 0),
            columns=r.get("columns", 0),
            column_names=r.get("column_names", []),
        )

    def get_dataset(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> Optional[DatasetInfo]:
        """Alias for get_dataset_by_id."""
        return self.get_dataset_by_id(dataset_id, user_id=user_id)

    def delete_dataset(self, dataset_id: str, user_id: Optional[str] = None) -> bool:
        """Delete a dataset from SQL storage and disk cache."""
        return self.storage.delete_dataset(dataset_id, user_id=user_id)

    def get_dataset_columns(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> List[str]:
        """Retrieve the column names of a dataset."""
        dataset = self.get_dataset_by_id(dataset_id, user_id=user_id)
        if dataset and getattr(dataset, "column_names", None):
            return dataset.column_names
        try:
            df = self.load_dataset_file(dataset_id, user_id=user_id)
            cols = [str(c) for c in df.columns.tolist()]
            return cols
        except Exception as e:
            logger.error(f"Failed to extract columns for dataset {dataset_id}: {e}")
            return []

    def load_dataset_file(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Load dataset as DataFrame (cached in RAM & disk)."""
        return self.storage.get_dataset_dataframe(dataset_id, user_id=user_id)

    def load_dataset_dataframe(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> pd.DataFrame:
        """Alias for load_dataset_file (used by insights_service)."""
        return self.load_dataset_file(dataset_id, user_id=user_id)


dataset_service = DatasetService()
