const mensaje = document.querySelector("#mensaje");
const indicadorApi = document.querySelector("#api-indicator");
const listaMovimientos = document.querySelector("#lista-movimientos");
const formularioMovimiento = document.querySelector("#formulario-movimiento");
const selectorProducto = document.querySelector("#producto-movimiento");
const selectorUsuario = document.querySelector("#usuario-movimiento");
const tipoMovimiento = document.querySelector("#tipo-movimiento");
const cantidadMovimiento = document.querySelector("#cantidad-movimiento");
const disponibilidadMovimiento = document.querySelector("#disponibilidad-movimiento");
const movimientoBloqueado = document.querySelector("#movimiento-bloqueado");
const dialogoMovimiento = document.querySelector("#dialogo-movimiento");
const formatoCantidad = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 3 });

let productos = [];
let movimientos = [];
let movimientoEnEdicion = null;

function mostrarMensaje(texto, tipo = "danger") {
  mensaje.textContent = texto;
  mensaje.className = `alert alert-${tipo}`;
}

function ocultarMensaje() {
  mensaje.textContent = "";
  mensaje.className = "alert d-none";
}

function mostrarEstadoApi(estado, texto) {
  indicadorApi.className = `api-indicator api-indicator-${estado}`;
  indicadorApi.lastElementChild.textContent = texto;
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

async function cargarDatosIniciales() {
  const [catalogos, productosCargados] = await Promise.all([
    solicitar("/catalogos"),
    solicitar("/productos"),
  ]);
  productos = productosCargados;
  for (const usuario of catalogos.usuarios) {
    selectorUsuario.append(new Option(usuario.nombre, String(usuario.id_usuario)));
  }
}

function crearFila(movimiento) {
  const fila = document.createElement("tr");
  const fecha = new Date(movimiento.fecha.replace(" ", "T"));
  const fechaTexto = Number.isNaN(fecha.getTime())
    ? movimiento.fecha
    : fecha.toLocaleString("es-CO");
  agregarCelda(fila, fechaTexto, "ps-3 text-secondary");

  const celdaTipo = agregarCelda(fila, "");
  const etiquetaTipo = document.createElement("span");
  etiquetaTipo.className = `badge rounded-pill ${movimiento.tipo === "ENTRADA" ? "text-bg-success-subtle text-success-emphasis" : "text-bg-primary-subtle text-primary-emphasis"}`;
  etiquetaTipo.textContent = movimiento.tipo === "ENTRADA" ? "Ingreso" : "Venta / salida";
  celdaTipo.append(etiquetaTipo);
  agregarCelda(fila, movimiento.producto, "fw-medium");
  agregarCelda(
    fila,
    `${formatoCantidad.format(movimiento.cantidad)} ${movimiento.unidad}`,
    "text-end",
  );
  agregarCelda(fila, movimiento.usuario);
  agregarCelda(fila, movimiento.observacion || "—");
  fila.append(document.createElement("td"));
  const boton = document.createElement("button");
  boton.type = "button";
  boton.textContent = "Editar";
  boton.className = "btn btn-sm btn-outline-secondary";
  boton.addEventListener("click", () => editarMovimiento(movimiento));
  fila.lastElementChild.append(boton);
  fila.lastElementChild.classList.add("pe-3");
  return fila;
}

function agregarCelda(fila, texto, clase = "") {
  const celda = document.createElement("td");
  celda.textContent = texto;
  if (clase) celda.className = clase;
  fila.append(celda);
  return celda;
}

function renderizarMovimientos() {
  const termino = document.querySelector("#buscar-movimiento")
    .value.trim().toLocaleLowerCase("es");
  const tipoFiltro = document.querySelector("#filtro-tipo").value;
  const filtrados = movimientos.filter((movimiento) => {
    const coincideTipo = !tipoFiltro || movimiento.tipo === tipoFiltro;
    const texto = [
      movimiento.producto,
      movimiento.usuario,
      movimiento.observacion || "",
    ].join(" ").toLocaleLowerCase("es");
    return coincideTipo && texto.includes(termino);
  });

  listaMovimientos.replaceChildren();
  if (!filtrados.length) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = 7;
    celda.className = "text-center text-secondary py-5";
    celda.textContent = movimientos.length
      ? "No hay movimientos que coincidan con los filtros."
      : "Todavía no hay movimientos registrados.";
    fila.append(celda);
    listaMovimientos.append(fila);
  } else {
    listaMovimientos.append(...filtrados.map(crearFila));
  }
  document.querySelector("#total-movimientos").textContent =
    `${filtrados.length} de ${movimientos.length} movimientos`;
}

