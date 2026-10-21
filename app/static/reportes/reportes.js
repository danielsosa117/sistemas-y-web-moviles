const REPORTES = {
  "inventario-por-categoria": {
    descripcion:
      "Productos activos por categoría, cuántos están en o bajo el stock mínimo y el valor del inventario (stock × precio de venta).",
    usaFechas: false,
    columnas: [
      { clave: "categoria", titulo: "Categoría" },
      { clave: "productos", titulo: "Productos activos", tipo: "numero" },
      { clave: "bajo_minimo", titulo: "En o bajo el mínimo", tipo: "numero" },
      { clave: "valor_inventario", titulo: "Valor del inventario", tipo: "moneda" },
    ],
  },
  "stock-bajo": {
    descripcion:
      "Productos activos con stock igual o inferior al mínimo, los más urgentes primero, con el proveedor al que se les puede pedir.",
    usaFechas: false,
    columnas: [
      { clave: "nombre", titulo: "Producto" },
      { clave: "categoria", titulo: "Categoría" },
      { clave: "proveedor", titulo: "Proveedor" },
      { clave: "proveedor_telefono", titulo: "Teléfono" },
      { clave: "unidad", titulo: "Unidad" },
      { clave: "stock_actual", titulo: "Stock actual", tipo: "numero" },
      { clave: "stock_minimo", titulo: "Stock mínimo", tipo: "numero" },
      { clave: "faltante", titulo: "Faltante", tipo: "numero" },
    ],
  },
  "movimientos-por-proveedor": {
    descripcion:
      "Entradas y salidas de los productos de cada proveedor, separadas por unidad (KG o UND). Sin fechas se incluyen todos los movimientos.",
    usaFechas: true,
    columnas: [
      { clave: "proveedor", titulo: "Proveedor" },
      { clave: "unidad", titulo: "Unidad" },
      { clave: "movimientos", titulo: "Movimientos", tipo: "numero" },
      { clave: "entradas", titulo: "Entradas", tipo: "numero" },
      { clave: "salidas", titulo: "Salidas", tipo: "numero" },
    ],
  },
  "movimientos-por-usuario": {
    descripcion:
      "Cuántos movimientos registró cada usuario, con sus entradas y salidas por unidad. Sin fechas se incluyen todos los movimientos.",
    usaFechas: true,
    columnas: [
      { clave: "usuario", titulo: "Usuario" },
      { clave: "rol", titulo: "Rol" },
      { clave: "unidad", titulo: "Unidad" },
      { clave: "movimientos", titulo: "Movimientos", tipo: "numero" },
      { clave: "entradas", titulo: "Entradas", tipo: "numero" },
      { clave: "salidas", titulo: "Salidas", tipo: "numero" },
    ],
  },
};

const selectorReporte = document.querySelector("#reporte");
const campoDesde = document.querySelector("#desde");
const campoHasta = document.querySelector("#hasta");
const botonConsultar = document.querySelector("#consultar");
const botonCsv = document.querySelector("#descargar-csv");
const descripcion = document.querySelector("#descripcion-reporte");
const cabecera = document.querySelector("#cabecera-reporte");
const cuerpo = document.querySelector("#cuerpo-reporte");
const totalFilas = document.querySelector("#total-filas");
const mensaje = document.querySelector("#mensaje");

const formatoMoneda = new Intl.NumberFormat("es-CO", {
  style: "currency",
  currency: "COP",
  maximumFractionDigits: 0,
});
const formatoNumero = new Intl.NumberFormat("es-CO", { maximumFractionDigits: 2 });

let reporteMostrado = null;
let filasMostradas = [];
let numeroPeticion = 0;

function mostrarMensaje(texto, tipo = "danger") {
  mensaje.textContent = texto;
  mensaje.className = `alert alert-${tipo}`;
}

function ocultarMensaje() {
  mensaje.className = "alert d-none";
}

function formatear(valor, tipo) {
  if (valor === null || valor === undefined || valor === "") return "—";
  if (tipo === "moneda") return formatoMoneda.format(valor);
  if (tipo === "numero") return formatoNumero.format(valor);
  return String(valor);
}

function crearCelda(texto, tipo) {
  const celda = document.createElement("td");
  celda.textContent = texto;
  if (tipo) celda.className = "text-end";
  return celda;
}

function dibujarCabecera(columnas) {
  cabecera.replaceChildren(
    ...columnas.map((columna) => {
      const celda = document.createElement("th");
      celda.textContent = columna.titulo;
      celda.className = columna.tipo ? "text-end" : "";
      return celda;
    }),
  );
}

