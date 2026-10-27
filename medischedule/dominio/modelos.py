"""Entidades del dominio médico. Sin dependencias de otros componentes."""
from dataclasses import dataclass
from datetime import date, time
from enum import Enum
from typing import Optional


class EstadoCita(Enum):
    CONFIRMADA = "Confirmada"
    CANCELADA = "Cancelada"


@dataclass(frozen=True)
class Clinica:
    id: str
    nombre: str
    direccion: str


@dataclass(frozen=True)
class Medico:
    id: str
    nombre: str
    especialidad: str
    clinica_id: str


@dataclass
class Paciente:
    id: Optional[int]
    nombre: str
    correo: str
    telefono: str
    hash_clave: str


@dataclass
class Cita:
    paciente_id: int
    medico_id: str
    clinica_id: str
    fecha: date
    hora: time
    estado: EstadoCita = EstadoCita.CONFIRMADA
    id: Optional[int] = None

    def ocupa_horario(self, fecha: date, hora: time) -> bool:
        """True si esta cita está confirmada y ocupa exactamente ese horario."""
        return (
            self.estado == EstadoCita.CONFIRMADA
            and self.fecha == fecha
            and self.hora == hora
        )
