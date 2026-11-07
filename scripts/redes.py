"""
Actualiza redes.json con las métricas de Instagram, Facebook y TikTok.

Lo ejecuta GitHub Actions una vez al día (.github/workflows/redes.yml).
Solo usa Python estándar. Las llaves llegan como secretos de GitHub:

  META_TOKEN            Llave de Meta (usuario del sistema, sin caducidad) con
                        pages_show_list, pages_read_engagement, instagram_basic.
  FB_PAGE_ID            (opcional) ID de la página de Facebook. Si falta, se usa
                        la primera página a la que tiene acceso la llave.
  TIKTOK_CLIENT_KEY     Datos de la app de TikTok for Developers.
  TIKTOK_CLIENT_SECRET
  TIKTOK_REFRESH_TOKEN  Se obtiene una vez con scripts/tiktok_autorizar.py.

Si falta la llave de una red, o su API falla, esa red conserva sus últimas
cifras y las demás se actualizan igual. Nunca se escriben llaves en el archivo
ni en el registro.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARCHIVO = RAIZ / "redes.json"
GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_VERSION", "v23.0")
TIKTOK = "https://open.tiktokapis.com/v2"
MAX_HISTORIAL = 800  # días


class ErrorRed(Exception):
    pass


def ocultar(valor: str) -> None:
    """Pide a GitHub Actions que nunca muestre este valor en el registro."""
    if valor and os.environ.get("GITHUB_ACTIONS"):
        print(f"::add-mask::{valor}")


def pedir(url: str, *, datos: dict | None = None, cabeceras: dict | None = None) -> dict:
    cuerpo = urllib.parse.urlencode(datos).encode() if datos is not None else None
    req = urllib.request.Request(url, data=cuerpo, headers={"User-Agent": "quim-fabregas-web/1.0", **(cabeceras or {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detalle = json.loads(e.read().decode("utf-8"))
            detalle = detalle.get("error", detalle)
            if isinstance(detalle, dict):
                detalle = detalle.get("message") or detalle.get("error_description") or detalle.get("code")
        except Exception:
            detalle = ""
        raise ErrorRed(f"HTTP {e.code} {detalle}".strip()) from None
    except (urllib.error.URLError, TimeoutError) as e:
        raise ErrorRed(f"sin conexión ({e})") from None


def graph(ruta: str, token: str, **params) -> dict:
    params["access_token"] = token
    return pedir(f"{GRAPH}/{ruta}?{urllib.parse.urlencode(params)}")


# ------------------------------------------------------------------ Meta
def pagina_facebook(token: str) -> dict:
    page_id = os.environ.get("FB_PAGE_ID", "").strip()
    if page_id:
        return {"id": page_id}
    paginas = graph("me/accounts", token, fields="id,name", limit=25).get("data", [])
    if not paginas:
        raise ErrorRed("la llave de Meta no tiene acceso a ninguna página de Facebook")
    return paginas[0]


def leer_facebook(token: str, pagina: dict) -> dict:
    d = graph(pagina["id"], token, fields="name,link,username,followers_count,fan_count,instagram_business_account")
    usuario = d.get("username")
    return {
        "nombre": d.get("name", ""),
        "usuario": usuario or "",
        "url": d.get("link") or (f"https://www.facebook.com/{usuario}" if usuario else f"https://www.facebook.com/{pagina['id']}"),
        "seguidores": d.get("followers_count", d.get("fan_count")),
        "me_gusta_pagina": d.get("fan_count"),
        "_ig": (d.get("instagram_business_account") or {}).get("id"),
    }


def leer_instagram(token: str, ig_id: str) -> dict:
    d = graph(ig_id, token, fields="username,name,followers_count,follows_count,media_count")
    datos = {
        "nombre": d.get("name") or d.get("username", ""),
        "usuario": d.get("username", ""),
        "url": f"https://www.instagram.com/{d.get('username', '')}/",
        "seguidores": d.get("followers_count"),
        "publicaciones": d.get("media_count"),
    }
    # Interacción media de las últimas 12 publicaciones (me gusta + comentarios)
    try:
        medios = graph(f"{ig_id}/media", token, fields="like_count,comments_count,timestamp", limit=12).get("data", [])
        if medios:
            inter = [(m.get("like_count") or 0) + (m.get("comments_count") or 0) for m in medios]
            media = sum(inter) / len(inter)
            datos["interacciones_por_publicacion"] = round(media, 1)
            if datos["seguidores"]:
                datos["tasa_interaccion"] = round(100 * media / datos["seguidores"], 2)
    except ErrorRed as e:
        print(f"  Instagram: sin datos de publicaciones ({e})")
    return datos


# ---------------------------------------------------------------- TikTok
def leer_tiktok(client_key: str, client_secret: str, refresh_token: str) -> tuple[dict, str | None]:
    tok = pedir(f"{TIKTOK}/oauth/token/", datos={
        "client_key": client_key, "client_secret": client_secret,
        "grant_type": "refresh_token", "refresh_token": refresh_token,
    }, cabeceras={"Content-Type": "application/x-www-form-urlencoded"})
    if "access_token" not in tok:
        raise ErrorRed(tok.get("error_description") or tok.get("error") or "TikTok no ha devuelto llave")
    acceso = tok["access_token"]
    ocultar(acceso)
    nuevo_refresh = tok.get("refresh_token")
    if nuevo_refresh:
        ocultar(nuevo_refresh)
    campos = "display_name,username,profile_deep_link,follower_count,following_count,likes_count,video_count"
    r = pedir(f"{TIKTOK}/user/info/?fields={campos}", cabeceras={"Authorization": f"Bearer {acceso}"})
    err = r.get("error") or {}
    if err.get("code") not in (None, "ok"):
        raise ErrorRed(err.get("message") or err.get("code"))
    u = (r.get("data") or {}).get("user") or {}
    usuario = u.get("username", "")
    datos = {
        "nombre": u.get("display_name", ""),
        "usuario": usuario,
        "url": f"https://www.tiktok.com/@{usuario}" if usuario else (u.get("profile_deep_link") or ""),
        "seguidores": u.get("follower_count"),
        "me_gusta": u.get("likes_count"),
        "videos": u.get("video_count"),
    }
    return datos, (nuevo_refresh if nuevo_refresh and nuevo_refresh != refresh_token else None)


# ------------------------------------------------------------------ main
def main() -> int:
    ahora = datetime.now(timezone.utc)
    anterior = json.loads(ARCHIVO.read_text(encoding="utf-8")) if ARCHIVO.exists() else {}
    redes: dict = dict(anterior.get("redes") or {})
    historial: list = list(anterior.get("historial") or [])
    estado: dict = {}

    def actualizar(nombre: str, datos: dict) -> None:
        datos = {k: v for k, v in datos.items() if not k.startswith("_") and v not in (None, "")}
        datos["actualizado"] = ahora.isoformat(timespec="seconds")
        redes[nombre] = datos
        estado[nombre] = "ok"
        print(f"  {nombre}: {datos.get('seguidores')} seguidores")

    def fallo(nombre: str, motivo: str) -> None:
        estado[nombre] = motivo
        print(f"::warning title=Redes ({nombre})::{motivo}" if os.environ.get("GITHUB_ACTIONS") else f"  {nombre}: {motivo}")

    meta = os.environ.get("META_TOKEN", "").strip()
    if meta:
        ocultar(meta)
        try:
            pagina = pagina_facebook(meta)
            fb = leer_facebook(meta, pagina)
            ig_id = fb.get("_ig")
            actualizar("facebook", fb)
            if ig_id:
                try:
                    actualizar("instagram", leer_instagram(meta, ig_id))
                except ErrorRed as e:
                    fallo("instagram", str(e))
            else:
                fallo("instagram", "la página de Facebook no tiene una cuenta profesional de Instagram vinculada")
        except ErrorRed as e:
            fallo("facebook", str(e)); fallo("instagram", str(e))
    else:
        fallo("facebook", "falta el secreto META_TOKEN"); fallo("instagram", "falta el secreto META_TOKEN")

    tk = [os.environ.get(k, "").strip() for k in ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET", "TIKTOK_REFRESH_TOKEN")]
    if all(tk):
        for v in tk[1:]:
            ocultar(v)
        try:
            datos, nuevo = leer_tiktok(*tk)
            actualizar("tiktok", datos)
            if nuevo:
                destino = os.environ.get("NUEVO_REFRESH_TIKTOK")
                if destino:
                    Path(destino).write_text(nuevo, encoding="utf-8")
                print("  tiktok: TikTok ha renovado la llave de acceso")
        except ErrorRed as e:
            fallo("tiktok", str(e))
    else:
        fallo("tiktok", "faltan los secretos de TikTok")

    # Una foto al día de los seguidores, para la gráfica de evolución
    hoy = ahora.date().isoformat()
    foto = {"fecha": hoy, **{r: d["seguidores"] for r, d in redes.items() if isinstance(d.get("seguidores"), int)}}
    if len(foto) > 1:
        historial = [h for h in historial if h.get("fecha") != hoy] + [foto]
        historial = sorted(historial, key=lambda h: h["fecha"])[-MAX_HISTORIAL:]

    nuevo = {"actualizado": ahora.isoformat(timespec="seconds") if estado and "ok" in estado.values() else anterior.get("actualizado"),
             "redes": redes, "historial": historial}
    ARCHIVO.write_text(json.dumps(nuevo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    resumen = os.environ.get("GITHUB_STEP_SUMMARY")
    if resumen:
        with open(resumen, "a", encoding="utf-8") as f:
            f.write("### Métricas de redes\n\n| Red | Resultado | Seguidores |\n|---|---|---|\n")
            for r in ("instagram", "facebook", "tiktok"):
                f.write(f"| {r} | {'✅ actualizado' if estado.get(r) == 'ok' else '⚠️ ' + estado.get(r, '')} | {redes.get(r, {}).get('seguidores', '—')} |\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
