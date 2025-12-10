# MockingBird3DApp

Aplicación web para gestión de pedidos de impresión 3D, construida con Flask, SQLAlchemy y Flask-Login.

Este README explica la arquitectura de la aplicación, los modelos principales, las rutas y cómo levantar el proyecto tanto en Linux como en Windows usando un entorno virtual.

## Índice
- Descripción y arquitectura
- Modelos principales
- Rutas y plantillas clave
- Requisitos
- Instalación y puesta en marcha (Linux / Windows / PowerShell)
- Migraciones y base de datos
- Crear el primer usuario (admin)
- Ejecutar la aplicación
- Notas de seguridad y producción
- Depuración y problemas frecuentes

## Descripción y arquitectura

MockingBird3DApp es una pequeña aplicación monolítica Flask que ofrece:

- Autenticación de usuarios (Flask-Login).
- CRUD simple para materiales y pedidos de impresión.
- Cálculo de precio aproximado por pedido basado en material, tiempo de impresión y configuración (precio electricidad / potencia impresora / margen).

Estructura principal (resumen):

- `app.py` — punto de entrada de Flask; define rutas y la lógica HTTP.
- `models.py` — modelos SQLAlchemy: `User`, `Settings`, `Material`, `Order`.
- `templates/` — Jinja2 templates (base, dashboard, login, materials, etc.).
- `static/` — CSS, JS e imágenes (logo, estilos).
- `migrations/` — carpeta generada por Flask-Migrate/Alembic (si usas migraciones).
- `config.py` — configuración de la app (SECRET_KEY, SQLALCHEMY_DATABASE_URI).

Diagrama lógico (texto):

Client (browser) <-HTTPS-> Flask app (`app.py`) -> SQLAlchemy -> SQLite (archivo `app.db` por defecto)

## Modelos principales

- User
	- id, email (único), password (hash)
- Settings
	- electricity_price, printer_power, profit_margin
- Material
	- id, name, price_per_kg
- Order
	- id, name, client, weight_grams, material_id, print_time_hours, status

Consulta `models.py` para detalles del esquema y el método `calculate_price` en `Order`.

## Rutas y plantillas clave

- `/login` — login y registro (template: `templates/login.html`).
- `/logout` — logout del usuario.
- `/dashboard` — panel principal que muestra pedidos en progreso y terminados (`templates/dashboard.html`).
- `/orders/new` — formulario para crear un pedido (`templates/order_form.html`).
- `/materials` — ver y agregar materiales (`templates/materials.html`).
- `/settings` — página para ajustar parámetros de impresión (`templates/settings.html`).

Las rutas están implementadas en `app.py`. Los mensajes de error/success se muestran mediante `flash()` y el template base ya incluye el bloque para mostrarlos.

## Requisitos

- Python 3.12+
- Pip
- Virtualenv (recomendado)
- SQLite (incluido en Python) o cualquier otra DB soportada por SQLAlchemy

Revisa `requirements.txt` para versiones concretas de dependencias (Flask, Flask-Login, Flask-SQLAlchemy, etc.).

## Instalación y puesta en marcha

Las instrucciones siguientes cubren Linux/macOS (Bash) y Windows (cmd.exe y PowerShell). Ajusta `python`/`python3` según tu instalación.

1) Clona el repositorio

```bash
git clone <repo-url>
cd MockingBird3DApp
```

2) Crear y activar entorno virtual

