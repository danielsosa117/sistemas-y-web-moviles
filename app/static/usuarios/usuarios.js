const lista = document.querySelector("#lista-usuarios");
const formulario = document.querySelector("#formulario-usuario");
const dialogo = document.querySelector("#dialogo-usuario");
const mensaje = document.querySelector("#mensaje");
const indicadorApi = document.querySelector("#api-indicator");
const busqueda = document.querySelector("#buscar-usuario");
const filtroEstado = document.querySelector("#filtro-estado");
let usuarios = [];
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

function agregarCelda(fila, texto, clase = "") {
  const celda = document.createElement("td");
  celda.textContent = texto;
  if (clase) celda.className = clase;
  fila.append(celda);
  return celda;
}

function renderizar() {
  const termino = busqueda.value.trim().toLocaleLowerCase("es");
  const estado = filtroEstado.value;
  const resultado = usuarios.filter((usuario) => {
    const coincideBusqueda = [usuario.nombre, usuario.email, usuario.rol]
      .some((campo) => campo.toLocaleLowerCase("es").includes(termino));
    const coincideEstado = !estado || (usuario.activo ? "activo" : "inactivo") === estado;
    return coincideBusqueda && coincideEstado;
  });

  lista.replaceChildren();
  if (!resultado.length) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = 6;
    celda.className = "text-center text-secondary py-5";
    celda.textContent = usuarios.length
      ? "No hay usuarios que coincidan con los filtros."
      : "Todavía no hay usuarios registrados.";
    fila.append(celda);
    lista.append(fila);
  } else {
    for (const usuario of resultado) {
      const fila = document.createElement("tr");
      agregarCelda(fila, String(usuario.id_usuario), "ps-3 text-secondary");
      agregarCelda(fila, usuario.nombre, "fw-medium");
      agregarCelda(fila, usuario.email);
      agregarCelda(fila, usuario.rol);
      const estadoCelda = agregarCelda(fila, "");
      const insignia = document.createElement("span");
      insignia.className = `badge rounded-pill ${usuario.activo ? "text-bg-success" : "text-bg-secondary"}`;
      insignia.textContent = usuario.activo ? "Activo" : "Inactivo";
      estadoCelda.append(insignia);
      const acciones = agregarCelda(fila, "", "pe-3");
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "btn btn-sm btn-outline-primary";
      boton.textContent = "Editar";
      boton.addEventListener("click", () => editar(usuario));
      acciones.append(boton);
      lista.append(fila);
    }
  }

  document.querySelector("#total-usuarios").textContent =
    `${resultado.length} de ${usuarios.length} usuarios`;
  document.querySelector("#kpi-usuarios").textContent = String(usuarios.length);
  document.querySelector("#kpi-activos").textContent =
    String(usuarios.filter((usuario) => usuario.activo).length);
}

async function cargar() {
  try {
    const [usuariosCargados, rolesCargados] = await Promise.all([
      solicitar("/usuarios"),
      solicitar("/roles"),
    ]);
    usuarios = usuariosCargados;
    roles = rolesCargados;
    renderizar();
    mostrarEstadoApi("ok", "API conectado");
    return true;
  } catch (error) {
    mostrarEstadoApi("error", "No se pudo conectar al API");
    mostrarMensaje(`No se pudieron cargar los usuarios: ${error.message}`);
    return false;
  }
}

function editar(usuario) {
  idEnEdicion = usuario.id_usuario;
  formulario.elements.nombre.value = usuario.nombre;
  formulario.elements.email.value = usuario.email;
  formulario.elements.id_rol.replaceChildren();
  for (const rol of roles) {
    const opcion = document.createElement("option");
    opcion.value = String(rol.id_rol);
    opcion.textContent = rol.nombre;
    formulario.elements.id_rol.append(opcion);
  }
  formulario.elements.id_rol.value = String(usuario.id_rol);
  formulario.elements.activo.checked = usuario.activo;
  document.querySelector("#titulo-formulario").textContent =
    `Editar usuario #${usuario.id_usuario}`;
  dialogo.showModal();
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  if (idEnEdicion === null) return;
  const datos = {
    nombre: formulario.elements.nombre.value.trim(),
    email: formulario.elements.email.value.trim(),
    id_rol: Number(formulario.elements.id_rol.value),
    activo: formulario.elements.activo.checked,
  };
  try {
    await solicitar(`/usuarios/${idEnEdicion}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(datos),
    });
    dialogo.close();
    if (!(await cargar())) return;
    mostrarMensaje("Usuario actualizado.", "success");
  } catch (error) {
    mostrarMensaje(`No se pudo actualizar el usuario: ${error.message}`);
  }
});

document.querySelector("#cerrar-dialogo").addEventListener("click", () => dialogo.close());
document.querySelector("#cancelar-edicion").addEventListener("click", () => dialogo.close());
busqueda.addEventListener("input", renderizar);
filtroEstado.addEventListener("change", renderizar);
cargar();
