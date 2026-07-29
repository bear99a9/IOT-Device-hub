import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.main import app, get_db
from app.database import Base

# clean in memory db, shared across tests and cleaned up after tests run
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_db():
    """Recreate all tables before every test, and drop them afterwards."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


def _register(name="Living Room Thermometer", type="thermometer", status="off", config=None):
    payload = {"name": name, "type": type, "status": status}
    if config is not None:
        payload["config"] = config
    return client.post("/devices", json=payload)


# --- Registration (POST /devices) -----------------------------------------

def test_register_device_returns_201_and_id():
    """We return the details of the new device"""
    response = _register()
    assert response.status_code == 201
    body = response.json()
    assert body["id"]
    assert body["name"] == "Living Room Thermometer"
    assert body["type"] == "thermometer"
    assert body["status"] == "off"


def test_register_device_defaults_status_to_off_when_omitted():
    response = client.post("/devices", json={"name": "Hallway Light", "type": "light"})
    assert response.status_code == 201
    assert response.json()["status"] == "off"


def test_register_device_with_config():
    """We can set a custom json config"""
    response = _register(config={"target_temperature": 21})
    assert response.status_code == 201
    assert response.json()["config"] == {"target_temperature": 21}


def test_register_device_missing_name_returns_422():
    response = client.post("/devices", json={"type": "light"})
    assert response.status_code == 422


def test_register_device_invalid_status_literal_returns_422():
    response = client.post("/devices", json={"name": "Light", "type": "light", "status": "purple"})
    assert response.status_code == 422


def test_register_device_creates_initial_history_entry():
    created = _register(status="off").json()
    detail = client.get(f"/devices/{created['id']}").json()
    assert len(detail["history"]) == 1
    assert detail["history"][0]["status"] == "off"


# --- Listing (GET /devices) -------------------------------------------------

def test_list_devices_empty_by_default():
    """Empty lists do not throw errors"""
    response = client.get("/devices")
    assert response.status_code == 200
    assert response.json() == []


def test_list_devices_returns_all_registered_devices():
    _register(name="Device 1")
    _register(name="Device 2")
    response = client.get("/devices")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_devices_respects_limit():
    """Testing pagination works correctly"""
    for i in range(5):
        _register(name=f"Device {i}")
    response = client.get("/devices?limit=2")
    assert response.status_code == 200
    assert len(response.json()) == 2


def test_list_devices_respects_offset():
    """Testing pagination works correctly"""
    ids_in_order = []
    for i in range(3):
        ids_in_order.append(_register(name=f"Device {i}").json()["id"])
    response = client.get("/devices?limit=10&offset=1")
    returned_ids = [d["id"] for d in response.json()]
    assert returned_ids == ids_in_order[1:]


def test_list_devices_limit_over_max_returns_422():
    response = client.get("/devices?limit=500")
    assert response.status_code == 422


def test_list_devices_negative_offset_returns_422():
    response = client.get("/devices?offset=-1")
    assert response.status_code == 422


# --- Get by ID (GET /devices/{id}) -----------------------------------------

def test_get_device_by_id_returns_details_and_history():
    created = _register().json()
    response = client.get(f"/devices/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert "history" in body


def test_get_device_with_unknown_id_returns_404():
    response = client.get("/devices/does-not-exist")
    assert response.status_code == 404


# --- Update status (PATCH /devices/{id}/status) -----------------------------

def test_update_status_changes_current_state():
    created = _register(status="off").json()
    response = client.patch(f"/devices/{created['id']}/status", json={"status": "on"})
    assert response.status_code == 200
    assert response.json()["status"] == "on"


def test_update_status_persists():
    created = _register(status="off").json()
    client.patch(f"/devices/{created['id']}/status", json={"status": "on"})
    fetched = client.get(f"/devices/{created['id']}").json()
    assert fetched["status"] == "on"


def test_update_status_appends_to_history():
    """Testing pagination works correctly"""
    created = _register(status="off").json()
    client.patch(f"/devices/{created['id']}/status", json={"status": "on"})
    client.patch(f"/devices/{created['id']}/status", json={"status": "off"})

    fetched = client.get(f"/devices/{created['id']}").json()

    assert fetched["history"][0]["status"] == "off"
    assert fetched["history"][1]["status"] == "on"
    assert fetched["history"][2]["status"] == "off"


def test_update_status_missing_body_field_returns_422():
    created = _register().json()
    response = client.patch(f"/devices/{created['id']}/status", json={})
    assert response.status_code == 422


def test_update_status_unknown_device_returns_404():
    response = client.patch("/devices/does-not-exist/status", json={"status": "on"})
    assert response.status_code == 404


# --- Update info (PUT /devices/{id}) ----------------------------------------

def test_update_info_changes_name_type_config():
    created = _register(name="Old Name", type="light").json()
    response = client.put(
        f"/devices/{created['id']}",
        json={"name": "New Name", "type": "thermostat", "config": {"target_temperature": 19}},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "New Name"
    assert body["type"] == "thermostat"
    assert body["config"] == {"target_temperature": 19}


def test_update_info_does_not_change_status():
    created = _register(status="on").json()
    client.put(
        f"/devices/{created['id']}",
        json={"name": "New Name", "type": "light"},
    )
    fetched = client.get(f"/devices/{created['id']}").json()
    assert fetched["status"] == "on"


def test_update_info_does_not_add_history_entry():
    created = _register().json()
    client.put(f"/devices/{created['id']}", json={"name": "New Name", "type": "light"})
    fetched = client.get(f"/devices/{created['id']}").json()
    # only the one entry from registration - PUT shouldn't log history
    assert len(fetched["history"]) == 1


def test_update_info_missing_required_field_returns_422():
    created = _register().json()
    response = client.put(f"/devices/{created['id']}", json={"type": "light"})  # no "name"
    assert response.status_code == 422


def test_update_info_unknown_device_returns_404():
    response = client.put("/devices/does-not-exist", json={"name": "X", "type": "light"})
    assert response.status_code == 404


# --- Deletion (DELETE /devices/{id}) ----------------------------------------

def test_delete_device_returns_204():
    created = _register().json()
    response = client.delete(f"/devices/{created['id']}")
    assert response.status_code == 204


def test_delete_device_actually_removes_it():
    created = _register().json()
    client.delete(f"/devices/{created['id']}")
    follow_up = client.get(f"/devices/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_unknown_device_returns_404():
    response = client.delete("/devices/does-not-exist")
    assert response.status_code == 404