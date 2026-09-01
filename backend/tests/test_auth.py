"""Authentication, authorization, and health tests. Results must be executed, not invented."""

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.user import UserRole
from tests.conftest import create_role_user, make_expired_token
from app.models.lawyer import Specialization
from app.core.security import create_refresh_token


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"


def test_health_db(client: TestClient) -> None:
    response = client.get("/health/db")
    assert response.status_code == 200
    assert response.json()["database"] == "reachable"


def test_register_success(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Anupa Client",
            "email": "Anupa@Example.com",
            "password": "securePass1",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "anupa@example.com"
    assert body["name"] == "Anupa Client"
    assert body["role"] == "CLIENT"
    assert body["is_active"] is True
    assert "id" in body
    assert "created_at" in body


def test_register_does_not_return_password(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Safe User",
            "email": "safe@example.com",
            "password": "securePass1",
        },
    )
    assert response.status_code == 201
    body = response.json()
    assert "password" not in body
    assert "password_hash" not in body
    raw = response.text.lower()
    assert "securepass1" not in raw
    assert "password_hash" not in raw


def test_register_rejects_role_in_payload(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={
            "name": "Attacker",
            "email": "attacker@example.com",
            "password": "securePass1",
            "role": "ADMIN",
        },
    )
    assert response.status_code == 422


def test_duplicate_email(client: TestClient) -> None:
    payload = {
        "name": "First",
        "email": "dup@example.com",
        "password": "securePass1",
    }
    assert client.post("/api/auth/register", json=payload).status_code == 201
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


def test_invalid_registration_short_password(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"name": "X", "email": "bad@example.com", "password": "short"},
    )
    assert response.status_code == 422


def test_invalid_registration_bad_email(client: TestClient) -> None:
    response = client.post(
        "/api/auth/register",
        json={"name": "X", "email": "not-an-email", "password": "securePass1"},
    )
    assert response.status_code == 422


