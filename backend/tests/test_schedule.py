from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app


def test_schedule_conflicts_filtering_and_update():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)

    def override_db():
        with Session() as db:
            yield db

    previous = app.dependency_overrides.get(get_db)
    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as client:
            customer = client.post("/api/clients", json={"name": "Cliente Agenda"}).json()
            tech = client.post("/api/technicians", json={"name": "Técnico Agenda"}).json()
            assert tech["id"]

            first = client.post("/api/work-orders", json={
                "client_id": customer["id"], "title": "Visita técnica",
                "technician_id": tech["id"], "scheduled_at": "2026-11-04T10:00:00Z",
                "estimated_duration_hours": 2,
            })
            assert first.status_code == 201, first.text
            assert first.json()["technician_id"] == tech["id"]
            assert first.json()["estimated_duration_hours"] == 2

            overlap = client.post("/api/work-orders", json={
                "client_id": customer["id"], "title": "Visita em conflito",
                "technician_id": tech["id"], "scheduled_at": "2026-11-04T11:30:00Z",
                "estimated_duration_hours": 1,
            })
            assert overlap.status_code == 409

            non_overlap = client.post("/api/work-orders", json={
                "client_id": customer["id"], "title": "Visita seguinte",
                "technician_id": tech["id"], "scheduled_at": "2026-11-04T12:00:00Z",
                "estimated_duration_hours": 1,
            })
            assert non_overlap.status_code == 201, non_overlap.text

            schedule = client.get("/api/schedule", params={
                "start": "2026-11-04T00:00:00Z", "end": "2026-11-05T00:00:00Z",
                "technician_id": tech["id"],
            })
            assert schedule.status_code == 200
            assert len(schedule.json()) == 2

            updated = client.patch(f"/api/work-orders/{non_overlap.json()['id']}", json={
                "scheduled_at": "2026-11-04T11:00:00Z",
            })
            assert updated.status_code == 409

            finished = client.patch(f"/api/work-orders/{first.json()['id']}", json={"status": "concluida"})
            assert finished.status_code == 200
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
