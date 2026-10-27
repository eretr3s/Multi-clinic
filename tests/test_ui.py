"""Pruebas de UI automatizadas (caja negra): simulan lo que hace el usuario en pantalla.

Solo interactúan por HTTP/HTML (formularios, enlaces, botones), igual que un
navegador, y verifican lo que el usuario VE.
"""
import unittest
from unittest.mock import Mock

from medischedule.composicion import construir_servicios
from medischedule.web.app import crear_app
from tests.base import AHORA, MANANA


class PruebasUI(unittest.TestCase):
    def setUp(self):
        self.app = crear_app(construir_servicios(notificador=Mock(), reloj=lambda: AHORA))
        self.app.config["TESTING"] = True

    def nuevo_usuario(self, nombre, correo):
        c = self.app.test_client()
        c.post("/registro", data={"nombre": nombre, "correo": correo, "telefono": "1", "clave": "secreto1"})
        r = c.post("/login", data={"correo": correo, "clave": "secreto1"}, follow_redirects=True)
        self.assertIn("Hola, " + nombre, r.text)
        return c

    def test_pantallas_protegidas_redirigen_al_login(self):
        r = self.app.test_client().get("/mis-citas")
        self.assertEqual(r.status_code, 302)
        self.assertIn("/login", r.headers["Location"])

    def test_login_incorrecto_muestra_error(self):
        r = self.app.test_client().post("/login", data={"correo": "x@x.com", "clave": "mala"})
        self.assertIn("Correo o contraseña incorrectos", r.text)

    def test_flujo_completo_agendar_ver_y_cancelar(self):
        c = self.nuevo_usuario("Ana", "ana@mail.com")

        r = c.get("/agendar?clinica=central&especialidad=Medicina+General")
        self.assertIn("Dra. Ana López", r.text)

        r = c.get(f"/calendario/central-1?fecha={MANANA.isoformat()}")
        self.assertIn("09:00", r.text)

        r = c.post("/confirmar", follow_redirects=True,
                   data={"medico_id": "central-1", "fecha": MANANA.isoformat(), "hora": "09:00"})
        self.assertIn("¡Cita confirmada!", r.text)

        self.assertIn("Dra. Ana López", c.get("/mis-citas").text)
        self.assertIn("Próxima cita", c.get("/").text)

        r = c.post("/citas/1/cancelar", follow_redirects=True)
        self.assertIn("Cita cancelada", r.text)
        self.assertIn("Cancelada", c.get("/mis-citas").text)

    def test_conflicto_de_agenda_muestra_error_al_segundo_usuario(self):
        ana = self.nuevo_usuario("Ana", "ana@mail.com")
        beto = self.nuevo_usuario("Beto", "beto@mail.com")
        datos = {"medico_id": "central-1", "fecha": MANANA.isoformat(), "hora": "09:00"}
        url = f"/calendario/central-1?fecha={MANANA.isoformat()}"

        # Beto ve el horario libre mientras Ana todavía no reserva...
        self.assertIn('value="09:00"', beto.get(url).text)
        # ...Ana reserva primero...
        self.assertIn("¡Cita confirmada!", ana.post("/confirmar", data=datos, follow_redirects=True).text)
        # ...y Beto intenta el mismo horario con su pantalla ya desactualizada.
        r = beto.post("/confirmar", data=datos)
        self.assertEqual(r.status_code, 409)
        self.assertIn("No se pudo agendar", r.text)
        self.assertIn("ya fue reservado", r.text)

        # El calendario ahora muestra el horario como ocupado y no permite elegirlo.
        pagina = beto.get(url).text
        self.assertNotIn('value="09:00"', pagina)
        self.assertIn("Ocupado", pagina)

    def test_perfil_modificar_datos(self):
        c = self.nuevo_usuario("Ana", "ana@mail.com")
        r = c.post("/perfil", data={"nombre": "Ana María", "telefono": "9999"}, follow_redirects=True)
        self.assertIn("Datos actualizados", r.text)
        self.assertIn("Ana María", r.text)

    def test_cerrar_sesion(self):
        c = self.nuevo_usuario("Ana", "ana@mail.com")
        c.get("/logout")
        self.assertEqual(c.get("/").status_code, 302)


if __name__ == "__main__":
    unittest.main()
