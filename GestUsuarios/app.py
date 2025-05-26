from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import models, db_config
from models import UsuarioCreate, UsuarioResponse, SessionResponse
import uuid
from datetime import datetime, timedelta
import secrets
from passlib.context import CryptContext

app = FastAPI(
    title="API de Gestión de Usuarios",
    description="Microservicio para gestión de usuarios con autenticación",
    version="0.2.0"
)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Crear tablas al iniciar (solo para desarrollo)
models.Base.metadata.create_all(bind=db_config.engine)

# --- Helpers ---
def generar_token():
    return secrets.token_urlsafe(32)

def calcular_expiracion(hours=24):
    return datetime.now() + timedelta(hours=hours)

def verificar_contraseña(contraseña: str, hashed_contraseña: str) -> bool:
    return pwd_context.verify(contraseña, hashed_contraseña)

def obtener_hashed_contraseña(contraseña: str) -> str:
    return pwd_context.hash(contraseña)

# --- Endpoints de Usuarios ---
@app.get("/")
def read_root():
    return {
        "message": "Bienvenido a la API de Gestión de Usuarios",
        "documentación": "Visite /docs o /redoc para la interfaz interactiva"
    }
@app.post("/usuarios/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def crear_usuario(usuario: UsuarioCreate, db: Session = Depends(db_config.get_db)):
    # Verificar si el correo ya existe
    db_usuario = db.query(models.UsuarioDB).filter(models.UsuarioDB.correo == usuario.correo).first()
    if db_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El correo ya está registrado"
        ) 
    # Crear usuario en la base de datos
    usuario_db = models.UsuarioDB(
        id=str(uuid.uuid4()),
        nombre=usuario.nombre,
        correo=usuario.correo,
        contraseña= obtener_hashed_contraseña(usuario.contraseña),
        fecha_registro=datetime.now()
    )

    db.add(usuario_db)
    db.commit()
    db.refresh(usuario_db)
    
    return usuario_db

@app.get("/usuarios/", response_model=List[UsuarioResponse])
def listar_usuarios(db: Session = Depends(db_config.get_db)):
    return db.query(models.UsuarioDB).all()

@app.get("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def obtener_usuario(usuario_id: str, db: Session = Depends(db_config.get_db)):
    usuario = db.query(models.UsuarioDB).filter(models.UsuarioDB.id == usuario_id).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario

# --- Endpoints de Autenticación ---
@app.post("/login/", response_model=SessionResponse)
def iniciar_sesion(correo: str, contraseña: str, db: Session = Depends(db_config.get_db)):
    # Verificar credenciales 
    usuario = db.query(models.UsuarioDB).filter(
        models.UsuarioDB.correo == correo,
    ).first()
    
    if not usuario or not verificar_contraseña(contraseña, usuario.contraseña):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas",
            headers={"WWW-Authenticate": "Bearer"}
        )
        # Invalidar sesiones anteriores (opcional)
    db.query(models.SessionDB).filter(
        models.SessionDB.usuario_id == usuario.id,
        models.SessionDB.activa == True
    ).update({"activa": False})
    
    # Crear nueva sesión
    nueva_sesion = models.SessionDB(
        usuario_id=usuario.id,
        token=generar_token(),
        fecha_expiracion=calcular_expiracion()
    )
    
    db.add(nueva_sesion)
    db.commit()
    db.refresh(nueva_sesion)
    
    return nueva_sesion

@app.post("/logout/")
def cerrar_sesion(session_id: str, db: Session = Depends(db_config.get_db)):
    sesion = db.query(models.SessionDB).filter(models.SessionDB.id == session_id).first()
    
    if not sesion:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sesión no encontrada"
        )
    
    sesion.activa = False
    db.commit()
    
    return {"message": "Sesión cerrada correctamente"}

@app.put("/usuarios/{usuario_id}", response_model=UsuarioResponse)
def actualizar_usuario(
    usuario_id: str,
    usuario_actualizado: UsuarioCreate,
    db: Session = Depends(db_config.get_db)
):
    # Buscar el usuario en la base de datos
    db_usuario = db.query(models.UsuarioDB).filter(models.UsuarioDB.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Verificar si el nuevo email ya existe (si es diferente al actual)
    if usuario_actualizado.correo != db_usuario.correo:
        existe_email = db.query(models.UsuarioDB).filter(
            models.UsuarioDB.correo == usuario_actualizado.correo,
            models.UsuarioDB.id != usuario_id
        ).first()
        if existe_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El correo ya está en uso por otro usuario"
            )
    
    # Actualizar los campos
    db_usuario.nombre = usuario_actualizado.nombre
    db_usuario.correo = usuario_actualizado.correo
    
    # Solo actualizar contraseña si se proporcionó una nueva
    if usuario_actualizado.contraseña:
        db_usuario.contraseña = obtener_hashed_contraseña(usuario_actualizado.contraseña)
    
    db.commit()
    db.refresh(db_usuario)
    
    return db_usuario

@app.delete("/usuarios/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_usuario(
    usuario_id: str,
    db: Session = Depends(db_config.get_db)
):
    # Buscar el usuario en la base de datos
    db_usuario = db.query(models.UsuarioDB).filter(models.UsuarioDB.id == usuario_id).first()
    if not db_usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    
    # Primero eliminar las sesiones asociadas
    db.query(models.SessionDB).filter(
        models.SessionDB.usuario_id == usuario_id
    ).delete()
    
    # Luego eliminar el usuario
    db.delete(db_usuario)
    db.commit()
    
    return None  # 204 No Content