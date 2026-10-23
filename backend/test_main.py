
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database import Base, get_db
from main import app


@pytest.fixture
def client(tmp_path):
    # Create a separate SQLite database for each test.
    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'test_applyflow.db'}",
        connect_args={"check_same_thread": False},
    )

    TestingSessionLocal = sessionmaker(bind=test_engine)

    # Ensure all models are registered.
    import models  # noqa: F401

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Override the production database dependency.
    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:

            # Register a test user.
            registration = test_client.post(
                "/auth/register",
                json={
                    "email": "pytest-user@example.com",
                    "password": "TestPassword123!",
                },
            )

            assert registration.status_code == 201, registration.text

            # Log in the test user.
            login = test_client.post(
                "/auth/login",
                json={
                    "email": "pytest-user@example.com",
                    "password": "TestPassword123!",
                },
            )

            assert login.status_code == 200, login.text

            # Authenticate all subsequent requests.
            token = login.json()["access_token"]

            test_client.headers.update({
                "Authorization": f"Bearer {token}"
            })

            yield test_client

    finally:
        app.dependency_overrides.clear()
        test_engine.dispose()


# -----------------------------------
# Health check
# -----------------------------------

def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# -----------------------------------
# Create application
# -----------------------------------

def test_create_application(client):
    response = client.post(
        "/api/applications",
        json={
            "company": "Test Company",
            "role": "Software Engineer",
            "location": "Remote",
            "status": "Applied",
        },
    )

    assert response.status_code == 201
    assert response.json()["company"] == "Test Company"
    assert response.json()["status"] == "Applied"


# -----------------------------------
# Update application
# -----------------------------------

def test_update_application_status(client):
    created = client.post(
        "/api/applications",
        json={
            "company": "Test Company",
            "role": "Software Engineer",
            "location": "Remote",
            "status": "Applied",
        },
    )

    assert created.status_code == 201
    application_id = created.json()["id"]

    response = client.patch(
        f"/api/applications/{application_id}",
        json={"status": "Interview"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Interview"


# -----------------------------------
# Delete application
# -----------------------------------

def test_delete_application(client):
    created = client.post(
        "/api/applications",
        json={
            "company": "Test Company",
            "role": "Software Engineer",
            "location": "Remote",
            "status": "Applied",
        },
    )

    assert created.status_code == 201
    application_id = created.json()["id"]

    response = client.delete(
        f"/api/applications/{application_id}"
    )

    assert response.status_code == 204

    remaining = client.get("/api/applications").json()

    assert all(
        item["id"] != application_id
        for item in remaining
    )


# -----------------------------------
# Validation tests
# -----------------------------------

def test_reject_application_without_company(client):
    response = client.post(
        "/api/applications",
        json={
            "role": "Software Engineer",
            "location": "Remote",
            "status": "Applied",
        },
    )

    assert response.status_code == 422


def test_reject_invalid_application_status(client):
    response = client.post(
        "/api/applications",
        json={
            "company": "Test Company",
            "role": "Software Engineer",
            "location": "Remote",
            "status": "Maybe",
        },
    )

    assert response.status_code == 422


# -----------------------------------
# Nonexistent application tests
# -----------------------------------

def test_update_nonexistent_application(client):
    response = client.patch(
        "/api/applications/99999",
        json={"status": "Interview"},
    )

    assert response.status_code == 404


def test_delete_nonexistent_application(client):
    response = client.delete(
        "/api/applications/99999"
    )

    assert response.status_code == 404


# -----------------------------------
# Authentication tests
# -----------------------------------

def test_reject_unauthenticated_access(client):
    client.headers.pop("Authorization", None)

    response = client.get("/api/applications")

    assert response.status_code == 401


def test_reject_invalid_token(client):
    client.headers["Authorization"] = "Bearer invalid-token"

    response = client.get("/api/applications")

    assert response.status_code == 401


def test_reject_wrong_password(client):
    response = client.post(
        "/auth/login",
        json={
            "email": "pytest-user@example.com",
            "password": "WrongPassword123!",
        },
    )

    assert response.status_code == 401
