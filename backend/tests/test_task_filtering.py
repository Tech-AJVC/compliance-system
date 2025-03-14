from fastapi.testclient import TestClient
from main import app
from app.database.base import get_db, Base
from app.models.user import User
from app.models.compliance_task import ComplianceTask, TaskState, TaskCategory
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pytest
import uuid
from app.auth.security import create_access_token
from datetime import datetime, timedelta, timezone
import json

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
def test_users_and_tasks(test_client):
    """Create test users and tasks in the database"""
    db = TestingSessionLocal()
    
    # Create test users with proper UUID v4
    alice = User(
        user_id=uuid.uuid4(),
        name="Alice Johnson",
        email="alice@example.com",
        role="Fund Manager",
        password_hash="hashed_password",
        mfa_enabled=False,
    )
    
    bob = User(
        user_id=uuid.uuid4(),
        name="Bob Smith",
        email="bob@example.com",
        role="Compliance Officer",
        password_hash="hashed_password",
        mfa_enabled=False,
    )
    
    charlie = User(
        user_id=uuid.uuid4(),
        name="Charlie Brown",
        email="charlie@example.com",
        role="LP",
        password_hash="hashed_password",
        mfa_enabled=False,
    )
    
    admin = User(
        user_id=uuid.uuid4(),
        name="Test Admin",
        email="test-admin@example.com",
        role="Compliance Officer",
        password_hash="hashed_password",
        mfa_enabled=False,
    )
    
    users = [alice, bob, charlie, admin]
    for user in users:
        db.add(user)
    
    db.commit()
    
    # Create tasks with different due dates and assignees
    now = datetime.now(timezone.utc)
    tasks = [
        # Task due tomorrow assigned to Alice
        ComplianceTask(
            compliance_task_id=uuid.uuid4(),
            description="Task due tomorrow",
            deadline=now + timedelta(days=1),
            state=TaskState.OPEN.value,
            category=TaskCategory.SEBI.value,
            assignee_id=alice.user_id,
        ),
        # Task due in 3 days assigned to Bob
        ComplianceTask(
            compliance_task_id=uuid.uuid4(),
            description="Task due in 3 days",
            deadline=now + timedelta(days=3),
            state=TaskState.OPEN.value,
            category=TaskCategory.RBI.value,
            assignee_id=bob.user_id,
        ),
        # Task due in 7 days assigned to Charlie
        ComplianceTask(
            compliance_task_id=uuid.uuid4(),
            description="Task due in 7 days",
            deadline=now + timedelta(days=7),
            state=TaskState.PENDING.value,
            category=TaskCategory.IT_GST.value,
            assignee_id=charlie.user_id,
        ),
        # Task overdue (yesterday) assigned to Alice
        ComplianceTask(
            compliance_task_id=uuid.uuid4(),
            description="Task overdue",
            deadline=now - timedelta(days=1),
            state=TaskState.OVERDUE.value,
            category=TaskCategory.SEBI.value,
            assignee_id=alice.user_id,
        ),
        # Task due in 14 days assigned to Bob
        ComplianceTask(
            compliance_task_id=uuid.uuid4(),
            description="Task due in 14 days",
            deadline=now + timedelta(days=14),
            state=TaskState.OPEN.value,
            category=TaskCategory.RBI.value,
            assignee_id=bob.user_id,
        ),
    ]
    
    for task in tasks:
        db.add(task)
    
    db.commit()
    
    # Return users and tasks for reference in tests
    user_data = {
        'alice': str(alice.user_id),
        'bob': str(bob.user_id),
        'charlie': str(charlie.user_id),
        'admin': str(admin.user_id)
    }
    
    db.close()
    return user_data

