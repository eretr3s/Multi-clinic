"""Registro, inicio de sesión, recuperación de contraseña y perfil."""
import logging
import secrets

from medischedule.cuentas import seguridad
from medischedule.dominio.excepciones import (
    CorreoYaRegistrado,
    CredencialesInvalidas,
    DatosInvalidos,
    NoEncontrado,
)
from medischedule.dominio.modelos import Paciente
from medischedule.notificaciones import Notificador
from medischedule.persistencia.repositorios import RepositorioPacientes

log = logging.getLogger("medischedule.cuentas")


class ServicioCuentas:
    def __init__(self, repo: RepositorioPacientes, notificador: Notificador):
        self._repo = repo
        self._notificador = notificador

    def registrar(self, nombre: str, correo: str, telefono: str, clave: str) -> Paciente:
        nombre, correo, telefono = nombre.strip(), correo.strip().lower(), telefono.strip()
        if not nombre:
            raise DatosInvalidos("El nombre es obligatorio.")
        if "@" not in correo:
            raise DatosInvalidos("Correo inválido.")
        if len(clave) < 6:
            raise DatosInvalidos("La contraseña debe tener al menos 6 caracteres.")
        if self._repo.por_correo(correo):
            raise CorreoYaRegistrado("Ya existe una cuenta con ese correo.")
        return self._repo.agregar(
            Paciente(None, nombre, correo, telefono, seguridad.hashear(clave))
        )

    def iniciar_sesion(self, correo: str, clave: str) -> Paciente:
        paciente = self._repo.por_correo(correo)
        if paciente is None or not seguridad.verificar(clave, paciente.hash_clave):
            raise CredencialesInvalidas("Correo o contraseña incorrectos.")
        return paciente

    def recuperar_clave(self, correo: str) -> None:
        """Genera una clave temporal y la 'envía'. No revela si el correo existe."""
        paciente = self._repo.por_correo(correo)
        if paciente is None:
            return
        temporal = secrets.token_urlsafe(6)
        paciente.hash_clave = seguridad.hashear(temporal)
        self._repo.guardar(paciente)
        try:
            self._notificador.enviar(
                paciente.correo, "Recuperación de contraseña", f"Contraseña temporal: {temporal}"
            )
        except Exception:
            log.exception("No se pudo enviar el correo de recuperación")

    def obtener(self, paciente_id: int) -> Paciente:
        paciente = self._repo.obtener(paciente_id)
        if paciente is None:
            raise NoEncontrado("Paciente no encontrado")
        return paciente

    def actualizar_perfil(self, paciente_id: int, nombre: str, telefono: str) -> Paciente:
        if not nombre.strip():
            raise DatosInvalidos("El nombre es obligatorio.")
        paciente = self.obtener(paciente_id)
        paciente.nombre, paciente.telefono = nombre.strip(), telefono.strip()
        self._repo.guardar(paciente)
        return paciente