def test_login_success(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={"name": "Login User", "email": "login@example.com", "password": "securePass1"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "login@example.com", "password": "securePass1"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert isinstance(body["access_token"], str)
    assert body["access_token"]
    assert "password" not in body


def test_login_incorrect_password(client: TestClient) -> None:
    client.post(
        "/api/auth/register",
        json={"name": "Login User", "email": "wrongpw@example.com", "password": "securePass1"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "wrongpw@example.com", "password": "incorrect-password"},
    )
    assert response.status_code == 401


def test_login_unknown_email(client: TestClient) -> None:
    response = client.post(
        "/api/auth/login",
        json={"email": "missing@example.com", "password": "securePass1"},
    )
    assert response.status_code == 401


def test_me_with_valid_token(client: TestClient, auth_header: dict[str, str]) -> None:
    response = client.get("/api/auth/me", headers=auth_header)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "client@example.com"
    assert body["role"] == "CLIENT"
    assert "password" not in body
    assert "password_hash" not in body


def test_me_without_token(client: TestClient) -> None:
    response = client.get("/api/auth/me")
    assert response.status_code == 401


def test_me_invalid_token(client: TestClient) -> None:
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )
    assert response.status_code == 401


def test_me_expired_token(client: TestClient, db: Session) -> None:
    token = make_expired_token(uuid4())
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401


def _login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"email": email, "password": "securePass1"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_client_authorization(client: TestClient, db: Session) -> None:
    create_role_user(db, email="role-client@example.com", role=UserRole.CLIENT)
    headers = _login(client, "role-client@example.com")
    assert client.get("/api/dev/client", headers=headers).status_code == 200
    assert client.get("/api/dev/lawyer", headers=headers).status_code == 403
    assert client.get("/api/dev/admin", headers=headers).status_code == 403


def test_lawyer_authorization(client: TestClient, db: Session) -> None:
    create_role_user(db, email="role-lawyer@example.com", role=UserRole.LAWYER)
    headers = _login(client, "role-lawyer@example.com")
    assert client.get("/api/dev/lawyer", headers=headers).status_code == 200
    assert client.get("/api/dev/client", headers=headers).status_code == 403
    assert client.get("/api/dev/admin", headers=headers).status_code == 403


def test_admin_authorization(client: TestClient, db: Session) -> None:
    create_role_user(db, email="role-admin@example.com", role=UserRole.ADMIN)
    headers = _login(client, "role-admin@example.com")
    assert client.get("/api/dev/admin", headers=headers).status_code == 200
    assert client.get("/api/dev/client", headers=headers).status_code == 403
    assert client.get("/api/dev/lawyer", headers=headers).status_code == 403


def test_dev_routes_require_auth(client: TestClient) -> None:
    assert client.get("/api/dev/client").status_code == 401
    assert client.get("/api/dev/lawyer").status_code == 401
    assert client.get("/api/dev/admin").status_code == 401


def test_refresh_rotation_and_reuse_rejected(client: TestClient) -> None:
    client.post("/api/auth/register", json={"name":"R", "email":"r@example.com", "password":"securePass1"})
    login = client.post("/api/auth/login", json={"email":"r@example.com", "password":"securePass1"}).json()
    refreshed = client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != login["refresh_token"]
    assert client.post("/api/auth/refresh", json={"refresh_token": login["refresh_token"]}).status_code == 401


def test_invalid_and_expired_refresh_rejected(client: TestClient, db: Session) -> None:
    assert client.post("/api/auth/refresh", json={"refresh_token":"invalid"}).status_code == 401
    create_role_user(db, email="expired@example.com", role=UserRole.CLIENT)
    user = db.query(__import__('app.models.user', fromlist=['User']).User).filter_by(email="expired@example.com").one()
    token, _, _ = create_refresh_token(subject=user.id, role=user.role.value)
    assert client.post("/api/auth/refresh", json={"refresh_token": token}).status_code == 401


def test_logout_revokes_refresh(client: TestClient) -> None:
    client.post("/api/auth/register", json={"name":"L", "email":"l@example.com", "password":"securePass1"})
    tokens = client.post("/api/auth/login", json={"email":"l@example.com", "password":"securePass1"}).json()
    assert client.post("/api/auth/logout", headers={"Authorization": f"Bearer {tokens['access_token']}"}, json={"refresh_token":tokens["refresh_token"]}).status_code == 204
    assert client.post("/api/auth/refresh", json={"refresh_token":tokens["refresh_token"]}).status_code == 401


def test_lawyer_registration_and_profile_access(client: TestClient) -> None:
    response = client.post("/api/auth/register/lawyer", json={"name":"Lawyer", "email":"lawyer@example.com", "password":"securePass1"})
    assert response.status_code == 201 and response.json()["role"] == "LAWYER"
    tokens = client.post("/api/auth/login", json={"email":"lawyer@example.com", "password":"securePass1"}).json()
    headers={"Authorization":f"Bearer {tokens['access_token']}"}
    assert client.get("/api/lawyers/me", headers=headers).status_code == 200
    assert client.put("/api/lawyers/me", headers=headers, json={"city":"Delhi", "years_of_experience":2}).json()["city"] == "Delhi"


def test_client_cannot_access_lawyer_profile(client: TestClient, auth_header: dict[str, str]) -> None:
    assert client.get("/api/lawyers/me", headers=auth_header).status_code == 403


def test_specialization_update_validates_ids(client: TestClient, db: Session) -> None:
    client.post("/api/auth/register/lawyer", json={"name":"Spec", "email":"spec@example.com", "password":"securePass1"})
    spec = Specialization(slug="property", name="Property")
    db.add(spec); db.commit(); db.refresh(spec)
    tokens=client.post("/api/auth/login",json={"email":"spec@example.com","password":"securePass1"}).json(); headers={"Authorization":f"Bearer {tokens['access_token']}"}
    assert client.put("/api/lawyers/me/specializations",headers=headers,json={"specialization_ids":[str(spec.id)]}).status_code==200
    assert client.put("/api/lawyers/me/specializations",headers=headers,json={"specialization_ids":[str(spec.id),str(spec.id)]}).status_code==422
