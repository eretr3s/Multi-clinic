"""Servicio de citas: orquesta catálogo, repositorio, anticolisión y notificaciones.

Todas sus dependencias llegan por el constructor y son abstracciones (DIP).
"""
import logging
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Callable

from medischedule.agenda.anticolision import hay_colision
from medischedule.clinicas.catalogo import CatalogoClinicas
from medischedule.dominio.excepciones import (
    ConflictoHorario,
    ErrorDominio,
    HorarioInvalido,
    NoEncontrado,
)
from medischedule.dominio.modelos import Cita, EstadoCita
from medischedule.nucleo.gestor_sincronizacion import GestorSincronizacion
from medischedule.notificaciones import Notificador
from medischedule.persistencia.repositorios import RepositorioCitas, RepositorioPacientes

log = logging.getLogger("medischedule.citas")


@dataclass(frozen=True)
class Horario:
    hora: time
    libre: bool


@dataclass(frozen=True)
class ResultadoAgendamiento:
    cita: Cita
    notificado: bool  # False si el servicio externo falló (la cita sigue válida)


class ServicioCitas:
    def __init__(
        self,
        repo_citas: RepositorioCitas,
        repo_pacientes: RepositorioPacientes,
        catalogo: CatalogoClinicas,
        notificador: Notificador,
        gestor: GestorSincronizacion | None = None,
        reloj: Callable[[], datetime] = datetime.now,
        dias_visibles: int = 7,
    ):
        self._citas = repo_citas
        self._pacientes = repo_pacientes
        self._catalogo = catalogo
        self._notificador = notificador
        self._gestor = gestor or GestorSincronizacion()
        self._reloj = reloj
        self._dias = dias_visibles

    # ---------- Consulta de disponibilidad ----------
    def fechas_disponibles(self) -> list[date]:
        hoy = self._reloj().date()
        dias = (hoy + timedelta(days=i) for i in range(self._dias))
        return [d for d in dias if d.weekday() != 6]  # sin domingos

    def horarios(self, medico_id: str, fecha: date) -> list[Horario]:
        medico = self._catalogo.medico(medico_id)
        ocupadas = {c.hora for c in self._citas.confirmadas_de_medico(medico_id, fecha)}
        ahora = self._reloj()
        return [
            Horario(h, h not in ocupadas and datetime.combine(fecha, h) > ahora)
            for h in self._catalogo.horas(medico.clinica_id)
        ]

    # ---------- Agendar ----------
    def agendar(
        self, paciente_id: int, medico_id: str, fecha: date, hora: time
    ) -> ResultadoAgendamiento:
        medico = self._catalogo.medico(medico_id)
        self._validar_horario(medico.clinica_id, fecha, hora)
        nueva = Cita(paciente_id, medico_id, medico.clinica_id, fecha, hora)

        # Sección crítica: verificar + guardar debe ser atómico.
        with self._gestor.bloquear(f"medico:{medico_id}", f"paciente:{paciente_id}"):
            if hay_colision(self._citas.confirmadas_en(fecha, hora), nueva):
                raise ConflictoHorario(
                    "Ese horario ya fue reservado. Por favor elige otro."
                )
            cita = self._citas.agregar(nueva)

        return ResultadoAgendamiento(cita, self._notificar_confirmacion(cita))

    def _validar_horario(self, clinica_id: str, fecha: date, hora: time) -> None:
        if fecha not in self.fechas_disponibles():
            raise HorarioInvalido("La fecha no está disponible.")
        if hora not in self._catalogo.horas(clinica_id):
            raise HorarioInvalido("La clínica no atiende a esa hora.")
        if datetime.combine(fecha, hora) <= self._reloj():
            raise HorarioInvalido("Ese horario ya pasó.")

    def _notificar_confirmacion(self, cita: Cita) -> bool:
        """Resiliencia (Larsson): si falla el servicio externo, la cita NO se pierde."""
        paciente = self._pacientes.obtener(cita.paciente_id)
        try:
            self._notificador.enviar(
                paciente.correo,
                "Cita confirmada",
                f"Su cita del {cita.fecha} a las {cita.hora:%H:%M} está confirmada.",
            )
            return True
        except Exception:  # servicio externo caído, sin conexión, etc.
            log.exception("No se pudo enviar la notificación de la cita %s", cita.id)
            return False

    # ---------- Consultas del paciente ----------
    def obtener(self, cita_id: int, paciente_id: int) -> Cita:
        cita = self._citas.obtener(cita_id)
        if cita is None or cita.paciente_id != paciente_id:
            raise NoEncontrado("Cita no encontrada")
        return cita

    def _es_proxima(self, cita: Cita) -> bool:
        inicio = datetime.combine(cita.fecha, cita.hora)
        return cita.estado == EstadoCita.CONFIRMADA and inicio > self._reloj()

    def proximas(self, paciente_id: int) -> list[Cita]:
        citas = [c for c in self._citas.de_paciente(paciente_id) if self._es_proxima(c)]
        return sorted(citas, key=lambda c: (c.fecha, c.hora))

    def proxima(self, paciente_id: int) -> Cita | None:
        proximas = self.proximas(paciente_id)
        return proximas[0] if proximas else None

    def historial(self, paciente_id: int) -> list[Cita]:
        citas = [c for c in self._citas.de_paciente(paciente_id) if not self._es_proxima(c)]
        return sorted(citas, key=lambda c: (c.fecha, c.hora), reverse=True)

    # ---------- Cancelar ----------
    def cancelar(self, cita_id: int, paciente_id: int) -> Cita:
        cita = self.obtener(cita_id, paciente_id)
        with self._gestor.bloquear(f"medico:{cita.medico_id}"):
            if not self._es_proxima(cita):
                raise ErrorDominio("Solo se pueden cancelar citas próximas confirmadas.")
            cita.estado = EstadoCita.CANCELADA
            self._citas.guardar(cita)
        return cita
