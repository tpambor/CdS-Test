#
# Pruebas unitarias para los elementos de tarjeta
#

import unittest
import os
from datetime import datetime, timedelta
from faker import Faker

# Usa base de datos en memoria para las pruebas
os.environ['CAJA_DB'] = 'sqlite://' # noqa

from src.modelo.declarative_base import Session
from src.modelo import Elemento, Tarjeta, ClaveFavorita
from src.logica.LogicaCaja import LogicaCaja
from src.logica.typing import TipoElemento
from test_ClaveFavorita import gen_clave

def gen_tarjeta(fake: Faker, clave: ClaveFavorita, vencimiento=None):
    name = fake.unique.name()
    tarjeta = Tarjeta()
    tarjeta.nombre = f"{name} {fake.credit_card_provider()}"
    tarjeta.nota = fake.text()
    tarjeta.numero = fake.credit_card_number()
    tarjeta.titular = name.upper()
    tarjeta.codigo_seguridad = fake.credit_card_security_code()
    tarjeta.direccion = fake.address()
    tarjeta.telefono = fake.phone_number()
    tarjeta.vencimiento = fake.date_between('+4M', '+5y') if vencimiento == None else vencimiento
    tarjeta.clave = clave
    tarjeta.caja_id = 1

    esperado: TipoElemento = {
        "nombre_elemento": tarjeta.nombre,
        "notas": tarjeta.nota,
        "tipo": "Tarjeta",
        "numero": tarjeta.numero,
        "titular": tarjeta.titular,
        "ccv": tarjeta.codigo_seguridad,
        "direccion": tarjeta.direccion,
        "telefono": tarjeta.telefono,
        "fecha_venc": tarjeta.vencimiento.isoformat(),
        "clave": tarjeta.clave.nombre
    }

    return (tarjeta, esperado)

