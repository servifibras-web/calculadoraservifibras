#!/usr/bin/env python3
"""Copia gioval/ (la app web, SIN compilar nada) a gioval-android/www/ para que Capacitor la meta dentro del APK.

    python3 preparar_web.py                   # app normal
    python3 preparar_web.py --espacio beta    # variante beta: otro espacio de datos y cartel visible "BETA"
    python3 preparar_web.py --version         # solo imprime GIOVAL_VERSION (lo usa el flujo de GitHub Actions)

Igual que gioval-dev/tools/hacer_beta.py: si el texto que espera cambiar NO está exactamente una vez, FALLA con un mensaje
claro y no deja nada a medias. Así, si alguien cambia js/version.js o index.html, la beta no sale "disfrazada de real".
"""
import argparse, re, shutil, sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ORIGEN = AQUI.parent / "gioval"
DESTINO = AQUI / "www"


def fallar(msg):
    sys.exit("ERROR: " + msg)


def sustituir(txt, viejo, nuevo, donde):
    n = txt.count(viejo)
    if n != 1:
        fallar("en %s esperaba 1 ocurrencia de %r y hay %d. La app cambió: actualizá este script antes de armar el APK." % (donde, viejo, n))
    return txt.replace(viejo, nuevo)


def version(origen=ORIGEN):
    f = origen / "js" / "version.js"
    if not f.exists():
        fallar("no encuentro %s" % f)
    m = re.search(r'GIOVAL_VERSION\s*=\s*"([^"]+)"', f.read_text(encoding="utf-8"))
    if not m:
        fallar("no encuentro GIOVAL_VERSION en js/version.js")
    return m.group(1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--espacio", default="", choices=["", "beta"], help='"" = app normal, "beta" = copia de prueba')
    ap.add_argument("--version", action="store_true", help="solo imprime la versión de la app y sale")
    ap.add_argument("--origen", default=str(ORIGEN))
    ap.add_argument("--destino", default=str(DESTINO))
    a = ap.parse_args()
    origen, destino = Path(a.origen), Path(a.destino)
    if a.version:
        print(version(origen)); return
    if not (origen / "index.html").exists():
        fallar("no encuentro %s/index.html" % origen)

    if destino.exists():
        shutil.rmtree(destino)
    shutil.copytree(origen, destino)

    if a.espacio == "beta":
        v = (destino / "js" / "version.js").read_text(encoding="utf-8")
        v = sustituir(v, 'self.GIOVAL_ESPACIO = "";', 'self.GIOVAL_ESPACIO = "beta";', "js/version.js")
        (destino / "js" / "version.js").write_text(v, encoding="utf-8")
        ix = (destino / "index.html").read_text(encoding="utf-8")
        ix = sustituir(ix, "<title>Mundo Gioval - A jugar</title>", "<title>Mundo Gioval BETA</title>", "index.html")
        cartel = ('<div style="position:fixed;left:0;right:0;bottom:0;z-index:99999;background:#d32f2f;color:#fff;'
                  'font:700 11px sans-serif;text-align:center;padding:2px;pointer-events:none">'
                  "BETA · versión de prueba · no es la app de todos los días</div>\n</body>")
        ix = sustituir(ix, "</body>", cartel, "index.html")
        (destino / "index.html").write_text(ix, encoding="utf-8")

    # control final: lo que tiene que haber quedado
    v = (destino / "js" / "version.js").read_text(encoding="utf-8")
    esperado = 'self.GIOVAL_ESPACIO = "beta";' if a.espacio == "beta" else 'self.GIOVAL_ESPACIO = "";'
    if esperado not in v:
        fallar("js/version.js no quedó con el espacio de datos pedido (%r)" % a.espacio)
    for f in ("js/core/alarma.js", "js/core/alarma_nativa.js", "js/core/envoltorio.js"):
        if not (destino / f).exists():
            fallar("falta %s en la copia" % f)
    ix = (destino / "index.html").read_text(encoding="utf-8")
    if "js/core/alarma_nativa.js" not in ix:
        fallar("index.html no carga js/core/alarma_nativa.js")
    n = sum(1 for p in destino.rglob("*") if p.is_file())
    print("Web copiada a %s (%d archivos), versión %s, espacio %r" % (destino, n, version(destino), a.espacio))


main()
