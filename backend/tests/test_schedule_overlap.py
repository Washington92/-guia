from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Client, Technician, WorkOrder
from app.routers.schedule import list_schedule


def test_schedule_includes_appointments_started_before_window():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    try:
        with Session(engine) as db:
            client = Client(name="Cliente")
            technician = Technician(name="Técnico")
            db.add_all([client, technician])
            db.flush()
            order = WorkOrder(
                client_id=client.id, technician_id=technician.id,
                title="Visita", scheduled_at=datetime(2026, 11, 4, 10, tzinfo=timezone.utc),
                estimated_duration_hours=2,
            )
            db.add(order)
            db.commit()
            result = list_schedule(
                start=datetime(2026, 11, 4, 11, tzinfo=timezone.utc),
                end=datetime(2026, 11, 4, 11, 30, tzinfo=timezone.utc),
                technician_id=technician.id, db=db,
            )
            assert [row.id for row in result] == [order.id]
    finally:
        engine.dispose()