class TarjetaTestCase(unittest.TestCase):
    def setUp(self):
        self.logica = LogicaCaja()
        self.session = Session()
        self.fake = Faker(["es-CO"])
        Faker.seed(1000)

        (self.clave, _) = gen_clave(self.fake)

        self.session.add(self.clave)
        self.session.commit()

        # test_data es ordenado segun el nombre de las tarjetas
        self.test_data = sorted([gen_tarjeta(self.fake, self.clave) for _ in range(3)], key=lambda x:x[0].nombre)

        # De lista de tuplas a tupla de listas
        cl = list()
        el = list()
        for (c, e) in self.test_data:
            cl.append(c)
            el.append(e)
        self.test_data = (cl, el)

        # Agregar tarjetas al base de datos mezclado
        self.order = list(range(len(self.test_data[0])))
        while self.order == sorted(self.order):
            self.fake.random.shuffle(self.order)

    def tearDown(self):
        [self.session.delete(x) for x in self.session.query(Elemento).all()]
        [self.session.delete(x) for x in self.session.query(ClaveFavorita).all()]
        self.session.commit()
        self.session.close()

    # Prueba para verificar que la logica retorna los elementos de tarjeta del base de datos
    def test_listar_tarjeta(self):
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

    # Función de ayuda para llamar a self.logica.validar_crear_editar_tarjeta con los datos de un objeto de tipo Tarjeta
    # Los parámetros opcionales se pueden utilizar para inyectar errores
    def validar_crear_editar(self, id, tarjeta: Tarjeta, vencimiento=None):
        fvenc = tarjeta.vencimiento.isoformat() if vencimiento is None else vencimiento
        nombre_clave = "" if tarjeta.clave is None else tarjeta.clave.nombre

        return self.logica.validar_crear_editar_tarjeta(id,
            tarjeta.nombre, tarjeta.numero, tarjeta.titular,
            fvenc, tarjeta.codigo_seguridad, nombre_clave,
            tarjeta.direccion, tarjeta.telefono, tarjeta.nota)

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

    # Prueba para verificar que se genera un error al crear un elemento con titular corto
    def test_titular_corto(self):
        self.test_data[0][0].titular = ''.join(self.fake.random_letters(2))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("titular".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con titular de 256 caracteres
    def test_titular_largo(self):
        self.test_data[0][0].titular = ''.join(self.fake.random_letters(256))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("titular".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con titular con minúsculas
    def test_titular_mal_formado(self):
        self.test_data[0][0].titular = self.test_data[0][0].titular.lower()

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("titular".casefold(), error.casefold())

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

    # Prueba para verificar que se genera un error al crear un elemento con numero de 256 dígitos
    def test_numero_largo(self):
        self.test_data[0][0].numero = ''.join([str(self.fake.random_digit()) for _ in range(256)])

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("número".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con CCV con caracteres no numericos
    def test_ccv_no_numerico(self):
        self.test_data[0][0].codigo_seguridad = self.fake.word()

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("CCV".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con CCV corto
    def test_ccv_corto(self):
        self.test_data[0][0].codigo_seguridad = ''.join([str(self.fake.random_digit()) for _ in range(2)])

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("CCV".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con CCV de 5 dígitos
    def test_ccv_largo(self):
        self.test_data[0][0].codigo_seguridad = ''.join([str(self.fake.random_digit()) for _ in range(5)])

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("CCV".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con fecha mal formada
    def test_fecha_mal_formada(self):
        error = self.validar_crear_editar(-1, self.test_data[0][0], vencimiento=self.fake.date_object().ctime())
        self.assertIn("fecha de vencimiento".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con telefono corto
    def test_telefono_corto(self):
        self.test_data[0][0].telefono = ''.join([str(self.fake.random_digit()) for _ in range(2)])

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("teléfono".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con telefono de 256 caracteres
    def test_telefono_largo(self):
        self.test_data[0][0].telefono = ''.join([str(self.fake.random_digit()) for _ in range(256)])

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("teléfono".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con telefono mal formado
    def test_telefono_mal_formado(self):
        self.test_data[0][0].telefono = self.fake.country_calling_code() + self.fake.country_calling_code() + self.fake.msisdn()

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("teléfono".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con dirección corta
    def test_direccion_corta(self):
        self.test_data[0][0].direccion = ''.join(self.fake.random_letters(2))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("dirección".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con dirección de 256 caracteres
    def test_direccion_largo(self):
        self.test_data[0][0].direccion = ''.join(self.fake.random_letters(256))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("dirección".casefold(), error.casefold())

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
        self.assertEqual(esperado["numero"], elemento.numero)
        self.assertEqual(esperado["titular"], elemento.titular)
        self.assertEqual(esperado["fecha_venc"], elemento.vencimiento.isoformat())
        self.assertEqual(esperado["ccv"], elemento.codigo_seguridad)
        self.assertEqual(esperado["clave"], elemento.clave.nombre)
        self.assertEqual(esperado["direccion"], elemento.direccion)
        self.assertEqual(esperado["telefono"], elemento.telefono)
        self.assertEqual(esperado["notas"], elemento.nota)

    # Prueba para verificar que al crear una tarjeta se ha guardado en el base de datos
    def test_agregar_tarjeta_db(self):
        tarjeta = self.test_data[0][0]

        self.logica.crear_tarjeta(
            tarjeta.nombre, tarjeta.numero, tarjeta.titular, tarjeta.vencimiento.isoformat(),
            tarjeta.codigo_seguridad, tarjeta.clave.nombre, tarjeta.direccion, tarjeta.telefono, tarjeta.nota)

        elementos = self.session.query(Elemento).all()
        self.assertEqual(1, len(elementos))
        self.assertEsperado(self.test_data[1][0], elementos[0])

    # Prueba para verificar que no hay error al cambiar una tarjeta sin cambiar el nombre
    def test_editar_tarjeta_sin_cambiar_nombre(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        self.test_data[0][1].nombre = self.test_data[0][0].nombre

        error = self.validar_crear_editar(0, self.test_data[0][1])
        self.assertEqual("", error)

    # Prueba para verificar que se genera un error al cambiar el nombre de una tarjeta al nombre de un elemento que ya existe
    def test_editar_tarjeta_duplicada(self):
        self.session.add(self.test_data[0][0])
        self.session.add(self.test_data[0][1])
        self.session.commit()

        error = self.validar_crear_editar(0, self.test_data[0][1])
        self.assertNotEqual("", error)

    # Prueba para verificar que al editar una tarjeta el cambio se refleja en el base de datos
    def test_editar_tarjeta_db(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        self.logica.editar_tarjeta(0,
            self.test_data[0][1].nombre, self.test_data[0][1].numero, self.test_data[0][1].titular, self.test_data[0][1].vencimiento.isoformat(),
            self.test_data[0][1].codigo_seguridad, self.test_data[0][1].clave.nombre, self.test_data[0][1].direccion, self.test_data[0][1].telefono, self.test_data[0][1].nota)

        elementos = self.session.query(Elemento).all()
        self.assertEqual(1, len(elementos))
        self.assertEsperado(self.test_data[1][1], elementos[0])

    # Prueba para verificar que al borrar una tarjeta se ha borrado en el base de datos también
    def test_borrar_tarjeta_db(self):
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
