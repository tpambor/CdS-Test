from sqlalchemy import Column, ForeignKey, String, Integer
from .declarative_base import Base

class ClaveFavorita(Base):
    __tablename__ = "clavefavorita"
    id = Column(Integer, primary_key=True)
    nombre = Column(String, unique=True)
    clave = Column(String)
    pista = Column(String)
    caja_id = Column(Integer, ForeignKey("caja.id"))
