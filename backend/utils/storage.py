"""
Persistent SQL storage for users and API keys.
Supports PostgreSQL (production on Render) and SQLite (local development).
Note: Render Free PostgreSQL instances expire 90 days after creation
(~Dec 4, 2026 if created Sep 5, 2026).
"""

import io
import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import joblib
import pandas as pd
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    LargeBinary,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, scoped_session, sessionmaker

from .config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


class UserModel(Base):
    """SQLAlchemy model for persistent user accounts."""

    __tablename__ = "users"

    id = Column(String(128), primary_key=True)
    username = Column(String(128), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(64), default="user", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    last_login = Column(DateTime, nullable=True)
    extra_data = Column(Text, nullable=True)

    def to_dict(self) -> Dict[str, Any]:
        """Convert database record to dictionary matching auth and schema expectations."""
        d = {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "hashed_password": self.hashed_password,
            "role": self.role,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "failed_login_attempts": self.failed_login_attempts,
            "last_login": self.last_login,
        }
        if self.extra_data:
            try:
                extra = json.loads(self.extra_data)
                if isinstance(extra, dict):
                    # Don't overwrite primary fields with extra_data
                    for k, v in extra.items():
                        if k not in d:
                            d[k] = v
            except Exception:
                pass
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UserModel":
        """Build UserModel from dictionary."""
        known_keys = {
            "id",
            "username",
            "email",
            "hashed_password",
            "role",
            "is_active",
            "is_verified",
            "created_at",
            "updated_at",
            "failed_login_attempts",
            "last_login",
        }

        def parse_dt(val):
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val)
                except Exception:
                    return datetime.utcnow()
            elif isinstance(val, datetime):
                return val
            return None

        extra = {k: v for k, v in data.items() if k not in known_keys}

        return cls(
            id=str(data["id"]),
            username=str(data["username"]),
            email=str(data["email"]),
            hashed_password=str(data["hashed_password"]),
            role=str(data.get("role", "user")),
            is_active=bool(data.get("is_active", True)),
            is_verified=bool(data.get("is_verified", False)),
            created_at=parse_dt(data.get("created_at")) or datetime.utcnow(),
            updated_at=parse_dt(data.get("updated_at")) or datetime.utcnow(),
            failed_login_attempts=int(data.get("failed_login_attempts", 0) or 0),
            last_login=parse_dt(data.get("last_login")),
            extra_data=json.dumps(extra) if extra else None,
        )


class APIKeyModel(Base):
    """SQLAlchemy model for persistent API keys."""

    __tablename__ = "api_keys"

    key_hash = Column(String(128), primary_key=True)
    user_id = Column(String(128), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "name": self.name,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "is_active": self.is_active,
        }

    @classmethod
    def from_dict(cls, key_hash: str, data: Dict[str, Any]) -> "APIKeyModel":
        def parse_dt(val):
            if isinstance(val, str):
                try:
                    return datetime.fromisoformat(val)
                except Exception:
                    return None
            elif isinstance(val, datetime):
                return val
            return None

        return cls(
            key_hash=str(key_hash),
            user_id=str(data["user_id"]),
            name=str(data.get("name", "Default Key")),
            created_at=parse_dt(data.get("created_at")) or datetime.utcnow(),
            expires_at=parse_dt(data.get("expires_at")),
            is_active=bool(data.get("is_active", True)),
        )


