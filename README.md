# Quim Fàbregas — web personal

Web estática de una sola página (`index.html` + `css/estilo.css`), publicada en GitHub Pages:
https://jeanetteakumbele-bit.github.io/quim-fabregas/

## Cómo cambiar cosas

- **Textos:** edita `index.html`. Cada sección empieza con un comentario (`<!-- VIDA -->`, `<!-- SERIES -->`…).
- **Colores y tipografía:** las variables al principio de `css/estilo.css`.
- **Fotos:** ahora se usan las de fundacionakumbele.org. Para usar fotos propias, guárdalas en una carpeta `img/` y cambia la dirección por `img/nombre.jpg`.

## Publicar

```powershell
git add -A
git commit -m "Describe el cambio"
git push
```

En 1-2 minutos los cambios están en internet.

## Noticias

- **Panel:** https://jeanetteakumbele-bit.github.io/quim-fabregas/admin.html (con contraseña).
- La primera vez pide una llave de GitHub (fine-grained token con *Contents: Read and write* solo para este repositorio) y una contraseña. La llave se guarda cifrada en `admin-config.json`.
- Las noticias se guardan en `noticias.json` y las fotos en `img/noticias/`. Se ven en `noticias.html` y las tres últimas en la portada.
