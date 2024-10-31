#
# Pruebas unitarias para los elementos de login
#

import unittest
import os
from faker import Faker

# Usa base de datos en memoria para las pruebas
os.environ['CAJA_DB'] = 'sqlite://' # noqa


from src.modelo.declarative_base import Session
from src.modelo import Elemento, Login, ClaveFavorita
from src.logica.LogicaCaja import LogicaCaja
from src.logica.typing import TipoElemento
from test_ClaveFavorita import gen_clave

def gen_login(fake: Faker, clave: ClaveFavorita):
    login = Login()
    login.nombre = fake.unique.name()
    login.nota = fake.text()
    login.email = fake.email()
    login.usuario = fake.user_name()
    login.url = fake.url()
    login.clave = clave
    login.caja_id = 1

    esperado: TipoElemento = {
        "nombre_elemento": login.nombre,
        "notas": login.nota,
        "tipo": "Login",
        "email": login.email,
        "usuario": login.usuario,
        "url": login.url,
        "clave": login.clave.nombre
    }

    return (login, esperado)

class LoginTestCase(unittest.TestCase):
    def setUp(self):
        self.logica = LogicaCaja()
        self.session = Session()
        self.fake=Faker(["es-CO"])
        Faker.seed(1000)

        (self.clave,_) = gen_clave(self.fake)
        self.session.add(self.clave)
        self.session.commit()

        # test_data es ordenado segun el nombre de las claves
        self.test_data = sorted([gen_login(self.fake, self.clave) for _ in range(3)], key=lambda x:x[0].nombre)

        # De lista de tuplas a tupla de listas
        cl = list()
        el = list()
        for (c, e) in self.test_data:
            cl.append(c)
            el.append(e)
        self.test_data = (cl, el)

        # Agregar logins al base de datos mezclado
        self.order = list(range(len(self.test_data[0])))
        while self.order == sorted(self.order):
            self.fake.random.shuffle(self.order)

    def tearDown(self):
        [self.session.delete(x) for x in self.session.query(Elemento).all()]
        [self.session.delete(x) for x in self.session.query(ClaveFavorita).all()]
        self.session.commit()
        self.session.close()

    # Prueba para verificar que la logica retorna los elementos de login del base de datos
    def test_listar_login(self):
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

  # Función de ayuda para llamar a self.logica.validar_crear_editar_login con los datos de un objeto de tipo Login
    def validar_crear_editar(self, idx, login: Login):
        nombre_clave = "" if login.clave is None else login.clave.nombre
        return self.logica.validar_crear_editar_login(idx,
            login.nombre, login.email, login.usuario,
            nombre_clave, login.url,  login.nota)

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

    # Prueba para verificar que se genera un error al crear un elemento con usuario vacio
    def test_usuario_vacio(self):
        self.test_data[0][0].usuario = ""

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("usuario".casefold(), error.casefold())

     # Prueba para verificar que se genera un error al crear un elemento con un usuario de 256 caracteres
    def test_usuario_largo(self):
        self.test_data[0][0].usuario = ''.join(self.fake.random_letters(256))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("usuario".casefold(), error.casefold())

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

    # Prueba para verificar que se genera un error al crear un elemento con email inválido
    def test_email_invalido(self):
        self.test_data[0][0].email = self.fake.user_name() + "#" + self.fake.domain_name()

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("email".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con URL larga
    def test_url_larga(self):
        self.test_data[0][0].url = ''.join(self.fake.random_letters(513))

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("url".casefold(), error.casefold())

    # Prueba para verificar que se genera un error al crear un elemento con URL inválida
    def test_url_invalida(self):
        self.test_data[0][0].url = self.fake.domain_word() + "," + self.fake.tld()

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("url".casefold(), error.casefold())

    # Prueba para verificar que no es posible generar dos elementos con el mismo nombre
    def test_agregar_con_mismo_nombre(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertNotEqual("", error)

    # Prueba para verificar que se genera un error al crear un elemento sin clave favorita
    def test_sin_clave(self):
        self.test_data[0][0].clave = None

        error = self.validar_crear_editar(-1, self.test_data[0][0])
        self.assertIn("clave".casefold(), error.casefold())

    # Assert si elemento no contiene los datos esperados
    def assertEsperado(self, esperado: TipoElemento, elemento: Elemento):
        self.assertEqual(esperado["tipo"], elemento.tipo)
        self.assertEqual(esperado["nombre_elemento"], elemento.nombre)
        self.assertEqual(esperado["email"], elemento.email)
        self.assertEqual(esperado["usuario"], elemento.usuario)
        self.assertEqual(esperado["clave"], elemento.clave.nombre)
        self.assertEqual(esperado["url"], elemento.url)
        self.assertEqual(esperado["notas"], elemento.nota)

    # Prueba para verificar que al crear un login se ha guardado en el base de datos
    def test_agregar_login_db(self):
        login = self.test_data[0][0]

        self.logica.crear_login(
            login.nombre, login.email, login.usuario,
            login.clave.nombre, login.url,  login.nota)

        elementos = self.session.query(Elemento).all()
        self.assertEqual(1, len(elementos))
        self.assertEsperado(self.test_data[1][0], elementos[0])

    # Prueba para verificar que no hay error al cambiar un login sin cambiar el nombre
    def test_editar_login_sin_cambiar_nombre(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        self.test_data[0][1].nombre = self.test_data[0][0].nombre

        error = self.validar_crear_editar(0, self.test_data[0][1])
        self.assertEqual("", error)

    # Prueba para verificar que se genera un error al cambiar el nombre de un login al nombre de un elemento que ya existe
    def test_editar_login_duplicada(self):
        self.session.add(self.test_data[0][0])
        self.session.add(self.test_data[0][1])
        self.session.commit()

        error = self.validar_crear_editar(0, self.test_data[0][1])
        self.assertNotEqual("", error)

    # Prueba para verificar que al editar un ID el cambio se refleja en el base de datos
    def test_editar_login_db(self):
        self.session.add(self.test_data[0][0])
        self.session.commit()

        self.logica.editar_login(0, self.test_data[0][1].nombre, self.test_data[0][1].email, self.test_data[0][1].usuario,
                              self.test_data[0][1].clave.nombre, self.test_data[0][1].url,
                              self.test_data[0][1].nota)

        elementos = self.session.query(Elemento).all()
        self.assertEqual(1, len(elementos))
        self.assertEsperado(self.test_data[1][1], elementos[0])

    # Prueba para verificar que al borrar un login se ha borrado en el base de datos también
    def test_borrar_login_db(self):
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
