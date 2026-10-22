
import pytest
from fastapi.testclient import TestClient

import main
from main import app



@pytest.fixture
def client(tmp_path):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from database import Base, get_db

    test_engine = create_engine(
        f"sqlite:///{tmp_path / 'test_applyflow.db'}",
        connect_args={"check_same_thread": False},
    )

    TestingSessionLocal = sessionmaker(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        test_engine.dispose()



def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


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
    application_id = created.json()["id"]

    response = client.patch(
        f"/api/applications/{application_id}",
        json={"status": "Interview"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "Interview"


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
    application_id = created.json()["id"]

    response = client.delete(f"/api/applications/{application_id}")

    assert response.status_code == 204

    remaining = client.get("/api/applications").json()
    assert all(item["id"] != application_id for item in remaining)


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


def test_update_nonexistent_application(client):
    response = client.patch(
        "/api/applications/99999",
        json={"status": "Interview"},
    )

    assert response.status_code == 404


def test_delete_nonexistent_application(client):
    response = client.delete("/api/applications/99999")

    assert response.status_code == 404

