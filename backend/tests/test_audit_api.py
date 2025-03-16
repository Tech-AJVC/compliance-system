import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
import sys
import os
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add the parent directory to sys.path to allow imports from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.auth.security import create_access_token, get_current_user
from app.utils.audit import log_activity
from conftest import TestUser, TestAuditLog


@pytest.fixture
def test_audit_logs(db: Session):
    """Create test audit logs and users for testing"""
    # Create test users with different roles
    fund_manager = TestUser(
        user_id=str(uuid.uuid4()),
        name="Fund Manager User",
        email="fund_manager@example.com",
        role="Fund Manager",
        password_hash="hashed_password"
    )
    compliance_officer = TestUser(
        user_id=str(uuid.uuid4()),
        name="Compliance Officer",
        email="compliance_officer@example.com",
        role="Compliance Officer",
        password_hash="hashed_password"
    )
    db.add(fund_manager)
    db.add(compliance_officer)
    db.commit()
    db.refresh(fund_manager)
    db.refresh(compliance_officer)
    
    # Create various audit log entries
    log_entries = [
        # Login activities
        TestAuditLog(
            log_id=str(uuid.uuid4()),
            user_id=fund_manager.user_id,
            activity="login",
            details="Successful login from 192.168.1.1"
        ),
        TestAuditLog(
            log_id=str(uuid.uuid4()),
            user_id=compliance_officer.user_id,
            activity="login",
            details="Successful login from 192.168.1.2"
        ),
        # Document activities
        TestAuditLog(
            log_id=str(uuid.uuid4()),
            user_id=fund_manager.user_id,
            activity="document_upload",
            details="Uploaded financial_report_2025.pdf"
        ),
        TestAuditLog(
            log_id=str(uuid.uuid4()),
            user_id=compliance_officer.user_id,
            activity="document_view",
            details="Viewed compliance_checklist.pdf"
        ),
        # System activities (no user)
        TestAuditLog(
            log_id=str(uuid.uuid4()),
            activity="system_backup",
            details="Automatic daily backup completed"
        ),
        # Add more activities with different timestamps
        TestAuditLog(
            log_id=str(uuid.uuid4()),
            user_id=fund_manager.user_id,
            activity="task_create",
            details="Created compliance task: Annual review",
            timestamp=datetime.now() - timedelta(days=5)
        ),
        TestAuditLog(
            log_id=str(uuid.uuid4()),
            user_id=compliance_officer.user_id,
            activity="task_update",
            details="Updated task status to In Progress",
            timestamp=datetime.now() - timedelta(days=3)
        ),
        TestAuditLog(
            log_id=str(uuid.uuid4()),
            user_id=fund_manager.user_id,
            activity="report_generate",
            details="Generated quarterly compliance report",
            timestamp=datetime.now() - timedelta(days=1)
        ),
    ]
    
    for log in log_entries:
        db.add(log)
    
    db.commit()
    
    # Refresh all logs to ensure they have proper IDs
    for log in log_entries:
        db.refresh(log)
    
    # Return user IDs for test verification
    return {
        "fund_manager_id": fund_manager.user_id,
        "compliance_officer_id": compliance_officer.user_id,
        "total_logs": len(log_entries),
        "logs": log_entries
    }


def test_get_audit_logs(client, db: Session, test_audit_logs, monkeypatch):
    """Test retrieving paginated audit logs"""
    # Mock the get_current_user dependency to return a Fund Manager
    async def mock_get_current_user():
        return {"sub": "fund_manager@example.com", "role": "Fund Manager"}
    
    # Import app here to avoid circular imports
    from main import app
    
    # Override the dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    # We need to patch the query to use our test models
    with patch('app.api.audit.AuditLog', TestAuditLog), \
         patch('app.api.audit.User', TestUser):
        
        # Test basic retrieval of all logs
        response = client.get("/api/audit/logs")
        
        # Reset dependency override
        app.dependency_overrides = {}
        
        assert response.status_code == 200
        data = response.json()
        assert "logs" in data
        assert "total" in data
        assert len(data["logs"]) == test_audit_logs["total_logs"]
        
        # Test pagination
        app.dependency_overrides[get_current_user] = mock_get_current_user
        
        response = client.get("/api/audit/logs?skip=2&limit=3")
        
        # Reset dependency override
        app.dependency_overrides = {}
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["logs"]) == 3  # Limited to 3 items


