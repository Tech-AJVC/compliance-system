import pytest
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

# Add the parent directory to sys.path to allow imports from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database.base import get_db

# Create in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Add SQLite UUID type handler
@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    # Enable foreign key constraints
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
    
    # Register UUID converter
    def _uuid_converter(uuid_str):
        if uuid_str is not None:
            return uuid.UUID(uuid_str)
        return None
    
    dbapi_connection.create_function("uuid", 1, _uuid_converter)


# Create custom SQLite-compatible models for testing
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy.ext.declarative import declarative_base

TestBase = declarative_base()

class TestUser(TestBase):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    role = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    mfa_enabled = Column(String, default="0")
    phone = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now())

class TestAuditLog(TestBase):
    __tablename__ = "audit_logs"
    
    log_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.user_id"), nullable=True)
    activity = Column(String, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    details = Column(Text, nullable=True)


TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    # Create the database tables
    TestBase.metadata.create_all(bind=engine)
    
    # Create a new database session for each test
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
    # Drop all tables after the test is complete
    TestBase.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    # Import here to avoid circular imports
    from main import app
    
    # Override the get_db dependency to use our test database
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    with TestClient(app) as test_client:
        yield test_client
    
    # Reset dependency overrides after test
    app.dependency_overrides = {}
