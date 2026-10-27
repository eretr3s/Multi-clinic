"""Abstracciones de almacenamiento (DIP) + implementación en memoria.

Los servicios dependen de las interfaces; cambiar a SQLite/PostgreSQL solo
requiere una nueva clase que las implemente (OCP).
"""
import threading
from abc import ABC, abstractmethod
from datetime import date, time
from typing import Optional

from medischedule.dominio.modelos import Cita, EstadoCita, Paciente


class RepositorioCitas(ABC):
    @abstractmethod
    def agregar(self, cita: Cita) -> Cita: ...

    @abstractmethod
    def obtener(self, cita_id: int) -> Optional[Cita]: ...

    @abstractmethod
    def guardar(self, cita: Cita) -> None: ...

    @abstractmethod
    def de_paciente(self, paciente_id: int) -> list[Cita]: ...

    @abstractmethod
    def confirmadas_en(self, fecha: date, hora: time) -> list[Cita]: ...

    @abstractmethod
    def confirmadas_de_medico(self, medico_id: str, fecha: date) -> list[Cita]: ...


class RepositorioPacientes(ABC):
    @abstractmethod
    def agregar(self, paciente: Paciente) -> Paciente: ...

    @abstractmethod
    def obtener(self, paciente_id: int) -> Optional[Paciente]: ...

    @abstractmethod
    def por_correo(self, correo: str) -> Optional[Paciente]: ...

    @abstractmethod
    def guardar(self, paciente: Paciente) -> None: ...


class RepositorioCitasMemoria(RepositorioCitas):
    def __init__(self):
        self._citas: dict[int, Cita] = {}
        self._siguiente = 1
        self._candado = threading.Lock()

    def agregar(self, cita: Cita) -> Cita:
        with self._candado:
            cita.id = self._siguiente
            self._siguiente += 1
            self._citas[cita.id] = cita
        return cita

    def obtener(self, cita_id: int) -> Optional[Cita]:
        return self._citas.get(cita_id)

    def guardar(self, cita: Cita) -> None:
        with self._candado:
            self._citas[cita.id] = cita

    def de_paciente(self, paciente_id: int) -> list[Cita]:
        return [c for c in list(self._citas.values()) if c.paciente_id == paciente_id]

    def confirmadas_en(self, fecha: date, hora: time) -> list[Cita]:
        return [c for c in list(self._citas.values()) if c.ocupa_horario(fecha, hora)]

    def confirmadas_de_medico(self, medico_id: str, fecha: date) -> list[Cita]:
        return [
            c
            for c in list(self._citas.values())
            if c.medico_id == medico_id
            and c.fecha == fecha
            and c.estado == EstadoCita.CONFIRMADA
        ]


class RepositorioPacientesMemoria(RepositorioPacientes):
    def __init__(self):
        self._pacientes: dict[int, Paciente] = {}
        self._siguiente = 1
        self._candado = threading.Lock()

    def agregar(self, paciente: Paciente) -> Paciente:
        with self._candado:
            paciente.id = self._siguiente
            self._siguiente += 1
            self._pacientes[paciente.id] = paciente
        return paciente

    def obtener(self, paciente_id: int) -> Optional[Paciente]:
        return self._pacientes.get(paciente_id)

    def por_correo(self, correo: str) -> Optional[Paciente]:
        correo = correo.strip().lower()
        for p in list(self._pacientes.values()):
            if p.correo == correo:
                return p
        return None

    def guardar(self, paciente: Paciente) -> None:
        with self._candado:
            self._pacientes[paciente.id] = paciente
