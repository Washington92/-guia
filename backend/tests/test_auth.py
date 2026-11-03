"""Fluxo de autenticação isolado em SQLite na memória."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    previous = app.dependency_overrides.get(get_db)

    def override_db():
        with Session() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
        engine.dispose()


def test_bootstrap_login_logout(client):
    credentials = {"username": "admin", "password": "SenhaForteDeTeste123!"}
    assert client.post("/api/auth/bootstrap", json={"username": "admin", "password": "curta"}).status_code == 422
    assert client.post("/api/auth/bootstrap", json=credentials).status_code == 201
    assert client.post("/api/auth/bootstrap", json={"username": "outro", "password": "SenhaForteDeTeste123!"}).status_code == 403
    assert client.post("/api/auth/login", json={"username": "admin", "password": "errada"}).status_code == 401
    assert client.get("/api/auth/me").status_code == 401
    login = client.post("/api/auth/login", json=credentials)
    assert login.status_code == 200
    token = login.json()["access_token"]
    headers = {"Authorization": "Bearer " + token}
    assert client.get("/api/auth/me", headers=headers).json()["role"] == "admin"
    assert client.post("/api/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/auth/me", headers=headers).status_code == 401