class DatasetModel(Base):
    """SQLAlchemy model for persistent dataset files and metadata."""

    __tablename__ = "datasets"

    id = Column(String(128), primary_key=True)
    user_id = Column(String(128), nullable=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32), default="csv", nullable=False)
    size_bytes = Column(Integer, default=0, nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    column_count = Column(Integer, default=0, nullable=False)
    columns_json = Column(Text, nullable=True)
    file_content = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    extra_data = Column(Text, nullable=True)

    def to_dict(self, include_content: bool = False) -> Dict[str, Any]:
        column_names = []
        if self.columns_json:
            try:
                column_names = json.loads(self.columns_json)
            except Exception:
                column_names = []
        d = {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "filename": self.filename,
            "file_type": self.file_type,
            "file_path": f"storage/datasets/{self.id}_{self.filename}",
            "size": self.size_bytes,
            "file_size": self.size_bytes,
            "rows": self.row_count,
            "columns": self.column_count,
            "column_names": column_names,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if include_content:
            d["file_content"] = self.file_content
        if self.extra_data:
            try:
                extra = json.loads(self.extra_data)
                if isinstance(extra, dict):
                    for k, v in extra.items():
                        if k not in d:
                            d[k] = v
            except Exception:
                pass
        return d


class ModelRecord(Base):
    """SQLAlchemy model for persistent trained ML models."""

    __tablename__ = "trained_models"

    id = Column(String(128), primary_key=True)
    user_id = Column(String(128), nullable=True, index=True)
    dataset_id = Column(String(128), nullable=True, index=True)
    target_column = Column(String(255), nullable=False)
    task_type = Column(String(64), default="classification", nullable=False)
    best_model_name = Column(String(128), nullable=False)
    best_score = Column(Float, default=0.0, nullable=False)
    feature_names_json = Column(Text, nullable=True)
    metrics_json = Column(Text, nullable=True)
    all_results_json = Column(Text, nullable=True)
    model_artifact = Column(LargeBinary, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    extra_data = Column(Text, nullable=True)

    def to_dict(self, include_artifact: bool = False) -> Dict[str, Any]:
        feature_names = []
        if self.feature_names_json:
            try:
                feature_names = json.loads(self.feature_names_json)
            except Exception:
                feature_names = []
        metrics = {}
        if self.metrics_json:
            try:
                metrics = json.loads(self.metrics_json)
            except Exception:
                metrics = {}
        all_results = {}
        if self.all_results_json:
            try:
                all_results = json.loads(self.all_results_json)
            except Exception:
                all_results = {}

        primary_metric_name = (
            "accuracy" if self.task_type == "classification" else "r2_score"
        )
        metrics_payload = dict(metrics)
        if primary_metric_name not in metrics_payload:
            metrics_payload[primary_metric_name] = self.best_score
        metrics_payload["best_score"] = self.best_score

        d = {
            "model_id": self.id,
            "id": self.id,
            "user_id": self.user_id,
            "model_type": self.best_model_name,
            "best_model": self.best_model_name,
            "best_model_name": self.best_model_name,
            "dataset_id": self.dataset_id or "",
            "target_column": self.target_column,
            "task_type": self.task_type,
            "best_score": self.best_score,
            "features": len(feature_names),
            "feature_names": feature_names,
            "metrics": metrics_payload,
            "all_results": all_results,
            "created_at": (
                self.created_at.isoformat()
                if isinstance(self.created_at, datetime)
                else str(self.created_at)
            ),
        }
        if include_artifact:
            d["model_artifact"] = self.model_artifact
        if self.extra_data:
            try:
                extra = json.loads(self.extra_data)
                if isinstance(extra, dict):
                    for k, v in extra.items():
                        if k not in d:
                            d[k] = v
            except Exception:
                pass
        return d


def _get_engine(database_url: Optional[str] = None):
    """Configure SQLAlchemy engine supporting PostgreSQL and SQLite."""
    url = database_url or settings.database_url

    if url:
        # Render and Heroku use 'postgres://' which SQLAlchemy 1.4+ rejects;
        # normalize to 'postgresql://'
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)

        logger.info(f"Connecting to configured database: {url.split('@')[-1]}")
        if url.startswith("sqlite"):
            return create_engine(url, connect_args={"check_same_thread": False})
        else:
            return create_engine(
                url,
                pool_pre_ping=True,
                pool_recycle=300,
            )
    else:
        # Fallback to local SQLite database in storage/ directory
        storage_dir = Path("storage")
        storage_dir.mkdir(exist_ok=True)
        db_path = storage_dir / "decisera.db"
        sqlite_url = f"sqlite:///{db_path.resolve()}"
        logger.info(
            f"No DATABASE_URL configured. Using local SQLite database: {db_path}"
        )
        return create_engine(sqlite_url, connect_args={"check_same_thread": False})


class SQLUserStorage:
    """Dict-compatible wrapper around SQLAlchemy for user persistence."""

    def __init__(self, engine=None):
        self.engine = engine or _get_engine()
        Base.metadata.create_all(bind=self.engine)
        self.SessionFactory = scoped_session(sessionmaker(bind=self.engine))

    def _get_session(self):
        return self.SessionFactory()

    def get(self, user_id: str, default=None) -> Optional[Dict[str, Any]]:
        session = self._get_session()
        try:
            user = session.get(UserModel, str(user_id))
            if user:
                return user.to_dict()
            return default
        finally:
            session.close()

    def __getitem__(self, user_id: str) -> Dict[str, Any]:
        val = self.get(user_id)
        if val is None:
            raise KeyError(user_id)
        return val

    def __setitem__(self, user_id: str, data: Dict[str, Any]):
        session = self._get_session()
        try:
            data = dict(data)
            data["id"] = user_id
            existing = session.get(UserModel, str(user_id))
            if existing:
                # Update fields
                user_obj = UserModel.from_dict(data)
                existing.username = user_obj.username
                existing.email = user_obj.email
                existing.hashed_password = user_obj.hashed_password
                existing.role = user_obj.role
                existing.is_active = user_obj.is_active
                existing.is_verified = user_obj.is_verified
                existing.failed_login_attempts = user_obj.failed_login_attempts
                existing.last_login = user_obj.last_login
                existing.updated_at = datetime.utcnow()
                existing.extra_data = user_obj.extra_data
            else:
                user_obj = UserModel.from_dict(data)
                session.add(user_obj)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def __delitem__(self, user_id: str):
        session = self._get_session()
        try:
            existing = session.get(UserModel, str(user_id))
            if not existing:
                raise KeyError(user_id)
            session.delete(existing)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def __contains__(self, user_id: str) -> bool:
        session = self._get_session()
        try:
            return session.get(UserModel, str(user_id)) is not None
        finally:
            session.close()

    def items(self) -> List[Tuple[str, Dict[str, Any]]]:
        session = self._get_session()
        try:
            users = session.query(UserModel).all()
            return [(u.id, u.to_dict()) for u in users]
        finally:
            session.close()

    def values(self) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            users = session.query(UserModel).all()
            return [u.to_dict() for u in users]
        finally:
            session.close()

    def keys(self) -> List[str]:
        session = self._get_session()
        try:
            ids = session.query(UserModel.id).all()
            return [row[0] for row in ids]
        finally:
            session.close()

    def clear(self):
        session = self._get_session()
        try:
            session.query(UserModel).delete()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def __len__(self) -> int:
        session = self._get_session()
        try:
            return session.query(UserModel.id).count()
        finally:
            session.close()


class SQLAPIKeyStorage:
    """Dict-compatible wrapper around SQLAlchemy for API key persistence."""

    def __init__(self, engine=None):
        self.engine = engine or _get_engine()
        Base.metadata.create_all(bind=self.engine)
        self.SessionFactory = scoped_session(sessionmaker(bind=self.engine))

    def _get_session(self):
        return self.SessionFactory()

    def get(self, key_hash: str, default=None) -> Optional[Dict[str, Any]]:
        session = self._get_session()
        try:
            key_obj = session.get(APIKeyModel, str(key_hash))
            if key_obj:
                return key_obj.to_dict()
            return default
        finally:
            session.close()

    def __getitem__(self, key_hash: str) -> Dict[str, Any]:
        val = self.get(key_hash)
        if val is None:
            raise KeyError(key_hash)
        return val

    def __setitem__(self, key_hash: str, data: Dict[str, Any]):
        session = self._get_session()
        try:
            existing = session.get(APIKeyModel, str(key_hash))
            if existing:
                key_obj = APIKeyModel.from_dict(key_hash, data)
                existing.name = key_obj.name
                existing.expires_at = key_obj.expires_at
                existing.is_active = key_obj.is_active
            else:
                key_obj = APIKeyModel.from_dict(key_hash, data)
                session.add(key_obj)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def __delitem__(self, key_hash: str):
        session = self._get_session()
        try:
            existing = session.get(APIKeyModel, str(key_hash))
            if not existing:
                raise KeyError(key_hash)
            session.delete(existing)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def __contains__(self, key_hash: str) -> bool:
        session = self._get_session()
        try:
            return session.get(APIKeyModel, str(key_hash)) is not None
        finally:
            session.close()

    def items(self) -> List[Tuple[str, Dict[str, Any]]]:
        session = self._get_session()
        try:
            keys = session.query(APIKeyModel).all()
            return [(k.key_hash, k.to_dict()) for k in keys]
        finally:
            session.close()

    def values(self) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            keys = session.query(APIKeyModel).all()
            return [k.to_dict() for k in keys]
        finally:
            session.close()

    def keys(self) -> List[str]:
        session = self._get_session()
        try:
            keys = session.query(APIKeyModel.key_hash).all()
            return [row[0] for row in keys]
        finally:
            session.close()

    def clear(self):
        session = self._get_session()
        try:
            session.query(APIKeyModel).delete()
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def __len__(self) -> int:
        session = self._get_session()
        try:
            return session.query(APIKeyModel.key_hash).count()
        finally:
            session.close()


class SQLDatasetStorage:
    """Persistent storage for datasets with in-memory & local-disk tiered caching."""

    def __init__(self, engine=None, cache_dir: Optional[Path] = None):
        self.engine = engine or _get_engine()
        Base.metadata.create_all(bind=self.engine)
        self.SessionFactory = scoped_session(sessionmaker(bind=self.engine))
        self.cache_dir = cache_dir or Path("storage/datasets")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._df_cache: Dict[str, Tuple[float, pd.DataFrame]] = {}
        self._lock = threading.Lock()
        self._cache_ttl = 600  # 10 minutes memory cache TTL

    def _get_session(self):
        return self.SessionFactory()

    def save_dataset(
        self,
        dataset_id: str,
        name: str,
        filename: str,
        file_type: str,
        file_content: bytes,
        description: Optional[str] = None,
        user_id: Optional[str] = None,
        row_count: int = 0,
        column_count: int = 0,
        column_names: Optional[List[str]] = None,
        extra_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        session = self._get_session()
        try:
            record = session.get(DatasetModel, str(dataset_id))
            if record:
                record.name = name
                record.description = description
                record.filename = filename
                record.file_type = file_type
                record.size_bytes = len(file_content)
                record.row_count = row_count
                record.column_count = column_count
                record.columns_json = json.dumps(column_names or [])
                record.file_content = file_content
                record.user_id = user_id or record.user_id
                record.updated_at = datetime.utcnow()
                if extra_data:
                    record.extra_data = json.dumps(extra_data)
            else:
                record = DatasetModel(
                    id=str(dataset_id),
                    user_id=user_id,
                    name=name,
                    description=description,
                    filename=filename,
                    file_type=file_type,
                    size_bytes=len(file_content),
                    row_count=row_count,
                    column_count=column_count,
                    columns_json=json.dumps(column_names or []),
                    file_content=file_content,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                    extra_data=json.dumps(extra_data) if extra_data else None,
                )
                session.add(record)
            session.commit()

            # Cache to disk
            disk_file = self.cache_dir / f"{dataset_id}_{filename}"
            try:
                with open(disk_file, "wb") as f:
                    f.write(file_content)
            except Exception as e:
                logger.warning(f"Failed to cache dataset to disk: {e}")

            res = record.to_dict()
            return res
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_dataset(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        session = self._get_session()
        try:
            record = session.get(DatasetModel, str(dataset_id))
            if not record:
                return None
            if user_id is not None and record.user_id and record.user_id != user_id:
                return None
            return record.to_dict()
        finally:
            session.close()

    def get_dataset_content(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> Optional[bytes]:
        # Check disk cache first
        session = self._get_session()
        try:
            record = session.get(DatasetModel, str(dataset_id))
            if not record:
                return None
            if user_id is not None and record.user_id and record.user_id != user_id:
                return None
            disk_file = self.cache_dir / f"{dataset_id}_{record.filename}"
            if disk_file.exists() and disk_file.stat().st_size == record.size_bytes:
                try:
                    with open(disk_file, "rb") as f:
                        return f.read()
                except Exception:
                    pass
            return record.file_content
        finally:
            session.close()

    def get_dataset_dataframe(
        self, dataset_id: str, user_id: Optional[str] = None
    ) -> pd.DataFrame:
        now = time.time()
        with self._lock:
            cached = self._df_cache.get(dataset_id)
            if cached:
                cached_time, df = cached
                if now - cached_time < self._cache_ttl:
                    return df.copy()

        meta = self.get_dataset(dataset_id, user_id=user_id)
        if not meta:
            raise ValueError(f"Dataset {dataset_id} not found")

        content = self.get_dataset_content(dataset_id, user_id=user_id)
        if content is None:
            raise ValueError(f"Dataset content for {dataset_id} not found")

        file_type = meta.get("file_type", "csv").lower()
        if not file_type.startswith("."):
            file_type = f".{file_type}"

        buf = io.BytesIO(content)
        if file_type == ".csv":
            df = pd.read_csv(buf)
        elif file_type in [".xlsx", ".xls"]:
            df = pd.read_excel(buf)
        elif file_type == ".json":
            df = pd.read_json(buf)
        elif file_type == ".parquet":
            df = pd.read_parquet(buf)
        else:
            try:
                df = pd.read_csv(buf)
            except Exception:
                raise ValueError(f"Unsupported file format: {file_type}")

        with self._lock:
            self._df_cache[dataset_id] = (now, df.copy())

        return df

    def list_datasets(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            # Query metadata columns only (avoid transferring LargeBinary across WAN)
            query = session.query(
                DatasetModel.id,
                DatasetModel.user_id,
                DatasetModel.name,
                DatasetModel.description,
                DatasetModel.filename,
                DatasetModel.file_type,
                DatasetModel.size_bytes,
                DatasetModel.row_count,
                DatasetModel.column_count,
                DatasetModel.columns_json,
                DatasetModel.created_at,
                DatasetModel.updated_at,
                DatasetModel.extra_data,
            )
            if user_id is not None:
                query = query.filter(
                    (DatasetModel.user_id == user_id) | (DatasetModel.user_id.is_(None))
                )
            rows = query.order_by(DatasetModel.created_at.desc()).all()
            result = []
            for row in rows:
                col_names = []
                if row.columns_json:
                    try:
                        col_names = json.loads(row.columns_json)
                    except Exception:
                        col_names = []
                d = {
                    "id": row.id,
                    "user_id": row.user_id,
                    "name": row.name,
                    "description": row.description,
                    "filename": row.filename,
                    "file_type": row.file_type,
                    "file_path": f"storage/datasets/{row.id}_{row.filename}",
                    "size": row.size_bytes,
                    "file_size": row.size_bytes,
                    "rows": row.row_count,
                    "columns": row.column_count,
                    "column_names": col_names,
                    "created_at": row.created_at,
                    "updated_at": row.updated_at,
                }
                if row.extra_data:
                    try:
                        extra = json.loads(row.extra_data)
                        if isinstance(extra, dict):
                            for k, v in extra.items():
                                if k not in d:
                                    d[k] = v
                    except Exception:
                        pass
                result.append(d)
            return result
        finally:
            session.close()

    def delete_dataset(self, dataset_id: str, user_id: Optional[str] = None) -> bool:
        session = self._get_session()
        try:
            record = session.get(DatasetModel, str(dataset_id))
            if not record:
                return False
            if user_id is not None and record.user_id and record.user_id != user_id:
                return False

            filename = record.filename
            session.delete(record)
            session.commit()

            with self._lock:
                self._df_cache.pop(dataset_id, None)

            disk_file = self.cache_dir / f"{dataset_id}_{filename}"
            if disk_file.exists():
                try:
                    disk_file.unlink()
                except OSError:
                    pass
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def clear(self):
        session = self._get_session()
        try:
            session.query(DatasetModel).delete()
            session.commit()
            with self._lock:
                self._df_cache.clear()
        finally:
            session.close()

    def __len__(self) -> int:
        session = self._get_session()
        try:
            return session.query(DatasetModel.id).count()
        finally:
            session.close()


class SQLModelStorage:
    """Persistent storage for trained ML models with in-memory artifact caching."""

    def __init__(self, engine=None):
        self.engine = engine or _get_engine()
        Base.metadata.create_all(bind=self.engine)
        self.SessionFactory = scoped_session(sessionmaker(bind=self.engine))
        self._bundle_cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def _get_session(self):
        return self.SessionFactory()

    def save_model(
        self,
        model_id: str,
        dataset_id: str,
        target_column: str,
        task_type: str,
        best_model_name: str,
        best_score: float,
        feature_names: List[str],
        metrics: Dict[str, Any],
        all_results: Dict[str, Any],
        model_artifact: Optional[bytes] = None,
        user_id: Optional[str] = None,
        extra_data: Optional[Dict[str, Any]] = None,
        bundle: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        session = self._get_session()
        try:
            record = session.get(ModelRecord, str(model_id))
            if record:
                record.user_id = user_id or record.user_id
                record.dataset_id = dataset_id
                record.target_column = target_column
                record.task_type = task_type
                record.best_model_name = best_model_name
                record.best_score = float(best_score)
                record.feature_names_json = json.dumps(feature_names or [])
                record.metrics_json = json.dumps(metrics or {})
                record.all_results_json = json.dumps(all_results or {})
                if model_artifact:
                    record.model_artifact = model_artifact
                if extra_data:
                    record.extra_data = json.dumps(extra_data)
            else:
                record = ModelRecord(
                    id=str(model_id),
                    user_id=user_id,
                    dataset_id=dataset_id,
                    target_column=target_column,
                    task_type=task_type,
                    best_model_name=best_model_name,
                    best_score=float(best_score),
                    feature_names_json=json.dumps(feature_names or []),
                    metrics_json=json.dumps(metrics or {}),
                    all_results_json=json.dumps(all_results or {}),
                    model_artifact=model_artifact,
                    created_at=datetime.utcnow(),
                    extra_data=json.dumps(extra_data) if extra_data else None,
                )
                session.add(record)
            session.commit()

            res = record.to_dict()
            if bundle:
                with self._lock:
                    self._bundle_cache[model_id] = bundle

            return res
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def get_model(
        self, model_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        session = self._get_session()
        try:
            record = session.get(ModelRecord, str(model_id))
            if not record:
                return None
            if user_id is not None and record.user_id and record.user_id != user_id:
                return None
            return record.to_dict()
        finally:
            session.close()

    def get_model_bundle(
        self, model_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        with self._lock:
            if model_id in self._bundle_cache:
                return self._bundle_cache[model_id]

        session = self._get_session()
        try:
            record = session.get(ModelRecord, str(model_id))
            if not record or not record.model_artifact:
                return None
            if user_id is not None and record.user_id and record.user_id != user_id:
                return None

            buf = io.BytesIO(record.model_artifact)
            loaded_payload = joblib.load(buf)

            # Reconstruct bundle
            if isinstance(loaded_payload, dict):
                bundle = loaded_payload
            else:
                # Bare model or AutoML object
                feature_names = []
                if record.feature_names_json:
                    try:
                        feature_names = json.loads(record.feature_names_json)
                    except Exception:
                        feature_names = []
                all_results = {}
                if record.all_results_json:
                    try:
                        all_results = json.loads(record.all_results_json)
                    except Exception:
                        all_results = {}

                bundle = {
                    "automl": (
                        loaded_payload
                        if hasattr(loaded_payload, "best_model")
                        else None
                    ),
                    "model": getattr(loaded_payload, "best_model", loaded_payload),
                    "explainer": None,
                    "X_sample": getattr(loaded_payload, "X_train_processed", None),
                    "feature_names": feature_names,
                    "dataset_id": record.dataset_id or "",
                    "target_column": record.target_column,
                    "task_type": record.task_type,
                    "best_model_name": record.best_model_name,
                    "best_score": record.best_score,
                    "all_results": all_results,
                    "created_at": record.created_at.isoformat(),
                }

            with self._lock:
                self._bundle_cache[model_id] = bundle

            return bundle
        except Exception as e:
            logger.error(f"Failed to load model artifact for {model_id}: {e}")
            return None
        finally:
            session.close()

    def list_models(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        session = self._get_session()
        try:
            query = session.query(
                ModelRecord.id,
                ModelRecord.user_id,
                ModelRecord.dataset_id,
                ModelRecord.target_column,
                ModelRecord.task_type,
                ModelRecord.best_model_name,
                ModelRecord.best_score,
                ModelRecord.feature_names_json,
                ModelRecord.metrics_json,
                ModelRecord.all_results_json,
                ModelRecord.created_at,
                ModelRecord.extra_data,
            )
            if user_id is not None:
                query = query.filter(
                    (ModelRecord.user_id == user_id) | (ModelRecord.user_id.is_(None))
                )
            rows = query.order_by(ModelRecord.created_at.desc()).all()
            result = []
            for row in rows:
                feat_names = []
                if row.feature_names_json:
                    try:
                        feat_names = json.loads(row.feature_names_json)
                    except Exception:
                        feat_names = []
                metrics = {}
                if row.metrics_json:
                    try:
                        metrics = json.loads(row.metrics_json)
                    except Exception:
                        metrics = {}

                primary_metric = (
                    "accuracy" if row.task_type == "classification" else "r2_score"
                )
                metrics_payload = dict(metrics)
                if primary_metric not in metrics_payload:
                    metrics_payload[primary_metric] = row.best_score
                metrics_payload["best_score"] = row.best_score

                result.append(
                    {
                        "model_id": row.id,
                        "id": row.id,
                        "user_id": row.user_id,
                        "model_type": row.best_model_name,
                        "best_model": row.best_model_name,
                        "best_model_name": row.best_model_name,
                        "dataset_id": row.dataset_id or "",
                        "target_column": row.target_column,
                        "task_type": row.task_type,
                        "best_score": row.best_score,
                        "features": len(feat_names),
                        "feature_names": feat_names,
                        "metrics": metrics_payload,
                        "created_at": (
                            row.created_at.isoformat()
                            if isinstance(row.created_at, datetime)
                            else str(row.created_at)
                        ),
                    }
                )
            return result
        finally:
            session.close()

    def delete_model(self, model_id: str, user_id: Optional[str] = None) -> bool:
        session = self._get_session()
        try:
            record = session.get(ModelRecord, str(model_id))
            if not record:
                return False
            if user_id is not None and record.user_id and record.user_id != user_id:
                return False

            session.delete(record)
            session.commit()

            with self._lock:
                self._bundle_cache.pop(model_id, None)

            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def clear(self):
        session = self._get_session()
        try:
            session.query(ModelRecord).delete()
            session.commit()
            with self._lock:
                self._bundle_cache.clear()
        finally:
            session.close()

    def __len__(self) -> int:
        session = self._get_session()
        try:
            return session.query(ModelRecord.id).count()
        finally:
            session.close()


# Legacy JSONStorage preserved for backwards compatibility
class JSONStorage:
    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.lock = threading.Lock()
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        if self.file_path.exists():
            with open(self.file_path, "r") as f:
                try:
                    self._data = json.load(f)
                except json.JSONDecodeError:
                    self._data = {}
        else:
            self._data = {}
            self._save()

    def _save(self):
        def json_serial(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            raise TypeError(f"Type {type(obj)} not serializable")

        with open(self.file_path, "w") as f:
            json.dump(self._data, f, indent=2, default=json_serial)

    def get(self, key: str, default=None):
        with self.lock:
            return self._data.get(key, default)

    def __setitem__(self, key: str, value: Any):
        with self.lock:
            self._data[key] = value
            self._save()

    def __getitem__(self, key: str):
        with self.lock:
            return self._data[key]

    def __delitem__(self, key: str):
        with self.lock:
            del self._data[key]
            self._save()

    def __contains__(self, key: str):
        return key in self._data

    def keys(self):
        return self._data.keys()

    def values(self):
        return self._data.values()

    def items(self):
        return self._data.items()

    def clear(self):
        with self.lock:
            self._data = {}
            self._save()

    def __len__(self):
        return len(self._data)


# Shared engine for user, API key, dataset, and model storage
_default_engine = _get_engine()

# Initialize primary persistent storage
users_storage = SQLUserStorage(_default_engine)
api_keys_storage = SQLAPIKeyStorage(_default_engine)
datasets_storage = SQLDatasetStorage(_default_engine)
models_storage = SQLModelStorage(_default_engine)

# One-time automatic migration: if legacy users.json exists and SQL is empty
try:
    legacy_users_json = Path("storage/users.json")
    if legacy_users_json.exists() and len(users_storage) == 0:
        with open(legacy_users_json, "r") as f:
            legacy_data = json.load(f)
            if isinstance(legacy_data, dict):
                logger.info(
                    f"Migrating {len(legacy_data)} users from storage/users.json "
                    "to SQL database..."
                )
                for uid, udata in legacy_data.items():
                    if (
                        isinstance(udata, dict)
                        and "username" in udata
                        and "hashed_password" in udata
                    ):
                        users_storage[uid] = udata
                logger.info("✓ Legacy users migration completed.")
except Exception as migration_err:
    logger.warning(f"Could not check or migrate legacy users.json: {migration_err}")
