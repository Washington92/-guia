from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.models import Client, Ticket


def test_inspection_trace_links_ticket_and_order():
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
            client = Client(name="Unidade Teste")
            db.add(client)
            db.flush()
            ticket = Ticket(client_id=client.id, title="Rack: switch", description="Vistoria: Mensal | Unidade: Centro")
            db.add(ticket)
            db.commit()
            ticket_id = ticket.id

        with TestClient(app) as http:
            approval = http.post(f"/api/integrations/inspection-approval/{ticket_id}")
            assert approval.status_code == 201, approval.text
            trace = http.get(f"/api/integrations/inspection-trace/{ticket_id}")
            assert trace.status_code == 200, trace.text
            result = trace.json()
            assert result["origin"] == "inspection"
            assert result["ticket"]["id"] == ticket_id
            assert result["client"]["name"] == "Unidade Teste"
            assert result["work_orders"][0]["id"] == approval.json()["work_order"]["id"]
            assert result["assignment"] is None
            assert isinstance(result["events"], list)
            assert isinstance(result["notes"], list)
            assert http.get("/api/integrations/inspection-trace/999999").status_code == 404
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
        engine.dispose()
