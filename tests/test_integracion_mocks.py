"""Pruebas de integración con Mocks: Factory + servicios + servicio externo simulado."""
import unittest
from datetime import date, time
from unittest.mock import Mock

from medischedule.clinicas.fabrica import FabricaClinicas
from medischedule.clinicas.proveedores import ClinicaCentral, ProveedorClinica
from medischedule.composicion import construir_servicios
from medischedule.dominio.excepciones import (
    ConflictoHorario, ErrorDominio, HorarioInvalido, NoEncontrado,
)
from medischedule.dominio.modelos import Clinica, EstadoCita, Medico
from tests.base import AHORA, HORA, MANANA, MEDICO, BaseServicios


class PruebasFactory(unittest.TestCase):
    def test_crea_la_clinica_correcta_como_abstraccion(self):
        p = FabricaClinicas().crear("central")
        self.assertIsInstance(p, ProveedorClinica)
        self.assertIsInstance(p, ClinicaCentral)

    def test_clave_desconocida_falla(self):
        with self.assertRaises(NoEncontrado):
            FabricaClinicas().crear("inexistente")

    def test_es_extensible_sin_modificar_codigo_existente(self):  # OCP
        class ClinicaMock(ProveedorClinica):
            clinica = Clinica("mock", "Clínica Mock", "N/A")

            def medicos(self):
                return [Medico("mock-1", "Dr. Mock", "Medicina General", "mock")]

            def horas_atencion(self):
                return [time(9)]

        fabrica = FabricaClinicas()
        fabrica.registrar("mock", ClinicaMock)
        s = construir_servicios(notificador=Mock(), reloj=lambda: AHORA, fabrica=fabrica)
        self.assertIn("mock", [c.id for c in s.catalogo.clinicas()])
        p = s.cuentas.registrar("X", "x@mail.com", "", "secreto1")
        self.assertEqual(s.citas.agendar(p.id, "mock-1", MANANA, time(9)).cita.clinica_id, "mock")


class PruebasServicioExternoSimulado(BaseServicios):
    def test_agendar_envia_notificacion_al_servicio_externo(self):
        r = self.servicios.citas.agendar(self.paciente.id, MEDICO, MANANA, HORA)
        self.assertTrue(r.notificado)
        self.notificador.enviar.assert_called_once()
        self.assertEqual(self.notificador.enviar.call_args.args[0], "uno@mail.com")

    def test_si_el_servicio_externo_falla_la_cita_se_conserva(self):  # Larsson: resiliencia
        self.notificador.enviar.side_effect = ConnectionError("sin conexión")
        r = self.servicios.citas.agendar(self.paciente.id, MEDICO, MANANA, HORA)
        self.assertFalse(r.notificado)
        self.assertEqual(self.servicios.citas.proxima(self.paciente.id).id, r.cita.id)

    def test_conflicto_no_envia_notificacion(self):
        self.servicios.citas.agendar(self.paciente.id, MEDICO, MANANA, HORA)
        self.notificador.reset_mock()
        with self.assertRaises(ConflictoHorario):
            self.servicios.citas.agendar(self.paciente2.id, MEDICO, MANANA, HORA)
        self.notificador.enviar.assert_not_called()


class PruebasFlujoServicios(BaseServicios):
    def test_horarios_muestran_ocupado_tras_reservar(self):
        self.servicios.citas.agendar(self.paciente.id, MEDICO, MANANA, HORA)
        estado = {h.hora: h.libre for h in self.servicios.citas.horarios(MEDICO, MANANA)}
        self.assertFalse(estado[HORA])
        self.assertTrue(estado[time(10)])

    def test_cancelar_libera_el_horario_para_otro_paciente(self):
        citas = self.servicios.citas
        cita = citas.agendar(self.paciente.id, MEDICO, MANANA, HORA).cita
        citas.cancelar(cita.id, self.paciente.id)
        self.assertEqual(cita.estado, EstadoCita.CANCELADA)
        self.assertNotEqual(citas.agendar(self.paciente2.id, MEDICO, MANANA, HORA).cita.id, cita.id)
        self.assertIn(cita, citas.historial(self.paciente.id))

    def test_no_se_puede_cancelar_cita_de_otro_paciente(self):
        cita = self.servicios.citas.agendar(self.paciente.id, MEDICO, MANANA, HORA).cita
        with self.assertRaises(NoEncontrado):
            self.servicios.citas.cancelar(cita.id, self.paciente2.id)

    def test_horarios_invalidos_son_rechazados(self):
        casos = [
            (date(2030, 1, 13), time(9)),  # domingo
            (date(2030, 1, 7), time(6)),   # fuera de horario / ya pasó
            (MANANA, time(12)),            # la clínica no atiende a esa hora
            (date(2030, 2, 1), time(9)),   # fuera de la ventana de días
        ]
        for fecha, hora in casos:
            with self.subTest(fecha=fecha, hora=hora), self.assertRaises(HorarioInvalido):
                self.servicios.citas.agendar(self.paciente.id, MEDICO, fecha, hora)

    def test_cuentas_registro_login_y_recuperacion(self):
        c = self.servicios.cuentas
        c.registrar("Ana", "ana@mail.com", "1", "secreto1")
        self.assertEqual(c.iniciar_sesion("ANA@mail.com", "secreto1").nombre, "Ana")
        with self.assertRaises(ErrorDominio):
            c.iniciar_sesion("ana@mail.com", "mala")
        with self.assertRaises(ErrorDominio):
            c.registrar("Ana", "ana@mail.com", "1", "secreto1")  # duplicado
        c.recuperar_clave("ana@mail.com")
        temporal = self.notificador.enviar.call_args.args[2].split(": ")[1]
        self.assertEqual(c.iniciar_sesion("ana@mail.com", temporal).correo, "ana@mail.com")


if __name__ == "__main__":
    unittest.main()
