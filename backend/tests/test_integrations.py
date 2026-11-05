from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app.models import Client, Technician, Ticket, WorkOrder

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def override_db():
    with TestSession() as db:
        yield db

def test_checklist_import_creates_ticket_and_optional_work_order():
    app.dependency_overrides[get_db] = override_db
    try:
        with TestSession() as db:
            client = Client(name="Unidade Smart Fit")
            tech = Technician(name="Técnica Exemplo")
            db.add_all([client, tech]); db.commit()
            client_id, tech_id = client.id, tech.id
        with TestClient(app) as http:
            sectors = http.get("/api/integrations/sectors")
            assert sectors.status_code == 200 and "Catracas" in sectors.json()["sectors"]
            response = http.post("/api/integrations/checklist-import", json={
                "client_id": client_id, "checklist_name": "Vistoria semanal", "unit_name": "Paulista",
                "inspector_name": "Equipe local", "auto_create_work_orders": True, "technician_id": tech_id,
                "issues": [{"sector":"Catracas", "item":"Leitor não responde", "observation":"Necessário avaliar conexão", "priority":"alta", "photo_url":"https://example.com/foto.jpg"}]
            })
            assert response.status_code == 201, response.text
            data = response.json()
            assert len(data["created_tickets"]) == 1 and len(data["created_work_orders"]) == 1
            with TestSession() as db:
                ticket = db.get(Ticket, data["created_tickets"][0]["id"])
                order = db.get(WorkOrder, data["created_work_orders"][0]["id"])
                assert "Catracas" in ticket.description and "https://example.com/foto.jpg" in ticket.description
                assert order.ticket_id == ticket.id and order.technician_id == tech_id
    finally:
        app.dependency_overrides.clear()

def test_checklist_import_rejects_unknown_client():
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            response = client.post("/api/integrations/checklist-import", json={
                "client_id":999,"checklist_name":"Vistoria","unit_name":"Unidade","inspector_name":"Pessoa",
                "issues":[{"sector":"Rack","item":"Switch sem energia"}]
            })
            assert response.status_code == 404
    finally:
        app.dependency_overrides.clear()

def test_checklist_batch_approval_and_discard():
    app.dependency_overrides[get_db] = override_db
    try:
        with TestSession() as db:
            client = Client(name="Smart Fit Santana")
            tech = Technician(name="Técnico Validador")
            db.add_all([client, tech])
            db.commit()
            c_id, t_id = client.id, tech.id

        with TestClient(app) as http:
            # Test template endpoint
            tmpl = http.get("/api/integrations/template/smartfit")
            assert tmpl.status_code == 200
            assert "Facial SPA" in tmpl.json()["sectors"]
            assert len(tmpl.json()["suggested_items"]) >= 10

            # Test batch approval
            payload = {
                "client_id": c_id,
                "checklist_name": "Auditoria de Unidade",
                "unit_name": "Santana",
                "inspector_name": "Supervisor Regional",
                "items": [
                    {
                        "sector": "Facial SPA",
                        "item": "Câmera de reconhecimento offline",
                        "observation": "Necessário reiniciar switch PoE",
                        "priority": "critica",
                        "approved": True,
                        "create_work_order": True,
                        "technician_id": t_id,
                        "estimated_duration_hours": 1.5
                    },
                    {
                        "sector": "Som",
                        "item": "Caixa da sala de ginástica sem áudio",
                        "observation": "Cabo desconectado no canal 2",
                        "priority": "media",
                        "approved": True,
                        "create_work_order": False
                    },
                    {
                        "sector": "Balcão",
                        "item": "Impressora térmica limpa e funcionando",
                        "observation": "Item em conformidade",
                        "priority": "baixa",
                        "approved": False
                    }
                ]
            }
            res = http.post("/api/integrations/checklist-batch", json=payload)
            assert res.status_code == 201, res.text
            body = res.json()
            assert body["summary"]["total_items"] == 3
            assert body["summary"]["approved_tickets"] == 2
            assert body["summary"]["created_work_orders"] == 1
            assert body["summary"]["discarded_count"] == 1
            assert len(body["discarded_items"]) == 1
            assert body["discarded_items"][0]["sector"] == "Balcão"
    finally:
        app.dependency_overrides.clear()


def test_approval_creates_work_order_once_for_inspection_ticket():
    app.dependency_overrides[get_db] = override_db
    try:
        with TestSession() as db:
            client = Client(name="Unidade Aprovação")
            db.add(client); db.commit()
            ticket = Ticket(client_id=client.id, title="Rack: switch superaquecido", description="Vistoria: Mensal | Unidade: Centro | Setor: Rack", priority="alta")
            db.add(ticket); db.commit()
            ticket_id = ticket.id

        with TestClient(app) as http:
            first = http.post(f"/api/integrations/inspection-approval/{ticket_id}")
            assert first.status_code == 201, first.text
            assert first.json()["created"] is True
            second = http.post(f"/api/integrations/inspection-approval/{ticket_id}")
            assert second.status_code == 201, second.text
            assert second.json()["created"] is False
            assert second.json()["work_order"]["id"] == first.json()["work_order"]["id"]
            with TestSession() as db:
                assert db.query(WorkOrder).filter(WorkOrder.ticket_id == ticket_id).count() == 1
    finally:
        app.dependency_overrides.clear()
