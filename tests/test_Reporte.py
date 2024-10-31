#
# Pruebas unitarias para el reporte
#

import unittest
import os
from datetime import datetime, timedelta
from faker import Faker

# Usa base de datos en memoria para las pruebas
os.environ['CAJA_DB'] = 'sqlite://' # noqa

from src.modelo.declarative_base import Session
from src.modelo import Elemento, ClaveFavorita
from src.logica.LogicaCaja import LogicaCaja
from src.logica.typing import TipoReporte

from test_ClaveFavorita import gen_clave
from test_Login import gen_login
from test_Identificacion import gen_id
from test_Tarjeta import gen_tarjeta
from test_Secreto import gen_secreto

class ReporteTestCase(unittest.TestCase):
    def setUp(self):
        self.logica = LogicaCaja()
        self.session = Session()
        self.fake = Faker(["es-CO"])
        Faker.seed(1000)

    def tearDown(self):
        [self.session.delete(x) for x in self.session.query(Elemento).all()]
        [self.session.delete(x) for x in self.session.query(ClaveFavorita).all()]
        self.session.commit()
        self.session.close()

    # Prueba para verificar que cantidad de logins en el reporte es correcto
    def test_cantidad_logins(self):
        (clave1, _) = gen_clave(self.fake)
        self.session.add(clave1)
        self.session.commit()

        (login1, _) = gen_login(self.fake, clave1)
        (login2, _) = gen_login(self.fake, clave1)
        (login3, _) = gen_login(self.fake, clave1)
        logins = [login1, login2, login3]

        for x in logins:
            self.session.add(x)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(len(logins), reporte["logins"])

    # Prueba para verificar que cantidad de IDs en el reporte es correcto
    def test_cantidad_ids(self):
        (id1, _) = gen_id(self.fake)
        (id2, _) = gen_id(self.fake)
        (id3, _) = gen_id(self.fake)
        ids = [id1, id2, id3]

        for x in ids:
            self.session.add(x)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(len(ids), reporte["ids"])

    # Prueba para verificar que cantidad de tarjetas en el reporte es correcto
    def test_cantidad_tarjetas(self):
        (clave1, _) = gen_clave(self.fake)
        self.session.add(clave1)
        self.session.commit()
    
        (tarjeta1, _) = gen_tarjeta(self.fake, clave1)
        (tarjeta2, _) = gen_tarjeta(self.fake, clave1)
        (tarjeta3, _) = gen_tarjeta(self.fake, clave1)
        tarjetas = [tarjeta1, tarjeta2, tarjeta3]

        for x in tarjetas:
            self.session.add(x)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(len(tarjetas), reporte["tarjetas"])

    # Prueba para verificar que cantidad de secretos en el reporte es correcto
    def test_cantidad_secretos(self):
        (clave1, _) = gen_clave(self.fake)
        self.session.add(clave1)
        self.session.commit()
    
        (secreto1, _) = gen_secreto(self.fake, clave1)
        (secreto2, _) = gen_secreto(self.fake, clave1)
        (secreto3, _) = gen_secreto(self.fake, clave1)
        tarjetas = [secreto1, secreto2, secreto3]

        for x in tarjetas:
            self.session.add(x)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(len(tarjetas), reporte["secretos"])

    # Prueba para verificar el reporte con una caja vacia
    def test_caja_vacia(self):
        esperado = TipoReporte(
            logins=0,
            ids=0,
            tarjetas=0,
            secretos=0,
            inseguras=0,
            avencer=0,
            masdeuna=0,
            nivel=1.0
        )

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(esperado, reporte)

    # Prueba para verificar que la cantidad de tarjetas a vencer en el reporte es correcto
    def test_tarjetas_a_vencer(self):
        (clave1, _) = gen_clave(self.fake)
        self.session.add(clave1)
        self.session.commit()
    
        (tarjeta1, _) = gen_tarjeta(self.fake, clave1, vencimiento=self.fake.date_between('+3M','+2y'))
        (tarjeta2, _) = gen_tarjeta(self.fake, clave1, vencimiento=self.fake.date_between('now','+3M'))
        self.session.add(tarjeta1)
        self.session.add(tarjeta2)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(1, reporte["avencer"])

    # Prueba para verificar que la cantidad de IDs a vencer en el reporte es correcto
    def test_ids_a_vencer(self):
        (id1, _) = gen_id(self.fake, vencimiento=self.fake.date_between('+3M','+2y'))
        (id2, _) = gen_id(self.fake, vencimiento=self.fake.date_between('now','+3M'))

        self.session.add(id1)
        self.session.add(id2)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(1, reporte["avencer"])


    # Prueba para verificar que la porcentaje de elementos a vencer es correcto
    def test_porcentaje_no_por_vencer(self):
        (clave1, _) = gen_clave(self.fake)
        (clave2, _) = gen_clave(self.fake)
        self.session.add(clave1)
        self.session.add(clave2)
        self.session.commit()
    
        (tarjeta1, _) = gen_tarjeta(self.fake, clave1, vencimiento=self.fake.date_between('+3M','+2y'))
        (tarjeta2, _) = gen_tarjeta(self.fake, clave2, vencimiento=self.fake.date_between('now','+3M'))
        (id1, _) = gen_id(self.fake, vencimiento=self.fake.date_between('+3M','+2y'))
        (id2, _) = gen_id(self.fake, vencimiento=self.fake.date_between('+3M','+2y'))
        (id3, _) = gen_id(self.fake, vencimiento=self.fake.date_between('now','+3M'))

        self.session.add(tarjeta1)
        self.session.add(tarjeta2)
        self.session.add(id1)
        self.session.add(id2)
        self.session.add(id3)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertAlmostEqual(0.8 + 0.2 * 3/5, reporte["nivel"])

    # Prueba para verificar que cantidad de claves usadas más que una vez es correcto
    def test_cantidad_claves_usadas(self):
        (clave1, _) = gen_clave(self.fake)
        (clave2, _) = gen_clave(self.fake)
        (clave3, _) = gen_clave(self.fake)
        (clave4, _) = gen_clave(self.fake)
        claves = [clave1, clave2, clave3, clave4]
        for x in claves:
            self.session.add(x)
        self.session.commit()

        (login1, _) = gen_login(self.fake, clave1)
        (tarjeta1, _) = gen_tarjeta(self.fake, clave1)

        (login2, _) = gen_login(self.fake, clave2)
        (secreto1, _) = gen_secreto(self.fake, clave2)

        (tarjeta2, _) = gen_tarjeta(self.fake, clave3)
        (secreto2, _) = gen_secreto(self.fake, clave3)

        (login3, _) = gen_login(self.fake, clave4)
        
        elementos = [login1, login2, login3, tarjeta1, tarjeta2, secreto1, secreto2]

        for x in elementos:
            self.session.add(x)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(3, reporte["masdeuna"])

    # Prueba para verificar que claves usadas más que tres veces se refleja en nivel del seguridad
    def test_cantidad_clave_usada_4(self):
        (clave1, _) = gen_clave(self.fake)
        (clave2, _) = gen_clave(self.fake)
        (clave3, _) = gen_clave(self.fake)
        (clave4, _) = gen_clave(self.fake)
        claves = [clave1, clave2, clave3, clave4]
        for x in claves:
            self.session.add(x)
        self.session.commit()

        (login1, _) = gen_login(self.fake, clave1)
        (tarjeta1, _) = gen_tarjeta(self.fake, clave1)

        (login2, _) = gen_login(self.fake, clave1)
        (secreto1, _) = gen_secreto(self.fake, clave1)

        (tarjeta2, _) = gen_tarjeta(self.fake, clave2)
        (secreto2, _) = gen_secreto(self.fake, clave3)

        (login3, _) = gen_login(self.fake, clave4)
        
        elementos = [login1, login2, login3, tarjeta1, tarjeta2, secreto1, secreto2]

        for x in elementos:
            self.session.add(x)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertAlmostEqual(0.7 + 0.3 * 0.0, reporte["nivel"])

    # Prueba para verificar que claves usadas más que una vez se refleja en nivel del seguridad
    def test_cantidad_clave_usada_3(self):
        (clave1, _) = gen_clave(self.fake)
        (clave2, _) = gen_clave(self.fake)
        (clave3, _) = gen_clave(self.fake)
        claves = [clave1, clave2, clave3]
        for x in claves:
            self.session.add(x)
        self.session.commit()

        (login1, _) = gen_login(self.fake, clave1)
        (tarjeta1, _) = gen_tarjeta(self.fake, clave1)
        (login2, _) = gen_login(self.fake, clave1)

        (secreto1, _) = gen_secreto(self.fake, clave2)
        (tarjeta2, _) = gen_tarjeta(self.fake, clave2)

        (secreto2, _) = gen_secreto(self.fake, clave3)
        
        elementos = [login1, login2, tarjeta1, tarjeta2, secreto1, secreto2]

        for x in elementos:
            self.session.add(x)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertAlmostEqual(0.7 + 0.3 * 0.5, reporte["nivel"])

    # Prueba para verificar que una clave corta cuenta como clave insegura
    def test_clave_corta(self):
        (clave1, _) = gen_clave(self.fake, longitud_min=0, longitud_max=7)
        self.session.add(clave1)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(1, reporte["inseguras"]) 

    # Prueba para verificar que una clave sin números cuenta como clave insegura
    def test_clave_sin_numeros(self):
        (clave1, _) = gen_clave(self.fake, numeros=False)
        self.session.add(clave1)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(1, reporte["inseguras"]) 

    # Prueba para verificar que una clave sin mayúsculas cuenta como clave insegura
    def test_clave_sin_mayusculas(self):
        (clave1, _) = gen_clave(self.fake, mayuscula=False)
        self.session.add(clave1)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(1, reporte["inseguras"]) 

    # Prueba para verificar que una clave sin minúsculas cuenta como clave insegura
    def test_clave_sin_minusculas(self):
        (clave1, _) = gen_clave(self.fake, minuscula=False)
        self.session.add(clave1)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(1, reporte["inseguras"]) 

    # Prueba para verificar que una clave sin caracteres espaciales cuenta como clave insegura
    def test_clave_sin_especiales(self):
        (clave1, _) = gen_clave(self.fake, especiales=False)
        self.session.add(clave1)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(1, reporte["inseguras"]) 

    # Prueba para verificar que una clave con espacios cuenta como clave insegura
    def test_clave_con_espacios(self):
        (clave1, _) = gen_clave(self.fake, espacios=True)
        self.session.add(clave1)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertEqual(1, reporte["inseguras"]) 

    # Prueba para verificar que la porcentaje de claves seguras es correcto
    def test_porcentaje_claves_seguras(self):
        (clave1, _) = gen_clave(self.fake)
        (clave2, _) = gen_clave(self.fake, especiales=False)
        (clave3, _) = gen_clave(self.fake)
        (clave4, _) = gen_clave(self.fake, mayuscula=False)
        (clave5, _) = gen_clave(self.fake, numeros=False)
        claves = [clave1, clave2, clave3, clave4, clave5]
        for x in claves:
            self.session.add(x)
        self.session.commit()

        reporte = self.logica.dar_reporte_seguridad()
        self.assertAlmostEqual(0.5 + 0.5 * 2/5, reporte["nivel"])
