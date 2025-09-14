from pydantic import BaseModel
from datetime import date
from typing import Optional

# --- Plaza Schemas ---
class Plaza(BaseModel):
    plaza: str
    categoria: str
    horario: str
    dias_descanso: str
    matricula_actual: Optional[str] = None
    nombre_actual: Optional[str] = None
    class Config: from_attributes = True

# --- Incidente Schemas ---
class IncidenteCreate(BaseModel):
    plaza_id: str
    fecha_incidente: date
    tipo_incidencia: str
    descripcion: Optional[str] = None
    registrado_por: Optional[str] = None

class Incidente(IncidenteCreate):
    incidente_id: int
    class Config: from_attributes = True

# --- Sustitucion Schemas ---
class SustitucionCreate(BaseModel):
    fecha: date
    plaza_ausente_id: str
    plaza_suplente_id: str
    motivo: Optional[str] = None

class Sustitucion(SustitucionCreate):
    sustitucion_id: int
    class Config: from_attributes = True

# --- TiempoExtra Schemas ---
class TiempoExtraCreate(BaseModel):
    plaza_id: str
    fecha: date
    horas: float
    motivo_cobertura: str

class TiempoExtra(TiempoExtraCreate):
    id: int
    class Config: from_attributes = True

# --- NEW SCHEMAS FOR SERVICE ASSIGNMENTS ---
class AsignacionServicioCreate(BaseModel):
    plaza_id: str
    fecha: date
    turno: str
    area_servicio: str

class AsignacionServicio(AsignacionServicioCreate):
    id: int
    class Config: from_attributes = True
# --- NEW SCHEMAS FOR PLANNED COVERAGE NEEDS ---
class CoberturaNecesariaCreate(BaseModel):
    plaza_id_ausente: str
    start_date: date
    end_date: date

class CoberturaNecesaria(CoberturaNecesariaCreate):
    id: int
    class Config: from_attributes = True

class PlazaUpdate(BaseModel):
    nombre_actual: Optional[str] = None
    categoria: Optional[str] = None
    horario: Optional[str] = None
    dias_descanso: Optional[str] = None
    matricula_actual: Optional[str] = None
    # Añade aquí cualquier otro campo de la tabla 'plazas' que quieras que sea editable

    class Config:
        orm_mode = True