function actualizarResumen() {
  document.querySelector("#kpi-movimientos").textContent = movimientos.length;
  document.querySelector("#kpi-ingresos").textContent =
    movimientos.filter((movimiento) => movimiento.tipo === "ENTRADA").length;
  document.querySelector("#kpi-salidas").textContent =
    movimientos.filter((movimiento) => movimiento.tipo === "SALIDA").length;
}

async function cargarMovimientos() {
  movimientos = await solicitar("/movimientos");
  actualizarResumen();
  renderizarMovimientos();
}

function obtenerProductoSeleccionado() {
  return productos.find(
    (producto) => producto.id_producto === Number(selectorProducto.value),
  );
}

function actualizarRestriccionesCantidad() {
  const producto = obtenerProductoSeleccionado();
  cantidadMovimiento.setCustomValidity("");
  cantidadMovimiento.removeAttribute("max");
  disponibilidadMovimiento.textContent = "";
  if (!producto) return;

  const esUnidad = producto.unidad === "UND";
  const minimo = esUnidad ? 1 : 0.001;
  cantidadMovimiento.min = String(minimo);
  cantidadMovimiento.step = esUnidad ? "1" : "0.001";
  if (movimientoEnEdicion?.tipo === "ENTRADA") {
    cantidadMovimiento.min = String(
      Math.max(minimo, movimientoEnEdicion.cantidad - producto.stock_actual),
    );
    disponibilidadMovimiento.textContent =
      "Reducir la entrada no puede dejar existencias negativas.";
  } else if (tipoMovimiento.value === "SALIDA") {
    const disponible = producto.stock_actual +
      (movimientoEnEdicion?.tipo === "SALIDA" ? movimientoEnEdicion.cantidad : 0);
    cantidadMovimiento.max = String(disponible);
    disponibilidadMovimiento.textContent =
      `Disponible para esta operación: ${formatoCantidad.format(disponible)} ${producto.unidad}.`;
  }

  const cantidad = Number(cantidadMovimiento.value);
  if (cantidadMovimiento.value && esUnidad && !Number.isInteger(cantidad)) {
    cantidadMovimiento.setCustomValidity("La cantidad debe ser entera para productos UND.");
  } else if (
    cantidadMovimiento.value &&
    tipoMovimiento.value === "SALIDA" &&
    cantidad > Number(cantidadMovimiento.max || producto.stock_actual)
  ) {
    cantidadMovimiento.setCustomValidity(
      `Stock insuficiente. Disponible: ${formatoCantidad.format(Number(cantidadMovimiento.max || producto.stock_actual))}.`,
    );
  } else if (
    cantidadMovimiento.value &&
    movimientoEnEdicion?.tipo === "ENTRADA" &&
    cantidad < Number(cantidadMovimiento.min)
  ) {
    cantidadMovimiento.setCustomValidity(
      "La reducción no puede dejar el stock actual en negativo.",
    );
  }
}

function abrirMovimiento(tipo) {
  formularioMovimiento.reset();
  movimientoEnEdicion = null;
  selectorProducto.disabled = false;
  movimientoBloqueado.classList.add("d-none");
  tipoMovimiento.value = tipo;
  const disponibles = productos.filter(
    (producto) => producto.activo && (tipo === "ENTRADA" || producto.stock_actual > 0),
  );
  selectorProducto.replaceChildren(
    new Option("Selecciona un producto", ""),
    ...disponibles.map((producto) => new Option(
      `${producto.nombre} (${producto.stock_actual} ${producto.unidad} disponibles)`,
      String(producto.id_producto),
    )),
  );
  document.querySelector("#titulo-movimiento").textContent =
    tipo === "ENTRADA" ? "Registrar ingreso" : "Registrar venta / salida";
  document.querySelector("#guardar-movimiento").textContent = "Registrar";
  actualizarRestriccionesCantidad();
  dialogoMovimiento.showModal();
}

