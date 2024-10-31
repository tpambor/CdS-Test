#
# Pruebas unitarias para los elementos de identificación
#

import unittest
import os
from datetime import datetime, timedelta
from faker import Faker

# Usa base de datos en memoria para las pruebas
os.environ['CAJA_DB'] = 'sqlite://'  # noqa

from src.modelo.declarative_base import Session
from src.modelo import Elemento, Identificacion, ClaveFavorita
from src.logica.LogicaCaja import LogicaCaja
from src.logica.typing import TipoElemento

def gen_id(fake: Faker, vencimiento=None):
    id = Identificacion()
    id.nombre = fake.unique.name()
    id.nota = fake.text()
    id.numero = str(fake.random_number(digits=fake.random_int(3, 20), fix_len=True))
    id.nombre_completo = fake.name()
    id.nacimiento = fake.date_of_birth(minimum_age=18, maximum_age=70)
    id.expedicion = fake.date_between('-2y', 'now')
    id.vencimiento = fake.date_between('+4M', '+5y') if vencimiento == None else vencimiento
    id.caja_id = 1

    esperado: TipoElemento = {
        "nombre_elemento": id.nombre,
        "notas": id.nota,
        "tipo": "Identificación",
        "numero": id.numero,
        "nombre": id.nombre_completo,
        "fecha_nacimiento": id.nacimiento.isoformat(),
        "fecha_exp": id.expedicion.isoformat(),
        "fecha_venc": id.vencimiento.isoformat(),
    }

    return (id, esperado)

