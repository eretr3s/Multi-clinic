"""Lógica anticolisión (función aislada y pura para poder medir su V(G)).

Una nueva cita colisiona si, en el mismo día y hora, ya existe una cita
confirmada del MISMO médico o del MISMO paciente.

Grafo de Flujo de Control (nodos):
  N1  for cita in citas        (decisión)
  N2  if not ocupa_horario     (decisión)
  N3  if mismo médico          (decisión)
  N4  return True              (colisión de médico)
  N5  if mismo paciente        (decisión)
  N6  return True              (colisión de paciente)
  N7  return False             (sin colisión)
  N8  salida

Aristas (11): N1→N2, N1→N7, N2→N1, N2→N3, N3→N4, N3→N5, N5→N6, N5→N1,
              N4→N8, N6→N8, N7→N8

Complejidad ciclomática:
  V(G) = E - N + 2P = 11 - 8 + 2(1) = 5
  V(G) = Predicados + 1 = 4 + 1 = 5      (límite exigido: ≤ 8)
"""
from typing import Iterable

from medischedule.dominio.modelos import Cita


def hay_colision(citas: Iterable[Cita], nueva: Cita) -> bool:
    for cita in citas:
        if not cita.ocupa_horario(nueva.fecha, nueva.hora):
            continue
        if cita.medico_id == nueva.medico_id:
            return True
        if cita.paciente_id == nueva.paciente_id:
            return True
    return False
