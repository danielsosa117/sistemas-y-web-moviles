const lista = document.querySelector("#lista-categorias");
const formulario = document.querySelector("#formulario-categoria");
const dialogo = document.querySelector("#dialogo-categoria");
const mensaje = document.querySelector("#mensaje");
const indicadorApi = document.querySelector("#api-indicator");
const busqueda = document.querySelector("#buscar-categoria");
let categorias = [];
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
  const resultado = categorias.filter((categoria) =>
    categoria.nombre.toLocaleLowerCase("es").includes(termino),
  );
  lista.replaceChildren();
  if (!resultado.length) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = 3;
    celda.className = "text-center text-secondary py-5";
    celda.textContent = categorias.length
      ? "No hay categorías que coincidan con la búsqueda."
      : "Todavía no hay categorías registradas.";
    fila.append(celda);
    lista.append(fila);
  } else {
    for (const categoria of resultado) {
      const fila = document.createElement("tr");
      const id = document.createElement("td");
      id.className = "ps-3 text-secondary";
      id.textContent = categoria.id_categoria;
      const nombre = document.createElement("td");
      nombre.className = "fw-medium";
      nombre.textContent = categoria.nombre;
      const acciones = document.createElement("td");
      acciones.className = "pe-3";
      agregarAccion(acciones, "Editar", "btn-outline-primary", () => editar(categoria));
      agregarAccion(acciones, "Eliminar", "btn-outline-danger", () => eliminar(categoria));
      fila.append(id, nombre, acciones);
      lista.append(fila);
    }
  }
  document.querySelector("#total-categorias").textContent =
    `${resultado.length} de ${categorias.length} categorías`;
}

async function cargar() {
  try {
    categorias = await solicitar("/categorias");
    renderizar();
    mostrarEstadoApi("ok", "API conectado");
    return true;
  } catch (error) {
    mostrarEstadoApi("error", "No se pudo conectar al API");
    mostrarMensaje(`No se pudieron cargar las categorías: ${error.message}`);
    return false;
  }
}

function abrirNueva() {
  idEnEdicion = null;
  formulario.reset();
  document.querySelector("#titulo-formulario").textContent = "Agregar categoría";
  document.querySelector("#guardar-categoria").textContent = "Guardar categoría";
  document.querySelector("#cancelar-edicion").classList.add("d-none");
  dialogo.showModal();
}

function editar(categoria) {
  idEnEdicion = categoria.id_categoria;
  formulario.elements.nombre.value = categoria.nombre;
  document.querySelector("#titulo-formulario").textContent =
    `Editar categoría #${categoria.id_categoria}`;
  document.querySelector("#guardar-categoria").textContent = "Guardar cambios";
  document.querySelector("#cancelar-edicion").classList.remove("d-none");
  dialogo.showModal();
}

function cerrarFormulario() {
  dialogo.close();
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const editando = idEnEdicion !== null;
  const url = editando ? `/categorias/${idEnEdicion}` : "/categorias";
  try {
    await solicitar(url, {
      method: editando ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre: formulario.elements.nombre.value.trim() }),
    });
    cerrarFormulario();
    if (!(await cargar())) return;
    mostrarMensaje(editando ? "Categoría actualizada." : "Categoría creada.", "success");
  } catch (error) {
    mostrarMensaje(`No se pudo guardar la categoría: ${error.message}`);
  }
});

async function eliminar(categoria) {
  if (!confirm(`¿Eliminar la categoría "${categoria.nombre}"?`)) return;
  try {
    await solicitar(`/categorias/${categoria.id_categoria}`, { method: "DELETE" });
    if (!(await cargar())) return;
    mostrarMensaje("Categoría eliminada.", "success");
  } catch (error) {
    mostrarMensaje(`No se pudo eliminar la categoría: ${error.message}`);
  }
}

document.querySelector("#abrir-formulario").addEventListener("click", abrirNueva);
document.querySelector("#cerrar-dialogo").addEventListener("click", cerrarFormulario);
document.querySelector("#cancelar-edicion").addEventListener("click", cerrarFormulario);
dialogo.addEventListener("close", () => {
  idEnEdicion = null;
  formulario.reset();
});
busqueda.addEventListener("input", renderizar);
cargar();
