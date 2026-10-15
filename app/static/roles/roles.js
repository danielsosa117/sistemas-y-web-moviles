const lista = document.querySelector("#lista-roles");
const formulario = document.querySelector("#formulario-rol");
const dialogo = document.querySelector("#dialogo-rol");
const mensaje = document.querySelector("#mensaje");
const indicadorApi = document.querySelector("#api-indicator");
const busqueda = document.querySelector("#buscar-rol");
let roles = [];
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
  const resultado = roles.filter((rol) =>
    rol.nombre.toLocaleLowerCase("es").includes(termino),
  );
  lista.replaceChildren();
  if (!resultado.length) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = 3;
    celda.className = "text-center text-secondary py-5";
    celda.textContent = roles.length
      ? "No hay roles que coincidan con la búsqueda."
      : "Todavía no hay roles registrados.";
    fila.append(celda);
    lista.append(fila);
  } else {
    for (const rol of resultado) {
      const fila = document.createElement("tr");
      const id = document.createElement("td");
      id.className = "ps-3 text-secondary";
      id.textContent = String(rol.id_rol);
      const nombre = document.createElement("td");
      nombre.className = "fw-medium";
      nombre.textContent = rol.nombre;
      const acciones = document.createElement("td");
      acciones.className = "pe-3";
      agregarAccion(acciones, "Editar", "btn-outline-primary", () => editar(rol));
      agregarAccion(acciones, "Eliminar", "btn-outline-danger", () => eliminar(rol));
      fila.append(id, nombre, acciones);
      lista.append(fila);
    }
  }
  document.querySelector("#total-roles").textContent =
    `${resultado.length} de ${roles.length} roles`;
}

async function cargar() {
  try {
    roles = await solicitar("/roles");
    renderizar();
    mostrarEstadoApi("ok", "API conectado");
    return true;
  } catch (error) {
    mostrarEstadoApi("error", "No se pudo conectar al API");
    mostrarMensaje(`No se pudieron cargar los roles: ${error.message}`);
    return false;
  }
}

function abrirNuevo() {
  idEnEdicion = null;
  formulario.reset();
  document.querySelector("#titulo-formulario").textContent = "Agregar rol";
  document.querySelector("#guardar-rol").textContent = "Guardar rol";
  document.querySelector("#cancelar-edicion").classList.add("d-none");
  dialogo.showModal();
}

function editar(rol) {
  idEnEdicion = rol.id_rol;
  formulario.elements.nombre.value = rol.nombre;
  document.querySelector("#titulo-formulario").textContent = `Editar rol #${rol.id_rol}`;
  document.querySelector("#guardar-rol").textContent = "Guardar cambios";
  document.querySelector("#cancelar-edicion").classList.remove("d-none");
  dialogo.showModal();
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const editando = idEnEdicion !== null;
  const url = editando ? `/roles/${idEnEdicion}` : "/roles";
  try {
    await solicitar(url, {
      method: editando ? "PUT" : "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ nombre: formulario.elements.nombre.value.trim() }),
    });
    dialogo.close();
    if (!(await cargar())) return;
    mostrarMensaje(editando ? "Rol actualizado." : "Rol creado.", "success");
  } catch (error) {
    mostrarMensaje(`No se pudo guardar el rol: ${error.message}`);
  }
});

async function eliminar(rol) {
  if (!confirm(`¿Eliminar el rol "${rol.nombre}"?`)) return;
  try {
    await solicitar(`/roles/${rol.id_rol}`, { method: "DELETE" });
    if (!(await cargar())) return;
    mostrarMensaje("Rol eliminado.", "success");
  } catch (error) {
    mostrarMensaje(`No se pudo eliminar el rol: ${error.message}`);
  }
}

document.querySelector("#abrir-formulario").addEventListener("click", abrirNuevo);
document.querySelector("#cerrar-dialogo").addEventListener("click", () => dialogo.close());
document.querySelector("#cancelar-edicion").addEventListener("click", () => dialogo.close());
dialogo.addEventListener("close", () => {
  idEnEdicion = null;
  formulario.reset();
});
busqueda.addEventListener("input", renderizar);
cargar();
