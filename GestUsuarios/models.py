from sqlalchemy import Column, String, Boolean, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from uuid import uuid4
from db_config import Base
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional

# Modelos de SQLAlchemy
class UsuarioDB(Base):
    __tablename__ = "Usuario"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    nombre = Column(String(100))
    correo = Column(String(100), unique=True, nullable=False)
    contraseña = Column(String(255), nullable=False)
    fecha_registro = Column(TIMESTAMP, server_default=func.now())

class SessionDB(Base):
    __tablename__ = "Session"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    usuario_id = Column(String(36), ForeignKey('Usuario.id'))
    token = Column(String(255), nullable=False)
    fecha_inicio = Column(TIMESTAMP, server_default=func.now())
    fecha_expiracion = Column(TIMESTAMP, nullable=False)
    activa = Column(Boolean, default=True)

# Esquemas Pydantic
class UsuarioBase(BaseModel):
    nombre: str
    correo: EmailStr

class UsuarioCreate(UsuarioBase):
    contraseña: str

class UsuarioResponse(UsuarioBase):
    id: str
    fecha_registro: datetime

    class Config:
        orm_mode = True

class SessionBase(BaseModel):
    token: str
    fecha_expiracion: datetime

class SessionCreate(SessionBase):
    usuario_id: str

class SessionResponse(SessionBase):
    id: str
    usuario_id: str
    fecha_inicio: datetime
    activa: bool

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    correo: Optional[EmailStr] = None
    contraseña: Optional[str] = None

    class Config:
        from_attributes = True