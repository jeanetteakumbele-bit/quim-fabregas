/* Métricas de redes: lee redes.json (lo actualiza GitHub Actions cada día)
   y pinta una tarjeta por red en [data-redes]. Oculta la sección si no hay datos. */
(() => {
  "use strict";
  const el = document.querySelector("[data-redes]");
  if (!el) return;
  const seccion = document.querySelector(el.dataset.ocultar || "#redes");
  const RED = {
    instagram: { nombre: "Instagram", extra: [["publicaciones", "publicaciones"], ["interacciones_por_publicacion", "interacciones por publicación"], ["tasa_interaccion", "% de interacción", "pct"]] },
    facebook: { nombre: "Facebook", extra: [["me_gusta_pagina", "me gusta en la página"]] },
    tiktok: { nombre: "TikTok", extra: [["videos", "vídeos"], ["me_gusta", "me gusta en total"]] }
  };
  const num = (n) => new Intl.NumberFormat("es-ES", { notation: n >= 100000 ? "compact" : "standard", maximumFractionDigits: 1 }).format(n);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  function linea(puntos) {
    if (puntos.length < 2) return "";
    const w = 240, h = 56, p = 3;
    const ys = puntos.map((x) => x.v), min = Math.min(...ys), max = Math.max(...ys), rango = max - min || 1;
    const t0 = +new Date(puntos[0].f), t1 = +new Date(puntos[puntos.length - 1].f), tr = t1 - t0 || 1;
    const xy = puntos.map((x) => [p + (w - 2 * p) * (+new Date(x.f) - t0) / tr, h - p - (h - 2 * p) * (x.v - min) / rango]);
    const d = xy.map(([x, y], i) => (i ? "L" : "M") + x.toFixed(1) + " " + y.toFixed(1)).join(" ");
    const [ux, uy] = xy[xy.length - 1];
    return `<svg class="red-linea" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true">
      <path d="${d} L${ux.toFixed(1)} ${h} L${xy[0][0].toFixed(1)} ${h} Z" class="red-area"/>
      <path d="${d}" class="red-trazo" vector-effect="non-scaling-stroke"/>
      <circle cx="${ux.toFixed(1)}" cy="${uy.toFixed(1)}" r="3" class="red-punto"/></svg>`;
  }

  function variacion(historial, red, actual) {
    const hace = new Date(Date.now() - 30 * 864e5).toISOString().slice(0, 10);
    const previo = historial.filter((h) => typeof h[red] === "number" && h.fecha <= hace).pop()
                || historial.find((h) => typeof h[red] === "number");
    if (!previo || previo[red] === actual) return "";
    const dias = Math.round((Date.now() - new Date(previo.fecha)) / 864e5);
    if (dias < 1) return "";
    const dif = actual - previo[red];
    return `<span class="red-var ${dif > 0 ? "sube" : "baja"}">${dif > 0 ? "+" : "−"}${num(Math.abs(dif))} en ${dias >= 28 ? "30 días" : dias + (dias === 1 ? " día" : " días")}</span>`;
  }

  fetch("redes.json?v=" + Math.floor(Date.now() / 3600000), { cache: "no-cache" })
    .then((r) => (r.ok ? r.json() : null))
    .then((datos) => {
      const redes = (datos && datos.redes) || {};
      const historial = (datos && datos.historial) || [];
      const claves = Object.keys(RED).filter((k) => redes[k] && typeof redes[k].seguidores === "number");
      if (!claves.length) { if (seccion) seccion.hidden = true; return; }
      el.innerHTML = claves.map((k) => {
        const d = redes[k], cfg = RED[k];
        const puntos = historial.filter((h) => typeof h[k] === "number").slice(-90).map((h) => ({ f: h.fecha, v: h[k] }));
        const extra = cfg.extra.filter(([c]) => typeof d[c] === "number")
          .map(([c, txt, tipo]) => `<li><b>${tipo === "pct" ? d[c].toLocaleString("es-ES") + " %" : num(d[c])}</b> ${tipo === "pct" ? "de interacción" : txt}</li>`).join("");
        const url = /^https:\/\//.test(d.url || "") ? d.url : "";
        return `<article class="red">
          <header class="red-cab"><span class="red-nombre">${cfg.nombre}</span>${d.usuario ? `<span class="red-usuario">@${esc(d.usuario)}</span>` : ""}</header>
          <p class="red-cifra">${num(d.seguidores)}</p>
          <p class="red-etq">${k === "tiktok" || k === "instagram" ? "seguidores" : "seguidores de la página"} ${variacion(historial, k, d.seguidores)}</p>
          ${linea(puntos)}
          ${extra ? `<ul class="red-extra">${extra}</ul>` : ""}
          ${url ? `<a class="red-ir" href="${esc(url)}" target="_blank" rel="noopener">Ver perfil ↗</a>` : ""}
        </article>`;
      }).join("");
      const nota = document.querySelector("[data-redes-fecha]");
      if (nota && datos.actualizado) {
        nota.textContent = "Actualizado automáticamente el " + new Date(datos.actualizado).toLocaleDateString("es-ES", { day: "numeric", month: "long", year: "numeric" }) + ".";
      }
      if (seccion) seccion.hidden = false;
    })
    .catch(() => { if (seccion) seccion.hidden = true; });
})();
