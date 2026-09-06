"""
Tests for persistent SQL database storage (SQLite and PostgreSQL).
Validates CRUD, bcrypt password hash round-trips, duplicate constraints,
and URL normalization.
"""

import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException

import backend.utils.storage as storage_mod
from backend.utils.storage import (
    SQLUserStorage,
    SQLAPIKeyStorage,
    SQLDatasetStorage,
    SQLModelStorage,
    UserModel,
    Base,
)
from backend.utils.auth import (
    get_password_hash,
    verify_password,
    register_user,
    authenticate_user,
)


@pytest.fixture
def test_db_engine():
    """Isolated in-memory SQLite database engine for storage tests."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def user_storage(test_db_engine):
    return SQLUserStorage(engine=test_db_engine)


@pytest.fixture
def api_key_storage(test_db_engine):
    return SQLAPIKeyStorage(engine=test_db_engine)


class TestSQLUserStorage:

    def test_password_hash_round_trip_and_validation(
        self, user_storage, test_db_engine
    ):
        """
        Explicit round-trip test:
        1. Hashes plaintext password with real bcrypt.
        2. Persists to SQL database.
        3. Retrieves user record back from SQL storage (both via .get() and ['key']).
        4. Confirms bcrypt verification succeeds against original plaintext password.
        5. Confirms bcrypt verification fails against wrong passwords.
        6. Confirms raw hash stored in the DB row matches bcrypt signature ($2b$...).
        """
        plaintext = "SuperSecretP@ssw0rd!2026"
        hashed = get_password_hash(plaintext)

        # Confirm valid bcrypt hash signature
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

        user_data = {
            "id": "user_hash_test_001",
            "username": "hashtestuser",
            "email": "hashtest@example.com",
            "hashed_password": hashed,
            "role": "user",
            "is_active": True,
            "is_verified": False,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "failed_login_attempts": 0,
            "last_login": None,
        }

        # Save to database
        user_storage["user_hash_test_001"] = user_data

        # 1. Retrieve using .get()
        retrieved_get = user_storage.get("user_hash_test_001")
        assert retrieved_get is not None
        assert retrieved_get["username"] == "hashtestuser"
        assert retrieved_get["hashed_password"] == hashed

        # 2. Retrieve using bracket indexing
        retrieved_bracket = user_storage["user_hash_test_001"]
        assert retrieved_bracket["hashed_password"] == hashed

        # 3. Verify bcrypt password validation round-trip
        assert verify_password(plaintext, retrieved_get["hashed_password"]) is True
        assert (
            verify_password("WrongPassword123!", retrieved_get["hashed_password"])
            is False
        )
        assert verify_password(plaintext, retrieved_bracket["hashed_password"]) is True

        # 4. Verify raw DB record directly from the database session
        session = user_storage._get_session()
        try:
            db_row = session.get(UserModel, "user_hash_test_001")
            assert db_row is not None
            assert db_row.hashed_password == hashed
            assert verify_password(plaintext, db_row.hashed_password) is True
        finally:
            session.close()

    def test_duplicate_username_constraint_rejection(self, user_storage, monkeypatch):
        """
        Duplicate username test:
        Confirms attempting to register two accounts with the same username fails
        with HTTPException 400 'Username already exists'.
        """
        monkeypatch.setattr("backend.utils.auth.users_db", user_storage)

        # Register first user
        u1 = register_user(
            username="duplicate_user",
            email="first_email@example.com",
            password="Password123!",
            role="user",
        )
        assert u1["username"] == "duplicate_user"

        # Attempt to register second user with same username but different email
        with pytest.raises(HTTPException) as exc_info:
            register_user(
                username="duplicate_user",
                email="second_email@example.com",
                password="Password123!",
                role="user",
            )

        assert exc_info.value.status_code == 400
        assert "Username already exists" in str(exc_info.value.detail)

    def test_duplicate_email_constraint_rejection(self, user_storage, monkeypatch):
        """
        Duplicate email test:
        Confirms attempting to register two accounts with the same email fails
        with HTTPException 400 'Email already exists'.
        """
        monkeypatch.setattr("backend.utils.auth.users_db", user_storage)

        # Register first user
        u1 = register_user(
            username="unique_user_one",
            email="shared_email@example.com",
            password="Password123!",
            role="user",
        )
        assert u1["email"] == "shared_email@example.com"

        # Attempt to register second user with different username but same email
        with pytest.raises(HTTPException) as exc_info:
            register_user(
                username="unique_user_two",
                email="shared_email@example.com",
                password="Password123!",
                role="user",
            )

        assert exc_info.value.status_code == 400
        assert "Email already exists" in str(exc_info.value.detail)

    def test_duplicate_sql_schema_unique_constraints(self, user_storage):
        """
        Confirms database-level UNIQUE constraints raise IntegrityError on duplicate
        username or email insertions directly against the UserModel table.
        """
        session = user_storage._get_session()
        try:
            user1 = UserModel(
                id="user_db_uniq_1",
                username="schema_unique_user",
                email="schema_unique@example.com",
                hashed_password="some_hashed_password",
                role="user",
            )
            session.add(user1)
            session.commit()

            # Duplicate username directly into database table
            user2 = UserModel(
                id="user_db_uniq_2",
                username="schema_unique_user",
                email="different_email@example.com",
                hashed_password="some_hashed_password",
                role="user",
            )
            session.add(user2)
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()

            # Duplicate email directly into database table
            user3 = UserModel(
                id="user_db_uniq_3",
                username="different_user",
                email="schema_unique@example.com",
                hashed_password="some_hashed_password",
                role="user",
            )
            session.add(user3)
            with pytest.raises(IntegrityError):
                session.commit()
            session.rollback()
        finally:
            session.close()

    def test_crud_operations(self, user_storage):
        """Verify get, set, contains, del, items, values, keys, len, clear."""
        assert len(user_storage) == 0
        assert "test_id" not in user_storage

        user_data = {
            "id": "test_id",
            "username": "cruduser",
            "email": "crud@example.com",
            "hashed_password": "fake_hash_value",
            "role": "admin",
            "is_active": True,
            "is_verified": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "failed_login_attempts": 0,
            "last_login": None,
        }

        # Set
        user_storage["test_id"] = user_data
        assert len(user_storage) == 1
        assert "test_id" in user_storage

        # Get & Getitem
        retrieved = user_storage["test_id"]
        assert retrieved["username"] == "cruduser"
        assert retrieved["role"] == "admin"

        # Update
        user_data["role"] = "viewer"
        user_storage["test_id"] = user_data
        assert user_storage["test_id"]["role"] == "viewer"

        # Iterators
        assert "test_id" in user_storage.keys()
        assert any(u["username"] == "cruduser" for u in user_storage.values())
        assert any(
            k == "test_id" and v["username"] == "cruduser"
            for k, v in user_storage.items()
        )

        # Delete
        del user_storage["test_id"]
        assert len(user_storage) == 0
        assert "test_id" not in user_storage

        with pytest.raises(KeyError):
            _ = user_storage["test_id"]

    def test_authenticate_user_with_sql_storage(self, user_storage, monkeypatch):
        """Verify authenticate_user integrates end-to-end with SQL storage."""
        monkeypatch.setattr("backend.utils.auth.users_db", user_storage)

        register_user(
            username="auth_tester",
            email="authtest@example.com",
            password="SecurePassword987!",
            role="user",
        )

        # Successful authentication
        authenticated = authenticate_user("auth_tester", "SecurePassword987!")
        assert authenticated is not None
        assert authenticated["username"] == "auth_tester"

        # Failed authentication
        wrong = authenticate_user("auth_tester", "WrongPassword!")
        assert wrong is None


class TestSQLAPIKeyStorage:

    def test_api_key_crud(self, api_key_storage):
        key_hash = "mock_hash_12345"
        key_data = {
            "user_id": "user_xyz",
            "name": "Production Key",
            "created_at": datetime.utcnow(),
            "expires_at": None,
            "is_active": True,
        }

        api_key_storage[key_hash] = key_data
        assert key_hash in api_key_storage
        assert len(api_key_storage) == 1

        retrieved = api_key_storage.get(key_hash)
        assert retrieved["user_id"] == "user_xyz"
        assert retrieved["name"] == "Production Key"

        del api_key_storage[key_hash]
        assert len(api_key_storage) == 0


class TestDatabaseURLNormalization:

    def test_postgres_url_scheme_normalization(self, monkeypatch):
        """Render uses postgres:// which SQLAlchemy 1.4+ rejects; ensure it's normalized to postgresql://"""
        captured_urls = []

        def mock_create_engine(url, **kwargs):
            captured_urls.append(url)
            return None

        monkeypatch.setattr(storage_mod, "create_engine", mock_create_engine)

        test_url = "postgres://user:pass@ep-cool-db.oregon.render.com:5432/decisera"
        storage_mod._get_engine(test_url)

        assert len(captured_urls) == 1
        assert captured_urls[0].startswith("postgresql://")
        assert (
            captured_urls[0]
            == "postgresql://user:pass@ep-cool-db.oregon.render.com:5432/decisera"
        )