def test_audit_logs_permissions(client, db: Session, test_audit_logs, monkeypatch):
    """Test that only Fund Managers can access audit logs"""
    # Mock the get_current_user dependency to return a Compliance Officer
    async def mock_compliance_officer():
        return {"sub": "compliance_officer@example.com", "role": "Compliance Officer"}
    
    # Import app here to avoid circular imports
    from main import app
    app.dependency_overrides[get_current_user] = mock_compliance_officer
    
    # Attempt to access audit logs with unauthorized role
    response = client.get("/api/audit/logs")
    
    # Reset dependency override
    app.dependency_overrides = {}
    
    assert response.status_code == 403
    assert "Only Fund Managers can access audit logs" in response.json()["detail"]
    
    # Mock the get_current_user dependency to return a Fund Manager
    async def mock_fund_manager():
        return {"sub": "fund_manager@example.com", "role": "Fund Manager"}
    
    app.dependency_overrides[get_current_user] = mock_fund_manager
    
    # Access audit logs with authorized role
    with patch('app.api.audit.AuditLog', TestAuditLog), \
         patch('app.api.audit.User', TestUser):
        response = client.get("/api/audit/logs")
    
    # Reset dependency override
    app.dependency_overrides = {}
    
    assert response.status_code == 200


def test_get_specific_audit_log(client, db: Session, test_audit_logs, monkeypatch):
    """Test retrieving a specific audit log by ID"""
    # Mock the get_current_user dependency to return a Fund Manager
    async def mock_fund_manager():
        return {"sub": "fund_manager@example.com", "role": "Fund Manager"}
    
    # Import app here to avoid circular imports
    from main import app
    app.dependency_overrides[get_current_user] = mock_fund_manager
    
    # Get a specific log ID from our test data
    test_log = test_audit_logs["logs"][0]
    log_id = test_log.log_id
    
    # First, we need to mock the database query to return our test log
    with patch('app.api.audit.AuditLog', TestAuditLog), \
         patch('app.api.audit.User', TestUser):
        
        # Mock the specific query for the log
        with patch('sqlalchemy.orm.query.Query.filter') as mock_filter:
            # Set up the mock to return a query that will find our test log
            mock_query = MagicMock()
            mock_query.first.return_value = (test_log, "Fund Manager User")
            mock_filter.return_value = mock_query
            
            # Test retrieving a specific log
            response = client.get(f"/api/audit/logs/{log_id}")
    
    # Reset dependency override
    app.dependency_overrides = {}
    
    assert response.status_code == 200
    log = response.json()
    assert log["log_id"] == log_id
    
    # Test with non-existent ID
    app.dependency_overrides[get_current_user] = mock_fund_manager
    
    non_existent_id = str(uuid.uuid4())
    
    # Mock the database query to return None for non-existent ID
    with patch('app.api.audit.AuditLog', TestAuditLog), \
         patch('app.api.audit.User', TestUser):
        
        # Mock the specific query for the non-existent log
        with patch('sqlalchemy.orm.query.Query.filter') as mock_filter:
            # Set up the mock to return a query that will not find any log
            mock_query = MagicMock()
            mock_query.first.return_value = None
            mock_filter.return_value = mock_query
            
            # Test retrieving a non-existent log
            response = client.get(f"/api/audit/logs/{non_existent_id}")
    
    # Reset dependency override
    app.dependency_overrides = {}
    
    assert response.status_code == 404
