from sqlalchemy import Column, String, Date, Integer, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Plaza(Base):
    __tablename__ = 'plazas'
    plaza = Column(String, primary_key=True, index=True)
    categoria = Column(String)
    horario = Column(String)
    dias_descanso = Column(String)
    matricula_actual = Column(String, nullable=True)
    nombre_actual = Column(String, nullable=True)

class Incidente(Base):
    __tablename__ = 'incidentes'
    incidente_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plaza_id = Column(String, ForeignKey('plazas.plaza'))
    fecha_incidente = Column(Date, nullable=False)
    tipo_incidencia = Column(String, nullable=False)
    descripcion = Column(String, nullable=True)
    registrado_por = Column(String, nullable=True)

class Sustitucion(Base):
    __tablename__ = 'sustituciones'
    sustitucion_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    fecha = Column(Date, nullable=False)
    plaza_ausente_id = Column(String, ForeignKey('plazas.plaza'))
    plaza_suplente_id = Column(String, ForeignKey('plazas.plaza'))
    motivo = Column(String, nullable=True)

class TiempoExtra(Base):
    __tablename__ = 'tiempo_extra'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plaza_id = Column(String, ForeignKey('plazas.plaza'))
    fecha = Column(Date, nullable=False)
    horas = Column(Float, nullable=False)
    motivo_cobertura = Column(String, nullable=False)

class AsignacionServicio(Base):
    __tablename__ = 'asignaciones_servicio'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plaza_id = Column(String, ForeignKey('plazas.plaza'))
    fecha = Column(Date, nullable=False)
    turno = Column(String, nullable=False)
    area_servicio = Column(String, nullable=False)

# NEW MODEL FOR PLANNED COVERAGE NEEDS
class CoberturaNecesaria(Base):
    __tablename__ = 'coberturas_necesarias'
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plaza_id_ausente = Column(String, ForeignKey('plazas.plaza'))
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)

class CoberturaTemporal(Base):
    __tablename__ = 'coberturas_temporales'
    cobertura_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    plaza_id = Column(String, ForeignKey('plazas.plaza'))
    nombre_trabajador_original = Column(String)
    fecha_inicio = Column(Date, nullable=False)
    fecha_fin = Column(Date, nullable=False)
