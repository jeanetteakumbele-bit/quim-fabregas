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

## Métricas de redes (Instagram, Facebook, TikTok)

La sección **Redes** de la portada lee `redes.json`. Ese archivo lo actualiza solo, cada día, el proceso
*Métricas de redes* (`.github/workflows/redes.yml` + `scripts/redes.py`). Mientras no haya datos, la sección no se ve.
Las llaves se guardan como **secretos del repositorio** (Settings → Secrets and variables → Actions), nunca en la web.

### Instagram y Facebook (una sola llave de Meta)

1. Instagram tiene que ser una **cuenta profesional** (creador o empresa) **vinculada a la página de Facebook**.
2. En [Meta for Developers](https://developers.facebook.com/apps) crea una app de tipo *Business*.
3. En [Meta Business Suite → Configuración del negocio → Usuarios del sistema](https://business.facebook.com/settings/system-users)
   crea un usuario del sistema, asígnale la página de Facebook y la cuenta de Instagram, y pulsa **Generar token**:
   elige la app, caducidad **Nunca** y los permisos `pages_show_list`, `pages_read_engagement`, `instagram_basic`.
4. Guarda ese token como secreto **`META_TOKEN`**. Si la llave tiene acceso a varias páginas, guarda también el
   ID de la página como **`FB_PAGE_ID`**.

### TikTok

1. En [TikTok for Developers](https://developers.tiktok.com/apps) crea una app con **Login Kit** y los permisos
   `user.info.basic`, `user.info.profile` y `user.info.stats`. Dirección de redirección:
   `https://jeanetteakumbele-bit.github.io/quim-fabregas/tiktok.html`. Mientras la app no esté revisada por TikTok,
   añade la cuenta de Quim como *tester* en el modo Sandbox.
2. En tu ordenador, con GitHub CLI iniciado (`gh auth login`), ejecuta una vez:
   `python scripts/tiktok_autorizar.py`. Te pide los datos de la app, abre TikTok para dar permiso y guarda
   los secretos `TIKTOK_CLIENT_KEY`, `TIKTOK_CLIENT_SECRET` y `TIKTOK_REFRESH_TOKEN` sin mostrarlos.
3. La llave de TikTok dura un año. Si TikTok la renueva, el proceso avisa; para que se guarde sola, crea un
   token *fine-grained* con permiso **Secrets: Read and write** en este repositorio y guárdalo como `SECRETS_TOKEN`.

### Probar

Pestaña **Actions** → *Métricas de redes* → **Run workflow**. El resumen de la ejecución dice qué red se ha
actualizado y, si alguna falla, por qué.
