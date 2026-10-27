"""Catálogo de consulta (clínicas, especialidades, médicos). Solo lectura."""
from datetime import time

from medischedule.clinicas.proveedores import ProveedorClinica
from medischedule.dominio.excepciones import NoEncontrado
from medischedule.dominio.modelos import Clinica, Medico


class CatalogoClinicas:
    def __init__(self, proveedores: list[ProveedorClinica]):
        self._proveedores = {p.clinica.id: p for p in proveedores}

    def _proveedor(self, clinica_id: str) -> ProveedorClinica:
        try:
            return self._proveedores[clinica_id]
        except KeyError:
            raise NoEncontrado("Clínica no encontrada") from None

    def clinicas(self) -> list[Clinica]:
        return [p.clinica for p in self._proveedores.values()]

    def clinica(self, clinica_id: str) -> Clinica:
        return self._proveedor(clinica_id).clinica

    def especialidades(self, clinica_id: str) -> list[str]:
        return sorted({m.especialidad for m in self._proveedor(clinica_id).medicos()})

    def medicos(self, clinica_id: str, especialidad: str | None = None) -> list[Medico]:
        medicos = self._proveedor(clinica_id).medicos()
        if especialidad:
            medicos = [m for m in medicos if m.especialidad == especialidad]
        return medicos

    def medico(self, medico_id: str) -> Medico:
        for proveedor in self._proveedores.values():
            for m in proveedor.medicos():
                if m.id == medico_id:
                    return m
        raise NoEncontrado("Médico no encontrado")

    def horas(self, clinica_id: str) -> list[time]:
        return self._proveedor(clinica_id).horas_atencion()
