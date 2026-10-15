# Catálogo de productos con FastAPI, SQLite y Docker

Aplicación web para administrar un catálogo y registrar ingresos y salidas de inventario, guardados localmente en SQLite. La página y la API no dependen de una conexión en vivo con Oracle APEX.

## Componentes

- FastAPI y Pydantic: API y validación de productos.
- Rutas HTTP en `app/api/` y lógica de negocio en `app/servicios/`, separadas de `app/main.py`.
- Interfaz por módulo: `static/productos/` y `static/movimientos/`, con un JavaScript por página.
- SQLite: almacenamiento local persistente con seis tablas relacionadas.
- Bootstrap: interfaz web adaptable a móvil y escritorio.
- Docker Compose: ejecuta la aplicación y conserva la base en `data/productos.db`.
- pytest y httpx: pruebas HTTP de la API.

## Requisitos

- Python 3.11 o superior, o Docker.
- Para Docker en Windows: Docker Desktop iniciado y con el motor de contenedores Linux listo.

## Ejecutar localmente

1. Crear un entorno virtual e instalar dependencias:

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Iniciar la aplicación:

   ```bash
   uvicorn app.main:app --reload
   ```

   SQLite crea automáticamente las tablas definidas en `sql/esquema.sql` dentro de `data/productos.db`.

3. Abrir `http://localhost:8000` para ver productos, `/movimientos-ui` para movimientos, `/categorias-ui` para categorías, `/proveedores-ui` para proveedores, `/usuarios-ui` para usuarios, `/roles-ui` para roles o `/docs` para la documentación interactiva.

## Ejecutar con Docker

En Windows, abre Docker Desktop y espera a que indique que el motor está en ejecución. En PowerShell, desde la carpeta del proyecto:

```powershell
docker compose up --build -d
docker compose ps
```

La base de datos se guarda en `data/productos.db` en el proyecto y sobrevive a la recreación del contenedor. Abre `http://localhost:8000` para productos, `/movimientos-ui` para movimientos, `/categorias-ui` para categorías, `/proveedores-ui` para proveedores, `/usuarios-ui` para usuarios, `/roles-ui` para roles y `/docs` para la documentación interactiva. Usa `docker compose logs -f api` para ver los registros y `docker compose down` para detener la aplicación. Las claves foráneas se validan en SQLite.

Bootstrap se carga desde jsDelivr y requiere acceso a internet desde el navegador. La API no consulta Oracle APEX.

La interfaz CRUD y la API no tienen autenticación; ejecútalas solo en un entorno local o de confianza.

## Cargar productos

`sql/esquema.sql` define los seis objetos de la base: roles, usuarios, categorías, proveedores, productos y movimientos. Se ejecuta automáticamente al iniciar la aplicación.

Para cargar los datos de ejemplo, ejecuta una sola vez el script SQLite `sql/productos.sql`. Desde PowerShell, en la raíz del proyecto y con el contenedor en ejecución:

```powershell
docker compose exec api python -m app.ejecutar_sql /app/sql/productos.sql
```

El script se ejecuta contra `data/productos.db`. Si quieres cargar tu inventario real, edita sus sentencias `INSERT` antes de ejecutarlo. La tabla web muestra productos activos e inactivos, incluyendo categoría, proveedor, unidad, precio de venta y stock. El stock nuevo inicia en cero y solo cambia mediante un movimiento para conservar el historial. Consulta [`docs/sqlite.md`](docs/sqlite.md) para más detalles.

Si ya existía una base de la versión previa y tenía productos, la aplicación no borra ni convierte automáticamente esos registros: detiene el arranque e indica que debes hacer una copia y migrarlos. La tabla antigua vacía se sustituye automáticamente por el nuevo esquema.

## Probar

```bash
python -m pytest
```

Las pruebas usan bases de datos temporales y no necesitan conexión a internet ni a APEX.

## Ruta de la API

| Método | Ruta | Acción |
| --- | --- | --- |
| GET | `/productos` | Listar productos |
| GET | `/productos/{id}` | Consultar un producto |
| POST | `/productos` | Crear un producto |
| PUT | `/productos/{id}` | Actualizar un producto |
| DELETE | `/productos/{id}` | Eliminar un producto |
| GET | `/movimientos` | Consultar el historial de movimientos |
| POST | `/movimientos` | Registrar un ingreso o una salida |
| PUT | `/movimientos/{id}` | Actualizar cantidad, usuario y observación |
| GET/POST | `/categorias` | Listar o crear categorías |
| GET/PUT/DELETE | `/categorias/{id}` | Consultar, actualizar o eliminar una categoría |
| GET/POST | `/proveedores` | Listar o crear proveedores |
| GET/PUT/DELETE | `/proveedores/{id}` | Consultar, actualizar o eliminar un proveedor |
| GET/POST | `/roles` | Listar o crear roles |
| GET/PUT/DELETE | `/roles/{id}` | Consultar, actualizar o eliminar un rol |
| GET | `/usuarios` | Listar usuarios sin exponer hashes de contraseña |
| GET | `/usuarios/{id}` | Consultar un usuario sin exponer su hash |
| PUT | `/usuarios/{id}` | Actualizar nombre, correo, rol y estado activo |

La administración de usuarios permite consultar y editar nombre, correo, rol y estado. No existe creación ni eliminación de usuarios desde este módulo. La creación de cuentas y la gestión de contraseñas quedan reservadas para la integración del módulo de autenticación; `password_hash` nunca se devuelve ni se acepta en estas rutas.

Los roles tienen un módulo CRUD independiente. No se permite eliminar un rol mientras haya usuarios asignados a él.
