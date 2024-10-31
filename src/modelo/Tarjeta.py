from sqlalchemy import Column, ForeignKey, String, Integer, Date
from sqlalchemy.orm import relationship
from .Elemento import Elemento

# Importar para asegurar de que se conocen antes de hacer referencia a ellos
from .ClaveFavorita import ClaveFavorita

class Tarjeta(Elemento):
    __tablename__ = "tarjeta"
    id = Column(Integer, ForeignKey("elemento.id"), primary_key=True)
    numero = Column(String)
    titular = Column(String)
    codigo_seguridad = Column(String)
    direccion = Column(String)
    telefono = Column(String)
    vencimiento = Column(Date)
    clave_id = Column(Integer, ForeignKey("clavefavorita.id"))
    clave = relationship("ClaveFavorita")

    __mapper_args__ = {
        "polymorphic_identity": "Tarjeta",
    }
