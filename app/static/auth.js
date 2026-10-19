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

    const caja = document.createElement("span");
    caja.className = "navbar-text ms-3 d-flex align-items-center gap-2";
    const nombre = document.createElement("small");
    nombre.textContent = `${usuario.nombre} · ${usuario.rol}`;
    const cambiarPassword = document.createElement("a");
    cambiarPassword.className = "btn btn-sm btn-outline-secondary";
    cambiarPassword.href = RUTA_CAMBIAR_PASSWORD;
    cambiarPassword.textContent = "Cambiar contraseña";
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "btn btn-sm btn-outline-secondary";
    boton.textContent = "Cerrar sesión";
    boton.addEventListener("click", cerrarSesion);
    caja.append(nombre, cambiarPassword, boton);
    menu.append(caja);
  }

  if (!obtenerToken()) {
    irAlLogin();
  } else if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", mostrarSesion);
  } else {
    mostrarSesion();
  }
})();
