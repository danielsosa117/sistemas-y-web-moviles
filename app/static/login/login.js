const CLAVE_TOKEN = "catalogo_token";
const formulario = document.querySelector("#formulario-login");
const mensaje = document.querySelector("#mensaje");
const botonLogin = document.querySelector("#boton-login");

function mostrarMensaje(texto, tipo = "danger") {
  mensaje.textContent = texto;
  mensaje.className = `alert alert-${tipo}`;
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  mensaje.className = "alert d-none";

  const email = formulario.elements.email.value.trim();
  const password = formulario.elements.password.value;
  if (!email || !password) {
    mostrarMensaje("Escribe tu correo y tu contraseña.", "warning");
    return;
  }

  botonLogin.disabled = true;
  try {
    const respuesta = await fetch("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const datos = await respuesta.json().catch(() => null);
    if (!respuesta.ok) {
      const detalle = typeof datos?.detail === "string" ? datos.detail : null;
      throw new Error(detalle || "No se pudo iniciar sesión. Revisa los datos.");
    }
    localStorage.setItem(CLAVE_TOKEN, datos.access_token);
    location.replace("/");
  } catch (error) {
    mostrarMensaje(error.message);
    botonLogin.disabled = false;
  }
});
