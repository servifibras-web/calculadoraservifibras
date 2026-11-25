#!/usr/bin/env python3
"""Genera gioval-beta/ a partir de una versión de gioval/ (rama, etiqueta o commit).

La copia beta se publica en el MISMO dominio que la app real, así que comparten
localStorage, IndexedDB y caché del navegador. Este script les pone nombres propios
("giovalbeta...") para que la beta NUNCA lea, migre ni borre los datos reales de los chicos.
Si queda algún nombre sin separar, falla y no escribe nada.

Uso (desde la raíz del repo):
    python3 gioval-dev/tools/hacer_beta.py [origen]      # origen por defecto: origin/cimientos
"""
import io, os, re, shutil, subprocess, sys, tarfile

RAIZ = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
ORIGEN = sys.argv[1] if len(sys.argv) > 1 else "origin/cimientos"
DESTINO = os.path.join(RAIZ, "gioval-beta")

# cadenas "gioval..." que pueden quedar tal cual (no son claves de almacenamiento)
PERMITIDAS = {"gioval", "gioval-alarma", "gioval-respaldo-", "gioval-beta"}
# ("gioval" solo se permite como etiqueta de formato del respaldo: app:"gioval" / o.app!=="gioval")


def sustituir(txt, viejo, nuevo, donde):
    n = txt.count(viejo)
    if n != 1:
        sys.exit(f"ERROR: en {donde} esperaba 1 ocurrencia de {viejo!r} y hay {n}. "
                 "La app cambió: actualizá este script antes de publicar la beta.")
    return txt.replace(viejo, nuevo)


