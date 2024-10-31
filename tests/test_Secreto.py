#
# Pruebas unitarias para los elementos de secreto
#

import unittest
import os
from faker import Faker

# Usa base de datos en memoria para las pruebas
os.environ['CAJA_DB'] = 'sqlite://' # noqa

from src.modelo.declarative_base import Session
from src.modelo import Elemento, Secreto, ClaveFavorita
from src.logica.LogicaCaja import LogicaCaja
from src.logica.typing import TipoElemento
from test_ClaveFavorita import gen_clave

def gen_secreto(fake: Faker, clave: ClaveFavorita):
    secreto = Secreto()
    secreto.nombre = fake.unique.name()
    secreto.nota = fake.text()
    secreto.secreto = fake.text()
    secreto.clave=clave
    secreto.caja_id = 1

    esperado: TipoElemento = {
        "nombre_elemento": secreto.nombre,
        "notas": secreto.nota,
        "tipo": "Secreto",
        "secreto": secreto.secreto,
        "clave": secreto.clave.nombre
    }

    return (secreto, esperado)

class SecretoTestCase(unittest.TestCase):
    def setUp(self):
        self.logica = LogicaCaja()
        self.session = Session()
        self.fake=Faker(["es-CO"])
        Faker.seed(1000)

        (self.clave,_) = gen_clave(self.fake)
        self.session.add(self.clave)
        self.session.commit()

        # test_data es ordenado segun el nombre de las claves
        self.test_data = sorted([gen_secreto(self.fake, self.clave) for _ in range(3)], key=lambda x:x[0].nombre)

        # De lista de tuplas a tupla de listas
        cl = list()
        el = list()
        for (c, e) in self.test_data:
            cl.append(c)
            el.append(e)
        self.test_data = (cl, el)

        # Agregar secretos al base de datos mezclado
        self.order = list(range(len(self.test_data[0])))
        while self.order == sorted(self.order):
            self.fake.random.shuffle(self.order)

    def tearDown(self):
        [self.session.delete(x) for x in self.session.query(Elemento).all()]
        [self.session.delete(x) for x in self.session.query(ClaveFavorita).all()]
        self.session.commit()
        self.session.close()

    # Prueba para verificar que la logica retorna los elementos de secreto del base de datos
    def test_listar_secreto(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        elementos = self.logica.dar_elementos()
        self.assertEqual([self.test_data[1][0]], elementos)

    # Prueba para verificar que la lista elementos esta ordenado segun sus nombres
    def test_listar_ordenado(self):
        for idx in self.order:
            self.session.add(self.test_data[0][idx])
        self.session.commit()

        self.assertEqual(self.test_data[1], self.logica.dar_elementos())

    # Prueba para verificar que se puede buscar un elemento por su id
    def test_buscar_por_id(self):
        for idx in self.order:
            self.session.add(self.test_data[0][idx])
        self.session.commit()

        for (idx, esperado) in enumerate(self.test_data[1]):
            self.assertEqual(esperado, self.logica.dar_elemento(idx))

    # Función de ayuda para llamar a self.logica.validar_crear_editar_secreto con los datos de un objeto de tipo Secreto
    def validar_crear_editar(self, id: int, secreto: Secreto):
        nombre_clave = "" if secreto.clave is None else secreto.clave.nombre
        return self.logica.validar_crear_editar_secreto(id,
            secreto.nombre, secreto.secreto, nombre_clave, secreto.nota)

    # Prueba para verificar que no se genera un error al crear un elemento valido
    def test_agregar_elemento_valido_sin_error(self):
        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertEqual("", error)

    # Prueba para verificar que se genera un error al crear un elemento con nombre vacio
    def test_nombre_vacio(self):
        self.test_data[0][0].nombre = ""

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("nombre".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con un nombre de 256 caracteres
    def test_nombre_largo(self):
        self.test_data[0][0].nombre = ''.join(self.fake.random_letters(256))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("nombre".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con nota corta
    def test_nota_corta(self):
        self.test_data[0][0].nota = ''.join(self.fake.random_letters(2))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("notas".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con nota de 513 caracteres
    def test_nota_larga(self):
        self.test_data[0][0].nota = ''.join(self.fake.random_letters(513))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("notas".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con secreto corto
    def test_secreto_corto(self):
        self.test_data[0][0].secreto = ''.join(self.fake.random_letters(2))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("secreto".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con secreto de 256 caracteres
    def test_secreto_largo(self):
        self.test_data[0][0].secreto = ''.join(self.fake.random_letters(256))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("secreto".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento sin clave favorita
    def test_sin_clave(self):
        self.test_data[0][0].clave = None

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("clave".casefold(), error.casefold())

    # Prueba para verificar que no es posible generar dos elementos con el mismo nombre
    def test_agregar_con_mismo_nombre(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertNotEqual("", error)

    # Assert si elemento no contiene los datos esperados
    def assertEsperado(self, esperado: TipoElemento, elemento: Elemento):
        self.assertEqual(esperado["tipo"], elemento.tipo)
        self.assertEqual(esperado["nombre_elemento"], elemento.nombre)
        self.assertEqual(esperado["secreto"], elemento.secreto)
        self.assertEqual(esperado["clave"], elemento.clave.nombre)
        self.assertEqual(esperado["notas"], elemento.nota)

    # Prueba para verificar que al crear una tarjeta se ha guardado en el base de datos
    def test_agregar_secreto_db(self):
        secreto = self.test_data[0][0]

        self.logica.crear_secreto(
            secreto.nombre, secreto.secreto, secreto.clave.nombre, secreto.nota)

        elementos = self.session.query(Elemento).all()
        self.assertEqual(1, len(elementos))
        self.assertEsperado(self.test_data[1][0], elementos[0])

    # Prueba para verificar que no hay error al cambiar un secreto sin cambiar el nombre
    def test_editar_secreto_sin_cambiar_nombre(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        self.test_data[0][1].nombre = self.test_data[0][0].nombre

        error = self.validar_crear_editar(0, self.test_data[0][1])
        self.assertEqual("", error)

    # Prueba para verificar que se genera un error al cambiar el nombre de un secreto al nombre de un elemento que ya existe
    def test_editar_secreto_duplicado(self):
        self.session.add(self.test_data[0][0])
        self.session.add(self.test_data[0][1])
        self.session.commit()

        error = self.validar_crear_editar(0, self.test_data[0][1])
        self.assertNotEqual("", error)

    # Prueba para verificar que al editar un secreto el cambio se refleja en el base de datos
    def test_editar_secreto_db(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        secreto = self.test_data[0][1]
        self.logica.editar_secreto(0, secreto.nombre, secreto.secreto, secreto.clave.nombre, secreto.nota)
        
        elementos = self.session.query(Elemento).all()
        self.assertEqual(1, len(elementos))
        self.assertEsperado(self.test_data[1][1], elementos[0])

    # Prueba para verificar que al borrar un secreto se ha borrado en el base de datos también
    def test_borrar_secreto_db(self):
        for idx in self.order:
            self.session.add(self.test_data[0][idx])
        self.session.commit()

        id_borrar = self.fake.random.randrange(len(self.order))

        self.logica.eliminar_elemento(id_borrar)

        piezas = list(range(len(self.order)))
        piezas.remove(id_borrar)

        elementos = sorted(self.session.query(Elemento).all(), key=lambda x:x.nombre)
        self.assertEqual(len(piezas), len(elementos))
        for i, j in enumerate(piezas):
            self.assertEsperado(self.test_data[1][j], elementos[i])