function dibujarFilas(columnas, filas) {
  if (filas.length === 0) {
    const fila = document.createElement("tr");
    const celda = document.createElement("td");
    celda.colSpan = columnas.length;
    celda.className = "text-center text-secondary py-4";
    celda.textContent = "No hay datos para los filtros elegidos.";
    fila.append(celda);
    cuerpo.replaceChildren(fila);
    return;
  }
  cuerpo.replaceChildren(
    ...filas.map((dato) => {
      const fila = document.createElement("tr");
      fila.append(
        ...columnas.map((columna) =>
          crearCelda(formatear(dato[columna.clave], columna.tipo), columna.tipo),
        ),
      );
      return fila;
    }),
  );
}

function actualizarFiltros() {
  const { descripcion: texto, usaFechas } = REPORTES[selectorReporte.value];
  descripcion.textContent = texto;
  document
    .querySelectorAll(".filtro-fechas")
    .forEach((campo) => campo.classList.toggle("d-none", !usaFechas));
}

function construirUrl(clave) {
  const parametros = new URLSearchParams();
  if (REPORTES[clave].usaFechas) {
    if (campoDesde.value) parametros.set("desde", campoDesde.value);
    if (campoHasta.value) parametros.set("hasta", campoHasta.value);
  }
  const texto = parametros.toString();
  return `/reportes/${clave}${texto ? `?${texto}` : ""}`;
}

async function consultar() {
  const clave = selectorReporte.value;
  const reporte = REPORTES[clave];
  ocultarMensaje();

  if (reporte.usaFechas && campoDesde.value && campoHasta.value && campoDesde.value > campoHasta.value) {
    mostrarMensaje("La fecha inicial no puede ser posterior a la final.", "warning");
    return;
  }

  const peticion = ++numeroPeticion;
  botonConsultar.disabled = true;
  botonCsv.disabled = true;
  try {
    const respuesta = await fetch(construirUrl(clave));
    const datos = await respuesta.json().catch(() => null);
    if (peticion !== numeroPeticion) return;
    if (!respuesta.ok) {
      const detalle = typeof datos?.detail === "string" ? datos.detail : null;
      throw new Error(detalle || `No se pudo generar el reporte (código ${respuesta.status}).`);
    }
    reporteMostrado = clave;
    filasMostradas = datos;
    dibujarCabecera(reporte.columnas);
    dibujarFilas(reporte.columnas, datos);
    totalFilas.textContent = `${datos.length} ${datos.length === 1 ? "fila" : "filas"}`;
    botonCsv.disabled = datos.length === 0;
  } catch (error) {
    if (peticion !== numeroPeticion) return;
    mostrarMensaje(error.message);
  } finally {
    if (peticion === numeroPeticion) botonConsultar.disabled = false;
  }
}

function celdaCsv(valor) {
  let texto = valor === null || valor === undefined ? "" : String(valor);
  // Evita que Excel interprete como fórmula un texto que empieza con = + - @
  if (typeof valor === "string" && /^[=+\-@\t\r]/.test(texto)) texto = `'${texto}`;
  return /[";\r\n]/.test(texto) ? `"${texto.replaceAll('"', '""')}"` : texto;
}

function descargarCsv() {
  if (!reporteMostrado) return;
  const columnas = REPORTES[reporteMostrado].columnas;
  const lineas = [
    columnas.map((columna) => celdaCsv(columna.titulo)),
    ...filasMostradas.map((dato) => columnas.map((columna) => celdaCsv(dato[columna.clave]))),
  ];
  // Punto y coma y BOM UTF-8: Excel en español abre bien las columnas y las tildes.
  const contenido = `\ufeff${lineas.map((linea) => linea.join(";")).join("\r\n")}`;
  const archivo = new Blob([contenido], { type: "text/csv;charset=utf-8" });
  const enlace = document.createElement("a");
  enlace.href = URL.createObjectURL(archivo);
  enlace.download = `reporte-${reporteMostrado}.csv`;
  document.body.append(enlace);
  enlace.click();
  enlace.remove();
  URL.revokeObjectURL(enlace.href);
}

selectorReporte.addEventListener("change", () => {
  actualizarFiltros();
  consultar();
});
botonConsultar.addEventListener("click", consultar);
botonCsv.addEventListener("click", descargarCsv);

actualizarFiltros();
consultar();
