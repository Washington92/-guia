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

def test_health(client):
    assert client.get("/health").json()["status"] == "ok"

def test_client_ticket_flow(client):
    c = client.post("/api/clients", json={"name": "Cliente Teste"})
    assert c.status_code == 201
    cid = c.json()["id"]
    t = client.post("/api/tickets", json={"client_id": cid, "title": "Sem conectividade", "priority": "alta"})
    assert t.status_code == 201
    tid = t.json()["id"]
    assert client.patch(f"/api/tickets/{tid}", json={"status": "em_andamento"}).json()["status"] == "em_andamento"
    assert any(x["id"] == tid for x in client.get("/api/tickets").json())