def test_filter_by_date_range(test_client, test_users_and_tasks):
    """Test filtering tasks by date range"""
    # Create access token for authentication
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Compliance Officer"})
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get current time for constructing date ranges
    now = datetime.now(timezone.utc)
    
    # Test case 1: Filter tasks due within next 2 days
    start_date = now.strftime("%Y-%m-%d")
    end_date = (now + timedelta(days=2)).strftime("%Y-%m-%d")
    
    response = test_client.get(
        f"/api/tasks/?start_date={start_date}&end_date={end_date}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert "tasks" in response_data
    assert "total" in response_data
    assert response_data["total"] == 1
    tasks = response_data["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["description"] == "Task due tomorrow"
    
    # Test case 2: Filter tasks due within next 5 days
    end_date = (now + timedelta(days=5)).strftime("%Y-%m-%d")
    
    response = test_client.get(
        f"/api/tasks/?start_date={start_date}&end_date={end_date}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    tasks = response_data["tasks"]
    assert len(tasks) == 2
    
    # Test case 3: Filter tasks due within next 30 days
    end_date = (now + timedelta(days=30)).strftime("%Y-%m-%d")
    
    response = test_client.get(
        f"/api/tasks/?start_date={start_date}&end_date={end_date}",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 4
    tasks = response_data["tasks"]
    assert len(tasks) == 4  # Should include all future tasks

def test_filter_by_assignee_name(test_client, test_users_and_tasks):
    """Test filtering tasks by assignee name"""
    # Create access token for authentication
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Compliance Officer"})
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test case 1: Filter tasks assigned to Alice Johnson
    response = test_client.get(
        "/api/tasks/?assignee_name=Alice",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    tasks = response_data["tasks"]
    assert len(tasks) == 2
    alice_id = test_users_and_tasks['alice']
    for task in tasks:
        assert task["assignee_id"] == alice_id
    
    # Test case 2: Filter tasks assigned to Bob Smith
    response = test_client.get(
        "/api/tasks/?assignee_name=Bob",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    tasks = response_data["tasks"]
    assert len(tasks) == 2
    bob_id = test_users_and_tasks['bob']
    for task in tasks:
        assert task["assignee_id"] == bob_id
    
    # Test case 3: Search for a non-existent assignee
    response = test_client.get(
        "/api/tasks/?assignee_name=NonExistent",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 0
    tasks = response_data["tasks"]
    assert len(tasks) == 0

def test_sort_by_due_date(test_client, test_users_and_tasks):
    """Test sorting tasks by due date"""
    # Create access token for authentication
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Compliance Officer"})
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test case 1: Sort ascending (earliest deadline first)
    response = test_client.get(
        "/api/tasks/?sort=deadline_asc",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 5
    tasks = response_data["tasks"]
    assert len(tasks) == 5
    
    # Verify the tasks are sorted by deadline (ascending)
    for i in range(len(tasks) - 1):
        assert tasks[i]["deadline"] <= tasks[i+1]["deadline"]
    
    # Test case 2: Sort descending (latest deadline first)
    response = test_client.get(
        "/api/tasks/?sort=deadline_desc",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 5
    tasks = response_data["tasks"]
    assert len(tasks) == 5
    
    # Verify the tasks are sorted by deadline (descending)
    for i in range(len(tasks) - 1):
        assert tasks[i]["deadline"] >= tasks[i+1]["deadline"]

def test_combined_filters(test_client, test_users_and_tasks):
    """Test combining multiple filters"""
    # Create access token for authentication
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Compliance Officer"})
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Get current time for constructing date ranges
    now = datetime.now(timezone.utc)
    
    # Test case: Filter by date range, assignee name, and sort by deadline (ascending)
    start_date = (now - timedelta(days=2)).strftime("%Y-%m-%d")  # Include overdue tasks
    end_date = (now + timedelta(days=30)).strftime("%Y-%m-%d")
    
    response = test_client.get(
        f"/api/tasks/?start_date={start_date}&end_date={end_date}&assignee_name=Alice&sort=deadline_asc",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 2
    tasks = response_data["tasks"]
    assert len(tasks) == 2
    
    # Verify all tasks are assigned to Alice
    alice_id = test_users_and_tasks['alice']
    for task in tasks:
        assert task["assignee_id"] == alice_id
        
    # Verify tasks are sorted by deadline (ascending)
    assert tasks[0]["deadline"] <= tasks[1]["deadline"]

def test_pagination(test_client, test_users_and_tasks):
    """Test task pagination"""
    # Create access token for authentication
    access_token = create_access_token(data={"sub": "test-admin@example.com", "role": "Compliance Officer"})
    auth_headers = {"Authorization": f"Bearer {access_token}"}
    
    # Test case 1: Get first page with 2 items
    response = test_client.get(
        "/api/tasks/?limit=2&skip=0",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 5  # Total count should be 5
    tasks = response_data["tasks"]
    assert len(tasks) == 2  # But only 2 returned due to limit
    
    # Test case 2: Get second page with 2 items
    response = test_client.get(
        "/api/tasks/?limit=2&skip=2",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 5
    tasks = response_data["tasks"]
    assert len(tasks) == 2
    
    # Test case 3: Get third page with remaining item
    response = test_client.get(
        "/api/tasks/?limit=2&skip=4",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["total"] == 5
    tasks = response_data["tasks"]
    assert len(tasks) == 1  # Only 1 item left
