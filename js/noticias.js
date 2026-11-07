/* Noticias: lee noticias.json y las pinta en cualquier elemento con data-noticias.
   Atributos:
     data-noticias="completo"  → lista con el texto entero (página de noticias)
     data-noticias="resumen"   → tarjetas con resumen y enlace (portada)
     data-limite="3"           → cuántas mostrar
     data-enlace="noticias.html" → página a la que lleva cada tarjeta
     data-img-base="https://…/uploads/" → prefijo para rutas cortas 2026/10/foto.jpg
     data-ocultar="#seccion"   → elemento a ocultar si no hay noticias           */
(() => {
  "use strict";
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const enLinea = (s) => esc(s)
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[^*])\*(?!\s)(.+?)\*/g, "$1<em>$2</em>")
    .replace(/\[([^\]]+)\]\(((?:https?:\/\/|mailto:|\/|\.\.?\/|#|[\w-]+\.html)[^)\s]*)\)/g, (m, t, u) =>
      `<a href="${u}"${/^https?:/.test(u) ? ' target="_blank" rel="noopener"' : ""}>${t}</a>`);
  const parrafos = (t) => String(t || "").trim().split(/\n\s*\n/).filter(Boolean)
    .map((p) => `<p>${enLinea(p).replace(/\n/g, "<br>")}</p>`).join("");
  const fecha = (f) => { const d = new Date(f + "T12:00:00"); return isNaN(d) ? esc(f) : d.toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" }); };

  async function pintar(el) {
    const modo = el.dataset.noticias || "completo";
    const limite = parseInt(el.dataset.limite || "0", 10);
    const base = el.dataset.imgBase || "";
    const enlace = el.dataset.enlace || "noticias.html";
    const foto = (r) => !r ? "" : (/^\d{4}\/\d{2}\//.test(r) && base ? base + r : r);
    const src = el.dataset.fuente || "noticias.json";
    let lista = [];
    try {
      const r = await fetch(src + (src.includes("?") ? "&" : "?") + "v=" + Math.floor(Date.now() / 60000), { cache: "no-cache" });
      if (r.ok) lista = await r.json();
    } catch {}
    lista = (Array.isArray(lista) ? lista : []).filter((n) => !n.borrador)
      .sort((a, b) => String(b.fecha).localeCompare(String(a.fecha)));
    if (limite) lista = lista.slice(0, limite);
    if (!lista.length) {
      if (el.dataset.ocultar) document.querySelectorAll(el.dataset.ocultar).forEach((x) => (x.hidden = true));
      el.innerHTML = modo === "completo" ? '<p class="noticias-vacio">Todavía no hay noticias. Vuelve pronto.</p>' : "";
      return;
    }
    if (el.dataset.ocultar) document.querySelectorAll(el.dataset.ocultar).forEach((x) => (x.hidden = false));
    el.innerHTML = lista.map((n) => {
      const img = foto(n.imagen);
      if (modo === "resumen") {
        return `<a class="noticia-tarjeta" href="${esc(enlace)}#${esc(n.id)}">
          ${img ? `<span class="noticia-tarjeta-img" style="background-image:url('${esc(img)}')"></span>` : ""}
          <span class="noticia-tarjeta-cuerpo"><span class="noticia-fecha">${fecha(n.fecha)}</span>
          <span class="noticia-titulo">${esc(n.titulo)}</span>
          ${n.resumen ? `<span class="noticia-resumen">${esc(n.resumen)}</span>` : ""}
          <span class="noticia-leer">Leer →</span></span></a>`;
      }
      return `<article class="noticia" id="${esc(n.id)}">
        <p class="noticia-fecha">${fecha(n.fecha)}</p>
        <h2 class="noticia-titulo">${esc(n.titulo)}</h2>
        ${n.resumen ? `<p class="noticia-resumen">${enLinea(n.resumen)}</p>` : ""}
        ${img ? `<figure class="noticia-foto"><img src="${esc(img)}" alt="${esc(n.pie || n.titulo)}" loading="lazy">${n.pie ? `<figcaption>${esc(n.pie)}</figcaption>` : ""}</figure>` : ""}
        <div class="noticia-texto">${parrafos(n.texto)}</div>
      </article>`;
    }).join("");
    if (modo === "completo" && location.hash) { const t = document.getElementById(decodeURIComponent(location.hash.slice(1))); if (t) t.scrollIntoView(); }
  }
  document.querySelectorAll("[data-noticias]").forEach(pintar);
})();
