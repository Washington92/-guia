"""Testes de regressão: atribuições, histórico e isolamento de dados."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import Base, get_db
from app.main import app


@pytest.fixture
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    previous = app.dependency_overrides.get(get_db)

    def override_db():
        with Session() as db:
            yield db

    app.dependency_overrides[get_db] = override_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        if previous is None:
            app.dependency_overrides.pop(get_db, None)
        else:
            app.dependency_overrides[get_db] = previous
        engine.dispose()


def make_ticket(client):
    customer = client.post("/api/clients", json={"name": "Cliente Laboratório"})
    assert customer.status_code == 201
    ticket = client.post("/api/tickets", json={"client_id": customer.json()["id"], "title": "Falha na rede"})
    assert ticket.status_code == 201
    return ticket.json()["id"]


def test_notes_are_scoped_to_ticket(client):
    ticket_id = make_ticket(client)
    note = client.post(f"/api/tickets/{ticket_id}/notes", json={"author": "Técnico N2", "content": "Teste de VLAN executado"})
    assert note.status_code == 201
    assert note.json()["ticket_id"] == ticket_id
    notes = client.get(f"/api/tickets/{ticket_id}/notes")
    assert notes.status_code == 200
    assert len(notes.json()) == 1
    assert notes.json()[0]["content"] == "Teste de VLAN executado"
    assert client.get("/api/tickets/99999/notes").status_code == 404
    assert client.post("/api/tickets/99999/notes", json={"author": "Técnico", "content": "Nota inválida"}).status_code == 404
    assert client.post(f"/api/tickets/{ticket_id}/notes", json={"author": "A", "content": "x"}).status_code == 422


def test_status_audit_only_when_value_changes(client):
    ticket_id = make_ticket(client)
    url = f"/api/tickets/{ticket_id}"
    assert client.patch(url, json={"status": "em_andamento"}).status_code == 200
    assert client.patch(url, json={"status": "em_andamento"}).status_code == 200
    events = client.get(url + "/events")
    assert events.status_code == 200
    assert len(events.json()) == 1
    assert events.json()[0]["previous_value"] == "aberto"
    assert events.json()[0]["new_value"] == "em_andamento"


def test_technician_assignment_and_reassignment_audit(client):
    ticket_id = make_ticket(client)
    first = client.post("/api/technicians", json={"name": "Técnico N1", "specialty": "Service Desk"})
    second = client.post("/api/technicians", json={"name": "Técnico N2", "specialty": "Redes"})
    assert first.status_code == 201 and second.status_code == 201
    first_id, second_id = first.json()["id"], second.json()["id"]
    endpoint = f"/api/tickets/{ticket_id}/assignment"
    assert client.put(endpoint, json={"technician_id": first_id}).status_code == 200
    assert client.put(endpoint, json={"technician_id": first_id}).status_code == 200
    assert client.put(endpoint, json={"technician_id": second_id}).status_code == 200
    assignments = client.get("/api/tickets/assignments")
    assert assignments.status_code == 200
    assert assignments.json()[0]["technician_id"] == second_id
    events = client.get(f"/api/tickets/{ticket_id}/events").json()
    assert len([event for event in events if event["event_type"] == "assignment"]) == 2
    assert client.put(endpoint, json={"technician_id": 99999}).status_code == 404
    assert client.put("/api/tickets/99999/assignment", json={"technician_id": first_id}).status_code == 404