function editarMovimiento(movimiento) {
  formularioMovimiento.reset();
  movimientoEnEdicion = movimiento;
  tipoMovimiento.value = movimiento.tipo;
  selectorProducto.replaceChildren(
    new Option(
      `${movimiento.producto} (${movimiento.unidad})`,
      String(movimiento.id_producto),
      true,
      true,
    ),
  );
  selectorProducto.disabled = true;
  selectorUsuario.value = String(movimiento.id_usuario);
  cantidadMovimiento.value = movimiento.cantidad;
  formularioMovimiento.elements.observacion.value = movimiento.observacion || "";
  movimientoBloqueado.textContent =
    `Solo puedes modificar cantidad, usuario y observación. Tipo: ${movimiento.tipo === "ENTRADA" ? "Ingreso" : "Venta / salida"}.`;
  movimientoBloqueado.classList.remove("d-none");
  document.querySelector("#titulo-movimiento").textContent = "Editar movimiento";
  document.querySelector("#guardar-movimiento").textContent = "Guardar cambios";
  actualizarRestriccionesCantidad();
  dialogoMovimiento.showModal();
}

formularioMovimiento.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  actualizarRestriccionesCantidad();
  if (!formularioMovimiento.reportValidity()) return;

  ocultarMensaje();
  const esEdicion = movimientoEnEdicion !== null;
  const tipoOperacion = tipoMovimiento.value;
  const cambios = {
    cantidad: Number(cantidadMovimiento.value),
    id_usuario: Number(selectorUsuario.value),
    observacion: formularioMovimiento.elements.observacion.value.trim() || null,
  };
  const payload = esEdicion
    ? cambios
    : {
        ...cambios,
        id_producto: Number(selectorProducto.value),
        tipo: tipoOperacion,
      };

  try {
    await solicitar(
      esEdicion ? `/movimientos/${movimientoEnEdicion.id_movimiento}` : "/movimientos",
      {
        method: esEdicion ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    dialogoMovimiento.close();
    await Promise.all([cargarMovimientos(), cargarProductos()]);
    mostrarEstadoApi("ok", "API conectado");
    mostrarMensaje(
      esEdicion
        ? "Movimiento actualizado."
        : tipoOperacion === "ENTRADA"
          ? "Ingreso registrado."
          : "Venta / salida registrada.",
      "success",
    );
  } catch (error) {
    mostrarEstadoApi("error", "Error de comunicación");
    mostrarMensaje(
      `${esEdicion ? "No se pudo actualizar" : "No se pudo registrar"} el movimiento: ${error.message}`,
    );
  }
});

selectorProducto.addEventListener("change", actualizarRestriccionesCantidad);
cantidadMovimiento.addEventListener("input", actualizarRestriccionesCantidad);
document.querySelector("#abrir-ingreso").addEventListener("click", () => abrirMovimiento("ENTRADA"));
document.querySelector("#abrir-salida").addEventListener("click", () => abrirMovimiento("SALIDA"));
document.querySelector("#cerrar-movimiento").addEventListener("click", () => dialogoMovimiento.close());
document.querySelector("#cancelar-movimiento").addEventListener("click", () => dialogoMovimiento.close());
document.querySelector("#buscar-movimiento").addEventListener("input", renderizarMovimientos);
document.querySelector("#filtro-tipo").addEventListener("change", renderizarMovimientos);
dialogoMovimiento.addEventListener("close", () => {
  movimientoEnEdicion = null;
  formularioMovimiento.reset();
  selectorProducto.disabled = false;
  movimientoBloqueado.classList.add("d-none");
  disponibilidadMovimiento.textContent = "";
});

async function iniciar() {
  try {
    await cargarDatosIniciales();
    await Promise.all([cargarMovimientos(), cargarProductos()]);
    mostrarEstadoApi("ok", "API conectado");
  } catch (error) {
    mostrarEstadoApi("error", "No se pudo conectar al API");
    mostrarMensaje(`No se pudieron cargar los datos: ${error.message}`);
  }
}

async function cargarProductos() {
  productos = await solicitar("/productos");
}

iniciar();
