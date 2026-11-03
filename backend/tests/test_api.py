from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
Session = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def override_db():
    with Session() as db:
        yield db

app.dependency_overrides[get_db] = override_db
client = TestClient(app)

def test_health():
    assert client.get("/health").json()["status"] == "ok"

def test_client_ticket_flow():
    c = client.post("/api/clients", json={"name": "Cliente Teste"})
    assert c.status_code == 201
    cid = c.json()["id"]
    t = client.post("/api/tickets", json={"client_id": cid, "title": "Sem conectividade", "priority": "alta"})
    assert t.status_code == 201
    tid = t.json()["id"]
    assert client.patch(f"/api/tickets/{tid}", json={"status": "em_andamento"}).json()["status"] == "em_andamento"
    assert any(x["id"] == tid for x in client.get("/api/tickets").json())
