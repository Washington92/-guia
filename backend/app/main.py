import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine
from . import models  # noqa: F401 - register tables
from .routers import clients, tickets, work_orders, dashboard, assets, stock, technicians

app = FastAPI(title="Águia Gestão CRM", version="0.5.0")
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_methods=["GET", "POST", "PATCH", "PUT"], allow_headers=["Content-Type"])
Base.metadata.create_all(bind=engine)  # MVP only; replace with Alembic migrations before production
app.include_router(clients.router)
app.include_router(tickets.router)
app.include_router(work_orders.router)
app.include_router(dashboard.router)
app.include_router(assets.router)
app.include_router(stock.router)
app.include_router(technicians.router)
app.include_router(technicians.assignments)

@app.get("/health")
def health():
    return {"status": "ok", "service": "aguia-gestao-crm"}
