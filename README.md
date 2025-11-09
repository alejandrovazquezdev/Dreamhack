# Dreamhack — Aplicación de ejemplo en Flask

Proyecto con el proposito de facilitar transacciones de compras personales. Incluye un modelo `Usuarios`, un formulario para registrar usuarios, vistas destinadas a la creación de salas par la interacción entre comprador y vendedor, cuyo propósito es asegurar una transacción fácil y rápida. Esta documentación cubre instalación, configuración, endpoints y detalles del modelo de datos.

## Contenido

- `app.py` — punto de entrada de la aplicación y rutas.
- `models.py` — definición del modelo `Usuarios`.
- `db.py` — objeto `SQLAlchemy` compartido.
- `forms.py` — formularios con `Flask-WTF`.
- `init_db.sql` — script SQL para crear y poblar la tabla `usuarios`.
- `templates/` — plantillas Jinja para la UI (`index.html`, `login.html`, `signup.html`).
- `static/` — assets CSS/JS.

## Tecnologías

- Python 3.x
- Flask
- Flask-SQLAlchemy
- Flask-Migrate
- Flask-WTF
- PostgreSQL (psycopg2)

Las dependencias están en `requeriments.txt`.

## Resumen rápido — Ejecutar localmente

1. Crear y activar un entorno virtual: `python -m venv .venv && source .venv/bin/activate`.
2. Instalar dependencias: `pip install -r requeriments.txt`.
3. Configurar la conexión a la base de datos (ver sección de configuración).
4. Crear la base de datos y ejecutar `init_db.sql` o usar Flask-Migrate para crear las tablas.
5. Ejecutar la app: `python app.py` (va a http://localhost:5000).

Para pasos detallados, ver `docs/INSTALL.md` y `docs/USAGE.md`.

## Notas importantes

- La configuración de base de datos en `app.py` está actualmente codificada con credenciales de ejemplo. No usar en producción tal cual. Preferible usar variables de entorno.
- Rutas principales:
    - `/` — Página de inicio que muestra la lista de usuarios y el total.
    - `/login` — Formulario de registro (GET) y manejo de envío (POST).
    - `/static/admin/` — Endpoint simple que devuelve un JSON de estado.

## Contribuciones

Ver `docs/CONTRIBUTING.md` para pautas básicas.

## Licencia

Incluye la licencia que prefieras o especifica "MIT" si quieres usar una licencia permisiva.

---

Para documentación técnica más completa, revisar la carpeta `docs/`.