from sqlalchemy import Column, ForeignKey, String, Integer
from sqlalchemy.orm import relationship
from .Elemento import Elemento

# Importar para asegurar de que se conocen antes de hacer referencia a ellos
from .ClaveFavorita import ClaveFavorita

class Login(Elemento):
    __tablename__ = "login"
    id = Column(Integer, ForeignKey("elemento.id"), primary_key=True)
    email = Column(String)
    usuario = Column(String)
    url = Column(String)
    clave_id = Column(Integer, ForeignKey("clavefavorita.id"))
    clave = relationship("ClaveFavorita")

    __mapper_args__ = {
        "polymorphic_identity": "Login",
    }
