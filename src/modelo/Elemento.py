from sqlalchemy import Column, ForeignKey, String, Integer
from .declarative_base import Base

class Elemento(Base):
    __tablename__ = "elemento"
    id = Column(Integer, primary_key=True)
    tipo = Column(String)
    nombre = Column(String, unique=True)
    nota = Column(String)
    caja_id = Column(Integer, ForeignKey("caja.id"))

    __mapper_args__ = {
        "polymorphic_identity": "Elemento",
        "polymorphic_on": tipo,
    }
