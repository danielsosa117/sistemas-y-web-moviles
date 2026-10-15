const lista = document.querySelector("#lista-proveedores");
const formulario = document.querySelector("#formulario-proveedor");
const dialogo = document.querySelector("#dialogo-proveedor");
const mensaje = document.querySelector("#mensaje");
const indicadorApi = document.querySelector("#api-indicator");
const busqueda = document.querySelector("#buscar-proveedor");
let proveedores = [];
let idEnEdicion = null;

async function solicitar(url, opciones = {}) {
  const respuesta = await fetch(url, opciones);
  if (!respuesta.ok) {
    const detalle = await respuesta.json().catch(() => null);
    throw new Error(detalle?.detail || `Error HTTP ${respuesta.status}`);
  }
  return respuesta.status === 204 ? null : respuesta.json();
}

function mostrarMensaje(texto, tipo = "danger") {
  mensaje.textContent = texto;
  mensaje.className = `alert alert-${tipo}`;
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
  return celda;
}

function agregarAccion(celda, texto, clase, accion) {
  const boton = document.createElement("button");
  boton.type = "button";
  boton.className = `btn btn-sm ${clase} me-1`;
  boton.textContent = texto;
  boton.addEventListener("click", accion);
  celda.append(boton);
}

function renderizar() {
  const termino = busqueda.value.trim().toLocaleLowerCase("es");
  const resultado = proveedores.filter((proveedor) =>
    [proveedor.nombre, proveedor.telefono || "", proveedor.email || ""]
      .some((campo) => campo.toLocaleLowerCase("es").includes(termino)),
  );
  lista.replaceChildren();
  if (!resultado.length) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = 5;
    celda.className = "text-center text-secondary py-5";
    celda.textContent = proveedores.length
      ? "No hay proveedores que coincidan con la búsqueda."
      : "Todavía no hay proveedores registrados.";
    fila.append(celda);
    lista.append(fila);
  } else {
    for (const proveedor of resultado) {
      const fila = document.createElement("tr");
      agregarCelda(fila, String(proveedor.id_proveedor), "ps-3 text-secondary");
      agregarCelda(fila, proveedor.nombre, "fw-medium");
      agregarCelda(fila, proveedor.telefono || "—");
      agregarCelda(fila, proveedor.email || "—");
      const acciones = agregarCelda(fila, "", "pe-3");
      agregarAccion(acciones, "Editar", "btn-outline-primary", () => editar(proveedor));
      agregarAccion(acciones, "Eliminar", "btn-outline-danger", () => eliminar(proveedor));
      lista.append(fila);
    }
  }
  document.querySelector("#total-proveedores").textContent =
    `${resultado.length} de ${proveedores.length} proveedores`;
}

async function cargar() {
  try {
    proveedores = await solicitar("/proveedores");
    renderizar();
    mostrarEstadoApi("ok", "API conectado");
    return true;
  } catch (error) {
    mostrarEstadoApi("error", "No se pudo conectar al API");
    mostrarMensaje(`No se pudieron cargar los proveedores: ${error.message}`);
    return false;
  }
}

function limpiarFormulario() {
  idEnEdicion = null;
  formulario.reset();
  document.querySelector("#titulo-formulario").textContent = "Agregar proveedor";
  document.querySelector("#guardar-proveedor").textContent = "Guardar proveedor";
  document.querySelector("#cancelar-edicion").classList.add("d-none");
}

function abrirNuevo() {
  limpiarFormulario();
  dialogo.showModal();
}

function editar(proveedor) {
  idEnEdicion = proveedor.id_proveedor;
  formulario.elements.nombre.value = proveedor.nombre;
  formulario.elements.telefono.value = proveedor.telefono || "";
  formulario.elements.email.value = proveedor.email || "";
  document.querySelector("#titulo-formulario").textContent =
    `Editar proveedor #${proveedor.id_proveedor}`;
  document.querySelector("#guardar-proveedor").textContent = "Guardar cambios";
  document.querySelector("#cancelar-edicion").classList.remove("d-none");
  dialogo.showModal();
}

function datosFormulario() {
  return {
    nombre: formulario.elements.nombre.value.trim(),
    telefono: formulario.elements.telefono.value.trim() || null,
    email: formulario.elements.email.value.trim() || null,
  };
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const editando = idEnEdicion !== null;
  const url = editando ? `/proveedores/${idEnEdicion}` : "/proveedores";
  try {
    await solicitar(url, {
      method: editando ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datosFormulario()),
    });
    dialogo.close();
    limpiarFormulario();
    if (!(await cargar())) return;
    mostrarMensaje(editando ? "Proveedor actualizado." : "Proveedor creado.", "success");
  } catch (error) {
    mostrarMensaje(`No se pudo guardar el proveedor: ${error.message}`);
  }
});

async function eliminar(proveedor) {
  if (!confirm(`¿Eliminar el proveedor "${proveedor.nombre}"?`)) return;
  try {
    await solicitar(`/proveedores/${proveedor.id_proveedor}`, { method: "DELETE" });
    if (!(await cargar())) return;
    mostrarMensaje("Proveedor eliminado.", "success");
  } catch (error) {
    mostrarMensaje(`No se pudo eliminar el proveedor: ${error.message}`);
  }
}

document.querySelector("#abrir-formulario").addEventListener("click", abrirNuevo);
document.querySelector("#cerrar-dialogo").addEventListener("click", () => dialogo.close());
document.querySelector("#cancelar-edicion").addEventListener("click", () => dialogo.close());
dialogo.addEventListener("close", limpiarFormulario);
busqueda.addEventListener("input", renderizar);
cargar();
