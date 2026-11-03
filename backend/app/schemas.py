from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class ClientCreate(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    email: str | None = Field(default=None, max_length=254)
    phone: str | None = Field(default=None, max_length=40)
    document: str | None = Field(default=None, max_length=32)

class ClientRead(ClientCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime

class TicketCreate(BaseModel):
    client_id: int
    title: str = Field(min_length=3, max_length=180)
    description: str = ""
    priority: Literal["baixa", "media", "alta", "critica"] = "media"

class TicketUpdate(BaseModel):
    status: Literal["aberto", "em_andamento", "resolvido", "fechado"]

class TicketRead(TicketCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime

class WorkOrderCreate(BaseModel):
    client_id: int
    ticket_id: int | None = None
    title: str = Field(min_length=3, max_length=180)
    description: str = ""

class WorkOrderUpdate(BaseModel):
    status: Literal["pendente", "em_execucao", "concluida", "cancelada"] | None = None
    description: str | None = None

class WorkOrderRead(WorkOrderCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    status: str
    created_at: datetime