class TestSQLDatasetStorage:
    @pytest.fixture
    def dataset_storage(self, test_db_engine, tmp_path):
        cache_dir = tmp_path / "datasets_cache"
        return SQLDatasetStorage(engine=test_db_engine, cache_dir=cache_dir)

    def test_save_and_retrieve_dataset(self, dataset_storage):
        csv_bytes = b"feature_a,feature_b,target\n1.0,2.0,1\n3.0,4.0,0\n5.0,6.0,1\n"
        saved = dataset_storage.save_dataset(
            dataset_id="ds_test_001",
            name="Test Dataset",
            filename="test.csv",
            file_type="csv",
            file_content=csv_bytes,
            description="Testing dataset persistence",
            user_id="user_test_1",
            row_count=3,
            column_count=3,
            column_names=["feature_a", "feature_b", "target"],
        )

        assert saved["id"] == "ds_test_001"
        assert saved["name"] == "Test Dataset"
        assert saved["rows"] == 3
        assert saved["columns"] == 3

        # Retrieve metadata
        retrieved = dataset_storage.get_dataset("ds_test_001", user_id="user_test_1")
        assert retrieved is not None
        assert retrieved["name"] == "Test Dataset"
        # Large binary file content should NOT be in metadata dict
        assert "file_content" not in retrieved

        # Retrieve dataframe
        df = dataset_storage.get_dataset_dataframe("ds_test_001", user_id="user_test_1")
        assert df.shape == (3, 3)
        assert list(df.columns) == ["feature_a", "feature_b", "target"]
        assert df["target"].tolist() == [1, 0, 1]

    def test_user_isolation(self, dataset_storage):
        csv_bytes = b"x,y\n1,2\n"
        dataset_storage.save_dataset(
            dataset_id="ds_user1",
            name="User 1 Data",
            filename="u1.csv",
            file_type="csv",
            file_content=csv_bytes,
            user_id="user_1",
        )
        dataset_storage.save_dataset(
            dataset_id="ds_user2",
            name="User 2 Data",
            filename="u2.csv",
            file_type="csv",
            file_content=csv_bytes,
            user_id="user_2",
        )

        # User 1 should only see their dataset
        user1_list = dataset_storage.list_datasets(user_id="user_1")
        assert len(user1_list) == 1
        assert user1_list[0]["id"] == "ds_user1"

        # User 2 cannot access user 1's dataset
        assert dataset_storage.get_dataset("ds_user1", user_id="user_2") is None

    def test_container_restart_simulation(
        self, dataset_storage, test_db_engine, tmp_path
    ):
        """Simulate container restart: wipe in-memory cache and local disk cache; verify SQL restores data."""
        csv_bytes = b"col1,col2\n10,20\n30,40\n"
        dataset_storage.save_dataset(
            dataset_id="ds_restart_test",
            name="Restart Dataset",
            filename="restart.csv",
            file_type="csv",
            file_content=csv_bytes,
            user_id="user_restart",
            row_count=2,
            column_count=2,
            column_names=["col1", "col2"],
        )

        # Wipe RAM cache and disk cache
        dataset_storage._df_cache.clear()
        for f in dataset_storage.cache_dir.glob("*"):
            f.unlink()
        assert len(list(dataset_storage.cache_dir.glob("*"))) == 0

        # Create a new storage instance pointing to the same database (simulating a fresh container boot)
        fresh_cache_dir = tmp_path / "fresh_cache"
        fresh_storage = SQLDatasetStorage(
            engine=test_db_engine, cache_dir=fresh_cache_dir
        )

        # Fresh storage must successfully reconstruct the DataFrame from the SQL LargeBinary column
        restored_df = fresh_storage.get_dataset_dataframe(
            "ds_restart_test", user_id="user_restart"
        )
        assert restored_df.shape == (2, 2)
        assert restored_df["col1"].tolist() == [10, 30]
        assert restored_df["col2"].tolist() == [20, 40]

    def test_delete_dataset(self, dataset_storage):
        csv_bytes = b"a,b\n1,2\n"
        dataset_storage.save_dataset(
            dataset_id="ds_del_test",
            name="Delete Me",
            filename="del.csv",
            file_type="csv",
            file_content=csv_bytes,
            user_id="user_del",
        )
        assert (
            dataset_storage.get_dataset("ds_del_test", user_id="user_del") is not None
        )

        deleted = dataset_storage.delete_dataset("ds_del_test", user_id="user_del")
        assert deleted is True
        assert dataset_storage.get_dataset("ds_del_test", user_id="user_del") is None


