(() => {
  "use strict";

  const paginas = [
    { nombre: "Productos", ruta: "/productos-ui" },
    { nombre: "Movimientos", ruta: "/movimientos-ui" },
    { nombre: "Categorías", ruta: "/categorias-ui" },
    { nombre: "Proveedores", ruta: "/proveedores-ui" },
    { nombre: "Usuarios", ruta: "/usuarios-ui" },
    { nombre: "Roles", ruta: "/roles-ui" },
  ];

  const nav = document.createElement("nav");
  nav.className = "navbar navbar-expand-lg navbar-inventory";
  nav.setAttribute("aria-label", "Navegación principal");
  const contenedor = document.createElement("div");
  contenedor.className = "container";

  const marca = document.createElement("a");
  marca.className = "navbar-brand fw-semibold d-flex align-items-center gap-2";
  marca.href = "/";
  const iconoMarca = document.createElement("span");
  iconoMarca.className = "brand-mark";
  iconoMarca.setAttribute("aria-hidden", "true");
  iconoMarca.textContent = "S";
  const nombreMarca = document.createElement("span");
  nombreMarca.textContent = "Salsamentaria";
  marca.append(iconoMarca, nombreMarca);

  const enlaces = document.createElement("div");
  enlaces.className = "navbar-nav flex-row ms-auto";
  const rutaActual = location.pathname === "/" ? "/productos-ui" : location.pathname;

  paginas.forEach(({ nombre, ruta }) => {
    const enlace = document.createElement("a");
    enlace.className = "nav-link";
    enlace.href = ruta;
    enlace.textContent = nombre;
    if (rutaActual === ruta) {
      enlace.classList.add("active");
      enlace.setAttribute("aria-current", "page");
    }
    enlaces.append(enlace);
  });

  contenedor.append(marca, enlaces);
  nav.append(contenedor);
  document.body.insertBefore(nav, document.body.firstChild);

  const pie = document.createElement("footer");
  pie.className = "site-footer";
  const contenidoPie = document.createElement("div");
  contenidoPie.className = "container site-footer-content";
  const nombrePie = document.createElement("span");
  nombrePie.textContent = "Salsamentaria";
  const descripcionPie = document.createElement("span");
  descripcionPie.textContent = "Gestión de inventario";
  contenidoPie.append(nombrePie, descripcionPie);
  pie.append(contenidoPie);
  document.body.append(pie);
})();
