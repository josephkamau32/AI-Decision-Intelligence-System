from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List
from ..schemas.dataset import DatasetUploadRequest, DatasetListResponse
from ..services.dataset_service import dataset_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/upload", response_model=dict)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(None)
):
    """Upload a dataset file."""
    logger.info(f"Uploading dataset: {name}")
    try:
        request = DatasetUploadRequest(name=name, description=description)
        dataset = await dataset_service.upload_dataset(file, request)
        logger.info(f"Dataset {name} uploaded successfully")
        return {"message": "Dataset uploaded successfully", "dataset": dataset.dict()}
    except Exception as e:
        logger.error(f"Failed to upload dataset {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/", response_model=DatasetListResponse)
async def list_datasets():
    """List all uploaded datasets."""
    logger.info("Listing datasets")
    datasets = dataset_service.list_datasets()
    logger.info(f"Found {len(datasets)} datasets")
    return DatasetListResponse(datasets=datasets)