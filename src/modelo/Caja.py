from sqlalchemy import Column, String, Integer
from sqlalchemy.orm import relationship
from .declarative_base import Base

# Importar para asegurar de que se conocen antes de hacer referencia a ellos
from .ClaveFavorita import ClaveFavorita
from .Elemento import Elemento

class Caja(Base):
    __tablename__ = "caja"
    id = Column(Integer, primary_key=True)
    clave_maestra = Column(String)
    claves = relationship("ClaveFavorita", lazy="dynamic")
    elementos = relationship("Elemento", lazy="dynamic")
