#!/usr/bin/env python3
"""Genera los íconos del proyecto Android a partir de los íconos de la app web (gioval/icon-512.png e icon-maskable.png).

    python3 generar_iconos.py          # íconos normales (ya están commiteados; solo hace falta si cambia el ícono de la app)
    python3 generar_iconos.py --beta   # los mismos con una cinta roja "BETA" (lo usa el flujo de GitHub Actions para la variante beta)

Escribe en android/app/src/main/res/: mipmap-*/ic_launcher*.png, values/ic_launcher_background.xml y las pantallas de arranque (splash).
Si falta algún archivo esperado, FALLA en vez de seguir (así nunca queda una app a medio armar).
"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

AQUI = Path(__file__).resolve().parent
WEB = AQUI.parent / "gioval"
RES = AQUI / "android" / "app" / "src" / "main" / "res"
MORADO = (124, 77, 255, 255)
BETA = "--beta" in sys.argv

# tamaños en px por densidad: ícono clásico (48 dp) y capa de adelante del ícono adaptable (108 dp)
DENSIDADES = {"mdpi": (48, 108), "hdpi": (72, 162), "xhdpi": (96, 216), "xxhdpi": (144, 324), "xxxhdpi": (192, 432)}


def fallar(msg):
    sys.exit("ERROR: " + msg)


def abrir(ruta):
    if not ruta.exists():
        fallar("no encuentro %s" % ruta)
    return Image.open(ruta).convert("RGBA")


def cinta(im):
    """Cinta roja 'BETA' atravesada en la parte baja (dentro de la zona segura del ícono adaptable)."""
    w, h = im.size
    d = ImageDraw.Draw(im)
    y0, y1 = int(h * 0.62), int(h * 0.74)
    d.rectangle([0, y0, w, y1], fill=(211, 47, 47, 255))
    try:
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", int((y1 - y0) * 0.75))
    except OSError:
        f = ImageFont.load_default()
    d.text((w / 2, (y0 + y1) / 2), "BETA", fill="white", font=f, anchor="mm")
    return im


def redondeado(im, radio_rel):
    w, h = im.size
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, w - 1, h - 1], radius=int(w * radio_rel), fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im, (0, 0), m)
    return out


def circulo(im):
    w, h = im.size
    m = Image.new("L", (w, h), 0)
    ImageDraw.Draw(m).ellipse([0, 0, w - 1, h - 1], fill=255)
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    out.paste(im, (0, 0), m)
    return out


def main():
    base = abrir(WEB / "icon-512.png")
    maskable = abrir(WEB / "icon-maskable.png")
    if BETA:
        base, maskable = cinta(base.copy()), cinta(maskable.copy())
    for dens, (clasico, adaptable) in DENSIDADES.items():
        carpeta = RES / ("mipmap-" + dens)
        if not carpeta.is_dir():
            fallar("no existe %s (¿corriste 'npx cap add android'?)" % carpeta)
        redondeado(base.resize((clasico, clasico), Image.LANCZOS), 0.18).save(carpeta / "ic_launcher.png")
        circulo(base.resize((clasico, clasico), Image.LANCZOS)).save(carpeta / "ic_launcher_round.png")
        maskable.resize((adaptable, adaptable), Image.LANCZOS).save(carpeta / "ic_launcher_foreground.png")
    fondo = RES / "values" / "ic_launcher_background.xml"
    if not fondo.exists():
        fallar("no existe %s" % fondo)
    fondo.write_text('<?xml version="1.0" encoding="utf-8"?>\n<resources>\n    <color name="ic_launcher_background">#7C4DFF</color>\n</resources>\n', encoding="utf-8")
    # pantallas de arranque (Android 11 o menos y respaldo): fondo morado con el ícono al medio
    chicas = sorted(RES.glob("drawable*/splash.png"))
    if not chicas:
        fallar("no encuentro los splash.png del proyecto")
    for ruta in chicas:
        w, h = Image.open(ruta).size
        im = Image.new("RGBA", (w, h), MORADO)
        lado = int(min(w, h) * 0.34)
        ic = redondeado(base.resize((lado, lado), Image.LANCZOS), 0.2)
        im.paste(ic, ((w - lado) // 2, (h - lado) // 2), ic)
        im.convert("RGB").save(ruta)
    print("Íconos %s generados en %s" % ("BETA" if BETA else "normales", RES))


main()
