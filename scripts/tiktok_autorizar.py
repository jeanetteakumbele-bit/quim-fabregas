"""
Conecta la cuenta de TikTok de Quim con la web. Se ejecuta UNA vez, en tu ordenador:

    python scripts/tiktok_autorizar.py

Necesitas:
  - GitHub CLI con sesión iniciada (gh auth status).
  - Una app en https://developers.tiktok.com con «Login Kit», los permisos
    user.info.basic, user.info.profile y user.info.stats, y esta dirección de
    redirección:  https://jeanetteakumbele-bit.github.io/quim-fabregas/tiktok.html

El script te pide el Client key y el Client secret de la app (no se ven al
escribir), abre TikTok para que des permiso, y guarda las tres llaves como
secretos del repositorio. Nunca las muestra en pantalla ni las guarda en disco.
"""
from __future__ import annotations

import getpass
import json
import secrets
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import webbrowser

REPO = "jeanetteakumbele-bit/quim-fabregas"
REDIRECCION = "https://jeanetteakumbele-bit.github.io/quim-fabregas/tiktok.html"
PERMISOS = "user.info.basic,user.info.profile,user.info.stats"


def guardar_secreto(nombre: str, valor: str) -> None:
    r = subprocess.run(["gh", "secret", "set", nombre, "--repo", REPO], input=valor, text=True, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"No se ha podido guardar {nombre} en GitHub: {r.stderr.strip()}")
    print(f"  ✓ {nombre} guardado en los secretos de {REPO}")


def main() -> None:
    if not shutil.which("gh"):
        sys.exit("Falta GitHub CLI (gh). Instálalo desde https://cli.github.com y ejecuta: gh auth login")
    if subprocess.run(["gh", "auth", "status"], capture_output=True).returncode != 0:
        sys.exit("GitHub CLI no tiene sesión iniciada. Ejecuta: gh auth login")

    print("Datos de tu app de TikTok (developers.tiktok.com → tu app → App details).")
    clave = getpass.getpass("Client key (no se verá al escribir): ").strip()
    secreto = getpass.getpass("Client secret (no se verá al escribir): ").strip()
    if not clave or not secreto:
        sys.exit("Faltan datos.")

    estado = secrets.token_urlsafe(16)
    url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
        "client_key": clave, "scope": PERMISOS, "response_type": "code",
        "redirect_uri": REDIRECCION, "state": estado,
    })
    print("\nSe va a abrir TikTok en el navegador. Entra con la cuenta de Quim y pulsa «Autorizar».")
    print("Si no se abre, copia esta dirección en el navegador:\n" + url + "\n")
    webbrowser.open(url)
    codigo = getpass.getpass("Pega aquí el código que muestra la página (no se verá): ").strip()
    codigo = urllib.parse.unquote(codigo)
    if not codigo:
        sys.exit("No has pegado ningún código.")

    datos = urllib.parse.urlencode({
        "client_key": clave, "client_secret": secreto, "code": codigo,
        "grant_type": "authorization_code", "redirect_uri": REDIRECCION,
    }).encode()
    req = urllib.request.Request("https://open.tiktokapis.com/v2/oauth/token/", data=datos,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            resp = json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        sys.exit(f"TikTok ha rechazado el código (HTTP {e.code}). Vuelve a ejecutar el script; el código solo dura unos minutos.")
    if "refresh_token" not in resp:
        sys.exit("TikTok no ha dado acceso: " + str(resp.get("error_description") or resp.get("error") or "respuesta inesperada"))
    falta = set(PERMISOS.split(",")) - set((resp.get("scope") or "").split(","))
    if falta:
        print("  ! Aviso: TikTok no ha concedido " + ", ".join(sorted(falta)) + ". Revisa los permisos de la app.")

    print("\nGuardando en GitHub…")
    guardar_secreto("TIKTOK_CLIENT_KEY", clave)
    guardar_secreto("TIKTOK_CLIENT_SECRET", secreto)
    guardar_secreto("TIKTOK_REFRESH_TOKEN", resp["refresh_token"])
    print("\nListo. Para ver las cifras ya: pestaña Actions del repositorio → «Métricas de redes» → Run workflow.")


if __name__ == "__main__":
    main()
