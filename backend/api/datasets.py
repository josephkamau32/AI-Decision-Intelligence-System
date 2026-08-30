from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from typing import List, Optional
from ..schemas.dataset import (
    DatasetUploadRequest,
    DatasetListResponse,
    PaginatedResponse,
)
from ..services.dataset_service import dataset_service
from ..utils.validators import (
    validate_file_extension,
    validate_file_size,
    validate_dataset_name,
    validate_pagination_params,
)
from ..utils.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload", response_model=dict)
async def upload_dataset(
    file: UploadFile = File(...), name: str = Form(...), description: str = Form(None)
):
    """Upload a dataset file."""
    logger.info(f"Uploading dataset: {name}")

    try:
        # Validate dataset name
        name_validation = validate_dataset_name(name)
        if not name_validation.valid:
            raise HTTPException(status_code=400, detail=name_validation.errors[0])

        # Validate file extension
        allowed_extensions = ["csv", "xlsx", "json", "parquet"]
        ext_validation = validate_file_extension(file.filename, allowed_extensions)
        if not ext_validation.valid:
            raise HTTPException(status_code=400, detail=ext_validation.errors[0])

        # Validate file size (read file to get size)
        content = await file.read()
        size_validation = validate_file_size(len(content), settings.max_upload_size)
        if not size_validation.valid:
            raise HTTPException(status_code=400, detail=size_validation.errors[0])

        # Reset file pointer
        await file.seek(0)

        request = DatasetUploadRequest(name=name, description=description)
        dataset = await dataset_service.upload_dataset(file, request)
        logger.info(f"Dataset {name} uploaded successfully")
        return {"message": "Dataset uploaded successfully", "dataset": dataset.dict()}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to upload dataset {name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/", response_model=PaginatedResponse)
async def list_datasets(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search query"),
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query(
        "desc", regex="^(asc|desc)$", description="Sort order"
    ),
):
    """List all uploaded datasets with pagination, search, and sorting."""
    logger.info(f"Listing datasets - page: {page}, page_size: {page_size}")

    # Validate pagination parameters
    pagination_validation = validate_pagination_params(page, page_size)
    if not pagination_validation.valid:
        raise HTTPException(status_code=400, detail=pagination_validation.errors[0])

    # Get datasets (this would normally query a database)
    all_datasets = dataset_service.list_datasets()

    # Apply search if provided
    if search:
        all_datasets = [
            d
            for d in all_datasets
            if search.lower() in d.name.lower()
            or (d.description and search.lower() in d.description.lower())
        ]

    # Calculate pagination
    total_count = len(all_datasets)
    total_pages = (total_count + page_size - 1) // page_size
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    # Get page of datasets
    page_datasets = all_datasets[start_idx:end_idx]

    logger.info(f"Found {total_count} datasets, returning page {page} of {total_pages}")

    return PaginatedResponse(
        data=page_datasets,
        total_count=total_count,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{dataset_id}")
async def get_dataset(dataset_id: str):
    """Get details of a specific dataset."""
    logger.info(f"Getting dataset: {dataset_id}")

    try:
        dataset = dataset_service.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=404, detail=f"Dataset not found: {dataset_id}"
            )

        logger.info(f"Retrieved dataset: {dataset_id}")
        return dataset.dict()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve dataset {dataset_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to retrieve dataset: {str(e)}"
        )


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: str):
    """Delete a dataset."""
    logger.info(f"Deleting dataset: {dataset_id}")

    try:
        success = dataset_service.delete_dataset(dataset_id)

        if not success:
            raise HTTPException(
                status_code=404, detail=f"Dataset not found: {dataset_id}"
            )

        logger.info(f"Dataset deleted successfully: {dataset_id}")
        return {"message": f"Dataset {dataset_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete dataset {dataset_id}: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to delete dataset: {str(e)}"
        )
