"""Pruebas unitarias: componente anticolisión (casos límite)."""
import unittest
from datetime import date, time

from medischedule.agenda.anticolision import hay_colision
from medischedule.dominio.modelos import Cita, EstadoCita

F, H = date(2030, 1, 8), time(9, 0)


def cita(paciente=1, medico="m1", fecha=F, hora=H, estado=EstadoCita.CONFIRMADA):
    return Cita(paciente, medico, "c", fecha, hora, estado)


class PruebasAnticolision(unittest.TestCase):
    def test_sin_citas_no_hay_colision(self):
        self.assertFalse(hay_colision([], cita()))

    def test_mismo_medico_mismo_horario_colisiona(self):
        self.assertTrue(hay_colision([cita(paciente=2)], cita(paciente=1)))

    def test_medico_y_paciente_distintos_no_colisionan(self):
        self.assertFalse(hay_colision([cita(paciente=2, medico="m2")], cita(paciente=1)))

    def test_mismo_paciente_con_otro_medico_a_la_misma_hora_colisiona(self):
        self.assertTrue(hay_colision([cita(paciente=1, medico="m2")], cita(paciente=1, medico="m1")))

    def test_hora_contigua_no_colisiona(self):
        self.assertFalse(hay_colision([cita(hora=time(10, 0))], cita(hora=time(9, 0))))

    def test_otro_dia_no_colisiona(self):
        self.assertFalse(hay_colision([cita(fecha=date(2030, 1, 9))], cita()))

    def test_cita_cancelada_libera_el_horario(self):
        self.assertFalse(hay_colision([cita(paciente=2, estado=EstadoCita.CANCELADA)], cita()))

    def test_colision_detectada_aunque_no_sea_la_primera_de_la_lista(self):
        citas = [cita(medico="m9", paciente=9), cita(hora=time(11)), cita(paciente=2)]
        self.assertTrue(hay_colision(citas, cita(paciente=1)))


if __name__ == "__main__":
    unittest.main()

