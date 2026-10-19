const formulario = document.querySelector("#formulario-recuperar");
const mensaje = document.querySelector("#mensaje");
const boton = document.querySelector("#boton-recuperar");

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
    const respuesta = await fetch("/auth/recuperar-password", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: formulario.elements.email.value.trim(),
        password_nueva: passwordNueva,
      }),
    });
    if (!respuesta.ok) {
      const datos = await respuesta.json().catch(() => null);
      throw new Error(datos?.detail || `Error HTTP ${respuesta.status}`);
    }
    mostrarMensaje(
      "Si la cuenta existe y está activa, la contraseña quedó actualizada. Ya puedes iniciar sesión.",
      "success",
    );
    formulario.reset();
  } catch (error) {
    mostrarMensaje(error.message);
  } finally {
    boton.disabled = false;
  }
});
