"""Hash de contraseñas (PBKDF2 de la biblioteca estándar)."""
import hashlib
import hmac
import os

_ITERACIONES = 100_000


def hashear(clave: str) -> str:
    sal = os.urandom(16)
    h = hashlib.pbkdf2_hmac("sha256", clave.encode(), sal, _ITERACIONES)
    return f"{sal.hex()}${h.hex()}"


def verificar(clave: str, almacenado: str) -> bool:
    sal_hex, h_hex = almacenado.split("$")
    h = hashlib.pbkdf2_hmac("sha256", clave.encode(), bytes.fromhex(sal_hex), _ITERACIONES)
    return hmac.compare_digest(h.hex(), h_hex)
