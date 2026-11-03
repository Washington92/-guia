from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app

def test_assets_flow():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    def override_db():
        with Session() as db:
            yield db
    original = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            invalid = client.post("/api/assets", json={"client_id": 999, "name": "Switch 24 portas"})
            assert invalid.status_code == 404
            customer = client.post("/api/clients", json={"name": "Unidade Centro"}).json()
            created = client.post("/api/assets", json={"client_id": customer["id"], "name": "Switch 24 portas", "category": "switch", "location": "Rack TI"})
            assert created.status_code == 201
            asset_id = created.json()["id"]
            assert client.patch(f"/api/assets/{asset_id}", json={"status": "manutencao"}).json()["status"] == "manutencao"
            assert len(client.get(f"/api/assets?client_id={customer['id']}").json()) == 1
            assert client.get("/api/assets/9999").status_code == 404
    finally:
        if original is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = original
        engine.dispose()
