"""Servicio externo simulado: notificaciones por correo/SMS."""
import logging
from abc import ABC, abstractmethod

log = logging.getLogger("medischedule.notificaciones")


class Notificador(ABC):
    @abstractmethod
    def enviar(self, correo: str, asunto: str, mensaje: str) -> None:
        """Debe lanzar una excepción si el servicio externo falla."""


class NotificadorConsola(Notificador):
    """Implementación de demo: imprime el mensaje en la consola del servidor."""

    def enviar(self, correo: str, asunto: str, mensaje: str) -> None:
        log.warning("[CORREO a %s] %s | %s", correo, asunto, mensaje)
