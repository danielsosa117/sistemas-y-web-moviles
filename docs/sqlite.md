# Esquema y datos SQLite

La aplicación usa SQLite como fuente local y no consulta Oracle APEX/ORDS al mostrar el catálogo. El archivo persistente está en `data/productos.db`.

El script original estaba escrito para Oracle. No se puede ejecutar directamente en SQLite: Oracle `NUMBER`, `VARCHAR2`, columnas `IDENTITY`, `SYSDATE` y los `ALTER TABLE ... ADD CONSTRAINT` no son compatibles tal cual. El esquema convertido está en `sql/esquema.sql`; la aplicación lo ejecuta al arrancar.

El esquema contiene seis tablas: `roles`, `usuarios`, `categorias`, `proveedores`, `productos` y `movimientos`. Las claves foráneas y restricciones `CHECK` se definen junto a sus tablas y SQLite las valida.

## Cargar datos

`sql/productos.sql` contiene datos de ejemplo compatibles con SQLite. Para cargar tus propios datos, edita sus `INSERT`, respetando las relaciones: roles antes de usuarios, categorías y proveedores antes de productos, y productos/usuarios antes de movimientos. El archivo actual incluye productos demostrativos; reemplázalos por los registros reales antes de ejecutar si no quieres conservarlos.

Los usuarios de ejemplo traen contraseñas con hash PBKDF2-SHA256 (`admin123` y `ventas123`, solo para demostración).

Ejecuta el archivo **una sola vez**. Desde PowerShell, en la raíz del proyecto y con Docker Desktop activo:

```powershell
docker compose up -d
docker compose exec api python -m app.ejecutar_sql /app/sql/productos.sql
```

La carpeta `sql/` se monta como solo lectura dentro del contenedor y el ejecutor aplica el archivo a `/data/productos.db`. La carpeta local `data/` conserva la base aunque el contenedor se detenga o se reconstruya. Recarga `http://localhost:8000` para ver el catálogo.

Al volver a ejecutar el script de ejemplo, las claves primarias y restricciones únicas producirán un error de duplicado. Para editar registros existentes, usa `UPDATE`; para agregar, usa IDs nuevos. Los IDs de los ejemplos están fijados para que las relaciones de movimientos coincidan.

## Diferencias con el modelo anterior de la API

El catálogo actual usa las columnas que realmente define el modelo de inventario: nombre, categoría, proveedor, unidad, precio de venta, existencias, mínimo y activo. Ya no espera `codigo`, `descripcion` ni `precio_compra`, campos que no existen en la tabla Oracle del archivo original.

## Operaciones de productos

El código Python mantiene las responsabilidades separadas: `app/api/` contiene las rutas HTTP por módulo y `app/servicios/` contiene la lógica de negocio y acceso a SQLite. `app/main.py` registra los routers y sirve las páginas; los esquemas, la inicialización de la base de datos y los scripts SQL permanecen en `app/`.

El dashboard está en `app/static/dashboard/index.html`, y su lógica en `dashboard/dashboard.js`; se muestra en `/` y resume las tablas de inventario, movimientos y catálogos. Los administradores también ven los resúmenes de usuarios y roles. La página de productos está en `app/static/productos/index.html`, y su lógica en `productos/productos.js`. La página de movimientos está en `app/static/movimientos/index.html`, y su lógica en `movimientos/movimientos.js`. Las páginas de categorías, proveedores, usuarios y roles están en sus respectivas carpetas de `app/static/`, también con un archivo JavaScript propio. Se accede a productos desde `/productos-ui`, a movimientos desde `/movimientos-ui`, a categorías desde `/categorias-ui`, a proveedores desde `/proveedores-ui`, a usuarios desde `/usuarios-ui` y a roles desde `/roles-ui`. La lógica y las rutas de API también están separadas en módulos; `app/main.py` conserva la creación de la aplicación y las páginas. El stock no se edita desde el formulario del producto: los productos nuevos comienzan con cero existencias para que todo cambio posterior quede reflejado en el historial. Los campos categoría y proveedor se eligen de los catálogos existentes y el precio debe ser mayor que cero.

La sección de movimientos permite registrar ingresos y ventas/salidas y consultar el historial. Cada movimiento registra producto, cantidad, tipo, fecha, observación y usuario elegido de la lista. La salida solo se registra si hay stock suficiente; la comprobación, el descuento del inventario y la inserción del movimiento se realizan en una transacción. Todas las cantidades deben ser mayores que cero; las cantidades de productos `UND` deben ser enteras. Si el producto ya tiene stock o movimientos, su unidad no se puede cambiar para no reinterpretar el inventario ni el historial.

Un movimiento se puede corregir desde la acción **Editar** o con `PUT /movimientos/{id}`; solo se aceptan cantidad, usuario y observación. Tipo, producto y fecha se conservan. La corrección actualiza el stock por la diferencia entre la cantidad anterior y la nueva, dentro de una transacción; si el cambio haría que el stock quedara negativo, se rechaza sin modificar el movimiento.

Categorías y proveedores cuentan con operaciones de listar, consultar, crear, actualizar y eliminar en `/categorias` y `/proveedores`. Los nombres no pueden estar vacíos; no se permiten nombres de categoría duplicados. No se puede eliminar una categoría o proveedor que tenga productos asociados, para evitar dejar referencias huérfanas.

Un producto asociado a movimientos no se puede eliminar, para conservar el historial. En ese caso la API devuelve `409 Conflict`; se puede editar para marcarlo inactivo. La selección de usuario identifica al responsable en el registro, pero no es autenticación: como la aplicación todavía no implementa inicio de sesión, no constituye una medida de control de acceso.

La administración de usuarios permite listar y consultar cuentas, y actualizar nombre, correo, rol y estado activo. No se ofrece creación ni eliminación de usuarios desde este módulo. Las contraseñas y su hash no se devuelven ni pueden actualizarse aquí; la creación de cuentas y la gestión de credenciales se implementarán junto con autenticación.

Los roles se administran desde `/roles-ui` y la API `/roles` permite listar, consultar, crear, actualizar y eliminar roles. Los nombres deben ser únicos y no pueden quedar vacíos. SQLite impide eliminar un rol que esté asignado a uno o más usuarios; en ese caso la API devuelve `409 Conflict`.

La aplicación aún no tiene autenticación. Limita su uso a un entorno local o de confianza.
