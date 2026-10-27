"""Utilidades comunes de prueba (reloj fijo => resultados deterministas)."""
import unittest
from datetime import date, datetime, time
from unittest.mock import Mock

from medischedule.composicion import construir_servicios
from medischedule.notificaciones import Notificador

AHORA = datetime(2030, 1, 7, 7, 0)  # lunes 07:00
MANANA = date(2030, 1, 8)  # martes
HORA = time(9, 0)
MEDICO = "central-1"


class BaseServicios(unittest.TestCase):
    """Cada prueba recibe servicios nuevos, un notificador simulado y dos pacientes."""

    def setUp(self):
        self.notificador = Mock(spec=Notificador)
        self.servicios = construir_servicios(notificador=self.notificador, reloj=lambda: AHORA)
        self.paciente = self.servicios.cuentas.registrar("Paciente Uno", "uno@mail.com", "1", "secreto1")
        self.paciente2 = self.servicios.cuentas.registrar("Paciente Dos", "dos@mail.com", "2", "secreto2")
