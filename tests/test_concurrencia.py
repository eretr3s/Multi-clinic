"""Concurrencia: muchos usuarios intentan el MISMO horario a la vez."""
import unittest
from concurrent.futures import ThreadPoolExecutor

from medischedule.dominio.excepciones import ConflictoHorario
from tests.base import HORA, MANANA, MEDICO, BaseServicios


class PruebasConcurrencia(BaseServicios):
    def _intentar(self, paciente_id, medico_id):
        try:
            self.servicios.citas.agendar(paciente_id, medico_id, MANANA, HORA)
            return "ok"
        except ConflictoHorario:
            return "conflicto"

    def test_solo_un_usuario_obtiene_el_mismo_horario(self):
        pacientes = [
            self.servicios.cuentas.registrar(f"P{i}", f"p{i}@mail.com", "", "secreto1")
            for i in range(30)
        ]
        with ThreadPoolExecutor(max_workers=30) as pool:
            resultados = list(pool.map(lambda p: self._intentar(p.id, MEDICO), pacientes))
        self.assertEqual(resultados.count("ok"), 1)
        self.assertEqual(resultados.count("conflicto"), 29)

    def test_mismo_paciente_no_reserva_dos_medicos_a_la_misma_hora(self):
        medicos = ["central-1", "central-2", "central-3"] * 5
        with ThreadPoolExecutor(max_workers=3) as pool:
            resultados = list(pool.map(lambda m: self._intentar(self.paciente.id, m), medicos))
        self.assertEqual(resultados.count("ok"), 1)


if __name__ == "__main__":
    unittest.main()
