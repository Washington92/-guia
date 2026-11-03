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

def test_work_order_flow():
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            c = client.post("/api/clients", json={"name": "Cliente OS"}).json()
            created = client.post("/api/work-orders", json={"client_id": c["id"], "title": "Instalação de AP", "description": "Configurar Wi-Fi"})
            assert created.status_code == 201
            order = created.json()
            assert order["status"] == "pendente"
            changed = client.patch(f"/api/work-orders/{order['id']}", json={"status": "em_execucao"})
            assert changed.status_code == 200
            assert changed.json()["status"] == "em_execucao"
            assert client.get("/api/dashboard/summary").json()["work_orders"] == 1
    finally:
        app.dependency_overrides.clear()
