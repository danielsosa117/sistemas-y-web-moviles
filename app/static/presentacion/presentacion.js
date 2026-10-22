(() => {
  "use strict";

  const diapositivas = [...document.querySelectorAll(".slide")];
  const progreso = document.querySelector("#progreso");
  const barraProgreso = document.querySelector(".slide-progress");
  const contador = document.querySelector("#contador");
  const botonAnterior = document.querySelector("#anterior");
  const botonSiguiente = document.querySelector("#siguiente");
  const botonPantallaCompleta = document.querySelector("#pantalla-completa");
  let indiceActual = 0;

  function mostrarDiapositiva(indice) {
    indiceActual = Math.max(0, Math.min(indice, diapositivas.length - 1));
    diapositivas.forEach((diapositiva, indiceDiapositiva) => {
      const activa = indiceDiapositiva === indiceActual;
      diapositiva.hidden = !activa;
      diapositiva.classList.toggle("is-active", activa);
    });

    const numero = String(indiceActual + 1).padStart(2, "0");
    contador.textContent = `${numero} / ${String(diapositivas.length).padStart(2, "0")}`;
    progreso.style.width = `${((indiceActual + 1) / diapositivas.length) * 100}%`;
    barraProgreso.setAttribute("aria-valuenow", String(indiceActual + 1));
    botonAnterior.disabled = indiceActual === 0;
    botonSiguiente.disabled = indiceActual === diapositivas.length - 1;
  }

  function alternarPantallaCompleta() {
    if (document.fullscreenElement) {
      document.exitFullscreen();
      return;
    }
    document.documentElement.requestFullscreen();
  }

  botonAnterior.addEventListener("click", () => mostrarDiapositiva(indiceActual - 1));
  botonSiguiente.addEventListener("click", () => mostrarDiapositiva(indiceActual + 1));
  botonPantallaCompleta.addEventListener("click", alternarPantallaCompleta);

  document.addEventListener("keydown", (evento) => {
    if (evento.altKey || evento.ctrlKey || evento.metaKey) return;
    if (["ArrowRight", "PageDown", " "].includes(evento.key)) {
      evento.preventDefault();
      mostrarDiapositiva(indiceActual + 1);
    } else if (["ArrowLeft", "PageUp"].includes(evento.key)) {
      evento.preventDefault();
      mostrarDiapositiva(indiceActual - 1);
    } else if (evento.key === "Home") {
      mostrarDiapositiva(0);
    } else if (evento.key === "End") {
      mostrarDiapositiva(diapositivas.length - 1);
    } else if (evento.key.toLocaleLowerCase("es") === "f") {
      alternarPantallaCompleta();
    }
  });

  mostrarDiapositiva(0);
})();
