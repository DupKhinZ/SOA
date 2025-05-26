import datetime
from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import models, db_config
from models import (
    HogarDB, MiembroHogarDB,  # Modelos SQLAlchemy
    HogarCreate, HogarResponse,  # Esquemas Pydantic
    MiembroHogarBase, MiembroHogarResponse,
    InvitacionRequest, RolMiembro
)
from uuid import uuid4
import secrets

app = FastAPI(
    title="API de Gestión de Hogares",
    description="Microservicio para administración de hogares compartidos",
    version="1.0.0"
)

# Crear tablas (solo desarrollo)
models.Base.metadata.create_all(bind=db_config.engine)

# --- Funciones auxiliares ---
def obtener_usuario_por_email(db: Session, email: str):
    """Función simulada - deberías integrar con tu servicio de usuarios"""
    # Esto es un mock - en producción usa tu servicio real de usuarios
    usuario_mock = models.UsuarioDB(
        id=str(uuid4()),
        nombre="Usuario Mock",
        correo=email,
        contraseña="hasheada",
        fecha_registro=datetime.now()
    )
    return usuario_mock

def verificar_permisos_admin(db: Session, hogar_id: str, usuario_id: str):
    miembro = db.query(MiembroHogarDB).filter(
        MiembroHogarDB.hogar_id == hogar_id,
        MiembroHogarDB.usuario_id == usuario_id,
        MiembroHogarDB.rol.in_(['administrador', 'propietario'])
    ).first()
    if not miembro:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos de administrador"
        )
    return miembro

# --- Endpoints de Hogares ---
@app.post("/hogares/", response_model=HogarResponse, status_code=status.HTTP_201_CREATED)
def crear_hogar(
    hogar: HogarCreate,
    usuario_id: str = "usuario-temporal-id",  # En producción, obtener del token JWT
    db: Session = Depends(db_config.get_db)
):
    # Verificar si el nombre ya existe
    db_hogar = db.query(HogarDB).filter(HogarDB.nombre == hogar.nombre).first()
    if db_hogar:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ya existe un hogar con este nombre"
        )
    
    # Crear el hogar
    hogar_db = HogarDB(
        nombre=hogar.nombre,
        propietario_id=usuario_id
    )
    db.add(hogar_db)
    db.commit()
    db.refresh(hogar_db)
    
    # Agregar al propietario como miembro
    miembro_db = MiembroHogarDB(
        usuario_id=usuario_id,
        hogar_id=hogar_db.id,
        rol='propietario'
    )
    db.add(miembro_db)
    db.commit()
    
    return hogar_db

@app.get("/hogares/", response_model=List[HogarResponse])
def listar_hogares(db: Session = Depends(db_config.get_db)):
    return db.query(HogarDB).all()

@app.get("/hogares/{hogar_id}", response_model=HogarResponse)
def obtener_hogar(hogar_id: str, db: Session = Depends(db_config.get_db)):
    hogar = db.query(HogarDB).filter(HogarDB.id == hogar_id).first()
    if not hogar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hogar no encontrado"
        )
    return hogar

# --- Endpoints de Miembros ---
@app.post("/hogares/{hogar_id}/miembros/invitar", response_model=MiembroHogarResponse)
def invitar_miembro(
    hogar_id: str,
    invitacion: InvitacionRequest,
    usuario_actual_id: str = "usuario-temporal-id",  # En producción, obtener del token JWT
    db: Session = Depends(db_config.get_db)
):
    # Verificar que el hogar existe
    hogar = db.query(HogarDB).filter(HogarDB.id == hogar_id).first()
    if not hogar:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hogar no encontrado"
        )
    
    # Verificar permisos de administrador
    verificar_permisos_admin(db, hogar_id, usuario_actual_id)
    
    # Buscar usuario por email (simulado)
    db_usuario = obtener_usuario_por_email(db, invitacion.email_invitado)
    
    # Verificar si ya es miembro
    db_miembro = db.query(MiembroHogarDB).filter(
        MiembroHogarDB.hogar_id == hogar_id,
        MiembroHogarDB.usuario_id == db_usuario.id
    ).first()
    if db_miembro:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El usuario ya es miembro de este hogar"
        )
    
    # Crear la membresía
    miembro_db = MiembroHogarDB(
        usuario_id=db_usuario.id,
        hogar_id=hogar_id,
        rol=invitacion.rol
    )
    db.add(miembro_db)
    db.commit()
    db.refresh(miembro_db)
    
    return miembro_db

@app.get("/hogares/{hogar_id}/miembros", response_model=List[MiembroHogarResponse])
def listar_miembros(
    hogar_id: str,
    db: Session = Depends(db_config.get_db)
):
    miembros = db.query(MiembroHogarDB).filter(
        MiembroHogarDB.hogar_id == hogar_id
    ).all()
    return miembros

@app.delete("/hogares/{hogar_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_hogar(
    hogar_id: str,
    usuario_actual_id: str = "usuario-temporal-id",  # En producción, obtener del token JWT
    db: Session = Depends(db_config.get_db)
):
    # Verificar que el usuario es propietario
    db_hogar = db.query(HogarDB).filter(
        HogarDB.id == hogar_id,
        HogarDB.propietario_id == usuario_actual_id
    ).first()
    if not db_hogar:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo el propietario puede eliminar el hogar"
        )
    
    # Eliminar miembros primero
    db.query(MiembroHogarDB).filter(
        MiembroHogarDB.hogar_id == hogar_id
    ).delete()
    
    # Eliminar el hogar
    db.delete(db_hogar)
    db.commit()
    
    return None