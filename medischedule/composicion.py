"""Raíz de composición: único lugar que conoce las clases concretas y las conecta."""
from dataclasses import dataclass
from datetime import datetime
from typing import Callable

from medischedule.agenda.servicio_citas import ServicioCitas
from medischedule.clinicas.catalogo import CatalogoClinicas
from medischedule.clinicas.fabrica import FabricaClinicas
from medischedule.cuentas.servicio_cuentas import ServicioCuentas
from medischedule.nucleo.gestor_sincronizacion import GestorSincronizacion
from medischedule.notificaciones import Notificador, NotificadorConsola
from medischedule.persistencia.repositorios import (
    RepositorioCitasMemoria,
    RepositorioPacientesMemoria,
)


@dataclass
class Servicios:
    cuentas: ServicioCuentas
    citas: ServicioCitas
    catalogo: CatalogoClinicas


def construir_servicios(
    notificador: Notificador | None = None,
    reloj: Callable[[], datetime] = datetime.now,
    fabrica: FabricaClinicas | None = None,
) -> Servicios:
    fabrica = fabrica or FabricaClinicas()
    catalogo = CatalogoClinicas([fabrica.crear(k) for k in fabrica.claves()])
    notificador = notificador or NotificadorConsola()
    repo_citas, repo_pacientes = RepositorioCitasMemoria(), RepositorioPacientesMemoria()
    return Servicios(
        cuentas=ServicioCuentas(repo_pacientes, notificador),
        citas=ServicioCitas(
            repo_citas, repo_pacientes, catalogo, notificador, GestorSincronizacion(), reloj
        ),
        catalogo=catalogo,
    )
