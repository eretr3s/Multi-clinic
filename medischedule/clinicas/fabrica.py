"""PATRÓN FACTORY METHOD.

¿Por qué aquí? Cada clínica expone médicos y horarios de forma distinta. La
fábrica crea el proveedor correcto a partir de una clave ("central", "norte"...)
y devuelve siempre la abstracción ProveedorClinica, así el resto del sistema
no conoce las clases concretas (bajo acoplamiento).

Abierta a extensión: `registrar()` añade clínicas sin modificar el código existente.
"""
from medischedule.clinicas.proveedores import (
    ClinicaCentral,
    ClinicaNorte,
    ClinicaSur,
    ProveedorClinica,
)
from medischedule.dominio.excepciones import NoEncontrado


class FabricaClinicas:
    def __init__(self, registro: dict[str, type] | None = None):
        self._registro: dict[str, type] = dict(
            registro
            or {"central": ClinicaCentral, "norte": ClinicaNorte, "sur": ClinicaSur}
        )

    def registrar(self, clave: str, tipo: type) -> None:
        self._registro[clave] = tipo

    def claves(self) -> list[str]:
        return list(self._registro)

    def crear(self, clave: str) -> ProveedorClinica:
        try:
            return self._registro[clave]()
        except KeyError:
            raise NoEncontrado(f"Clínica desconocida: {clave}") from None
