(() => {
  "use strict";

  const indicadorApi = document.querySelector("#api-indicator");
  const mensaje = document.querySelector("#mensaje");
  const formatoCantidad = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 3 });
  const formatoMoneda = new Intl.NumberFormat("es-CO", {
    style: "currency",
    currency: "COP",
    maximumFractionDigits: 0,
  });

  async function solicitar(url) {
    const respuesta = await fetch(url);
    if (!respuesta.ok) {
      const detalle = await respuesta.json().catch(() => null);
      throw new Error(detalle?.detail || `Error HTTP ${respuesta.status}`);
    }
    return respuesta.json();
  }

  function mostrarEstadoApi(estado, texto) {
    indicadorApi.className = `api-indicator api-indicator-${estado}`;
    indicadorApi.lastElementChild.textContent = texto;
  }

  function agregarCelda(fila, texto, clase = "") {
    const celda = document.createElement("td");
    celda.textContent = texto;
    if (clase) celda.className = clase;
    fila.append(celda);
  }

  function mostrarVacio(cuerpo, columnas, texto) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = columnas;
    celda.className = "text-center text-secondary py-4";
    celda.textContent = texto;
    fila.append(celda);
    cuerpo.replaceChildren(fila);
  }

  function renderizarStockBajo(productos) {
    const cuerpo = document.querySelector("#lista-stock-bajo");
    const bajos = productos
      .filter((producto) => producto.activo && producto.stock_actual <= producto.stock_minimo)
      .sort((a, b) => (a.stock_actual - a.stock_minimo) - (b.stock_actual - b.stock_minimo))
      .slice(0, 6);
    if (!bajos.length) {
      mostrarVacio(cuerpo, 4, "No hay productos activos con stock bajo.");
      return;
    }

    cuerpo.replaceChildren();
    bajos.forEach((producto) => {
      const fila = document.createElement("tr");
      agregarCelda(fila, producto.nombre, "ps-3 fw-medium");
      agregarCelda(fila, producto.categoria);
      agregarCelda(fila, `${formatoCantidad.format(producto.stock_actual)} ${producto.unidad}`, "text-end text-danger fw-semibold");
      agregarCelda(fila, `${formatoCantidad.format(producto.stock_minimo)} ${producto.unidad}`, "text-end pe-3");
      cuerpo.append(fila);
    });
  }

  function renderizarCategorias(productos, categorias) {
    const contenedor = document.querySelector("#resumen-categorias");
    const cantidades = new Map(categorias.map((categoria) => [categoria.nombre, 0]));
    productos.forEach((producto) => {
      cantidades.set(producto.categoria, (cantidades.get(producto.categoria) || 0) + 1);
    });
    const ordenadas = [...cantidades.entries()].sort((a, b) => b[1] - a[1]);
    if (!ordenadas.length) {
      contenedor.replaceChildren();
      const vacio = document.createElement("p");
      vacio.className = "text-secondary mb-0";
      vacio.textContent = "No hay categorías registradas.";
      contenedor.append(vacio);
      return;
    }

    const maximo = Math.max(1, ...ordenadas.map(([, cantidad]) => cantidad));
    contenedor.replaceChildren();
    ordenadas.slice(0, 7).forEach(([nombre, cantidad]) => {
      const fila = document.createElement("div");
      fila.className = "dashboard-category";
      const encabezado = document.createElement("div");
      encabezado.className = "dashboard-category-heading";
      const etiqueta = document.createElement("span");
      etiqueta.textContent = nombre;
      const total = document.createElement("strong");
      total.textContent = String(cantidad);
      encabezado.append(etiqueta, total);
      const barra = document.createElement("div");
      barra.className = "dashboard-category-track";
      const progreso = document.createElement("span");
      progreso.style.width = `${(cantidad / maximo) * 100}%`;
      barra.append(progreso);
      fila.append(encabezado, barra);
      contenedor.append(fila);
    });
  }

  function renderizarMovimientos(movimientos) {
    const cuerpo = document.querySelector("#lista-movimientos");
    const recientes = [...movimientos]
      .sort((a, b) => b.fecha.localeCompare(a.fecha))
      .slice(0, 5);
    if (!recientes.length) {
      mostrarVacio(cuerpo, 5, "Todavía no hay movimientos registrados.");
      return;
    }

    cuerpo.replaceChildren();
    recientes.forEach((movimiento) => {
      const fila = document.createElement("tr");
      const fecha = new Date(movimiento.fecha.replace(" ", "T"));
      const textoFecha = Number.isNaN(fecha.getTime())
        ? movimiento.fecha
        : fecha.toLocaleString("es-CO");
      agregarCelda(fila, textoFecha, "ps-3 text-secondary");
      const tipo = document.createElement("td");
      const etiqueta = document.createElement("span");
      etiqueta.className = `badge rounded-pill ${movimiento.tipo === "ENTRADA" ? "text-bg-success-subtle text-success-emphasis" : "text-bg-primary-subtle text-primary-emphasis"}`;
      etiqueta.textContent = movimiento.tipo === "ENTRADA" ? "Ingreso" : "Salida";
      tipo.append(etiqueta);
      fila.append(tipo);
      agregarCelda(fila, movimiento.producto, "fw-medium");
      agregarCelda(fila, `${formatoCantidad.format(movimiento.cantidad)} ${movimiento.unidad}`, "text-end");
      agregarCelda(fila, movimiento.usuario, "pe-3");
      cuerpo.append(fila);
    });
  }

  function actualizarResumenTabla(id, cantidad) {
    document.querySelector(`#${id}`).textContent = String(cantidad);
  }

  function agregarModuloAdmin(usuarios, roles) {
    const resumen = document.querySelector("#resumen-tablas");
    [
      { nombre: "Usuarios", ruta: "/usuarios-ui", total: usuarios.length },
      { nombre: "Roles", ruta: "/roles-ui", total: roles.length },
    ].forEach(({ nombre, ruta, total }) => {
      const columna = document.createElement("div");
      columna.className = "col-6 col-lg-4";
      const enlace = document.createElement("a");
      enlace.className = "dashboard-module-card";
      enlace.href = ruta;
      const etiqueta = document.createElement("span");
      etiqueta.className = "dashboard-module-label";
      etiqueta.textContent = nombre;
      const cantidad = document.createElement("strong");
      cantidad.textContent = String(total);
      const accion = document.createElement("span");
      accion.textContent = `Ver ${nombre.toLocaleLowerCase("es")} →`;
      enlace.append(etiqueta, cantidad, accion);
      columna.append(enlace);
      resumen.append(columna);
    });
  }

  async function iniciarDashboard() {
    try {
      const sesion = await solicitar("/auth/yo");
      const solicitudes = [
        solicitar("/productos"),
        solicitar("/movimientos"),
        solicitar("/categorias"),
        solicitar("/proveedores"),
      ];
      if (sesion.rol === "ADMINISTRADOR") {
        solicitudes.push(solicitar("/usuarios"), solicitar("/roles"));
      }
      const datos = await Promise.all(solicitudes);
      const [productos, movimientos, categorias, proveedores, usuarios, roles] = datos;
      const productosActivos = productos.filter((producto) => producto.activo);
      const productosBajos = productosActivos.filter(
        (producto) => producto.stock_actual <= producto.stock_minimo,
      );
      const valorInventario = productos.reduce(
        (total, producto) => total + producto.stock_actual * producto.precio_venta,
        0,
      );
      const entradas = movimientos.filter((movimiento) => movimiento.tipo === "ENTRADA").length;
      const salidas = movimientos.length - entradas;

      document.querySelector("#kpi-productos").textContent = String(productosActivos.length);
      document.querySelector("#nota-productos").textContent = `de ${productos.length} en catálogo`;
      document.querySelector("#kpi-stock-bajo").textContent = String(productosBajos.length);
      document.querySelector("#kpi-movimientos").textContent = String(movimientos.length);
      document.querySelector("#nota-movimientos").textContent = `${entradas} ingresos · ${salidas} salidas`;
      document.querySelector("#kpi-valor").textContent = formatoMoneda.format(valorInventario);

      actualizarResumenTabla("total-productos", productos.length);
      actualizarResumenTabla("total-categorias", categorias.length);
      actualizarResumenTabla("total-proveedores", proveedores.length);
      actualizarResumenTabla("total-movimientos", movimientos.length);
      if (sesion.rol === "ADMINISTRADOR") agregarModuloAdmin(usuarios, roles);

      renderizarStockBajo(productos);
      renderizarCategorias(productos, categorias);
      renderizarMovimientos(movimientos);
      mostrarEstadoApi("ok", "Datos actualizados");
    } catch (error) {
      mensaje.textContent = `No se pudo cargar el dashboard: ${error.message}`;
      mensaje.className = "alert alert-danger";
      mostrarEstadoApi("error", "Error al cargar datos");
      mostrarVacio(document.querySelector("#lista-stock-bajo"), 4, "No se pudo cargar el inventario.");
      mostrarVacio(document.querySelector("#lista-movimientos"), 5, "No se pudieron cargar los movimientos.");
      const categorias = document.querySelector("#resumen-categorias");
      categorias.replaceChildren();
      const errorCategoria = document.createElement("p");
      errorCategoria.className = "text-danger mb-0";
      errorCategoria.textContent = "No se pudo cargar el resumen por categoría.";
      categorias.append(errorCategoria);
    }
  }

  iniciarDashboard();
})();
