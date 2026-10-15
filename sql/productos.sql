-- Datos de ejemplo SQLite.
-- Ejecutar una sola vez después de iniciar la aplicación.
-- Contraseñas de demostración (solo para pruebas): admin123 y ventas123.
-- Los hashes son PBKDF2-SHA256. Cámbialas antes de publicar la aplicación.

BEGIN;

INSERT INTO roles (id_rol, nombre) VALUES (1, 'ADMINISTRADOR');
INSERT INTO roles (id_rol, nombre) VALUES (2, 'VENDEDOR');

INSERT INTO usuarios (id_usuario, nombre, email, password_hash, id_rol) VALUES
    (1, 'Administrador', 'admin@salsamentaria.com', 'pbkdf2_sha256$600000$e4a343263b698a15c5892918210019d2$35f4e8912fd8d208fd4901d8775f4934cd64ddb783ef1e9e6bcc350490f3b934', 1),
    (2, 'Laura Vendedora', 'ventas@salsamentaria.com', 'pbkdf2_sha256$600000$41344ec2e1faef7c3410cb49ff074e99$5589b069254e5706d36e6ec47d3e55963a20f6c439e0946552be7e6334cebf3a', 2);

INSERT INTO categorias (id_categoria, nombre) VALUES
    (1, 'Embutidos'),
    (2, 'Quesos'),
    (3, 'Lácteos'),
    (4, 'Abarrotes');

INSERT INTO proveedores (id_proveedor, nombre, telefono, email) VALUES
    (1, 'Cárnicos del Valle', '3101234567', 'ventas@carnicosvalle.com'),
    (2, 'Lácteos La Pradera', '3112345678', 'pedidos@lapradera.com'),
    (3, 'Abarrotes Central', '3123456789', 'contacto@abarrotescentral.com');

INSERT INTO productos (
    id_producto, nombre, id_categoria, id_proveedor, unidad, precio_venta,
    stock_actual, stock_minimo
) VALUES
    (1, 'Jamón de cerdo', 1, 1, 'KG', 32000, 16.5, 5),
    (2, 'Salchichón cervecero', 1, 1, 'KG', 26000, 14.2, 4),
    (3, 'Chorizo santarrosano', 1, 1, 'UND', 3800, 90, 20),
    (4, 'Queso campesino', 2, 2, 'KG', 24000, 15.75, 6),
    (5, 'Queso mozzarella', 2, 2, 'KG', 30000, 4, 5),
    (6, 'Leche entera 1 L', 3, 2, 'UND', 4800, 54, 24),
    (7, 'Arroz 500 g', 4, 3, 'UND', 3000, 75, 30),
    (8, 'Huevos cubeta x30', 4, 3, 'UND', 19500, 6, 8);

INSERT INTO movimientos (
    id_producto, id_usuario, tipo, cantidad, fecha, observacion
) VALUES
    (1, 1, 'ENTRADA', 20, datetime('now', '-20 days'), 'Compra inicial'),
    (2, 1, 'ENTRADA', 15, datetime('now', '-20 days'), 'Compra inicial'),
    (3, 1, 'ENTRADA', 100, datetime('now', '-20 days'), 'Compra inicial'),
    (4, 1, 'ENTRADA', 18, datetime('now', '-10 days'), 'Compra inicial'),
    (5, 1, 'ENTRADA', 10, datetime('now', '-10 days'), 'Compra inicial'),
    (6, 1, 'ENTRADA', 60, datetime('now', '-10 days'), 'Compra inicial'),
    (7, 1, 'ENTRADA', 80, datetime('now', '-7 days'), 'Compra inicial'),
    (8, 1, 'ENTRADA', 20, datetime('now', '-7 days'), 'Compra inicial'),
    (1, 2, 'SALIDA', 3.5, datetime('now', '-5 days'), 'Ventas de la semana'),
    (2, 2, 'SALIDA', 0.8, datetime('now', '-4 days'), 'Venta mostrador'),
    (3, 2, 'SALIDA', 10, datetime('now', '-4 days'), 'Venta mostrador'),
    (4, 2, 'SALIDA', 2.25, datetime('now', '-3 days'), 'Venta mostrador'),
    (5, 2, 'SALIDA', 6, datetime('now', '-2 days'), 'Pedido de restaurante'),
    (6, 2, 'SALIDA', 6, datetime('now', '-2 days'), 'Venta mostrador'),
    (7, 2, 'SALIDA', 5, datetime('now', '-1 day'), 'Venta mostrador'),
    (8, 2, 'SALIDA', 14, datetime('now'), 'Pedido de tienda');

COMMIT;
