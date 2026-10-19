const formulario = document.querySelector("#formulario-password");
const mensaje = document.querySelector("#mensaje");
const boton = document.querySelector("#boton-password");

function mostrarMensaje(texto, tipo = "danger") {
  mensaje.textContent = texto;
  mensaje.className = `alert alert-${tipo}`;
}

formulario.addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const passwordNueva = formulario.elements.password_nueva.value;
  if (passwordNueva !== formulario.elements.confirmar_password.value) {
    mostrarMensaje("Las contraseñas nuevas no coinciden.", "warning");
    return;
  }

  boton.disabled = true;
  try {
    const respuesta = await fetch("/auth/password", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        password_actual: formulario.elements.password_actual.value,
        password_nueva: passwordNueva,
      }),
    });
    if (!respuesta.ok) {
      const datos = await respuesta.json().catch(() => null);
      throw new Error(datos?.detail || `Error HTTP ${respuesta.status}`);
    }
    location.replace("/");
  } catch (error) {
    mostrarMensaje(error.message);
    boton.disabled = false;
  }
});
