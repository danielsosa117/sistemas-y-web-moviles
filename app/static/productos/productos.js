const listaProductos = document.querySelector("#lista-productos");
const totalProductos = document.querySelector("#total-productos");
const mensaje = document.querySelector("#mensaje");
const formulario = document.querySelector("#formulario-producto");
const dialogoProducto = document.querySelector("#dialogo-producto");
const selectorCategoria = document.querySelector("#id_categoria");
const selectorProveedor = document.querySelector("#id_proveedor");
const busquedaProducto = document.querySelector("#buscar-producto");
const indicadorApi = document.querySelector("#api-indicator");
const formatoPrecio = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});
const formatoCantidad = new Intl.NumberFormat("es-CO", {
  maximumFractionDigits: 3,
});

let idProductoEnEdicion = null;
let productosDisponibles = [];

function mostrarMensaje(texto, tipo = "danger") {
  mensaje.textContent = texto;
  mensaje.className = `alert alert-${tipo}`;
}

function mostrarEstadoApi(estado, texto) {
  indicadorApi.className = `api-indicator api-indicator-${estado}`;
  indicadorApi.lastElementChild.textContent = texto;
}

function ocultarMensaje() {
  mensaje.textContent = "";
  mensaje.className = "alert d-none";
}

async function solicitar(url, opciones = {}) {
  const respuesta = await fetch(url, opciones);
  if (!respuesta.ok) {
    const detalle = await respuesta.json().catch(() => null);
    throw new Error(detalle?.detail || `Error HTTP ${respuesta.status}`);
  }
  if (respuesta.status === 204) return null;
  return respuesta.json();
}

function agregarCelda(fila, texto, clase = "") {
  const celda = document.createElement("td");
  celda.textContent = texto;
  if (clase) celda.className = clase;
  fila.append(celda);
  return celda;
}

function agregarBoton(fila, texto, clase, accion) {
  const boton = document.createElement("button");
  boton.type = "button";
  boton.textContent = texto;
  boton.className = `btn btn-sm ${clase} me-1`;
  boton.addEventListener("click", accion);
  fila.lastElementChild.append(boton);
}

function crearFila(producto) {
  const fila = document.createElement("tr");
  agregarCelda(fila, String(producto.id_producto), "ps-3 text-secondary");
  agregarCelda(fila, producto.nombre, "fw-medium");
  agregarCelda(fila, producto.categoria);
  agregarCelda(fila, producto.proveedor);
  agregarCelda(fila, producto.unidad);
  agregarCelda(fila, formatoPrecio.format(producto.precio_venta), "text-end");

  const celdaStock = agregarCelda(fila, "", "text-end");
  const stock = document.createElement("span");
  stock.textContent = formatoCantidad.format(producto.stock_actual);
  celdaStock.append(stock);
  if (producto.stock_actual <= producto.stock_minimo) {
    const aviso = document.createElement("span");
    aviso.className = "badge rounded-pill text-bg-warning-subtle text-warning-emphasis ms-2";
    aviso.textContent = "Bajo";
    celdaStock.append(aviso);
  }

  agregarCelda(fila, formatoCantidad.format(producto.stock_minimo), "text-end");
  const celdaEstado = agregarCelda(fila, "");
  const estado = document.createElement("span");
  estado.className = `badge rounded-pill ${producto.activo ? "text-bg-success-subtle text-success-emphasis" : "text-bg-secondary-subtle text-secondary-emphasis"}`;
  estado.textContent = producto.activo ? "Activo" : "Inactivo";
  celdaEstado.append(estado);
  fila.append(document.createElement("td"));
  agregarBoton(fila, "Editar", "btn-outline-primary", () => editarProducto(producto));
  agregarBoton(fila, "Eliminar", "btn-outline-danger", () => borrarProducto(producto));
  fila.lastElementChild.classList.add("pe-3");
  return fila;
}

function agregarOpciones(selector, opciones, propiedadId) {
  for (const opcion of opciones) {
    selector.append(new Option(opcion.nombre, String(opcion[propiedadId])));
  }
}

async function cargarCatalogos() {
  const catalogos = await solicitar("/catalogos");
  agregarOpciones(selectorCategoria, catalogos.categorias, "id_categoria");
  agregarOpciones(selectorProveedor, catalogos.proveedores, "id_proveedor");
}

function actualizarResumenProductos() {
  document.querySelector("#kpi-productos").textContent = productosDisponibles.length;
  document.querySelector("#kpi-activos").textContent =
    productosDisponibles.filter((producto) => producto.activo).length;
  document.querySelector("#kpi-stock-bajo").textContent =
    productosDisponibles.filter(
      (producto) => producto.activo && producto.stock_actual <= producto.stock_minimo,
    ).length;
}

