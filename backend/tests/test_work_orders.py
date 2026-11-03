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

def test_work_order_flow_and_costs():
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            c = client.post("/api/clients", json={"name": "Cliente OS"}).json()

            # Criar OS básica com custo de mão de obra
            created = client.post("/api/work-orders", json={
                "client_id": c["id"],
                "title": "Instalação de AP",
                "description": "Configurar Wi-Fi",
                "labor_cost": 150.0
            })
            assert created.status_code == 201
            order = created.json()
            assert order["status"] == "pendente"
            assert order["labor_cost"] == 150.0
            assert order["parts_cost"] == 0.0
            assert order["total_cost"] == 150.0
            assert order["items"] == []

            # Adicionar item/peça na OS
            item_res = client.post(f"/api/work-orders/{order['id']}/items", json={
                "description": "Cabo de Rede Furukawa Cat6 (metros)",
                "quantity": 20,
                "unit_price": 4.5
            })
            assert item_res.status_code == 201
            item = item_res.json()
            assert item["total_price"] == 90.0

            # Verificar se custos foram atualizados na OS
            refreshed = client.get(f"/api/work-orders/{order['id']}").json()
            assert refreshed["parts_cost"] == 90.0
            assert refreshed["total_cost"] == 240.0
            assert len(refreshed["items"]) == 1

            # Atualizar status e mão de obra
            changed = client.patch(f"/api/work-orders/{order['id']}", json={
                "status": "em_execucao",
                "labor_cost": 200.0
            })
            assert changed.status_code == 200
            updated = changed.json()
            assert updated["status"] == "em_execucao"
            assert updated["labor_cost"] == 200.0
            assert updated["total_cost"] == 290.0

            # Remover item e checar recalculo
            del_res = client.delete(f"/api/work-orders/{order['id']}/items/{item['id']}")
            assert del_res.status_code == 204
            after_del = client.get(f"/api/work-orders/{order['id']}").json()
            assert after_del["parts_cost"] == 0.0
            assert after_del["total_cost"] == 200.0
            assert len(after_del["items"]) == 0

            assert client.get("/api/dashboard/summary").json()["work_orders"] == 1
    finally:
        app.dependency_overrides.clear()