class IdentificacionTestCase(unittest.TestCase):
    def setUp(self):
        self.logica = LogicaCaja()
        self.session = Session()

        self.fake=Faker(["es-CO"])
        Faker.seed(1000)

        # test_data es ordenado segun el nombre de las IDs
        self.test_data = sorted([gen_id(self.fake) for _ in range(3)], key=lambda x:x[0].nombre)

        # De lista de tuplas a tupla de listas
        cl = list()
        el = list()
        for (c, e) in self.test_data:
            cl.append(c)
            el.append(e)
        self.test_data = (cl, el)

        # Agregar IDs al base de datos mezclado
        self.order = list(range(len(self.test_data[0])))
        while self.order == sorted(self.order):
            self.fake.random.shuffle(self.order)

    def tearDown(self):
        [self.session.delete(x) for x in self.session.query(Elemento).all()]
        self.session.commit()
        self.session.close()

    # Prueba para verificar que la logica retorna los elementos de identificación del base de datos
    def test_listar_id(self):
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
        
    # Función de ayuda para llamar a self.logica.validar_crear_editar_id con los datos de un objeto de tipo Identificación
    def validar_crear_editar(self, idx, id: Identificacion, vencimiento = None, expedicion = None, nacimiento = None):
        fvenc = id.vencimiento.isoformat() if vencimiento is None else vencimiento
        fexp = id.expedicion.isoformat() if expedicion is None else expedicion
        fnaci = id.nacimiento.isoformat() if nacimiento is None else nacimiento
        return self.logica.validar_crear_editar_id(idx,
            id.nombre, id.numero, id.nombre_completo, fnaci,
            fexp, fvenc,id.nota)

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

    # Prueba para verificar que se genera un error al crear un elemento con nota larga
    def test_nota_larga(self):
        self.test_data[0][0].nota = ''.join(self.fake.random_letters(513))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("notas".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con numero con caracteres no numericos
    def test_numero_no_numerico(self):
        self.test_data[0][0].numero = self.fake.word()

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("número".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con numero corto
    def test_numero_corto(self):
        self.test_data[0][0].numero = ''.join([str(self.fake.random_digit()) for _ in range(2)])

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("número".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con numero de 21 dígitos
    def test_numero_largo(self):
        self.test_data[0][0].numero = ''.join([str(self.fake.random_digit()) for _ in range(21)])

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("número".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con fecha de vencimiento
    def test_fecha_vencimiento(self):
        error = self.validar_crear_editar(-1, self.test_data[0][0], vencimiento=self.fake.date_object().ctime())
        self.assertIn("fecha de vencimiento".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con fecha de expedición
    def test_fecha_expedicion(self):
        error = self.validar_crear_editar(-1, self.test_data[0][0], expedicion=self.fake.date_object().ctime())
        self.assertIn("fecha de expedición".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con fecha de nacimiento
    def test_fecha_nacimiento(self):
        error = self.validar_crear_editar(-1, self.test_data[0][0], nacimiento=self.fake.date_object().ctime())
        self.assertIn("fecha de nacimiento".casefold(), error.casefold())

     # Prueba para verificar que no es posible generar dos elementos con el mismo nombre
    def test_agregar_con_mismo_nombre(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertNotEqual("", error)

    # Prueba para verificar que se genera un error al crear un elemento con nombre completo corto
    def test_nombre_completo_corto(self):
        self.test_data[0][0].nombre_completo = ''.join(self.fake.random_letters(2))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("nombre completo".casefold(), error.casefold())

     # Prueba para verificar que se genera un error al crear un elemento con nombre completo largo
    def test_nombre_completo_largo(self):
        self.test_data[0][0].nombre_completo = ''.join(self.fake.random_letters(256))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("nombre completo".casefold(), error.casefold())

    # Assert si elemento no contiene los datos esperados
    def assertEsperado(self, esperado: TipoElemento, elemento: Elemento):
        self.assertEqual(esperado["tipo"], elemento.tipo)
        self.assertEqual(esperado["nombre_elemento"], elemento.nombre)
        self.assertEqual(esperado["numero"], elemento.numero)
        self.assertEqual(esperado["nombre"], elemento.nombre_completo)
        self.assertEqual(esperado["fecha_nacimiento"], elemento.nacimiento.isoformat())
        self.assertEqual(esperado["fecha_exp"], elemento.expedicion.isoformat())
        self.assertEqual(esperado["fecha_venc"], elemento.vencimiento.isoformat())
        self.assertEqual(esperado["notas"], elemento.nota)

    # Prueba para verificar que al crear una ID se ha guardado en el base de datos
    def test_agregar_id_db(self):
        id = self.test_data[0][0]

        self.logica.crear_id(
             id.nombre, id.numero, id.nombre_completo, id.nacimiento.isoformat(),
            id.expedicion.isoformat(), id.vencimiento.isoformat(),id.nota)

        elementos = self.session.query(Elemento).all()
        self.assertEqual(1, len(elementos))
        self.assertEsperado(self.test_data[1][0], elementos[0])

    # Prueba para verificar que no hay error al cambiar una ID sin cambiar el nombre
    def test_editar_id_sin_cambiar_nombre(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        self.test_data[0][1].nombre = self.test_data[0][0].nombre

        error = self.validar_crear_editar(0, self.test_data[0][1])
        self.assertEqual("", error)

    # Prueba para verificar que se genera un error al cambiar el nombre de una ID al nombre de un elemento que ya existe
    def test_editar_id_duplicada(self):
        self.session.add(self.test_data[0][0])
        self.session.add(self.test_data[0][1])
        self.session.commit()

        error = self.validar_crear_editar(0, self.test_data[0][1])
        self.assertNotEqual("", error)

    # Prueba para verificar que al editar un ID el cambio se refleja en el base de datos
    def test_editar_id_db(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        self.logica.editar_id(0,
            self.test_data[0][1].nombre, self.test_data[0][1].numero, self.test_data[0][1].nombre_completo,
            self.test_data[0][1].nacimiento.isoformat(), self.test_data[0][1].expedicion.isoformat(), self.test_data[0][1].vencimiento.isoformat(),
            self.test_data[0][1].nota)

        elementos = self.session.query(Elemento).all()
        self.assertEqual(1, len(elementos))
        self.assertEsperado(self.test_data[1][1], elementos[0])

    # Prueba para verificar que al borrar un ID se ha borrado en el base de datos también
    def test_borrar_id_db(self):
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