Linux / macOS (bash/zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows (cmd.exe):

```cmd
python -m venv .venv
.venv\Scripts\activate
```

Windows PowerShell:

```powershell
python -m venv .venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

3) Instalar dependencias

```bash
pip install -r requirements.txt
```

4) Configurar variables de entorno (opcional pero recomendado)

- `FLASK_APP=app.py` — indica a Flask dónde está la app.
- `FLASK_ENV=development` — (opcional) activa modo debug en Flask < 3; para Flask 3 usa `FLASK_DEBUG=1`.
- `SECRET_KEY` — en `config.py` hay un valor por defecto; para producción usa una variable de entorno o cambia `Config.SECRET_KEY`.

Ejemplos:

Linux/macOS:

```bash
export FLASK_APP=app.py
export FLASK_DEBUG=1
```

Windows (cmd.exe):

```cmd
set FLASK_APP=app.py
set FLASK_DEBUG=1
```

Windows PowerShell:

```powershell
$env:FLASK_APP = "app.py"
$env:FLASK_DEBUG = "1"
```

## Inicializar o migrar la base de datos

Este repo incluye `Flask-Migrate` (ya importado en `app.py`) y una carpeta `migrations/` (si ya existe). Tienes dos opciones:

- Opción A — Crear tablas rápidamente (útil en desarrollo):

```bash
# con entorno virtual activo
flask shell
>>> from app import db
>>> db.create_all()
>>> exit()
```

- Opción B — Usar Alembic / Flask-Migrate (recomendado si usarás migraciones en el tiempo):

```bash
flask db init        # sólo una vez (si no existe migrations/)
flask db migrate -m "Initial"
flask db upgrade
```

Si la carpeta `migrations/` ya está presente en el repo (como en este proyecto), normalmente basta con `flask db upgrade`.

## Crear el primer usuario (admin)

Puedes crear un usuario admin desde la shell de Flask si quieres un inicio rápido:

```bash
flask shell
>>> from app import db
>>> from models import User
>>> from werkzeug.security import generate_password_hash
>>> admin = User(email='admin@example.com', password=generate_password_hash('admin123'))
>>> db.session.add(admin)
>>> db.session.commit()
>>> exit()
```

Nota: `app.py` contiene un bloque que crea un usuario admin por defecto si no existe cuando ejecutas `python app.py` directamente; sin embargo, para entornos controlados es mejor crear usuarios explícitamente.

## Ejecutar la aplicación

Hay dos formas comunes de arrancar la app:

- Usar el comando `flask run` (usa el entorno definido por `FLASK_APP`):

```bash
flask run
```

- Ejecutar directamente el módulo (esto respeta el `app.run(...)` de `app.py`, que en este proyecto fija el puerto a 5001 por defecto si no hay variable `PORT`):

```bash
python app.py
# o en Windows PowerShell
python .\app.py
```

Por defecto, al ejecutar con `python app.py` la app arranca en el puerto 5001 (ver `app.run(..., port=int(os.environ.get("PORT", 5001)))`).

## Uso básico y pruebas rápidas

1. Accede a `http://127.0.0.1:5000/login` (o :5001 si ejecutas `python app.py`).
2. Regístrate o entra con el usuario admin.
3. Crea materiales desde `/materials` y luego crea pedidos en `/orders/new`.

## Notas de seguridad y recomendaciones para producción

- Cambia `SECRET_KEY` por una variable de entorno segura en producción.
- No uses `app.run(debug=True)` en producción. Emplea un servidor WSGI como Gunicorn o uWSGI detrás de Nginx.
- Considera utilizar una base de datos más robusta que SQLite (Postgres, MySQL) para entornos multiusuario.
- Añade limitación de intentos de inicio de sesión (rate limiting) y verificación por email para registros sensibles.

## Depuración y problemas frecuentes

- Error al convertir `price`/`float` en `/materials`: asegúrate de pasar un número válido; el formulario ahora valida `required` y `min`.
- Si el colapsable de Bootstrap (Crear cuenta) no funciona: asegúrate de haber incluido el bundle JS de Bootstrap (ya añadido en `templates/base.html`). Comprueba la consola del navegador.
- Si las tablas no aparecen: usa `flask db upgrade` o `db.create_all()` según tu flujo.

## Extensiones y mejoras posibles

- Persistir roles/permissiones en `User` (añadir campo `role` y migración).
- Añadir tests unitarios para rutas críticas y modelos.
- Integrar envío de emails para verificación/recuperación de contraseña.

---
