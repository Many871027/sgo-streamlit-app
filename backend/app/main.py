from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

import models, schemas
from database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestión de Operaciones (SGO) API",
    description="API for managing employee incidents, substitutions, and overtime.",
    version="1.8.0"
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Plazas Endpoint ---
@app.get("/plazas/", response_model=List[schemas.Plaza])
def read_plazas(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.Plaza).offset(skip).limit(limit).all()

# --- Incidente Endpoints ---
@app.get("/incidentes/", response_model=List[schemas.Incidente])
def read_incidentes_by_date(fecha: date, db: Session = Depends(get_db)):
    return db.query(models.Incidente).filter(models.Incidente.fecha_incidente == fecha).all()

@app.get("/incidentes/range/", response_model=List[schemas.Incidente])
def read_incidentes_by_range(start_date: date, end_date: date, db: Session = Depends(get_db)):
    return db.query(models.Incidente).filter(
        models.Incidente.fecha_incidente >= start_date,
        models.Incidente.fecha_incidente <= end_date
    ).all()

@app.post("/incidentes/", response_model=schemas.Incidente, status_code=201)
def create_or_update_incidente(incidente: schemas.IncidenteCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Incidente).filter(
        models.Incidente.plaza_id == incidente.plaza_id,
        models.Incidente.fecha_incidente == incidente.fecha_incidente
    ).first()
    if existing:
        existing.tipo_incidencia = incidente.tipo_incidencia
        existing.descripcion = incidente.descripcion
        db_obj = existing
    else:
        db_obj = models.Incidente(**incidente.dict())
        db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# --- Sustitucion Endpoints ---
@app.get("/sustituciones/range/", response_model=List[schemas.Sustitucion])
def read_sustituciones_by_range(start_date: date, end_date: date, db: Session = Depends(get_db)):
    return db.query(models.Sustitucion).filter(
        models.Sustitucion.fecha >= start_date,
        models.Sustitucion.fecha <= end_date
    ).all()

@app.post("/sustituciones/", response_model=schemas.Sustitucion, status_code=201)
def create_or_update_sustitucion(sustitucion: schemas.SustitucionCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Sustitucion).filter(
        models.Sustitucion.fecha == sustitucion.fecha,
        models.Sustitucion.plaza_ausente_id == sustitucion.plaza_ausente_id
    ).first()
    if existing:
        existing.plaza_suplente_id = sustitucion.plaza_suplente_id
        existing.motivo = sustitucion.motivo
        db_obj = existing
    else:
        db_obj = models.Sustitucion(**sustitucion.dict())
        db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# --- Tiempo Extra Endpoints ---
@app.get("/tiempo-extra/", response_model=List[schemas.TiempoExtra])
def read_tiempo_extra_by_range(start_date: date, end_date: date, db: Session = Depends(get_db)):
    return db.query(models.TiempoExtra).filter(
        models.TiempoExtra.fecha >= start_date,
        models.TiempoExtra.fecha <= end_date
    ).all()