def main():
    datos = subprocess.check_output(["git", "-C", RAIZ, "archive", ORIGEN, "gioval"])
    tmp = os.path.join(RAIZ, "gioval-dev", "tools", ".tmp_beta")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(tmp)
    with tarfile.open(fileobj=io.BytesIO(datos)) as t:
        t.extractall(tmp, filter="data")
    src = os.path.join(tmp, "gioval")

    def leer(rel):
        with open(os.path.join(src, rel), encoding="utf-8") as f:
            return f.read()

    def escribir(rel, txt):
        with open(os.path.join(src, rel), "w", encoding="utf-8") as f:
            f.write(txt)

    # 1) almacén: base de datos y claves propias
    a = leer("js/core/almacen.js")
    a = sustituir(a, 'const DB = "gioval-db", DB_V = 1, LS = "gioval", LS_PRE = "gioval_pre_migracion";',
                  'const DB = "giovalbeta-db", DB_V = 1, LS = "giovalbeta", LS_PRE = "giovalbeta_pre_migracion";',
                  "almacen.js")
    a = sustituir(a, '"gioval-respaldo-"', '"giovalbeta-respaldo-"', "almacen.js")
    escribir("js/core/almacen.js", a)

    # 2) alarma: clave propia
    al = leer("js/core/alarma.js")
    al = sustituir(al, 'KEY = "gioval_alarma"', 'KEY = "giovalbeta_alarma"', "alarma.js")
    escribir("js/core/alarma.js", al)

    # 3) service worker: caché propia y solo borra cachés de la beta
    sw = leer("sw.js")
    sw = sustituir(sw, 'const C="gioval-"+self.GIOVAL_VERSION;', 'const C="giovalbeta-"+self.GIOVAL_VERSION;', "sw.js")
    sw = sustituir(sw, "k.filter(x=>x!==C)", 'k.filter(x=>x.startsWith("giovalbeta-")&&x!==C)', "sw.js")
    escribir("sw.js", sw)

    # 4) manifest: otra identidad, para poder instalarla al lado de la real
    m = leer("manifest.json")
    m = sustituir(m, '"name":"Mundo Gioval - A jugar","short_name":"Gioval",',
                  '"id":"gioval-beta","name":"Mundo Gioval BETA","short_name":"Gioval BETA",', "manifest.json")
    escribir("manifest.json", m)

    # 5) index: título y cartel visible de "versión de prueba"
    ix = leer("index.html")
    ix = sustituir(ix, "<title>Mundo Gioval - A jugar</title>", "<title>Mundo Gioval BETA</title>", "index.html")
    ix = sustituir(ix, '<meta name="apple-mobile-web-app-title" content="Gioval">',
                   '<meta name="apple-mobile-web-app-title" content="Gioval BETA">', "index.html")
    cartel = ('<div style="position:fixed;left:0;right:0;bottom:0;z-index:99999;background:#d32f2f;color:#fff;'
              'font:700 11px sans-serif;text-align:center;padding:2px;pointer-events:none">'
              "BETA · versión de prueba · no es la app de todos los días</div>\n</body>")
    ix = sustituir(ix, "</body>", cartel, "index.html")
    escribir("index.html", ix)

    # 6) íconos con cinta roja "BETA" para distinguirla en la pantalla de inicio
    from PIL import Image, ImageDraw, ImageFont
    for nombre in ("icon-192.png", "icon-512.png", "icon-maskable.png", "apple-touch-icon.png"):
        ruta = os.path.join(src, nombre)
        im = Image.open(ruta).convert("RGBA")
        w, h = im.size
        d = ImageDraw.Draw(im)
        alto = max(14, h // 5)
        d.rectangle([0, h - alto, w, h], fill=(211, 47, 47, 255))
        try:
            fuente = ImageFont.truetype("DejaVuSans-Bold.ttf", int(alto * 0.7))
        except OSError:
            fuente = ImageFont.load_default()
        d.text((w / 2, h - alto / 2), "BETA", fill="white", font=fuente, anchor="mm")
        im.convert("RGB" if nombre.startswith("apple") else "RGBA").save(ruta)

    # 7) verificación: ninguna clave de almacenamiento real puede haber quedado sin separar
    malas = []
    for base, _, archivos in os.walk(src):
        for nom in archivos:
            if not nom.endswith((".js", ".html", ".json")):
                continue
            ruta = os.path.join(base, nom)
            with open(ruta, encoding="utf-8") as f:
                txt = f.read()
            if nom.endswith(".js"):  # los comentarios no son claves: se ignoran para el control
                txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
                txt = re.sub(r"(?m)^\s*//.*$", "", txt)
            for lit in re.findall(r'["\'](gioval[\w\-]*)["\']', txt):
                if lit in PERMITIDAS or lit.startswith("giovalbeta"):
                    continue
                malas.append((os.path.relpath(ruta, src), lit))
    if malas:
        shutil.rmtree(tmp, ignore_errors=True)
        sys.exit("ERROR: quedaron nombres que podrían chocar con la app real: " + repr(sorted(set(malas))) +
                 "\nAgregalos a las sustituciones (o a PERMITIDAS si NO son claves de almacenamiento).")
    # y que ninguna llamada a localStorage/indexedDB use un literal "gioval" sin separar
    for base, _, archivos in os.walk(src):
        for nom in archivos:
            if nom.endswith(".js"):
                with open(os.path.join(base, nom), encoding="utf-8") as f:
                    txt = f.read()
                txt = re.sub(r"/\*.*?\*/", "", txt, flags=re.S)
                txt = re.sub(r"(?m)^\s*//.*$", "", txt)
                if re.search(r'(localStorage|indexedDB)[^;\n]{0,80}["\']gioval(-db|_[\w]+)?["\']', txt):
                    shutil.rmtree(tmp, ignore_errors=True)
                    sys.exit(f"ERROR: {nom} usa una clave de almacenamiento real.")

    shutil.rmtree(DESTINO, ignore_errors=True)
    shutil.move(src, DESTINO)
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"OK: {DESTINO} generada desde {ORIGEN} ({subprocess.check_output(['git','-C',RAIZ,'rev-parse','--short',ORIGEN],text=True).strip()})")


if __name__ == "__main__":
    main()
