#
# Pruebas unitarias para las claves favoritas
#

import unittest
import os
import re
from faker import Faker
from typing import Tuple

# Usa base de datos en memoria para las pruebas
os.environ['CAJA_DB'] = 'sqlite://'  # noqa

from src.modelo.declarative_base import Session
from src.modelo import ClaveFavorita
from src.logica.LogicaCaja import LogicaCaja
from src.logica.typing import TipoClaveFavorita

# Generar claves seguras
# Opcional se puede activar/desactivar unos grupos de caracteres y especificar el longitud del clave para generar claves inseguras para pruebas
def gen_clave_segura(fake: Faker, mayuscula=True, minuscula=True, numeros=True, especiales=True, espacios=False, longitud_min=8, longitud_max=12) -> str:
    GRUPO_MAYUSCULA = "ABCDEFGHIJKLMNOPQRSTUVWXYZÑÉÓÚÍÜ"
    GRUPO_MINUSCULA = "abcdefghijklmnopqrstuvwxyzñéóúíü"
    GRUPO_NUMEROS = "0123456789"
    GRUPO_ESPECIALES = "?-*!@#$/(){}=.,;:"

    grupos_activados = []
    if mayuscula:
        grupos_activados.append(lambda: fake.random.choice(GRUPO_MAYUSCULA))
    if minuscula:
        grupos_activados.append(lambda: fake.random.choice(GRUPO_MINUSCULA))
    if numeros:
        grupos_activados.append(lambda: fake.random.choice(GRUPO_NUMEROS))
    if especiales:
        grupos_activados.append(lambda: fake.random.choice(GRUPO_ESPECIALES))
    if espacios:
        grupos_activados.append(lambda: " ")

    longitud = fake.random.randint(longitud_min, longitud_max)

    clave = []
    while len(clave) < longitud:
        fake.random.shuffle(grupos_activados)
        for x in grupos_activados:
            clave.append(x())
            if len(clave) >= longitud:
                break

    fake.random.shuffle(clave)

    return ''.join(clave)

# Genera una clave favorita con datos aleatorias
def gen_clave(fake: Faker, mayuscula=True, minuscula=True, numeros=True, especiales=True, espacios=False, longitud_min=8, longitud_max=12) -> Tuple[ClaveFavorita, TipoClaveFavorita]:
    c = ClaveFavorita()
    c.nombre = fake.unique.name()
    c.clave = gen_clave_segura(fake, mayuscula, minuscula, numeros, especiales, espacios, longitud_min, longitud_max)
    c.pista = fake.text()
    c.caja_id = 1

    esperado: TipoClaveFavorita = {
        "nombre": c.nombre,
        "clave": c.clave,
        "pista": c.pista
    }

    return (c, esperado)

