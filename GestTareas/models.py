from sqlalchemy import Column, String, Text, TIMESTAMP, Boolean, ForeignKey
from sqlalchemy.sql import func
from uuid import uuid4
from db_config import Base
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TareaDB(Base):
    __tablename__ = "Tarea"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    titulo = Column(String(150), nullable=False)
    descripcion = Column(Text)
    fecha_asignacion = Column(TIMESTAMP, server_default=func.now())
    fecha_limite = Column(TIMESTAMP)
    completada = Column(Boolean, default=False)
    creador_id = Column(String(36), nullable=False)  # Usuario externo
    hogar_id = Column(String(36), nullable=False)    # Hogar externo

class AsignacionDB(Base):
    __tablename__ = "Asignacion"
    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    tarea_id = Column(String(36), nullable=False)     # Tarea interna
    usuario_id = Column(String(36), nullable=False)   # Usuario externo
# Esquemas Pydantic


class TareaBase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    fecha_limite: Optional[datetime] = None
    hogar_id: str

class TareaCreate(TareaBase):
    pass

class TareaResponse(TareaBase):
    id: str
    fecha_asignacion: datetime
    completada: bool
    creador_id: str
    
    class Config:
        from_attributes = True

class AsignacionBase(BaseModel):
    tarea_id: str
    usuario_id: str

class AsignacionResponse(AsignacionBase):
    id: str
    
    class Config:
        from_attributes = True