@app.post("/tiempo-extra/", response_model=schemas.TiempoExtra, status_code=201)
def create_or_update_tiempo_extra(tiempo_extra: schemas.TiempoExtraCreate, db: Session = Depends(get_db)):
    existing = db.query(models.TiempoExtra).filter(
        models.TiempoExtra.plaza_id == tiempo_extra.plaza_id,
        models.TiempoExtra.fecha == tiempo_extra.fecha
    ).first()
    if existing:
        existing.horas = tiempo_extra.horas
        existing.motivo_cobertura = tiempo_extra.motivo_cobertura
        db_obj = existing
    else:
        db_obj = models.TiempoExtra(**tiempo_extra.dict())
        db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@app.delete("/tiempo-extra/{overtime_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tiempo_extra(overtime_id: int, db: Session = Depends(get_db)):
    db_obj = db.query(models.TiempoExtra).filter(models.TiempoExtra.id == overtime_id).first()
    if db_obj is None:
        raise HTTPException(status_code=404, detail="Overtime record not found")
    db.delete(db_obj)
    db.commit()
    return

# --- Asignacion Endpoints ---
@app.get("/asignaciones/", response_model=List[schemas.AsignacionServicio])
def read_asignaciones(fecha: date, turno: str, db: Session = Depends(get_db)):
    return db.query(models.AsignacionServicio).filter(
        models.AsignacionServicio.fecha == fecha,
        models.AsignacionServicio.turno == turno
    ).all()

@app.post("/asignaciones/", response_model=schemas.AsignacionServicio, status_code=201)
def create_or_update_asignacion(asignacion: schemas.AsignacionServicioCreate, db: Session = Depends(get_db)):
    existing = db.query(models.AsignacionServicio).filter(
        models.AsignacionServicio.plaza_id == asignacion.plaza_id,
        models.AsignacionServicio.fecha == asignacion.fecha,
        models.AsignacionServicio.turno == asignacion.turno
    ).first()
    if existing:
        existing.area_servicio = asignacion.area_servicio
        db_obj = existing
    else:
        db_obj = models.AsignacionServicio(**asignacion.dict())
        db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

# --- Coberturas Necesarias Endpoints ---
@app.get("/coberturas-necesarias/", response_model=List[schemas.CoberturaNecesaria])
def read_coberturas_necesarias(db: Session = Depends(get_db)):
    return db.query(models.CoberturaNecesaria).all()

@app.post("/coberturas-necesarias/", response_model=schemas.CoberturaNecesaria, status_code=201)
def create_cobertura_necesaria(cobertura: schemas.CoberturaNecesariaCreate, db: Session = Depends(get_db)):
    db_obj = models.CoberturaNecesaria(**cobertura.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

@app.delete("/coberturas-necesarias/{cobertura_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cobertura_necesaria(cobertura_id: int, db: Session = Depends(get_db)):
    db_obj = db.query(models.CoberturaNecesaria).filter(models.CoberturaNecesaria.id == cobertura_id).first()
    if db_obj is None:
        raise HTTPException(status_code=404, detail="Coverage need not found")
    db.delete(db_obj)
    db.commit()
    return

@app.put("/plazas/{plaza_id}", response_model=schemas.PlazaUpdate)
def update_plaza_by_id(plaza_id: str, plaza_data: schemas.PlazaUpdate, db: Session = Depends(get_db)):
    """
    Actualiza los datos de un trabajador buscando por su 'plaza' (ID).
    """
    # 1. Buscar el registro en la base de datos
    db_plaza = db.query(models.Plaza).filter(models.Plaza.plaza == plaza_id).first()

    # 2. Si no se encuentra, devolver un error 404
    if db_plaza is None:
        raise HTTPException(status_code=404, detail="Plaza no encontrada")

    # 3. Actualizar los campos del objeto con los datos recibidos
    # El método dict(exclude_unset=True) es clave: solo incluye los campos
    # que realmente se enviaron en la solicitud (ej. solo 'nombre_actual').
    update_data = plaza_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_plaza, key, value)

    # 4. Guardar los cambios en la base de datos
    db.commit()
    db.refresh(db_plaza)

    # 5. Devolver el registro actualizado
    return db_plaza

@app.post("/plazas/{plaza_id}/asignar-cobertura-temporal", response_model=schemas.Plaza)
def asignar_cobertura(plaza_id: str, cobertura_data: schemas.CoberturaTemporalCreate, db: Session = Depends(get_db)):
    db_plaza = db.query(models.Plaza).filter(models.Plaza.plaza == plaza_id).first()
    if db_plaza is None:
        raise HTTPException(status_code=404, detail="Plaza no encontrada")

    # 1. Guardar la información del trabajador original en la nueva tabla
    nueva_cobertura = models.CoberturaTemporal(
        plaza_id=db_plaza.plaza,
        nombre_trabajador_original=db_plaza.nombre_actual,
        fecha_inicio=cobertura_data.fecha_inicio,
        fecha_fin=cobertura_data.fecha_fin
    )
    db.add(nueva_cobertura)
    
    # 2. Actualizar la tabla 'plazas' con el nombre del trabajador eventual
    db_plaza.nombre_actual = cobertura_data.nombre_trabajador_eventual
    
    db.commit()
    db.refresh(db_plaza)
    return db_plaza

@app.get("/coberturas-temporales/", response_model=List[schemas.CoberturaTemporal])
def leer_coberturas_activas(db: Session = Depends(get_db)):
    return db.query(models.CoberturaTemporal).all()

@app.post("/coberturas-temporales/{cobertura_id}/finalizar", response_model=schemas.Plaza)
def finalizar_cobertura(cobertura_id: int, db: Session = Depends(get_db)):
    cobertura = db.query(models.CoberturaTemporal).filter(models.CoberturaTemporal.cobertura_id == cobertura_id).first()
    if cobertura is None:
        raise HTTPException(status_code=404, detail="Cobertura no encontrada")

    db_plaza = db.query(models.Plaza).filter(models.Plaza.plaza == cobertura.plaza_id).first()
    if db_plaza is None:
        # Esto no debería pasar, pero es una buena práctica de seguridad
        db.delete(cobertura)
        db.commit()
        raise HTTPException(status_code=404, detail="La plaza original ya no existe, se eliminó la cobertura.")

    # 1. Restaurar el nombre original en la tabla 'plazas'
    db_plaza.nombre_actual = cobertura.nombre_trabajador_original
    
    # 2. Eliminar el registro de la tabla de coberturas
    db.delete(cobertura)
    
    db.commit()
    db.refresh(db_plaza)
    return db_plaza