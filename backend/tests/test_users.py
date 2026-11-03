"""Controle de acesso administrativo e revogação de sessão."""
from test_auth import client  # noqa: F401 - fixture de banco isolado

def test_user_lifecycle_and_permissions(client):
    admin = {"username": "root", "password": "SenhaAdminMuitoForte123!"}
    assert client.post("/api/auth/bootstrap", json=admin).status_code == 201
    admin_token = client.post("/api/auth/login", json=admin).json()["access_token"]
    headers = {"Authorization": "Bearer " + admin_token}
    assert client.get("/api/users").status_code == 401
    technician = {"username": "tecnico.n1", "password": "SenhaTecnicoMuitoForte123!", "role": "technician"}
    created = client.post("/api/users", json=technician, headers=headers)
    assert created.status_code == 201
    uid = created.json()["id"]
    assert created.json()["role"] == "technician"
    assert "password_hash" not in created.json()
    assert client.post("/api/users", json=technician, headers=headers).status_code == 409
    tech_token = client.post("/api/auth/login", json={"username": technician["username"], "password": technician["password"]}).json()["access_token"]
    tech_headers = {"Authorization": "Bearer " + tech_token}
    assert client.get("/api/users", headers=tech_headers).status_code == 403
    assert client.post("/api/users", json={"username": "outro", "password": "SenhaValida123!"}, headers=tech_headers).status_code == 403
    assert client.patch("/api/users/1", json={"active": False}, headers=headers).status_code == 409
    assert client.patch(f"/api/users/{uid}", json={"role": "supervisor"}, headers=headers).status_code == 200
    assert client.patch(f"/api/users/{uid}", json={"active": False}, headers=headers).status_code == 200
    assert client.get("/api/auth/me", headers=tech_headers).status_code == 401
    assert client.post("/api/auth/login", json={"username": technician["username"], "password": technician["password"]}).status_code == 401
