from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
import models
import db_config
from models import (
    TareaDB, AsignacionDB,
    TareaCreate, TareaResponse,
    AsignacionBase, AsignacionResponse
)

app = FastAPI(
    title="API de Gestión de Tareas",
    description="Microservicio para administración de tareas en hogares compartidos",
    version="1.0.0"
)

# Crear tablas (solo desarrollo)
models.Base.metadata.create_all(bind=db_config.engine)

# --- Endpoints de Tareas ---
@app.post("/tareas/", response_model=TareaResponse, status_code=status.HTTP_201_CREATED)
def crear_tarea(
    tarea: TareaCreate,
    creador_id: str = "usuario-temporal-id",  # En producción, obtener del token JWT
    db: Session = Depends(db_config.get_db)
):
    # Verificar que el hogar existe (deberías tener esta verificación)
    
    tarea_db = TareaDB(
        titulo=tarea.titulo,
        descripcion=tarea.descripcion,
        fecha_limite=tarea.fecha_limite,
        hogar_id=tarea.hogar_id,
        creador_id=creador_id
    )
    
    db.add(tarea_db)
    db.commit()
    db.refresh(tarea_db)
    
    return tarea_db

@app.get("/tareas/", response_model=List[TareaResponse])
def listar_tareas(hogar_id: str, db: Session = Depends(db_config.get_db)):
    return db.query(TareaDB).filter(TareaDB.hogar_id == hogar_id).all()

@app.get("/tareas/{tarea_id}", response_model=TareaResponse)
def obtener_tarea(tarea_id: str, db: Session = Depends(db_config.get_db)):
    tarea = db.query(TareaDB).filter(TareaDB.id == tarea_id).first()
    if not tarea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )
    return tarea

@app.put("/tareas/{tarea_id}/completar", response_model=TareaResponse)
def marcar_como_completada(
    tarea_id: str,
    db: Session = Depends(db_config.get_db)
):
    tarea = db.query(TareaDB).filter(TareaDB.id == tarea_id).first()
    if not tarea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )
    
    tarea.completada = True
    db.commit()
    db.refresh(tarea)
    
    return tarea

# --- Endpoints de Asignaciones ---
@app.post("/tareas/{tarea_id}/asignar", response_model=AsignacionResponse)
def asignar_tarea(
    tarea_id: str,
    asignacion: AsignacionBase,
    db: Session = Depends(db_config.get_db)
):
    # Verificar que la tarea existe
    tarea = db.query(TareaDB).filter(TareaDB.id == tarea_id).first()
    if not tarea:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tarea no encontrada"
        )
    
    # Verificar que el usuario existe (deberías integrar con servicio de usuarios)
    
    # Crear la asignación
    asignacion_db = AsignacionDB(
        tarea_id=tarea_id,
        usuario_id=asignacion.usuario_id
    )
    
    db.add(asignacion_db)
    db.commit()
    db.refresh(asignacion_db)
    
    return asignacion_db

@app.get("/tareas/{tarea_id}/asignaciones", response_model=List[AsignacionResponse])
def listar_asignaciones(
    tarea_id: str,
    db: Session = Depends(db_config.get_db)
):
    return db.query(AsignacionDB).filter(AsignacionDB.tarea_id == tarea_id).all()

@app.delete("/asignaciones/{asignacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_asignacion(
    asignacion_id: str,
    db: Session = Depends(db_config.get_db)
):
    asignacion = db.query(AsignacionDB).filter(AsignacionDB.id == asignacion_id).first()
    if not asignacion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Asignación no encontrada"
        )
    
    db.delete(asignacion)
    db.commit()
    
    return None