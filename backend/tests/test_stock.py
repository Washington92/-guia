from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app

def test_stock_movements_and_shortage():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    previous = app.dependency_overrides.get(get_db)
    def override_db():
        with Session() as db:
            yield db
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            item_response = client.post("/api/stock/items", json={"name": "Cabo CAT6", "unit": "m", "min_quantity": 10})
            assert item_response.status_code == 201
            item_id = item_response.json()["id"]
            assert client.post("/api/stock/movements", json={"item_id": item_id, "type": "saida", "quantity": 1}).status_code == 409
            assert client.post("/api/stock/movements", json={"item_id": item_id, "type": "entrada", "quantity": 30}).status_code == 201
            assert client.post("/api/stock/movements", json={"item_id": item_id, "type": "saida", "quantity": 12}).status_code == 201
            assert client.get("/api/stock/items").json()[0]["quantity"] == 18
            assert len(client.get("/api/stock/movements").json()) == 2
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
        engine.dispose()
