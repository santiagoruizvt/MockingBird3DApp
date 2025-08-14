# MockingBird3DApp

Aplicación web para gestión de pedidos de impresión 3D con Flask, SQLAlchemy y Flask-Login.

## Funcionalidades
- Login / Logout de usuarios.
- Dashboard con pedidos en progreso y terminados.
- Crear nuevos pedidos, asignando material y tiempo de impresión.
- Administrar materiales disponibles.
- Configuración de parámetros de impresión (precio de electricidad, potencia de impresora, margen de ganancia).

## Requisitos
- Python 3.12+
- SQLite (o cualquier DB soportada por SQLAlchemy)
- Virtualenv (opcional, recomendado)

## Instalación

1. Clonar el repositorio:
```bash
git clone <repo-url>
cd MockingBird3DApp
```
2. Crear entorno virtual e instalar dependencias necesarias
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
3. Inicializar la db
```bash
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()
```

4. Ejecutar la app (puerto 5000)
```bash
flask run
