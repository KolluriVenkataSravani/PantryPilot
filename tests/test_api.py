from collections.abc import Generator
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import create_app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=test_engine, autoflush=False, expire_on_commit=False
    )
    Base.metadata.create_all(bind=test_engine)

    def override_get_db() -> Generator[Session, None, None]:
        with TestingSessionLocal() as session:
            yield session

    application = create_app(initialize_db=False)
    application.dependency_overrides[get_db] = override_get_db
    with TestClient(application) as test_client:
        yield test_client
    application.dependency_overrides.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


def create_item(client: TestClient, **overrides: object) -> dict:
    payload = {
        "name": "Rolled oats",
        "category": "Grains & pasta",
        "quantity": 2,
        "unit": "bags",
        "expires_on": (date.today() + timedelta(days=3)).isoformat(),
        "notes": "",
    }
    payload.update(overrides)
    response = client.post("/api/items", json=payload)
    assert response.status_code == 201
    return response.json()


def test_add_list_and_filter_items(client: TestClient) -> None:
    create_item(client)
    create_item(client, name="Old crackers", expires_on=(date.today() - timedelta(days=1)).isoformat())

    assert len(client.get("/api/items").json()) == 2
    expiring = client.get("/api/items", params={"status": "expiring"}).json()
    assert [item["name"] for item in expiring] == ["Rolled oats"]
    expired = client.get("/api/items", params={"status": "expired"}).json()
    assert [item["name"] for item in expired] == ["Old crackers"]
    searched = client.get("/api/items", params={"q": "oats"}).json()
    assert [item["name"] for item in searched] == ["Rolled oats"]


def test_summary_and_delete_item(client: TestClient) -> None:
    item = create_item(client)
    create_item(client, name="Old crackers", expires_on=(date.today() - timedelta(days=1)).isoformat())

    assert client.get("/api/summary").json() == {
        "total_items": 2,
        "expiring_soon": 1,
        "expired": 1,
    }
    assert client.delete(f"/api/items/{item['id']}").status_code == 204
    assert client.get("/api/summary").json()["total_items"] == 1
    assert client.delete(f"/api/items/{item['id']}").status_code == 404


def test_update_item(client: TestClient) -> None:
    item = create_item(client)
    updated = client.put(
        f"/api/items/{item['id']}",
        json={
            "name": "Steel-cut oats",
            "category": "Grains & pasta",
            "quantity": 3,
            "unit": "jars",
            "expires_on": None,
            "notes": "Top shelf",
        },
    )

    assert updated.status_code == 200
    assert updated.json()["name"] == "Steel-cut oats"
    assert updated.json()["quantity"] == 3
    assert updated.json()["expires_on"] is None
    assert client.put("/api/items/999", json=updated.json()).status_code == 404


def test_rejects_invalid_item(client: TestClient) -> None:
    response = client.post(
        "/api/items",
        json={"name": "   ", "quantity": 0, "unit": "item"},
    )
    assert response.status_code == 422


def test_health_checks_database(client: TestClient) -> None:
    assert client.get("/api/health").json() == {"status": "ok"}


def test_homepage_serves_ui(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "Pantry Pilot" in response.text
    assert client.get("/static/app.js").status_code == 200