class TestSQLModelStorage:
    @pytest.fixture
    def model_storage(self, test_db_engine):
        return SQLModelStorage(engine=test_db_engine)

    def test_save_and_retrieve_model(self, model_storage):
        import io
        import joblib
        from sklearn.ensemble import RandomForestClassifier
        import numpy as np

        # Train dummy model
        clf = RandomForestClassifier(n_estimators=5, random_state=42)
        X = np.array([[1.0, 2.0], [2.0, 3.0], [3.0, 4.0], [4.0, 5.0]])
        y = np.array([0, 0, 1, 1])
        clf.fit(X, y)

        buf = io.BytesIO()
        joblib.dump(clf, buf)
        artifact_bytes = buf.getvalue()

        saved = model_storage.save_model(
            model_id="model_test_001",
            dataset_id="ds_001",
            target_column="target",
            task_type="classification",
            best_model_name="RandomForestClassifier",
            best_score=0.95,
            feature_names=["f1", "f2"],
            metrics={"accuracy": 0.95, "f1_score": 0.94},
            all_results={"RandomForestClassifier": {"accuracy": 0.95}},
            model_artifact=artifact_bytes,
            user_id="user_model_1",
        )

        assert saved["model_id"] == "model_test_001"
        assert saved["best_model"] == "RandomForestClassifier"
        assert saved["best_score"] == 0.95

        # Metadata listing should not fetch LargeBinary
        models = model_storage.list_models(user_id="user_model_1")
        assert len(models) == 1
        assert models[0]["model_id"] == "model_test_001"
        assert "model_artifact" not in models[0]

        # Model bundle loading and prediction
        bundle = model_storage.get_model_bundle(
            "model_test_001", user_id="user_model_1"
        )
        assert bundle is not None
        estimator = bundle["model"]
        preds = estimator.predict([[1.0, 2.0], [4.0, 5.0]])
        assert len(preds) == 2
        assert preds[0] == 0
        assert preds[1] == 1

    def test_model_container_restart_simulation(self, model_storage, test_db_engine):
        """Simulate container restart: clear RAM cache and ensure bundle is restored from SQL bytea column."""
        import io
        import joblib
        from sklearn.tree import DecisionTreeClassifier

        tree = DecisionTreeClassifier()
        tree.fit([[1], [2], [3], [4]], [0, 0, 1, 1])
        buf = io.BytesIO()
        joblib.dump(tree, buf)

        model_storage.save_model(
            model_id="model_restart_test",
            dataset_id="ds_999",
            target_column="y",
            task_type="classification",
            best_model_name="DecisionTreeClassifier",
            best_score=1.0,
            feature_names=["f1"],
            metrics={"accuracy": 1.0},
            all_results={},
            model_artifact=buf.getvalue(),
            user_id="user_restart",
        )

        # Clear in-memory bundle cache
        model_storage._bundle_cache.clear()

        # Create fresh instance to simulate new container
        fresh_model_storage = SQLModelStorage(engine=test_db_engine)
        bundle = fresh_model_storage.get_model_bundle(
            "model_restart_test", user_id="user_restart"
        )

        assert bundle is not None
        assert bundle["best_model_name"] == "DecisionTreeClassifier"
        # Verify model makes predictions correctly
        assert bundle["model"].predict([[1]])[0] == 0
        assert bundle["model"].predict([[4]])[0] == 1
