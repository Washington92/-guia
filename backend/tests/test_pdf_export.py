from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app.models import Client, Technician, WorkOrder, WorkOrderItem

engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def override_db():
    with TestSession() as db:
        yield db


def test_work_order_pdf_export():
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            with TestSession() as db:
                cli = Client(name="Smart Fit Paulista", document="12.345.678/0001-90", email="contato@smartfit.com", phone="(11) 99999-8888")
                db.add(cli)
                tech = Technician(name="Carlos Silva", email="carlos.silva@aguia.com")
                db.add(tech)
                db.commit()

                wo = WorkOrder(
                    client_id=cli.id,
                    title="Manutenção Preventiva de Racks e Switch",
                    description="Substituição de conectores RJ45 e alinhamento de cabeamento de dados.",
                    status="em_andamento",
                    technician_id=tech.id,
                    scheduled_at=datetime(2026, 11, 10, 14, 0, tzinfo=timezone.utc),
                    estimated_duration_hours=3.0,
                    labor_cost=150.0,
                    parts_cost=80.0,
                    total_cost=230.0,
                )
                db.add(wo)
                db.commit()

                it1 = WorkOrderItem(work_order_id=wo.id, description="Conector RJ45 Cat6", quantity=10, unit_price=3.0, total_price=30.0)
                it2 = WorkOrderItem(work_order_id=wo.id, description="Patch Cord 1.5m", quantity=2, unit_price=25.0, total_price=50.0)
                db.add_all([it1, it2])
                db.commit()
                wo_id = wo.id

            response = client.get(f"/api/work-orders/{wo_id}/pdf")
            assert response.status_code == 200
            assert response.headers["content-type"] == "application/pdf"
            assert f"ordem_servico_{wo_id:05d}.pdf" in response.headers["content-disposition"]
            assert response.content.startswith(b"%PDF-")
            assert len(response.content) > 1000

            resp_404 = client.get("/api/work-orders/999999/pdf")
            assert resp_404.status_code == 404
    finally:
        app.dependency_overrides.clear()
