"""Arranque de la aplicación:  python run.py  →  http://localhost:5000"""
from medischedule.web.app import crear_app

if __name__ == "__main__":
    # threaded=True: atiende peticiones simultáneas (el anticolisión lo soporta).
    crear_app().run(host="0.0.0.0", port=5000, threaded=True)
