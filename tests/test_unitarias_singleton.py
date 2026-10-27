"""Pruebas unitarias: Singleton."""
import unittest
from concurrent.futures import ThreadPoolExecutor

from medischedule.nucleo.gestor_sincronizacion import GestorSincronizacion


class PruebasSingleton(unittest.TestCase):
    def test_devuelve_siempre_la_misma_instancia(self):
        self.assertIs(GestorSincronizacion(), GestorSincronizacion())

    def test_es_unico_incluso_con_hilos_simultaneos(self):
        GestorSincronizacion.reiniciar()
        with ThreadPoolExecutor(max_workers=16) as pool:
            instancias = list(pool.map(lambda _: GestorSincronizacion(), range(200)))
        self.assertEqual(len({id(i) for i in instancias}), 1)

    def test_mismo_candado_para_la_misma_clave(self):
        g = GestorSincronizacion()
        self.assertIs(g._candado_de("medico:x"), g._candado_de("medico:x"))
        self.assertIsNot(g._candado_de("medico:x"), g._candado_de("medico:y"))

    def test_bloquear_libera_los_candados_al_salir(self):
        g = GestorSincronizacion()
        with g.bloquear("medico:a", "paciente:1"):
            pass
        candado = g._candado_de("medico:a")
        self.assertTrue(candado.acquire(blocking=False))
        candado.release()


if __name__ == "__main__":
    unittest.main()