class ClaveFavoritaTestCase(unittest.TestCase):
    def setUp(self):
        self.logica = LogicaCaja()
        self.session = Session()
        self.fake = Faker(["es-CO"])
        Faker.seed(1000)

        # test_data es ordenado segun el nombre de las claves
        self.test_data = sorted([gen_clave(self.fake) for _ in range(3)], key=lambda x:x[0].nombre)

        # De lista de tuplas a tupla de listas
        cl = list()
        el = list()
        for (c, e) in self.test_data:
            cl.append(c)
            el.append(e)
        self.test_data = (cl, el)

        # Agregar claves al base de datos mezclado
        self.order = list(range(len(self.test_data[0])))
        while self.order == sorted(self.order):
            self.fake.random.shuffle(self.order)

    def tearDown(self):
        [self.session.delete(x) for x in self.session.query(ClaveFavorita).all()]
        self.session.commit()
        self.session.close()

    # Prueba para verificar que se genera un error al crear una clave con nombre vacio
    def test_nombre_vacio(self):
        self.test_data[0][0].nombre = ""
        error = self.logica.validar_crear_editar_clave(-1, self.test_data[0][0].nombre, self.test_data[0][0].clave, self.test_data[0][0].pista)
        self.assertIn("nombre".casefold(), error.casefold())

    # Prueba para verificar que se puede crear/editar una clave con un solo caracter sin error
    def test_nombre_corto(self):
        self.test_data[0][0].nombre = self.fake.random_letter()
        error = self.logica.validar_crear_editar_clave(-1, self.test_data[0][0].nombre, self.test_data[0][0].clave, self.test_data[0][0].pista)
        self.assertEqual("", error)

    # Prueba para verificar que se genera un error al crear una clave con un nombre de 256 caracteres
    def test_nombre_largo(self):
        self.test_data[0][0].nombre = ''.join(self.fake.random_letters(256))
        error = self.logica.validar_crear_editar_clave(-1, self.test_data[0][0].nombre, self.test_data[0][0].clave, self.test_data[0][0].pista)
        self.assertIn("nombre".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear una clave con maximum 2 caracteres
    def test_clave_corto(self):
        self.test_data[0][0].clave = gen_clave_segura(self.fake, longitud_min=0, longitud_max=2)
        error = self.logica.validar_crear_editar_clave(-1, self.test_data[0][0].nombre, self.test_data[0][0].clave, self.test_data[0][0].pista)
        self.assertIn("clave".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear una clave con 256 caracteres
    def test_clave_larga(self):
        self.test_data[0][0].clave = gen_clave_segura(self.fake, longitud_min=256, longitud_max=256)
        error = self.logica.validar_crear_editar_clave(-1, self.test_data[0][0].nombre, self.test_data[0][0].clave, self.test_data[0][0].pista)
        self.assertIn("clave".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear una clave con pista de solo 2 caracteres
    def test_pista_corto(self):
        self.test_data[0][0].pista = ''.join(self.fake.random_letters(2))
        error = self.logica.validar_crear_editar_clave(-1, self.test_data[0][0].nombre, self.test_data[0][0].clave, self.test_data[0][0].pista)
        self.assertIn("pista".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear una clave con pista de 256 caracteres
    def test_pista_larga(self):
        self.test_data[0][0].pista = ''.join(self.fake.random_letters(256))
        error = self.logica.validar_crear_editar_clave(-1, self.test_data[0][0].nombre, self.test_data[0][0].clave, self.test_data[0][0].pista)
        self.assertIn("pista".casefold(), error.casefold())

    # Prueba para verificar que al crear una clave se ha guardado en el base de datos
    def test_agregar_clave(self):
        self.logica.crear_clave(self.test_data[0][0].nombre, self.test_data[0][0].clave, self.test_data[0][0].pista)

        claves = self.session.query(ClaveFavorita).all()
        self.assertEqual(1, len(claves))
        self.assertEqual(self.test_data[0][0].nombre, claves[0].nombre)
        self.assertEqual(self.test_data[0][0].clave, claves[0].clave)
        self.assertEqual(self.test_data[0][0].pista, claves[0].pista)

    # Prueba para verificar que no es posible generar dos claves con el mismo nombre
    def test_agregar_clave_duplicada(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        error = self.logica.validar_crear_editar_clave(-1, self.test_data[0][0].nombre, self.test_data[0][0].clave, self.test_data[0][0].pista)
        self.assertNotEqual("", error)

    # Prueba para verificar que no hay error al cambiar la clave sin cambiar el nombre
    def test_editar_clave_sin_cambiar_nombre(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        self.test_data[0][1].nombre = self.test_data[0][0].nombre

        error = self.logica.validar_crear_editar_clave(0, self.test_data[0][1].nombre, self.test_data[0][1].clave, self.test_data[0][1].pista)
        self.assertEqual("", error)

    # Prueba para verificar que se genera un error al cambiar el nombre de una clave al nombre de una clave que ya existe
    def test_editar_clave_duplicada(self):
        self.session.add(self.test_data[0][0])
        self.session.add(self.test_data[0][1])
        self.session.commit()

        error = self.logica.validar_crear_editar_clave(0, self.test_data[0][1].nombre, self.test_data[0][0].clave, self.test_data[0][0].pista)
        self.assertNotEqual("", error)

    # Prueba para verificar que al editar una clave el cambio se refleja en el base de datos
    def test_editar_clave_db(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        self.logica.editar_clave(0, self.test_data[0][1].nombre, self.test_data[0][1].clave, self.test_data[0][1].pista)

        claves = self.session.query(ClaveFavorita).all()
        self.assertEqual(1, len(claves))
        self.assertEqual(self.test_data[0][1].nombre, claves[0].nombre)
        self.assertEqual(self.test_data[0][1].clave, claves[0].clave)
        self.assertEqual(self.test_data[0][1].pista, claves[0].pista)

    # Prueba para verificar que la clave generada tiene longitud igual o mayor a 8
    def test_generar_clave_longitud(self):
        clave = self.logica.generar_clave()
        self.assertGreaterEqual(len(clave), 8)

    # Prueba para verificar que la clave generada contiene numeros
    def test_generar_clave_numeros(self):
        clave = self.logica.generar_clave()
        self.assertTrue(re.search("[0-9]", clave))

    # Prueba para verificar que la clave generada contiene minusculas
    def test_generar_clave_minusculas(self):
        clave = self.logica.generar_clave()
        self.assertTrue(re.search("[a-zñéóúíü]", clave))

    # Prueba para verificar que la clave generada contiene mayusculas
    def test_generar_clave_mayusculas(self):
        clave = self.logica.generar_clave()
        self.assertTrue(re.search("[A-ZÑÉÓÚÍÜ]", clave))

    # Prueba para verificar que la clave generada contiene caracteres especiales
    def test_generar_clave_caracteres(self):
        clave = self.logica.generar_clave()
        self.assertTrue(re.search("[?\-*!@#$/(){}=.,;:]", clave))

    # Prueba para verificar que la clave generada no contiene espacios
    def test_generar_clave_espacio(self):
        clave = self.logica.generar_clave()
        self.assertNotIn(" ", clave)
    
    # Prueba para verificar que cada vez se genera diferentes claves
    def test_generar_clave_diferente(self):
        clave1 = self.logica.generar_clave()
        clave2 = self.logica.generar_clave()
        self.assertNotEqual(clave1, clave2)

    # Prueba para verificar que la logica retorna las claves favoritas del base de datos
    def test_listar_clave_favorita(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        claves = self.logica.dar_claves_favoritas()
        self.assertEqual([self.test_data[1][0]], claves)

    # Prueba para verificar que la lista de las claves favoritas esta ordenado segun sus nombres
    def test_lista_claves_ordenadas(self):
        # Agregar claves al base de datos en orden predefinido
        for idx in self.order:
            self.session.add(self.test_data[0][idx])
        self.session.commit()

        # Esperamos que retorna la lista ordenada
        self.assertEqual(self.test_data[1], self.logica.dar_claves_favoritas())

    # Prueba para verificar que se puede buscar una clave por su nombre
    def test_clave_por_nombre(self):
        # Agregar claves al base de datos en orden predefinido
        for idx in self.order:
            self.session.add(self.test_data[0][idx])
        self.session.commit()

        for x in self.test_data[0]:
            self.assertEqual(self.logica.dar_clave(x.nombre), x.clave)

    # Prueba para verificar que se puede buscar una clave por su id
    def test_clave_por_id(self):
        # Agregar claves al base de datos en orden predefinido
        for idx in self.order:
            self.session.add(self.test_data[0][idx])
        self.session.commit()

        for (idx, esperado) in enumerate(self.test_data[1]):
            self.assertEqual(self.logica.dar_clave_favorita(idx), esperado)

    # Prueba para verificar que al borrar una clave favorita se ha borrado en el base de datos también
    def test_borrar_clave(self):
        for idx in self.order:
            self.session.add(self.test_data[0][idx])
        self.session.commit()       

        id_borrar = self.fake.random.randrange(len(self.order))

        self.logica.eliminar_clave(id_borrar)

        piezas = list(range(len(self.order)))
        piezas.remove(id_borrar)

        claves = sorted(self.session.query(ClaveFavorita).all(), key=lambda x:x.nombre)
        self.assertEqual(len(piezas), len(claves))
        for i, j in enumerate(piezas):
            self.assertEqual(self.test_data[1][j]["nombre"], claves[i].nombre)
            self.assertEqual(self.test_data[1][j]["clave"], claves[i].clave)
            self.assertEqual(self.test_data[1][j]["pista"], claves[i].pista)

    # Prueba para verificar que al borrar una clave favorita no usada no se genera un error
    def test_borrar_clave_no_usada(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        error = self.logica.validar_eliminar_clave(0)
        self.assertEqual("", error)

    # Prueba para verificar que al borrar una clave favorita usada se genera un error
    def test_borrar_clave_usada(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        from test_Login import gen_login
        (login, _) = gen_login(self.fake, self.test_data[0][0])
        self.session.add(login)
        self.session.commit()

        error = self.logica.validar_eliminar_clave(0)
        self.assertNotEqual("", error)
