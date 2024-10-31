from sqlalchemy import Column, ForeignKey, String, Integer, Date
from .Elemento import Elemento

class Identificacion(Elemento):
    __tablename__ = "identificacion"
    id = Column(Integer, ForeignKey("elemento.id"), primary_key=True)
    numero = Column(String)
    nombre_completo = Column(String)
    nacimiento = Column(Date)
    expedicion = Column(Date)
    vencimiento = Column(Date)

    __mapper_args__= {
        "polymorphic_identity": "Identificación",
    }
