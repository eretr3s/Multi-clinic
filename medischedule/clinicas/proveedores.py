"""Familia de productos del Factory: cada clínica es un ProveedorClinica.

Los servicios solo conocen la abstracción ProveedorClinica (DIP). Una clínica
nueva se agrega creando una subclase y registrándola en la fábrica (OCP).
"""
from abc import ABC, abstractmethod
from datetime import time

from medischedule.dominio.modelos import Clinica, Medico


class ProveedorClinica(ABC):
    @property
    @abstractmethod
    def clinica(self) -> Clinica: ...

    @abstractmethod
    def medicos(self) -> list[Medico]: ...

    @abstractmethod
    def horas_atencion(self) -> list[time]: ...


class _ProveedorEstatico(ProveedorClinica):
    """Base con datos fijos (en un sistema real vendrían de una API de la clínica)."""

    CLINICA: Clinica
    MEDICOS: tuple = ()
    HORAS: tuple = ()

    @property
    def clinica(self) -> Clinica:
        return self.CLINICA

    def medicos(self) -> list[Medico]:
        return list(self.MEDICOS)

    def horas_atencion(self) -> list[time]:
        return list(self.HORAS)


class ClinicaCentral(_ProveedorEstatico):
    CLINICA = Clinica("central", "Clínica Central", "Zona 1, Quetzaltenango")
    MEDICOS = (
        Medico("central-1", "Dra. Ana López", "Medicina General", "central"),
        Medico("central-2", "Dr. Luis Pérez", "Pediatría", "central"),
        Medico("central-3", "Dra. Marta Ruiz", "Cardiología", "central"),
    )
    HORAS = (time(8), time(9), time(10), time(11), time(14), time(15), time(16))


class ClinicaNorte(_ProveedorEstatico):
    CLINICA = Clinica("norte", "Clínica Norte", "Zona 3, Quetzaltenango")
    MEDICOS = (
        Medico("norte-1", "Dr. Erick Tribouillier", "Medicina General", "norte"),
        Medico("norte-2", "Dra. Sofía Castillo", "Dermatología", "norte"),
    )
    HORAS = (time(9), time(10), time(11), time(15), time(16), time(17))


class ClinicaSur(_ProveedorEstatico):
    CLINICA = Clinica("sur", "Clínica Sur", "Zona 7, Quetzaltenango")
    MEDICOS = (
        Medico("sur-1", "Dr. Jorge Díaz", "Pediatría", "sur"),
        Medico("sur-2", "Dra. Elena Morales", "Cardiología", "sur"),
    )
    HORAS = (time(8), time(9), time(10), time(13), time(14), time(15))
