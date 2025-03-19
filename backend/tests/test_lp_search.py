from fastapi.testclient import TestClient
from main import app
from app.database.base import get_db, Base
from app.models.lp_details import LPDetails
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import uuid
from datetime import date, datetime
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
    return {"sub": "test-admin@example.com", "role": "Fund Manager"}

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
def test_lps(test_client):
    """Create test LP records in the database"""
    db = TestingSessionLocal()
    
    # Create a few test LP records with different names
    lps = [
        LPDetails(
            lp_id=uuid.uuid4(),
            lp_name="Acme Investments",
            email="acme@example.com",
            mobile_no="1234567890",
            pan="ABCDE1234F",
            commitment_amount=1000000.00,
            type="Corporate",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        LPDetails(
            lp_id=uuid.uuid4(),
            lp_name="Smith Family Office",
            email="smith@familyoffice.com",
            mobile_no="9876543210",
            pan="FGHIJ5678K",
            commitment_amount=2500000.00,
            type="Family Office",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        LPDetails(
            lp_id=uuid.uuid4(),
            lp_name="Global Ventures Partners",
            email="info@globalventures.com",
            mobile_no="5555555555",
            pan="LMNOP9012Q",
            commitment_amount=5000000.00,
            type="Corporate",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
        LPDetails(
            lp_id=uuid.uuid4(),
            lp_name="SMITH CAPITAL",
            email="contact@smithcapital.com",
            mobile_no="1112223333",
            pan="RSTUV3456W",
            commitment_amount=3000000.00,
            type="Corporate",
            created_at=datetime.now(),
            updated_at=datetime.now()
        ),
    ]
    
    for lp in lps:
        db.add(lp)
    
    db.commit()
    
    # Close the db session
    db.close()

def test_search_lps_exact_match(test_client, test_lps):
    """Test searching LPs with an exact match"""
    # Create access token for authenticated request
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Fund Manager"})
    
    # Search for "Acme Investments"
    response = test_client.get(
        "/api/lps/search/?name=Acme Investments",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["lp_name"] == "Acme Investments"
    assert data[0]["email"] == "acme@example.com"
    assert "lp_id" in data[0]

def test_search_lps_partial_match(test_client, test_lps):
    """Test searching LPs with a partial match"""
    # Create access token for authenticated request
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Fund Manager"})
    
    # Search for "Smith" which should match multiple LPs
    response = test_client.get(
        "/api/lps/search/?name=Smith",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # Should match Smith Family Office and SMITH CAPITAL
    
    # Verify each LP has the required fields
    for lp in data:
        assert "lp_id" in lp
        assert "lp_name" in lp
        assert "email" in lp
        assert "Smith" in lp["lp_name"] or "SMITH" in lp["lp_name"]

def test_search_lps_case_insensitive(test_client, test_lps):
    """Test that search is case-insensitive"""
    # Create access token for authenticated request
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Fund Manager"})
    
    # Search for "smith" in lowercase
    response = test_client.get(
        "/api/lps/search/?name=smith",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2  # Should match Smith Family Office and SMITH CAPITAL
    
    # Verify that both uppercase and lowercase matches are returned
    lp_names = [lp["lp_name"] for lp in data]
    assert any("Smith" in name for name in lp_names)
    assert any("SMITH" in name for name in lp_names)

def test_search_lps_no_match(test_client, test_lps):
    """Test searching for an LP name that doesn't exist"""
    # Create access token for authenticated request
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Fund Manager"})
    
    # Search for a non-existent name
    response = test_client.get(
        "/api/lps/search/?name=NonExistentLP",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0  # Should return an empty list

def test_search_lps_unauthorized(test_client, test_lps):
    """Test that unauthenticated requests are rejected"""
    # Search without an access token
    response = test_client.get("/api/lps/search/?name=Smith")
    
    # Verify response
    assert response.status_code == 401  # Unauthorized

def test_search_lps_pagination(test_client, test_lps):
    """Test pagination for LP search results"""
    # Create access token for authenticated request
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Fund Manager"})
    
    # Search with pagination parameters
    response = test_client.get(
        "/api/lps/search/?name=&skip=1&limit=2",  # Empty name should match all LPs
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    # Verify response
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Should return exactly 2 results due to limit
