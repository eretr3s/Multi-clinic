"""PATRÓN SINGLETON.

¿Por qué aquí? La integridad del calendario depende de que TODOS los hilos
(peticiones simultáneas) usen los mismos candados. Si cada servicio creara su
propio gestor, dos usuarios podrían reservar el mismo horario a la vez.
Por eso existe una única instancia con acceso global.

Eficiencia (Larsson): se usa un candado por médico/paciente, no uno global,
así reservas de médicos distintos no se bloquean entre sí.
"""
import threading
from contextlib import ExitStack, contextmanager


class GestorSincronizacion:
    _instancia = None
    _candado_creacion = threading.Lock()

    def __new__(cls):
        # Double-checked locking: seguro aunque dos hilos lo pidan a la vez.
        if cls._instancia is None:
            with cls._candado_creacion:
                if cls._instancia is None:
                    instancia = super().__new__(cls)
                    instancia._candados = {}
                    instancia._candado_mapa = threading.Lock()
                    cls._instancia = instancia
        return cls._instancia

    def _candado_de(self, clave: str) -> threading.Lock:
        with self._candado_mapa:
            return self._candados.setdefault(clave, threading.Lock())

    @contextmanager
    def bloquear(self, *claves: str):
        """Toma varios candados en orden fijo (evita interbloqueos)."""
        with ExitStack() as pila:
            for clave in sorted(set(claves)):
                pila.enter_context(self._candado_de(clave))
            yield

    @classmethod
    def reiniciar(cls) -> None:
        """Solo para pruebas: descarta la instancia única."""
        with cls._candado_creacion:
            cls._instancia = None
