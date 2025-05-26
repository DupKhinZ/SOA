from sqlalchemy import Column, String, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from uuid import uuid4
from db_config import Base
from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
from enum import Enum

# --- Modelos de SQLAlchemy ---
class HogarDB(Base):
    __tablename__ = "Hogar"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    nombre = Column(String(100), unique=True, nullable=False)
    fecha_creacion = Column(TIMESTAMP, server_default=func.now())
    propietario_id = Column(String(5))  


class MiembroHogarDB(Base):
    __tablename__ = "MiembroHogar"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid4()))
    usuario_id = Column(String(36), nullable=False) 
    hogar_id = Column(String(36), ForeignKey('Hogar.id'), nullable=False)  
    rol = Column(String(50), default='miembro')

# --- Esquemas Pydantic ---
class RolMiembro(str, Enum):
    miembro = "miembro"
    administrador = "administrador"
    propietario = "propietario"

class HogarBase(BaseModel):
    nombre: str

class HogarCreate(HogarBase):
    pass

class HogarResponse(HogarBase):
    id: str
    fecha_creacion: datetime
    propietario_id: str

    class Config:
        orm_mode = True

class MiembroHogarBase(BaseModel):
    usuario_id: str
    hogar_id: str
    rol: RolMiembro = RolMiembro.miembro

class MiembroHogarResponse(MiembroHogarBase):
    id: str

    class Config:
        orm_mode = True

class InvitacionRequest(BaseModel):
    email_invitado: EmailStr
    rol: RolMiembro = RolMiembro.miembro