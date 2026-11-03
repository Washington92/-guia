"""Regression coverage for authenticated dashboard analytics."""
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app
from app.models import Client, Ticket, WorkOrder, Asset, Technician, TicketAssignment


def test_dashboard_analytics_filters_and_workload():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    previous = app.dependency_overrides.get(get_db)

    def override_db():
        with Session() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with Session() as db:
            first = Client(name="Unidade A")
            second = Client(name="Unidade B")
            tech = Technician(name="Lucas", specialty="N1")
            db.add_all([first, second, tech])
            db.flush()
            db.add_all([
                Ticket(client_id=first.id, title="Crítico", priority="critica", status="aberto",
                       created_at=datetime(2026, 11, 1, tzinfo=timezone.utc)),
                Ticket(client_id=first.id, title="Resolvido", priority="baixa", status="resolvido",
                       created_at=datetime(2026, 11, 2, tzinfo=timezone.utc)),
                Ticket(client_id=second.id, title="Outro", priority="alta", status="em_andamento",
                       created_at=datetime(2026, 10, 1, tzinfo=timezone.utc)),
                WorkOrder(client_id=first.id, title="OS", status="pendente",
                          created_at=datetime(2026, 11, 1, tzinfo=timezone.utc)),
                Asset(client_id=first.id, name="Switch", status="ativo",
                      created_at=datetime(2026, 11, 1, tzinfo=timezone.utc)),
            ])
            db.flush()
            ticket_id = db.query(Ticket).filter_by(title="Crítico").one().id
            db.add(TicketAssignment(ticket_id=ticket_id, technician_id=tech.id))
            first_id = first.id
            db.commit()
        with TestClient(app) as client:
            response = client.get("/api/dashboard/analytics", params={
                "client_id": first_id, "start_date": "2026-11-01", "end_date": "2026-11-02"
            })
            assert response.status_code == 200
            data = response.json()
            assert data["tickets"]["total"] == 2
            assert data["tickets"]["active"] == 1
            assert data["tickets"]["urgent_active"] == 1
            assert data["tickets"]["by_priority"]["critica"] == 1
            assert data["tickets"]["by_priority"]["baixa"] == 1
            assert data["tickets"]["unassigned_active"] == 0
            assert data["work_orders"]["pending_or_running"] == 1
            assert data["assets"]["total"] == 1
            assert data["technician_workload"][0]["active_tickets"] == 1\n            assert data["top_technician"]["leaders"] == []\n            assert data["top_technician"]["completed_total"] == 1\n            assert data["top_technician"]["completed_without_assignment"] == 1
            assert data["sla"]["configured"] is False
            assert client.get("/api/dashboard/analytics", params={
                "start_date": "2026-11-03", "end_date": "2026-11-01"
            }).status_code == 422
            assert client.get("/api/dashboard/analytics", params={"client_id": 999}).status_code == 404
            empty = client.get("/api/dashboard/analytics", params={
                "start_date": "2026-12-01", "end_date": "2026-12-31"
            }).json()
            assert empty["tickets"]["total"] == 0
            assert empty["tickets"]["unassigned_active"] == 0
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
        engine.dispose()
