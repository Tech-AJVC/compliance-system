from fastapi.testclient import TestClient
from main import app
from app.database.base import get_db, Base
from app.models.user import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import uuid
from app.auth.security import create_access_token

# Test database URL
DATABASE_URL = "postgresql://vccrm:vccrm@localhost:5432/vccrm_test"

# Create test database engine
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Mock current user for testing
def get_test_user():
    return {"sub": "test-admin@example.com", "role": "Compliance Officer"}

@pytest.fixture(scope="function")
def test_client():
    # Create test database tables
    Base.metadata.create_all(bind=engine)
    
    # Override the database dependency
    app.dependency_overrides[get_db] = override_get_db
    
    # Create test client
    client = TestClient(app)
    
    yield client
    
    # Clean up
    Base.metadata.drop_all(bind=engine)
    app.dependency_overrides.clear()

@pytest.fixture
def test_users(test_client):
    """Create test users in the database"""
    db = TestingSessionLocal()
    
    # Create a few test users with different names
    users = [
        User(
            user_id=uuid.uuid4(),
            name="John Smith",
            email="john@example.com",
            role="Fund Manager",
            password_hash="hashed_password",
            mfa_enabled=False,
        ),
        User(
            user_id=uuid.uuid4(),
            name="Jane Smith",
            email="jane@example.com",
            role="Compliance Officer",
            password_hash="hashed_password",
            mfa_enabled=False,
        ),
        User(
            user_id=uuid.uuid4(),
            name="Alice Johnson",
            email="alice@example.com",
            role="LP",
            password_hash="hashed_password",
            mfa_enabled=False,
        ),
        User(
            user_id=uuid.uuid4(),
            name="SMITH ANDERSON",
            email="smith@example.com",
            role="Auditor",
            password_hash="hashed_password",
            mfa_enabled=False,
        ),
        User(
            user_id=uuid.uuid4(),
            name="Test Admin",
            email="test-admin@example.com",
            role="Compliance Officer",
            password_hash="hashed_password",
            mfa_enabled=False,
        ),
    ]
    
    for user in users:
        db.add(user)
    
    db.commit()
    
    # Close the db session
    db.close()

def test_search_users_exact_match(test_client, test_users):
    """Test searching users with an exact match"""
    # Create access token for authenticated request
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Compliance Officer"})
    
    # Search for "John Smith"
    response = test_client.get(
        "/api/users/search?username=John Smith",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["UserName"] == "John Smith"
    assert data[0]["email"] == "john@example.com"
    assert data[0]["role"] == "Fund Manager"
    assert "UserId" in data[0]

def test_search_users_partial_match(test_client, test_users):
    """Test searching users with a partial match"""
    # Create access token for authenticated request
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Compliance Officer"})
    
    # Search for "Smith" which should match multiple users
    response = test_client.get(
        "/api/users/search?username=Smith",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # Should match John Smith, Jane Smith, and SMITH ANDERSON
    
    # Verify each user has the required fields
    for user in data:
        assert "UserId" in user
        assert "UserName" in user
        assert "email" in user
        assert "role" in user
        assert "Smith" in user["UserName"] or "SMITH" in user["UserName"]

def test_search_users_case_insensitive(test_client, test_users):
    """Test that search is case-insensitive"""
    # Create access token for authenticated request
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Compliance Officer"})
    
    # Search for "smith" in lowercase which should match users with "Smith" or "SMITH"
    response = test_client.get(
        "/api/users/search?username=smith",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 3  # Should match John Smith, Jane Smith, and SMITH ANDERSON
    
    # Check if Smith ANDERSON (uppercase) is in the results
    smith_anderson_found = False
    for user in data:
        if user["UserName"] == "SMITH ANDERSON":
            smith_anderson_found = True
            break
    
    assert smith_anderson_found, "Case-insensitive search didn't return uppercase SMITH"

def test_search_users_no_match(test_client, test_users):
    """Test searching for a username that doesn't exist"""
    # Create access token for authenticated request
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Compliance Officer"})
    
    # Search for a non-existent username
    response = test_client.get(
        "/api/users/search?username=NonExistentUser",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify response returns empty list
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
    assert isinstance(data, list)

def test_search_users_unauthorized(test_client, test_users):
    """Test that unauthenticated requests are rejected"""
    # Try to search without authentication
    response = test_client.get("/api/users/search?username=Smith")
    
    # Verify the request is rejected
    assert response.status_code == 401  # Unauthorized
