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

La interfaz y la API requieren iniciar sesión; consulta la sección «Autenticación y roles».

## Autenticación y roles

La API y las páginas piden iniciar sesión. Abre `/login-ui` (o cualquier página, que te redirige) y entra con uno de los usuarios de demostración:

| Correo | Contraseña | Rol |
| --- | --- | --- |
| `admin@salsamentaria.com` | `admin123` | ADMINISTRADOR |
| `ventas@salsamentaria.com` | `ventas123` | VENDEDOR |

Son solo para pruebas locales. Antes de publicar la aplicación cámbialas con las variables `ADMIN_PASSWORD` y `VENDEDOR_PASSWORD`, o con `python -m app.establecer_password correo@ejemplo.com`.

El administrador puede crear cuentas desde `/usuarios-ui`. La aplicación genera una contraseña temporal aleatoria y la muestra una sola vez después de guardar; debe entregarse al usuario de forma segura. El primer inicio de sesión obliga a cambiarla antes de usar cualquier módulo. Cada usuario puede cambiar luego su contraseña desde el menú de sesión.

El enlace «Olvidé mi contraseña» permite restablecerla indicando el correo y la nueva contraseña dos veces, sin correo ni SMS. Esta recuperación no verifica la identidad y cualquiera que conozca el correo podría tomar la cuenta: está desactivada por defecto y es solo para pruebas locales. Para habilitarla explícitamente en desarrollo, configura `AUTH_RECUPERACION_SIN_VERIFICACION=1`; nunca la habilites en producción. Render la mantiene desactivada.

**Permisos por rol**

| Acción | ADMINISTRADOR | VENDEDOR |
| --- | --- | --- |
| Consultar productos, movimientos, categorías y proveedores | Sí | Sí |
| Registrar movimientos (`POST /movimientos`) | Sí | Sí |
| Crear, editar o eliminar productos, categorías, proveedores y movimientos | Sí | No (403) |
| Usuarios y roles (cualquier operación) | Sí | No (403) |

Sin sesión válida la API responde `401`; con una sesión sin permiso, `403`. Las sesiones duran 8 horas y se firman con `SECRET_KEY`; una cuenta desactivada pierde el acceso de inmediato.

**Probar en Swagger:** en `/docs` ejecuta `POST /auth/login`, copia el `access_token`, pulsa **Authorize** y pégalo.

La documentación de `/docs` agrupa las rutas por los módulos Productos, Movimientos, Categorías, Proveedores, Usuarios, Roles y Autenticación. Las páginas de la interfaz web no aparecen en el esquema de la API.

**Variables de entorno**

| Variable | Uso |
| --- | --- |
| `SECRET_KEY` | Clave para firmar las sesiones. En Render se genera sola. |
| `ADMIN_PASSWORD`, `VENDEDOR_PASSWORD` | Reemplazan las contraseñas de demostración al arrancar. |
| `AUTH_ACTIVADA` | `0` desactiva la autenticación. Solo para pruebas automáticas; no la uses en un despliegue. |
| `AUTH_RECUPERACION_SIN_VERIFICACION` | `1` habilita el restablecimiento sin verificación. Solo para pruebas locales; por defecto y en Render queda en `0`. |

Si tu base local se creó antes de esta versión, sus usuarios tienen contraseñas de relleno. Actualízalas con:

```bash
python -m app.establecer_password admin@salsamentaria.com --password admin123
python -m app.establecer_password ventas@salsamentaria.com --password ventas123
```

## Reportes

La opción **Reportes** del menú (`/reportes-ui`) consulta cuatro reportes consolidados. Los pueden ver ambos roles; la API de reportes es solo de lectura.

| Reporte | Ruta | Filtros |
| --- | --- | --- |
| Inventario por categoría (productos, bajo el mínimo y valor) | `GET /reportes/inventario-por-categoria` | — |
| Productos con stock bajo y su proveedor | `GET /reportes/stock-bajo` | — |
| Movimientos por proveedor (entradas y salidas) | `GET /reportes/movimientos-por-proveedor` | `desde`, `hasta` (opcionales, `AAAA-MM-DD`) |
| Movimientos por usuario | `GET /reportes/movimientos-por-usuario` | `desde`, `hasta` (opcionales, `AAAA-MM-DD`) |

Las cantidades se separan por unidad (KG o UND) para no sumar kilos con unidades. Cada reporte se puede descargar en CSV desde la página (separado por punto y coma, listo para Excel). Una fecha inicial posterior a la final responde `422`.

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
| POST | `/auth/login` | Iniciar sesión y obtener el token |
| GET | `/auth/yo` | Consultar el usuario de la sesión |
| PUT | `/auth/password` | Cambiar la contraseña propia |
| POST | `/auth/usuarios` | Crear un usuario con contraseña temporal generada (solo administrador) |
| POST | `/auth/recuperar-password` | Restablecer contraseña sin verificación (solo si `AUTH_RECUPERACION_SIN_VERIFICACION=1`) |

La administración de usuarios permite consultar, crear y editar nombre, correo, rol y estado. No existe eliminación de usuarios desde este módulo. La creación genera una contraseña temporal que se revela una sola vez; `password_hash` nunca se devuelve ni se acepta en estas rutas.

Los roles tienen un módulo CRUD independiente. No se permite eliminar un rol mientras haya usuarios asignados a él.
