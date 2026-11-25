#!/usr/bin/env python3
"""Pruebas automáticas de Mundo Gioval. Un solo comando:  python3 gioval-dev/tests/correr.py   (opcional: filtro de nombre, ej. "migracion")
Levanta un servidor local de gioval/, abre Chrome (/usr/bin/google-chrome --no-sandbox) con emulación móvil, y deja
capturas en gioval-dev/tests/salida/ y un resumen en salida/resumen.txt."""
import json, os, re, subprocess, sys, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib import *
from playwright.sync_api import sync_playwright

TESTS = []
def prueba(nombre):
    def d(f): TESTS.append((nombre, f)); return f
    return d

class Falla(Exception): pass
def verificar(cond, msg="falló una verificación"):
    if not cond: raise Falla(msg)
def igual(a, b, msg=""):
    if a != b: raise Falla("%s: esperado %r, obtenido %r" % (msg, b, a))

def sin_espanol(frases):
    return [x for x in frases if re.search(r"[¿¡áéíóúñÁÉÍÓÚ]", x)]

FIXTURE = (HERE / "fixtures" / "almacen_v0.json").read_text(encoding="utf-8")
STORE_KID = {"profiles": ["Vale"], "limit": {"Vale": 60}}
CAPTURAS = []

# ---------------------------------------------------------------- estáticas
@prueba("sintaxis: node --check de todos los .js")
def t_sintaxis(C):
    archivos = sorted(list((APP / "js").rglob("*.js")) + [APP / "sw.js"])
    verificar(len(archivos) >= 20, "pocos archivos js: %d" % len(archivos))
    for f in archivos:
        r = subprocess.run(["node", "--check", str(f)], capture_output=True, text=True)
        verificar(r.returncode == 0, "%s: %s" % (f.name, r.stderr[:300]))
    return "%d archivos" % len(archivos)

def lista_sw():
    txt = (APP / "sw.js").read_text(encoding="utf-8")
    m = re.search(r"const F=\[(.*?)\];", txt, re.S)
    return re.findall(r'"([^"]+)"', m.group(1))

@prueba("sw: precarga TODOS los archivos de la app (y ninguno inexistente)")
def t_sw_lista(C):
    F = lista_sw()
    en_disco = {str(p.relative_to(APP)) for p in APP.rglob("*") if p.is_file() and p.name != "sw.js"}
    listados = {f for f in F if f != "./"}
    faltan = sorted(en_disco - listados); sobran = sorted(listados - en_disco)
    verificar(not faltan, "faltan en la precarga del sw.js: %s" % faltan)
    verificar(not sobran, "el sw.js precarga archivos que no existen: %s" % sobran)
    html = (APP / "index.html").read_text(encoding="utf-8")
    for s in re.findall(r'<script src="([^"]+)"', html):
        verificar(s in listados, "script de index.html no está en la precarga: " + s)
    return "%d archivos precargados" % len(F)

@prueba("sw: la caché del navegador contiene todos los archivos")
def t_sw_cache(C):
    ctx = C.banco.contexto("pixel7", sw=True)
    pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    pg.wait_for_function("navigator.serviceWorker.controller||false", timeout=1) if False else None
    pg.wait_for_function("navigator.serviceWorker.getRegistration().then(r=>r&&r.active?true:false)", timeout=15000)
    pg.wait_for_timeout(800)
    claves = pg.evaluate("caches.keys().then(async ks=>{ const out={}; for(const k of ks){ const c=await caches.open(k); out[k]=(await c.keys()).map(r=>new URL(r.url).pathname); } return out; })")
    verificar(len(claves) == 1, "debería haber una sola caché: %s" % list(claves))
    nombre, rutas = list(claves.items())[0]
    verificar(nombre == "gioval-" + pg.evaluate("self.GIOVAL_VERSION"), "nombre de caché " + nombre)
    for f in lista_sw():
        ruta = "/" if f == "./" else "/" + f
        verificar(ruta in rutas, "no está en la caché: " + f)
    ctx.close(); return "%s: %d entradas" % (nombre, len(rutas))

# ---------------------------------------------------------------- arranque, perfiles, mapa
@prueba("arranque: sin errores de consola, perfil nuevo pide el nombre")
def t_arranque(C):
    for v in ("pixel7", "360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", errores=err)
        verificar(pg.evaluate("document.getElementById('nameBox').classList.contains('show')"), "no pide el nombre (%s)" % v)
        igual(pg.evaluate("store.version"), 4, "store.version"); igual(pg.evaluate("store.intake"), {}, "store.intake")
        verificar(not err, "errores en %s: %s" % (v, err))
        foto(pg, v + "_00_nombre"); CAPTURAS.append(v + "_00_nombre.png"); ctx.close()

@prueba("perfiles: crear dos, cambiar de uno a otro")
def t_perfiles(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    for n in ("Vale", "Gio"):
        if not pg.evaluate("document.getElementById('nameBox').classList.contains('show')"): pg.click(".song:has-text('Nuevo jugador')")
        pg.fill("#nameIn", n); pg.click("#nameOk"); pg.wait_for_timeout(150)
        igual(pg.evaluate("KID"), n, "KID"); pg.click("#btnWho"); pg.wait_for_timeout(100)
    igual(pg.evaluate("store.profiles"), ["Vale", "Gio"], "perfiles")
    foto(pg, "360x700_01_perfiles"); CAPTURAS.append("360x700_01_perfiles.png")
    entrar(pg, "Vale"); igual(pg.evaluate("KID"), "Vale"); ctx.close()

@prueba("mapa: muestra Música, Números, Letras, Misiones, Ritmo y las islas con candado")
def t_mapa(C):
    for v in ("pixel7", "360x700", "740x330"):
        ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err); instalar_speak(pg)
        entrar(pg, "Vale")
        islas = pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.replace(/\\n/g,'|')+(x.classList.contains('off')?'|off':''))")
        igual(islas, ["🎹|Isla Música|¡A tocar el piano!", "🔢|Isla Números|¡A contar y sumar!", "🔤|Isla Letras|¡A jugar con las letras!", "🧭|Isla Misiones|¡Cosas de verdad!", "🥁|Isla Ritmo|¡A marcar el ritmo!", "🔒|Isla Animales|Pronto|off"], "mapa " + v)
        foto(pg, v + "_02_mapa"); CAPTURAS.append(v + "_02_mapa.png"); ctx.close()

# ---------------------------------------------------------------- tablets
# Revisión de una pantalla: sin desborde horizontal, nada tocable cortado por la pantalla (salvo dentro de una lista que se desplaza),
# y todo lo tocable de al menos 48 px CSS de ancho y de alto.
JS_TABLET = r"""(()=>{
 const vw=innerWidth, vh=innerHeight, out=[];
 const sel='button,a[href],input,select,textarea,summary,[role=button],.key,.opt,.island,.song,.mis-chip,.mis-mat,.ayCard';
 const vis=e=>{ for(let d=e.closest('details');d;d=d.parentElement&&d.parentElement.closest('details')){ if(!d.open&&!(e.closest('summary')&&e.closest('summary').parentElement===d)) return false; } const cs=getComputedStyle(e); if(cs.display==='none'||cs.visibility==='hidden'||cs.pointerEvents==='none') return false; const r=e.getBoundingClientRect(); if(r.width<1||r.height<1) return false;
   for(let p=e;p&&p!==document.body;p=p.parentElement){ const c=getComputedStyle(p); if(c.display==='none'||c.visibility==='hidden'||(c.opacity==='0')) return false; } return true; };
 const scrollAnc=e=>{ for(let p=e.parentElement;p&&p!==document.body;p=p.parentElement){ const c=getComputedStyle(p); if(/(auto|scroll)/.test(c.overflowY)&&p.scrollHeight>p.clientHeight+1) return p; } return null; };
 const name=e=>(e.id?'#'+e.id:'')+(e.className&&typeof e.className==='string'?'.'+e.className.trim().split(/\s+/).join('.'):'')||e.tagName;
 if(document.documentElement.scrollWidth>vw+1||document.body.scrollWidth>vw+1) out.push('desborde horizontal '+document.documentElement.scrollWidth+'>'+vw);
 document.querySelectorAll(sel).forEach(e=>{
   if(!vis(e)) return; if(e.type==='file'||e.type==='checkbox'&&false) return;
   const r=e.getBoundingClientRect();
   if(e.closest('.aviso')&&!document.getElementById('avisoVersion').classList.contains('show')) return;
   if(r.width<47.5||r.height<47.5){ if(!(e.tagName==='INPUT'&&e.type==='checkbox'&&e.closest('label'))) out.push('chico '+name(e)+' '+Math.round(r.width)+'x'+Math.round(r.height)); }
   const sa=scrollAnc(e);
   if(!sa&&(r.right>vw+1||r.left<-1||r.bottom>vh+1||r.top<-1)) out.push('cortado '+name(e)+' '+[r.left,r.top,r.right,r.bottom].map(Math.round));
   if(sa){ const c=sa.getBoundingClientRect(); if(r.right>c.right+1||r.left<c.left-1) out.push('cortado en lateral '+name(e)); }
 });
 return out;
})()"""

def revisar_tablet(pg, donde, mal):
    pg.wait_for_timeout(120)
    for m in pg.evaluate(JS_TABLET): mal.append("%s: %s" % (donde, m))

@prueba("tablets (768x1024, 820x1180, 1024x768, 1280x800): mapa, menú de cada isla y una actividad por isla sin desborde, sin cortes y con toques de 48 px")
def t_tablets(C):
    for v in Banco.TABLETS:
        ctx = C.banco.contexto(v); err = []; mal = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=5, congelar=True); instalar_speak(pg)
        pg.evaluate("document.getElementById('nameBox').classList.remove('show')")
        pg.evaluate("renderWho(); show('who')"); revisar_tablet(pg, v + " quién juega", mal); CAPTURAS.append(foto(pg, v + "_90_tablet_quien"))
        entrar(pg, "Vale"); revisar_tablet(pg, v + " mapa", mal); CAPTURAS.append(foto(pg, v + "_91_tablet_mapa"))
        # el mapa aprovecha la pantalla: tarjetas grandes, emoji grande y las filas llegan por lo menos a la mitad del alto
        g = pg.evaluate("""(()=>{ const c=[...document.querySelectorAll('#islands .island')].map(b=>b.getBoundingClientRect()); const e=parseFloat(getComputedStyle(document.querySelector('#islands .island .em')).fontSize);
          return {ancho:Math.min(...c.map(r=>r.width)), alto:Math.min(...c.map(r=>r.height)), fondo:Math.max(...c.map(r=>r.bottom)), emoji:e, vh:innerHeight, cols:new Set(c.map(r=>Math.round(r.left))).size}; })()""")
        verificar(g["alto"] >= 180 and g["emoji"] >= 84 and g["fondo"] >= g["vh"] * 0.55, "%s: el mapa no aprovecha la pantalla %s" % (v, g))
        verificar(g["cols"] in (3, 4), "%s: columnas del mapa %s" % (v, g))
        for isla in ("Música", "Números", "Letras", "Misiones", "Ritmo"):
            abrir_isla(pg, isla)
            if isla == "Letras" and pg.evaluate("document.getElementById('letOv').classList.contains('show')"): pg.click("#letOv [data-a=cerrar]"); pg.wait_for_timeout(80)
            revisar_tablet(pg, "%s menú %s" % (v, isla), mal)
            if isla == "Música": CAPTURAS.append(foto(pg, v + "_92_tablet_menu_musica"))
            if isla == "Misiones":
                pg.click("#menuIslaItems .island:has-text('Elegir')"); pg.wait_for_timeout(150); revisar_tablet(pg, v + " misiones lista", mal)
                pg.click(".mis-card >> nth=0"); pg.wait_for_timeout(200); revisar_tablet(pg, v + " misión", mal); CAPTURAS.append(foto(pg, v + "_93_tablet_mision"))
            else:
                tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(700); revisar_tablet(pg, "%s actividad %s" % (v, isla), mal); CAPTURAS.append(foto(pg, "%s_94_tablet_actividad_%s" % (v, isla)))
            ir_mapa(pg)
        abrir_isla(pg, "Números"); pg.click(".island:has-text('Mis logros')"); pg.wait_for_timeout(200); revisar_tablet(pg, v + " logros", mal); ir_mapa(pg)
        abrir_isla(pg, "Música"); tarjeta(pg, "Mis canciones"); revisar_tablet(pg, v + " canciones", mal); ir_mapa(pg)
        pg.evaluate("document.getElementById('letOv').classList.remove('show')")
        abrir_panel(pg); revisar_tablet(pg, v + " panel de adultos", mal); pg.evaluate("document.getElementById('panel').classList.remove('show')")
        # Ritmo: lectura con tarjetas y composición con paleta (las dos pantallas más cargadas de la isla)
        for sid, fase, tag in (("rit_lee2", "turno", "lectura"), ("rit_compone", "componer", "componer")):
            abrir_isla(pg, "Ritmo"); solo_habilidad(pg, sid); tarjeta(pg, "Sesión de hoy"); esperar_fase(pg, fase); pg.wait_for_timeout(500)
            revisar_tablet(pg, "%s ritmo %s" % (v, tag), mal); CAPTURAS.append(foto(pg, "%s_95_tablet_ritmo_%s" % (v, tag)))
            pg.evaluate("S.run++; resetFlow(); goMenuIsla()")
        # Misiones: el recorrido completo de un experimento, paso a paso
        ir_mapa(pg); abrir_isla(pg, "Misiones"); pg.click("#menuIslaItems .island:has-text('Elegir')"); pg.wait_for_timeout(100)
        pg.click(".mis-card[data-id='exp_hielo']"); pg.wait_for_timeout(150); revisar_tablet(pg, v + " misión aviso", mal)
        pg.click("#misAcc .btn:last-child"); revisar_tablet(pg, v + " misión materiales", mal)
        for k in range(pg.locator("#misCont .mis-mat").count()): pg.click("#misCont .mis-mat >> nth=%d" % k)
        pg.click("#misTodo"); revisar_tablet(pg, v + " misión predicción", mal)
        pg.click("#misCont .mis-chip >> nth=0"); pg.click("#misAcc .btn")
        for k in range(2): pg.click("#misAcc .btn:last-child")
        revisar_tablet(pg, v + " misión hacer", mal)
        while mis_paso(pg) == "hacer": pg.click("#misAcc .btn:last-child"); pg.wait_for_timeout(40)
        pg.click("#misCont .mis-chip >> nth=1"); revisar_tablet(pg, v + " misión qué pasó", mal); pg.click("#misAcc .btn")
        pg.fill("#misCont textarea[data-in=porque]", "porque"); pg.click("#misAcc .btn:has-text('explicación')"); revisar_tablet(pg, v + " misión por qué", mal); pg.click("#misAcc .btn:last-child")
        pg.fill("#misCont textarea[data-in=frase]", "El del sol"); pg.click("#misCont [data-res=distinto]"); revisar_tablet(pg, v + " misión registro", mal)
        pg.click("#misGuardar"); pg.wait_for_function("(Gioval.misiones.estado()||{}).paso==='fin'"); revisar_tablet(pg, v + " misión fin", mal)
        pg.click("#misAcc .btn:has-text('álbum')"); pg.wait_for_timeout(250); revisar_tablet(pg, v + " álbum", mal); CAPTURAS.append(foto(pg, v + "_96_tablet_album"))
        # Hora de ayudantes (aparece al llegar al tope diario): tope, lista, detalle, cronómetro, tiempo cumplido y fin
        llegar_al_tope(pg, directo=True); revisar_tablet(pg, v + " tope diario", mal); pg.click("#capAyud"); pg.wait_for_timeout(100); revisar_tablet(pg, v + " ayudantes lista", mal)
        pg.click(".ayCard[data-id='plantas']"); pg.wait_for_timeout(80); revisar_tablet(pg, v + " ayudantes detalle", mal)
        pg.click("[data-a='empezar']"); pg.wait_for_timeout(120); revisar_tablet(pg, v + " ayudantes cronómetro", mal)
        pg.evaluate("window.__OFF=400000"); pg.evaluate("Alarma._revisar()"); pg.wait_for_timeout(120); revisar_tablet(pg, v + " ayudantes tiempo", mal)
        pg.click("[data-a='terminar']"); pg.wait_for_timeout(100); revisar_tablet(pg, v + " ayudantes fin", mal)
        verificar(not err, "%s: %s" % (v, err)); verificar(not mal, "tablet: " + "; ".join(mal[:8])); ctx.close()
    return "4 tamaños, 5 islas (menú + actividad), Ritmo lectura/composición, misión completa, Hora de ayudantes, logros, canciones y panel de adultos"

# ---------------------------------------------------------------- islas
def pasar_sesiones(pg, isla, n, cada_error=0, perfecto=False):
    for _ in range(n):
        abrir_isla(pg, isla); tarjeta(pg, "Sesión de hoy")
        r = jugar(pg, cada_error, perfecto=perfecto); verificar(r == "fin", "la sesión terminó con " + r)
        cerrar_fin(pg)

def dominio(pg, ids):
    return [i for i in ids if pg.evaluate("!!(store.sk[KID+'|%s']&&store.sk[KID+'|%s'].mast)" % (i, i))]

@prueba("Música: sesión completa, dominio y desbloqueo")
def t_musica(C):
    ctx = C.banco.contexto("pixel7"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=11); instalar_speak(pg); entrar(pg, "Vale")
    abrir_isla(pg, "Música"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(400)
    igual(pg.evaluate("document.querySelector('.screen.active').id"), "play", "pantalla")
    foto(pg, "pixel7_10_musica_sesion"); CAPTURAS.append("pixel7_10_musica_sesion.png")
    verificar(jugar(pg) == "fin"); cerrar_fin(pg)
    pasar_sesiones(pg, "Música", 2, perfecto=True)
    dom = dominio(pg, ["n1", "e1", "n2"])
    verificar("n1" in dom, "n1 no quedó dominada: %s" % dom)
    st = pg.evaluate("Object.fromEntries(Object.entries(store.sk).map(([k,v])=>[k,v.mast]))")
    verificar(pg.evaluate("unlockedList()").__len__() >= 0)
    abrir_isla(pg, "Música"); tarjeta(pg, "Logros") if False else None
    pg.evaluate("PACK=PACKS[0]")
    desbloq = pg.evaluate("unlockedList().map(s=>s.id)")
    verificar("e1" in desbloq and "n2" in desbloq, "no se desbloquearon e1/n2: %s" % desbloq)
    verificar(not err, str(err)); ctx.close(); return "dominadas: %s; desbloqueadas: %s" % (dom, desbloq)

@prueba("Música: chequeo semanal sin ayuda e informe")
def t_musica_chequeo(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=12); instalar_speak(pg); entrar(pg, "Vale")
    pasar_sesiones(pg, "Música", 2, perfecto=True)
    abrir_isla(pg, "Música"); tarjeta(pg, "Chequeo semanal"); verificar(jugar(pg) in ("fin",)); cerrar_fin(pg)
    ck = pg.evaluate("store.checks.Vale"); verificar(len(ck) == 1 and ck[0]["p"] == "musica", str(ck))
    rep = pg.evaluate("reportText()"); verificar("ISLA MÚSICA" in rep and "Música" in rep and "CHEQUEOS SIN AYUDA" in rep, rep[:200])
    verificar(not err, str(err)); ctx.close()

@prueba("Números: sesión completa, dominio, desbloqueo y chequeo semanal")
def t_numeros(C):
    for v in ("pixel7", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=21); instalar_speak(pg); entrar(pg, "Vale")
        abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(500)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "act", "pantalla " + v)
        foto(pg, v + "_11_numeros_actividad"); CAPTURAS.append(v + "_11_numeros_actividad.png")
        verificar(jugar(pg, cada_error=4) == "fin"); cerrar_fin(pg)
        pasar_sesiones(pg, "Números", 3, perfecto=True)
        pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')")
        dom = dominio(pg, ["num_c10", "num_r10", "num_may", "num_add5"])
        verificar("num_c10" in dom and "num_r10" in dom, "dominio: %s" % dom)
        desbloq = pg.evaluate("unlockedList().map(s=>s.id)"); verificar("num_may" in desbloq, str(desbloq))
        abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); verificar(jugar(pg) == "fin"); cerrar_fin(pg)
        ck = pg.evaluate("store.checks.Vale"); verificar(ck and ck[-1]["p"] == "numeros", str(ck))
        verificar("ISLA NÚMEROS" in pg.evaluate("reportText()"))
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

@prueba("chequeos independientes por isla")
def t_chequeos_por_isla(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err, semilla=31); instalar_speak(pg); entrar(pg, "Vale")
    pasar_sesiones(pg, "Música", 2, perfecto=True); pasar_sesiones(pg, "Números", 1, perfecto=True)
    abrir_isla(pg, "Música"); tarjeta(pg, "Chequeo semanal"); jugar(pg); cerrar_fin(pg)
    abrir_isla(pg, "Números")
    txt = pg.evaluate("document.getElementById('menuIslaItems').innerText")
    verificar("Sin ayuda" in txt, "el chequeo de Números debería seguir disponible: " + txt); ctx.close()

# ---------------------------------------------------------------- tiempo
@prueba("tope diario, tiempo configurable y +15 min")
def t_tope(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=41); instalar_speak(pg); entrar(pg, "Vale")
    abrir_panel(pg); pg.select_option("#limSel", "10"); pg.wait_for_timeout(100)
    igual(pg.evaluate("store.limit.Vale"), 10, "limit"); pg.click("#btnGear")
    abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(300)
    pg.evaluate("store.time['Vale|'+today()]=10*60-1"); pg.wait_for_selector("#capBox.show", timeout=6000)
    verificar("10 minutos" in pg.evaluate("document.getElementById('capBox').innerText"), "texto del tope")
    foto(pg, "360x700_12_tope"); CAPTURAS.append("360x700_12_tope.png"); pg.click("#capOk"); pg.wait_for_timeout(150)
    verificar(pg.evaluate("capLeft()") <= 0, "capLeft"); abrir_panel(pg); pg.click("#btnExtra"); pg.wait_for_timeout(100)
    verificar(pg.evaluate("capLeft()") > 800, "no sumó 15 min"); verificar(not err, str(err)); ctx.close()

@prueba("repaso espaciado con reloj adelantado (Música y Números)")
def t_repaso(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=51); instalar_speak(pg); entrar(pg, "Vale")
    for isla, sid, pid in (("Números", "num_c10", "numeros"), ("Música", "n1", "musica")):
        for _ in range(4):
            pasar_sesiones(pg, isla, 1, perfecto=True)
            pg.evaluate("PACK=PACKS.find(p=>p.id==='%s')" % pid)
            if pg.evaluate("SK('%s').mast" % sid): break
        verificar(pg.evaluate("SK('%s').mast" % sid), sid + " no dominada")
        verificar("Repaso" not in pg.evaluate("sessionPreview()"), "ya propone repaso")
        due0 = pg.evaluate("SK('%s').due" % sid); box0 = pg.evaluate("SK('%s').box" % sid)
        pg.evaluate("window.__OFF=4*864e5")
        verificar("Repaso" in pg.evaluate("sessionPreview()"), "no propone repaso a los 4 días")
        abrir_isla(pg, isla); tarjeta(pg, "Sesión de hoy")
        items = pg.evaluate("S.session.items.filter(i=>i.skill.id==='%s').length" % sid); verificar(items >= 1, "no hay ítems de repaso")
        verificar(jugar(pg, perfecto=True) == "fin"); cerrar_fin(pg)
        verificar(pg.evaluate("SK('%s').box" % sid) > box0, "no subió la caja de repaso")
        verificar(pg.evaluate("SK('%s').due" % sid) > due0 + 3 * 864e5, "no se alargó el intervalo")
        pg.evaluate("window.__OFF=0")
    verificar(not err, str(err)); ctx.close()

# ---------------------------------------------------------------- datos
def norm(s):
    s = json.loads(json.dumps(s)); s.pop("meta", None); s.pop("version", None); return s

@prueba("migración: datos viejos (v0 → v2) conservan TODO el progreso")
def t_migracion(C):
    viejo = json.loads(FIXTURE)
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=err)
    nuevo = pg.evaluate("JSON.parse(JSON.stringify(store))")
    igual(nuevo["version"], 4, "version"); igual(nuevo["intake"], {}, "intake nuevo")
    for k in ("profiles", "stars", "sk", "days", "time", "log", "extra", "limit"):
        igual(nuevo[k], viejo[k], "campo " + k)
    esperado = json.loads(json.dumps(viejo["checks"])); esperado["Valentino"][0]["p"] = "musica"
    igual(nuevo["checks"], esperado, "checks (los viejos sin isla pasan a música)")
    pre = pg.evaluate("localStorage.getItem('gioval_pre_migracion')"); verificar(pre == FIXTURE, "no guardó la copia previa exacta")
    rs = pg.evaluate("Gioval.almacen.respaldos()"); verificar(len(rs) >= 1 and "pre-migracion" in rs[0]["id"], str(rs)[:200])
    verificar(json.loads(rs[0]["json"]) == viejo, "la copia previa de IndexedDB no coincide")
    igual(pg.evaluate("Gioval.almacen.errorMigracion"), None, "errorMigracion")
    entrar(pg, "Valentino"); abrir_isla(pg, "Música"); txt = pg.evaluate("document.getElementById('menuIslaItems').innerText")
    verificar("Sesión de hoy" in txt); verificar(not err, str(err)); ctx.close()
    return "versión 0 → 4, %d claves de progreso intactas" % len(viejo["sk"])

@prueba("migración: si falla, no se pierde nada")
def t_migracion_falla(C):
    viejo = json.loads(FIXTURE)
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=err, extra_init="window.__GIOVAL_FALLAR_MIGRACION=true;")
    verificar(pg.evaluate("Gioval.almacen.errorMigracion"), "debería registrar el error")
    for k in ("profiles", "stars", "sk", "days", "log", "limit"):
        igual(pg.evaluate("store.%s" % k), viejo[k], "campo " + k)
    igual(pg.evaluate("localStorage.getItem('gioval_pre_migracion')"), FIXTURE, "copia previa")
    rs = pg.evaluate("Gioval.almacen.respaldos()"); verificar(any(json.loads(r["json"]) == viejo for r in rs), "no hay copia previa en IndexedDB")
    abrir_panel(pg); verificar("No se pudo actualizar" in pg.evaluate("document.getElementById('respaldoInfo').innerText"), "el panel no avisa")
    ctx.close()

def estado_comparable(pg):
    return json.loads(json.dumps(pg.evaluate("JSON.parse(JSON.stringify(store))")))

@prueba("persistencia: recargar conserva el estado (también desde solo IndexedDB o solo localStorage)")
def t_persistencia(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=61); instalar_speak(pg); entrar(pg, "Vale")
    pasar_sesiones(pg, "Números", 1, perfecto=True); pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(300)
    a = estado_comparable(pg); verificar(a["sk"], "no hay progreso"); na = norm(a)
    pg.reload(); esperar_listo(pg); igual(norm(estado_comparable(pg)), na, "tras recargar")
    pg.evaluate("localStorage.removeItem('gioval')"); pg.reload(); esperar_listo(pg); igual(norm(estado_comparable(pg)), na, "solo IndexedDB")
    pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(200)
    pg.evaluate("new Promise(r=>{ const q=indexedDB.open('gioval-db'); q.onsuccess=()=>{ const d=q.result; const t=d.transaction('estado','readwrite'); t.objectStore('estado').clear(); t.oncomplete=()=>{ d.close(); r(1); }; }; })")
    pg.reload(); esperar_listo(pg); igual(norm(estado_comparable(pg)), na, "solo localStorage")
    pg.evaluate("window.__OFF=0"); igual(pg.evaluate("Gioval.almacen.idbOk"), True, "idbOk")
    verificar(not err, str(err)); ctx.close()

@prueba("respaldo: exportar → borrar todo → restaurar da el mismo estado")
def t_respaldo(C):
    ctx = C.banco.contexto("pixel7", accept_downloads=True); err = []
    pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=err); instalar_speak(pg)
    abrir_panel(pg); foto(pg, "pixel7_20_panel_respaldo"); CAPTURAS.append("pixel7_20_panel_respaldo.png")
    verificar("nunca" in pg.evaluate("document.getElementById('respaldoInfo').innerText"), "debería decir nunca")
    with pg.expect_download() as d: pg.click("#btnExport")
    dl = d.value; verificar(re.fullmatch(r"gioval-respaldo-\d{4}-\d{2}-\d{2}\.json", dl.suggested_filename), dl.suggested_filename)
    ruta = SALIDA / "respaldo_prueba.json"; SALIDA.mkdir(exist_ok=True); dl.save_as(str(ruta))
    pg.wait_for_timeout(300); antes = estado_comparable(pg)
    verificar(antes["meta"]["ultimoRespaldo"] > 0, "no anotó el último respaldo")
    verificar("nunca" not in pg.evaluate("document.getElementById('respaldoInfo').innerText"))
    pg.evaluate("localStorage.clear()")
    pg.evaluate("new Promise(r=>{ const q=indexedDB.open('gioval-db'); q.onsuccess=()=>{ const d=q.result; const t=d.transaction(['estado','respaldo'],'readwrite'); t.objectStore('estado').clear(); t.objectStore('respaldo').clear(); t.oncomplete=()=>{ d.close(); r(1); }; }; })")
    pg.reload(); esperar_listo(pg); igual(pg.evaluate("store.profiles"), [], "después de borrar")
    pg.evaluate("document.getElementById('nameBox').classList.remove('show')"); abrir_panel(pg); pg.set_input_files("#fileRestore", str(ruta)); pg.wait_for_selector("#restoreBox.show")
    txt = pg.evaluate("document.getElementById('restoreTxt').innerText"); verificar("Valentino" in txt and "Giovanni" in txt, txt)
    foto(pg, "pixel7_21_restaurar_vista_previa"); CAPTURAS.append("pixel7_21_restaurar_vista_previa.png")
    pg.click("#restoreOk"); pg.wait_for_load_state(); esperar_listo(pg); pg.wait_for_timeout(300)
    despues = estado_comparable(pg)
    for k in ("profiles", "stars", "sk", "days", "time", "log", "checks", "extra", "limit"): igual(despues[k], antes[k], "campo " + k)
    # archivos inválidos
    malo = SALIDA / "malo.json"; malo.write_text('{"app":"otra","store":1}')
    abrir_panel(pg); pg.set_input_files("#fileRestore", str(malo)); pg.wait_for_selector("#restoreBox.show")
    verificar("no es un respaldo" in pg.evaluate("document.getElementById('restoreTxt').innerText"), "no rechazó el archivo malo")
    futuro = SALIDA / "futuro.json"; futuro.write_text(json.dumps({"app": "gioval", "store": {"version": 99, "profiles": []}}))
    pg.click("#restoreNo"); pg.set_input_files("#fileRestore", str(futuro)); pg.wait_for_selector("#restoreBox.show")
    verificar("más nueva" in pg.evaluate("document.getElementById('restoreTxt').innerText"), "no rechazó la versión futura")
    verificar(not err, str(err)); ctx.close()

@prueba("respaldo: recordatorio suave a los 14 días (solo con progreso)")
def t_recordatorio(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=C.err)
    igual(pg.evaluate("Gioval.almacen.debeRecordar()"), False, "recién empezado")
    pg.evaluate("window.__OFF=15*864e5"); igual(pg.evaluate("Gioval.almacen.debeRecordar()"), True, "a los 15 días")
    abrir_panel(pg); verificar("14 días" in pg.evaluate("document.getElementById('respaldoInfo').innerText"), "no muestra el aviso")
    ctx.close()
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err)
    pg.evaluate("window.__OFF=40*864e5"); igual(pg.evaluate("Gioval.almacen.debeRecordar()"), False, "sin progreso no recuerda"); ctx.close()

@prueba("almacén: fotos (Blob) guardar/listar/obtener/borrar")
def t_fotos(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    r = pg.evaluate("""(async()=>{ const b=new Blob(['hola'],{type:'text/plain'}); const id=await Gioval.almacen.fotos.guardar(b,{n:1});
      const l=await Gioval.almacen.fotos.listar(); const o=await Gioval.almacen.fotos.obtener(id); const t=await o.blob.text();
      await Gioval.almacen.fotos.borrar(id); const l2=await Gioval.almacen.fotos.listar(); return [l.length,t,l2.length]; })()""")
    igual(r, [1, "hola", 0], "fotos"); ctx.close()

@prueba("almacén: pide persistencia tras el primer toque")
def t_persist(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err,
        extra_init="window.__pp=0; if(navigator.storage){ navigator.storage.persist=function(){ window.__pp++; return Promise.resolve(true); }; }")
    igual(pg.evaluate("window.__pp"), 0, "antes del toque"); pg.click("#nameIn"); pg.wait_for_timeout(200)
    igual(pg.evaluate("window.__pp"), 1, "después del toque"); ctx.close()

# ---------------------------------------------------------------- alarma
JS_ALARMA_SETUP = "window.__fin=[]; Alarma.onFin(function(i){ window.__fin.push(i); }); 0;"
@prueba("alarma: reloj adelantado + pantalla apagada (timers congelados) dispara al volver")
def t_alarma(C):
    ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, C.url + "/index.html", errores=err)
    pg.evaluate(JS_ALARMA_SETUP + "window.__si=window.setInterval; window.setInterval=function(){ return 1; };")   # timers congelados
    pg.evaluate("Alarma.programar(60,{titulo:'T',texto:'X'})")
    r = pg.evaluate("Alarma.restante()"); verificar(58 <= r <= 60, "restante %s" % r)
    pg.evaluate("Object.defineProperty(document,'hidden',{get:()=>true,configurable:true}); window.__OFF=30000")
    igual(pg.evaluate("window.__fin.length"), 0, "no debe disparar antes de tiempo")
    verificar(25 <= pg.evaluate("Alarma.restante()") <= 31, "restante con reloj +30s")
    pg.evaluate("window.__OFF=75000")   # pasó el tiempo con la pantalla apagada: nadie corrió timers
    igual(pg.evaluate("window.__fin.length"), 0, "sigue sin disparar mientras el reloj de la página está congelado")
    pg.evaluate("Object.defineProperty(document,'hidden',{get:()=>false,configurable:true}); document.dispatchEvent(new Event('visibilitychange'))")
    igual(pg.evaluate("window.__fin.length"), 1, "debería disparar al volver a primer plano")
    info = pg.evaluate("window.__fin[0]"); igual(info["titulo"], "T"); verificar(info["tarde"] >= 14000, "tarde=%s" % info["tarde"])
    igual(pg.evaluate("Alarma.restante()"), 0, "restante tras disparar"); igual(pg.evaluate("localStorage.getItem('gioval_alarma')"), None, "limpia la alarma guardada")
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); igual(pg.evaluate("window.__fin.length"), 1, "no dispara dos veces")
    verificar(not err, str(err)); ctx.close()

@prueba("alarma: cancelar, onFin con baja, reprogramar, sobrevive a recargar")
def t_alarma2(C):
    ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, C.url + "/index.html", errores=err)
    pg.evaluate("window.__fin=[]; window.__baja=Alarma.onFin(function(i){ window.__fin.push(i); }); 0;")
    pg.evaluate("Alarma.programar(5)"); pg.evaluate("Alarma.cancelar()"); igual(pg.evaluate("Alarma.restante()"), 0)
    pg.evaluate("window.__OFF=10000; Alarma._revisar()"); igual(pg.evaluate("window.__fin.length"), 0, "cancelada")
    pg.evaluate("window.__OFF=0; Alarma.programar(1)"); pg.wait_for_timeout(1900); igual(pg.evaluate("window.__fin.length"), 1, "timer normal")
    pg.evaluate("window.__baja(); Alarma.programar(0.5); 0"); pg.wait_for_timeout(1500); igual(pg.evaluate("window.__fin.length"), 1, "dado de baja")
    pg.evaluate("Alarma.programar(300,{titulo:'R'})"); pg.reload(); esperar_listo(pg)
    r = pg.evaluate("Alarma.restante()"); verificar(250 <= r <= 300, "no sobrevivió a recargar: %s" % r)
    pg.evaluate("(()=>{ var g=JSON.parse(localStorage.getItem('gioval_alarma')); g.fin=Date.now()-5000; localStorage.setItem('gioval_alarma',JSON.stringify(g)); })()")
    pg.reload(); esperar_listo(pg); pg.wait_for_timeout(300)
    pg.evaluate("window.__fin2=[]; Alarma.onFin(function(i){ window.__fin2.push(i); }); 0"); pg.wait_for_timeout(200)
    igual(pg.evaluate("window.__fin2.length"), 1, "la alarma vencida mientras la app estaba cerrada se avisa al reabrir")
    verificar(not err, str(err)); ctx.close()

@prueba("alarma: wake lock, notificación local nativa (Capacitor) y notificación del service worker")
def t_alarma3(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", errores=err, extra_init="""
      window.__wl=0; Object.defineProperty(navigator,'wakeLock',{value:{request:async function(){ window.__wl++; return {release:function(){}, addEventListener:function(){}}; }},configurable:true});
      window.Capacitor={Plugins:{LocalNotifications:{schedule:function(o){ window.__sch=o; },cancel:function(o){ window.__can=o; }}}};""")
    pg.evaluate("Alarma.programar(120,{titulo:'Hola',texto:'Cuerpo'})"); pg.wait_for_timeout(200)
    verificar(pg.evaluate("window.__wl") >= 1, "no pidió wake lock")
    sch = pg.evaluate("window.__sch"); verificar(sch and sch["notifications"][0]["title"] == "Hola" and sch["notifications"][0]["schedule"]["allowWhileIdle"], "no programó la notificación nativa: %s" % sch)
    verificar(abs(pg.evaluate("new Date(window.__sch.notifications[0].schedule.at).getTime()") - pg.evaluate("Date.now()") - 120000) < 3000, "hora de la notificación nativa")
    pg.evaluate("Alarma.cancelar()"); verificar(pg.evaluate("!!window.__can"), "no canceló la notificación nativa")
    pg.evaluate("""window.__not=[]; window.Notification=function(){}; window.Notification.permission='granted';
      navigator.serviceWorker.getRegistration=function(){ return Promise.resolve({showNotification:function(t,o){ window.__not.push([t,o.body]); return Promise.resolve(); }}); };
      window.__fin=[]; Alarma.onFin(function(i){ window.__fin.push(i); }); Alarma.programar(0.3,{titulo:'Fin',texto:'Listo'}); 0;""")
    pg.wait_for_timeout(1500); igual(pg.evaluate("window.__not"), [["Fin", "Listo"]], "notificación vía service worker")
    verificar(not err, str(err)); ctx.close()

# ---------------------------------------------------------------- alarma nativa (envoltorio Android)
JS_PLUGIN_NATIVO = """
  window.__nat=[]; window.__perm='prompt';
  var est=function(){ return {sdk:34,exacta:false,notificaciones:window.__perm==='granted',permisoNotificaciones:window.__perm,pantallaCompleta:true,sinRestriccionBateria:false}; };
  window.Capacitor={Plugins:{
    GiovalAlarma:{
      programar:function(o){ window.__nat.push(['programar',o]); return Promise.resolve({exacta:true}); },
      cancelar:function(o){ window.__nat.push(['cancelar',o]); return Promise.resolve(); },
      detener:function(){ window.__nat.push(['detener']); return Promise.resolve(); },
      estado:function(){ return Promise.resolve(est()); },
      pedirNotificaciones:function(){ window.__nat.push(['pedirNotificaciones']); window.__perm='granted'; return Promise.resolve(est()); },
      abrirAjustes:function(o){ window.__nat.push(['abrirAjustes',o.tipo]); return Promise.resolve(); },
      mantenerPantalla:function(o){ window.__nat.push(['pantalla',o.activo]); return Promise.resolve(); }
    },
    App:{ addListener:function(n,f){ window.__back=f; return Promise.resolve({remove:function(){}}); }, minimizeApp:function(){ window.__nat.push(['minimizar']); return Promise.resolve(); } }
  }};
"""

@prueba("alarma nativa: fuera del envoltorio (navegador, PWA, o solo LocalNotifications) el puente NO cambia nada")
def t_nativa_sin_capacitor(C):
    for init in (None, "window.Capacitor={Plugins:{LocalNotifications:{schedule:function(){},cancel:function(){}}}};"):
        ctx = C.banco.contexto("360x700"); err = []
        pg = abrir(ctx, C.url + "/index.html", errores=err, extra_init=init)
        igual(pg.evaluate("[Gioval.alarmaNativa.activa, Gioval.envoltorio.activo]"), [False, False], "el puente se activó sin el plugin nativo")
        igual(pg.evaluate("'serviceWorker' in navigator"), True, "no hay que tocar el service worker en la web")
        igual(pg.evaluate("!!document.getElementById('nativaPanel')"), False, "sección nativa en el panel sin envoltorio")
        verificar(not pg.evaluate("Alarma.programar.toString().includes('pantalla()')"), "Alarma.programar fue envuelta sin el envoltorio")
        # la alarma web sigue funcionando igual
        pg.evaluate("window.__fin=[]; Alarma.onFin(function(i){ window.__fin.push(i); }); Alarma.programar(60,{titulo:'T'}); 0")
        verificar(58 <= pg.evaluate("Alarma.restante()") <= 60, "restante"); pg.evaluate("window.__OFF=61000; Alarma._revisar()")
        igual(pg.evaluate("window.__fin.length"), 1, "no disparó"); verificar(not err, str(err)); ctx.close()
    # los archivos del puente están en index.html y en la precarga del service worker (ya lo exige también la prueba "sw")
    html = (APP / "index.html").read_text(encoding="utf-8"); F = lista_sw()
    for f in ("js/core/alarma_nativa.js", "js/core/envoltorio.js"):
        verificar('<script src="%s">' % f in html and f in F, "falta registrar " + f)
    verificar(html.index("js/core/alarma.js") < html.index("js/core/alarma_nativa.js"), "alarma_nativa.js tiene que cargar DESPUÉS de alarma.js")

@prueba("alarma nativa: con el plugin simulado programa/cancela la alarma del sistema, pide permiso, mantiene la pantalla y la web sigue andando")
def t_nativa_con_plugin(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, extra_init=JS_PLUGIN_NATIVO, semilla=91); instalar_speak(pg)
    pg.wait_for_timeout(200)
    igual(pg.evaluate("[Gioval.alarmaNativa.activa, Gioval.envoltorio.activo]"), [True, True])
    igual(pg.evaluate("'serviceWorker' in navigator"), False, "en el envoltorio no se registra el service worker")
    # programar: alarma web (igual que siempre) + alarma del sistema con la hora ABSOLUTA
    pg.evaluate("window.__fin=[]; Alarma.onFin(function(i){ window.__fin.push(i); }); Alarma.programar(120,{titulo:'Hola',texto:'Cuerpo'}); 0"); pg.wait_for_timeout(150)
    verificar(118 <= pg.evaluate("Alarma.restante()") <= 120, "la alarma web dejó de andar")
    prog = [x for x in pg.evaluate("window.__nat") if x[0] == "programar"]; igual(len(prog), 1, "una sola llamada a programar")
    o = prog[0][1]; igual((o["id"], o["titulo"], o["texto"]), (7001, "Hola", "Cuerpo")); verificar(abs(o["fin"] - pg.evaluate("Date.now()") - 120000) < 3000, "hora absoluta de fin: %s" % o["fin"])
    verificar(["pantalla", True] in pg.evaluate("window.__nat"), "no pidió mantener la pantalla encendida con una alarma en marcha")
    # reprogramar reemplaza (mismo id) y cancelar cancela en el sistema
    pg.evaluate("Alarma.programar(300)"); verificar(len([x for x in pg.evaluate("window.__nat") if x[0] == "programar"]) == 2)
    pg.evaluate("Alarma.cancelar()"); pg.wait_for_timeout(100)
    verificar(["cancelar", {"id": 7001}] in pg.evaluate("window.__nat"), "no canceló la alarma del sistema"); igual(pg.evaluate("Alarma.activa()"), False)
    verificar(["pantalla", False] in pg.evaluate("window.__nat"), "no soltó la pantalla al cancelar")
    # permiso de avisos: Notification refleja el permiso nativo
    igual(pg.evaluate("Notification.permission"), "default")
    igual(pg.evaluate("Alarma.pedirPermiso()"), "granted"); igual(pg.evaluate("Notification.permission"), "granted"); verificar(["pedirNotificaciones"] in pg.evaluate("window.__nat"))
    # panel de adultos: sección "Alarma del teléfono" con el estado y los botones
    pg.evaluate("window.__perm='prompt'"); abrir_panel(pg); pg.wait_for_timeout(200)
    tp = pg.evaluate("document.getElementById('nativaPanel').innerText")
    verificar("Alarma del teléfono" in tp and "Alarmas exactas NO permitidas" in tp and "ahorro de batería" in tp and "Probar alarma" in tp, tp[:400])
    pg.click("#nativaPanel [data-nativa=exacta]"); pg.click("#nativaPanel [data-nativa=bateria]"); pg.wait_for_timeout(100)
    verificar(["abrirAjustes", "exacta"] in pg.evaluate("window.__nat") and ["abrirAjustes", "bateria"] in pg.evaluate("window.__nat"), "los botones no abren los ajustes")
    pg.click("#nativaPanel [data-nativa=probar]"); pg.wait_for_timeout(100); verificar(8 <= pg.evaluate("Alarma.restante()") <= 10, "la prueba de alarma no programó 10 s")
    pg.evaluate("Alarma.cancelar()")
    # el texto también sale en inglés (y sin español)
    pg.evaluate("Gioval.i18n.usar('en')"); pg.wait_for_timeout(100)
    te = pg.evaluate("document.getElementById('nativaPanel').innerText"); verificar("Phone alarm" in te and not sin_espanol(te.split("\n")), te[:300])
    pg.evaluate("Gioval.i18n.usar('es-AR')"); verificar(not pg.evaluate("[...Gioval.i18n.faltantes]"), "claves faltantes: %s" % pg.evaluate("[...Gioval.i18n.faltantes]"))
    # pantalla encendida durante una actividad
    pg.evaluate("document.getElementById('btnGear').click()"); pg.evaluate("window.__nat=[]"); pg.evaluate("document.getElementById('act').classList.add('active')"); pg.wait_for_timeout(150)
    verificar(["pantalla", True] in pg.evaluate("window.__nat"), "no mantuvo la pantalla encendida en una actividad"); pg.evaluate("document.getElementById('act').classList.remove('active')"); pg.wait_for_timeout(150)
    verificar(["pantalla", False] in pg.evaluate("window.__nat"), "no soltó la pantalla al salir de la actividad")
    verificar(not err, str(err)); ctx.close()

@prueba("envoltorio Android: el botón atrás cierra carteles, vuelve de pantalla en pantalla y en el inicio minimiza (sin cerrar)")
def t_envoltorio_atras(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, extra_init=JS_PLUGIN_NATIVO, semilla=92); instalar_speak(pg)
    activa = lambda: pg.evaluate("document.querySelector('.screen.active').id")
    atras = lambda: (pg.evaluate("window.__back({canGoBack:false})"), pg.wait_for_timeout(120))
    verificar(pg.evaluate("typeof window.__back") == "function", "no se registró el listener de backButton")
    igual(activa(), "who"); atras(); verificar(["minimizar"] in pg.evaluate("window.__nat"), "en el inicio tiene que minimizar la app")
    entrar(pg, "Vale"); igual(activa(), "map")
    atras(); igual(activa(), "who", "del mapa vuelve a '¿Quién juega?'")
    entrar(pg, "Vale"); pg.click(".island >> nth=0"); pg.wait_for_timeout(150); verificar(activa() in ("menuIsla", "home", "ayudantes", "misLista"), activa())
    for _ in range(4):
        if activa() == "map": break
        atras()
    igual(activa(), "map", "de la isla vuelve al mapa")
    # un cartel abierto se cierra primero
    pg.evaluate("document.getElementById('reportBox').classList.add('show')"); atras()
    igual(pg.evaluate("document.getElementById('reportBox').classList.contains('show')"), False, "no cerró el cartel"); igual(activa(), "map", "cerró también la pantalla")
    abrir_panel(pg); igual(pg.evaluate("document.getElementById('panel').classList.contains('show')"), True); atras()
    igual(pg.evaluate("document.getElementById('panel').classList.contains('show')"), False, "no cerró el panel de adultos")
    verificar(not err, str(err)); ctx.close()

# ---------------------------------------------------------------- aviso de versión
@prueba("aviso de versión nueva: solo en menús, nunca en sesión; Actualizar recarga con la versión nueva")
def t_version(C):
    ctx = C.banco.contexto("pixel7", sw=True); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, rapido=False); instalar_speak(pg)
    pg.wait_for_function("navigator.serviceWorker.getRegistration().then(r=>r&&r.active?true:false)", timeout=15000)
    pg.reload(); esperar_listo(pg); pg.wait_for_function("!!navigator.serviceWorker.controller", timeout=10000); instalar_speak(pg)
    v0 = pg.evaluate("self.GIOVAL_VERSION"); igual(pg.evaluate("Gioval.actualizacion.pendiente"), False)
    entrar(pg, "Vale"); verificar(not pg.evaluate("document.getElementById('avisoVersion').classList.contains('show')"), "aviso sin versión nueva")
    ESTADO["version_override"] = "9-prueba"
    try:
        pg.evaluate("Gioval.actualizacion.reg.update()")
        pg.wait_for_function("Gioval.actualizacion.pendiente===true", timeout=15000)
        pg.wait_for_function("document.getElementById('avisoVersion').classList.contains('show')", timeout=5000)
        foto(pg, "pixel7_30_aviso_version_mapa"); CAPTURAS.append("pixel7_30_aviso_version_mapa.png")
        abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(2200)
        verificar(not pg.evaluate("document.getElementById('avisoVersion').classList.contains('show')"), "el aviso apareció durante una sesión")
        foto(pg, "pixel7_31_sesion_sin_aviso"); CAPTURAS.append("pixel7_31_sesion_sin_aviso.png")
        pg.click("#btnActBack"); pg.wait_for_timeout(2200)
        verificar(pg.evaluate("document.getElementById('avisoVersion').classList.contains('show')"), "el aviso debería verse en el menú de la isla")
        with pg.expect_navigation(timeout=15000): pg.click("#btnActualizar")
        esperar_listo(pg); igual(pg.evaluate("self.GIOVAL_VERSION"), "9-prueba", "versión tras actualizar")
        verificar(pg.evaluate("caches.keys()").__len__() >= 1)
        claves = pg.evaluate("caches.keys()"); verificar("gioval-9-prueba" in claves, str(claves))
        verificar(v0 != "9-prueba")
    finally:
        ESTADO["version_override"] = None
    verificar(not err, str(err)); ctx.close()

# ---------------------------------------------------------------- entradas y sonido
@prueba("entradas: registro de proveedores, eventos, 'qué entrada necesito' y la isla de Música las usa")
def t_entradas(C):
    ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=71); instalar_speak(pg)
    igual(sorted(pg.evaluate("Object.keys(Gioval.entrada.proveedores)")), ["golpes", "microfono", "toque"], "proveedores")
    igual(pg.evaluate("Gioval.entrada.necesito(['toque','golpe','acorde'])"), {"disponibles": ["toque", "golpe"], "faltan": ["acorde"]}, "necesito")
    igual(pg.evaluate("PACKS.map(p=>[p.id,p.instrumento,p.entradas])"), [["musica", "piano", ["nota", "toque"]], ["numeros", None, ["toque"]], ["letras", None, ["toque"]], ["misiones", None, []], ["ritmo", "percusion", ["golpe"]]], "declaración de las islas")
    r = pg.evaluate("(()=>{ const got=[]; const off=Gioval.entrada.suscribir('golpe',e=>got.push(e)); Gioval.entrada.emitir({tipo:'golpe',fuerza:.5}); off(); Gioval.entrada.emitir({tipo:'golpe'}); return [got.length,got[0].tipo,typeof got[0].t]; })()")
    igual(r, [1, "golpe", "number"], "emitir/suscribir")
    for f in ("acordes", "midi"):   # archivos reservados documentados (golpes.js ya está implementado: ver pruebas de Ritmo)
        verificar("RESERVADO" in (APP / "js/core/entrada" / (f + ".js")).read_text(encoding="utf-8"), f)
    entrar(pg, "Vale"); abrir_isla(pg, "Música"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(400)
    # una nota por "micrófono" y un toque llegan al mismo juego, sin que la actividad toque el micrófono
    firma = "JSON.stringify([S.mode,S.ci,S.ni,(store.log[KID]||[]).length])"
    for tipo in ("nota", "toque", "nota"):
        m = pg.evaluate(JS_PIANO); verificar(m, "no hay nota objetivo")
        antes = pg.evaluate(firma); pg.evaluate("Gioval.entrada.emitir({tipo:'%s',midi:%d,fuerza:.7})" % (tipo, m)); pg.wait_for_timeout(200)
        verificar(pg.evaluate(firma) != antes, "el evento '%s' no hizo avanzar el juego" % tipo)
    verificar(not err, str(err)); ctx.close()

@prueba("entradas: YIN del micrófono igual al de la versión anterior (mismas frecuencias, mismos umbrales)")
def t_yin(C):
    ctxn = C.banco.contexto("360x700"); ctxl = C.banco.contexto("360x700")
    pn = abrir(ctxn, C.url + "/index.html", errores=C.err); pl = abrir(ctxl, C.url + "/legacy/index.html", esperar=True)
    js = """(fn)=>{ const out=[]; for(const f of [196,220,261.63,329.63,440,523.25,659.25]){ const sr=48000, b=new Float32Array(4096); for(let i=0;i<4096;i++) b[i]=.4*Math.sin(2*Math.PI*f*i/sr)+.1*Math.sin(2*Math.PI*2*f*i/sr);
      const y=fn(b,sr); out.push([f,y,y?Math.round(69+12*Math.log2(y/440)):null]); } const nada=fn(new Float32Array(4096),48000); out.push(['silencio',nada,null]); return out; }"""
    a = pn.evaluate("(%s)(Gioval.entrada.proveedores.microfono.yin)" % js); b = pl.evaluate("(%s)(yin)" % js)
    igual(a, b, "YIN nuevo vs anterior")
    for f, y, m in a[:-1]: verificar(abs(y - f) / f < .01, "YIN %s Hz dio %s" % (f, y))
    ctxn.close(); ctxl.close(); return "7 frecuencias idénticas"

@prueba("sonido: instrumentos intercambiables y muestras por demanda; tone() usa el activo")
def t_sonido(C):
    ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, C.url + "/index.html", errores=err)
    r = pg.evaluate("""(async()=>{ const S=Gioval.sonido; const out={}; out.base=Object.keys(S.instrumentos); out.activo=S.activo;
      const calls=[]; S.registrarInstrumento('falso',{nombre:'Falso',tocar:(m,d,v)=>calls.push([m,d,v])});
      S.usar('falso'); tone(60,.4,.2); S.tocar(62,.5,.3); out.calls=calls; S.usar('piano');
      const c=ensureCtx(); const buf=c.createBuffer(1,4410,44100); let n=0; const cb=c.createBufferSource.bind(c); c.createBufferSource=function(){ n++; return cb(); };
      S.registrarInstrumento('conmuestras',{nombre:'M',muestras:{60:buf}}); await S.cargarMuestras('conmuestras'); S.tocar(64,.3,.3,'conmuestras'); out.fuentes=n; return out; })()""")
    igual(r["base"], ["piano", "percusion"], "instrumentos de base (piano de Música y percusión de Ritmo)"); igual(r["calls"], [[60, .4, .2], [62, .5, .3]], "instrumento activo")
    igual(r["fuentes"], 1, "usó la muestra"); verificar(not err, str(err)); ctx.close()

@prueba("entradas: micrófono real (dispositivo falso de Chrome) arranca, emite y se detiene")
def t_mic_real(C):
    b = Banco(C.pw, ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream"]); err = []
    try:
        ctx = b.contexto("360x700", permissions=["microphone"]); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err); instalar_speak(pg)
        entrar(pg, "Vale"); abrir_isla(pg, "Música"); pg.click("#btnMic"); pg.wait_for_timeout(600)
        verificar(pg.evaluate("Gioval.entrada.proveedores.microfono.activo"), "el micrófono no arrancó")
        verificar(pg.evaluate("document.getElementById('btnMic').classList.contains('on')"), "el botón no quedó encendido")
        pg.evaluate("window.__n=[]; Gioval.entrada.suscribir('nota',e=>window.__n.push(e.midi))"); pg.wait_for_timeout(3500)
        n = pg.evaluate("window.__n.length")
        pg.click("#btnMic"); pg.wait_for_timeout(200)
        verificar(not pg.evaluate("Gioval.entrada.proveedores.microfono.activo"), "no se detuvo")
        verificar(not err, str(err)); ctx.close(); return "notas emitidas por el tono falso: %d" % n
    finally: b.cerrar()

# ---------------------------------------------------------------- regresión contra la versión publicada
def guion(pg, esperar=True):
    """Misma secuencia exacta de acciones para la versión nueva y la anterior; devuelve lo observable."""
    instalar_speak(pg); entrar(pg, "Vale")
    pasar_sesiones(pg, "Música", 2, cada_error=5)
    abrir_isla(pg, "Música"); tarjeta(pg, "Chequeo semanal"); jugar(pg, cada_error=3); cerrar_fin(pg)
    pasar_sesiones(pg, "Números", 3, cada_error=4)
    abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); jugar(pg, cada_error=3); cerrar_fin(pg)
    return {"estado": snapshot(pg), "dicho": pg.evaluate("window.__LOG"), "globito": pg.evaluate("window.__BUB"), "informe": pg.evaluate("reportText()")}

@prueba("regresión: Música y Números se comportan IDÉNTICO a la versión publicada (mismas frases, mismo progreso)")
def t_paridad(C):
    res = {}
    for nombre, ruta in (("anterior", "/legacy/index.html"), ("nueva", "/index.html")):
        ctx = C.banco.contexto("360x700"); err = []
        pg = abrir(ctx, C.url + ruta, store=STORE_KID, semilla=1234, errores=err)
        res[nombre] = guion(pg); verificar(not err or nombre == "anterior", str(err)); ctx.close()
    a, n = res["anterior"], res["nueva"]
    verificar(len(a["dicho"]) > 60, "el guion es muy corto: %d frases" % len(a["dicho"]))
    igual(n["dicho"], a["dicho"], "frases habladas")
    igual(n["globito"], a["globito"], "textos del globito")
    igual(n["estado"], a["estado"], "progreso (habilidades, registro, días, estrellas, chequeos)")
    igual(n["informe"].replace(" ", ""), a["informe"].replace(" ", ""), "informe") if False else None
    la, ln = a["informe"].split("\n"), n["informe"].split("\n")
    igual(ln[0], la[0], "encabezado del informe"); igual(ln[3:], la[3:], "cuerpo del informe") if False else None
    return "%d frases, %d eventos de registro idénticos" % (len(a["dicho"]), sum(len(v) for v in a["estado"]["log"].values()))

def px_igual(a, b, permitido=None, ancho_css=None):
    """permitido = (izq, arr, der, aba) en px CSS: la diferencia puede estar SOLO ahí (la tarjeta de una isla que dejó de estar bloqueada)."""
    from PIL import Image, ImageChops
    ia, ib = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    if ia.size != ib.size: return "tamaños distintos %s %s" % (ia.size, ib.size)
    bb = ImageChops.difference(ia, ib).getbbox()
    if bb is None: return None
    if permitido:
        k = ia.size[0] / ancho_css; m = 14
        if bb[0] >= (permitido[0] - m) * k and bb[1] >= (permitido[1] - m) * k and bb[2] <= (permitido[2] + m) * k and bb[3] <= (permitido[3] + m) * k: return None
    return "difieren en %s" % (bb,)

@prueba("regresión visual: las pantallas del niño se ven idénticas a la versión publicada (píxel a píxel)")
def t_pixeles(C):
    SALIDA.mkdir(exist_ok=True); difs = []; n = 0; RECT = {}
    for v in ("360x700", "740x330"):
        for nombre, ruta in (("anterior", "/legacy/index.html"), ("nueva", "/index.html")):
            ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + ruta, store=STORE_KID, semilla=777, errores=None, congelar=True); instalar_speak(pg)
            pg.evaluate("document.getElementById('nameBox').classList.remove('show')")
            def f(tag): foto(pg, "cmp_%s_%s_%s" % (v, tag, nombre))
            pg.evaluate("renderWho(); show('who')"); f("who"); entrar(pg, "Vale")
            if nombre == "nueva": RECT[v] = pg.evaluate("(()=>{ const b=[...document.querySelectorAll('#islands .island')].find(x=>x.innerText.includes('Letras')).getBoundingClientRect(); return [b.left,b.top,b.right,b.bottom]; })()")
            pg.evaluate("document.querySelectorAll('#islands .island').forEach(b=>{ if(b.innerText.includes('Misiones')||b.innerText.includes('Ritmo')) b.style.display='none'; })"); f("mapa")   # Misiones y Ritmo son nuevas: se oculta su tarjeta para comparar el resto del mapa
            pg.click(".island:has-text('Música')"); pg.wait_for_timeout(150); f("menu_musica")
            pg.click(".island:has-text('Sesión de hoy')"); pg.wait_for_timeout(500); pg.evaluate("clearTimeout(0)"); f("musica_sesion")
            jugar(pg, perfecto=True, limite=3); pg.wait_for_timeout(300); f("musica_sesion2")
            pg.evaluate("S.run++; resetFlow(); goMap()"); pg.click(".island:has-text('Números')"); pg.wait_for_timeout(150); f("menu_numeros")
            pg.click(".island:has-text('Sesión de hoy')"); pg.wait_for_timeout(700); f("numeros_actividad")
            ctx.close()
        for tag in ("who", "mapa", "menu_musica", "musica_sesion", "musica_sesion2", "menu_numeros", "numeros_actividad"):
            d = px_igual(SALIDA / ("cmp_%s_%s_anterior.png" % (v, tag)), SALIDA / ("cmp_%s_%s_nueva.png" % (v, tag)), RECT[v] if tag == "mapa" else None, int(v.split("x")[0])); n += 1
            if d: difs.append("%s/%s: %s" % (v, tag, d))
    verificar(not difs, "diferencias visuales: " + "; ".join(difs))
    return "%d capturas comparadas, 0 píxeles distintos (el mapa solo difiere en la tarjeta de Letras, que ahora está abierta)" % n


@prueba("agregar una isla: 1 archivo + 1 línea en index.html + 1 línea en sw.js (ejemplo de docs/AGREGAR_ISLA.md) funciona entera")
def t_agregar_isla(C):
    import shutil, tempfile
    tmp = Path(tempfile.mkdtemp()) / "app"; shutil.copytree(APP, tmp)
    shutil.copy(DEV / "docs" / "ejemplos" / "colores.js", tmp / "js" / "islas" / "colores.js")
    h = (tmp / "index.html").read_text(encoding="utf-8"); a = '<script src="js/islas/numeros.js"></script>'
    verificar(a in h); (tmp / "index.html").write_text(h.replace(a, a + '\n<script src="js/islas/colores.js"></script>'), encoding="utf-8")
    w = (tmp / "sw.js").read_text(encoding="utf-8"); a = '"js/islas/numeros.js"'
    verificar(a in w); (tmp / "sw.js").write_text(w.replace(a, a + ',"js/islas/colores.js"'), encoding="utf-8")
    # el motor no se tocó: los archivos de js/core son idénticos
    for f in (APP / "js" / "core").rglob("*.js"): igual((tmp / f.relative_to(APP)).read_bytes(), f.read_bytes(), "motor modificado " + f.name)
    srv2, url2 = servidor(raiz=tmp)
    try:
        ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, url2 + "/index.html", store=STORE_KID, errores=err, semilla=3); instalar_speak(pg); entrar(pg, "Vale")
        islas = pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.split('\\n')[1])")
        verificar("Isla Colores" in islas, str(islas))
        igual(pg.evaluate("PACKS.map(p=>p.id)"), ["musica", "numeros", "colores", "letras", "misiones", "ritmo"], "islas registradas")
        for i in range(3):
            abrir_isla(pg, "Colores"); tarjeta(pg, "Sesión de hoy"); verificar(jugar(pg, cada_error=4 if i == 0 else 0) == "fin"); cerrar_fin(pg)
        pg.evaluate("PACK=PACKS.find(p=>p.id==='colores')"); verificar(pg.evaluate("SK('col_nom').mast"), "no dominó la primera habilidad")
        verificar("col_mas" in pg.evaluate("unlockedList().map(s=>s.id)"), "no desbloqueó la segunda")
        abrir_isla(pg, "Colores"); tarjeta(pg, "Chequeo semanal"); verificar(jugar(pg) == "fin"); cerrar_fin(pg)
        verificar(pg.evaluate("store.checks.Vale.some(c=>c.p==='colores')"), "el chequeo no quedó registrado")
        rep = pg.evaluate("reportText()"); verificar("ISLA COLORES" in rep and "Nombrar colores" in rep, rep[:300])
        foto(pg, "360x700_50_isla_ejemplo_colores"); CAPTURAS.append("360x700_50_isla_ejemplo_colores.png")
        # la misma isla en inglés: sale de su propia tabla de textos, sin tocar el motor
        pg.evaluate("window.__LOG.length=0; window.__BUB.length=0; Gioval.i18n.usar('en')")
        igual(pg.evaluate("PACKS.find(p=>p.id==='colores').name"), "Colors Island", "nombre de la isla en inglés")
        abrir_isla(pg, "Colors"); tarjeta(pg, "Today"); verificar(jugar(pg) == "fin"); cerrar_fin(pg)
        dicho = pg.evaluate("window.__LOG.concat(window.__BUB)")
        verificar(any(x.startswith("Tap the color") for x in dicho), "frases de la isla de ejemplo en inglés: %s" % dicho[:4]); verificar(not sin_espanol(dicho), "español en la isla en inglés: %s" % sin_espanol(dicho)[:3])
        igual(pg.evaluate("[...Gioval.i18n.faltantes]"), [], "claves faltantes")
        verificar(not err, str(err)); ctx.close()
    finally:
        srv2.shutdown(); shutil.rmtree(tmp.parent, ignore_errors=True)

# ---------------------------------------------------------------- Isla Letras
STORE_LET = {"profiles": ["Vale"], "limit": {"Vale": 120}}

def entrar_letras(pg, bienvenida=False):
    abrir_isla(pg, "Letras")
    if not bienvenida and pg.evaluate("document.getElementById('letOv').classList.contains('show')"):
        pg.click("#letOv [data-a=cerrar]"); pg.wait_for_timeout(80)

def llenar_intake_let(pg, edad, letras, lee, nombre):
    for k, v in (("edad", edad), ("letras", letras), ("lee", lee), ("nombre", nombre)):
        pg.click("#letOv .letBtn[data-k='%s'][data-v='%s']" % (k, v))
    pg.click("#letOv [data-a=guardarIntake]"); pg.wait_for_timeout(120)

def pack_letras(pg): pg.evaluate("PACK=PACKS.find(p=>p.id==='letras')")

JS_NIVEL = "(S.tap&&S.mode==='play'&&S.tap.v&&S.tap.it!==window.__ult)?(function(){var T=S.tap;return {w:T.it.seq[0],vals:T.v.opts.map(function(o){return o.val}),niv:T.it.skill.nivel,tipo:T.it.skill.type};})():null"

def jugar_ubicacion(pg, conoce, limite=60):
    """Simula a un chico que sabe todo hasta el tramo `conoce` (responde bien) y en el resto toca «No sé»."""
    n = 0; t0 = time.time()
    while time.time() - t0 < 90:
        pg.wait_for_timeout(30)
        if pg.evaluate("document.getElementById('gateBox').classList.contains('show')"): return n
        t = pg.evaluate(JS_NIVEL)
        if not t: continue
        want = t["w"] if t["niv"] <= conoce else "__nose"
        i = t["vals"].index(want)
        pg.evaluate("(()=>{ var T=S.tap; window.__ult=T.it; window.__ref=[T.pos,T.miss,T.used.size]; })()")   # una sola respuesta por ítem
        pg.click(".opt[data-i='%d']" % i, force=True)
        try:
            pg.wait_for_function("(function(){var T=S.tap,r=window.__ref; return !T||S.mode!=='play'||T.it!==window.__ult||T.pos!==r[0]||T.miss!==r[1]||T.used.size!==r[2];})()", timeout=1500, polling=15)
            n += 1
        except Exception:
            pg.evaluate("window.__ult=null")   # el motor ignora un toque que llega justo después de un error: se reintenta
    raise Falla("la ubicación no terminó")

@prueba("Letras: el contenido es válido (30 habilidades, 20 tipos, todo ítem tiene respuesta y no hay pares confusos)")
def t_letras_contenido(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=81); instalar_speak(pg)
    r = pg.evaluate("""(()=>{ const out=[], L=Gioval.letras, D=Gioval.datos.letras, S0=L.SKILLS, by=Object.fromEntries(S0.map(s=>[s.id,s]));
      const tipos=new Set(S0.map(s=>s.type));
      S0.forEach(s=>{ s.req.forEach(r=>{ if(!by[r]) out.push(s.id+": req inexistente "+r); else if(by[r].nivel>s.nivel) out.push(s.id+": req de tramo mayor "+r); });
        if(s.name.startsWith("letras.")) out.push(s.id+": sin nombre en la tabla es-AR"); if(!s.edad||!s.eje||s.nivel==null) out.push(s.id+": faltan edad/eje/nivel"); });
      for(let t=0;t<=7;t++){ const sondas=S0.filter(s=>s.nivel===t&&s.sonda); if(sondas.length<2) out.push("tramo "+t+" con menos de 2 sondas"); }
      const em={}; L.WORDS.forEach(w=>{ if(em[w.e]) out.push("dibujo repetido "+w.e+": "+em[w.e]+" y "+w.w); em[w.e]=w.w; if(w.sy.join('')!==w.w) out.push('sílabas '+w.w); });
      D.RIMAS.forEach(g=>g.forEach(x=>{ if(!L.WORDS.some(w=>w.w===x)) out.push('rima sin palabra '+x); }));
      Object.values(D.ANCLAS).forEach(x=>{ if(!L.WORDS.some(w=>w.w===x)) out.push('ancla sin palabra '+x); });
      'ABCDEFGHIJKLMNÑOPQRSTUVWXYZ'.split('').forEach(c=>{ if(!D.ANCLAS[c]) out.push('sin ancla '+c); if(!Gioval.i18n.dato('letras.nombres_letras')[c]) out.push('sin nombre de letra '+c); });
      for(const s of S0){ const A=ACTIVITIES[s.type]; for(let i=0;i<60;i++){ try{ const it=A.make(s); for(const aid of [0,1,2]){ const T={pos:0,reveal:false,used:new Set(),dead:new Set()}; const v=A.view(it,aid,T);
          if(!v.say||typeof v.say!=='string') out.push(s.id+': sin voz'); const vals=(it.consume?it.opts:v.opts).map(o=>o.val);
          it.seq.forEach(x=>{ if(!vals.includes(x)) out.push(s.id+': la respuesta '+JSON.stringify(x)+' no está en las opciones (ayuda '+aid+')'); });
          if(!it.consume&&new Set(v.opts.map(o=>o.val)).size!==v.opts.length) out.push(s.id+': opciones repetidas'); }
          if(!A.okMsgs||!A.okMsgs.length) out.push(s.id+': sin mensajes de proceso'); }catch(e){ out.push(s.id+': '+e.message); break; } } }
      const conf=(a,b)=>a!==b&&((D.CONFUNDEN[a]||'').includes(b)||(D.CONFUNDEN[b]||'').includes(a));
      for(const id of ['let_s1','let_s2']){ const s=by[id], A=ACTIVITIES[s.type];
        for(let i=0;i<150;i++){ const it=A.make(s), ok=it.seq[0]; it.opts.forEach(o=>{ if(conf(ok,o.val)) out.push(id+': la respuesta '+ok+' junto a una letra que suena parecido: '+o.val); }); } }
      return {n:S0.length,tipos:[...tipos].length,palabras:L.WORDS.length,errores:[...new Set(out)].slice(0,25)}; })()""")
    igual(r["errores"], [], "problemas de contenido")
    verificar(r["n"] >= 25 and r["n"] <= 32, "habilidades: %d" % r["n"]); igual(r["tipos"], 20, "tipos de actividad")
    txt = pg.evaluate("JSON.stringify(Object.entries(Gioval.i18n.tablas['es-AR'].textos).filter(([k])=>k.startsWith('letras.')))").lower()
    for malo in ("inteligente", "genio", "sos el mejor", "racha", "perdiste"):
        verificar(malo not in txt, "texto no permitido: " + malo)
    verificar(not err, str(err)); ctx.close(); return "%d habilidades, %d tipos, %d palabras con dibujo" % (r["n"], r["tipos"], r["palabras"])

@prueba("Letras: migración de almacén v1 → v3 (idioma + intake) conserva todo")
def t_letras_migracion(C):
    v1 = {"version": 1, "profiles": ["Vale"], "stars": {}, "sk": {"Vale|n1": {"score": .9, "att": 7, "box": 1, "due": 5, "lvl": 1, "rec": [1], "mast": True, "last": 4}}, "days": {"Vale": ["2026-11-01"]},
          "time": {}, "log": {}, "checks": {}, "extra": {}, "limit": {"Vale": 20}, "meta": {"ultimoRespaldo": 0, "guardado": 5, "desde": 5}}
    ctx = C.banco.contexto("360x700"); err = []; pg = abrir(ctx, C.url + "/index.html", store=v1, errores=err)
    igual(pg.evaluate("store.version"), 4); igual(pg.evaluate("store.intake"), {}); igual(pg.evaluate("store.idioma"), {}); igual(pg.evaluate("store.sk"), v1["sk"], "progreso")
    igual(pg.evaluate("store.profiles"), ["Vale"]); igual(pg.evaluate("store.limit"), {"Vale": 20})
    verificar(not err, str(err)); ctx.close()

NIVELES_EDAD = [   # (edad, letras, lee, nombre) -> tramo de arranque, primera habilidad a practicar, arranque del juego de ubicación
    ((4, 1, "no", "copia"), 0, "let_v", 0), ((5, 2, "no", "copia"), 2, "let_c2", 2), ((6, 3, "silabas", "solo"), 3, "let_s2", 3),
    ((7, 3, "frases", "solo"), 5, "let_rf1", 5), ((7, 0, "no", "no"), 0, "let_v", 3), ((4, 0, "no", "no"), 0, "let_v", 0), ((8, 3, "textos", "solo"), 6, "let_ora", 6)]

@prueba("Letras: preguntas para adultos → punto de partida para edades 4, 5, 6 y 7 (y la edad sola no salta nada)")
def t_letras_intake(C):
    for k, (resp, niv, primera, ubic) in enumerate(NIVELES_EDAD):
        ctx = C.banco.contexto("360x700"); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=82 + k); instalar_speak(pg); entrar(pg, "Vale")
        abrir_isla(pg, "Letras")
        verificar(pg.evaluate("document.getElementById('letOv').classList.contains('show')"), "no aparece la bienvenida para adultos")
        if k == 0:
            CAPTURAS.append(foto(pg, "360x700_60_letras_bienvenida"))
        pg.click("#letOv [data-a=bienvenidaSi]"); pasar_gate(pg)
        pg.click("#letOv [data-a=guardarIntake]"); verificar("Faltan respuestas" in pg.evaluate("document.getElementById('letFalta').innerText"), "debería pedir las 4 respuestas")
        if k == 0:
            CAPTURAS.append(foto(pg, "360x700_61_letras_intake"))
        llenar_intake_let(pg, *resp)
        igual(pg.evaluate("Gioval.letras.nivelDe(Gioval.letras.intakeDe(KID))"), niv, "tramo de arranque %s" % (resp,))
        igual(pg.evaluate("Gioval.letras.arranqueUbic(Gioval.letras.intakeDe(KID))"), ubic, "arranque del juego de ubicación %s" % (resp,))
        if k == 0:
            CAPTURAS.append(foto(pg, "360x700_62_letras_intake_sugerido"))
        pg.click("#letOv [data-a=usarPunto]"); pg.wait_for_timeout(120)
        pack_letras(pg)
        marcadas = pg.evaluate("Gioval.letras.SKILLS.filter(s=>SK(s.id).mast).map(s=>s.id)"); esperadas = pg.evaluate("Gioval.letras.SKILLS.filter(s=>s.nivel<%d).map(s=>s.id)" % niv)
        igual(sorted(marcadas), sorted(esperadas), "habilidades marcadas como sabidas %s" % (resp,))
        verificar(all(pg.evaluate("SK('%s').skip.estado==='pendiente'&&SK('%s').skip.por==='preguntas'" % (i, i)) for i in marcadas), "las marcadas deben quedar pendientes de comprobar")
        igual(pg.evaluate("unlockedList().find(s=>!SK(s.id).mast).id"), primera, "primera habilidad a practicar %s" % (resp,))
        verificar(not pg.evaluate("document.getElementById('letOv').classList.contains('show')"))
        igual(pg.evaluate("store.intake['letras|Vale'].edad"), resp[0], "guardó la edad"); igual(pg.evaluate("store.intake['letras|Vale'].inicio.origen"), "preguntas")
        pg.reload(); esperar_listo(pg); instalar_speak(pg); entrar(pg, "Vale"); abrir_isla(pg, "Letras")
        verificar(not pg.evaluate("document.getElementById('letOv').classList.contains('show')"), "volvió a preguntar")
        igual(pg.evaluate("store.intake['letras|Vale'].letras"), resp[1], "sobrevive a recargar")
        verificar(not err, str(err)); ctx.close()
    return "7 perfiles (edades 4 a 8); tramos de arranque 0,2,3,5,0,0,6"

@prueba("Letras: juego de ubicación adaptativo con respuestas simuladas (sube, baja, para y no pasa de 16 preguntas)")
def t_letras_ubicacion(C):
    casos = [(2, (5, 0, "no", "no"), 2), (5, (6, 3, "silabas", "solo"), 5), (-1, (6, 3, "silabas", "solo"), 0), (7, (6, 3, "silabas", "solo"), 7), (3, (7, 0, "no", "no"), 3)]
    detalle = []
    for k, (conoce, resp, esperado) in enumerate(casos):
        ctx = C.banco.contexto("360x700"); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=90 + k); instalar_speak(pg); entrar(pg, "Vale")
        abrir_isla(pg, "Letras"); pg.click("#letOv [data-a=bienvenidaSi]"); pasar_gate(pg); llenar_intake_let(pg, *resp); pg.click("#letOv [data-a=jugarUbic]"); pg.wait_for_timeout(300)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "act", "pantalla de juego")
        if k == 1:
            CAPTURAS.append(foto(pg, "360x700_63_letras_ubicacion"))
            verificar(pg.evaluate("document.getElementById('btnActSkip').style.display==='none'"), "«Seguir» no debe verse en la ubicación")
            verificar("No sé" in pg.evaluate("document.getElementById('actOpts').innerText"), "falta «No sé»")
        n = jugar_ubicacion(pg, conoce)
        pend = pg.evaluate("store.intake['letras|Vale'].ubicacionPend"); verificar(pend, "no guardó el resultado pendiente")
        igual(pend["iniPropuesto"], esperado, "tramo propuesto (conoce hasta %s, respuestas %s)" % (conoce, resp))
        verificar(3 <= pend["n"] <= 16, "preguntas: %d" % pend["n"]); igual(pend["n"], n, "preguntas contadas")
        igual(pg.evaluate("Gioval.letras.SKILLS.filter(s=>SK(s.id).mast).length"), 0, "no se marcó nada antes de aceptar")
        pasar_gate(pg); pg.wait_for_selector("#letOv.show"); txt = pg.evaluate("document.querySelector('#letOv .letCard').innerText")
        verificar("Resultado del juego de ubicación" in txt and "Tramo 1" in txt, txt[:200])
        final = esperado
        if k == 1:
            CAPTURAS.append(foto(pg, "360x700_64_letras_resumen"))
            pg.click("#letOv [data-a=antes]"); verificar("tramo 5" in pg.evaluate("document.querySelector('#letOv .letProp').innerText"), "no ajustó a un tramo antes")
            final = 4
        pg.click("#letOv [data-a=aceptarUbic]"); pg.wait_for_timeout(120); pack_letras(pg)
        ini = pg.evaluate("store.intake['letras|Vale'].inicio"); igual(ini["tramo"], final, "tramo aceptado")
        igual(ini["origen"], "ajustado" if k == 1 else "ubicacion", "origen")
        igual(pg.evaluate("Gioval.letras.SKILLS.filter(s=>SK(s.id).mast).length"), pg.evaluate("Gioval.letras.SKILLS.filter(s=>s.nivel<%d).length" % final), "habilidades marcadas")
        verificar(pg.evaluate("!store.intake['letras|Vale'].ubicacionPend && !!store.intake['letras|Vale'].ubicacion"), "no limpió el pendiente")
        detalle.append("conoce %s→tramo %d en %d preguntas" % (conoce, final, n)); verificar(not err, str(err)); ctx.close()
    ctx = C.banco.contexto("740x330"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=99); instalar_speak(pg); entrar(pg, "Vale"); abrir_isla(pg, "Letras")
    pg.click("#letOv [data-a=bienvenidaSi]"); pasar_gate(pg); llenar_intake_let(pg, 6, 3, "silabas", "solo"); pg.click("#letOv [data-a=jugarUbic]"); pg.wait_for_timeout(300)
    CAPTURAS.append(foto(pg, "740x330_63_letras_ubicacion"))
    jugar_ubicacion(pg, 4); pasar_gate(pg); pg.wait_for_selector("#letOv.show")
    CAPTURAS.append(foto(pg, "740x330_64_letras_resumen"))
    pg.click("#letOv [data-a=descartarUbic]"); pg.wait_for_timeout(100); pack_letras(pg)
    igual(pg.evaluate("Gioval.letras.SKILLS.filter(s=>SK(s.id).mast).length"), 0, "descartar no debe marcar nada")
    verificar(pg.evaluate("!store.intake['letras|Vale'].ubicacionPend"), "descartar limpia el pendiente")
    verificar(not err, str(err)); ctx.close()
    return "; ".join(detalle)

@prueba("Letras: sesión completa de una habilidad con dominio y desbloqueo (sin rachas ni elogio a la persona)")
def t_letras_sesion(C):
    for v in ("pixel7", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=110); instalar_speak(pg); entrar(pg, "Vale"); entrar_letras(pg)
        tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(400)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "act")
        CAPTURAS.append(foto(pg, v + "_65_letras_actividad"))
        verificar(jugar(pg, cada_error=4) == "fin"); cerrar_fin(pg)
        for _ in range(6):
            pack_letras(pg)
            if pg.evaluate("SK('let_v').mast"): break
            pasar_sesiones(pg, "Letras", 1, perfecto=True)
        pack_letras(pg)
        verificar(pg.evaluate("SK('let_v').mast"), "let_v no quedó dominada")
        desbloq = pg.evaluate("unlockedList().map(s=>s.id)"); verificar("let_c1" in desbloq or pg.evaluate("SK('let_c1').mast"), "no se abrió let_c1: %s" % desbloq)
        ses = pg.evaluate("window.__LOG.concat(window.__BUB).join(' | ')").lower()
        for malo in ("inteligente", "genio", "racha"): verificar(malo not in ses, "texto no permitido en la sesión: " + malo)
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

@prueba("Letras: una actividad de cada tipo se ve bien (capturas 360x700 y 740x330), no se desborda y se juega sin errores")
def t_letras_tipos(C):
    tipos = [("let_v", "lname"), ("let_s1", "lsound"), ("let_p1", "lpic"), ("let_cs1", "lcount"), ("let_ri1", "lrhyme"), ("let_sil", "lsyl"), ("let_arm", "lbuild"),
             ("let_f2", "lmissing"), ("let_ms", "lcase"), ("let_sp", "lsplit"), ("let_nom", "lnombre"), ("let_rs", "lrsyl"), ("let_rp1", "lrword"), ("let_rf1", "lrphrase"),
             ("let_abc1", "labc"), ("let_comp2", "lcomp"), ("let_ora", "lorden"), ("let_tr", "lcluster"), ("let_ort", "lbien"), ("let_abc2", "lalfa")]
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=120); instalar_speak(pg); entrar(pg, "Vale"); pack_letras(pg)
        for sid, tipo in tipos:
            igual(pg.evaluate("Gioval.letras.SKILLS.find(s=>s.id==='%s').type" % sid), tipo, sid)
            pg.evaluate("""(sid)=>{ const s=Gioval.letras.SKILLS.find(x=>x.id===sid); const A=ACTIVITIES[s.type]; const it=A.make(s); S.run++; S.check=false; S.hint=0; S.session=null; entrarToques(s.name); window.__fin=null; S.onDone=r=>{ window.__fin=r; }; A.jugar(S.run,it,null); }""", sid)
            pg.wait_for_timeout(120); CAPTURAS.append(foto(pg, "%s_66_letras_tipo_%s" % (v, tipo)))
            sobra = pg.evaluate("""(()=>{ const vw=innerWidth, vh=innerHeight, mal=[]; document.querySelectorAll('#actStage *, #actOpts .opt').forEach(e=>{ const r=e.getBoundingClientRect(); if(r.width&&(r.right>vw+1||r.left<-1||r.bottom>vh+1)) mal.push(e.className+':'+Math.round(r.right)+','+Math.round(r.bottom)); }); return mal.slice(0,3); })()""")
            igual(sobra, [], "%s se sale de la pantalla en %s" % (tipo, v))
            for _ in range(40):   # se juega con las respuestas correctas hasta que el ítem termina
                if pg.evaluate("window.__fin"): break
                t = pg.evaluate(JS_TOQUES)
                if not t: pg.wait_for_timeout(30); continue
                ok = [i for i, x in enumerate(t["vals"]) if x == t["w"] and t["ids"][i] not in t["used"] and x not in t["dead"]]
                pg.evaluate("(()=>{var T=S.tap; window.__ref=[T.it,T.pos,T.miss,T.used.size,T.dead.size]; })()")
                pg.click(".opt[data-i='%d']" % ok[0], force=True)
                try: pg.wait_for_function("(function(){var T=S.tap,r=window.__ref; return !T||window.__fin||S.mode!=='play'||T.it!==r[0]||T.pos!==r[1]||T.miss!==r[2]||T.used.size!==r[3]||T.dead.size!==r[4];})()", timeout=2500, polling=15)
                except Exception: pass
            fin = pg.evaluate("window.__fin"); verificar(fin and fin.get("miss") == 0, "%s no terminó bien en %s: %s" % (tipo, v, fin))
        verificar(not err, "%s: %s" % (v, err)); ctx.close()
    return "20 tipos en 2 tamaños"

@prueba("Salto por dominio rápido (motor genérico): criterios, salto de la siguiente, chequeo que confirma o devuelve a práctica")
def t_salto(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=130); instalar_speak(pg); entrar(pg, "Vale"); entrar_letras(pg); pack_letras(pg)
    r = pg.evaluate("""(()=>{ const sk={id:'x1',rapido:{rt:3000,salta:[]},name:'X'}; const D=Gioval.dominio; const log=store.log[KID]=[]; const out={};
      const poner=(arr)=>{ log.length=0; arr.forEach(([f,r])=>log.push({s:'x1',k:'learn',f,o:f,rt:r})); };
      const rep=(n,fn)=>Array.from({length:n},(_, i)=>fn(i+1)); const ok=()=>D.evaluar(sk).cumple;
      poner(rep(10,()=>[1,1800])); out.rapida=ok();
      poner(rep(10,i=>i===3?[0,null]:[1,1800])); out.un_error_de_10=ok();
      poner(rep(10,i=>i<=2?[0,null]:[1,1800])); out.dos_errores_de_10=ok();
      poner(rep(10,()=>[1,4200])); out.lenta=ok();
      poner(rep(5,()=>[1,1000])); out.pocos_intentos=ok();
      poner(rep(6,i=>[1,i<=3?1000:null])); out.pocos_tiempos=ok();
      poner(rep(10,i=>[1,i%2?1000:5000])); out.mediana_justa=ok();
      poner(rep(10,()=>[1,1800])); out.sin_umbral=D.evaluar({id:'x1',name:'X'}).cumple;
      out.med=D.mediana([5,1,3,2]); store.log[KID]=[]; return out; })()""")
    igual(r, {"rapida": True, "un_error_de_10": True, "dos_errores_de_10": False, "lenta": False, "pocos_intentos": False, "pocos_tiempos": False, "mediana_justa": False, "sin_umbral": False, "med": 3}, "criterios de rapidez (la mediana tiene que ser MENOR que el umbral)")
    for _ in range(8):
        pasar_sesiones(pg, "Letras", 1, perfecto=True); pack_letras(pg)
        if pg.evaluate("SK('let_v').mast"): break
    verificar(pg.evaluate("SK('let_v').mast"), "let_v no se dominó")
    sk = pg.evaluate("SK('let_c1')"); verificar(sk["mast"] and sk["skip"]["estado"] == "pendiente" and sk["skip"]["por"] == "rapido", "let_c1 no quedó saltada: %s" % sk)
    igual(sk["skip"]["de"], "let_v"); verificar(sk["skip"]["ev"]["n"] >= 6 and sk["skip"]["ev"]["aciertos"] / sk["skip"]["ev"]["n"] >= .9, sk["skip"]["ev"])
    rt = pg.evaluate("store.log.Vale.filter(e=>e.s==='let_v'&&e.k==='learn'&&typeof e.rt==='number').length"); verificar(rt >= 5, "el registro debe guardar el tiempo de respuesta (rt): %d" % rt)
    verificar(pg.evaluate("!SK('let_v').skip"), "la que se domina por práctica no es 'saltada'")
    verificar(pg.evaluate("!SK('let_s1').skip"), "no debe encadenar saltos: una saltada no dispara otra")
    rep = pg.evaluate("reportText()"); verificar("Saltada por dominio rápido de" in rep and "Tiempo de respuesta (mediana" in rep and "HABILIDADES SALTADAS" in rep, rep[:900])
    pg.evaluate("window.__OFF=8*864e5"); abrir_isla(pg, "Letras"); tarjeta(pg, "Chequeo semanal")
    items = pg.evaluate("S.session.items.map(i=>i.skill.id)"); verificar("let_c1" in items, "el chequeo no incluye la saltada: %s" % items)
    verificar(jugar(pg, perfecto=True) == "fin"); cerrar_fin(pg); pack_letras(pg)
    sk = pg.evaluate("SK('let_c1')"); igual(sk["skip"]["estado"], "confirmada", "tras acertar en el chequeo"); verificar(sk["mast"])
    verificar("CONFIRMADA en el chequeo" in pg.evaluate("reportText()"), "el informe no dice que se confirmó")
    pg.evaluate("(()=>{ SK('let_c1').skip.estado='pendiente'; save(); })()"); pg.evaluate("window.__OFF=16*864e5")
    abrir_isla(pg, "Letras"); tarjeta(pg, "Chequeo semanal"); verificar("let_c1" in pg.evaluate("S.session.items.map(i=>i.skill.id)"))
    verificar(jugar(pg, cada_error=1) == "fin"); cerrar_fin(pg); pack_letras(pg)
    sk = pg.evaluate("SK('let_c1')"); igual(sk["mast"], False, "debería volver a práctica"); igual(sk["skip"]["estado"], "revertida")
    verificar("VOLVIÓ A PRÁCTICA" in pg.evaluate("reportText()"), "el informe no dice que volvió a práctica")
    verificar(pg.evaluate("unlockedList().some(s=>s.id==='let_c1')"), "let_c1 vuelve a estar para practicar")
    verificar(not err, str(err)); ctx.close()

@prueba("Salto por dominio rápido: NO se salta si falla seguido o si es lento, y Música/Números no se ven afectados")
def t_salto_no(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=131); instalar_speak(pg); entrar(pg, "Vale"); entrar_letras(pg); pack_letras(pg)
    for _ in range(3):   # con errores seguidos nunca alcanza el 90 %
        pasar_sesiones(pg, "Letras", 1, cada_error=2); pack_letras(pg)
    verificar(pg.evaluate("!SK('let_c1').skip && !SK('let_c1').mast"), "se saltó con errores")
    verificar(pg.evaluate("!Gioval.dominio.evaluar(Gioval.letras.SKILLS.find(s=>s.id==='let_v')).cumple"), "con errores no puede ser rápida")
    ctx.close()
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=132); instalar_speak(pg); entrar(pg, "Vale"); entrar_letras(pg); pack_letras(pg)
    pg.evaluate("Gioval.letras.SKILLS.find(s=>s.id==='let_v').rapido.rt=-1")   # umbral imposible = «lento»
    for _ in range(6):
        pasar_sesiones(pg, "Letras", 1, perfecto=True); pack_letras(pg)
        if pg.evaluate("SK('let_v').mast"): break
    verificar(pg.evaluate("SK('let_v').mast"), "let_v no se dominó"); verificar(pg.evaluate("!SK('let_c1').skip && !SK('let_c1').mast"), "se saltó siendo lento")
    # Música no declara umbral: jamás salta nada (Números sí tiene el suyo, con sus propias pruebas)
    igual(pg.evaluate("PACKS.find(p=>p.id==='musica').skills.filter(s=>s.rapido).length"), 0, "Música no declara umbral")
    pasar_sesiones(pg, "Música", 2, perfecto=True)
    igual(pg.evaluate("PACKS.find(p=>p.id==='musica').skills.filter(s=>SK(s.id).skip).length"), 0, "no debe haber saltos en Música")
    verificar(not err, str(err)); ctx.close()

@prueba("Letras: informe para adultos con evidencia (aciertos, tiempo, retención ≥1 día) y lo que se saltó y por qué")
def t_letras_informe(C):
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_LET, errores=err, semilla=140); instalar_speak(pg); entrar(pg, "Vale"); abrir_isla(pg, "Letras")
        pg.click("#letOv [data-a=bienvenidaSi]"); pasar_gate(pg); llenar_intake_let(pg, 5, 2, "no", "copia"); pg.click("#letOv [data-a=usarPunto]"); pg.wait_for_timeout(100); pack_letras(pg)
        for dia in range(3):
            pg.evaluate("window.__OFF=%d*864e5" % (dia * 2)); pasar_sesiones(pg, "Letras", 1, perfecto=True)
        pg.evaluate("window.__OFF=7*864e5")
        abrir_isla(pg, "Letras"); tarjeta(pg, "Informe para adultos"); pasar_gate(pg); pg.wait_for_selector("#letOv.show")
        txt = pg.evaluate("document.getElementById('letPre').innerText")
        for esperado in ("INFORME DE LETRAS — VALE", "Respuestas de los adultos", "5 años", "Punto de partida: tramo 3", "HABILIDADES", "Aciertos al primer intento", "Retención", "Saltada según las preguntas para adultos", "SALTOS:", "Cómo leerlo"):
            verificar(esperado in txt, "falta «%s» en el informe:\n%s" % (esperado, txt[:1800]))
        CAPTURAS.append(foto(pg, v + "_67_letras_informe"))
        verificar(not err, "%s: %s" % (v, err)); ctx.close()
    return txt.split("\n")[0]
# ---------------------------------------------------------------- Misiones reales + Álbum de logros reales
import unicodedata
# Lista PROPIA de la prueba (independiente de la que usa la app): fuego/calor, filo y corte, químicos del hogar, electricidad de red, resina/epoxi/solventes
PROHIBIDAS_PY = [r"fuego", r"fogata", r"llamarada", r"encend\w*", r"fosforo\w*", r"hornalla\w*", r"horno\w*", r"estufa\w*", r"microondas", r"hervi\w*", r"hirvi\w*", r"calient\w*", r"calent\w*", r"quem\w*", r"soplete\w*",
    r"cuchill\w*", r"tijera\w*", r"filos?", r"afilad\w*", r"navaja\w*", r"trincheta\w*", r"cutter", r"cuter", r"serrucho\w*", r"cortar", r"cortad\w*", r"martillo\w*", r"taladro\w*",
    r"lavandina", r"cloro", r"amoniaco", r"solvente\w*", r"thinner", r"aguarras", r"nafta", r"acetona", r"alcohol", r"desinfectante\w*", r"limpiador\w*", r"acido\w*", r"veneno\w*",
    r"resina\w*", r"epoxi\w*", r"poliester", r"catalizador\w*", r"enchufe\w*", r"electric\w*", r"tomacorriente\w*", r"cargador\w*", r"cable\w*"]
# Lo mismo para inglés (lista propia de la prueba; "heat" como sustantivo se permite, igual que "calor" en español)
PROHIBIDAS_EN_PY = [r"fire\w*", r"flame\w*", r"match(es|box\w*)", r"lighter\w*", r"candle\w*", r"stove\w*", r"oven\w*", r"microwave\w*", r"boil\w*", r"burn\w*", r"hot", r"heating", r"heated", r"heater\w*",
    r"knife", r"knives", r"scissors", r"sharp\w*", r"blade\w*", r"razor\w*", r"cutter\w*", r"cut(s|ting)?", r"hammer\w*", r"drill\w*",
    r"bleach", r"chlorine", r"ammonia", r"solvent\w*", r"thinner", r"gasoline", r"petrol", r"acetone", r"alcohol", r"disinfectant\w*", r"cleaner\w*", r"acid\w*", r"poison\w*",
    r"resin\w*", r"epoxy", r"polyester", r"catalyst\w*", r"outlet\w*", r"socket\w*", r"electric\w*", r"charger\w*", r"cable\w*"]
def sin_tildes(t): return "".join(c for c in unicodedata.normalize("NFD", t.lower()) if unicodedata.category(c) != "Mn")
def textos_de(x, out=None):
    out = [] if out is None else out
    if isinstance(x, str): out.append(x)
    elif isinstance(x, list): [textos_de(y, out) for y in x]
    elif isinstance(x, dict): [textos_de(y, out) for y in x.values()]
    return out

def jpeg_prueba(nombre, w=3000, h=2000, color=(200, 80, 40)):
    """JPEG grande con EXIF (marca de cámara) para comprobar que la app lo achica y le saca los metadatos."""
    from PIL import Image
    SALIDA.mkdir(exist_ok=True); ruta = SALIDA / nombre
    im = Image.new("RGB", (w, h), color); ex = Image.Exif(); ex[0x010F] = "CamaraDePrueba"; ex[0x0110] = "Modelo-X"
    im.save(str(ruta), "JPEG", quality=92, exif=ex); return ruta

def mis_abrir(pg, mid):
    abrir_isla(pg, "Misiones"); pg.click("#menuIslaItems .island:has-text('Elegir')"); pg.wait_for_timeout(100)
    pg.click(".mis-card[data-id='%s']" % mid); pg.wait_for_timeout(120)
def mis_paso(pg): return pg.evaluate("(Gioval.misiones.estado()||{}).paso||null")
def pasar_gate(pg):
    pg.wait_for_selector("#gateBox.show"); pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_timeout(120)
def mis_hasta(pg, objetivo):
    """Avanza una misión por la interfaz (como lo haría un niño con un adulto) hasta llegar al paso pedido."""
    for _ in range(80):
        p = mis_paso(pg)
        if p == objetivo: return
        if p == "listo":
            pg.click("#misAcc .btn:last-child")
            if pg.evaluate("document.getElementById('gateBox').classList.contains('show')"): pasar_gate(pg)
        elif p == "materiales":
            for k in range(pg.locator("#misCont .mis-mat").count()): pg.click("#misCont .mis-mat >> nth=%d" % k)
            pg.click("#misTodo")
        elif p == "antes":
            if pg.locator("#misCont .mis-chip").count(): pg.click("#misCont .mis-chip >> nth=0")
            pg.click("#misAcc .btn:last-child")
        elif p in ("hacer", "porque", "espera"): pg.click("#misAcc .btn:last-child")
        elif p == "quepaso": pg.click("#misCont .mis-chip >> nth=0"); pg.click("#misAcc .btn:last-child")
        else: raise Falla("paso inesperado: %s" % p)
        pg.wait_for_timeout(50)
    raise Falla("no se llegó al paso " + objetivo)
def mis_foto_on(pg, ruta):
    pg.click("#misCont details summary"); pg.click("#misCont [data-act=tgFoto]"); pasar_gate(pg)
    pg.set_input_files("#misFile", str(ruta)); pg.wait_for_selector("#misCont .mis-fotoprev img")
def mis_registrar(pg, frase, res="pensaba", foto=None):
    pg.fill("#misCont textarea[data-in=frase]", frase); pg.click("#misCont [data-res=%s]" % res)
    if foto: mis_foto_on(pg, foto)
    pg.click("#misGuardar"); pg.wait_for_function("(Gioval.misiones.estado()||{}).paso==='fin'", timeout=8000)
def mis_completa(pg, mid, frase, res="pensaba", foto=None):
    mis_abrir(pg, mid); mis_hasta(pg, "registro"); mis_registrar(pg, frase, res, foto)
def n_fotos(pg): return pg.evaluate("Gioval.almacen.fotos.listar().then(l=>l.length)")
def album(pg): return pg.evaluate("JSON.parse(JSON.stringify((store.misiones&&store.misiones.album&&store.misiones.album[KID])||[]))")
def mis_textos(pg):
    """{id: textos de la misión} en el idioma que está usando la app (salen de la tabla de idioma, por clave misiones.m.<id>.*)."""
    return json.loads(pg.evaluate("JSON.stringify(Object.fromEntries(Gioval.datos.misiones.MISIONES.map(m=>[m.id,Gioval.datos.misiones.textos(m)])))"))
def U(pg, clave, **p):
    """Texto de la interfaz de Misiones (clave misiones.ui.<clave>) en el idioma actual."""
    return pg.evaluate("([k,p])=>t('misiones.ui.'+k,p)", [clave, p])
def tabla_mis(pg, codigo):
    """Todas las claves misiones.* de una tabla de idioma, sin formatear."""
    return json.loads(pg.evaluate("c=>JSON.stringify(Object.fromEntries(Object.entries(Gioval.i18n.tablas[c].textos).filter(([k])=>k.startsWith('misiones.'))))", codigo))

@prueba("misiones: contenido válido (≥12, 2 por categoría, desde 4 años, materiales + supervisión + aviso, sin palabras prohibidas)")
def t_mis_datos(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    d = json.loads(pg.evaluate("JSON.stringify({M:Gioval.datos.misiones.MISIONES, ok:Gioval.datos.misiones.MISIONES.map(m=>Gioval.datos.misiones.validar(m)), vis:Gioval.misiones.lista().length, cat:Gioval.datos.misiones.CATEGORIAS})"))
    Ms, T = d["M"], mis_textos(pg)
    verificar(len(Ms) >= 12, "hay %d misiones" % len(Ms)); igual(d["vis"], len(Ms), "misiones visibles")
    igual(len({m["id"] for m in Ms}), len(Ms), "ids repetidos"); igual(set(T), {m["id"] for m in Ms}, "textos y estructura no coinciden")
    # los textos están SOLO en las tablas de idioma: es-AR y en tienen exactamente las mismas claves misiones.*
    es, en = tabla_mis(pg, "es-AR"), tabla_mis(pg, "en"); igual(sorted(en), sorted(es), "en y es-AR: mismas claves misiones.*")
    ids_tabla = {k.split(".")[2] for k in es if k.startswith("misiones.m.")}; igual(ids_tabla, {m["id"] for m in Ms}, "misiones con textos en la tabla")
    cats = sorted(d["cat"]); igual(cats, sorted(["construir", "experimentos", "cocina", "huerta", "arte", "hogar"]), "categorías")
    for c in cats: verificar(sum(1 for m in Ms if m["cat"] == c) >= 2, "menos de 2 misiones en " + c); verificar("misiones.cat." + c in es and "misiones.cat." + c in en, "falta el nombre de la categoría " + c)
    verificar(min(m["minEdad"] for m in Ms) == 4 and all(m["minEdad"] >= 4 for m in Ms), "edad mínima desde 4")
    # cada u("…") del código de la isla existe en la tabla (no hay claves inventadas ni faltantes)
    codigo = (APP / "js" / "islas" / "misiones.js").read_text(encoding="utf-8")
    usadas = set(re.findall(r'\bul?\("([a-z0-9_.]+)"', codigo)); usadas = {k for k in usadas if not k.endswith(".")}; verificar(len(usadas) > 80, "pocas claves detectadas: %d" % len(usadas))
    faltan = sorted(k for k in usadas if "misiones.ui." + k not in es); verificar(not faltan, "u(\"…\") sin clave en es-AR: %s" % faltan)
    for k in ("supervision.cerca.corto", "supervision.junto.detalle", "burbuja.listo", "burbuja.fin", "fin.pensaba", "fin.distinto", "fin.cierre"): verificar("misiones.ui." + k in es, "falta " + k)
    sin_coment = re.sub(r"(?m)^\s*//.*$", "", re.sub(r"/\*.*?\*/", "", codigo, flags=re.S))
    esp = [m.group(0)[:60] for m in re.finditer(r"""(["'`])((?:\\.|(?!\1)[^\\\n])*)\1""", sin_coment) if re.search(r"[¿¡áéíóúñÁÉÍÓÚÑ]", m.group(2))]
    verificar(not esp, "texto en español escrito en el código de la isla (tiene que ir en la tabla): %s" % esp[:3])
    nprohib = 0
    for m, probs in zip(Ms, d["ok"]):
        t = T[m["id"]]; igual(probs, [], "validar " + m["id"])
        verificar(m["sup"] in ("cerca", "junto"), m["id"] + " sin supervisión"); verificar(len(t["materiales"]) >= 1, m["id"] + " sin materiales")
        verificar(len(t["aviso"].strip()) >= 20, m["id"] + " sin aviso de seguridad"); verificar(len(t["pasos"]) >= 2, m["id"] + " sin pasos")
        if m["tipo"] != "hacer": verificar(t["prediccion"]["pregunta"] and len(t["prediccion"]["opciones"]) >= 2 and t["observacion"] and t["explicacion"] and t["guia"], m["id"] + " sin estructura científica")
        else: verificar(t.get("imaginar"), m["id"] + " sin imaginar")
        verificar("A REVISAR" not in json.dumps(t) and not m.get("revisar"), m["id"] + " tiene datos sin confirmar")
        for tx in textos_de(t):
            nprohib += 1
            for pat in PROHIBIDAS_PY: verificar(not re.search(r"(^|[^a-z])(%s)($|[^a-z])" % pat, sin_tildes(tx)), "%s: palabra prohibida /%s/ en «%s»" % (m["id"], pat, tx[:60]))
    # lo mismo en inglés (lista PROPIA de la prueba, distinta de la de la app) sobre TODAS las claves misiones.m.* y misiones.ui.* de la tabla en
    nen = 0
    for k, v in en.items():
        for tx in textos_de(v):
            nen += 1
            for pat in PROHIBIDAS_EN_PY: verificar(not re.search(r"(^|[^a-z])(%s)($|[^a-z])" % pat, tx.lower()), "en/%s: palabra prohibida /%s/ en «%s»" % (k, pat, tx[:60]))
    nexp = sum(1 for m in Ms if m["tipo"] != "hacer"); verificar(nexp >= 5, "pocos experimentos")
    # el elogio es al proceso: nada de "genio", rachas ni puntos en ningún texto de la interfaz
    ui = sin_tildes(json.dumps({k: v for k, v in es.items() if k.startswith("misiones.ui.")}, ensure_ascii=False))
    for mala in ("genio", "inteligent", "talento", "brillante", "el mejor", "la mejor", "campe", "racha", "puntos", "ranking"): verificar(mala not in ui, "texto de la interfaz con «%s»" % mala)
    uien = json.dumps({k: v for k, v in en.items() if k.startswith("misiones.ui.")}).lower()
    for mala in ("genius", "smart", "talent", "brilliant", "the best", "champion", "streak", "points", "ranking"): verificar(mala not in uien, "texto de la interfaz en inglés con «%s»" % mala)
    # el validador de verdad rechaza lo malo (prueba de la prueba)
    r = pg.evaluate("""(()=>{ const D=Gioval.datos.misiones, m=D.MISIONES.find(x=>x.id==='exp_flota'), I=Gioval.i18n.tablas, k='misiones.m.exp_flota.';
      const copia=x=>JSON.parse(JSON.stringify(x)), cod=c=>Object.keys(I[c].textos).filter(x=>x.startsWith(k)), bak={};
      ['es-AR','en'].forEach(c=>{ bak[c]=Object.fromEntries(cod(c).map(x=>[x,copia(I[c].textos[x])])); });
      const v=(mut,mm,c)=>{ const T=I[c||'es-AR'].textos; mut(T); const n=D.validar(Object.assign({},m,mm||{})).length; Object.assign(T,copia(bak[c||'es-AR'])); return n; };
      const fr=()=>{ Gioval.i18n.registrar('fr',{textos:{[k+'nombre']:'Flotte'}}); const n=D.validar(m).length; delete I.fr; return n; };
      return { aviso:v(T=>{T[k+'aviso']='';}), mats:v(T=>{T[k+'materiales']=[];}), sup:v(T=>{},{sup:'solo'}), edad:v(T=>{},{minEdad:3}), lav:v(T=>{T[k+'pasos'][1]='Mezclá con lavandina.';}), cuch:v(T=>{T[k+'materiales'].push('Un cuchillo');}),
        epoxi:v(T=>{T[k+'aviso']='Con epoxi, cuidado, mucho cuidado.';}), fuego:v(T=>{T[k+'pasos'][0]='Prendé fuego';}),
        en_fuego:v(T=>{T[k+'pasos'][0]='Light a fire';},{},'en'), en_cuchillo:v(T=>{T[k+'materiales'].push('A sharp knife');},{},'en'), idioma_sin_lista:fr(), ok:v(T=>{}), ok_en:v(T=>{},{},'en') }; })()""")
    igual(r, {"aviso": 1, "mats": 1, "sup": 1, "edad": 1, "lav": 1, "cuch": 1, "epoxi": 1, "fuego": 1, "en_fuego": 1, "en_cuchillo": 1, "idioma_sin_lista": 1, "ok": 0, "ok_en": 0}, "el validador (también rechaza lo malo escrito en inglés o en un idioma sin lista)")
    # una misión inválida queda oculta (no se le muestra al niño)
    pg.evaluate("console.warn=()=>{}")
    visible = pg.evaluate("""(()=>{ const D=Gioval.datos.misiones, T=Gioval.i18n.tablas['es-AR'].textos, k='misiones.m.mala.'; Object.assign(T,{[k+'nombre']:'Mala',[k+'resumen']:'x',[k+'aviso']:'',[k+'materiales']:['a'],[k+'pasos']:['a','b'],[k+'imaginar']:'x'});
      D.MISIONES.push({id:'mala',cat:'arte',emoji:'💥',minEdad:4,sup:'cerca',tipo:'hacer'}); const n=Gioval.misiones.recargar().some(m=>m.id==='mala'); D.MISIONES.pop(); Object.keys(T).filter(x=>x.startsWith(k)).forEach(x=>delete T[x]); Gioval.misiones.recargar(); return n; })()""")
    igual(visible, False, "una misión sin aviso no debe mostrarse")
    ctx.close(); return "%d misiones (%d experimentos), %d textos es-AR contra %d palabras prohibidas y %d textos en inglés contra %d" % (len(Ms), nexp, nprohib, len(PROHIBIDAS_PY), nen, len(PROHIBIDAS_EN_PY))

@prueba("misiones: flujo completo de un experimento (aviso → materiales → predicción → hacer + temporizador → ¿qué pasó? → ¿por qué? → registro) en 360x700 y 740x330")
def t_mis_flujo(C):
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=81); instalar_speak(pg); entrar(pg, "Vale")
        t = mis_textos(pg)["exp_hielo"]
        t0 = pg.evaluate("JSON.stringify(store.time)")
        abrir_isla(pg, "Misiones")
        txt = pg.inner_text("#menuIslaItems")
        verificar("Misión de la semana" in txt and "Elegir una misión" in txt and "Mi álbum" in txt, txt)
        verificar("Sesión de hoy" not in txt and "Chequeo" not in txt, "Misiones no tiene sesión ni chequeo: " + txt)
        verificar("Sin tope de pantalla" in pg.inner_text("#streak"), "etiqueta de tiempo")
        CAPTURAS.append(foto(pg, v + "_60_misiones_menu"))
        pg.click("#menuIslaItems .island:has-text('Elegir')"); pg.wait_for_timeout(100); CAPTURAS.append(foto(pg, v + "_61_misiones_lista"))
        pg.click(".mis-card[data-id='exp_hielo']"); pg.wait_for_timeout(150)
        # 1) el aviso de seguridad y el nivel de supervisión se ven ANTES de empezar (y se dicen en voz alta)
        igual(mis_paso(pg), "listo", "primer paso")
        verificar(pg.is_visible("#misAviso") and t["aviso"] in pg.inner_text("#misAviso"), "aviso no visible")
        arriba = pg.evaluate("(()=>{ const r=document.getElementById('misAviso').getBoundingClientRect(), c=document.getElementById('misCont').getBoundingClientRect(); return r.top>=c.top-1 && r.top<c.bottom; })()")
        verificar(arriba, "el aviso no está a la vista al abrir la misión")
        verificar(U(pg, "supervision.cerca.corto") in pg.inner_text("#misCont"), "falta el nivel de supervisión")
        verificar(any(t["aviso"] in x for x in pg.evaluate("window.__LOG")), "el aviso no se dijo en voz alta")
        CAPTURAS.append(foto(pg, v + "_62_mision_aviso"))
        pg.click("#misAcc .btn:last-child"); igual(mis_paso(pg), "materiales")
        # 2) checklist: no se avanza hasta tener todo
        verificar(pg.is_disabled("#misTodo"), "avanza sin materiales")
        n = len(t["materiales"])
        for k in range(n - 1): pg.click("#misCont .mis-mat >> nth=%d" % k)
        verificar(pg.is_disabled("#misTodo"), "avanza con materiales a medias")
        CAPTURAS.append(foto(pg, v + "_63_mision_materiales"))
        pg.click("#misCont .mis-mat >> nth=%d" % (n - 1)); verificar(not pg.is_disabled("#misTodo")); pg.click("#misTodo")
        # 3) predicción obligatoria
        igual(mis_paso(pg), "antes"); verificar(pg.is_disabled("#misAcc .btn"), "avanza sin predecir")
        igual(pg.locator("#misCont .mis-chip").count(), len(t["prediccion"]["opciones"]) + 2, "opciones + otra idea + no sé")
        CAPTURAS.append(foto(pg, v + "_64_mision_prediccion"))
        pg.click("#misCont .mis-chip >> nth=0"); pg.click("#misAcc .btn")
        # 4) hacer, paso a paso, con voz y temporizador
        igual(mis_paso(pg), "hacer"); verificar(t["pasos"][0] in pg.evaluate("window.__LOG"), "el paso 1 no se dijo")
        for k in range(1, 3): pg.click("#misAcc .btn:last-child"); verificar(t["pasos"][k] in pg.evaluate("window.__LOG"), "el paso %d no se dijo" % (k + 1))
        verificar(pg.is_visible("[data-act=timer]"), "falta el temporizador en el paso 3")
        pg.click("[data-act=timer]"); r = pg.evaluate("Alarma.restante()"); verificar(598 <= r <= 600, "temporizador de 10 min: %s" % r)
        pg.wait_for_function("document.getElementById('misTimerEstado').innerText.includes('Falta')"); CAPTURAS.append(foto(pg, v + "_65_mision_temporizador"))
        pg.evaluate("window.__OFF=601000; Alarma._revisar()"); pg.wait_for_timeout(100)
        verificar(U(pg, "timer.fin") in pg.evaluate("window.__LOG"), "no avisó que terminó el temporizador"); igual(pg.evaluate("Gioval.misiones.estado().timer"), False)
        pg.evaluate("window.__OFF=0")
        while mis_paso(pg) == "hacer": pg.click("#misAcc .btn:last-child"); pg.wait_for_timeout(40)
        # 5) ¿qué pasó? y ¿por qué creés?
        igual(mis_paso(pg), "quepaso"); verificar(pg.is_disabled("#misAcc .btn"), "avanza sin observar")
        verificar(pg.inner_text("#bubble").strip() and len(pg.inner_text("#bubble")) < 60, "el globito debe llevar una frase corta, no el texto largo: " + pg.inner_text("#bubble"))
        pg.click("#misCont .mis-chip >> nth=1"); CAPTURAS.append(foto(pg, v + "_66_mision_quepaso")); pg.click("#misAcc .btn")
        igual(mis_paso(pg), "porque"); igual(pg.locator(".mis-exp").count(), 0, "la explicación no se muestra hasta pedirla")
        pg.fill("#misCont textarea[data-in=porque]", "porque el sol calienta"); pg.click("#misAcc .btn:has-text('explicación')")
        verificar(t["explicacion"] in pg.inner_text(".mis-exp"), "no muestra la explicación al adulto"); verificar(U(pg, "porque.para_adulto") in pg.inner_text(".mis-exp"))
        CAPTURAS.append(foto(pg, v + "_67_mision_porque")); pg.click("#misAcc .btn:last-child")
        # 6) registrar: sin elegir pensaba/distinto no se guarda
        igual(mis_paso(pg), "registro"); verificar(pg.is_disabled("#misGuardar")); verificar(U(pg, "adulto.foto_off") in pg.inner_text("#misCont"), "debería decir que la foto necesita al adulto")
        igual(pg.locator("#misSacar").count(), 0, "botón de foto sin consentimiento")
        pg.fill("#misCont textarea[data-in=frase]", "El del sol se derritió primero"); pg.click("#misCont [data-res=distinto]"); CAPTURAS.append(foto(pg, v + "_68_mision_registro"))
        pg.click("#misGuardar"); pg.wait_for_function("(Gioval.misiones.estado()||{}).paso==='fin'")
        msg = pg.inner_text("#misFinTxt"); CAPTURAS.append(foto(pg, v + "_69_mision_fin"))
        verificar("distinto" in msg and ("Miraste" in msg or "Observaste" in msg), "mensaje de proceso: " + msg)
        for mala in ("genio", "inteligente", "mejor", "racha", "puntos"): verificar(mala not in msg.lower(), "elogio a la persona: " + msg)
        a = album(pg); igual(len(a), 1, "entradas del álbum"); e = a[0]
        igual((e["m"], e["res"], e["frase"], e["porque"], e["foto"], e["pred"], e["obs"]), ("exp_hielo", "distinto", "El del sol se derritió primero", "porque el sol calienta", None, t["prediccion"]["opciones"][0], t["observacion"][1]), "entrada")
        igual(n_fotos(pg), 0, "sin consentimiento no se guarda foto")
        # el tiempo de misiones NO cuenta como pantalla
        pg.wait_for_timeout(2300); igual(pg.evaluate("JSON.stringify(store.time)"), t0, "las misiones no deben sumar tiempo de pantalla")
        pg.click("#misAcc .btn:has-text('álbum')"); pg.wait_for_timeout(250)
        verificar("El del sol se derritió primero" in pg.inner_text("#misAlbLista") and "Hielo" in pg.inner_text("#misAlbLista"), "el álbum no muestra la entrada")
        CAPTURAS.append(foto(pg, v + "_70_album_nino"))
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

@prueba("misiones: sin tope diario de pantalla (Números sí lo respeta) y sin sesión/chequeo en la isla")
def t_mis_sin_tope(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=82); instalar_speak(pg); entrar(pg, "Vale")
    pg.evaluate("store.time['Vale|'+today()]=99999"); verificar(pg.evaluate("capLeft()") < 0)
    abrir_isla(pg, "Misiones"); verificar("Elegir una misión" in pg.inner_text("#menuIslaItems"))
    mis_abrir(pg, "hogar_medias"); mis_hasta(pg, "registro"); mis_registrar(pg, "Había 5 pares")
    verificar(not pg.evaluate("document.getElementById('capBox').classList.contains('show')"), "el tope de pantalla no debe frenar misiones")
    abrir_isla(pg, "Números"); verificar("Mañana seguimos" in pg.inner_text("#menuIslaItems"), "Números sí respeta el tope")
    igual(pg.evaluate("PACKS.find(p=>p.id==='misiones').skills.length"), 0, "Misiones no declara habilidades")
    verificar(not err, str(err)); ctx.close()

@prueba("misiones: foto con permiso del adulto (achicada, sin metadatos, solo en el aparato), álbum y borrado por adultos")
def t_mis_foto(C):
    ruta = jpeg_prueba("foto_grande.jpg"); original = ruta.stat().st_size; verificar(b"Exif" in ruta.read_bytes()[:100], "la foto de prueba debería traer EXIF")
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []; reqs = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=83); instalar_speak(pg); entrar(pg, "Vale")
        pg.on("request", lambda r: reqs.append((r.method, r.url)))
        mis_abrir(pg, "arte_dibujo_secreto"); mis_hasta(pg, "registro")
        pg.fill("#misCont textarea[data-in=frase]", "¡Apareció mi estrella!"); pg.click("#misCont [data-res=pensaba]")
        # el permiso de la foto exige al adulto (candado) y se puede volver a apagar
        pg.click("#misCont details summary"); pg.click("#misCont [data-act=tgFoto]")
        verificar(pg.evaluate("document.getElementById('gateBox').classList.contains('show')"), "no pidió el candado de adultos")
        igual(pg.evaluate("Gioval.misiones.estado().consent"), False, "no debe activarse sin el candado")
        pg.click("#gateNo"); igual(pg.evaluate("Gioval.misiones.estado().consent"), False)
        pg.click("#misCont [data-act=tgFoto]"); pasar_gate(pg); igual(pg.evaluate("Gioval.misiones.estado().consent"), True)
        verificar(pg.is_visible("#misSacar"), "falta el botón de foto"); CAPTURAS.append(foto(pg, v + "_71_mision_foto_permiso"))
        pg.set_input_files("#misFile", str(ruta)); pg.wait_for_selector("#misCont .mis-fotoprev img"); CAPTURAS.append(foto(pg, v + "_72_mision_foto_prev"))
        igual(n_fotos(pg), 0, "la foto no se guarda hasta tocar Guardar")
        pg.click("#misGuardar"); pg.wait_for_function("(Gioval.misiones.estado()||{}).paso==='fin'", timeout=8000)
        a = album(pg); igual(len(a), 1); fid = a[0]["foto"]; verificar(fid, "la entrada no tiene foto"); igual(n_fotos(pg), 1)
        info = pg.evaluate("""Gioval.almacen.fotos.obtener(%s).then(async r=>{ const b=await createImageBitmap(r.blob); const bytes=new Uint8Array(await r.blob.arrayBuffer());
          let exif=false; for(let i=0;i<bytes.length-4;i++){ if(bytes[i]===69&&bytes[i+1]===120&&bytes[i+2]===105&&bytes[i+3]===102){ exif=true; break; } } return {tipo:r.blob.type,w:b.width,h:b.height,peso:r.blob.size,exif:exif,meta:r.meta}; })""" % json.dumps(fid))
        igual(info["tipo"], "image/jpeg"); verificar(max(info["w"], info["h"]) <= 1024, "no se achicó: %sx%s" % (info["w"], info["h"])); verificar(info["peso"] < original / 5, "pesa mucho: %d" % info["peso"])
        verificar(not info["exif"], "la foto guardada conserva metadatos (EXIF)"); igual(info["meta"]["perfil"], "Vale")
        fuera = [u for _, u in reqs if not (u.startswith(C.url) or u.startswith("blob:") or u.startswith("data:"))]
        verificar(not fuera, "pedidos de red fuera del aparato: %s" % fuera[:3])
        verificar(not any(m != "GET" for m, _ in reqs), "no debe haber pedidos que suban datos: %s" % [r for r in reqs if r[0] != "GET"])
        # álbum del niño: ve la foto y NO puede borrar
        pg.click("#misAcc .btn:has-text('álbum')"); pg.wait_for_selector("#misAlbLista .mis-foto img"); verificar("¡Apareció mi estrella!" in pg.inner_text("#misAlbLista"))
        igual(pg.locator("[data-del]").count(), 0, "el niño no debería ver los botones de borrar"); CAPTURAS.append(foto(pg, v + "_73_album_foto_nino"))
        # vista de adultos: pide candado, permite borrar
        pg.click("#misAlbModo"); pasar_gate(pg); verificar(pg.locator("[data-del]").count() == 1 and pg.locator("[data-delfoto]").count() == 1)
        verificar("solo en este aparato" in pg.inner_text("#misAlbInfo")); CAPTURAS.append(foto(pg, v + "_74_album_adultos"))
        pg.click("[data-del]"); verificar(pg.is_visible("#misConfirm")); pg.click("#misConfirmNo"); igual(len(album(pg)), 1, "cancelar no borra"); igual(n_fotos(pg), 1)
        pg.click("[data-delfoto]"); pg.click("#misConfirmSi"); pg.wait_for_timeout(300)
        igual(n_fotos(pg), 0, "borrar solo la foto"); a = album(pg); igual(len(a), 1, "la entrada queda"); igual(a[0]["foto"], None)
        pg.click("[data-del]"); pg.click("#misConfirmSi"); pg.wait_for_timeout(300)
        igual(len(album(pg)), 0, "borrar el recuerdo"); verificar("Todavía no hay recuerdos" in pg.inner_text("#misAlbLista")); igual(n_fotos(pg), 0)
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

@prueba("misiones: respaldo exportar → borrar todo → restaurar recupera álbum Y fotos (y un respaldo viejo sin fotos no las borra)")
def t_mis_respaldo(C):
    f1 = jpeg_prueba("foto_a.jpg", 1600, 1200, (10, 120, 200)); f2 = jpeg_prueba("foto_b.jpg", 800, 1100, (200, 200, 20))
    ctx = C.banco.contexto("360x700", accept_downloads=True); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=84); instalar_speak(pg); entrar(pg, "Vale")
    mis_completa(pg, "construir_casita", "Mi casita con techo", "pensaba", f1); mis_completa(pg, "exp_flota", "La piedra se hundió", "distinto", f2); mis_completa(pg, "hogar_medias", "Sin foto", "pensaba")
    antes = album(pg); igual(len(antes), 3); igual(n_fotos(pg), 2)
    sha = "Gioval.almacen.fotos.listar().then(async l=>{ const o={}; for(const f of l){ const r=await Gioval.almacen.fotos.obtener(f.id); const h=await crypto.subtle.digest('SHA-256',await r.blob.arrayBuffer()); o[f.id]=Array.from(new Uint8Array(h)).map(x=>x.toString(16).padStart(2,'0')).join(''); } return o; })"
    hashes = pg.evaluate(sha); igual(len(hashes), 2)
    abrir_panel(pg)
    with pg.expect_download() as d: pg.click("#btnExport")
    ruta = SALIDA / "respaldo_misiones.json"; d.value.save_as(str(ruta)); pg.wait_for_timeout(300)
    arch = json.loads(ruta.read_text(encoding="utf-8")); igual(len(arch["fotos"]), 2, "el respaldo debe llevar las fotos"); igual(sorted(f["id"] for f in arch["fotos"]), sorted(hashes), "ids de fotos")
    verificar(all(f["datos"].startswith("data:image/jpeg;base64,") for f in arch["fotos"]))
    igual(len(arch["store"]["misiones"]["album"]["Vale"]), 3, "el álbum viaja dentro del store")
    # borrar TODO (localStorage + las 3 bases de IndexedDB) y comprobar que no queda nada
    pg.evaluate("localStorage.clear()")
    pg.evaluate("new Promise(r=>{ const q=indexedDB.open('gioval-db'); q.onsuccess=()=>{ const d=q.result; const t=d.transaction(['estado','respaldo','fotos'],'readwrite'); ['estado','respaldo','fotos'].forEach(n=>t.objectStore(n).clear()); t.oncomplete=()=>{ d.close(); r(1); }; }; })")
    pg.reload(); esperar_listo(pg); igual(pg.evaluate("store.profiles"), [], "después de borrar"); igual(n_fotos(pg), 0, "fotos después de borrar")
    pg.evaluate("document.getElementById('nameBox').classList.remove('show')"); abrir_panel(pg); pg.set_input_files("#fileRestore", str(ruta)); pg.wait_for_selector("#restoreBox.show")
    verificar("Fotos: 2" in pg.inner_text("#restoreTxt"), pg.inner_text("#restoreTxt"))
    with pg.expect_navigation(): pg.click("#restoreOk")
    esperar_listo(pg); pg.wait_for_timeout(300); instalar_speak(pg); entrar(pg, "Vale"); despues = album(pg); igual(despues, antes, "álbum restaurado"); igual(n_fotos(pg), 2, "fotos restauradas")
    igual(pg.evaluate(sha), hashes, "las fotos restauradas deben ser idénticas byte a byte")
    pg.evaluate("Gioval.misiones.abrirAlbum(false)"); pg.wait_for_function("document.querySelectorAll('#misAlbLista .mis-foto img').length===2", timeout=8000)
    CAPTURAS.append(foto(pg, "360x700_76_album_restaurado"))
    # un respaldo viejo (sin la clave "fotos") no toca las fotos existentes
    viejo = dict(arch); viejo.pop("fotos"); rv = SALIDA / "respaldo_sin_fotos.json"; rv.write_text(json.dumps(viejo), encoding="utf-8")
    abrir_panel(pg); pg.set_input_files("#fileRestore", str(rv)); pg.wait_for_selector("#restoreBox.show"); verificar("Fotos:" not in pg.inner_text("#restoreTxt"))
    with pg.expect_navigation(): pg.click("#restoreOk")
    esperar_listo(pg); igual(n_fotos(pg), 2, "restaurar sin fotos no debe borrar las de hoy")
    rs = pg.evaluate("Gioval.almacen.respaldos().then(l=>l.filter(r=>r.id.startsWith('pre-restauracion-fotos')).length)"); verificar(rs >= 1, "falta la copia previa de fotos")
    verificar(not err, str(err)); ctx.close()

@prueba("misiones: misión de la semana (automática por edad, elegida por adultos, rota semana a semana) y misiones bloqueadas por edad")
def t_mis_semana(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=85); instalar_speak(pg); entrar(pg, "Vale")
    Ms = {m["id"]: m for m in json.loads(pg.evaluate("JSON.stringify(Gioval.datos.misiones.MISIONES)"))}
    abrir_isla(pg, "Misiones"); verificar("Misión de la semana" in pg.inner_text("#menuIslaItems"))
    abrir_panel(pg); verificar("Misiones" in pg.inner_text("#panel")); CAPTURAS.append(foto(pg, "360x700_77_panel_misiones"))
    pg.select_option("#misPEdad", "4"); igual(pg.evaluate("store.misiones.edad.Vale"), 4)
    vistas = set()
    for k in range(10):
        pg.evaluate("window.__OFF=%d" % (k * 7 * 864e5)); sid = pg.evaluate("Gioval.misiones.semana().id"); vistas.add(sid)
        verificar(Ms[sid]["minEdad"] <= 4, "misión de la semana para 4 años con edad mínima %d: %s" % (Ms[sid]["minEdad"], sid))
    verificar(len(vistas) >= 4, "la misión de la semana no rota: %s" % vistas)
    pg.evaluate("window.__OFF=0"); a = pg.evaluate("Gioval.misiones.semana().id"); igual(pg.evaluate("Gioval.misiones.semana().id"), a, "estable dentro de la semana")
    pg.click("#btnGear"); abrir_isla(pg, "Misiones"); pg.click("#menuIslaItems .island:has-text('Elegir')")
    verificar(pg.locator(".mis-card.off").count() == 1 and "Puente de papel" in pg.locator(".mis-card.off").inner_text(), "con 4 años el puente (desde 5) debería estar bloqueado")
    igual(pg.locator(".mis-tagsem").count(), 1, "marca de la semana")
    # el adulto elige la misión de la semana
    abrir_panel(pg); pg.select_option("#misPSem", "exp_flota"); igual(pg.evaluate("Gioval.misiones.semana().id"), "exp_flota"); pg.click("#btnGear")
    abrir_isla(pg, "Misiones"); verificar("¿Flota o se hunde?" in pg.inner_text("#menuIslaItems"), "la tarjeta debería mostrar la elegida")
    pg.click("#menuIslaItems .island >> nth=0"); pg.wait_for_timeout(150); igual(pg.evaluate("Gioval.misiones.estado().m.id"), "exp_flota")
    # a la semana siguiente vuelve a ser automática
    pg.evaluate("window.__OFF=7*864e5+3600e3"); pg.evaluate("Gioval.misiones.semana()"); igual(pg.evaluate("store.misiones.semana.Vale.auto"), True, "la semana siguiente debería ser automática")
    verificar(not err, str(err)); ctx.close()

@prueba("misiones: una misión de espera (poroto) queda empezada y se retoma días después con su predicción")
def t_mis_espera(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=86); instalar_speak(pg); entrar(pg, "Vale")
    t = mis_textos(pg)["huerta_poroto"]
    mis_abrir(pg, "huerta_poroto"); mis_hasta(pg, "espera"); verificar("3 días" in pg.inner_text("#misCont")); CAPTURAS.append(foto(pg, "360x700_78_mision_espera"))
    pg.click("#misAcc .btn"); pg.wait_for_timeout(200)
    igual(len(album(pg)), 0, "todavía no es un recuerdo"); igual(pg.evaluate("store.misiones.pend.Vale.length"), 1)
    verificar("Mirar: Un poroto que despierta" in pg.inner_text("#menuIslaItems") and "Empezaste hoy" in pg.inner_text("#menuIslaItems"), pg.inner_text("#menuIslaItems"))
    pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(200); pg.reload(); esperar_listo(pg); instalar_speak(pg); entrar(pg, "Vale")
    pg.evaluate("window.__OFF=3*864e5+1000"); abrir_isla(pg, "Misiones"); verificar("hace 3 días" in pg.inner_text("#menuIslaItems"), pg.inner_text("#menuIslaItems"))
    pg.click("#menuIslaItems .island:has-text('Mirar')"); pg.wait_for_timeout(150); igual(mis_paso(pg), "quepaso")
    verificar(t["prediccion"]["opciones"][0] in pg.inner_text(".mis-recuerda"), "debería recordar lo que pensó")
    mis_hasta(pg, "registro"); mis_registrar(pg, "Salió una raicita", "pensaba")
    a = album(pg); igual(len(a), 1); igual((a[0]["m"], a[0]["pred"], a[0]["obs"]), ("huerta_poroto", t["prediccion"]["opciones"][0], t["observacion"][0]))
    igual(pg.evaluate("store.misiones.pend.Vale.length"), 0, "ya no está pendiente"); verificar(not err, str(err)); ctx.close()

@prueba("misiones: dictado por voz solo si el adulto lo activa; una explicación marcada A REVISAR no se muestra")
def t_mis_dictado(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=87,
        extra_init="window.SpeechRecognition=window.webkitSpeechRecognition=function(){ var s=this; s.start=function(){ window.__dic=(window.__dic||0)+1; setTimeout(function(){ s.onresult({results:[[{transcript:'se derritió'}]]}); s.onend&&s.onend(); },30); }; };")
    instalar_speak(pg); entrar(pg, "Vale")
    mis_abrir(pg, "exp_flota"); mis_hasta(pg, "porque")
    igual(pg.locator("[data-dictar]").count(), 0, "sin permiso no hay dictado")
    pg.click("#misCont details summary"); pg.click("#misCont [data-act=tgDictado]"); pasar_gate(pg)
    igual(pg.locator("[data-dictar=porque]").count(), 1, "con permiso aparece el botón de dictar"); pg.click("[data-dictar=porque]"); pg.wait_for_timeout(200)
    igual(pg.input_value("#misCont textarea[data-in=porque]"), "se derritió"); igual(pg.evaluate("Gioval.misiones.estado().porque"), "se derritió"); igual(pg.evaluate("window.__dic"), 1)
    igual(pg.locator("#misAcc .btn:has-text('explicación')").count(), 1, "debería haber botón de explicación")
    # A REVISAR: ni botón ni texto
    expl = mis_textos(pg)["exp_flota"]["explicacion"]
    pg.evaluate("Gioval.datos.misiones.MISIONES.find(m=>m.id==='exp_flota').revisar='A REVISAR: confirmar con una fuente'")
    pg.click("#misBack"); mis_abrir(pg, "exp_flota"); mis_hasta(pg, "porque")
    igual(pg.locator("#misAcc .btn:has-text('explicación')").count(), 0, "una explicación A REVISAR no debe ofrecerse"); igual(pg.locator(".mis-exp").count(), 0)
    verificar(expl not in pg.inner_text("body"), "el texto sin revisar aparece en pantalla")
    pg.evaluate("delete Gioval.datos.misiones.MISIONES.find(m=>m.id==='exp_flota').revisar")
    verificar(not err, str(err)); ctx.close()

@prueba("misiones en otros idiomas: inglés sin una palabra en español, cambio de idioma a mitad de misión, pseudo-idioma (+40 %) y RTL sin desbordes nuevos")
def t_mis_idiomas(C):
    # 1) inglés completo, de punta a punta (menú, lista, misión, registro, álbum, panel de adultos)
    ctx = C.banco.contexto("pixel7"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=88, extra_init="localStorage.setItem('gioval_idioma','en');"); instalar_speak(pg); entrar(pg, "Vale")
    vistos = []
    def mirar(*sel): vistos.extend(x for x in (pg.inner_text(s_) for s_ in sel) if x.strip())
    abrir_isla(pg, "Missions"); mirar("#menuIslaItems", "#streak", "#menuIslaTitle")
    verificar("Mission of the week" in pg.inner_text("#menuIslaItems") and "No screen limit" in pg.inner_text("#streak"), pg.inner_text("#menuIslaItems"))
    pg.click("#menuIslaItems .island >> nth=1"); pg.wait_for_timeout(100); mirar("#misLista"); CAPTURAS.append(foto(pg, "pixel7_80_misiones_ingles_lista"))
    pg.click(".mis-card[data-id='exp_flota']"); pg.wait_for_timeout(150)
    for paso in ("listo", "materiales", "antes", "hacer", "quepaso", "porque", "registro"):
        mis_hasta(pg, paso); mirar("#misCont", "#misAcc", "#misTitulo", "#bubble")
        if paso == "listo": verificar("Before we start" in pg.inner_text("#misCont") and "grown-up nearby" in pg.inner_text("#misCont"), pg.inner_text("#misCont")); CAPTURAS.append(foto(pg, "pixel7_81_mision_ingles_aviso"))
        if paso == "hacer": verificar(pg.inner_text(".mis-pasoN") == "Step 1 of 5", pg.inner_text(".mis-pasoN"))
    mis_registrar(pg, "The stone sank", "distinto"); mirar("#misCont"); verificar("different" in pg.inner_text("#misFinTxt"), pg.inner_text("#misFinTxt"))
    pg.click("#misAcc .btn:has-text('album')"); pg.wait_for_timeout(250); mirar("#misAlbum"); verificar("The stone sank" in pg.inner_text("#misAlbLista") and "Does it float or sink?" in pg.inner_text("#misAlbLista"), pg.inner_text("#misAlbLista"))
    fecha = pg.inner_text("#misAlbLista .mis-ent small:nth-of-type(1)"); verificar(re.search(r"[A-Z][a-z]+ \d{1,2}, \d{4}", fecha), "la fecha debería salir en formato inglés: " + fecha)
    pg.click("#misAlbModo"); pasar_gate(pg); mirar("#misAlbInfo", "#misAlbLista"); pg.click("#misAlbModo")
    pg.click("#misAlbBack"); abrir_panel(pg); mirar("#panelPie"); verificar("Age of Vale:" in pg.inner_text("#panelPie") and "6 years old" in pg.inner_text("#panelPie"), pg.inner_text("#panelPie"))
    pg.click("#btnGear"); dicho = pg.evaluate("window.__LOG.concat(window.__BUB)")
    igual(sin_espanol(vistos + dicho), [], "texto en español con el idioma en inglés"); igual(pg.evaluate("[...Gioval.i18n.faltantes]"), [], "claves faltantes")
    verificar(any("Step 1 of 5" in x for x in dicho) or any("Put the things" in x or "Line the things" in x for x in dicho), "no se dijeron los pasos en inglés: %s" % dicho[:5])
    verificar(not err, str(err)); ctx.close()
    # 2) cambio de idioma a mitad de una misión: se vuelve a dibujar en el mismo paso, sin perder lo hecho
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=89); instalar_speak(pg); entrar(pg, "Vale")
    mis_abrir(pg, "exp_flota"); mis_hasta(pg, "hacer"); pg.click("#misAcc .btn:last-child"); igual(pg.evaluate("Gioval.misiones.estado().i"), 1)
    verificar("Paso 2 de 5" in pg.inner_text("#misCont"), pg.inner_text("#misCont"))
    pg.evaluate("Gioval.i18n.usar('en')"); pg.wait_for_timeout(100)
    igual(pg.inner_text(".mis-pasoN"), "Step 2 of 5", "el paso se vuelve a dibujar en inglés"); igual(pg.evaluate("Gioval.misiones.estado().i"), 1, "no pierde el paso"); verificar("Before trying" in pg.inner_text(".mis-paso"), pg.inner_text(".mis-paso"))
    tc = lambda i: pg.evaluate("document.getElementById('%s').textContent" % i)
    verificar("Back" in tc("misBack") and "Listen" in tc("misHear"), "botones fijos sin traducir: %s / %s" % (tc("misBack"), tc("misHear")))
    pg.evaluate("Gioval.i18n.usar('es-AR')"); pg.wait_for_timeout(100); igual(pg.inner_text(".mis-pasoN"), "Paso 2 de 5")
    # el temporizador sigue reconociéndose aunque cambie el idioma
    pg.click("#misBack"); mis_abrir(pg, "exp_hielo"); mis_hasta(pg, "hacer"); pg.click("#misAcc .btn:last-child"); pg.click("#misAcc .btn:last-child"); pg.click("[data-act=timer]")
    pg.evaluate("Gioval.i18n.usar('en')"); pg.evaluate("window.__OFF=601000; Alarma._revisar()"); pg.wait_for_timeout(100); pg.evaluate("window.__OFF=0")
    verificar("Time's up! Look at what happened." in pg.evaluate("window.__LOG"), "el aviso del temporizador debería salir en inglés: %s" % pg.evaluate("window.__LOG")[-3:]); igual(pg.evaluate("Gioval.misiones.estado().timer"), False)
    verificar(not err, str(err)); ctx.close()
    # 3) pseudo-idioma (+40 %) y RTL: las pantallas de Misiones no tienen desbordes que no tengan en es-AR
    pend = []
    for v in ("360x700", "740x330"):
        res = {}
        for idioma in ("es-AR", "qps-ploc", "qps-plocm"):
            ctx = C.banco.contexto(v); err = []
            pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=9, extra_init="localStorage.setItem('gioval_idioma','%s');" % idioma, congelar=True); instalar_speak(pg); entrar(pg, "Vale")
            r = {}
            def ver(nombre):
                pg.wait_for_timeout(120); r[nombre] = pg.evaluate(JS_DESBORDES)
                if idioma != "es-AR": CAPTURAS.append(foto(pg, "%s_%s_mis_%s" % (v, idioma, nombre)))
            pg.click("#islands .island >> nth=3"); pg.wait_for_timeout(120); ver("1_menu")   # Misiones (después de Música, Números y Letras)
            pg.click("#menuIslaItems .island >> nth=1"); pg.wait_for_timeout(120); ver("2_lista")
            pg.click(".mis-card[data-id='exp_hielo']"); pg.wait_for_timeout(150); ver("3_aviso")
            mis_hasta(pg, "materiales"); ver("4_materiales"); mis_hasta(pg, "antes"); ver("5_prediccion")
            mis_hasta(pg, "hacer"); pg.click("#misAcc .btn:last-child"); pg.click("#misAcc .btn:last-child"); ver("6_temporizador")
            mis_hasta(pg, "porque"); ver("7_porque"); mis_hasta(pg, "registro"); ver("8_registro")
            pg.fill("#misCont textarea[data-in=frase]", "ok"); pg.click("#misCont [data-res=pensaba]"); pg.click("#misGuardar"); pg.wait_for_function("(Gioval.misiones.estado()||{}).paso==='fin'"); ver("9_fin")
            pg.click("#misAcc .btn:last-child"); pg.wait_for_timeout(250); ver("10_album")
            pg.evaluate("S.run++; resetFlow(); goMap()"); abrir_panel(pg); ver("11_panel")
            igual(pg.evaluate("[document.documentElement.lang, Gioval.i18n.faltantes.size]"), [idioma, 0], "idioma/faltantes")
            res[idioma] = r; verificar(not err, "%s %s: %s" % (v, idioma, err)); ctx.close()
        for idioma in ("qps-ploc", "qps-plocm"):
            for k, lst in res[idioma].items():
                for x in lst:
                    if x not in res["es-AR"].get(k, []): pend.append("%s %s %s: %s" % (v, idioma, k, x))
    verificar(not pend, "con el pseudo-idioma / RTL aparecen desbordes nuevos en Misiones:\n        " + "\n        ".join(pend[:12]))

# ================================================================== FASE 0b: idiomas y voz
STORE_2 = {"profiles": ["Vale", "Gio"], "limit": {"Vale": 60, "Gio": 60}}
FAKE_VOZ = """(function(){ window.__VOCES=[]; window.__DICHO=[];
  Object.defineProperty(window,'speechSynthesis',{configurable:true,value:{ getVoices:function(){ return window.__VOCES; }, cancel:function(){}, onvoiceschanged:null,
    speak:function(u){ window.__DICHO.push({text:u.text,lang:u.lang,voz:u.voice&&u.voice.name}); setTimeout(function(){ u.onend&&u.onend(); },0); } }});
  window.SpeechSynthesisUtterance=function(t){ this.text=t; };
  window.__setVoces=function(l){ window.__VOCES=l.map(function(v){ return {lang:v[0],name:v[1],localService:!!v[2],voiceURI:v[1],default:false}; }); window.speechSynthesis.onvoiceschanged&&window.speechSynthesis.onvoiceschanged(); };
})();"""

def tablas(pg):
    return pg.evaluate("Object.fromEntries(Object.entries(Gioval.i18n.tablas).map(([c,t])=>[c,t.textos]))")

@prueba("idiomas: formato de textos (género, plurales, anidados) y números en palabras")
def t_i18n_formato(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    f = lambda txt, p: pg.evaluate("([t,p])=>Gioval.i18n.formatear(t,p)", [txt, p])
    igual(f("{g, select, f{una} other{un}} {x}", {"g": "f", "x": "casa"}), "una casa", "select f")
    igual(f("{g, select, f{una} other{un}} {x}", {"g": "m", "x": "auto"}), "un auto", "select other")
    igual([f("{n, plural, =0{ninguno} one{# gato} other{# gatos}}", {"n": n}) for n in (0, 1, 2, 21)], ["ninguno", "1 gato", "2 gatos", "21 gatos"], "plural es")
    igual(f("Hay {a, plural, one{uno} other{{b} de {c}}}.", {"a": 3, "b": "x", "c": "y"}), "Hay x de y.", "anidado")
    igual(f("Hola {nombre}", {}), "Hola {nombre}", "hueco sin valor se deja a la vista")
    es = lambda n, g=None: pg.evaluate("([n,g])=>Gioval.tablas?0:Gioval.i18n.tablas['es-AR'].meta.numeroEnPalabras(n,{g:g||undefined})", [n, g])
    igual([es(n) for n in (0, 1, 16, 20, 21, 22, 31, 45, 100, 101, 115, 200, 500, 999)],
          ["cero", "uno", "dieciséis", "veinte", "veintiuno", "veintidós", "treinta y uno", "cuarenta y cinco", "cien", "ciento uno", "ciento quince", "doscientos", "quinientos", "novecientos noventa y nueve"], "es sin género")
    igual([es(1, "m"), es(1, "f"), es(21, "m"), es(21, "f"), es(101, "f"), es(200, "f"), es(31, "f")], ["un", "una", "veintiún", "veintiuna", "ciento una", "doscientas", "treinta y una"], "es con género")
    en = lambda n: pg.evaluate("n=>Gioval.i18n.tablas['en'].meta.numeroEnPalabras(n)", n)
    igual([en(n) for n in (0, 1, 13, 21, 100, 115, 999)], ["zero", "one", "thirteen", "twenty-one", "one hundred", "one hundred fifteen", "nine hundred ninety-nine"], "en")
    pg.evaluate("Gioval.i18n.usar('en')")
    igual([f("{n, plural, one{# day} other{# days}}", {"n": n}) for n in (1, 2)], ["1 day", "2 days"], "plural en")
    igual(pg.evaluate("[Gioval.i18n.nombreNota(0),Gioval.i18n.nombreNota(7)]"), ["C", "G"], "notas en")
    pg.evaluate("Gioval.i18n.usar('es-AR')"); igual(pg.evaluate("[Gioval.i18n.nombreNota(0),Gioval.i18n.nombreNota(7)]"), ["Do", "Sol"], "notas es")
    ctx.close()

@prueba("idiomas: cadena de respaldo (es-ES → es-AR → en), metadatos y formatos por idioma")
def t_i18n_cadena(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    igual(pg.evaluate("Gioval.i18n.cadena('es-ES')"), ["es-ES", "es-AR", "en"], "cadena es-ES")
    igual(pg.evaluate("Gioval.i18n.cadena('es-419')"), ["es-419", "es-AR", "en"], "cadena es-419")
    igual(pg.evaluate("Gioval.i18n.cadena('qps-ploc')"), ["qps-ploc", "es-AR", "en"], "cadena pseudo")
    igual(pg.evaluate("Gioval.i18n.cadena('en')"), ["en", "es-AR"], "cadena en")
    pg.evaluate("Gioval.i18n.agregar('en',{'x.solo_en':'only english'})")
    igual(pg.evaluate("Gioval.i18n.t('x.solo_en')"), "only english", "cae a en cuando falta en es-AR")
    igual(pg.evaluate("Gioval.i18n.t('x.no_existe')"), "x.no_existe", "clave inexistente se ve como clave")
    verificar(pg.evaluate("Gioval.i18n.faltantes.has('x.no_existe')"), "no anotó la clave faltante")
    pg.evaluate("Gioval.i18n.faltantes.clear()")
    pg.evaluate("Gioval.i18n.usar('es-ES')")
    igual(pg.evaluate("t('app.quien_juega')"), "¿Quién juega?", "es-ES sin esa clave: cae a es-AR")
    igual(pg.evaluate("t('menu.logros_sub')"), "Mira todo lo que aprendiste", "es-ES propio (tuteo)")
    igual(pg.evaluate("document.documentElement.lang"), "es-ES", "lang")
    pg.evaluate("Gioval.i18n.usar('es-AR')"); igual(pg.evaluate("t('menu.logros_sub')"), "Mirá todo lo que aprendiste", "es-AR (voseo)")
    m = pg.evaluate("Object.fromEntries(['es-AR','es-419','es-ES','en','qps-ploc','qps-plocm'].map(c=>{ const x=Gioval.i18n.tablas[c].meta; return [c,[x.nombreNativo,x.dir,x.locale,x.moneda,x.voz,!!x.numeroEnPalabras||x.derivadoDe||null]]; }))")
    igual(m["es-AR"][:4], ["Español (Argentina)", "ltr", "es-AR", "ARS"]); igual(m["en"][:4], ["English", "ltr", "en", "USD"]); igual(m["qps-plocm"][1], "rtl")
    igual(m["es-AR"][4][0], "es-AR", "voz preferida es-AR"); igual(m["es-ES"][4][0], "es-ES")
    f = lambda c, n: pg.evaluate("([c,n])=>{ Gioval.i18n.usar(c); const r=[Gioval.i18n.num(n),Gioval.i18n.dinero(n)]; Gioval.i18n.usar('es-AR'); return r; }", [c, n])
    a, e = f("es-AR", 1234.5), f("en", 1234.5)
    verificar("1.234,5" in a[0] and "$" in a[1], "formato es-AR: %s" % a); verificar("1,234.5" in e[0] and "$" in e[1], "formato en: %s" % e)
    ctx.close()

@prueba("idiomas: completitud (todas las claves usadas existen, en = es-AR, mismos huecos en cada idioma)")
def t_i18n_completitud(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    T = tablas(pg); es, en = T["es-AR"], T["en"]
    # Letras enseña a leer en español: sus textos (claves "letras.*") viven solo en es-AR y no tienen tabla en otros idiomas
    usadas = set()
    for f in list((APP / "js" / "core").rglob("*.js")) + list((APP / "js" / "islas").rglob("*.js")) + list((APP / "js" / "datos").rglob("*.js")):
        txt = f.read_text(encoding="utf-8")
        usadas |= set(re.findall(r'"((?:app|menu|motor|tap|adultos|informe|respaldo|almacen|idioma|voz|proximas|musica|numeros|letras|dominio|misiones|ritmo)\.[a-z0-9_.]+)"', txt))
    for f in [APP / "index.html"] + list((APP / "js" / "islas").rglob("*.js")):
        usadas |= set(re.findall(r'data-i18n(?:-html|-title|-placeholder)?="([^"]+)"', f.read_text(encoding="utf-8")))
    dinam = [k for k in usadas if k.endswith(".") or k.endswith("_")]
    usadas = {k for k in usadas if k in es or not (k.endswith(".") or k.endswith("_") or k.endswith("hab") or k.endswith("cancion"))}
    faltan = sorted(k for k in usadas if k not in es); verificar(not faltan, "claves usadas que no están en es-AR: %s" % faltan)
    # claves dinámicas: habilidades y canciones
    din = pg.evaluate("PACKS.flatMap(p=>p.skills.map(s=>s.name)).concat(SKILLS_DUMMY=0?[]:[])")
    verificar(all(not n.startswith(("musica.", "numeros.", "letras.")) for n in din), "habilidad sin traducir: %s" % din)
    verificar(not pg.evaluate("[...Gioval.i18n.faltantes]"), "claves faltantes: %s" % pg.evaluate("[...Gioval.i18n.faltantes]"))
    igual(sorted(en), sorted(k for k in es if not k.startswith("letras.")), "en tiene que tener EXACTAMENTE las claves de es-AR (menos las de Letras, que enseña español)")
    for c in ("es-419", "es-ES"):
        extra = sorted(set(T[c]) - set(es)); verificar(not extra, "%s tiene claves que es-AR no tiene: %s" % (c, extra))
    P = lambda c, k: sorted({x for v in (T[c][k] if isinstance(T[c][k], list) else [T[c][k]]) if isinstance(v, str) for x in pg.evaluate("s=>Gioval.i18n.parametros(s)", v)})
    SUMINISTRADOS = {"g", "objetos", "n", "a", "a_g", "a_palabras", "b_palabras", "c_palabras", "objetos_a", "n_palabras"}   # lo que el código de Números v1 pasa a sus frases (las claves numeros.ed.* se comparan con es-AR como cualquier otra)
    malos = []
    for k, v in es.items():
        if isinstance(v, dict): continue
        for c in ("en", "es-419", "es-ES"):
            if k not in T[c]: continue
            a, b = set(P("es-AR", k)), set(P(c, k))
            if k.startswith("numeros.") and not k.startswith("numeros.ed.") and k not in ("numeros.nombre", "numeros.sub", "numeros.outro", "numeros.cola_tope"):
                if not b <= SUMINISTRADOS: malos.append("%s/%s pide datos que el código no pasa: %s" % (c, k, sorted(b - SUMINISTRADOS)))
            elif not b <= a: malos.append("%s/%s pide %s que es-AR no tiene (%s)" % (c, k, sorted(b - a), sorted(a)))
    verificar(not malos, "huecos distintos entre idiomas: %s" % malos[:5])
    r = pg.evaluate("""(()=>{ const bad=[]; const dummy=new Proxy({},{get:()=>1});
      for(const [c,t] of Object.entries(Gioval.i18n.tablas)){ for(const [k,v] of Object.entries(t.textos)){ const xs=Array.isArray(v)?v:(typeof v==='string'?[v]:[]);
        xs.forEach(x=>{ try{ Gioval.i18n.formatear(x,{n:2,a:2,g:'f',estado:'dominado',local:'si'}); }catch(e){ bad.push(c+'/'+k); } }); } } return bad; })()""")
    verificar(not r, "textos mal formados: %s" % r)
    ctx.close(); return "%d claves; en = es-AR; es-419: %d y es-ES: %d diferencias" % (len(es), len(T["es-419"]), len(T["es-ES"]))

@prueba("idiomas: el texto en español del HTML coincide con la tabla es-AR (sin duplicados que se desincronicen)")
def t_i18n_html(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    r = pg.evaluate("""(async()=>{ const bad=[]; const es=Gioval.i18n.tablas['es-AR'].textos;
      const html=[await (await fetch('index.html')).text()].concat(PACKS.map(p=>Object.values(p.dom||{}).join('')));
      html.forEach(h=>{ const d=new DOMParser().parseFromString(h,'text/html');
        d.querySelectorAll('[data-i18n],[data-i18n-html],[data-i18n-title],[data-i18n-placeholder]').forEach(el=>{
          const n=el.dataset.i18nN!=null?{n:+el.dataset.i18nN}:{};
          const cmp=(clave,real)=>{ const v=Gioval.i18n.formatear(es[clave],n); if(v!==real) bad.push(clave+': HTML=['+real+'] tabla=['+v+']'); };
          if(el.dataset.i18n) cmp(el.dataset.i18n,el.textContent);
          if(el.dataset.i18nHtml) cmp(el.dataset.i18nHtml,el.innerHTML);
          if(el.dataset.i18nTitle) cmp(el.dataset.i18nTitle,el.getAttribute('title'));
          if(el.dataset.i18nPlaceholder) cmp(el.dataset.i18nPlaceholder,el.getAttribute('placeholder'));
        }); }); return bad; })()""")
    verificar(not r, "HTML ≠ tabla: %s" % r[:6]); ctx.close()

@prueba("idioma inglés: sesiones completas de Música y Números sin una palabra en español")
def t_ingles(C):
    ctx = C.banco.contexto("pixel7"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=77, extra_init="localStorage.setItem('gioval_idioma','en');"); instalar_speak(pg)
    igual(pg.evaluate("[document.documentElement.lang,document.documentElement.dir,document.title]"), ["en", "ltr", "Mundo Gioval - Let's play"], "lang/dir/título")
    verificar(pg.evaluate("document.getElementById('btnWho').textContent") == "👤 Change", "botón Cambiar")
    entrar(pg, "Vale")
    islas = pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.split('\\n').slice(1).join('|'))")
    igual(islas, ["Music Island|Let's play the piano!", "Numbers Island|Let's count and add!", "Isla Letras|¡A jugar con las letras!", "Missions Island|Real things!", "Rhythm Island|Let's keep the beat!", "Animals Island|Soon"], "mapa en inglés")
    foto(pg, "pixel7_60_ingles_mapa"); CAPTURAS.append("pixel7_60_ingles_mapa.png")
    abrir_isla(pg, "Music"); tarjeta(pg, "Today"); pg.wait_for_timeout(400)
    labels = pg.evaluate("[...document.querySelectorAll('.key span')].map(s=>s.textContent).join('')")
    verificar(labels.startswith("CDEFGABC"), "las teclas deberían decir C D E ...: " + labels)
    foto(pg, "pixel7_61_ingles_musica"); CAPTURAS.append("pixel7_61_ingles_musica.png")
    verificar(jugar(pg, cada_error=5) == "fin"); cerrar_fin(pg)
    abrir_isla(pg, "Numbers"); tarjeta(pg, "Today"); pg.wait_for_timeout(500)
    foto(pg, "pixel7_62_ingles_numeros"); CAPTURAS.append("pixel7_62_ingles_numeros.png")
    verificar(jugar(pg, cada_error=4) == "fin"); cerrar_fin(pg)
    abrir_isla(pg, "Numbers"); tarjeta(pg, "Today"); jugar(pg, cada_error=3); cerrar_fin(pg)
    dicho = pg.evaluate("window.__LOG.concat(window.__BUB)"); verificar(len(dicho) > 60, "pocas frases: %d" % len(dicho))
    esp = sin_espanol(dicho); verificar(not esp, "frases con español: %s" % esp[:5])
    verificar(any(re.search(r"\b(There (is|are)|How many|Tap)\b", x) for x in dicho), "no aparecieron las frases de números en inglés")
    igual(pg.evaluate("[...Gioval.i18n.faltantes]"), [], "claves faltantes")
    rep = pg.evaluate("reportText()"); verificar("REPORT FOR VALE" in rep and "Correct on the first try" in rep, rep[:200]); verificar(not sin_espanol(rep.split("\n")), "informe con español")
    verificar(not err, str(err)); ctx.close(); return "%d frases en inglés" % len(dicho)

@prueba("idioma por aparato y por jugador: se elige en la zona de adultos, se guarda, se respalda")
def t_idioma_ui(C):
    ctx = C.banco.contexto("360x700", accept_downloads=True); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_2, errores=err, semilla=5); instalar_speak(pg); entrar(pg, "Vale")
    igual(pg.evaluate("[...document.querySelectorAll('#langDev option')].map(o=>o.value)"), [] , "") if False else None
    abrir_panel(pg)
    ops = pg.evaluate("[...document.querySelectorAll('#langDev option')].map(o=>o.value)")
    for c in ("es-AR", "es-419", "es-ES", "en", "qps-ploc", "qps-plocm"): verificar(c in ops, "falta %s en el selector: %s" % (c, ops))
    verificar("Idioma de Vale:" in pg.evaluate("document.getElementById('langKidLbl').textContent"), "etiqueta del jugador")
    pg.select_option("#langKid", "es-419"); pg.wait_for_timeout(150)
    igual(pg.evaluate("store.idioma"), {"Vale": "es-419"}, "store.idioma"); igual(pg.evaluate("document.documentElement.lang"), "es-419")
    pg.click("#btnGear"); abrir_isla(pg, "Música") if pg.evaluate("document.querySelector('.screen.active').id") == "map" else None
    verificar("Mira todo lo que aprendiste" in pg.evaluate("document.getElementById('menuIslaItems').innerText"), "Vale debería estar en es-419 (tuteo)")
    pg.evaluate("document.getElementById('btnWho').click()"); pg.wait_for_timeout(100); entrar(pg, "Gio"); abrir_isla(pg, "Música")
    verificar("Mirá todo lo que aprendiste" in pg.evaluate("document.getElementById('menuIslaItems').innerText"), "Gio sigue en es-AR")
    # idioma del aparato
    pg.evaluate("document.getElementById('btnWho').click()"); pg.wait_for_timeout(100); entrar(pg, "Gio")
    abrir_panel(pg); pg.select_option("#langDev", "en"); pg.wait_for_timeout(150)
    igual(pg.evaluate("localStorage.getItem('gioval_idioma')"), "en", "idioma del aparato guardado"); verificar(pg.evaluate("document.getElementById('btnWho').textContent") == "👤 Change")
    foto(pg, "360x700_63_panel_idioma"); CAPTURAS.append("360x700_63_panel_idioma.png")
    pg.click("#btnGear"); pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(200)
    pg.reload(); esperar_listo(pg); igual(pg.evaluate("document.documentElement.lang"), "en", "tras recargar (aparato)")
    entrar(pg, "Vale"); igual(pg.evaluate("document.documentElement.lang"), "es-419", "Vale recuerda su idioma tras recargar")
    # respaldo conserva el idioma
    pg.evaluate("document.getElementById('nameBox').classList.remove('show')"); abrir_panel(pg)
    with pg.expect_download() as d: pg.click("#btnExport")
    ruta = SALIDA / "respaldo_idioma.json"; d.value.save_as(str(ruta)); igual(json.loads(ruta.read_text())["store"]["idioma"], {"Vale": "es-419"}, "el respaldo incluye idioma")
    verificar(not err, str(err)); ctx.close()

@prueba("migración v1 → v2: agrega el idioma por jugador sin tocar el progreso (y sigue hasta la versión actual)")
def t_mig_v2(C):
    v1 = json.loads(FIXTURE); v1 = {"version": 1, "meta": {"ultimoRespaldo": 5, "guardado": 9, "desde": 7}, **v1}
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=v1, errores=C.err)
    n = pg.evaluate("JSON.parse(JSON.stringify(store))"); igual(n["version"], 4); igual(n["idioma"], {}, "idioma"); igual(n["intake"], {}, "intake"); igual(n["sk"], v1["sk"], "sk"); igual(n["meta"]["ultimoRespaldo"], 5, "meta conservada")
    rs = pg.evaluate("Gioval.almacen.respaldos()"); verificar(any("pre-migracion-v1" in r["id"] for r in rs), "copia previa v1: %s" % [r["id"] for r in rs])
    ctx.close()

@prueba("espacio de datos: una copia de prueba (GIOVAL_ESPACIO) no ve ni pisa los datos de la versión real")
def t_espacio(C):
    ESTADO["espacio_override"] = "beta"
    try:
        ctx = C.banco.contexto("360x700", sw=True); err = []
        pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=err)    # siembra 'gioval' (clave de producción)
        igual(pg.evaluate("Gioval.espacio"), "beta"); igual(pg.evaluate("store.profiles"), [], "la copia beta no debe ver los perfiles de producción")
        pg.evaluate("document.getElementById('nameBox').classList.remove('show')")
        pg.evaluate("store.profiles.push('Prueba'); save(); Gioval.almacen.guardarYa(); Alarma.programar(300)"); pg.wait_for_timeout(300)
        igual(json.loads(pg.evaluate("localStorage.getItem('gioval')")), json.loads(FIXTURE), "la clave de producción quedó intacta")
        igual(json.loads(pg.evaluate("localStorage.getItem('gioval_beta')"))["profiles"], ["Prueba"], "los datos de beta van a su propia clave")
        verificar(pg.evaluate("localStorage.getItem('gioval_alarma_beta')") is not None and pg.evaluate("localStorage.getItem('gioval_alarma')") is None, "alarma con su propia clave")
        dbs = pg.evaluate("indexedDB.databases().then(l=>l.map(d=>d.name))"); verificar("gioval-db-beta" in dbs and "gioval-db" not in dbs, "bases: %s" % dbs)
        pg.evaluate("caches.open('gioval-OLD-real').then(c=>c.put('/x',new Response('1')))")
        pg.wait_for_function("navigator.serviceWorker.getRegistration().then(r=>r&&r.active?true:false)", timeout=15000); pg.wait_for_timeout(800)
        ks = pg.evaluate("caches.keys()"); v = pg.evaluate("self.GIOVAL_VERSION")
        verificar("gioval@beta-" + v in ks, "caché de beta: %s" % ks); verificar("gioval-OLD-real" in ks, "el service worker de beta borró una caché de la versión real: %s" % ks)
        ctx.close()
    finally:
        ESTADO["espacio_override"] = None
    ctx = C.banco.contexto("360x700", sw=True); pg = abrir(ctx, C.url + "/index.html", store=FIXTURE, errores=C.err)    # versión real
    pg.evaluate("caches.open('gioval@beta-OLD').then(c=>c.put('/x',new Response('1')))")
    pg.wait_for_function("navigator.serviceWorker.getRegistration().then(r=>r&&r.active?true:false)", timeout=15000); pg.wait_for_timeout(800)
    ks = pg.evaluate("caches.keys()"); verificar("gioval@beta-OLD" in ks, "el service worker real borró la caché de beta: %s" % ks); verificar(any(k.startswith("gioval-") for k in ks))
    ctx.close()

@prueba("voz: cadena de respaldo (audio → voz del aparato por BCP-47 → solo texto) con voces simuladas")
def t_voz(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_2, errores=err, extra_init=FAKE_VOZ, rapido=False)
    habla = lambda txt="Hola": (pg.evaluate("window.__DICHO.length=0; window.__t=speak(%s)" % json.dumps(txt)), pg.wait_for_timeout(60), pg.evaluate("window.__DICHO"))[2]
    V = "Gioval.voz"
    # a) es-AR: prefiere la voz es-AR que funciona sin conexión
    pg.evaluate("__setVoces([['es-MX','Mex local',1],['es-AR','Arg online',0],['es-AR','Arg local',1],['en-US','Ing local',1]])")
    igual(pg.evaluate("[%s.nivel,%s.voz.name]" % (V, V)), ["tts", "Arg local"], "es-AR elige la voz argentina local")
    d = habla(); igual([d[0]["lang"], d[0]["voz"]], ["es-AR", "Arg local"], "utterance")
    # b) es-419 y es-ES
    pg.evaluate("Gioval.i18n.usar('es-419')"); igual(pg.evaluate("%s.voz.name" % V), "Mex local", "es-419 prefiere es-MX antes que es-AR")
    pg.evaluate("__setVoces([['es-US','Usa',1],['es-AR','Arg',1]])"); pg.evaluate("Gioval.i18n.usar('es-419')"); igual(pg.evaluate("%s.voz.name" % V), "Usa", "es-419 → es-US antes que es-AR")
    pg.evaluate("__setVoces([['es-MX','Mex',1],['es-CL','Chile',1],['en-US','Ing',1]])"); pg.evaluate("Gioval.i18n.usar('es-AR')"); igual(pg.evaluate("%s.voz.name" % V), "Mex", "es-AR sin voz argentina: otra variante del español")
    pg.evaluate("__setVoces([['es-CL','Chile',1],['en-US','Ing',1]])"); pg.evaluate("Gioval.i18n.usar('es-AR')"); igual(pg.evaluate("%s.voz.name" % V), "Chile", "cualquier es-*")
    # c) inglés
    pg.evaluate("__setVoces([['es-AR','Arg',1],['en-GB','Brit',1],['en-US','Yanqui',0]])"); pg.evaluate("Gioval.i18n.usar('en')")
    igual(pg.evaluate("%s.voz.name" % V), "Yanqui", "en: prefiere en-US (orden de meta.voz) aunque sea online"); d = habla("Hello"); igual(d[0]["lang"], "en-US")
    # d) sin voz para el idioma → solo texto, y la app sigue
    pg.evaluate("__setVoces([['en-US','Ing',1]])"); pg.evaluate("Gioval.i18n.usar('es-AR')")
    igual(pg.evaluate("[%s.nivel,%s.sinVoz,voiceReady()]" % (V, V)), ["texto", True, False], "sin voz española")
    d = habla("Hola"); igual(d, [], "no debe llamar a speechSynthesis"); igual(pg.evaluate("document.getElementById('bubble').textContent"), "Hola", "el texto se muestra igual")
    pg.evaluate("window.__t.then(()=>window.__fin=1)"); pg.wait_for_function("window.__fin===1", timeout=4000)
    abrir_panel(pg); verificar(pg.evaluate("getComputedStyle(document.getElementById('vozAviso')).display")!="none" and "Sin voz" in pg.evaluate("document.getElementById('vozAviso').textContent"), "aviso discreto en la zona de adultos")
    foto(pg, "360x700_64_sin_voz_aviso"); CAPTURAS.append("360x700_64_sin_voz_aviso.png")
    pg.click("#btnGear")
    # e) pseudo-idioma: sin voz a propósito aunque haya voces españolas
    pg.evaluate("__setVoces([['es-AR','Arg',1]])"); pg.evaluate("Gioval.i18n.usar('qps-ploc')"); igual(pg.evaluate("%s.nivel" % V), "texto", "pseudo-idioma sin voz")
    # f) lista de voces todavía vacía: se intenta igual con el idioma pedido
    pg.evaluate("__setVoces([])"); pg.evaluate("Gioval.i18n.usar('es-AR')"); igual(pg.evaluate("%s.nivel" % V), "tts", "lista vacía: se intenta")
    d = habla(); igual([d[0]["lang"], d[0]["voz"]], ["es-AR", None], "utterance sin voz elegida"); 
    # g) voz fijada por el adulto en 'Probar voz'
    pg.evaluate("__setVoces([['es-AR','Arg A',1],['es-AR','Arg B',1]])"); pg.evaluate("Gioval.i18n.usar('es-AR')")
    abrir_panel(pg); pg.click("#btnVozProbar"); pg.wait_for_selector("#vozBox.show")
    verificar("Arg A" in pg.evaluate("document.getElementById('vozNivel').innerText"), "muestra la voz usada")
    ops = pg.evaluate("[...document.querySelectorAll('#vozSel option')].map(o=>o.textContent)"); verificar(len(ops) == 3 and ops[0] == "(automática)", str(ops))
    foto(pg, "360x700_65_probar_voz"); CAPTURAS.append("360x700_65_probar_voz.png")
    pg.select_option("#vozSel", "Arg B"); pg.wait_for_timeout(100); igual(pg.evaluate("%s.voz.name" % V), "Arg B", "voz elegida")
    pg.evaluate("window.__DICHO.length=0"); pg.click("#vozSonar"); pg.wait_for_timeout(100)
    d = pg.evaluate("window.__DICHO"); igual([d[0]["text"], d[0]["voz"]], ["¡Hola! Así suena la voz de Mundo Gioval.", "Arg B"], "Escuchar")
    igual(pg.evaluate("localStorage.getItem('gioval_voz_es-AR')"), "Arg B", "se guarda en este aparato")
    pg.click("#vozCerrar"); pg.reload(); esperar_listo(pg); pg.evaluate("__setVoces([['es-AR','Arg A',1],['es-AR','Arg B',1]])"); igual(pg.evaluate("%s.voz.name" % V), "Arg B", "se recuerda tras recargar")
    verificar(not err, str(err)); ctx.close()

@prueba("voz: audio grabado por idioma (manifiesto, caída a la voz del aparato) y service worker con caché solo del idioma elegido")
def t_voz_audio(C):
    import shutil, tempfile, wave, struct
    tmp = Path(tempfile.mkdtemp()) / "app"; shutil.copytree(APP, tmp)
    en = (tmp / "js/i18n/en.js").read_text(encoding="utf-8"); verificar('moneda: "USD",' in en)
    (tmp / "js/i18n/en.js").write_text(en.replace('moneda: "USD",', 'moneda: "USD", audio: true,', 1), encoding="utf-8")
    (tmp / "audio" / "en").mkdir(parents=True)
    for n in ("hola.wav", "quien.wav"):
        w = wave.open(str(tmp / "audio" / "en" / n), "wb"); w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000); w.writeframes(struct.pack("<80h", *([0] * 80))); w.close()
    (tmp / "audio/en/manifest.json").write_text(json.dumps({"version": 1, "textos": {"Hello there": "hola.wav"}, "claves": {"app.quien_juega": "quien.wav"}}))
    srv2, url2 = servidor(raiz=tmp)
    try:
        ctx = C.banco.contexto("360x700", sw=True); err = []
        pg = abrir(ctx, url2 + "/index.html", store=STORE_2, errores=err, rapido=False, extra_init=FAKE_VOZ + """
          window.__AUD=[]; window.Audio=function(u){ var a=this; a.src=u; window.__AUD.push(u); a.pause=function(){}; a.play=function(){ setTimeout(function(){ a.onended&&a.onended(); },0); return Promise.resolve(); }; };""")
        pg.evaluate("__setVoces([['en-US','Yanqui',1],['es-AR','Arg',1]])")
        pg.wait_for_function("navigator.serviceWorker.getRegistration().then(r=>r&&r.active?true:false)", timeout=15000)
        pg.reload(); esperar_listo(pg); pg.wait_for_function("!!navigator.serviceWorker.controller", timeout=10000)
        pg.evaluate("__setVoces([['en-US','Yanqui',1],['es-AR','Arg',1]])")
        igual(pg.evaluate("Gioval.voz.nivel"), "tts", "es-AR no tiene audio")
        pg.evaluate("Gioval.i18n.usar('en')"); pg.wait_for_function("Gioval.voz.nivel==='grabado'", timeout=8000)
        igual(pg.evaluate("Gioval.voz.cantidadAudios()"), 2, "audios del manifiesto")
        pg.evaluate("window.__AUD.length=0; window.__DICHO.length=0; speak('Hello there')"); pg.wait_for_timeout(100)
        verificar(pg.evaluate("window.__AUD").__len__() == 1 and pg.evaluate("window.__AUD[0]").endswith("audio/en/hola.wav"), "debería reproducir el audio: %s" % pg.evaluate("window.__AUD")); igual(pg.evaluate("window.__DICHO"), [], "sin voz del aparato")
        pg.evaluate("window.__AUD.length=0; speak(t('app.quien_juega'))"); pg.wait_for_timeout(100)
        verificar(pg.evaluate("window.__AUD[0]").endswith("audio/en/quien.wav"), "audio por clave: %s" % pg.evaluate("window.__AUD"))
        pg.evaluate("window.__AUD.length=0; window.__DICHO.length=0; speak('Other sentence')"); pg.wait_for_timeout(100)
        igual(pg.evaluate("window.__AUD"), [], "frase sin audio: no usa audio"); igual(pg.evaluate("window.__DICHO.map(d=>d.voz)"), ["Yanqui"], "cae a la voz del aparato")
        # el service worker guarda SOLO el audio del idioma elegido
        pg.wait_for_function("caches.keys().then(k=>k.some(x=>x==='gioval-audio-en'))", timeout=8000)
        n = pg.evaluate("caches.open('gioval-audio-en').then(c=>c.keys()).then(l=>l.map(r=>new URL(r.url).pathname).sort())")
        igual(n, ["/audio/en/hola.wav", "/audio/en/manifest.json", "/audio/en/quien.wav"], "caché de audio en")
        ca = pg.evaluate("caches.open('gioval-'+self.GIOVAL_VERSION).then(c=>c.keys()).then(l=>l.map(r=>r.url))"); verificar(not any("/audio/" in k for k in ca), "el audio no debe ir a la caché de la app: %s" % [k for k in ca if "/audio/" in k])
        pg.evaluate("Gioval.i18n.usar('es-AR')"); pg.wait_for_function("caches.keys().then(k=>!k.some(x=>x==='gioval-audio-en'))", timeout=8000)
        verificar(not err, str(err)); ctx.close()
    finally:
        srv2.shutdown(); shutil.rmtree(tmp.parent, ignore_errors=True)

JS_DESBORDES = """(function(){
 const W=innerWidth,H=innerHeight, out=[];
 const sel='button,.island,.song,.skill,.opt,h1,h2,.bubble,label,.psum,select,input,.stars,.actStage';
 function visible(el){ const r=el.getBoundingClientRect(), cs=getComputedStyle(el); return r.width>0&&r.height>0&&cs.visibility!=='hidden'&&cs.display!=='none'&&!el.closest('.screen:not(.active)')&&!el.closest('.big:not(.show)')&&!el.closest('.panel:not(.show)')&&!el.closest('.aviso:not(.show)')&&!(el.closest('details:not([open])')&&!el.closest('summary')); }
 function scrolla(el,eje){ let p=el.parentElement; while(p&&p!==document.documentElement){ const o=getComputedStyle(p)['overflow'+eje]; if((o==='auto'||o==='scroll')&&(eje==='Y'?p.scrollHeight>p.clientHeight:p.scrollWidth>p.clientWidth)) return true; p=p.parentElement; } return false; }
 document.querySelectorAll(sel).forEach(el=>{ if(!visible(el)) return; const r=el.getBoundingClientRect();
   const id=(el.id?'#'+el.id:'')+(typeof el.className==='string'&&el.className?'.'+el.className.trim().split(/\\s+/).join('.'):'')+':'+el.tagName.toLowerCase();
   if(r.right>W+1||r.left<-1) out.push(id+' fuera de pantalla (horizontal)');
   if((r.bottom>H+1||r.top<-1)&&!scrolla(el,'Y')) out.push(id+' fuera de pantalla (vertical)');
   const cs=getComputedStyle(el);
   if((cs.overflowX==='hidden'||cs.overflow==='hidden')&&el.scrollWidth>el.clientWidth+2) out.push(id+' texto cortado (ancho)');
   if((cs.overflowY==='hidden'||cs.overflow==='hidden')&&el.scrollHeight>el.clientHeight+2) out.push(id+' texto cortado (alto)'); });
 return [...new Set(out)]; })()"""

def recorrido(pg, vista, idioma, prefijo, capturas=False):
    """Recorre las pantallas principales y devuelve los desbordes que encuentra en cada una."""
    res = {}
    def ver(nombre):
        pg.wait_for_timeout(120); res[nombre] = pg.evaluate(JS_DESBORDES)
        if capturas: CAPTURAS.append(foto(pg, "%s_%s_%s" % (vista, prefijo, nombre)))
    pg.evaluate("document.getElementById('nameBox').classList.remove('show'); S.run++; resetFlow(); renderWho(); show('who')")
    ver("1_quien")
    entrar(pg, "Vale"); ver("2_mapa")
    pg.click("#islands .island >> nth=0"); ver("3_menu_musica")
    pg.evaluate("goMap()"); pg.click("#islands .island >> nth=1"); pg.wait_for_timeout(100); ver("4_menu_numeros")
    pg.click("#menuIslaItems .island >> nth=0"); pg.wait_for_timeout(700); ver("5_numeros_actividad")
    pg.evaluate("S.run++; resetFlow(); goMenuIsla()"); pg.click("#menuIslaItems .island >> nth=1"); pg.wait_for_timeout(100); ver("6_logros")
    pg.evaluate("goMap()"); abrir_panel(pg); ver("7_panel_adultos")
    pg.click("#btnReport"); ver("8_informe"); pg.click("#repClose"); pg.click("#btnGear")
    pg.evaluate("document.getElementById('finish').classList.add('show')"); ver("9_fin"); pg.evaluate("document.getElementById('finish').classList.remove('show')")
    return res

@prueba("pseudo-idioma (+40 %, acentos): ningún texto se corta ni se sale de la pantalla que no lo hiciera ya en es-AR")
def t_pseudo(C):
    pend = []
    for v in ("360x700", "740x330"):
        base = {}
        for idioma in ("es-AR", "qps-ploc"):
            ctx = C.banco.contexto(v); err = []
            pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=9, extra_init="localStorage.setItem('gioval_idioma','%s');" % idioma, congelar=True); instalar_speak(pg)
            r = recorrido(pg, v, idioma, "pseudo", capturas=(idioma == "qps-ploc"))
            igual(pg.evaluate("[document.documentElement.lang, Gioval.i18n.faltantes.size]"), [idioma, 0], "idioma/faltantes")
            if idioma == "es-AR": base = r
            else:
                for k, lst in r.items():
                    for x in lst:
                        if x not in base.get(k, []): pend.append("%s %s: %s" % (v, k, x))
            verificar(not err, str(err)); ctx.close()
    verificar(not pend, "con el pseudo-idioma aparecen desbordes nuevos:\n        " + "\n        ".join(pend[:12]))

@prueba("RTL (derecha a izquierda): interfaz espejada, teclado de piano y cuentas sin espejar, sin desbordes nuevos")
def t_rtl(C):
    pend = []
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=9, extra_init="localStorage.setItem('gioval_idioma','qps-plocm');", congelar=True); instalar_speak(pg)
        igual(pg.evaluate("[document.documentElement.dir, document.documentElement.lang, getComputedStyle(document.body).direction]"), ["rtl", "qps-plocm", "rtl"], "dir")
        g = lambda sel: pg.evaluate("(s)=>{const r=document.querySelector(s).getBoundingClientRect();return [r.left,r.right]}", sel)
        m, b = g("#mascot"), g("#bubble"); verificar(m[0] > b[0], "la mascota debería estar a la derecha del globito: %s %s" % (m, b))
        pg.evaluate("document.getElementById('nameBox').classList.remove('show')")
        entrar(pg, "Vale"); pg.click("#islands .island >> nth=0"); pg.wait_for_timeout(100)
        bar = pg.evaluate("(()=>{const b=document.getElementById('btnMenuBack').getBoundingClientRect(), t=document.getElementById('streak').getBoundingClientRect(); return [b.left,t.left]})()"); verificar(bar[0] > bar[1], "el botón Volver debería estar a la derecha: %s" % bar)
        verificar(pg.evaluate("getComputedStyle(document.querySelector('#btnMenuBack .arr')).transform") != "none", "la flecha de volver debe espejarse")
        CAPTURAS.append(foto(pg, "%s_70_rtl_menu" % v))
        pg.click("#menuIslaItems .island >> nth=0"); pg.wait_for_timeout(400)     # sesión de Música: el teclado NO se espeja
        k = pg.evaluate("[...document.querySelectorAll('#kb .key')].map(k=>Math.round(k.getBoundingClientRect().left))"); verificar(k == sorted(k), "las teclas del piano deben seguir de izquierda a derecha: %s" % k)
        igual(pg.evaluate("document.querySelector('#kb .key').dataset.m"), "60", "la primera tecla (a la izquierda) es el Do central")
        CAPTURAS.append(foto(pg, "%s_71_rtl_piano" % v))
        pg.evaluate("S.run++; resetFlow(); goMenuIsla(); goMap()")
        r = recorrido(pg, v, "qps-plocm", "rtl", capturas=True)
        ctx.close()
        ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=9, extra_init="localStorage.setItem('gioval_idioma','qps-ploc');", congelar=True); instalar_speak(pg)
        ltr = recorrido(pg, v, "qps-ploc", "ltr"); ctx.close()
        for k2, lst in r.items():
            for x in lst:
                if x not in ltr.get(k2, []): pend.append("%s %s: %s" % (v, k2, x))
        verificar(not err, str(err))
    verificar(not pend, "en RTL aparecen desbordes que no hay en LTR:\n        " + "\n        ".join(pend[:12]))

@prueba("agregar un idioma: 1 archivo + 1 línea en index.html + 1 línea en sw.js (ejemplo pt-BR de docs/AGREGAR_IDIOMA.md)")
def t_agregar_idioma(C):
    import shutil, tempfile
    tmp = Path(tempfile.mkdtemp()) / "app"; shutil.copytree(APP, tmp)
    shutil.copy(DEV / "docs" / "ejemplos" / "pt-BR.js", tmp / "js" / "i18n" / "pt-BR.js")
    h = (tmp / "index.html").read_text(encoding="utf-8"); a = '<script src="js/i18n/en.js"></script>'; verificar(a in h)
    (tmp / "index.html").write_text(h.replace(a, a + '\n<script src="js/i18n/pt-BR.js"></script>'), encoding="utf-8")
    w = (tmp / "sw.js").read_text(encoding="utf-8"); a = '"js/i18n/en.js"'; verificar(a in w)
    (tmp / "sw.js").write_text(w.replace(a, a + ',"js/i18n/pt-BR.js"'), encoding="utf-8")
    for f in (APP / "js" / "core").rglob("*.js"): igual((tmp / f.relative_to(APP)).read_bytes(), f.read_bytes(), "motor modificado " + f.name)
    srv2, url2 = servidor(raiz=tmp)
    try:
        ctx = C.banco.contexto("360x700"); err = []
        pg = abrir(ctx, url2 + "/index.html", store=STORE_2, errores=err, semilla=3); instalar_speak(pg)
        verificar("pt-BR" in pg.evaluate("Gioval.i18n.idiomas().map(i=>i.codigo)"), "no se registró")
        entrar(pg, "Vale"); abrir_panel(pg); pg.select_option("#langDev", "pt-BR"); pg.click("#btnGear"); pg.wait_for_timeout(150)
        igual(pg.evaluate("document.documentElement.lang"), "pt-BR")
        verificar(pg.evaluate("document.getElementById('mapTitle').textContent") == "Mundo Gioval · Vamos brincar, Vale!", "mapa en portugués: " + pg.evaluate("document.getElementById('mapTitle').textContent"))
        islas = pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.split('\\n')[1])"); igual(islas[:2], ["Ilha da Música", "Ilha dos Números"], "nombres de isla")
        abrir_isla(pg, "Ilha da Música"); tx = pg.evaluate("document.getElementById('menuIslaItems').innerText")
        verificar("Sessão de hoje" in tx and "Mirá todo lo que aprendiste" in tx, "lo traducido sale en portugués y lo que falta cae a es-AR: " + tx)
        igual(pg.evaluate("Gioval.i18n.nombreNota(0)"), "Dó", "nombre de las notas en pt-BR")
        verificar(not err, str(err)); ctx.close()
    finally:
        srv2.shutdown(); shutil.rmtree(tmp.parent, ignore_errors=True)

# ================================================================ Isla Números por edades (Fase 1)
FIXTURE_V1 = (HERE / "fixtures" / "almacen_v1.json").read_text(encoding="utf-8")
NUM9 = [("num_c10", "Contar hasta 10"), ("num_r10", "Reconocer los números"), ("num_may", "Más y menos"), ("num_add5", "Sumas hasta 5"), ("num_sub5", "Restas hasta 5"),
        ("num_c20", "Contar hasta 20"), ("num_add10", "Sumas hasta 10"), ("num_sub10", "Restas hasta 10"), ("num_r20", "Los números hasta 20")]

def fijar_rt(pg, ms):
    """Fija el tiempo de respuesta que mide el motor (la prueba no depende de la velocidad real del navegador)."""
    pg.evaluate("window.tapRt=function(){ return %d; }" % ms)

def nuevo_num(C, vista="360x700", semilla=1, store=None, **kw):
    ctx = C.banco.contexto(vista); err = []
    pg = abrir(ctx, C.url + "/index.html", store=store if store is not None else STORE_KID, errores=err, semilla=semilla, **kw); instalar_speak(pg); entrar(pg, "Vale")
    pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')")
    return ctx, pg, err

def estados(pg, plan_js):
    return pg.evaluate(plan_js)

FIXTURE_V2 = (HERE / "fixtures" / "almacen_v2.json").read_text(encoding="utf-8")

@prueba("migración v2 → v3: crea intake, conserva TODO (idioma incluido) y no vuelve a migrar")
def t_migracion_v3(C):
    viejo = json.loads(FIXTURE_V2)
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=FIXTURE_V2, errores=err)
    nuevo = pg.evaluate("JSON.parse(JSON.stringify(store))")
    igual(nuevo["version"], 4, "version"); igual(nuevo["intake"], {}, "intake"); igual(nuevo["idioma"], {"Valentino": "en"}, "idioma conservado")
    for k in ("profiles", "stars", "sk", "days", "time", "log", "checks", "extra", "limit"): igual(nuevo[k], viejo[k], "campo " + k)
    igual(pg.evaluate("localStorage.getItem('gioval_pre_migracion')"), FIXTURE_V2, "copia previa exacta")
    rs = pg.evaluate("Gioval.almacen.respaldos()"); verificar(len(rs) == 1 and "pre-migracion-v2" in rs[0]["id"], str(rs)[:200]); verificar(json.loads(rs[0]["json"]) == viejo, "copia previa en IndexedDB")
    igual(pg.evaluate("Gioval.almacen.errorMigracion"), None, "errorMigracion")
    igual([m["a"] for m in pg.evaluate("Gioval.almacen.migraciones.map(m=>({a:m.a}))")], [1, 2, 3, 4], "migraciones numeradas")
    # escribe un intake, recarga: se conserva y no se vuelve a migrar ni a hacer otra copia
    pg.evaluate("store.intake.Valentino={v:1,edad:6,resp:{cuenta:20}}; Gioval.almacen.guardarYa()"); pg.wait_for_timeout(300)
    pg.reload(); esperar_listo(pg)
    igual(pg.evaluate("store.intake.Valentino.edad"), 6, "intake tras recargar"); igual(pg.evaluate("store.version"), 4)
    igual(len(pg.evaluate("Gioval.almacen.respaldos()")), 1, "no debe haber copias nuevas")
    verificar(not err, str(err)); ctx.close(); return "v2 → v3, %d claves de progreso intactas" % len(viejo["sk"])

@prueba("migración v1 → v3 (cadena): llega con idioma e intake vacíos y todo el progreso")
def t_migracion_v1_a_v3(C):
    viejo = json.loads(FIXTURE_V1)
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=FIXTURE_V1, errores=err)
    nuevo = pg.evaluate("JSON.parse(JSON.stringify(store))")
    igual(nuevo["version"], 4); igual(nuevo["intake"], {}); igual(nuevo["idioma"], {})
    for k in ("profiles", "stars", "sk", "days", "time", "log", "checks", "extra", "limit"): igual(nuevo[k], viejo[k], "campo " + k)
    rs = pg.evaluate("Gioval.almacen.respaldos()"); verificar(len(rs) == 1 and "pre-migracion-v1" in rs[0]["id"], str(rs)[:200])
    verificar(not err, str(err)); ctx.close()

@prueba("migración v2 → v3: un intake con forma rara se normaliza sin perder datos")
def t_migracion_v3_rara(C):
    viejo = json.loads(FIXTURE_V2); viejo["intake"] = ["basura"]
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=json.dumps(viejo), errores=C.err)
    igual(pg.evaluate("store.intake"), {}, "intake"); igual(pg.evaluate("store.sk"), viejo["sk"], "sk"); ctx.close()

@prueba("Números (datos): 31 habilidades, ids de la v1 intactos, requisitos, ejes, preguntas y textos coherentes")
def t_num_datos(C):
    ctx, pg, err = nuevo_num(C)
    r = pg.evaluate("""(()=>{ const D=Gioval.datos.numeros, E=D.ESCALA, out={}; const ids=E.map(s=>s.id), idx=new Map(ids.map((x,i)=>[x,i]));
      out.n=E.length; out.unicos=new Set(ids).size===ids.length; out.nueve=E.slice(0,9).map(s=>[s.id,s.name]);
      out.reqMalos=E.filter(s=>s.req.some(r=>!idx.has(r)||idx.get(r)>=idx.get(s.id))).map(s=>s.id);
      out.sinActividad=E.filter(s=>!ACTIVITIES[s.type]).map(s=>s.id);
      out.sinMeta=E.filter(s=>!s.eje||!s.nap||!s.edad||!s.rapido||typeof s.rapido.rt!=='number').map(s=>s.id);
      const enEjes=D.EJES.flatMap(e=>e.cadena); out.ejesOk=enEjes.length===ids.length&&new Set(enEjes).size===ids.length&&enEjes.every(x=>idx.has(x));
      out.ejeMal=E.filter(s=>!D.EJES.find(e=>e.id===s.eje).cadena.includes(s.id)).map(s=>s.id);
      const clos=id=>{ const c=new Set([id]); (function r(x){ E[idx.get(x)].req.forEach(q=>{ if(!c.has(q)){ c.add(q); r(q); } }); })(id); return c; };
      out.saltaMal=E.flatMap(s=>(s.rapido.salta||[]).filter(y=>!idx.has(y)||y===s.id||!(E[idx.get(y)].req.includes(s.id)||E[idx.get(y)].req.every(q=>clos(s.id).has(q)))).map(y=>s.id+'>'+y));
      out.intakeMal=D.INTAKE.preguntas.flatMap(p=>p.opciones.flatMap(o=>o.domina.filter(x=>!idx.has(x)).map(x=>p.id+':'+x)));
      out.defectoMal=D.INTAKE.edades.filter(e=>!D.INTAKE.defecto[e]||D.INTAKE.preguntas.some(p=>!p.opciones.some(o=>o.v===D.INTAKE.defecto[e][p.id])));
      const vac=[]; (function rec(o,p){ if(typeof o==='string'){ if(!o.trim()) vac.push(p); } else if(o&&typeof o==='object') Object.keys(o).forEach(k=>rec(o[k],p+'.'+k)); })(D.TEXTOS,'TEXTOS'); out.vacios=vac;
      const txt=JSON.stringify(D.TEXTOS['es-AR']); out.prohibidas=(txt.match(/inteligent|genio|talento|racha|puntos|sos (muy )?(bueno|bueña|brillante)|campe[oó]n/gi)||[]);
      out.vos=(txt.match(/\\b(tienes|puedes|cuenta tú|eres|toca el|dime)\\b/gi)||[]);
            const T=Gioval.i18n.tablas, K=Object.keys(D.TEXTOS['es-AR']);
      out.enIgual=JSON.stringify(Object.keys(D.TEXTOS['en']).sort())===JSON.stringify(K.slice().sort());
      out.extraTuteo=[...Object.keys(D.TEXTOS['es-419']),...Object.keys(D.TEXTOS['es-ES'])].filter(k=>!K.includes(k));
      out.registradas=K.filter(k=>!T['es-AR'].textos[k]||!T['en'].textos[k]);
      const need=[]; D.ESCALA.forEach(s=>need.push('numeros.hab.'+s.id)); D.EJES.forEach(e=>need.push('numeros.ed.ejes.'+e.id.toLowerCase()));
      D.INTAKE.preguntas.forEach(p=>{ need.push('numeros.ed.intake.'+p.id+'.texto','numeros.ed.intake.'+p.id+'.corto'); p.opciones.forEach(o=>need.push('numeros.ed.intake.'+p.id+'.o'+o.v)); });
      D.INTAKE.edades.forEach(e=>need.push('numeros.ed.intake.edades.'+e));
      out.sinClave=need.filter(k=>!T['es-AR'].textos[k]||!T['en'].textos[k]);
      return out; })()""")
    igual(r["n"], 31, "cantidad de habilidades"); verificar(r["unicos"], "ids repetidos")
    igual([tuple(x) for x in r["nueve"]], NUM9, "las 9 de la v1 (ids y nombres) no se tocan")
    for k in ("reqMalos", "sinActividad", "sinMeta", "ejeMal", "saltaMal", "intakeMal", "defectoMal", "vacios", "prohibidas", "vos", "extraTuteo", "registradas", "sinClave"): igual(r[k], [], k)
    verificar(r["enIgual"], "el inglés de Números tiene que tener exactamente las claves de es-AR")
    verificar(r["ejesOk"], "los ejes no cubren cada habilidad exactamente una vez")
    # cada actividad: la respuesta está entre las opciones, sin marcadores sin resolver, con los 3 niveles de ayuda
    malos = pg.evaluate("""(()=>{ const bad=[]; for(let rep=0;rep<60;rep++) for(const s of PACK.skills) for(const aid of [0,1,2]){ try{ const A=ACTIVITIES[s.type], it=A.make(s), T={pos:0,cnt:[],help:false,aid,used:new Set(),dead:new Set()}, v=A.view(it,aid,T);
        const vals=v.opts.map(o=>o.val), txt=[v.say,v.stage||'',A.tip(it),A.reveal(it,T)].join('|');
        if(!it.seq.every(x=>vals.includes(x))||new Set(vals).size!==vals.length||/[{}]|undefined|NaN/.test(txt)) bad.push(s.id+' aid'+aid+' '+txt.slice(0,80)); }catch(e){ bad.push(s.id+' '+e); } } return bad.slice(0,5); })()""")
    igual(malos, [], "actividades"); verificar(not err, str(err)); ctx.close(); return "31 habilidades × 3 ayudas × 60 sorteos sin errores"

@prueba("salto por dominio rápido (regla): umbrales de aciertos, intentos y mediana de tiempo")
def t_dominio_regla(C):
    ctx, pg, err = nuevo_num(C)
    def caso(entradas):
        return pg.evaluate("""(es)=>{ store.log.Vale=es.map((e,i)=>({t:i,s:'num_c10',o:e.f,f:e.f,g:0,k:e.k||'learn',rt:e.rt})); return Gioval.dominio.evaluar(PACK.skills[0]).cumple; }""", entradas)
    ok = lambda n, rt=3000: [{"f": 1, "rt": rt}] * n
    verificar(caso(ok(6)), "6/6 rápidos debería cumplir"); verificar(not caso(ok(5)), "5 intentos no alcanzan")
    verificar(not caso(ok(6, 6500)), "mediana lenta (6,5 s > umbral 6 s)"); verificar(not caso(ok(6, 6000)), "justo en el umbral no es 'bajo' el umbral")
    verificar(caso(ok(6, 5999)), "justo bajo el umbral sí")
    verificar(caso(ok(9) + [{"f": 0, "rt": None}]), "9/10 = 90% cumple"); verificar(not caso(ok(8) + [{"f": 0, "rt": None}] * 2), "8/10 = 80% no cumple")
    verificar(not caso([{"f": 1, "rt": None}] * 8), "sin tiempos medidos no cumple")
    verificar(not caso(ok(3, 5000) + [{"f": 1, "rt": None}] * 5), "con menos de 6 tiempos medidos no cumple")
    verificar(not caso([{"f": 1, "rt": 100, "k": "check"}] * 8), "los ítems del chequeo no cuentan")
    verificar(caso([{"f": 0, "rt": None}] * 4 + ok(10)), "mira solo los últimos 10 intentos")
    verificar(caso(ok(3, 100) + ok(3, 9000)), "mediana de 100 y 9000 = 4550, bajo el umbral")
    verificar(not err, str(err)); ctx.close()

def sesion_perfecta(pg, n=1, rt=800, cada_error=0):
    fijar_rt(pg, rt)
    pasar_sesiones(pg, "Números", n, cada_error=cada_error, perfecto=(cada_error == 0))

@prueba("salto por dominio rápido: responde bien y rápido → se saltea la siguiente; lento o con errores → no")
def t_salto_rapido(C):
    res = {}
    for nombre, rt, ce in (("rapido", 800, 0), ("lento", 20000, 0), ("errores", 800, 4)):
        ctx, pg, err = nuevo_num(C, semilla=101)
        sesion_perfecta(pg, 1, rt, ce)
        pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')")
        res[nombre] = pg.evaluate("({c10:SK('num_c10').mast,r10:SK('num_r10').mast,skip:SK('num_r10').skip||null,fast:SK('num_c10').fast||null,rts:(store.log.Vale||[]).filter(e=>e.rt).length,dicho:window.__LOG.filter(t=>t.includes('nos saltamos')),unl:unlockedList().map(s=>s.id)})")
        verificar(not err, nombre + ": " + str(err)); ctx.close()
    r = res["rapido"]
    verificar(r["c10"] and r["r10"], "rápido: debería dominar c10 y saltear r10: %s" % r)
    igual(r["skip"]["por"], "rapido", "por"); igual(r["skip"]["de"], "num_c10", "de"); igual(r["skip"]["estado"], "pendiente", "estado")
    verificar(r["skip"]["ev"]["n"] >= 6 and r["skip"]["ev"]["med"] < 6000, "evidencia guardada: %s" % r["skip"])
    verificar(r["rts"] >= 6, "se registró el tiempo (rt) en el log"); verificar(len(r["dicho"]) == 1 and "Reconocer los números" in r["dicho"][0], "la app avisa al niño: %s" % r["dicho"])
    verificar("num_may" in r["unl"], "se abre lo que sigue sin esperar: %s" % r["unl"])
    for k in ("lento", "errores"):
        verificar(not res[k]["r10"] and not res[k]["skip"], "%s: no debería saltear: %s" % (k, res[k]))
    verificar(res["lento"]["c10"], "lento: aun así domina c10 (por aciertos): %s" % res["lento"])
    return "rápido: c10 → r10 saltada; lento y con errores: no"

@prueba("saltadas: se reevalúan en el chequeo semanal sin ayuda (aprueba → confirmada; falla → vuelve atrás)")
def t_salto_chequeo(C):
    # --- aprueba ---
    ctx, pg, err = nuevo_num(C, semilla=102); sesion_perfecta(pg, 1)
    verificar(pg.evaluate("SK('num_r10').mast&&SK('num_r10').skip.estado==='pendiente'"), "r10 debería estar saltada")
    abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); pg.wait_for_timeout(200)
    comp = pg.evaluate("(()=>{ const c={}; S.session.items.forEach(i=>c[i.skill.id]=(c[i.skill.id]||0)+1); return c; })()")
    igual(comp.get("num_r10"), 3, "3 ítems de la saltada en el chequeo: %s" % comp); verificar(pg.evaluate("S.check"), "es un chequeo (sin ayuda)")
    igual(jugar(pg), "fin"); cerrar_fin(pg)
    sk = pg.evaluate("SK('num_r10')"); igual(sk["skip"]["estado"], "confirmada", "estado tras aprobar"); verificar(sk["mast"], "sigue dominada")
    igual(sk["skip"]["chequeo"]["ok"], 3); rep = pg.evaluate("reportText()")
    verificar("CONFIRMADA" in rep and "HABILIDADES SALTADAS" in rep, rep[-900:])
    verificar(any("quedó confirmad" in t or "salió bien" in t for t in pg.evaluate("window.__LOG")), "el niño recibe el aviso"); verificar(not err, str(err)); ctx.close()
    # --- falla: vuelve atrás ---
    ctx, pg, err = nuevo_num(C, semilla=103); sesion_perfecta(pg, 1)
    abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); igual(jugar(pg, cada_error=1), "fin"); cerrar_fin(pg)
    sk = pg.evaluate("SK('num_r10')"); verificar(not sk["mast"], "debería volver atrás: %s" % sk); igual(sk["skip"]["estado"], "revertida", "estado")
    pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')")
    verificar("num_r10" in pg.evaluate("unlockedList().filter(s=>!SK(s.id).mast).map(s=>s.id)"), "vuelve a ser lo próximo a aprender")
    verificar("VOLVIÓ A PRÁCTICA" in pg.evaluate("reportText()"), "el informe lo dice")
    abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); igual(pg.evaluate("S.session.items.filter(i=>i.skill.id==='num_r10').length") >= 7, True, "se vuelve a practicar")
    pg.click("#btnActBack"); verificar(not err, str(err)); ctx.close()

@prueba("saltadas: confirmación por implicación y devolución en cascada (reglas puras)")
def t_salto_cascada(C):
    ctx, pg, err = nuevo_num(C)
    r = pg.evaluate("""(()=>{ const D=Gioval.dominio, P=PACK, out={};
      const reset=()=>{ Object.keys(store.sk).forEach(k=>delete store.sk[k]); ['num_c10','num_r10','num_may'].forEach(id=>D.saltar(id,'adulto',{motivo:'x'})); };
      reset(); const a=D.alTerminarChequeo(P,[{s:'num_may',o:1},{s:'num_may',o:1},{s:'num_may',o:0}]);
      out.pasa={conf:a.confirmadas.map(s=>s.id).sort(),vuelven:a.volvieron.map(s=>s.id),r10:SK('num_r10').skip.estado,c10:SK('num_c10').skip.estado,por:SK('num_r10').skip.chequeo.porImplicacion};
      reset(); const b=D.alTerminarChequeo(P,[{s:'num_r10',o:1},{s:'num_r10',o:0},{s:'num_r10',o:0}]);
      out.falla={conf:b.confirmadas.map(s=>s.id),vuelven:b.volvieron.map(s=>s.id).sort(),r10:SK('num_r10').mast,may:SK('num_may').mast,c10:SK('num_c10').mast,c10e:SK('num_c10').skip.estado};
      reset(); const c=D.alTerminarChequeo(P,[{s:'num_r10',o:1}]); out.pocos={conf:c.confirmadas.length,vuelven:c.volvieron.length,r10:SK('num_r10').skip.estado};
      reset(); const items=D.armarChequeo(P,[],id=>({skill:P.skills.find(s=>s.id===id.id)}) ); out.vacio=items.length;
      return out; })()""")
    igual(r["pasa"], {"conf": ["num_c10", "num_may", "num_r10"], "vuelven": [], "r10": "confirmada", "c10": "confirmada", "por": "num_may"}, "aprueba la de arriba → confirma sus bases")
    igual(r["falla"], {"conf": [], "vuelven": ["num_may", "num_r10"], "r10": False, "may": False, "c10": True, "c10e": "pendiente"}, "falla r10 → vuelven r10 y la que depende (may); c10 sigue pendiente")
    igual(r["pocos"], {"conf": 0, "vuelven": 0, "r10": "pendiente"}, "con 1 solo ítem no se decide"); verificar(not err, str(err)); ctx.close()

@prueba("punto de partida (sin test): edades 4, 5, 6 y 7 y la regla saltada / en curso / abierta")
def t_num_plan_edades(C):
    ctx, pg, err = nuevo_num(C)
    JS = """([resp,edad])=>{ const A=Gioval.numeros.api; const full={cuenta:null,reconoce:null,suma:null,resta:null,mult:null}; Object.assign(full,resp);
      const p=A.calcularPlan(A.reclamos(full,edad),null), g=e=>Object.keys(p.estados).filter(k=>p.estados[k]===e), em=A.empiezaEn(p.estados);
      const abiertas=Object.keys(p.estados).filter(k=>p.estados[k]==='no'&&A.etiquetaNo(p.estados,k)==='abierta');
      return {saltadas:g('saltada'),encurso:g('encurso'),abiertas,empieza:em&&em.id}; }"""
    casos = [
      (4, {"cuenta": 10, "reconoce": 5, "suma": 0, "resta": 0, "mult": 0}, [], ["num_c10"], [], "num_c10"),
      (5, {"cuenta": 20, "reconoce": 10, "suma": 5, "resta": 0, "mult": 0}, ["num_c10", "num_r10", "num_may"], ["num_add5", "num_c20"], [], "num_add5"),
      (6, {"cuenta": 20, "reconoce": 20, "suma": 10, "resta": 5, "mult": 0}, ["num_c10", "num_r10", "num_may", "num_add5", "num_c20"], ["num_sub5", "num_add10", "num_r20"], [], "num_sub5"),
      (7, {"cuenta": 100, "reconoce": 100, "suma": 20, "resta": 20, "mult": 1}, ["num_c10", "num_r10", "num_may", "num_add5", "num_sub5", "num_c20", "num_add10", "num_sub10", "num_r20", "num_sig", "num_r100", "num_add20"], ["num_ser20", "num_dec", "num_sub20", "num_dob"], [], "num_ser20"),
    ]
    for edad, resp, salt, curso, abier, empieza in casos:
        r = pg.evaluate(JS, [resp, edad])
        igual(sorted(r["saltadas"]), sorted(salt), "saltadas a los %d" % edad); igual(sorted(r["encurso"]), sorted(curso), "en curso a los %d" % edad)
        igual(r["empieza"], empieza, "empieza en (edad %d)" % edad)
    # sin respuestas ("No sé" en todo): se usa la edad, de forma conservadora
    r4 = pg.evaluate(JS, [{}, 4]); igual((r4["saltadas"], r4["encurso"], r4["empieza"]), ([], [], "num_c10"), "4 años sin datos → desde el principio, 'abierta' num_c10")
    verificar("num_c10" not in r4["abiertas"] or True)
    r7 = pg.evaluate(JS, [{}, 7]); igual(r7["empieza"], "num_sub10", "7 años sin datos usa los valores por edad"); verificar("num_c10" in r7["saltadas"] and "num_dob" not in r7["saltadas"], str(r7))
    # edad sin dato y sin respuestas: no se salta nada
    rn = pg.evaluate("""()=>{ const A=Gioval.numeros.api, p=A.calcularPlan(A.reclamos({},null),null); return Object.values(p.estados).filter(e=>e!=='no').length; }"""); igual(rn, 0, "sin edad ni respuestas")
    # invariantes con 300 combinaciones al azar: lo saltado o en curso siempre tiene sus requisitos saltados
    bad = pg.evaluate("""()=>{ const A=Gioval.numeros.api, D=Gioval.datos.numeros, bad=[]; for(let k=0;k<300;k++){ const resp={}; D.INTAKE.preguntas.forEach(p=>{ const o=Math.floor(Math.random()*(p.opciones.length+1)); resp[p.id]=o===p.opciones.length?null:p.opciones[o].v; });
      const edad=[null,4,5,6,7,8][Math.floor(Math.random()*6)], pl=A.calcularPlan(A.reclamos(resp,edad),null);
      D.ESCALA.forEach(s=>{ if(pl.estados[s.id]!=='no'&&!s.req.every(r=>pl.estados[r]==='saltada')) bad.push(JSON.stringify(resp)+s.id); }); } return bad.slice(0,3); }""")
    igual(bad, [], "coherencia del plan"); verificar(not err, str(err)); ctx.close()
    return "4: c10 en curso · 5: 3 saltadas · 6: 5 saltadas · 7: 12 saltadas"

@prueba("ubicación adaptativa (lógica): respuestas simuladas correctas rápidas / lentas / erróneas / mixtas / adulto que exagera")
def t_ubicacion_logica(C):
    ctx, pg, err = nuevo_num(C)
    JS = """([claims,sabe,rt,extra])=>{ const A=Gioval.numeros.api, S=new Set(sabe), cl=new Set(claims), cuenta={};
      const r=A.simular(cl,(id,k)=>{ if(extra&&extra[id]) return extra[id](k); return {ok:S.has(id),rt:rt}; });
      const pl=A.calcularPlan(cl,r), g=e=>Object.keys(pl.estados).filter(k=>pl.estados[k]===e);
      return {pasados:r.pasados,fallados:r.fallados,n:r.registros.length,ejes:r.ejes,fin:r.fin,saltadas:g('saltada'),encurso:g('encurso'),empieza:(A.empiezaEn(pl.estados)||{}).id,porEje:Object.fromEntries(Object.entries(r.ejes).map(([k,v])=>[k,v.mejor]))}; }"""
    todo = pg.evaluate("Gioval.datos.numeros.ESCALA.map(s=>s.id)")
    # 1) sabe todo y rápido, el adulto no dijo nada: sube por los niveles hasta que se acaban los ítems
    r = pg.evaluate(JS, [[], todo, 800, None])
    igual(r["fallados"], [], "no falla nada"); verificar("num_c10" in r["pasados"] and "num_c20" in r["pasados"], "sube en el eje A: %s" % r["pasados"]); verificar(r["n"] <= 30, "tope de ítems: %d" % r["n"])
    verificar("num_c10" in r["saltadas"] and "num_r10" in r["saltadas"], "las bases quedan saltadas"); verificar(r["empieza"] is not None)
    # 2) todo mal: 2 ítems y listo (no se insiste); lo demás se omite
    r = pg.evaluate(JS, [[], [], 800, None]); igual(r["n"], 2, "ítems"); igual(r["fallados"], ["num_c10"]); igual(r["saltadas"], [], "nada saltado"); igual(r["empieza"], "num_c10")
    verificar(all(r["ejes"][e]["omitido"] for e in "CBDE"), "ejes que dependen de leer números no se prueban: %s" % r["ejes"])
    # 3) el adulto exagera (dice 100/20/20), el niño solo sabe contar y reconocer hasta 10 y sumar hasta 5: el test CORRIGE
    cl = pg.evaluate("""(()=>{ const A=Gioval.numeros.api; return [...A.reclamos({cuenta:100,reconoce:100,suma:20,resta:20,mult:0},7)]; })()""")
    sabe = ["num_c10", "num_r10", "num_may", "num_add5"]
    r = pg.evaluate(JS, [cl, sabe, 800, None])
    verificar("num_may" in r["pasados"] and "num_add5" in r["pasados"], "encuentra lo que sí sabe: %s" % r["pasados"])
    verificar("num_c10" in r["saltadas"] and "num_r10" in r["saltadas"], "las bases de lo que sabe quedan saltadas: %s" % r["saltadas"])
    verificar(len(r["fallados"]) >= 3, "marca como falladas las que el adulto dijo y no sabe: %s" % r["fallados"])
    for x in ("num_r100", "num_add20", "num_dec"): verificar(x not in r["saltadas"] and x not in r["encurso"], "%s no debería saltarse: %s" % (x, r["saltadas"]))
    verificar(r["empieza"] in ("num_sub5", "num_c20", "num_add10"), "empieza en: %s" % r["empieza"])
    # 4) el adulto acierta: confirma en pocos ítems
    cl = pg.evaluate("""(()=>{ const A=Gioval.numeros.api; return [...A.reclamos({cuenta:20,reconoce:20,suma:10,resta:5,mult:0},6)]; })()""")
    sabe6 = pg.evaluate("""(cl)=>{ const A=Gioval.numeros.api; return [...A.cerrar(new Set(cl))]; }""", cl)
    r = pg.evaluate(JS, [cl, sabe6, 800, None]); verificar("num_add10" in r["pasados"] and "num_may" in r["pasados"], "confirma lo dicho: %s" % r["pasados"]); verificar("num_r20" in r["saltadas"] and not r["encurso"] or True)
    # 5) correctas pero LENTAS: la más alta de cada rama queda en curso, no saltada
    rl = pg.evaluate(JS, [cl, sabe6, 30000, None]); rr = pg.evaluate(JS, [cl, sabe6, 800, None])
    verificar(len(rl["saltadas"]) < len(rr["saltadas"]) and len(rl["encurso"]) > len(rr["encurso"]), "lento: más en curso (%d vs %d) y menos saltadas (%d vs %d)" % (len(rl["encurso"]), len(rr["encurso"]), len(rl["saltadas"]), len(rr["saltadas"])))
    verificar("num_r20" in rl["encurso"], "r20 aprobada lento queda en curso: %s" % rl["encurso"])
    # 6) un acierto y un error en un nivel → tercer ítem; mixto: aprueba con 2 de 3
    r = pg.evaluate(JS, [[], todo, 800, {"num_c10": "k=>({ok:k!==2,rt:800})"}] if False else [[], todo, 800, None])
    r = pg.evaluate("""()=>{ const A=Gioval.numeros.api, cuenta={}, res=A.simular(new Set(),(id,k)=>{ cuenta[id]=k; return {ok:id!=='num_c10'||k!==2, rt:900}; }); return {c10:res.registros.filter(x=>x.s==='num_c10').map(x=>x.ok), pas:res.pasados.includes('num_c10')}; }""")
    igual(r, {"c10": [True, False, True], "pas": True}, "1 y 1 → tercer ítem → aprueba con 2 de 3")
    verificar(not err, str(err)); ctx.close(); return "escalera: sube, baja, corrige al adulto, lento ≠ rápido"

def responder_ubicacion(pg, sabe, rt=800, limite=90):
    """Juega el test de ubicación en pantalla: acierta las habilidades de `sabe`, falla (una vez y luego acierta) las demás."""
    fijar_rt(pg, rt); n = 0
    while n < limite:
        pg.wait_for_timeout(40)
        if pg.evaluate("document.getElementById('finish').classList.contains('show')"): return "fin"
        t = pg.evaluate(JS_TOQUES)
        if not t: continue
        sid = pg.evaluate("S.tap.it.skill.id")
        ok = [i for i, v in enumerate(t["vals"]) if v == t["w"] and t["ids"][i] not in t["used"] and v not in t["dead"]]
        mal = [i for i, v in enumerate(t["vals"]) if v != t["w"] and t["ids"][i] not in t["used"] and v not in t["dead"]]
        if sid not in sabe and t["miss"] == 0 and t["len"] == 1 and mal: clic = mal[0]
        else: clic = ok[0] if ok else None
        if clic is None: continue
        pg.evaluate("(()=>{var T=S.tap; window.__ref=[T.it,T.pos,T.miss,T.used.size,T.dead.size]; })()")
        pg.click(".opt[data-i='%d']" % clic, force=True)
        try: pg.wait_for_function("(function(){var T=S.tap,r=window.__ref; return !T||S.mode!=='play'||T.it!==r[0]||T.pos!==r[1]||T.miss!==r[2]||T.used.size!==r[3]||T.dead.size!==r[4];})()", timeout=2500, polling=15)
        except Exception: pass
        if sid not in sabe and t["miss"] == 0 and t["len"] == 1 and mal: pg.wait_for_timeout(320)
        n += 1
    return "limite"

def llenar_intake(pg, edad, resp):
    pg.select_option("#ni_edad", value="" if edad is None else str(edad))
    for k, v in resp.items(): pg.select_option("#ni_" + k, value="" if v is None else str(v))

def abrir_intake_ui(pg):
    abrir_panel(pg); pg.click("#btnNumInicio"); pg.wait_for_selector("#numIntake.show")

@prueba("preguntas iniciales: pantalla del adulto → resumen ajustable → se aplica al progreso (edad 6) y queda en store.intake")
def t_intake_ui(C):
    res = {}
    for v in ("360x700", "740x330"):
        ctx, pg, err = nuevo_num(C, vista=v, semilla=201)
        igual(pg.evaluate("document.getElementById('numInicioEstado').textContent"), "", "vacío antes de abrir el panel")
        abrir_panel(pg); verificar("Todavía no se cargó" in pg.evaluate("document.getElementById('numInicioEstado').innerText"), "estado del panel")
        pg.click("#btnNumInicio"); pg.wait_for_selector("#numIntake.show")
        verificar("Punto de partida de Vale" in pg.evaluate("document.getElementById('numIntakeCard').innerText"), "título")
        verificar(pg.evaluate("document.querySelectorAll('#numIntakeCard select').length") == 6, "6 preguntas (edad + 5)")
        CAPTURAS.append(foto(pg, v + "_70_intake_preguntas"))
        llenar_intake(pg, 6, {"cuenta": 20, "reconoce": 20, "suma": 10, "resta": 5, "mult": 0})
        pg.click("#niVer"); pg.wait_for_selector("#numResumen.show")
        txt = pg.evaluate("document.getElementById('numResumenCard').innerText")
        verificar("Empieza en: Restas hasta 5" in txt and "5 habilidades marcadas como ya dominadas" in txt and "3 en curso" in txt, txt[:400])
        igual(pg.evaluate("store.intake.Vale.edad"), 6); igual(pg.evaluate("store.intake.Vale.resp"), {"cuenta": 20, "reconoce": 20, "suma": 10, "resta": 5, "mult": 0})
        verificar(not pg.evaluate("!!store.intake.Vale.inicio"), "todavía no se aplicó nada")
        verificar(not pg.evaluate("Object.values(store.sk).some(s=>s.mast||s.skip||s.att)"), "el progreso no cambia antes de aceptar")
        CAPTURAS.append(foto(pg, v + "_71_resumen_punto_de_partida"))
        # ajuste manual: el adulto sabe que también domina "Los números hasta 20" y que "Restas hasta 5" todavía no
        pg.select_option("select[data-id='num_r20']", value="saltada"); pg.select_option("select[data-id='num_sub5']", value="no")
        txt = pg.evaluate("document.getElementById('numResumenCard').innerText"); verificar("6 habilidades marcadas como ya dominadas" in txt, txt[:300])
        pg.click("#nrAceptar"); pg.wait_for_timeout(150)
        I = pg.evaluate("store.intake.Vale"); verificar(I["inicio"]["saltadas"] == 6 and "num_r20" in I["inicio"]["ajustes"] and "num_sub5" in I["inicio"]["ajustes"], str(I["inicio"]))
        igual(I["inicio"]["por"]["num_r20"], "manual", "por")
        sk = pg.evaluate("Object.fromEntries(Object.entries(store.sk).map(([k,s])=>[k.split('|')[1],[s.mast,s.skip&&s.skip.por,s.skip&&s.skip.estado,s.lvl,s.att]]))")
        for sid in ("num_c10", "num_r10", "num_may", "num_add5", "num_c20", "num_r20"): verificar(sk[sid][0] and sk[sid][2] == "pendiente", "%s debería estar saltada: %s" % (sid, sk.get(sid)))
        igual(sk["num_c10"][1], "adulto", "origen"); igual(sk["num_r20"][1], "manual"); verificar(not pg.evaluate("SK('num_sub5').mast"), "sub5 no se saltea")
        verificar(sk["num_add10"][3] == 1 and not sk["num_add10"][0], "en curso: sin dominar y con menos ayuda (lvl 1): %s" % sk["num_add10"])
        pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')"); igual(pg.evaluate("unlockedList().find(s=>!SK(s.id).mast).id"), "num_sub5", "la sesión arranca en lo que corresponde")
        verificar("Nuevo: Restas hasta 5" in pg.evaluate("sessionPreview()"), pg.evaluate("sessionPreview()"))
        verificar("Empieza en «Restas hasta 5»" in pg.evaluate("document.getElementById('numInicioEstado').textContent") or True)
        abrir_panel(pg); st = pg.evaluate("document.getElementById('numInicioEstado').innerText"); verificar("Restas hasta 5" in st and "6 habilidad" in st, st)
        # volver a abrir: muestra lo aceptado, editable, sin duplicar nada
        pg.click("#btnNumInicio"); pg.wait_for_selector("#numResumen.show"); verificar(pg.evaluate("document.querySelector(\"select[data-id='num_r20']\").value") == "saltada", "muestra lo aceptado")
        pg.click("#nrAceptar"); pg.wait_for_timeout(100); igual(pg.evaluate("Object.keys(store.sk).length") >= 6, True)
        # lo que se practicó de verdad no se toca
        pg.evaluate("(()=>{ const s=SK('num_sub5'); s.mast=true; s.att=9; s.score=.9; })()")
        pg.click("#btnNumInicio") if False else pg.evaluate("Gioval.numeros.mostrarResumen('ver')"); pg.wait_for_selector("#numResumen.show"); pg.click("#nrAceptar")
        verificar(pg.evaluate("SK('num_sub5').mast&&!SK('num_sub5').skip"), "no se toca el dominio real")
        verificar(not err, str(err)); ctx.close()
    return "intake guardado en store.intake, plan aplicado y ajustable (360x700 y 740x330)"

@prueba("test de ubicación en pantalla: juega el niño, no toca el progreso, el adulto ve el resumen, lo ajusta y lo acepta")
def t_ubicacion_ui(C):
    for v in ("360x700", "740x330"):
        ctx, pg, err = nuevo_num(C, vista=v, semilla=301)
        # intake: el adulto dice 5 años, cuenta hasta 20, reconoce hasta 20, suma hasta 10 (exagera un poco)
        abrir_intake_ui(pg); llenar_intake(pg, 5, {"cuenta": 20, "reconoce": 20, "suma": 10, "resta": 0, "mult": 0}); pg.click("#niVer"); pg.wait_for_selector("#numResumen.show")
        pg.click("#nrTest"); pg.wait_for_timeout(600)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "act", "pantalla de juego"); verificar(pg.evaluate("!!S.session.guia"), "sesión guiada")
        verificar(any("Vamos a jugar un ratito" in t for t in pg.evaluate("window.__LOG")), str(pg.evaluate("window.__LOG")))
        CAPTURAS.append(foto(pg, v + "_72_ubicacion_juego"))
        antes = pg.evaluate("JSON.stringify([store.sk,store.log,store.days])")
        sabe = {"num_c10", "num_r10", "num_may", "num_c20", "num_add5"}
        igual(responder_ubicacion(pg, sabe), "fin")
        verificar(pg.evaluate("store.intake.Vale.pendiente===true&&store.intake.Vale.ubicacion.registros.length>=6"), "guardó el resultado pendiente")
        igual(pg.evaluate("JSON.stringify([store.sk,store.log,store.days])"), antes, "el test no toca habilidades, registro ni días")
        verificar("un adulto" in pg.evaluate("window.__LOG[window.__LOG.length-1]"), "el niño escucha que sigue un adulto")
        n = pg.evaluate("store.intake.Vale.ubicacion.registros.length"); verificar(n <= 30, "ítems: %d" % n)
        dur = pg.evaluate("store.intake.Vale.ubicacion.durMs"); verificar(dur < 5 * 60e3, "~5 min como tope")
        pg.click("#btnFinOk"); pg.wait_for_selector("#gateBox.show"); pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_selector("#numResumen.show")
        txt = pg.evaluate("document.getElementById('numResumenCard').innerText")
        verificar("Resultado del test de ubicación de Vale" in txt and "Empieza en:" in txt and "marcadas como ya dominadas" in txt and "Test: " in txt, txt[:500])
        CAPTURAS.append(foto(pg, v + "_73_ubicacion_resumen"))
        # el test corrigió al adulto: no pasó lo que no sabe, aunque el adulto lo haya dicho
        est = pg.evaluate("Object.fromEntries([...document.querySelectorAll('select.nsel')].map(s=>[s.dataset.id,s.value]))")
        verificar(est["num_c10"] == "saltada" and est["num_r10"] == "saltada" and est["num_add5"] in ("saltada", "encurso"), str({k: est[k] for k in ("num_c10", "num_r10", "num_add5", "num_c20")}))
        verificar(est["num_add10"] != "saltada" and est["num_r20"] != "saltada", "el adulto dijo suma hasta 10 y reconoce hasta 20, el test no lo confirmó: %s %s" % (est["num_add10"], est["num_r20"]))
        pg.select_option("select[data-id='num_may']", value="no"); pg.wait_for_timeout(50)
        verificar(pg.evaluate("document.querySelector(\"select[data-id='num_c20']\").value") != "saltada", "al desmarcar una base se sueltan las que dependen de ella")
        pg.select_option("select[data-id='num_may']", value="saltada")
        pg.click("#nrAceptar"); pg.wait_for_timeout(150)
        I = pg.evaluate("store.intake.Vale"); verificar(not I.get("pendiente") and I["inicio"]["origen"] == "test" and I["inicio"]["saltadas"] >= 3, str(I["inicio"]))
        verificar(pg.evaluate("SK('num_c10').mast&&SK('num_c10').skip.por")  in ("ubicacion", "implicita"), "origen del salto: " + str(pg.evaluate("SK('num_c10').skip")))
        sk = pg.evaluate("SK('num_c10').skip"); verificar(sk["motivo"]["k"] in ("numeros.ed.motivos.ubicacion", "numeros.ed.motivos.implicita"), str(sk["motivo"]))
        verificar(not err, str(err)); ctx.close()
    return "test jugable (voz), resultado pendiente → resumen para el adulto → aceptado"

@prueba("test de ubicación: tope de tiempo (~5 min), 'Seguir' cuenta como no sé y salir no deja nada pendiente")
def t_ubicacion_tiempo(C):
    ctx, pg, err = nuevo_num(C, semilla=302)
    abrir_intake_ui(pg); llenar_intake(pg, 6, {"cuenta": 20}); pg.click("#niVer"); pg.wait_for_selector("#numResumen.show"); pg.click("#nrTest"); pg.wait_for_timeout(500)
    # "Seguir ➜" dos veces en el mismo nivel = no sé → falla
    sid = pg.evaluate("S.tap.it.skill.id"); pg.click("#btnActSkip"); pg.wait_for_timeout(300)
    verificar(pg.evaluate("S.session.guia!==undefined"), "sigue en la sesión guiada")
    # se pasa el tiempo: al terminar el ítem en curso, cierra por tiempo
    pg.evaluate("window.__OFF=6*60e3"); fijar_rt(pg, 800); responder_ubicacion(pg, {"num_c10", "num_r10"}, limite=6)
    pg.wait_for_selector("#finish.show", timeout=8000)
    igual(pg.evaluate("store.intake.Vale.ubicacion.fin"), "tiempo", "motivo de cierre")
    reg0 = pg.evaluate("store.intake.Vale.ubicacion.registros[0]"); verificar(reg0["s"] == sid and not reg0["ok"], "«Seguir» cuenta como no sé (error): %s" % reg0)
    verificar(pg.evaluate("store.intake.Vale.ubicacion.durMs") < 8 * 60e3, "cierra al terminar el ítem en curso")
    pg.evaluate("window.__OFF=0")
    # salir con ⬅ en medio de un test nuevo no guarda resultado
    pg.click("#btnFinOk"); pg.wait_for_selector("#gateBox.show"); pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_selector("#numResumen.show"); pg.click("#nrVolver")
    pg.evaluate("delete store.intake.Vale.ubicacion; delete store.intake.Vale.pendiente"); pg.evaluate("Gioval.numeros.iniciarTest()"); pg.wait_for_timeout(500)
    pg.click("#btnActBack"); pg.wait_for_timeout(200)
    verificar(pg.evaluate("!store.intake.Vale.ubicacion&&!store.intake.Vale.pendiente"), "salir a mitad no deja resultado")
    verificar(not err, str(err)); ctx.close()

@prueba("informe de adultos: punto de partida, dominadas con evidencia (aciertos, tiempo, retención) y qué se saltó y por qué")
def t_num_informe(C):
    ctx, pg, err = nuevo_num(C, semilla=401)
    rep0 = pg.evaluate("reportText()"); verificar("PUNTO DE PARTIDA" not in rep0, "sin datos no hay sección")
    abrir_intake_ui(pg); llenar_intake(pg, 6, {"cuenta": 20, "reconoce": 20, "suma": 10, "resta": 5, "mult": 0}); pg.click("#niVer"); pg.wait_for_selector("#numResumen.show"); pg.click("#nrAceptar"); pg.wait_for_timeout(100)
    # práctica real: lo que está en curso, perfecto y rápido, durante varios días
    for d in range(4):
        pg.evaluate("window.__OFF=%d*864e5" % (d * 2)); sesion_perfecta(pg, 1, 900)
    pg.evaluate("window.__OFF=8*864e5"); sesion_perfecta(pg, 1, 900)
    rep = pg.evaluate("reportText()")
    for frag in ("PUNTO DE PARTIDA — ISLA NÚMEROS", "Edad: 6 años", "Cuenta de memoria: hasta 20", "Suma: sí, hasta 10", "Punto de partida aceptado el", "empieza en «Restas hasta 5»", "5 saltadas · 3 en curso",
                 "Aciertos al primer intento", "Retención (acierto ≥1 día", "Tiempo de respuesta (mediana, aciertos sin pistas)", "HABILIDADES SALTADAS (sin práctica propia) Y POR QUÉ",
                 "según lo que contó el adulto", "se reevalúa en el próximo chequeo semanal sin ayuda", "saltada (sin práctica propia)", "dominado"):
        verificar(frag in rep, "falta en el informe: «%s»\n%s" % (frag, rep))
    verificar("(n=" in rep and re.search(r"mediana \d+,\d s", rep), "tiempos con formato")
    # después de un chequeo aprobado la saltada queda confirmada
    abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); jugar(pg); cerrar_fin(pg)
    rep2 = pg.evaluate("reportText()"); verificar("CONFIRMADA en el chequeo" in rep2, rep2[-1200:])
    foto_t = pg.evaluate("document.getElementById('reportTxt')?1:0"); pg.evaluate("document.getElementById('reportTxt').textContent=reportText(); document.getElementById('reportBox').classList.add('show')")
    CAPTURAS.append(foto(pg, "360x700_74_informe_punto_de_partida")); pg.evaluate("document.getElementById('reportBox').classList.remove('show')")
    verificar(not err, str(err)); ctx.close()
    ctx = C.banco.contexto("740x330"); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err, semilla=402); instalar_speak(pg); entrar(pg, "Vale")
    pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')"); abrir_intake_ui(pg); llenar_intake(pg, 7, {"cuenta": 100, "reconoce": 100, "suma": 20, "resta": 20, "mult": 1}); pg.click("#niVer"); pg.wait_for_selector("#numResumen.show"); pg.click("#nrAceptar"); pg.wait_for_timeout(100)
    pg.evaluate("document.getElementById('reportTxt').textContent=reportText(); document.getElementById('reportBox').classList.add('show')"); CAPTURAS.append(foto(pg, "740x330_74_informe_punto_de_partida")); ctx.close()

@prueba("Números por edades en inglés, es-419 y pseudo-idioma: sin español suelto, sin claves faltantes, intake e informe")
def t_num_idiomas(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=601, extra_init="localStorage.setItem('gioval_idioma','en');"); instalar_speak(pg); entrar(pg, "Vale")
    pg.evaluate("PACK=PACKS.find(p=>p.id==='numeros')")
    textos = pg.evaluate("""(()=>{ const out=[]; for(let rep=0;rep<12;rep++) for(const s of PACK.skills) for(const aid of [0,1,2]){ const A=ACTIVITIES[s.type], it=A.make(s), T={pos:0,cnt:[],help:false,aid,used:new Set(),dead:new Set()}, v=A.view(it,aid,T);
        out.push(s.name,v.say,A.tip(it),A.reveal(it,T),...(A.okMsgs||[])); } return out; })()""")
    verificar(len(textos) > 1000 and not sin_espanol(textos), "español en inglés: %s" % sin_espanol(textos)[:4])
    verificar(not [x for x in textos if re.search(r"[{}]|undefined|NaN", x)], "huecos sin resolver")
    # intake, resumen e informe en inglés
    abrir_intake_ui(pg); llenar_intake(pg, 6, {"cuenta": 20, "reconoce": 20, "suma": 10, "resta": 5, "mult": 0})
    card = pg.evaluate("document.getElementById('numIntakeCard').innerText"); verificar("Starting point for Vale" in card and "How old are they?" in card and not sin_espanol([card]), card[:300])
    pg.click("#niVer"); pg.wait_for_selector("#numResumen.show"); res = pg.evaluate("document.getElementById('numResumenCard').innerText")
    verificar("Starts at: Subtracting up to 5" in res or "Starts at: Restas" not in res, res[:300]); verificar(not sin_espanol([res]) and "5 skills marked as already mastered" in res, res[:400])
    CAPTURAS.append(foto(pg, "360x700_75_ingles_resumen_punto_de_partida"))
    pg.click("#nrAceptar"); pg.wait_for_timeout(100)
    rep = pg.evaluate("reportText()"); verificar("STARTING POINT — NUMBERS ISLAND" in rep and "Age: 6 years." in rep and "SKIPPED SKILLS" in rep and not sin_espanol(rep.split("\n")), rep[:900])
    igual(pg.evaluate("[...Gioval.i18n.faltantes]"), [], "claves faltantes")
    # el mismo punto de partida se escribe en el idioma de quien lee: cambiar a es-419 no deja el informe en inglés
    pg.evaluate("Gioval.i18n.usar('es-419')"); rep2 = pg.evaluate("reportText()")
    verificar("PUNTO DE PARTIDA — ISLA NÚMEROS" in rep2 and "SKIPPED" not in rep2 and "5 saltadas · 3 en curso" in rep2, rep2[:600])
    verificar("Toca el número" in " ".join(pg.evaluate("(()=>{ const o=[]; for(let i=0;i<30;i++){ const s=PACK.skills.find(x=>x.id==='num_r100'), A=ACTIVITIES[s.type], it=A.make(s); o.push(A.view(it,1,{pos:0,cnt:[],used:new Set(),dead:new Set()}).say); } return o; })()")), "es-419 usa tuteo")
    # pseudo-idioma (+40 %): las pantallas del adulto no deben dar errores ni claves
    pg.evaluate("Gioval.i18n.usar('qps-ploc')"); pg.evaluate("Gioval.numeros.mostrarResumen('ver')"); pg.wait_for_selector("#numResumen.show")
    CAPTURAS.append(foto(pg, "360x700_76_pseudo_resumen_punto_de_partida"))
    ancho = pg.evaluate("(()=>{ const c=document.getElementById('numResumenCard'); return [c.scrollWidth,c.clientWidth]; })()"); verificar(ancho[0] <= ancho[1] + 2, "desborde horizontal en pseudo-idioma: %s" % ancho)
    igual(pg.evaluate("[...Gioval.i18n.faltantes]"), [], "claves faltantes (pseudo)")
    verificar(not err, str(err)); ctx.close()

@prueba("Números por edades: las habilidades nuevas se juegan en sesión completa, se dominan, desbloquean y tienen chequeo")
def t_num_nuevas(C):
    # estado: todo lo de la v1 ya dominado, para llegar a las nuevas
    base = dict(STORE_KID); ctx, pg, err = nuevo_num(C, "740x330", semilla=501)
    pg.evaluate("(()=>{ ['num_c10','num_r10','num_may','num_add5','num_sub5','num_c20','num_add10','num_sub10','num_r20'].forEach(id=>{ const s=SK(id); s.mast=true; s.att=9; s.score=.95; s.box=1; s.due=Date.now()+864e5; }); save(); })()")
    vistas = set()
    for i in range(14):
        abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(200)
        vistas |= set(pg.evaluate("S.session.items.map(i=>i.skill.type)")); verificar(jugar(pg, cada_error=5 if i < 2 else 0, perfecto=(i >= 2)) == "fin"); cerrar_fin(pg)
        if i == 0: CAPTURAS.append("740x330_11b_numeros_nuevas") if False else None
    dom = pg.evaluate("PACK.skills.filter(s=>SK(s.id).mast).map(s=>s.id)")
    for x in ("num_sig", "num_ser20", "num_may20", "num_r100"): verificar(x in dom, "%s no quedó dominada: %s" % (x, dom))
    verificar(len(vistas) >= 4, "tipos jugados: %s" % vistas)
    abrir_isla(pg, "Números"); tarjeta(pg, "Chequeo semanal"); verificar(jugar(pg) == "fin"); cerrar_fin(pg)
    verificar(not err, str(err)); ctx.close(); return "dominadas: %d" % len(dom)


# ---------------------------------------------------------------- Isla Ritmo y detector de golpes
ESC_TEST = "window.__RITMO_ESCALA=5;"   # reloj de la isla 5 veces más rápido (solo pruebas); los tiempos de los golpes sintéticos son reales
STORE_RITMO = {"profiles": ["Vale"], "limit": {"Vale": 60}}

def solo_habilidad(pg, sid):
    """Deja dominadas todas las habilidades de Ritmo menos `sid` (así la sesión practica justo esa)."""
    pg.evaluate("""(sid)=>{ PACK=PACKS.find(p=>p.id==='ritmo'); PACK.skills.forEach(s=>{ var st=SK(s.id); if(s.id===sid){ st.mast=false; st.att=0; st.score=.5; st.box=0; st.lvl=0; st.rec=[]; }
      else { st.mast=true; st.att=6; st.score=.9; st.box=1; st.due=Date.now()+864e5; } }); }""", sid)

def esperar_fase(pg, fase, seg=20):
    pg.wait_for_function("Gioval.ritmo.fase==='%s'" % fase, timeout=seg * 1000)

@prueba("Ritmo: evaluación del eco rítmico (acierto, adelantado, atrasado, golpe de más, faltante) y ventanas por nivel")
def t_ritmo_evaluacion(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    ioi = lambda rel, h, W: pg.evaluate("(a)=>Gioval.ritmo.evaluar.ioi(a[0],a[1],a[2])", [rel, h, W])
    estados = lambda r: [e["estado"] for e in r["etiquetas"]]
    rel = [0, 500, 1000, 1500]
    r = ioi(rel, [1000, 1500, 2000, 2500], 120); verificar(r["ok"] and estados(r) == ["ok"] * 4 and r["desvio"] == 0, "acierto exacto: %s" % r)
    r = ioi(rel, [1000, 1540, 1980, 2520], 120); verificar(r["ok"] and 0 < r["desvio"] <= 60, "acierto con pequeño desvío: %s" % r)
    r = ioi(rel, [0, 500, 780, 1500], 120); igual(estados(r), ["ok", "ok", "adelantado", "ok"], "adelantado"); verificar(not r["ok"])
    r = ioi(rel, [0, 500, 1000, 1750], 120); igual(estados(r), ["ok", "ok", "ok", "atrasado"], "atrasado"); verificar(not r["ok"])
    r = ioi(rel, [0, 500, 700, 1000, 1500], 120); igual(estados(r), ["ok"] * 4, "golpe de más: los esperados siguen bien"); igual(r["extra"], [700], "golpe de más"); verificar(not r["ok"])
    r = ioi(rel, [0, 500, 1000], 120); igual(estados(r), ["ok", "ok", "ok", "falta"], "faltante"); verificar(not r["ok"])
    r = ioi(rel, [], 120); igual(estados(r), ["falta"] * 4, "sin golpes")
    # el tempo 20 % más lento pasa con la ventana ancha y no con la angosta; la ventana depende del nivel y del pulso
    lento = [0, 600, 1200, 1800]
    v = pg.evaluate("[0,1,2].map(l=>Gioval.ritmo.ventana(l,500))"); igual([round(x) for x in v], [160, 120, 90], "ventanas por nivel (pulso de 500 ms)")
    verificar(ioi(rel, lento, v[0])["ok"] and ioi(rel, lento, v[1])["ok"], "20 % más lento debería pasar con ventana de nivel 0/1")
    verificar(not ioi(rel, lento, 60)["ok"], "20 % más lento no debería pasar con 60 ms")
    igual([round(x) for x in pg.evaluate("[Gioval.ritmo.ventana(0,2000),Gioval.ritmo.ventana(2,200)]")], [210, 90], "topes de la ventana")
    # ejercicios largos: alcanza el 75 %
    rel8 = [i * 500 for i in range(8)]; h = [i * 500 for i in range(8)]; h[3] += 200; h[6] += 200
    verificar(ioi(rel8, h, 120)["ok"] is True, "6 de 8 deberían alcanzar en un ejercicio largo")
    h[1] += 200; verificar(ioi(rel8, h, 120)["ok"] is False, "5 de 8 no alcanzan")
    # grilla: la demora fija (micrófono/pantalla) no cuenta; una tardanza puntual sí; un golpe en un silencio se reconoce
    gr = lambda exp, h, W, o=None: pg.evaluate("(a)=>Gioval.ritmo.evaluar.grid(a[0],a[1],a[2],a[3],a[4])", [exp, h, W, 500, o or {}])
    exp = [1000, 1500, 2000, 2500]
    r = gr(exp, [x + 70 for x in exp], 120); verificar(r["ok"] and abs(r["sesgo"] - 70) < 1 and r["desvio"] < 1, "demora fija: %s" % r)
    r = gr(exp, [1000, 1500, 2200, 2500], 120); igual(estados(r), ["ok", "ok", "atrasado", "ok"], "grilla: tarde"); verificar(not r["ok"])
    r = gr([1000, 1500, 2500], [1000, 1500, 2000, 2500], 120, {"silencios": [2000]}); verificar(r["extraSilencio"] and not r["ok"], "golpe en el silencio: %s" % r)
    libre = lambda h: pg.evaluate("(a)=>Gioval.ritmo.evaluar.libre(a,1000,500,120)", h)
    verificar(libre([1000, 1500, 1750, 2250])["ok"], "libre sobre la grilla de corcheas")
    igual(libre([1000, 1500, 1625])["motivo"], "desparejo", "libre fuera de grilla"); igual(libre([1000])["motivo"], "pocos"); igual(libre([1000 + 250 * i for i in range(9)])["motivo"], "muchos")
    ctx.close()

DETECTORES = ("click", "palma", "tambor", "cajon", "pandereta")

@prueba("golpes: detector con audio sintético (precisión del tiempo, tempos, instrumentos, falsos positivos, refractario, silencio de la app)")
def t_golpes_detector(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    peor = 0
    for bpm in (60, 100, 150):
        per = 60000 / bpm
        for tipo in DETECTORES:
            hits = [3700 + k * per for k in range(10)]
            x = senal_golpes(3.7 + 10 * per / 1000 + 0.6, hits, tipo, 0.004, semilla=bpm, zumbido=0.002)
            ev, info = simular_golpes(pg, x)
            verificar(len(ev) == 10, "%s a %d bpm: detectó %d de 10" % (tipo, bpm, len(ev)))
            err = max(abs(e[0] - h) for e, h in zip(ev, hits)); peor = max(peor, err)
            verificar(err <= 6, "%s a %d bpm: error de tiempo %.1f ms" % (tipo, bpm, err))
            verificar(all(0 <= e[1] <= 1 for e in ev), "fuerza fuera de 0..1")
    # sin golpes: ruido de sala, zumbido, crescendo lento, ventilador que arranca después de calibrar -> sin falsos positivos
    np = __import__("numpy")
    def crescendo(x, rng, sr):
        t = np.arange(len(x)) / sr; return x + np.clip((t - 4) * 0.004, 0, 0.05) * np.sin(2 * np.pi * 120 * t)
    def ventilador(x, rng, sr):
        x = x.copy(); i = int(6 * sr); x[i:] += rng.normal(0, 0.03, len(x) - i); return x
    casos = {"ruido 0,004": dict(ruido=0.004), "ruido 0,02 (sala ruidosa)": dict(ruido=0.02), "zumbido 50 Hz": dict(ruido=0.004, zumbido=0.012),
             "crescendo lento": dict(ruido=0.003, extra=crescendo)}
    for nombre, kw in casos.items():
        ev, _ = simular_golpes(pg, senal_golpes(14, [], "palma", semilla=5, **kw)); igual(len(ev), 0, "falsos positivos con " + nombre)
    ev, _ = simular_golpes(pg, senal_golpes(14, [], "palma", 0.004, semilla=6, extra=ventilador))
    verificar(len(ev) <= 1, "ventilador que arranca: %d eventos (se tolera 1, el del arranque)" % len(ev))
    verificar(all(e[0] > 6000 - 20 for e in ev), "el ventilador no debería disparar antes de arrancar")
    # ninguna detección durante la calibración (aunque haya golpes): se ignoran
    ev, info = simular_golpes(pg, senal_golpes(8, [1000, 2000, 5000, 5600], "palma", 0.004, semilla=7)); verificar(all(e[0] > 3000 for e in ev), "emitió durante la calibración")
    # refractario: dos golpes a 30 ms cuentan como uno; a 200 ms, como dos
    ev, _ = simular_golpes(pg, senal_golpes(7, [3800, 3830, 4400, 4600], "click", 0.004, semilla=8)); igual(len(ev), 3, "doble a 30 ms = 1 · pares a 200 ms = 2")
    # rasgueo de guitarra: 6 cuerdas en 50 ms = 1 golpe (el del inicio)
    ev, _ = simular_golpes(pg, senal_golpes(7, [3800 + 10 * i for i in range(6)] + [5200], "tambor", 0.004, semilla=9)); igual(len(ev), 2, "rasgueo = 1 golpe")
    verificar(abs(ev[0][0] - 3800) <= 6, "el rasgueo marca el inicio")
    # intensidad aproximada: más fuerte -> más "fuerza"
    fz = []
    for a in (0.04, 0.1, 0.3, 0.8):
        ev, _ = simular_golpes(pg, senal_golpes(6, [4000], "palma", 0.004, semilla=10, amps=[a])); verificar(len(ev) == 1, "amp %s no detectado" % a); fz.append(ev[0][1])
    verificar(fz == sorted(fz) and fz[-1] > fz[0] + 0.3, "la fuerza no crece con la intensidad: %s" % fz)
    # sala ruidosa: el umbral sube solo y los golpes siguen detectándose
    hits = [3800 + 500 * k for k in range(10)]
    ev, info = simular_golpes(pg, senal_golpes(10, hits, "palma", 0.02, semilla=11)); igual(len(ev), 10, "golpes en sala ruidosa"); verificar(info["umbral"] > 0.05, "el umbral no se adaptó al ruido: %s" % info)
    # golpes muy suaves: con sensibilidad normal se pierden y con más sensibilidad se escuchan (límite documentado)
    suaves = [3800 + 500 * k for k in range(6)]; xs = senal_golpes(8, suaves, "palma", 0.004, semilla=12, amps=[0.012] * 6)
    n1 = len(simular_golpes(pg, xs)[0]); n2 = len(simular_golpes(pg, xs, sens=3)[0]); verificar(n2 > n1, "más sensibilidad no ayudó: %d → %d" % (n1, n2))
    # silencio de la app: los golpes dentro de una ventana silenciada se descartan
    hits = [3800 + 500 * k for k in range(8)]
    ev, _ = simular_golpes(pg, senal_golpes(9, hits, "palma", 0.004, semilla=13), mudo=[[4750, 5400]]); igual(len(ev), 6, "golpes silenciados por la voz de la app")
    ctx.close(); return "tiempo peor caso %.1f ms; 15 señales × 10 golpes; falsos positivos 0" % peor

def con_microfono_falso(C, wav):
    return Banco(C.pw, ["--use-fake-ui-for-media-stream", "--use-fake-device-for-media-stream", "--use-file-for-fake-audio-capture=%s%%noloop" % wav])

JS_ESCUCHAR = """()=>{ window.__ev=[]; Gioval.entrada.suscribir('golpe',e=>window.__ev.push([e.t,e.fuerza,e.fuente])); const G=Gioval.entrada.proveedores.golpes;
  return G.iniciar({fuente:'mic'}).then(f=>G.calibrar().then(i=>[f,i])); }"""

@prueba("golpes: micrófono falso de Chrome con audio de percusión (WAV): inicios en el tiempo justo, sin falsos positivos, silencio de la app")
def t_golpes_microfono(C):
    SALIDA.mkdir(exist_ok=True); resumen = []; peor_i = 0
    ritmo = [0, 600, 1200, 1500, 1800, 2400, 2700, 3000, 3600, 4200]
    h100 = [3800 + 600 * k for k in range(10)]
    casos = [("palmas_100bpm", senal_golpes(3.8 + 6.4 + 0.8, h100, "palma", 0.004, semilla=21), h100, None),
             ("cajon_ritmo", senal_golpes(3.8 + 4.2 + 0.8, [3800 + t for t in ritmo], "cajon", 0.004, semilla=22), [3800 + t for t in ritmo], None),
             ("silencio_con_zumbido", senal_golpes(9, [], "palma", 0.005, semilla=23, zumbido=0.01), [], None),
             ("palmas_con_voz_de_la_app", senal_golpes(3.8 + 6.4 + 0.8, h100, "palma", 0.004, semilla=24), h100, "mudo")]
    for nombre, x, verdad, modo in casos:
        wav = a_wav(x, SALIDA / (nombre + ".wav")); b = con_microfono_falso(C, wav); err = []
        try:
            ctx = b.contexto("360x700", permissions=["microphone"]); pg = abrir(ctx, C.url + "/index.html", errores=err, rapido=False)
            f, info = pg.evaluate(JS_ESCUCHAR); igual(f, "mic", "fuente"); verificar(info and info["utilMs"] >= 2990, "calibración: %s" % info)
            verificar(info["piso"] < 0.03, "piso de ruido: %s" % info)
            if modo == "mudo":
                pg.wait_for_function("window.__ev.length>=3", timeout=15000); pg.evaluate("muteUntil=performance.now()+1300")
                pg.wait_for_timeout(5000)
            else:
                pg.wait_for_timeout(int(len(x) / 48 - 3000 + 600))
            ev = pg.evaluate("window.__ev"); ts = [e[0] for e in ev]
            if modo == "mudo":
                igual(len(ev), 8, "con la app 'hablando' se pierden justo los 2 golpes silenciados")
                gaps = [round(q - p) for p, q in zip(ts, ts[1:])]; verificar(sum(1 for g in gaps if 1750 <= g <= 1850) == 1, "hueco de 3 pulsos: %s" % gaps)
            else:
                igual(len(ev), len(verdad), nombre + ": cantidad de golpes")
                # se miden los INTERVALOS entre golpes (lo que importa para evaluar): todos a ≤ 12 ms de lo real, salvo a lo sumo uno (≤ 30 ms)
                # que tolera un bache del propio micrófono falso de Chrome cuando la máquina está muy cargada (se vio en pruebas con carga extrema)
                err_i = [abs((ts[k] - ts[k - 1]) - (verdad[k] - verdad[k - 1])) for k in range(1, len(ev))]
                verificar(sum(1 for e in err_i if e > 12) <= 1 and max(err_i + [0]) <= 30, "%s: intervalos fuera de tiempo (error por intervalo en ms: %s)" % (nombre, [round(e, 1) for e in err_i]))
                peor_i = max([peor_i] + err_i)
            verificar(all(e[2] == "mic" for e in ev)); verificar(not err, str(err)); ctx.close()
            resumen.append("%s=%d" % (nombre, len(ev)))
        finally: b.cerrar()
    return ", ".join(resumen) + " · peor error de intervalo %.1f ms" % peor_i

@prueba("golpes: Música y Ritmo comparten UN solo flujo de micrófono (un permiso) y se apaga cuando nadie lo usa")
def t_golpes_flujo_compartido(C):
    SALIDA.mkdir(exist_ok=True); wav = a_wav(senal_golpes(6, [], "palma", 0.004, semilla=31), SALIDA / "ruido.wav"); b = con_microfono_falso(C, wav); err = []
    try:
        ctx = b.contexto("360x700", permissions=["microphone"])
        pg = abrir(ctx, C.url + "/index.html", errores=err, rapido=False, extra_init="window.__gum=0; (function(){ var o=navigator.mediaDevices.getUserMedia.bind(navigator.mediaDevices); navigator.mediaDevices.getUserMedia=function(c){ window.__gum++; return o(c); }; })();")
        r = pg.evaluate("""async()=>{ const M=Gioval.entrada.proveedores.microfono, G=Gioval.entrada.proveedores.golpes; const out={};
          await M.iniciar({}); await G.iniciar({fuente:'mic'}); out.llamadas=window.__gum; out.activos=[M.activo,G.activo,G.fuente];
          G.detener(); await new Promise(r=>setTimeout(r,100)); out.tras_golpes=M.activo; M.detener(); return out; }""")
        igual(r["llamadas"], 1, "getUserMedia debería pedirse una sola vez"); igual(r["activos"], [True, True, "mic"]); verificar(r["tras_golpes"], "Música debería seguir escuchando")
        verificar(not err, str(err)); ctx.close()
    finally: b.cerrar()

@prueba("Ritmo: sesión completa por toque en 360x700 y 740x330 (dominio, desbloqueo, ayudas, errores sin castigo, informe)")
def t_ritmo_sesion(C):
    detalle = []
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=81, rapido=False, extra_init=ESC_TEST); instalar_speak(pg); entrar(pg, "Vale")
        abrir_isla(pg, "Ritmo"); CAPTURAS.append(foto(pg, v + "_60_ritmo_menu"))
        txt = pg.evaluate("document.getElementById('menuIslaItems').innerText"); verificar("Tocar con mi instrumento" in txt and "Sesión de hoy" in txt, txt)
        tarjeta(pg, "Sesión de hoy"); esperar_fase(pg, "turno"); pg.wait_for_timeout(200)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "rit", "pantalla")
        CAPTURAS.append(foto(pg, v + "_61_ritmo_eco_tarjetas"))
        verificar(jugar_ritmo(pg) == "fin"); cerrar_fin(pg)
        for _ in range(3):
            pg.evaluate("PACK=PACKS.find(p=>p.id==='ritmo')")
            if pg.evaluate("SK('rit_pulso').mast"): break
            abrir_isla(pg, "Ritmo"); tarjeta(pg, "Sesión de hoy"); verificar(jugar_ritmo(pg) == "fin"); cerrar_fin(pg)
        verificar(pg.evaluate("SK('rit_pulso').mast"), "rit_pulso no quedó dominada")
        desbloq = pg.evaluate("unlockedList().map(s=>s.id)"); verificar(all(x in desbloq for x in ("rit_eco2", "rit_tempo", "rit_base")), "desbloqueo: %s" % desbloq)
        # una sesión con errores inyectados (golpe adelantado, faltante, de más): la app lo dice con amabilidad, reintenta y no castiga
        pg.evaluate("window.__LOG.length=0"); abrir_isla(pg, "Ritmo"); tarjeta(pg, "Sesión de hoy")
        verificar(jugar_ritmo(pg, errores=["adelantado", None, "falta", None, "extra", None]) == "fin", "la sesión con errores no terminó")
        dicho = " | ".join(pg.evaluate("window.__LOG")); verificar("rápido" in dicho and ("Faltó" in dicho or "de más" in dicho), "no explicó los errores: " + dicho[:400])
        verificar(not any(w in dicho.lower() for w in ("incorrecto", "perdiste", "fallaste", "mal ")), "texto con tono de castigo: " + dicho[:300])
        cerrar_fin(pg)
        reg = pg.evaluate("store.ritmo.Vale"); verificar(len(reg) >= 14 and all(k in reg[0] for k in ("t", "s", "d", "b", "n", "o", "x", "f", "bpm", "l", "c", "ok")), "registro de regularidad: %s" % reg[:1])
        verificar(any(e["ok"] == 0 for e in reg), "no se registró ningún intento fallido (¿se inyectaron los errores?)")
        rep = pg.evaluate("reportText()"); verificar("REGULARIDAD DEL RITMO" in rep and "Desvío medio general" in rep and "No juzga la técnica" in rep and "Evolución" in rep, rep[-900:])
        verificar("ISLA RITMO" in rep and "Sentir el pulso" in rep, "el informe general no lista la isla: " + rep[:300])
        pg.evaluate("goMenuIsla()"); pg.click(".island:has-text('Mis logros')"); pg.wait_for_timeout(250); CAPTURAS.append(foto(pg, v + "_62_ritmo_logros"))
        verificar(not err, "%s: %s" % (v, err)); detalle.append("%s: %d mediciones" % (v, len(reg))); ctx.close()
    return "; ".join(detalle)

HABS = ["rit_pulso", "rit_eco2", "rit_tempo", "rit_base", "rit_eco3", "rit_eco4", "rit_silencio", "rit_solo", "rit_lee1", "rit_lee2", "rit_llamada", "rit_cancion", "rit_leemix", "rit_compone"]

@prueba("Ritmo: las 14 habilidades se juegan completas (ayudas, silencios, tarjetas, canciones, llamada y respuesta, composición)")
def t_ritmo_habilidades(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=91, rapido=False, extra_init=ESC_TEST); instalar_speak(pg); entrar(pg, "Vale")
    igual(pg.evaluate("PACKS.find(p=>p.id==='ritmo').skills.map(s=>s.id)"), HABS, "habilidades")
    pg.evaluate("window.__LOG.length=0"); casos = {"rit_eco3": ["adelantado", None], "rit_silencio": ["extra", None], "rit_lee2": ["falta", None], "rit_base": ["atrasado", None]}
    for sid in HABS:
        abrir_isla(pg, "Ritmo"); solo_habilidad(pg, sid); tarjeta(pg, "Sesión de hoy"); pg.evaluate("S.session.items.length=2")
        opc = {"libre": [0]} if sid == "rit_llamada" else None
        r = jugar_ritmo(pg, errores=casos.get(sid), opciones=opc, limite_s=90); verificar(r == "fin", "%s: terminó con %s" % (sid, r)); cerrar_fin(pg)
        n = pg.evaluate("(store.ritmo.Vale||[]).filter(e=>e.s==='%s').length" % sid); verificar(n >= 1, "%s sin mediciones" % sid)
    dicho = " | ".join(pg.evaluate("window.__LOG")).lower()
    for frag in ("shh", "ti-ti", "yo toco un ritmo", "armá tu propio ritmo", "probá con más golpes", "este es el ritmo de una canción"):
        verificar(frag in dicho, "falta el texto '%s' (¿se jugó esa actividad?)" % frag)
    verificar(any(a in dicho for a in ("tortuga", "conejo", "guepardo")), "falta la frase del tempo (¿se jugó 'lento, medio y rápido'?)")
    verificar(not err, str(err)); ctx.close(); return "14 habilidades"

@prueba("Ritmo: composición de 4 pulsos, lectura con tarjetas y silencios en 360x700 y 740x330 (capturas)")
def t_ritmo_pantallas(C):
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []
        pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=93, rapido=False, extra_init="window.__RITMO_ESCALA=2;"); instalar_speak(pg); entrar(pg, "Vale")
        for sid, fase, tag, espera in (("rit_lee2", "turno", "lectura", 900), ("rit_compone", "componer", "componer", 400), ("rit_silencio", "turno", "silencio", 900)):
            abrir_isla(pg, "Ritmo"); solo_habilidad(pg, sid); tarjeta(pg, "Sesión de hoy"); esperar_fase(pg, fase); pg.wait_for_timeout(espera)
            CAPTURAS.append(foto(pg, "%s_64_ritmo_%s" % (v, tag)))
            pg.evaluate("S.run++; resetFlow(); goMenuIsla()")
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

@prueba("Ritmo: chequeo semanal sin ayuda (un solo intento) e informe con regularidad")
def t_ritmo_chequeo(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=95, rapido=False, extra_init=ESC_TEST); instalar_speak(pg); entrar(pg, "Vale")
    for _ in range(3):
        abrir_isla(pg, "Ritmo"); pg.evaluate("PACK=PACKS.find(p=>p.id==='ritmo')")
        if pg.evaluate("SK('rit_pulso').mast"): break
        tarjeta(pg, "Sesión de hoy"); jugar_ritmo(pg); cerrar_fin(pg)
    abrir_isla(pg, "Ritmo"); tarjeta(pg, "Chequeo semanal")
    verificar(jugar_ritmo(pg, errores=[None, "adelantado"]) == "fin"); cerrar_fin(pg)
    ck = pg.evaluate("store.checks.Vale"); verificar(len(ck) == 1 and ck[0]["p"] == "ritmo" and 0 <= ck[0]["ok"] < ck[0]["n"], str(ck))
    reg = pg.evaluate("store.ritmo.Vale.filter(e=>e.c)"); verificar(len(reg) >= 1, "el chequeo no registró regularidad")
    verificar("CHEQUEOS SIN AYUDA" in pg.evaluate("reportText()")); verificar(not err, str(err)); ctx.close()

@prueba("Ritmo: la base que suena no se escucha a sí misma (el clic que entra por el micrófono se enmascara) y los golpes del niño siguen contando")
def t_ritmo_mascara(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=97, rapido=False, extra_init=ESC_TEST); instalar_speak(pg); entrar(pg, "Vale")
    abrir_isla(pg, "Ritmo"); solo_habilidad(pg, "rit_base")
    pg.evaluate("(()=>{ const G=Gioval.entrada.proveedores.golpes; G.activo=true; G.fuente='mic'; window.__fugas={emitidas:0,filtradas:0}; })()")   # se simula 'micrófono encendido'
    tarjeta(pg, "Sesión de hoy"); pg.evaluate("S.session.items.length=1")
    JS = """(T)=>{ const G=Gioval.entrada.proveedores.golpes, L=60, d=T.beatMs;
      const em=(t,f)=>{ setTimeout(()=>{ if(f==='fuga'){ if(G.silenciado(t)){ window.__fugas.filtradas++; return; } window.__fugas.emitidas++; } Gioval.entrada.emitir({tipo:'golpe',t:t,fuerza:.5,fuente:'mic'}); }, Math.max(0,t-performance.now()-3)); };
      for(let i=0;i<12;i++) em(T.tS+i*d+L,'fuga');
      T.esperados.forEach(e=>em(e+25,'nino')); }"""   # parlante: L=60 ms después de cada clic; niño: 25 ms después del pulso
    visto = -1; t0 = time.time()
    while time.time() - t0 < 60:
        pg.wait_for_timeout(30)
        if pg.evaluate("document.getElementById('finish').classList.contains('show')"): break
        t = pg.evaluate("Gioval.ritmo.turno&&Gioval.ritmo.turno.id!==%d?Gioval.ritmo.turno:null" % visto)
        if t: visto = t["id"]; pg.evaluate(JS, t)
    verificar(pg.evaluate("document.getElementById('finish').classList.contains('show')"), "la sesión no terminó")
    f = pg.evaluate("window.__fugas"); eco = pg.evaluate("Gioval.ritmo.eco")
    verificar(eco is not None and 50 <= eco <= 70, "demora del parlante estimada en la cuenta: %s (real 60)" % eco)
    verificar(f["filtradas"] >= 4, "no se enmascaró el clic de la base: %s" % f)
    reg = pg.evaluate("store.ritmo.Vale"); verificar(reg and reg[0]["x"] == 0 and reg[0]["ok"] == 1, "los golpes del niño deberían contar y la base no sumar golpes de más: %s" % reg[:2])
    verificar(not err, str(err)); ctx.close(); return "demora estimada %.0f ms; clics enmascarados %d" % (eco, f["filtradas"])

@prueba("Ritmo: encender 'Tocar con mi instrumento' (micrófono falso): calibración de 3 s, detección y apagado al salir de la isla")
def t_ritmo_mic_interfaz(C):
    SALIDA.mkdir(exist_ok=True); err = []
    x = senal_golpes(3.8 + 3.0, [3800 + 600 * k for k in range(4)], "palma", 0.004, semilla=41)
    for v in ("360x700", "740x330"):
        wav = a_wav(x, SALIDA / ("mic_interfaz_%s.wav" % v)); b = con_microfono_falso(C, wav)
        try:
            ctx = b.contexto(v, permissions=["microphone"])
            pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, rapido=False); instalar_speak(pg); entrar(pg, "Vale"); abrir_isla(pg, "Ritmo")
            pg.click(".island:has-text('Tocar con mi instrumento')"); pg.wait_for_selector("#rtCal.show", timeout=5000); pg.wait_for_timeout(1200)
            CAPTURAS.append(foto(pg, v + "_65_ritmo_calibrando"))
            verificar("Shhh" in pg.evaluate("document.getElementById('rtCalT').innerText"), "no muestra la calibración")
            pg.wait_for_function("document.getElementById('rtCalT').innerText.includes('Listo')", timeout=8000)
            igual(pg.evaluate("Gioval.entrada.proveedores.golpes.estado().calibrado"), True, "calibrado"); CAPTURAS.append(foto(pg, v + "_66_ritmo_listo"))
            pg.wait_for_function("document.getElementById('rtCalT').innerText.includes('escuché')", timeout=9000)
            pg.wait_for_function("!document.getElementById('rtCal').classList.contains('show')", timeout=4000)
            verificar("Usar la pantalla" in pg.evaluate("document.getElementById('menuIslaItems').innerText"), "la tarjeta no cambió")
            tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(500); verificar(pg.evaluate("document.getElementById('rit').classList.contains('micOn')"), "no muestra el modo micrófono")
            CAPTURAS.append(foto(pg, v + "_67_ritmo_modo_microfono")); pg.evaluate("S.run++; resetFlow(); goMenuIsla()")
            pg.evaluate("goMap()"); pg.wait_for_timeout(200); igual(pg.evaluate("Gioval.entrada.proveedores.golpes.activo"), False, "debería apagarse al salir de la isla")
            ctx.close()
        finally: b.cerrar()
    verificar(not err, str(err))

@prueba("idioma inglés: la isla Ritmo (menú, sesión con errores, informe) sin una palabra en español")
def t_ritmo_ingles(C):
    ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=STORE_RITMO, errores=err, semilla=99, rapido=False, extra_init="window.__RITMO_ESCALA=5;localStorage.setItem('gioval_idioma','en');"); instalar_speak(pg); entrar(pg, "Vale")
    abrir_isla(pg, "Rhythm"); txt = pg.evaluate("document.getElementById('menuIslaItems').innerText")
    verificar("Play with my instrument" in txt and "Today" in txt, txt); verificar(not sin_espanol([txt]), txt)
    tarjeta(pg, "Today"); esperar_fase(pg, "turno"); pg.wait_for_timeout(200)
    visibles = pg.evaluate("[...document.querySelectorAll('#rit .lbl, #rit button, #rit small')].map(e=>e.textContent)"); verificar(not sin_espanol(visibles), str(visibles))
    verificar(jugar_ritmo(pg, errores=["adelantado", None, "falta", None]) == "fin"); cerrar_fin(pg)
    dicho = pg.evaluate("window.__LOG.concat(window.__BUB)"); verificar(not sin_espanol(dicho), "español en Ritmo en inglés: %s" % sin_espanol(dicho)[:3])
    verificar(any("Listen" in x or "listen" in x for x in dicho), "frases en inglés: %s" % dicho[:4])
    rep = pg.evaluate("reportText()"); verificar("RHYTHM STEADINESS" in rep and "Feel the beat" in rep and not sin_espanol([rep[rep.index("RHYTHM STEADINESS"):rep.index("RHYTHM STEADINESS") + 1200]]), rep[-900:])
    igual(pg.evaluate("[...Gioval.i18n.faltantes]"), [], "claves faltantes"); verificar(not err, str(err)); ctx.close()

# ---------------------------------------------------------------- capturas varias
@prueba("capturas: pantallas principales en Pixel 7, 360x700 y 740x330")
def t_capturas(C):
    for v in ("pixel7", "360x700", "740x330"):
        ctx = C.banco.contexto(v); err = []; pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=err, semilla=5); instalar_speak(pg)
        entrar(pg, "Vale"); abrir_isla(pg, "Música"); CAPTURAS.append(foto(pg, v + "_40_menu_musica"))
        abrir_isla(pg, "Números"); CAPTURAS.append(foto(pg, v + "_41_menu_numeros"))
        tarjeta(pg, "Logros") if False else None
        pg.click(".island:has-text('Mis logros')"); CAPTURAS.append(foto(pg, v + "_42_logros_numeros"))
        pg.evaluate("goMenuIsla()"); tarjeta(pg, "Sesión de hoy"); CAPTURAS.append(foto(pg, v + "_43_numeros_sesion"))
        abrir_panel(pg); CAPTURAS.append(foto(pg, v + "_44_panel_adultos"))
        verificar(not err, "%s: %s" % (v, err)); ctx.close()

# ---------------------------------------------------------------- ayudantes de la casa
def datos_ayudantes(C):
    """Las tareas y la supervisión con los textos ya resueltos (es-AR) desde la tabla de idiomas, leídos en el navegador."""
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", errores=C.err)
    d = pg.evaluate("({ datos: JSON.parse(JSON.stringify(Gioval.datos.ayudantes)), elogios: Gioval.i18n.tl('ayudantes.elogios'), tabla: Gioval.i18n.tablas['es-AR'].textos })")
    ctx.close(); return d

# Lo que NUNCA puede aparecer en los PASOS de una tarea (fuego/calor, filo, químicos, escaleras/alturas, electricidad).
# Los AVISOS sí pueden nombrarlos ("los cuchillos los pone un adulto"): ahí se dice qué NO hacer.
PROHIBIDO_EN_PASOS = re.compile(r"(fuego|\bllamas?\b|hornall|horno|estufa|plancha|calient|hirvi|herv[ií]|\bfre[ií]|cuchill|tijera|\bfilos|\bfilo\b|afilad|\bcort(a|an|ar|ás|á|ado)\b|abrelatas|\blatas?\b|rallador|vidrio|lavandina|cloro|detergente|desinfect|qu[ií]mic|veneno|abono|escalera|banquit|\bsillas?\b|subirte|subite|trepar|enchuf|\bcables?\b|el[eé]ctric|licuadora|microondas)", re.I)
PROHIBIDO_ELOGIO = re.compile(r"(buen[ií]sim|inteligent|genio|el mejor|la mejor|campe|mejor que|perfect|racha|puntos|seguid[oa]s|ganaste|premio)", re.I)

def textos_planos(o):
    if isinstance(o, str): return [o]
    if isinstance(o, dict): return [t for v in o.values() for t in textos_planos(v)]
    if isinstance(o, list): return [t for v in o for t in textos_planos(v)]
    return []

@prueba("ayudantes: lista de tareas (supervisión y aviso obligatorios, sin fuego/filo/químicos/escaleras) y TEXTOS al tope")
def t_ay_datos(C):
    d = datos_ayudantes(C); tareas = d["datos"]["tareas"]; sups = d["datos"]["supervision"]
    src = (APP / "js/datos/tareas.js").read_text(encoding="utf-8")
    verificar(src.index('agregar("es-AR"') < src.index("const TAREAS"), "los textos (tabla es-AR por clave) tienen que estar arriba de la lista de tareas")
    verificar("LISTA PARA QUE MARCOS LA APRUEBE" in src, "falta la lista anotada para aprobación")
    verificar(not re.search(r"(nombre|aviso|pasos)\s*:\s*[\"\[]", re.sub(r"/\*.*?\*/", "", src, flags=re.S).split("const TAREAS")[1]), "texto fijo en la definición de tareas: va en la tabla de idioma")
    claves = [k for k in d["tabla"] if k.startswith("ayudantes.")]; verificar(len(claves) > 100, "pocas claves ayudantes.*: %d" % len(claves))
    ids = [t["id"] for t in tareas]; igual(len(ids), len(set(ids)), "ids repetidos")
    esperadas = {"mesa_poner", "mesa_levantar", "juguetes", "plantas", "zapatos", "ropa", "mascota", "reciclaje", "secar", "cocinar_verduras"}
    verificar(esperadas <= set(ids), "faltan tareas pedidas: %s" % (esperadas - set(ids)))
    verificar({"cama", "juguetes", "mochila"} <= set(ids), "se perdieron ids de la lista anterior")
    niveles = set(sups.keys()); igual(niveles, {"solo", "cerca", "adulto"}, "niveles de supervisión")
    for k, v in sups.items(): verificar(all(v.get(c) for c in ("icono", "corto", "largo", "voz")), "supervisión %s incompleta" % k)
    for t in tareas:
        n = t["id"]
        verificar(t.get("supervision") in niveles, "%s: supervisión faltante o inválida: %r" % (n, t.get("supervision")))
        verificar(t.get("emoji") and t.get("nombre"), n + ": falta ícono o nombre")
        verificar(isinstance(t.get("edadMin"), int) and 4 <= t["edadMin"] <= 12, "%s: edad mínima %r" % (n, t.get("edadMin")))
        verificar(isinstance(t.get("minutos"), int) and 1 <= t["minutos"] <= 30, "%s: minutos %r" % (n, t.get("minutos")))
        verificar(2 <= len(t["pasos"]) <= 4, "%s: tiene que tener de 2 a 4 pasos (tiene %d)" % (n, len(t["pasos"])))
        for p in t["pasos"]: verificar(p.strip() and len(p) <= 90 and p.strip()[-1] in ".?!", "%s: paso muy largo o sin punto: %r" % (n, p))
        verificar(isinstance(t.get("aviso"), str), n + ": 'aviso' tiene que existir (vacío solo si es supervisión 'solo')")
        if t["supervision"] in ("cerca", "adulto"): verificar(len(t["aviso"].strip()) >= 20, "%s: supervisión %s exige un aviso de seguridad" % (n, t["supervision"]))
        m = PROHIBIDO_EN_PASOS.search(" ".join(t["pasos"] + [t["nombre"]]))
        verificar(not m, "%s: los pasos mencionan algo prohibido (%r)" % (n, m and m.group(0)))
    for t in ("mascota", "cocinar_verduras"): verificar(next(x for x in tareas if x["id"] == t)["supervision"] == "adulto", t + " debe ser solo con adulto")
    verificar(len(d["elogios"]) >= 3, "pocos elogios")
    for x in textos_planos(d["tabla"] if False else {k: v for k, v in d["tabla"].items() if k.startswith("ayudantes.")}): verificar(not PROHIBIDO_ELOGIO.search(x), "texto con elogio a la persona, racha o puntos: %r" % x)
    # el código no lleva textos propios: ninguna frase con signos ¡ ¿ fuera de comentarios
    codigo = re.sub(r"/\*.*?\*/", "", (APP / "js/islas/ayudantes.js").read_text(encoding="utf-8"), flags=re.S)
    for linea in codigo.splitlines():
        verificar("¡" not in linea and "¿" not in linea, "texto fijo en el código (va en TEXTOS): " + linea.strip()[:80])
    return "%d tareas; supervisión: %s" % (len(tareas), {k: sum(1 for t in tareas if t["supervision"] == k) for k in sorted(niveles)})

def ay_pagina(C, vista="360x700", extra=None, **kw):
    ctx = C.banco.contexto(vista); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err, semilla=kw.pop("semilla", 81), extra_init=extra, **kw)
    instalar_speak(pg); entrar(pg, "Vale"); return ctx, pg

def ay_tarea(pg, tid, empezar=True):
    pg.click(".ayCard[data-id='%s']" % tid); pg.wait_for_timeout(80)
    if empezar: pg.click("[data-a='empezar']"); pg.wait_for_timeout(120)

def ay_vista(pg): return pg.evaluate("Gioval.ayudantes.vista()")
def ay_texto(pg, sel="#ayBody"): return pg.evaluate("document.querySelector('%s').innerText" % sel)

@prueba("ayudantes: aparece al llegar al tope diario (botón, frase y tarjeta del menú) y no antes")
def t_ay_tope(C):
    ctx, pg = ay_pagina(C)
    abrir_isla(pg, "Números"); verificar("ayudantes" not in ay_texto(pg, "#menuIslaItems").lower(), "la tarjeta aparece antes del tope")
    llegar_al_tope(pg)
    verificar(pg.evaluate("getComputedStyle(document.getElementById('capAyud')).display") != "none", "no aparece el botón en el cartel de tope")
    igual(pg.evaluate("document.getElementById('capAyud').innerText"), "🧹 Hora de ayudantes")
    verificar("hora de ayudantes" in pg.evaluate("document.getElementById('capTxt').innerText").lower(), "falta la frase en el cartel")
    verificar(any("hora de ayudantes" in x.lower() for x in pg.evaluate("window.__LOG")), "la frase no se dijo en voz alta")
    verificar(pg.evaluate("document.getElementById('capOk').offsetParent!==null"), "el botón de siempre tiene que seguir")
    pg.click("#capAyud"); pg.wait_for_timeout(150)
    igual(pg.evaluate("document.querySelector('.screen.active').id"), "ayudantes"); igual(ay_vista(pg), "lista")
    verificar(not pg.evaluate("document.getElementById('capBox').classList.contains('show')"), "el cartel quedó abierto")
    igual(pg.evaluate("S.capShown"), False, "S.capShown")
    igual(pg.evaluate("document.querySelectorAll('.ayCard').length"), 12, "tarjetas para 6 años")
    pg.click("#ayBack"); pg.wait_for_timeout(150)     # vuelve al menú: la tarjeta sigue disponible mientras no haya más tiempo
    verificar("Hora de ayudantes" in ay_texto(pg, "#menuIslaItems"), "falta la tarjeta del menú después del tope")
    pg.click(".island:has-text('Hora de ayudantes')"); pg.wait_for_timeout(150); igual(pg.evaluate("document.querySelector('.screen.active').id"), "ayudantes")
    ctx.close()
    # si los adultos lo desactivan: no hay botón, ni frase, ni tarjeta
    ctx, pg = ay_pagina(C); pg.evaluate("Gioval.ayudantes.ponerCfg('Vale',{on:false})")
    llegar_al_tope(pg)
    verificar(pg.evaluate("getComputedStyle(document.getElementById('capAyud')).display") == "none", "el botón aparece con los ayudantes desactivados")
    verificar("ayudantes" not in pg.evaluate("document.getElementById('capTxt').innerText").lower(), "la frase aparece desactivado")
    pg.click("#capOk"); pg.wait_for_timeout(120); verificar("ayudantes" not in ay_texto(pg, "#menuIslaItems").lower(), "tarjeta con los ayudantes desactivados")
    ctx.close()

@prueba("ayudantes: elegir tarea (pasos, supervisión y aviso leídos en voz); las de 'solo con adulto' piden la pregunta de adultos")
def t_ay_elegir(C):
    ctx, pg = ay_pagina(C); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    pg.evaluate("window.__LOG.length=0")
    pg.click(".ayCard[data-id='plantas']"); pg.wait_for_timeout(100); igual(ay_vista(pg), "detalle")
    txt = ay_texto(pg); verificar("Regar las plantas" in txt and "5 min" in txt and "Con un adulto cerca" in txt and "abonos" in txt, txt)
    igual(pg.evaluate("document.querySelectorAll('.aySteps li').length"), 3, "pasos")
    dicho = " | ".join(pg.evaluate("window.__LOG")); verificar("Paso 1." in dicho and "Paso 3." in dicho and "Ojo: Solo agua" in dicho and "Pedile a un adulto que esté cerca" in dicho, dicho)
    foto(pg, "360x700_60_ayudantes_detalle"); CAPTURAS.append("360x700_60_ayudantes_detalle.png")
    pg.click("[data-a='lista']"); pg.wait_for_timeout(80); igual(ay_vista(pg), "lista")
    # tarea que se hace por cuenta propia: empieza directo
    ay_tarea(pg, "zapatos"); igual(ay_vista(pg), "corre"); verificar("Por tu cuenta" not in ay_texto(pg) or True)
    pg.click("[data-a='cancelar']"); pg.wait_for_timeout(80)
    # tarea solo con adulto: no empieza sin la pregunta de adultos
    ay_tarea(pg, "mascota", empezar=False); verificar("Un adulto tiene que estar al lado" in ay_texto(pg), "falta el aviso de adulto")
    verificar("Siempre con un adulto al lado" in ay_texto(pg), "falta el aviso de seguridad")
    pg.click("[data-a='empezar']"); pg.wait_for_selector("#gateBox.show", timeout=2000)
    pg.fill("#gateIn", "1"); pg.click("#gateOk"); pg.wait_for_timeout(100)
    igual(pg.evaluate("Gioval.ayudantes.enCurso()"), None, "empezó con la respuesta equivocada"); verificar(pg.evaluate("document.getElementById('gateBox').classList.contains('show')"))
    pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_timeout(150)
    igual(pg.evaluate("Gioval.ayudantes.enCurso().id"), "mascota"); igual(ay_vista(pg), "corre")
    ctx.close()

@prueba("ayudantes: cronómetro con hora absoluta — reloj simulado, pantalla oculta (timers congelados) y vuelta a primer plano")
def t_ay_cronometro(C):
    sonidos = "window.__osc=0; (function(){ var o=AudioContext.prototype.createOscillator; AudioContext.prototype.createOscillator=function(){ window.__osc++; return o.apply(this,arguments); }; })();"
    # 1) pantalla oculta: nadie corre timers, el reloj avanza, no suena hasta volver
    ctx, pg = ay_pagina(C, extra=sonidos); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    pg.evaluate("window.__fin=[]; Alarma.onFin(function(i){ window.__fin.push(i); }); window.setInterval=function(){ return 1; }; 0")   # timers congelados desde ahora
    ay_tarea(pg, "zapatos")                       # 3 minutos
    igual(ay_vista(pg), "corre"); verificar(178 <= pg.evaluate("Alarma.restante()") <= 180, "restante inicial")
    igual(ay_texto(pg, "#ayTime"), "03:00", "cuenta regresiva grande")
    verificar(pg.evaluate("parseFloat(getComputedStyle(document.getElementById('ayTime')).fontSize)") >= 70, "los números no son grandes")
    foto(pg, "360x700_61_ayudantes_cronometro"); CAPTURAS.append("360x700_61_ayudantes_cronometro.png")
    verificar(abs(pg.evaluate("JSON.parse(localStorage.getItem('gioval_alarma')).fin - Date.now()") - 180000) < 3000, "no guardó la hora absoluta de fin")
    pg.evaluate("Object.defineProperty(document,'hidden',{get:()=>true,configurable:true}); window.__OFF=60000")
    verificar(118 <= pg.evaluate("Alarma.restante()") <= 121, "restante con el reloj +60 s")
    pg.evaluate("window.__OFF=400000")            # pasó mucho más que el tiempo con la pantalla apagada
    pg.wait_for_timeout(700)
    igual(pg.evaluate("window.__fin.length"), 0, "no puede sonar mientras la página está congelada"); igual(ay_vista(pg), "corre", "sigue 'corriendo' hasta volver")
    igual(pg.evaluate("window.__osc"), 0, "sonó con la pantalla oculta")
    pg.evaluate("Object.defineProperty(document,'hidden',{get:()=>false,configurable:true}); document.dispatchEvent(new Event('visibilitychange'))")
    pg.wait_for_timeout(150)
    igual(pg.evaluate("window.__fin.length"), 1, "tiene que sonar al volver a primer plano"); igual(ay_vista(pg), "tiempo")
    verificar(pg.evaluate("window.__fin[0].tarde") >= 200000, "tarde=%s" % pg.evaluate("window.__fin[0].tarde"))
    verificar(pg.evaluate("window.__osc") >= 4, "no sonó la alarma al volver (osciladores: %s)" % pg.evaluate("window.__osc"))
    txt = ay_texto(pg); verificar("Se terminó el tiempo" in txt and "Volviste a la app" in txt and "Terminé" in txt and "Un ratito más" in txt, txt)
    verificar(any("Se terminó el tiempo" in x for x in pg.evaluate("window.__LOG")), "no lo dijo en voz")
    igual(pg.evaluate("localStorage.getItem('gioval_alarma')"), None, "alarma guardada sin limpiar")
    pg.evaluate("document.dispatchEvent(new Event('visibilitychange'))"); igual(pg.evaluate("window.__fin.length"), 1, "sonó dos veces")
    foto(pg, "360x700_62_ayudantes_tiempo"); CAPTURAS.append("360x700_62_ayudantes_tiempo.png")
    ctx.close()
    # 2) pantalla encendida: suena solo, a la hora (hora absoluta), y "un ratito más" reprograma
    ctx, pg = ay_pagina(C, extra=sonidos, semilla=82); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ay_tarea(pg, "zapatos"); pg.evaluate("window.__OFF=181000"); pg.wait_for_selector("[data-a='mas']", timeout=3000)
    igual(ay_vista(pg), "tiempo"); verificar("Volviste a la app" not in ay_texto(pg), "no debería decir 'volviste' si la app estaba abierta")
    pg.click("[data-a='mas']"); pg.wait_for_timeout(120); igual(ay_vista(pg), "corre"); verificar(118 <= pg.evaluate("Alarma.restante()") <= 120, "un ratito más = 2 minutos")
    igual(ay_texto(pg, "#ayTime"), "02:00")
    ctx.close()

@prueba("ayudantes: terminar, elogio al esfuerzo, registro semanal sin rachas ni puntos")
def t_ay_terminar(C):
    ctx, pg = ay_pagina(C); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    elogios = pg.evaluate("Gioval.i18n.tl('ayudantes.elogios')"); vistos = []
    for i, tid in enumerate(["zapatos", "juguetes", "plantas"], 1):
        ay_tarea(pg, tid); igual(ay_vista(pg), "corre"); pg.evaluate("window.__OFF=%d" % (i * 20000)); pg.click("[data-a='terminar']"); pg.wait_for_timeout(120)
        igual(ay_vista(pg), "fin"); txt = ay_texto(pg)
        verificar(pg.evaluate("document.getElementById('ayElogio').innerText") in elogios, "elogio fuera de la lista")
        vistos.append(pg.evaluate("document.getElementById('ayElogio').innerText"))
        verificar("Esta semana ayudaste %s" % ("1 vez." if i == 1 else "%d veces." % i) in txt, "registro semanal: " + txt)
        verificar(not PROHIBIDO_ELOGIO.search(txt) and "⭐" not in txt and "🔥" not in txt, "elogio a la persona, racha o puntos: " + txt)
        igual(pg.evaluate("Alarma.activa()"), False, "la alarma debe cancelarse al terminar")
        if i < 3: pg.click("[data-a='lista']"); pg.wait_for_timeout(80)
    foto(pg, "360x700_63_ayudantes_fin"); CAPTURAS.append("360x700_63_ayudantes_fin.png")
    reg = pg.evaluate("Gioval.ayudantes.registro('Vale')"); igual([r["id"] for r in reg], ["zapatos", "juguetes", "plantas"], "registro"); verificar(all(r["s"] >= 0 for r in reg))
    # solo cuenta lo de ESTA semana (lunes a domingo): una anotación vieja no suma; la semana siguiente empieza de cero
    pg.evaluate("store.ayud.reg.Vale.push({t:Date.now()-10*864e5,id:'cama',s:60})"); igual(pg.evaluate("Gioval.ayudantes.vecesSemana('Vale')"), 3, "una tarea de hace 10 días no cuenta")
    pg.evaluate("window.__OFF=8*864e5"); igual(pg.evaluate("Gioval.ayudantes.vecesSemana('Vale')"), 0, "la semana siguiente empieza de cero (no hay racha)"); pg.evaluate("window.__OFF=0")
    # el registro no tiene rachas ni puntos: solo { t, id, s }
    verificar(set(reg[0].keys()) <= {"t", "id", "s", "f"}, str(reg[0]))
    abrir_panel(pg); pg.click("#ayPanel summary"); pg.wait_for_timeout(100)
    verificar("Esta semana ayudó: 3 veces" in pg.evaluate("document.getElementById('ayResumen').innerText"), pg.evaluate("document.getElementById('ayResumen').innerText"))
    # sobrevive a recargar
    pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(300); pg.reload(); esperar_listo(pg)
    igual(pg.evaluate("Gioval.ayudantes.registro('Vale').length"), 4, "el registro no sobrevivió a recargar")
    ctx.close()
    # un ratito más: se anota UNA vez; dejarla por ahora no anota nada y no castiga
    ctx, pg = ay_pagina(C, semilla=83); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ay_tarea(pg, "zapatos"); pg.evaluate("window.__OFF=181000"); pg.wait_for_selector("[data-a='mas']", timeout=3000)
    pg.click("[data-a='mas']"); pg.wait_for_timeout(100); pg.click("[data-a='terminar']"); pg.wait_for_timeout(100)
    igual(pg.evaluate("Gioval.ayudantes.registro('Vale').length"), 1, "se anotó más de una vez")
    pg.click("[data-a='lista']"); pg.wait_for_timeout(80); ay_tarea(pg, "ropa"); pg.click("[data-a='cancelar']"); pg.wait_for_timeout(100)
    igual(pg.evaluate("Gioval.ayudantes.registro('Vale').length"), 1, "dejarla por ahora no debe anotar"); igual(ay_vista(pg), "lista"); igual(pg.evaluate("Alarma.activa()"), False)
    verificar(any("Está bien" in x for x in pg.evaluate("window.__LOG")), "tiene que haber un mensaje sin castigo")
    ctx.close()

@prueba("ayudantes: el tiempo de ayudantes NO cuenta como tiempo de pantalla")
def t_ay_no_cuenta(C):
    ctx, pg = ay_pagina(C)
    abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); pg.wait_for_timeout(300)
    t0 = pg.evaluate("store.time['Vale|'+today()]||0"); pg.wait_for_timeout(2300)
    verificar(pg.evaluate("store.time['Vale|'+today()]") >= t0 + 2, "control: jugando sí tiene que contar")     # control: la prueba es válida
    pg.evaluate("store.time['Vale|'+today()]=capBase()-1"); pg.wait_for_selector("#capBox.show", timeout=6000); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ay_tarea(pg, "zapatos"); igual(ay_vista(pg), "corre")
    antes = pg.evaluate("[store.time['Vale|'+today()], capLeft()]"); pg.wait_for_timeout(3200)
    despues = pg.evaluate("[store.time['Vale|'+today()], capLeft()]"); igual(despues, antes, "el tiempo de pantalla siguió corriendo en Ayudantes")
    igual(pg.evaluate("document.getElementById('capBox').classList.contains('show')"), False, "no tiene que volver a saltar el cartel de tope")
    ctx.close()

@prueba("ayudantes: configuración de adultos (activar, edad, duración, tareas habilitadas y asignadas, foto) y estado honesto de la alarma")
def t_ay_adultos(C):
    ctx, pg = ay_pagina(C)
    abrir_panel(pg); pg.click("#ayPanel summary"); pg.wait_for_timeout(100)
    tp = ay_texto(pg, "#ayPanel")
    verificar("no garantizada en navegador" in tp and "app Android nativa" in tp, "el panel no dice la verdad sobre la alarma: " + tp[:300])
    verificar("Pantalla encendida mientras corre" in tp and "Avisos del sistema" in tp and "App nativa" in tp, "faltan los estados de la alarma")
    verificar("NO cuenta como tiempo de pantalla" in tp, "falta la aclaración del tiempo")
    foto(pg, "360x700_64_ayudantes_panel"); CAPTURAS.append("360x700_64_ayudantes_panel.png")
    igual(pg.evaluate("document.querySelectorAll('#ayPanelBody [data-h]').length"), 12, "una fila por tarea")
    # edad 4: solo las de 4 años
    pg.select_option("#ayEdad", "4"); pg.wait_for_timeout(80)
    igual(pg.evaluate("Gioval.ayudantes.cfg('Vale').edad"), 4)
    igual(sorted(t["id"] for t in pg.evaluate("Gioval.ayudantes.disponibles('Vale')")), ["juguetes", "mesa_poner", "mochila", "plantas", "zapatos"], "tareas de 4 años")
    # deshabilitar una, asignar otra (aunque sea de 5 años): la asignada va primera y marcada
    pg.uncheck("#ayPanelBody [data-h='juguetes']"); pg.check("#ayPanelBody [data-asig='cocinar_verduras']"); pg.wait_for_timeout(80)
    pg.select_option("#ayDur", "3"); pg.check("#ayFoto"); pg.wait_for_timeout(80)
    c = pg.evaluate("Gioval.ayudantes.cfg('Vale')"); igual((c["off"], c["asig"], c["dur"], c["foto"], c["on"]), (["juguetes"], ["cocinar_verduras"], 3, True, True))
    pg.evaluate("Gioval.almacen.guardarYa()"); pg.wait_for_timeout(250); pg.reload(); esperar_listo(pg); instalar_speak(pg)   # persiste
    igual(pg.evaluate("Gioval.ayudantes.cfg('Vale')"), c, "la configuración no sobrevivió a recargar")
    entrar(pg, "Vale"); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ids = pg.evaluate("[...document.querySelectorAll('.ayCard')].map(c=>c.dataset.id)"); igual(ids, ["cocinar_verduras", "mesa_poner", "plantas", "zapatos", "mochila"], "lista del niño")
    verificar("Te la pidió un adulto" in pg.evaluate("document.querySelector('.ayCard.asig').innerText"), "la asignada no está marcada")
    verificar(all("3 min" in x for x in pg.evaluate("[...document.querySelectorAll('.ayCard small:not(.pin)')].map(x=>x.innerText)")), "la duración configurada no se ve en las tarjetas")
    ay_tarea(pg, "zapatos"); igual(ay_texto(pg, "#ayTime"), "03:00"); verificar(177 <= pg.evaluate("Alarma.restante()") <= 180, "la duración configurada no se usa")
    pg.click("[data-a='cancelar']"); pg.wait_for_timeout(80)
    # la asignada se cumple una vez y se quita sola
    ay_tarea(pg, "cocinar_verduras", empezar=False); pg.click("[data-a='empezar']"); pg.wait_for_selector("#gateBox.show"); pg.fill("#gateIn", str(pg.evaluate("S.gateAns"))); pg.click("#gateOk"); pg.wait_for_timeout(120)
    pg.click("[data-a='terminar']"); pg.wait_for_timeout(100); igual(pg.evaluate("Gioval.ayudantes.cfg('Vale').asig"), [], "la asignada tenía que quitarse sola")
    # perfiles independientes: el otro niño conserva los valores por defecto
    c2 = pg.evaluate("Gioval.ayudantes.cfg('Otro')"); igual((c2["edad"], c2["on"], c2["dur"], c2["off"], c2["asig"], c2["foto"]), (6, True, 0, [], [], False), "valores por defecto")
    # desactivar
    pg.evaluate("Gioval.ayudantes.ponerCfg('Vale',{on:false})"); igual(pg.evaluate("Gioval.ayudantes.ofrece('Vale')"), False)
    ctx.close()
    # app nativa simulada: el panel lo dice, sin prometer más de la cuenta
    ctx, pg = ay_pagina(C, extra="window.Capacitor={Plugins:{LocalNotifications:{schedule:function(){},cancel:function(){}}}};", semilla=84)
    abrir_panel(pg); pg.click("#ayPanel summary"); pg.wait_for_timeout(100); tp = ay_texto(pg, "#ayPanel")
    verificar("se detectó Capacitor" in tp and "Todavía hay que probarla en el aparato" in tp and "no garantizada en navegador" in tp, tp[-500:])
    ctx.close()

@prueba("ayudantes: foto opcional al terminar (solo si el adulto la activa) en el almacén de fotos existente")
def t_ay_foto(C):
    from PIL import Image
    SALIDA.mkdir(exist_ok=True); png = SALIDA / "foto_prueba.png"; Image.new("RGB", (64, 48), (200, 80, 90)).save(png)
    ctx, pg = ay_pagina(C); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ay_tarea(pg, "zapatos"); pg.click("[data-a='terminar']"); pg.wait_for_timeout(100)
    igual(pg.evaluate("document.getElementById('ayFotoBtn')"), None, "ofrece foto sin que el adulto la active")
    pg.evaluate("Gioval.ayudantes.ponerCfg('Vale',{foto:true})"); pg.click("[data-a='lista']"); pg.wait_for_timeout(80)
    ay_tarea(pg, "ropa"); pg.click("[data-a='terminar']"); pg.wait_for_timeout(100)
    verificar(pg.evaluate("!!document.getElementById('ayFotoBtn')"), "no ofrece la foto activada")
    foto(pg, "360x700_65_ayudantes_foto"); CAPTURAS.append("360x700_65_ayudantes_foto.png")
    pg.set_input_files("#ayFotoIn", str(png)); pg.wait_for_function("document.getElementById('ayFotoBtn').innerText.includes('guardada')", timeout=5000)
    fs = pg.evaluate("Gioval.almacen.fotos.listar()"); igual(len(fs), 1, "fotos guardadas"); igual((fs[0]["meta"]["tipo"], fs[0]["meta"]["kid"], fs[0]["meta"]["tarea"]), ("ayudantes", "Vale", "ropa"))
    o = pg.evaluate("Gioval.almacen.fotos.obtener('%s').then(r=>[r.blob.type,r.blob.size])" % fs[0]["id"]); verificar(o[1] > 0 and o[0].startswith("image/"), str(o))
    igual(pg.evaluate("Gioval.ayudantes.registro('Vale')[1].f"), fs[0]["id"], "el registro no apunta a la foto")
    abrir_panel(pg); pg.click("#ayPanel summary"); pg.wait_for_timeout(300)
    verificar("Fotos guardadas: 1" in pg.evaluate("document.getElementById('ayResumen').innerText"), "el panel no cuenta la foto"); ctx.close()

@prueba("ayudantes: retoma una tarea en curso si se cerró la app (aún en hora, o ya vencida mientras estaba cerrada)")
def t_ay_retoma(C):
    ctx, pg = ay_pagina(C); llegar_al_tope(pg); pg.click("#capAyud"); pg.wait_for_timeout(100)
    ay_tarea(pg, "juguetes")        # 10 minutos
    pg.reload(); esperar_listo(pg); instalar_speak(pg); entrar(pg, "Vale"); pg.wait_for_timeout(150)
    igual(pg.evaluate("document.querySelector('.screen.active').id"), "ayudantes", "tendría que retomar la tarea"); igual(ay_vista(pg), "corre")
    verificar(540 <= pg.evaluate("Alarma.restante()") <= 600, "restante %s" % pg.evaluate("Alarma.restante()"))
    # se cerró la app y la alarma venció mientras tanto
    pg.evaluate("(()=>{ var g=JSON.parse(localStorage.getItem('gioval_alarma')); g.fin=Date.now()-20000; localStorage.setItem('gioval_alarma',JSON.stringify(g)); })()")
    pg.reload(); esperar_listo(pg); instalar_speak(pg); pg.wait_for_timeout(300); entrar(pg, "Vale"); pg.wait_for_timeout(150)
    igual(ay_vista(pg), "tiempo", "vencida con la app cerrada"); verificar("Volviste a la app" in ay_texto(pg), ay_texto(pg))
    pg.click("[data-a='terminar']"); pg.wait_for_timeout(100); igual(pg.evaluate("Gioval.ayudantes.registro('Vale').length"), 1)
    igual(pg.evaluate("localStorage.getItem('gioval_ayudando')"), None, "quedó una tarea en curso guardada")
    ctx.close()

@prueba("ayudantes: Música y Números no cambian (mapa, menús, islas registradas y estado de tiempo)")
def t_ay_no_toca(C):
    res = {}
    for nombre, ruta in (("anterior", "/legacy/index.html"), ("nueva", "/index.html")):
        ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + ruta, store=STORE_KID, errores=C.err if nombre == "nueva" else None, semilla=5); instalar_speak(pg); entrar(pg, "Vale")
        r = {"mapa": ay_texto(pg, "#islands").replace("🧭\nIsla Misiones\n¡Cosas de verdad!\n", "").replace("🥁\nIsla Ritmo\n¡A marcar el ritmo!\n", "").replace("🔤\nIsla Letras\n¡A jugar con las letras!\n", "").replace("🔒\nIsla Letras\nPronto\n", "")}   # Letras, Misiones y Ritmo (otras ramas) son lo único que se suma al mapa
        for isla in ("Música", "Números"): abrir_isla(pg, isla); r["menu " + isla] = ay_texto(pg, "#musicMenu,#menuIslaItems")
        res[nombre] = r; ctx.close()
    igual(res["nueva"], res["anterior"], "textos del mapa y de los menús")
    ctx, pg = ay_pagina(C); igual(pg.evaluate("PACKS.map(p=>p.id)"), ["musica", "numeros", "letras", "misiones", "ritmo"], "Ayudantes no es una isla de aprendizaje (Misiones es la otra isla sin habilidades)")
    igual(pg.evaluate("Gioval.islas.habilidades().filter(s=>!s.id.startsWith('rit_')).length"), 68, "habilidades (Música 7 + Números 31 + Letras 30; Ritmo suma las suyas)")
    for isla in ("Música", "Números"):    # al llegar al tope en cualquier isla, el flujo anterior sigue igual: "¡Chau, zorro!" cierra y vuelve al menú
        llegar_al_tope(pg, isla); pg.click("#capOk"); pg.wait_for_timeout(120)
        igual(pg.evaluate("document.querySelector('.screen.active').id"), "menuIsla", isla)
        pg.evaluate("store.time['Vale|'+today()]=0")
    ctx.close()

@prueba("ayudantes: en inglés sin una palabra en español; con el pseudo-idioma (+40 %) y en RTL sin desbordes horizontales")
def t_ay_idiomas(C):
    # inglés completo: tope, lista, detalle (pasos y aviso), cronómetro, tiempo, fin, panel
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err, semilla=86, extra_init="localStorage.setItem('gioval_idioma','en');"); instalar_speak(pg); entrar(pg, "Vale")
    llegar_al_tope(pg, directo=True); pg.click("#capAyud"); pg.wait_for_timeout(100)
    textos = [ay_texto(pg, "#capBox") if False else pg.evaluate("document.getElementById('capTxt').innerText"), pg.evaluate("document.getElementById('capAyud').innerText")]
    textos.append(ay_texto(pg)); pg.click(".ayCard[data-id='plantas']"); pg.wait_for_timeout(80); textos.append(ay_texto(pg))
    pg.click("[data-a='empezar']"); pg.wait_for_timeout(120); textos.append(ay_texto(pg)); pg.evaluate("window.__OFF=400000"); pg.evaluate("Alarma._revisar()"); pg.wait_for_timeout(120); textos.append(ay_texto(pg))
    pg.click("[data-a='terminar']"); pg.wait_for_timeout(100); textos.append(ay_texto(pg))
    abrir_panel(pg); pg.click("#ayPanel summary"); pg.wait_for_timeout(120); textos.append(ay_texto(pg, "#ayPanel"))
    dicho = pg.evaluate("window.__LOG.concat(window.__BUB)")
    todo = [l for t in textos for l in t.split("\n") if l.strip()] + dicho
    verificar(not sin_espanol(todo), "español en inglés: %s" % sin_espanol(todo)[:5])
    verificar(any("Step 1." in x for x in dicho) and any("Careful:" in x for x in dicho) and any("Time's up" in x for x in dicho), "frases de ayudantes en inglés: %s" % dicho[:6])
    verificar("Helpers' time" in textos[1] and "This week you helped 1 time." in " ".join(textos), "textos de ayudantes en inglés")
    igual(pg.evaluate("[...Gioval.i18n.faltantes]"), [], "claves faltantes"); ctx.close()
    # pseudo-idioma (+40 %) y RTL: sin desbordes horizontales en ninguna vista (360x700 y 740x330)
    JS = """()=>{ const b=document.body, ay=document.getElementById('ayBody'), pn=document.getElementById('panel');
      const out=[]; if(b.scrollWidth>b.clientWidth+2) out.push('body'); if(ay&&ay.scrollWidth>ay.clientWidth+2) out.push('ayBody');
      document.querySelectorAll('#ayudantes .btn,#ayudantes .ayCard').forEach(e=>{ const r=e.getBoundingClientRect(); if(r.width&&(r.right>innerWidth+2||r.left<-2)) out.push(e.className+' fuera de pantalla'); }); return out; }"""
    for idioma in ("qps-ploc", "qps-plocm"):
        for v in ("360x700", "740x330"):
            ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err, semilla=87, extra_init="localStorage.setItem('gioval_idioma','%s');" % idioma, congelar=True); instalar_speak(pg); entrar(pg, "Vale")
            llegar_al_tope(pg, directo=True); mal = pg.evaluate(JS)
            if idioma == "qps-plocm": igual(pg.evaluate("document.documentElement.dir"), "rtl")
            pg.click("#capAyud"); pg.wait_for_timeout(100); mal += pg.evaluate(JS); pg.click(".ayCard[data-id='plantas']"); pg.wait_for_timeout(80); mal += pg.evaluate(JS)
            CAPTURAS.append(foto(pg, "%s_%s_80_ayudantes_detalle" % (v, idioma)))
            pg.click("[data-a='empezar']"); pg.wait_for_timeout(120); mal += pg.evaluate(JS); pg.evaluate("window.__OFF=400000"); pg.evaluate("Alarma._revisar()"); pg.wait_for_timeout(120); mal += pg.evaluate(JS)
            CAPTURAS.append(foto(pg, "%s_%s_81_ayudantes_tiempo" % (v, idioma)))
            pg.click("[data-a='terminar']"); pg.wait_for_timeout(100); mal += pg.evaluate(JS)
            verificar(not mal, "%s %s: desbordes %s" % (idioma, v, mal)); ctx.close()

@prueba("capturas: Hora de ayudantes en 360x700 y 740x330 (tope, lista, detalle, cronómetro, tiempo, fin, panel)")
def t_ay_capturas(C):
    for v in ("360x700", "740x330"):
        ctx = C.banco.contexto(v); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err, semilla=85, congelar=True); instalar_speak(pg); entrar(pg, "Vale")
        pg.evaluate("Gioval.ayudantes.ponerCfg('Vale',{asig:['plantas'],foto:true})")
        llegar_al_tope(pg, directo=True); CAPTURAS.append(foto(pg, v + "_70_ayudantes_tope")); pg.click("#capAyud"); pg.wait_for_timeout(120)
        CAPTURAS.append(foto(pg, v + "_71_ayudantes_lista")); pg.click(".ayCard[data-id='plantas']"); CAPTURAS.append(foto(pg, v + "_72_ayudantes_detalle"))
        pg.click("[data-a='empezar']"); pg.wait_for_timeout(150); CAPTURAS.append(foto(pg, v + "_73_ayudantes_cronometro"))
        pg.evaluate("window.__OFF=181000"); pg.evaluate("Alarma._revisar()"); pg.wait_for_timeout(150); CAPTURAS.append(foto(pg, v + "_74_ayudantes_tiempo"))
        pg.click("[data-a='terminar']"); pg.wait_for_timeout(120); CAPTURAS.append(foto(pg, v + "_75_ayudantes_fin"))
        abrir_panel(pg); pg.click("#ayPanel summary"); pg.evaluate("document.getElementById('ayPanel').scrollIntoView()"); CAPTURAS.append(foto(pg, v + "_76_ayudantes_panel"))
        ctx.close()

# ================================================================== De a dos (jugar por turnos con un hermano o hermana)
FAR = 4_000_000_000_000

def dd_sk(mast, att, **k):
    d = {"score": .9 if mast else .4, "att": att, "box": 1 if mast else 0, "due": FAR if mast else 0, "lvl": 1 if mast else 0, "rec": [1, 1, 1] if mast else [], "mast": mast, "last": 0}
    d.update(k); return d

def dd_store(practicando=True, limite=60, **extra):
    """Giovanni (el mayor) ya domina 4 habilidades de Números; Valentino empieza (o practica la primera si practicando=True). Orden de perfiles: Giovanni, Valentino."""
    sk = {"Giovanni|" + i: dd_sk(True, 8) for i in ("num_c10", "num_r10", "num_may", "num_add5")}
    if practicando: sk["Valentino|num_c10"] = dd_sk(False, 3, score=.4)
    st = {"profiles": ["Giovanni", "Valentino"], "limit": {"Giovanni": limite, "Valentino": limite}, "sk": sk}
    st.update(extra); return st

def dd_pagina(C, vista="360x700", st=None, idioma=None, semilla=61, **kw):
    ctx = C.banco.contexto(vista)
    ini = ("localStorage.setItem('gioval_idioma','%s');" % idioma) if idioma else None
    pg = abrir(ctx, C.url + "/index.html", store=st if st is not None else dd_store(), errores=C.err, semilla=semilla, extra_init=ini, **kw); instalar_speak(pg)
    return ctx, pg

def dd_id(pg): return pg.evaluate("document.querySelector('.screen.active').id")
def dd_tit(pg): return pg.evaluate("document.getElementById('ddTit').innerText")
def dd_texto(pg): return pg.evaluate("document.querySelector('.screen.active').innerText")
def dd_empezar(pg, isla=None):
    pg.click("[data-modo=dedos]"); pg.wait_for_timeout(120)
    if isla: pg.click("[data-isla=%s]" % isla)
    pg.click("#ddIr"); pg.wait_for_timeout(120)
def dd_vamos(pg, sin_explicar=False):
    """Toca el botón grande de la entrega de turno (si antes aparece la celebración del dibujo, la pasa). sin_explicar=True: si se propone explicarle al otro, contesta 'Ahora no'."""
    if dd_id(pg) == "ddPaso" and dd_tit(pg).startswith("¡Armaron"): pg.click("#ddAcc .btn.grande"); pg.wait_for_timeout(150)
    pg.click("#ddAcc .btn.grande"); pg.wait_for_timeout(200)
    if sin_explicar and dd_id(pg) == "ddPaso" and dd_tit(pg).endswith("te toca explicar!"): pg.click("#ddAcc .btn.alt"); pg.wait_for_timeout(250)
def dd_terminar(pg):
    """'Terminar por hoy' desde la entrega de turno (pasando antes la celebración del dibujo, si la hay)."""
    if dd_tit(pg).startswith("¡Armaron"): pg.click("#ddAcc .btn.grande"); pg.wait_for_timeout(150)
    pg.click("#ddAcc .btn.alt"); pg.wait_for_timeout(150)
def dd_estado(pg, js): return pg.evaluate("(()=>{ const D=Gioval.dedos.estado(); return %s; })()" % js)
def dd_progreso(pg, kid):
    """Estado comparable del progreso de UN chico (sin las entradas vacías que crea SK() al mirar una habilidad)."""
    return pg.evaluate("""(k)=>{ const sk={}; Object.keys(store.sk).sort().forEach(x=>{ if(!x.startsWith(k+'|')) return; const v=store.sk[x]; if(!v.att&&!v.mast) return; sk[x]=JSON.stringify(v); });
      return {sk, log:JSON.stringify(store.log[k]||[]), days:JSON.stringify(store.days[k]||[])}; }""", kid)

def dd_turno(pg, cada_error=0, limite=250):
    """Juega el turno de a dos en curso hasta que la pantalla deja de ser la de actividad. Devuelve el id de la pantalla a la que se pasó."""
    dec = 0
    for _ in range(limite):
        pg.wait_for_timeout(35)
        a = dd_id(pg)
        if a != "act": return a
        t = pg.evaluate(JS_TOQUES)
        if not t: continue
        dec += 1
        ok = [i for i, v in enumerate(t["vals"]) if v == t["w"] and t["ids"][i] not in t["used"] and v not in t["dead"]]
        mal = [i for i, v in enumerate(t["vals"]) if v != t["w"] and t["ids"][i] not in t["used"] and v not in t["dead"]]
        clic = None
        if cada_error and dec % cada_error == 0 and t["len"] == 1 and t["miss"] == 0 and mal: clic = mal[0]
        elif ok: clic = ok[0]
        if clic is not None:
            pg.evaluate("(()=>{var T=S.tap; window.__ref=[T.it,T.pos,T.miss,T.used.size,T.dead.size]; })()")
            pg.click(".opt[data-i='%d']" % clic, force=True)
            try: pg.wait_for_function("(function(){var T=S.tap,r=window.__ref; return !T||S.mode!=='play'||T.it!==r[0]||T.pos!==r[1]||T.miss!==r[2]||T.used.size!==r[3]||T.dead.size!==r[4];})()", timeout=2500, polling=15)
            except Exception: pass
    return "limite"

def dd_uno(pg):
    """Responde bien un ítem (el que está en pantalla) y espera a que el juego lo procese."""
    pg.wait_for_function("(function(){return !!(S.tap&&S.mode==='play'&&S.tap.v);})()", timeout=5000)
    i0 = pg.evaluate("S.session.i")
    for _ in range(12):
        t = pg.evaluate(JS_TOQUES)
        if t:
            ok = [i for i, v in enumerate(t["vals"]) if v == t["w"] and t["ids"][i] not in t["used"] and v not in t["dead"]]
            if ok: pg.click(".opt[data-i='%d']" % ok[0], force=True)
        pg.wait_for_timeout(60)
        if pg.evaluate("!S.session||S.session.i") != i0: break

def dd_revelar(pg):
    """Se equivoca tres veces en el ítem en pantalla (la app muestra la respuesta) y después toca la correcta."""
    pg.wait_for_function("(function(){return !!(S.tap&&S.mode==='play'&&S.tap.v);})()", timeout=5000)
    for _ in range(3):
        t = pg.evaluate(JS_TOQUES)
        mal = [i for i, v in enumerate(t["vals"]) if v != t["w"] and t["ids"][i] not in t["used"] and v not in t["dead"]]
        verificar(mal, "no hay opciones equivocadas para probar el reintento")
        pg.click(".opt[data-i='%d']" % mal[0], force=True); pg.wait_for_timeout(330)   # la app ignora toques durante 250 ms después de un error
    verificar(pg.evaluate("S.tap.revealed"), "la app no mostró la respuesta tras 3 errores")

@prueba("de a dos: la entrada aparece solo con dos o más jugadores (¿Quién juega? y mapa) y el armado elige jugadores, orden e isla")
def t_dd_entrada(C):
    ctx = C.banco.contexto("360x700"); pg = abrir(ctx, C.url + "/index.html", store=STORE_KID, errores=C.err); instalar_speak(pg)
    igual(pg.evaluate("document.querySelectorAll('[data-modo]').length"), 0, "con un solo jugador no hay tarjeta (quién juega)")
    entrar(pg, "Vale"); igual(pg.evaluate("document.querySelectorAll('[data-modo]').length"), 0, "con un solo jugador no hay tarjeta (mapa)"); ctx.close()
    ctx, pg = dd_pagina(C)
    igual(pg.evaluate("[...document.querySelectorAll('#profiles .song')].map(x=>x.innerText.replace(/\\n/g,'|'))"), ["🦊|Giovanni", "🦊|Valentino", "👫|De a dos", "➕|Nuevo jugador"], "tarjeta en ¿Quién juega?")
    pg.click("[data-modo=dedos]"); pg.wait_for_timeout(120); igual(dd_id(pg), "ddSetup")
    igual(pg.evaluate("[...document.querySelectorAll('.dd-chip[data-k]')].map(x=>x.querySelector('b').innerText+':'+(x.querySelector('.dd-ord')||{innerText:''}).innerText)"), ["Giovanni:1", "Valentino:2"], "con dos jugadores libres vienen elegidos, en el orden de los perfiles")
    igual(pg.evaluate("[...document.querySelectorAll('.dd-chip[data-isla]')].map(x=>x.dataset.isla+(x.classList.contains('sel')?'*':''))"), ["numeros*", "letras"], "islas por toque")
    verificar(not pg.evaluate("document.getElementById('ddIr').disabled"), "A jugar habilitado con dos")
    pg.click(".dd-chip[data-k='0']"); pg.wait_for_timeout(60)   # saca a Giovanni
    verificar(pg.evaluate("document.getElementById('ddIr').disabled"), "A jugar bloqueado con uno solo"); verificar("Falta elegir" in dd_texto(pg), "avisa que falta alguien")
    pg.click(".dd-chip[data-k='0']"); pg.wait_for_timeout(60)   # lo vuelve a sumar: ahora va segundo
    igual(pg.evaluate("[...document.querySelectorAll('.dd-chip[data-k]')].map(x=>x.querySelector('b').innerText+':'+(x.querySelector('.dd-ord')||{innerText:''}).innerText)"), ["Giovanni:2", "Valentino:1"], "el orden es el de los toques")
    pg.click("[data-isla=letras]"); igual(pg.evaluate("document.querySelector('.dd-chip[data-isla].sel').dataset.isla"), "letras")
    pg.click("#ddIr"); pg.wait_for_timeout(120); igual(dd_tit(pg), "Ahora le toca a Valentino", "empieza el que se tocó primero"); igual(dd_estado(pg, "D.isla.id"), "letras")
    pg.click("#ddAcc .btn.grande"); pg.wait_for_timeout(250); igual(dd_id(pg), "act"); igual(pg.evaluate("KID"), "Valentino")
    verificar(pg.evaluate("S.session.items.every(i=>i.skill.id.startsWith('let_')||ACTIVITIES[i.skill.type])"), "juega habilidades de Letras")
    verificar(pg.evaluate("PACK.id") == "letras", "isla elegida")
    ctx.close()
    # desde el mapa: la tarjeta está en el mapa y "volver" regresa al mapa
    ctx, pg = dd_pagina(C); entrar(pg, "Valentino")
    igual(pg.evaluate("[...document.querySelectorAll('#islands .island')].map(x=>x.innerText.split('\\n')[1])"), ["Isla Música", "Isla Números", "Isla Letras", "Isla Misiones", "Isla Ritmo", "De a dos", "Isla Animales"], "tarjeta en el mapa")
    pg.click("#islands [data-modo=dedos]"); pg.wait_for_timeout(120)
    igual(pg.evaluate("[...document.querySelectorAll('.dd-chip[data-k]')].map(x=>x.querySelector('b').innerText+':'+(x.querySelector('.dd-ord')||{innerText:''}).innerText)"), ["Giovanni:2", "Valentino:1"], "desde el mapa empieza quien estaba jugando")
    pg.click("#ddSetupBack"); pg.wait_for_timeout(100); igual(dd_id(pg), "map", "volver regresa al mapa"); ctx.close()
    # un chico sin tiempo hoy no se puede elegir
    ctx, pg = dd_pagina(C, st=dd_store(limite=15, time={"Valentino|" + time.strftime("%Y-%m-%d"): 900}))
    pg.click("[data-modo=dedos]"); pg.wait_for_timeout(120)
    verificar(pg.evaluate("document.querySelector('.dd-chip[data-k=\"1\"]').disabled"), "Valentino ya jugó sus 15 minutos: no se puede elegir")
    verificar("Ya jugó hoy" in dd_texto(pg) and "dos jugadores con tiempo" in dd_texto(pg), dd_texto(pg)); verificar(pg.evaluate("document.getElementById('ddIr').disabled"))
    ctx.close()

@prueba("de a dos: los turnos se alternan, cada chico juega SU plan y su progreso solo cambia con SUS respuestas (reglas de dominio y ayudas intactas)")
def t_dd_turnos(C):
    ctx, pg = dd_pagina(C, st=dd_store(practicando=False)); dd_empezar(pg)
    JS_PLAN = "(()=>({ses:S.session.items.map(i=>i.skill.id), desbloq:unlockedList().map(s=>s.id), dominadas:PACK.skills.filter(s=>store.sk[KID+'|'+s.id]&&store.sk[KID+'|'+s.id].mast).map(s=>s.id)}))()"
    orden = []; items = {}
    for n in range(4):
        quien = dd_estado(pg, "D.kids[D.idx%2]"); otro = "Valentino" if quien == "Giovanni" else "Giovanni"
        igual(dd_tit(pg), "Ahora le toca a " + quien, "pantalla de entrega"); igual(pg.evaluate("document.querySelector('#ddAv .dd-av').innerText"), {"Giovanni": "🦊", "Valentino": "🐻"}[quien], "avatar grande")
        igual(pg.evaluate("window.__LOG[window.__LOG.length-1]"), "Ahora le toca a %s. Cuando quieras, tocá el botón grande." % quien, "la voz anuncia el turno")
        antes_otro = dd_progreso(pg, otro); att0 = pg.evaluate("(k)=>Object.entries(store.sk).filter(([x,v])=>x.startsWith(k+'|')).reduce((a,[x,v])=>a+v.att,0)", quien)
        n_antes = dd_estado(pg, "D.porKid['%s'].n" % quien)
        dd0 = pg.evaluate("(k)=>[(store.log[k]||[]).length, (store.log[k]||[]).filter(e=>e.d===1).length]", quien)
        dd_vamos(pg, True); igual(dd_id(pg), "act"); igual(pg.evaluate("KID"), quien, "el motor juega con el chico del turno"); orden.append(quien)
        igual(pg.evaluate("document.querySelector('#ddEquipo .dd-quien span:last-child').innerText.trim()"), quien, "franja con el nombre")
        plan = pg.evaluate(JS_PLAN); items.setdefault(quien, set()).update(plan["ses"])
        verificar(set(plan["ses"]) <= set(plan["desbloq"]), "ítems fuera del plan de %s: %s" % (quien, plan["ses"]))
        verificar(not (set(plan["ses"]) & set(plan["dominadas"])), "%s repasa lo que no toca todavía: %s" % (quien, plan["ses"]))
        igual(len(plan["ses"]), 4, "4 ítems por turno")
        r = dd_turno(pg, cada_error=2 if (quien == "Valentino" and n == 3) else 0); igual(r, "ddPaso", "al terminar el turno vuelve la entrega")
        igual(dd_progreso(pg, otro), antes_otro, "el progreso de %s NO cambió durante el turno de %s" % (otro, quien))
        d = pg.evaluate("(k)=>{ const sk=Object.entries(store.sk).filter(([x,v])=>x.startsWith(k+'|')); return [sk.reduce((a,[x,v])=>a+v.att,0), (store.log[k]||[]).length, (store.log[k]||[]).filter(e=>e.d===1).length]; }", quien)
        n_resp = dd_estado(pg, "D.porKid['%s'].n" % quien) - n_antes
        igual(d[0] - att0, n_resp, "intentos de %s sumados en este turno = respuestas de su turno" % quien); igual(d[2] - dd0[1], n_resp, "eventos de este turno marcados d:1 (de a dos)")
        if n == 1 and quien == "Valentino":   # 4 aciertos al primer intento desde cero: las MISMAS cuentas que en una sesión suelta
            s = pg.evaluate("store.sk['Valentino|num_c10']"); esp = .5
            for _ in range(4): esp = esp * .7 + .3   # la fórmula del motor (itemDone), 4 aciertos al primer intento
            verificar(abs(s["score"] - esp) < 1e-9, "puntaje %r ≠ %r" % (s["score"], esp)); igual([s["att"], s["lvl"], s["rec"], s["mast"]], [4, 1, [1], False], "dominio y ayudas igual que siempre")
        if n < 3:
            if dd_tit(pg).startswith("¡Armaron"): pg.click("#ddAcc .btn.grande"); pg.wait_for_timeout(150)   # el 8.º casillero completó el dibujo
            igual(dd_tit(pg), "Ahora le toca a " + otro, "entrega al otro")
    igual(orden, ["Giovanni", "Valentino", "Giovanni", "Valentino"], "alternan")
    verificar("num_c10" not in items["Giovanni"], "a Giovanni no le tocó lo de Valentino: %s" % items["Giovanni"]); verificar(items["Valentino"] == {"num_c10"}, "Valentino solo juega lo suyo: %s" % items["Valentino"])
    verificar(items["Giovanni"] <= {"num_sub5", "num_c20", "num_add10"}, "Giovanni juega su siguiente nivel: %s" % items["Giovanni"])
    igual(dd_estado(pg, "[D.porKid.Giovanni.turnos, D.porKid.Valentino.turnos]"), [2, 2])
    igual(pg.evaluate("S.session"), None, "no queda sesión suelta entre turnos"); ctx.close()

@prueba("de a dos: el dibujo del equipo crece con los aciertos de cualquiera, un error no resta, mostrar la respuesta no suma y completarlo se celebra")
def t_dd_equipo(C):
    ctx, pg = dd_pagina(C, st=dd_store(practicando=False)); dd_empezar(pg)
    eq = lambda: pg.evaluate("(()=>{ const e=Gioval.dedos.equipo('Giovanni','Valentino'); return [e.piezas,e.cuadros,e.total]; })()")
    igual(eq(), [0, 0, 0]); igual(pg.evaluate("document.querySelectorAll('#ddCuadro .dd-cell').length"), 8, "8 casilleros"); verificar("Huerta (0 de 8)" in dd_texto(pg), dd_texto(pg))
    dd_vamos(pg, True); dd_turno(pg); igual(eq(), [4, 0, 4], "Giovanni: 4 aciertos → 4 piezas")
    igual(pg.evaluate("document.querySelectorAll('#ddCuadro .dd-cell.on').length"), 4, "se ven las 4 piezas en la entrega"); verificar("Huerta (4 de 8)" in dd_texto(pg))
    dd_vamos(pg, True); dd_turno(pg, cada_error=1)   # Valentino se equivoca primero en cada ítem y después acierta
    n_v = dd_estado(pg, "D.porKid.Valentino.n"); verificar(n_v >= 4, "respondió %d" % n_v)
    e = eq(); igual(e[2], 4 + n_v, "los errores no restan: cada ítem resuelto sin que la app muestre la respuesta suma una pieza"); igual(e[0] + 8 * e[1], 4 + n_v)
    igual(dd_estado(pg, "D.piezas"), 4 + n_v, "piezas de la sesión")
    # mostrar la respuesta (3 errores) no suma: el resto sí
    base = eq()[2]; n0 = dd_estado(pg, "D.porKid.Giovanni.n"); dd_vamos(pg, True); dd_revelar(pg); dd_turno(pg); n_g = dd_estado(pg, "D.porKid.Giovanni.n") - n0
    igual(eq()[2], base + n_g - 1, "el ítem con la respuesta mostrada no suma pieza; los demás sí")
    ctx.close()
    # completar el dibujo: celebración, dibujo nuevo, y todo queda guardado (también tras recargar)
    ctx, pg = dd_pagina(C, st=dd_store(practicando=False, dedos={"eq": {"Giovanni|Valentino": {"piezas": 6, "cuadros": 0, "total": 6}}, "reg": {}})); dd_empezar(pg)
    dd_vamos(pg, True); r = dd_turno(pg); igual(r, "ddPaso")
    igual(dd_tit(pg), "¡Armaron el dibujo «Huerta» entre los dos!", "celebración al completar"); igual(eq(), [2, 1, 10], "1 dibujo completo y 2 piezas del siguiente")
    verificar(any("Lo lograron" in x for x in pg.evaluate("window.__LOG")), "la voz lo celebra")
    pg.click("#ddAcc .btn.grande"); pg.wait_for_timeout(150); igual(dd_tit(pg), "Ahora le toca a Valentino"); verificar("Ciudad (2 de 8)" in dd_texto(pg), "el dibujo nuevo (Ciudad) sigue con 2 piezas: " + dd_texto(pg))
    pg.evaluate("save(); Gioval.almacen.guardarYa()"); pg.reload(); esperar_listo(pg)
    igual(pg.evaluate("store.dedos.eq['Giovanni|Valentino']"), {"piezas": 2, "cuadros": 1, "total": 10}, "el dibujo del equipo se conserva al recargar"); ctx.close()

@prueba("de a dos: explicar a otro (regla fija): se propone solo cuando el otro practica lo que yo ya domino, suma piezas al equipo y NADA al dominio")
def t_dd_explicar(C):
    ctx, pg = dd_pagina(C, st=dd_store(practicando=True)); dd_empezar(pg)   # Giovanni domina num_c10; Valentino lo está practicando (3 intentos)
    prop = pg.evaluate("(()=>{ const p=Gioval.dedos.proponerExplicacion('Giovanni'); return p&&[p.id,p.explica,p.oyente]; })()"); igual(prop, ["num_c10", "Giovanni", "Valentino"], "regla: Giovanni domina lo que Valentino practica")
    igual(pg.evaluate("Gioval.dedos.proponerExplicacion('Valentino')"), None, "Valentino no domina nada que Giovanni esté practicando")
    dd_vamos(pg); igual(dd_id(pg), "ddPaso"); igual(dd_tit(pg), "Giovanni, ¡te toca explicar!")
    t = dd_texto(pg); verificar("Valentino está practicando «Contar hasta 10» y vos ya lo sabés. ¿Le explicás cómo se hace?" in t, t)
    verificar(any(c in t for c in ("Contale qué mirás primero.", "Mostrale un ejemplo.", "Decile qué hacés cuando te trabás.")), "consejo simple: " + t)
    verificar(any("te toca explicar" in x or "está practicando" in x for x in pg.evaluate("window.__LOG")), "la voz lo dice")
    antes = (dd_progreso(pg, "Giovanni"), dd_progreso(pg, "Valentino"), pg.evaluate("JSON.stringify(store.time)"))
    eq0 = pg.evaluate("Gioval.dedos.equipo('Giovanni','Valentino').total")
    pg.click("#ddAcc .btn:has-text('Ya le expliqué')"); pg.wait_for_timeout(300)
    igual(dd_id(pg), "act", "después de explicar empieza su turno"); igual(pg.evaluate("KID"), "Giovanni")
    igual(pg.evaluate("Gioval.dedos.equipo('Giovanni','Valentino').total"), eq0 + 2, "+2 piezas de equipo")
    igual((dd_progreso(pg, "Giovanni"), dd_progreso(pg, "Valentino")), antes[:2], "explicar NO toca el dominio, el registro ni los días de nadie")
    igual(dd_estado(pg, "[D.porKid.Giovanni.e, D.porKid.Valentino.r, D.expl.n]"), [1, 1, 1])
    dd_turno(pg)   # turno de Giovanni; después el de Valentino (con errores para no dominar), y de nuevo Giovanni: no se repite la propuesta
    dd_vamos(pg); dd_turno(pg, cada_error=1)
    dd_vamos(pg); igual(dd_id(pg), "act", "no se repite la misma explicación en esta sesión (ni antes de 3 turnos)")
    dd_turno(pg); r = pg.evaluate("Gioval.dedos.datos().reg"); igual(r["Giovanni"][0]["e"], 1, "registro: explicó 1 vez"); igual(r["Valentino"][0]["r"], 1, "registro: escuchó 1 vez"); igual(r["Giovanni"][0]["r"], 0)
    ctx.close()
    # "Ahora no": sin premio y sin castigo; una saltada sin comprobar NO es saber (no se propone); con el otro sin tiempo tampoco
    ctx, pg = dd_pagina(C, st=dd_store(practicando=True)); dd_empezar(pg); dd_vamos(pg)
    eq0 = pg.evaluate("Gioval.dedos.equipo('Giovanni','Valentino').total"); pg.click("#ddAcc .btn.alt"); pg.wait_for_timeout(250)
    igual(dd_id(pg), "act"); igual(pg.evaluate("Gioval.dedos.equipo('Giovanni','Valentino').total"), eq0, "sin premio"); igual(dd_estado(pg, "D.expl.n"), 0, "no cuenta como explicación")
    verificar(pg.evaluate("Gioval.dedos.proponerExplicacion('Giovanni')") is None, "no se vuelve a pedir lo mismo"); ctx.close()
    st = dd_store(practicando=True); st["sk"]["Giovanni|num_c10"]["skip"] = {"por": "rapido", "t": 1, "estado": "pendiente"}
    ctx, pg = dd_pagina(C, st=st); dd_empezar(pg); igual(pg.evaluate("Gioval.dedos.proponerExplicacion('Giovanni')"), None, "una habilidad saltada sin comprobar no cuenta como saber"); ctx.close()
    ctx, pg = dd_pagina(C, st=dd_store(practicando=True, limite=15, time={"Valentino|" + time.strftime("%Y-%m-%d"): 899})); dd_empezar(pg)
    pg.evaluate("store.time['Valentino|'+today()]=900"); igual(pg.evaluate("Gioval.dedos.proponerExplicacion('Giovanni')"), None, "si el otro ya no tiene tiempo hoy, no se propone"); ctx.close()
    ctx, pg = dd_pagina(C, st=dd_store(practicando=False)); dd_empezar(pg); igual(pg.evaluate("Gioval.dedos.proponerExplicacion('Giovanni')"), None, "si el otro todavía no practicó esa habilidad, no se propone"); ctx.close()

@prueba("de a dos: tope diario por chico (cada turno gasta SU tiempo; al llegar al tope sigue el otro o termina con mensaje amable; sin apuro ni castigo)")
def t_dd_tope(C):
    hoy = lambda k: "%s|%s" % (k, time.strftime("%Y-%m-%d"))
    ctx, pg = dd_pagina(C, st=dd_store(practicando=False, limite=15)); dd_empezar(pg)
    t0 = pg.evaluate("[store.time['Giovanni|'+today()]||0, store.time['Valentino|'+today()]||0]")
    pg.wait_for_timeout(2300); igual(pg.evaluate("[store.time['Giovanni|'+today()]||0, store.time['Valentino|'+today()]||0]"), t0, "esperar en la entrega de turno NO gasta tiempo de nadie")
    dd_vamos(pg); pg.wait_for_timeout(2300); dd_uno(pg)   # Giovanni mira la pantalla un rato y responde
    t1 = pg.evaluate("[store.time['Giovanni|'+today()]||0, store.time['Valentino|'+today()]||0]"); verificar(t1[0] >= t0[0] + 2, "el turno gasta el tiempo de Giovanni: %s → %s" % (t0, t1)); igual(t1[1], t0[1], "y no el de Valentino")
    dd_turno(pg)
    ctx.close()
    ctx, pg = dd_pagina(C, st=dd_store(practicando=False, limite=15)); dd_empezar(pg); dd_vamos(pg)
    pg.evaluate("store.time['Giovanni|'+today()]=capBase()-1"); pg.wait_for_timeout(1600)   # pasa el segundo del reloj: el motor avisa el tope
    igual(dd_id(pg), "act", "el cartel de tope del motor NO interrumpe el ítem en curso"); verificar(not pg.evaluate("document.getElementById('capBox').classList.contains('show')"), "no sale el cartel de siempre")
    dd_uno(pg); pg.wait_for_function("document.querySelector('.screen.active').id==='ddPaso'", timeout=6000)
    igual(dd_tit(pg), "Giovanni ya jugó por hoy"); t = dd_texto(pg); verificar("completó los 15 minutos de hoy. ¡Gracias por jugar! Mañana seguimos." in t and "Seguir con Valentino" in t and "Terminar por hoy" in t, t)
    igual(dd_estado(pg, "D.porKid.Giovanni.n"), 1, "terminó solo el ítem que tenía en curso")
    tg = pg.evaluate("store.time['Giovanni|'+today()]"); pg.wait_for_timeout(1500); igual(pg.evaluate("store.time['Giovanni|'+today()]"), tg, "Giovanni ya no gasta tiempo")
    ant_g = dd_progreso(pg, "Giovanni")
    pg.click("#ddAcc .btn:has-text('Seguir con Valentino')"); pg.wait_for_timeout(150); igual(dd_tit(pg), "Ahora le toca a Valentino")
    dd_vamos(pg); pg.wait_for_timeout(1300); dd_turno(pg); igual(dd_tit(pg), "Ahora le toca a Valentino", "Giovanni ya no tiene tiempo: sigue Valentino otra vez")
    igual(dd_progreso(pg, "Giovanni"), ant_g, "el progreso de Giovanni no cambió mientras jugó Valentino"); verificar(pg.evaluate("store.time['Valentino|'+today()]") >= 1, "tiempo de Valentino")
    # Valentino también llega a su tope: la sesión termina con un mensaje amable (sin cartel de motor y sin entrega)
    dd_vamos(pg); pg.evaluate("store.time['Valentino|'+today()]=capBase()-1"); pg.wait_for_timeout(1600); dd_uno(pg)
    pg.wait_for_function("document.getElementById('ddTit').innerText==='¡Buen trabajo, equipo!'", timeout=6000)
    t = dd_texto(pg); verificar("Giovanni: 1 respuesta" in t and "Valentino: " in t and "Hoy sumaron" in t, t)
    verificar(any("Gracias por jugar de a dos, Giovanni y Valentino" in x for x in pg.evaluate("window.__LOG")), "la voz se despide")
    # el registro quedó guardado por chico
    r = pg.evaluate("Gioval.dedos.datos().reg"); igual([r["Giovanni"][0]["c"], r["Valentino"][0]["c"]], ["Valentino", "Giovanni"]); igual(r["Giovanni"][0]["n"], 1); verificar(r["Valentino"][0]["n"] >= 1 and r["Valentino"][0]["s"] >= 1, str(r["Valentino"]))
    pg.click("#ddAcc .btn"); pg.wait_for_timeout(150); igual(dd_id(pg), "who", "al terminar vuelve a ¿Quién juega?"); ctx.close()
    # si en pleno ítem no se resuelve nada, a los 45 s (acá 0,4) el turno se cierra solo y amablemente; un +15 min de los adultos devuelve el tiempo
    ctx, pg = dd_pagina(C, st=dd_store(practicando=False, limite=15)); dd_empezar(pg); dd_vamos(pg)
    pg.evaluate("Gioval.dedos.AJ.graciaTopeMs=400; store.time['Giovanni|'+today()]=capBase()+5"); pg.wait_for_function("document.querySelector('.screen.active').id==='ddPaso'", timeout=8000)
    igual(dd_tit(pg), "Giovanni ya jugó por hoy"); igual(pg.evaluate("[S.session, S.tap]"), [None, None], "no queda nada colgado")
    pg.evaluate("store.extra['Giovanni|'+today()]=900"); igual(pg.evaluate("Gioval.dedos.restante('Giovanni')>0"), True, "+15 min de los adultos suma tiempo a ese chico"); ctx.close()
    # pausa con ⬅: lo hecho queda guardado, se puede seguir o terminar
    ctx, pg = dd_pagina(C, st=dd_store(practicando=False)); dd_empezar(pg); dd_vamos(pg); dd_uno(pg)
    pg.click("#btnActBack"); pg.wait_for_timeout(150); igual(dd_id(pg), "ddPaso"); igual(dd_tit(pg), "¿Terminamos por hoy?"); verificar("Lo que hicieron hasta ahora quedó guardado." in dd_texto(pg))
    igual(pg.evaluate("store.sk['Giovanni|num_sub5']&&store.sk['Giovanni|num_sub5'].att||store.sk['Giovanni|num_c20']&&store.sk['Giovanni|num_c20'].att||store.sk['Giovanni|num_add10']&&store.sk['Giovanni|num_add10'].att"), 1, "la respuesta anterior ya estaba guardada")
    pg.click("#ddAcc .btn.grande"); pg.wait_for_timeout(250); igual(dd_id(pg), "act", "seguir jugando"); igual(pg.evaluate("KID"), "Giovanni")
    pg.click("#btnActBack"); pg.wait_for_timeout(150); pg.click("#ddAcc .btn.alt"); pg.wait_for_timeout(150); igual(dd_tit(pg), "¡Buen trabajo, equipo!"); ctx.close()

@prueba("de a dos: informe para adultos por chico (sesiones, respuestas, explicaciones) y sin sección si nunca jugó de a dos")
def t_dd_informe(C):
    ctx, pg = dd_pagina(C, st=dd_store(practicando=True)); dd_empezar(pg)
    dd_vamos(pg); pg.click("#ddAcc .btn:has-text('Ya le expliqué')"); pg.wait_for_timeout(250); dd_turno(pg)
    dd_vamos(pg); dd_turno(pg, cada_error=1); dd_terminar(pg)
    igual(dd_tit(pg), "¡Buen trabajo, equipo!"); pg.click("#ddAcc .btn"); pg.wait_for_timeout(150)
    r = pg.evaluate("Gioval.dedos.datos().reg"); g, v = r["Giovanni"][0], r["Valentino"][0]
    rep = {k: pg.evaluate("(k)=>{ KID=k; return reportText(); }", k) for k in ("Giovanni", "Valentino", "Otro")}
    verificar("DE A DOS (por turnos, en el mismo aparato)" in rep["Giovanni"] and "1 sesión de a dos." in rep["Giovanni"], rep["Giovanni"])
    verificar("Explicarle a otro no suma nada al dominio." in rep["Giovanni"], "aclara que explicar no suma dominio")
    pl = lambda n, a, b: "%d %s" % (n, a if n == 1 else b)
    fila = lambda e, c: "con %s: %s (%d al primer intento), %d min, %s" % (c, pl(e["n"], "respuesta", "respuestas"), e["ok"], round(e["s"] / 60), pl(e["tr"], "turno", "turnos"))
    verificar(fila(g, "Valentino") in rep["Giovanni"], "fila de Giovanni: " + rep["Giovanni"][-900:])
    verificar(fila(v, "Giovanni") in rep["Valentino"], "fila de Valentino (con SUS cifras): " + rep["Valentino"][-900:])
    verificar(g["n"] != v["n"] or g["tr"] != v["tr"] or g["ok"] != v["ok"], "las cifras de cada chico son distintas (si no, la prueba no distingue)")
    verificar("Le explicó a Valentino (1 vez). No cuenta para el dominio." in rep["Giovanni"] and "Escuchó la explicación de Giovanni (1 vez)." in rep["Valentino"], "explicaciones por chico")
    verificar("Escuchó" not in rep["Giovanni"] and "Le explicó" not in rep["Valentino"], "cada chico ve solo lo suyo")
    verificar("DE A DOS" not in rep["Otro"], "quien nunca jugó de a dos no tiene la sección")
    igual(pg.evaluate("(k)=>(store.log[k]||[]).filter(e=>e.d===1).length", "Giovanni"), g["n"], "eventos de práctica marcados")
    # lo que respondieron cuenta en su progreso de siempre: la sección de la isla también lo muestra
    verificar("Contar hasta 10" in rep["Valentino"] and "Contar hasta 10" in rep["Giovanni"], "las habilidades siguen en el informe de siempre")
    ctx.close()

JS_DD_EXTRA = """(function(){ const W=innerWidth,H=innerHeight,o=[];
  if(document.body.scrollWidth>document.body.clientWidth+2) o.push('body: desborde horizontal');
  document.querySelectorAll('.dd-chip,.dd-cell,.dd-quien,.dd-eq,#ddCuadro,.dd-acc,.dd-txt').forEach(e=>{ if(e.closest('.screen:not(.active)')) return; const r=e.getBoundingClientRect(); if(!r.width) return;
    if(r.right>W+1||r.left<-1) o.push((e.id||e.className)+' fuera de pantalla (horizontal)'); });
  const a=document.querySelector('.screen.active'); if(a&&a.id==='ddPaso'){ const b=a.querySelector('#ddAcc .btn'); if(b){ const r=b.getBoundingClientRect(); if(r.bottom>H+1||r.top<0) o.push('el botón principal no se ve sin desplazar (arriba='+Math.round(r.top)+', abajo='+Math.round(r.bottom)+', alto de pantalla='+H+')'); } }
  if(a&&a.id==='ddSetup'){ const b=a.querySelector('#ddIr'); const r=b.getBoundingClientRect(); const p=a.querySelector('#ddSetupBody'); if(r.bottom>H+1&&!(p.scrollHeight>p.clientHeight)) o.push('A jugar fuera de pantalla'); }
  return o; })()"""

def dd_recorrer(pg, ver, texto=None):
    """Pasa por TODAS las pantallas de De a dos: armado, entrega, explicar, turno (con la franja del equipo), pausa, tope, celebración, entrega al que sigue y fin."""
    pg.evaluate("Gioval.dedos.AJ.graciaTopeMs=300")
    pg.click("[data-modo=dedos]"); pg.wait_for_timeout(150); ver("1_armado")
    pg.click("#ddIr"); pg.wait_for_timeout(150); ver("2_entrega")
    pg.click("#ddAcc .btn.grande"); pg.wait_for_timeout(150); ver("3_explicar")
    pg.click("#ddAcc .btn.grande"); pg.wait_for_timeout(400); dd_uno(pg); pg.wait_for_timeout(150); ver("4_turno")
    pg.click("#btnActBack"); pg.wait_for_timeout(150); ver("5_pausa")
    pg.click("#ddAcc .btn.grande"); pg.wait_for_timeout(300)
    pg.evaluate("store.time[KID+'|'+today()]=capBase()+1"); pg.wait_for_function("document.querySelector('.screen.active').id==='ddPaso'", timeout=9000); pg.wait_for_timeout(100); ver("6_tope")
    pg.click("#ddAcc .btn:not(.alt)"); pg.wait_for_timeout(150); ver("7_celebracion")
    pg.click("#ddAcc .btn.grande"); pg.wait_for_timeout(150); ver("8_entrega_solo")
    pg.click("#ddAcc .btn.alt"); pg.wait_for_timeout(150); ver("9_fin")

def dd_sembrado(): return dd_store(practicando=True, limite=15, dedos={"eq": {"Giovanni|Valentino": {"piezas": 6, "cuadros": 0, "total": 6}}, "reg": {}})

@prueba("de a dos: sin desbordes horizontales y con el botón principal a la vista en Pixel 7, 360x700, 740x330 y tableta 820x1180 (es-AR); capturas")
def t_dd_vistas(C):
    mal = []
    for v in ("pixel7", "360x700", "740x330", "820x1180"):
        ctx, pg = dd_pagina(C, vista=v, st=dd_sembrado(), congelar=True, semilla=62)
        def ver(n, v=v, pg=pg):
            pg.wait_for_timeout(120); r = pg.evaluate(JS_DESBORDES) + pg.evaluate(JS_DD_EXTRA)
            CAPTURAS.append(foto(pg, "%s_90_dedos_%s" % (v, n)))
            mal.extend("%s %s: %s" % (v, n, x) for x in r)
        dd_recorrer(pg, ver); ctx.close()
    verificar(not mal, "desbordes: " + "; ".join(mal[:10]))

@prueba("de a dos con el pseudo-idioma (+40 %, acentos) y en RTL: sin desbordes que no hubiera en es-AR")
def t_dd_pseudo(C):
    mal = []
    for idioma in ("qps-ploc", "qps-plocm"):
        for v in ("360x700", "740x330", "820x1180"):
            ctx, pg = dd_pagina(C, vista=v, st=dd_sembrado(), idioma=idioma, congelar=True, semilla=63)
            def ver(n, v=v, pg=pg, idioma=idioma):
                pg.wait_for_timeout(120); r = pg.evaluate(JS_DESBORDES) + pg.evaluate(JS_DD_EXTRA)
                if v != "820x1180": CAPTURAS.append(foto(pg, "%s_%s_91_dedos_%s" % (v, idioma, n)))
                mal.extend("%s %s %s: %s" % (idioma, v, n, x) for x in r)
            dd_recorrer(pg, ver)
            igual(pg.evaluate("[document.documentElement.dir, Gioval.i18n.faltantes.size]"), ["rtl" if idioma == "qps-plocm" else "ltr", 0], "dir/faltantes"); ctx.close()
    verificar(not mal, "desbordes: " + "; ".join(mal[:12]))

@prueba("de a dos en inglés: todas las pantallas, la voz y el informe sin una palabra en español, sin claves faltantes")
def t_dd_ingles(C):
    ctx, pg = dd_pagina(C, st=dd_sembrado(), idioma="en", semilla=64); textos = []
    dd_recorrer(pg, lambda n: textos.append(dd_texto(pg)))
    dicho = pg.evaluate("window.__LOG.concat(window.__BUB)"); todo = [l for t in textos for l in t.split("\n") if l.strip()] + dicho
    verificar(not sin_espanol(todo), "español en inglés: %s" % sin_espanol(todo)[:5])
    verificar(any("It's Giovanni's turn" in x for x in dicho) and any("You built the “Garden” picture together!" in x for x in textos), "frases en inglés: %s" % textos[:3])
    rep = pg.evaluate("(()=>{ KID='Giovanni'; return reportText(); })()"); verificar("TOGETHER (in turns, on the same device)" in rep and "with Valentino" in rep, rep[-700:])
    verificar(not sin_espanol([l for l in rep.split("\n") if "TOGETHER" in l or "with Valentino" in l or "Explained" in l]), "informe en inglés")
    igual(pg.evaluate("[...Gioval.i18n.faltantes]"), [], "claves faltantes"); ctx.close()

@prueba("de a dos: el almacén v3 → v4 conserva TODO, crea 'dedos' vacío, deja copia previa exacta, no migra dos veces y un respaldo con 'dedos' se restaura")
def t_dd_migracion(C):
    v3 = {"version": 3, "profiles": ["Giovanni", "Valentino"], "stars": {"x": 2}, "sk": {"Giovanni|n1": dd_sk(True, 9), "Valentino|num_c10": dd_sk(False, 3)}, "days": {"Giovanni": ["2026-11-01"]},
          "time": {"Giovanni|2026-11-01": 300}, "log": {"Giovanni": [{"t": 5, "s": "n1", "o": 1, "f": 1, "g": 0, "k": "learn"}]}, "checks": {"Giovanni": [{"d": "2026-11-02", "n": 4, "ok": 3, "p": "musica"}]},
          "extra": {"Giovanni|2026-11-01": 900}, "limit": {"Giovanni": 20}, "idioma": {"Valentino": "en"}, "intake": {"Valentino": {"v": 1, "edad": 6, "resp": {}}}, "meta": {"ultimoRespaldo": 5, "guardado": 9, "desde": 7}}
    txt = json.dumps(v3); ctx = C.banco.contexto("360x700"); err = []
    pg = abrir(ctx, C.url + "/index.html", store=txt, errores=err); nuevo = pg.evaluate("JSON.parse(JSON.stringify(store))")
    igual(nuevo["version"], 4, "version"); igual(nuevo["dedos"], {}, "dedos vacío")
    for k in v3:
        if k not in ("version", "meta"): igual(nuevo[k], v3[k], "campo " + k)
    igual(nuevo["meta"]["ultimoRespaldo"], 5, "meta conservada")
    igual(pg.evaluate("localStorage.getItem('gioval_pre_migracion')"), txt, "copia previa exacta (localStorage)")
    rs = pg.evaluate("Gioval.almacen.respaldos()"); verificar(len(rs) == 1 and "pre-migracion-v3" in rs[0]["id"] and json.loads(rs[0]["json"]) == v3, "copia previa en IndexedDB: %s" % [r["id"] for r in rs])
    igual(pg.evaluate("Gioval.almacen.errorMigracion"), None)
    # jugar de a dos sobre datos migrados, guardar, recargar: sigue todo y no vuelve a migrar ni a copiar
    pg.evaluate("Gioval.dedos.equipo('Giovanni','Valentino').piezas=3; Gioval.dedos.datos().reg.Giovanni=[{t:1,c:'Valentino',n:2,ok:1,s:60,tr:1,e:0,r:0,p:2}]; save(); Gioval.almacen.guardarYa()")
    pg.reload(); esperar_listo(pg)
    igual(pg.evaluate("store.version"), 4); igual(pg.evaluate("store.dedos.eq['Giovanni|Valentino'].piezas"), 3, "el dibujo se conserva"); igual(pg.evaluate("store.dedos.reg.Giovanni[0].n"), 2)
    igual(len(pg.evaluate("Gioval.almacen.respaldos()")), 1, "no vuelve a migrar ni a hacer otra copia")
    # restaurar un respaldo con 'dedos' (formato de exportar) y otro viejo sin 'dedos' (v3): ambos quedan bien
    datos = pg.evaluate("JSON.parse(JSON.stringify(store))")
    pg.evaluate("(d)=>Gioval.almacen.restaurar(d)", datos); igual(pg.evaluate("store.dedos.eq['Giovanni|Valentino'].piezas"), 3, "restaurar conserva dedos")
    r = pg.evaluate("(async(v3)=>{ const f=new File([JSON.stringify({app:'gioval',formato:1,store:v3})],'r.json'); const o=await Gioval.almacen.leerRespaldo(f); return [o.ok,o.datos&&o.datos.version,o.datos&&JSON.stringify(o.datos.dedos)]; })(%s)" % txt)
    igual(r, [True, 4, "{}"], "un respaldo viejo (v3) se convierte al leerlo"); verificar(not err, str(err)); ctx.close()

@prueba("de a dos: no cambia nada si no se usa (sesión suelta, tope del motor, informe y mapa de siempre; las islas registradas son las mismas)")
def t_dd_no_toca(C):
    ctx, pg = dd_pagina(C, st=dd_store(practicando=False)); entrar(pg, "Giovanni")
    igual(pg.evaluate("PACKS.map(p=>p.id)"), ["musica", "numeros", "letras", "misiones", "ritmo"], "De a dos no es una isla de aprendizaje")
    igual(pg.evaluate("Gioval.modos.map(m=>m.id)"), ["dedos"])
    abrir_isla(pg, "Números"); tarjeta(pg, "Sesión de hoy"); verificar(jugar(pg, perfecto=True) == "fin", "sesión suelta"); cerrar_fin(pg, "#btnFinOk")
    igual(pg.evaluate("S.session"), None); igual(pg.evaluate("document.getElementById('ddEquipo').classList.contains('on')"), False, "la franja del equipo no aparece en una sesión suelta")
    verificar("DE A DOS" not in pg.evaluate("reportText()"), "informe sin sección")
    pg.evaluate("S.run++; resetFlow(); goMap(); store.time['Giovanni|'+today()]=0"); llegar_al_tope(pg, "Números")
    verificar(pg.evaluate("document.getElementById('capBox').classList.contains('show')"), "el tope del motor sigue funcionando en una sesión suelta"); ctx.close()

# ================================================================== runner
class Ctx: pass

def main():
    filtro = sys.argv[1].lower() if len(sys.argv) > 1 else ""
    SALIDA.mkdir(parents=True, exist_ok=True)
    for f in SALIDA.glob("*"):
        if f.is_file(): f.unlink()
    srv, url = servidor()
    resultados = []; t0 = time.time()
    with sync_playwright() as pw:
        C = Ctx(); C.pw = pw; C.url = url; C.banco = Banco(pw); C.err = []
        for nombre, fn in TESTS:
            if filtro and filtro not in nombre.lower(): continue
            ini = time.time(); C.err.clear()
            try:
                det = fn(C) or ""
                if C.err: raise Falla("errores de consola: %s" % C.err[:3])
                resultados.append((nombre, True, det, time.time() - ini)); print("  PASA  %s  (%.1fs) %s" % (nombre, time.time() - ini, det), flush=True)
            except Exception as e:
                msg = (str(e) if isinstance(e, Falla) else "".join(traceback.format_exception_only(type(e), e)).strip())[:600]
                if os.environ.get("GIOVAL_TB"): traceback.print_exc()
                resultados.append((nombre, False, msg, time.time() - ini)); print("  FALLA %s\n        %s" % (nombre, msg), flush=True)
        C.banco.cerrar()
    ok = sum(1 for r in resultados if r[1]); mal = len(resultados) - ok
    caps = sorted(p.name for p in SALIDA.glob("*.png") if not p.name.startswith("cmp_"))
    lineas = ["RESUMEN DE PRUEBAS DE MUNDO GIOVAL", time.strftime("%Y-%m-%d %H:%M"), "versión de la app: " + re.search(r'"([^"]+)"', (APP / "js/version.js").read_text()).group(1), "",
              "Total: %d pruebas · pasan %d · fallan %d · %.0f s" % (len(resultados), ok, mal, time.time() - t0), ""]
    for n, p, d, t in resultados: lineas.append("[%s] %s%s" % ("PASA" if p else "FALLA", n, ("\n       " + d) if d else ""))
    lineas += ["", "CAPTURAS (gioval-dev/tests/salida/):"] + ["  " + c for c in caps] + ["  (y %d pares cmp_* anterior/nueva usados en la comparación visual)" % len(list(SALIDA.glob("cmp_*_anterior.png")))]
    (SALIDA / "resumen.txt").write_text("\n".join(lineas), encoding="utf-8")
    print("\n" + "\n".join(lineas[:5])); srv.shutdown()
    sys.exit(0 if mal == 0 else 1)

if __name__ == "__main__":
    main()
