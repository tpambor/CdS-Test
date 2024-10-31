#
# Pruebas unitarias para caja
#

import unittest
import os

# Usa base de datos en memoria para las pruebas
os.environ['CAJA_DB'] = 'sqlite://'  # noqa

from src.modelo.declarative_base import Session
from src.modelo import Caja
from src.logica.LogicaCaja import LogicaCaja

class CajaTestCase(unittest.TestCase):

    def setUp(self):
        self.logica = LogicaCaja()
        self.session = Session()

    def tearDown(self):
        self.session.query(Caja).delete()
        self.session.commit()
        self.session.close()

    # Prueba para verificar que la lógica retorna la clave maestra guardada en el base de datos
    def test_clave_maestra(self):
        clave = self.session.query(Caja).first().clave_maestra

        self.assertEqual(clave,self.logica.dar_claveMaestra())


