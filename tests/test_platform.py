import uuid
from contextlib import ExitStack

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import insert, select

from car_fault_detection.api.app import create_app
from car_fault_detection.platform.access import hasher
from car_fault_detection.platform.database import accounts, schema, sessions

ORIGIN = "http://localhost:3000"
PASSWORD = "local-test-only-password"
ADMIN_EMAIL = "operator@example.test"
MECHANIC_EMAIL = "mechanic@example.test"


@pytest.fixture
def clients(monkeypatch, tmp_path):
    monkeypatch.setenv(
        "PLATFORM_DATABASE_URL", f"sqlite:///{(tmp_path / 'platform.db').as_posix()}"
    )
    monkeypatch.setenv("PLATFORM_WEB_ORIGIN", ORIGIN)
    app = create_app(lambda: None, lambda: None, lambda: None)
    engine = app.state.platform_engine
    schema.create_all(engine)
    with engine.begin() as db:
        db.execute(
            insert(accounts).values(
                id=str(uuid.uuid4()),
                name="Test operator",
                email=ADMIN_EMAIL,
                password_hash=hasher.hash(PASSWORD),
                role="admin",
                available=False,
            )
        )
    with ExitStack() as stack:
        yield (
            [stack.enter_context(TestClient(app, headers={"Origin": ORIGIN})) for _ in range(4)],
            engine,
        )


def post(client, path, body, expected=200):
    response = client.post("/platform" + path, json=body)
    assert response.status_code == expected, response.text
    assert response.headers["cache-control"] == "no-store"
    return response.json()


def workspace(client):
    response = client.get("/platform/workspace")
    assert response.status_code == 200, response.text
    return response.json()


def register(client, email, *, code=None, expected=201):
    payload = {"name": email.split("@")[0], "email": email, "password": PASSWORD}
    if code:
        payload["invite"] = code
    return post(client, "/access/register", payload, expected)


def garage(client, **extra):
    payload = {
        "name": "Test garage",
        "city": "Addis Ababa",
        "area": "Bole",
        "phone": "+251911000000",
        "latitude": 9.012,
        "longitude": 38.78,
        "published": True,
        **extra,
    }
    return post(client, "/admin/garages", payload)["id"]


def test_driver_mechanic_admin_end_to_end(clients):
    (admin, mechanic, driver, other), engine = clients
    login = admin.post("/platform/access/login", json={"email": ADMIN_EMAIL, "password": PASSWORD})
    assert login.status_code == 200
    assert "httponly" in login.headers["set-cookie"].lower()
    assert "samesite=lax" in login.headers["set-cookie"].lower()
    with engine.connect() as db:
        hashes = db.execute(select(sessions.c.token_hash)).scalars().all()
        assert len(hashes[0]) == 64
        assert admin.cookies.get("vehicle_session") not in hashes

    garage_id = garage(admin)
    garage(admin, name="Hidden garage", published=False)
    garage(admin, name="Outside search radius", latitude=10.0)
    code = post(
        admin, "/admin/invitations", {"garage_id": garage_id, "email": MECHANIC_EMAIL}, 201
    )["code"]
    register(other, "wrong@example.test", code=code, expected=400)
    account = register(mechanic, MECHANIC_EMAIL, code=code)["account"]
    register(other, MECHANIC_EMAIL, code=code, expected=400)
    assert account["role"] == "mechanic"
    register(driver, "driver@example.test")
    register(other, "other@example.test")

    mechanics = post(driver, "/directory/search", {"city": "addis ababa"})["garages"]
    assert all(row["mechanics"] == [] for row in mechanics)
    post(mechanic, "/mechanic/availability", {"available": True})
    matches = post(driver, "/directory/search", {"latitude": 9.0, "longitude": 38.78})["garages"]
    assert len(matches) == 1 and matches[0]["id"] == garage_id
    assert matches[0]["distance_km"] < 2
    assert matches[0]["mechanics"][0]["id"] == account["id"]
    assert workspace(admin)["stats"] == {"published": 2, "available": 1, "open": 0}

    payload = {
        "mechanic_id": account["id"],
        "request_key": str(uuid.uuid4()),
        "service": "tyres",
        "details": "There is a visible cut in one tyre",
        "callback": "+251911000001",
    }
    request_id = post(driver, "/requests", payload, 201)["id"]
    assert post(driver, "/requests", payload, 201)["id"] == request_id
    assert workspace(other)["requests"] == []
    assert workspace(driver)["counts"] == {"requested": 1}
    assert "callback" not in workspace(mechanic)["requests"][0]
    status_path = f"/requests/{request_id}/status"
    post(other, status_path, {"status": "cancelled"}, 404)
    post(driver, status_path, {"status": "accepted"}, 403)
    post(mechanic, status_path, {"status": "completed"}, 409)
    post(mechanic, status_path, {"status": "accepted"})
    assert workspace(mechanic)["requests"][0]["callback"] == payload["callback"]
    post(mechanic, "/mechanic/availability", {"available": False})
    post(driver, "/requests", {**payload, "request_key": str(uuid.uuid4())}, 409)
    post(mechanic, status_path, {"status": "completed"})
    assert workspace(driver)["requests"][0]["status"] == "completed"
    assert "callback" not in workspace(mechanic)["requests"][0]
    post(driver, status_path, {"status": "cancelled"}, 409)
    post(driver, "/access/logout", {})
    assert driver.get("/platform/workspace").status_code == 401


def test_origin_role_and_credentials_controls(clients):
    (_, _, driver, _), engine = clients
    body = {"name": "Driver", "email": "driver@example.test", "password": PASSWORD}
    assert (
        driver.post(
            "/platform/access/register", json=body, headers={"Origin": "https://elsewhere.example"}
        ).status_code
        == 403
    )
    invalid = driver.post(
        "/platform/access/register", json={**body, "role": "admin", "password": "dont-echo-this"}
    )
    assert invalid.status_code == 422 and "dont-echo-this" not in invalid.text
    register(driver, body["email"])
    assert workspace(driver)["account"]["role"] == "driver"
    post(
        driver,
        "/admin/garages",
        {"name": "Another", "area": "Test", "city": "Test", "phone": "0911000000"},
        403,
    )
    post(driver, "/directory/search", {"latitude": 9}, 422)
    for _ in range(8):
        post(driver, "/access/login", {"email": body["email"], "password": "wrong"}, 401)
    post(driver, "/access/login", {"email": body["email"], "password": "wrong"}, 429)
    with engine.connect() as db:
        account = (
            db.execute(select(accounts).where(accounts.c.email == body["email"])).mappings().one()
        )
        assert account["role"] == "driver"
        assert account["password_hash"].startswith("$argon2id$")
