"""Errores de negocio. La capa web los traduce a mensajes para el usuario."""


class ErrorDominio(Exception):
    """Base de todos los errores esperados del negocio."""


class ConflictoHorario(ErrorDominio):
    """El horario ya fue tomado (por otro usuario o por el mismo paciente)."""


class HorarioInvalido(ErrorDominio):
    """Fecha u hora fuera de lo ofrecido por la clínica o ya pasada."""


class DatosInvalidos(ErrorDominio):
    """Datos de formulario incorrectos."""


class CredencialesInvalidas(ErrorDominio):
    """Correo o contraseña incorrectos."""


class CorreoYaRegistrado(ErrorDominio):
    """Ya existe una cuenta con ese correo."""


class NoEncontrado(ErrorDominio):
    """Recurso inexistente (cita, médico, clínica...)."""
