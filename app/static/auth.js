// Sesión del usuario: agrega el token a cada petición, redirige al login
// cuando falta o venció, y muestra el usuario con el botón de cerrar sesión.
(() => {
  "use strict";

  const CLAVE_TOKEN = "catalogo_token";
  const RUTA_LOGIN = "/login-ui";
  const RUTA_CAMBIAR_PASSWORD = "/cambiar-password-ui";
  const ROL_ADMIN = "ADMINISTRADOR";
  const fetchOriginal = window.fetch.bind(window);

  const obtenerToken = () => localStorage.getItem(CLAVE_TOKEN);

  function irAlLogin() {
    localStorage.removeItem(CLAVE_TOKEN);
    if (location.pathname !== RUTA_LOGIN) location.replace(RUTA_LOGIN);
  }

  window.fetch = async (entrada, opciones = {}) => {
    const direccion = new URL(
      typeof entrada === "string" ? entrada : entrada.url,
      location.origin,
    );
    const esPropia = direccion.origin === location.origin;
    const esLogin = direccion.pathname === "/auth/login";
    const token = obtenerToken();

    if (esPropia && !esLogin && token) {
      const cabeceras = new Headers(opciones.headers || {});
      cabeceras.set("Authorization", `Bearer ${token}`);
      opciones = { ...opciones, headers: cabeceras };
    }

    const respuesta = await fetchOriginal(entrada, opciones);
    if (esPropia && !esLogin && respuesta.status === 401) irAlLogin();
    return respuesta;
  };

  function cerrarSesion() {
    localStorage.removeItem(CLAVE_TOKEN);
    location.replace(RUTA_LOGIN);
  }

  async function mostrarSesion() {
    const menu = document.querySelector(".navbar-nav");
    if (!obtenerToken()) return;

    const respuesta = await fetch("/auth/yo");
    if (!respuesta.ok) return;
    const usuario = await respuesta.json();
    document.body.dataset.rol = usuario.rol;

    if (
      usuario.requiere_cambio_password
      && location.pathname !== RUTA_CAMBIAR_PASSWORD
    ) {
      location.replace(RUTA_CAMBIAR_PASSWORD);
      return;
    }
    if (!menu) return;

    if (usuario.rol !== ROL_ADMIN) {
      menu
        .querySelectorAll('a[href="/usuarios-ui"], a[href="/roles-ui"]')
        .forEach((enlace) => enlace.remove());
    }

    const menuAgente = document.createElement("details");
    menuAgente.className = "user-menu";
    const disparador = document.createElement("summary");
    disparador.className = "user-menu-trigger";
    disparador.setAttribute("aria-label", "Abrir menú del agente");
    disparador.title = "Menú del agente";
    const icono = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    icono.setAttribute("viewBox", "0 0 24 24");
    icono.setAttribute("aria-hidden", "true");
    icono.setAttribute("fill", "none");
    icono.setAttribute("stroke", "currentColor");
    icono.setAttribute("stroke-width", "1.8");
    icono.setAttribute("stroke-linecap", "round");
    icono.setAttribute("stroke-linejoin", "round");
    const cabeza = document.createElementNS("http://www.w3.org/2000/svg", "circle");
    cabeza.setAttribute("cx", "12");
    cabeza.setAttribute("cy", "8");
    cabeza.setAttribute("r", "3.5");
    const cuerpo = document.createElementNS("http://www.w3.org/2000/svg", "path");
    cuerpo.setAttribute("d", "M4.5 20c.7-3.8 3.2-6 7.5-6s6.8 2.2 7.5 6");
    icono.append(cabeza, cuerpo);
    disparador.append(icono);

    const panel = document.createElement("div");
    panel.className = "user-menu-panel";
    const informacion = document.createElement("div");
    informacion.className = "user-menu-information";
    const titulo = document.createElement("span");
    titulo.className = "user-menu-eyebrow";
    titulo.textContent = "Agente conectado";
    const nombre = document.createElement("strong");
    nombre.className = "user-menu-name";
    nombre.textContent = usuario.nombre;
    const correo = document.createElement("span");
    correo.className = "user-menu-email";
    correo.textContent = usuario.email;
    const rol = document.createElement("span");
    rol.className = "user-menu-role";
    rol.textContent = usuario.rol;
    informacion.append(titulo, nombre, correo, rol);

    const cambiarPassword = document.createElement("a");
    cambiarPassword.className = "user-menu-action";
    cambiarPassword.href = RUTA_CAMBIAR_PASSWORD;
    cambiarPassword.textContent = "Cambiar contraseña";
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "user-menu-action user-menu-logout";
    boton.textContent = "Cerrar sesión";
    boton.addEventListener("click", cerrarSesion);

    panel.append(informacion, cambiarPassword, boton);
    menuAgente.append(disparador, panel);
    document.addEventListener("click", (evento) => {
      if (!menuAgente.contains(evento.target)) menuAgente.open = false;
    });
    menu.append(menuAgente);
  }

  if (!obtenerToken()) {
    irAlLogin();
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mostrarSesion);
  } else {
    mostrarSesion();
  }
})();