function mostrarProductosFiltrados() {
  const termino = busquedaProducto.value.trim().toLocaleLowerCase("es");
  const filtrados = productosDisponibles.filter((producto) =>
    [producto.nombre, producto.categoria, producto.proveedor]
      .some((campo) => campo.toLocaleLowerCase("es").includes(termino)),
  );
  listaProductos.replaceChildren();

  if (filtrados.length === 0) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = 10;
    celda.className = "text-center text-secondary py-5";
    celda.textContent = productosDisponibles.length
      ? "No hay productos que coincidan con la búsqueda."
      : "Todavía no hay productos en el catálogo.";
    fila.append(celda);
    listaProductos.append(fila);
  } else {
    listaProductos.append(...filtrados.map(crearFila));
  }

  totalProductos.textContent =
    `${filtrados.length} de ${productosDisponibles.length} productos`;
}

async function cargarProductos() {
  ocultarMensaje();
  try {
    productosDisponibles = await solicitar("/productos");
    actualizarResumenProductos();
    mostrarProductosFiltrados();
    mostrarEstadoApi("ok", "API conectado");
  } catch (error) {
    mostrarEstadoApi("error", "No se pudo conectar al API");
    mostrarMensaje(`No se pudieron cargar los productos: ${error.message}`);
    productosDisponibles = [];
    actualizarResumenProductos();
    mostrarProductosFiltrados();
  }
}

function editarProducto(producto) {
  idProductoEnEdicion = producto.id_producto;
  formulario.elements.nombre.value = producto.nombre;
  formulario.elements.id_categoria.value = producto.id_categoria;
  formulario.elements.id_proveedor.value = producto.id_proveedor;
  formulario.elements.unidad.value = producto.unidad;
  formulario.elements.precio_venta.value = producto.precio_venta;
  formulario.elements.stock_actual.value = producto.stock_actual;
  formulario.elements.stock_minimo.value = producto.stock_minimo;
  formulario.elements.activo.checked = producto.activo;
  document.querySelector("#titulo-formulario").textContent =
    `Editar producto #${producto.id_producto}`;
  document.querySelector("#guardar-producto").textContent = "Guardar cambios";
  document.querySelector("#cancelar-edicion").classList.remove("d-none");
  dialogoProducto.showModal();
}

function limpiarFormulario() {
  idProductoEnEdicion = null;
  formulario.reset();
  document.querySelector("#titulo-formulario").textContent = "Agregar producto";
  document.querySelector("#guardar-producto").textContent = "Guardar producto";
  document.querySelector("#cancelar-edicion").classList.add("d-none");
}

function datosDelFormulario() {
  return {
    nombre: formulario.elements.nombre.value.trim(),
    id_categoria: Number(formulario.elements.id_categoria.value),
    id_proveedor: Number(formulario.elements.id_proveedor.value),
    unidad: formulario.elements.unidad.value,
    precio_venta: Number(formulario.elements.precio_venta.value),
    stock_minimo: Number(formulario.elements.stock_minimo.value),
    activo: formulario.elements.activo.checked,
  };
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  ocultarMensaje();
  const esEdicion = idProductoEnEdicion !== null;
  const url = esEdicion ? `/productos/${idProductoEnEdicion}` : "/productos";
  try {
    await solicitar(url, {
      method: esEdicion ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datosDelFormulario()),
    });
    dialogoProducto.close();
    limpiarFormulario();
    await cargarProductos();
    mostrarMensaje(esEdicion ? "Producto actualizado." : "Producto creado.", "success");
  } catch (error) {
    mostrarMensaje(`No se pudo guardar el producto: ${error.message}`);
  }
});

async function borrarProducto(producto) {
  if (!confirm(`¿Eliminar "${producto.nombre}"? Esta acción no se puede deshacer.`)) {
    return;
  }
  ocultarMensaje();
  try {
    await solicitar(`/productos/${producto.id_producto}`, { method: "DELETE" });
    await cargarProductos();
    mostrarMensaje("Producto eliminado.", "success");
  } catch (error) {
    mostrarMensaje(`No se pudo eliminar el producto: ${error.message}`);
  }
}

document.querySelector("#abrir-formulario").addEventListener("click", () => {
  limpiarFormulario();
  dialogoProducto.showModal();
});
document.querySelector("#cerrar-dialogo").addEventListener("click", () => dialogoProducto.close());
document.querySelector("#cancelar-edicion").addEventListener("click", () => dialogoProducto.close());
dialogoProducto.addEventListener("close", limpiarFormulario);
busquedaProducto.addEventListener("input", mostrarProductosFiltrados);

async function iniciar() {
  try {
    await cargarCatalogos();
    await cargarProductos();
  } catch (error) {
    mostrarEstadoApi("error", "No se pudo conectar al API");
    mostrarMensaje(`No se pudieron cargar categorías y proveedores: ${error.message}`);
  }
}

iniciar();
