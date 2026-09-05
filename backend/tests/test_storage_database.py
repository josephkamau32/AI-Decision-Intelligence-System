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
